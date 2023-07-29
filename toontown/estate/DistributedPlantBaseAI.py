from otp.ai.AIBase import *
from . import DistributedLawnDecorAI
from direct.directnotify import DirectNotifyGlobal
from . import GardenGlobals

from direct.showbase.ShowBase import *

class DistributedPlantBaseAI(DistributedLawnDecorAI.DistributedLawnDecorAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPlantBaseAI')
    
    
    def __init__(self, typeIndex = 0, waterLevel = 0, growthLevel = 0, optional = None, ownerIndex = 0, plot = 0):
        DistributedLawnDecorAI.DistributedLawnDecorAI.__init__(self, simbase.air, ownerIndex, plot)
        self.typeIndex = typeIndex
        self.waterLevel = waterLevel
        self.growthLevel = growthLevel
        self.optional = optional
        self.name = GardenGlobals.PlantAttributes[typeIndex]['name']
        self.plantType = GardenGlobals.PlantAttributes[typeIndex]['plantType']
        self.growthThresholds = GardenGlobals.PlantAttributes[typeIndex]['growthThresholds']
        self.maxWaterLevel = GardenGlobals.PlantAttributes[typeIndex]['maxWaterLevel']
        self.minWaterLevel = GardenGlobals.PlantAttributes[typeIndex]['minWaterLevel']
        self.seedlingModel = GardenGlobals.PlantAttributes[typeIndex]['seedlingModel']
        self.establishedModel = GardenGlobals.PlantAttributes[typeIndex]['establishedModel']
        self.fullGrownModel = GardenGlobals.PlantAttributes[typeIndex]['fullGrownModel']
        
    def setTypeIndex(self, typeIndex):
        self.typeIndex = typeIndex
        
    def getTypeIndex(self):
        return self.typeIndex
        
    def setWaterLevel(self, waterLevel, finalize):
        self.waterLevel = waterLevel
        self.updateEstate(waterLevel=waterLevel, finalize=finalize)

    def d_setWaterLevel(self,waterLevel):
        self.sendUpdate('setWaterLevel' , [waterLevel])
        
    def b_setWaterLevel(self,waterLevel, finalize=True):
        self.setWaterLevel(waterLevel, finalize)
        self.d_setWaterLevel(waterLevel)
        
    def getWaterLevel(self):
        return self.waterLevel
        
    def setGrowthLevel(self, growthLevel, finalize):
        self.growthLevel = growthLevel
        self.updateEstate(growthLevel=growthLevel, finalize=finalize)
        
    def d_setGrowthLevel(self,growthLevel):
        self.sendUpdate('setGrowthLevel' , [growthLevel])
        
    def b_setGrowthLevel(self,growthLevel, finalize=True):
        if growthLevel > 127:
            growthLevel = 127 #range clamping
        self.setGrowthLevel(growthLevel, finalize)
        self.d_setGrowthLevel(growthLevel)
        
    def getGrowthLevel(self):
        return self.growthLevel

    def waterPlant(self):
        senderId = self.air.getAvatarIdFromSender()
        toon = simbase.air.doId2do.get(senderId)
        if not toon:
            self.sendInteractionDenied(senderId)
            return

        if not self.requestInteractingToon(senderId):
            self.sendInteractionDenied(senderId)
            return
            

        waterPower = GardenGlobals.getWateringCanPower(toon.wateringCan, toon.wateringCanSkill)
        
        self.skillUp = 0
        curLevel = self.getWaterLevel()
        if curLevel < self.maxWaterLevel:
            self.skillUp = 1
            
        level = curLevel + waterPower
        if level > self.maxWaterLevel:
            level = self.maxWaterLevel
        if level < 1:
            level = 1
        self.b_setWaterLevel(level)
        self.setMovie(GardenGlobals.MOVIE_WATER, senderId)

    def waterPlantDone(self):
        # delay sending the toon skillup until after the water movie is finished
        senderId = self.air.getAvatarIdFromSender()
        toon = simbase.air.doId2do.get(senderId)
        if not toon:
            return
        if hasattr(self, 'skillUp') and self.skillUp:
            #print ("!!!watering skill up!!!!!!!!")
            toon.b_setWateringCanSkill(toon.wateringCanSkill+1)
        else:
            # this non-update is used to free the avatar
            toon.b_setWateringCanSkill(toon.wateringCanSkill)

        #Just to be safe clear the movie, fixes an infinite loop teleport bug
        self.notify.debug('waterPlantDone: clearing the movie')
        self.setMovie(GardenGlobals.MOVIE_CLEAR, senderId)            

    def doEpoch(self, numEpochs):
        growthLevel = 0
        waterLevel = 0
        for i in range(numEpochs):
            waterLevel = self.getWaterLevel()
            growthLevel = self.getGrowthLevel()

            if waterLevel > 0:
                print("growing plant")
                # grow the plant
                growthLevel += 1
                waterLevel -= 1
            else:
                waterLevel -= 1
                waterLevel = max (waterLevel, self.minWaterLevel)

            self.b_setWaterLevel(waterLevel, False)
            self.b_setGrowthLevel(growthLevel, False)

        return (growthLevel, waterLevel)

    # Note the isFruiting, isGTEFruiting ... is seedling is also defined in
    # DistributedPlantBase.py, if any changes are done, make sure they're in sync

    def isFruiting(self):
        retval = self.growthLevel >= self.growthThresholds[2]
        return retval

    def isGTEFruiting(self):
        """
        is greater than or equal to Fruiting
        """
        retval = self.growthLevel >= self.growthThresholds[2]
        return retval        

    def isFullGrown(self):
        """
        returns true only if it's exactly full grown
        """
        if self.growthLevel >= self.growthThresholds[2]:
            #the plant is fruiting
            return False
        elif self.growthLevel >= self.growthThresholds[1]:
            #the plant is full grown
            return True

        return False

    def isGTEFullGrown(self):
        """
        is greater than or equal to full grown
        """
        retval = self.growthLevel >= self.growthThresholds[1]
        return retval

    def isEstablished(self):
        if self.growthLevel >= self.growthThresholds[2]:
            #the plant is fruiting
            return False
        elif self.growthLevel >= self.growthThresholds[1]:
            #the plant is full grown
            return False
        elif self.growthLevel >= self.growthThresholds[0]:
            #the plant is established
            return True
        return False

    def isGTEEstablished(self):
        if self.growthLevel >= self.growthThresholds[0]:
            #the plant is >= established
            return True
        return False

    def isSeedling(self):
        if self.growthLevel >= self.growthThresholds[2]:
            #the plant is fruiting
            return False
        elif self.growthLevel >= self.growthThresholds[1]:
            #the plant is full grown
            return False
        elif self.growthLevel >= self.growthThresholds[0]:
            #the plant is established
            return False
        elif self.growthLevel < self.growthThresholds[0]:
            #the plant is a seedling
            return True

        return False

    def isGTESeedling(self):
        #duh everything >= seedling
        return True

    def isWilted(self):
        return self.waterLevel < 0
    
    def updateEstate(self, waterLevel=None, growthLevel=-1, variety=-1, finalize=True):
        if self.estateId:
            estate = simbase.air.doId2do.get(self.estateId)
            if estate:
                if finalize:
                    func = estate.b_setOneItem
                else:
                    func = estate.setOneItem

                func(self.ownerIndex, self.plot,
                     waterLevel=waterLevel,
                     growthLevel=growthLevel,
                     variety=variety)


