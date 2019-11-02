from pandac.PandaModules import *
from toontown.toonbase.ToontownGlobals import *
from direct.interval.IntervalGlobal import *
from direct.fsm import ClassicFSM, State
from toontown.safezone import SafeZoneLoader
import random
from toontown.launcher import DownloadForceAcknowledge
import House
import Estate
import HouseGlobals
import random
import math
from toontown.coghq import MovingPlatform
from direct.directnotify import DirectNotifyGlobal

class EstateLoader(SafeZoneLoader.SafeZoneLoader):
    notify = DirectNotifyGlobal.directNotify.newCategory('EstateLoader')

    def __init__(self, hood, parentFSM, doneEvent):
        SafeZoneLoader.SafeZoneLoader.__init__(self, hood, parentFSM, doneEvent)
        del self.fsm
        self.fsm = ClassicFSM.ClassicFSM('EstateLoader', [State.State('start', self.enterStart, self.exitStart, ['quietZone', 'estate', 'house']),
         State.State('estate', self.enterEstate, self.exitEstate, ['quietZone']),
         State.State('house', self.enterHouse, self.exitHouse, ['quietZone']),
         State.State('quietZone', self.enterQuietZone, self.exitQuietZone, ['house', 'estate']),
         State.State('final', self.enterFinal, self.exitFinal, ['start'])], 'start', 'final')
        self.musicFile = 'phase_4/audio/bgm/TC_nbrhood.mid'
        self.activityMusicFile = 'phase_3.5/audio/bgm/TC_SZ_activity.mid'
        self.dnaFile = 'phase_5.5/dna/estate_1.dna'
        self.safeZoneStorageDNAFile = None
        self.cloudSwitch = 0
        self.id = MyEstate
        self.estateOwnerId = None
        self.branchZone = None
        self.houseDoneEvent = 'houseDone'
        self.estateDoneEvent = 'estateDone'
        self.enteredHouse = None
        self.houseNode = [None] * 6
        self.houseModels = [None] * HouseGlobals.NUM_HOUSE_TYPES
        self.houseId2house = {}
        self.barrel = None
        self.clouds = []
        self.cloudTrack = None
        self.sunMoonNode = None
        self.fsm.enterInitialState()
        return

    def load(self):
        SafeZoneLoader.SafeZoneLoader.load(self)
        self.music = base.loadMusic('phase_4/audio/bgm/TC_nbrhood.mid')
        self.underwaterSound = base.loadSfx('phase_4/audio/sfx/AV_ambient_water.mp3')
        self.swimSound = base.loadSfx('phase_4/audio/sfx/AV_swim_single_stroke.mp3')
        self.submergeSound = base.loadSfx('phase_5.5/audio/sfx/AV_jump_in_water.mp3')
        self.birdSound = map(base.loadSfx, ['phase_4/audio/sfx/SZ_TC_bird1.mp3', 'phase_4/audio/sfx/SZ_TC_bird2.mp3', 'phase_4/audio/sfx/SZ_TC_bird3.mp3'])
        self.cricketSound = map(base.loadSfx, ['phase_4/audio/sfx/SZ_TC_bird1.mp3', 'phase_4/audio/sfx/SZ_TC_bird2.mp3', 'phase_4/audio/sfx/SZ_TC_bird3.mp3'])
        if base.goonsEnabled:
            invModel = loader.loadModel('phase_3.5/models/gui/inventory_icons')
            self.invModels = []
            from toontown.toonbase import ToontownBattleGlobals
            for track in range(len(ToontownBattleGlobals.AvPropsNew)):
                itemList = []
                for item in range(len(ToontownBattleGlobals.AvPropsNew[track])):
                    itemList.append(invModel.find('**/' + ToontownBattleGlobals.AvPropsNew[track][item]))

                self.invModels.append(itemList)

            invModel.removeNode()
            del invModel

    def unload(self):
        self.ignoreAll()
        base.cr.estateMgr.leaveEstate()
        self.estateOwnerId = None
        self.estateZoneId = None
        if self.place:
            self.place.exit()
            self.place.unload()
            del self.place
        del self.underwaterSound
        del self.swimSound
        del self.submergeSound
        del self.birdSound
        del self.cricketSound
        for node in self.houseNode:
            node.removeNode()

        del self.houseNode
        for model in self.houseModels:
            model.removeNode()

        del self.houseModels
        del self.houseId2house
        if self.sunMoonNode:
            self.sunMoonNode.removeNode()
            del self.sunMoonNode
            self.sunMoonNode = None
        if self.clouds:
            for cloud in self.clouds:
                cloud[0].removeNode()
                del cloud[1]

            del self.clouds
        if self.barrel:
            self.barrel.removeNode()
        SafeZoneLoader.SafeZoneLoader.unload(self)
        return

    def enter(self, requestStatus):
        self.estateOwnerId = requestStatus.get('ownerId', base.localAvatar.doId)
        base.localAvatar.inEstate = 1
        self.loadCloudPlatforms()
        if base.cloudPlatformsEnabled and 0:
            self.setCloudSwitch(1)
        if self.cloudSwitch:
            self.setCloudSwitch(self.cloudSwitch)
        SafeZoneLoader.SafeZoneLoader.enter(self, requestStatus)

    def exit(self):
        self.ignoreAll()
        base.cr.cache.flush()
        base.localAvatar.stopChat()
        base.localAvatar.inEstate = 0
        SafeZoneLoader.SafeZoneLoader.exit(self)

    def createSafeZone(self, dnaFile):
        SafeZoneLoader.SafeZoneLoader.createSafeZone(self, dnaFile)
        self.loadHouses()
        self.loadSunMoon()

    def loadHouses(self):
        for i in range(HouseGlobals.NUM_HOUSE_TYPES):
            self.houseModels[i] = loader.loadModel(HouseGlobals.houseModels[i])

        for i in range(6):
            posHpr = HouseGlobals.houseDrops[i]
            self.houseNode[i] = self.geom.attachNewNode('esHouse_' + str(i))
            self.houseNode[i].setPosHpr(*posHpr)

    def loadSunMoon(self):
        self.sun = loader.loadModel('phase_4/models/props/sun.bam')
        self.moon = loader.loadModel('phase_5.5/models/props/moon.bam')
        self.sunMoonNode = self.geom.attachNewNode('sunMoon')
        self.sunMoonNode.setPosHpr(0, 0, 0, 0, 0, 0)
        if self.sun:
            self.sun.reparentTo(self.sunMoonNode)
            self.sun.setY(270)
            self.sun.setScale(2)
            self.sun.setBillboardPointEye()
        if self.moon:
            self.moon.setP(180)
            self.moon.reparentTo(self.sunMoonNode)
            self.moon.setY(-270)
            self.moon.setScale(15)
            self.moon.setBillboardPointEye()
        self.sunMoonNode.setP(30)

    def enterEstate(self, requestStatus):
        self.notify.debug('enterEstate: requestStatus = %s' % requestStatus)
        ownerId = requestStatus.get('ownerId')
        if ownerId:
            self.estateOwnerId = ownerId
        zoneId = requestStatus['zoneId']
        self.notify.debug('enterEstate, ownerId = %s, zoneId = %s' % (self.estateOwnerId, zoneId))
        self.accept(self.estateDoneEvent, self.handleEstateDone)
        self.place = Estate.Estate(self, self.estateOwnerId, zoneId, self.fsm.getStateNamed('estate'), self.estateDoneEvent)
        base.cr.playGame.setPlace(self.place)
        self.place.load()
        self.place.enter(requestStatus)
        self.estateZoneId = zoneId

    def exitEstate(self):
        self.notify.debug('exitEstate')
        self.ignore(self.estateDoneEvent)
        self.place.exit()
        self.place.unload()
        self.place = None
        base.cr.playGame.setPlace(self.place)
        base.cr.cache.flush()
        return

    def handleEstateDone(self, doneStatus = None):
        if not doneStatus:
            doneStatus = self.place.getDoneStatus()
        how = doneStatus['how']
        shardId = doneStatus['shardId']
        hoodId = doneStatus['hoodId']
        zoneId = doneStatus['zoneId']
        avId = doneStatus.get('avId', -1)
        ownerId = doneStatus.get('ownerId', -1)
        if shardId != None or hoodId != MyEstate:
            self.notify.debug('estate done, and we are backing out to a different hood/shard')
            self.notify.debug('hoodId = %s, avId = %s' % (hoodId, avId))
            self.doneStatus = doneStatus
            messenger.send(self.doneEvent)
            return
        if how in ['tunnelIn',
         'teleportIn',
         'doorIn',
         'elevatorIn']:
            self.notify.debug('staying in estateloader')
            self.fsm.request('quietZone', [doneStatus])
        else:
            self.notify.error('Exited hood with unexpected mode %s' % how)
        return

    def enterHouse(self, requestStatus):
        ownerId = requestStatus.get('ownerId')
        if ownerId:
            self.estateOwnerId = ownerId
        self.acceptOnce(self.houseDoneEvent, self.handleHouseDone)
        self.place = House.House(self, self.estateOwnerId, self.fsm.getStateNamed('house'), self.houseDoneEvent)
        base.cr.playGame.setPlace(self.place)
        self.place.load()
        self.place.enter(requestStatus)

    def exitHouse(self):
        self.ignore(self.houseDoneEvent)
        self.place.exit()
        self.place.unload()
        self.place = None
        base.cr.playGame.setPlace(self.place)
        return

    def handleHouseDone(self, doneStatus = None):
        if not doneStatus:
            doneStatus = self.place.getDoneStatus()
        shardId = doneStatus['shardId']
        hoodId = doneStatus['hoodId']
        if shardId != None or hoodId != MyEstate:
            self.doneStatus = doneStatus
            messenger.send(self.doneEvent)
            return
        how = doneStatus['how']
        if how in ['tunnelIn',
         'teleportIn',
         'doorIn',
         'elevatorIn']:
            self.fsm.request('quietZone', [doneStatus])
        else:
            self.notify.error('Exited hood with unexpected mode %s' % how)
        return

    def handleQuietZoneDone(self):
        status = self.quietZoneStateData.getRequestStatus()
        self.fsm.request(status['where'], [status])

    def atMyEstate(self):
        if self.estateOwnerId != None:
            if self.estateOwnerId == base.localAvatar.getDoId():
                return 1
            else:
                return 0
        else:
            self.notify.warning("We aren't in an estate")
        return

    def setHouse(self, houseId):
        try:
            houseDo = base.cr.doId2do[houseId]
            self.enteredHouse = houseDo.house
        except KeyError:
            self.notify.debug("can't find house: %d" % houseId)

    def startCloudPlatforms(self):
        return
        if len(self.clouds):
            self.cloudTrack = self.__cloudTrack()
            self.cloudTrack.loop()

    def stopCloudPlatforms(self):
        if self.cloudTrack:
            self.cloudTrack.pause()
            del self.cloudTrack
            self.cloudTrack = None
        return

    def __cloudTrack(self):
        track = Parallel()
        for cloud in self.clouds:
            axis = cloud[1]
            pos = cloud[0].getPos(render)
            newPos = pos + axis * 30
            reversePos = pos - axis * 30
            track.append(Sequence(LerpPosInterval(cloud[0], 10, newPos), LerpPosInterval(cloud[0], 20, reversePos), LerpPosInterval(cloud[0], 10, pos)))

        return track

    def debugGeom(self, decomposed):
        print 'numPrimitives = %d' % decomposed.getNumPrimitives()
        for primIndex in range(decomposed.getNumPrimitives()):
            prim = decomposed.getPrimitive(primIndex)
            print 'prim = %s' % prim
            print 'isIndexed = %d' % prim.isIndexed()
            print 'prim.getNumPrimitives = %d' % prim.getNumPrimitives()
            for basicPrim in range(prim.getNumPrimitives()):
                print '%d start=%d' % (basicPrim, prim.getPrimitiveStart(basicPrim))
                print '%d end=%d' % (basicPrim, prim.getPrimitiveEnd(basicPrim))

    def loadOnePlatform(self, version, radius, zOffset, score, multiplier):
        self.notify.debug('loadOnePlatform version=%d' % version)
        cloud = NodePath('cloud-%d-%d' % (score, multiplier))
        cloudModel = loader.loadModel('phase_5.5/models/estate/bumper_cloud')
        cc = cloudModel.copyTo(cloud)
        colCube = cc.find('**/collision')
        colCube.setName('cloudSphere-0')
        dTheta = 2.0 * math.pi / self.numClouds
        cloud.reparentTo(self.cloudOrigin)
        axes = [Vec3(1, 0, 0), Vec3(0, 1, 0), Vec3(0, 0, 1)]
        cloud.setPos(radius * math.cos(version * dTheta), radius * math.sin(version * dTheta), 4 * random.random() + zOffset)
        cloud.setScale(4.0)
        self.clouds.append([cloud, random.choice(axes)])

    def loadSkyCollision(self):
        plane = CollisionPlane(Plane(Vec3(0, 0, -1), Point3(0, 0, 300)))
        plane.setTangible(0)
        planeNode = CollisionNode('cloudSphere-0')
        planeNode.addSolid(plane)
        self.cloudOrigin.attachNewNode(planeNode)

    def loadCloudPlatforms(self):
        self.cloudOrigin = self.geom.attachNewNode('cloudOrigin')
        self.cloudOrigin.setZ(30)
        self.loadSkyCollision()
        self.numClouds = 12
        pinballScore = PinballScoring[PinballCloudBumperLow]
        for i in range(12):
            self.loadOnePlatform(i, 40, 0, pinballScore[0], pinballScore[1])

        pinballScore = PinballScoring[PinballCloudBumperMed]
        for i in range(12):
            self.loadOnePlatform(i, 60, 40, pinballScore[0], pinballScore[1])

        pinballScore = PinballScoring[PinballCloudBumperHigh]
        for i in range(12):
            self.loadOnePlatform(i, 20, 80, pinballScore[0], pinballScore[1])

        self.cloudOrigin.stash()

    def setCloudSwitch(self, on):
        self.cloudSwitch = on
        if hasattr(self, 'cloudOrigin'):
            if on:
                self.cloudOrigin.unstash()
            else:
                self.cloudOrigin.stash()
