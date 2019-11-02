from DistributedMinigameAI import *
from toontown.ai.ToonBarrier import *
from direct.fsm import ClassicFSM, State
from direct.fsm import State
import random
import PatternGameGlobals
import copy

class DistributedPatternGameAI(DistributedMinigameAI):

    def __init__(self, air, minigameId):
        try:
            self.DistributedPatternGameAI_initialized
        except:
            self.DistributedPatternGameAI_initialized = 1
            DistributedMinigameAI.__init__(self, air, minigameId)
            self.gameFSM = ClassicFSM.ClassicFSM('DistributedPatternGameAI', [State.State('off', self.enterInactive, self.exitInactive, ['waitClientsReady', 'cleanup']),
             State.State('waitClientsReady', self.enterWaitClientsReady, self.exitWaitClientsReady, ['generatePattern', 'cleanup']),
             State.State('generatePattern', self.enterGeneratePattern, self.exitGeneratePattern, ['waitForResults', 'cleanup']),
             State.State('waitForResults', self.enterWaitForResults, self.exitWaitForResults, ['waitClientsReady', 'cleanup']),
             State.State('cleanup', self.enterCleanup, self.exitCleanup, [])], 'off', 'cleanup')
            self.addChildGameFSM(self.gameFSM)

    def delete(self):
        self.notify.debug('delete')
        del self.gameFSM
        DistributedMinigameAI.delete(self)

    def setGameReady(self):
        self.notify.debug('setGameReady')
        DistributedMinigameAI.setGameReady(self)
        self.__initGameVars()

    def setGameStart(self, timestamp):
        self.notify.debug('setGameStart')
        DistributedMinigameAI.setGameStart(self, timestamp)
        self.gameFSM.request('waitClientsReady')

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

    def __initGameVars(self):
        self.pattern = []
        self.round = 0
        self.perfectResults = {}
        for avId in self.avIdList:
            self.perfectResults[avId] = 1

        self.readyClients = []
        self.timeoutTaskName = self.uniqueName('PatternGameResultsTimeout')

    def enterWaitClientsReady(self):
        self.notify.debug('enterWaitClientsReady')
        self.nextRoundBarrier = ToonBarrier('nextRoundReady', self.uniqueName('nextRoundReady'), self.avIdList, PatternGameGlobals.ClientsReadyTimeout, self.__allPlayersReady, self.__clientsReadyTimeout)
        for avId in self.readyClients:
            self.nextRoundBarrier.clear(avId)

    def reportPlayerReady(self):
        if not self._inState('waitClientsReady'):
            return
        avId = self.air.getAvatarIdFromSender()
        if avId not in self.avIdList:
            self.notify.warning('Got reportPlayerReady from an avId: %s not in our list: %s' % (avId, self.avIdList))
        else:
            self.readyClients.append(avId)
            self.nextRoundBarrier.clear(avId)

    def __allPlayersReady(self):
        self.readyClients = []
        self.gameFSM.request('generatePattern')

    def __clientsReadyTimeout(self, avIds):
        self.notify.debug('__clientsReadyTimeout: clients %s have not responded' % avIds)
        self.setGameAbort()

    def exitWaitClientsReady(self):
        self.nextRoundBarrier.cleanup()
        del self.nextRoundBarrier

    def enterGeneratePattern(self):
        self.notify.debug('enterGeneratePattern')
        self.round += 1
        targetLen = PatternGameGlobals.INITIAL_ROUND_LENGTH + PatternGameGlobals.ROUND_LENGTH_INCREMENT * (self.round - 1)
        count = targetLen - len(self.pattern)
        for i in range(0, count):
            self.pattern.append(random.randint(0, 3))

        self.gameFSM.request('waitForResults')
        self.sendUpdate('setPattern', [self.pattern])

    def exitGeneratePattern(self):
        pass

    def enterWaitForResults(self):
        self.notify.debug('enterWaitForResults')
        self.results = [None] * self.numPlayers
        self.fastestTime = PatternGameGlobals.InputTime * 2
        self.fastestAvId = 0
        self.resultsBarrier = ToonBarrier('results', self.uniqueName('results'), self.avIdList, PatternGameGlobals.InputTimeout + 1.0 * self.round, self.__gotAllPatterns, self.__resultsTimeout)
        return

    def reportButtonPress(self, index, wrong):
        if not self._inState('waitForResults'):
            return
        avId = self.air.getAvatarIdFromSender()
        if avId not in self.avIdList:
            self.air.writeServerEvent('suspicious', avId, 'PatternGameAI.reportButtonPress avId not on list')
            return
        if index < 0 or index > 3:
            self.air.writeServerEvent('warning', index, 'PatternGameAI.reportButtonPress got bad index')
            return
        if wrong not in [0, 1]:
            self.air.writeServerEvent('warning', wrong, "PatternGameAI.reportButtonPress got bad 'wrong'")
            return
        self.sendUpdate('remoteButtonPressed', [avId, index, wrong])

    def __resultsTimeout(self, avIds):
        self.notify.debug('__resultsTimeout: %s' % avIds)
        for avId in avIds:
            index = self.avIdList.index(avId)
            self.__acceptPlayerPattern(avId, [], PatternGameGlobals.InputTime * 2)

        self.__gotAllPatterns()

    def reportPlayerPattern(self, pattern, totalTime):
        if not self._inState('waitForResults'):
            return
        avId = self.air.getAvatarIdFromSender()
        self.__acceptPlayerPattern(avId, pattern, totalTime)
        self.resultsBarrier.clear(avId)

    def __acceptPlayerPattern(self, avId, pattern, totalTime):
        index = self.avIdList.index(avId)
        if self.results[index] != None:
            return
        self.results[index] = pattern
        if totalTime < self.fastestTime and pattern == self.pattern:
            self.fastestTime = totalTime
            self.fastestAvId = avId
            if self.numPlayers == 1:
                self.fastestAvId = 1
            else:
                self.scoreDict[self.fastestAvId] += 2
        return

    def __gotAllPatterns(self):
        patterns = [[]] * 4
        for i in range(0, len(self.results)):
            patterns[i] = self.results[i]
            if patterns[i] is None:
                patterns[i] = []

        self.sendUpdate('setPlayerPatterns', patterns + [self.fastestAvId])
        for i in range(0, self.numPlayers):
            avId = self.avIdList[i]
            if not self.results[i] == self.pattern:
                self.perfectResults[avId] = 0
            else:
                self.scoreDict[avId] += self.round

        if self.round < PatternGameGlobals.NUM_ROUNDS:
            self.gameFSM.request('waitClientsReady')
        else:
            for avId in self.avIdList:
                if self.perfectResults[avId]:
                    self.scoreDict[avId] += 4
                    self.logPerfectGame(avId)

            self.gameOver()
            self.gameFSM.request('cleanup')
        return

    def exitWaitForResults(self):
        self.resultsBarrier.cleanup()
        del self.resultsBarrier

    def enterCleanup(self):
        self.notify.debug('enterCleanup')

    def exitCleanup(self):
        pass
