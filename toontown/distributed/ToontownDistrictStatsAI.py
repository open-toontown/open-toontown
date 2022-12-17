from direct.distributed import DistributedObjectAI
from direct.directnotify import DirectNotifyGlobal
from direct.task import Task

from otp.distributed.OtpDoGlobals import *


class ToontownDistrictStatsAI(DistributedObjectAI.DistributedObjectAI):
    """
    See Also: "toontown/src/distributed/DistributedDistrictAi.py"
    """
    notify = DirectNotifyGlobal.directNotify.newCategory("ToontownDistrictStatsAI")
    
    defaultParent = OTP_DO_ID_TOONTOWN
    defaultZone =  OTP_ZONE_ID_DISTRICTS_STATS
            
                
    
    def __init__(self, air):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.updateFreq = 5
        self.toontownDistrictId = 0
        
    def gettoontownDistrictId(self):
        return self.toontownDistrictId        
        
    def generate(self):        
        DistributedObjectAI.DistributedObjectAI.generate(self)
        self.pushDistrictStats(firstTime=True)


    def delete(self):
        taskMgr.remove("DistributedToonDistrictAIStatsUpdate")
        DistributedObjectAI.DistributedObjectAI.delete(self)        
    
    # set avatar count
    def setAvatarCount(self, avatarCount):
        pass
    
    def d_setAvatarCount(self, avatarCount):
         self.sendUpdate("setAvatarCount", [avatarCount])
    
    def b_setAvatarCount(self, avatarCount):
         self.setAvatarCount(avatarCount)
         self.d_setAvatarCount(avatarCount)

    def getAvatarCount(self):
        return 0
         
    ##   avatars in bewbe zone...     
    def setNewAvatarCount(self, newAvatarCount):
        pass

    def d_setNewAvatarCount(self, newAvatarCount):
         self.sendUpdate("setAvatarCount", [newAvatarCount])
        
    def b_setNewAvatarCount(self, newAvatarCount):
        self.setNewAvatarCount(newAvatarCount)
        self.d_setNewAvatarCount(newAvatarCount)

    def getNewAvatarCount(self):
        return 0

    ## stat fields...

    def setStats(self, avatarCount,  newAvatarCount):
         self.setAvatarCount(avatarCount)
         self.setNewAvatarCount(newAvatarCount)

    def d_setStats(self, avatarCount,  newAvatarCount):
         self.sendUpdate("setStats", [avatarCount, newAvatarCount])

    def b_setStats(self, avatarCount,  newAvatarCount):
        self.setStats(avatarCount,  newAvatarCount)
        self.d_setStats(avatarCount,  newAvatarCount)
        
        
    def pushDistrictStats(self, task=None, firstTime=False):
        if self.isDeleted():
            return
        # the first time we're called, the AIR doesn't have a welcomeValleyManager yet
        if firstTime:
            wvCount = 0
        else:
            wvCount = self.air.getWelcomeValleyCount()
        avatar_count = self.air.getPopulation()
        self.b_setStats(avatar_count, wvCount)
        taskMgr.doMethodLater(self.updateFreq, self.pushDistrictStats, "DistributedDistrictUpdate")
        self.air.writeServerStatus("", avatar_count, len(self.air.doId2do))
