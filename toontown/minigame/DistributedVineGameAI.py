from DistributedMinigameAI import *
from direct.fsm import ClassicFSM, State
from direct.fsm import State
import VineGameGlobals

class DistributedVineGameAI(DistributedMinigameAI):

    def __init__(self, air, minigameId):
        try:
            self.DistributedVineGameAI_initialized
        except:
            self.DistributedVineGameAI_initialized = 1
            DistributedMinigameAI.__init__(self, air, minigameId)
            self.gameFSM = ClassicFSM.ClassicFSM('DistributedVineGameAI', [State.State('inactive', self.enterInactive, self.exitInactive, ['play']),
             State.State('play', self.enterPlay, self.exitPlay, ['cleanup', 'waitShowScores']),
             State.State('waitShowScores', self.enterWaitShowScores, self.exitWaitShowScores, ['cleanup']),
             State.State('cleanup', self.enterCleanup, self.exitCleanup, ['inactive'])], 'inactive', 'inactive')
            self.toonInfo = {}
            self.addChildGameFSM(self.gameFSM)
            self.vineSections = []
            self.finishedBonus = {}
            self.finishedTimeLeft = {}
            self.totalSpiders = 0
            self.calculatedPartialBeans = False

    def generate(self):
        self.notify.debug('generate')
        DistributedMinigameAI.generate(self)

    def delete(self):
        self.notify.debug('delete')
        del self.gameFSM
        DistributedMinigameAI.delete(self)

    def _playing(self):
        if not hasattr(self, 'gameFSM'):
            return False
        if self.gameFSM.getCurrentState() == None:
            return False
        return self.gameFSM.getCurrentState().getName() == 'play'

    def setGameReady(self):
        self.notify.debug('setGameReady')
        for avId in self.avIdList:
            self.updateToonInfo(avId, vineIndex=0, vineT=VineGameGlobals.VineStartingT)

        DistributedMinigameAI.setGameReady(self)
        self.numTreasures = VineGameGlobals.NumVines - 1
        self.numTreasuresTaken = 0
        self.takenTable = [0] * self.numTreasures
        for avId in self.scoreDict.keys():
            self.scoreDict[avId] = 0
            self.finishedBonus[avId] = 0
            self.finishedTimeLeft[avId] = -1

    def setGameStart(self, timestamp):
        self.notify.debug('setGameStart')
        DistributedMinigameAI.setGameStart(self, timestamp)
        self.gameFSM.request('play')

    def setGameAbort(self):
        self.notify.debug('setGameAbort')
        if self.gameFSM.getCurrentState():
            self.gameFSM.request('cleanup')
        DistributedMinigameAI.setGameAbort(self)

    def gameOver(self):
        self.notify.debug('gameOver')
        vineReached = []
        scoreList = []
        finishedList = []
        timeLeftList = []
        for avId in self.avIdList:
            vineReached.append(self.toonInfo[avId][0])
            scoreList.append(self.scoreDict[avId])
            finishedList.append(self.finishedBonus[avId])
            timeLeftList.append(self.finishedTimeLeft[avId])

        totalBats = len(VineGameGlobals.BatInfo[self.getSafezoneId()])
        self.air.writeServerEvent('minigame_vine', self.doId, '%s|%s|%s|%s|%s|%s|%s|%s|%s|%s' % (ToontownGlobals.VineGameId,
         self.getSafezoneId(),
         self.avIdList,
         scoreList,
         self.vineSections,
         finishedList,
         timeLeftList,
         vineReached,
         self.totalSpiders,
         totalBats))
        self.gameFSM.request('cleanup')
        DistributedMinigameAI.gameOver(self)

    def enterInactive(self):
        self.notify.debug('enterInactive')

    def exitInactive(self):
        pass

    def enterPlay(self):
        self.notify.debug('enterPlay')
        self.vines = []
        index = 0
        taskMgr.doMethodLater(VineGameGlobals.GameDuration, self.timerExpired, self.taskName('gameTimer'))

    def exitPlay(self):
        taskMgr.remove(self.taskName('gameTimer'))
        for vine in self.vines:
            vine.requestDelete()

    def enterCleanup(self):
        self.notify.debug('enterCleanup')
        self.gameFSM.request('inactive')

    def exitCleanup(self):
        pass

    def claimTreasure(self, treasureNum):
        if not self._playing():
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
        if self.takenTable[treasureNum]:
            return
        self.takenTable[treasureNum] = 1
        avId = self.air.getAvatarIdFromSender()
        self.sendUpdate('setTreasureGrabbed', [avId, treasureNum])
        self.scoreDict[avId] += 1
        self.numTreasuresTaken += 1

    def timerExpired(self, task):
        self.notify.debug('timer expired')
        if not VineGameGlobals.EndlessGame:
            self.gameFSM.request('waitShowScores')
        return Task.done

    def enterWaitShowScores(self):
        self.notify.debug('enterWaitShowScores')
        self.awardPartialBeans()
        taskMgr.doMethodLater(VineGameGlobals.ShowScoresDuration, self.__doneShowingScores, self.taskName('waitShowScores'))

    def __doneShowingScores(self, task):
        self.notify.debug('doneShowingScores')
        self.gameOver()
        return Task.done

    def exitWaitShowScores(self):
        taskMgr.remove(self.taskName('waitShowScores'))

    def reachedEndVine(self, vineIndex):
        self.notify.debug('reachedEndVine')
        return
        avId = self.air.getAvatarIdFromSender()
        oldVineIndex = self.toonInfo[avId][0]
        self.updateToonInfo(avId, vineIndex=vineIndex)
        if not oldVineIndex == vineIndex:
            self.checkForEndVine(avId)
            self.checkForEndGame()

    def setNewVine(self, avId, vineIndex, vineT, facingRight):
        self.notify.debug('setNewVine')
        if not self._playing():
            return
        if avId not in self.avIdList:
            self.air.writeServerEvent('suspicious', avId, 'VineGameAI.setNewVine: invalid avId')
            return
        oldVineIndex = self.toonInfo[avId][0]
        debugStr = 'setNewVine doId=%s avId=%d vineIndex=%s oldVineIndex=%s' % (self.doId,
         avId,
         vineIndex,
         oldVineIndex)
        self.updateToonInfo(avId, vineIndex=vineIndex, vineT=vineT, facingRight=facingRight)
        if not oldVineIndex == vineIndex:
            self.checkForEndVine(avId)
            self.checkForEndGame()

    def checkForEndGame(self):
        allDone = True
        for avId in self.toonInfo:
            if not self.toonInfo[avId][0] == VineGameGlobals.NumVines - 1:
                allDone = False
                break

        if allDone:
            if not VineGameGlobals.EndlessGame:
                self.awardPartialBeans()
                self.sendUpdate('allAtEndVine', [])
                self.gameOver()

    def checkForEndVine(self, avId):
        if self.toonInfo[avId][0] == VineGameGlobals.NumVines - 1:
            curTime = self.getCurrentGameTime()
            timeLeft = VineGameGlobals.GameDuration - curTime
            self.notify.debug('curTime =%s timeLeft = %s' % (curTime, timeLeft))
            if not self.scoreDict.has_key(avId):
                self.notify.warning('PROBLEM: avatar %s called claimTreasure(%s) but he is not in the scoreDict: %s. avIdList is: %s' % (avId,
                 treasureNum,
                 self.scoreDict,
                 self.avIdList))
                return
            addBonus = int(VineGameGlobals.BaseBonusOnEndVine[self.getSafezoneId()] + VineGameGlobals.BonusPerSecondLeft * timeLeft)
            self.notify.debug('addBOnus = %d' % addBonus)
            if addBonus < 0:
                addBonus = 0
            self.finishedBonus[avId] = addBonus
            timeLeftStr = '%.1f' % timeLeft
            self.finishedTimeLeft[avId] = timeLeftStr
            self.scoreDict[avId] += addBonus
            self.sendUpdate('setScore', [avId, self.scoreDict[avId]])

    def updateToonInfo(self, avId, vineIndex = None, vineT = None, posX = None, posZ = None, facingRight = None, climbDir = None, velX = None, velZ = None):
        newVineIndex = vineIndex
        newVineT = vineT
        newPosX = posX
        newPosZ = posZ
        newFacingRight = facingRight
        newClimbDir = climbDir
        newVelX = velX
        newVelZ = velZ
        oldInfo = None
        if self.toonInfo.has_key(avId):
            oldInfo = self.toonInfo[avId]
            if vineIndex == None:
                newVineIndex = oldInfo[0]
            if vineT == None:
                newVineT = oldInfo[1]
            if posX == None:
                newPosX = oldInfo[2]
            if posZ == None:
                newPosZ = oldInfo[3]
            if facingRight == None:
                newFacingRight = oldInfo[4]
            if climbDir == None:
                newClimbDir = oldInfo[5]
            if velX == None:
                newVelX = oldInfo[6]
            if velZ == None:
                newVelZ = oldInfo[7]
        if newVineIndex < -1 or newVineIndex >= VineGameGlobals.NumVines:
            newVineIndex = 0
        if newVineT < 0 or newVineT > 1:
            pass
        if not newFacingRight == 0 and not newFacingRight == 1:
            newFacingRight = 1
        if newPosX < -1000 or newPosX > 2000:
            newPosX = 0
        if newPosZ < -100 or newPosZ > 1000:
            newPosZ = 0
        if newVelX < -1000 or newVelX > 1000:
            newVelX = 0
        if newVelZ < -1000 or newVelZ > 1000:
            newVelZ = 0
        newInfo = [newVineIndex,
         newVineT,
         newPosX,
         newPosZ,
         newFacingRight,
         newClimbDir,
         newVelX,
         newVelZ]
        self.toonInfo[avId] = newInfo
        return

    def setupVineSections(self):
        szId = self.getSafezoneId()
        courseWeights = VineGameGlobals.CourseWeights[szId]
        pool = [[],
         [],
         [],
         [],
         [],
         []]
        for weights in courseWeights:
            section, chances = weights
            numSpiders = VineGameGlobals.getNumSpidersInSection(section)
            pool[numSpiders] += [section] * chances

        maxSpiders = VineGameGlobals.SpiderLimits[szId]
        curSpiders = 0
        for i in range(4):
            spidersLeft = maxSpiders - curSpiders
            validChoices = []
            for numSpiders in range(spidersLeft + 1):
                validChoices += pool[numSpiders]

            if not validChoices:
                self.notify.warning('we ran out of valid choices szId=%s, vineSections=%s' % (szId, self.vineSections))
                validChoices += [0]
            section = random.choice(validChoices)
            curSpiders += VineGameGlobals.getNumSpidersInSection(section)
            self.vineSections.append(section)

        self.totalSpiders = curSpiders
        self.notify.debug('calc vineSections = %s' % self.vineSections)

    def getVineSections(self):
        return self.vineSections

    def setTrolleyZone(self, trolleyZone):
        DistributedMinigameAI.setTrolleyZone(self, trolleyZone)
        self.setupVineSections()

    def awardPartialBeans(self):
        if self.calculatedPartialBeans:
            return
        self.calculatedPartialBeans = True
        for avId in self.avIdList:
            vineIndex = self.toonInfo[avId][0]
            if not vineIndex == VineGameGlobals.NumVines - 1:
                partialBeans = int(vineIndex / 5.0)
                if self.scoreDict.has_key(avId):
                    self.scoreDict[avId] += partialBeans
                    self.sendUpdate('setScore', [avId, self.scoreDict[avId]])
