from . import FishBase
from . import FishGlobals

class FishCollection:

    def __init__(self):
        self.fishList = []

    def __len__(self):
        return len(self.fishList)

    def getFish(self):
        return self.fishList

    def makeFromNetLists(self, genusList, speciesList, weightList):
        self.fishList = []
        for genus, species, weight in zip(genusList, speciesList, weightList):
            self.fishList.append(FishBase.FishBase(genus, species, weight))

    def getNetLists(self):
        genusList = []
        speciesList = []
        weightList = []
        for fish in self.fishList:
            genusList.append(fish.getGenus())
            speciesList.append(fish.getSpecies())
            weightList.append(fish.getWeight())

        return [genusList, speciesList, weightList]

    def hasFish(self, genus, species):
        for fish in self.fishList:
            if fish.getGenus() == genus and fish.getSpecies() == species:
                return 1

        return 0

    def hasGenus(self, genus):
        for fish in self.fishList:
            if fish.getGenus() == genus:
                return 1

        return 0

    def __collect(self, newFish, updateCollection):
        for fish in self.fishList:
            if fish.getGenus() == newFish.getGenus() and fish.getSpecies() == newFish.getSpecies():
                if fish.getWeight() < newFish.getWeight():
                    if updateCollection:
                        fish.setWeight(newFish.getWeight())
                    return FishGlobals.COLLECT_NEW_RECORD
                else:
                    return FishGlobals.COLLECT_NO_UPDATE

        if updateCollection:
            self.fishList.append(newFish)
        return FishGlobals.COLLECT_NEW_ENTRY

    def collectFish(self, newFish):
        return self.__collect(newFish, updateCollection=1)

    def getCollectResult(self, newFish):
        return self.__collect(newFish, updateCollection=0)

    def __str__(self):
        numFish = len(self.fishList)
        txt = 'Fish Collection (%s fish):' % numFish
        for fish in self.fishList:
            txt += '\n' + str(fish)

        return txt
