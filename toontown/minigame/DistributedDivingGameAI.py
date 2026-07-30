from .DistributedMinigameAI import *
from direct.distributed.ClockDelta import *
from direct.interval.IntervalGlobal import *
from direct.fsm import ClassicFSM
from direct.fsm import State
from direct.actor import Actor
from . import DivingGameGlobals
import random
import random
import types

class DistributedDivingGameAI(DistributedMinigameAI):
    fishProportions = []
    for i in range(6):
        fishProportions.append([])

    n = 100
    fishProportions[0]
    fishProportions[0].append(([0, 0.8],
     [0.8, 0.9],
     [0.9, 1],
     [n, n],
     [n, n],
     [n, n]))
    fishProportions[0].append(([0, 0.8],
     [0.8, 1],
     [n, n],
     [n, n],
     [n, n],
     [n, n]))
    fishProportions[0].append(([0, 0.7],
     [0.7, 1],
     [n, n],
     [n, n],
     [n, n],
     [n, n]))
    fishProportions[0].append(([0, 0.7],
     [0.7, 0.9],
     [0.9, 1],
     [n, n],
     [n, n],
     [n, n]))
    fishProportions[0].append(([0, 0.5],
     [0.5, 1],
     [n, n],
     [n, n],
     [n, n],
     [n, n]))
    fishProportions[0].append(([n, 0.5],
     [0.5, 1],
     [n, n],
     [n, n],
     [n, n],
     [n, n]))
    fishProportions[1]
    fishProportions[1].append(([0, 0.8],
     [0.8, 0.9],
     [0.9, 1],
     [n, n],
     [n, n],
     [n, n]))
    fishProportions[1].append(([0, 0.8],
     [0.8, 1],
     [n, n],
     [n, n],
     [n, n],
     [n, n]))
    fishProportions[1].append(([0, 0.7],
     [0.7, 1],
     [n, n],
     [n, n],
     [n, n],
     [n, n]))
    fishProportions[1].append(([0, 0.7],
     [0.7, 0.9],
     [n, n],
     [n, n],
     [n, n],
     [0.9, 1]))
    fishProportions[1].append(([0, 0.4],
     [0.4, 0.8],
     [n, n],
     [n, n],
     [n, n],
     [0.8, 1]))
    fishProportions[1].append(([n, 0.3],
     [0.3, 0.6],
     [n, n],
     [n, n],
     [n, n],
     [0.6, 1]))
    fishProportions[2]
    fishProportions[2].append(([0, 0.7],
     [0.7, 0.9],
     [0.9, 1],
     [n, n],
     [n, n],
     [n, n]))
    fishProportions[2].append(([0, 0.6],
     [0.6, 1],
     [n, n],
     [n, n],
     [n, n],
     [n, n]))
    fishProportions[2].append(([0, 0.6],
     [0.6, 0.8],
     [n, n],
     [0.8, 1],
     [n, n],
     [n, n]))
    fishProportions[2].append(([0, 0.5],
     [0.5, 0.7],
     [n, n],
     [0.7, 0.9],
     [n, n],
     [0.9, 1]))
    fishProportions[2].append(([0, 0.2],
     [0.2, 0.4],
     [n, n],
     [0.4, 0.75],
     [n, n],
     [0.75, 1]))
    fishProportions[2].append(([n, 0.2],
     [0.2, 0.6],
     [n, n],
     [0.6, 0.8],
     [n, n],
     [0.8, 1]))
    fishProportions[3]
    fishProportions[3].append(([0, 0.7],
     [0.7, 0.9],
     [0.9, 1],
     [n, n],
     [n, n],
     [n, n]))
    fishProportions[3].append(([0, 0.6],
     [0.6, 1],
     [n, n],
     [n, n],
     [n, n],
     [n, n]))
    fishProportions[3].append(([0, 0.6],
     [0.6, 0.8],
     [n, n],
     [0.95, 1],
     [n, n],
     [n, n]))
    fishProportions[3].append(([0, 0.5],
     [0.5, 0.7],
     [n, n],
     [0.7, 0.85],
     [0.9, 0.95],
     [0.95, 1]))
    fishProportions[3].append(([0, 0.2],
     [0.2, 0.4],
     [n, n],
     [0.4, 0.75],
     [0.75, 0.85],
     [0.85, 1]))
    fishProportions[3].append(([n, 0.2],
     [0.2, 0.6],
     [n, n],
     [0.6, 0.8],
     [n, n],
     [0.8, 1]))
    fishProportions[4]
    fishProportions[4].append(([0, 0.7],
     [0.7, 0.9],
     [0.9, 1],
     [n, n],
     [n, n],
     [n, n]))
    fishProportions[4].append(([0, 0.45],
     [0.45, 0.9],
     [n, n],
     [0.9, 1],
     [n, n],
     [n, n]))
    fishProportions[4].append(([0, 0.2],
     [0.2, 0.5],
     [n, n],
     [0.5, 0.95],
     [0.95, 1],
     [n, n]))
    fishProportions[4].append(([0, 0.1],
     [0.1, 0.3],
     [n, n],
     [0.3, 0.75],
     [0.75, 0.8],
     [0.8, 1]))
    fishProportions[4].append(([n, n],
     [0, 0.15],
     [n, n],
     [0.15, 0.4],
     [n, n],
     [0.4, 1]))
    fishProportions[4].append(([n, n],
     [n, n],
     [n, n],
     [0, 0.4],
     [n, n],
     [0.6, 1]))
    fishProportions[5]
    fishProportions[5].append(([0, 0.7],
     [0.7, 0.9],
     [0.9, 1],
     [n, n],
     [n, n],
     [n, n]))
    fishProportions[5].append(([0, 0.45],
     [0.45, 0.9],
     [n, n],
     [0.9, 1],
     [n, n],
     [n, n]))
    fishProportions[5].append(([0, 0.2],
     [0.2, 0.5],
     [n, n],
     [0.5, 0.95],
     [0.95, 1],
     [n, n]))
    fishProportions[5].append(([0, 0.1],
     [0.1, 0.3],
     [n, n],
     [0.3, 0.75],
     [0.75, 0.8],
     [0.8, 1]))
    fishProportions[5].append(([n, n],
     [0, 0.15],
     [n, n],
     [0.15, 0.4],
     [n, n],
     [0.4, 1]))
    fishProportions[5].append(([n, n],
     [n, n],
     [n, n],
     [0, 0.4],
     [n, n],
     [0.6, 1]))
    difficultyPatternsAI = {ToontownGlobals.ToontownCentral: [3.5, fishProportions[0], 1.5],
     ToontownGlobals.DonaldsDock: [3.0, fishProportions[1], 1.8],
     ToontownGlobals.DaisyGardens: [2.5, fishProportions[2], 2.1],
     ToontownGlobals.MinniesMelodyland: [2.0, fishProportions[3], 2.4],
     ToontownGlobals.TheBrrrgh: [2.0, fishProportions[4], 2.7],
     ToontownGlobals.DonaldsDreamland: [1.5, fishProportions[5], 3.0]}

    def __init__(self, air, minigameId):
        try:
            self.DistributedDivingGameAI_initialized
        except:
            self.DistributedDivingGameAI_initialized = 1
            DistributedMinigameAI.__init__(self, air, minigameId)
            self.gameFSM = ClassicFSM.ClassicFSM('DistributedDivingGameAI', [State.State('inactive', self.enterInactive, self.exitInactive, ['swimming']), State.State('swimming', self.enterSwimming, self.exitSwimming, ['cleanup']), State.State('cleanup', self.enterCleanup, self.exitCleanup, ['inactive'])], 'inactive', 'inactive')
            self.addChildGameFSM(self.gameFSM)
            self.__timeBase = globalClockDelta.localToNetworkTime(globalClock.getRealTime())

    def delete(self):
        self.notify.debug('delete')
        del self.gameFSM
        DistributedMinigameAI.delete(self)

    def setGameReady(self):
        self.notify.debug('setGameReady')
        self.sendUpdate('setTrolleyZone', [self.trolleyZone])
        for avId in list(self.scoreDict.keys()):
            self.scoreDict[avId] = 0

        self.SPAWNTIME = self.difficultyPatternsAI[self.getSafezoneId()][0]
        self.proportion = self.difficultyPatternsAI[self.getSafezoneId()][1]
        self.REWARDMOD = self.difficultyPatternsAI[self.getSafezoneId()][2]
        DistributedMinigameAI.setGameReady(self)
        self.spawnings = []
        for i in range(DivingGameGlobals.NUM_SPAWNERS):
            self.spawnings.append(Sequence(Func(self.spawnFish, i), Wait(self.SPAWNTIME + random.random()), Func(self.spawnFish, i), Wait(self.SPAWNTIME - 0.5 + random.random())))
            self.spawnings[i].loop()

    def setGameStart(self, timestamp):
        self.notify.debug('setGameStart')
        DistributedMinigameAI.setGameStart(self, timestamp)
        self.gameFSM.request('swimming')
        self.scoreTracking = {}
        for avId in list(self.scoreDict.keys()):
            self.scoreTracking[avId] = [0,
             0,
             0,
             0,
             0]

    def getCrabMoving(self, crabId, crabX, dir):
        timestamp = globalClockDelta.getFrameNetworkTime()
        rand1 = int(random.random() * 10)
        rand2 = int(random.random() * 10)
        self.sendUpdate('setCrabMoving', [crabId,
         timestamp,
         rand1,
         rand2,
         crabX,
         dir])

    def treasureRecovered(self):
        if not hasattr(self, 'scoreTracking'):
            return
        avId = self.air.getAvatarIdFromSender()
        if avId not in self.avIdList:
            self.air.writeServerEvent('suspicious', avId, 'DivingGameAI.treasureRecovered: invalid avId')
            return
        timestamp = globalClockDelta.getFrameNetworkTime()
        newSpot = int(random.random() * 30)
        self.scoreTracking[avId][4] += 1
        for someAvId in list(self.scoreDict.keys()):
            if someAvId == avId:
                self.scoreDict[avId] += 10 * (self.REWARDMOD * 0.25)
            self.scoreDict[someAvId] += 10 * (self.REWARDMOD * 0.75 / float(len(list(self.scoreDict.keys()))))

        self.sendUpdate('incrementScore', [avId, newSpot, timestamp])

    def hasScoreMult(self):
        return 0

    def setGameAbort(self):
        self.notify.debug('setGameAbort')
        taskMgr.remove(self.taskName('gameTimer'))
        if self.gameFSM.getCurrentState():
            self.gameFSM.request('cleanup')
        DistributedMinigameAI.setGameAbort(self)

    def gameOver(self):
        self.notify.debug('gameOver')
        self.gameFSM.request('cleanup')
        DistributedMinigameAI.gameOver(self)
        trackingString = 'MiniGame Stats : Diving Game'
        trackingString += '\nDistrict:%s' % self.getSafezoneId()
        for avId in list(self.scoreTracking.keys()):
            trackingString = trackingString + '\navId:%s fishHits:%s crabHits:%s treasureCatches:%s treasureDrops:%s treasureRecoveries:%s Score: %s' % (avId,
             self.scoreTracking[avId][0],
             self.scoreTracking[avId][1],
             self.scoreTracking[avId][2],
             self.scoreTracking[avId][3],
             self.scoreTracking[avId][4],
             self.scoreDict[avId])

        self.air.writeServerEvent('MiniGame Stats', None, trackingString)
        return

    def enterInactive(self):
        self.notify.debug('enterInactive')

    def exitInactive(self):
        pass

    def getTimeBase(self):
        return self.__timeBase

    def enterSwimming(self):
        self.notify.debug('enterSwimming')
        duration = 65.0
        taskMgr.doMethodLater(duration, self.timerExpired, self.taskName('gameTimer'))

    def timerExpired(self, task):
        self.notify.debug('timer expired')
        for avId in list(self.scoreDict.keys()):
            if self.scoreDict[avId] < 5:
                self.scoreDict[avId] = 5

        self.gameOver()
        return Task.done

    def exitSwimming(self):
        for i in range(DivingGameGlobals.NUM_SPAWNERS):
            self.spawnings[i].pause()

    def enterCleanup(self):
        self.notify.debug('enterCleanup')
        for i in range(DivingGameGlobals.NUM_SPAWNERS):
            self.spawnings[i].finish()

        del self.spawnings
        self.gameFSM.request('inactive')

    def exitCleanup(self):
        pass

    def pickupTreasure(self, chestId):
        if not hasattr(self, 'scoreTracking'):
            return
        timestamp = globalClockDelta.getFrameNetworkTime()
        avId = self.air.getAvatarIdFromSender()
        if avId not in self.avIdList:
            self.air.writeServerEvent('suspicious', avId, 'DivingGameAI.pickupTreasure: invalid avId')
            return
        self.scoreTracking[avId][2] += 1
        self.sendUpdate('setTreasureGrabbed', [avId, chestId])

    def spawnFish(self, spawnerId):
        timestamp = globalClockDelta.getFrameNetworkTime()
        props = self.proportion[spawnerId]
        num = random.random()
        for i in range(len(props)):
            prop = props[i]
            low = prop[0]
            high = prop[1]
            if num > low and num <= high:
                offset = int(10 * random.random())
                self.sendUpdate('fishSpawn', [timestamp,
                 i,
                 spawnerId,
                 offset])
                return

    def handleCrabCollision(self, avId, status):
        if avId not in self.avIdList:
            self.air.writeServerEvent('suspicious', avId, 'DivingGameAI.handleCrabCollision: invalid avId')
            return
        timestamp = globalClockDelta.getFrameNetworkTime()
        self.sendUpdate('setTreasureDropped', [avId, timestamp])
        self.scoreTracking[avId][1] += 1
        if status == 'normal' or status == 'treasure':
            timestamp = globalClockDelta.getFrameNetworkTime()
            self.sendUpdate('performCrabCollision', [avId, timestamp])
            if status == 'treasure':
                self.scoreTracking[avId][3] += 1

    def handleFishCollision(self, avId, spawnId, spawnerId, status):
        if avId not in self.avIdList:
            self.air.writeServerEvent('suspicious', avId, 'DivingGameAI.handleFishCollision: invalid avId')
            return
        timestamp = globalClockDelta.getFrameNetworkTime()
        self.sendUpdate('setTreasureDropped', [avId, timestamp])
        timestamp = globalClockDelta.getFrameNetworkTime()
        self.scoreTracking[avId][0] += 1
        if status == 'treasure':
            self.scoreTracking[avId][3] += 1
        self.sendUpdate('performFishCollision', [avId,
         spawnId,
         spawnerId,
         timestamp])
