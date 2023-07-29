from otp.ai.AIBase import *
from . import DistributedLawnDecorAI
from direct.directnotify import DirectNotifyGlobal
from . import GardenGlobals

from direct.showbase.ShowBase import *

class DistributedGardenPlotAI(DistributedLawnDecorAI.DistributedLawnDecorAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPlantBaseAI')
    
    
    def __init__(self, typeIndex = 0, ownerIndex = 0, plot = 0):
        DistributedLawnDecorAI.DistributedLawnDecorAI.__init__(self, simbase.air, ownerIndex, plot)
        self.type = typeIndex
        self.occupied = False
        
    def plantNothing(self, burntBeans):
        senderId = self.air.getAvatarIdFromSender()
        toon = simbase.air.doId2do.get(senderId)
        toon.takeMoney(burntBeans)
        print(("burning money%s" % (burntBeans)))
        #deliberately not burning the special, since they cost so much,
        #beside Clarabelle tells you what beans to plant it with anyway.

    def plantFlower(self, species, variety):
        print("planting flower species=%d variety=%d" % (species, variety))
        senderId = self.air.getAvatarIdFromSender()
        
        zoneId = self.zoneId
        estateOwnerDoId = simbase.air.estateMgr.zone2owner.get(zoneId)

        if not senderId == estateOwnerDoId:
            self.notify.warning("how did this happen, planting a flower you don't own")
            return

        if not species in GardenGlobals.PlantAttributes:
            self.air.writeServerEvent('suspicious', senderId, 'Planting a species %s that does not exist.' % (species))
            return
            
        if estateOwnerDoId:
            estate = simbase.air.estateMgr.estate.get(estateOwnerDoId)
            if estate:
                #we should have a valid DistributedEstateAI at this point
                #first get the recipe back
                plantType = GardenGlobals.PlantAttributes[species]['plantType']
                if plantType == GardenGlobals.STATUARY_TYPE:
                    # Statues have only one type. Added this so that I could use the variety to contain the optional field for the ToonStatuary
                    recipeKey = GardenGlobals.PlantAttributes[species]['varieties'][0][0]
                else:
                    recipeKey = GardenGlobals.PlantAttributes[species]['varieties'][variety][0]
                recipe = GardenGlobals.Recipes[recipeKey]
                #find out how many beans the toon can plant
                toon = simbase.air.doId2do.get(senderId)
                shovelIndex = toon.getShovel()
                shovelPower = GardenGlobals.getShovelPower(shovelIndex, toon.getShovelSkill())
                allOk = 1
                if shovelPower >= len(recipe['beans']):
                    skillUpOnPlanting = 0
                    if skillUpOnPlanting:
                        if shovelPower == len(recipe['beans']):
                            #time to add skill points
                            currentShovelSkill = toon.getShovelSkill()
                            newShovelSkill = currentShovelSkill + shovelPower
                            toon.b_setShovelSkill(newShovelSkill)
                else:
                    self.notify.warning("ILLEGAL recipe used!! shovel is not powerful enough!!! fool!")
                    allOk = 0
                if toon.takeMoney(len(recipe['beans'])):
                    pass
                else:
                    self.notify.warning("Not enough beans for recipe!!! fool!")
                    allOk = 0
                    
                #if all goes well plant the flower
                if allOk:
                    self.setMovie(GardenGlobals.MOVIE_PLANT, senderId, (species, variety))
         
                    
    def burnSpecial(self, species):
        variety = 0
        
        if not species in GardenGlobals.PlantAttributes or not variety in GardenGlobals.PlantAttributes[species]['varieties']:
            self.notify.warning("Suspicious: Calling on a species does not exist.")
            return
        
        recipeKey = GardenGlobals.PlantAttributes[species]['varieties'][variety][0]
        recipe = GardenGlobals.Recipes[recipeKey]
        special = recipe['special']
        
        senderId = self.air.getAvatarIdFromSender()
        toon = simbase.air.doId2do.get(senderId)
        toon.removeGardenItem(special, 1)


    def doGardenAccelerator(self):
        senderId = self.air.getAvatarIdFromSender()
        zoneId = self.zoneId
        estateOwnerDoId = simbase.air.estateMgr.zone2owner.get(zoneId)

        if not senderId == estateOwnerDoId:
            self.notify.warning("how did this happen, planting an item you don't own")
            return
        if estateOwnerDoId:
            estate = simbase.air.estateMgr.estate.get(estateOwnerDoId)
            if estate:
                #we should have a valid DistributedEstateAI at this point
                estate.doEpochNow(onlyForThisToonIndex = self.ownerIndex)

    def plantStatuary(self, species):
        print("planting item species=%d " % (species))
        if species == GardenGlobals.GardenAcceleratorSpecies:
            self.doGardenAccelerator()
        else:
            self.plantFlower(species, 0)

        self.burnSpecial(species)

    def plantToonStatuary(self, species, variety = 0):
        if species == GardenGlobals.GardenAcceleratorSpecies:
            self.doGardenAccelerator()
        else:
            self.plantFlower(species, variety)
            
        self.burnSpecial(species)

    def plantGagTree(self, gagTrack, gagLevel):
        self.notify.info("Planting GagTree: %s %s" % (gagTrack, gagLevel))
        senderId = self.air.getAvatarIdFromSender()
        
        zoneId = self.zoneId
        estateOwnerDoId = simbase.air.estateMgr.zone2owner.get(zoneId)

        if not senderId == estateOwnerDoId:
            self.notify.warning("how did this happen, planting in a plot you don't own")
            return
        
        if estateOwnerDoId:
            estate = simbase.air.estateMgr.estate.get(estateOwnerDoId)
            if estate:
                #we should have a valid DistributedEstateAI at this point
                toon = simbase.air.doId2do.get(senderId)

                allOk = True
                # does the toon have an extra gag of this type?
                if toon.inventory.numItem(gagTrack, gagLevel) <= 0:
                    self.notify.warning("Toon tried to plant a tree without having the gag! %s" % toon.doId)
                    allOk = False

                # is this tree already planted?
                if estate.hasGagTree(self.ownerIndex, gagTrack, gagLevel):
                    allOk = False

                # is the gagtree before this one already planted?
                if gagLevel > 0:
                    if not estate.hasGagTree(self.ownerIndex, gagTrack, gagLevel-1):
                        allOk = False

                #if all goes well plant the flower
                if allOk:
                    self.setMovie(GardenGlobals.MOVIE_PLANT, senderId, (gagTrack, gagLevel))
                else:
                    self.setMovie(GardenGlobals.MOVIE_PLANT_REJECTED, senderId, (gagTrack, gagLevel))


                                   
    def movieDone(self):
        self.clearInteractingToon()        
        if self.lastMovie == GardenGlobals.MOVIE_PLANT:
            type = GardenGlobals.whatCanBePlanted(self.ownerIndex, self.plot)
            if type == GardenGlobals.GAG_TREE_TYPE:
                self.lastMovie = None
                avId = self.lastMovieAvId
                gagTrack,gagLevel = self.lastMovieArgs
                zoneId = self.zoneId
                estateOwnerDoId = simbase.air.estateMgr.zone2owner.get(zoneId)
                estate = simbase.air.estateMgr.estate.get(estateOwnerDoId)
                if estate:
                    toon = simbase.air.doId2do.get(avId)
                    toon.inventory.useItem(gagTrack, gagLevel)
                    toon.d_setInventory(toon.inventory.makeNetString())
                    estate.removeGardenPlot(self.ownerIndex, self.plot)
                    typeIndex = GardenGlobals.getTreeTypeIndex(gagTrack, gagLevel)
                    itemId = estate.plantTree(avId = avId,
                                                type = typeIndex,
                                                plot = self.plot,
                                                water = 0,
                                                growth = 0,
                                                optional = 0)

                    # tell the new tree to tell the avatar to finish up the planting movie
                    tree = simbase.air.doId2do.get(itemId)
                    tree.setMovie(GardenGlobals.MOVIE_FINISHPLANTING, avId)

                    #log we are planting a tree
                    self.air.writeServerEvent("garden_plant_tree", avId,
                                                  '%d|%d' % (gagTrack,gagLevel))                    
            else:
                self.lastMovie = None
                avId = self.lastMovieAvId
                species,variety = self.lastMovieArgs
                zoneId = self.zoneId
                estateOwnerDoId = simbase.air.estateMgr.zone2owner.get(zoneId)
                estate = simbase.air.estateMgr.estate.get(estateOwnerDoId)

                if estate:
                    estate.removeGardenPlot(self.ownerIndex, self.plot)
                    itemId = estate.plantFlower(avId = avId,
                                                type = species,
                                                plot = self.plot,
                                                water = 0,
                                                growth = 0,
                                                optional = variety)

                    # tell the new tree to tell the avatar to finish up the planting movie
                    flower = simbase.air.doId2do.get(itemId)
                    flower.setMovie(GardenGlobals.MOVIE_FINISHPLANTING, avId)

                   #since plant statuary calls plant flower, lets differentiate between the two
                    if type == GardenGlobals.FLOWER_TYPE:
                        #log we are planting a flower
                        self.air.writeServerEvent("garden_plant_flower", avId,
                                                  '%d|%d' % (species,variety))
                    elif type == GardenGlobals.STATUARY_TYPE:
                        #log we are planting a statue
                        self.air.writeServerEvent("garden_plant_statue", avId,
                                                  '%d' % (species))
                    else:
                        self.notify.warning('unhandled case %s' % type)

        elif self.lastMovie == GardenGlobals.MOVIE_FINISHREMOVING:
            self.lastMovie = None
            zoneId = self.zoneId
            avId = self.lastMovieAvId
            estateOwnerDoId = simbase.air.estateMgr.zone2owner.get(zoneId)
            estate = simbase.air.estateMgr.estate.get(estateOwnerDoId)
            if estate:
                itemId = self.doId
                # tell the gardenplot to tell the toon to clear the movie 
                item = simbase.air.doId2do.get(itemId)
                item.setMovie(GardenGlobals.MOVIE_CLEAR, avId)                




    
                    



