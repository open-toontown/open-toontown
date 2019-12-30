from .DistributedMinigameAI import *
from direct.fsm import ClassicFSM, State
from direct.fsm import State
import random
from direct.task.Task import Task
import copy
from . import TugOfWarGameGlobals
import math

class DistributedTugOfWarGameAI(DistributedMinigameAI):

    def __init__(self, air, minigameId):
        try:
            self.DistributedTugOfWarGameAI_initialized
        except:
            self.DistributedTugOfWarGameAI_initialized = 1
            DistributedMinigameAI.__init__(self, air, minigameId)
            self.gameFSM = ClassicFSM.ClassicFSM('DistributedTugOfWarGameAI', [State.State('off', self.enterInactive, self.exitInactive, ['waitClientsReady', 'cleanup']),
             State.State('waitClientsReady', self.enterWaitClientsReady, self.exitWaitClientsReady, ['sendGoSignal', 'cleanup']),
             State.State('sendGoSignal', self.enterSendGoSignal, self.exitSendGoSignal, ['waitForResults', 'cleanup']),
             State.State('waitForResults', self.enterWaitForResults, self.exitWaitForResults, ['waitClientsReady', 'contestOver', 'cleanup']),
             State.State('contestOver', self.enterContestOver, self.exitContestOver, ['cleanup']),
             State.State('cleanup', self.enterCleanup, self.exitCleanup, ['off'])], 'off', 'off')
            self.addChildGameFSM(self.gameFSM)

        self.switched = 0
        self.side = {}
        self.forceDict = [{}, {}]
        self.keyRateDict = {}
        self.howManyReported = 0
        self.offsetDict = {}
        self.kMovement = 0.02
        self.suitId = 666
        self.suitForces = [(6, 4),
         (2, 5),
         (2, 6.5),
         (3, 8.0),
         (5, 6),
         (8, 8),
         (9, 8.5),
         (4, 9)]
        self.suitForceMultiplier = 0.75
        self.curSuitForce = 0
        self.suitOffset = 0
        self.contestEnded = 0
        self.losingSide = -1
        self.winners = []
        self.losers = []
        self.tieers = []
        self.timeBonus = float(TugOfWarGameGlobals.TIME_BONUS_RANGE)

    def delete(self):
        self.notify.debug('delete')
        del self.gameFSM
        del self.side
        del self.forceDict
        del self.keyRateDict
        del self.offsetDict
        del self.suitForces
        del self.winners
        del self.tieers
        del self.losers
        DistributedMinigameAI.delete(self)

    def setGameReady(self):
        self.notify.debug('setGameReady')
        self.suitType = random.randrange(1, 5)
        self.suitJellybeanReward = math.pow(2, self.suitType - 1)
        if self.isSinglePlayer():
            self.gameType = TugOfWarGameGlobals.TOON_VS_COG
            self.suitForceMultiplier = 0.58 + float(self.suitType) / 10.0
        else:
            randInt = random.randrange(0, 10)
            if randInt < 8:
                self.gameType = TugOfWarGameGlobals.TOON_VS_COG
                self.suitForceMultiplier = 0.65 + float(self.suitType) / 16.0
                self.kMovement = 0.02
            else:
                self.gameType = TugOfWarGameGlobals.TOON_VS_TOON
                self.kMovement = 0.04
        self.sendUpdate('sendGameType', [self.gameType, self.suitType])
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
        self.currentButtons = [0, 0]
        self.readyClients = []

    def enterWaitClientsReady(self):
        self.notify.debug('enterWaitClientsReady')
        taskMgr.doMethodLater(TugOfWarGameGlobals.WAIT_FOR_CLIENTS_TIMEOUT, self.waitForClientsTimeout, self.taskName('clients-timeout'))

    def exitWaitClientsReady(self):
        taskMgr.remove(self.taskName('clients-timeout'))

    def waitForClientsTimeout(self, task):
        self.notify.debug('Done waiting for clients')
        self.sendUpdate('sendStopSignal', [self.winners, self.losers, self.tieers])
        self.gameOver()
        return Task.done

    def reportPlayerReady(self, side):
        avId = self.air.getAvatarIdFromSender()
        if avId in self.readyClients:
            self.notify.warning('Got reportPlayerReady from an avId more than once: %s' % avId)
            return
        if avId not in self.avIdList or side not in [0, 1]:
            self.notify.warning('Got reportPlayerReady from an avId: %s not in our list: %s' % (avId, self.avIdList))
        else:
            self.readyClients.append(avId)
            self.side[avId] = side
            self.forceDict[side][avId] = 0
            self.offsetDict[avId] = 0
        if len(self.readyClients) == self.numPlayers:
            self.readyClients = []
            self.gameFSM.request('sendGoSignal')

    def sendNewAvIdList(self, newAvIdList):
        for avId in newAvIdList:
            if avId not in self.scoreDict:
                self.notify.debug('invalid avId in new list from %s' % self.air.getAvatarIdFromSender())
                return

        if not self.switched:
            self.switched = 1
            self.avIdList = newAvIdList
        elif self.avIdList != newAvIdList:
            self.notify.debug('Big trouble in little TugOWar Town')

    def enterSendGoSignal(self):
        self.notify.debug('enterSendGoSignal')
        taskMgr.doMethodLater(TugOfWarGameGlobals.GAME_DURATION, self.timerExpired, self.taskName('gameTimer'))
        if self.gameType == TugOfWarGameGlobals.TOON_VS_COG:
            self.curSuitForceInd = 0
            taskMgr.add(self.timeForNewSuitForce, self.taskName('suitForceTimer'))
        taskMgr.doMethodLater(1, self.calcTimeBonus, self.taskName('timeBonusTimer'))
        self.sendUpdate('sendGoSignal', [[0, 1]])
        self.gameFSM.request('waitForResults')

    def timerExpired(self, task):
        self.notify.debug('timer expired')
        self.gameFSM.request('contestOver')
        return Task.done

    def timeForNewSuitForce(self, task):
        self.notify.debug('timeForNewSuitForce')
        if self.curSuitForceInd < len(self.suitForces):
            randForce = random.random() - 0.5
            self.curSuitForce = self.suitForceMultiplier * self.numPlayers * (self.suitForces[self.curSuitForceInd][1] + randForce)
            taskMgr.doMethodLater(self.suitForces[self.curSuitForceInd][0], self.timeForNewSuitForce, self.taskName('suitForceTimer'))
        self.curSuitForceInd += 1
        return Task.done

    def calcTimeBonus(self, task):
        delta = float(TugOfWarGameGlobals.TIME_BONUS_RANGE) / float(TugOfWarGameGlobals.GAME_DURATION)
        self.timeBonus = self.timeBonus - delta
        taskMgr.doMethodLater(1, self.calcTimeBonus, self.taskName('timeBonusTimer'))
        return Task.done

    def exitSendGoSignal(self):
        pass

    def enterWaitForResults(self):
        self.notify.debug('enterWaitForResults')

    def calculateOffsets(self):
        f = [0, 0]
        for i in [0, 1]:
            for x in list(self.forceDict[i].values()):
                f[i] += x

        if self.gameType == TugOfWarGameGlobals.TOON_VS_COG:
            f[1] += self.curSuitForce
        deltaF = f[1] - f[0]
        deltaX = deltaF * self.kMovement
        for avId in self.avIdList:
            offset = deltaX
            if self.side[avId] == 0:
                if deltaX < 0:
                    offset = deltaX / 2.0
            elif deltaX > 0:
                offset = deltaX / 2.0
            self.offsetDict[avId] += offset

        if deltaX < 0:
            self.suitOffset += deltaX
        else:
            self.suitOffset += deltaX / 2.0

    def reportCurrentKeyRate(self, keyRate, force):
        avId = self.air.getAvatarIdFromSender()
        if avId not in self.side:
            self.notify.warning('Avatar %s sent reportCurrentKeyRate too early %s' % (avId, self.side))
            return
        self.keyRateDict[avId] = keyRate
        self.forceDict[self.side[avId]][avId] = force
        self.sendUpdate('remoteKeyRateUpdate', [avId, self.keyRateDict[avId]])
        self.howManyReported += 1
        if self.howManyReported == self.numPlayers:
            self.howManyReported = 0
            self.calculateOffsets()
            self.sendUpdate('sendCurrentPosition', [list(self.offsetDict.keys()), list(self.offsetDict.values())])
            if self.gameType == TugOfWarGameGlobals.TOON_VS_COG:
                self.sendUpdate('sendSuitPosition', [self.suitOffset])

    def reportEndOfContest(self, index):
        if index not in [0, 1]:
            self.notify.warning('Got a bad index %s ' % index)
            return
        self.losingSide = index
        self.notify.debug('losing side = %d' % self.losingSide)
        if self.contestEnded == 0:
            self.contestEnded = 1
            self.gameFSM.request('contestOver')

    def __processResults(self):
        if self.contestEnded:
            self.timeBonus = TugOfWarGameGlobals.TIME_BONUS_MIN + int(self.timeBonus + 0.5)
            if self.gameType == TugOfWarGameGlobals.TOON_VS_COG:
                if self.losingSide == 1:
                    self.losers.append(self.suitId)
                else:
                    self.winners.append(self.suitId)
                for i in range(0, self.numPlayers):
                    avId = self.avIdList[i]
                    if self.side[avId] != self.losingSide:
                        self.scoreDict[avId] = self.suitJellybeanReward + TugOfWarGameGlobals.WIN_JELLYBEANS
                        self.winners.append(avId)
                    else:
                        self.scoreDict[avId] = TugOfWarGameGlobals.LOSS_JELLYBEANS
                        self.losers.append(avId)

            else:
                for i in range(0, self.numPlayers):
                    avId = self.avIdList[i]
                    if self.side[avId] != self.losingSide:
                        self.scoreDict[avId] = TugOfWarGameGlobals.WIN_JELLYBEANS
                        self.winners.append(avId)
                    else:
                        self.scoreDict[avId] = TugOfWarGameGlobals.LOSS_JELLYBEANS
                        self.losers.append(avId)

        elif self.gameType == TugOfWarGameGlobals.TOON_VS_COG:
            for i in range(0, self.numPlayers):
                avId = self.avIdList[i]
                if -self.offsetDict[avId] > self.suitOffset:
                    self.scoreDict[avId] = self.suitJellybeanReward / 2 + TugOfWarGameGlobals.TIE_WIN_JELLYBEANS
                    self.winners.append(avId)
                else:
                    self.scoreDict[avId] = self.suitJellybeanReward / 2 + TugOfWarGameGlobals.TIE_LOSS_JELLYBEANS
                    self.losers.append(avId)
                    self.winners.append(self.suitId)

        else:
            maxOffset = -100
            minOffset = 100
            for i in range(0, self.numPlayers):
                avId = self.avIdList[i]
                if self.side[avId] == 0:
                    if -self.offsetDict[avId] > maxOffset:
                        maxOffset = -self.offsetDict[avId]
                    elif -self.offsetDict[avId] < minOffset:
                        minOffset = -self.offsetDict[avId]
                elif self.side[avId] == 1:
                    if self.offsetDict[avId] > maxOffset:
                        maxOffset = self.offsetDict[avId]
                    elif self.offsetDict[avId] < minOffset:
                        minOffset = self.offsetDict[avId]

            for i in range(0, self.numPlayers):
                avId = self.avIdList[i]
                if maxOffset != minOffset:
                    if self.side[avId] == 0:
                        if -self.offsetDict[avId] == maxOffset:
                            self.scoreDict[avId] = TugOfWarGameGlobals.TIE_WIN_JELLYBEANS
                            self.winners.append(avId)
                        else:
                            self.scoreDict[avId] = TugOfWarGameGlobals.TIE_LOSS_JELLYBEANS
                            self.losers.append(avId)
                    elif self.side[avId] == 1:
                        if self.offsetDict[avId] == maxOffset:
                            self.scoreDict[avId] = TugOfWarGameGlobals.TIE_WIN_JELLYBEANS
                            self.winners.append(avId)
                        else:
                            self.scoreDict[avId] = TugOfWarGameGlobals.TIE_LOSS_JELLYBEANS
                            self.losers.append(avId)
                else:
                    self.scoreDict[avId] += TugOfWarGameGlobals.TIE_JELLYBEANS
                    self.tieers.append(avId)

        self.gameOver()

    def exitWaitForResults(self):
        pass

    def enterContestOver(self):
        self.__processResults()
        self.sendUpdate('sendStopSignal', [self.winners, self.losers, self.tieers])

    def exitContestOver(self):
        pass

    def enterCleanup(self):
        self.notify.debug('enterCleanup')
        taskMgr.remove(self.taskName('gameTimer'))
        taskMgr.remove(self.taskName('timeBonusTimer'))
        taskMgr.remove(self.taskName('suitForceTimer'))
        self.gameFSM.request('off')

    def exitCleanup(self):
        pass
