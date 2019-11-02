from pandac.PandaModules import Point3
from direct.distributed.ClockDelta import globalClockDelta
from direct.fsm import ClassicFSM, State
from direct.task import Task
from toontown.minigame import DistributedMinigameAI
from toontown.minigame import MinigameGlobals
from toontown.minigame import IceGameGlobals
from toontown.ai.ToonBarrier import ToonBarrier

class DistributedIceGameAI(DistributedMinigameAI.DistributedMinigameAI):
    notify = directNotify.newCategory('DistributedIceGameAI')

    def __init__(self, air, minigameId):
        try:
            self.DistributedIceGameAI_initialized
        except:
            self.DistributedIceGameAI_initialized = 1
            DistributedMinigameAI.DistributedMinigameAI.__init__(self, air, minigameId)
            self.gameFSM = ClassicFSM.ClassicFSM('DistributedIceGameAI', [State.State('off', self.enterOff, self.exitOff, ['waitClientsChoices']),
             State.State('waitClientsChoices', self.enterWaitClientsChoices, self.exitWaitClientsChoices, ['cleanup', 'processChoices']),
             State.State('processChoices', self.enterProcessChoices, self.exitProcessChoices, ['waitEndingPositions', 'cleanup']),
             State.State('waitEndingPositions', self.enterWaitEndingPositions, self.exitWaitEndingPositions, ['processEndingPositions', 'cleanup']),
             State.State('processEndingPositions', self.enterProcessEndingPositions, self.exitProcessEndingPositions, ['waitClientsChoices', 'scoreMatch', 'cleanup']),
             State.State('scoreMatch', self.enterScoreMatch, self.exitScoreMatch, ['waitClientsChoices', 'finalResults', 'cleanup']),
             State.State('finalResults', self.enterFinalResults, self.exitFinalResults, ['cleanup']),
             State.State('cleanup', self.enterCleanup, self.exitCleanup, ['off'])], 'off', 'off')
            self.addChildGameFSM(self.gameFSM)
            self.avatarChoices = {}
            self.avatarEndingPositions = {}
            self.curRound = 0
            self.curMatch = 0
            self.finalEndingPositions = [Point3(IceGameGlobals.StartingPositions[0]),
             Point3(IceGameGlobals.StartingPositions[1]),
             Point3(IceGameGlobals.StartingPositions[2]),
             Point3(IceGameGlobals.StartingPositions[3])]

    def generate(self):
        self.notify.debug('generate')
        DistributedMinigameAI.DistributedMinigameAI.generate(self)

    def delete(self):
        self.notify.debug('delete')
        taskMgr.remove(self.taskName('wait-choices-timeout'))
        taskMgr.remove(self.taskName('endingPositionsTimeout'))
        del self.gameFSM
        DistributedMinigameAI.DistributedMinigameAI.delete(self)

    def setGameReady(self):
        self.notify.debug('setGameReady')
        DistributedMinigameAI.DistributedMinigameAI.setGameReady(self)
        self.numTreasures = IceGameGlobals.NumTreasures[self.getSafezoneId()]
        self.numTreasuresTaken = 0
        self.takenTreasuresTable = [0] * self.numTreasures
        self.numPenalties = IceGameGlobals.NumPenalties[self.getSafezoneId()]
        self.numPenaltiesTaken = 0
        self.takenPenaltiesTable = [0] * self.numPenalties

    def setGameStart(self, timestamp):
        self.notify.debug('setGameStart')
        DistributedMinigameAI.DistributedMinigameAI.setGameStart(self, timestamp)
        self.gameFSM.request('waitClientsChoices')

    def setGameAbort(self):
        self.notify.debug('setGameAbort')
        if self.gameFSM.getCurrentState():
            self.gameFSM.request('cleanup')
        DistributedMinigameAI.DistributedMinigameAI.setGameAbort(self)

    def gameOver(self):
        self.notify.debug('gameOver')
        self.gameFSM.request('cleanup')
        DistributedMinigameAI.DistributedMinigameAI.gameOver(self)

    def enterOff(self):
        self.notify.debug('enterOff')

    def exitOff(self):
        pass

    def enterCleanup(self):
        self.notify.debug('enterCleanup')
        self.gameFSM.request('off')

    def exitCleanup(self):
        pass

    def enterWaitClientsChoices(self):
        self.notify.debug('enterWaitClientsChoices')
        self.resetChoices()
        self.sendUpdate('setMatchAndRound', [self.curMatch, self.curRound])
        self.sendUpdate('setNewState', ['inputChoice'])
        taskMgr.doMethodLater(IceGameGlobals.InputTimeout, self.waitClientsChoicesTimeout, self.taskName('wait-choices-timeout'))
        self.sendUpdate('setTimerStartTime', [globalClockDelta.getFrameNetworkTime()])

    def exitWaitClientsChoices(self):
        self.notify.debug('exitWaitClientsChoices')
        taskMgr.remove(self.taskName('wait-choices-timeout'))

    def enterProcessChoices(self):
        forceAndHeading = []
        for avId in self.avIdList:
            force = self.avatarChoices[avId][0]
            heading = self.avatarChoices[avId][1]
            forceAndHeading.append([force, heading])

        self.notify.debug('tireInputs = %s' % forceAndHeading)
        self.sendUpdate('setTireInputs', [forceAndHeading])
        self.gameFSM.request('waitEndingPositions')

    def exitProcessChoices(self):
        pass

    def enterWaitEndingPositions(self):
        if self.curRound == 0:
            self.takenTreasuresTable = [0] * self.numTreasures
            self.takenPenaltiesTable = [0] * self.numPenalties
        taskMgr.doMethodLater(IceGameGlobals.InputTimeout, self.waitClientsChoicesTimeout, self.taskName('endingPositionsTimeout'))
        self.avatarEndingPositions = {}

    def exitWaitEndingPositions(self):
        taskMgr.remove(self.taskName('endingPositionsTimeout'))

    def enterProcessEndingPositions(self):
        averagePos = [Point3(0, 0, 0),
         Point3(0, 0, 0),
         Point3(0, 0, 0),
         Point3(0, 0, 0)]
        divisor = 0
        for avId in self.avatarEndingPositions.keys():
            divisor += 1
            oneClientEndingPositions = self.avatarEndingPositions[avId]
            avIndex = self.avIdList.index(avId)
            for index in xrange(len(oneClientEndingPositions)):
                pos = oneClientEndingPositions[index]
                averagePos[index] += Point3(pos[0], pos[1], pos[2])
                self.notify.debug('index = %d averagePos = %s' % (index, averagePos))

        sentPos = []
        if divisor:
            for newPos in averagePos:
                newPos /= divisor
                newPos.setZ(IceGameGlobals.TireRadius)
                sentPos.append([newPos[0], newPos[1], newPos[2]])

        else:
            sentPos = self.finalEndingPositions
        self.sendUpdate('setFinalPositions', [sentPos])
        self.finalEndingPositions = sentPos
        if self.curMatch == IceGameGlobals.NumMatches - 1 and self.curRound == IceGameGlobals.NumRounds - 1:
            self.gameFSM.request('scoreMatch')
        elif self.curRound == IceGameGlobals.NumRounds - 1:
            self.gameFSM.request('scoreMatch')
        else:
            self.curRound += 1
            self.sendUpdate('setMatchAndRound', [self.curMatch, self.curRound])
            self.gameFSM.request('waitClientsChoices')

    def exitProcessEndingPositions(self):
        pass

    def enterScoreMatch(self):
        sortedByDistance = []
        for avId in self.avIdList:
            index = self.avIdList.index(avId)
            pos = Point3(*self.finalEndingPositions[index])
            pos.setZ(0)
            sortedByDistance.append((avId, pos.length()))

        def compareDistance(x, y):
            if x[1] - y[1] > 0:
                return 1
            elif x[1] - y[1] < 0:
                return -1
            else:
                return 0

        sortedByDistance.sort(cmp=compareDistance)
        self.scoresAsList = []
        totalPointsAdded = 0
        for index in xrange(len(self.avIdList)):
            pos = Point3(*self.finalEndingPositions[index])
            pos.setZ(0)
            length = pos.length()
            points = length / IceGameGlobals.FarthestLength * (IceGameGlobals.PointsInCorner - IceGameGlobals.PointsDeadCenter[self.numPlayers])
            points += IceGameGlobals.PointsDeadCenter[self.numPlayers]
            self.notify.debug('length = %s points=%s avId=%d' % (length, points, avId))
            avId = self.avIdList[index]
            bonusIndex = 0
            for sortIndex in xrange(len(sortedByDistance)):
                if sortedByDistance[sortIndex][0] == avId:
                    bonusIndex = sortIndex

            bonusIndex += 4 - len(self.avIdList)
            pointsToAdd = int(points + 0.5) + IceGameGlobals.BonusPointsForPlace[bonusIndex]
            totalPointsAdded += pointsToAdd
            self.scoreDict[avId] += pointsToAdd
            self.scoresAsList.append(self.scoreDict[avId])

        self.curMatch += 1
        self.curRound = 0
        self.sendUpdate('setScores', [self.curMatch, self.curRound, self.scoresAsList])
        self.sendUpdate('setNewState', ['scoring'])

        def allToonsScoringMovieDone(self = self):
            self.notify.debug('allToonsScoringMovieDone')
            if self.curMatch == IceGameGlobals.NumMatches:
                self.gameFSM.request('finalResults')
            else:
                self.gameFSM.request('waitClientsChoices')

        def handleTimeout(avIds, self = self):
            self.notify.debug('handleTimeout: avatars %s did not report "done"' % avIds)
            if self.curMatch == IceGameGlobals.NumMatches:
                self.gameFSM.request('finalResults')
            else:
                self.gameFSM.request('waitClientsChoices')

        scoreMovieDuration = IceGameGlobals.FarthestLength * IceGameGlobals.ExpandFeetPerSec
        scoreMovieDuration += totalPointsAdded * IceGameGlobals.ScoreCountUpRate
        self.scoringMovieDoneBarrier = ToonBarrier('waitScoringMovieDone', self.uniqueName('waitScoringMovieDone'), self.avIdList, scoreMovieDuration + MinigameGlobals.latencyTolerance, allToonsScoringMovieDone, handleTimeout)

    def exitScoreMatch(self):
        self.scoringMovieDoneBarrier.cleanup()
        self.scoringMovieDoneBarrier = None
        return

    def enterFinalResults(self):
        self.checkScores()
        self.sendUpdate('setNewState', ['finalResults'])
        taskMgr.doMethodLater(IceGameGlobals.ShowScoresDuration, self.__doneShowingScores, self.taskName('waitShowScores'))

    def exitFinalResults(self):
        taskMgr.remove(self.taskName('waitShowScores'))

    def __doneShowingScores(self, task):
        self.notify.debug('doneShowingScores')
        self.gameOver()
        return Task.done

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

    def setAvatarChoice(self, force, direction):
        avatarId = self.air.getAvatarIdFromSender()
        self.notify.debug('setAvatarChoice: avatar: ' + str(avatarId) + ' votes: ' + str(force) + ' direction: ' + str(direction))
        self.avatarChoices[avatarId] = self.checkChoice(avatarId, force, direction)
        if self.allAvatarsChosen():
            self.notify.debug('setAvatarChoice: all avatars have chosen')
            self.gameFSM.request('processChoices')
        else:
            self.notify.debug('setAvatarChoice: still waiting for more choices')

    def checkChoice(self, avId, force, direction):
        retForce = force
        retDir = direction
        if retForce < 0:
            retForce = 0
        if retForce > 100:
            retForce = 100
        return (retForce, retDir)

    def allAvatarsChosen(self):
        for avId in self.avatarChoices.keys():
            choice = self.avatarChoices[avId]
            if choice[0] == -1 and not self.stateDict[avId] == DistributedMinigameAI.EXITED:
                return False

        return True

    def endingPositions(self, positions):
        if not self.gameFSM or not self.gameFSM.getCurrentState() or self.gameFSM.getCurrentState().getName() != 'waitEndingPositions':
            return
        self.notify.debug('got endingPositions from client %s' % positions)
        avId = self.air.getAvatarIdFromSender()
        self.avatarEndingPositions[avId] = positions
        if self.allAvatarsSentEndingPositions():
            self.gameFSM.request('processEndingPositions')

    def allAvatarsSentEndingPositions(self):
        if len(self.avatarEndingPositions) == len(self.avIdList):
            return True
        return False

    def endingPositionsTimeout(self, task):
        self.notify.debug('endingPositionsTimeout : did not hear from all clients')
        self.gameFSM.request('processEndingPositions')
        return Task.done

    def reportScoringMovieDone(self):
        if not self.gameFSM or not self.gameFSM.getCurrentState() or self.gameFSM.getCurrentState().getName() != 'scoreMatch':
            return
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug('reportScoringMovieDone: avatar %s is done' % avId)
        self.scoringMovieDoneBarrier.clear(avId)

    def claimTreasure(self, treasureNum):
        if not self.gameFSM or not self.gameFSM.getCurrentState() or self.gameFSM.getCurrentState().getName() != 'waitEndingPositions':
            return
        avId = self.air.getAvatarIdFromSender()
        if not self.scoreDict.has_key(avId):
            self.notify.warning('PROBLEM: avatar %s called claimTreasure(%s) but he is not in the scoreDict: %s. avIdList is: %s' % (avId,
             treasureNum,
             self.scoreDict,
             self.avIdList))
            return
        if treasureNum < 0 or treasureNum >= self.numTreasures:
            self.air.writeServerEvent('warning', treasureNum, 'MazeGameAI.claimTreasure treasureNum out of range')
            return
        if self.takenTreasuresTable[treasureNum]:
            return
        self.takenTreasuresTable[treasureNum] = 1
        avId = self.air.getAvatarIdFromSender()
        self.sendUpdate('setTreasureGrabbed', [avId, treasureNum])
        self.scoreDict[avId] += 1
        self.numTreasuresTaken += 1

    def claimPenalty(self, penaltyNum):
        if not self.gameFSM or not self.gameFSM.getCurrentState() or self.gameFSM.getCurrentState().getName() != 'waitEndingPositions':
            return
        avId = self.air.getAvatarIdFromSender()
        if not self.scoreDict.has_key(avId):
            self.notify.warning('PROBLEM: avatar %s called claimPenalty(%s) but he is not in the scoreDict: %s. avIdList is: %s' % (avId,
             penaltyNum,
             self.scoreDict,
             self.avIdList))
            return
        if penaltyNum < 0 or penaltyNum >= self.numPenalties:
            self.air.writeServerEvent('warning', penaltyNum, 'IceGameAI.claimPenalty penaltyNum out of range')
            return
        if self.takenPenaltiesTable[penaltyNum]:
            return
        self.takenPenaltiesTable[penaltyNum] = 1
        avId = self.air.getAvatarIdFromSender()
        self.sendUpdate('setPenaltyGrabbed', [avId, penaltyNum])
        self.scoreDict[avId] -= 1
        self.numPenaltiesTaken += 1

    def checkScores(self):
        self.scoresAsList = []
        for index in xrange(len(self.avIdList)):
            avId = self.avIdList[index]
            if self.scoreDict[avId] < 0:
                self.scoreDict[avId] = 1
            self.scoresAsList.append(self.scoreDict[avId])
