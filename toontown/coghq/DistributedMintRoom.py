from pandac.PandaModules import *
from toontown.toonbase.ToontownGlobals import *
from direct.distributed.ClockDelta import *
from direct.interval.IntervalGlobal import *
import random
from otp.level import DistributedLevel
from direct.directnotify import DirectNotifyGlobal
import MintRoomBase, MintRoom
import FactoryEntityCreator
import MintRoomSpecs
from otp.level import LevelSpec, LevelConstants
from toontown.toonbase import TTLocalizer
if __dev__:
    from otp.level import EditorGlobals

def getMintRoomReadyPostName(doId):
    return 'mintRoomReady-%s' % doId


class DistributedMintRoom(DistributedLevel.DistributedLevel, MintRoomBase.MintRoomBase, MintRoom.MintRoom):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedMintRoom')
    EmulateEntrancePoint = False

    def __init__(self, cr):
        DistributedLevel.DistributedLevel.__init__(self, cr)
        MintRoomBase.MintRoomBase.__init__(self)
        MintRoom.MintRoom.__init__(self)
        self.suitIds = []
        self.suits = []
        self.reserveSuits = []
        self.joiningReserves = []
        self.suitsInitialized = 0
        self.goonClipPlanes = {}
        self.mint = None
        return

    def createEntityCreator(self):
        return FactoryEntityCreator.FactoryEntityCreator(level=self)

    def generate(self):
        self.notify.debug('generate')
        DistributedLevel.DistributedLevel.generate(self)

    def delete(self):
        del self.mint
        DistributedLevel.DistributedLevel.delete(self)
        MintRoom.MintRoom.delete(self)
        self.ignoreAll()

    def setMintId(self, mintId):
        self.notify.debug('mintId: %s' % mintId)
        MintRoomBase.MintRoomBase.setMintId(self, mintId)

    def setRoomId(self, roomId):
        self.notify.debug('roomId: %s' % roomId)
        MintRoomBase.MintRoomBase.setRoomId(self, roomId)

    def setRoomNum(self, num):
        self.notify.debug('roomNum: %s' % num)
        MintRoom.MintRoom.setRoomNum(self, num)

    def levelAnnounceGenerate(self):
        self.notify.debug('levelAnnounceGenerate')
        DistributedLevel.DistributedLevel.levelAnnounceGenerate(self)
        specModule = MintRoomSpecs.getMintRoomSpecModule(self.roomId)
        roomSpec = LevelSpec.LevelSpec(specModule)
        if __dev__:
            typeReg = self.getEntityTypeReg()
            roomSpec.setEntityTypeReg(typeReg)
        DistributedLevel.DistributedLevel.initializeLevel(self, roomSpec)

    def getReadyPostName(self):
        return getMintRoomReadyPostName(self.doId)

    def privGotSpec(self, levelSpec):
        if __dev__:
            if not levelSpec.hasEntityTypeReg():
                typeReg = self.getEntityTypeReg()
                levelSpec.setEntityTypeReg(typeReg)
        DistributedLevel.DistributedLevel.privGotSpec(self, levelSpec)
        MintRoom.MintRoom.enter(self)
        self.acceptOnce('leavingMint', self.announceLeaving)
        bboard.post(self.getReadyPostName())

    def fixupLevelModel(self):
        MintRoom.MintRoom.setGeom(self, self.geom)
        MintRoom.MintRoom.initFloorCollisions(self)

    def setMint(self, mint):
        self.mint = mint

    def setBossConfronted(self, avId):
        self.mint.setBossConfronted(avId)

    def setDefeated(self):
        self.notify.info('setDefeated')
        from toontown.coghq import DistributedMint
        messenger.send(DistributedMint.DistributedMint.WinEvent)

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
        MintRoom.MintRoom.enterLtNotPresent(self)
        if __dev__:
            bboard.removeIfEqual(EditorGlobals.EditTargetPostName, self)
        self.ignore('f2')

    def enterLtPresent(self):
        MintRoom.MintRoom.enterLtPresent(self)
        if __dev__:
            bboard.post(EditorGlobals.EditTargetPostName, self)
        if self.mint is not None:
            self.mint.currentRoomName = MintRoomSpecs.CashbotMintRoomId2RoomName[self.roomId]

        def printPos(self = self):
            thisZone = self.getZoneNode(LevelConstants.UberZoneEntId)
            pos = base.localAvatar.getPos(thisZone)
            h = base.localAvatar.getH(thisZone)
            roomName = MintRoomSpecs.CashbotMintRoomId2RoomName[self.roomId]
            print 'mint pos: %s, h: %s, room: %s' % (repr(pos), h, roomName)
            if self.mint is not None:
                floorNum = self.mint.floorNum
            else:
                floorNum = '???'
            posStr = 'X: %.3f' % pos[0] + '\nY: %.3f' % pos[1] + '\nZ: %.3f' % pos[2] + '\nH: %.3f' % h + '\nmintId: %s' % self.mintId + '\nfloor: %s' % floorNum + '\nroomId: %s' % self.roomId + '\nroomName: %s' % roomName
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
        MintRoom.MintRoom.exit(self)
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

    def reservesJoining(self):
        pass

    def getCogSpec(self, cogId):
        cogSpecModule = MintRoomSpecs.getCogSpecModule(self.roomId)
        return cogSpecModule.CogData[cogId]

    def getReserveCogSpec(self, cogId):
        cogSpecModule = MintRoomSpecs.getCogSpecModule(self.roomId)
        return cogSpecModule.ReserveCogData[cogId]

    def getBattleCellSpec(self, battleCellId):
        cogSpecModule = MintRoomSpecs.getCogSpecModule(self.roomId)
        return cogSpecModule.BattleCells[battleCellId]

    def getFloorOuchLevel(self):
        return 8

    def getTaskZoneId(self):
        return self.mintId

    def getBossTaunt(self):
        return TTLocalizer.MintBossTaunt

    def getBossBattleTaunt(self):
        return TTLocalizer.MintBossBattleTaunt

    def __str__(self):
        if hasattr(self, 'roomId'):
            return '%s %s: %s' % (self.__class__.__name__, self.roomId, MintRoomSpecs.CashbotMintRoomId2RoomName[self.roomId])
        else:
            return 'DistributedMintRoom'

    def __repr__(self):
        return str(self)
