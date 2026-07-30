from toontown.pets.PetConstants import AnimMoods
from toontown.pets import PetMood
import string

class PetBase:

    def getSetterName(self, valueName, prefix = 'set'):
        return '%s%s%s' % (prefix, string.upper(valueName[0]), valueName[1:])

    def getAnimMood(self):
        if self.mood.getDominantMood() in PetMood.PetMood.ExcitedMoods:
            return AnimMoods.EXCITED
        elif self.mood.getDominantMood() in PetMood.PetMood.UnhappyMoods:
            return AnimMoods.SAD
        else:
            return AnimMoods.NEUTRAL

    def isExcited(self):
        return self.getAnimMood() == AnimMoods.EXCITED

    def isSad(self):
        return self.getAnimMood() == AnimMoods.SAD
