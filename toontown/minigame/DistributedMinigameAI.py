from otp.ai.AIBase import *
from direct.distributed.ClockDelta import *
from toontown.ai.ToonBarrier import *
from direct.distributed import DistributedObjectAI
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from toontown.shtiker import PurchaseManagerAI
from toontown.shtiker import NewbiePurchaseManagerAI
from . import MinigameCreatorAI
from direct.task import Task
import random
from . import MinigameGlobals
from direct.showbase import PythonUtil
from . import TravelGameGlobals
from toontown.toonbase import ToontownGlobals
EXITED = 0
EXPECTED = 1
JOINED = 2
READY = 3
DEFAULT_POINTS = 1
MAX_POINTS = 7
JOIN_TIMEOUT = 40.0 + MinigameGlobals.latencyTolerance
READY_TIMEOUT = MinigameGlobals.MaxLoadTime + MinigameGlobals.rulesDuration + MinigameGlobals.latencyTolerance
EXIT_TIMEOUT = 20.0 + MinigameGlobals.latencyTolerance

class DistributedMinigameAI(DistributedObjectAI.DistributedObjectAI):
    notify = directNotify.newCategory('DistributedMinigameAI')

    def __init__(self, air, minigameId):
        try:
            self.DistributedMinigameAI_initialized
        except:
            self.DistributedMinigameAI_initialized = 1
            DistributedObjectAI.DistributedObjectAI.__init__(self, air)
            self.minigameId = minigameId
            self.frameworkFSM = ClassicFSM.ClassicFSM('DistributedMinigameAI', [State.State('frameworkOff', self.enterFrameworkOff, self.exitFrameworkOff, ['frameworkWaitClientsJoin']),
             State.State('frameworkWaitClientsJoin', self.enterFrameworkWaitClientsJoin, self.exitFrameworkWaitClientsJoin, ['frameworkWaitClientsReady', 'frameworkWaitClientsExit', 'frameworkCleanup']),
             State.State('frameworkWaitClientsReady', self.enterFrameworkWaitClientsReady, self.exitFrameworkWaitClientsReady, ['frameworkGame', 'frameworkWaitClientsExit', 'frameworkCleanup']),
             State.State('frameworkGame', self.enterFrameworkGame, self.exitFrameworkGame, ['frameworkWaitClientsExit', 'frameworkCleanup']),
             State.State('frameworkWaitClientsExit', self.enterFrameworkWaitClientsExit, self.exitFrameworkWaitClientsExit, ['frameworkCleanup']),
             State.State('frameworkCleanup', self.enterFrameworkCleanup, self.exitFrameworkCleanup, ['frameworkOff'])], 'frameworkOff', 'frameworkOff')
            self.frameworkFSM.enterInitialState()
            self.avIdList = []
            self.stateDict = {}
            self.scoreDict = {}
            self.difficultyOverride = None
            self.trolleyZoneOverride = None
            self.metagameRound = -1
            self.startingVotes = {}

        return

    def addChildGameFSM(self, gameFSM):
        self.frameworkFSM.getStateNamed('frameworkGame').addChild(gameFSM)

    def removeChildGameFSM(self, gameFSM):
        self.frameworkFSM.getStateNamed('frameworkGame').removeChild(gameFSM)

    def setExpectedAvatars(self, avIds):
        self.avIdList = avIds
        self.numPlayers = len(self.avIdList)
        self.notify.debug('BASE: setExpectedAvatars: expecting avatars: ' + str(self.avIdList))

    def setNewbieIds(self, newbieIds):
        self.newbieIdList = newbieIds
        if len(self.newbieIdList) > 0:
            self.notify.debug('BASE: setNewbieIds: %s' % self.newbieIdList)

    def setTrolleyZone(self, trolleyZone):
        self.trolleyZone = trolleyZone

    def setDifficultyOverrides(self, difficultyOverride, trolleyZoneOverride):
        self.difficultyOverride = difficultyOverride
        if self.difficultyOverride is not None:
            self.difficultyOverride = MinigameGlobals.QuantizeDifficultyOverride(difficultyOverride)
        self.trolleyZoneOverride = trolleyZoneOverride
        return

    def setMetagameRound(self, roundNum):
        self.metagameRound = roundNum

    def _playing(self):
        if not hasattr(self, 'gameFSM'):
            return False
        if self.gameFSM.getCurrentState() == None:
            return False
        return self.gameFSM.getCurrentState().getName() == 'play'

    def _inState(self, states):
        if not hasattr(self, 'gameFSM'):
            return False
        if self.gameFSM.getCurrentState() == None:
            return False
        return self.gameFSM.getCurrentState().getName() in makeList(states)

    def generate(self):
        DistributedObjectAI.DistributedObjectAI.generate(self)
        self.frameworkFSM.request('frameworkWaitClientsJoin')

    def delete(self):
        self.notify.debug('BASE: delete: deleting AI minigame object')
        del self.frameworkFSM
        self.ignoreAll()
        DistributedObjectAI.DistributedObjectAI.delete(self)

    def isSinglePlayer(self):
        if self.numPlayers == 1:
            return 1
        else:
            return 0

    def getParticipants(self):
        return self.avIdList

    def getTrolleyZone(self):
        return self.trolleyZone

    def getDifficultyOverrides(self):
        response = [self.difficultyOverride, self.trolleyZoneOverride]
        if response[0] is None:
            response[0] = MinigameGlobals.NoDifficultyOverride
        else:
            response[0] *= MinigameGlobals.DifficultyOverrideMult
            response[0] = int(response[0])
        if response[1] is None:
            response[1] = MinigameGlobals.NoTrolleyZoneOverride
        return response

    def b_setGameReady(self):
        self.setGameReady()
        self.d_setGameReady()

    def d_setGameReady(self):
        self.notify.debug('BASE: Sending setGameReady')
        self.sendUpdate('setGameReady', [])

    def setGameReady(self):
        self.notify.debug('BASE: setGameReady: game ready with avatars: %s' % self.avIdList)
        self.normalExit = 1

    def b_setGameStart(self, timestamp):
        self.d_setGameStart(timestamp)
        self.setGameStart(timestamp)

    def d_setGameStart(self, timestamp):
        self.notify.debug('BASE: Sending setGameStart')
        self.sendUpdate('setGameStart', [timestamp])

    def setGameStart(self, timestamp):
        self.notify.debug('BASE: setGameStart')

    def b_setGameExit(self):
        self.d_setGameExit()
        self.setGameExit()

    def d_setGameExit(self):
        self.notify.debug('BASE: Sending setGameExit')
        self.sendUpdate('setGameExit', [])

    def setGameExit(self):
        self.notify.debug('BASE: setGameExit')

    def setGameAbort(self):
        self.notify.debug('BASE: setGameAbort')
        self.normalExit = 0
        self.sendUpdate('setGameAbort', [])
        self.frameworkFSM.request('frameworkCleanup')

    def handleExitedAvatar(self, avId):
        self.notify.warning('BASE: handleExitedAvatar: avatar id exited: ' + str(avId))
        self.stateDict[avId] = EXITED
        self.setGameAbort()

    def gameOver(self):
        self.notify.debug('BASE: gameOver')
        self.frameworkFSM.request('frameworkWaitClientsExit')

    def enterFrameworkOff(self):
        self.notify.debug('BASE: enterFrameworkOff')

    def exitFrameworkOff(self):
        pass

    def enterFrameworkWaitClientsJoin(self):
        self.notify.debug('BASE: enterFrameworkWaitClientsJoin')
        for avId in self.avIdList:
            self.stateDict[avId] = EXPECTED
            self.scoreDict[avId] = DEFAULT_POINTS
            self.acceptOnce(self.air.getAvatarExitEvent(avId), self.handleExitedAvatar, extraArgs=[avId])

        def allAvatarsJoined(self = self):
            self.notify.debug('BASE: all avatars joined')
            self.b_setGameReady()
            self.frameworkFSM.request('frameworkWaitClientsReady')

        def handleTimeout(avIds, self = self):
            self.notify.debug('BASE: timed out waiting for clients %s to join' % avIds)
            self.setGameAbort()

        self.__barrier = ToonBarrier('waitClientsJoin', self.uniqueName('waitClientsJoin'), self.avIdList, JOIN_TIMEOUT, allAvatarsJoined, handleTimeout)

    def setAvatarJoined(self):
        if self.frameworkFSM.getCurrentState().getName() != 'frameworkWaitClientsJoin':
            self.notify.debug('BASE: Ignoring setAvatarJoined message')
            return
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug('BASE: setAvatarJoined: avatar id joined: ' + str(avId))
        self.air.writeServerEvent('minigame_joined', avId, '%s|%s' % (self.minigameId, self.trolleyZone))
        self.stateDict[avId] = JOINED
        self.notify.debug('BASE: setAvatarJoined: new states: ' + str(self.stateDict))
        self.__barrier.clear(avId)

    def exitFrameworkWaitClientsJoin(self):
        self.__barrier.cleanup()
        del self.__barrier

    def enterFrameworkWaitClientsReady(self):
        self.notify.debug('BASE: enterFrameworkWaitClientsReady')

        def allAvatarsReady(self = self):
            self.notify.debug('BASE: all avatars ready')
            self.frameworkFSM.request('frameworkGame')

        def handleTimeout(avIds, self = self):
            self.notify.debug("BASE: timed out waiting for clients %s to report 'ready'" % avIds)
            self.setGameAbort()

        self.__barrier = ToonBarrier('waitClientsReady', self.uniqueName('waitClientsReady'), self.avIdList, READY_TIMEOUT, allAvatarsReady, handleTimeout)
        for avId in list(self.stateDict.keys()):
            if self.stateDict[avId] == READY:
                self.__barrier.clear(avId)

        self.notify.debug('  safezone: %s' % self.getSafezoneId())
        self.notify.debug('difficulty: %s' % self.getDifficulty())

    def setAvatarReady(self):
        if self.frameworkFSM.getCurrentState().getName() not in ['frameworkWaitClientsReady', 'frameworkWaitClientsJoin']:
            self.notify.debug('BASE: Ignoring setAvatarReady message')
            return
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug('BASE: setAvatarReady: avatar id ready: ' + str(avId))
        self.stateDict[avId] = READY
        self.notify.debug('BASE: setAvatarReady: new avId states: ' + str(self.stateDict))
        if self.frameworkFSM.getCurrentState().getName() == 'frameworkWaitClientsReady':
            self.__barrier.clear(avId)

    def exitFrameworkWaitClientsReady(self):
        self.__barrier.cleanup()
        del self.__barrier

    def enterFrameworkGame(self):
        self.notify.debug('BASE: enterFrameworkGame')
        self.gameStartTime = globalClock.getRealTime()
        self.b_setGameStart(globalClockDelta.localToNetworkTime(self.gameStartTime))

    def exitFrameworkGame(self):
        pass

    def enterFrameworkWaitClientsExit(self):
        self.notify.debug('BASE: enterFrameworkWaitClientsExit')
        self.b_setGameExit()

        def allAvatarsExited(self = self):
            self.notify.debug('BASE: all avatars exited')
            self.frameworkFSM.request('frameworkCleanup')

        def handleTimeout(avIds, self = self):
            self.notify.debug('BASE: timed out waiting for clients %s to exit' % avIds)
            self.frameworkFSM.request('frameworkCleanup')

        self.__barrier = ToonBarrier('waitClientsExit', self.uniqueName('waitClientsExit'), self.avIdList, EXIT_TIMEOUT, allAvatarsExited, handleTimeout)
        for avId in list(self.stateDict.keys()):
            if self.stateDict[avId] == EXITED:
                self.__barrier.clear(avId)

    def setAvatarExited(self):
        if self.frameworkFSM.getCurrentState().getName() != 'frameworkWaitClientsExit':
            self.notify.debug('BASE: Ignoring setAvatarExit message')
            return
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug('BASE: setAvatarExited: avatar id exited: ' + str(avId))
        self.stateDict[avId] = EXITED
        self.notify.debug('BASE: setAvatarExited: new avId states: ' + str(self.stateDict))
        self.__barrier.clear(avId)

    def exitFrameworkWaitClientsExit(self):
        self.__barrier.cleanup()
        del self.__barrier

    def hasScoreMult(self):
        return 1

    def enterFrameworkCleanup(self):
        self.notify.debug('BASE: enterFrameworkCleanup: normalExit=%s' % self.normalExit)
        scoreMult = MinigameGlobals.getScoreMult(self.getSafezoneId())
        if not self.hasScoreMult():
            scoreMult = 1.0
        self.notify.debug('score multiplier: %s' % scoreMult)
        for avId in self.avIdList:
            self.scoreDict[avId] *= scoreMult

        scoreList = []
        if not self.normalExit:
            randReward = random.randrange(DEFAULT_POINTS, MAX_POINTS + 1)
        for avId in self.avIdList:
            if self.normalExit:
                score = int(self.scoreDict[avId] + 0.5)
            else:
                score = randReward
            if ToontownGlobals.JELLYBEAN_TROLLEY_HOLIDAY in simbase.air.holidayManager.currentHolidays or ToontownGlobals.JELLYBEAN_TROLLEY_HOLIDAY_MONTH in simbase.air.holidayManager.currentHolidays:
                score *= MinigameGlobals.JellybeanTrolleyHolidayScoreMultiplier
            logEvent = False
            if score > 255:
                score = 255
                logEvent = True
            elif score < 0:
                score = 0
                logEvent = True
            if logEvent:
                self.air.writeServerEvent('suspicious', avId, 'got %s jellybeans playing minigame %s in zone %s' % (score, self.minigameId, self.getSafezoneId()))
            scoreList.append(score)

        self.requestDelete()
        if self.metagameRound > -1:
            self.handleMetagamePurchaseManager(scoreList)
        else:
            self.handleRegularPurchaseManager(scoreList)
        self.frameworkFSM.request('frameworkOff')

    def handleMetagamePurchaseManager(self, scoreList):
        self.notify.debug('self.newbieIdList = %s' % self.newbieIdList)
        votesToUse = self.startingVotes
        if hasattr(self, 'currentVotes'):
            votesToUse = self.currentVotes
        votesArray = []
        for avId in self.avIdList:
            if avId in votesToUse:
                votesArray.append(votesToUse[avId])
            else:
                self.notify.warning('votesToUse=%s does not have avId=%d' % (votesToUse, avId))
                votesArray.append(0)

        if self.metagameRound < TravelGameGlobals.FinalMetagameRoundIndex:
            newRound = self.metagameRound
            if not self.minigameId == ToontownGlobals.TravelGameId:
                for index in range(len(scoreList)):
                    votesArray[index] += scoreList[index]

            self.notify.debug('votesArray = %s' % votesArray)
            desiredNextGame = None
            if hasattr(self, 'desiredNextGame'):
                desiredNextGame = self.desiredNextGame
            numToons = 0
            lastAvId = 0
            for avId in self.avIdList:
                av = simbase.air.doId2do.get(avId)
                if av:
                    numToons += 1
                    lastAvId = avId

            doNewbie = False
            if numToons == 1 and lastAvId in self.newbieIdList:
                doNewbie = True
            if doNewbie:
                pm = NewbiePurchaseManagerAI.NewbiePurchaseManagerAI(self.air, lastAvId, self.avIdList, scoreList, self.minigameId, self.trolleyZone)
                MinigameCreatorAI.acquireMinigameZone(self.zoneId)
                pm.generateWithRequired(self.zoneId)
            else:
                pm = PurchaseManagerAI.PurchaseManagerAI(self.air, self.avIdList, scoreList, self.minigameId, self.trolleyZone, self.newbieIdList, votesArray, newRound, desiredNextGame)
                pm.generateWithRequired(self.zoneId)
        else:
            self.notify.debug('last minigame, handling newbies')
            if ToontownGlobals.JELLYBEAN_TROLLEY_HOLIDAY in simbase.air.holidayManager.currentHolidays or ToontownGlobals.JELLYBEAN_TROLLEY_HOLIDAY_MONTH in simbase.air.holidayManager.currentHolidays:
                votesArray = [MinigameGlobals.JellybeanTrolleyHolidayScoreMultiplier * x for x in votesArray]
            for id in self.newbieIdList:
                pm = NewbiePurchaseManagerAI.NewbiePurchaseManagerAI(self.air, id, self.avIdList, scoreList, self.minigameId, self.trolleyZone)
                MinigameCreatorAI.acquireMinigameZone(self.zoneId)
                pm.generateWithRequired(self.zoneId)

            if len(self.avIdList) > len(self.newbieIdList):
                pm = PurchaseManagerAI.PurchaseManagerAI(self.air, self.avIdList, scoreList, self.minigameId, self.trolleyZone, self.newbieIdList, votesArray=votesArray, metagameRound=self.metagameRound)
                pm.generateWithRequired(self.zoneId)
        return

    def handleRegularPurchaseManager(self, scoreList):
        for id in self.newbieIdList:
            pm = NewbiePurchaseManagerAI.NewbiePurchaseManagerAI(self.air, id, self.avIdList, scoreList, self.minigameId, self.trolleyZone)
            MinigameCreatorAI.acquireMinigameZone(self.zoneId)
            pm.generateWithRequired(self.zoneId)

        if len(self.avIdList) > len(self.newbieIdList):
            pm = PurchaseManagerAI.PurchaseManagerAI(self.air, self.avIdList, scoreList, self.minigameId, self.trolleyZone, self.newbieIdList)
            pm.generateWithRequired(self.zoneId)

    def exitFrameworkCleanup(self):
        pass

    def requestExit(self):
        self.notify.debug('BASE: requestExit: client has requested the game to end')
        self.setGameAbort()

    def local2GameTime(self, timestamp):
        return timestamp - self.gameStartTime

    def game2LocalTime(self, timestamp):
        return timestamp + self.gameStartTime

    def getCurrentGameTime(self):
        return self.local2GameTime(globalClock.getFrameTime())

    def getDifficulty(self):
        if self.difficultyOverride is not None:
            return self.difficultyOverride
        if hasattr(self.air, 'minigameDifficulty'):
            return float(self.air.minigameDifficulty)
        return MinigameGlobals.getDifficulty(self.getSafezoneId())

    def getSafezoneId(self):
        if self.trolleyZoneOverride is not None:
            return self.trolleyZoneOverride
        if hasattr(self.air, 'minigameSafezoneId'):
            return MinigameGlobals.getSafezoneId(self.air.minigameSafezoneId)
        return MinigameGlobals.getSafezoneId(self.trolleyZone)

    def logPerfectGame(self, avId):
        self.air.writeServerEvent('perfectMinigame', avId, '%s|%s|%s' % (self.minigameId, self.trolleyZone, self.avIdList))

    def logAllPerfect(self):
        for avId in self.avIdList:
            self.logPerfectGame(avId)

    def getStartingVotes(self):
        retval = []
        for avId in self.avIdList:
            if avId in self.startingVotes:
                retval.append(self.startingVotes[avId])
            else:
                self.notify.warning('how did this happen? avId=%d not in startingVotes %s' % (avId, self.startingVotes))
                retval.append(0)

        return retval

    def setStartingVote(self, avId, startingVote):
        self.startingVotes[avId] = startingVote
        self.notify.debug('setting starting vote of avId=%d to %d' % (avId, startingVote))

    def getMetagameRound(self):
        return self.metagameRound
