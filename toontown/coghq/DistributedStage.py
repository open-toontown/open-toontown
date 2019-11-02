from pandac.PandaModules import *
from direct.distributed.ClockDelta import *
from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from direct.showbase import BulletinBoardWatcher
from otp.otpbase import OTPGlobals
from toontown.toonbase.ToontownGlobals import *
from toontown.toonbase import TTLocalizer
from direct.gui import OnscreenText
from toontown.toonbase import ToontownGlobals
from toontown.coghq import DistributedStageRoom, StageLayout, StageRoom
import random
from direct.task.Task import Task
from direct.interval.IntervalGlobal import *

class DistributedStage(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedStage')
    ReadyPost = 'StageReady'
    WinEvent = 'StageWinEvent'
    FloorNum = 'StageFloorNum'

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        self.titleColor = (1, 1, 1, 1)
        self.titleText = OnscreenText.OnscreenText('', fg=self.titleColor, shadow=(0, 0, 0, 1), font=ToontownGlobals.getSuitFont(), pos=(0, -0.5), scale=0.1, drawOrder=0, mayChange=1)
        self.titleSequence = None
        self.pendingZoneChange = 0
        return

    def generate(self):
        self.notify.debug('generate: %s' % self.doId)
        DistributedObject.DistributedObject.generate(self)
        bboard.post('stage', self)
        self.roomWatcher = None
        self.geom = None
        self.rooms = []
        self.hallways = []
        self.allRooms = []
        self.curToonRoomNum = None
        base.localAvatar.setCameraCollisionsCanMove(1)
        self.accept('SOSPanelEnter', self.handleSOSPanel)
        return

    def announceGenerate(self):
        DistributedObject.DistributedObject.announceGenerate(self)

    def placeToon(self):
        pX = random.randint(-2, 2)
        pY = random.randint(-2, 2)
        base.localAvatar.reparentTo(render)
        base.localAvatar.setPosHpr(pX, pY, 0, 0, 0, 0)
        self.camEnterRoom(0)

    def setLayoutIndex(self, layoutIndex):
        self.layoutIndex = layoutIndex

    def getLayoutIndex(self):
        return self.layoutIndex

    def setZoneId(self, zoneId):
        self.zoneId = zoneId

    def setStageId(self, id):
        DistributedStage.notify.debug('setStageId: %s' % id)
        self.stageId = id

    def setFloorNum(self, num):
        DistributedStage.notify.debug('floorNum: %s' % num)
        self.floorNum = num
        bboard.post(DistributedStage.FloorNum, num)
        self.layout = StageLayout.StageLayout(self.stageId, self.floorNum, self.layoutIndex)

    def setRoomDoIds(self, roomDoIds):
        self.roomDoIds = roomDoIds
        self.roomWatcher = BulletinBoardWatcher.BulletinBoardWatcher('roomWatcher-%s' % self.doId, [ DistributedStageRoom.getStageRoomReadyPostName(doId) for doId in self.roomDoIds ], self.gotAllRooms)

    def gotAllRooms(self):
        self.notify.debug('stage %s: got all rooms' % self.doId)
        self.roomWatcher.destroy()
        self.roomWatcher = None
        self.geom = render.attachNewNode('stage%s' % self.doId)
        for doId in self.roomDoIds:
            self.rooms.append(base.cr.doId2do[doId])
            self.rooms[-1].setStage(self)

        self.notify.info('stageId %s, floor %s, %s' % (self.stageId, self.floorNum, self.rooms[0].avIdList))
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
                hallway = StageRoom.StageRoom(self.layout.getHallwayModel(i))
                hallway.attachTo(room, rng)
                hallway.setRoomNum(i * 2 + 1)
                hallway.initFloorCollisions()
                hallway.enter()
                self.hallways.append(hallway)
                self.allRooms.append(hallway)
                self.listenForFloorEvents(hallway)

        self.placeToon()

        def handleCameraRayFloorCollision(collEntry, self = self):
            name = collEntry.getIntoNode().getName()
            self.notify.debug('camera floor ray collided with: %s' % name)
            prefix = StageRoom.StageRoom.FloorCollPrefix
            prefixLen = len(prefix)
            if name[:prefixLen] == prefix:
                try:
                    roomNum = int(name[prefixLen:])
                except:
                    DistributedLevel.notify.warning('Invalid zone floor collision node: %s' % name)
                else:
                    self.camEnterRoom(roomNum)
                    print collEntry
                    print

        self.accept('on-floor', handleCameraRayFloorCollision)
        if bboard.has('stageRoom'):
            self.warpToRoom(bboard.get('stageRoom'))
        firstSetZoneDoneEvent = self.cr.getNextSetZoneDoneEvent()

        def handleFirstSetZoneDone():
            self.notify.debug('stageHandleFirstSetZoneDone')
            bboard.post(DistributedStage.ReadyPost, self)

        self.acceptOnce(firstSetZoneDoneEvent, handleFirstSetZoneDone)
        zoneList = [OTPGlobals.UberZone, self.zoneId]
        for room in self.rooms:
            zoneList.extend(room.zoneIds)

        base.cr.sendSetZoneMsg(self.zoneId, zoneList)
        self.accept('takingScreenshot', self.handleScreenshot)
        base.transitions.irisIn()
        taskMgr.doMethodLater(0.25, self._delayedInit, 'delayedInit')
        return

    def _delayedInit(self, taskFooler = 0):
        self.camEnterRoom(0)
        base.localAvatar.unpauseGlitchKiller()
        try:
            fsm = base.cr.playGame.getPlace().fsm
            fsm.forceTransition('walk')
        except:
            pass

        return Task.done

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
        self.notify.warning('stage %s: timed out waiting for room objs' % self.doId)

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
        self.notify.info('CAMENTERROOM doID%s num%s' % (self.doId, roomNum))
        self.notify.info('av: %s, cam: %s' % (localAvatar.getPos(), camera.getPos()))
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
        base.localAvatar.setSystemMessage(avId, TTLocalizer.StageBossConfrontedMsg % av.getName())
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
        if self.titleSequence:
            self.titleSequence.finish()
        self.titleSequence = None
        self.ignoreAll()
        if self.titleText:
            self.titleText.cleanup()
            self.titleText = None
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
        bboard.remove('stage')

    def handleSOSPanel(self, panel):
        avIds = []
        for avId in self.rooms[0].avIdList:
            if base.cr.doId2do.get(avId):
                avIds.append(avId)

        panel.setFactoryToonIdList(avIds)

    def handleScreenshot(self):
        base.addScreenshotString('stageId: %s, floor (from 1): %s' % (self.stageId, self.floorNum + 1))
        if hasattr(self, 'currentRoomName'):
            base.addScreenshotString('%s' % self.currentRoomName)

    def setStageZone(self, zoneId):
        base.cr.sendSetZoneMsg(zoneId)
        base.cr.playGame.getPlace().fsm.request('walk')
        scale = base.localAvatar.getScale()
        base.camera.setScale(scale)

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
            self.titleText.setText('')

    def elevatorAlert(self, avId):
        if base.localAvatar.doId != avId:
            name = base.cr.doId2do[avId].getName()
            self.showInfoText(TTLocalizer.stageToonEnterElevator % name)
