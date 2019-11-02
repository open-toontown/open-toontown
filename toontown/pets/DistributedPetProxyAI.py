from direct.showbase.PythonUtil import contains, lerp, clampScalar
from direct.distributed import DistributedObjectAI
from direct.directnotify import DirectNotifyGlobal
from toontown.pets import PetTraits, PetTricks
from toontown.pets import PetMood
from toontown.toonbase import ToontownGlobals
import random
import time
import string
import copy
BATTLE_TRICK_HP_MULTIPLIER = 10.0

class DistributedPetProxyAI(DistributedObjectAI.DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPetProxyAI')

    def __init__(self, air):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.ownerId = 0
        self.petName = 'unnamed'
        self.traitSeed = 0
        self.safeZone = ToontownGlobals.ToontownCentral
        self.traitList = [0] * PetTraits.PetTraits.NumTraits
        self.head = -1
        self.ears = -1
        self.nose = -1
        self.tail = -1
        self.bodyTexture = 0
        self.color = 0
        self.colorScale = 0
        self.eyeColor = 0
        self.gender = 0
        self.trickAptitudes = []
        self.lastSeenTimestamp = self.getCurEpochTimestamp()
        self.requiredMoodComponents = {}
        self.__funcsToDelete = []
        self.__generateDistTraitFuncs()
        self.__generateDistMoodFuncs()

    def getSetterName(self, valueName, prefix = 'set'):
        return '%s%s%s' % (prefix, string.upper(valueName[0]), valueName[1:])

    def setDNA(self, dna):
        head, ears, nose, tail, body, color, colorScale, eyes, gender = dna
        self.b_setHead(head)
        self.b_setEars(ears)
        self.b_setNose(nose)
        self.b_setTail(tail)
        self.b_setBodyTexture(body)
        self.b_setColor(color)
        self.b_setColorScale(colorScale)
        self.b_setEyeColor(eyes)
        self.b_setGender(gender)

    def getOwnerId(self):
        return self.ownerId

    def b_setOwnerId(self, ownerId):
        self.d_setOwnerId(ownerId)
        self.setOwnerId(ownerId)

    def d_setOwnerId(self, ownerId):
        self.sendUpdate('setOwnerId', [ownerId])

    def setOwnerId(self, ownerId):
        self.ownerId = ownerId

    def getPetName(self):
        return self.petName

    def b_setPetName(self, petName):
        self.d_setPetName(petName)
        self.setPetName(petName)

    def d_setPetName(self, petName):
        self.sendUpdate('setPetName', [petName])

    def setPetName(self, petName):
        self.petName = petName

    def getTraitSeed(self):
        return self.traitSeed

    def b_setTraitSeed(self, traitSeed):
        self.d_setTraitSeed(traitSeed)
        self.setTraitSeed(traitSeed)

    def d_setTraitSeed(self, traitSeed):
        self.sendUpdate('setTraitSeed', [traitSeed])

    def setTraitSeed(self, traitSeed):
        self.traitSeed = traitSeed

    def getSafeZone(self):
        return self.safeZone

    def b_setSafeZone(self, safeZone):
        self.d_setSafeZone(safeZone)
        self.setSafeZone(safeZone)

    def d_setSafeZone(self, safeZone):
        self.sendUpdate('setSafeZone', [safeZone])

    def setSafeZone(self, safeZone):
        self.safeZone = safeZone

    def setTraits(self, traitList):
        self.traitList = traitList

    def __generateDistTraitFuncs(self):
        for i in xrange(PetTraits.PetTraits.NumTraits):
            traitName = PetTraits.getTraitNames()[i]
            getterName = self.getSetterName(traitName, 'get')
            b_setterName = self.getSetterName(traitName, 'b_set')
            d_setterName = self.getSetterName(traitName, 'd_set')
            setterName = self.getSetterName(traitName)

            def traitGetter(i = i):
                return self.traitList[i]

            def b_traitSetter(value, setterName = setterName, d_setterName = d_setterName):
                self.__dict__[d_setterName](value)
                self.__dict__[setterName](value)

            def d_traitSetter(value, setterName = setterName):
                self.sendUpdate(setterName, [value])

            def traitSetter(value, i = i):
                self.traitList[i] = value

            self.__dict__[getterName] = traitGetter
            self.__dict__[b_setterName] = b_traitSetter
            self.__dict__[d_setterName] = d_traitSetter
            self.__dict__[setterName] = traitSetter
            self.__funcsToDelete.append(getterName)
            self.__funcsToDelete.append(b_setterName)
            self.__funcsToDelete.append(d_setterName)
            self.__funcsToDelete.append(setterName)

    def getHead(self):
        return self.head

    def b_setHead(self, head):
        self.d_setHead(head)
        self.setHead(head)

    def d_setHead(self, head):
        self.sendUpdate('setHead', [head])

    def setHead(self, head):
        self.head = head

    def getEars(self):
        return self.ears

    def b_setEars(self, ears):
        self.d_setEars(ears)
        self.setEars(ears)

    def d_setEars(self, ears):
        self.sendUpdate('setEars', [ears])

    def setEars(self, ears):
        self.ears = ears

    def getNose(self):
        return self.nose

    def b_setNose(self, nose):
        self.d_setNose(nose)
        self.setNose(nose)

    def d_setNose(self, nose):
        self.sendUpdate('setNose', [nose])

    def setNose(self, nose):
        self.nose = nose

    def getTail(self):
        return self.tail

    def b_setTail(self, tail):
        self.d_setTail(tail)
        self.setTail(tail)

    def d_setTail(self, tail):
        self.sendUpdate('setTail', [tail])

    def setTail(self, tail):
        self.tail = tail

    def getBodyTexture(self):
        return self.bodyTexture

    def b_setBodyTexture(self, bodyTexture):
        self.d_setBodyTexture(bodyTexture)
        self.setBodyTexture(bodyTexture)

    def d_setBodyTexture(self, bodyTexture):
        self.sendUpdate('setBodyTexture', [bodyTexture])

    def setBodyTexture(self, bodyTexture):
        self.bodyTexture = bodyTexture

    def getColor(self):
        return self.color

    def b_setColor(self, color):
        self.d_setColor(color)
        self.setColor(color)

    def d_setColor(self, color):
        self.sendUpdate('setColor', [color])

    def setColor(self, color):
        self.color = color

    def getColorScale(self):
        return self.colorScale

    def b_setColorScale(self, colorScale):
        self.d_setColorScale(colorScale)
        self.setColorScale(colorScale)

    def d_setColorScale(self, colorScale):
        self.sendUpdate('setColorScale', [colorScale])

    def setColorScale(self, colorScale):
        self.colorScale = colorScale

    def getEyeColor(self):
        return self.eyeColor

    def b_setEyeColor(self, eyeColor):
        self.d_setEyeColor(eyeColor)
        self.setEyeColor(eyeColor)

    def d_setEyeColor(self, eyeColor):
        self.sendUpdate('setEyeColor', [eyeColor])

    def setEyeColor(self, eyeColor):
        self.eyeColor = eyeColor

    def getGender(self):
        return self.gender

    def b_setGender(self, gender):
        self.d_setGender(gender)
        self.setGender(gender)

    def d_setGender(self, gender):
        self.sendUpdate('setGender', [gender])

    def setGender(self, gender):
        self.gender = gender

    def getLastSeenTimestamp(self):
        return self.lastSeenTimestamp

    def b_setLastSeenTimestamp(self, timestamp):
        self.d_setLastSeenTimestamp(timestamp)
        self.setLastSeenTimestamp(timestamp)

    def d_setLastSeenTimestamp(self, timestamp):
        self.sendUpdate('setLastSeenTimestamp', [timestamp])

    def setLastSeenTimestamp(self, timestamp):
        self.lastSeenTimestamp = timestamp

    def getCurEpochTimestamp(self):
        return int(time.time())

    def getTimeSinceLastSeen(self):
        t = time.time() - self.lastSeenTimestamp
        return max(0.0, t)

    def __handleMoodSet(self, component, value):
        if self.isGenerated():
            self.mood.setComponent(component, value)
        else:
            self.requiredMoodComponents[component] = value

    def __handleMoodGet(self, component):
        if self.isGenerated():
            return self.mood.getComponent(component)
        else:
            return 0.0

    def __generateDistMoodFuncs(self):
        for compName in PetMood.PetMood.Components:
            getterName = self.getSetterName(compName, 'get')
            setterName = self.getSetterName(compName)

            def moodGetter(compName = compName):
                return self.__handleMoodGet(compName)

            def b_moodSetter(value, setterName = setterName):
                self.__dict__[setterName](value)

            def d_moodSetter(value, setterName = setterName):
                self.sendUpdate(setterName, [value])

            def moodSetter(value, compName = compName):
                self.__handleMoodSet(compName, value)

            self.__dict__[getterName] = moodGetter
            self.__dict__['b_%s' % setterName] = b_moodSetter
            self.__dict__['d_%s' % setterName] = d_moodSetter
            self.__dict__[setterName] = moodSetter
            self.__funcsToDelete.append(getterName)
            self.__funcsToDelete.append('b_%s' % setterName)
            self.__funcsToDelete.append('d_%s' % setterName)
            self.__funcsToDelete.append(setterName)

    def getTrickAptitudes(self):
        return self.trickAptitudes

    def b_setTrickAptitudes(self, aptitudes):
        self.setTrickAptitudes(aptitudes, local=1)
        self.d_setTrickAptitudes(aptitudes)

    def d_setTrickAptitudes(self, aptitudes):
        if __dev__:
            for aptitude in aptitudes:
                pass

        while len(aptitudes) < len(PetTricks.Tricks) - 1:
            aptitudes.append(0.0)

        self.sendUpdate('setTrickAptitudes', [aptitudes])

    def setTrickAptitudes(self, aptitudes, local = 0):
        if not local:
            DistributedPetProxyAI.notify.debug('setTrickAptitudes: %s' % aptitudes)
        while len(self.trickAptitudes) < len(PetTricks.Tricks) - 1:
            self.trickAptitudes.append(0.0)

        self.trickAptitudes = aptitudes

    def getTrickAptitude(self, trickId):
        if trickId > len(self.trickAptitudes) - 1:
            return 0.0
        return self.trickAptitudes[trickId]

    def setTrickAptitude(self, trickId, aptitude, send = 1):
        aptitude = clampScalar(aptitude, 0.0, 1.0)
        aptitudes = self.trickAptitudes
        while len(aptitudes) - 1 < trickId:
            aptitudes.append(0.0)

        if aptitudes[trickId] != aptitude:
            aptitudes[trickId] = aptitude
            if send:
                self.b_setTrickAptitudes(aptitudes)
            else:
                self.setTrickAptitudes(aptitudes, local=1)

    def generate(self):
        DistributedObjectAI.DistributedObjectAI.generate(self)
        self.traits = PetTraits.PetTraits(self.traitSeed, self.safeZone)
        print self.traits.traits
        for i in xrange(len(self.traitList)):
            value = self.traitList[i]
            if value == 0.0:
                traitName = PetTraits.getTraitNames()[i]
                traitValue = self.traits.getTraitValue(traitName)
                DistributedPetProxyAI.notify.info("%s: initializing new trait '%s' to %s, seed=%s" % (self.doId,
                 traitName,
                 traitValue,
                 self.traitSeed))
                setterName = self.getSetterName(traitName, 'b_set')
                self.__dict__[setterName](traitValue)

        self.mood = PetMood.PetMood(self)
        for mood, value in self.requiredMoodComponents.items():
            self.mood.setComponent(mood, value, announce=0)

        self.requiredMoodComponents = {}
        self.accept(self.mood.getMoodChangeEvent(), self.handleMoodChange)
        self.mood.start()

    def broadcastDominantMood(self):
        self.d_setDominantMood(self.mood.getDominantMood())

    def delete(self):
        self.ignore(self.mood.getMoodChangeEvent())
        self.mood.destroy()
        del self.mood
        del self.traits
        for funcName in self.__funcsToDelete:
            del self.__dict__[funcName]

        DistributedObjectAI.DistributedObjectAI.delete(self)

    def setMoodComponent(self, component, value):
        setter = self.getSetterName(component, 'b_set')
        self.__dict__[setter](value)

    def addToMood(self, component, delta):
        value = self.mood.getComponent(component)
        value += delta
        self.setMoodComponent(component, clampScalar(value, 0.0, 1.0))

    def lerpMood(self, component, factor):
        curVal = self.mood.getComponent(component)
        if factor < 0:
            self.setMoodComponent(component, lerp(curVal, 0.0, -factor))
        else:
            self.setMoodComponent(component, lerp(curVal, 1.0, factor))

    def addToMoods(self, mood2delta):
        for mood, delta in mood2delta.items():
            self.addToMood(mood, delta)

    def lerpMoods(self, mood2factor):
        for mood, factor in mood2factor.items():
            self.lerpMood(mood, factor)

    def isContented(self):
        return self.mood.getDominantMood() in PetMood.PetMood.ContentedMoods

    def _willDoTrick(self, trickId):
        if self.isContented():
            minApt = PetTricks.MinActualTrickAptitude
            maxApt = PetTricks.MaxActualTrickAptitude
        else:
            minApt = PetTricks.NonHappyMinActualTrickAptitude
            maxApt = PetTricks.NonHappyMaxActualTrickAptitude
        randVal = random.random()
        cutoff = lerp(minApt, maxApt, self.getTrickAptitude(trickId))
        if self.mood.isComponentActive('fatigue'):
            cutoff *= 0.5
        cutoff *= PetTricks.TrickAccuracies[trickId]
        DistributedPetProxyAI.notify.debug('_willDoTrick: %s / %s' % (randVal, cutoff))
        return randVal < cutoff

    def _handleDidTrick(self, trickId):
        DistributedPetProxyAI.notify.debug('_handleDidTrick: %s' % trickId)
        if trickId == PetTricks.Tricks.BALK:
            return
        aptitude = self.getTrickAptitude(trickId)
        self.setTrickAptitude(trickId, aptitude + PetTricks.AptitudeIncrementDidTrick)
        self.addToMood('fatigue', lerp(PetTricks.MaxTrickFatigue, PetTricks.MinTrickFatigue, aptitude))
        self.d_setDominantMood(self.mood.getDominantMood())

    def attemptBattleTrick(self, trickId):
        self.lerpMoods({'boredom': -.1,
         'excitement': 0.05,
         'loneliness': -.05})
        if self._willDoTrick(trickId):
            self._handleDidTrick(trickId)
            self.b_setLastSeenTimestamp(self.getCurEpochTimestamp())
            return 0
        else:
            self.b_setLastSeenTimestamp(self.getCurEpochTimestamp())
            return 1

    def handleMoodChange(self, components = [], distribute = 1):
        if len(components) == 0:
            components = PetMood.PetMood.Components
        if distribute:
            if len(components) == len(PetMood.PetMood.Components):
                values = []
                for comp in PetMood.PetMood.Components:
                    values.append(self.mood.getComponent(comp))

                self.sendUpdate('setMood', values)
            else:
                for comp in components:
                    setter = self.getSetterName(comp, 'd_set')
                    self.__dict__[setter](self.mood.getComponent(comp))

    def d_setDominantMood(self, dominantMood):
        self.sendUpdate('setDominantMood', [dominantMood])
