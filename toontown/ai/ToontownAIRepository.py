from direct.directnotify import DirectNotifyGlobal
from otp.ai.AIZoneData import AIZoneDataStore
from otp.distributed.OtpDoGlobals import *
from toontown.distributed.ToontownInternalRepository import ToontownInternalRepository
from toontown.distributed.ToontownDistrictAI import ToontownDistrictAI
from toontown.distributed.ToontownDistrictStatsAI import ToontownDistrictStatsAI
from toontown.ai.HolidayManagerAI import HolidayManagerAI
from toontown.ai.NewsManagerAI import NewsManagerAI
from toontown.catalog.CatalogManagerAI import CatalogManagerAI
from toontown.uberdog.DistributedInGameNewsMgrAI import DistributedInGameNewsMgrAI

class ToontownAIRepository(ToontownInternalRepository):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownAIRepository')

    def __init__(self, baseChannel, serverId, districtName):
        ToontownInternalRepository.__init__(self, baseChannel, serverId, dcSuffix='AI')
        self.districtName = districtName
        self.doLiveUpdates = config.GetBool('want-live-updates', True)
        self.districtId = None
        self.district = None
        self.districtStats = None
        self.holidayManager = None
        self.zoneDataStore = None
        self.newsManager = None
        self.inGameNewsMgr = None
        self.catalogManager = None

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

    def createGlobals(self):
        """
        Creates "global" (distributed) objects.
        """

        # Generate our district stats...
        self.districtStats = ToontownDistrictStatsAI(self)
        self.districtStats.settoontownDistrictId(self.districtId)
        self.districtStats.generateWithRequiredAndId(self.allocateChannel(), self.district.getDoId(),
                                                     OTP_ZONE_ID_DISTRICTS_STATS)

        # Generate our news manager...
        self.newsManager = NewsManagerAI(self)
        self.newsManager.generateWithRequired(OTP_ZONE_ID_MANAGEMENT)

        # Generate our in-game news manager...
        self.inGameNewsMgr = DistributedInGameNewsMgrAI(self)
        self.inGameNewsMgr.generateWithRequired(OTP_ZONE_ID_MANAGEMENT)

        # Generate our catalog manager...
        self.catalogManager = CatalogManagerAI(self)
        self.catalogManager.generateWithRequired(OTP_ZONE_ID_MANAGEMENT)

    def getTrackClsends(self):
        return False

    def getAvatarExitEvent(self, avId):
        return 'distObjDelete-%d' % avId

    def getZoneDataStore(self):
        return self.zoneDataStore

    def incrementPopulation(self):
        self.districtStats.b_setAvatarCount(self.districtStats.getAvatarCount() + 1)

    def decrementPopulation(self):
        self.districtStats.b_setAvatarCount(self.districtStats.getAvatarCount() - 1)

    def sendQueryToonMaxHp(self, avId, callback):
        pass  # TODO?
