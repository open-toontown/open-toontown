from otp.level import DistributedLevelAI
from direct.directnotify import DirectNotifyGlobal
from toontown.coghq import LevelSuitPlannerAI, LawOfficeBase
from direct.task import Task
from toontown.coghq import FactoryEntityCreatorAI, FactorySpecs
from otp.level import LevelSpec
from toontown.coghq import CogDisguiseGlobals
from toontown.suit import DistributedFactorySuitAI
from toontown.toonbase import ToontownGlobals, ToontownBattleGlobals
from toontown.coghq import DistributedBattleFactoryAI
from toontown.coghq import LawOfficeLayout
from toontown.coghq import DistributedLawOfficeElevatorIntAI
from direct.distributed import DistributedObjectAI
from toontown.ai.ToonBarrier import *

class DistributedLawOfficeFloorAI(DistributedLevelAI.DistributedLevelAI, LawOfficeBase.LawOfficeBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedLawOfficeAI')

    def __init__(self, air, lawOfficeId, zoneId, entranceId, avIds, spec):
        DistributedLevelAI.DistributedLevelAI.__init__(self, air, zoneId, entranceId, avIds)
        LawOfficeBase.LawOfficeBase.__init__(self)
        self.setLawOfficeId(lawOfficeId)
        self.layout = None
        self.elevator = None
        self.level = None
        self.spec = spec
        return

    def createEntityCreator(self):
        return FactoryEntityCreatorAI.FactoryEntityCreatorAI(level=self)

    def getBattleCreditMultiplier(self):
        return ToontownBattleGlobals.getFactoryCreditMultiplier(self.lawOfficeId)

    def generate(self):
        self.notify.info('generate')
        self.notify.info('start factory %s %s creation, frame=%s' % (self.lawOfficeId, self.doId, globalClock.getFrameCount()))
        self.layout = LawOfficeLayout.LawOfficeLayout(self.lawOfficeId)
        self.startFloor()

    def startFloor(self):
        self.notify.info('loading spec')
        self.factorySpec = LevelSpec.LevelSpec(self.spec)
        if __dev__:
            self.notify.info('creating entity type registry')
            typeReg = self.getEntityTypeReg()
            self.factorySpec.setEntityTypeReg(typeReg)
        self.notify.info('creating entities')
        DistributedLevelAI.DistributedLevelAI.generate(self, self.factorySpec)
        self.notify.info('creating cogs')
        cogSpecModule = FactorySpecs.getCogSpecModule(self.lawOfficeId)
        self.planner = LevelSuitPlannerAI.LevelSuitPlannerAI(self.air, self, DistributedFactorySuitAI.DistributedFactorySuitAI, DistributedBattleFactoryAI.DistributedBattleFactoryAI, cogSpecModule.CogData, cogSpecModule.ReserveCogData, cogSpecModule.BattleCells)
        suitHandles = self.planner.genSuits()
        messenger.send('plannerCreated-' + str(self.doId))
        self.suits = suitHandles['activeSuits']
        self.reserveSuits = suitHandles['reserveSuits']
        self.d_setSuits()
        scenario = 0
        description = '%s|%s|%s|%s' % (self.lawOfficeId, self.entranceId, scenario, self.avIdList)
        for avId in self.avIdList:
            self.air.writeServerEvent('DAOffice Entered', avId, description)

        self.notify.info('finish factory %s %s creation' % (self.lawOfficeId, self.doId))

    def delete(self):
        self.notify.info('delete: %s' % self.doId)
        suits = self.suits
        for reserve in self.reserveSuits:
            suits.append(reserve[0])

        self.planner.destroy()
        del self.planner
        for suit in suits:
            if not suit.isDeleted():
                suit.factoryIsGoingDown()
                suit.requestDelete()

        DistributedLevelAI.DistributedLevelAI.delete(self, False)

    def readyForNextFloor(self):
        toonId = self.air.getAvatarIdFromSender()
        self.__barrier.clear(toonId)

    def dumpEveryone(self):
        pass

    def getTaskZoneId(self):
        return self.lawOfficeId

    def getLawOfficeId(self):
        return self.lawOfficeId

    def d_setForemanConfronted(self, avId):
        if avId in self.avIdList:
            self.sendUpdate('setForemanConfronted', [avId])
        else:
            self.notify.warning('%s: d_setForemanConfronted: av %s not in av list %s' % (self.doId, avId, self.avIdList))

    def setVictors(self, victorIds):
        activeVictors = []
        activeVictorIds = []
        for victorId in victorIds:
            toon = self.air.doId2do.get(victorId)
            if toon is not None:
                activeVictors.append(toon)
                activeVictorIds.append(victorId)

        scenario = 0
        description = '%s|%s|%s|%s' % (self.lawOfficeId, self.entranceId, scenario, activeVictorIds)
        for avId in activeVictorIds:
            self.air.writeServerEvent('DAOffice Defeated', avId, description)

        for toon in activeVictors:
            simbase.air.questManager.toonDefeatedFactory(toon, self.lawOfficeId, activeVictors)

        return

    def b_setDefeated(self):
        self.d_setDefeated()
        self.setDefeated()

    def d_setDefeated(self):
        self.sendUpdate('setDefeated')

    def setDefeated(self):
        pass

    def getCogLevel(self):
        return self.cogLevel

    def d_setSuits(self):
        self.sendUpdate('setSuits', [self.getSuits(), self.getReserveSuits()])

    def getSuits(self):
        suitIds = []
        for suit in self.suits:
            suitIds.append(suit.doId)

        return suitIds

    def getReserveSuits(self):
        suitIds = []
        for suit in self.reserveSuits:
            suitIds.append(suit[0].doId)

        return suitIds
