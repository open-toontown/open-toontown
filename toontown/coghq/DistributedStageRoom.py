from pandac.PandaModules import *
from toontown.toonbase.ToontownGlobals import *
from direct.distributed.ClockDelta import *
from direct.interval.IntervalGlobal import *
import random
from otp.level import DistributedLevel
from direct.directnotify import DirectNotifyGlobal
from . import StageRoomBase, StageRoom
from . import FactoryEntityCreator
from . import StageRoomSpecs
from otp.level import LevelSpec, LevelConstants
from toontown.toonbase import TTLocalizer
if __dev__:
    from otp.level import EditorGlobals

def getStageRoomReadyPostName(doId):
    return 'stageRoomReady-%s' % doId


class DistributedStageRoom(DistributedLevel.DistributedLevel, StageRoomBase.StageRoomBase, StageRoom.StageRoom):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedStageRoom')
    EmulateEntrancePoint = False

    def __init__(self, cr):
        DistributedLevel.DistributedLevel.__init__(self, cr)
        StageRoomBase.StageRoomBase.__init__(self)
        StageRoom.StageRoom.__init__(self)
        self.suitIds = []
        self.suits = []
        self.reserveSuits = []
        self.joiningReserves = []
        self.suitsInitialized = 0
        self.goonClipPlanes = {}
        self.stage = None
        return

    def createEntityCreator(self):
        return FactoryEntityCreator.FactoryEntityCreator(level=self)

    def generate(self):
        self.notify.debug('generate')
        DistributedLevel.DistributedLevel.generate(self)

    def delete(self):
        del self.stage
        DistributedLevel.DistributedLevel.delete(self)
        StageRoom.StageRoom.delete(self)
        self.ignoreAll()

    def setStageId(self, stageId):
        self.notify.debug('stageId: %s' % stageId)
        StageRoomBase.StageRoomBase.setStageId(self, stageId)

    def setRoomId(self, roomId):
        self.notify.debug('roomId: %s' % roomId)
        StageRoomBase.StageRoomBase.setRoomId(self, roomId)

    def setRoomNum(self, num):
        self.notify.debug('roomNum: %s' % num)
        StageRoom.StageRoom.setRoomNum(self, num)

    def levelAnnounceGenerate(self):
        self.notify.debug('levelAnnounceGenerate')
        DistributedLevel.DistributedLevel.levelAnnounceGenerate(self)
        specModule = StageRoomSpecs.getStageRoomSpecModule(self.roomId)
        roomSpec = LevelSpec.LevelSpec(specModule)
        if __dev__:
            typeReg = self.getEntityTypeReg()
            roomSpec.setEntityTypeReg(typeReg)
        DistributedLevel.DistributedLevel.initializeLevel(self, roomSpec)

    def getReadyPostName(self):
        return getStageRoomReadyPostName(self.doId)

    def privGotSpec(self, levelSpec):
        if __dev__:
            if not levelSpec.hasEntityTypeReg():
                typeReg = self.getEntityTypeReg()
                levelSpec.setEntityTypeReg(typeReg)
        DistributedLevel.DistributedLevel.privGotSpec(self, levelSpec)
        StageRoom.StageRoom.enter(self)
        self.acceptOnce('leavingStage', self.announceLeaving)
        bboard.post(self.getReadyPostName())

    def fixupLevelModel(self):
        StageRoom.StageRoom.setGeom(self, self.geom)
        StageRoom.StageRoom.initFloorCollisions(self)

    def setStage(self, stage):
        self.stage = stage

    def setBossConfronted(self, avId):
        self.stage.setBossConfronted(avId)

    def setDefeated(self):
        self.notify.info('setDefeated')
        from toontown.coghq import DistributedStage
        messenger.send(DistributedStage.DistributedStage.WinEvent)

    def initVisibility(self, *args, **kw):
        pass

    def shutdownVisibility(self, *args, **kw):
        pass

    def lockVisibility(self, *args, **kw):
        pass

    def unlockVisibility(self, *args, **kw):
        pass

    def enterZone(self, *args, **kw):
        pass

    def updateVisibility(self, *args, **kw):
        pass

    def setVisibility(self, *args, **kw):
        pass

    def resetVisibility(self, *args, **kw):
        pass

    def handleVisChange(self, *args, **kw):
        pass

    def forceSetZoneThisFrame(self, *args, **kw):
        pass

    def getParentTokenForEntity(self, entId):
        if __dev__:
            pass
        return 1000000 * self.roomNum + entId

    def enterLtNotPresent(self):
        StageRoom.StageRoom.enterLtNotPresent(self)
        if __dev__:
            bboard.removeIfEqual(EditorGlobals.EditTargetPostName, self)
        self.ignore('f2')

    def enterLtPresent(self):
        StageRoom.StageRoom.enterLtPresent(self)
        if __dev__:
            bboard.post(EditorGlobals.EditTargetPostName, self)
        if self.stage is not None:
            self.stage.currentRoomName = StageRoomSpecs.CashbotStageRoomId2RoomName[self.roomId]

        def printPos(self = self):
            thisZone = self.getZoneNode(LevelConstants.UberZoneEntId)
            pos = base.localAvatar.getPos(thisZone)
            h = base.localAvatar.getH(thisZone)
            roomName = StageRoomSpecs.CashbotStageRoomId2RoomName[self.roomId]
            print('stage pos: %s, h: %s, room: %s' % (repr(pos), h, roomName))
            if self.stage is not None:
                floorNum = self.stage.floorNum
            else:
                floorNum = '???'
            posStr = 'X: %.3f' % pos[0] + '\nY: %.3f' % pos[1] + '\nZ: %.3f' % pos[2] + '\nH: %.3f' % h + '\nstageId: %s' % self.stageId + '\nfloor: %s' % floorNum + '\nroomId: %s' % self.roomId + '\nroomName: %s' % roomName
            base.localAvatar.setChatAbsolute(posStr, CFThought | CFTimeout)
            return

        self.accept('f2', printPos)
        return

    def handleSOSPanel(self, panel):
        avIds = []
        for avId in self.avIdList:
            if base.cr.doId2do.get(avId):
                avIds.append(avId)

        panel.setFactoryToonIdList(avIds)

    def disable(self):
        self.notify.debug('disable')
        StageRoom.StageRoom.exit(self)
        if hasattr(self, 'suits'):
            del self.suits
        if hasattr(self, 'relatedObjectMgrRequest') and self.relatedObjectMgrRequest:
            self.cr.relatedObjectMgr.abortRequest(self.relatedObjectMgrRequest)
            del self.relatedObjectMgrRequest
        bboard.remove(self.getReadyPostName())
        DistributedLevel.DistributedLevel.disable(self)

    def setSuits(self, suitIds, reserveSuitIds):
        oldSuitIds = list(self.suitIds)
        self.suitIds = suitIds
        self.reserveSuitIds = reserveSuitIds
        newSuitIds = []
        for suitId in self.suitIds:
            if suitId not in oldSuitIds:
                newSuitIds.append(suitId)

        if len(newSuitIds):

            def bringOutOfReserve(suits):
                for suit in suits:
                    suit.comeOutOfReserve()

            self.relatedObjectMgrRequest = self.cr.relatedObjectMgr.requestObjects(newSuitIds, bringOutOfReserve)

    def reservesJoining(self):
        pass

    def getCogSpec(self, cogId):
        cogSpecModule = StageRoomSpecs.getCogSpecModule(self.roomId)
        return cogSpecModule.CogData[cogId]

    def getReserveCogSpec(self, cogId):
        cogSpecModule = StageRoomSpecs.getCogSpecModule(self.roomId)
        return cogSpecModule.ReserveCogData[cogId]

    def getBattleCellSpec(self, battleCellId):
        cogSpecModule = StageRoomSpecs.getCogSpecModule(self.roomId)
        return cogSpecModule.BattleCells[battleCellId]

    def getFloorOuchLevel(self):
        return 8

    def getTaskZoneId(self):
        return self.stageId

    def getBossTaunt(self):
        return TTLocalizer.StageBossTaunt

    def getBossBattleTaunt(self):
        return TTLocalizer.StageBossBattleTaunt

    def __str__(self):
        if hasattr(self, 'roomId'):
            return '%s %s: %s' % (self.__class__.__name__, self.roomId, StageRoomSpecs.CashbotStageRoomId2RoomName[self.roomId])
        else:
            return 'DistributedStageRoom'

    def __repr__(self):
        return str(self)

    def complexVis(self):
        return 0
