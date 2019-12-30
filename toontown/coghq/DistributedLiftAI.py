from direct.distributed.ClockDelta import *
from otp.level import DistributedEntityAI
from direct.directnotify import DirectNotifyGlobal
from direct.task import Task
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from . import LiftConstants

class DistributedLiftAI(DistributedEntityAI.DistributedEntityAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedLiftAI')

    def __init__(self, level, entId, initialState=LiftConstants.Down):
        DistributedEntityAI.DistributedEntityAI.__init__(self, level, entId)
        self.name = 'Lift%s:%s' % (self.levelDoId, self.entId)
        self.startMoveTaskName = '%s-StartMove' % self.name
        self.moveDoneTaskName = '%s-MoveDone' % self.name
        self.state = initialState
        self.fromState = initialState
        self.stateTimestamp = globalClock.getFrameTime()
        self.boardedAvs = []

    def generate(self):
        self.notify.debug('generate')
        DistributedEntityAI.DistributedEntityAI.generate(self)
        self.fsm = ClassicFSM.ClassicFSM('DistributedLiftAI', [
         State.State('off', self.enterOff, self.exitOff, [
          'waiting']),
         State.State('waiting', self.enterWaiting, self.exitWaiting, [
          'moving', 'waiting']),
         State.State('moving', self.enterMoving, self.exitMoving, [
          'waiting'])], 'off', 'off')
        self.fsm.enterInitialState()
        self.fsm.request('waiting')

    def delete(self):
        self.notify.debug('delete')
        DistributedEntityAI.DistributedEntityAI.delete(self)
        self.ignoreAll()
        taskMgr.remove(self.startMoveTaskName)
        taskMgr.remove(self.moveDoneTaskName)
        del self.fsm

    def b_setStateTransition(self, toState, fromState, arrivalTimestamp):
        self.d_setStateTransition(toState, fromState, arrivalTimestamp)
        self.setStateTransition(toState, fromState, arrivalTimestamp)

    def d_setStateTransition(self, toState, fromState, arrivalTimestamp):
        self.sendUpdate('setStateTransition', [
         toState, fromState, arrivalTimestamp])

    def setStateTransition(self, toState, fromState, arrivalTimestamp):
        self.state = toState
        self.fromState = fromState
        self.stateTimestamp = arrivalTimestamp

    def getStateTransition(self):
        return (
         self.state, self.fromState, self.stateTimestamp)

    def setAvatarEnter(self):
        avId = self.air.getAvatarIdFromSender()
        avatar = self.air.doId2do.get(avId)
        if not avatar:
            self.air.writeServerEvent('suspicious', avId, 'LiftAI.setAvatarEnter avId not valid')
            return
        self.notify.debug('setAvatarEnter: %s' % avId)
        if avId in self.boardedAvs:
            self.notify.warning('avatar %s already in list' % avId)
        else:
            self.boardedAvs.append(avId)

            def handleExitedAvatar(self=self, avId=avId):
                self.notify.debug('avatar %s exited' % avId)
                self.avatarLeft(avId)

            self.acceptOnce(self.air.getAvatarExitEvent(avId), handleExitedAvatar)
            self.setMoveLater(self.moveDelay)

    def setAvatarLeave(self):
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug('setAvatarLeave: %s' % avId)
        self.avatarLeft(avId)

    def avatarLeft(self, avId):
        if avId in self.boardedAvs:
            self.boardedAvs.remove(avId)
            self.ignore(self.air.getAvatarExitEvent(avId))
            if len(self.boardedAvs) == 0:
                if self.fsm.getCurrentState().getName() == 'waiting':
                    self.fsm.request('waiting')
        else:
            self.notify.warning('avatar %s tried to leave, but is not in list' % avId)

    def setMoveLater(self, delay):

        def startMoving(task, self=self):
            targetState = LiftConstants.oppositeState(self.state)
            self.fsm.request('moving', [targetState])
            return Task.done

        self.cancelMoveLater()
        taskMgr.doMethodLater(delay, startMoving, self.startMoveTaskName)

    def cancelMoveLater(self):
        taskMgr.remove(self.startMoveTaskName)

    def enterOff(self):
        self.notify.debug('enterOff')

    def exitOff(self):
        pass

    def enterWaiting(self):
        self.notify.debug('enterWaiting')
        self.setMoveLater(self.autoMoveDelay)

    def exitWaiting(self):
        self.cancelMoveLater()

    def enterMoving(self, targetState):
        self.notify.debug('enterMoving, target=%s' % targetState)
        if self.state == targetState:
            self.notify.warning('already in state %s' % targetState)
            return
        arriveDelay = 1.0 + self.duration
        self.b_setStateTransition(targetState, self.state, globalClockDelta.localToNetworkTime(globalClock.getFrameTime() + arriveDelay, bits=32))

        def doneMoving(task, self=self):
            self.fsm.request('waiting')
            return Task.done

        taskMgr.doMethodLater(arriveDelay, doneMoving, self.moveDoneTaskName)

    def exitMoving(self):
        pass
