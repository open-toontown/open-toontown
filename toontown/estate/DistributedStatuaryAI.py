from otp.ai.AIBase import *
from . import DistributedLawnDecorAI
from direct.directnotify import DirectNotifyGlobal
from . import GardenGlobals

class DistributedStatuaryAI(DistributedLawnDecorAI.DistributedLawnDecorAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedStatuaryAI')
    
    
    def __init__(self, typeIndex = 201, waterLevel = 0, growthLevel = 0, optional = None, ownerIndex = 0, plot = 0):
        DistributedLawnDecorAI.DistributedLawnDecorAI.__init__(self, simbase.air, ownerIndex, plot)
        self.typeIndex = typeIndex
        self.waterLevel = waterLevel
        self.growthLevel = growthLevel
        self.optional = optional
        self.name = GardenGlobals.PlantAttributes[typeIndex]['name']
        self.plantType = GardenGlobals.PlantAttributes[typeIndex]['plantType']
        self.modelPath = GardenGlobals.PlantAttributes[typeIndex]['model']

        #testStatue = DistributedToonStatuaryAI.DistributedToonStatuaryAI()
        #testStatue.copyToon()
        #testStatue.removeTextures()
        
    def setTypeIndex(self, typeIndex):
        self.typeIndex = typeIndex
        
    def getTypeIndex(self):
        return self.typeIndex
        
    def setWaterLevel(self, waterLevel):
        self.waterLevel = waterLevel
        
    def getWaterLevel(self):
        return self.waterLevel
        
    def setGrowthLevel(self, growthLevel):
        self.growthLevel = growthLevel
        
    def getGrowthLevel(self):
        return self.growthLevel
