from pandac.PandaModules import *
from toontown.toonbase.ToonBaseGlobal import *
from .DistributedMinigame import *
from direct.interval.IntervalGlobal import *
from .OrthoWalk import *
from direct.showbase.PythonUtil import Functor, bound, lineupPos, lerp
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from toontown.toonbase import TTLocalizer
from . import CatchGameGlobals
from direct.task.Task import Task
from toontown.toon import Toon
from toontown.suit import Suit
from . import MinigameAvatarScorePanel
from toontown.toonbase import ToontownTimer
from toontown.toonbase import ToontownGlobals
from . import CatchGameToonSD
from . import Trajectory
import math
from direct.distributed import DistributedSmoothNode
from direct.showbase.RandomNumGen import RandomNumGen
from . import MinigameGlobals
from toontown.toon import ToonDNA
from toontown.suit import SuitDNA
from .CatchGameGlobals import DropObjectTypes
from .CatchGameGlobals import Name2DropObjectType
from .DropPlacer import *
from .DropScheduler import *
from functools import reduce

class DistributedCatchGame(DistributedMinigame):
    DropTaskName = 'dropSomething'
    EndGameTaskName = 'endCatchGame'
    SuitWalkTaskName = 'catchGameSuitWalk'
    DropObjectPlurals = {'apple': TTLocalizer.CatchGameApples,
     'orange': TTLocalizer.CatchGameOranges,
     'pear': TTLocalizer.CatchGamePears,
     'coconut': TTLocalizer.CatchGameCoconuts,
     'watermelon': TTLocalizer.CatchGameWatermelons,
     'pineapple': TTLocalizer.CatchGamePineapples,
     'anvil': TTLocalizer.CatchGameAnvils}

    def __init__(self, cr):
        DistributedMinigame.__init__(self, cr)
        self.gameFSM = ClassicFSM.ClassicFSM('DistributedCatchGame', [State.State('off', self.enterOff, self.exitOff, ['play']), State.State('play', self.enterPlay, self.exitPlay, ['cleanup']), State.State('cleanup', self.enterCleanup, self.exitCleanup, [])], 'off', 'cleanup')
        self.addChildGameFSM(self.gameFSM)
        self.setUsesSmoothing()
        self.setUsesLookAround()

    def getTitle(self):
        return TTLocalizer.CatchGameTitle

    def getInstructions(self):
        return TTLocalizer.CatchGameInstructions % {'fruit': self.DropObjectPlurals[self.fruitName],
         'badThing': self.DropObjectPlurals['anvil']}

    def getMaxDuration(self):
        return CatchGameGlobals.GameDuration + 5

    def load(self):
        self.notify.debug('load')
        DistributedMinigame.load(self)
        self.defineConstants()
        groundModels = ['phase_4/models/minigames/treehouse_2players',
         'phase_4/models/minigames/treehouse_2players',
         'phase_4/models/minigames/treehouse_3players',
         'phase_4/models/minigames/treehouse_4players']
        index = self.getNumPlayers() - 1
        self.ground = loader.loadModel(groundModels[index])
        self.ground.setHpr(180, -90, 0)
        self.dropShadow = loader.loadModel('phase_3/models/props/drop_shadow')
        self.dropObjModels = {}
        for objType in DropObjectTypes:
            if objType.name not in ['anvil', self.fruitName]:
                continue
            model = loader.loadModel(objType.modelPath)
            self.dropObjModels[objType.name] = model
            modelScales = {'apple': 0.7,
             'orange': 0.7,
             'pear': 0.5,
             'coconut': 0.7,
             'watermelon': 0.6,
             'pineapple': 0.45}
            if objType.name in modelScales:
                model.setScale(modelScales[objType.name])
            if objType == Name2DropObjectType['pear']:
                model.setZ(-.6)
            if objType == Name2DropObjectType['coconut']:
                model.setP(180)
            if objType == Name2DropObjectType['watermelon']:
                model.setH(135)
                model.setZ(-.5)
            if objType == Name2DropObjectType['pineapple']:
                model.setZ(-1.7)
            if objType == Name2DropObjectType['anvil']:
                model.setZ(-self.ObjRadius)
            model.flattenMedium()

        self.music = base.loader.loadMusic('phase_4/audio/bgm/MG_toontag.ogg')
        self.sndGoodCatch = base.loader.loadSfx('phase_4/audio/sfx/SZ_DD_treasure.ogg')
        self.sndOof = base.loader.loadSfx('phase_4/audio/sfx/MG_cannon_hit_dirt.ogg')
        self.sndAnvilLand = base.loader.loadSfx('phase_4/audio/sfx/AA_drop_anvil_miss.ogg')
        self.sndPerfect = base.loader.loadSfx('phase_4/audio/sfx/ring_perfect.ogg')
        self.toonSDs = {}
        avId = self.localAvId
        toonSD = CatchGameToonSD.CatchGameToonSD(avId, self)
        self.toonSDs[avId] = toonSD
        toonSD.load()
        if self.WantSuits:
            suitTypes = ['f',
             'tm',
             'pp',
             'dt']
            self.suits = []
            for type in suitTypes:
                suit = Suit.Suit()
                d = SuitDNA.SuitDNA()
                d.newSuit(type)
                suit.setDNA(d)
                suit.pose('walk', 0)
                self.suits.append(suit)

        self.__textGen = TextNode('ringGame')
        self.__textGen.setFont(ToontownGlobals.getSignFont())
        self.__textGen.setAlign(TextNode.ACenter)
        self.introMovie = self.getIntroMovie()

    def unload(self):
        self.notify.debug('unload')
        DistributedMinigame.unload(self)
        self.removeChildGameFSM(self.gameFSM)
        del self.gameFSM
        self.introMovie.finish()
        del self.introMovie
        del self.__textGen
        for avId in list(self.toonSDs.keys()):
            toonSD = self.toonSDs[avId]
            toonSD.unload()

        del self.toonSDs
        for suit in self.suits:
            suit.reparentTo(hidden)
            suit.delete()

        del self.suits
        self.ground.removeNode()
        del self.ground
        self.dropShadow.removeNode()
        del self.dropShadow
        for model in list(self.dropObjModels.values()):
            model.removeNode()

        del self.dropObjModels
        del self.music
        del self.sndGoodCatch
        del self.sndOof
        del self.sndAnvilLand
        del self.sndPerfect

    def getObjModel(self, objName):
        return self.dropObjModels[objName].copyTo(hidden)

    def __genText(self, text):
        self.__textGen.setText(text)
        return self.__textGen.generate()

    def calcDifficultyConstants(self, difficulty, numPlayers):
        ToonSpeedRange = [16.0, 25.0]
        self.ToonSpeed = lerp(ToonSpeedRange[0], ToonSpeedRange[1], difficulty)
        self.SuitSpeed = self.ToonSpeed / 2.0
        self.SuitPeriodRange = [lerp(5.0, 3.0, self.getDifficulty()), lerp(15.0, 8.0, self.getDifficulty())]

        def scaledDimensions(widthHeight, scale):
            w, h = widthHeight
            return [math.sqrt(scale * w * w), math.sqrt(scale * h * h)]

        BaseStageDimensions = [20, 15]
        areaScales = [1.0,
         1.0,
         3.0 / 2,
         4.0 / 2]
        self.StageAreaScale = areaScales[numPlayers - 1]
        self.StageLinearScale = math.sqrt(self.StageAreaScale)
        self.notify.debug('StageLinearScale: %s' % self.StageLinearScale)
        self.StageDimensions = scaledDimensions(BaseStageDimensions, self.StageAreaScale)
        self.notify.debug('StageDimensions: %s' % self.StageDimensions)
        self.StageHalfWidth = self.StageDimensions[0] / 2.0
        self.StageHalfHeight = self.StageDimensions[1] / 2.0
        MOHs = [24] * 2 + [26, 28]
        self.MinOffscreenHeight = MOHs[self.getNumPlayers() - 1]
        distance = math.sqrt(self.StageDimensions[0] * self.StageDimensions[0] + self.StageDimensions[1] * self.StageDimensions[1])
        distance /= self.StageLinearScale
        if self.DropPlacerType == PathDropPlacer:
            distance /= 1.5
        ToonRunDuration = distance / self.ToonSpeed
        offScreenOnScreenRatio = 1.0
        fraction = 1.0 / 3 * 0.85
        self.BaselineOnscreenDropDuration = ToonRunDuration / (fraction * (1.0 + offScreenOnScreenRatio))
        self.notify.debug('BaselineOnscreenDropDuration=%s' % self.BaselineOnscreenDropDuration)
        self.OffscreenTime = offScreenOnScreenRatio * self.BaselineOnscreenDropDuration
        self.notify.debug('OffscreenTime=%s' % self.OffscreenTime)
        self.BaselineDropDuration = self.BaselineOnscreenDropDuration + self.OffscreenTime
        self.MaxDropDuration = self.BaselineDropDuration
        self.DropPeriod = self.BaselineDropDuration / 2.0
        scaledNumPlayers = (numPlayers - 1.0) * 0.75 + 1.0
        self.DropPeriod /= scaledNumPlayers
        typeProbs = {'fruit': 3,
         'anvil': 1}
        probSum = reduce(lambda x, y: x + y, list(typeProbs.values()))
        for key in list(typeProbs.keys()):
            typeProbs[key] = float(typeProbs[key]) / probSum

        scheduler = DropScheduler(CatchGameGlobals.GameDuration, self.FirstDropDelay, self.DropPeriod, self.MaxDropDuration, self.FasterDropDelay, self.FasterDropPeriodMult)
        self.totalDrops = 0
        while not scheduler.doneDropping():
            scheduler.stepT()
            self.totalDrops += 1

        self.numFruits = int(self.totalDrops * typeProbs['fruit'])
        self.numAnvils = int(self.totalDrops - self.numFruits)

    def getNumPlayers(self):
        return self.numPlayers

    def defineConstants(self):
        self.notify.debug('defineConstants')
        self.DropPlacerType = RegionDropPlacer
        fruits = {ToontownGlobals.ToontownCentral: 'apple',
         ToontownGlobals.DonaldsDock: 'orange',
         ToontownGlobals.DaisyGardens: 'pear',
         ToontownGlobals.MinniesMelodyland: 'coconut',
         ToontownGlobals.TheBrrrgh: 'watermelon',
         ToontownGlobals.DonaldsDreamland: 'pineapple'}
        self.fruitName = fruits[self.getSafezoneId()]
        self.ShowObjSpheres = 0
        self.ShowToonSpheres = 0
        self.ShowSuitSpheres = 0
        self.PredictiveSmoothing = 1
        self.UseGravity = 1
        self.TrickShadows = 1
        self.WantSuits = 1
        self.FirstDropDelay = 0.5
        self.FasterDropDelay = int(2.0 / 3 * CatchGameGlobals.GameDuration)
        self.notify.debug('will start dropping fast after %s seconds' % self.FasterDropDelay)
        self.FasterDropPeriodMult = 0.5
        self.calcDifficultyConstants(self.getDifficulty(), self.getNumPlayers())
        self.notify.debug('ToonSpeed: %s' % self.ToonSpeed)
        self.notify.debug('total drops: %s' % self.totalDrops)
        self.notify.debug('numFruits: %s' % self.numFruits)
        self.notify.debug('numAnvils: %s' % self.numAnvils)
        self.ObjRadius = 1.0
        dropGridDimensions = [[5, 5],
         [5, 5],
         [6, 6],
         [7, 7]]
        self.DropRows, self.DropColumns = dropGridDimensions[self.getNumPlayers() - 1]
        self.cameraPosTable = [[0, -29.36, 28.17]] * 2 + [[0, -32.87, 30.43], [0, -35.59, 32.1]]
        self.cameraHpr = [0, -35, 0]
        self.CameraPosHpr = self.cameraPosTable[self.getNumPlayers() - 1] + self.cameraHpr
        for objType in DropObjectTypes:
            self.notify.debug('*** Object Type: %s' % objType.name)
            objType.onscreenDuration = objType.onscreenDurMult * self.BaselineOnscreenDropDuration
            self.notify.debug('onscreenDuration=%s' % objType.onscreenDuration)
            v_0 = 0.0
            t = objType.onscreenDuration
            x_0 = self.MinOffscreenHeight
            x = 0.0
            g = 2.0 * (x - x_0 - v_0 * t) / (t * t)
            self.notify.debug('gravity=%s' % g)
            objType.trajectory = Trajectory.Trajectory(0, Vec3(0, 0, x_0), Vec3(0, 0, v_0), gravMult=abs(g / Trajectory.Trajectory.gravity))
            objType.fallDuration = objType.onscreenDuration + self.OffscreenTime

    def grid2world(self, column, row):
        x = column / float(self.DropColumns - 1)
        y = row / float(self.DropRows - 1)
        x = x * 2.0 - 1.0
        y = y * 2.0 - 1.0
        x *= self.StageHalfWidth
        y *= self.StageHalfHeight
        return (x, y)

    def showPosts(self):
        self.hidePosts()
        self.posts = [Toon.Toon(),
         Toon.Toon(),
         Toon.Toon(),
         Toon.Toon()]
        for i in range(len(self.posts)):
            toon = self.posts[i]
            toon.setDNA(base.localAvatar.getStyle())
            toon.reparentTo(render)
            x = self.StageHalfWidth
            y = self.StageHalfHeight
            if i > 1:
                x = -x
            if i % 2:
                y = -y
            toon.setPos(x, y, 0)

    def hidePosts(self):
        if hasattr(self, 'posts'):
            for toon in self.posts:
                toon.removeNode()

            del self.posts

    def showDropGrid(self):
        self.hideDropGrid()
        self.dropMarkers = []
        print('dropRows: %s' % self.DropRows)
        print('dropCols: %s' % self.DropColumns)
        for row in range(self.DropRows):
            self.dropMarkers.append([])
            rowList = self.dropMarkers[row]
            for column in range(self.DropColumns):
                toon = Toon.Toon()
                toon.setDNA(base.localAvatar.getStyle())
                toon.reparentTo(render)
                toon.setScale(1.0 / 3)
                x, y = self.grid2world(column, row)
                toon.setPos(x, y, 0)
                rowList.append(toon)

    def hideDropGrid(self):
        if hasattr(self, 'dropMarkers'):
            for row in self.dropMarkers:
                for marker in row:
                    marker.removeNode()

            del self.dropMarkers

    def onstage(self):
        self.notify.debug('onstage')
        DistributedMinigame.onstage(self)
        self.ground.reparentTo(render)
        self.scorePanels = []
        camera.reparentTo(render)
        camera.setPosHpr(*self.CameraPosHpr)
        lt = base.localAvatar
        lt.reparentTo(render)
        self.__placeToon(self.localAvId)
        lt.setSpeed(0, 0)
        toonSD = self.toonSDs[self.localAvId]
        toonSD.enter()
        toonSD.fsm.request('normal')
        self.orthoWalk.stop()
        radius = 0.7
        handler = CollisionHandlerEvent()
        handler.setInPattern('ltCatch%in')
        self.ltLegsCollNode = CollisionNode('catchLegsCollNode')
        self.ltLegsCollNode.setCollideMask(ToontownGlobals.CatchGameBitmask)
        self.ltHeadCollNode = CollisionNode('catchHeadCollNode')
        self.ltHeadCollNode.setCollideMask(ToontownGlobals.CatchGameBitmask)
        self.ltLHandCollNode = CollisionNode('catchLHandCollNode')
        self.ltLHandCollNode.setCollideMask(ToontownGlobals.CatchGameBitmask)
        self.ltRHandCollNode = CollisionNode('catchRHandCollNode')
        self.ltRHandCollNode.setCollideMask(ToontownGlobals.CatchGameBitmask)
        legsCollNodepath = lt.attachNewNode(self.ltLegsCollNode)
        legsCollNodepath.hide()
        head = base.localAvatar.getHeadParts().getPath(2)
        headCollNodepath = head.attachNewNode(self.ltHeadCollNode)
        headCollNodepath.hide()
        lHand = base.localAvatar.getLeftHands()[0]
        lHandCollNodepath = lHand.attachNewNode(self.ltLHandCollNode)
        lHandCollNodepath.hide()
        rHand = base.localAvatar.getRightHands()[0]
        rHandCollNodepath = rHand.attachNewNode(self.ltRHandCollNode)
        rHandCollNodepath.hide()
        lt.cTrav.addCollider(legsCollNodepath, handler)
        lt.cTrav.addCollider(headCollNodepath, handler)
        lt.cTrav.addCollider(lHandCollNodepath, handler)
        lt.cTrav.addCollider(lHandCollNodepath, handler)
        if self.ShowToonSpheres:
            legsCollNodepath.show()
            headCollNodepath.show()
            lHandCollNodepath.show()
            rHandCollNodepath.show()
        self.ltLegsCollNode.addSolid(CollisionSphere(0, 0, radius, radius))
        self.ltHeadCollNode.addSolid(CollisionSphere(0, 0, 0, radius))
        self.ltLHandCollNode.addSolid(CollisionSphere(0, 0, 0, 2 * radius / 3.0))
        self.ltRHandCollNode.addSolid(CollisionSphere(0, 0, 0, 2 * radius / 3.0))
        self.toonCollNodes = [legsCollNodepath,
         headCollNodepath,
         lHandCollNodepath,
         rHandCollNodepath]
        if self.PredictiveSmoothing:
            DistributedSmoothNode.activateSmoothing(1, 1)
        self.introMovie.start()

    def offstage(self):
        self.notify.debug('offstage')
        DistributedSmoothNode.activateSmoothing(1, 0)
        self.introMovie.finish()
        for avId in list(self.toonSDs.keys()):
            self.toonSDs[avId].exit()

        self.hidePosts()
        self.hideDropGrid()
        for collNode in self.toonCollNodes:
            while collNode.node().getNumSolids():
                collNode.node().removeSolid(0)

            base.localAvatar.cTrav.removeCollider(collNode)

        del self.toonCollNodes
        for panel in self.scorePanels:
            panel.cleanup()

        del self.scorePanels
        self.ground.reparentTo(hidden)
        DistributedMinigame.offstage(self)

    def handleDisabledAvatar(self, avId):
        self.notify.debug('handleDisabledAvatar')
        self.notify.debug('avatar ' + str(avId) + ' disabled')
        self.toonSDs[avId].exit(unexpectedExit=True)
        del self.toonSDs[avId]
        DistributedMinigame.handleDisabledAvatar(self, avId)

    def __placeToon(self, avId):
        toon = self.getAvatar(avId)
        idx = self.avIdList.index(avId)
        x = lineupPos(idx, self.numPlayers, 4.0)
        toon.setPos(x, 0, 0)
        toon.setHpr(180, 0, 0)

    def setGameReady(self):
        if not self.hasLocalToon:
            return
        self.notify.debug('setGameReady')
        if DistributedMinigame.setGameReady(self):
            return
        headCollNP = base.localAvatar.find('**/catchHeadCollNode')
        if headCollNP and not headCollNP.isEmpty():
            headCollNP.hide()
        for avId in self.remoteAvIdList:
            toon = self.getAvatar(avId)
            if toon:
                toon.reparentTo(render)
                self.__placeToon(avId)
                toonSD = CatchGameToonSD.CatchGameToonSD(avId, self)
                self.toonSDs[avId] = toonSD
                toonSD.load()
                toonSD.enter()
                toonSD.fsm.request('normal')
                toon.startSmooth()

    def setGameStart(self, timestamp):
        if not self.hasLocalToon:
            return
        self.notify.debug('setGameStart')
        DistributedMinigame.setGameStart(self, timestamp)
        self.introMovie.finish()
        camera.reparentTo(render)
        camera.setPosHpr(*self.CameraPosHpr)
        self.gameFSM.request('play')

    def enterOff(self):
        self.notify.debug('enterOff')

    def exitOff(self):
        pass

    def enterPlay(self):
        self.notify.debug('enterPlay')
        self.orthoWalk.start()
        for suit in self.suits:
            suitCollSphere = CollisionSphere(0, 0, 0, 1.0)
            suit.collSphereName = 'suitCollSphere%s' % self.suits.index(suit)
            suitCollSphere.setTangible(0)
            suitCollNode = CollisionNode(self.uniqueName(suit.collSphereName))
            suitCollNode.setIntoCollideMask(ToontownGlobals.WallBitmask)
            suitCollNode.addSolid(suitCollSphere)
            suit.collNodePath = suit.attachNewNode(suitCollNode)
            suit.collNodePath.hide()
            if self.ShowSuitSpheres:
                suit.collNodePath.show()
            self.accept(self.uniqueName('enter' + suit.collSphereName), self.handleSuitCollision)

        self.scores = [0] * self.numPlayers
        spacing = 0.4
        for i in range(self.numPlayers):
            avId = self.avIdList[i]
            avName = self.getAvatarName(avId)
            scorePanel = MinigameAvatarScorePanel.MinigameAvatarScorePanel(avId, avName)
            scorePanel.setScale(0.9)
            scorePanel.setPos(0.75 - spacing * (self.numPlayers - 1 - i), 0.0, 0.85)
            scorePanel.makeTransparent(0.75)
            self.scorePanels.append(scorePanel)

        self.fruitsCaught = 0
        self.droppedObjCaught = {}
        self.dropIntervals = {}
        self.droppedObjNames = []
        self.dropSchedule = []
        self.numItemsDropped = 0
        self.scheduleDrops()
        self.startDropTask()
        if self.WantSuits:
            self.startSuitWalkTask()
        self.timer = ToontownTimer.ToontownTimer()
        self.timer.posInTopRightCorner()
        self.timer.setTime(CatchGameGlobals.GameDuration)
        self.timer.countdown(CatchGameGlobals.GameDuration, self.timerExpired)
        self.timer.setTransparency(1)
        self.timer.setColorScale(1, 1, 1, 0.75)
        base.playMusic(self.music, looping=0, volume=0.9)

    def exitPlay(self):
        self.stopDropTask()
        self.stopSuitWalkTask()
        if hasattr(self, 'perfectIval'):
            self.perfectIval.pause()
            del self.perfectIval
        self.timer.stop()
        self.timer.destroy()
        del self.timer
        self.music.stop()
        for suit in self.suits:
            self.ignore(self.uniqueName('enter' + suit.collSphereName))
            suit.collNodePath.removeNode()

        for ival in list(self.dropIntervals.values()):
            ival.finish()

        del self.dropIntervals
        del self.droppedObjNames
        del self.droppedObjCaught
        del self.dropSchedule
        taskMgr.remove(self.EndGameTaskName)

    def timerExpired(self):
        pass

    def __handleCatch(self, objNum):
        self.notify.debug('catch: %s' % objNum)
        self.showCatch(self.localAvId, objNum)
        objName = self.droppedObjNames[objNum]
        objTypeId = CatchGameGlobals.Name2DOTypeId[objName]
        self.sendUpdate('claimCatch', [objNum, objTypeId])
        self.finishDropInterval(objNum)

    def showCatch(self, avId, objNum):
        isLocal = avId == self.localAvId
        objName = self.droppedObjNames[objNum]
        objType = Name2DropObjectType[objName]
        if objType.good:
            if objNum not in self.droppedObjCaught:
                if isLocal:
                    base.playSfx(self.sndGoodCatch)
                fruit = self.getObjModel(objName)
                toon = self.getAvatar(avId)
                rHand = toon.getRightHands()[0]
                self.toonSDs[avId].eatFruit(fruit, rHand)
        else:
            self.toonSDs[avId].fsm.request('fallForward')
        self.droppedObjCaught[objNum] = 1

    def setObjectCaught(self, avId, objNum):
        if not self.hasLocalToon:
            return
        if self.gameFSM.getCurrentState().getName() != 'play':
            self.notify.warning('ignoring msg: object %s caught by %s' % (objNum, avId))
            return
        isLocal = avId == self.localAvId
        if not isLocal:
            self.notify.debug('AI: avatar %s caught %s' % (avId, objNum))
            self.finishDropInterval(objNum)
            self.showCatch(avId, objNum)
        objName = self.droppedObjNames[objNum]
        if Name2DropObjectType[objName].good:
            i = self.avIdList.index(avId)
            self.scores[i] += 1
            self.scorePanels[i].setScore(self.scores[i])
            self.fruitsCaught += 1

    def finishDropInterval(self, objNum):
        if objNum in self.dropIntervals:
            self.dropIntervals[objNum].finish()

    def scheduleDrops(self):
        self.droppedObjNames = [self.fruitName] * self.numFruits + ['anvil'] * self.numAnvils
        self.randomNumGen.shuffle(self.droppedObjNames)
        dropPlacer = self.DropPlacerType(self, self.getNumPlayers(), self.droppedObjNames)
        while not dropPlacer.doneDropping():
            self.dropSchedule.append(dropPlacer.getNextDrop())

    def startDropTask(self):
        taskMgr.add(self.dropTask, self.DropTaskName)

    def stopDropTask(self):
        taskMgr.remove(self.DropTaskName)

    def dropTask(self, task):
        curT = self.getCurrentGameTime()
        while self.dropSchedule[0][0] <= curT:
            drop = self.dropSchedule[0]
            self.dropSchedule = self.dropSchedule[1:]
            dropTime, objName, dropCoords = drop
            objNum = self.numItemsDropped
            lastDrop = len(self.dropSchedule) == 0
            x, y = self.grid2world(*dropCoords)
            dropIval = self.getDropIval(x, y, objName, objNum)

            def cleanup(self = self, objNum = objNum, lastDrop = lastDrop):
                del self.dropIntervals[objNum]
                if lastDrop:
                    self.sendUpdate('reportDone')

            dropIval.append(Func(cleanup))
            self.dropIntervals[objNum] = dropIval
            self.numItemsDropped += 1
            dropIval.start(curT - dropTime)
            if lastDrop:
                return Task.done

        return Task.cont

    def setEveryoneDone(self):
        if not self.hasLocalToon:
            return
        if self.gameFSM.getCurrentState().getName() != 'play':
            self.notify.warning('ignoring setEveryoneDone msg')
            return
        self.notify.debug('setEveryoneDone')

        def endGame(task, self = self):
            if not CatchGameGlobals.EndlessGame:
                self.gameOver()
            return Task.done

        self.notify.debug('num fruits: %s' % self.numFruits)
        self.notify.debug('num catches: %s' % self.fruitsCaught)
        self.timer.hide()
        if self.fruitsCaught >= self.numFruits:
            self.notify.debug('perfect game!')
            perfectTextSubnode = hidden.attachNewNode(self.__genText(TTLocalizer.CatchGamePerfect))
            perfectText = hidden.attachNewNode('perfectText')
            perfectTextSubnode.reparentTo(perfectText)
            frame = self.__textGen.getCardActual()
            offsetY = -abs(frame[2] + frame[3]) / 2.0
            perfectTextSubnode.setPos(0, 0, offsetY)
            perfectText.setColor(1, 0.1, 0.1, 1)

            def fadeFunc(t, text = perfectText):
                text.setColorScale(1, 1, 1, t)

            def destroyText(text = perfectText):
                text.removeNode()

            textTrack = Sequence(Func(perfectText.reparentTo, aspect2d), Parallel(LerpScaleInterval(perfectText, duration=0.5, scale=0.3, startScale=0.0), LerpFunctionInterval(fadeFunc, fromData=0.0, toData=1.0, duration=0.5)), Wait(2.0), Parallel(LerpScaleInterval(perfectText, duration=0.5, scale=1.0), LerpFunctionInterval(fadeFunc, fromData=1.0, toData=0.0, duration=0.5, blendType='easeIn')), Func(destroyText), WaitInterval(0.5), Func(endGame, None))
            soundTrack = SoundInterval(self.sndPerfect)
            self.perfectIval = Parallel(textTrack, soundTrack)
            self.perfectIval.start()
        else:
            taskMgr.doMethodLater(1, endGame, self.EndGameTaskName)
        return

    def getDropIval(self, x, y, dropObjName, num):
        objType = Name2DropObjectType[dropObjName]
        dropNode = hidden.attachNewNode('catchDropNode%s' % num)
        dropNode.setPos(x, y, 0)
        shadow = self.dropShadow.copyTo(dropNode)
        shadow.setZ(0.2)
        shadow.setColor(1, 1, 1, 1)
        object = self.getObjModel(dropObjName)
        object.reparentTo(dropNode)
        if dropObjName in ['watermelon', 'anvil']:
            objH = object.getH()
            absDelta = {'watermelon': 12,
             'anvil': 15}[dropObjName]
            delta = (self.randomNumGen.random() * 2.0 - 1.0) * absDelta
            newH = objH + delta
        else:
            newH = self.randomNumGen.random() * 360.0
        object.setH(newH)
        sphereName = 'FallObj%s' % num
        radius = self.ObjRadius
        if objType.good:
            radius *= lerp(1.0, 1.3, self.getDifficulty())
        collSphere = CollisionSphere(0, 0, 0, radius)
        collSphere.setTangible(0)
        collNode = CollisionNode(sphereName)
        collNode.setCollideMask(ToontownGlobals.CatchGameBitmask)
        collNode.addSolid(collSphere)
        collNodePath = object.attachNewNode(collNode)
        collNodePath.hide()
        if self.ShowObjSpheres:
            collNodePath.show()
        catchEventName = 'ltCatch' + sphereName

        def eatCollEntry(forward, collEntry):
            forward()

        self.accept(catchEventName, Functor(eatCollEntry, Functor(self.__handleCatch, num)))

        def cleanup(self = self, dropNode = dropNode, num = num, event = catchEventName):
            self.ignore(event)
            dropNode.removeNode()

        duration = objType.fallDuration
        onscreenDuration = objType.onscreenDuration
        dropHeight = self.MinOffscreenHeight
        targetShadowScale = 0.3
        if self.TrickShadows:
            intermedScale = targetShadowScale * (self.OffscreenTime / self.BaselineDropDuration)
            shadowScaleIval = Sequence(LerpScaleInterval(shadow, self.OffscreenTime, intermedScale, startScale=0))
            shadowScaleIval.append(LerpScaleInterval(shadow, duration - self.OffscreenTime, targetShadowScale, startScale=intermedScale))
        else:
            shadowScaleIval = LerpScaleInterval(shadow, duration, targetShadowScale, startScale=0)
        targetShadowAlpha = 0.4
        shadowAlphaIval = LerpColorScaleInterval(shadow, self.OffscreenTime, Point4(1, 1, 1, targetShadowAlpha), startColorScale=Point4(1, 1, 1, 0))
        shadowIval = Parallel(shadowScaleIval, shadowAlphaIval)
        if self.UseGravity:

            def setObjPos(t, objType = objType, object = object):
                z = objType.trajectory.calcZ(t)
                object.setZ(z)

            setObjPos(0)
            dropIval = LerpFunctionInterval(setObjPos, fromData=0, toData=onscreenDuration, duration=onscreenDuration)
        else:
            startPos = Point3(0, 0, self.MinOffscreenHeight)
            object.setPos(startPos)
            dropIval = LerpPosInterval(object, onscreenDuration, Point3(0, 0, 0), startPos=startPos, blendType='easeIn')
        ival = Sequence(Func(Functor(dropNode.reparentTo, render)), Parallel(Sequence(WaitInterval(self.OffscreenTime), dropIval), shadowIval), Func(cleanup), name='drop%s' % num)
        landSound = None
        if objType == Name2DropObjectType['anvil']:
            landSound = self.sndAnvilLand
        if landSound:
            ival.append(SoundInterval(landSound))
        return ival

    def startSuitWalkTask(self):
        ival = Parallel(name='catchGameMetaSuitWalk')
        rng = RandomNumGen(self.randomNumGen)
        delay = 0.0
        while delay < CatchGameGlobals.GameDuration:
            delay += lerp(self.SuitPeriodRange[0], self.SuitPeriodRange[0], rng.random())
            walkIval = Sequence(name='catchGameSuitWalk')
            walkIval.append(Wait(delay))

            def pickY(self = self, rng = rng):
                return lerp(-self.StageHalfHeight, self.StageHalfHeight, rng.random())

            m = [2.5,
             2.5,
             2.3,
             2.1][self.getNumPlayers() - 1]
            startPos = Point3(-(self.StageHalfWidth * m), pickY(), 0)
            stopPos = Point3(self.StageHalfWidth * m, pickY(), 0)
            if rng.choice([0, 1]):
                startPos, stopPos = stopPos, startPos
            walkIval.append(self.getSuitWalkIval(startPos, stopPos, rng))
            ival.append(walkIval)

        ival.start()
        self.suitWalkIval = ival

    def stopSuitWalkTask(self):
        self.suitWalkIval.finish()
        del self.suitWalkIval

    def getSuitWalkIval(self, startPos, stopPos, rng):
        data = {}
        lerpNP = render.attachNewNode('catchGameSuitParent')

        def setup(self = self, startPos = startPos, stopPos = stopPos, data = data, lerpNP = lerpNP, rng = rng):
            if len(self.suits) == 0:
                return
            suit = rng.choice(self.suits)
            data['suit'] = suit
            self.suits.remove(suit)
            suit.reparentTo(lerpNP)
            suit.loop('walk')
            suit.setPlayRate(self.SuitSpeed / ToontownGlobals.SuitWalkSpeed, 'walk')
            suit.setPos(0, 0, 0)
            lerpNP.setPos(startPos)
            suit.lookAt(stopPos)

        def cleanup(self = self, data = data, lerpNP = lerpNP):
            if 'suit' in data:
                suit = data['suit']
                suit.reparentTo(hidden)
                self.suits.append(suit)
            lerpNP.removeNode()

        distance = Vec3(stopPos - startPos).length()
        duration = distance / self.SuitSpeed
        ival = Sequence(FunctionInterval(setup), LerpPosInterval(lerpNP, duration, stopPos), FunctionInterval(cleanup))
        return ival

    def handleSuitCollision(self, collEntry):
        self.toonSDs[self.localAvId].fsm.request('fallBack')
        timestamp = globalClockDelta.localToNetworkTime(globalClock.getFrameTime())
        self.sendUpdate('hitBySuit', [self.localAvId, timestamp])

    def hitBySuit(self, avId, timestamp):
        if not self.hasLocalToon:
            return
        if self.gameFSM.getCurrentState().getName() != 'play':
            self.notify.warning('ignoring msg: av %s hit by suit' % avId)
            return
        toon = self.getAvatar(avId)
        if toon == None:
            return
        self.notify.debug('avatar %s hit by a suit' % avId)
        if avId != self.localAvId:
            self.toonSDs[avId].fsm.request('fallBack')
        return

    def enterCleanup(self):
        self.notify.debug('enterCleanup')

    def exitCleanup(self):
        pass

    def initOrthoWalk(self):
        self.notify.debug('startOrthoWalk')

        def doCollisions(oldPos, newPos, self = self):
            x = bound(newPos[0], self.StageHalfWidth, -self.StageHalfWidth)
            y = bound(newPos[1], self.StageHalfHeight, -self.StageHalfHeight)
            newPos.setX(x)
            newPos.setY(y)
            return newPos

        orthoDrive = OrthoDrive(self.ToonSpeed, customCollisionCallback=doCollisions)
        self.orthoWalk = OrthoWalk(orthoDrive, broadcast=not self.isSinglePlayer())

    def destroyOrthoWalk(self):
        self.notify.debug('destroyOrthoWalk')
        self.orthoWalk.destroy()
        del self.orthoWalk

    def getIntroMovie(self):
        locNode = self.ground.find('**/locator_tree')
        treeNode = locNode.attachNewNode('treeNode')
        treeNode.setHpr(render, 0, 0, 0)

        def cleanupTree(treeNode = treeNode):
            treeNode.removeNode()

        initialCamPosHpr = (-0.21,
         -19.56,
         13.94,
         0.0,
         26.57,
         0.0)
        suitViewCamPosHpr = (0, -11.5, 13, 0, -35, 0)
        finalCamPosHpr = self.CameraPosHpr
        cameraIval = Sequence(Func(camera.reparentTo, render), Func(camera.setPosHpr, treeNode, *initialCamPosHpr), WaitInterval(4.0), LerpPosHprInterval(camera, 2.0, Point3(*suitViewCamPosHpr[:3]), Point3(*suitViewCamPosHpr[3:]), blendType='easeInOut', name='lerpToSuitView'), WaitInterval(4.0), LerpPosHprInterval(camera, 3.0, Point3(*finalCamPosHpr[:3]), Point3(*finalCamPosHpr[3:]), blendType='easeInOut', name='lerpToPlayView'))

        def getIntroToon(toonProperties, parent, pos):
            toon = Toon.Toon()
            dna = ToonDNA.ToonDNA()
            dna.newToonFromProperties(*toonProperties)
            toon.setDNA(dna)
            toon.reparentTo(parent)
            toon.setPos(*pos)
            toon.setH(180)
            toon.startBlink()
            return toon

        def cleanupIntroToon(toon):
            toon.detachNode()
            toon.stopBlink()
            toon.delete()

        def getThrowIval(toon, hand, object, leftToon, isAnvil = 0):
            anim = 'catch-intro-throw'
            grabFrame = 12
            fullSizeFrame = 30
            framePeriod = 1.0 / toon.getFrameRate(anim)
            objScaleDur = (fullSizeFrame - grabFrame) * framePeriod
            releaseFrame = 35
            trajDuration = 1.6
            trajDistance = 4
            if leftToon:
                releaseFrame = 34
                trajDuration = 1.0
                trajDistance = 1
            animIval = ActorInterval(toon, anim, loop=0)

            def getThrowDest(object = object, offset = trajDistance):
                dest = object.getPos(render)
                dest += Point3(0, -offset, 0)
                dest.setZ(0)
                return dest

            if leftToon:
                trajIval = ProjectileInterval(object, startVel=Point3(0, 0, 0), duration=trajDuration)
            else:
                trajIval = ProjectileInterval(object, endPos=getThrowDest, duration=trajDuration)
            trajIval = Sequence(Func(object.wrtReparentTo, render), trajIval, Func(object.wrtReparentTo, hidden))
            if isAnvil:
                trajIval.append(SoundInterval(self.sndAnvilLand))
            objIval = Track((grabFrame * framePeriod, Sequence(Func(object.reparentTo, hand), Func(object.setPosHpr, 0.05, -.13, 0.62, 0, 0, 336.8), LerpScaleInterval(object, objScaleDur, 1.0, startScale=0.1, blendType='easeInOut'))), (releaseFrame * framePeriod, trajIval))

            def cleanup(object = object):
                object.reparentTo(hidden)
                object.removeNode()

            throwIval = Sequence(Parallel(animIval, objIval), Func(cleanup))
            return throwIval

        tY = -4.0
        tZ = 19.5
        props = ['css',
         'md',
         'm',
         'f',
         9,
         0,
         9,
         9,
         13,
         5,
         11,
         5,
         8,
         7]
        leftToon = getIntroToon(props, treeNode, [-2.3, tY, tZ])
        props = ['mss',
         'ls',
         'l',
         'm',
         6,
         0,
         6,
         6,
         3,
         5,
         3,
         5,
         5,
         0]
        rightToon = getIntroToon(props, treeNode, [1.8, tY, tZ])
        fruit = self.getObjModel(self.fruitName)
        if self.fruitName == 'pineapple':
            fruit.setZ(0.42)
            fruit.flattenMedium()
        anvil = self.getObjModel('anvil')
        anvil.setH(100)
        anvil.setZ(0.42)
        anvil.flattenMedium()
        leftToonIval = getThrowIval(leftToon, leftToon.getRightHands()[0], fruit, leftToon=1)
        rightToonIval = getThrowIval(rightToon, rightToon.getLeftHands()[0], anvil, leftToon=0, isAnvil=1)
        animDur = leftToon.getNumFrames('catch-intro-throw') / leftToon.getFrameRate('catch-intro-throw')
        toonIval = Sequence(Parallel(Sequence(leftToonIval, Func(leftToon.loop, 'neutral')), Sequence(Func(rightToon.loop, 'neutral'), WaitInterval(animDur / 2.0), rightToonIval, Func(rightToon.loop, 'neutral')), WaitInterval(cameraIval.getDuration())), Func(cleanupIntroToon, leftToon), Func(cleanupIntroToon, rightToon))
        self.treeNode = treeNode
        self.fruit = fruit
        self.anvil = anvil
        self.leftToon = leftToon
        self.rightToon = rightToon
        introMovie = Sequence(Parallel(cameraIval, toonIval), Func(cleanupTree))
        return introMovie
