from toontown.estate import DistributedStatuaryAI
from direct.directnotify import DirectNotifyGlobal
from otp.ai.AIBase import *
from . import GardenGlobals

class DistributedToonStatuaryAI(DistributedStatuaryAI.DistributedStatuaryAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedToonStatuaryAI')
    
    def __init__(self, typeIndex = 205, waterLevel = 0, growthLevel = 0, optional = None, ownerIndex = 0, plot = 0):
        DistributedStatuaryAI.DistributedStatuaryAI.__init__(self, typeIndex, waterLevel, growthLevel, optional, ownerIndex, plot)
        self.notify.debug('constructing DistributedToonStatuaryAI')
        simbase.ts = self
        
    def setOptional(self, optional):
        self.optional = optional

    def getOptional(self):
        return self.optional