from pandac.PandaModules import *
from direct.distributed.ClockDelta import *
from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from direct.showbase import BulletinBoardWatcher
from otp.otpbase import OTPGlobals
from toontown.toonbase.ToontownGlobals import *
from toontown.toonbase import TTLocalizer
from toontown.coghq import DistributedMintRoom, MintLayout, MintRoom

class DistributedMint(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedMint')
    ReadyPost = 'MintReady'
    WinEvent = 'MintWinEvent'

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)

    def generate(self):
        self.notify.debug('generate: %s' % self.doId)
        DistributedObject.DistributedObject.generate(self)
        bboard.post('mint', self)
        self.roomWatcher = None
        self.geom = None
        self.rooms = []
        self.hallways = []
        self.allRooms = []
        self.curToonRoomNum = None
        base.localAvatar.setCameraCollisionsCanMove(1)
        base.localAvatar.reparentTo(render)
        base.localAvatar.setPosHpr(0, 0, 0, 0, 0, 0)
        self.accept('SOSPanelEnter', self.handleSOSPanel)
        return

    def setZoneId(self, zoneId):
        self.zoneId = zoneId

    def setMintId(self, id):
        DistributedMint.notify.debug('setMintId: %s' % id)
        self.mintId = id

    def setFloorNum(self, num):
        DistributedMint.notify.debug('floorNum: %s' % num)
        self.floorNum = num
        self.layout = MintLayout.MintLayout(self.mintId, self.floorNum)

    def setRoomDoIds(self, roomDoIds):
        self.roomDoIds = roomDoIds
        self.roomWatcher = BulletinBoardWatcher.BulletinBoardWatcher('roomWatcher-%s' % self.doId, [ DistributedMintRoom.getMintRoomReadyPostName(doId) for doId in self.roomDoIds ], self.gotAllRooms)

    def gotAllRooms(self):
        self.notify.debug('mint %s: got all rooms' % self.doId)
        self.roomWatcher.destroy()
        self.roomWatcher = None
        self.geom = render.attachNewNode('mint%s' % self.doId)
        for doId in self.roomDoIds:
            self.rooms.append(base.cr.doId2do[doId])
            self.rooms[-1].setMint(self)

        self.notify.info('mintId %s, floor %s, %s' % (self.mintId, self.floorNum, self.rooms[0].avIdList))
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
                hallway = MintRoom.MintRoom(self.layout.getHallwayModel(i))
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
            prefix = MintRoom.MintRoom.FloorCollPrefix
            prefixLen = len(prefix)
            if name[:prefixLen] == prefix:
                try:
                    roomNum = int(name[prefixLen:])
                except:
                    DistributedLevel.notify.warning('Invalid zone floor collision node: %s' % name)
                else:
                    self.camEnterRoom(roomNum)

        self.accept('on-floor', handleCameraRayFloorCollision)
        if bboard.has('mintRoom'):
            self.warpToRoom(bboard.get('mintRoom'))
        firstSetZoneDoneEvent = self.cr.getNextSetZoneDoneEvent()

        def handleFirstSetZoneDone():
            self.notify.debug('mintHandleFirstSetZoneDone')
            bboard.post(DistributedMint.ReadyPost, self)

        self.acceptOnce(firstSetZoneDoneEvent, handleFirstSetZoneDone)
        zoneList = [OTPGlobals.UberZone, self.zoneId]
        for room in self.rooms:
            zoneList.extend(room.zoneIds)

        base.cr.sendSetZoneMsg(self.zoneId, zoneList)
        self.accept('takingScreenshot', self.handleScreenshot)
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
        self.notify.warning('mint %s: timed out waiting for room objs' % self.doId)

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
        if roomNum % 2 == 1:
            minVis = roomNum - 2
            maxVis = roomNum + 2
        else:
            minVis = roomNum - 1
            maxVis = roomNum + 1
        for i, room in enumerate(self.allRooms):
            if i < minVis or i > maxVis:
                room.getGeom().stash()
            else:
                room.getGeom().unstash()

    def setBossConfronted(self, avId):
        if avId == base.localAvatar.doId:
            return
        av = base.cr.identifyFriend(avId)
        if av is None:
            return
        base.localAvatar.setSystemMessage(avId, TTLocalizer.MintBossConfrontedMsg % av.getName())
        return

    def warpToRoom(self, roomId):
        for i in xrange(len(self.rooms)):
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
        bboard.remove('mint')

    def handleSOSPanel(self, panel):
        avIds = []
        for avId in self.rooms[0].avIdList:
            if base.cr.doId2do.get(avId):
                avIds.append(avId)

        panel.setFactoryToonIdList(avIds)

    def handleScreenshot(self):
        base.addScreenshotString('mintId: %s, floor (from 1): %s' % (self.mintId, self.floorNum + 1))
        if hasattr(self, 'currentRoomName'):
            base.addScreenshotString('%s' % self.currentRoomName)
