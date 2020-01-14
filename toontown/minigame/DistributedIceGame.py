import math
from pandac.PandaModules import Vec3, deg2Rad, Point3, NodePath, VBase4, CollisionHandlerEvent, CollisionNode, CollisionSphere
from direct.fsm import ClassicFSM, State
from direct.distributed.ClockDelta import globalClockDelta
from direct.gui.DirectGui import DirectLabel
from direct.interval.IntervalGlobal import Sequence, LerpScaleInterval, LerpFunctionInterval, Func, Parallel, LerpPosInterval, Wait, SoundInterval, LerpColorScaleInterval
from toontown.toonbase import ToontownGlobals, TTLocalizer, ToontownTimer
from toontown.minigame import ArrowKeys
from toontown.minigame import DistributedMinigame
from toontown.minigame import DistributedIceWorld
from toontown.minigame import IceGameGlobals
from toontown.minigame import MinigameAvatarScorePanel
from toontown.minigame import IceTreasure
import functools

class DistributedIceGame(DistributedMinigame.DistributedMinigame, DistributedIceWorld.DistributedIceWorld):
    notify = directNotify.newCategory('DistributedIceGame')
    MaxLocalForce = 100
    MaxPhysicsForce = 25000

    def __init__(self, cr):
        DistributedMinigame.DistributedMinigame.__init__(self, cr)
        DistributedIceWorld.DistributedIceWorld.__init__(self, cr)
        self.gameFSM = ClassicFSM.ClassicFSM('DistributedIceGame', [State.State('off', self.enterOff, self.exitOff, ['inputChoice']),
         State.State('inputChoice', self.enterInputChoice, self.exitInputChoice, ['waitServerChoices',
          'moveTires',
          'displayVotes',
          'cleanup']),
         State.State('waitServerChoices', self.enterWaitServerChoices, self.exitWaitServerChoices, ['moveTires', 'cleanup']),
         State.State('moveTires', self.enterMoveTires, self.exitMoveTires, ['synch', 'cleanup']),
         State.State('synch', self.enterSynch, self.exitSynch, ['inputChoice', 'scoring', 'cleanup']),
         State.State('scoring', self.enterScoring, self.exitScoring, ['cleanup', 'finalResults', 'inputChoice']),
         State.State('finalResults', self.enterFinalResults, self.exitFinalResults, ['cleanup']),
         State.State('cleanup', self.enterCleanup, self.exitCleanup, [])], 'off', 'cleanup')
        self.addChildGameFSM(self.gameFSM)
        self.cameraThreeQuarterView = (0, -22, 45, 0, -62.89, 0)
        self.tireDict = {}
        self.forceArrowDict = {}
        self.canDrive = False
        self.timer = None
        self.timerStartTime = None
        self.curForce = 0
        self.curHeading = 0
        self.headingMomentum = 0.0
        self.forceMomentum = 0.0
        self.allTireInputs = None
        self.curRound = 0
        self.curMatch = 0
        self.controlKeyWarningLabel = DirectLabel(text=TTLocalizer.IceGameControlKeyWarning, text_fg=VBase4(1, 0, 0, 1), relief=None, pos=(0.0, 0, 0), scale=0.15)
        self.controlKeyWarningLabel.hide()
        self.waitingMoveLabel = DirectLabel(text=TTLocalizer.IceGameWaitingForPlayersToFinishMove, text_fg=VBase4(1, 1, 1, 1), relief=None, pos=(-0.6, 0, -0.75), scale=0.075)
        self.waitingMoveLabel.hide()
        self.waitingSyncLabel = DirectLabel(text=TTLocalizer.IceGameWaitingForAISync, text_fg=VBase4(1, 1, 1, 1), relief=None, pos=(-0.6, 0, -0.75), scale=0.075)
        self.waitingSyncLabel.hide()
        self.infoLabel = DirectLabel(text='', text_fg=VBase4(0, 0, 0, 1), relief=None, pos=(0.0, 0, 0.7), scale=0.075)
        self.updateInfoLabel()
        self.lastForceArrowUpdateTime = 0
        self.sendForceArrowUpdateAsap = False
        self.treasures = []
        self.penalties = []
        self.obstacles = []
        self.controlKeyPressed = False
        self.controlKeyWarningIval = None
        return

    def delete(self):
        DistributedIceWorld.DistributedIceWorld.delete(self)
        DistributedMinigame.DistributedMinigame.delete(self)
        if self.controlKeyWarningIval:
            self.controlKeyWarningIval.finish()
            self.controlKeyWarningIval = None
        self.controlKeyWarningLabel.destroy()
        del self.controlKeyWarningLabel
        self.waitingMoveLabel.destroy()
        del self.waitingMoveLabel
        self.waitingSyncLabel.destroy()
        del self.waitingSyncLabel
        self.infoLabel.destroy()
        del self.infoLabel
        for treasure in self.treasures:
            treasure.destroy()

        del self.treasures
        for penalty in self.penalties:
            penalty.destroy()

        del self.penalties
        for obstacle in self.obstacles:
            obstacle.removeNode()

        del self.obstacles
        del self.gameFSM
        return

    def announceGenerate(self):
        DistributedMinigame.DistributedMinigame.announceGenerate(self)
        DistributedIceWorld.DistributedIceWorld.announceGenerate(self)
        self.debugTaskName = self.uniqueName('debugTask')

    def getTitle(self):
        return TTLocalizer.IceGameTitle

    def getInstructions(self):
        szId = self.getSafezoneId()
        numPenalties = IceGameGlobals.NumPenalties[szId]
        result = TTLocalizer.IceGameInstructions
        if numPenalties == 0:
            result = TTLocalizer.IceGameInstructionsNoTnt
        return result

    def getMaxDuration(self):
        return 0

    def load(self):
        self.notify.debug('load')
        DistributedMinigame.DistributedMinigame.load(self)
        self.music = base.loader.loadMusic('phase_4/audio/bgm/MG_IceGame.ogg')
        self.gameBoard = loader.loadModel('phase_4/models/minigames/ice_game_icerink')
        background = loader.loadModel('phase_4/models/minigames/ice_game_2d')
        background.reparentTo(self.gameBoard)
        self.gameBoard.setPosHpr(0, 0, 0, 0, 0, 0)
        self.gameBoard.setScale(1.0)
        self.setupSimulation()
        index = 0
        for avId in self.avIdList:
            self.setupTire(avId, index)
            self.setupForceArrow(avId)
            index += 1

        for index in range(len(self.avIdList), 4):
            self.setupTire(-index, index)
            self.setupForceArrow(-index)

        self.showForceArrows(realPlayersOnly=True)
        self.westWallModel = NodePath()
        if not self.westWallModel.isEmpty():
            self.westWallModel.reparentTo(self.gameBoard)
            self.westWallModel.setPos(IceGameGlobals.MinWall[0], IceGameGlobals.MinWall[1], 0)
            self.westWallModel.setScale(4)
        self.eastWallModel = NodePath()
        if not self.eastWallModel.isEmpty():
            self.eastWallModel.reparentTo(self.gameBoard)
            self.eastWallModel.setPos(IceGameGlobals.MaxWall[0], IceGameGlobals.MaxWall[1], 0)
            self.eastWallModel.setScale(4)
            self.eastWallModel.setH(180)
        self.arrowKeys = ArrowKeys.ArrowKeys()
        self.target = loader.loadModel('phase_3/models/misc/sphere')
        self.target.setScale(0.01)
        self.target.reparentTo(self.gameBoard)
        self.target.setPos(0, 0, 0)
        self.scoreCircle = loader.loadModel('phase_4/models/minigames/ice_game_score_circle')
        self.scoreCircle.setScale(0.01)
        self.scoreCircle.reparentTo(self.gameBoard)
        self.scoreCircle.setZ(IceGameGlobals.TireRadius / 2.0)
        self.scoreCircle.setAlphaScale(0.5)
        self.scoreCircle.setTransparency(1)
        self.scoreCircle.hide()
        self.treasureModel = loader.loadModel('phase_4/models/minigames/ice_game_barrel')
        self.penaltyModel = loader.loadModel('phase_4/models/minigames/ice_game_tnt2')
        self.penaltyModel.setScale(0.75, 0.75, 0.7)
        szId = self.getSafezoneId()
        obstacles = IceGameGlobals.Obstacles[szId]
        index = 0
        cubicObstacle = IceGameGlobals.ObstacleShapes[szId]
        for pos in obstacles:
            newPos = Point3(pos[0], pos[1], IceGameGlobals.TireRadius)
            newObstacle = self.createObstacle(newPos, index, cubicObstacle)
            self.obstacles.append(newObstacle)
            index += 1

        self.countSound = loader.loadSfx('phase_3.5/audio/sfx/tick_counter.ogg')
        self.treasureGrabSound = loader.loadSfx('phase_4/audio/sfx/MG_sfx_vine_game_bananas.ogg')
        self.penaltyGrabSound = loader.loadSfx('phase_4/audio/sfx/MG_cannon_fire_alt.ogg')
        self.tireSounds = []
        for tireIndex in range(4):
            tireHit = loader.loadSfx('phase_4/audio/sfx/Golf_Hit_Barrier_1.ogg')
            wallHit = loader.loadSfx('phase_4/audio/sfx/MG_maze_pickup.ogg')
            obstacleHit = loader.loadSfx('phase_4/audio/sfx/Golf_Hit_Barrier_2.ogg')
            self.tireSounds.append({'tireHit': tireHit,
             'wallHit': wallHit,
             'obstacleHit': obstacleHit})

        self.arrowRotateSound = loader.loadSfx('phase_4/audio/sfx/MG_sfx_ice_force_rotate.ogg')
        self.arrowUpSound = loader.loadSfx('phase_4/audio/sfx/MG_sfx_ice_force_increase_3sec.ogg')
        self.arrowDownSound = loader.loadSfx('phase_4/audio/sfx/MG_sfx_ice_force_decrease_3sec.ogg')
        self.scoreCircleSound = loader.loadSfx('phase_4/audio/sfx/MG_sfx_ice_scoring_1.ogg')

    def unload(self):
        self.notify.debug('unload')
        DistributedMinigame.DistributedMinigame.unload(self)
        del self.music
        self.gameBoard.removeNode()
        del self.gameBoard
        for forceArrow in list(self.forceArrowDict.values()):
            forceArrow.removeNode()

        del self.forceArrowDict
        self.scoreCircle.removeNode()
        del self.scoreCircle
        del self.countSound

    def onstage(self):
        self.notify.debug('onstage')
        DistributedMinigame.DistributedMinigame.onstage(self)
        self.gameBoard.reparentTo(render)
        self.__placeToon(self.localAvId)
        self.moveCameraToTop()
        self.scorePanels = []
        base.playMusic(self.music, looping=1, volume=0.8)

    def offstage(self):
        self.notify.debug('offstage')
        self.music.stop()
        self.gameBoard.hide()
        self.infoLabel.hide()
        for avId in self.tireDict:
            self.tireDict[avId]['tireNodePath'].hide()

        for panel in self.scorePanels:
            panel.cleanup()

        del self.scorePanels
        for obstacle in self.obstacles:
            obstacle.hide()

        for treasure in self.treasures:
            treasure.nodePath.hide()

        for penalty in self.penalties:
            penalty.nodePath.hide()

        for avId in self.avIdList:
            av = self.getAvatar(avId)
            if av:
                av.dropShadow.show()
                av.resetLOD()

        taskMgr.remove(self.uniqueName('aimtask'))
        self.arrowKeys.destroy()
        del self.arrowKeys
        DistributedMinigame.DistributedMinigame.offstage(self)

    def handleDisabledAvatar(self, avId):
        self.notify.debug('handleDisabledAvatar')
        self.notify.debug('avatar ' + str(avId) + ' disabled')
        DistributedMinigame.DistributedMinigame.handleDisabledAvatar(self, avId)

    def setGameReady(self):
        if not self.hasLocalToon:
            return
        self.notify.debug('setGameReady')
        if DistributedMinigame.DistributedMinigame.setGameReady(self):
            return
        for index in range(self.numPlayers):
            avId = self.avIdList[index]
            toon = self.getAvatar(avId)
            if toon:
                toon.reparentTo(render)
                self.__placeToon(avId)
                toon.forwardSpeed = 0
                toon.rotateSpeed = False
                toon.dropShadow.hide()
                toon.setAnimState('Sit')
                if avId in self.tireDict:
                    tireNp = self.tireDict[avId]['tireNodePath']
                    toon.reparentTo(tireNp)
                    toon.setY(1.0)
                    toon.setZ(-3)
                toon.startLookAround()

    def setGameStart(self, timestamp):
        if not self.hasLocalToon:
            return
        self.notify.debug('setGameStart')
        DistributedMinigame.DistributedMinigame.setGameStart(self, timestamp)
        for avId in self.remoteAvIdList:
            toon = self.getAvatar(avId)
            if toon:
                toon.stopLookAround()

        self.scores = [0] * self.numPlayers
        spacing = 0.4
        for i in range(self.numPlayers):
            avId = self.avIdList[i]
            avName = self.getAvatarName(avId)
            scorePanel = MinigameAvatarScorePanel.MinigameAvatarScorePanel(avId, avName)
            scorePanel.setScale(0.9)
            scorePanel.setPos(0.75 - spacing * (self.numPlayers - 1 - i), 0.0, 0.875)
            scorePanel.makeTransparent(0.75)
            self.scorePanels.append(scorePanel)

        self.arrowKeys.setPressHandlers([self.__upArrowPressed,
         self.__downArrowPressed,
         self.__leftArrowPressed,
         self.__rightArrowPressed,
         self.__controlPressed])

    def isInPlayState(self):
        if not self.gameFSM.getCurrentState():
            return False
        if not self.gameFSM.getCurrentState().getName() == 'play':
            return False
        return True

    def enterOff(self):
        self.notify.debug('enterOff')

    def exitOff(self):
        pass

    def enterInputChoice(self):
        self.notify.debug('enterInputChoice')
        self.forceLocalToonToTire()
        self.controlKeyPressed = False
        if self.curRound == 0:
            self.setupStartOfMatch()
        else:
            self.notify.debug('self.curRound = %s' % self.curRound)
        self.timer = ToontownTimer.ToontownTimer()
        self.timer.hide()
        if self.timerStartTime != None:
            self.startTimer()
        self.showForceArrows(realPlayersOnly=True)
        self.localForceArrow().setPosHpr(0, 0, -1.0, 0, 0, 0)
        self.localForceArrow().reparentTo(self.localTireNp())
        self.localForceArrow().setY(IceGameGlobals.TireRadius)
        self.localTireNp().headsUp(self.target)
        self.notify.debug('self.localForceArrow() heading = %s' % self.localForceArrow().getH())
        self.curHeading = self.localTireNp().getH()
        self.curForce = 25
        self.updateLocalForceArrow()
        for avId in self.forceArrowDict:
            forceArrow = self.forceArrowDict[avId]
            forceArrow.setPosHpr(0, 0, -1.0, 0, 0, 0)
            tireNp = self.tireDict[avId]['tireNodePath']
            forceArrow.reparentTo(tireNp)
            forceArrow.setY(IceGameGlobals.TireRadius)
            tireNp.headsUp(self.target)
            self.updateForceArrow(avId, tireNp.getH(), 25)

        taskMgr.add(self.__aimTask, self.uniqueName('aimtask'))
        if base.localAvatar.laffMeter:
            base.localAvatar.laffMeter.stop()
        self.sendForceArrowUpdateAsap = False
        return

    def exitInputChoice(self):
        if not self.controlKeyPressed:
            if self.controlKeyWarningIval:
                self.controlKeyWarningIval.finish()
                self.controlKeyWarningIval = None
            self.controlKeyWarningIval = Sequence(Func(self.controlKeyWarningLabel.show), self.controlKeyWarningLabel.colorScaleInterval(10, VBase4(1, 1, 1, 0), startColorScale=VBase4(1, 1, 1, 1)), Func(self.controlKeyWarningLabel.hide))
            self.controlKeyWarningIval.start()
        if self.timer != None:
            self.timer.destroy()
            self.timer = None
        self.timerStartTime = None
        self.hideForceArrows()
        self.arrowRotateSound.stop()
        self.arrowUpSound.stop()
        self.arrowDownSound.stop()
        taskMgr.remove(self.uniqueName('aimtask'))
        return

    def enterWaitServerChoices(self):
        self.waitingMoveLabel.show()
        self.showForceArrows(True)

    def exitWaitServerChoices(self):
        self.waitingMoveLabel.hide()
        self.hideForceArrows()

    def enterMoveTires(self):
        for key in self.tireDict:
            body = self.tireDict[key]['tireBody']
            body.setAngularVel(0, 0, 0)
            body.setLinearVel(0, 0, 0)

        for index in range(len(self.allTireInputs)):
            input = self.allTireInputs[index]
            avId = self.avIdList[index]
            body = self.getTireBody(avId)
            degs = input[1] + 90
            tireNp = self.getTireNp(avId)
            tireH = tireNp.getH()
            self.notify.debug('tireH = %s' % tireH)
            radAngle = deg2Rad(degs)
            foo = NodePath('foo')
            dirVector = Vec3(math.cos(radAngle), math.sin(radAngle), 0)
            self.notify.debug('dirVector is now=%s' % dirVector)
            inputForce = input[0]
            inputForce /= self.MaxLocalForce
            inputForce *= self.MaxPhysicsForce
            force = dirVector * inputForce
            self.notify.debug('adding force %s to %d' % (force, avId))
            body.addForce(force)

        self.enableAllTireBodies()
        self.totalPhysicsSteps = 0
        self.startSim()
        taskMgr.add(self.__moveTiresTask, self.uniqueName('moveTiresTtask'))

    def exitMoveTires(self):
        self.forceLocalToonToTire()
        self.disableAllTireBodies()
        self.stopSim()
        self.notify.debug('total Physics steps = %d' % self.totalPhysicsSteps)
        taskMgr.remove(self.uniqueName('moveTiresTtask'))

    def enterSynch(self):
        self.waitingSyncLabel.show()

    def exitSynch(self):
        self.waitingSyncLabel.hide()

    def enterScoring(self):
        sortedByDistance = []
        for avId in self.avIdList:
            np = self.getTireNp(avId)
            pos = np.getPos()
            pos.setZ(0)
            sortedByDistance.append((avId, pos.length()))

        def compareDistance(x, y):
            if x[1] - y[1] > 0:
                return 1
            elif x[1] - y[1] < 0:
                return -1
            else:
                return 0

        sortedByDistance.sort(key=functools.cmp_to_key(compareDistance))
        self.scoreMovie = Sequence()
        curScale = 0.01
        curTime = 0
        self.scoreCircle.setScale(0.01)
        self.scoreCircle.show()
        self.notify.debug('newScores = %s' % self.newScores)
        circleStartTime = 0
        for index in range(len(sortedByDistance)):
            distance = sortedByDistance[index][1]
            avId = sortedByDistance[index][0]
            scorePanelIndex = self.avIdList.index(avId)
            time = (distance - curScale) / IceGameGlobals.ExpandFeetPerSec
            if time < 0:
                time = 0.01
            scaleXY = distance + IceGameGlobals.TireRadius
            self.notify.debug('circleStartTime = %s' % circleStartTime)
            self.scoreMovie.append(Parallel(LerpScaleInterval(self.scoreCircle, time, Point3(scaleXY, scaleXY, 1.0)), SoundInterval(self.scoreCircleSound, duration=time, startTime=circleStartTime)))
            circleStartTime += time
            startScore = self.scorePanels[scorePanelIndex].getScore()
            destScore = self.newScores[scorePanelIndex]
            self.notify.debug('for avId %d, startScore=%d, newScores=%d' % (avId, startScore, destScore))

            def increaseScores(t, scorePanelIndex = scorePanelIndex, startScore = startScore, destScore = destScore):
                oldScore = self.scorePanels[scorePanelIndex].getScore()
                diff = destScore - startScore
                newScore = int(startScore + diff * t)
                if newScore > oldScore:
                    base.playSfx(self.countSound)
                self.scorePanels[scorePanelIndex].setScore(newScore)
                self.scores[scorePanelIndex] = newScore

            duration = (destScore - startScore) * IceGameGlobals.ScoreCountUpRate
            tireNp = self.tireDict[avId]['tireNodePath']
            self.scoreMovie.append(Parallel(LerpFunctionInterval(increaseScores, duration), Sequence(LerpColorScaleInterval(tireNp, duration / 6.0, VBase4(1, 0, 0, 1)), LerpColorScaleInterval(tireNp, duration / 6.0, VBase4(1, 1, 1, 1)), LerpColorScaleInterval(tireNp, duration / 6.0, VBase4(1, 0, 0, 1)), LerpColorScaleInterval(tireNp, duration / 6.0, VBase4(1, 1, 1, 1)), LerpColorScaleInterval(tireNp, duration / 6.0, VBase4(1, 0, 0, 1)), LerpColorScaleInterval(tireNp, duration / 6.0, VBase4(1, 1, 1, 1)))))
            curScale += distance

        self.scoreMovie.append(Func(self.sendUpdate, 'reportScoringMovieDone', []))
        self.scoreMovie.start()

    def exitScoring(self):
        self.scoreMovie.finish()
        self.scoreMovie = None
        self.scoreCircle.hide()
        return

    def enterFinalResults(self):
        lerpTrack = Parallel()
        lerpDur = 0.5
        tY = 0.6
        bY = -.05
        lX = -.5
        cX = 0
        rX = 0.5
        scorePanelLocs = (((cX, bY),),
         ((lX, bY), (rX, bY)),
         ((cX, tY), (lX, bY), (rX, bY)),
         ((lX, tY),
          (rX, tY),
          (lX, bY),
          (rX, bY)))
        scorePanelLocs = scorePanelLocs[self.numPlayers - 1]
        for i in range(self.numPlayers):
            panel = self.scorePanels[i]
            pos = scorePanelLocs[i]
            lerpTrack.append(Parallel(LerpPosInterval(panel, lerpDur, Point3(pos[0], 0, pos[1]), blendType='easeInOut'), LerpScaleInterval(panel, lerpDur, Vec3(panel.getScale()) * 2.0, blendType='easeInOut')))

        self.showScoreTrack = Parallel(lerpTrack, Sequence(Wait(IceGameGlobals.ShowScoresDuration), Func(self.gameOver)))
        self.showScoreTrack.start()

    def exitFinalResults(self):
        self.showScoreTrack.pause()
        del self.showScoreTrack

    def enterCleanup(self):
        self.notify.debug('enterCleanup')
        if base.localAvatar.laffMeter:
            base.localAvatar.laffMeter.start()

    def exitCleanup(self):
        pass

    def __placeToon(self, avId):
        toon = self.getAvatar(avId)
        if toon:
            toon.setPos(0, 0, 0)
            toon.setHpr(0, 0, 0)

    def moveCameraToTop(self):
        camera.reparentTo(render)
        p = self.cameraThreeQuarterView
        camera.setPosHpr(p[0], p[1], p[2], p[3], p[4], p[5])

    def setupTire(self, avId, index):
        tireNp, tireBody, tireOdeGeom = self.createTire(index)
        self.tireDict[avId] = {'tireNodePath': tireNp,
         'tireBody': tireBody,
         'tireOdeGeom': tireOdeGeom}
        if avId <= 0:
            tireBlocker = tireNp.find('**/tireblockermesh')
            if not tireBlocker.isEmpty():
                tireBlocker.hide()
        if avId == self.localAvId:
            tireNp = self.tireDict[avId]['tireNodePath']
            self.treasureSphereName = 'treasureCollider'
            self.treasureCollSphere = CollisionSphere(0, 0, 0, IceGameGlobals.TireRadius)
            self.treasureCollSphere.setTangible(0)
            self.treasureCollNode = CollisionNode(self.treasureSphereName)
            self.treasureCollNode.setFromCollideMask(ToontownGlobals.PieBitmask)
            self.treasureCollNode.addSolid(self.treasureCollSphere)
            self.treasureCollNodePath = tireNp.attachNewNode(self.treasureCollNode)
            self.treasureHandler = CollisionHandlerEvent()
            self.treasureHandler.addInPattern('%fn-intoTreasure')
            base.cTrav.addCollider(self.treasureCollNodePath, self.treasureHandler)
            eventName = '%s-intoTreasure' % self.treasureCollNodePath.getName()
            self.notify.debug('eventName = %s' % eventName)
            self.accept(eventName, self.toonHitSomething)

    def setupForceArrow(self, avId):
        arrow = loader.loadModel('phase_4/models/minigames/ice_game_arrow')
        priority = 0
        if avId < 0:
            priority = -avId
        else:
            priority = self.avIdList.index(avId)
            if avId == self.localAvId:
                priority = 10
        self.forceArrowDict[avId] = arrow

    def hideForceArrows(self):
        for forceArrow in list(self.forceArrowDict.values()):
            forceArrow.hide()

    def showForceArrows(self, realPlayersOnly = True):
        for avId in self.forceArrowDict:
            if realPlayersOnly:
                if avId > 0:
                    self.forceArrowDict[avId].show()
                else:
                    self.forceArrowDict[avId].hide()
            else:
                self.forceArrowDict[avId].show()

    def localForceArrow(self):
        if self.localAvId in self.forceArrowDict:
            return self.forceArrowDict[self.localAvId]
        else:
            return None
        return None

    def setChoices(self, input0, input1, input2, input3):
        pass

    def startDebugTask(self):
        taskMgr.add(self.debugTask, self.debugTaskName)

    def stopDebugTask(self):
        taskMgr.remove(self.debugTaskName)

    def debugTask(self, task):
        if self.canDrive and localAvatar.doId in self.tireDict:
            dt = globalClock.getDt()
            forceMove = 25000
            forceMoveDt = forceMove
            tireBody = self.tireDict[localAvatar.doId]['tireBody']
            if self.arrowKeys.upPressed() and not tireBody.isEnabled():
                x = 0
                y = 1
                tireBody.enable()
                tireBody.addForce(Vec3(x * forceMoveDt, y * forceMoveDt, 0))
            if self.arrowKeys.downPressed() and not tireBody.isEnabled():
                x = 0
                y = -1
                tireBody.enable()
                tireBody.addForce(Vec3(x * forceMoveDt, y * forceMoveDt, 0))
            if self.arrowKeys.leftPressed() and not tireBody.isEnabled():
                x = -1
                y = 0
                tireBody.enable()
                tireBody.addForce(Vec3(x * forceMoveDt, y * forceMoveDt, 0))
            if self.arrowKeys.rightPressed() and not tireBody.isEnabled():
                x = 1
                y = 0
                tireBody.enable()
                tireBody.addForce(Vec3(x * forceMoveDt, y * forceMoveDt, 0))
        return task.cont

    def __upArrowPressed(self):
        pass

    def __downArrowPressed(self):
        pass

    def __leftArrowPressed(self):
        pass

    def __rightArrowPressed(self):
        pass

    def __controlPressed(self):
        if self.gameFSM.getCurrentState().getName() == 'inputChoice':
            self.sendForceArrowUpdateAsap = True
            self.updateLocalForceArrow()
            self.controlKeyPressed = True
            self.sendUpdate('setAvatarChoice', [self.curForce, self.curHeading])
            self.gameFSM.request('waitServerChoices')

    def startTimer(self):
        now = globalClock.getFrameTime()
        elapsed = now - self.timerStartTime
        self.timer.posInTopRightCorner()
        self.timer.setTime(IceGameGlobals.InputTimeout)
        self.timer.countdown(IceGameGlobals.InputTimeout - elapsed, self.handleChoiceTimeout)
        self.timer.show()

    def setTimerStartTime(self, timestamp):
        if not self.hasLocalToon:
            return
        self.timerStartTime = globalClockDelta.networkToLocalTime(timestamp)
        if self.timer != None:
            self.startTimer()
        return

    def handleChoiceTimeout(self):
        self.sendUpdate('setAvatarChoice', [0, 0])
        self.gameFSM.request('waitServerChoices')

    def localTireNp(self):
        ret = None
        if self.localAvId in self.tireDict:
            ret = self.tireDict[self.localAvId]['tireNodePath']
        return ret

    def localTireBody(self):
        ret = None
        if self.localAvId in self.tireDict:
            ret = self.tireDict[self.localAvId]['tireBody']
        return ret

    def getTireBody(self, avId):
        ret = None
        if avId in self.tireDict:
            ret = self.tireDict[avId]['tireBody']
        return ret

    def getTireNp(self, avId):
        ret = None
        if avId in self.tireDict:
            ret = self.tireDict[avId]['tireNodePath']
        return ret

    def updateForceArrow(self, avId, curHeading, curForce):
        forceArrow = self.forceArrowDict[avId]
        tireNp = self.tireDict[avId]['tireNodePath']
        tireNp.setH(curHeading)
        tireBody = self.tireDict[avId]['tireBody']
        tireBody.setQuaternion(tireNp.getQuat())
        self.notify.debug('curHeading = %s' % curHeading)
        yScale = curForce / 100.0
        yScale *= 1
        headY = yScale * 15
        xScale = (yScale - 1) / 2.0 + 1.0
        shaft = forceArrow.find('**/arrow_shaft')
        head = forceArrow.find('**/arrow_head')
        shaft.setScale(xScale, yScale, 1)
        head.setPos(0, headY, 0)
        head.setScale(xScale, xScale, 1)

    def updateLocalForceArrow(self):
        avId = self.localAvId
        self.b_setForceArrowInfo(avId, self.curHeading, self.curForce)

    def __aimTask(self, task):
        if not hasattr(self, 'arrowKeys'):
            return task.done
        dt = globalClock.getDt()
        headingMomentumChange = dt * 60.0
        forceMomentumChange = dt * 160.0
        arrowUpdate = False
        arrowRotating = False
        arrowUp = False
        arrowDown = False
        if self.arrowKeys.upPressed() and not self.arrowKeys.downPressed():
            self.forceMomentum += forceMomentumChange
            if self.forceMomentum < 0:
                self.forceMomentum = 0
            if self.forceMomentum > 50:
                self.forceMomentum = 50
            oldForce = self.curForce
            self.curForce += self.forceMomentum * dt
            arrowUpdate = True
            if oldForce < self.MaxLocalForce:
                arrowUp = True
        elif self.arrowKeys.downPressed() and not self.arrowKeys.upPressed():
            self.forceMomentum += forceMomentumChange
            if self.forceMomentum < 0:
                self.forceMomentum = 0
            if self.forceMomentum > 50:
                self.forceMomentum = 50
            oldForce = self.curForce
            self.curForce -= self.forceMomentum * dt
            arrowUpdate = True
            if oldForce > 0.01:
                arrowDown = True
        else:
            self.forceMomentum = 0
        if self.arrowKeys.leftPressed() and not self.arrowKeys.rightPressed():
            self.headingMomentum += headingMomentumChange
            if self.headingMomentum < 0:
                self.headingMomentum = 0
            if self.headingMomentum > 50:
                self.headingMomentum = 50
            self.curHeading += self.headingMomentum * dt
            arrowUpdate = True
            arrowRotating = True
        elif self.arrowKeys.rightPressed() and not self.arrowKeys.leftPressed():
            self.headingMomentum += headingMomentumChange
            if self.headingMomentum < 0:
                self.headingMomentum = 0
            if self.headingMomentum > 50:
                self.headingMomentum = 50
            self.curHeading -= self.headingMomentum * dt
            arrowUpdate = True
            arrowRotating = True
        else:
            self.headingMomentum = 0
        if arrowUpdate:
            self.normalizeHeadingAndForce()
            self.updateLocalForceArrow()
        if arrowRotating:
            if not self.arrowRotateSound.status() == self.arrowRotateSound.PLAYING:
                base.playSfx(self.arrowRotateSound, looping=True)
        else:
            self.arrowRotateSound.stop()
        if arrowUp:
            if not self.arrowUpSound.status() == self.arrowUpSound.PLAYING:
                base.playSfx(self.arrowUpSound, looping=False)
        else:
            self.arrowUpSound.stop()
        if arrowDown:
            if not self.arrowDownSound.status() == self.arrowDownSound.PLAYING:
                base.playSfx(self.arrowDownSound, looping=False)
        else:
            self.arrowDownSound.stop()
        return task.cont

    def normalizeHeadingAndForce(self):
        if self.curForce > self.MaxLocalForce:
            self.curForce = self.MaxLocalForce
        if self.curForce < 0.01:
            self.curForce = 0.01

    def setTireInputs(self, tireInputs):
        if not self.hasLocalToon:
            return
        self.allTireInputs = tireInputs
        self.gameFSM.request('moveTires')

    def enableAllTireBodies(self):
        for avId in list(self.tireDict.keys()):
            self.tireDict[avId]['tireBody'].enable()

    def disableAllTireBodies(self):
        for avId in list(self.tireDict.keys()):
            self.tireDict[avId]['tireBody'].disable()

    def areAllTiresDisabled(self):
        for avId in list(self.tireDict.keys()):
            if self.tireDict[avId]['tireBody'].isEnabled():
                return False

        return True

    def __moveTiresTask(self, task):
        if self.areAllTiresDisabled():
            self.sendTirePositions()
            self.gameFSM.request('synch')
            return task.done
        return task.cont

    def sendTirePositions(self):
        tirePositions = []
        for index in range(len(self.avIdList)):
            avId = self.avIdList[index]
            tire = self.getTireBody(avId)
            pos = Point3(tire.getPosition())
            tirePositions.append([pos[0], pos[1], pos[2]])

        for index in range(len(self.avIdList), 4):
            avId = -index
            tire = self.getTireBody(avId)
            pos = Point3(tire.getPosition())
            tirePositions.append([pos[0], pos[1], pos[2]])

        self.sendUpdate('endingPositions', [tirePositions])

    def setFinalPositions(self, finalPos):
        if not self.hasLocalToon:
            return
        for index in range(len(self.avIdList)):
            avId = self.avIdList[index]
            tire = self.getTireBody(avId)
            np = self.getTireNp(avId)
            pos = finalPos[index]
            tire.setPosition(pos[0], pos[1], pos[2])
            np.setPos(pos[0], pos[1], pos[2])

        for index in range(len(self.avIdList), 4):
            avId = -index
            tire = self.getTireBody(avId)
            np = self.getTireNp(avId)
            pos = finalPos[index]
            tire.setPosition(pos[0], pos[1], pos[2])
            np.setPos(pos[0], pos[1], pos[2])

    def updateInfoLabel(self):
        self.infoLabel['text'] = TTLocalizer.IceGameInfo % {'curMatch': self.curMatch + 1,
         'numMatch': IceGameGlobals.NumMatches,
         'curRound': self.curRound + 1,
         'numRound': IceGameGlobals.NumRounds}

    def setMatchAndRound(self, match, round):
        if not self.hasLocalToon:
            return
        self.curMatch = match
        self.curRound = round
        self.updateInfoLabel()

    def setScores(self, match, round, scores):
        if not self.hasLocalToon:
            return
        self.newMatch = match
        self.newRound = round
        self.newScores = scores

    def setNewState(self, state):
        if not self.hasLocalToon:
            return
        self.notify.debug('setNewState gameFSM=%s newState=%s' % (self.gameFSM, state))
        self.gameFSM.request(state)

    def putAllTiresInStartingPositions(self):
        for index in range(len(self.avIdList)):
            avId = self.avIdList[index]
            np = self.tireDict[avId]['tireNodePath']
            np.setPos(IceGameGlobals.StartingPositions[index])
            self.notify.debug('avId=%s newPos=%s' % (avId, np.getPos))
            np.setHpr(0, 0, 0)
            quat = np.getQuat()
            body = self.tireDict[avId]['tireBody']
            body.setPosition(IceGameGlobals.StartingPositions[index])
            body.setQuaternion(quat)

        for index in range(len(self.avIdList), 4):
            avId = -index
            np = self.tireDict[avId]['tireNodePath']
            np.setPos(IceGameGlobals.StartingPositions[index])
            self.notify.debug('avId=%s newPos=%s' % (avId, np.getPos))
            np.setHpr(0, 0, 0)
            quat = np.getQuat()
            body = self.tireDict[avId]['tireBody']
            body.setPosition(IceGameGlobals.StartingPositions[index])
            body.setQuaternion(quat)

    def b_setForceArrowInfo(self, avId, force, heading):
        self.setForceArrowInfo(avId, force, heading)
        self.d_setForceArrowInfo(avId, force, heading)

    def d_setForceArrowInfo(self, avId, force, heading):
        sendIt = False
        curTime = self.getCurrentGameTime()
        if self.sendForceArrowUpdateAsap:
            sendIt = True
        elif curTime - self.lastForceArrowUpdateTime > 0.2:
            sendIt = True
        if sendIt:
            self.sendUpdate('setForceArrowInfo', [avId, force, heading])
            self.sendForceArrowUpdateAsap = False
            self.lastForceArrowUpdateTime = self.getCurrentGameTime()

    def setForceArrowInfo(self, avId, force, heading):
        if not self.hasLocalToon:
            return
        self.updateForceArrow(avId, force, heading)

    def setupStartOfMatch(self):
        self.putAllTiresInStartingPositions()
        szId = self.getSafezoneId()
        self.numTreasures = IceGameGlobals.NumTreasures[szId]
        if self.treasures:
            for treasure in self.treasures:
                treasure.destroy()

            self.treasures = []
        index = 0
        treasureMargin = IceGameGlobals.TireRadius + 1.0
        while len(self.treasures) < self.numTreasures:
            xPos = self.randomNumGen.randrange(IceGameGlobals.MinWall[0] + 5, IceGameGlobals.MaxWall[0] - 5)
            yPos = self.randomNumGen.randrange(IceGameGlobals.MinWall[1] + 5, IceGameGlobals.MaxWall[1] - 5)
            self.notify.debug('yPos=%s' % yPos)
            pos = Point3(xPos, yPos, IceGameGlobals.TireRadius)
            newTreasure = IceTreasure.IceTreasure(self.treasureModel, pos, index, self.doId, penalty=False)
            goodSpot = True
            for obstacle in self.obstacles:
                if newTreasure.nodePath.getDistance(obstacle) < treasureMargin:
                    goodSpot = False
                    break

            if goodSpot:
                for treasure in self.treasures:
                    if newTreasure.nodePath.getDistance(treasure.nodePath) < treasureMargin:
                        goodSpot = False
                        break

            if goodSpot:
                self.treasures.append(newTreasure)
                index += 1
            else:
                newTreasure.destroy()

        self.numPenalties = IceGameGlobals.NumPenalties[szId]
        if self.penalties:
            for penalty in self.penalties:
                penalty.destroy()

            self.penalties = []
        index = 0
        while len(self.penalties) < self.numPenalties:
            xPos = self.randomNumGen.randrange(IceGameGlobals.MinWall[0] + 5, IceGameGlobals.MaxWall[0] - 5)
            yPos = self.randomNumGen.randrange(IceGameGlobals.MinWall[1] + 5, IceGameGlobals.MaxWall[1] - 5)
            self.notify.debug('yPos=%s' % yPos)
            pos = Point3(xPos, yPos, IceGameGlobals.TireRadius)
            newPenalty = IceTreasure.IceTreasure(self.penaltyModel, pos, index, self.doId, penalty=True)
            goodSpot = True
            for obstacle in self.obstacles:
                if newPenalty.nodePath.getDistance(obstacle) < treasureMargin:
                    goodSpot = False
                    break

            if goodSpot:
                for treasure in self.treasures:
                    if newPenalty.nodePath.getDistance(treasure.nodePath) < treasureMargin:
                        goodSpot = False
                        break

            if goodSpot:
                for penalty in self.penalties:
                    if newPenalty.nodePath.getDistance(penalty.nodePath) < treasureMargin:
                        goodSpot = False
                        break

            if goodSpot:
                self.penalties.append(newPenalty)
                index += 1
            else:
                newPenalty.destroy()

    def toonHitSomething(self, entry):
        self.notify.debug('---- treasure Enter ---- ')
        self.notify.debug('%s' % entry)
        name = entry.getIntoNodePath().getName()
        parts = name.split('-')
        if len(parts) < 3:
            self.notify.debug('collided with %s, but returning' % name)
            return
        if not int(parts[1]) == self.doId:
            self.notify.debug("collided with %s, but doId doesn't match" % name)
            return
        treasureNum = int(parts[2])
        if 'penalty' in parts[0]:
            self.__penaltyGrabbed(treasureNum)
        else:
            self.__treasureGrabbed(treasureNum)

    def __treasureGrabbed(self, treasureNum):
        self.treasures[treasureNum].showGrab()
        self.treasureGrabSound.play()
        self.sendUpdate('claimTreasure', [treasureNum])

    def setTreasureGrabbed(self, avId, treasureNum):
        if not self.hasLocalToon:
            return
        self.notify.debug('treasure %s grabbed by %s' % (treasureNum, avId))
        if avId != self.localAvId:
            self.treasures[treasureNum].showGrab()
        i = self.avIdList.index(avId)
        self.scores[i] += 1
        self.scorePanels[i].setScore(self.scores[i])

    def __penaltyGrabbed(self, penaltyNum):
        self.penalties[penaltyNum].showGrab()
        self.sendUpdate('claimPenalty', [penaltyNum])

    def setPenaltyGrabbed(self, avId, penaltyNum):
        if not self.hasLocalToon:
            return
        self.notify.debug('penalty %s grabbed by %s' % (penaltyNum, avId))
        if avId != self.localAvId:
            self.penalties[penaltyNum].showGrab()
        i = self.avIdList.index(avId)
        self.scores[i] -= 1
        self.scorePanels[i].setScore(self.scores[i])

    def postStep(self):
        DistributedIceWorld.DistributedIceWorld.postStep(self)
        for entry in self.colEntries:
            c0, c1 = self.getOrderedContacts(entry)
            if c1 in self.tireCollideIds:
                tireIndex = self.tireCollideIds.index(c1)
                if c0 in self.tireCollideIds:
                    self.tireSounds[tireIndex]['tireHit'].play()
                elif c0 == self.wallCollideId:
                    self.tireSounds[tireIndex]['wallHit'].play()
                elif c0 == self.obstacleCollideId:
                    self.tireSounds[tireIndex]['obstacleHit'].play()

    def forceLocalToonToTire(self):
        toon = localAvatar
        if toon and self.localAvId in self.tireDict:
            tireNp = self.tireDict[self.localAvId]['tireNodePath']
            toon.reparentTo(tireNp)
            toon.setPosHpr(0, 0, 0, 0, 0, 0)
            toon.setY(1.0)
            toon.setZ(-3)
