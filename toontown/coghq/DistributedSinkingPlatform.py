from pandac.PandaModules import *
from direct.distributed.ClockDelta import *
from direct.interval.IntervalGlobal import *
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from otp.level import BasicEntities
from . import MovingPlatform
from direct.distributed import DistributedObject
from . import SinkingPlatformGlobals
from direct.directnotify import DirectNotifyGlobal

class DistributedSinkingPlatform(BasicEntities.DistributedNodePathEntity):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedSinkingPlatform')

    def __init__(self, cr):
        BasicEntities.DistributedNodePathEntity.__init__(self, cr)
        self.moveIval = None
        return

    def generateInit(self):
        self.notify.debug('generateInit')
        BasicEntities.DistributedNodePathEntity.generateInit(self)
        self.fsm = ClassicFSM.ClassicFSM('DistributedSinkingPlatform', [State.State('off', self.enterOff, self.exitOff, ['sinking']), State.State('sinking', self.enterSinking, self.exitSinking, ['rising']), State.State('rising', self.enterRising, self.exitRising, ['sinking', 'off'])], 'off', 'off')
        self.fsm.enterInitialState()

    def generate(self):
        self.notify.debug('generate')
        BasicEntities.DistributedNodePathEntity.generate(self)

    def announceGenerate(self):
        self.notify.debug('announceGenerate')
        BasicEntities.DistributedNodePathEntity.announceGenerate(self)
        self.loadModel()
        self.accept(self.platform.getEnterEvent(), self.localToonEntered)
        self.accept(self.platform.getExitEvent(), self.localToonLeft)

    def disable(self):
        self.notify.debug('disable')
        self.ignoreAll()
        self.fsm.requestFinalState()
        BasicEntities.DistributedNodePathEntity.disable(self)

    def delete(self):
        self.notify.debug('delete')
        self.ignoreAll()
        if self.moveIval:
            self.moveIval.pause()
            del self.moveIval
        self.platform.destroy()
        del self.platform
        BasicEntities.DistributedNodePathEntity.delete(self)

    def loadModel(self):
        self.notify.debug('loadModel')
        model = loader.loadModel('phase_9/models/cogHQ/platform1')
        self.platform = MovingPlatform.MovingPlatform()
        self.platform.setupCopyModel(self.getParentToken(), model, 'platformcollision')
        self.platform.reparentTo(self)
        self.platform.setPos(0, 0, 0)

    def localToonEntered(self):
        ts = globalClockDelta.localToNetworkTime(globalClock.getFrameTime(), bits=32)
        self.sendUpdate('setOnOff', [1, ts])

    def localToonLeft(self):
        ts = globalClockDelta.localToNetworkTime(globalClock.getFrameTime(), bits=32)
        self.sendUpdate('setOnOff', [0, ts])

    def enterOff(self):
        self.notify.debug('enterOff')

    def exitOff(self):
        self.notify.debug('exitOff')

    def enterSinking(self, ts = 0):
        self.notify.debug('enterSinking')
        self.startMoving(SinkingPlatformGlobals.SINKING, ts)

    def exitSinking(self):
        self.notify.debug('exitSinking')
        if self.moveIval:
            self.moveIval.pause()
            del self.moveIval
            self.moveIval = None
        return

    def enterRising(self, ts = 0):
        self.notify.debug('enterRising')
        self.startMoving(SinkingPlatformGlobals.RISING, ts)

    def exitRising(self):
        self.notify.debug('exitRising')
        if self.moveIval:
            self.moveIval.pause()
            del self.moveIval
            self.moveIval = None
        return

    def setSinkMode(self, avId, mode, ts):
        self.notify.debug('setSinkMode %s' % mode)
        if mode == SinkingPlatformGlobals.OFF:
            self.fsm.requestInitialState()
        elif mode == SinkingPlatformGlobals.RISING:
            self.fsm.request('rising', [ts])
        elif mode == SinkingPlatformGlobals.SINKING:
            self.fsm.request('sinking', [ts])

    def startMoving(self, direction, ts):
        if direction == SinkingPlatformGlobals.RISING:
            endPos = Vec3(0, 0, 0)
            pause = self.pauseBeforeRise
            duration = self.riseDuration
        else:
            endPos = Vec3(0, 0, -self.verticalRange)
            pause = None
            duration = self.sinkDuration
        startT = globalClockDelta.networkToLocalTime(ts, bits=32)
        curT = globalClock.getFrameTime()
        ivalTime = curT - startT
        if ivalTime < 0:
            ivalTime = 0
        elif ivalTime > duration:
            ivalTime = duration
        duration = duration - ivalTime
        duration = max(0.0, duration)
        moveNode = self.platform
        self.moveIval = Sequence()
        if pause is not None:
            self.moveIval.append(WaitInterval(pause))
        self.moveIval.append(LerpPosInterval(moveNode, duration, endPos, startPos=moveNode.getPos(), blendType='easeInOut', name='%s-move' % self.platform.name, fluid=1))
        self.moveIval.start()
        return
