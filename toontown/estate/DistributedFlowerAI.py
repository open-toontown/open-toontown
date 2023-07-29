from toontown.estate import DistributedPlantBaseAI
from direct.directnotify import DirectNotifyGlobal
from . import GardenGlobals

class DistributedFlowerAI(DistributedPlantBaseAI.DistributedPlantBaseAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedFlowerAI')
    
    
    def __init__(self, typeIndex = 0, waterLevel = 0, growthLevel = 0, optional = None, ownerIndex = 0, plot = 0):
        DistributedPlantBaseAI.DistributedPlantBaseAI.__init__(self, typeIndex, waterLevel, growthLevel, optional, ownerIndex, plot)

    def getVariety(self):
        return self.optional

    def handleSkillUp(self, toon):
        #first get the recipe back
        recipeKey = GardenGlobals.PlantAttributes[self.typeIndex]\
                    ['varieties'][self.optional][0]
        recipe = GardenGlobals.Recipes[recipeKey]
        #find out how many beans the toon can plant
        
        shovelIndex = toon.getShovel()
        shovelPower = GardenGlobals.getShovelPower(shovelIndex, toon.getShovelSkill())
        giveSkillUp = 1
        if not shovelPower == len(recipe['beans']):
            giveSkillUp = 0

        #dont give a skill up if its wilted
        if self.isWilted():
            giveSkillUp = -1

        #dont give a skill up if the plant is not fruiting err blooming
        if not self.isFruiting():
            giveSkillUp = -2

        if giveSkillUp > 0:
            #time to add skill points
            currentShovelSkill = toon.getShovelSkill()
            newShovelSkill = currentShovelSkill + 1
            toon.b_setShovelSkill(newShovelSkill)

        #log each time he picks a flower, if he got a skillup or why he didnt,
        # what his shovel is,  and what his new shovel skill is
        self.air.writeServerEvent("garden_flower_pick", toon.doId,
                                  '%d|%d|%d' % (giveSkillUp,toon.getShovel(), toon.getShovelSkill()))
        

    def handleFlowerBasket(self, toon):
        addToBasket = True

        if self.isWilted():
            #don't put a wilted flower in the flower basket
            addToBasket = False

        #dont put it in the basket if the plant is not fruiting err blooming
        if not self.isFruiting():
            addToBasket = False

        if addToBasket:
            toon.addFlowerToBasket(self.typeIndex, self.optional)

    def removeItem(self):
        #import pdb; pdb.set_trace()
        senderId = self.air.getAvatarIdFromSender()
        
        zoneId = self.zoneId
        estateOwnerDoId = simbase.air.estateMgr.zone2owner.get(zoneId)

        if not senderId == estateOwnerDoId:
            self.notify.warning("how did this happen, picking a flower you don't own")
            self.sendInteractionDenied(senderId)
            return

        if not self.requestInteractingToon(senderId):
            self.sendInteractionDenied(senderId)
            return
            
        
        if estateOwnerDoId:
            estate = simbase.air.estateMgr.estate.get(estateOwnerDoId)
            if estate:
                #we should have a valid DistributedEstateAI at this point
                self.setMovie(GardenGlobals.MOVIE_REMOVE, senderId)
                

    def movieDone(self):
        if self.lastMovie == GardenGlobals.MOVIE_REMOVE:
            self.lastMovie = None
            zoneId = self.zoneId
            avId = self.lastMovieAvId
            estateOwnerDoId = simbase.air.estateMgr.zone2owner.get(zoneId)
            estate = simbase.air.estateMgr.estate.get(estateOwnerDoId)
            if estate:
                itemId = estate.removePlantAndPlaceGardenPlot(self.ownerIndex, self.plot)

                # tell the gardenplot to tell the toon to finish 'removing'
                item = simbase.air.doId2do.get(itemId)
                item.setMovie(GardenGlobals.MOVIE_FINISHREMOVING, avId)

                toon = simbase.air.doId2do.get(avId)
                if toon:
                    self.handleSkillUp(toon)
                    self.handleFlowerBasket(toon)
        elif self.lastMovie == GardenGlobals.MOVIE_FINISHPLANTING:
            self.lastMovie = None
            zoneId = self.zoneId
            avId = self.lastMovieAvId
            estateOwnerDoId = simbase.air.estateMgr.zone2owner.get(zoneId)
            estate = simbase.air.estateMgr.estate.get(estateOwnerDoId)
            if estate:
                itemId = self.doId

                # tell the gardenplot to tell the toon to clear the movie, so the
                # results dialog doesn't come up again when he exits from his house
                item = simbase.air.doId2do.get(itemId)
                item.setMovie(GardenGlobals.MOVIE_CLEAR, avId)                



