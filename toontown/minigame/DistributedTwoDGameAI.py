from .DistributedMinigameAI import *
from toontown.ai.ToonBarrier import *
from direct.fsm import ClassicFSM, State
from direct.directnotify import DirectNotifyGlobal
from toontown.minigame import ToonBlitzGlobals
from math import sqrt

class DistributedTwoDGameAI(DistributedMinigameAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedTwoDGameAI')

    def __init__(self, air, minigameId):
        try:
            self.DistributedTwoDGameAI_initialized
        except:
            self.DistributedTwoDGame_initialized = 1
            DistributedMinigameAI.__init__(self, air, minigameId)
            self.gameFSM = ClassicFSM.ClassicFSM('DistributedTwoDGameAI', [State.State('inactive', self.enterInactive, self.exitInactive, ['play']), State.State('play', self.enterPlay, self.exitPlay, ['cleanup']), State.State('cleanup', self.enterCleanup, self.exitCleanup, ['inactive'])], 'inactive', 'inactive')
            self.addChildGameFSM(self.gameFSM)
            self.finishedBonusDict = {}
            self.finishedTimeLeftDict = {}
            self.numFallDownDict = {}
            self.numHitByEnemyDict = {}
            self.numSquishDict = {}
            self.treasuresCollectedDict = {}
            self.sectionsSelected = []
            self.enemyHealthTable = []
            self.treasureTakenTable = []
            self.sectionIndexList = []

    def generate(self):
        self.notify.debug('generate')
        DistributedMinigameAI.generate(self)

    def delete(self):
        self.notify.debug('delete')
        del self.gameFSM
        DistributedMinigameAI.delete(self)

    def setTrolleyZone(self, trolleyZone):
        DistributedMinigameAI.setTrolleyZone(self, trolleyZone)
        self.setupSections()

    def setGameReady(self):
        self.notify.debug('setGameReady')
        DistributedMinigameAI.setGameReady(self)
        self.numTreasures = ToonBlitzGlobals.NumTreasures
        self.numEnemies = ToonBlitzGlobals.NumEnemies
        self.numTreasuresTaken = 0
        self.numEnemiesKilled = 0
        for avId in list(self.scoreDict.keys()):
            self.scoreDict[avId] = 0
            self.finishedBonusDict[avId] = 0
            self.finishedTimeLeftDict[avId] = -1
            self.numFallDownDict[avId] = 0
            self.numHitByEnemyDict[avId] = 0
            self.numSquishDict[avId] = 0
            self.treasuresCollectedDict[avId] = [0,
             0,
             0,
             0]

        for i in range(len(self.sectionsSelected)):
            sectionIndex = self.sectionsSelected[i][0]
            attribs = ToonBlitzGlobals.SectionTypes[sectionIndex]
            enemiesPool = attribs[3]
            self.enemyHealthTable += [[]]
            enemyIndicesSelected = self.sectionsSelected[i][1]
            for j in range(len(enemyIndicesSelected)):
                enemyIndex = enemyIndicesSelected[j]
                enemyType = enemiesPool[enemyIndex][0]
                self.enemyHealthTable[i] += [ToonBlitzGlobals.EnemyBaseHealth]
                self.enemyHealthTable[i][j] *= self.numPlayers
                if enemyType in ToonBlitzGlobals.EnemyHealthMultiplier:
                    self.enemyHealthTable[i][j] *= ToonBlitzGlobals.EnemyHealthMultiplier[enemyType]

            self.treasureTakenTable += [[]]
            treasureIndicesSelected = self.sectionsSelected[i][2]
            for j in range(len(treasureIndicesSelected)):
                self.treasureTakenTable[i] += [0]

            enemyIndicesSelected = self.sectionsSelected[i][1]
            for j in range(len(enemyIndicesSelected)):
                self.treasureTakenTable[i] += [0]

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
        scoreList = []
        finishedBonusList = []
        timeLeftList = []
        treasureCollectedList = []
        playerErrorList = []
        for avId in self.avIdList:
            scoreList.append(self.scoreDict[avId])
            finishedBonusList.append(self.finishedBonusDict[avId])
            timeLeftList.append(self.finishedTimeLeftDict[avId])
            treasureCollectedList.append(self.treasuresCollectedDict[avId])
            playerError = [self.numFallDownDict[avId], self.numHitByEnemyDict[avId], self.numSquishDict[avId]]
            playerErrorList.append(playerError)
            self.scoreDict[avId] = max(0, self.scoreDict[avId])
            jellybeans = sqrt(self.scoreDict[avId] * ToonBlitzGlobals.ScoreToJellyBeansMultiplier)
            self.scoreDict[avId] = max(1, int(jellybeans))

        self.air.writeServerEvent('minigame_twoD', self.doId, '%s|%s|%s|%s|%s|%s|%s|%s|%s' % (ToontownGlobals.TwoDGameId,
         self.getSafezoneId(),
         self.avIdList,
         scoreList,
         finishedBonusList,
         timeLeftList,
         treasureCollectedList,
         playerErrorList,
         self.sectionIndexList))
        self.notify.debug('minigame_twoD%s: %s|%s|%s|%s|%s|%s|%s|%s|%s' % (self.doId,
         ToontownGlobals.TwoDGameId,
         self.getSafezoneId(),
         self.avIdList,
         scoreList,
         finishedBonusList,
         timeLeftList,
         treasureCollectedList,
         playerErrorList,
         self.sectionIndexList))
        self.gameFSM.request('cleanup')
        DistributedMinigameAI.gameOver(self)

    def enterInactive(self):
        self.notify.debug('enterInactive')

    def exitInactive(self):
        pass

    def enterPlay(self):
        self.notify.debug('enterPlay')

        def allToonsDone(self = self):
            self.notify.debug('allToonsDone')
            self.sendUpdate('setEveryoneDone')
            if not ToonBlitzGlobals.EndlessGame:
                self.gameOver()

        def handleTimeout(avIds, self = self):
            self.notify.debug('handleTimeout: avatars %s did not report "done"' % avIds)
            self.setGameAbort()

        self.doneBarrier = ToonBarrier('waitClientsDone', self.uniqueName('waitClientsDone'), self.avIdList, ToonBlitzGlobals.GameDuration[self.getSafezoneId()] + ToonBlitzGlobals.ShowScoresDuration + MinigameGlobals.latencyTolerance, allToonsDone, handleTimeout)

    def exitPlay(self):
        pass

    def enterCleanup(self):
        self.notify.debug('enterCleanup')
        self.doneBarrier.cleanup()
        del self.doneBarrier
        self.gameFSM.request('inactive')

    def exitCleanup(self):
        pass

    def claimTreasure(self, sectionIndex, treasureIndex):
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug('treasure %s-%s claimed by %s' % (sectionIndex, treasureIndex, avId))
        if sectionIndex < 0 or sectionIndex >= len(self.sectionsSelected):
            self.air.writeServerEvent('warning', sectionIndex, 'TwoDGameAI.claimTreasure sectionIndex out of range.')
            return
        if treasureIndex < 0 or treasureIndex >= len(self.treasureTakenTable[sectionIndex]):
            self.notify.warning('Treasure %s: TwoDGameAI.claimTreasure treasureIndex out of range.' % treasureIndex)
            self.air.writeServerEvent('warning', treasureIndex, 'TwoDGameAI.claimTreasure treasureIndex out of range.')
            return
        if self.treasureTakenTable[sectionIndex][treasureIndex]:
            return
        initialTreasureList = self.sectionsSelected[sectionIndex][2]
        if treasureIndex < len(initialTreasureList):
            treasureValue = initialTreasureList[treasureIndex][1]
        else:
            treasureValue = self.numPlayers
        self.treasureTakenTable[sectionIndex][treasureIndex] = treasureValue
        self.treasuresCollectedDict[avId][treasureValue - 1] += 1
        self.scoreDict[avId] += ToonBlitzGlobals.ScoreGainPerTreasure * treasureValue
        self.numTreasuresTaken += 1
        self.sendUpdate('setTreasureGrabbed', [avId, sectionIndex, treasureIndex])

    def claimEnemyShot(self, sectionIndex, enemyIndex):
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug('enemy %s-%s shot claimed by %s' % (sectionIndex, enemyIndex, avId))
        if sectionIndex < 0 or sectionIndex >= len(self.sectionsSelected):
            self.air.writeServerEvent('warning', sectionIndex, 'TwoDGameAI.claimEnemyShot sectionIndex out of range.')
            return
        if enemyIndex < 0 or enemyIndex >= len(self.sectionsSelected[sectionIndex][1]):
            self.air.writeServerEvent('warning', enemyIndex, 'TwoDGameAI.claimEnemyShot enemyIndex out of range.')
            return
        if self.enemyHealthTable[sectionIndex][enemyIndex] > 0:
            self.enemyHealthTable[sectionIndex][enemyIndex] -= ToonBlitzGlobals.DamagePerBullet
            if self.enemyHealthTable[sectionIndex][enemyIndex] <= 0:
                self.numEnemiesKilled += 1
            self.sendUpdate('setEnemyShot', [avId,
             sectionIndex,
             enemyIndex,
             self.enemyHealthTable[sectionIndex][enemyIndex]])

    def reportDone(self):
        if self.gameFSM.getCurrentState() == None or self.gameFSM.getCurrentState().getName() != 'play':
            return
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug('reportDone: avatar %s is done' % avId)
        self.doneBarrier.clear(avId)
        return

    def toonVictory(self, avId, timestamp):
        if self.gameFSM.getCurrentState() == None or self.gameFSM.getCurrentState().getName() != 'play':
            msg = 'TwoDGameAI.toonVictory not in play state!'
            self.notify.warning('suspicious: ' + str(avId) + ' ' + msg)
            self.air.writeServerEvent('suspicious: ', avId, msg)
            return
        if avId not in list(self.scoreDict.keys()):
            self.notify.warning('Avatar %s not in list.' % avId)
            self.air.writeServerEvent('suspicious: ', avId, 'TwoDGameAI.toonVictory toon not in list.')
            return
        curTime = self.getCurrentGameTime()
        timeLeft = ToonBlitzGlobals.GameDuration[self.getSafezoneId()] - curTime
        self.notify.debug('curTime =%s timeLeft = %s' % (curTime, timeLeft))
        addBonus = int(ToonBlitzGlobals.BaseBonusOnCompletion[self.getSafezoneId()] + ToonBlitzGlobals.BonusPerSecondLeft * timeLeft)
        self.notify.debug('addBOnus = %d' % addBonus)
        if addBonus < 0:
            addBonus = 0
        self.finishedBonusDict[avId] = addBonus
        timeLeftStr = '%.1f' % timeLeft
        self.finishedTimeLeftDict[avId] = timeLeftStr
        self.scoreDict[avId] += addBonus
        self.sendUpdate('addVictoryScore', [avId, addBonus])
        self.doneBarrier.clear(avId)
        return

    def toonFellDown(self, avId, timestamp):
        if avId not in list(self.scoreDict.keys()):
            self.notify.warning('Avatar %s not in list.' % avId)
            self.air.writeServerEvent('warning', avId, 'TwoDGameAI.toonFellDown toon not in list.')
            return
        self.numFallDownDict[avId] += 1
        self.scoreDict[avId] += ToonBlitzGlobals.ScoreLossPerFallDown[self.getSafezoneId()]

    def toonHitByEnemy(self, avId, timestamp):
        if avId not in list(self.scoreDict.keys()):
            self.notify.warning('Avatar %s not in list.' % avId)
            self.air.writeServerEvent('warning', avId, 'TwoDGameAI.toonHitByEnemy toon not in list.')
            return
        self.numHitByEnemyDict[avId] += 1
        self.scoreDict[avId] += ToonBlitzGlobals.ScoreLossPerEnemyCollision[self.getSafezoneId()]

    def toonSquished(self, avId, timestamp):
        if avId not in list(self.scoreDict.keys()):
            self.notify.warning('Avatar %s not in list.' % avId)
            self.air.writeServerEvent('warning', avId, 'TwoDGameAI.toonSquished toon not in list.')
            return
        self.numSquishDict[avId] += 1
        self.scoreDict[avId] += ToonBlitzGlobals.ScoreLossPerStomperSquish[self.getSafezoneId()]

    def setupSections(self):
        szId = self.getSafezoneId()
        sectionWeights = ToonBlitzGlobals.SectionWeights[szId]
        numSections = ToonBlitzGlobals.NumSections[szId]
        difficultyPool = []
        difficultyList = []
        sectionsPool = ToonBlitzGlobals.SectionsPool
        sectionTypes = ToonBlitzGlobals.SectionTypes
        sectionsPoolByDifficulty = [[],
         [],
         [],
         [],
         [],
         []]
        sectionsSelectedByDifficulty = [[],
         [],
         [],
         [],
         [],
         []]
        sectionIndicesSelected = []
        for weight in sectionWeights:
            difficulty, probability = weight
            difficultyPool += [difficulty] * probability

        for i in range(numSections):
            difficulty = random.choice(difficultyPool)
            difficultyList.append(difficulty)

        difficultyList.sort()
        for sectionIndex in sectionsPool:
            difficulty = sectionTypes[sectionIndex][0]
            sectionsPoolByDifficulty[difficulty] += [sectionIndex]

        for targetDifficulty in difficultyList:
            whileCount = 0
            difficulty = targetDifficulty
            while not len(sectionsPoolByDifficulty[difficulty]) > 0:
                difficulty += 1
                if difficulty >= 5:
                    difficulty = 0
                    whileCount += 1
                    if whileCount > 1:
                        break
            else:
                sectionIndexChoice = random.choice(sectionsPoolByDifficulty[difficulty])
                sectionsSelectedByDifficulty[difficulty] += [sectionIndexChoice]
                sectionsPoolByDifficulty[difficulty].remove(sectionIndexChoice)

            if whileCount > 1:
                self.notify.debug('We need more sections than we have choices. We have to now repeat.')

        for i in range(len(sectionsSelectedByDifficulty)):
            for j in range(len(sectionsSelectedByDifficulty[i])):
                sectionIndicesSelected.append(sectionsSelectedByDifficulty[i][j])

        for i in range(len(sectionIndicesSelected)):
            sectionIndex = sectionIndicesSelected[i]
            self.sectionIndexList.append(sectionIndex)
            attribs = sectionTypes[sectionIndex]
            difficulty = attribs[0]
            length = attribs[1]
            blocksPool = attribs[2]
            enemiesPool = attribs[3]
            treasuresPool = attribs[4]
            spawnPointsPool = attribs[5]
            stompersPool = attribs[6]
            enemyIndicesPool = []
            enemyIndicesSelected = []
            if enemiesPool != None:
                minEnemies, maxEnemies = attribs[7]
                for i in range(len(enemiesPool)):
                    enemyIndicesPool += [i]

                numEnemies = maxEnemies * ToonBlitzGlobals.PercentMaxEnemies[szId] / 100
                numEnemies = max(numEnemies, minEnemies)
                for j in range(int(numEnemies)):
                    if len(enemyIndicesPool) == 0:
                        break
                    enemyIndex = random.choice(enemyIndicesPool)
                    enemyIndicesSelected.append(enemyIndex)
                    enemyIndicesPool.remove(enemyIndex)

                enemyIndicesSelected.sort()
            treasureIndicesPool = []
            treasureValuePool = []
            for value in range(1, 5):
                treasureValuePool += [value] * ToonBlitzGlobals.TreasureValueProbability[value]

            treasureIndicesSelected = []
            if treasuresPool != None:
                minTreasures, maxTreasures = attribs[8]
                for i in range(len(treasuresPool)):
                    treasureIndicesPool += [i]

                numTreasures = maxTreasures * ToonBlitzGlobals.PercentMaxTreasures[szId] / 100
                numTreasures = max(numTreasures, minTreasures)
                for i in range(int(numTreasures)):
                    if len(treasureIndicesPool) == 0:
                        break
                    treasureIndex = random.choice(treasureIndicesPool)
                    treasureValue = random.choice(treasureValuePool)
                    treasure = (treasureIndex, treasureValue)
                    treasureIndicesPool.remove(treasureIndex)
                    treasureIndicesSelected.append(treasure)

                treasureIndicesSelected.sort()
            spawnPointIndicesPool = []
            spawnPointIndicesSelected = []
            if spawnPointsPool != None:
                minSpawnPoints, maxSpawnPoints = attribs[9]
                for i in range(len(spawnPointsPool)):
                    spawnPointIndicesPool += [i]

                numSpawnPoints = maxSpawnPoints * ToonBlitzGlobals.PercentMaxSpawnPoints[szId] / 100
                numSpawnPoints = max(numSpawnPoints, minSpawnPoints)
                for i in range(int(numSpawnPoints)):
                    if len(spawnPointIndicesPool) == 0:
                        break
                    spawnPoint = random.choice(spawnPointIndicesPool)
                    spawnPointIndicesSelected.append(spawnPoint)
                    spawnPointIndicesPool.remove(spawnPoint)

                spawnPointIndicesSelected.sort()
            stomperIndicesPool = []
            stomperIndicesSelected = []
            if stompersPool != None:
                minStompers, maxStompers = attribs[10]
                for i in range(len(stompersPool)):
                    stomperIndicesPool += [i]

                numStompers = maxStompers * ToonBlitzGlobals.PercentMaxStompers[szId] / 100
                numStompers = max(numStompers, minStompers)
                for i in range(int(numStompers)):
                    if len(stomperIndicesPool) == 0:
                        break
                    stomper = random.choice(stomperIndicesPool)
                    stomperIndicesSelected.append(stomper)
                    stomperIndicesPool.remove(stomper)

                stomperIndicesSelected.sort()
            sctionTuple = (sectionIndex,
             enemyIndicesSelected,
             treasureIndicesSelected,
             spawnPointIndicesSelected,
             stomperIndicesSelected)
            self.sectionsSelected.append(sctionTuple)

        return

    def getSectionsSelected(self):
        return self.sectionsSelected
