"""
The Toontown Uber Distributed Object Globals server.
"""

from pandac.PandaModules import *
import time
if __debug__:
    from direct.showbase.PythonUtil import *

from direct.directnotify.DirectNotifyGlobal import directNotify

from otp.distributed import OtpDoGlobals
from otp.ai.AIMsgTypes import *
from otp.ai import TimeManagerAI
from otp.uberdog.UberDog import UberDog

from otp.friends.AvatarFriendsManagerUD import AvatarFriendsManagerUD
from toontown.uberdog.DistributedDeliveryManagerUD import DistributedDeliveryManagerUD
from toontown.uberdog.DistributedMailManagerUD import DistributedMailManagerUD
from toontown.parties import ToontownTimeManager
from toontown.rpc.RATManagerUD import RATManagerUD
from toontown.rpc.AwardManagerUD import AwardManagerUD
from toontown.uberdog import TTSpeedchatRelayUD
from toontown.uberdog import DistributedInGameNewsMgrUD
from toontown.uberdog import DistributedCpuInfoMgrUD
    
from otp.uberdog.RejectCode import RejectCode

class ToontownUberDog(UberDog):
    notify = directNotify.newCategory("UberDog")

    def __init__(
            self, mdip, mdport, esip, esport, dcFilenames,
            serverId, minChannel, maxChannel):
        assert self.notify.debugStateCall(self)
        # TODO: The UD needs to know server time, but perhaps this isn't
        # the place to do this? -SG-SLWP
        self.toontownTimeManager = ToontownTimeManager.ToontownTimeManager()
        self.toontownTimeManager.updateLoginTimes(time.time(), time.time(), globalClock.getRealTime())         

        def isManagerFor(name):
            return len(uber.objectNames) == 0 or name in uber.objectNames
        self.isFriendsManager = False # latest from Ian this should not run anymore
        #self.isFriendsManager = isManagerFor('friends')
        self.isSpeedchatRelay = isManagerFor('speedchatRelay')
        self.isGiftingManager = isManagerFor('gifting')
        self.isMailManager = False # isManagerFor('mail')
        self.isPartyManager = isManagerFor('party')
        self.isRATManager = False # isManagerFor('RAT')
        self.isAwardManager = isManagerFor('award')
        self.isCodeRedemptionManager = isManagerFor('coderedemption')
        self.isInGameNewsMgr = isManagerFor('ingamenews')
        self.isCpuInfoMgr = isManagerFor('cpuinfo')
        self.isRandomSourceManager = False # isManagerFor('randomsource')

        UberDog.__init__(
            self, mdip, mdport, esip, esport, dcFilenames,
            serverId, minChannel, maxChannel)

    def createObjects(self):
        UberDog.createObjects(self)
        # Ask for the ObjectServer so we can check the dc hash value 
        self.queryObjectAll(self.serverId)

        if self.isFriendsManager:
            self.playerFriendsManager = self.generateGlobalObject(
                OtpDoGlobals.OTP_DO_ID_PLAYER_FRIENDS_MANAGER,
                "TTPlayerFriendsManager")
                
        if self.isSpeedchatRelay:
            self.speedchatRelay = self.generateGlobalObject(
                OtpDoGlobals.OTP_DO_ID_TOONTOWN_SPEEDCHAT_RELAY,
                "TTSpeedchatRelay")

        if self.isGiftingManager:
            self.deliveryManager = self.generateGlobalObject(
                OtpDoGlobals.OTP_DO_ID_TOONTOWN_DELIVERY_MANAGER,
                "DistributedDeliveryManager")
            
        if self.isMailManager:
            self.mailManager = self.generateGlobalObject(
                OtpDoGlobals.OTP_DO_ID_TOONTOWN_MAIL_MANAGER,
                "DistributedMailManager")

        if self.isPartyManager:
            self.partyManager = self.generateGlobalObject(
                OtpDoGlobals.OTP_DO_ID_TOONTOWN_PARTY_MANAGER,
                "DistributedPartyManager")              

        if simbase.config.GetBool('want-ddsm', 1):
            self.dataStoreManager = self.generateGlobalObject(
                OtpDoGlobals.OTP_DO_ID_TOONTOWN_TEMP_STORE_MANAGER,
                "DistributedDataStoreManager")

        if self.isRATManager:
            self.RATManager = self.generateGlobalObject(
                OtpDoGlobals.OTP_DO_ID_TOONTOWN_RAT_MANAGER,
                "RATManager")

        if self.isAwardManager:
            self.awardManager = self.generateGlobalObject(
                OtpDoGlobals.OTP_DO_ID_TOONTOWN_AWARD_MANAGER,
                "AwardManager")

        if config.GetBool('want-code-redemption', 1):
            if self.isCodeRedemptionManager:
                self.codeRedemptionManager = self.generateGlobalObject(
                    OtpDoGlobals.OTP_DO_ID_TOONTOWN_CODE_REDEMPTION_MANAGER,
                    "TTCodeRedemptionMgr")

        if self.isInGameNewsMgr:
            self.inGameNewsMgr = self.generateGlobalObject(
                OtpDoGlobals.OTP_DO_ID_TOONTOWN_IN_GAME_NEWS_MANAGER,
                "DistributedInGameNewsMgr")
        
        if self.isCpuInfoMgr:
            self.cpuInfoMgr = self.generateGlobalObject(
                OtpDoGlobals.OTP_DO_ID_TOONTOWN_CPU_INFO_MANAGER,
                "DistributedCpuInfoMgr")              
        
        if self.isRandomSourceManager:
            self.randomSourceManager = self.generateGlobalObject(
                OtpDoGlobals.OTP_DO_ID_TOONTOWN_NON_REPEATABLE_RANDOM_SOURCE,
                "NonRepeatableRandomSource")

    def getDatabaseIdForClassName(self, className):
        return DatabaseIdFromClassName.get(
            className, DefaultDatabaseChannelId)
    
    if __debug__:
        def status(self):
            if self.isGiftingManager:
                print("deliveryManager is", self.deliveryManager)
            if self.isFriendsManager:
                print("playerFriendsManager is ",self.playerFriendsManager)
            
