from toontown.toonbase.ToontownGlobals import *
from otp.otpbase import OTPGlobals
from otp.ai import BanManagerAI
from direct.directnotify import DirectNotifyGlobal
from otp.ai.AIDistrict import AIDistrict
from toontown.suit import DistributedSuitPlannerAI
from toontown.safezone import DistributedBoatAI
from toontown.safezone import DistributedMMPianoAI
from toontown.safezone import DistributedDGFlowerAI
from toontown.safezone import DistributedTrolleyAI
#from otp.friends import FriendManagerAI
from toontown.shtiker import DeleteManagerAI
from toontown.safezone import SafeZoneManagerAI
from . import ToontownMagicWordManagerAI
from toontown.tutorial import TutorialManagerAI
from toontown.catalog import CatalogManagerAI
from otp.ai import TimeManagerAI
from . import WelcomeValleyManagerAI
from toontown.building import DistributedBuildingMgrAI
from toontown.building import DistributedTrophyMgrAI
from toontown.estate import DistributedBankMgrAI
from toontown.hood import TTHoodDataAI
from toontown.hood import DDHoodDataAI
from toontown.hood import MMHoodDataAI
from toontown.hood import DGHoodDataAI
from toontown.hood import BRHoodDataAI
from toontown.hood import DLHoodDataAI
from toontown.hood import CSHoodDataAI
from toontown.hood import GSHoodDataAI
from toontown.hood import OZHoodDataAI
from toontown.hood import GZHoodDataAI
from toontown.hood import CashbotHQDataAI
from toontown.hood import LawbotHQDataAI
from toontown.hood import BossbotHQDataAI
from toontown.quest import QuestManagerAI
from toontown.fishing import FishManagerAI
from toontown.shtiker import CogPageManagerAI
from toontown.coghq import FactoryManagerAI
from toontown.coghq import MintManagerAI
from toontown.coghq import LawOfficeManagerAI
from toontown.coghq import CountryClubManagerAI
from . import NewsManagerAI
from toontown.hood import ZoneUtil
from toontown.fishing import DistributedFishingPondAI
from toontown.safezone import DistributedFishingSpotAI
from toontown.safezone import DistributedButterflyAI
from toontown.safezone import DistributedPartyGateAI
from toontown.toon import NPCDialogueManagerAI
from toontown.toon import NPCToons

from toontown.safezone import ButterflyGlobals
from toontown.estate import EstateManagerAI
from toontown.suit import SuitInvasionManagerAI
from . import HolidayManagerAI
from toontown.effects import FireworkManagerAI
from toontown.coghq import CogSuitManagerAI
from toontown.coghq import PromotionManagerAI
from direct.task.Task import Task
if simbase.wantKarts:
    from toontown.racing import RaceGlobals
    from toontown.racing import RaceManagerAI
    from toontown.racing.DistributedRacePadAI import DistributedRacePadAI
    from toontown.racing.DistributedViewPadAI import DistributedViewPadAI
    from toontown.racing.DistributedStartingBlockAI import DistributedStartingBlockAI
    from toontown.racing.DistributedStartingBlockAI import DistributedViewingBlockAI
    from toontown.racing.DistributedLeaderBoardAI import DistributedLeaderBoardAI
if simbase.wantBingo:
    from toontown.fishing import BingoManagerAI
if simbase.wantPets:
    from toontown.pets import PetManagerAI

import string
import os
import time

from . import DatabaseObject
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator
from .ToontownAIMsgTypes import *
from otp.otpbase.OTPGlobals import *
from toontown.distributed.ToontownDistrictAI import ToontownDistrictAI
#from otp.distributed.DistributedDirectoryAI import DistributedDirectoryAI
from toontown.toon import DistributedToonAI
from otp.distributed import OtpDoGlobals
from toontown.uberdog import DistributedPartyManagerAI
from toontown.uberdog import DistributedInGameNewsMgrAI
from toontown.uberdog import DistributedCpuInfoMgrAI
from toontown.parties import ToontownTimeManager
from toontown.coderedemption.TTCodeRedemptionMgrAI import TTCodeRedemptionMgrAI
from toontown.distributed.NonRepeatableRandomSourceAI import NonRepeatableRandomSourceAI

from . import ToontownGroupManager

if __debug__:
    import pdb
    
class ToontownAIRepository(AIDistrict):
    notify = DirectNotifyGlobal.directNotify.newCategory(
            "ToontownAIRepository")

    # The zone table determines which dnaStores are created and 
    # whether bulding manager or suit planner ai objects are created.
    # The elements consist of:
    # (int the_zone_ID, bool create_building_manager, bool create_suit_planner)
    zoneTable = {
        ToontownCentral: ([ToontownCentral, 1, 0],
                          [ToontownCentral + 100, 1, 1],
                          [ToontownCentral + 200, 1, 1],
                          [ToontownCentral + 300, 1, 1],
                          ),

        DonaldsDock: ([DonaldsDock, 1, 0],
                      [DonaldsDock + 100, 1, 1],
                      [DonaldsDock + 200, 1, 1],
                      [DonaldsDock + 300, 1, 1],
                      ),

        MinniesMelodyland: ([MinniesMelodyland, 1, 0],
                            [MinniesMelodyland + 100, 1, 1],
                            [MinniesMelodyland + 200, 1, 1],
                            [MinniesMelodyland + 300, 1, 1],
                            ),

        TheBrrrgh: ([TheBrrrgh, 1, 0],
                    [TheBrrrgh + 100, 1, 1],
                    [TheBrrrgh + 200, 1, 1],
                    [TheBrrrgh + 300, 1, 1],
                    ),

        DonaldsDreamland: ([DonaldsDreamland, 1, 0],
                           [DonaldsDreamland + 100, 1, 1],
                           [DonaldsDreamland + 200, 1, 1],
                           ),

        DaisyGardens: ([DaisyGardens, 1, 0],
                       [DaisyGardens + 100, 1, 1],
                       [DaisyGardens + 200, 1, 1],
                       [DaisyGardens + 300, 1, 1],
                       ),

        GoofySpeedway: ([GoofySpeedway, 1, 0],
                       ),

        OutdoorZone: ([OutdoorZone, 0, 0],
                       ),        

        SellbotHQ: ([SellbotHQ, 0, 1],
                    [SellbotHQ + 200, 0, 1],
                    ),

        CashbotHQ: ([CashbotHQ, 0, 1],
                    ),

        LawbotHQ: ([LawbotHQ, 0, 1],
                    ),

        GolfZone: ([GolfZone, 0, 0],
                   ),

        BossbotHQ: ([BossbotHQ, 0, 0],                   
                       ),          

        }

    def __init__(self, *args, **kw):
        AIDistrict.__init__(self, *args, **kw)
        self.setTimeWarning(simbase.config.GetFloat('aimsg-time-warning', 4))

        self.dnaSearchPath = DSearchPath()
        if os.getenv('TTMODELS'):
            self.dnaSearchPath.appendDirectory(Filename.expandFrom('$TTMODELS/built/phase_3.5/dna'))
            self.dnaSearchPath.appendDirectory(Filename.expandFrom('$TTMODELS/built/phase_4/dna'))
            self.dnaSearchPath.appendDirectory(Filename.expandFrom('$TTMODELS/built/phase_5/dna'))
            self.dnaSearchPath.appendDirectory(Filename.expandFrom('$TTMODELS/built/phase_5.5/dna'))
            self.dnaSearchPath.appendDirectory(Filename.expandFrom('$TTMODELS/built/phase_6/dna'))
            self.dnaSearchPath.appendDirectory(Filename.expandFrom('$TTMODELS/built/phase_8/dna'))
            self.dnaSearchPath.appendDirectory(Filename.expandFrom('$TTMODELS/built/phase_9/dna'))
            self.dnaSearchPath.appendDirectory(Filename.expandFrom('$TTMODELS/built/phase_10/dna'))
            self.dnaSearchPath.appendDirectory(Filename.expandFrom('$TTMODELS/built/phase_11/dna'))

            # In the publish environment, TTMODELS won't be on the model
            # path by default, so we always add it there.  In the dev
            # environment, it'll be on the model path already, but it
            # doesn't hurt to add it again.
            getModelPath().appendDirectory(Filename.expandFrom("$TTMODELS"))
        else:
            self.dnaSearchPath.appendDirectory(Filename('.'))
            self.dnaSearchPath.appendDirectory(Filename('ttmodels/src/dna'))

        # Initialize our query context.
        self.__queryEstateContext = 0
        self.__queryEstateFuncMap = {}

        # Set a hook so we can process queryToonMaxHp() requests.
        self.accept('queryToonMaxHp', self.__queryToonMaxHpResponse)
                
        # For debugging
        wantNewToonhall = simbase.config.GetBool('want-new-toonhall', 1)
        if (not wantNewToonhall) or \
            (wantNewToonhall and not simbase.config.GetBool('show-scientists', 0)):
                for i in range(3):
                    npcId = 2018+i
                    if npcId in NPCToons.NPCToonDict:
                        del NPCToons.NPCToonDict[npcId]
                    
        NPCToons.generateZone2NpcDict()

        if not simbase.config.GetBool('want-suits-everywhere', 1):
            # This is a special mode for development: we don't want
            # suits walking around all over the world.  Turn off all
            # the SuitPlanner flags.
            for zones in self.zoneTable.values():
                for zone in zones:
                    zone[2] = 0

            if not simbase.config.GetBool('want-suits-nowhere', 1):
                # However, we do want them in at least one street.
                self.zoneTable[ToontownCentral][1][2] = 1

        # minigame debug flags
        self.wantMinigameDifficulty = simbase.config.GetBool(
            'want-minigame-difficulty', 0)

        self.minigameDifficulty = simbase.config.GetFloat(
            'minigame-difficulty', -1.)
        if self.minigameDifficulty == -1.:
            del self.minigameDifficulty
        self.minigameSafezoneId = simbase.config.GetInt(
            'minigame-safezone-id', -1)
        if self.minigameSafezoneId == -1:
            del self.minigameSafezoneId

        # should we pick from the entire list of minigames regardless of
        # the number of participating toons? (for debugging)
        self.useAllMinigames = simbase.config.GetBool('use-all-minigames', 0)

        self.wantCogdominiums = simbase.config.GetBool('want-cogdominiums', 0)

        self.hoods = []
        self.buildingManagers = {}
        self.suitPlanners = {}

        # Guard for publish
        if simbase.wantBingo:
            self.bingoMgr = None

        self.toontownTimeManager = ToontownTimeManager.ToontownTimeManager()
        self.toontownTimeManager.updateLoginTimes(time.time(), time.time(), globalClock.getRealTime())         

        # turn on garbage-collection debugging to see if it's related
        # to the chugs we're seeing
        # eventually we will probably put in our own gc pump
        if simbase.config.GetBool('gc-debug', 0):
            import gc
            gc.set_debug(gc.DEBUG_STATS)
            
        self.deliveryManager = self.generateGlobalObject(
            OtpDoGlobals.OTP_DO_ID_TOONTOWN_DELIVERY_MANAGER,
            "DistributedDeliveryManager")

        self.mailManager = self.generateGlobalObject(
            OtpDoGlobals.OTP_DO_ID_TOONTOWN_MAIL_MANAGER,
            "DistributedMailManager")

        #self.partyManager = self.generateGlobalObject(
        #    OtpDoGlobals.OTP_DO_ID_TOONTOWN_PARTY_MANAGER,
        #    "DistributedPartyManager")               

        #self.codeRedemptionManager = self.generateGlobalObject(
        #    OtpDoGlobals.OTP_DO_ID_TOONTOWN_CODE_REDEMPTION_MANAGER,
        #    "TTCodeRedemptionMgr")               

        #self.randomSourceManager = self.generateGlobalObject(
        #    OtpDoGlobals.OTP_DO_ID_TOONTOWN_NON_REPEATABLE_RANDOM_SOURCE,
        #    "NonRepeatableRandomSource")               

        if simbase.config.GetBool('want-ddsm', 1):
            self.dataStoreManager = self.generateGlobalObject(
                OtpDoGlobals.OTP_DO_ID_TOONTOWN_TEMP_STORE_MANAGER,
                "DistributedDataStoreManager")
                
        self.groupManager = ToontownGroupManager.ToontownGroupManager()
            
    def getGameDoId(self):
        return OTP_DO_ID_TOONTOWN

    def getDatabaseIdForClassName(self, className):
        return DatabaseIdFromClassName.get(
            className, DefaultDatabaseChannelId)

    def _isValidPlayerLocation(self, parentId, zoneId):
        # keep players out of parents that are smaller than N, where N is smaller than all district IDs
        # and N is random enough to be confusing for hackers
        if parentId < 900000:
            return False
        # keep players out of uberzones and zones up to 900 which are not used anyway, to confuse hackers
        if (OTPGlobals.UberZone <= zoneId <= 900):
            return False
        """
        # this doesn't work in the current TT LIVE publish, when teleporting, old district gets
        # setLocation on new district
        if parentId != self.districtId:
            return False
        if zoneId == 2:
            return False
            """
        return True

    def saveBuildings(self):
        """
        Saves the state of all the buildings on all the managed
        streets, so it will be restored on AI restart.
        """
        for mgr in self.buildingManagers.values():
            mgr.save()

    def genDNAFileName(self, zoneId):
        """
        determines the name of the DNA file that should
        be loaded for the neighborhood.
        """
        zoneId = ZoneUtil.getCanonicalZoneId(zoneId)
        hoodId = ZoneUtil.getCanonicalHoodId(zoneId)
        hood = dnaMap[hoodId]
        if hoodId == zoneId:
            zoneId = "sz"

        # Nowadays, we use a search path to find the DNA file, instead
        # of looking for it in only one place.  Not sure if this is a
        # great idea; but it makes it easier to run a test AI on
        # ttown.

        return self.lookupDNAFileName("%s_%s.dna" % (hood, zoneId))

    def lookupDNAFileName(self, filename):
        dnaFile = Filename(filename)
        found = vfs.resolveFilename(dnaFile, self.dnaSearchPath)

        return dnaFile.cStr()
        
##         phase = streetPhaseMap[hoodId]
##         if hoodId==zoneId:
##             zoneId="sz"
##             if hood=='toontown_central':
##                 phase-=1

##         try:
##             # There may be no simbase, if this is client code.
##             if simbase.aiService:
##                 return "./" + hood + "_" + str(zoneId) + ".dna"
##             else:
##                 return "phase_" + str(phase) + "/dna/" + hood + "_" + \
##                        str(zoneId) + ".dna"
##         except:
##             return "phase_" + str(phase) + "/dna/" + hood + "_" + \
##                    str(zoneId) + ".dna"

    def loadDNA(self):
        """
        Return a dictionary of zoneId to DNAStorage objects
        """
        self.dnaStoreMap = {}
        self.dnaDataMap = {}
        for zones in self.zoneTable.values():
            for zone in zones:
                zoneId=zone[0]
                dnaStore = DNAStorage()
                dnaFileName = self.genDNAFileName(zoneId)
                dnaData = self.loadDNAFileAI(dnaStore, dnaFileName)
                self.dnaStoreMap[zoneId] = dnaStore
                self.dnaDataMap[zoneId] = dnaData
            
    
    def createObjects(self):
        # First, load up all of our DNA files for the world.
        self.loadDNA()

        # Create a new district (aka shard) for this AI:
        self.district = ToontownDistrictAI(self, self.districtName)
        self.district.generateOtpObject(
                OTP_DO_ID_TOONTOWN, OTP_ZONE_ID_DISTRICTS,
                doId=self.districtId)

        # The Time manager.  This negotiates a timestamp exchange for
        # the purposes of synchronizing clocks between client and
        # server with a more accurate handshaking protocol than we
        # would otherwise get.
        #
        # We must create this object first, so clients who happen to
        # come into the world while the AI is still coming up
        # (particularly likely if the AI crashed while players were
        # in) will get a chance to synchronize.
        self.timeManager = TimeManagerAI.TimeManagerAI(self)
        self.timeManager.generateOtpObject(
            self.district.getDoId(), OTPGlobals.UberZone)

        self.partyManager = DistributedPartyManagerAI.DistributedPartyManagerAI(self)
        self.partyManager.generateOtpObject(
            self.district.getDoId(), OTPGlobals.UberZone)            
        
        self.inGameNewsMgr = DistributedInGameNewsMgrAI.DistributedInGameNewsMgrAI(self)
        self.inGameNewsMgr.generateOtpObject(
            self.district.getDoId(), OTPGlobals.UberZone)

        self.cpuInfoMgr = DistributedCpuInfoMgrAI.DistributedCpuInfoMgrAI(self)
        self.cpuInfoMgr.generateOtpObject(
            self.district.getDoId(), OTPGlobals.UberZone)     

        if config.GetBool('want-code-redemption', 1):
            self.codeRedemptionManager = TTCodeRedemptionMgrAI(self)
            self.codeRedemptionManager.generateOtpObject(
                self.district.getDoId(), OTPGlobals.UberZone)

        self.randomSourceManager = NonRepeatableRandomSourceAI(self)
        # QuietZone so that the client doesn't get a generate
        self.randomSourceManager.generateOtpObject(
            self.district.getDoId(), OTPGlobals.QuietZone)

        self.welcomeValleyManager = WelcomeValleyManagerAI.WelcomeValleyManagerAI(self)
        self.welcomeValleyManager.generateWithRequired(OTPGlobals.UberZone)

        # The trophy manager should be created before the building
        # managers.
        self.trophyMgr = DistributedTrophyMgrAI.DistributedTrophyMgrAI(self)
        self.trophyMgr.generateWithRequired(OTPGlobals.UberZone)

        # The bank manager handles banking transactions
        self.bankMgr = DistributedBankMgrAI.DistributedBankMgrAI(self)
        self.bankMgr.generateWithRequired(OTPGlobals.UberZone)

        # The Friend Manager
        #self.friendManager = FriendManagerAI.FriendManagerAI(self)
        #self.friendManager.generateWithRequired(OTPGlobals.UberZone)

        # The Delete Manager
        self.deleteManager = DeleteManagerAI.DeleteManagerAI(self)
        self.deleteManager.generateWithRequired(OTPGlobals.UberZone)

        # The Safe Zone manager
        self.safeZoneManager = SafeZoneManagerAI.SafeZoneManagerAI(self)
        self.safeZoneManager.generateWithRequired(OTPGlobals.UberZone)

        # The Magic Word Manager
        magicWordString = simbase.config.GetString('want-magic-words', '1')
        if magicWordString not in ('', '0', '#f'):
            self.magicWordManager = ToontownMagicWordManagerAI.ToontownMagicWordManagerAI(self)
            self.magicWordManager.generateWithRequired(OTPGlobals.UberZone)
            
        # The Tutorial manager
        self.tutorialManager = TutorialManagerAI.TutorialManagerAI(self)
        self.tutorialManager.generateWithRequired(OTPGlobals.UberZone)

        # The Catalog Manager
        self.catalogManager = CatalogManagerAI.CatalogManagerAI(self)
        self.catalogManager.generateWithRequired(OTPGlobals.UberZone)

        # The Quest manager
        self.questManager = QuestManagerAI.QuestManagerAI(self)

        # The Fish manager
        self.fishManager = FishManagerAI.FishManagerAI(self)

        # The Cog Page manager
        self.cogPageManager = CogPageManagerAI.CogPageManagerAI(self)

        # The Suit Invasion Manager
        self.suitInvasionManager = SuitInvasionManagerAI.SuitInvasionManagerAI(self)

        # The Firework Manager: This object really only exists so we can
        # fire off fireworks with magic words. Normally this is a holiday
        # manager driven event and therefore the constructor needs a
        # holidayId. Pass in fourth of july as default.  To do: override 
        # holiday ID with a magic word
        self.fireworkManager = FireworkManagerAI.FireworkManagerAI(
            self, NEWYEARS_FIREWORKS)
            
        # Create an NPC Dialogue manager that manages conversations
        # amongst a set of NPC's
        self.dialogueManager = NPCDialogueManagerAI.NPCDialogueManagerAI()
        
        # The News manager
        self.newsManager = NewsManagerAI.NewsManagerAI(self)
        self.newsManager.generateWithRequired(OTPGlobals.UberZone)

        # The Factory Manager
        self.factoryMgr = FactoryManagerAI.FactoryManagerAI(self)
        
        # The Mint Manager
        self.mintMgr = MintManagerAI.MintManagerAI(self)
        
        #the Law Office Manager
        self.lawMgr = LawOfficeManagerAI.LawOfficeManagerAI(self)

        # The Cog Country Club Manager
        self.countryClubMgr = CountryClubManagerAI.CountryClubManagerAI(self)        

        if simbase.wantKarts:
            # The Race Manager
            self.raceMgr = RaceManagerAI.RaceManagerAI(self)
        
        self.cogSuitMgr = CogSuitManagerAI.CogSuitManagerAI(self)
        self.promotionMgr = PromotionManagerAI.PromotionManagerAI(self)

        # Housing
        self.estateMgr = EstateManagerAI.EstateManagerAI(self)
        self.estateMgr.generateWithRequired(OTPGlobals.UberZone)

        if simbase.wantPets:
            # Pets -- must be created after estateMgr
            self.petMgr = PetManagerAI.PetManagerAI(self)

        # Now create the neighborhood-specific objects.
        self.startupHood(TTHoodDataAI.TTHoodDataAI(self))
        self.startupHood(DDHoodDataAI.DDHoodDataAI(self))
        self.startupHood(MMHoodDataAI.MMHoodDataAI(self))
        self.startupHood(DGHoodDataAI.DGHoodDataAI(self))
        self.startupHood(BRHoodDataAI.BRHoodDataAI(self))
        self.startupHood(DLHoodDataAI.DLHoodDataAI(self))
        self.startupHood(CSHoodDataAI.CSHoodDataAI(self))
        self.startupHood(GSHoodDataAI.GSHoodDataAI(self))
        self.startupHood(OZHoodDataAI.OZHoodDataAI(self))
        self.startupHood(GZHoodDataAI.GZHoodDataAI(self))                
        self.startupHood(CashbotHQDataAI.CashbotHQDataAI(self))
        self.startupHood(LawbotHQDataAI.LawbotHQDataAI(self))
        self.startupHood(BossbotHQDataAI.BossbotHQDataAI(self))        

        # The Holiday Manager should be instantiated after the each
        # of the hoods and estateMgrAI are generated because Bingo Night
        # needs to reference the HoodDataAI and EstateMgrAI for pond
        # information. (JJT - 7/22/04)
        self.holidayManager = HolidayManagerAI.HolidayManagerAI(self)

        self.banManager = BanManagerAI.BanManagerAI()

        # Now that we've created all the suit planners, any one of
        # them can be used to fill the world with requests for suit
        # buildings.
        if self.suitPlanners:
            list(self.suitPlanners.values())[0].assignInitialSuitBuildings()
            
        # mark district as avaliable
        self.district.b_setAvailable(1)

        # Now that everything's created, start checking the leader
        # boards for correctness.  We only need to check every 30
        # seconds or so.
        self.__leaderboardFlush(None)
        taskMgr.doMethodLater(30, self.__leaderboardFlush,
                              'leaderboardFlush', appendTask = True)

    def __leaderboardFlush(self, task):
        messenger.send('leaderboardFlush')
        return Task.again
            
    def getWelcomeValleyCount(self):
        # avatars in Welcom Vally
        return self.welcomeValleyManager.getAvatarCount();        
            
    def getHandleClassNames(self):
        # This function should return a tuple or list of string names
        # that represent distributed object classes for which we want
        # to make a special 'handle' class available.
        return ('DistributedToon',)

    def deleteObjects(self):
        # This function is where objects that manage DistributedObjectAI's
        # should be cleaned up. Since this is only called during a district
        # shutdown of some kind, it is not useful to delete the existing
        # DistributedObjectAI's, but rather to just make sure that they
        # are no longer referenced, and no new ones are created.
        for hood in self.hoods:
            hood.shutdown()
        self.hoods = []

        taskMgr.remove('leaderboardFlush')
        
    def queryToonMaxHp(self, toonId, callback, *args):
        """
        Looks up the maxHp of the given toon, and calls the given
        callback function, passing the maxHp as a parameter (or None
        if the toonId is unknown) followed by the given extra args.
        If the toon happens to be online and on the same shard, the
        callback is made immediately; otherwise, it will be made at
        some point in the future, after we have heard back from the
        database.
        """
        toon = self.doId2do.get(toonId, None)
        if toon != None:
            # The toon is online and on this shard.
            callback(toon.getMaxHp(), *args)
        else:
            # The toon is offline or on another shard; we have to
            # query the database.
            db = DatabaseObject.DatabaseObject(self, toonId)
            db.doneEvent = 'queryToonMaxHp'
            db.userCallback = callback
            db.userArgs = args
            db.getFields(['setMaxHp'])

    def __queryToonMaxHpResponse(self, db, retCode):
        maxHpDatagram = db.values.get('setMaxHp', None)
        if retCode == 0 and maxHpDatagram != None:
            di = PyDatagramIterator(maxHpDatagram)
            maxHp = di.getInt16()
        else:
            # The toonId is unknown or not a toon.
            maxHp = None

        db.userCallback(maxHp, *db.userArgs)


    def getMinDynamicZone(self):
        # Override this to return the minimum allowable value for a
        # dynamically-allocated zone id.
        return DynamicZonesBegin

    def getMaxDynamicZone(self):
        # Override this to return the maximum allowable value for a
        # dynamically-allocated zone id.

        # Note that each zone requires the use of the channel derived
        # by self.districtId + zoneId.  Thus, we cannot have any zones
        # greater than or equal to self.minChannel - self.districtId,
        # which is our first allocated doId.
        return min(self.minChannel - self.districtId, DynamicZonesEnd) - 1

    def findPartyHats(self, dnaGroup, zoneId, overrideDNAZone = 0):
        """
        Recursively scans the given DNA tree for party hats.  These
        are defined as all the groups whose code includes the string
        "party_gate".  For each such group, creates a
        DistributedPartyGateAI.  Returns the list of distributed
        objects.
        """
        partyHats = []

        if ((isinstance(dnaGroup, DNAGroup)) and
            # If it is a DNAGroup, and the name has party_gate, count it
            (string.find(dnaGroup.getName(), 'party_gate') >= 0)):
            # Here's a party hat!
            ph = DistributedPartyGateAI.DistributedPartyGateAI(self)
            ph.generateWithRequired(zoneId)
            partyHats.append(ph)
        else:
            # Now look in the children
            # Party hats cannot have other party hats in them,
            # so do not search the one we just found:
            # If we come across a visgroup, note the zoneId and then recurse
            if (isinstance(dnaGroup, DNAVisGroup) and not overrideDNAZone):
                # Make sure we get the real zone id, in case we are in welcome valley
                zoneId = ZoneUtil.getTrueZoneId(
                        int(dnaGroup.getName().split(':')[0]), zoneId)
            for i in range(dnaGroup.getNumChildren()):
                childPartyHats = self.findPartyHats(dnaGroup.at(i), zoneId, overrideDNAZone)
                partyHats += childPartyHats
                
        return partyHats

    def findFishingPonds(self, dnaGroup, zoneId, area, overrideDNAZone = 0):
        """
        Recursively scans the given DNA tree for fishing ponds.  These
        are defined as all the groups whose code includes the string
        "fishing_pond".  For each such group, creates a
        DistributedFishingPondAI.  Returns the list of distributed
        objects and a list of the DNAGroups so we can search them for
        spots and targets.
        """
        fishingPonds = []
        fishingPondGroups = []

        if ((isinstance(dnaGroup, DNAGroup)) and
            # If it is a DNAGroup, and the name starts with fishing_pond, count it
            (string.find(dnaGroup.getName(), 'fishing_pond') >= 0)):
            # Here's a fishing pond!
            fishingPondGroups.append(dnaGroup)
            fp = DistributedFishingPondAI.DistributedFishingPondAI(self, area)
            fp.generateWithRequired(zoneId)
            fishingPonds.append(fp)
        else:
            # Now look in the children
            # Fishing ponds cannot have other ponds in them,
            # so do not search the one we just found:
            # If we come across a visgroup, note the zoneId and then recurse
            if (isinstance(dnaGroup, DNAVisGroup) and not overrideDNAZone):
                # Make sure we get the real zone id, in case we are in welcome valley
                zoneId = ZoneUtil.getTrueZoneId(
                        int(dnaGroup.getName().split(':')[0]), zoneId)
            for i in range(dnaGroup.getNumChildren()):
                childFishingPonds, childFishingPondGroups = self.findFishingPonds(
                        dnaGroup.at(i), zoneId, area, overrideDNAZone)
                fishingPonds += childFishingPonds
                fishingPondGroups += childFishingPondGroups
        return fishingPonds, fishingPondGroups
            
    def findFishingSpots(self, dnaPondGroup, distPond):
        """
        Scans the given DNAGroup pond for fishing spots.  These
        are defined as all the props whose code includes the string
        "fishing_spot".  Fishing spots should be the only thing under a pond
        node. For each such prop, creates a DistributedFishingSpotAI.
        Returns the list of distributed objects created.
        """
        fishingSpots = []
        # Search the children of the pond
        for i in range(dnaPondGroup.getNumChildren()):
            dnaGroup = dnaPondGroup.at(i)
            if ((isinstance(dnaGroup, DNAProp)) and 
                (string.find(dnaGroup.getCode(), 'fishing_spot') >= 0)):
                # Here's a fishing spot!
                pos = dnaGroup.getPos()
                hpr = dnaGroup.getHpr()
                fs = DistributedFishingSpotAI.DistributedFishingSpotAI(
                     self, distPond, pos[0], pos[1], pos[2], hpr[0], hpr[1], hpr[2])
                fs.generateWithRequired(distPond.zoneId)
                fishingSpots.append(fs)
            else:
                self.notify.debug("Found dnaGroup that is not a fishing_spot under a pond group")
        return fishingSpots

    def findRacingPads(self, dnaGroup, zoneId, area, overrideDNAZone = 0, type = 'racing_pad'):
        racingPads = []
        racingPadGroups = []
        if ((isinstance(dnaGroup, DNAGroup)) and (string.find(dnaGroup.getName(), type) >= 0)):
            racingPadGroups.append(dnaGroup)
            if (type == 'racing_pad'):
                nameInfo = dnaGroup.getName().split('_')
                #pdb.set_trace()
                #print("Name Info: ", nameInfo)
                #print("Race Info: ", raceInfo)
                racingPad = DistributedRacePadAI(self, area, nameInfo[3], int(nameInfo[2]))
            else:
                racingPad = DistributedViewPadAI(self, area)
            racingPad.generateWithRequired(zoneId)
            racingPads.append(racingPad)
        else:
            if (isinstance(dnaGroup, DNAVisGroup) and not overrideDNAZone):
                zoneId = ZoneUtil.getTrueZoneId(int(dnaGroup.getName().split(':')[0]), zoneId)
            for i in range(dnaGroup.getNumChildren()):
                childRacingPads, childRacingPadGroups = self.findRacingPads(dnaGroup.at(i), zoneId, area, overrideDNAZone, type)
                racingPads += childRacingPads
                racingPadGroups += childRacingPadGroups
        return racingPads, racingPadGroups

    def getRacingPadList(self):
        list = []
        for do in self.doId2do.values():
            if (isinstance(do, DistributedRacePadAI)):
                list.append(do.doId)
        return list

    def getViewPadList(self):
        list = []
        for do in self.doId2do.values():
            if (isinstance(do, DistributedViewPadAI)):
                list.append(do.doId)
        return list

    def getStartingBlockDict(self):
        dict = {}
        for do in self.doId2do.values():
            if (isinstance(do, DistributedStartingBlockAI)):
                if (isinstance(do.kartPad, DistributedRacePadAI)):
                    # Add the do to the dict
                    if (dict.has_key(do.kartPad.doId)):
                        dict[do.kartPad.doId].append(do.doId)
                    else:
                        dict[do.kartPad.doId] = [do.doId]
        return dict

    def getViewingBlockDict(self):
        dict = {}
        for do in self.doId2do.values():
            if (isinstance(do, DistributedStartingBlockAI)):
                if (isinstance(do.kartPad, DistributedViewPadAI)):
                    # Add the do to the dict
                    if (dict.has_key(do.kartPad.doId)):
                        dict[do.kartPad.doId].append(do.doId)
                    else:
                        dict[do.kartPad.doId] = [do.doId]
        return dict

    def findStartingBlocks(self, dnaRacingPadGroup, distRacePad):
        """
        Comment goes here...
        """
        startingBlocks = []
        # Search the children of the racing pad
        for i in range(dnaRacingPadGroup.getNumChildren()):
            dnaGroup = dnaRacingPadGroup.at(i)

            # TODO - check if DNAProp instance
            if ((string.find(dnaGroup.getName(), 'starting_block') >= 0)):
                padLocation = dnaGroup.getName().split('_')[2]
                pos = dnaGroup.getPos()
                hpr = dnaGroup.getHpr()

                if (isinstance(distRacePad, DistributedRacePadAI)):
                    sb = DistributedStartingBlockAI(self, distRacePad, pos[0], pos[1], pos[2], hpr[0], hpr[1], hpr[2], int(padLocation))
                else:
                    sb = DistributedViewingBlockAI(self, distRacePad, pos[0], pos[1], pos[2], hpr[0], hpr[1], hpr[2], int(padLocation))
                sb.generateWithRequired(distRacePad.zoneId)
                startingBlocks.append(sb)
            else:
                self.notify.debug("Found dnaGroup that is not a starting_block under a race pad group")
        return startingBlocks
        
    def findLeaderBoards(self, dnaPool, zoneID):
        '''
        Find and return leader boards
        '''
        leaderBoards = []
        if (string.find(dnaPool.getName(), 'leaderBoard') >= 0):
            #found a leader board
            pos = dnaPool.getPos()
            hpr = dnaPool.getHpr()
                
            lb = DistributedLeaderBoardAI(self, dnaPool.getName(), zoneID, [], pos, hpr)
            lb.generateWithRequired(zoneID)
            leaderBoards.append(lb)
        else: 
            for i in range(dnaPool.getNumChildren()):
                result = self.findLeaderBoards(dnaPool.at(i), zoneID)
                if result:
                    leaderBoards += result
                    
        return leaderBoards
                                                               
    def loadDNAFileAI(self, dnaStore, dnaFile):
        return loadDNAFileAI(dnaStore, dnaFile, CSDefault)

    #AIGEOM
    def loadDNAFile(self, dnaStore, dnaFile, cs=CSDefault):
        """
        load everything, including geometry
        """
        return loadDNAFile(dnaStore, dnaFile, cs)

    def startupHood(self, hoodDataAI):
        hoodDataAI.startup()
        self.hoods.append(hoodDataAI)

    def shutdownHood(self, hoodDataAI):
        hoodDataAI.shutdown()
        self.hoods.remove(hoodDataAI)


    def getEstate(self, avId, zone, callback):
        """
        Asks the database to fill in details about this avatars
        estate.

        We make a request to the server and wait for its response.
        """
        context = self.__queryEstateContext
        self.__queryEstateContext += 1
        self.__queryEstateFuncMap[context] = callback
        self.__sendGetEstate(avId, context)
        
    def __sendGetEstate(self, avId, context):
        """
        Sends the query-object message to the server.  The return
        message will be handled by __handleGetEstateResp().
        See getEstate().
        """
        datagram = PyDatagram()
        datagram.addServerHeader(
            DBSERVER_ID, self.ourChannel, DBSERVER_GET_ESTATE)
        datagram.addUint32(context)
        # The avId we are querying.
        datagram.addUint32(avId)
        self.send(datagram)

    def __handleGetEstateResp(self, di):
        # Use the context to retrieve the callback parameter passed in
        # to getEstate().
        context = di.getUint32()
        callback = self.__queryEstateFuncMap.get(context)
        if callback == None:
            self.notify.warning("Got unexpected estate context: %s" % (context))
            return
        del self.__queryEstateFuncMap[context]

        # return code = 0 if estate was returned without problems
        retCode = di.getUint8()

        estateVal = {}
        if (retCode == 0):
            estateId = di.getUint32()
            numFields = di.getUint16()
            
            for i in range(numFields):
                key = di.getString()
                #key = key[2:]
                #right why to do this???? ask Roger and/or Dave
                value = di.getString()
                found = di.getUint8()
                
                #print(key);
                #print(value);
                #print(found);

                if found:
                    # create another datagram for this value
                    #vdg = PyDatagram(estateVal[i])
                    #vdgi = PyDatagramIterator(vdg)
                    # do something with this data
                    estateVal[key] = value
                
                    
            numHouses = di.getUint16()
            self.notify.debug("numHouses = %s" % numHouses)
            houseId = [None] * numHouses
            for i in range(numHouses):
                houseId[i] = di.getUint32()
                self.notify.debug("houseId = %s" % houseId[i])
                
            numHouseKeys = di.getUint16()
            self.notify.debug("numHouseKeys = %s" % numHouseKeys)
            houseKey = [None] * numHouseKeys
            for i in range(numHouseKeys):
                houseKey[i] = di.getString()

            numHouseVal = di.getUint16()
            assert (numHouseVal == numHouseKeys)
            tempHouseVal = [None] * numHouseVal
            for i in range(numHouseVal):
                numHouses2 = di.getUint16()
                assert(numHouses2 == numHouses)
                tempHouseVal[i] = [None] * numHouses
                for j in range(numHouses):
                    tempHouseVal[i][j] = di.getString()
                    # do we need a check for "value found" here?

            #print(houseKey)
            #print(tempHouseVal)

            numHouseFound = di.getUint16()


            # keep track of which attributes are found
            foundVal = [None] * numHouses
            for i in range(numHouses):
                foundVal[i] = [None] * numHouseVal
                
            # create empty dictionaries for each house
            houseVal = []
            for i in range(numHouses):
                houseVal.append({})
                
            for i in range(numHouseVal):
                hvLen = di.getUint16()
                for j in range(numHouses):
                    found = di.getUint8()
                    if found:
                        houseVal[j][houseKey[i]] = tempHouseVal[i][j]
                        foundVal[j][i] = 1
                    else:
                        foundVal[j][i] = 0

            numPets = di.getUint16()
            petIds = []
            for i in xrange(numPets):
                petIds.append(di.getUint32())

            # create estate with houses
            # and call DistributedEstateAI's initEstateData func

            # call function originally passed to getEstate
            callback(estateId, estateVal, numHouses, houseId, houseVal,
                     petIds, estateVal)
        else:
            print("ret code != 0, something went wrong with estate creation")

    def getFirstBattle(self):
        # Return the first battle in the repository (for testing purposes)
        from toontown.battle import DistributedBattleBaseAI
        for dobj in self.doId2do.values():
            if isinstance(
                    dobj, DistributedBattleBaseAI.DistributedBattleBaseAI):
                return dobj

    def handlePlayGame(self, msgType, di):
        # Handle Toontown specific message types before
        # calling the base class
        if msgType == DBSERVER_GET_ESTATE_RESP:
            self.__handleGetEstateResp(di)
        elif msgType == PARTY_MANAGER_UD_TO_ALL_AI:
            self.__handlePartyManagerUdToAllAi(di)
        elif msgType == IN_GAME_NEWS_MANAGER_UD_TO_ALL_AI:
            self.__handleInGameNewsManagerUdToAllAi(di)
        else:
            AIDistrict.handlePlayGame(self, msgType, di)

    def handleAvCatch(self, avId, zoneId, catch):
        """
        avId - ID of avatar to update
        zoneId - zoneId of the pond the catch was made in.
                This is used by the BingoManagerAI to
                determine which PBMgrAI needs to update
                the catch.
        catch - a fish tuple of (genus, species)
        returns: None
        
        This method instructs the BingoManagerAI to
        tell the appropriate PBMgrAI to update the
        catch of an avatar at the particular pond. This
        method is called in the FishManagerAI's
        RecordCatch method.
        """
        # Guard for publish
        if simbase.wantBingo:
            if self.bingoMgr:
                self.bingoMgr.setAvCatchForPondMgr(avId, zoneId, catch)

    def createPondBingoMgrAI(self, estate):
        """
        estate - the estate for which the PBMgrAI should
                be created.
        returns: None
        
        This method instructs the BingoManagerAI to
        create a new PBMgrAI for a newly generated
        estate.
        """
        # Guard for publish
        if simbase.wantBingo:
            if self.bingoMgr:
                self.notify.info('createPondBingoMgrAI: Creating a DPBMAI for Dynamic Estate')
                self.bingoMgr.createPondBingoMgrAI(estate, 1)

    def __handlePartyManagerUdToAllAi(self,di):
        """Send all msgs of this type to the party manager on our district."""
        # we know the format is STATE_SERVER_OBJECT_UPDATE_FIELD
        # we just changed the msg type to PARTY_MANAGER_UD_TO_ALL_AI
        # so that it gets handled here
        # otherwise it just gets dropped on the floor
        do = self.partyManager
        if do:
            globalId = di.getUint32()
            if globalId != OtpDoGlobals.OTP_DO_ID_TOONTOWN_PARTY_MANAGER:
                self.notify.error('__handlePartyManagerUdToAllAi globalId=%d not equal to %d' %
                                  (globalId, OtpDoGlobals.OTP_DO_ID_TOONTOWN_PARTY_MANAGER))
            # Let the dclass finish the job
            do.dclass.receiveUpdate(do, di)

    def __handleInGameNewsManagerUdToAllAi(self,di):
        """Send all msgs of this type to the party manager on our district."""
        # we know the format is STATE_SERVER_OBJECT_UPDATE_FIELD
        # we just changed the msg type to PARTY_MANAGER_UD_TO_ALL_AI
        # so that it gets handled here
        # otherwise it just gets dropped on the floor
        do = self.inGameNewsMgr
        if do:
            globalId = di.getUint32()
            if globalId != OtpDoGlobals.OTP_DO_ID_TOONTOWN_IN_GAME_NEWS_MANAGER:
                self.notify.error('__handleInGameNewsManagerUdToAllAi  globalId=%d not equal to %d' %
                                  (globalId, OtpDoGlobals.OTP_DO_ID_TOONTOWN_PARTY_MANAGER))
            # Let the dclass finish the job
            do.dclass.receiveUpdate(do, di)
