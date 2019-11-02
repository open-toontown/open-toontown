from toontown.minigame.DistributedMinigameAI import *
from direct.fsm import ClassicFSM, State
from direct.fsm import State
import TravelGameGlobals
from toontown.toonbase import ToontownGlobals

class DistributedTravelGameAI(DistributedMinigameAI):
    notify = directNotify.newCategory('DistributedTravelGameAI')

    def __init__(self, air, minigameId):
        try:
            self.DistributedTravelGameAI_initialized
        except:
            self.DistributedTravelGameAI_initialized = 1
            DistributedMinigameAI.__init__(self, air, minigameId)
            self.gameFSM = ClassicFSM.ClassicFSM('DistributedTravelGameAI', [State.State('inactive', self.enterInactive, self.exitInactive, ['waitClientsChoices']),
             State.State('waitClientsChoices', self.enterWaitClientsChoices, self.exitWaitClientsChoices, ['processChoices', 'cleanup']),
             State.State('processChoices', self.enterProcessChoices, self.exitProcessChoices, ['waitClientsChoices', 'cleanup']),
             State.State('cleanup', self.enterCleanup, self.exitCleanup, ['inactive'])], 'inactive', 'inactive')
            self.addChildGameFSM(self.gameFSM)
            self.currentVotes = {}
            self.avatarChoices = {}
            self.currentSwitch = 0
            self.destSwitch = 0
            self.gotBonus = {}
            self.desiredNextGame = -1
            self.boardIndex = random.choice(range(len(TravelGameGlobals.BoardLayouts)))

    def generate(self):
        self.notify.debug('generate')
        DistributedMinigameAI.generate(self)

    def delete(self):
        self.notify.debug('delete')
        del self.gameFSM
        DistributedMinigameAI.delete(self)

    def setGameReady(self):
        self.notify.debug('setGameReady')
        DistributedMinigameAI.setGameReady(self)
        self.calcMinigames()
        self.calcBonusBeans()

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
        scoreList = []
        curVotesList = []
        bonusesList = []
        for avId in self.avIdList:
            scoreList.append(self.scoreDict[avId])
            curVotesList.append(self.currentVotes[avId])
            bonusesList.append((self.avIdBonuses[avId][0], self.avIdBonuses[avId][1]))

        self.air.writeServerEvent('minigame_travel', self.doId, '%s|%s|%s|%s|%s|%s|%s|%s' % (ToontownGlobals.TravelGameId,
         self.getSafezoneId(),
         self.avIdList,
         scoreList,
         self.boardIndex,
         curVotesList,
         bonusesList,
         self.desiredNextGame))
        self.gameFSM.request('cleanup')
        DistributedMinigameAI.gameOver(self)

    def enterInactive(self):
        self.notify.debug('enterInactive')

    def exitInactive(self):
        pass

    def enterWaitClientsChoices(self):
        self.notify.debug('enterWaitClientsChoices')
        self.resetChoices()
        taskMgr.doMethodLater(TravelGameGlobals.InputTimeout, self.waitClientsChoicesTimeout, self.taskName('input-timeout'))
        self.sendUpdate('setTimerStartTime', [globalClockDelta.getFrameNetworkTime()])

    def exitWaitClientsChoices(self):
        taskMgr.remove(self.taskName('input-timeout'))

    def enterProcessChoices(self):
        self.directionVotes = []
        for dir in range(TravelGameGlobals.MaxDirections):
            self.directionVotes.append([dir, 0])

        for key in self.avatarChoices:
            choice = self.avatarChoices[key]
            numVotes = choice[0]
            direction = choice[1]
            self.directionVotes[direction][1] += numVotes

        def voteCompare(directionVoteA, directionVoteB):
            if directionVoteA[1] < directionVoteB[1]:
                return -1
            elif directionVoteA[1] == directionVoteB[1]:
                return 0
            else:
                return 1

        self.directionVotes.sort(voteCompare, reverse=True)
        winningVotes = self.directionVotes[0][1]
        self.winningDirections = []
        self.notify.debug('self.directionVotes = %s' % self.directionVotes)
        for vote in self.directionVotes:
            if vote[1] == winningVotes:
                self.winningDirections.append(vote[0])
                self.notify.debug('add direction %d to winning directions' % vote[0])

        self.directionReason = TravelGameGlobals.ReasonVote
        if len(self.winningDirections) > 1:
            self.notify.debug('multiple winningDirections=%s' % self.winningDirections)
            self.directionReason = TravelGameGlobals.ReasonRandom
        self.directionToGo = random.choice(self.winningDirections)
        self.notify.debug('self.directionToGo =%d' % self.directionToGo)
        self.votesArray = []
        self.directionArray = []
        for avId in self.avIdList:
            vote = self.avatarChoices[avId][0]
            direction = self.avatarChoices[avId][1]
            if vote < 0:
                vote = 0
            self.votesArray.append(vote)
            self.directionArray.append(direction)

        curSwitch = TravelGameGlobals.BoardLayouts[self.boardIndex][self.currentSwitch]
        self.destSwitch = curSwitch['links'][self.directionToGo]
        self.checkForEndGame()

    def exitProcessChoices(self):
        taskMgr.remove(self.taskName('move-timeout'))

    def enterCleanup(self):
        self.notify.debug('enterCleanup')
        self.gameFSM.request('inactive')

    def exitCleanup(self):
        pass

    def setExpectedAvatars(self, avIds):
        DistributedMinigameAI.setExpectedAvatars(self, avIds)

    def createDefaultStartingVotes(self):
        for avId in self.avIdList:
            self.startingVotes[avId] = TravelGameGlobals.DefaultStartingVotes
            self.currentVotes[avId] = TravelGameGlobals.DefaultStartingVotes

    def waitClientsChoicesTimeout(self, task):
        self.notify.debug('waitClientsChoicesTimeout: did not hear from all clients')
        for avId in self.avatarChoices.keys():
            if self.avatarChoices[avId] == (-1, 0):
                self.avatarChoices[avId] = (0, 0)

        self.gameFSM.request('processChoices')
        return Task.done

    def resetChoices(self):
        for avId in self.avIdList:
            self.avatarChoices[avId] = (-1, 0)

    def setAvatarChoice(self, votes, direction):
        avatarId = self.air.getAvatarIdFromSender()
        self.notify.debug('setAvatarChoice: avatar: ' + str(avatarId) + ' votes: ' + str(votes) + ' direction: ' + str(direction))
        self.avatarChoices[avatarId] = self.checkChoice(avatarId, votes, direction)
        self.currentVotes[avatarId] -= self.avatarChoices[avatarId][0]
        if self.currentVotes[avatarId] < 0:
            self.notify.warning('currentVotes < 0  avId=%s, currentVotes=%s' % (avatarId, self.currentVotes[avatarId]))
        self.notify.debug('currentVotes = %s' % self.currentVotes)
        self.notify.debug('avatarChoices = %s' % self.avatarChoices)
        self.sendUpdate('setAvatarChose', [avatarId])
        if self.allAvatarsChosen():
            self.notify.debug('setAvatarChoice: all avatars have chosen')
            self.gameFSM.request('processChoices')
        else:
            self.notify.debug('setAvatarChoice: still waiting for more choices')

    def checkChoice(self, avId, votes, direction):
        retDir = direction
        if direction < 0 or direction >= TravelGameGlobals.MaxDirections:
            self.notify.debug('invalid direction %d. Using 0.' % direction)
            retDir = 0
        availableVotes = self.currentVotes[avId]
        retVotes = min(votes, availableVotes)
        retVotes = max(votes, 0)
        return (retVotes, retDir)

    def allAvatarsChosen(self):
        for avId in self.avatarChoices.keys():
            choice = self.avatarChoices[avId]
            if choice[0] == -1 and not self.stateDict[avId] == EXITED:
                return False

        return True

    def isLeaf(self, switchIndex):
        retval = False
        links = TravelGameGlobals.BoardLayouts[self.boardIndex][switchIndex]['links']
        if len(links) == 0:
            retval = True
        return retval

    def giveBonusBeans(self, endingSwitch):
        noOneGotBonus = True
        for avId in self.avIdBonuses.keys():
            self.scoreDict[avId] = 0
            if self.avIdBonuses[avId][0] == endingSwitch and not self.stateDict[avId] == EXITED:
                noOneGotBonus = False
                self.scoreDict[avId] = self.avIdBonuses[avId][1]
                self.gotBonus[avId] = self.avIdBonuses[avId][1]

        if noOneGotBonus:
            for avId in self.avIdBonuses.keys():
                self.scoreDict[avId] = 1

    def checkForEndGame(self):
        self.notify.debug('checkForEndgame: ')
        self.currentSwitch = self.destSwitch
        didWeReachMiniGame = self.isLeaf(self.currentSwitch)
        numPlayers = len(self.avIdList)
        if TravelGameGlobals.SpoofFour:
            numPlayers = 4
        delay = TravelGameGlobals.DisplayVotesTimePerPlayer * (numPlayers + 1) + TravelGameGlobals.MoveTrolleyTime + TravelGameGlobals.FudgeTime
        if didWeReachMiniGame:
            self.desiredNextGame = self.switchToMinigameDict[self.currentSwitch]
            taskMgr.doMethodLater(delay, self.moveTimeoutTaskGameOver, self.taskName('move-timeout'))
            self.giveBonusBeans(self.currentSwitch)
        else:
            taskMgr.doMethodLater(delay, self.moveTimeoutTask, self.taskName('move-timeout'))
        self.sendUpdate('setServerChoices', [self.votesArray,
         self.directionArray,
         self.directionToGo,
         self.directionReason])

    def moveTimeoutTask(self, task):
        self.notify.debug('Done waiting for trolley move')
        self.gameFSM.request('waitClientsChoices')
        return Task.done

    def moveTimeoutTaskGameOver(self, task):
        self.notify.debug('Done waiting for trolley move, gmae over')
        self.gameOver()
        return Task.done

    def calcMinigames(self):
        numPlayers = len(self.avIdList)
        allowedGames = list(ToontownGlobals.MinigamePlayerMatrix[numPlayers])
        from toontown.minigame import MinigameCreatorAI
        allowedGames = MinigameCreatorAI.removeUnreleasedMinigames(allowedGames)
        self.switchToMinigameDict = {}
        for switch in TravelGameGlobals.BoardLayouts[self.boardIndex].keys():
            if self.isLeaf(switch):
                if len(allowedGames) == 0:
                    allowedGames = list(ToontownGlobals.MinigamePlayerMatrix[numPlayers])
                    allowedGames = MinigameCreatorAI.removeUnreleasedMinigames(allowedGames)
                minigame = random.choice(allowedGames)
                self.switchToMinigameDict[switch] = minigame
                allowedGames.remove(minigame)

        switches = []
        minigames = []
        for key in self.switchToMinigameDict.keys():
            switches.append(key)
            minigames.append(self.switchToMinigameDict[key])

        self.sendUpdate('setMinigames', [switches, minigames])

    def calcBonusBeans(self):
        possibleLeaves = []
        for switch in TravelGameGlobals.BoardLayouts[self.boardIndex].keys():
            if self.isLeaf(switch):
                possibleLeaves.append(switch)

        self.avIdBonuses = {}
        for avId in self.avIdList:
            switch = random.choice(possibleLeaves)
            possibleLeaves.remove(switch)
            beans = TravelGameGlobals.BoardLayouts[self.boardIndex][switch]['baseBonus']
            baseBeans = TravelGameGlobals.BaseBeans
            numPlayerMultiplier = len(self.avIdList) / 4.0
            roundMultiplier = self.metagameRound / 2.0 + 1.0
            beans *= baseBeans * numPlayerMultiplier * roundMultiplier
            self.avIdBonuses[avId] = (switch, beans)

        switches = []
        beans = []
        for avId in self.avIdList:
            switches.append(self.avIdBonuses[avId][0])
            beans.append(self.avIdBonuses[avId][1])

        self.sendUpdate('setBonuses', [switches, beans])

    def setStartingVote(self, avId, startingVote):
        DistributedMinigameAI.setStartingVote(self, avId, startingVote)
        self.currentVotes[avId] = startingVote
        self.notify.debug('setting current  vote of avId=%d to %d' % (avId, startingVote))

    def handleExitedAvatar(self, avId):
        self.notify.warning('DistrbutedTravelGameAI: handleExitedAvatar: avatar id exited: ' + str(avId))
        self.stateDict[avId] = EXITED
        allExited = True
        for avId in self.avIdList:
            if avId in self.stateDict.keys() and self.stateDict[avId] != EXITED:
                allExited = False
                break

        if allExited:
            self.setGameAbort()

    def getBoardIndex(self):
        return self.boardIndex

    def hasScoreMult(self):
        return 0
