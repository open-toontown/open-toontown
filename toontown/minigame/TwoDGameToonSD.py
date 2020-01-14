from pandac.PandaModules import *
from toontown.toonbase.ToonBaseGlobal import *
from direct.interval.IntervalGlobal import *
from toontown.toonbase.ToontownGlobals import *
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import StateData
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from . import ToonBlitzGlobals
from otp.otpbase import OTPGlobals
from direct.task.Task import Task
from toontown.minigame import TwoDBattleMgr
from toontown.racing import RaceHeadFrame
COLOR_RED = VBase4(1, 0, 0, 0.3)

class TwoDGameToonSD(StateData.StateData):
    notify = DirectNotifyGlobal.directNotify.newCategory('TwoDGameToonSD')
    FallBackAnim = 'slip-backward'
    NeutralAnim = 'neutral'
    RunAnim = 'run'
    ShootGun = 'water-gun'
    Victory = 'victory'
    animList = [FallBackAnim,
     NeutralAnim,
     RunAnim,
     ShootGun,
     Victory]
    ScoreTextGenerator = TextNode('ScoreTextGenerator')

    def __init__(self, avId, game):
        self.avId = avId
        self.game = game
        self.isLocal = avId == base.localAvatar.doId
        self.toon = self.game.getAvatar(self.avId)
        self.unexpectedExit = False
        self.fallBackIval = None
        self.fallDownIval = None
        self.victoryIval = None
        self.squishIval = None
        self.fsm = ClassicFSM.ClassicFSM('TwoDGameAnimFSM-%s' % self.avId, [State.State('init', self.enterInit, self.exitInit, ['normal']),
         State.State('normal', self.enterNormal, self.exitNormal, ['shootGun',
          'fallBack',
          'fallDown',
          'victory',
          'squish']),
         State.State('shootGun', self.enterShootGun, self.exitShootGun, ['normal',
          'fallBack',
          'fallDown',
          'victory',
          'squish']),
         State.State('fallBack', self.enterFallBack, self.exitFallBack, ['normal', 'fallDown', 'squish']),
         State.State('fallDown', self.enterFallDown, self.exitFallDown, ['normal']),
         State.State('squish', self.enterSquish, self.exitSquish, ['normal']),
         State.State('victory', self.enterVictory, self.exitVictory, ['normal', 'fallDown']),
         State.State('cleanup', self.enterCleanup, self.exitCleanup, [])], 'init', 'cleanup')
        self.scoreText = None
        self.load()
        self.progressLineLength = self.game.assetMgr.faceEndPos[0] - self.game.assetMgr.faceStartPos[0]
        self.conversionRatio = self.progressLineLength / self.game.gameLength
        self.scoreTextSeq = None
        return

    def load(self):
        for anim in self.animList:
            self.toon.pose(anim, 0)

        self.battleMgr = TwoDBattleMgr.TwoDBattleMgr(self.game, self.toon)
        self.squishSound = base.loader.loadSfx('phase_3.5/audio/dial/AV_' + self.toon.style.getAnimal() + '_exclaim.ogg')

    def destroy(self):
        if self.fallBackIval != None:
            self.fallBackIval.finish()
            self.fallBackIval = None
        if self.fallDownIval != None:
            self.fallDownIval.finish()
            self.fallDownIval = None
        if self.squishIval != None:
            self.squishIval.finish()
            self.squishIval = None
        if self.victoryIval != None:
            self.victoryIval.finish()
            self.victoryIval = None
        self.hideScoreText()
        self.headFrame.destroy()
        self.battleMgr.destroy()
        del self.battleMgr
        del self.fsm
        return

    def enter(self):
        self.fsm.enterInitialState()

    def exit(self, unexpectedExit = False):
        self.unexpectedExit = unexpectedExit
        self.fsm.requestFinalState()

    def enterInit(self):
        self.notify.debug('enterInit')
        self.toon.startBlink()
        self.toon.stopLookAround()
        self.toon.useLOD(1000)
        self.toon.dropShadow.hide()

    def exitInit(self):
        pass

    def enterNormal(self):
        self.notify.debug('enterNormal')

    def exitNormal(self):
        pass

    def enterFallBack(self):
        self.notify.debug('enterFallBack')
        fallBackDist = 9
        self.blinkRed = self.blinkColor(COLOR_RED, 2)
        duration = 4
        animName = self.FallBackAnim
        startFrame = 1
        endFrame = 22
        totalFrames = self.toon.getNumFrames(animName)
        frames = totalFrames - 1 - startFrame
        frameRate = self.toon.getFrameRate(animName)
        newRate = frames / duration
        playRate = newRate / frameRate
        fallBackAnim = Sequence(ActorInterval(self.toon, animName, startTime=startFrame / newRate, endTime=endFrame / newRate, playRate=playRate), ActorInterval(self.toon, animName, startFrame=23, playRate=1), FunctionInterval(self.resume))
        self.fallBackIval = Parallel(self.blinkRed, fallBackAnim)
        if self.isLocal:
            self.game.ignoreInputs()
            self.toon.controlManager.currentControls.lifter.setVelocity(12)
            if self.toon.getH() == 90:
                endPoint = Point3(self.toon.getX() + fallBackDist, self.toon.getY(), self.toon.getZ())
            else:
                endPoint = Point3(self.toon.getX() - fallBackDist, self.toon.getY(), self.toon.getZ())
            enemyHitTrajectory = LerpFunc(self.toon.setX, fromData=self.toon.getX(), toData=endPoint.getX(), duration=0.75, name='enemyHitTrajectory')
            self.fallBackIval.append(enemyHitTrajectory)
            base.playSfx(self.game.assetMgr.sndOof)
        self.fallBackIval.start()

    def exitFallBack(self):
        self.fallBackIval.pause()
        self.blinkRed.finish()
        if self.isLocal:
            if self.game.gameFSM.getCurrentState().getName() == 'play':
                self.game.acceptInputs()

    def shootGun(self):
        if self.fsm.getCurrentState().getName() == 'shootGun':
            self.fsm.request('normal')
        self.fsm.request('shootGun')

    def enterShootGun(self):
        self.battleMgr.shoot()
        self.fsm.request('normal')

    def exitShootGun(self):
        pass

    def enterFallDown(self):
        self.notify.debug('enterFallDown')
        self.fallDownIval = Sequence()
        self.blinkRed = self.blinkColor(COLOR_RED, 2)
        if self.isLocal:
            self.game.ignoreInputs()
            base.playSfx(self.game.assetMgr.fallSound)
            pos = self.game.sectionMgr.getLastSpawnPoint()
            toonRespawnIval = Sequence(Wait(1), Func(base.localAvatar.setPos, pos))
            self.fallDownIval.append(toonRespawnIval)
        self.fallDownIval.append(Func(self.resume))
        self.fallDownIval.append(self.blinkRed)
        self.fallDownIval.start()

    def exitFallDown(self):
        if self.isLocal:
            if self.game.gameFSM.getCurrentState().getName() == 'play':
                self.game.acceptInputs()

    def enterSquish(self):
        self.notify.debug('enterSquish')
        if self.isLocal:
            self.game.ignoreInputs()
        self.toon.setAnimState('Squish')
        self.toon.stunToon()
        base.playSfx(self.squishSound, node=self.toon, volume=2)
        self.blinkRed = self.blinkColor(COLOR_RED, 3)
        self.squishIval = Parallel(self.blinkRed, Sequence(Wait(2.5), Func(self.resume)))
        self.squishIval.start()

    def exitSquish(self):
        if self.isLocal:
            if self.game.gameFSM.getCurrentState().getName() == 'play':
                self.game.acceptInputs()

    def enterVictory(self):
        self.notify.debug('enterVictory')
        outsideElevatorPos = self.game.sectionMgr.exitElevator.find('**/loc_elevator_front').getPos(render)
        insideElevatorPos = self.game.sectionMgr.exitElevator.find('**/loc_elevator_inside').getPos(render)
        runToElevator = Parallel(LerpPosInterval(self.toon, self.game.timeToRunToElevator, outsideElevatorPos), ActorInterval(self.toon, self.RunAnim, loop=1, duration=self.game.timeToRunToElevator))
        danceIval = Parallel(LerpPosInterval(self.toon, 2, insideElevatorPos), ActorInterval(self.toon, self.Victory, loop=1, duration=ToonBlitzGlobals.GameDuration[self.game.getSafezoneId()]))
        waitToLand = 0.0
        if self.toon.getZ(render) > 13:
            waitToLand = 1
        self.victoryIval = Sequence(Wait(waitToLand), runToElevator, danceIval)
        self.victoryIval.start()

    def exitVictory(self):
        pass

    def enterCleanup(self):
        self.notify.debug('enterCleanup')
        self.toon.stopBlink()
        self.toon.startLookAround()
        self.toon.resetLOD()
        self.toon.dropShadow.show()

    def exitCleanup(self):
        pass

    def resume(self):
        self.fsm.request('normal')
        messenger.send('jumpLand')

    def blinkColor(self, color, duration):
        blink = Sequence(LerpColorScaleInterval(self.toon, 0.5, color, startColorScale=VBase4(1, 1, 1, 1)), LerpColorScaleInterval(self.toon, 0.5, VBase4(1, 1, 1, 1), startColorScale=color))
        track = Sequence(Func(blink.loop), Wait(duration), Func(blink.finish))
        return track

    def setAnimState(self, newState, playRate):
        if not self.unexpectedExit:
            self.toon.setAnimState(newState, playRate)

    def createHeadFrame(self, drawNum):
        toon = base.cr.doId2do.get(self.avId, None)
        self.headFrame = RaceHeadFrame.RaceHeadFrame(av=toon)
        eyes = self.headFrame.head.find('**/eyes*')
        eyes.setDepthTest(1)
        eyes.setDepthWrite(1)
        self.headFrame.configure(geom_scale=(0.5, 0.5, 0.5))
        self.headFrame.setZ(self.game.assetMgr.faceStartPos[2])
        self.headFrame.setDepthWrite(True)
        self.headFrame.setDepthTest(True)
        self.headFrame.reparentTo(self.game.assetMgr.aspect2dRoot)
        self.headFrame.setY(-drawNum)
        if self.isLocal:
            self.headFrame.setScale(0.2)
        else:
            self.headFrame.setScale(0.15)
        self.headFrame.setX(self.game.assetMgr.faceStartPos[0])
        return

    def update(self):
        toonCurrX = self.toon.getX(render)
        progress = toonCurrX - self.game.gameStartX
        headFrameProgress = progress * self.conversionRatio
        headFrameX = self.game.assetMgr.faceStartPos[0] + headFrameProgress
        headFrameX = max(self.game.assetMgr.faceStartPos[0], headFrameX)
        headFrameX = min(self.game.assetMgr.faceEndPos[0], headFrameX)
        self.headFrame.setX(headFrameX)

    def showScoreText(self, number, scale = 1.25):
        if not number == 0:
            if self.scoreText:
                self.hideScoreText()
            self.ScoreTextGenerator.setFont(OTPGlobals.getSignFont())
            if number < 0:
                self.ScoreTextGenerator.setText(str(number))
            else:
                self.ScoreTextGenerator.setText('+' + str(number))
            self.ScoreTextGenerator.clearShadow()
            self.ScoreTextGenerator.setAlign(TextNode.ACenter)
            if number < 0:
                r, g, b, a = (0.9, 0, 0, 1)
            else:
                r, g, b, a = (0.9, 0.9, 0, 1)
            self.scoreTextNode = self.ScoreTextGenerator.generate()
            self.scoreText = self.toon.attachNewNode(self.scoreTextNode)
            self.scoreText.setScale(scale)
            self.scoreText.setBillboardPointEye()
            self.scoreText.setBin('fixed', 100)
            self.scoreText.setPos(0, 0, self.toon.height / 2)
            self.scoreText.setTransparency(1)
            self.scoreText.setColor(r, g, b, a)
            self.scoreText.setDepthTest(0)
            self.scoreText.setDepthWrite(0)
            self.scoreTextSeq = Sequence(self.scoreText.posInterval(0.5, Point3(0, 0, self.toon.height + 2), blendType='easeOut'), self.scoreText.colorInterval(0.25, Vec4(r, g, b, 0)), Func(self.hideScoreText))
            self.scoreTextSeq.start()

    def hideScoreText(self):
        if self.scoreTextSeq:
            self.scoreTextSeq.finish()
            self.scoreTextSeq = None
        if self.scoreText:
            self.scoreText.removeNode()
            self.scoreText = None
        return
