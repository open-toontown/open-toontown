from pandac.PandaModules import *
from direct.distributed.ClockDelta import *
from direct.interval.IntervalGlobal import *
from otp.level import BasicEntities
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State
from direct.fsm import State
import LiftConstants
import MovingPlatform

class DistributedLift(BasicEntities.DistributedNodePathEntity):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedLift')

    def __init__(self, cr):
        BasicEntities.DistributedNodePathEntity.__init__(self, cr)

    def generateInit(self):
        self.notify.debug('generateInit')
        BasicEntities.DistributedNodePathEntity.generateInit(self)
        self.moveSnd = base.loadSfx('phase_9/audio/sfx/CHQ_FACT_elevator_up_down.mp3')
        self.fsm = ClassicFSM.ClassicFSM('DistributedLift', [State.State('off', self.enterOff, self.exitOff, ['moving']), State.State('moving', self.enterMoving, self.exitMoving, ['waiting']), State.State('waiting', self.enterWaiting, self.exitWaiting, ['moving'])], 'off', 'off')
        self.fsm.enterInitialState()

    def generate(self):
        self.notify.debug('generate')
        BasicEntities.DistributedNodePathEntity.generate(self)
        self.platform = self.attachNewNode('platParent')

    def setStateTransition(self, toState, fromState, arrivalTimestamp):
        self.notify.debug('setStateTransition: %s->%s' % (fromState, toState))
        if not self.isGenerated():
            self.initialState = toState
            self.initialFromState = fromState
            self.initialStateTimestamp = arrivalTimestamp
        else:
            self.fsm.request('moving', [toState, fromState, arrivalTimestamp])

    def announceGenerate(self):
        self.notify.debug('announceGenerate')
        BasicEntities.DistributedNodePathEntity.announceGenerate(self)
        self.initPlatform()
        self.state = None
        self.fsm.request('moving', [self.initialState, self.initialFromState, self.initialStateTimestamp])
        del self.initialState
        del self.initialStateTimestamp
        return

    def disable(self):
        self.notify.debug('disable')
        self.ignoreAll()
        self.fsm.requestFinalState()
        BasicEntities.DistributedNodePathEntity.disable(self)

    def delete(self):
        self.notify.debug('delete')
        del self.moveSnd
        del self.fsm
        self.destroyPlatform()
        self.platform.removeNode()
        del self.platform
        BasicEntities.DistributedNodePathEntity.delete(self)

    def initPlatform(self):
        model = loader.loadModel(self.modelPath)
        if model is None:
            return
        model.setScale(self.modelScale)
        if self.floorName is None:
            return
        self.platformModel = MovingPlatform.MovingPlatform()
        self.platformModel.setupCopyModel(self.getParentToken(), model, self.floorName)
        self.accept(self.platformModel.getEnterEvent(), self.localToonEntered)
        self.accept(self.platformModel.getExitEvent(), self.localToonLeft)
        self.startGuard = None
        self.endGuard = None
        zoneNp = self.getZoneNode()
        if len(self.startGuardName):
            self.startGuard = zoneNp.find('**/%s' % self.startGuardName)
        if len(self.endGuardName):
            self.endGuard = zoneNp.find('**/%s' % self.endGuardName)
        side2srch = {'front': '**/wall_front',
         'back': '**/wall_back',
         'left': '**/wall_left',
         'right': '**/wall_right'}
        for side in side2srch.values():
            np = self.platformModel.find(side)
            if not np.isEmpty():
                np.setScale(1.0, 1.0, 2.0)
                np.setZ(-10)
                np.flattenLight()

        self.startBoardColl = NodePathCollection()
        self.endBoardColl = NodePathCollection()
        for side in self.startBoardSides:
            np = self.platformModel.find(side2srch[side])
            if np.isEmpty():
                DistributedLift.warning("couldn't find %s board collision" % side)
            else:
                self.startBoardColl.addPath(np)

        for side in self.endBoardSides:
            np = self.platformModel.find(side2srch[side])
            if np.isEmpty():
                DistributedLift.warning("couldn't find %s board collision" % side)
            else:
                self.endBoardColl.addPath(np)

        self.platformModel.reparentTo(self.platform)
        return

    def destroyPlatform(self):
        if hasattr(self, 'platformModel'):
            self.ignore(self.platformModel.getEnterEvent())
            self.ignore(self.platformModel.getExitEvent())
            self.platformModel.destroy()
            del self.platformModel
            if self.startGuard is not None:
                self.startGuard.unstash()
            if self.endGuard is not None:
                self.endGuard.unstash()
            del self.startGuard
            del self.endGuard
            del self.startBoardColl
            del self.endBoardColl
        return

    def localToonEntered(self):
        self.sendUpdate('setAvatarEnter')

    def localToonLeft(self):
        self.sendUpdate('setAvatarLeave')

    def enterOff(self):
        self.notify.debug('enterOff')

    def exitOff(self):
        pass

    def getPosition(self, state):
        if state is LiftConstants.Down:
            return self.startPos
        else:
            return self.endPos

    def getGuard(self, state):
        if state is LiftConstants.Down:
            return self.startGuard
        else:
            return self.endGuard

    def getBoardColl(self, state):
        if state is LiftConstants.Down:
            return self.startBoardColl
        else:
            return self.endBoardColl

    def enterMoving(self, toState, fromState, arrivalTimestamp):
        self.notify.debug('enterMoving, %s->%s' % (fromState, toState))
        if self.state == toState:
            self.notify.warning('already in state %s' % toState)
        startPos = self.getPosition(fromState)
        endPos = self.getPosition(toState)
        startGuard = self.getGuard(fromState)
        endGuard = self.getGuard(toState)
        startBoardColl = self.getBoardColl(fromState)
        endBoardColl = self.getBoardColl(toState)

        def startMoving(self = self, guard = startGuard, boardColl = startBoardColl):
            if guard is not None and not guard.isEmpty():
                guard.unstash()
            boardColl.unstash()
            self.soundIval = SoundInterval(self.moveSnd, node=self.platform)
            self.soundIval.loop()
            return

        def doneMoving(self = self, guard = endGuard, boardColl = endBoardColl, newState = toState):
            self.state = newState
            if hasattr(self, 'soundIval'):
                self.soundIval.pause()
                del self.soundIval
            if guard is not None and not guard.isEmpty():
                guard.stash()
            boardColl.stash()
            self.fsm.request('waiting')
            return

        self.moveIval = Sequence(Func(startMoving), LerpPosInterval(self.platform, self.duration, endPos, startPos=startPos, blendType='easeInOut', name='lift-%s-move' % self.entId, fluid=1), Func(doneMoving))
        ivalStartT = globalClockDelta.networkToLocalTime(arrivalTimestamp, bits=32) - self.moveIval.getDuration()
        self.moveIval.start(globalClock.getFrameTime() - ivalStartT)

    def exitMoving(self):
        if hasattr(self, 'soundIval'):
            self.soundIval.pause()
            del self.soundIval
        self.moveIval.pause()
        del self.moveIval

    def enterWaiting(self):
        self.notify.debug('enterWaiting')

    def exitWaiting(self):
        pass

    if __dev__:

        def attribChanged(self, *args):
            BasicEntities.DistributedNodePathEntity.attribChanged(self, *args)
            self.destroyPlatform()
            self.initPlatform()
