from pandac.PandaModules import Point3, CollisionSphere, CollisionNode
from direct.showbase.DirectObject import DirectObject
from direct.showbase.PythonUtil import Functor
from direct.showbase.RandomNumGen import RandomNumGen
from direct.task.Task import Task
from toontown.minigame.MazeSuit import MazeSuit
from .CogdoGameGatherable import CogdoMemo
from .CogdoMazePlayer import CogdoMazePlayer
from .CogdoMazeLocalPlayer import CogdoMazeLocalPlayer
from .CogdoMazeGuiManager import CogdoMazeGuiManager
from .CogdoGameAudioManager import CogdoGameAudioManager
from .CogdoMazeGameObjects import CogdoMazeExit, CogdoMazeDrop
from .CogdoMazeSuits import CogdoMazeSuit, CogdoMazeSlowMinionSuit, CogdoMazeFastMinionSuit, CogdoMazeBossSuit
from .CogdoMazeGameMovies import CogdoMazeGameIntro, CogdoMazeGameFinish
from . import CogdoMazeGameGlobals as Globals
from . import CogdoUtil
import math
import random

class CogdoMazeGame(DirectObject):
    notify = directNotify.newCategory('CogdoMazeGame')
    UpdateTaskName = 'CogdoMazeGameUpdateTask'
    RemoveGagTaskName = 'CogdoMazeGameRemoveGag'
    PlayerCoolerCollision = '%s-into-%s' % (Globals.LocalPlayerCollisionName, Globals.WaterCoolerCollisionName)
    PlayerDropCollision = '%s-into-%s' % (Globals.LocalPlayerCollisionName, Globals.DropCollisionName)

    def __init__(self, distGame):
        self.distGame = distGame
        self._allowSuitsHitToons = base.config.GetBool('cogdomaze-suits-hit-toons', True)

    def load(self, cogdoMazeFactory, numSuits, bossCode):
        self._initAudio()
        self.maze = cogdoMazeFactory.createCogdoMaze()
        suitSpawnSpot = self.maze.createRandomSpotsList(numSuits, self.distGame.randomNumGen)
        self.guiMgr = CogdoMazeGuiManager(self.maze, bossCode)
        self.suits = []
        self.suitsById = {}
        self.shakers = []
        self.toonsThatRevealedDoor = []
        self.quake = 0
        self.dropCounter = 0
        self.drops = {}
        self.gagCounter = 0
        self.gags = []
        self.hackTemp = False
        self.dropGen = RandomNumGen(self.distGame.doId)
        self.gagTimeoutTasks = []
        self.finished = False
        self.lastBalloonTimestamp = None
        difficulty = self.distGame.getDifficulty()
        serialNum = 0
        for i in range(numSuits[0]):
            suitRng = RandomNumGen(self.distGame.doId + serialNum * 10)
            suit = CogdoMazeBossSuit(serialNum, self.maze, suitRng, difficulty, startTile=suitSpawnSpot[0][i])
            self.addSuit(suit)
            self.guiMgr.mazeMapGui.addSuit(suit.suit)
            serialNum += 1

        for i in range(numSuits[1]):
            suitRng = RandomNumGen(self.distGame.doId + serialNum * 10)
            suit = CogdoMazeFastMinionSuit(serialNum, self.maze, suitRng, difficulty, startTile=suitSpawnSpot[1][i])
            self.addSuit(suit)
            serialNum += 1

        for i in range(numSuits[2]):
            suitRng = RandomNumGen(self.distGame.doId + serialNum * 10)
            suit = CogdoMazeSlowMinionSuit(serialNum, self.maze, suitRng, difficulty, startTile=suitSpawnSpot[2][i])
            self.addSuit(suit)
            serialNum += 1

        self.toonId2Door = {}
        self.keyIdToKey = {}
        self.players = []
        self.toonId2Player = {}
        cellPos = (int(self.maze.width / 2), self.maze.height - 1)
        pos = self.maze.tile2world(*cellPos)
        self._exit = CogdoMazeExit()
        self._exit.reparentTo(render)
        self._exit.setPos(self.maze.exitPos)
        self._exit.stash()
        self.guiMgr.mazeMapGui.placeExit(*cellPos)
        self._collNode2waterCooler = {}
        for waterCooler in self.maze.getWaterCoolers():
            pos = waterCooler.getPos(render)
            tpos = self.maze.world2tile(pos[0], pos[1])
            self.guiMgr.mazeMapGui.addWaterCooler(*tpos)
            self._collNode2waterCooler[waterCooler.collNode] = waterCooler

        self.pickups = []
        self.gagModel = CogdoUtil.loadMazeModel('waterBalloon')
        self._movie = CogdoMazeGameIntro(self.maze, self._exit, self.distGame.randomNumGen)
        self._movie.load()
        return

    def _initAudio(self):
        self._audioMgr = CogdoGameAudioManager(Globals.MusicFiles, Globals.SfxFiles, camera, cutoff=Globals.AudioCutoff)
        self._quakeSfx1 = self._audioMgr.createSfx('quake')
        self._quakeSfx2 = self._audioMgr.createSfx('quake')

    def _destroyAudio(self):
        self._quakeSfx1.destroy()
        self._quakeSfx2.destroy()
        del self._quakeSfx1
        del self._quakeSfx2
        self._audioMgr.destroy()
        del self._audioMgr

    def addSuit(self, suit):
        id = suit.serialNum
        self.suits.append(suit)
        if suit.type == Globals.SuitTypes.Boss:
            self.shakers.append(suit)
        self.suitsById[id] = suit

    def removeSuit(self, suit):
        id = suit.serialNum
        del self.suitsById[id]
        if suit.type == Globals.SuitTypes.Boss:
            self.shakers.remove(suit)
            self.guiMgr.showBossCode(id)
            self.guiMgr.mazeMapGui.removeSuit(suit.suit)
        self.suits.remove(suit)
        suit.destroy()

    def unload(self):
        self.toonsThatRevealedDoor = []
        for suit in self.suits:
            suit.destroy()

        del self.suits
        for id in list(self.drops.keys()):
            self.cleanupDrop(id)

        self.__stopUpdateTask()
        self.ignoreAll()
        self.maze.destroy()
        del self.maze
        self._exit.destroy()
        del self._exit
        self.guiMgr.destroy()
        del self.guiMgr
        for player in self.players:
            player.destroy()

        del self.players
        del self.toonId2Player
        del self.localPlayer
        for pickup in self.pickups:
            pickup.destroy()

        self._destroyAudio()
        del self.distGame

    def onstage(self):
        self._exit.onstage()
        self.maze.onstage()

    def offstage(self):
        self.maze.offstage()
        self._exit.offstage()
        for suit in self.suits:
            suit.offstage()

    def startIntro(self):
        self._movie.play()
        self._audioMgr.playMusic('normal')

    def endIntro(self):
        self._movie.end()
        self._movie.unload()
        del self._movie
        for player in self.players:
            self.placePlayer(player)
            if player.toon is localAvatar:
                localAvatar.sendCurrentPosition()
            player.request('Ready')

    def startFinish(self):
        self._movie = CogdoMazeGameFinish(self.localPlayer, self._exit)
        self._movie.load()
        self._movie.play()

    def endFinish(self):
        self._movie.end()
        self._movie.unload()
        del self._movie

    def placeEntranceElevator(self, elevator):
        pos = self.maze.elevatorPos
        elevator.setPos(pos)
        tpos = self.maze.world2tile(pos[0], pos[1])
        self.guiMgr.mazeMapGui.placeEntrance(*tpos)

    def initPlayers(self):
        for toonId in self.distGame.getToonIds():
            toon = self.distGame.getToon(toonId)
            if toon is not None:
                if toon.isLocal():
                    player = CogdoMazeLocalPlayer(len(self.players), base.localAvatar, self, self.guiMgr)
                    self.localPlayer = player
                else:
                    player = CogdoMazePlayer(len(self.players), toon)
                self._addPlayer(player)

        return

    def start(self):
        self.accept(self.PlayerDropCollision, self.handleLocalToonMeetsDrop)
        self.accept(self.PlayerCoolerCollision, self.handleLocalToonMeetsWaterCooler)
        self.accept(CogdoMazeExit.EnterEventName, self.handleLocalToonEntersDoor)
        self.accept(CogdoMemo.EnterEventName, self.handleLocalToonMeetsPickup)
        if self._allowSuitsHitToons:
            self.accept(CogdoMazeSuit.COLLISION_EVENT_NAME, self.handleLocalToonMeetsSuit)
        self.accept(CogdoMazePlayer.GagHitEventName, self.handleToonMeetsGag)
        self.accept(CogdoMazeSuit.GagHitEventName, self.handleLocalSuitMeetsGag)
        self.accept(CogdoMazeSuit.DeathEventName, self.handleSuitDeath)
        self.accept(CogdoMazeSuit.ThinkEventName, self.handleSuitThink)
        self.accept(CogdoMazeBossSuit.ShakeEventName, self.handleBossShake)
        self.accept(CogdoMazePlayer.RemovedEventName, self._removePlayer)
        self.__startUpdateTask()
        for player in self.players:
            player.handleGameStart()
            player.request('Normal')

        for suit in self.suits:
            suit.onstage()
            suit.gameStart(self.distGame.getStartTime())

    def exit(self):
        self._quakeSfx1.stop()
        self._quakeSfx2.stop()
        for suit in self.suits:
            suit.gameEnd()

        self.ignore(self.PlayerDropCollision)
        self.ignore(self.PlayerCoolerCollision)
        self.ignore(CogdoMazeExit.EnterEventName)
        self.ignore(CogdoMemo.EnterEventName)
        self.ignore(CogdoMazeSuit.COLLISION_EVENT_NAME)
        self.ignore(CogdoMazePlayer.GagHitEventName)
        self.ignore(CogdoMazeSuit.GagHitEventName)
        self.ignore(CogdoMazeSuit.DeathEventName)
        self.ignore(CogdoMazeSuit.ThinkEventName)
        self.ignore(CogdoMazeBossSuit.ShakeEventName)
        self.ignore(CogdoMazePlayer.RemovedEventName)
        self.__stopUpdateTask()
        for timeoutTask in self.gagTimeoutTasks:
            taskMgr.remove(timeoutTask)

        self.finished = True
        self.localPlayer.handleGameExit()
        for player in self.players:
            player.request('Done')

        self.guiMgr.hideTimer()
        self.guiMgr.hideMazeMap()
        self.guiMgr.hideBossGui()

    def _addPlayer(self, player):
        self.players.append(player)
        self.toonId2Player[player.toon.doId] = player

    def _removePlayer(self, player):
        if player in self.players:
            self.players.remove(player)
        else:
            for cPlayer in self.players:
                if cPlayer.toon == player.toon:
                    self.players.remove(cPlayer)
                    break

        if player.toon.doId in self.toonId2Player:
            del self.toonId2Player[player.toon.doId]
        self.guiMgr.mazeMapGui.removeToon(player.toon)

    def handleToonLeft(self, toonId):
        self._removePlayer(self.toonId2Player[toonId])

    def __startUpdateTask(self):
        self.__stopUpdateTask()
        taskMgr.add(self.__updateTask, CogdoMazeGame.UpdateTaskName, 45)

    def __stopUpdateTask(self):
        taskMgr.remove(CogdoMazeGame.UpdateTaskName)
        taskMgr.remove('loopSecondQuakeSound')

    def __updateTask(self, task):
        dt = globalClock.getDt()
        self.localPlayer.update(dt)
        for player in self.players:
            curTX, curTY = self.maze.world2tileClipped(player.toon.getX(), player.toon.getY())
            self.guiMgr.mazeMapGui.updateToon(player.toon, curTX, curTY)

        self.__updateGags()
        if Globals.QuakeSfxEnabled:
            self.__updateQuakeSound()
        for pickup in self.pickups:
            pickup.update(dt)

        MazeSuit.thinkSuits(self.suits, self.distGame.getStartTime())
        return Task.cont

    def __updateGags(self):
        remove = []
        for i in range(len(self.gags)):
            balloon = self.gags[i]
            if balloon.isSingleton():
                remove.append(i)
            elif balloon.getParent() == render:
                loc = self.maze.world2tile(balloon.getX(), balloon.getY())
                if not self.maze.isAccessible(loc[0], loc[1]):
                    self.removeGag(balloon)

        remove.reverse()
        for i in remove:
            self.gags.pop(i)

    def __updateQuakeSound(self):
        shake = self.localPlayer.getCameraShake()
        if shake < 1.0:
            shake = 1.0
        volume = 3.0 * shake / Globals.CameraShakeMax
        if volume > 3.0:
            volume = 3.0
        if self._quakeSfx1.getAudioSound().status() != self._quakeSfx1.getAudioSound().PLAYING:
            self._quakeSfx1.loop(volume=volume)
        else:
            self._quakeSfx1.getAudioSound().setVolume(volume)
        volume = shake * shake / Globals.CameraShakeMax
        if not self.hackTemp and self._quakeSfx2.getAudioSound().status() != self._quakeSfx2.getAudioSound().PLAYING:
            taskMgr.doMethodLater(1.5, self._quakeSfx2.loop, 'loopSecondQuakeSound', extraArgs=[])
            self.hackTemp = True
        else:
            self._quakeSfx2.getAudioSound().setVolume(volume)

    def handleLocalToonMeetsSuit(self, suitType, suitNum):
        if self.localPlayer.state == 'Normal' and not self.localPlayer.invulnerable:
            self.distGame.b_toonHitBySuit(suitType, suitNum)

    def toonHitBySuit(self, toonId, suitType, suitNum, elapsedTime = 0.0):
        player = self.toonId2Player[toonId]
        if player.state == 'Normal':
            player.request('Hit', elapsedTime)

    def handleSuitDeath(self, suitType, suitNum):
        suit = self.suitsById[suitNum]
        self.dropMemos(suit)
        self.removeSuit(suit)

    def dropMemos(self, suit):
        numDrops = suit.memos
        if numDrops > 0:
            start = math.radians(random.randint(0, 360))
            step = math.radians(360.0 / numDrops)
            radius = 2.0
            for i in range(numDrops):
                angle = start + i * step
                x = radius * math.cos(angle) + suit.suit.getX()
                y = radius * math.sin(angle) + suit.suit.getY()
                self.generatePickup(x, y)

    def handleSuitThink(self, suit, TX, TY):
        if suit in self.shakers:
            self.guiMgr.mazeMapGui.updateSuit(suit.suit, TX, TY)
            suit.dropTimer += 1
            if suit.dropTimer >= Globals.DropFrequency:
                self.doDrop(suit)
                suit.dropTimer = 0

    def doDrop(self, boss):
        dropLoc = boss.pickRandomValidSpot()
        self.generateDrop(dropLoc[0], dropLoc[1])

    def handleBossShake(self, suit, strength):
        if Globals.BossShakeEnabled:
            self.shakeCamera(suit.suit, strength, Globals.BossMaxDistance)

    def randomDrop(self, centerTX, centerTY, radius):
        dropArray = []
        for i in range(1, distance):
            dropArray.append(i)
            dropArray.append(-1 * i)

        offsetTX = self.distGame.randomNumGen.choice(dropArray)
        offsetTY = self.distGame.randomNumGen.choice(dropArray)
        dropTX = sourceTX + offsetTX
        dropTY = sourceTY + offsetTY
        if self.maze.isWalkable(dropTX, dropTY):
            self.generateDrop(dropTX, dropTY)

    def generateDrop(self, TX, TY):
        drop = self.maze.tile2world(TX, TY)
        ival = self.createDrop(drop[0], drop[1])
        ival.start()

    def createDrop(self, x, y):
        self.dropCounter = self.dropCounter + 1
        id = self.dropCounter
        drop = CogdoMazeDrop(self, id, x, y)
        self.drops[id] = drop
        return drop.getDropIval()

    def cleanupDrop(self, id):
        if id in list(self.drops.keys()):
            drop = self.drops[id]
            drop.destroy()
            del self.drops[id]

    def dropHit(self, node, id):
        if self.finished:
            return
        if Globals.DropShakeEnabled:
            self.shakeCamera(node, Globals.DropShakeStrength, Globals.DropMaxDistance)

    def shakeCamera(self, node, strength, distanceCutoff = 60.0):
        distance = self.localPlayer.toon.getDistance(node)
        shake = strength * (1 - distance / distanceCutoff)
        if shake > 0:
            self.localPlayer.shakeCamera(shake)

    def handleLocalToonMeetsDrop(self, collEntry):
        fcabinet = collEntry.getIntoNodePath()
        if fcabinet.getTag('isFalling') == str('False'):
            return
        if self.localPlayer.state == 'Normal' and not self.localPlayer.invulnerable:
            self.distGame.b_toonHitByDrop()

    def toonHitByDrop(self, toonId):
        player = self.toonId2Player[toonId]
        player.hitByDrop()

    def handleLocalToonMeetsGagPickup(self, collEntry):
        if self.localPlayer.equippedGag != None:
            return
        into = collEntry.getIntoNodePath()
        if into.hasPythonTag('id'):
            id = into.getPythonTag('id')
            self.distGame.d_sendRequestGagPickUp(id)
        return

    def hasGag(self, toonId, elapsedTime = 0.0):
        player = self.toonId2Player[toonId]
        player.equipGag()

    def handleLocalToonMeetsWaterCooler(self, collEntry):
        if self.localPlayer.equippedGag != None:
            return
        if self.lastBalloonTimestamp and globalClock.getFrameTime() - self.lastBalloonTimestamp < Globals.BalloonDelay:
            return
        collNode = collEntry.getIntoNode()
        waterCooler = self._collNode2waterCooler[collNode]
        self.lastBalloonTimestamp = globalClock.getFrameTime()
        self.distGame.d_sendRequestGag(waterCooler.serialNum)
        return

    def requestUseGag(self, x, y, h):
        self.distGame.b_toonUsedGag(x, y, h)

    def toonUsedGag(self, toonId, x, y, h, elapsedTime = 0.0):
        player = self.toonId2Player[toonId]
        heading = h
        pos = Point3(x, y, 0)
        gag = player.showToonThrowingGag(heading, pos)
        if gag is not None:
            self.gags.append(gag)
        return

    def handleToonMeetsGag(self, playerId, gag):
        self.removeGag(gag)
        self.distGame.b_toonHitByGag(playerId)

    def toonHitByGag(self, toonId, hitToon, elapsedTime = 0.0):
        if toonId not in list(self.toonId2Player.keys()) or hitToon not in list(self.toonId2Player.keys()):
            return
        player = self.toonId2Player[hitToon]
        player.hitByGag()

    def handleLocalSuitMeetsGag(self, suitType, suitNum, gag):
        self.removeGag(gag)
        self.localPlayer.hitSuit(suitType)
        self.distGame.b_suitHitByGag(suitType, suitNum)

    def suitHitByGag(self, toonId, suitType, suitNum, elapsedTime = 0.0):
        if suitType == Globals.SuitTypes.Boss:
            self.guiMgr.showBossHit(suitNum)
        if suitNum in list(self.suitsById.keys()):
            suit = self.suitsById[suitNum]
            suit.hitByGag()

    def removeGag(self, gag):
        gag.detachNode()

    def toonRevealsDoor(self, toonId):
        self._exit.revealed = True

    def openDoor(self, timeLeft):
        self._audioMgr.playMusic('timeRunningOut')
        if not self._exit.isOpen():
            self._exit.open()
            self.localPlayer.handleOpenDoor(self._exit)
            self.guiMgr.showTimer(timeLeft, self._handleTimerExpired)
            self.guiMgr.mazeMapGui.showExit()
            self.guiMgr.mazeMapGui.revealAll()

    def countdown(self, timeLeft):
        self.guiMgr.showTimer(timeLeft, self._handleTimerExpired)

    def timeAlert(self):
        self._audioMgr.playMusic('timeRunningOut')

    def _handleTimerExpired(self):
        self.localPlayer.request('Done')

    def toonEntersDoor(self, toonId):
        player = self.toonId2Player[toonId]
        self.guiMgr.mazeMapGui.removeToon(player.toon)
        self._exit.playerEntersDoor(player)
        self.localPlayer.handleToonEntersDoor(toonId, self._exit)
        player.request('Done')

    def generatePickup(self, x, y):
        pickup = CogdoMemo(len(self.pickups), pitch=-90)
        self.pickups.append(pickup)
        pickup.reparentTo(self.maze.maze)
        pickup.setPos(x, y, 1)
        pickup.enable()

    def handleLocalToonMeetsPickup(self, pickup):
        pickup.disable()
        self.distGame.d_sendRequestPickUp(pickup.serialNum)

    def pickUp(self, toonId, pickupNum, elapsedTime = 0.0):
        self.notify.debugCall()
        player = self.toonId2Player[toonId]
        pickup = self.pickups[pickupNum]
        if not pickup.wasPickedUp():
            pickup.pickUp(player.toon, elapsedTime)
            self.localPlayer.handlePickUp(toonId)

    def placePlayer(self, player):
        toonIds = self.distGame.getToonIds()
        if player.toon.doId not in toonIds:
            return
        i = toonIds.index(player.toon.doId)
        x = int(self.maze.width / 2.0) - int(len(toonIds) / 2.0) + i
        y = 2
        while not self.maze.isAccessible(x, y):
            y += 1

        pos = self.maze.tile2world(x, y)
        player.toon.setPos(pos[0], pos[1], 0)
        self.guiMgr.mazeMapGui.addToon(player.toon, x, y)

    def handleLocalToonEntersDoor(self, door):
        localToonId = self.localPlayer.toon.doId
        if self._exit.isOpen():
            self.distGame.d_sendRequestAction(Globals.GameActions.EnterDoor, 0)
        else:
            if localToonId not in self.toonsThatRevealedDoor:
                self.toonsThatRevealedDoor.append(localToonId)
                self.localPlayer.handleToonRevealsDoor(localToonId, self._exit)
            if not self._exit.revealed:
                self.toonRevealsDoor(localToonId)
                self.distGame.d_sendRequestAction(Globals.GameActions.RevealDoor, 0)

    def handleToonWentSad(self, toonId):
        if toonId == self.localPlayer.toon.doId:
            for player in self.players:
                player.removeGag()

        elif toonId in list(self.toonId2Player.keys()):
            player = self.toonId2Player[toonId]
            player.removeGag()

    def handleToonDisconnected(self, toonId):
        if toonId == self.localPlayer.toon.doId:
            pass
        elif toonId in list(self.toonId2Player.keys()):
            player = self.toonId2Player[toonId]
            self._removePlayer(player)
