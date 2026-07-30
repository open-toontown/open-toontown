from .DistributedMinigameAI import *
from direct.distributed.ClockDelta import *
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from . import RingGameGlobals
import random
import types

class DistributedRingGameAI(DistributedMinigameAI):

    def __init__(self, air, minigameId):
        try:
            self.DistributedRingGameAI_initialized
        except:
            self.DistributedRingGameAI_initialized = 1
            DistributedMinigameAI.__init__(self, air, minigameId)
            self.gameFSM = ClassicFSM.ClassicFSM('DistributedRingGameAI', [State.State('inactive', self.enterInactive, self.exitInactive, ['swimming']), State.State('swimming', self.enterSwimming, self.exitSwimming, ['cleanup']), State.State('cleanup', self.enterCleanup, self.exitCleanup, ['inactive'])], 'inactive', 'inactive')
            self.addChildGameFSM(self.gameFSM)
            self.__timeBase = globalClockDelta.localToNetworkTime(globalClock.getRealTime())
            self.selectColorIndices()

    def delete(self):
        self.notify.debug('delete')
        del self.gameFSM
        DistributedMinigameAI.delete(self)

    def setGameReady(self):
        self.notify.debug('setGameReady')
        DistributedMinigameAI.setGameReady(self)

    def setGameStart(self, timestamp):
        self.notify.debug('setGameStart')
        DistributedMinigameAI.setGameStart(self, timestamp)
        self.gameFSM.request('swimming')

    def setGameAbort(self):
        self.notify.debug('setGameAbort')
        if self.gameFSM.getCurrentState():
            self.gameFSM.request('cleanup')
        DistributedMinigameAI.setGameAbort(self)

    def gameOver(self):
        self.notify.debug('gameOver')
        self.gameFSM.request('cleanup')
        DistributedMinigameAI.gameOver(self)

    def enterInactive(self):
        self.notify.debug('enterInactive')

    def exitInactive(self):
        pass

    def getTimeBase(self):
        return self.__timeBase

    def getColorIndices(self):
        return self.colorIndices

    def selectColorIndices(self):
        self.colorIndices = [None,
         None,
         None,
         None]
        chooseFrom = RingGameGlobals.ringColorSelection[:]
        for i in range(0, 4):
            c = random.choice(chooseFrom)
            chooseFrom.remove(c)
            if isinstance(c, tuple):
                c = random.choice(c)
            self.colorIndices[i] = c

        return

    def enterSwimming(self):
        self.notify.debug('enterSwimming')
        self.__nextRingGroup = {}
        for avId in self.avIdList:
            self.__nextRingGroup[avId] = 0

        self.__numRingsPassed = [0] * RingGameGlobals.NUM_RING_GROUPS
        self.__ringResultBitfield = [0] * RingGameGlobals.NUM_RING_GROUPS
        self.perfectGames = {}
        for avId in self.avIdList:
            self.perfectGames[avId] = 1

        for avId in self.avIdList:
            self.scoreDict[avId] = 0

    def exitSwimming(self):
        pass

    def enterCleanup(self):
        self.notify.debug('enterCleanup')
        self.gameFSM.request('inactive')

    def exitCleanup(self):
        pass

    def setToonGotRing(self, success):
        avId = self.air.getAvatarIdFromSender()
        if avId not in self.avIdList:
            self.air.writeServerEvent('suspicious', avId, 'RingGameAI.setToonGotRing: invalid avId')
            return
        if self.gameFSM.getCurrentState() is None or self.gameFSM.getCurrentState().getName() != 'swimming':
            self.air.writeServerEvent('suspicious', avId, 'RingGameAI.setToonGotRing: game not in swimming state')
            return
        ringGroupIndex = self.__nextRingGroup[avId]
        if ringGroupIndex >= RingGameGlobals.NUM_RING_GROUPS:
            self.notify.warning('warning: got extra ToonGotRing msg from av %s' % avId)
            return
        self.__nextRingGroup[avId] += 1
        if not success:
            self.__ringResultBitfield[ringGroupIndex] |= 1 << self.avIdList.index(avId)
            self.perfectGames[avId] = 0
        else:
            self.scoreDict[avId] += 1
        self.__numRingsPassed[ringGroupIndex] += 1
        if self.__numRingsPassed[ringGroupIndex] >= self.numPlayers:
            if not self.isSinglePlayer():
                bitfield = self.__ringResultBitfield[ringGroupIndex]
                if bitfield == 0:
                    for id in self.avIdList:
                        self.scoreDict[id] += 0.5

                self.sendUpdate('setRingGroupResults', [bitfield])
            if ringGroupIndex >= RingGameGlobals.NUM_RING_GROUPS - 1:
                perfectBonuses = {1: 5,
                 2: 5,
                 3: 10,
                 4: 18}
                numPerfectToons = 0
                for avId in self.avIdList:
                    if self.perfectGames[avId]:
                        numPerfectToons += 1

                for avId in self.avIdList:
                    if self.perfectGames[avId]:
                        self.scoreDict[avId] += perfectBonuses[numPerfectToons]
                        self.logPerfectGame(avId)

                for avId in self.avIdList:
                    self.scoreDict[avId] = max(1, self.scoreDict[avId])

                if not RingGameGlobals.ENDLESS_GAME:
                    self.gameOver()
        return
