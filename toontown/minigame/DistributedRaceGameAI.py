from math import *
from .DistributedMinigameAI import *
from direct.distributed.ClockDelta import *
from direct.fsm import ClassicFSM, State
from direct.fsm import State
import random
from direct.task.Task import Task
from . import RaceGameGlobals

class DistributedRaceGameAI(DistributedMinigameAI):

    def __init__(self, air, minigameId):
        try:
            self.DistributedRaceGameAI_initialized
        except:
            self.DistributedRaceGameAI_initialized = 1
            DistributedMinigameAI.__init__(self, air, minigameId)
            self.gameFSM = ClassicFSM.ClassicFSM('DistributedRaceGameAI', [State.State('inactive', self.enterInactive, self.exitInactive, ['waitClientsChoices']),
             State.State('waitClientsChoices', self.enterWaitClientsChoices, self.exitWaitClientsChoices, ['processChoices', 'cleanup']),
             State.State('processChoices', self.enterProcessChoices, self.exitProcessChoices, ['waitClientsChoices', 'cleanup']),
             State.State('cleanup', self.enterCleanup, self.exitCleanup, ['inactive'])], 'inactive', 'inactive')
            self.addChildGameFSM(self.gameFSM)
            self.avatarChoices = {}
            self.avatarPositions = {}
            self.chancePositions = {}
            self.rewardDict = {}

    def delete(self):
        self.notify.debug('delete')
        del self.gameFSM
        DistributedMinigameAI.delete(self)

    def setGameReady(self):
        self.notify.debug('setGameReady')
        DistributedMinigameAI.setGameReady(self)
        self.resetChancePositions()
        self.resetPositions()

    def setGameStart(self, timestamp):
        self.notify.debug('setGameStart')
        DistributedMinigameAI.setGameStart(self, timestamp)
        self.gameFSM.request('waitClientsChoices')

    def setGameAbort(self):
        self.notify.debug('setGameAbort')
        if self.gameFSM.getCurrentState():
            self.gameFSM.request('cleanup')
        DistributedMinigameAI.setGameAbort(self)

    def gameOver(self):
        self.notify.debug('gameOver')
        self.gameFSM.request('cleanup')
        DistributedMinigameAI.gameOver(self)

    def anyAvatarWon(self, positionDict):
        for avId, position in list(positionDict.items()):
            if position >= RaceGameGlobals.NumberToWin:
                self.notify.debug('anyAvatarWon: Somebody won')
                return 1

        self.notify.debug('anyAvatarWon: Nobody won')
        return 0

    def allAvatarsChosen(self):
        for choice in list(self.avatarChoices.values()):
            if choice == -1:
                return 0

        return 1

    def checkChoice(self, choice):
        if choice not in RaceGameGlobals.ValidChoices:
            self.notify.warning('checkChoice: invalid choice: ' + str(choice))
            return RaceGameGlobals.ValidChoices[0]
        else:
            return choice

    def resetChoices(self):
        for avId in self.avIdList:
            self.avatarChoices[avId] = -1

    def resetPositions(self):
        for avId in self.avIdList:
            self.avatarPositions[avId] = 0

    def resetChancePositions(self):
        chancePositions = []
        for avId in self.avIdList:
            pos = random.randint(5, RaceGameGlobals.NumberToWin - 1)
            self.chancePositions[avId] = pos
            self.rewardDict[avId] = random.randint(0, len(RaceGameGlobals.ChanceRewards) - 1)
            chancePositions.append(pos)

        self.sendUpdate('setChancePositions', [chancePositions])

    def setAvatarChoice(self, choice):
        avatarId = self.air.getAvatarIdFromSender()
        self.notify.debug('setAvatarChoice: avatar: ' + str(avatarId) + ' chose: ' + str(choice))
        self.avatarChoices[avatarId] = self.checkChoice(choice)
        self.sendUpdate('setAvatarChose', [avatarId])
        if self.allAvatarsChosen():
            self.notify.debug('setAvatarChoice: all avatars have chosen')
            self.gameFSM.request('processChoices')
        else:
            self.notify.debug('setAvatarChoice: still waiting for more choices')

    def enterInactive(self):
        self.notify.debug('enterInactive')

    def exitInactive(self):
        pass

    def enterWaitClientsChoices(self):
        self.notify.debug('enterWaitClientsChoices')
        self.resetChoices()
        taskMgr.doMethodLater(RaceGameGlobals.InputTimeout, self.waitClientsChoicesTimeout, self.taskName('input-timeout'))
        self.sendUpdate('setTimerStartTime', [globalClockDelta.getFrameNetworkTime()])

    def exitWaitClientsChoices(self):
        taskMgr.remove(self.taskName('input-timeout'))

    def waitClientsChoicesTimeout(self, task):
        self.notify.debug('waitClientsChoicesTimeout: did not hear from all clients')
        for avId in list(self.avatarChoices.keys()):
            if self.avatarChoices[avId] == -1:
                self.avatarChoices[avId] = 0

        self.gameFSM.request('processChoices')
        return Task.done

    def enterProcessChoices(self):
        self.notify.debug('enterProcessChoices: ')
        self.choiceArray = []
        self.positionArray = []
        self.rewardArray = []
        for avId in self.avIdList:
            choice = self.avatarChoices[avId]
            freq = list(self.avatarChoices.values()).count(choice)
            self.processChoice(avId, choice, freq)

        masterList = []
        for avId in self.avIdList:
            masterList.append(-1)

        done = 0
        rewarded = 0
        while not done:
            self.notify.debug('enterProcessChoice: notDone')
            rewardList = masterList[:]
            for avId in self.avIdList:
                reward = self.processReward(avId)
                if reward != -1:
                    rewarded = 1
                    rewardList[self.avIdList.index(avId)] = reward
                    self.rewardArray += rewardList
                    for av in self.avIdList:
                        if av == avId:
                            self.processChoice(av, RaceGameGlobals.ChanceRewards[reward][0][0])
                        else:
                            self.processChoice(av, RaceGameGlobals.ChanceRewards[reward][0][1])

                    break

            if not rewarded:
                self.rewardArray += rewardList
            self.notify.debug('      rewardList: ' + str(rewardList))
            self.notify.debug('      rewardArray: ' + str(self.rewardArray))
            done = rewardList.count(-1) == len(rewardList)

        self.checkForWinners()

    def processChoice(self, avId, choice, freq = 1):
        self.notify.debug('processChoice: av = ' + str(avId) + ' choice = ' + str(choice))
        if freq == 1:
            if choice != 0:
                if self.avatarPositions[avId] < RaceGameGlobals.NumberToWin:
                    self.avatarPositions[avId] += choice
                    if self.avatarPositions[avId] < 0:
                        self.avatarPositions[avId] = 0
        self.choiceArray.append(choice)
        self.positionArray.append(self.avatarPositions[avId])
        self.notify.debug('Process choice (' + str(choice) + ') for av: ' + str(avId))
        self.notify.debug('      choiceArray: ' + str(self.choiceArray))
        self.notify.debug('    positionArray: ' + str(self.positionArray))

    def processReward(self, rewardee):
        self.notify.debug('processReward: ' + str(rewardee))
        reward = -1
        if self.avatarPositions[rewardee] == self.chancePositions[rewardee]:
            reward = self.rewardDict[rewardee]
            bonus = RaceGameGlobals.ChanceRewards[reward][2]
            self.scoreDict[rewardee] = self.scoreDict[rewardee] + bonus
            self.chancePositions[rewardee] = -1
        return reward

    def checkForWinners(self):
        self.notify.debug('checkForWinners: ')
        self.sendUpdate('setServerChoices', [self.choiceArray, self.positionArray, self.rewardArray])
        delay = 0.0
        for reward in self.rewardArray:
            if reward != -1:
                delay += 7.0

        if self.anyAvatarWon(self.avatarPositions):
            numWinners = 0
            for avId in self.avIdList:
                if self.avatarPositions[avId] >= RaceGameGlobals.NumberToWin:
                    numWinners = numWinners + 1

            for avId in self.avIdList:
                newJellybeans = ceil(self.avatarPositions[avId] * 0.5)
                if self.avatarPositions[avId] >= RaceGameGlobals.NumberToWin:
                    newJellybeans = RaceGameGlobals.NumberToWin
                    if numWinners > 1:
                        newJellybeans = newJellybeans - 3
                self.scoreDict[avId] = self.scoreDict[avId] + newJellybeans

            taskMgr.doMethodLater(delay, self.rewardTimeoutTaskGameOver, self.taskName('reward-timeout'))
        else:
            taskMgr.doMethodLater(delay, self.rewardTimeoutTask, self.taskName('reward-timeout'))

    def oldEnterProcessChoices(self, recurse = 0):
        self.notify.debug('enterProcessChoices')
        if not recurse:
            self.choiceArray = []
            self.positionArray = []
            self.rewardArray = []
        for avId in self.avIdList:
            choice = self.avatarChoices[avId]
            reward = -1
            if choice != 0:
                freq = list(self.avatarChoices.values()).count(choice)
                if recurse or freq == 1:
                    self.avatarPositions[avId] += choice
                    if self.avatarPositions[avId] < 0:
                        self.avatarPositions[avId] = 0
                    if self.avatarPositions[avId] == self.chancePositions[avId]:
                        reward = self.rewardDict[avId]
                        self.scoreDict[avId] = self.scoreDict[avId] + RaceGameGlobals.ChanceRewards[reward][2]
                        self.chancePositions[avId] = -1
            self.choiceArray.append(choice)
            self.positionArray.append(self.avatarPositions[avId])
            self.rewardArray.append(reward)

        self.notify.debug('      choiceArray: ' + str(self.choiceArray))
        self.notify.debug('    positionArray: ' + str(self.positionArray))
        self.notify.debug('      rewardArray: ' + str(self.rewardArray))
        thisTurnRewards = self.rewardArray[-len(self.avatarPositions):]
        rewardIndex = 0
        for reward in thisTurnRewards:
            if reward != -1:
                for avId in self.avIdList:
                    if self.avIdList.index(avId) == rewardIndex:
                        self.avatarChoices[avId] = RaceGameGlobals.ChanceRewards[reward][0][0]
                    else:
                        self.avatarChoices[avId] = RaceGameGlobals.ChanceRewards[reward][0][1]

                self.enterProcessChoices(1)
            rewardIndex += 1

        if not recurse:
            self.sendUpdate('setServerChoices', [self.choiceArray, self.positionArray, self.rewardArray])
            delay = 0.0
            for reward in self.rewardArray:
                if reward != -1:
                    delay += 7.0

            if self.anyAvatarWon(self.avatarPositions):
                numWinners = 0
                for avId in self.avIdList:
                    if self.avatarPositions[avId] >= RaceGameGlobals.NumberToWin:
                        numWinners = numWinners + 1

                for avId in self.avIdList:
                    newJellybeans = ceil(self.avatarPositions[avId] * 0.5)
                    if self.avatarPositions[avId] >= RaceGameGlobals.NumberToWin:
                        newJellybeans = RaceGameGlobals.NumberToWin
                        if numWinners > 1:
                            newJellybeans = newJellybeans - 3
                    self.scoreDict[avId] = self.scoreDict[avId] + newJellybeans

                taskMgr.doMethodLater(delay, self.rewardTimeoutTaskGameOver, self.taskName('reward-timeout'))
            else:
                taskMgr.doMethodLater(delay, self.rewardTimeoutTask, self.taskName('reward-timeout'))
        return None

    def rewardTimeoutTaskGameOver(self, task):
        self.notify.debug('Done waiting for rewards, game over')
        self.gameOver()
        return Task.done

    def rewardTimeoutTask(self, task):
        self.notify.debug('Done waiting for rewards')
        self.gameFSM.request('waitClientsChoices')
        return Task.done

    def exitProcessChoices(self):
        taskMgr.remove(self.taskName('reward-timeout'))

    def enterCleanup(self):
        self.notify.debug('enterCleanup')
        self.gameFSM.request('inactive')

    def exitCleanup(self):
        pass
