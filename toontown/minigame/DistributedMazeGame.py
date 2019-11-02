from direct.interval.IntervalGlobal import LerpPosInterval, LerpHprInterval, LerpPosHprInterval
from direct.interval.IntervalGlobal import SoundInterval, LerpScaleInterval, LerpFunctionInterval
from direct.interval.IntervalGlobal import Wait, Func
from direct.interval.MetaInterval import Sequence, Parallel
from direct.gui.DirectGui import DirectWaitBar, DGG
from direct.showbase import PythonUtil
from direct.fsm import ClassicFSM, State
from direct.showbase import RandomNumGen
from direct.task.Task import Task
from direct.distributed.ClockDelta import globalClockDelta
from pandac.PandaModules import Point3, Vec3
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownTimer
from DistributedMinigame import DistributedMinigame
from MazeSuit import MazeSuit
from OrthoWalk import OrthoWalk
from OrthoDrive import OrthoDrive
import MazeGameGlobals
import MazeData
import MazeTreasure
import Trajectory
import Maze
import MinigameAvatarScorePanel
import MinigameGlobals

class DistributedMazeGame(DistributedMinigame):
    notify = directNotify.newCategory('DistributedMazeGame')
    CAMERA_TASK = 'MazeGameCameraTask'
    UPDATE_SUITS_TASK = 'MazeGameUpdateSuitsTask'
    TREASURE_GRAB_EVENT_NAME = 'MazeTreasureGrabbed'

    def __init__(self, cr):
        DistributedMinigame.__init__(self, cr)
        self.gameFSM = ClassicFSM.ClassicFSM('DistributedMazeGame', [State.State('off', self.enterOff, self.exitOff, ['play']),
         State.State('play', self.enterPlay, self.exitPlay, ['cleanup', 'showScores']),
         State.State('showScores', self.enterShowScores, self.exitShowScores, ['cleanup']),
         State.State('cleanup', self.enterCleanup, self.exitCleanup, [])], 'off', 'cleanup')
        self.addChildGameFSM(self.gameFSM)
        self.usesLookAround = 1

    def getTitle(self):
        return TTLocalizer.MazeGameTitle

    def getInstructions(self):
        return TTLocalizer.MazeGameInstructions

    def getMaxDuration(self):
        return MazeGameGlobals.GAME_DURATION

    def __defineConstants(self):
        self.TOON_SPEED = 8.0
        self.TOON_Z = 0
        self.MinSuitSpeedRange = [0.8 * self.TOON_SPEED, 0.6 * self.TOON_SPEED]
        self.MaxSuitSpeedRange = [1.1 * self.TOON_SPEED, 2.0 * self.TOON_SPEED]
        self.FASTER_SUIT_CURVE = 1
        self.SLOWER_SUIT_CURVE = self.getDifficulty() < 0.5
        self.slowerSuitPeriods = {2000: {4: [128, 76],
                8: [128,
                    99,
                    81,
                    68],
                12: [128,
                     108,
                     93,
                     82,
                     74,
                     67],
                16: [128,
                     112,
                     101,
                     91,
                     83,
                     76,
                     71,
                     66]},
         1000: {4: [110, 69],
                8: [110,
                    88,
                    73,
                    62],
                12: [110,
                     95,
                     83,
                     74,
                     67,
                     61],
                16: [110,
                     98,
                     89,
                     81,
                     75,
                     69,
                     64,
                     60]},
         5000: {4: [96, 63],
                8: [96,
                    79,
                    66,
                    57],
                12: [96,
                     84,
                     75,
                     67,
                     61,
                     56],
                16: [96,
                     87,
                     80,
                     73,
                     68,
                     63,
                     59,
                     55]},
         4000: {4: [86, 58],
                8: [86,
                    71,
                    61,
                    53],
                12: [86,
                     76,
                     68,
                     62,
                     56,
                     52],
                16: [86,
                     78,
                     72,
                     67,
                     62,
                     58,
                     54,
                     51]},
         3000: {4: [78, 54],
                8: [78,
                    65,
                    56,
                    49],
                12: [78,
                     69,
                     62,
                     57,
                     52,
                     48],
                16: [78,
                     71,
                     66,
                     61,
                     57,
                     54,
                     51,
                     48]},
         9000: {4: [71, 50],
                8: [71,
                    60,
                    52,
                    46],
                12: [71,
                     64,
                     58,
                     53,
                     49,
                     45],
                16: [71,
                     65,
                     61,
                     57,
                     53,
                     50,
                     47,
                     45]}}
        self.slowerSuitPeriodsCurve = {2000: {4: [128, 65],
                8: [128,
                    78,
                    66,
                    64],
                12: [128,
                     88,
                     73,
                     67,
                     64,
                     64],
                16: [128,
                     94,
                     79,
                     71,
                     67,
                     65,
                     64,
                     64]},
         1000: {4: [110, 59],
                8: [110,
                    70,
                    60,
                    58],
                12: [110,
                     78,
                     66,
                     61,
                     59,
                     58],
                16: [110,
                     84,
                     72,
                     65,
                     61,
                     59,
                     58,
                     58]},
         5000: {4: [96, 55],
                8: [96,
                    64,
                    56,
                    54],
                12: [96,
                     71,
                     61,
                     56,
                     54,
                     54],
                16: [96,
                     76,
                     65,
                     59,
                     56,
                     55,
                     54,
                     54]},
         4000: {4: [86, 51],
                8: [86,
                    59,
                    52,
                    50],
                12: [86,
                     65,
                     56,
                     52,
                     50,
                     50],
                16: [86,
                     69,
                     60,
                     55,
                     52,
                     51,
                     50,
                     50]},
         3000: {4: [78, 47],
                8: [78,
                    55,
                    48,
                    47],
                12: [78,
                     60,
                     52,
                     48,
                     47,
                     47],
                16: [78,
                     63,
                     55,
                     51,
                     49,
                     47,
                     47,
                     47]},
         9000: {4: [71, 44],
                8: [71,
                    51,
                    45,
                    44],
                12: [71,
                     55,
                     48,
                     45,
                     44,
                     44],
                16: [71,
                     58,
                     51,
                     48,
                     45,
                     44,
                     44,
                     44]}}
        self.fasterSuitPeriods = {2000: {4: [54, 42],
                8: [59,
                    52,
                    47,
                    42],
                12: [61,
                     56,
                     52,
                     48,
                     45,
                     42],
                16: [61,
                     58,
                     54,
                     51,
                     49,
                     46,
                     44,
                     42]},
         1000: {4: [50, 40],
                8: [55,
                    48,
                    44,
                    40],
                12: [56,
                     52,
                     48,
                     45,
                     42,
                     40],
                16: [56,
                     53,
                     50,
                     48,
                     45,
                     43,
                     41,
                     40]},
         5000: {4: [47, 37],
                8: [51,
                    45,
                    41,
                    37],
                12: [52,
                     48,
                     45,
                     42,
                     39,
                     37],
                16: [52,
                     49,
                     47,
                     44,
                     42,
                     40,
                     39,
                     37]},
         4000: {4: [44, 35],
                8: [47,
                    42,
                    38,
                    35],
                12: [48,
                     45,
                     42,
                     39,
                     37,
                     35],
                16: [49,
                     46,
                     44,
                     42,
                     40,
                     38,
                     37,
                     35]},
         3000: {4: [41, 33],
                8: [44,
                    40,
                    36,
                    33],
                12: [45,
                     42,
                     39,
                     37,
                     35,
                     33],
                16: [45,
                     43,
                     41,
                     39,
                     38,
                     36,
                     35,
                     33]},
         9000: {4: [39, 32],
                8: [41,
                    37,
                    34,
                    32],
                12: [42,
                     40,
                     37,
                     35,
                     33,
                     32],
                16: [43,
                     41,
                     39,
                     37,
                     35,
                     34,
                     33,
                     32]}}
        self.fasterSuitPeriodsCurve = {2000: {4: [62, 42],
                8: [63,
                    61,
                    54,
                    42],
                12: [63,
                     63,
                     61,
                     56,
                     50,
                     42],
                16: [63,
                     63,
                     62,
                     60,
                     57,
                     53,
                     48,
                     42]},
         1000: {4: [57, 40],
                8: [58,
                    56,
                    50,
                    40],
                12: [58,
                     58,
                     56,
                     52,
                     46,
                     40],
                16: [58,
                     58,
                     57,
                     56,
                     53,
                     49,
                     45,
                     40]},
         5000: {4: [53, 37],
                8: [54,
                    52,
                    46,
                    37],
                12: [54,
                     53,
                     52,
                     48,
                     43,
                     37],
                16: [54,
                     54,
                     53,
                     51,
                     49,
                     46,
                     42,
                     37]},
         4000: {4: [49, 35],
                8: [50,
                    48,
                    43,
                    35],
                12: [50,
                     49,
                     48,
                     45,
                     41,
                     35],
                16: [50,
                     50,
                     49,
                     48,
                     46,
                     43,
                     39,
                     35]},
         3000: {4: [46, 33],
                8: [47,
                    45,
                    41,
                    33],
                12: [47,
                     46,
                     45,
                     42,
                     38,
                     33],
                16: [47,
                     46,
                     46,
                     45,
                     43,
                     40,
                     37,
                     33]},
         9000: {4: [43, 32],
                8: [44,
                    42,
                    38,
                    32],
                12: [44,
                     43,
                     42,
                     40,
                     36,
                     32],
                16: [44,
                     44,
                     43,
                     42,
                     40,
                     38,
                     35,
                     32]}}
        self.CELL_WIDTH = MazeData.CELL_WIDTH
        self.MAX_FRAME_MOVE = self.CELL_WIDTH / 2
        startOffset = 3
        self.startPosHTable = [[Point3(0, startOffset, self.TOON_Z), 0],
         [Point3(0, -startOffset, self.TOON_Z), 180],
         [Point3(startOffset, 0, self.TOON_Z), 270],
         [Point3(-startOffset, 0, self.TOON_Z), 90]]
        self.camOffset = Vec3(0, -19, 45)

    def load(self):
        self.notify.debug('load')
        DistributedMinigame.load(self)
        self.__defineConstants()
        mazeName = MazeGameGlobals.getMazeName(self.doId, self.numPlayers, MazeData.mazeNames)
        self.maze = Maze.Maze(mazeName)
        model = loader.loadModel('phase_3.5/models/props/mickeySZ')
        self.treasureModel = model.find('**/mickeySZ')
        model.removeNode()
        self.treasureModel.setScale(1.6)
        self.treasureModel.setP(-90)
        self.music = base.loadMusic('phase_4/audio/bgm/MG_toontag.mid')
        self.toonHitTracks = {}
        self.scorePanels = []

    def unload(self):
        self.notify.debug('unload')
        DistributedMinigame.unload(self)
        del self.toonHitTracks
        self.maze.destroy()
        del self.maze
        self.treasureModel.removeNode()
        del self.treasureModel
        del self.music
        self.removeChildGameFSM(self.gameFSM)
        del self.gameFSM

    def onstage(self):
        self.notify.debug('onstage')
        DistributedMinigame.onstage(self)
        self.maze.onstage()
        self.randomNumGen.shuffle(self.startPosHTable)
        lt = base.localAvatar
        lt.reparentTo(render)
        lt.hideName()
        self.__placeToon(self.localAvId)
        lt.setAnimState('Happy', 1.0)
        lt.setSpeed(0, 0)
        self.camParent = render.attachNewNode('mazeGameCamParent')
        self.camParent.reparentTo(base.localAvatar)
        self.camParent.setPos(0, 0, 0)
        self.camParent.setHpr(render, 0, 0, 0)
        camera.reparentTo(self.camParent)
        camera.setPos(self.camOffset)
        self.__spawnCameraTask()
        self.toonRNGs = []
        for i in xrange(self.numPlayers):
            self.toonRNGs.append(RandomNumGen.RandomNumGen(self.randomNumGen))

        self.treasures = []
        for i in xrange(self.maze.numTreasures):
            self.treasures.append(MazeTreasure.MazeTreasure(self.treasureModel, self.maze.treasurePosList[i], i, self.doId))

        self.__loadSuits()
        for suit in self.suits:
            suit.onstage()

        self.sndTable = {'hitBySuit': [None] * self.numPlayers,
         'falling': [None] * self.numPlayers}
        for i in xrange(self.numPlayers):
            self.sndTable['hitBySuit'][i] = base.loadSfx('phase_4/audio/sfx/MG_Tag_C.mp3')
            self.sndTable['falling'][i] = base.loadSfx('phase_4/audio/sfx/MG_cannon_whizz.mp3')

        self.grabSounds = []
        for i in xrange(5):
            self.grabSounds.append(base.loadSfx('phase_4/audio/sfx/MG_maze_pickup.mp3'))

        self.grabSoundIndex = 0
        for avId in self.avIdList:
            self.toonHitTracks[avId] = Wait(0.1)

        self.scores = [0] * self.numPlayers
        self.goalBar = DirectWaitBar(parent=render2d, relief=DGG.SUNKEN, frameSize=(-0.35,
         0.35,
         -0.15,
         0.15), borderWidth=(0.02, 0.02), scale=0.42, pos=(0.84, 0, 0.5 - 0.28 * self.numPlayers + 0.05), barColor=(0, 0.7, 0, 1))
        self.goalBar.setBin('unsorted', 0)
        self.goalBar.hide()
        self.introTrack = self.getIntroTrack()
        self.introTrack.start()
        return

    def offstage(self):
        self.notify.debug('offstage')
        if self.introTrack.isPlaying():
            self.introTrack.finish()
        del self.introTrack
        for avId in self.toonHitTracks.keys():
            track = self.toonHitTracks[avId]
            if track.isPlaying():
                track.finish()

        self.__killCameraTask()
        camera.wrtReparentTo(render)
        self.camParent.removeNode()
        del self.camParent
        for panel in self.scorePanels:
            panel.cleanup()

        self.scorePanels = []
        self.goalBar.destroy()
        del self.goalBar
        base.setCellsAvailable(base.rightCells, 1)
        for suit in self.suits:
            suit.offstage()

        self.__unloadSuits()
        for treasure in self.treasures:
            treasure.destroy()

        del self.treasures
        del self.sndTable
        del self.grabSounds
        del self.toonRNGs
        self.maze.offstage()
        base.localAvatar.showName()
        DistributedMinigame.offstage(self)

    def __placeToon(self, avId):
        toon = self.getAvatar(avId)
        if self.numPlayers == 1:
            toon.setPos(0, 0, self.TOON_Z)
            toon.setHpr(180, 0, 0)
        else:
            posIndex = self.avIdList.index(avId)
            toon.setPos(self.startPosHTable[posIndex][0])
            toon.setHpr(self.startPosHTable[posIndex][1], 0, 0)

    def setGameReady(self):
        if not self.hasLocalToon:
            return
        self.notify.debug('setGameReady')
        if DistributedMinigame.setGameReady(self):
            return
        for avId in self.remoteAvIdList:
            toon = self.getAvatar(avId)
            if toon:
                toon.reparentTo(render)
                self.__placeToon(avId)
                toon.setAnimState('Happy', 1.0)
                toon.startSmooth()
                toon.startLookAround()

    def setGameStart(self, timestamp):
        if not self.hasLocalToon:
            return
        self.notify.debug('setGameStart')
        DistributedMinigame.setGameStart(self, timestamp)
        if self.introTrack.isPlaying():
            self.introTrack.finish()
        for avId in self.remoteAvIdList:
            toon = self.getAvatar(avId)
            if toon:
                toon.stopLookAround()

        self.gameFSM.request('play')

    def handleDisabledAvatar(self, avId):
        hitTrack = self.toonHitTracks[avId]
        if hitTrack.isPlaying():
            hitTrack.finish()
        DistributedMinigame.handleDisabledAvatar(self, avId)

    def enterOff(self):
        self.notify.debug('enterOff')

    def exitOff(self):
        pass

    def enterPlay(self):
        self.notify.debug('enterPlay')
        for i in xrange(self.numPlayers):
            avId = self.avIdList[i]
            avName = self.getAvatarName(avId)
            scorePanel = MinigameAvatarScorePanel.MinigameAvatarScorePanel(avId, avName)
            scorePanel.setPos(1.12, 0.0, 0.5 - 0.28 * i)
            self.scorePanels.append(scorePanel)

        self.goalBar.show()
        self.goalBar['value'] = 0.0
        base.setCellsAvailable(base.rightCells, 0)
        self.__spawnUpdateSuitsTask()
        orthoDrive = OrthoDrive(self.TOON_SPEED, maxFrameMove=self.MAX_FRAME_MOVE, customCollisionCallback=self.__doMazeCollisions, priority=1)
        self.orthoWalk = OrthoWalk(orthoDrive, broadcast=not self.isSinglePlayer())
        self.orthoWalk.start()
        self.accept(MazeSuit.COLLISION_EVENT_NAME, self.__hitBySuit)
        self.accept(self.TREASURE_GRAB_EVENT_NAME, self.__treasureGrabbed)
        self.timer = ToontownTimer.ToontownTimer()
        self.timer.posInTopRightCorner()
        self.timer.setTime(MazeGameGlobals.GAME_DURATION)
        self.timer.countdown(MazeGameGlobals.GAME_DURATION, self.timerExpired)
        self.accept('resetClock', self.__resetClock)
        base.playMusic(self.music, looping=0, volume=0.8)

    def exitPlay(self):
        self.notify.debug('exitPlay')
        self.ignore('resetClock')
        self.ignore(MazeSuit.COLLISION_EVENT_NAME)
        self.ignore(self.TREASURE_GRAB_EVENT_NAME)
        self.orthoWalk.stop()
        self.orthoWalk.destroy()
        del self.orthoWalk
        self.__killUpdateSuitsTask()
        self.timer.stop()
        self.timer.destroy()
        del self.timer
        for avId in self.avIdList:
            toon = self.getAvatar(avId)
            if toon:
                toon.loop('neutral')

    def __resetClock(self, tOffset):
        self.notify.debug('resetClock')
        self.gameStartTime += tOffset
        self.timer.countdown(self.timer.currentTime + tOffset, self.timerExpired)

    def __treasureGrabbed(self, treasureNum):
        self.treasures[treasureNum].showGrab()
        self.grabSounds[self.grabSoundIndex].play()
        self.grabSoundIndex = (self.grabSoundIndex + 1) % len(self.grabSounds)
        self.sendUpdate('claimTreasure', [treasureNum])

    def setTreasureGrabbed(self, avId, treasureNum):
        if not self.hasLocalToon:
            return
        if avId != self.localAvId:
            self.treasures[treasureNum].showGrab()
        i = self.avIdList.index(avId)
        self.scores[i] += 1
        self.scorePanels[i].setScore(self.scores[i])
        total = 0
        for score in self.scores:
            total += score

        self.goalBar['value'] = 100.0 * (float(total) / float(self.maze.numTreasures))

    def __hitBySuit(self, suitNum):
        self.notify.debug('hitBySuit')
        timestamp = globalClockDelta.localToNetworkTime(globalClock.getFrameTime())
        self.sendUpdate('hitBySuit', [self.localAvId, timestamp])
        self.__showToonHitBySuit(self.localAvId, timestamp)

    def hitBySuit(self, avId, timestamp):
        if not self.hasLocalToon:
            return
        if self.gameFSM.getCurrentState().getName() not in ['play', 'showScores']:
            self.notify.warning('ignoring msg: av %s hit by suit' % avId)
            return
        self.notify.debug('avatar ' + `avId` + ' hit by a suit')
        if avId != self.localAvId:
            self.__showToonHitBySuit(avId, timestamp)

    def __showToonHitBySuit(self, avId, timestamp):
        toon = self.getAvatar(avId)
        if toon == None:
            return
        rng = self.toonRNGs[self.avIdList.index(avId)]
        curPos = toon.getPos(render)
        oldTrack = self.toonHitTracks[avId]
        if oldTrack.isPlaying():
            oldTrack.finish()
        toon.setPos(curPos)
        toon.setZ(self.TOON_Z)
        parentNode = render.attachNewNode('mazeFlyToonParent-' + `avId`)
        parentNode.setPos(toon.getPos())
        toon.reparentTo(parentNode)
        toon.setPos(0,0,0)
        startPos = parentNode.getPos()
        dropShadow = toon.dropShadow.copyTo(parentNode)
        dropShadow.setScale(toon.dropShadow.getScale(render))
        trajectory = Trajectory.Trajectory(
            0,
            Point3(0,0,0),
            Point3(0,0,50),
            gravMult=1.0)
        flyDur = trajectory.calcTimeOfImpactOnPlane(0.0)
        while 1:
            endTile = [rng.randint(2, self.maze.width-1), rng.randint(2, self.maze.height-1)]
            if self.maze.isWalkable(endTile[0], endTile[1]):
                break
        endWorldCoords = self.maze.tile2world(endTile[0], endTile[1])
        endPos = Point3(endWorldCoords[0], endWorldCoords[1], startPos[2])
        def flyFunc(t, trajectory, startPos = startPos, endPos = endPos, dur = flyDur, moveNode = parentNode, flyNode = toon):
            u = t/dur
            moveNode.setX(startPos[0] + u * (endPos[0]-startPos[0]))
            moveNode.setY(startPos[1] + u * (endPos[1]-startPos[1]))
            flyNode.setPos(trajectory.getPos(t))
        flyTrack = Sequence(
            LerpFunctionInterval(flyFunc, fromData=0.0, toData=flyDur, duration=flyDur, extraArgs=[trajectory]),
            name=toon.uniqueName('hitBySuit-fly'))
        if avId != self.localAvId:
            cameraTrack = Sequence()
        else:
            self.camParent.reparentTo(parentNode)
            startCamPos = camera.getPos()
            destCamPos = camera.getPos()
            zenith = trajectory.getPos(flyDur/2.0)[2]
            destCamPos.setZ(zenith*1.3)
            destCamPos.setY(destCamPos[1]*0.3)
            def camTask(task, zenith = zenith, flyNode = toon, startCamPos = startCamPos, camOffset = destCamPos - startCamPos):
                u = flyNode.getZ()/zenith
                camera.setPos(startCamPos + camOffset*u)
                camera.lookAt(toon)
                return Task.cont
            camTaskName = 'mazeToonFlyCam-' + `avId`
            taskMgr.add(camTask, camTaskName, priority=20)
            def cleanupCamTask(self = self, toon = toon, camTaskName = camTaskName, startCamPos = startCamPos):
                taskMgr.remove(camTaskName)
                self.camParent.reparentTo(toon)
                camera.setPos(startCamPos)
                camera.lookAt(toon)

            cameraTrack = Sequence(
                Wait(flyDur),
                Func(cleanupCamTask),
                name='hitBySuit-cameraLerp')

        geomNode = toon.getGeomNode()
        startHpr = geomNode.getHpr()
        destHpr = Point3(startHpr)
        hRot = rng.randrange(1, 8)
        if rng.choice([0, 1]):
            hRot = -hRot
        destHpr.setX(destHpr[0] + hRot*360)
        spinHTrack = Sequence(
            LerpHprInterval(geomNode, flyDur, destHpr, startHpr=startHpr),
            Func(geomNode.setHpr, startHpr),
            name=toon.uniqueName('hitBySuit-spinH'))
        parent = geomNode.getParent()
        rotNode = parent.attachNewNode('rotNode')
        geomNode.reparentTo(rotNode)
        rotNode.setZ(toon.getHeight()/2.0)
        oldGeomNodeZ = geomNode.getZ()
        geomNode.setZ(-toon.getHeight()/2.0)
        startHpr = rotNode.getHpr()
        destHpr = Point3(startHpr)
        pRot = rng.randrange(1,3)
        if rng.choice([0, 1]):
            pRot = -pRot
        destHpr.setY(destHpr[1] + pRot*360)
        spinPTrack = Sequence(
            LerpHprInterval(rotNode, flyDur, destHpr, startHpr=startHpr),
            Func(rotNode.setHpr, startHpr),
            name=toon.uniqueName('hitBySuit-spinP'))
        i = self.avIdList.index(avId)
        soundTrack = Sequence(
            Func(base.playSfx, self.sndTable['hitBySuit'][i]),
            Wait(flyDur * (2.0/3.0)),
            SoundInterval(self.sndTable['falling'][i],
                          duration=flyDur * (1.0/3.0)),
            name=toon.uniqueName('hitBySuit-soundTrack'))

        def preFunc(self = self, avId = avId, toon = toon, dropShadow = dropShadow):
            forwardSpeed = toon.forwardSpeed
            rotateSpeed = toon.rotateSpeed
            if avId == self.localAvId:
                self.orthoWalk.stop()
            else:
                toon.stopSmooth()
            if forwardSpeed or rotateSpeed:
                toon.setSpeed(forwardSpeed, rotateSpeed)
            toon.dropShadow.hide()

        def postFunc(self = self, avId = avId, oldGeomNodeZ = oldGeomNodeZ, dropShadow = dropShadow, parentNode = parentNode):
            if avId == self.localAvId:
                base.localAvatar.setPos(endPos)
                if hasattr(self, 'orthoWalk'):
                    if self.gameFSM.getCurrentState().getName() == 'play':
                        self.orthoWalk.start()
            dropShadow.removeNode()
            del dropShadow
            toon.dropShadow.show()
            geomNode = toon.getGeomNode()
            rotNode = geomNode.getParent()
            baseNode = rotNode.getParent()
            geomNode.reparentTo(baseNode)
            rotNode.removeNode()
            del rotNode
            geomNode.setZ(oldGeomNodeZ)
            toon.reparentTo(render)
            toon.setPos(endPos)
            parentNode.removeNode()
            del parentNode
            if avId != self.localAvId:
                toon.startSmooth()

        preFunc()

        hitTrack = Sequence(Parallel(flyTrack, cameraTrack,
                                     spinHTrack, spinPTrack, soundTrack),
                            Func(postFunc),
                            name=toon.uniqueName('hitBySuit'))

        self.toonHitTracks[avId] = hitTrack

        hitTrack.start(globalClockDelta.localElapsedTime(timestamp))

    def allTreasuresTaken(self):
        if not self.hasLocalToon:
            return
        self.notify.debug('all treasures taken')
        if not MazeGameGlobals.ENDLESS_GAME:
            self.gameFSM.request('showScores')

    def timerExpired(self):
        self.notify.debug('local timer expired')
        if not MazeGameGlobals.ENDLESS_GAME:
            self.gameFSM.request('showScores')

    def __doMazeCollisions(self, oldPos, newPos):
        offset = newPos - oldPos
        WALL_OFFSET = 1.0
        curX = oldPos[0]
        curY = oldPos[1]
        curTX, curTY = self.maze.world2tile(curX, curY)

        def calcFlushCoord(curTile, newTile, centerTile):
            EPSILON = 0.01
            if newTile > curTile:
                return (newTile - centerTile) * self.CELL_WIDTH - EPSILON - WALL_OFFSET
            else:
                return (curTile - centerTile) * self.CELL_WIDTH + WALL_OFFSET

        offsetX = offset[0]
        offsetY = offset[1]
        WALL_OFFSET_X = WALL_OFFSET
        if offsetX < 0:
            WALL_OFFSET_X = -WALL_OFFSET_X
        WALL_OFFSET_Y = WALL_OFFSET
        if offsetY < 0:
            WALL_OFFSET_Y = -WALL_OFFSET_Y
        newX = curX + offsetX + WALL_OFFSET_X
        newY = curY
        newTX, newTY = self.maze.world2tile(newX, newY)
        if newTX != curTX:
            if self.maze.collisionTable[newTY][newTX]:
                offset.setX(calcFlushCoord(curTX, newTX, self.maze.originTX) - curX)
        newX = curX
        newY = curY + offsetY + WALL_OFFSET_Y
        newTX, newTY = self.maze.world2tile(newX, newY)
        if newTY != curTY:
            if self.maze.collisionTable[newTY][newTX]:
                offset.setY(calcFlushCoord(curTY, newTY, self.maze.originTY) - curY)
        offsetX = offset[0]
        offsetY = offset[1]
        newX = curX + offsetX + WALL_OFFSET_X
        newY = curY + offsetY + WALL_OFFSET_Y
        newTX, newTY = self.maze.world2tile(newX, newY)
        if self.maze.collisionTable[newTY][newTX]:
            cX = calcFlushCoord(curTX, newTX, self.maze.originTX)
            cY = calcFlushCoord(curTY, newTY, self.maze.originTY)
            if abs(cX - curX) < abs(cY - curY):
                offset.setX(cX - curX)
            else:
                offset.setY(cY - curY)
        return oldPos + offset

    def __spawnCameraTask(self):
        self.notify.debug('spawnCameraTask')
        camera.lookAt(base.localAvatar)
        taskMgr.remove(self.CAMERA_TASK)
        taskMgr.add(self.__cameraTask, self.CAMERA_TASK, priority=45)

    def __killCameraTask(self):
        self.notify.debug('killCameraTask')
        taskMgr.remove(self.CAMERA_TASK)

    def __cameraTask(self, task):
        self.camParent.setHpr(render, 0, 0, 0)
        return Task.cont

    def __loadSuits(self):
        self.notify.debug('loadSuits')
        self.suits = []
        self.numSuits = 4 * self.numPlayers
        safeZone = self.getSafezoneId()
        slowerTable = self.slowerSuitPeriods
        if self.SLOWER_SUIT_CURVE:
            slowerTable = self.slowerSuitPeriodsCurve
        slowerPeriods = slowerTable[safeZone][self.numSuits]
        fasterTable = self.fasterSuitPeriods
        if self.FASTER_SUIT_CURVE:
            fasterTable = self.fasterSuitPeriodsCurve
        fasterPeriods = fasterTable[safeZone][self.numSuits]
        suitPeriods = slowerPeriods + fasterPeriods
        self.notify.debug('suit periods: ' + `suitPeriods`)
        self.randomNumGen.shuffle(suitPeriods)
        for i in xrange(self.numSuits):
            self.suits.append(MazeSuit(i, self.maze, self.randomNumGen, suitPeriods[i], self.getDifficulty()))

    def __unloadSuits(self):
        self.notify.debug('unloadSuits')
        for suit in self.suits:
            suit.destroy()

        del self.suits

    def __spawnUpdateSuitsTask(self):
        self.notify.debug('spawnUpdateSuitsTask')
        for suit in self.suits:
            suit.gameStart(self.gameStartTime)

        taskMgr.remove(self.UPDATE_SUITS_TASK)
        taskMgr.add(self.__updateSuitsTask, self.UPDATE_SUITS_TASK)

    def __killUpdateSuitsTask(self):
        self.notify.debug('killUpdateSuitsTask')
        taskMgr.remove(self.UPDATE_SUITS_TASK)
        for suit in self.suits:
            suit.gameEnd()

    def __updateSuitsTask(self, task):
        curT = globalClock.getFrameTime() - self.gameStartTime
        curTic = int(curT * float(MazeGameGlobals.SUIT_TIC_FREQ))
        suitUpdates = []
        for i in xrange(len(self.suits)):
            updateTics = self.suits[i].getThinkTimestampTics(curTic)
            suitUpdates.extend(zip(updateTics, [i] * len(updateTics)))

        suitUpdates.sort(lambda a, b: a[0] - b[0])
        if len(suitUpdates) > 0:
            curTic = 0
            for i in xrange(len(suitUpdates)):
                update = suitUpdates[i]
                tic = update[0]
                suitIndex = update[1]
                suit = self.suits[suitIndex]
                if tic > curTic:
                    curTic = tic
                    j = i + 1
                    while j < len(suitUpdates):
                        if suitUpdates[j][0] > tic:
                            break
                        self.suits[suitUpdates[j][1]].prepareToThink()
                        j += 1

                unwalkables = []
                for si in xrange(suitIndex):
                    unwalkables.extend(self.suits[si].occupiedTiles)

                for si in xrange(suitIndex + 1, len(self.suits)):
                    unwalkables.extend(self.suits[si].occupiedTiles)

                suit.think(curTic, curT, unwalkables)

        return Task.cont

    def enterShowScores(self):
        self.notify.debug('enterShowScores')
        lerpTrack = Parallel()
        lerpDur = 0.5
        lerpTrack.append(Parallel(LerpPosInterval(self.goalBar, lerpDur, Point3(0, 0, -.6), blendType='easeInOut'), LerpScaleInterval(self.goalBar, lerpDur, Vec3(self.goalBar.getScale()) * 2.0, blendType='easeInOut')))
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
        for i in xrange(self.numPlayers):
            panel = self.scorePanels[i]
            pos = scorePanelLocs[i]
            lerpTrack.append(Parallel(LerpPosInterval(panel, lerpDur, Point3(pos[0], 0, pos[1]), blendType='easeInOut'), LerpScaleInterval(panel, lerpDur, Vec3(panel.getScale()) * 2.0, blendType='easeInOut')))

        self.showScoreTrack = Parallel(lerpTrack, Sequence(Wait(MazeGameGlobals.SHOWSCORES_DURATION), Func(self.gameOver)))
        self.showScoreTrack.start()

    def exitShowScores(self):
        self.showScoreTrack.pause()
        del self.showScoreTrack

    def enterCleanup(self):
        self.notify.debug('enterCleanup')

    def exitCleanup(self):
        pass

    def getIntroTrack(self):
        self.__cameraTask(None)
        origCamParent = camera.getParent()
        origCamPos = camera.getPos()
        origCamHpr = camera.getHpr()
        iCamParent = base.localAvatar.attachNewNode('iCamParent')
        iCamParent.setH(180)
        camera.reparentTo(iCamParent)
        toonHeight = base.localAvatar.getHeight()
        camera.setPos(0, -15, toonHeight * 3)
        camera.lookAt(0, 0, toonHeight / 2.0)
        iCamParent.wrtReparentTo(origCamParent)
        waitDur = 5.0
        lerpDur = 4.5
        lerpTrack = Parallel()
        startHpr = iCamParent.getHpr()
        startHpr.setX(PythonUtil.reduceAngle(startHpr[0]))
        lerpTrack.append(LerpPosHprInterval(iCamParent, lerpDur, pos=Point3(0, 0, 0), hpr=Point3(0, 0, 0), startHpr=startHpr, name=self.uniqueName('introLerpParent')))
        lerpTrack.append(LerpPosHprInterval(camera, lerpDur, pos=origCamPos, hpr=origCamHpr, blendType='easeInOut', name=self.uniqueName('introLerpCameraPos')))
        base.localAvatar.startLookAround()

        def cleanup(origCamParent = origCamParent, origCamPos = origCamPos, origCamHpr = origCamHpr, iCamParent = iCamParent):
            camera.reparentTo(origCamParent)
            camera.setPos(origCamPos)
            camera.setHpr(origCamHpr)
            iCamParent.removeNode()
            del iCamParent
            base.localAvatar.stopLookAround()

        return Sequence(Wait(waitDur),
                        lerpTrack,
                        Func(cleanup))
