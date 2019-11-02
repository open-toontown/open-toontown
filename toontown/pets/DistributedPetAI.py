from pandac.PandaModules import *
from direct.showbase.PythonUtil import weightedChoice, randFloat, lerp
from direct.showbase.PythonUtil import contains, list2dict, clampScalar
from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedSmoothNodeAI
from direct.distributed import DistributedSmoothNodeBase
from direct.distributed import ClockDelta
from direct.fsm import ClassicFSM, State
from direct.interval.IntervalGlobal import *
from toontown.toonbase import ToontownGlobals
from direct.task import Task
from otp.movement import Mover
from toontown.pets import PetChase, PetFlee, PetWander, PetLeash
from toontown.pets import PetCollider, PetSphere, PetLookerAI
from toontown.pets import PetConstants, PetDNA, PetTraits
from toontown.pets import PetObserve, PetBrain, PetMood
from toontown.pets import PetActionFSM, PetBase, PetGoal, PetTricks
from direct.fsm import FSM
from toontown.toon import DistributedToonAI
from toontown.ai import ServerEventBuffer
import random
import time
import string
import copy
from direct.showbase.PythonUtil import StackTrace

class DistributedPetAI(DistributedSmoothNodeAI.DistributedSmoothNodeAI, PetLookerAI.PetLookerAI, PetBase.PetBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPetAI')
    movieTimeSwitch = {PetConstants.PET_MOVIE_FEED: PetConstants.FEED_TIME,
     PetConstants.PET_MOVIE_SCRATCH: PetConstants.SCRATCH_TIME,
     PetConstants.PET_MOVIE_CALL: PetConstants.CALL_TIME}
    movieDistSwitch = {PetConstants.PET_MOVIE_FEED: PetConstants.FEED_DIST.get,
     PetConstants.PET_MOVIE_SCRATCH: PetConstants.SCRATCH_DIST.get}

    def __init__(self, air, dna = None):
        DistributedSmoothNodeAI.DistributedSmoothNodeAI.__init__(self, air)
        PetLookerAI.PetLookerAI.__init__(self)
        self.ownerId = 0
        self.petName = 'unnamed'
        self.traitSeed = 0
        self.safeZone = ToontownGlobals.ToontownCentral
        self.initialDNA = dna
        self.active = 1
        self.activated = 0
        self._outOfBounds = False
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
        self.movieMode = None
        self.lockMoverEnabled = 0
        self.trickAptitudes = []
        self.inEstate = 0
        self.estateOwnerId = None
        self.estateZones = []
        self.lastSeenTimestamp = self.getCurEpochTimestamp()
        self.requiredMoodComponents = {}
        self.__funcsToDelete = []
        self.__generateDistTraitFuncs()
        self.__generateDistMoodFuncs()
        self.busy = 0
        self.gaitFSM = ClassicFSM.ClassicFSM('petGaitFSM', [State.State('off', self.gaitEnterOff, self.gaitExitOff),
         State.State('neutral', self.gaitEnterNeutral, self.gaitExitNeutral),
         State.State('happy', self.gaitEnterHappy, self.gaitExitHappy),
         State.State('sad', self.gaitEnterSad, self.gaitExitSad)], 'off', 'off')
        self.gaitFSM.enterInitialState()
        self.unstickFSM = ClassicFSM.ClassicFSM('unstickFSM', [State.State('off', self.unstickEnterOff, self.unstickExitOff), State.State('on', self.unstickEnterOn, self.unstickExitOn)], 'off', 'off')
        self.unstickFSM.enterInitialState()
        if __dev__:
            self.pscMoveResc = PStatCollector('App:Show code:petMove:Reschedule')
        return

    def setInactive(self):
        self.active = 0

    def _initDBVals(self, ownerId, name = None, traitSeed = 0, dna = None, safeZone = ToontownGlobals.ToontownCentral):
        self.b_setOwnerId(ownerId)
        if name is None:
            name = 'pet%s' % self.doId
        self.b_setPetName(name)
        self.b_setTraitSeed(traitSeed)
        self.b_setSafeZone(safeZone)
        traits = PetTraits.PetTraits(traitSeed, safeZone)
        for traitName in PetTraits.getTraitNames():
            setter = self.getSetterName(traitName, 'b_set')
            self.__dict__[setter](traits.getTraitValue(traitName))

        self.traits = traits
        for component in PetMood.PetMood.Components:
            setterName = self.getSetterName(component, 'b_set')
            self.__dict__[setterName](0.0)

        if not dna:
            dna = PetDNA.getRandomPetDNA()
        self.setDNA(dna)
        self.b_setLastSeenTimestamp(self.getCurEpochTimestamp())
        for component in PetMood.PetMood.Components:
            self.setMoodComponent(component, 0.0)

        self.b_setTrickAptitudes([])
        return

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

    def handleZoneChange(self, newZoneId, oldZoneId):
        DistributedSmoothNodeAI.DistributedSmoothNodeAI.handleZoneChange(self, newZoneId, oldZoneId)
        self.ignore(PetObserve.getEventName(oldZoneId))
        self.accept(PetObserve.getEventName(newZoneId), self.brain.observe)

    def handleLogicalZoneChange(self, newZoneId, oldZoneId):
        DistributedSmoothNodeAI.DistributedSmoothNodeAI.handleLogicalZoneChange(self, newZoneId, oldZoneId)
        self.announceZoneChange(newZoneId, oldZoneId)
        self.destroySphereImpulse()
        self.createSphereImpulse()

    def announceZoneChange(self, newZoneId, oldZoneId):
        DistributedPetAI.notify.debug('%s.announceZoneChange: %s->%s' % (self.doId, oldZoneId, newZoneId))
        broadcastZones = list2dict([newZoneId, oldZoneId])
        self.estateOwnerId = simbase.air.estateMgr.getOwnerFromZone(newZoneId)
        if self.estateOwnerId:
            if __dev__:
                pass
            self.inEstate = 1
            self.estateZones = simbase.air.estateMgr.getEstateZones(self.estateOwnerId)
        else:
            self.inEstate = 0
            self.estateZones = []
        PetObserve.send(broadcastZones.keys(), PetObserve.PetActionObserve(PetObserve.Actions.CHANGE_ZONE, self.doId, (oldZoneId, newZoneId)))

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
        DistributedSmoothNodeAI.DistributedSmoothNodeAI.setName(self, self.petName)

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

    def getPetName(self):
        return self.petName

    def b_setPetName(self, petName):
        self.d_setPetName(petName)
        self.setPetName(petName)

    def d_setPetName(self, petName):
        self.sendUpdate('setPetName', [petName])

    def setPetName(self, petName):
        self.petName = petName
        DistributedSmoothNodeAI.DistributedSmoothNodeAI.setName(self, self.petName)

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

    def teleportIn(self, timestamp = None):
        self.notify.debug('DPAI: teleportIn')
        timestamp = ClockDelta.globalClockDelta.getRealNetworkTime()
        self.notify.debug('DPAI: sending update @ ts = %s' % timestamp)
        self.sendUpdate('teleportIn', [timestamp])
        return None

    def teleportOut(self, timestamp = None):
        self.notify.debug('DPAI: teleportOut')
        timestamp = ClockDelta.globalClockDelta.getRealNetworkTime()
        self.notify.debug('DPAI: sending update @ ts = %s' % timestamp)
        self.sendUpdate('teleportOut', [timestamp])
        return None

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
            DistributedPetAI.notify.debug('setTrickAptitudes: %s' % aptitudes)
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
        DistributedSmoothNodeAI.DistributedSmoothNodeAI.generate(self)
        self._hasCleanedUp = False
        self.setHasRequestedDelete(False)
        self.b_setParent(ToontownGlobals.SPHidden)
        self.lockedDown = 0
        self.leashMode = 0
        self.leashAvId = None
        self.leashGoal = None
        self.trickLogger = ServerEventBuffer.ServerEventMultiAccumulator(self.air, 'petTricksPerformed', self.doId)
        self.trickFailLogger = ServerEventBuffer.ServerEventMultiAccumulator(self.air, 'petTricksFailed', self.doId)
        self.feedLogger = ServerEventBuffer.ServerEventAccumulator(self.air, 'petFeedings', self.doId)
        self.scratchLogger = ServerEventBuffer.ServerEventAccumulator(self.air, 'petScratchings', self.doId)
        self.traits = PetTraits.PetTraits(self.traitSeed, self.safeZone)
        if not hasattr(self, '_beingCreatedInDB'):
            for i in xrange(len(self.traitList)):
                value = self.traitList[i]
                if value == 0.0:
                    traitName = PetTraits.getTraitNames()[i]
                    traitValue = self.traits.getTraitValue(traitName)
                    DistributedPetAI.notify.info("%s: initializing new trait '%s' to %s, seed=%s" % (self.doId,
                     traitName,
                     traitValue,
                     self.traitSeed))
                    setterName = self.getSetterName(traitName, 'b_set')
                    self.__dict__[setterName](traitValue)

        self.mood = PetMood.PetMood(self)
        if not self.active:
            return
        self.activated = 1
        self.announceZoneChange(self.zoneId, ToontownGlobals.QuietZone)
        self.b_setParent(ToontownGlobals.SPRender)
        self.setPos(randFloat(-20, 20), randFloat(-20, 20), 0)
        self.setH(randFloat(360))
        if self.initialDNA:
            self.setDNA(self.initialDNA)
        for mood, value in self.requiredMoodComponents.items():
            self.mood.setComponent(mood, value, announce=0)

        self.requiredMoodComponents = {}
        self.brain = PetBrain.PetBrain(self)
        self.mover = Mover.Mover(self)
        self.lockMover = Mover.Mover(self)
        self.createImpulses()
        self.enterPetLook()
        self.actionFSM = PetActionFSM.PetActionFSM(self)
        self.teleportIn()
        self.handleMoodChange(distribute=0)
        taskMgr.doMethodLater(simbase.petMovePeriod * random.random(), self.move, self.getMoveTaskName())
        self.startPosHprBroadcast()
        self.accept(PetObserve.getEventName(self.zoneId), self.brain.observe)
        self.accept(self.mood.getMoodChangeEvent(), self.handleMoodChange)
        self.mood.start()
        self.brain.start()
        return

    def _isPet(self):
        return 1

    def setHasRequestedDelete(self, flag):
        self._requestedDeleteFlag = flag

    def hasRequestedDelete(self):
        return self._requestedDeleteFlag

    def requestDelete(self, task = None):
        DistributedPetAI.notify.info('PetAI.requestDelete: %s, owner=%s' % (self.doId, self.ownerId))
        if self.hasRequestedDelete():
            DistributedPetAI.notify.info('PetAI.requestDelete: %s, owner=%s returning immediately' % (self.doId, self.ownerId))
            return
        self.setHasRequestedDelete(True)
        self.b_setLastSeenTimestamp(self.getCurEpochTimestamp())
        DistributedSmoothNodeAI.DistributedSmoothNodeAI.requestDelete(self)

    def _doDeleteCleanup(self):
        self.trickLogger.destroy()
        self.trickFailLogger.destroy()
        self.feedLogger.destroy()
        self.scratchLogger.destroy()
        del self.trickLogger
        del self.trickFailLogger
        del self.feedLogger
        del self.scratchLogger
        taskMgr.remove(self.uniqueName('clearMovie'))
        taskMgr.remove(self.uniqueName('PetMovieWait'))
        taskMgr.remove(self.uniqueName('PetMovieClear'))
        taskMgr.remove(self.uniqueName('PetMovieComplete'))
        taskMgr.remove(self.getLockMoveTaskName())
        taskMgr.remove(self.getMoveTaskName())
        if hasattr(self, 'zoneId'):
            self.announceZoneChange(ToontownGlobals.QuietZone, self.zoneId)
        else:
            myDoId = 'No doId'
            myTaskName = 'No task name'
            myStackTrace = StackTrace().trace
            myOldStackTrace = 'No Trace'
            if hasattr(self, 'doId'):
                myDoId = self.doId
            if task:
                myTaskName = task.name
            if hasattr(self, 'destroyDoStackTrace'):
                myOldStackTrace = self.destroyDoStackTrace.trace
            simbase.air.writeServerEvent('Pet RequestDelete duplicate', myDoId, 'from task %s' % myTaskName)
            simbase.air.writeServerEvent('Pet RequestDelete duplicate StackTrace', myDoId, '%s' % myStackTrace)
            simbase.air.writeServerEvent('Pet RequestDelete duplicate OldStackTrace', myDoId, '%s' % myOldStackTrace)
            DistributedPetAI.notify.warning('double requestDelete from task %s' % myTaskName)
        self.setParent(ToontownGlobals.SPHidden)
        if hasattr(self, 'activated'):
            if self.activated:
                self.activated = 0
                self.brain.destroy()
                del self.brain
                self.actionFSM.destroy()
                del self.actionFSM
                self.exitPetLook()
                self.destroyImpulses()
                self.mover.destroy()
                del self.mover
                self.lockMover.destroy()
                del self.lockMover
                self.stopPosHprBroadcast()
        if hasattr(self, 'mood'):
            self.mood.destroy()
            del self.mood
        if hasattr(self, 'traits'):
            del self.traits
        try:
            for funcName in self.__funcsToDelete:
                del self.__dict__[funcName]

        except:
            pass

        if hasattr(self, 'gaitFSM'):
            if self.gaitFSM:
                self.gaitFSM.requestFinalState()
            del self.gaitFSM
        if hasattr(self, 'unstickFSM'):
            if self.unstickFSM:
                self.unstickFSM.requestFinalState()
            del self.unstickFSM
        if __dev__:
            del self.pscMoveResc
        PetLookerAI.PetLookerAI.destroy(self)
        self.ignoreAll()
        self._hasCleanedUp = True

    def delete(self):
        DistributedPetAI.notify.info('PetAI.delete: %s, owner=%s' % (self.doId, self.ownerId))
        if not self._hasCleanedUp:
            self._doDeleteCleanup()
        self.setHasRequestedDelete(False)
        DistributedSmoothNodeAI.DistributedSmoothNodeAI.delete(self)

    def patchDelete(self):
        for funcName in self.__funcsToDelete:
            del self.__dict__[funcName]

        del self.gaitFSM
        del self.unstickFSM
        if __dev__:
            del self.pscMoveResc
        PetLookerAI.PetLookerAI.destroy(self)
        self.doNotDeallocateChannel = True
        self.zoneId = None
        DistributedSmoothNodeAI.DistributedSmoothNodeAI.delete(self)
        self.ignoreAll()
        return

    def createImpulses(self):
        self.createSphereImpulse()
        self.chaseImpulse = CPetChase()
        self.fleeImpulse = CPetFlee()
        self.wanderImpulse = PetWander.PetWander()
        self.lockChaseImpulse = CPetChase()

    def destroyImpulses(self):
        self.wanderImpulse.destroy()
        del self.chaseImpulse
        del self.fleeImpulse
        del self.wanderImpulse
        self.destroySphereImpulse()
        del self.lockChaseImpulse

    def createSphereImpulse(self):
        petRadius = 1.0
        collTrav = self.getCollTrav()
        if collTrav is None:
            DistributedPetAI.notify.warning('no collision traverser for zone %s' % self.zoneId)
        else:
            self.sphereImpulse = PetSphere.PetSphere(petRadius, collTrav)
            self.mover.addImpulse('sphere', self.sphereImpulse)
        return

    def destroySphereImpulse(self):
        self.mover.removeImpulse('sphere')
        if hasattr(self, 'sphereImpulse'):
            self.sphereImpulse.destroy()
            del self.sphereImpulse

    def getMoveTaskName(self):
        return 'petMove-%s' % self.doId

    def getLockMoveTaskName(self):
        return 'petLockMove-%s' % self.doId

    def move(self, task = None):
        if self.isEmpty():
            try:
                self.air.writeServerEvent('Late Pet Move Call', self.doId, ' ')
            except:
                pass

            taskMgr.remove(task.name)
            return Task.done
        if not self.isLockMoverEnabled():
            self.mover.move()
        numNearby = len(self.brain.nearbyAvs) - 1
        minNearby = 5
        if numNearby > minNearby:
            delay = 0.08 * (numNearby - minNearby)
            self.setPosHprBroadcastPeriod(PetConstants.PosBroadcastPeriod + lerp(delay * 0.75, delay, random.random()))
        maxDist = 1000
        if abs(self.getX()) > maxDist or abs(self.getY()) > maxDist:
            DistributedPetAI.notify.warning('deleting pet %s before he wanders off too far' % self.doId)
            self._outOfBounds = True
            self.stopPosHprBroadcast()
            self.requestDelete()
            return Task.done
        if __dev__:
            self.pscMoveResc.start()
        taskMgr.doMethodLater(simbase.petMovePeriod, self.move, self.getMoveTaskName())
        if __dev__:
            self.pscMoveResc.stop()
        return Task.done

    def startPosHprBroadcast(self):
        if self._outOfBounds:
            return
        DistributedSmoothNodeAI.DistributedSmoothNodeAI.startPosHprBroadcast(self, period=simbase.petPosBroadcastPeriod, type=DistributedSmoothNodeBase.DistributedSmoothNodeBase.BroadcastTypes.XYH)

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

        if self.isExcited():
            self.gaitFSM.request('happy')
        elif self.isSad():
            self.gaitFSM.request('sad')
        else:
            self.gaitFSM.request('neutral')

    def isContented(self):
        return self.mood.getDominantMood() in PetMood.PetMood.ContentedMoods

    def call(self, avatar):
        self.brain.observe(PetObserve.PetPhraseObserve(PetObserve.Phrases.COME, avatar.doId))
        self.__petMovieStart(avatar.doId)

    def feed(self, avatar):
        if avatar.takeMoney(PetConstants.FEED_AMOUNT):
            self.startLockPetMove(avatar.doId)
            self.brain.observe(PetObserve.PetActionObserve(PetObserve.Actions.FEED, avatar.doId))
            self.feedLogger.addEvent()

    def scratch(self, avatar):
        self.startLockPetMove(avatar.doId)
        self.brain.observe(PetObserve.PetActionObserve(PetObserve.Actions.SCRATCH, avatar.doId))
        self.scratchLogger.addEvent()

    def lockPet(self):
        DistributedPetAI.notify.debug('%s: lockPet' % self.doId)
        if not self.lockedDown:
            self.stopPosHprBroadcast()
        self.lockedDown += 1

    def isLockedDown(self):
        return self.lockedDown != 0

    def unlockPet(self):
        DistributedPetAI.notify.debug('%s: unlockPet' % self.doId)
        if self.lockedDown <= 0:
            DistributedPetAI.notify.warning('%s: unlockPet called on unlocked pet' % self.doId)
        else:
            self.lockedDown -= 1
            if not self.lockedDown and not self.isDeleted():
                self.startPosHprBroadcast()

    def handleStay(self, avatar):
        self.brain.observe(PetObserve.PetPhraseObserve(PetObserve.Phrases.STAY, avatar.doId))

    def handleShoo(self, avatar):
        self.brain.observe(PetObserve.PetPhraseObserve(PetObserve.Phrases.GO_AWAY, avatar.doId))

    def gaitEnterOff(self):
        pass

    def gaitExitOff(self):
        pass

    def gaitEnterNeutral(self):
        self.mover.setFwdSpeed(PetConstants.FwdSpeed)
        self.mover.setRotSpeed(PetConstants.RotSpeed)

    def gaitExitNeutral(self):
        pass

    def gaitEnterHappy(self):
        self.mover.setFwdSpeed(PetConstants.HappyFwdSpeed)
        self.mover.setRotSpeed(PetConstants.HappyRotSpeed)

    def gaitExitHappy(self):
        pass

    def gaitEnterSad(self):
        self.mover.setFwdSpeed(PetConstants.SadFwdSpeed)
        self.mover.setRotSpeed(PetConstants.SadRotSpeed)

    def gaitExitSad(self):
        pass

    def unstickEnterOff(self):
        pass

    def unstickExitOff(self):
        pass

    def unstickEnterOn(self):
        self._collisionTimestamps = []
        self.accept(self.mover.getCollisionEventName(), self._handleCollided)

    def _handleCollided(self, collEntry):
        now = globalClock.getFrameTime()
        self._collisionTimestamps.append(now)
        while now - self._collisionTimestamps[0] > PetConstants.UnstickSampleWindow:
            del self._collisionTimestamps[0:1]

        if len(self._collisionTimestamps) > PetConstants.UnstickCollisionThreshold:
            self._collisionTimestamps = []
            DistributedPetAI.notify.debug('unsticking pet %s' % self.doId)
            self.brain._unstick()

    def unstickExitOn(self):
        pass

    def ownerIsOnline(self):
        return self.ownerId in simbase.air.doId2do

    def ownerIsInSameZone(self):
        if not self.ownerIsOnline():
            return 0
        return self.zoneId == simbase.air.doId2do[self.ownerId].zoneId

    def _getOwnerDict(self):
        if self.owner is not None:
            if self.ownerIsInSameZone():
                return {self.ownerId: self.owner}
        return {}

    def _getFullNearbyToonDict(self):
        toons = self.air.getObjectsOfClassInZone(self.air.districtId, self.zoneId, DistributedToonAI.DistributedToonAI)
        return toons

    def _getNearbyToonDict(self):
        toons = self._getFullNearbyToonDict()
        if self.ownerId in toons:
            del toons[self.ownerId]
        return toons

    def _getNearbyPetDict(self):
        pets = self.air.getObjectsOfClassInZone(self.air.districtId, self.zoneId, DistributedPetAI)
        if self.doId in pets:
            del pets[self.doId]
        return pets

    def _getNearbyAvatarDict(self):
        avs = self._getFullNearbyToonDict()
        avs.update(self._getNearbyPetDict())
        return avs

    def _getOwner(self):
        return self.air.doId2do.get(self.ownerId)

    def _getNearbyToon(self):
        nearbyToonDict = self._getFullNearbyToonDict()
        if not len(nearbyToonDict):
            return None
        return nearbyToonDict[random.choice(nearbyToonDict.keys())]

    def _getNearbyToonNonOwner(self):
        nearbyToonDict = self._getNearbyToonDict()
        if not len(nearbyToonDict):
            return None
        return nearbyToonDict[random.choice(nearbyToonDict.keys())]

    def _getNearbyPet(self):
        nearbyPetDict = self._getNearbyPetDict()
        if not len(nearbyPetDict):
            return None
        return nearbyPetDict[random.choice(nearbyPetDict.keys())]

    def _getNearbyAvatar(self):
        nearbyAvDict = self._getNearbyAvatarDict()
        if not len(nearbyAvDict):
            return None
        return nearbyAvDict[random.choice(nearbyAvDict.keys())]

    def isBusy(self):
        return self.busy > 0

    def freeAvatar(self, avId):
        self.sendUpdateToAvatarId(avId, 'freeAvatar', [])

    def avatarInteract(self, avId):
        av = self.air.doId2do.get(avId)
        if av is None:
            self.notify.warning('Avatar: %s not found' % avId)
            return 0
        if self.isBusy():
            self.notify.debug('freeing avatar!')
            self.freeAvatar(avId)
            return 0
        self.busy = avId
        self.notify.debug('sending update')
        self.sendUpdateToAvatarId(avId, 'avatarInteract', [avId])
        self.acceptOnce(self.air.getAvatarExitEvent(avId), self.__handleUnexpectedExit, extraArgs=[avId])
        return 1

    def rejectAvatar(self, avId):
        self.notify.error('rejectAvatar: should not be called by a pet!')

    def d_setMovie(self, avId, flag):
        self.sendUpdate('setMovie', [flag, avId, ClockDelta.globalClockDelta.getRealNetworkTime()])

    def sendClearMovie(self, task = None):
        if self.air != None:
            self.ignore(self.air.getAvatarExitEvent(self.busy))
        taskMgr.remove(self.uniqueName('clearMovie'))
        self.busy = 0
        self.d_setMovie(0, PetConstants.PET_MOVIE_CLEAR)
        return Task.done

    def __handleUnexpectedExit(self, avId):
        self.notify.warning('avatar:' + str(avId) + ' has exited unexpectedly')
        self.notify.warning('not busy with avId: %s, busy: %s ' % (avId, self.busy))
        taskMgr.remove(self.uniqueName('clearMovie'))
        self.sendClearMovie()

    def handleAvPetInteraction(self, mode, avId):
        if mode not in (PetConstants.PET_MOVIE_SCRATCH, PetConstants.PET_MOVIE_FEED, PetConstants.PET_MOVIE_CALL):
            self.air.writeServerEvent('suspicious', avId, 'DistributedPetAI: unknown mode: %s' % mode)
            return
        if self.avatarInteract(avId):
            self.notify.debug('handleAvPetInteraction() avatarInteract calling callback')
            self.movieMode = mode
            callback = {PetConstants.PET_MOVIE_SCRATCH: self.scratch,
             PetConstants.PET_MOVIE_FEED: self.feed,
             PetConstants.PET_MOVIE_CALL: self.call}.get(mode)
            callback(self.air.doId2do.get(avId))
        else:
            self.notify.debug('handleAvPetInteraction() avatarInteract was busy or unhappy')

    def __petMovieStart(self, avId):
        self.d_setMovie(avId, self.movieMode)
        time = self.movieTimeSwitch.get(self.movieMode)
        taskMgr.doMethodLater(time, self.__petMovieComplete, self.uniqueName('PetMovieComplete'))

    def __petMovieComplete(self, task = None):
        self.disableLockMover()
        self.unlockPet()
        self.sendClearMovie()
        self.movieMode = None
        return Task.done

    def startLockPetMove(self, avId):
        self.enableLockMover()
        self.lockChaseImpulse.setTarget(self.air.doId2do.get(avId))
        self.lockMover.addImpulse('LockTarget', self.lockChaseImpulse)
        self.lockMover.setFwdSpeed(self.mover.getFwdSpeed())
        self.lockMover.setRotSpeed(self.mover.getRotSpeed())
        dist_Callable = self.movieDistSwitch.get(self.movieMode)
        dist = dist_Callable(self.air.doId2do.get(avId).getStyle().getLegSize())
        self.lockChaseImpulse.setMinDist(dist)
        self.distList = [0, 0, 0]
        self.__lockPetMoveTask(avId)

    def getAverageDist(self):
        sum = 0
        for i in self.distList:
            sum += i

        return sum / 3.0

    def __lockPetMoveTask(self, avId):
        if not hasattr(self, 'air') or not self.air.doId2do.has_key(avId):
            self.notify.warning('avId: %s gone or self deleted!' % avId)
            return Task.done
        av = self.air.doId2do.get(avId)
        dist = av.getDistance(self)
        self.distList.append(dist)
        if len(self.distList) > 3:
            self.distList.pop(0)
        if self.movieDistSwitch.has_key(self.movieMode):
            dist_Callable = self.movieDistSwitch.get(self.movieMode)
            movieDist = dist_Callable(av.getStyle().getLegSize())
        else:
            self.notify.warning('movieMode: %s not in movieSwitchDist map!' % self.movieMode)
            return Task.done
        avgDist = self.getAverageDist()
        if dist - movieDist > 0.25 and abs(avgDist - dist) > 0.1:
            self.lockMover.move()
            taskMgr.doMethodLater(simbase.petMovePeriod, self.__lockPetMoveTask, self.getLockMoveTaskName(), [avId])
        else:
            self.endLockPetMove(avId)
        return Task.done

    def endLockPetMove(self, avId):
        del self.distList
        taskMgr.remove(self.getLockMoveTaskName())
        self.lockPet()
        self.lockMover.removeImpulse('LockTarget')
        self.__petMovieStart(avId)

    def enableLockMover(self):
        if self.lockMoverEnabled == 0:
            self.brain._startMovie()
        self.lockMoverEnabled += 1

    def isLockMoverEnabled(self):
        return self.lockMoverEnabled > 0

    def disableLockMover(self):
        if self.lockMoverEnabled > 0:
            self.lockMoverEnabled -= 1
            if self.lockMoverEnabled == 0:
                self.brain._endMovie()

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
        DistributedPetAI.notify.debug('_willDoTrick: %s / %s' % (randVal, cutoff))
        return randVal < cutoff

    def _handleDidTrick(self, trickId):
        DistributedPetAI.notify.debug('_handleDidTrick: %s' % trickId)
        if trickId == PetTricks.Tricks.BALK:
            return
        aptitude = self.getTrickAptitude(trickId)
        self.setTrickAptitude(trickId, aptitude + PetTricks.AptitudeIncrementDidTrick)
        self.addToMood('fatigue', lerp(PetTricks.MaxTrickFatigue, PetTricks.MinTrickFatigue, aptitude))
        self.trickLogger.addEvent(trickId)

    def _handleGotPositiveTrickFeedback(self, trickId, magnitude):
        if trickId == PetTricks.Tricks.BALK:
            return
        self.setTrickAptitude(trickId, self.getTrickAptitude(trickId) + PetTricks.MaxAptitudeIncrementGotPraise * magnitude)

    def toggleLeash(self, avId):
        if self.leashMode:
            self.leashMode = 0
            self.leashAvId = None
            self.brain.goalMgr.removeGoal(self.leashGoal)
            del self.leashGoal
            response = 'leash OFF'
        else:
            self.leashMode = 1
            self.leashAvId = avId
            self.leashGoal = PetGoal.ChaseAvatarLeash(avId)
            self.brain.goalMgr.addGoal(self.leashGoal)
            response = 'leash ON'
        return response
