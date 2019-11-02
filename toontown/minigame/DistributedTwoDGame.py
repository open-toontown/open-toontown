from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from toontown.toonbase.ToonBaseGlobal import *
from toontown.toonbase import TTLocalizer
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectGui import DGG
from direct.task.Task import Task
from direct.fsm import ClassicFSM, State
from direct.directnotify import DirectNotifyGlobal
from DistributedMinigame import *
import MinigameAvatarScorePanel, ArrowKeys, ToonBlitzAssetMgr, TwoDCamera
import TwoDSectionMgr, ToonBlitzGlobals, TwoDGameToonSD
from toontown.toonbase import ToontownTimer
from TwoDWalk import *
from TwoDDrive import *
COLOR_RED = VBase4(1, 0, 0, 0.3)

class DistributedTwoDGame(DistributedMinigame):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedTwoDGame')
    UpdateLocalToonTask = 'ToonBlitzUpdateLocalToonTask'
    EndGameTaskName = 'endTwoDGame'

    def __init__(self, cr):
        DistributedMinigame.__init__(self, cr)
        self.gameFSM = ClassicFSM.ClassicFSM('DistributedTwoDGame', [State.State('off', self.enterOff, self.exitOff, ['play']),
         State.State('play', self.enterPlay, self.exitPlay, ['cleanup', 'pause', 'showScores']),
         State.State('pause', self.enterPause, self.exitPause, ['cleanup', 'play', 'showScores']),
         State.State('showScores', self.enterShowScores, self.exitShowScores, ['cleanup']),
         State.State('cleanup', self.enterCleanup, self.exitCleanup, [])], 'off', 'cleanup')
        self.addChildGameFSM(self.gameFSM)
        self.reportedDone = False
        self.showCollSpheres = False

    def getTitle(self):
        return TTLocalizer.TwoDGameTitle

    def getInstructions(self):
        return TTLocalizer.TwoDGameInstructions

    def getMaxDuration(self):
        return 200

    def __defineConstants(self):
        self.TOON_SPEED = 12.0
        self.MAX_FRAME_MOVE = 1
        self.isHeadInFloor = False
        self.timeToRunToElevator = 1.5

    def setSectionsSelected(self, sectionsSelected):
        self.sectionsSelected = sectionsSelected

    def load(self):
        self.notify.debug('load')
        DistributedMinigame.load(self)
        self.__defineConstants()
        self.assetMgr = ToonBlitzAssetMgr.ToonBlitzAssetMgr(self)
        self.cameraMgr = TwoDCamera.TwoDCamera(camera)
        self.sectionMgr = TwoDSectionMgr.TwoDSectionMgr(self, self.sectionsSelected)
        self.gameStartX = -40.0
        endSection = self.sectionMgr.sections[-1]
        self.gameEndX = endSection.spawnPointMgr.gameEndX
        self.gameLength = self.gameEndX - self.gameStartX
        self.toonSDs = {}
        avId = self.localAvId
        toonSD = TwoDGameToonSD.TwoDGameToonSD(avId, self)
        self.toonSDs[avId] = toonSD
        self.toonSDs[avId].createHeadFrame(0)

    def unload(self):
        self.notify.debug('unload')
        DistributedMinigame.unload(self)
        taskMgr.remove(self.UpdateLocalToonTask)
        for avId in self.toonSDs.keys():
            toonSD = self.toonSDs[avId]
            toonSD.destroy()

        del self.toonSDs
        self.cameraMgr.destroy()
        del self.cameraMgr
        self.sectionMgr.destroy()
        del self.sectionMgr
        for panel in self.scorePanels:
            panel.cleanup()

        del self.scorePanels
        self.assetMgr.destroy()
        del self.assetMgr
        self.removeChildGameFSM(self.gameFSM)
        del self.gameFSM

    def onstage(self):
        self.notify.debug('onstage')
        DistributedMinigame.onstage(self)
        self.scorePanels = []
        self.assetMgr.onstage()
        lt = base.localAvatar
        lt.reparentTo(render)
        lt.hideName()
        self.__placeToon(self.localAvId)
        lt.setAnimState('Happy', 1.0)
        lt.setSpeed(0, 0)
        base.localAvatar.collisionsOn()
        base.localAvatar.setTransparency(1)
        self.setupHeadCollision()
        self.cameraMgr.onstage()
        toonSD = self.toonSDs[self.localAvId]
        toonSD.enter()
        toonSD.fsm.request('normal')
        self.twoDDrive = TwoDDrive(self, self.TOON_SPEED, maxFrameMove=self.MAX_FRAME_MOVE)

    def offstage(self):
        self.notify.debug('offstage')
        self.assetMgr.offstage()
        for avId in self.toonSDs.keys():
            self.toonSDs[avId].exit()

        base.localAvatar.setTransparency(0)
        self.ignore('enterheadCollSphere-into-floor1')
        base.localAvatar.controlManager.currentControls.cTrav.removeCollider(self.headCollNP)
        self.headCollNP.removeNode()
        del self.headCollNP
        base.localAvatar.laffMeter.start()
        DistributedMinigame.offstage(self)

    def setGameReady(self):
        if not self.hasLocalToon:
            return
        self.notify.debug('setGameReady')
        if DistributedMinigame.setGameReady(self):
            return
        drawNum = 0
        for avId in self.remoteAvIdList:
            toon = self.getAvatar(avId)
            if toon:
                drawNum += 1
                toon.reparentTo(render)
                toon.setAnimState('Happy', 1.0)
                toon.hideName()
                toon.startSmooth()
                toon.startLookAround()
                distCNP = toon.find('**/distAvatarCollNode*')
                distCNP.node().setIntoCollideMask(BitMask32.allOff())
                toonSD = TwoDGameToonSD.TwoDGameToonSD(avId, self)
                self.toonSDs[avId] = toonSD
                toonSD.enter()
                toonSD.fsm.request('normal')
                self.toonSDs[avId].createHeadFrame(drawNum)

    def setGameStart(self, timestamp):
        if not self.hasLocalToon:
            return
        self.notify.debug('setGameStart')
        DistributedMinigame.setGameStart(self, timestamp)
        self.twoDWalk = TwoDWalk(self.twoDDrive, broadcast=not self.isSinglePlayer())
        self.scores = [0] * self.numPlayers
        spacing = 0.4
        for i in xrange(self.numPlayers):
            avId = self.avIdList[i]
            avName = self.getAvatarName(avId)
            scorePanel = MinigameAvatarScorePanel.MinigameAvatarScorePanel(avId, avName)
            scorePanel.setScale(0.9)
            scorePanel.setPos(0.75 - spacing * (self.numPlayers - 1 - i), 0.0, 0.85)
            scorePanel.makeTransparent(0.75)
            self.scorePanels.append(scorePanel)

        self.gameFSM.request('play', [timestamp])

    def enterOff(self):
        self.notify.debug('enterOff')

    def exitOff(self):
        pass

    def enterPlay(self, timestamp):
        self.notify.debug('enterPlay')
        elapsedTime = globalClockDelta.localElapsedTime(timestamp)
        self.sectionMgr.enterPlay(elapsedTime)
        handlers = [None,
         None,
         None,
         None,
         self.shootKeyHandler]
        self.twoDDrive.arrowKeys.setPressHandlers(handlers)
        self.twoDWalk.start()
        self.accept('jumpStart', self.startJump)
        self.accept('enemyHit', self.localToonHitByEnemy)
        self.accept('twoDTreasureGrabbed', self.__treasureGrabbed)
        self.accept('enemyShot', self.__enemyShot)
        taskMgr.remove(self.UpdateLocalToonTask)
        taskMgr.add(self.__updateLocalToonTask, self.UpdateLocalToonTask, priority=1)
        base.localAvatar.laffMeter.stop()
        self.timer = ToontownTimer.ToontownTimer()
        self.timer.posInTopRightCorner()
        self.timer.setTime(ToonBlitzGlobals.GameDuration[self.getSafezoneId()])
        self.timer.countdown(ToonBlitzGlobals.GameDuration[self.getSafezoneId()], self.timerExpired)
        return

    def exitPlay(self):
        handlers = [None,
         None,
         None,
         None,
         None]
        self.twoDDrive.arrowKeys.setPressHandlers(handlers)
        if self.toonSDs[self.localAvId].fsm.getCurrentState().getName() != 'victory':
            base.localAvatar.b_setAnimState('Happy', 1.0)
        self.ignore('jumpStart')
        self.ignore('enemyHit')
        self.ignore('twoDTreasureGrabbed')
        return

    def enterPause(self):
        self.notify.debug('enterPause')

    def exitPause(self):
        pass

    def enterShowScores(self):
        self.notify.debug('enterShowScores')
        lerpTrack = Parallel()
        lerpDur = 0.5
        tY = 0.6
        bY = -.6
        lX = -.7
        cX = 0
        rX = 0.7
        scorePanelLocs = (((cX, bY),),
         ((lX, bY), (rX, bY)),
         ((cX, bY), (lX, bY), (rX, bY)),
         ((lX, tY),
          (rX, tY),
          (lX, bY),
          (rX, bY)))
        scorePanelLocs = scorePanelLocs[self.numPlayers - 1]
        for i in xrange(self.numPlayers):
            panel = self.scorePanels[i]
            pos = scorePanelLocs[i]
            lerpTrack.append(Parallel(LerpPosInterval(panel, lerpDur, Point3(pos[0], 0, pos[1]), blendType='easeInOut'), LerpScaleInterval(panel, lerpDur, Vec3(panel.getScale()) * 1.5, blendType='easeInOut')))

        self.showScoreTrack = Parallel(lerpTrack, self.getElevatorCloseTrack(), Sequence(Wait(ToonBlitzGlobals.ShowScoresDuration), Func(self.gameOver)))
        self.showScoreTrack.start()

    def exitShowScores(self):
        self.showScoreTrack.pause()
        del self.showScoreTrack

    def enterCleanup(self):
        self.notify.debug('enterCleanup')
        self.timer.stop()
        self.timer.destroy()
        del self.timer
        taskMgr.remove(self.EndGameTaskName)
        self.twoDWalk.stop()
        self.twoDWalk.destroy()
        del self.twoDWalk
        self.twoDDrive = None
        del self.twoDDrive
        return

    def exitCleanup(self):
        pass

    def acceptInputs(self):
        if hasattr(self, 'twoDDrive'):
            handlers = [None,
             None,
             None,
             None,
             self.shootKeyHandler]
            self.twoDDrive.arrowKeys.setPressHandlers(handlers)
            self.twoDDrive.start()
        return

    def ignoreInputs(self):
        if hasattr(self, 'twoDDrive'):
            handlers = [None,
             None,
             None,
             None,
             None]
            self.twoDDrive.arrowKeys.setPressHandlers(handlers)
            self.twoDDrive.lastAction = None
            self.twoDDrive.stop()
        return

    def __updateLocalToonTask(self, task):
        dt = globalClock.getDt()
        self.cameraMgr.update()
        if self.gameFSM.getCurrentState().getName() == 'play':
            if not self.toonSDs[self.localAvId].fsm.getCurrentState().getName() == 'victory':
                if not base.localAvatar.getY() == 0:
                    base.localAvatar.setY(0)
        if base.localAvatar.getZ() < -2.0:
            self.localToonFellDown()
        for avId in self.toonSDs.keys():
            self.toonSDs[avId].update()

        return task.cont

    def handleDisabledAvatar(self, avId):
        self.notify.debug('handleDisabledAvatar')
        self.notify.debug('avatar ' + str(avId) + ' disabled')
        self.toonSDs[avId].exit(unexpectedExit=True)
        del self.toonSDs[avId]
        DistributedMinigame.handleDisabledAvatar(self, avId)

    def setupHeadCollision(self):
        collSphere = CollisionSphere(0, 0, 0, 1)
        collSphere.setTangible(1)
        collNode = CollisionNode('headCollSphere')
        collNode.setFromCollideMask(ToontownGlobals.WallBitmask)
        collNode.setIntoCollideMask(BitMask32.allOff())
        collNode.addSolid(collSphere)
        head = base.localAvatar.getPart('head', '1000')
        self.headCollNP = head.attachNewNode(collNode)
        self.headCollNP.setPos(0, 0, 0.0)
        animal = base.localAvatar.style.getAnimal()
        if animal == 'dog' or animal == 'bear' or animal == 'horse':
            torso = base.localAvatar.style.torso
            legs = base.localAvatar.style.legs
            if (torso == 'ls' or torso == 'ld') and legs == 'l':
                self.headCollNP.setZ(-1.3)
            else:
                self.headCollNP.setZ(-0.7)
        elif animal == 'mouse' or animal == 'duck':
            self.headCollNP.setZ(0.5)
        elif animal == 'cat':
            self.headCollNP.setZ(-0.3)
        elif animal == 'rabbit':
            self.headCollNP.setZ(-0.5)
        elif animal == 'monkey':
            self.headCollNP.setZ(0.3)
        elif animal == 'pig':
            self.headCollNP.setZ(-0.7)
        self.headCollNP.hide()
        if self.showCollSpheres:
            self.headCollNP.show()
        headCollisionEvent = CollisionHandlerEvent()
        headCollisionEvent.addInPattern('enter%fn-into-%in')
        headCollisionEvent.addOutPattern('%fn-exit-%in')
        cTrav = base.localAvatar.controlManager.currentControls.cTrav
        cTrav.addCollider(self.headCollNP, headCollisionEvent)
        self.accept('enterheadCollSphere-into-floor1', self.__handleHeadCollisionIntoFloor)
        self.accept('headCollSphere-exit-floor1', self.__handleHeadCollisionExitFloor)

    def __handleHeadCollisionIntoFloor(self, cevent):
        self.isHeadInFloor = True
        if base.localAvatar.controlManager.currentControls.lifter.getVelocity() > 0:
            base.localAvatar.controlManager.currentControls.lifter.setVelocity(0.0)
            self.assetMgr.playHeadCollideSound()

    def __handleHeadCollisionExitFloor(self, cevent):
        self.isHeadInFloor = False

    def __placeToon(self, avId):
        toon = self.getAvatar(avId)
        i = self.avIdList.index(avId)
        pos = Point3(ToonBlitzGlobals.ToonStartingPosition[0] + i, ToonBlitzGlobals.ToonStartingPosition[1], ToonBlitzGlobals.ToonStartingPosition[2])
        toon.setPos(pos)
        toon.setHpr(-90, 0, 0)

    def startJump(self):
        self.assetMgr.playJumpSound()

    def checkValidity(self, avId):
        if not self.hasLocalToon:
            return False
        if self.gameFSM.getCurrentState() == None or self.gameFSM.getCurrentState().getName() != 'play':
            self.notify.warning('ignoring msg: av %s performing some action.' % avId)
            return False
        toon = self.getAvatar(avId)
        if toon == None:
            return False
        return True

    def shootKeyHandler(self):
        self.toonSDs[self.localAvId].shootGun()
        timestamp = globalClockDelta.localToNetworkTime(globalClock.getFrameTime())
        self.sendUpdate('showShootGun', [self.localAvId, timestamp])

    def showShootGun(self, avId, timestamp):
        if self.checkValidity(avId):
            self.notify.debug('avatar %s is shooting water gun' % avId)
            if avId != self.localAvId:
                self.toonSDs[avId].shootGun()

    def localToonFellDown(self):
        if self.toonSDs[self.localAvId].fsm.getCurrentState().getName() != 'fallDown':
            self.toonSDs[self.localAvId].fsm.request('fallDown')
            timestamp = globalClockDelta.localToNetworkTime(globalClock.getFrameTime())
            self.updateScore(self.localAvId, ToonBlitzGlobals.ScoreLossPerFallDown[self.getSafezoneId()])
            self.sendUpdate('toonFellDown', [self.localAvId, timestamp])

    def toonFellDown(self, avId, timestamp):
        if self.checkValidity(avId):
            self.notify.debug('avatar %s fell down.' % avId)
            if avId != self.localAvId:
                self.updateScore(avId, ToonBlitzGlobals.ScoreLossPerFallDown[self.getSafezoneId()])
                self.toonSDs[avId].fsm.request('fallDown')

    def localToonHitByEnemy(self):
        currToonState = self.toonSDs[self.localAvId].fsm.getCurrentState().getName()
        if not (currToonState == 'fallBack' or currToonState == 'squish'):
            self.toonSDs[self.localAvId].fsm.request('fallBack')
            timestamp = globalClockDelta.localToNetworkTime(globalClock.getFrameTime())
            self.updateScore(self.localAvId, ToonBlitzGlobals.ScoreLossPerEnemyCollision[self.getSafezoneId()])
            self.sendUpdate('toonHitByEnemy', [self.localAvId, timestamp])

    def toonHitByEnemy(self, avId, timestamp):
        if self.checkValidity(avId):
            self.notify.debug('avatar %s hit by a suit' % avId)
            if avId != self.localAvId:
                self.updateScore(avId, ToonBlitzGlobals.ScoreLossPerEnemyCollision[self.getSafezoneId()])
                self.toonSDs[avId].fsm.request('fallBack')

    def localToonSquished(self):
        currToonState = self.toonSDs[self.localAvId].fsm.getCurrentState().getName()
        if not (currToonState == 'fallBack' or currToonState == 'squish'):
            self.toonSDs[self.localAvId].fsm.request('squish')
            timestamp = globalClockDelta.localToNetworkTime(globalClock.getFrameTime())
            self.updateScore(self.localAvId, ToonBlitzGlobals.ScoreLossPerStomperSquish[self.getSafezoneId()])
            self.sendUpdate('toonSquished', [self.localAvId, timestamp])

    def toonSquished(self, avId, timestamp):
        if self.checkValidity(avId):
            self.notify.debug('avatar %s is squished.' % avId)
            if avId != self.localAvId:
                self.updateScore(avId, ToonBlitzGlobals.ScoreLossPerStomperSquish[self.getSafezoneId()])
                self.toonSDs[avId].fsm.request('squish')

    def localToonVictory(self):
        if not ToonBlitzGlobals.EndlessGame:
            self.ignoreInputs()
        if not self.toonSDs[self.localAvId].fsm.getCurrentState().getName() == 'victory':
            self.toonSDs[self.localAvId].fsm.request('victory')
            timestamp = globalClockDelta.localToNetworkTime(globalClock.getFrameTime())
            self.sendUpdate('toonVictory', [self.localAvId, timestamp])

    def toonVictory(self, avId, timestamp):
        if self.checkValidity(avId):
            self.notify.debug('avatar %s achieves victory' % avId)
            if avId != self.localAvId:
                self.toonSDs[avId].fsm.request('victory')

    def addVictoryScore(self, avId, score):
        if not self.hasLocalToon:
            return
        self.updateScore(avId, score)
        if avId == self.localAvId:
            self.assetMgr.threeSparkles.play()

    def __treasureGrabbed(self, sectionIndex, treasureIndex):
        self.notify.debug('treasure %s-%s grabbed' % (sectionIndex, treasureIndex))
        section = self.sectionMgr.sections[sectionIndex]
        section.treasureMgr.treasures[treasureIndex].hideTreasure()
        self.assetMgr.treasureGrabSound.play()
        self.sendUpdate('claimTreasure', [sectionIndex, treasureIndex])

    def setTreasureGrabbed(self, avId, sectionIndex, treasureIndex):
        if not self.hasLocalToon:
            return
        if self.gameFSM.getCurrentState().getName() == 'play':
            self.notify.debug('treasure %s-%s grabbed by %s' % (sectionIndex, treasureIndex, avId))
            numSections = len(self.sectionMgr.sections)
            if sectionIndex < numSections:
                section = self.sectionMgr.sections[sectionIndex]
                numTreasures = len(section.treasureMgr.treasures)
                if treasureIndex < numTreasures:
                    treasure = section.treasureMgr.treasures[treasureIndex]
                    if avId != self.localAvId:
                        treasure.hideTreasure()
                    self.updateScore(avId, ToonBlitzGlobals.ScoreGainPerTreasure * treasure.value)
                else:
                    self.notify.error('WHOA!! treasureIndex %s is out of range; numTreasures = %s' % (treasureIndex, numTreasures))
                    base.localAvatar.sendLogMessage('treasureIndex %s is out of range; numTreasures = %s' % (treasureIndex, numTreasures))
            else:
                self.notify.error('WHOA!! sectionIndex %s is out of range; numSections = %s' % (sectionIndex, numSections))
                base.localAvatar.sendLogMessage('sectionIndex %s is out of range; numSections = %s' % (sectionIndex, numSections))

    def __enemyShot(self, sectionIndex, enemyIndex):
        self.sectionMgr.sections[sectionIndex].enemyMgr.enemies[enemyIndex].doShotTrack()
        self.sendUpdate('claimEnemyShot', [sectionIndex, enemyIndex])

    def setEnemyShot(self, avId, sectionIndex, enemyIndex, enemyHealth):
        if not self.hasLocalToon:
            return
        if self.gameFSM.getCurrentState().getName() == 'play':
            self.notify.debug('enemy %s is shot by %s. Health left %s' % (enemyIndex, avId, enemyHealth))
            if enemyHealth > 0:
                if not avId == self.localAvId:
                    self.sectionMgr.sections[sectionIndex].enemyMgr.enemies[enemyIndex].doShotTrack()
            else:
                enemy = self.sectionMgr.sections[sectionIndex].enemyMgr.enemies[enemyIndex]
                treasureSpawnPoint = Point3(enemy.suit.getX(), enemy.suit.getY(), enemy.suit.getZ() + enemy.suit.height / 2.0)
                self.spawnTreasure(sectionIndex, enemyIndex, treasureSpawnPoint)
                enemy.doDeathTrack()

    def updateScore(self, avId, deltaScore):
        i = self.avIdList.index(avId)
        self.scores[i] += deltaScore
        self.scorePanels[i].setScore(self.scores[i])
        self.toonSDs[avId].showScoreText(deltaScore)

    def spawnTreasure(self, sectionIndex, enemyIndex, pos):
        if self.gameFSM.getCurrentState().getName() == 'play':
            section = self.sectionMgr.sections[sectionIndex]
            treasure = section.treasureMgr.enemyTreasures[enemyIndex]
            treasure.setTreasurePos(pos)
            treasure.popupEnemyTreasure()

    def timerExpired(self):
        self.notify.debug('timer expired')
        if not self.reportedDone:
            if not ToonBlitzGlobals.EndlessGame:
                self.ignoreInputs()
            self.reportedDone = True
            self.sendUpdate('reportDone')

    def setEveryoneDone(self):
        if not self.hasLocalToon:
            return
        if self.gameFSM.getCurrentState().getName() != 'play':
            self.notify.warning('ignoring setEveryoneDone msg')
            return
        self.notify.debug('setEveryoneDone')

        def endGame(task, self = self):
            if not ToonBlitzGlobals.EndlessGame:
                self.gameFSM.request('showScores')
            return Task.done

        self.timer.hide()
        taskMgr.doMethodLater(1, endGame, self.EndGameTaskName)

    def getElevatorCloseTrack(self):
        leftDoor = self.sectionMgr.exitElevator.find('**/doorL')
        rightDoor = self.sectionMgr.exitElevator.find('**/doorR')
        leftDoorClose = LerpPosInterval(leftDoor, 2, Point3(3.02, 0, 0))
        rightDoorClose = LerpPosInterval(rightDoor, 2, Point3(-3.02, 0, 0))
        return Sequence(Wait(self.timeToRunToElevator), Parallel(leftDoorClose, rightDoorClose))

    def debugStartPause(self):
        self.sectionMgr.enterPause()

    def debugEndPause(self):
        self.sectionMgr.exitPause()
