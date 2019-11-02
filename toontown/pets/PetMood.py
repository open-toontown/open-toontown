from direct.directnotify import DirectNotifyGlobal
from direct.task import Task
from direct.showbase.PythonUtil import lerp, average, clampScalar
from toontown.toonbase import TTLocalizer
import random, time, weakref

class PetMood:
    notify = DirectNotifyGlobal.directNotify.newCategory('PetMood')
    Neutral = 'neutral'
    Components = ('boredom', 'restlessness', 'playfulness', 'loneliness', 'sadness', 'affection', 'hunger', 'confusion', 'excitement', 'fatigue', 'anger', 'surprise')
    SerialNum = 0
    ContentedMoods = ('neutral', 'excitement', 'playfulness', 'affection')
    ExcitedMoods = ('excitement', 'playfulness')
    UnhappyMoods = ('boredom', 'restlessness', 'loneliness', 'sadness', 'fatigue', 'hunger', 'anger')
    DisabledDominants = ('restlessness', 'playfulness')
    AssertiveDominants = ('fatigue',)
    HOUR = 1.0
    MINUTE = HOUR / 60.0
    DAY = 24.0 * HOUR
    WEEK = 7 * DAY
    LONGTIME = 5000 * WEEK
    TBoredom = 12 * HOUR
    TRestlessness = 18 * HOUR
    TPlayfulness = -1 * HOUR
    TLoneliness = 24 * HOUR
    TSadness = -1 * HOUR
    TFatigue = -15 * MINUTE
    THunger = 24 * HOUR
    TConfusion = -5 * MINUTE
    TExcitement = -5 * MINUTE
    TSurprise = -5 * MINUTE
    TAffection = -10 * MINUTE
    TAngerDec = -20 * MINUTE
    TAngerInc = 2 * WEEK

    def __init__(self, pet = None):
        self.setPet(pet)
        self.started = 0
        self.serialNum = PetMood.SerialNum
        PetMood.SerialNum += 1
        for comp in PetMood.Components:
            self.__dict__[comp] = 0.0

        def calcDrift(baseT, trait, fasterDriftIsBetter = False):
            value = trait.percentile
            if not trait.higherIsBetter:
                value = 1.0 - value
            if fasterDriftIsBetter:
                if value < 0.5:
                    factor = lerp(2.0, 1.0, value * 2.0)
                else:
                    rebased = (value - 0.5) * 2.0
                    factor = lerp(1.0, 0.1, rebased * rebased)
            elif value < 0.5:
                factor = lerp(0.75, 1.0, value * 2.0)
            else:
                rebased = (value - 0.5) * 2.0
                factor = lerp(1.0, 28.0, rebased * rebased)
            return baseT * factor

        pet = self.getPet()
        self.tBoredom = calcDrift(PetMood.TBoredom, pet.traits.traits['boredomThreshold'])
        self.tRestlessness = calcDrift(PetMood.TRestlessness, pet.traits.traits['restlessnessThreshold'])
        self.tPlayfulness = calcDrift(PetMood.TPlayfulness, pet.traits.traits['playfulnessThreshold'])
        self.tLoneliness = calcDrift(PetMood.TLoneliness, pet.traits.traits['lonelinessThreshold'])
        self.tSadness = calcDrift(PetMood.TSadness, pet.traits.traits['sadnessThreshold'], True)
        self.tFatigue = calcDrift(PetMood.TFatigue, pet.traits.traits['fatigueThreshold'], True)
        self.tHunger = calcDrift(PetMood.THunger, pet.traits.traits['hungerThreshold'])
        self.tConfusion = calcDrift(PetMood.TConfusion, pet.traits.traits['confusionThreshold'], True)
        self.tExcitement = calcDrift(PetMood.TExcitement, pet.traits.traits['excitementThreshold'])
        self.tSurprise = calcDrift(PetMood.TSurprise, pet.traits.traits['surpriseThreshold'], True)
        self.tAffection = calcDrift(PetMood.TAffection, pet.traits.traits['affectionThreshold'])
        self.tAngerDec = calcDrift(PetMood.TAngerDec, pet.traits.traits['angerThreshold'], True)
        self.tAngerInc = calcDrift(PetMood.TAngerInc, pet.traits.traits['angerThreshold'])
        self.dominantMood = PetMood.Neutral

    def destroy(self):
        self.stop()
        del self.petRef

    def setPet(self, pet):
        self.petRef = weakref.ref(pet)

    def getPet(self):
        pet = self.petRef()
        if pet is None:
            self.notify.error('pet has been deleted')
        return pet

    def getMoodDriftTaskName(self):
        return 'petMoodDrift-%s' % self.serialNum

    def getMoodChangeEvent(self):
        return 'petMoodChange-%s' % self.serialNum

    def getDominantMoodChangeEvent(self):
        return 'petDominantMoodChange-%s' % self.serialNum

    def announceChange(self, components = []):
        oldMood = self.dominantMood
        if hasattr(self, 'dominantMood'):
            del self.dominantMood
        newMood = self.getDominantMood()
        messenger.send(self.getMoodChangeEvent(), [components])
        if newMood != oldMood:
            messenger.send(self.getDominantMoodChangeEvent(), [newMood])

    def getComponent(self, compName):
        return self.__dict__[compName]

    def setComponent(self, compName, value, announce = 1):
        different = self.__dict__[compName] != value
        self.__dict__[compName] = value
        if announce and different:
            self.announceChange([compName])

    def _getComponentThreshold(self, compName):
        threshName = compName + 'Threshold'
        pet = self.getPet()
        return pet.traits.__dict__[threshName]

    def isComponentActive(self, compName):
        return self.getComponent(compName) >= self._getComponentThreshold(compName)

    def anyActive(self, compNames):
        for comp in compNames:
            if self.isComponentActive(comp):
                return 1

        return 0

    def getDominantMood(self):
        if hasattr(self, 'dominantMood'):
            return self.dominantMood
        dominantMood = PetMood.Neutral
        priority = 1.0
        for comp in PetMood.Components:
            if comp in PetMood.DisabledDominants:
                continue
            value = self.getComponent(comp)
            pri = value / max(self._getComponentThreshold(comp), 0.01)
            if pri >= priority:
                dominantMood = comp
                priority = pri
            elif comp in PetMood.AssertiveDominants and pri >= 1.0:
                dominantMood = comp

        self.dominantMood = dominantMood
        return dominantMood

    def makeCopy(self):
        other = PetMood(self.getPet())
        for comp in PetMood.Components:
            other.__dict__[comp] = self.__dict__[comp]

        return other

    def start(self):
        pet = self.getPet()
        taskMgr.doMethodLater(simbase.petMoodDriftPeriod / simbase.petMoodTimescale * random.random(), self._driftMoodTask, self.getMoodDriftTaskName())
        self.started = 1

    def stop(self):
        if not self.started:
            return
        self.started = 0
        taskMgr.remove(self.getMoodDriftTaskName())

    def driftMood(self, dt = None, curMood = None):
        now = globalClock.getFrameTime()
        if not hasattr(self, 'lastDriftTime'):
            self.lastDriftTime = now
        if dt is None:
            dt = now - self.lastDriftTime
        self.lastDriftTime = now
        if dt <= 0.0:
            return
        if curMood is None:
            curMood = self

        def doDrift(curValue, timeToMedian, dt = float(dt)):
            newValue = curValue + dt / (timeToMedian * 7200)
            return clampScalar(newValue, 0.0, 1.0)

        self.boredom = doDrift(curMood.boredom, self.tBoredom)
        self.loneliness = doDrift(curMood.loneliness, self.tLoneliness)
        self.sadness = doDrift(curMood.sadness, self.tSadness)
        self.fatigue = doDrift(curMood.fatigue, self.tFatigue)
        self.hunger = doDrift(curMood.hunger, self.tHunger)
        self.confusion = doDrift(curMood.confusion, self.tConfusion)
        self.excitement = doDrift(curMood.excitement, self.tExcitement)
        self.surprise = doDrift(curMood.surprise, self.tSurprise)
        self.affection = doDrift(curMood.affection, self.tAffection)
        abuse = average(curMood.hunger, curMood.hunger, curMood.hunger, curMood.boredom, curMood.loneliness)
        tipPoint = 0.6
        if abuse < tipPoint:
            tAnger = lerp(self.tAngerDec, -PetMood.LONGTIME, abuse / tipPoint)
        else:
            tAnger = lerp(PetMood.LONGTIME, self.tAngerInc, (abuse - tipPoint) / (1.0 - tipPoint))
        self.anger = doDrift(curMood.anger, tAnger)
        self.announceChange()
        return

    def _driftMoodTask(self, task = None):
        self.driftMood()
        taskMgr.doMethodLater(simbase.petMoodDriftPeriod / simbase.petMoodTimescale, self._driftMoodTask, self.getMoodDriftTaskName())
        return Task.done

    def __repr__(self):
        s = '%s' % self.__class__.__name__
        for comp in PetMood.Components:
            s += '\n %s: %s' % (comp, self.__dict__[comp])

        return s
