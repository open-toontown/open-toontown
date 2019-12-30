from pandac.PandaModules import *
from toontown.toonbase.ToonBaseGlobal import *
from direct.interval.IntervalGlobal import *
from toontown.toonbase.ToontownGlobals import *
from toontown.distributed.DelayDelete import DelayDelete
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import StateData
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from . import CatchGameGlobals
from direct.task.Task import Task

class CatchGameToonSD(StateData.StateData):
    notify = DirectNotifyGlobal.directNotify.newCategory('CatchGameToonSD')
    FallBackAnim = 'slip-backward'
    FallFwdAnim = 'slip-forward'
    CatchNeutralAnim = 'catch-neutral'
    CatchRunAnim = 'catch-run'
    EatNeutralAnim = 'catch-eatneutral'
    EatNRunAnim = 'catch-eatnrun'
    animList = [FallBackAnim,
     FallFwdAnim,
     CatchNeutralAnim,
     CatchRunAnim,
     EatNeutralAnim,
     EatNRunAnim]

    def __init__(self, avId, game):
        self.avId = avId
        self.game = game
        self.isLocal = avId == base.localAvatar.doId
        self.toon = self.game.getAvatar(self.avId)
        self._delayDelete = DelayDelete(self.toon, 'CatchGameToonSD')
        self.unexpectedExit = False
        self.fsm = ClassicFSM.ClassicFSM('CatchGameAnimFSM-%s' % self.avId, [State.State('init', self.enterInit, self.exitInit, ['normal']),
         State.State('normal', self.enterNormal, self.exitNormal, ['eatFruit', 'fallBack', 'fallForward']),
         State.State('eatFruit', self.enterEatFruit, self.exitEatFruit, ['normal',
          'fallBack',
          'fallForward',
          'eatFruit']),
         State.State('fallBack', self.enterFallBack, self.exitFallBack, ['normal']),
         State.State('fallForward', self.enterFallForward, self.exitFallForward, ['normal']),
         State.State('cleanup', self.enterCleanup, self.exitCleanup, [])], 'init', 'cleanup')

    def load(self):
        self.setAnimState('off', 1.0)
        for anim in self.animList:
            self.toon.pose(anim, 0)

    def unload(self):
        self._delayDelete.destroy()
        del self.fsm

    def enter(self):
        self.fsm.enterInitialState()
        self._exiting = False

    def exit(self, unexpectedExit = False):
        if self._exiting:
            return
        self._exiting = True
        self.unexpectedExit = unexpectedExit
        self.fsm.requestFinalState()
        del self._exiting

    def enterInit(self):
        self.notify.debug('enterInit')
        self.toon.startBlink()
        self.toon.stopLookAround()
        if self.isLocal:
            self.game.initOrthoWalk()
        self.toon.useLOD(1000)
        self.dropShadow = self.toon.dropShadow
        self.origDropShadowColor = self.dropShadow.getColor()
        c = self.origDropShadowColor
        alpha = 0.35
        self.dropShadow.setColor(c[0], c[1], c[2], alpha)

    def exitInit(self):
        pass

    def enterNormal(self):
        self.notify.debug('enterNormal')
        self.setAnimState('Catching', 1.0)
        if self.isLocal:
            self.game.orthoWalk.start()
        self.toon.lerpLookAt(Vec3.forward() + Vec3.up(), time=0.2, blink=0)

    def exitNormal(self):
        self.setAnimState('off', 1.0)
        if self.isLocal:
            self.game.orthoWalk.stop()
        self.toon.lerpLookAt(Vec3.forward(), time=0.2, blink=0)

    def eatFruit(self, fruitModel, handNode):
        if self.fsm.getCurrentState().getName() == 'eatFruit':
            self.fsm.request('normal')
        self.fsm.request('eatFruit', [fruitModel, handNode])

    def enterEatFruit(self, fruitModel, handNode):
        self.notify.debug('enterEatFruit')
        self.setAnimState('CatchEating', 1.0)
        if self.isLocal:
            self.game.orthoWalk.start()
        self.fruitModel = fruitModel
        renderScale = fruitModel.getScale(render)
        fruitModel.reparentTo(handNode)
        fruitModel.setScale(render, renderScale)

        def finishedEating(self = self, fruitModel = fruitModel):
            self.fsm.request('normal')
            return Task.done

        duration = self.toon.getDuration('catch-eatneutral')
        self.eatIval = Sequence(Parallel(WaitInterval(duration), Sequence(LerpScaleInterval(fruitModel, duration / 2.0, fruitModel.getScale() * 0.5, blendType='easeInOut'), Func(fruitModel.hide))), Func(finishedEating), name=self.toon.uniqueName('eatingIval'))
        self.eatIval.start()

    def exitEatFruit(self):
        self.eatIval.pause()
        del self.eatIval
        self.fruitModel.reparentTo(hidden)
        self.fruitModel.removeNode()
        del self.fruitModel
        self.setAnimState('off', 1.0)
        if self.isLocal:
            self.game.orthoWalk.stop()

    def enterFallBack(self):
        self.notify.debug('enterFallBack')
        if self.isLocal:
            base.playSfx(self.game.sndOof)
        duration = 1.0
        animName = self.FallBackAnim
        startFrame = 12
        totalFrames = self.toon.getNumFrames(animName)
        frames = totalFrames - 1 - startFrame
        frameRate = self.toon.getFrameRate(animName)
        newRate = frames / duration
        playRate = newRate / frameRate

        def resume(self = self):
            self.fsm.request('normal')

        self.fallBackIval = Sequence(ActorInterval(self.toon, animName, startTime=startFrame / newRate, endTime=totalFrames / newRate, playRate=playRate), FunctionInterval(resume))
        self.fallBackIval.start()

    def exitFallBack(self):
        self.fallBackIval.pause()
        del self.fallBackIval

    def enterFallForward(self):
        self.notify.debug('enterFallForward')
        if self.isLocal:
            base.playSfx(self.game.sndOof)
        duration = 1.0
        animName = self.FallFwdAnim
        startFrame = 12
        totalFrames = self.toon.getNumFrames(animName)
        frames = totalFrames - 1 - startFrame
        frameRate = self.toon.getFrameRate(animName)
        newRate = frames / duration
        playRate = newRate / frameRate

        def resume(self = self):
            self.fsm.request('normal')

        self.fallFwdIval = Sequence(ActorInterval(self.toon, animName, startTime=startFrame / newRate, endTime=totalFrames / newRate, playRate=playRate), FunctionInterval(resume))
        self.fallFwdIval.start()

    def exitFallForward(self):
        self.fallFwdIval.pause()
        del self.fallFwdIval

    def enterCleanup(self):
        self.notify.debug('enterCleanup')
        self.toon.stopBlink()
        self.toon.startLookAround()
        if self.isLocal:
            self.game.orthoWalk.stop()
            self.game.destroyOrthoWalk()
        self.toon.resetLOD()
        self.dropShadow.setColor(self.origDropShadowColor)

    def exitCleanup(self):
        pass

    def setAnimState(self, newState, playRate):
        if not self.unexpectedExit:
            self.toon.setAnimState(newState, playRate)
