from pandac.PandaModules import Vec3, Point3, Point4, TextNode, NodePath
from pandac.PandaModules import CollisionHandlerEvent, CollisionNode, CollisionSphere
from direct.distributed.ClockDelta import globalClockDelta
from direct.interval.IntervalGlobal import Sequence, Parallel
from direct.interval.IntervalGlobal import LerpScaleInterval, LerpFunctionInterval, LerpColorScaleInterval, LerpPosInterval
from direct.interval.IntervalGlobal import SoundInterval, WaitInterval
from direct.showbase.PythonUtil import Functor, bound, lerp, SerialNumGen
from direct.showbase.RandomNumGen import RandomNumGen
from direct.task.Task import Task
from direct.distributed import DistributedSmoothNode
from direct.directnotify import DirectNotifyGlobal
from direct.interval.FunctionInterval import Wait, Func
from toontown.toonbase import TTLocalizer
from toontown.toon import Toon
from toontown.toonbase import ToontownGlobals
from toontown.minigame.Trajectory import Trajectory
from toontown.minigame.OrthoDrive import OrthoDrive
from toontown.minigame.OrthoWalk import OrthoWalk
from toontown.minigame.DropPlacer import PartyRegionDropPlacer
from toontown.parties import PartyGlobals
from toontown.parties.PartyCatchActivityToonSD import PartyCatchActivityToonSD
from toontown.parties.DistributedPartyActivity import DistributedPartyActivity
from toontown.parties.DistributedPartyCatchActivityBase import DistributedPartyCatchActivityBase
from toontown.parties.DistributedPartyCannonActivity import DistributedPartyCannonActivity
from toontown.parties.activityFSMs import CatchActivityFSM

class DistributedPartyCatchActivity(DistributedPartyActivity, DistributedPartyCatchActivityBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPartyCatchActivity')
    DropTaskName = 'dropSomething'
    DropObjectPlurals = {'apple': TTLocalizer.PartyCatchActivityApples,
     'orange': TTLocalizer.PartyCatchActivityOranges,
     'pear': TTLocalizer.PartyCatchActivityPears,
     'coconut': TTLocalizer.PartyCatchActivityCoconuts,
     'watermelon': TTLocalizer.PartyCatchActivityWatermelons,
     'pineapple': TTLocalizer.PartyCatchActivityPineapples,
     'anvil': TTLocalizer.PartyCatchActivityAnvils}

    class Generation:

        def __init__(self, generation, startTime, startNetworkTime, numPlayers):
            self.generation = generation
            self.startTime = startTime
            self.startNetworkTime = startNetworkTime
            self.numPlayers = numPlayers
            self.hasBeenScheduled = False
            self.droppedObjNames = []
            self.dropSchedule = []
            self.numItemsDropped = 0
            self.droppedObjCaught = {}

    def __init__(self, cr):
        DistributedPartyActivity.__init__(self, cr, PartyGlobals.ActivityIds.PartyCatch, PartyGlobals.ActivityTypes.HostInitiated, wantRewardGui=True)
        self.setUsesSmoothing()
        self.setUsesLookAround()
        self._sNumGen = SerialNumGen()

    def getTitle(self):
        return TTLocalizer.PartyCatchActivityTitle

    def getInstructions(self):
        return TTLocalizer.PartyCatchActivityInstructions % {'badThing': self.DropObjectPlurals['anvil']}

    def generate(self):
        DistributedPartyActivity.generate(self)
        self.notify.info('localAvatar doId: %s' % base.localAvatar.doId)
        self.notify.info('generate()')
        self._generateFrame = globalClock.getFrameCount()
        self._id2gen = {}
        self._orderedGenerations = []
        self._orderedGenerationIndex = None
        rng = RandomNumGen(self.doId)
        self._generationSeedBase = rng.randrange(1000)
        self._lastDropTime = 0.0
        return

    def getCurGeneration(self):
        if self._orderedGenerationIndex is None:
            return
        return self._orderedGenerations[self._orderedGenerationIndex]

    def _addGeneration(self, generation, startTime, startNetworkTime, numPlayers):
        self._id2gen[generation] = self.Generation(generation, startTime, startNetworkTime, numPlayers)
        i = 0
        while 1:
            if i >= len(self._orderedGenerations):
                break
            gen = self._orderedGenerations[i]
            startNetT = self._id2gen[gen].startTime
            genId = self._id2gen[gen].generation
            if startNetT > startNetworkTime:
                break
            if startNetT == startNetworkTime and genId > generation:
                break
            i += 1
        self._orderedGenerations = self._orderedGenerations[:i] + [generation] + self._orderedGenerations[i:]
        if self._orderedGenerationIndex is not None:
            if self._orderedGenerationIndex >= i:
                self._orderedGenerationIndex += 1

    def _removeGeneration(self, generation):
        del self._id2gen[generation]
        i = self._orderedGenerations.index(generation)
        self._orderedGenerations = self._orderedGenerations[:i] + self._orderedGenerations[i + 1:]
        if self._orderedGenerationIndex is not None:
            if len(self._orderedGenerations):
                if self._orderedGenerationIndex >= i:
                    self._orderedGenerationIndex -= 1
            else:
                self._orderedGenerationIndex = None
        return

    def announceGenerate(self):
        self.notify.info('announceGenerate()')
        self.catchTreeZoneEvent = 'fence_floor'
        DistributedPartyActivity.announceGenerate(self)

    def load(self, loadModels = 1, arenaModel = 'partyCatchTree'):
        self.notify.info('load()')
        DistributedPartyCatchActivity.notify.debug('PartyCatch: load')
        self.activityFSM = CatchActivityFSM(self)
        if __dev__:
            for o in range(3):
                print({0: 'SPOTS PER PLAYER',
                 1: 'DROPS PER MINUTE PER SPOT DURING NORMAL DROP PERIOD',
                 2: 'DROPS PER MINUTE PER PLAYER DURING NORMAL DROP PERIOD'}[o])
                for i in range(1, self.FallRateCap_Players + 10):
                    self.defineConstants(forceNumPlayers=i)
                    numDropLocations = self.DropRows * self.DropColumns
                    numDropsPerMin = 60.0 / self.DropPeriod
                    if o == 0:
                        spotsPerPlayer = numDropLocations / float(i)
                        print('%2d PLAYERS: %s' % (i, spotsPerPlayer))
                    elif o == 1:
                        numDropsPerMinPerSpot = numDropsPerMin / numDropLocations
                        print('%2d PLAYERS: %s' % (i, numDropsPerMinPerSpot))
                    elif i > 0:
                        numDropsPerMinPerPlayer = numDropsPerMin / i
                        print('%2d PLAYERS: %s' % (i, numDropsPerMinPerPlayer))

        self.defineConstants()
        self.treesAndFence = loader.loadModel('phase_13/models/parties/%s' % arenaModel)
        self.treesAndFence.setScale(0.9)
        self.treesAndFence.find('**/fence_floor').setPos(0.0, 0.0, 0.1)
        self.treesAndFence.reparentTo(self.root)
        ground = self.treesAndFence.find('**/groundPlane')
        ground.setBin('ground', 1)
        DistributedPartyActivity.load(self)
        exitText = TextNode('PartyCatchExitText')
        exitText.setCardAsMargin(0.1, 0.1, 0.1, 0.1)
        exitText.setCardDecal(True)
        exitText.setCardColor(1.0, 1.0, 1.0, 0.0)
        exitText.setText(TTLocalizer.PartyCatchActivityExit)
        exitText.setTextColor(0.0, 8.0, 0.0, 0.9)
        exitText.setAlign(exitText.ACenter)
        exitText.setFont(ToontownGlobals.getBuildingNametagFont())
        exitText.setShadowColor(0, 0, 0, 1)
        exitText.setBin('fixed')
        if TTLocalizer.BuildingNametagShadow:
            exitText.setShadow(*TTLocalizer.BuildingNametagShadow)
        exitTextLoc = self.treesAndFence.find('**/loc_exitSignText')
        exitTextNp = exitTextLoc.attachNewNode(exitText)
        exitTextNp.setDepthWrite(0)
        exitTextNp.setScale(4)
        exitTextNp.setZ(-.5)
        self.sign.reparentTo(self.treesAndFence.find('**/loc_eventSign'))
        self.sign.wrtReparentTo(self.root)
        self.avatarNodePath = NodePath('PartyCatchAvatarNodePath')
        self.avatarNodePath.reparentTo(self.root)
        self._avatarNodePathParentToken = 3
        base.cr.parentMgr.registerParent(self._avatarNodePathParentToken, self.avatarNodePath)
        self.toonSDs = {}
        self.dropShadow = loader.loadModelOnce('phase_3/models/props/drop_shadow')
        self.dropObjModels = {}
        if loadModels:
            self.__loadDropModels()
        self.sndGoodCatch = base.loader.loadSfx('phase_4/audio/sfx/SZ_DD_treasure.ogg')
        self.sndOof = base.loader.loadSfx('phase_4/audio/sfx/MG_cannon_hit_dirt.ogg')
        self.sndAnvilLand = base.loader.loadSfx('phase_4/audio/sfx/AA_drop_anvil_miss.ogg')
        self.sndPerfect = base.loader.loadSfx('phase_4/audio/sfx/ring_perfect.ogg')
        self.__textGen = TextNode('partyCatchActivity')
        self.__textGen.setFont(ToontownGlobals.getSignFont())
        self.__textGen.setAlign(TextNode.ACenter)
        self.activityFSM.request('Idle')

    def __loadDropModels(self):
        for objType in PartyGlobals.DropObjectTypes:
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
            if objType == PartyGlobals.Name2DropObjectType['pear']:
                model.setZ(-.6)
            if objType == PartyGlobals.Name2DropObjectType['coconut']:
                model.setP(180)
            if objType == PartyGlobals.Name2DropObjectType['watermelon']:
                model.setH(135)
                model.setZ(-.5)
            if objType == PartyGlobals.Name2DropObjectType['pineapple']:
                model.setZ(-1.7)
            if objType == PartyGlobals.Name2DropObjectType['anvil']:
                model.setZ(-self.ObjRadius)
            model.flattenStrong()

    def unload(self):
        DistributedPartyCatchActivity.notify.debug('unload')
        self.finishAllDropIntervals()
        self.destroyOrthoWalk()
        DistributedPartyActivity.unload(self)
        self.stopDropTask()
        del self.activityFSM
        del self.__textGen
        for avId in list(self.toonSDs.keys()):
            if avId in self.toonSDs:
                toonSD = self.toonSDs[avId]
                toonSD.unload()

        del self.toonSDs
        self.treesAndFence.removeNode()
        del self.treesAndFence
        self.dropShadow.removeNode()
        del self.dropShadow
        base.cr.parentMgr.unregisterParent(self._avatarNodePathParentToken)
        for model in list(self.dropObjModels.values()):
            model.removeNode()

        del self.dropObjModels
        del self.sndGoodCatch
        del self.sndOof
        del self.sndAnvilLand
        del self.sndPerfect

    def setStartTimestamp(self, timestamp32):
        self.notify.info('setStartTimestamp(%s)' % (timestamp32,))
        self._startTimestamp = globalClockDelta.networkToLocalTime(timestamp32, bits=32)

    def getCurrentCatchActivityTime(self):
        return globalClock.getFrameTime() - self._startTimestamp

    def getObjModel(self, objName):
        return self.dropObjModels[objName].copyTo(hidden)

    def joinRequestDenied(self, reason):
        DistributedPartyActivity.joinRequestDenied(self, reason)
        base.cr.playGame.getPlace().fsm.request('walk')

    def handleToonJoined(self, toonId):
        if toonId not in self.toonSDs:
            toonSD = PartyCatchActivityToonSD(toonId, self)
            self.toonSDs[toonId] = toonSD
            toonSD.load()
        self.notify.debug('handleToonJoined : currentState = %s' % self.activityFSM.state)
        self.cr.doId2do[toonId].useLOD(500)
        if self.activityFSM.state == 'Active':
            if toonId in self.toonSDs:
                self.toonSDs[toonId].enter()
            if base.localAvatar.doId == toonId:
                base.localAvatar.b_setParent(self._avatarNodePathParentToken)
                self.putLocalAvatarInActivity()
            if toonId in self.toonSDs:
                self.toonSDs[toonId].fsm.request('rules')

    def handleToonExited(self, toonId):
        self.notify.debug('handleToonExited( toonId=%s )' % toonId)
        if toonId in self.cr.doId2do:
            self.cr.doId2do[toonId].resetLOD()
            if toonId in self.toonSDs:
                self.toonSDs[toonId].fsm.request('notPlaying')
                self.toonSDs[toonId].exit()
                self.toonSDs[toonId].unload()
                del self.toonSDs[toonId]
            if base.localAvatar.doId == toonId:
                base.localAvatar.b_setParent(ToontownGlobals.SPRender)

    def takeLocalAvatarOutOfActivity(self):
        self.notify.debug('localToon has left the circle')
        camera.reparentTo(base.localAvatar)
        base.localAvatar.startUpdateSmartCamera()
        base.localAvatar.enableSmartCameraViews()
        base.localAvatar.setCameraPositionByIndex(base.localAvatar.cameraIndex)
        DistributedSmoothNode.activateSmoothing(1, 0)

    def _enableCollisions(self):
        DistributedPartyActivity._enableCollisions(self)
        self._enteredTree = False
        self.accept('enter' + self.catchTreeZoneEvent, self._toonMayHaveEnteredTree)
        self.accept('again' + self.catchTreeZoneEvent, self._toonMayHaveEnteredTree)
        self.accept('exit' + self.catchTreeZoneEvent, self._toonExitedTree)
        self.accept(DistributedPartyCannonActivity.LOCAL_TOON_LANDED_EVENT, self._handleCannonLanded)

    def _disableCollisions(self):
        self.ignore(DistributedPartyCannonActivity.LOCAL_TOON_LANDED_EVENT)
        self.ignore('enter' + self.catchTreeZoneEvent)
        self.ignore('again' + self.catchTreeZoneEvent)
        self.ignore('exit' + self.catchTreeZoneEvent)
        DistributedPartyActivity._disableCollisions(self)

    def _handleCannonLanded(self):
        x = base.localAvatar.getX()
        y = base.localAvatar.getY()
        if x > self.x - self.StageHalfWidth and x < self.x + self.StageHalfWidth and y > self.y - self.StageHalfHeight and y < self.y + self.StageHalfHeight:
            self._toonEnteredTree(None)
        return

    def _toonMayHaveEnteredTree(self, collEntry):
        if self._enteredTree:
            return
        if base.localAvatar.controlManager.currentControls.getIsAirborne():
            return
        self._toonEnteredTree(collEntry)

    def _toonEnteredTree(self, collEntry):
        self.notify.debug('_toonEnteredTree : avid = %s' % base.localAvatar.doId)
        self.notify.debug('_toonEnteredTree : currentState = %s' % self.activityFSM.state)
        if self.isLocalToonInActivity():
            return
        if self.activityFSM.state == 'Active':
            base.cr.playGame.getPlace().fsm.request('activity')
            self.d_toonJoinRequest()
        elif self.activityFSM.state == 'Idle':
            base.cr.playGame.getPlace().fsm.request('activity')
            self.d_toonJoinRequest()
        self._enteredTree = True

    def _toonExitedTree(self, collEntry):
        self.notify.debug('_toonExitedTree : avid = %s' % base.localAvatar.doId)
        self._enteredTree = False
        if hasattr(base.cr.playGame.getPlace(), 'fsm') and self.activityFSM.state == 'Active' and self.isLocalToonInActivity():
            if base.localAvatar.doId in self.toonSDs:
                self.takeLocalAvatarOutOfActivity()
                self.toonSDs[base.localAvatar.doId].fsm.request('notPlaying')
            self.d_toonExitDemand()

    def setToonsPlaying(self, toonIds):
        self.notify.info('setToonsPlaying(%s)' % (toonIds,))
        DistributedPartyActivity.setToonsPlaying(self, toonIds)
        if self.isLocalToonInActivity() and base.localAvatar.doId not in toonIds:
            if base.localAvatar.doId in self.toonSDs:
                self.takeLocalAvatarOutOfActivity()
                self.toonSDs[base.localAvatar.doId].fsm.request('notPlaying')

    def __genText(self, text):
        self.__textGen.setText(text)
        return self.__textGen.generate()

    def getNumPlayers(self):
        return len(self.toonIds)

    def defineConstants(self, forceNumPlayers = None):
        DistributedPartyCatchActivity.notify.debug('defineConstants')
        self.ShowObjSpheres = 0
        self.ShowToonSpheres = 0
        self.useGravity = True
        self.trickShadows = True
        if forceNumPlayers is None:
            numPlayers = self.getNumPlayers()
        else:
            numPlayers = forceNumPlayers
        self.calcDifficultyConstants(numPlayers)
        DistributedPartyCatchActivity.notify.debug('ToonSpeed: %s' % self.ToonSpeed)
        DistributedPartyCatchActivity.notify.debug('total drops: %s' % self.totalDrops)
        DistributedPartyCatchActivity.notify.debug('numFruits: %s' % self.numFruits)
        DistributedPartyCatchActivity.notify.debug('numAnvils: %s' % self.numAnvils)
        self.ObjRadius = 1.0
        dropRegionTable = PartyRegionDropPlacer.getDropRegionTable(numPlayers)
        self.DropRows, self.DropColumns = len(dropRegionTable), len(dropRegionTable[0])
        for objType in PartyGlobals.DropObjectTypes:
            DistributedPartyCatchActivity.notify.debug('*** Object Type: %s' % objType.name)
            objType.onscreenDuration = objType.onscreenDurMult * self.BaselineOnscreenDropDuration
            DistributedPartyCatchActivity.notify.debug('onscreenDuration=%s' % objType.onscreenDuration)
            v_0 = 0.0
            t = objType.onscreenDuration
            x_0 = self.MinOffscreenHeight
            x = 0.0
            g = 2.0 * (x - x_0 - v_0 * t) / (t * t)
            DistributedPartyCatchActivity.notify.debug('gravity=%s' % g)
            objType.trajectory = Trajectory(0, Vec3(0, 0, x_0), Vec3(0, 0, v_0), gravMult=abs(g / Trajectory.gravity))
            objType.fallDuration = objType.onscreenDuration + self.OffscreenTime

        return

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
            tree = self.posts[i]
            tree.reparentTo(render)
            x = self.StageHalfWidth
            y = self.StageHalfHeight
            if i > 1:
                x = -x
            if i % 2:
                y = -y
            tree.setPos(x + self.x, y + self.y, 0)

    def hidePosts(self):
        if hasattr(self, 'posts'):
            for tree in self.posts:
                tree.removeNode()

            del self.posts

    def showDropGrid(self):
        self.hideDropGrid()
        self.dropMarkers = []
        for row in range(self.DropRows):
            self.dropMarkers.append([])
            rowList = self.dropMarkers[row]
            for column in range(self.DropColumns):
                toon = Toon.Toon()
                toon.setDNA(base.localAvatar.getStyle())
                toon.reparentTo(self.root)
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

    def handleToonDisabled(self, avId):
        DistributedPartyCatchActivity.notify.debug('handleToonDisabled')
        DistributedPartyCatchActivity.notify.debug('avatar ' + str(avId) + ' disabled')
        if avId in self.toonSDs:
            self.toonSDs[avId].exit(unexpectedExit=True)
        del self.toonSDs[avId]

    def turnOffSmoothingOnGuests(self):
        pass

    def setState(self, newState, timestamp):
        self.notify.info('setState(%s, %s)' % (newState, timestamp))
        DistributedPartyCatchActivity.notify.debug('setState( newState=%s, ... )' % newState)
        DistributedPartyActivity.setState(self, newState, timestamp)
        self.activityFSM.request(newState)
        if newState == 'Active':
            if base.localAvatar.doId != self.party.partyInfo.hostId:
                if globalClock.getFrameCount() > self._generateFrame:
                    if base.localAvatar.getX() > self.x - self.StageHalfWidth and base.localAvatar.getX() < self.x + self.StageHalfWidth and base.localAvatar.getY() > self.y - self.StageHalfHeight and base.localAvatar.getY() < self.y + self.StageHalfHeight:
                        self._toonEnteredTree(None)
        return

    def putLocalAvatarInActivity(self):
        if base.cr.playGame.getPlace() and hasattr(base.cr.playGame.getPlace(), 'fsm'):
            base.cr.playGame.getPlace().fsm.request('activity', [False])
        else:
            self.notify.info("Avoided crash: toontown.parties.DistributedPartyCatchActivity:632, toontown.parties.DistributedPartyCatchActivity:1198, toontown.parties.activityFSMMixins:49, direct.fsm.FSM:423, AttributeError: 'NoneType' object has no attribute 'fsm'")
        base.localAvatar.stopUpdateSmartCamera()
        camera.reparentTo(self.treesAndFence)
        camera.setPosHpr(0.0, -63.0, 30.0, 0.0, -20.0, 0.0)
        if not hasattr(self, 'ltLegsCollNode'):
            self.createCatchCollisions()

    def createCatchCollisions(self):
        radius = 0.7
        handler = CollisionHandlerEvent()
        handler.setInPattern('ltCatch%in')
        self.ltLegsCollNode = CollisionNode('catchLegsCollNode')
        self.ltLegsCollNode.setCollideMask(PartyGlobals.CatchActivityBitmask)
        self.ltHeadCollNode = CollisionNode('catchHeadCollNode')
        self.ltHeadCollNode.setCollideMask(PartyGlobals.CatchActivityBitmask)
        self.ltLHandCollNode = CollisionNode('catchLHandCollNode')
        self.ltLHandCollNode.setCollideMask(PartyGlobals.CatchActivityBitmask)
        self.ltRHandCollNode = CollisionNode('catchRHandCollNode')
        self.ltRHandCollNode.setCollideMask(PartyGlobals.CatchActivityBitmask)
        legsCollNodepath = base.localAvatar.attachNewNode(self.ltLegsCollNode)
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
        base.localAvatar.cTrav.addCollider(legsCollNodepath, handler)
        base.localAvatar.cTrav.addCollider(headCollNodepath, handler)
        base.localAvatar.cTrav.addCollider(lHandCollNodepath, handler)
        base.localAvatar.cTrav.addCollider(lHandCollNodepath, handler)
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

    def destroyCatchCollisions(self):
        if not hasattr(self, 'ltLegsCollNode'):
            return
        for collNode in self.toonCollNodes:
            while collNode.node().getNumSolids():
                collNode.node().removeSolid(0)

            base.localAvatar.cTrav.removeCollider(collNode)

        del self.toonCollNodes
        del self.ltLegsCollNode
        del self.ltHeadCollNode
        del self.ltLHandCollNode
        del self.ltRHandCollNode

    def timerExpired(self):
        pass

    def __handleCatch(self, generation, objNum):
        DistributedPartyCatchActivity.notify.debug('catch: %s' % [generation, objNum])
        if base.localAvatar.doId not in self.toonIds:
            return
        self.showCatch(base.localAvatar.doId, generation, objNum)
        objName = self._id2gen[generation].droppedObjNames[objNum]
        objTypeId = PartyGlobals.Name2DOTypeId[objName]
        self.sendUpdate('claimCatch', [generation, objNum, objTypeId])
        self.finishDropInterval(generation, objNum)

    def showCatch(self, avId, generation, objNum):
        if avId not in self.toonSDs:
            return
        isLocal = avId == base.localAvatar.doId
        if generation not in self._id2gen:
            return
        if not self._id2gen[generation].hasBeenScheduled:
            return
        objName = self._id2gen[generation].droppedObjNames[objNum]
        objType = PartyGlobals.Name2DropObjectType[objName]
        if objType.good:
            if objNum not in self._id2gen[generation].droppedObjCaught:
                if isLocal:
                    base.playSfx(self.sndGoodCatch)
                fruit = self.getObjModel(objName)
                toon = self.getAvatar(avId)
                rHand = toon.getRightHands()[1]
                self.toonSDs[avId].eatFruit(fruit, rHand)
        else:
            self.toonSDs[avId].fsm.request('fallForward')
        self._id2gen[generation].droppedObjCaught[objNum] = 1

    def setObjectCaught(self, avId, generation, objNum):
        self.notify.info('setObjectCaught(%s, %s, %s)' % (avId, generation, objNum))
        if self.activityFSM.state != 'Active':
            DistributedPartyCatchActivity.notify.warning('ignoring msg: object %s caught by %s' % (objNum, avId))
            return
        isLocal = avId == base.localAvatar.doId
        if not isLocal:
            DistributedPartyCatchActivity.notify.debug('AI: avatar %s caught %s' % (avId, objNum))
            self.finishDropInterval(generation, objNum)
            self.showCatch(avId, generation, objNum)
        self._scheduleGenerations()
        gen = self._id2gen[generation]
        if gen.hasBeenScheduled:
            objName = gen.droppedObjNames[objNum]
            if PartyGlobals.Name2DropObjectType[objName].good:
                if hasattr(self, 'fruitsCaught'):
                    self.fruitsCaught += 1

    def finishDropInterval(self, generation, objNum):
        if hasattr(self, 'dropIntervals'):
            if (generation, objNum) in self.dropIntervals:
                self.dropIntervals[generation, objNum].finish()

    def finishAllDropIntervals(self):
        if hasattr(self, 'dropIntervals'):
            for dropInterval in list(self.dropIntervals.values()):
                dropInterval.finish()

    def setGenerations(self, generations):
        self.notify.info('setGenerations(%s)' % (generations,))
        gen2t = {}
        gen2nt = {}
        gen2np = {}
        for id, timestamp32, numPlayers in generations:
            gen2t[id] = globalClockDelta.networkToLocalTime(timestamp32, bits=32) - self._startTimestamp
            gen2nt[id] = timestamp32
            gen2np[id] = numPlayers

        ids = list(self._id2gen.keys())
        for id in ids:
            if id not in gen2t:
                self._removeGeneration(id)

        for id in gen2t:
            if id not in self._id2gen:
                self._addGeneration(id, gen2t[id], gen2nt[id], gen2np[id])

    def scheduleDrops(self, genId = None):
        if genId is None:
            genId = self.getCurGeneration()
        gen = self._id2gen[genId]
        if gen.hasBeenScheduled:
            return
        fruitIndex = int((gen.startTime + 0.5 * self.DropPeriod) / PartyGlobals.CatchActivityDuration)
        fruitNames = ['apple',
         'orange',
         'pear',
         'coconut',
         'watermelon',
         'pineapple']
        fruitName = fruitNames[fruitIndex % len(fruitNames)]
        rng = RandomNumGen(genId + self._generationSeedBase)
        gen.droppedObjNames = [fruitName] * self.numFruits + ['anvil'] * self.numAnvils
        rng.shuffle(gen.droppedObjNames)
        dropPlacer = PartyRegionDropPlacer(self, gen.numPlayers, genId, gen.droppedObjNames, startTime=gen.startTime)
        gen.numItemsDropped = 0
        tIndex = gen.startTime % PartyGlobals.CatchActivityDuration
        tPercent = float(tIndex) / PartyGlobals.CatchActivityDuration
        gen.numItemsDropped += dropPlacer.skipPercent(tPercent)
        while not dropPlacer.doneDropping(continuous=True):
            nextDrop = dropPlacer.getNextDrop()
            gen.dropSchedule.append(nextDrop)

        gen.hasBeenScheduled = True
        return

    def startDropTask(self):
        taskMgr.add(self.dropTask, self.DropTaskName)

    def stopDropTask(self):
        taskMgr.remove(self.DropTaskName)

    def _scheduleGenerations(self):
        curT = self.getCurrentCatchActivityTime()
        genIndex = self._orderedGenerationIndex
        newGenIndex = genIndex
        while genIndex is None or genIndex < len(self._orderedGenerations) - 1:
            if genIndex is None:
                nextGenIndex = 0
            else:
                nextGenIndex = genIndex + 1
            nextGenId = self._orderedGenerations[nextGenIndex]
            nextGen = self._id2gen[nextGenId]
            startT = nextGen.startTime
            if curT >= startT:
                newGenIndex = nextGenIndex
            if not nextGen.hasBeenScheduled:
                self.defineConstants(forceNumPlayers=nextGen.numPlayers)
                self.scheduleDrops(genId=self._orderedGenerations[nextGenIndex])
            genIndex = nextGenIndex

        self._orderedGenerationIndex = newGenIndex
        return

    def dropTask(self, task):
        self._scheduleGenerations()
        curT = self.getCurrentCatchActivityTime()
        if self._orderedGenerationIndex is not None:
            i = self._orderedGenerationIndex
            genIndex = self._orderedGenerations[i]
            gen = self._id2gen[genIndex]
            while len(gen.dropSchedule) > 0 and gen.dropSchedule[0][0] < curT:
                drop = gen.dropSchedule[0]
                gen.dropSchedule = gen.dropSchedule[1:]
                dropTime, objName, dropCoords = drop
                objNum = gen.numItemsDropped
                x, y = self.grid2world(*dropCoords)
                dropIval = self.getDropIval(x, y, objName, genIndex, objNum)

                def cleanup(generation, objNum, self = self):
                    del self.dropIntervals[generation, objNum]

                dropIval.append(Func(Functor(cleanup, genIndex, objNum)))
                self.dropIntervals[genIndex, objNum] = dropIval
                gen.numItemsDropped += 1
                dropIval.start(curT - dropTime)
                self._lastDropTime = dropTime

        return Task.cont

    def getDropIval(self, x, y, dropObjName, generation, num):
        objType = PartyGlobals.Name2DropObjectType[dropObjName]
        id = (generation, num)
        dropNode = hidden.attachNewNode('catchDropNode%s' % (id,))
        dropNode.setPos(x, y, 0)
        shadow = self.dropShadow.copyTo(dropNode)
        shadow.setZ(PartyGlobals.CatchDropShadowHeight)
        shadow.setColor(1, 1, 1, 1)
        object = self.getObjModel(dropObjName)
        object.reparentTo(hidden)
        if dropObjName in ['watermelon', 'anvil']:
            objH = object.getH()
            absDelta = {'watermelon': 12,
             'anvil': 15}[dropObjName]
            delta = (self.randomNumGen.random() * 2.0 - 1.0) * absDelta
            newH = objH + delta
        else:
            newH = self.randomNumGen.random() * 360.0
        object.setH(newH)
        sphereName = 'FallObj%s' % (id,)
        radius = self.ObjRadius
        if objType.good:
            radius *= lerp(1.0, 1.3, 0.5)
        collSphere = CollisionSphere(0, 0, 0, radius)
        collSphere.setTangible(0)
        collNode = CollisionNode(sphereName)
        collNode.setCollideMask(PartyGlobals.CatchActivityBitmask)
        collNode.addSolid(collSphere)
        collNodePath = object.attachNewNode(collNode)
        collNodePath.hide()
        if self.ShowObjSpheres:
            collNodePath.show()
        catchEventName = 'ltCatch' + sphereName

        def eatCollEntry(forward, collEntry):
            forward()

        self.accept(catchEventName, Functor(eatCollEntry, Functor(self.__handleCatch, id[0], id[1])))

        def cleanup(self = self, dropNode = dropNode, id = id, event = catchEventName):
            self.ignore(event)
            dropNode.removeNode()

        duration = objType.fallDuration
        onscreenDuration = objType.onscreenDuration
        targetShadowScale = 0.3
        if self.trickShadows:
            intermedScale = targetShadowScale * (self.OffscreenTime / self.BaselineDropDuration)
            shadowScaleIval = Sequence(LerpScaleInterval(shadow, self.OffscreenTime, intermedScale, startScale=0))
            shadowScaleIval.append(LerpScaleInterval(shadow, duration - self.OffscreenTime, targetShadowScale, startScale=intermedScale))
        else:
            shadowScaleIval = LerpScaleInterval(shadow, duration, targetShadowScale, startScale=0)
        targetShadowAlpha = 0.4
        shadowAlphaIval = LerpColorScaleInterval(shadow, self.OffscreenTime, Point4(1, 1, 1, targetShadowAlpha), startColorScale=Point4(1, 1, 1, 0))
        shadowIval = Parallel(shadowScaleIval, shadowAlphaIval)
        if self.useGravity:

            def setObjPos(t, objType = objType, object = object):
                z = objType.trajectory.calcZ(t)
                object.setZ(z)

            setObjPos(0)
            dropIval = LerpFunctionInterval(setObjPos, fromData=0, toData=onscreenDuration, duration=onscreenDuration)
        else:
            startPos = Point3(0, 0, self.MinOffscreenHeight)
            object.setPos(startPos)
            dropIval = LerpPosInterval(object, onscreenDuration, Point3(0, 0, 0), startPos=startPos, blendType='easeIn')
        ival = Sequence(Func(Functor(dropNode.reparentTo, self.root)), Parallel(Sequence(WaitInterval(self.OffscreenTime), Func(Functor(object.reparentTo, dropNode)), dropIval), shadowIval), Func(cleanup), name='drop%s' % (id,))
        if objType == PartyGlobals.Name2DropObjectType['anvil']:
            ival.append(Func(self.playAnvil))
        return ival

    def playAnvil(self):
        if base.localAvatar.doId in self.toonIds:
            base.playSfx(self.sndAnvilLand)

    def initOrthoWalk(self):
        DistributedPartyCatchActivity.notify.debug('startOrthoWalk')

        def doCollisions(oldPos, newPos, self = self):
            x = bound(newPos[0], self.StageHalfWidth, -self.StageHalfWidth)
            y = bound(newPos[1], self.StageHalfHeight, -self.StageHalfHeight)
            newPos.setX(x)
            newPos.setY(y)
            return newPos

        orthoDrive = OrthoDrive(self.ToonSpeed, instantTurn=True)
        self.orthoWalk = OrthoWalk(orthoDrive, broadcast=True)

    def destroyOrthoWalk(self):
        DistributedPartyCatchActivity.notify.debug('destroyOrthoWalk')
        if hasattr(self, 'orthoWalk'):
            self.orthoWalk.stop()
            self.orthoWalk.destroy()
            del self.orthoWalk

    def startIdle(self):
        DistributedPartyCatchActivity.notify.debug('startIdle')

    def finishIdle(self):
        DistributedPartyCatchActivity.notify.debug('finishIdle')

    def startActive(self):
        DistributedPartyCatchActivity.notify.debug('startActive')
        for avId in self.toonIds:
            if avId in self.toonSDs:
                toonSD = self.toonSDs[avId]
                toonSD.enter()
                toonSD.fsm.request('normal')

        self.fruitsCaught = 0
        self.dropIntervals = {}
        self.startDropTask()
        if base.localAvatar.doId in self.toonIds:
            self.putLocalAvatarInActivity()

    def finishActive(self):
        DistributedPartyCatchActivity.notify.debug('finishActive')
        self.stopDropTask()
        if hasattr(self, 'finishIval'):
            self.finishIval.pause()
            del self.finishIval
        if base.localAvatar.doId in self.toonIds:
            self.takeLocalAvatarOutOfActivity()
        for ival in list(self.dropIntervals.values()):
            ival.finish()

        del self.dropIntervals

    def startConclusion(self):
        DistributedPartyCatchActivity.notify.debug('startConclusion')
        for avId in self.toonIds:
            if avId in self.toonSDs:
                toonSD = self.toonSDs[avId]
                toonSD.fsm.request('notPlaying')

        self.destroyCatchCollisions()
        if base.localAvatar.doId not in self.toonIds:
            return
        else:
            self.localToonExiting()
        if self.fruitsCaught >= self.numFruits:
            finishText = TTLocalizer.PartyCatchActivityFinishPerfect
        else:
            finishText = TTLocalizer.PartyCatchActivityFinish
        perfectTextSubnode = hidden.attachNewNode(self.__genText(finishText))
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

        textTrack = Sequence(Func(perfectText.reparentTo, aspect2d), Parallel(LerpScaleInterval(perfectText, duration=0.5, scale=0.3, startScale=0.0), LerpFunctionInterval(fadeFunc, fromData=0.0, toData=1.0, duration=0.5)), Wait(2.0), Parallel(LerpScaleInterval(perfectText, duration=0.5, scale=1.0), LerpFunctionInterval(fadeFunc, fromData=1.0, toData=0.0, duration=0.5, blendType='easeIn')), Func(destroyText), WaitInterval(0.5))
        soundTrack = SoundInterval(self.sndPerfect)
        self.finishIval = Parallel(textTrack, soundTrack)
        self.finishIval.start()

    def finishConclusion(self):
        DistributedPartyCatchActivity.notify.debug('finishConclusion')
        if base.localAvatar.doId in self.toonIds:
            self.takeLocalAvatarOutOfActivity()
            base.cr.playGame.getPlace().fsm.request('walk')

    def showJellybeanReward(self, earnedAmount, jarAmount, message):
        if earnedAmount > 0:
            DistributedPartyActivity.showJellybeanReward(self, earnedAmount, jarAmount, message)
        else:
            base.cr.playGame.getPlace().fsm.request('walk')
