from direct.directnotify import DirectNotifyGlobal
from panda3d.core import *

from libtoontown import *
from otp.ai.AIZoneData import AIZoneDataStore
from otp.ai.TimeManagerAI import TimeManagerAI
from otp.distributed.OtpDoGlobals import *
from toontown.ai.HolidayManagerAI import HolidayManagerAI
from toontown.ai.NewsManagerAI import NewsManagerAI
from toontown.ai.WelcomeValleyManagerAI import WelcomeValleyManagerAI
from toontown.building.DistributedTrophyMgrAI import DistributedTrophyMgrAI
from toontown.catalog.CatalogManagerAI import CatalogManagerAI
from toontown.coghq.CogSuitManagerAI import CogSuitManagerAI
from toontown.coghq.CountryClubManagerAI import CountryClubManagerAI
from toontown.coghq.FactoryManagerAI import FactoryManagerAI
from toontown.coghq.LawOfficeManagerAI import LawOfficeManagerAI
from toontown.coghq.MintManagerAI import MintManagerAI
from toontown.coghq.PromotionManagerAI import PromotionManagerAI
from toontown.distributed.ToontownDistrictAI import ToontownDistrictAI
from toontown.distributed.ToontownDistrictStatsAI import ToontownDistrictStatsAI
from toontown.distributed.ToontownInternalRepository import ToontownInternalRepository
from toontown.hood import ZoneUtil
from toontown.hood.BRHoodDataAI import BRHoodDataAI
from toontown.hood.BossbotHQDataAI import BossbotHQDataAI
from toontown.hood.CSHoodDataAI import CSHoodDataAI
from toontown.hood.CashbotHQDataAI import CashbotHQDataAI
from toontown.hood.DDHoodDataAI import DDHoodDataAI
from toontown.hood.DGHoodDataAI import DGHoodDataAI
from toontown.hood.DLHoodDataAI import DLHoodDataAI
from toontown.hood.GSHoodDataAI import GSHoodDataAI
from toontown.hood.GZHoodDataAI import GZHoodDataAI
from toontown.hood.LawbotHQDataAI import LawbotHQDataAI
from toontown.hood.MMHoodDataAI import MMHoodDataAI
from toontown.hood.OZHoodDataAI import OZHoodDataAI
from toontown.hood.TTHoodDataAI import TTHoodDataAI
from toontown.pets.PetManagerAI import PetManagerAI
from toontown.quest.QuestManagerAI import QuestManagerAI
from toontown.racing import RaceGlobals
from toontown.racing.DistributedLeaderBoardAI import DistributedLeaderBoardAI
from toontown.racing.DistributedRacePadAI import DistributedRacePadAI
from toontown.racing.DistributedStartingBlockAI import DistributedStartingBlockAI
from toontown.racing.DistributedStartingBlockAI import DistributedViewingBlockAI
from toontown.racing.DistributedViewPadAI import DistributedViewPadAI
from toontown.racing.RaceManagerAI import RaceManagerAI
from toontown.shtiker.CogPageManagerAI import CogPageManagerAI
from toontown.suit.SuitInvasionManagerAI import SuitInvasionManagerAI
from toontown.toon import NPCToons
from toontown.toonbase import ToontownGlobals
from toontown.uberdog.DistributedInGameNewsMgrAI import DistributedInGameNewsMgrAI


class ToontownAIRepository(ToontownInternalRepository):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownAIRepository')

    def __init__(self, baseChannel, serverId, districtName):
        ToontownInternalRepository.__init__(self, baseChannel, serverId, dcSuffix='AI')
        self.districtName = districtName
        self.doLiveUpdates = config.GetBool('want-live-updates', True)
        self.wantCogdominiums = config.GetBool('want-cogdominiums', True)
        self.useAllMinigames = config.GetBool('want-all-minigames', True)
        self.districtId = None
        self.district = None
        self.districtStats = None
        self.holidayManager = None
        self.zoneDataStore = None
        self.petMgr = None
        self.suitInvasionManager = None
        self.zoneAllocator = None
        self.zoneId2owner = {}
        self.questManager = None
        self.promotionMgr = None
        self.cogPageManager = None
        self.raceMgr = None
        self.countryClubMgr = None
        self.factoryMgr = None
        self.mintMgr = None
        self.lawMgr = None
        self.cogSuitMgr = None
        self.timeManager = None
        self.newsManager = None
        self.welcomeValleyManager = None
        self.inGameNewsMgr = None
        self.catalogManager = None
        self.trophyMgr = None
        self.zoneTable = {}
        self.dnaStoreMap = {}
        self.dnaDataMap = {}
        self.hoods = []
        self.buildingManagers = {}
        self.suitPlanners = {}

    def handleConnected(self):
        ToontownInternalRepository.handleConnected(self)

        # Generate our district...
        self.districtId = self.allocateChannel()
        self.district = ToontownDistrictAI(self)
        self.district.setName(self.districtName)
        self.district.generateWithRequiredAndId(self.districtId, self.getGameDoId(), OTP_ZONE_ID_DISTRICTS)

        # Claim ownership of that district...
        self.district.setAI(self.ourChannel)

        # Create our local objects.
        self.createLocals()

        # Create our global objects.
        self.createGlobals()

        # Create our zones.
        self.createZones()

        # Make our district available, and we're done.
        self.district.b_setAvailable(True)
        self.notify.info('Done.')

    def createLocals(self):
        """
        Creates "local" (non-distributed) objects.
        """

        # Create our holiday manager...
        self.holidayManager = HolidayManagerAI(self)

        # Create our zone data store...
        self.zoneDataStore = AIZoneDataStore()

        # Create our pet manager...
        self.petMgr = PetManagerAI(self)

        # Create our suit invasion manager...
        self.suitInvasionManager = SuitInvasionManagerAI(self)

        # Create our zone allocator...
        self.zoneAllocator = UniqueIdAllocator(ToontownGlobals.DynamicZonesBegin, ToontownGlobals.DynamicZonesEnd)

        # Create our quest manager...
        self.questManager = QuestManagerAI(self)

        # Create our promotion manager...
        self.promotionMgr = PromotionManagerAI(self)

        # Create our Cog page manager...
        self.cogPageManager = CogPageManagerAI(self)

        # Create our race manager...
        self.raceMgr = RaceManagerAI(self)

        # Create our country club manager...
        self.countryClubMgr = CountryClubManagerAI(self)

        # Create our factory manager...
        self.factoryMgr = FactoryManagerAI(self)

        # Create our mint manager...
        self.mintMgr = MintManagerAI(self)

        # Create our law office manager...
        self.lawMgr = LawOfficeManagerAI(self)

        # Create our Cog suit manager...
        self.cogSuitMgr = CogSuitManagerAI(self)

    def createGlobals(self):
        """
        Creates "global" (distributed) objects.
        """

        # Generate our district stats...
        self.districtStats = ToontownDistrictStatsAI(self)
        self.districtStats.settoontownDistrictId(self.districtId)
        self.districtStats.generateWithRequiredAndId(self.allocateChannel(), self.district.getDoId(),
                                                     OTP_ZONE_ID_DISTRICTS_STATS)

        # Generate our time manager...
        self.timeManager = TimeManagerAI(self)
        self.timeManager.generateWithRequired(OTP_ZONE_ID_MANAGEMENT)

        # Generate our news manager...
        self.newsManager = NewsManagerAI(self)
        self.newsManager.generateWithRequired(OTP_ZONE_ID_MANAGEMENT)

        # Generate our Welcome Valley manager...
        self.welcomeValleyManager = WelcomeValleyManagerAI(self)
        self.welcomeValleyManager.generateWithRequired(OTP_ZONE_ID_MANAGEMENT)

        # Generate our in-game news manager...
        self.inGameNewsMgr = DistributedInGameNewsMgrAI(self)
        self.inGameNewsMgr.generateWithRequired(OTP_ZONE_ID_MANAGEMENT)

        # Generate our catalog manager...
        self.catalogManager = CatalogManagerAI(self)
        self.catalogManager.generateWithRequired(OTP_ZONE_ID_MANAGEMENT)

        # Generate our trophy manager...
        self.trophyMgr = DistributedTrophyMgrAI(self)
        self.trophyMgr.generateWithRequired(OTP_ZONE_ID_MANAGEMENT)

    def generateHood(self, hoodConstructor, zoneId):
        # Bossbot HQ doesn't use DNA, so we skip over that.
        if zoneId != ToontownGlobals.BossbotHQ:
            self.dnaStoreMap[zoneId] = DNAStorage()
            self.dnaDataMap[zoneId] = loadDNAFileAI(self.dnaStoreMap[zoneId], self.genDNAFileName(zoneId))
            if zoneId in ToontownGlobals.HoodHierarchy:
                for streetId in ToontownGlobals.HoodHierarchy[zoneId]:
                    self.dnaStoreMap[streetId] = DNAStorage()
                    self.dnaDataMap[streetId] = loadDNAFileAI(self.dnaStoreMap[streetId], self.genDNAFileName(streetId))

        hood = hoodConstructor(self, zoneId)
        hood.startup()
        self.hoods.append(hood)

    def createZones(self):
        # First, generate our zone2NpcDict...
        NPCToons.generateZone2NpcDict()

        # Donald's Dock
        self.zoneTable[ToontownGlobals.DonaldsDock] = (
            (ToontownGlobals.DonaldsDock, 1, 0), (ToontownGlobals.BarnacleBoulevard, 1, 1),
            (ToontownGlobals.SeaweedStreet, 1, 1), (ToontownGlobals.LighthouseLane, 1, 1)
        )
        self.generateHood(DDHoodDataAI, ToontownGlobals.DonaldsDock)

        # Toontown Central
        self.zoneTable[ToontownGlobals.ToontownCentral] = (
            (ToontownGlobals.ToontownCentral, 1, 0), (ToontownGlobals.SillyStreet, 1, 1),
            (ToontownGlobals.LoopyLane, 1, 1), (ToontownGlobals.PunchlinePlace, 1, 1)
        )
        self.generateHood(TTHoodDataAI, ToontownGlobals.ToontownCentral)

        # The Brrrgh
        self.zoneTable[ToontownGlobals.TheBrrrgh] = (
            (ToontownGlobals.TheBrrrgh, 1, 0), (ToontownGlobals.WalrusWay, 1, 1),
            (ToontownGlobals.SleetStreet, 1, 1), (ToontownGlobals.PolarPlace, 1, 1)
        )
        self.generateHood(BRHoodDataAI, ToontownGlobals.TheBrrrgh)

        # Minnie's Melodyland
        self.zoneTable[ToontownGlobals.MinniesMelodyland] = (
            (ToontownGlobals.MinniesMelodyland, 1, 0), (ToontownGlobals.AltoAvenue, 1, 1),
            (ToontownGlobals.BaritoneBoulevard, 1, 1), (ToontownGlobals.TenorTerrace, 1, 1)
        )
        self.generateHood(MMHoodDataAI, ToontownGlobals.MinniesMelodyland)

        # Daisy Gardens
        self.zoneTable[ToontownGlobals.DaisyGardens] = (
            (ToontownGlobals.DaisyGardens, 1, 0), (ToontownGlobals.ElmStreet, 1, 1),
            (ToontownGlobals.MapleStreet, 1, 1), (ToontownGlobals.OakStreet, 1, 1)
        )
        self.generateHood(DGHoodDataAI, ToontownGlobals.DaisyGardens)

        # Chip 'n Dale's Acorn Acres
        self.zoneTable[ToontownGlobals.OutdoorZone] = (
            (ToontownGlobals.OutdoorZone, 1, 0),
        )
        self.generateHood(OZHoodDataAI, ToontownGlobals.OutdoorZone)

        # Goofy Speedway
        self.zoneTable[ToontownGlobals.GoofySpeedway] = (
            (ToontownGlobals.GoofySpeedway, 1, 0),
        )
        self.generateHood(GSHoodDataAI, ToontownGlobals.GoofySpeedway)

        # Donald's Dreamland
        self.zoneTable[ToontownGlobals.DonaldsDreamland] = (
            (ToontownGlobals.DonaldsDreamland, 1, 0), (ToontownGlobals.LullabyLane, 1, 1),
            (ToontownGlobals.PajamaPlace, 1, 1)
        )
        self.generateHood(DLHoodDataAI, ToontownGlobals.DonaldsDreamland)

        # Bossbot HQ
        self.zoneTable[ToontownGlobals.BossbotHQ] = (
            (ToontownGlobals.BossbotHQ, 0, 0),
        )
        self.generateHood(BossbotHQDataAI, ToontownGlobals.BossbotHQ)

        # Sellbot HQ
        self.zoneTable[ToontownGlobals.SellbotHQ] = (
            (ToontownGlobals.SellbotHQ, 0, 1), (ToontownGlobals.SellbotFactoryExt, 0, 1)
        )
        self.generateHood(CSHoodDataAI, ToontownGlobals.SellbotHQ)

        # Cashbot HQ
        self.zoneTable[ToontownGlobals.CashbotHQ] = (
            (ToontownGlobals.CashbotHQ, 0, 1),
        )
        self.generateHood(CashbotHQDataAI, ToontownGlobals.CashbotHQ)

        # Lawbot HQ
        self.zoneTable[ToontownGlobals.LawbotHQ] = (
            (ToontownGlobals.LawbotHQ, 0, 1),
        )
        self.generateHood(LawbotHQDataAI, ToontownGlobals.LawbotHQ)

        # Chip 'n Dale's MiniGolf
        self.zoneTable[ToontownGlobals.GolfZone] = (
            (ToontownGlobals.GolfZone, 1, 0),
        )
        self.generateHood(GZHoodDataAI, ToontownGlobals.GolfZone)

        # Welcome Valley zones
        self.welcomeValleyManager.createWelcomeValleyZones()

        # Assign the initial suit buildings.
        for suitPlanner in list(self.suitPlanners.values()):
            suitPlanner.assignInitialSuitBuildings()

    def genDNAFileName(self, zoneId):
        canonicalZoneId = ZoneUtil.getCanonicalZoneId(zoneId)
        canonicalHoodId = ZoneUtil.getCanonicalHoodId(canonicalZoneId)
        hood = ToontownGlobals.dnaMap[canonicalHoodId]
        if canonicalHoodId == canonicalZoneId:
            canonicalZoneId = 'sz'
            phase = ToontownGlobals.phaseMap[canonicalHoodId]
        else:
            phase = ToontownGlobals.streetPhaseMap[canonicalHoodId]

        if 'outdoor_zone' in hood or 'golf_zone' in hood:
            phase = '6'

        return 'phase_%s/dna/%s_%s.dna' % (phase, hood, canonicalZoneId)

    def lookupDNAFileName(self, dnaFileName):
        searchPath = DSearchPath()
        searchPath.appendDirectory(Filename('resources/phase_3.5/dna'))
        searchPath.appendDirectory(Filename('resources/phase_4/dna'))
        searchPath.appendDirectory(Filename('resources/phase_5/dna'))
        searchPath.appendDirectory(Filename('resources/phase_5.5/dna'))
        searchPath.appendDirectory(Filename('resources/phase_6/dna'))
        searchPath.appendDirectory(Filename('resources/phase_8/dna'))
        searchPath.appendDirectory(Filename('resources/phase_9/dna'))
        searchPath.appendDirectory(Filename('resources/phase_10/dna'))
        searchPath.appendDirectory(Filename('resources/phase_11/dna'))
        searchPath.appendDirectory(Filename('resources/phase_12/dna'))
        searchPath.appendDirectory(Filename('resources/phase_13/dna'))
        filename = Filename(dnaFileName)
        found = vfs.resolveFilename(filename, searchPath)
        if not found:
            self.notify.warning('lookupDNAFileName - %s not found on:' % dnaFileName)
            print(searchPath)
        else:
            return filename.getFullpath()

    def loadDNAFileAI(self, dnaStore, dnaFileName):
        return loadDNAFileAI(dnaStore, dnaFileName)

    def findFishingPonds(self, dnaData, zoneId, area):
        return [], []  # TODO

    def findPartyHats(self, dnaData, zoneId):
        return []  # TODO

    def findRacingPads(self, dnaData, zoneId, area, type='racing_pad', overrideDNAZone=False):
        kartPads, kartPadGroups = [], []
        if type in dnaData.getName():
            if type == 'racing_pad':
                nameSplit = dnaData.getName().split('_')
                racePad = DistributedRacePadAI(self)
                racePad.setArea(area)
                racePad.index = int(nameSplit[2])
                racePad.genre = nameSplit[3]
                trackInfo = RaceGlobals.getNextRaceInfo(-1, racePad.genre, racePad.index)
                racePad.setTrackInfo([trackInfo[0], trackInfo[1]])
                racePad.laps = trackInfo[2]
                racePad.generateWithRequired(zoneId)
                kartPads.append(racePad)
                kartPadGroups.append(dnaData)
            elif type == 'viewing_pad':
                viewPad = DistributedViewPadAI(self)
                viewPad.setArea(area)
                viewPad.generateWithRequired(zoneId)
                kartPads.append(viewPad)
                kartPadGroups.append(dnaData)

        for i in range(dnaData.getNumChildren()):
            foundKartPads, foundKartPadGroups = self.findRacingPads(dnaData.at(i), zoneId, area, type, overrideDNAZone)
            kartPads.extend(foundKartPads)
            kartPadGroups.extend(foundKartPadGroups)

        return kartPads, kartPadGroups

    def findStartingBlocks(self, dnaData, kartPad):
        startingBlocks = []
        for i in range(dnaData.getNumChildren()):
            groupName = dnaData.getName()
            block = dnaData.at(i)
            blockName = block.getName()
            if 'starting_block' in blockName:
                cls = DistributedStartingBlockAI if 'racing_pad' in groupName else DistributedViewingBlockAI
                x, y, z = block.getPos()
                h, p, r = block.getHpr()
                padLocationId = int(blockName[-1])
                startingBlock = cls(self, kartPad, x, y, z, h, p, r, padLocationId)
                startingBlock.generateWithRequired(kartPad.zoneId)
                startingBlocks.append(startingBlock)

        return startingBlocks

    def findLeaderBoards(self, dnaData, zoneId):
        leaderBoards = []
        if 'leaderBoard' in dnaData.getName():
            x, y, z = dnaData.getPos()
            h, p, r = dnaData.getHpr()
            leaderBoard = DistributedLeaderBoardAI(self, dnaData.getName(), x, y, z, h, p, r)
            leaderBoard.generateWithRequired(zoneId)
            leaderBoards.append(leaderBoard)

        for i in range(dnaData.getNumChildren()):
            foundLeaderBoards = self.findLeaderBoards(dnaData.at(i), zoneId)
            leaderBoards.extend(foundLeaderBoards)

        return leaderBoards

    def getTrackClsends(self):
        return False

    def getAvatarExitEvent(self, avId):
        return 'distObjDelete-%d' % avId

    def getAvatarDisconnectReason(self, avId):
        return self.timeManager.avId2disconnectcode.get(avId, ToontownGlobals.DisconnectUnknown)

    def getZoneDataStore(self):
        return self.zoneDataStore

    def incrementPopulation(self):
        self.districtStats.b_setAvatarCount(self.districtStats.getAvatarCount() + 1)

    def decrementPopulation(self):
        self.districtStats.b_setAvatarCount(self.districtStats.getAvatarCount() - 1)

    def allocateZone(self, owner=None):
        zoneId = self.zoneAllocator.allocate()
        if owner:
            self.zoneId2owner[zoneId] = owner

        return zoneId

    def deallocateZone(self, zone):
        if self.zoneId2owner.get(zone):
            del self.zoneId2owner[zone]

        self.zoneAllocator.free(zone)

    def trueUniqueName(self, idString):
        return self.uniqueName(idString)

    def sendQueryToonMaxHp(self, avId, callback):
        pass  # TODO?
