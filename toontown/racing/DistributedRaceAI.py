from direct.distributed import DistributedObjectAI
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from otp.otpbase.PythonUtil import nonRepeatingRandomList
from toontown.racing import DistributedGagAI, DistributedProjectileAI
from direct.task import Task
import random
from toontown.racing import Racer, RaceGlobals
from direct.distributed.ClockDelta import *

class DistributedRaceAI(DistributedObjectAI.DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedRaceAI')

    def __init__(self, air, trackId, zoneId, avIds, laps, raceType, racerFinishedFunc, raceDoneFunc, circuitLoop, circuitPoints, circuitTimes, qualTimes=[], circuitTimeList={}, circuitTotalBonusTickets={}):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.trackId = trackId
        self.direction = self.trackId % 2
        self.zoneId = zoneId
        self.racers = {}
        self.avIds = []
        self.kickedAvIds = []
        self.circuitPoints = circuitPoints
        self.circuitTimes = circuitTimes
        self.finishPending = []
        self.flushPendingTask = None
        self.kickSlowRacersTask = None
        for avId in avIds:
            if avId and avId in self.air.doId2do:
                self.avIds.append(avId)
                self.racers[avId] = Racer.Racer(self, air, avId, zoneId)

        self.toonCount = len(self.racers)
        self.startingPlaces = nonRepeatingRandomList(self.toonCount, 4)
        self.thrownGags = []
        self.ready = False
        self.setGo = False
        self.racerFinishedFunc = racerFinishedFunc
        self.raceDoneFunc = raceDoneFunc
        self.lapCount = laps
        self.raceType = raceType
        if raceType == RaceGlobals.Practice:
            self.gagList = []
        else:
            self.gagList = [
             0] * len(RaceGlobals.TrackDict[trackId][4])
        self.circuitLoop = circuitLoop
        self.qualTimes = qualTimes
        self.circuitTimeList = circuitTimeList
        self.qualTimes.append(RaceGlobals.TrackDict[trackId][1])
        self.circuitTotalBonusTickets = circuitTotalBonusTickets
        return

    def generate(self):
        DistributedObjectAI.DistributedObjectAI.generate(self)
        self.notify.debug('generate %s, id=%s, ' % (self.doId, self.trackId))
        trackFilepath = RaceGlobals.TrackDict[self.trackId][0]
        taskMgr.doMethodLater(0.5, self.enableEntryBarrier, 'enableWaitingBarrier')

    def enableEntryBarrier(self, task):
        self.enterRaceBarrier = self.beginBarrier('waitingForJoin', self.avIds, 60, self.b_racersJoined)
        self.notify.debug('Waiting for Joins!!!!')
        self.sendUpdate('waitingForJoin', [])

    def removeObject(self, object):
        if object:
            self.notify.debug('deleting object: %s' % object.doId)
            object.requestDelete()

    def requestDelete(self, lastRace=True):
        self.notify.debug('requestDelete: %s' % self.doId)
        self.ignoreBarrier('waitingForExit')
        for i in self.thrownGags:
            i.requestDelete()

        del self.thrownGags
        if lastRace:
            for i in self.racers:
                racer = self.racers[i]
                self.ignore(racer.exitEvent)
                if racer.kart:
                    racer.kart.requestDelete()
                    racer.kart = None
                if racer.avatar:
                    racer.avatar.kart = None
                    racer.avatar = None

        self.racers = {}
        if self.flushPendingTask:
            taskMgr.remove(self.flushPendingTask)
            self.flushPendingTask = None
        if self.kickSlowRacersTask:
            taskMgr.remove(self.kickSlowRacersTask)
            self.kickSlowRacersTask = None
        DistributedObjectAI.DistributedObjectAI.requestDelete(self)
        return

    def delete(self):
        self.notify.debug('delete: %s' % self.doId)
        DistributedObjectAI.DistributedObjectAI.delete(self)
        del self.raceDoneFunc
        del self.racerFinishedFunc

    def getTaskZoneId(self):
        return self.zoneId

    def allToonsGone(self):
        self.notify.debug('allToonsGone')
        self.requestDelete()

    def getZoneId(self):
        return self.zoneId

    def getTrackId(self):
        return self.trackId

    def getRaceType(self):
        return self.raceType

    def getCircuitLoop(self):
        return self.circuitLoop

    def getAvatars(self):
        avIds = []
        for i in self.racers:
            avIds.append(i)

        return avIds

    def getStartingPlaces(self):
        return self.startingPlaces

    def getLapCount(self):
        return self.lapCount

    def requestKart(self):
        avId = self.air.getAvatarIdFromSender()
        if avId in self.racers:
            kart = self.racers[avId].kart
            if kart:
                kart.request('Controlled', avId)

    def b_racersJoined(self, avIds):
        self.ignoreBarrier('waitingForJoin')
        racersOut = []
        for i in self.avIds:
            if i not in avIds:
                racersOut.append(i)

        if len(avIds) == 0:
            self.exitBarrier = self.beginBarrier('waitingForExit', self.avIds, 10, self.endRace)
            for i in self.avIds:
                self.d_kickRacer(i)

            return
        for i in racersOut:
            self.d_kickRacer(i)

        self.avIds = avIds
        self.waitingForPrepBarrier = self.beginBarrier('waitingForPrep', self.avIds, 30, self.b_prepForRace)
        avAndKarts = []
        for i in self.racers:
            avAndKarts.append([self.racers[i].avId, self.racers[i].kart.doId])

        self.sendUpdate('setEnteredRacers', [avAndKarts])

    def b_prepForRace(self, avIds):
        self.notify.debug('Prepping!!!')
        self.ignoreBarrier('waitingForPrep')
        racersOut = []
        for i in self.avIds:
            if i not in avIds:
                racersOut.append(i)

        if len(avIds) == 0:
            self.exitBarrier = self.beginBarrier('waitingForExit', self.avIds, 10, self.endRace)
        for i in racersOut:
            self.d_kickRacer(i)

        if len(avIds) == 0:
            return
        self.avIds = avIds
        for i in range(len(self.gagList)):
            self.d_genGag(i)

        self.waitingForReadyBarrier = self.beginBarrier('waitingForReady', self.avIds, 20, self.b_startTutorial)
        self.sendUpdate('prepForRace', [])

    def b_startTutorial(self, avIds):
        self.ignoreBarrier('waitingForReady')
        racersOut = []
        for i in self.avIds:
            if i not in avIds:
                racersOut.append(i)

        if len(avIds) == 0:
            self.exitBarrier = self.beginBarrier('waitingForExit', self.avIds, 10, self.endRace)
        for i in racersOut:
            self.d_kickRacer(i)

        if len(avIds) == 0:
            return
        for avId in avIds:
            av = self.air.doId2do.get(avId, None)
            if not av:
                self.notify.warning('b_racersJoined: Avatar not found with id %s' % avId)
            elif not self.raceType == RaceGlobals.Practice:
                if self.isCircuit() and not self.isFirstRace():
                    continue
                raceFee = RaceGlobals.getEntryFee(self.trackId, self.raceType)
                avTickets = av.getTickets()
                if avTickets < raceFee:
                    self.notify.warning('b_racersJoined: Avatar %s does not own enough tickets for the race!')
                    av.b_setTickets(0)
                else:
                    av.b_setTickets(avTickets - raceFee)

        self.avIds = avIds
        self.readRulesBarrier = self.beginBarrier('readRules', self.avIds, 10, self.b_startRace)
        self.sendUpdate('startTutorial', [])
        return

    def b_startRace(self, avIds):
        self.ignoreBarrier('readRules')
        if self.isDeleted():
            return
        self.notify.debug('Going!!!!!!')
        self.ignoreBarrier(self.waitingForReadyBarrier)
        self.toonCount = len(self.avIds)
        self.baseTime = globalClock.getFrameTime() + 0.5 + RaceGlobals.RaceCountdown
        for i in self.racers:
            self.racers[i].baseTime = self.baseTime

        self.sendUpdate('startRace', [globalClockDelta.localToNetworkTime(self.baseTime)])
        qualTime = RaceGlobals.getQualifyingTime(self.trackId)
        timeout = qualTime + 60 + 3
        self.kickSlowRacersTask = taskMgr.doMethodLater(timeout, self.kickSlowRacers, 'kickSlowRacers')

    def kickSlowRacers(self, task):
        self.kickSlowRacersTask = None
        if self.isDeleted():
            return
        for racer in list(self.racers.values()):
            avId = racer.avId
            av = simbase.air.doId2do.get(avId, None)
            if av and not av.allowRaceTimeout:
                continue
            if not racer.finished and avId not in self.kickedAvIds:
                self.notify.info('Racer %s timed out - kicking.' % racer.avId)
                self.d_kickRacer(avId, RaceGlobals.Exit_Slow)
                self.ignore(racer.exitEvent)
                racer.exited = True
                racer.finished = True
                taskMgr.doMethodLater(10, self.removeObject, 'removeKart-%s' % racer.kart.doId, extraArgs=[racer.kart])
                taskMgr.remove('make %s invincible' % avId)
                self.racers[avId].anvilTarget = True

        self.checkForEndOfRace()
        return

    def d_kickRacer(self, avId, reason=RaceGlobals.Exit_Barrier):
        if avId not in self.kickedAvIds:
            self.kickedAvIds.append(avId)
            if self.isCircuit() and not self.isFirstRace() and reason == RaceGlobals.Exit_Barrier:
                reason = RaceGlobals.Exit_BarrierNoRefund
            self.sendUpdate('goToSpeedway', [self.kickedAvIds, reason])

    def d_genGag(self, slot):
        index = random.randint(0, 5)
        self.gagList[slot] = index
        pos = slot
        self.sendUpdate('genGag', [slot, pos, index])

    def d_dropAnvil(self, ownerId):
        possibleTargets = []
        for i in self.racers:
            if not self.racers[i].anvilTarget:
                possibleTargets.append(self.racers[i])

        while len(possibleTargets) > 1:
            if possibleTargets[0].lapT <= possibleTargets[1].lapT:
                possibleTargets = possibleTargets[1:]
            else:
                possibleTargets = possibleTargets[1:] + possibleTargets[:1]

        if len(possibleTargets):
            id = possibleTargets[0].avId
            if id != ownerId:
                possibleTargets[0].anvilTarget = True
                taskMgr.doMethodLater(4, setattr, 'make %s invincible' % id, extraArgs=[self.racers[id], 'anvilTarget', False])
            self.sendUpdate('dropAnvilOn', [ownerId, id, globalClockDelta.getFrameNetworkTime()])

    def d_makeBanana(self, avId, x, y, z):
        gag = DistributedGagAI.DistributedGagAI(simbase.air, avId, self, 3, x, y, z, 0)
        self.thrownGags.append(gag)
        gag.generateWithRequired(self.zoneId)

    def d_launchPie(self, avId):
        ownerRacer = simbase.air.doId2do.get(avId, None)
        targetId = 0
        type = 0
        targetDist = 10000
        for iiId in self.racers:
            targetRacer = simbase.air.doId2do.get(iiId, None)
            if not (targetRacer and targetRacer.kart and ownerRacer and ownerRacer.kart):
                continue
            if targetRacer.kart.getPos(ownerRacer.kart)[1] < 500 and targetRacer.kart.getPos(ownerRacer.kart)[1] >= 0 and abs(targetRacer.kart.getPos(ownerRacer.kart)[0]) < 50 and avId != iiId and targetDist > targetRacer.kart.getPos(ownerRacer.kart)[1]:
                targetId = iiId
                targetDist = targetRacer.kart.getPos(ownerRacer.kart)[1]

        if targetId == 0:
            for iiId in self.racers:
                targetRacer = simbase.air.doId2do.get(iiId, None)
                if not (targetRacer and targetRacer.kart and ownerRacer and ownerRacer.kart):
                    continue
                if targetRacer.kart.getPos(ownerRacer.kart)[1] > -80 and targetRacer.kart.getPos(ownerRacer.kart)[1] <= 0 and abs(targetRacer.kart.getPos(ownerRacer.kart)[0]) < 50 and avId != iiId:
                    targetId = iiId

        self.sendUpdate('shootPiejectile', [avId, targetId, type])
        return

    def d_makePie(self, avId, x, y, z):
        gag = DistributedProjectileAI.DistributedProjectileAI(simbase.air, self, avId)
        self.thrownGags.append(gag)
        gag.generateWithRequired(self.zoneId)

    def endRace(self, avIds):
        if hasattr(self, 'raceDoneFunc'):
            self.raceDoneFunc(self, False)

    def racerLeft(self, avIdFromClient):
        avId = self.air.getAvatarIdFromSender()
        if avId in self.racers and avId == avIdFromClient:
            self.notify.debug('Removing %d from race %d' % (avId, self.doId))
            racer = self.racers[avId]
            taskMgr.doMethodLater(10, self.removeObject, racer.kart.uniqueName('removeIt'), extraArgs=[racer.kart])
            if racer.avatar:
                racer.avatar.kart = None
            self.racers[avId].exited = True
            taskMgr.remove('make %s invincible' % id)
            self.racers[avId].anvilTarget = True
            raceDone = True
            for i in self.racers:
                if not self.racers[i].exited:
                    raceDone = False

            if raceDone:
                self.notify.debug('race over, sending callback to raceMgr')
                self.raceDoneFunc(self)
            if avId in self.finishPending:
                self.finishPending.remove(avId)
        return

    def hasGag(self, slot, type, index):
        avId = self.air.getAvatarIdFromSender()
        if avId in self.racers:
            if self.racers[avId].hasGag:
                return
            if self.gagList[slot] == index:
                self.gagList[slot] = None
                taskMgr.doMethodLater(5, self.d_genGag, 'remakeGag-' + str(slot), extraArgs=[slot])
                self.racers[avId].hasGag = True
                self.racers[avId].gagType = type
            else:
                return
        return

    def requestThrow(self, x, y, z):
        avId = self.air.getAvatarIdFromSender()
        if avId in self.racers:
            racer = self.racers[avId]
            if racer.hasGag:
                if racer.gagType == 1:
                    self.d_makeBanana(avId, x, y, z)
                if racer.gagType == 2:
                    pass
                if racer.gagType == 3:
                    self.d_dropAnvil(avId)
                if racer.gagType == 4:
                    self.d_launchPie(avId)
                racer.hasGag = False
                racer.gagType = 0

    def heresMyT(self, inputAvId, numLaps, t, timestamp):
        avId = self.air.getAvatarIdFromSender()
        if avId in self.racers and avId == inputAvId:
            me = self.racers[avId]
            me.setLapT(numLaps, t, timestamp)
            if me.maxLap == self.lapCount and not me.finished:
                me.finished = True
                taskMgr.remove('make %s invincible' % id)
                me.anvilTarget = True
                someoneIsClose = False
                for racer in list(self.racers.values()):
                    if not racer.exited and not racer.finished:
                        if me.lapT - racer.lapT < 0.15:
                            someoneIsClose = True
                            break

                index = 0
                for racer in self.finishPending:
                    if me.totalTime < racer.totalTime:
                        break
                    index += 1

                self.finishPending.insert(index, me)
                if self.flushPendingTask:
                    taskMgr.remove(self.flushPendingTask)
                    self.flushPendingTask = None
                if someoneIsClose:
                    task = taskMgr.doMethodLater(3, self.flushPending, self.uniqueName('flushPending'))
                    self.flushPendingTask = task
                else:
                    self.flushPending()
        return

    def flushPending(self, task=None):
        for racer in self.finishPending:
            self.racerFinishedFunc(self, racer)

        self.finishPending = []
        self.flushPendingTask = None
        return

    def d_setPlace(self, avId, totalTime, place, entryFee, qualify, winnings, bonus, trophies, circuitPoints, circuitTime):
        self.sendUpdate('setPlace', [avId, totalTime, place, entryFee, qualify, winnings, bonus, trophies, circuitPoints, circuitTime])

    def d_setCircuitPlace(self, avId, place, entryFee, winnings, bonus, trophies):
        self.sendUpdate('setCircuitPlace', [avId, place, entryFee, winnings, bonus, trophies])

    def d_endCircuitRace(self):
        self.sendUpdate('endCircuitRace')

    def unexpectedExit(self, avId):
        self.notify.debug('racer disconnected: %s' % avId)
        racer = self.racers.get(avId, None)
        if racer:
            self.sendUpdate('racerDisconnected', [avId])
            self.ignore(racer.exitEvent)
            racer.exited = True
            taskMgr.doMethodLater(10, self.removeObject, 'removeKart-%s' % racer.kart.doId, extraArgs=[racer.kart])
            taskMgr.remove('make %s invincible' % id)
            self.racers[avId].anvilTarget = True
            self.checkForEndOfRace()
        return

    def checkForEndOfRace(self):
        if self.isCircuit() and self.everyoneDone():
            simbase.air.raceMgr.endCircuitRace(self)
        raceOver = True
        for i in self.racers:
            if not self.racers[i].exited:
                raceOver = False

        if raceOver:
            self.raceDoneFunc(self)

    def sendToonsToNextCircuitRace(self, raceZone, trackId):
        for avId in self.avIds:
            self.notify.debug('Handling Circuit Race transisiton for avatar %s' % avId)
            self.sendUpdateToAvatarId(avId, 'setRaceZone', [raceZone, trackId])

    def isCircuit(self):
        return self.raceType == RaceGlobals.Circuit

    def isLastRace(self):
        return len(self.circuitLoop) == 0

    def isFirstRace(self):
        return len(self.circuitLoop) == 2

    def everyoneDone(self):
        done = True
        for racer in list(self.racers.values()):
            if not racer.exited and racer.avId not in self.playersFinished and racer.avId not in self.kickedAvIds:
                done = False
                break

        return done
