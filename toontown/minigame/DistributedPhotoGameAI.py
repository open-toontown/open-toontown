from DistributedMinigameAI import *
from direct.distributed.ClockDelta import *
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from direct.task import Task
import PhotoGameGlobals
from toontown.minigame import PhotoGameBase
import random

class DistributedPhotoGameAI(DistributedMinigameAI, PhotoGameBase.PhotoGameBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPhotoGameAI')

    def __init__(self, air, minigameId):
        DistributedMinigameAI.__init__(self, air, minigameId)
        PhotoGameBase.PhotoGameBase.__init__(self)
        self.gameFSM = ClassicFSM.ClassicFSM('DistributedPhotoGameAI', [State.State('inactive', self.enterInactive, self.exitInactive, ['play']), State.State('play', self.enterPlay, self.exitPlay, ['cleanup']), State.State('cleanup', self.enterCleanup, self.exitCleanup, ['inactive'])], 'inactive', 'inactive')
        self.addChildGameFSM(self.gameFSM)

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
        assignmentTemplates = self.generateAssignmentTemplates(PhotoGameGlobals.ONSCREENASSIGNMENTS)
        self.assignmentData = self.generateAssignmentData(assignmentTemplates)
        self.gameFSM.request('play')
        self.filmCountList = [0,
         0,
         0,
         0]

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

    def enterPlay(self):
        self.notify.debug('enterPlay')
        if not config.GetBool('endless-photo-game', 0):
            taskMgr.doMethodLater(self.data['TIME'], self.timerExpired, self.taskName('gameTimer'))

    def timerExpired(self, task = None):
        self.notify.debug('timer expired')
        self.calculateScores()
        self.gameOver()
        if task:
            return task.done

    def __playing(self):
        if not hasattr(self, 'gameFSM'):
            return 0
        return self.gameFSM.getCurrentState().getName() == 'play'

    def generateAssignmentData(self, assignmentTemplates):
        assignmentData = []
        for template in assignmentTemplates:
            playerScores = [0,
             0,
             0,
             0]
            highScorer = None
            dataEntry = [template[0],
             template[1],
             playerScores,
             highScorer]
            assignmentData.append(dataEntry)

        return assignmentData

    def checkForFilmOut(self):
        numOut = 0
        for entry in self.filmCountList:
            if entry >= self.data['FILMCOUNT']:
                numOut += 1

        numPlayers = 0
        for entry in self.avIdList:
            if entry:
                numPlayers += 1

        if numOut >= numPlayers:
            self.timerExpired()

    def filmOut(self):
        avId = self.air.getAvatarIdFromSender()
        if avId not in self.avIdList:
            self.air.writeServerEvent('suspicious', avId, 'PhotoGameAI.filmOut: unknown avatar')
            return
        if self.gameFSM.getCurrentState() is None or self.gameFSM.getCurrentState().getName() != 'play':
            self.air.writeServerEvent('suspicious', avId, 'PhotoGameAI.filmOut: game not in play state')
            return
        playerIndex = self.avIdList.index(avId)
        self.filmCountList[playerIndex] = self.data['FILMCOUNT']
        self.checkForFilmOut()
        return

    def newClientPhotoScore(self, subjectIndex, pose, score):
        avId = self.air.getAvatarIdFromSender()
        if self.gameFSM.getCurrentState() is None or self.gameFSM.getCurrentState().getName() != 'play':
            if self.gameFSM.getCurrentState() is None:
                gameState = None
            else:
                gameState = self.gameFSM.getCurrentState().getName()
            self.air.writeServerEvent('suspicious', avId, 'PhotoGameAI.newClientPhotoScore: game not in play state %s' % gameState)
            return
        if score > PhotoGameGlobals.NUMSTARS:
            score = 0.0
        if avId not in self.avIdList:
            self.air.writeServerEvent('suspicious', avId, 'PhotoGameAI.newClientPhotoScore: non-player avatar')
            return
        playerIndex = self.avIdList.index(avId)
        self.filmCountList[playerIndex] += 1
        self.checkForFilmOut()
        if self.filmCountList[playerIndex] >= self.data['FILMCOUNT']:
            self.notify.debug('player used more film than possible')
            return
        assignmentIndex = None
        for dataIndex in range(len(self.assignmentData)):
            assignment = self.assignmentData[dataIndex]
            if assignment[0] == subjectIndex and assignment[1] == pose:
                assignmentIndex = dataIndex

        if assignmentIndex != None and self.assignmentData[assignmentIndex][2][playerIndex] < score:
            self.assignmentData[assignmentIndex][2][playerIndex] = score
            highScorer = self.assignmentData[assignmentIndex][3]
            if highScorer == None:
                self.assignmentData[assignmentIndex][3] = playerIndex
            elif self.assignmentData[assignmentIndex][2][highScorer] < self.assignmentData[assignmentIndex][2][playerIndex]:
                self.assignmentData[assignmentIndex][3] = playerIndex
            self.sendUpdate('newAIPhotoScore', [avId, assignmentIndex, score])
        self.notify.debug('newClientPhotoScore %s %s %s %s' % (avId,
         subjectIndex,
         pose,
         score))
        for data in self.assignmentData:
            self.notify.debug(str(data))

        return

    def calculateScores(self):
        playerBonus = [0.0,
         0.0,
         0.0,
         0.0]
        teamScore = 0.0
        for data in self.assignmentData:
            scores = data[2]
            highestIndex = data[3]
            if highestIndex != None:
                highestScore = scores[highestIndex]
                self.notify.debug('\nHighIndex:%s' % highestIndex)
                self.notify.debug('scores')
                self.notify.debug(str(scores))
                teamScore += highestScore
                if highestIndex != None:
                    playerBonus[highestIndex] += 1.0

        for avIdKey in self.scoreDict:
            playerIndex = self.avIdList.index(avIdKey)
            playerScore = playerBonus[playerIndex] + teamScore
            self.scoreDict[avIdKey] = playerScore

        self.notify.debug('Calculated Scores')
        self.notify.debug('playerbonus')
        self.notify.debug(str(playerBonus))
        self.notify.debug('teamscore')
        self.notify.debug(str(teamScore))
        self.notify.debug('dict')
        self.notify.debug(str(self.scoreDict))
        return

    def exitPlay(self):
        taskMgr.remove(self.taskName('gameTimer'))
        taskMgr.remove(self.taskName('game-over'))

    def enterCleanup(self):
        self.notify.debug('enterCleanup')
        self.gameFSM.request('inactive')

    def exitCleanup(self):
        pass
