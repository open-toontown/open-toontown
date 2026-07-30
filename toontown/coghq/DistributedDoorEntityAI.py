from direct.distributed.ClockDelta import *
from direct.directnotify import DirectNotifyGlobal
from direct.showbase import DirectObject
from . import DistributedDoorEntityBase
from direct.distributed import DistributedObjectAI
from otp.level import DistributedEntityAI
from direct.fsm import FourStateAI
from direct.fsm import ClassicFSM
from direct.fsm import State
from direct.task import Task

class Lock(DistributedDoorEntityBase.LockBase, DirectObject.DirectObject, FourStateAI.FourStateAI):

    def __init__(self, door, lockIndex, event, isUnlocked):
        self.door = door
        self.lockIndex = lockIndex
        FourStateAI.FourStateAI.__init__(self, self.stateNames, durations=self.stateDurations)
        self.unlockEvent = None
        self.setUnlockEvent(event)
        self.setIsUnlocked(isUnlocked)
        return

    def getLockState(self):
        return self.stateIndex

    def setup(self):
        pass

    def takedown(self):
        self.ignoreAll()
        FourStateAI.FourStateAI.delete(self)
        del self.door

    def setUnlockEvent(self, event):
        if self.unlockEvent:
            self.ignore(self.unlockEvent)
        self.unlockEvent = self.door.getOutputEventName(event)
        if self.unlockEvent:
            self.accept(self.unlockEvent, self.setIsUnlocked)

    def distributeStateChange(self):
        self.door.sendLocksState()

    def setIsUnlocked(self, isUnlocked):
        self.setIsOn(isUnlocked)
        if not isUnlocked:
            self.door.locking()

    def setLockState(self, stateIndex):
        if self.stateIndex != stateIndex:
            self.fsm.request(self.states[stateIndex])

    def isUnlocked(self):
        return self.isOn()


class DistributedDoorEntityAI(DistributedDoorEntityBase.DistributedDoorEntityBase, DistributedEntityAI.DistributedEntityAI, FourStateAI.FourStateAI):

    def __init__(self, level, entId, zoneId=None):
        self.entId = entId
        self._isGenerated = 0
        self.isOpenInput = None
        DistributedEntityAI.DistributedEntityAI.__init__(self, level, entId)
        self.stateDurations[2] = self.secondsOpen
        FourStateAI.FourStateAI.__init__(self, self.stateNames, durations=self.stateDurations)
        self.setup()
        if zoneId is not None:
            self.generateWithRequired(zoneId)
        return

    def generateWithRequired(self, zoneId):
        DistributedEntityAI.DistributedEntityAI.generateWithRequired(self, zoneId)
        self._isGenerated = 1

    def delete(self):
        self.takedown()
        FourStateAI.FourStateAI.delete(self)
        DistributedEntityAI.DistributedEntityAI.delete(self)

    def getLocksState(self):
        stateBits = 0
        if hasattr(self, 'locks'):
            stateBits = self.locks[0].getLockState() & 15 | self.locks[1].getLockState() << 4 & 240 | self.locks[2].getLockState() << 8 & 3840
        return stateBits

    def sendLocksState(self):
        if self._isGenerated:
            self.sendUpdate('setLocksState', [self.getLocksState()])

    def getDoorState(self):
        r = (
         self.stateIndex, globalClockDelta.getRealNetworkTime())
        return r

    def getName(self):
        return 'door-%s' % (self.entId,)

    def setup(self):
        if not hasattr(self, 'unlock0Event'):
            self.unlock0Event = None
        if not hasattr(self, 'unlock1Event'):
            self.unlock1Event = None
        if not hasattr(self, 'unlock2Event'):
            self.unlock2Event = None
        if not hasattr(self, 'unlock3Event'):
            self.unlock3Event = None
        if not hasattr(self, 'isLock0Unlocked'):
            self.isLock0Unlocked = None
        if not hasattr(self, 'isLock1Unlocked'):
            self.isLock1Unlocked = None
        if not hasattr(self, 'isLock2Unlocked'):
            self.isLock2Unlocked = None
        if not hasattr(self, 'isLock3Unlocked'):
            self.isLock3Unlocked = None
        self.locks = [Lock(self, 0, self.unlock0Event, self.isLock0Unlocked), Lock(self, 1, self.unlock1Event, self.isLock1Unlocked), Lock(self, 2, self.unlock2Event, self.isLock2Unlocked)]
        del self.unlock0Event
        del self.unlock1Event
        del self.unlock2Event
        del self.unlock3Event
        del self.isLock0Unlocked
        del self.isLock1Unlocked
        del self.isLock2Unlocked
        del self.isLock3Unlocked
        if hasattr(self, 'isOpenEvent'):
            self.setIsOpenEvent(self.isOpenEvent)
            del self.isOpenEvent
        if hasattr(self, 'isOpen'):
            self.setIsOpen(self.isOpen)
            del self.isOpen
        return

    def takedown(self):
        self.ignoreAll()
        for i in self.locks:
            i.takedown()

        del self.locks

    setScale = DistributedDoorEntityBase.stubFunction
    setColor = DistributedDoorEntityBase.stubFunction
    setModel = DistributedDoorEntityBase.stubFunction

    def setIsOpenEvent(self, event):
        if self.isOpenEvent:
            self.ignore(self.isOpenEvent)
        self.isOpenEvent = self.getOutputEventName(event)
        if self.isOpenEvent:
            self.accept(self.isOpenEvent, self.setIsOpen)

    def changedOnState(self, isOn):
        if hasattr(self, 'entId'):
            messenger.send(self.getOutputEventName(), [not isOn])

    def setIsOpen(self, isOpen):
        self.setIsOn(not isOpen)

    def getIsOpen(self):
        return not self.getIsOn()

    def setSecondsOpen(self, secondsOpen):
        if self.secondsOpen != secondsOpen:
            self.secondsOpen = secondsOpen
            if secondsOpen < 0.0:
                secondsOpen = None
            self.stateDurations[2] = secondsOpen
        return

    def locking(self):
        if self.stateIndex == 1 or self.stateIndex == 2:
            self.fsm.request(self.states[3])

    def setUnlock0Event(self, event):
        self.locks[0].setUnlockEvent(event)

    def setUnlock1Event(self, event):
        self.locks[1].setUnlockEvent(event)

    def setUnlock2Event(self, event):
        self.locks[2].setUnlockEvent(event)

    def setUnlock3Event(self, event):
        pass

    def setIsLock0Unlocked(self, unlocked):
        self.locks[0].setIsUnlocked(unlocked)

    def setIsLock1Unlocked(self, unlocked):
        self.locks[1].setIsUnlocked(unlocked)

    def setIsLock2Unlocked(self, unlocked):
        self.locks[2].setIsUnlocked(unlocked)

    def setIsLock3Unlocked(self, unlocked):
        pass

    def isUnlocked(self):
        isUnlocked = self.locks[0].isUnlocked() and self.locks[1].isUnlocked() and self.locks[2].isUnlocked()
        return isUnlocked

    def distributeStateChange(self):
        if self._isGenerated:
            self.sendUpdate('setDoorState', self.getDoorState())

    def requestOpen(self):
        if self.isUnlocked():
            if self.fsm.getCurrentState() is not self.states[2]:
                self.fsm.request(self.states[1])

    if __dev__:

        def attribChanged(self, attrib, value):
            self.takedown()
            self.setup()
