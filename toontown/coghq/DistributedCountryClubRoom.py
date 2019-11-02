from pandac.PandaModules import *
from toontown.toonbase.ToontownGlobals import *
from direct.distributed.ClockDelta import *
from direct.interval.IntervalGlobal import *
import random
from otp.level import DistributedLevel
from direct.directnotify import DirectNotifyGlobal
import CountryClubRoomBase, CountryClubRoom
import FactoryEntityCreator
import CountryClubRoomSpecs
from otp.level import LevelSpec, LevelConstants
from toontown.toonbase import TTLocalizer
if __dev__:
    from otp.level import EditorGlobals

def getCountryClubRoomReadyPostName(doId):
    return 'countryClubRoomReady-%s' % doId


class DistributedCountryClubRoom(DistributedLevel.DistributedLevel, CountryClubRoomBase.CountryClubRoomBase, CountryClubRoom.CountryClubRoom):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedCountryClubRoom')
    EmulateEntrancePoint = False

    def __init__(self, cr):
        DistributedLevel.DistributedLevel.__init__(self, cr)
        CountryClubRoomBase.CountryClubRoomBase.__init__(self)
        CountryClubRoom.CountryClubRoom.__init__(self)
        self.suitIds = []
        self.suits = []
        self.reserveSuits = []
        self.joiningReserves = []
        self.suitsInitialized = 0
        self.goonClipPlanes = {}
        self.countryClub = None
        return

    def createEntityCreator(self):
        return FactoryEntityCreator.FactoryEntityCreator(level=self)

    def generate(self):
        self.notify.debug('generate')
        DistributedLevel.DistributedLevel.generate(self)

    def delete(self):
        del self.countryClub
        DistributedLevel.DistributedLevel.delete(self)
        CountryClubRoom.CountryClubRoom.delete(self)
        self.ignoreAll()

    def setCountryClubId(self, countryClubId):
        self.notify.debug('countryClubId: %s' % countryClubId)
        CountryClubRoomBase.CountryClubRoomBase.setCountryClubId(self, countryClubId)

    def setRoomId(self, roomId):
        self.notify.debug('roomId: %s' % roomId)
        CountryClubRoomBase.CountryClubRoomBase.setRoomId(self, roomId)

    def setRoomNum(self, num):
        self.notify.debug('roomNum: %s' % num)
        CountryClubRoom.CountryClubRoom.setRoomNum(self, num)

    def levelAnnounceGenerate(self):
        self.notify.debug('levelAnnounceGenerate')
        DistributedLevel.DistributedLevel.levelAnnounceGenerate(self)
        specModule = CountryClubRoomSpecs.getCountryClubRoomSpecModule(self.roomId)
        roomSpec = LevelSpec.LevelSpec(specModule)
        if __dev__:
            typeReg = self.getCountryClubEntityTypeReg()
            roomSpec.setEntityTypeReg(typeReg)
        DistributedLevel.DistributedLevel.initializeLevel(self, roomSpec)

    def getReadyPostName(self):
        return getCountryClubRoomReadyPostName(self.doId)

    def privGotSpec(self, levelSpec):
        if __dev__:
            if not levelSpec.hasEntityTypeReg():
                typeReg = self.getCountryClubEntityTypeReg()
                levelSpec.setEntityTypeReg(typeReg)
        DistributedLevel.DistributedLevel.privGotSpec(self, levelSpec)
        base.localAvatar.setH(-90)
        CountryClubRoom.CountryClubRoom.enter(self)
        self.acceptOnce('leavingCountryClub', self.announceLeaving)
        bboard.post(self.getReadyPostName())

    def fixupLevelModel(self):
        CountryClubRoom.CountryClubRoom.setGeom(self, self.geom)
        CountryClubRoom.CountryClubRoom.initFloorCollisions(self)

    def setCountryClub(self, countryClub):
        self.countryClub = countryClub

    def setBossConfronted(self, avId):
        self.countryClub.setBossConfronted(avId)

    def setDefeated(self):
        self.notify.info('setDefeated')
        from toontown.coghq import DistributedCountryClub
        messenger.send(DistributedCountryClub.DistributedCountryClub.WinEvent)

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
        CountryClubRoom.CountryClubRoom.enterLtNotPresent(self)
        if __dev__:
            bboard.removeIfEqual(EditorGlobals.EditTargetPostName, self)
        self.ignore('f2')

    def enterLtPresent(self):
        CountryClubRoom.CountryClubRoom.enterLtPresent(self)
        if __dev__:
            bboard.post(EditorGlobals.EditTargetPostName, self)
        if self.countryClub is not None:
            self.countryClub.currentRoomName = CountryClubRoomSpecs.BossbotCountryClubRoomId2RoomName[self.roomId]

        def printPos(self = self):
            thisZone = self.getZoneNode(LevelConstants.UberZoneEntId)
            pos = base.localAvatar.getPos(thisZone)
            h = base.localAvatar.getH(thisZone)
            roomName = CountryClubRoomSpecs.BossbotCountryClubRoomId2RoomName[self.roomId]
            print 'countryClub pos: %s, h: %s, room: %s' % (repr(pos), h, roomName)
            if self.countryClub is not None:
                floorNum = self.countryClub.floorNum
            else:
                floorNum = '???'
            posStr = 'X: %.3f' % pos[0] + '\nY: %.3f' % pos[1] + '\nZ: %.3f' % pos[2] + '\nH: %.3f' % h + '\ncountryClubId: %s' % self.countryClubId + '\nfloor: %s' % floorNum + '\nroomId: %s' % self.roomId + '\nroomName: %s' % roomName
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
        CountryClubRoom.CountryClubRoom.exit(self)
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
        cogSpecModule = CountryClubRoomSpecs.getCogSpecModule(self.roomId)
        return cogSpecModule.CogData[cogId]

    def getReserveCogSpec(self, cogId):
        cogSpecModule = CountryClubRoomSpecs.getCogSpecModule(self.roomId)
        return cogSpecModule.ReserveCogData[cogId]

    def getBattleCellSpec(self, battleCellId):
        cogSpecModule = CountryClubRoomSpecs.getCogSpecModule(self.roomId)
        return cogSpecModule.BattleCells[battleCellId]

    def getFloorOuchLevel(self):
        return 8

    def getTaskZoneId(self):
        return self.countryClubId

    def getBossTaunt(self):
        return TTLocalizer.CountryClubBossTaunt

    def getBossBattleTaunt(self):
        return TTLocalizer.CountryClubBossBattleTaunt

    def __str__(self):
        if hasattr(self, 'roomId'):
            return '%s %s: %s' % (self.__class__.__name__, self.roomId, CountryClubRoomSpecs.BossbotCountryClubRoomId2RoomName[self.roomId])
        else:
            return 'DistributedCountryClubRoom'

    def __repr__(self):
        return str(self)

    def forceOuch(self, penalty):
        self.setOuch(penalty)
