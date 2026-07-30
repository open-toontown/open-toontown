from . import FishGlobals
from toontown.toonbase import TTLocalizer
from direct.directnotify import DirectNotifyGlobal

class FishBase:
    notify = DirectNotifyGlobal.directNotify.newCategory('FishBase')

    def __init__(self, genus, species, weight):
        self.genus = genus
        self.species = species
        self.weight = weight

    def getGenus(self):
        return self.genus

    def getSpecies(self):
        return self.species

    def getWeight(self):
        return self.weight

    def setWeight(self, weight):
        self.weight = weight

    def getVitals(self):
        return (self.genus, self.species, self.weight)

    def getValue(self):
        return FishGlobals.getValue(self.genus, self.species, self.weight)

    def getGenusName(self):
        return TTLocalizer.FishGenusNames[self.genus]

    def getSpeciesName(self):
        return TTLocalizer.FishSpeciesNames[self.genus][self.species]

    def getRarity(self):
        return FishGlobals.getRarity(self.genus, self.species)

    def getPhase(self):
        dict = FishGlobals.FishFileDict
        fileInfo = dict.get(self.genus, dict[-1])
        return fileInfo[0]

    def getActor(self):
        prefix = 'phase_%s/models/char/' % self.getPhase()
        dict = FishGlobals.FishFileDict
        fileInfo = dict.get(self.genus, dict[-1])
        from direct.actor import Actor
        actor = Actor.Actor(prefix + fileInfo[1], {'intro': prefix + fileInfo[2],
         'swim': prefix + fileInfo[3]})
        return actor

    def getSound(self):
        sound = None
        loop = None
        delay = None
        playRate = None
        if base.config.GetBool('want-fish-audio', 1):
            soundDict = FishGlobals.FishAudioFileDict
            fileInfo = soundDict.get(self.genus, None)
            if fileInfo:
                prefix = 'phase_%s/audio/sfx/' % self.getPhase()
                sound = loader.loadSfx(prefix + soundDict[self.genus][0])
                loop = soundDict[self.genus][1]
                delay = soundDict[self.genus][2]
                playRate = soundDict[self.genus][3]
        return (sound,
         loop,
         delay,
         playRate)

    def __str__(self):
        return '%s, weight: %s value: %s' % (self.getSpeciesName(), self.weight, self.getValue())
