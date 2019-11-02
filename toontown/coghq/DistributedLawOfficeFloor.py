from pandac.PandaModules import *
from toontown.toonbase.ToontownGlobals import *
from direct.distributed.ClockDelta import *
from direct.interval.IntervalGlobal import *
import random
from otp.level import DistributedLevel
from direct.directnotify import DirectNotifyGlobal
import LawOfficeBase
import FactoryEntityCreator
import FactorySpecs
from otp.level import LevelSpec
from otp.level import LevelConstants
from toontown.toonbase import TTLocalizer
from toontown.coghq import FactoryCameraViews
if __dev__:
    from otp.level import EditorGlobals

class DistributedLawOfficeFloor(DistributedLevel.DistributedLevel, LawOfficeBase.LawOfficeBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedLawOffice')

    def __init__(self, cr):
        DistributedLevel.DistributedLevel.__init__(self, cr)
        LawOfficeBase.LawOfficeBase.__init__(self)
        self.suitIds = []
        self.suits = []
        self.reserveSuits = []
        self.joiningReserves = []
        self.suitsInitialized = 0
        self.goonClipPlanes = {}

    def createEntityCreator(self):
        return FactoryEntityCreator.FactoryEntityCreator(level=self)

    def generate(self):
        self.notify.debug('generate')
        DistributedLevel.DistributedLevel.generate(self)
        self.factoryViews = FactoryCameraViews.FactoryCameraViews(self)
        base.localAvatar.chatMgr.chatInputSpeedChat.addFactoryMenu()
        if __dev__:
            bboard.post(EditorGlobals.EditTargetPostName, self)
        self.accept('SOSPanelEnter', self.handleSOSPanel)

    def delete(self):
        DistributedLevel.DistributedLevel.delete(self)
        base.localAvatar.chatMgr.chatInputSpeedChat.removeFactoryMenu()
        self.factoryViews.delete()
        del self.factoryViews
        self.ignore('SOSPanelEnter')
        if __dev__:
            bboard.removeIfEqual(EditorGlobals.EditTargetPostName, self)

    def setLawOfficeId(self, id):
        LawOfficeBase.LawOfficeBase.setLawOfficeId(self, id)

    def setForemanConfronted(self, avId):
        if avId == base.localAvatar.doId:
            return
        av = base.cr.identifyFriend(avId)
        if av is None:
            return
        base.localAvatar.setSystemMessage(avId, TTLocalizer.ForemanConfrontedMsg % av.getName())
        return

    def setDefeated(self):
        self.notify.info('setDefeated')
        messenger.send('FactoryWinEvent')

    def levelAnnounceGenerate(self):
        self.notify.debug('levelAnnounceGenerate')
        DistributedLevel.DistributedLevel.levelAnnounceGenerate(self)
        specModule = FactorySpecs.getFactorySpecModule(self.lawOfficeId)
        factorySpec = LevelSpec.LevelSpec(specModule)
        if __dev__:
            typeReg = self.getEntityTypeReg()
            factorySpec.setEntityTypeReg(typeReg)
        DistributedLevel.DistributedLevel.initializeLevel(self, factorySpec)

    def privGotSpec(self, levelSpec):
        if __dev__:
            if not levelSpec.hasEntityTypeReg():
                typeReg = self.getEntityTypeReg()
                levelSpec.setEntityTypeReg(typeReg)
        firstSetZoneDoneEvent = self.cr.getNextSetZoneDoneEvent()

        def handleFirstSetZoneDone():
            base.factoryReady = 1
            messenger.send('FactoryReady')

        self.acceptOnce(firstSetZoneDoneEvent, handleFirstSetZoneDone)
        modelCount = len(levelSpec.getAllEntIds())
        loader.beginBulkLoad('factory', TTLocalizer.HeadingToFactoryTitle % TTLocalizer.FactoryNames[self.lawOfficeId], modelCount, 1, TTLocalizer.TIP_COGHQ)
        DistributedLevel.DistributedLevel.privGotSpec(self, levelSpec)
        loader.endBulkLoad('factory')
        messenger.send('LawOffice_Spec_Loaded')

        def printPos(self = self):
            pos = base.localAvatar.getPos(self.getZoneNode(self.lastToonZone))
            h = base.localAvatar.getH(self.getZoneNode(self.lastToonZone))
            print 'factory pos: %s, h: %s, zone %s' % (repr(pos), h, self.lastToonZone)
            posStr = 'X: %.3f' % pos[0] + '\nY: %.3f' % pos[1] + '\nZ: %.3f' % pos[2] + '\nH: %.3f' % h + '\nZone: %s' % str(self.lastToonZone)
            base.localAvatar.setChat(posStr, CFThought, 0)

        self.accept('f2', printPos)
        base.localAvatar.setCameraCollisionsCanMove(1)
        self.acceptOnce('leavingFactory', self.announceLeaving)

    def handleSOSPanel(self, panel):
        avIds = []
        for avId in self.avIdList:
            if base.cr.doId2do.get(avId):
                avIds.append(avId)

        panel.setFactoryToonIdList(avIds)

    def handleFloorDone(self):
        self.sendUpdate('readyForNextFloor')

    def disable(self):
        self.notify.debug('disable')
        base.localAvatar.setCameraCollisionsCanMove(0)
        if hasattr(self, 'suits'):
            del self.suits
        if hasattr(self, 'relatedObjectMgrRequest') and self.relatedObjectMgrRequest:
            self.cr.relatedObjectMgr.abortRequest(self.relatedObjectMgrRequest)
            del self.relatedObjectMgrRequest
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
        cogSpecModule = FactorySpecs.getCogSpecModule(self.lawOfficeId)
        return cogSpecModule.CogData[cogId]

    def getReserveCogSpec(self, cogId):
        cogSpecModule = FactorySpecs.getCogSpecModule(self.lawOfficeId)
        return cogSpecModule.ReserveCogData[cogId]

    def getBattleCellSpec(self, battleCellId):
        cogSpecModule = FactorySpecs.getCogSpecModule(self.lawOfficeId)
        return cogSpecModule.BattleCells[battleCellId]

    def getFloorOuchLevel(self):
        return 2

    def getGoonPathId(self):
        return 'sellbotFactory'

    def getTaskZoneId(self):
        return self.lawOfficeId

    def getBossTaunt(self):
        return TTLocalizer.FactoryBossTaunt

    def getBossBattleTaunt(self):
        return TTLocalizer.FactoryBossBattleTaunt

    def placeLocalToon(self):
        initialZoneEnt = None
        if self.entranceId in self.entranceId2entity:
            epEnt = self.entranceId2entity[self.entranceId]
            initialZoneEnt = self.getEntity(epEnt.getZoneEntId())
        elif self.EmulateEntrancePoint:
            self.notify.debug('unknown entranceId %s' % self.entranceId)
            self.notify.debug('showing all zones')
            self.setColorZones(1)
            zoneEntIds = list(self.entType2ids['zone'])
            zoneEntIds.remove(LevelConstants.UberZoneEntId)
            if len(zoneEntIds):
                zoneEntId = random.choice(zoneEntIds)
                initialZoneEnt = self.getEntity(zoneEntId)
            else:
                initialZoneEnt = self.getEntity(LevelConstants.UberZoneEntId)
        if initialZoneEnt is not None:
            self.enterZone(initialZoneEnt.entId)
        return
