from otp.ai.AIBaseGlobal import *
from direct.task.Task import Task
from direct.distributed.ClockDelta import *
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State
from direct.distributed import DistributedObjectAI
from direct.fsm import State
from toontown.toonbase import ToontownAccessAI

class DistributedDoorAI(DistributedObjectAI.DistributedObjectAI):

    def __init__(self, air, blockNumber, doorType, doorIndex=0, lockValue=0, swing=3):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.block = blockNumber
        self.swing = swing
        self.otherDoor = None
        self.doorType = doorType
        self.doorIndex = doorIndex
        self.setDoorLock(lockValue)
        self.fsm = ClassicFSM.ClassicFSM('DistributedDoorAI_right', [
         State.State('off', self.enterOff, self.exitOff, [
          'closing', 'closed', 'opening', 'open']),
         State.State('closing', self.enterClosing, self.exitClosing, [
          'closed', 'opening']),
         State.State('closed', self.enterClosed, self.exitClosed, [
          'opening']),
         State.State('opening', self.enterOpening, self.exitOpening, [
          'open']),
         State.State('open', self.enterOpen, self.exitOpen, [
          'closing', 'open'])], 'off', 'off')
        self.fsm.enterInitialState()
        self.exitDoorFSM = ClassicFSM.ClassicFSM('DistributedDoorAI_left', [
         State.State('off', self.exitDoorEnterOff, self.exitDoorExitOff, [
          'closing', 'closed', 'opening', 'open']),
         State.State('closing', self.exitDoorEnterClosing, self.exitDoorExitClosing, [
          'closed', 'opening']),
         State.State('closed', self.exitDoorEnterClosed, self.exitDoorExitClosed, [
          'opening']),
         State.State('opening', self.exitDoorEnterOpening, self.exitDoorExitOpening, [
          'open']),
         State.State('open', self.exitDoorEnterOpen, self.exitDoorExitOpen, [
          'closing', 'open'])], 'off', 'off')
        self.exitDoorFSM.enterInitialState()
        self.doLaterTask = None
        self.exitDoorDoLaterTask = None
        self.avatarsWhoAreEntering = {}
        self.avatarsWhoAreExiting = {}
        return

    def delete(self):
        taskMgr.remove(self.uniqueName('door_opening-timer'))
        taskMgr.remove(self.uniqueName('door_open-timer'))
        taskMgr.remove(self.uniqueName('door_closing-timer'))
        taskMgr.remove(self.uniqueName('exit_door_open-timer'))
        taskMgr.remove(self.uniqueName('exit_door_closing-timer'))
        taskMgr.remove(self.uniqueName('exit_door_opening-timer'))
        self.ignoreAll()
        del self.fsm
        del self.exitDoorFSM
        del self.otherDoor
        DistributedObjectAI.DistributedObjectAI.delete(self)

    def getDoorIndex(self):
        return self.doorIndex

    def setSwing(self, swing):
        self.swing = swing

    def getSwing(self):
        return self.swing

    def getDoorType(self):
        return self.doorType

    def getZoneIdAndBlock(self):
        r = [
         self.zoneId, self.block]
        return r

    def setOtherDoor(self, door):
        self.otherDoor = door

    def getZoneId(self):
        return self.zoneId

    def getState(self):
        return [
         self.fsm.getCurrentState().getName(), globalClockDelta.getRealNetworkTime()]

    def getExitDoorState(self):
        return [
         self.exitDoorFSM.getCurrentState().getName(), globalClockDelta.getRealNetworkTime()]

    def isOpen(self):
        state = self.fsm.getCurrentState().getName()
        return state == 'open' or state == 'opening'

    def isClosed(self):
        return not self.isOpen()

    def setDoorLock(self, locked):
        self.lockedDoor = locked

    def isLockedDoor(self):
        if simbase.config.GetBool('no-locked-doors', 0):
            return 0
        else:
            return self.lockedDoor

    def sendReject(self, avatarID, lockedVal):
        self.sendUpdateToAvatarId(avatarID, 'rejectEnter', [lockedVal])

    def requestEnter(self):
        avatarID = self.air.getAvatarIdFromSender()
        lockedVal = self.isLockedDoor()
        if not ToontownAccessAI.canAccess(avatarID, self.zoneId, 'DistributedDoorAI.requestEnter'):
            lockedVal = True
        if lockedVal:
            self.sendReject(avatarID, lockedVal)
        else:
            self.enqueueAvatarIdEnter(avatarID)
            self.sendUpdateToAvatarId(avatarID, 'setOtherZoneIdAndDoId', [
             self.otherDoor.getZoneId(), self.otherDoor.getDoId()])

    def enqueueAvatarIdEnter(self, avatarID):
        if avatarID not in self.avatarsWhoAreEntering:
            self.avatarsWhoAreEntering[avatarID] = 1
            self.sendUpdate('avatarEnter', [avatarID])
        self.openDoor(self.fsm)

    def openDoor(self, doorFsm):
        stateName = doorFsm.getCurrentState().getName()
        if stateName == 'open':
            doorFsm.request('open')
        else:
            if stateName != 'opening':
                doorFsm.request('opening')

    def requestExit(self):
        avatarID = self.air.getAvatarIdFromSender()
        self.sendUpdate('avatarExit', [avatarID])
        self.enqueueAvatarIdExit(avatarID)

    def enqueueAvatarIdExit(self, avatarID):
        if avatarID in self.avatarsWhoAreEntering:
            del self.avatarsWhoAreEntering[avatarID]
        else:
            if avatarID not in self.avatarsWhoAreExiting:
                self.avatarsWhoAreExiting[avatarID] = 1
                self.openDoor(self.exitDoorFSM)

    def requestSuitEnter(self, avatarID):
        self.enqueueAvatarIdEnter(avatarID)

    def requestSuitExit(self, avatarID):
        self.sendUpdate('avatarExit', [avatarID])
        self.enqueueAvatarIdExit(avatarID)

    def d_setState(self, state):
        self.sendUpdate('setState', [state, globalClockDelta.getRealNetworkTime()])

    def d_setExitDoorState(self, state):
        self.sendUpdate('setExitDoorState', [state, globalClockDelta.getRealNetworkTime()])

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def openTask(self, task):
        self.fsm.request('closing')
        return Task.done

    def enterClosing(self):
        self.d_setState('closing')
        self.doLaterTask = taskMgr.doMethodLater(1, self.closingTask, self.uniqueName('door_closing-timer'))

    def exitClosing(self):
        if self.doLaterTask:
            taskMgr.remove(self.doLaterTask)
            self.doLaterTask = None
        return

    def closingTask(self, task):
        self.fsm.request('closed')
        return Task.done

    def enterClosed(self):
        self.d_setState('closed')

    def exitClosed(self):
        pass

    def enterOpening(self):
        self.d_setState('opening')
        self.doLaterTask = taskMgr.doMethodLater(1, self.openingTask, self.uniqueName('door_opening-timer'))

    def exitOpening(self):
        if self.doLaterTask:
            taskMgr.remove(self.doLaterTask)
            self.doLaterTask = None
        return

    def openingTask(self, task):
        self.fsm.request('open')
        return Task.done

    def enterOpen(self):
        self.d_setState('open')
        self.avatarsWhoAreEntering = {}
        self.doLaterTask = taskMgr.doMethodLater(1, self.openTask, self.uniqueName('door_open-timer'))

    def exitOpen(self):
        if self.doLaterTask:
            taskMgr.remove(self.doLaterTask)
            self.doLaterTask = None
        return

    def exitDoorEnterOff(self):
        pass

    def exitDoorExitOff(self):
        pass

    def exitDoorOpenTask(self, task):
        self.exitDoorFSM.request('closing')
        return Task.done

    def exitDoorEnterClosing(self):
        self.d_setExitDoorState('closing')
        self.exitDoorDoLaterTask = taskMgr.doMethodLater(1, self.exitDoorClosingTask, self.uniqueName('exit_door_closing-timer'))

    def exitDoorExitClosing(self):
        if self.exitDoorDoLaterTask:
            taskMgr.remove(self.exitDoorDoLaterTask)
            self.exitDoorDoLaterTask = None
        return

    def exitDoorClosingTask(self, task):
        self.exitDoorFSM.request('closed')
        return Task.done

    def exitDoorEnterClosed(self):
        self.d_setExitDoorState('closed')

    def exitDoorExitClosed(self):
        if self.exitDoorDoLaterTask:
            taskMgr.remove(self.exitDoorDoLaterTask)
            self.exitDoorDoLaterTask = None
        return

    def exitDoorEnterOpening(self):
        self.d_setExitDoorState('opening')
        self.exitDoorDoLaterTask = taskMgr.doMethodLater(1, self.exitDoorOpeningTask, self.uniqueName('exit_door_opening-timer'))

    def exitDoorExitOpening(self):
        if self.exitDoorDoLaterTask:
            taskMgr.remove(self.exitDoorDoLaterTask)
            self.exitDoorDoLaterTask = None
        return

    def exitDoorOpeningTask(self, task):
        self.exitDoorFSM.request('open')
        return Task.done

    def exitDoorEnterOpen(self):
        self.d_setExitDoorState('open')
        self.avatarsWhoAreExiting = {}
        self.exitDoorDoLaterTask = taskMgr.doMethodLater(1, self.exitDoorOpenTask, self.uniqueName('exit_door_open-timer'))

    def exitDoorExitOpen(self):
        if self.exitDoorDoLaterTask:
            taskMgr.remove(self.exitDoorDoLaterTask)
            self.exitDoorDoLaterTask = None
        return
