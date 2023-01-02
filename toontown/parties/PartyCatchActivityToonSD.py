from panda3d.core import Vec3
from direct.interval.IntervalGlobal import Sequence, Parallel, Wait, Func
from direct.interval.IntervalGlobal import LerpScaleInterval
from direct.interval.IntervalGlobal import WaitInterval, ActorInterval, FunctionInterval
from direct.task.Task import Task
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import StateData
from toontown.minigame.OrthoWalk import OrthoWalk
from toontown.minigame.MinigameRulesPanel import MinigameRulesPanel
from toontown.parties import PartyGlobals
from direct.fsm import ClassicFSM, State

class PartyCatchActivityToonSD(StateData.StateData):
    notify = DirectNotifyGlobal.directNotify.newCategory('PartyCatchActivityToonSD')
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

    def __init__(self, avId, activity):
        PartyCatchActivityToonSD.notify.debug('init : avId = %s, activity = %s ' % (avId, activity))
        self.avId = avId
        self.activity = activity
        self.isLocal = avId == base.localAvatar.doId
        self.toon = self.activity.getAvatar(self.avId)
        self.unexpectedExit = False
        self.fsm = ClassicFSM.ClassicFSM('CatchActivityAnimFSM-%s' % self.avId, [State.State('init', self.enterInit, self.exitInit, ['notPlaying', 'normal', 'rules']),
         State.State('notPlaying', self.enterNotPlaying, self.exitNotPlaying, ['normal', 'rules', 'cleanup']),
         State.State('rules', self.enterRules, self.exitRules, ['normal', 'cleanup']),
         State.State('normal', self.enterNormal, self.exitNormal, ['eatFruit',
          'fallBack',
          'fallForward',
          'notPlaying']),
         State.State('eatFruit', self.enterEatFruit, self.exitEatFruit, ['normal',
          'fallBack',
          'fallForward',
          'eatFruit',
          'notPlaying']),
         State.State('fallBack', self.enterFallBack, self.exitFallBack, ['normal', 'notPlaying']),
         State.State('fallForward', self.enterFallForward, self.exitFallForward, ['normal', 'notPlaying']),
         State.State('cleanup', self.enterCleanup, self.exitCleanup, [])], 'init', 'cleanup')
        self.enteredAlready = False

    def load(self):
        self.setAnimState('off', 1.0)
        for anim in self.animList:
            self.toon.pose(anim, 0)

    def unload(self):
        del self.fsm

    def enter(self):
        if not self.enteredAlready:
            self.enteredAlready = True
            self.fsm.enterInitialState()
            self._exiting = False

    def exit(self, unexpectedExit = False):
        if self._exiting:
            return
        self._exiting = True
        self.unexpectedExit = unexpectedExit
        if not self.unexpectedExit:
            self.fsm.requestFinalState()
        del self._exiting

    def enterInit(self):
        self.notify.debug('enterInit')
        self.toon.startBlink()
        self.toon.stopLookAround()
        if self.isLocal:
            self.activity.initOrthoWalk()
        self.dropShadow = self.toon.dropShadow
        self.origDropShadowColor = self.dropShadow.getColor()
        c = self.origDropShadowColor
        alpha = 0.35
        self.dropShadow.setColor(c[0], c[1], c[2], alpha)

    def exitInit(self):
        pass

    def enterNotPlaying(self):
        self.toon.stopBlink()
        self.toon.startLookAround()
        self.setAnimState('neutral', 1.0)
        if self.isLocal:
            self.activity.orthoWalk.stop()
        self.dropShadow.setColor(self.origDropShadowColor)

    def exitNotPlaying(self):
        self.dropShadow = self.toon.dropShadow
        self.origDropShadowColor = self.dropShadow.getColor()
        c = self.origDropShadowColor
        alpha = 0.35
        self.dropShadow.setColor(c[0], c[1], c[2], alpha)

    def enterRules(self):
        if self.isLocal:
            self.notify.debug('enterNormal')
            self.setAnimState('Catching', 1.0)
            self.activity.orthoWalk.stop()
            self.accept(self.activity.rulesDoneEvent, self.handleRulesDone)
            self.rulesPanel = MinigameRulesPanel('PartyRulesPanel', self.activity.getTitle(), self.activity.getInstructions(), self.activity.rulesDoneEvent, PartyGlobals.DefaultRulesTimeout)
            base.setCellsAvailable(base.bottomCells + [base.leftCells[0], base.rightCells[1]], False)
            self.rulesPanel.load()
            self.rulesPanel.enter()
        else:
            self.fsm.request('normal')

    def handleRulesDone(self):
        self.fsm.request('normal')

    def exitRules(self):
        self.setAnimState('off', 1.0)
        self.ignore(self.activity.rulesDoneEvent)
        if hasattr(self, 'rulesPanel'):
            self.rulesPanel.exit()
            self.rulesPanel.unload()
            del self.rulesPanel
            base.setCellsAvailable(base.bottomCells + [base.leftCells[0], base.rightCells[1]], True)

    def enterNormal(self):
        self.notify.debug('enterNormal')
        self.setAnimState('Catching', 1.0)
        if self.isLocal:
            self.activity.orthoWalk.start()
        self.toon.lerpLookAt(Vec3.forward() + Vec3.up(), time=0.2, blink=0)

    def exitNormal(self):
        self.setAnimState('off', 1.0)
        if self.isLocal:
            self.activity.orthoWalk.stop()
        self.toon.lerpLookAt(Vec3.forward(), time=0.2, blink=0)

    def eatFruit(self, fruitModel, handNode):
        if self.fsm.getCurrentState().getName() == 'eatFruit':
            self.fsm.request('normal')
        self.fsm.request('eatFruit', [fruitModel, handNode])

    def enterEatFruit(self, fruitModel, handNode):
        self.notify.debug('enterEatFruit')
        self.setAnimState('CatchEating', 1.0)
        if self.isLocal:
            self.activity.orthoWalk.start()
        self.fruitModel = fruitModel
        renderScale = fruitModel.getScale(render)
        fruitModel.reparentTo(handNode)
        fruitModel.setScale(render, renderScale)
        duration = self.toon.getDuration('catch-eatneutral')
        self.eatIval = Sequence(Parallel(WaitInterval(duration), Sequence(LerpScaleInterval(fruitModel, duration / 2.0, fruitModel.getScale() * 0.5, blendType='easeInOut'), Func(fruitModel.hide))), Func(self.fsm.request, 'normal'), name=self.toon.uniqueName('eatingIval'))
        self.eatIval.start()

    def exitEatFruit(self):
        self.eatIval.pause()
        del self.eatIval
        self.fruitModel.reparentTo(hidden)
        self.fruitModel.removeNode()
        del self.fruitModel
        self.setAnimState('off', 1.0)
        if self.isLocal:
            self.activity.orthoWalk.stop()

    def enterFallBack(self):
        self.notify.debug('enterFallBack')
        if self.isLocal:
            base.playSfx(self.activity.sndOof)
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
            base.playSfx(self.activity.sndOof)
        duration = 2.0
        animName = self.FallFwdAnim
        startFrame = 12
        totalFrames = self.toon.getNumFrames(animName)
        frames = totalFrames - 1 - startFrame
        pauseFrame = 19
        frameRate = self.toon.getFrameRate(animName)
        newRate = frames / (duration * 0.5)
        playRate = newRate / frameRate

        def resume(self = self):
            self.fsm.request('normal')

        self.fallFwdIval = Sequence(ActorInterval(self.toon, animName, startTime=startFrame / newRate, endTime=pauseFrame / newRate, playRate=playRate), WaitInterval(duration / 2.0), ActorInterval(self.toon, animName, startTime=pauseFrame / newRate, endTime=totalFrames / newRate, playRate=playRate), FunctionInterval(resume))
        self.fallFwdIval.start()

    def exitFallForward(self):
        self.fallFwdIval.pause()
        del self.fallFwdIval

    def enterCleanup(self):
        self.notify.debug('enterCleanup')
        self.toon.stopBlink()
        self.toon.startLookAround()
        if self.isLocal:
            self.activity.orthoWalk.stop()
            self.activity.destroyOrthoWalk()
        self.dropShadow.setColor(self.origDropShadowColor)

    def exitCleanup(self):
        pass

    def setAnimState(self, newState, playRate):
        if not self.unexpectedExit:
            self.toon.setAnimState(newState, playRate)
        else:
            self.notify.debug('setAnimState(): Toon unexpectedExit flag is set.')
