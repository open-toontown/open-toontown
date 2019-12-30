from pandac.PandaModules import *
from direct.distributed.ClockDelta import *
from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from direct.showbase import BulletinBoardWatcher
from otp.otpbase import OTPGlobals
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.coghq import CountryClubLayout
from toontown.coghq import DistributedCountryClubRoom
from toontown.coghq import CountryClubRoom
from toontown.coghq import FactoryCameraViews
from direct.gui import OnscreenText
from direct.task.Task import Task
from direct.interval.IntervalGlobal import *

class DistributedCountryClub(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedCountryClub')
    ReadyPost = 'CountryClubReady'
    WinEvent = 'CountryClubWinEvent'
    doBlockRooms = base.config.GetBool('block-country-club-rooms', 1)

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        self.lastCamEnterRoom = 0
        self.titleColor = (1, 1, 1, 1)
        self.titleText = OnscreenText.OnscreenText('', fg=self.titleColor, shadow=(0, 0, 0, 1), font=ToontownGlobals.getSignFont(), pos=(0, -0.5), scale=0.1, drawOrder=0, mayChange=1)
        self.titleSequence = None
        return

    def generate(self):
        self.notify.debug('generate: %s' % self.doId)
        DistributedObject.DistributedObject.generate(self)
        bboard.post('countryClub', self)
        self.roomWatcher = None
        self.geom = None
        self.rooms = []
        self.hallways = []
        self.allRooms = []
        self.curToonRoomNum = None
        self.allBlockedRooms = []
        base.localAvatar.setCameraCollisionsCanMove(1)
        base.localAvatar.reparentTo(render)
        base.localAvatar.setPosHpr(0, 0, 0, 0, 0, 0)
        self.accept('SOSPanelEnter', self.handleSOSPanel)
        self.factoryViews = FactoryCameraViews.FactoryCameraViews(self)
        base.localAvatar.chatMgr.chatInputSpeedChat.addFactoryMenu()
        self.__setupHighSky()
        return

    def startSky(self):
        self.sky = loader.loadModel('phase_12/models/bossbotHQ/BossTestSkyBox')
        self.sky.reparentTo(camera)
        self.sky.setZ(0.0)
        self.sky.setHpr(0.0, 0.0, 0.0)
        ce = CompassEffect.make(NodePath(), CompassEffect.PRot | CompassEffect.PZ)
        self.sky.node().setEffect(ce)
        self.sky.setBin('background', 0)

    def stopSky(self):
        taskMgr.remove('skyTrack')
        self.sky.removeNode()

    def __setupHighSky(self):
        self.startSky()
        sky = self.sky
        sky.setH(150)
        sky.setZ(-100)

    def __cleanupHighSky(self):
        sky = self.sky
        sky.setH(0)
        sky.setZ(0)
        self.stopSky()

    def setZoneId(self, zoneId):
        self.zoneId = zoneId

    def setCountryClubId(self, id):
        DistributedCountryClub.notify.debug('setCountryClubId: %s' % id)
        self.countryClubId = id

    def setFloorNum(self, num):
        DistributedCountryClub.notify.debug('floorNum: %s' % num)
        self.floorNum = num
        self.layout = CountryClubLayout.CountryClubLayout(self.countryClubId, self.floorNum, self.layoutIndex)

    def setLayoutIndex(self, layoutIndex):
        self.layoutIndex = layoutIndex

    def getLayoutIndex(self):
        return self.layoutIndex

    def setRoomDoIds(self, roomDoIds):
        self.roomDoIds = roomDoIds
        self.roomWatcher = BulletinBoardWatcher.BulletinBoardWatcher('roomWatcher-%s' % self.doId, [ DistributedCountryClubRoom.getCountryClubRoomReadyPostName(doId) for doId in self.roomDoIds ], self.gotAllRooms)

    def gotAllRooms(self):
        self.notify.debug('countryClub %s: got all rooms' % self.doId)
        self.roomWatcher.destroy()
        self.roomWatcher = None
        self.geom = render.attachNewNode('countryClub%s' % self.doId)
        for doId in self.roomDoIds:
            self.rooms.append(base.cr.doId2do[doId])
            self.rooms[-1].setCountryClub(self)

        self.notify.info('countryClubId %s, floor %s, %s' % (self.countryClubId, self.floorNum, self.rooms[0].avIdList))
        rng = self.layout.getRng()
        numRooms = self.layout.getNumRooms()
        for i, room in enumerate(self.rooms):
            if i == 0:
                room.getGeom().reparentTo(self.geom)
            else:
                room.attachTo(self.hallways[i - 1], rng)
            self.allRooms.append(room)
            self.listenForFloorEvents(room)
            if i < numRooms - 1:
                hallway = CountryClubRoom.CountryClubRoom(self.layout.getHallwayModel(i))
                hallway.attachTo(room, rng)
                hallway.setRoomNum(i * 2 + 1)
                hallway.initFloorCollisions()
                hallway.enter()
                self.hallways.append(hallway)
                self.allRooms.append(hallway)
                self.listenForFloorEvents(hallway)

        def handleCameraRayFloorCollision(collEntry, self = self):
            name = collEntry.getIntoNode().getName()
            self.notify.debug('camera floor ray collided with: %s' % name)
            prefix = CountryClubRoom.CountryClubRoom.FloorCollPrefix
            prefixLen = len(prefix)
            if name[:prefixLen] == prefix:
                try:
                    roomNum = int(name[prefixLen:])
                except:
                    DistributedLevel.notify.warning('Invalid zone floor collision node: %s' % name)
                else:
                    self.camEnterRoom(roomNum)

        self.accept('on-floor', handleCameraRayFloorCollision)
        if bboard.has('countryClubRoom'):
            self.warpToRoom(bboard.get('countryClubRoom'))
        firstSetZoneDoneEvent = self.cr.getNextSetZoneDoneEvent()

        def handleFirstSetZoneDone():
            self.notify.debug('countryClubHandleFirstSetZoneDone')
            self.accept('takingScreenshot', self.handleScreenshot)
            base.transitions.irisIn()
            bboard.post(DistributedCountryClub.ReadyPost, self)

        self.acceptOnce(firstSetZoneDoneEvent, handleFirstSetZoneDone)
        zoneList = [OTPGlobals.UberZone, self.zoneId]
        for room in self.rooms:
            zoneList.extend(room.zoneIds)

        base.cr.sendSetZoneMsg(self.zoneId, zoneList)
        return

    def listenForFloorEvents(self, room):
        roomNum = room.getRoomNum()
        floorCollName = room.getFloorCollName()

        def handleZoneEnter(collisionEntry, self = self, roomNum = roomNum):
            self.toonEnterRoom(roomNum)
            floorNode = collisionEntry.getIntoNode()
            if floorNode.hasTag('ouch'):
                room = self.allRooms[roomNum]
                ouchLevel = room.getFloorOuchLevel()
                room.startOuch(ouchLevel)

        self.accept('enter%s' % floorCollName, handleZoneEnter)

        def handleZoneExit(collisionEntry, self = self, roomNum = roomNum):
            floorNode = collisionEntry.getIntoNode()
            if floorNode.hasTag('ouch'):
                self.allRooms[roomNum].stopOuch()

        self.accept('exit%s' % floorCollName, handleZoneExit)

    def getAllRoomsTimeout(self):
        self.notify.warning('countryClub %s: timed out waiting for room objs' % self.doId)

    def toonEnterRoom(self, roomNum):
        self.notify.debug('toonEnterRoom: %s' % roomNum)
        if roomNum != self.curToonRoomNum:
            if self.curToonRoomNum is not None:
                self.allRooms[self.curToonRoomNum].localToonFSM.request('notPresent')
            self.allRooms[roomNum].localToonFSM.request('present')
            self.curToonRoomNum = roomNum
        return

    def camEnterRoom(self, roomNum):
        self.notify.debug('camEnterRoom: %s' % roomNum)
        blockRoomsAboveThisNumber = len(self.allRooms)
        if self.allBlockedRooms and self.doBlockRooms:
            blockRoomsAboveThisNumber = self.allBlockedRooms[0]
        if roomNum % 2 == 1:
            minVis = roomNum - 2
            maxVis = roomNum + 2
        else:
            minVis = roomNum - 1
            maxVis = roomNum + 1
        for i, room in enumerate(self.allRooms):
            if i < minVis or i > maxVis:
                if not room.getGeom().isEmpty():
                    room.getGeom().stash()
            elif i <= blockRoomsAboveThisNumber:
                if not room.getGeom().isEmpty():
                    room.getGeom().unstash()
            elif not room.getGeom().isEmpty():
                room.getGeom().stash()

        self.lastCamEnterRoom = roomNum

    def setBossConfronted(self, avId):
        if avId == base.localAvatar.doId:
            return
        av = base.cr.identifyFriend(avId)
        if av is None:
            return
        base.localAvatar.setSystemMessage(avId, TTLocalizer.CountryClubBossConfrontedMsg % av.getName())
        return

    def warpToRoom(self, roomId):
        for i in range(len(self.rooms)):
            room = self.rooms[i]
            if room.roomId == roomId:
                break
        else:
            return False

        base.localAvatar.setPosHpr(room.getGeom(), 0, 0, 0, 0, 0, 0)
        self.camEnterRoom(i * 2)
        return True

    def disable(self):
        self.notify.debug('disable')
        if self.titleSequence:
            self.titleSequence.finish()
        self.titleSequence = None
        self.__cleanupHighSky()
        self.ignoreAll()
        for hallway in self.hallways:
            hallway.exit()

        self.rooms = []
        for hallway in self.hallways:
            hallway.delete()

        self.hallways = []
        self.allRooms = []
        if self.roomWatcher:
            self.roomWatcher.destroy()
            self.roomWatcher = None
        if self.geom is not None:
            self.geom.removeNode()
            self.geom = None
        base.localAvatar.setCameraCollisionsCanMove(0)
        if hasattr(self, 'relatedObjectMgrRequest') and self.relatedObjectMgrRequest:
            self.cr.relatedObjectMgr.abortRequest(self.relatedObjectMgrRequest)
            del self.relatedObjectMgrRequest
        DistributedObject.DistributedObject.disable(self)
        return

    def delete(self):
        DistributedObject.DistributedObject.delete(self)
        self.ignore('SOSPanelEnter')
        bboard.remove('countryClub')
        base.localAvatar.chatMgr.chatInputSpeedChat.removeFactoryMenu()
        self.factoryViews.delete()
        del self.factoryViews

    def handleSOSPanel(self, panel):
        avIds = []
        for avId in self.rooms[0].avIdList:
            if base.cr.doId2do.get(avId):
                avIds.append(avId)

        panel.setFactoryToonIdList(avIds)

    def handleScreenshot(self):
        base.addScreenshotString('countryClubId: %s, floor (from 1): %s' % (self.countryClubId, self.floorNum + 1))
        if hasattr(self, 'currentRoomName'):
            base.addScreenshotString('%s' % self.currentRoomName)

    def setBlockedRooms(self, blockedRooms):
        self.blockedRooms = blockedRooms
        self.computeBlockedRoomsAndHallways()
        self.camEnterRoom(self.lastCamEnterRoom)

    def computeBlockedRoomsAndHallways(self):
        self.allBlockedRooms = []
        for roomIndex in self.blockedRooms:
            self.allBlockedRooms.append(roomIndex * 2)

        self.allBlockedRooms.sort()
        self.notify.debug('self.allBlockedRooms =%s' % self.allBlockedRooms)

    def setCountryClubZone(self, zoneId):
        base.cr.sendSetZoneMsg(zoneId)
        base.cr.playGame.getPlace().fsm.request('walk')
        scale = base.localAvatar.getScale()
        base.camera.setScale(scale)

    def elevatorAlert(self, avId):
        if base.localAvatar.doId != avId:
            name = base.cr.doId2do[avId].getName()
            self.showInfoText(TTLocalizer.CountryClubToonEnterElevator % name)

    def showInfoText(self, text = 'hello world'):
        description = text
        if description and description != '':
            self.titleText.setText(description)
            self.titleText.setColor(Vec4(*self.titleColor))
            self.titleText.setColorScale(1, 1, 1, 1)
            self.titleText.setFg(self.titleColor)
            if self.titleSequence:
                self.titleSequence.finish()
            self.titleSequence = None
            self.titleSequence = Sequence(Func(self.showTitleText), Wait(3.1), LerpColorScaleInterval(self.titleText, duration=0.5, colorScale=Vec4(1, 1, 1, 0.0)), Func(self.hideTitleText))
            self.titleSequence.start()
        return

    def showTitleText(self):
        if self.titleText:
            self.titleText.show()

    def hideTitleText(self):
        if self.titleText or 1:
            self.titleText.hide()
