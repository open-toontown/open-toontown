from pandac.PandaModules import *
from toontown.toonbase.ToonBaseGlobal import *
from direct.interval.IntervalGlobal import *
from toontown.toonbase.ToontownGlobals import *
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import StateData
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from direct.task.Task import Task

class CogThiefGameToonSD(StateData.StateData):
    notify = DirectNotifyGlobal.directNotify.newCategory('CogThiefGameToonSD')
    FallBackAnim = 'slip-backward'
    FallFwdAnim = 'slip-forward'
    NeutralAnim = 'neutral'
    RunAnim = 'run'
    ThrowNeutralAnim = 'throw'
    ThrowRunAnim = 'throw'
    animList = [FallBackAnim,
     FallFwdAnim,
     NeutralAnim,
     RunAnim,
     ThrowNeutralAnim,
     ThrowRunAnim]

    def __init__(self, avId, game):
        self.avId = avId
        self.game = game
        self.isLocal = avId == base.localAvatar.doId
        self.toon = self.game.getAvatar(self.avId)
        self.unexpectedExit = False
        self.fsm = ClassicFSM.ClassicFSM('CogThiefGameAnimFSM-%s' % self.avId, [State.State('init', self.enterInit, self.exitInit, ['normal']),
         State.State('normal', self.enterNormal, self.exitNormal, ['throwPie', 'fallBack', 'fallForward']),
         State.State('throwPie', self.enterThrowPie, self.exitThrowPie, ['normal',
          'fallBack',
          'fallForward',
          'throwPie']),
         State.State('fallBack', self.enterFallBack, self.exitFallBack, ['normal']),
         State.State('fallForward', self.enterFallForward, self.exitFallForward, ['normal']),
         State.State('cleanup', self.enterCleanup, self.exitCleanup, [])], 'init', 'cleanup')
        self.exitAlreadyCalled = False

    def load(self):
        self.setAnimState('off', 1.0)
        for anim in self.animList:
            self.toon.pose(anim, 0)

    def unload(self):
        del self.fsm

    def enter(self):
        self.fsm.enterInitialState()

    def exit(self, unexpectedExit = False):
        if self.exitAlreadyCalled:
            return
        self.exitAlreadyCalled = True
        self.notify.debug('in exit self.toon.doId=%s' % self.toon.doId)
        self.unexpectedExit = unexpectedExit
        self.fsm.requestFinalState()

    def enterInit(self):
        self.notify.debug('enterInit')
        self.toon.startBlink()
        self.toon.stopLookAround()
        if self.isLocal:
            self.game.initGameWalk()
        self.toon.useLOD(1000)
        self.dropShadow = self.toon.dropShadow
        self.origDropShadowColor = self.dropShadow.getColor()
        c = self.origDropShadowColor
        alpha = 0.35
        self.dropShadow.setColor(c[0], c[1], c[2], alpha)

    def exitInit(self):
        pass

    def setAnimState(self, newState, playRate):
        if not self.unexpectedExit:
            self.toon.setAnimState(newState, playRate)

    def enterNormal(self):
        self.notify.debug('enterNormal')
        self.setAnimState('CogThiefRunning', 1.0)
        if self.isLocal:
            self.game.startGameWalk()
        self.toon.lerpLookAt(Vec3.forward() + Vec3.up(), time=0.2, blink=0)

    def exitNormal(self):
        self.notify.debug('exitNormal')
        self.setAnimState('off', 1.0)
        if self.isLocal:
            self.game.stopGameWalk()
        self.toon.lerpLookAt(Vec3.forward(), time=0.2, blink=0)

    def throwPie(self, pieModel, handNode):
        if self.fsm.getCurrentState().getName() == 'throwPie':
            self.fsm.request('normal')
        self.fsm.request('throwPie', [pieModel, handNode])

    def enterThrowPie(self, pieModel, handNode):
        self.notify.debug('enterThrowPie')
        self.setAnimState('CatchEating', 1.0)
        if self.isLocal:
            self.game.startGameWalk()
        self.pieModel = pieModel
        renderScale = pieModel.getScale(render)
        pieModel.reparentTo(handNode)
        pieModel.setScale(render, renderScale)

        def finishedEating(self = self, pieModel = pieModel):
            self.fsm.request('normal')
            return Task.done

        duration = self.toon.getDuration('catch-eatneutral')
        self.eatIval = Sequence(Parallel(WaitInterval(duration), Sequence(LerpScaleInterval(pieModel, duration / 2.0, pieModel.getScale() * 0.5, blendType='easeInOut'), Func(pieModel.hide))), Func(finishedEating), name=self.toon.uniqueName('eatingIval'))
        self.eatIval.start()

    def exitThrowPie(self):
        self.eatIval.pause()
        del self.eatIval
        self.pieModel.reparentTo(hidden)
        self.pieModel.removeNode()
        del self.pieModel
        self.setAnimState('off', 1.0)
        if self.isLocal:
            self.game.stopGameWalk()

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
        self.notify.debug('enterCleanup %s' % self.toon.doId)
        if self.toon and not self.toon.isEmpty():
            self.toon.stopBlink()
            self.toon.startLookAround()
            if self.isLocal:
                self.game.stopGameWalk()
                self.game.destroyGameWalk()
            self.toon.resetLOD()
            self.dropShadow.setColor(self.origDropShadowColor)

    def exitCleanup(self):
        pass
