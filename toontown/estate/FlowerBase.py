import GardenGlobals
from toontown.toonbase import TTLocalizer
from direct.directnotify import DirectNotifyGlobal

class FlowerBase:
    notify = DirectNotifyGlobal.directNotify.newCategory('FlowerBase')

    def __init__(self, species, variety):
        self.species = species
        self.variety = variety
        if self.species not in GardenGlobals.PlantAttributes.keys():
            print 'remove me when everyone is updated'
            self.species = 56
            species = 56

    def getSpecies(self):
        return self.species

    def setSpecies(self, species):
        self.species = species

    def getVariety(self):
        return self.variety

    def setVariety(self, variety):
        self.variety = variety

    def getVitals(self):
        return (self.species, self.variety)

    def getValue(self):
        return GardenGlobals.PlantAttributes[self.species]['varieties'][self.variety][2]

    def getSpeciesName(self):
        return TTLocalizer.FlowerSpeciesNames[self.species]

    def getVarietyName(self):
        return self.getFullName()

    def getFullName(self):
        return GardenGlobals.getFlowerVarietyName(self.species, self.variety)

    def getFullNameWithRecipe(self):
        name = GardenGlobals.getFlowerVarietyName(self.species, self.variety)
        recipeKey = GardenGlobals.PlantAttributes[self.species]['varieties'][self.variety][0]
        name += ' (%s)' % GardenGlobals.Recipes[recipeKey]['beans']
        return name

    def __str__(self):
        return '%s, value: %s' % (self.getFullName(), self.getValue())
