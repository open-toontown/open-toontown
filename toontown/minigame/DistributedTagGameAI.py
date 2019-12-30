from .DistributedMinigameAI import *
from .TagTreasurePlannerAI import *
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from direct.task import Task
import random
from . import TagGameGlobals

class DistributedTagGameAI(DistributedMinigameAI):
    DURATION = TagGameGlobals.DURATION

    def __init__(self, air, minigameId):
        try:
            self.DistributedTagGameAI_initialized
        except:
            self.DistributedTagGameAI_initialized = 1
            DistributedMinigameAI.__init__(self, air, minigameId)
            self.gameFSM = ClassicFSM.ClassicFSM('DistributedTagGameAI', [State.State('inactive', self.enterInactive, self.exitInactive, ['play']), State.State('play', self.enterPlay, self.exitPlay, ['cleanup']), State.State('cleanup', self.enterCleanup, self.exitCleanup, ['inactive'])], 'inactive', 'inactive')
            self.addChildGameFSM(self.gameFSM)
            self.treasureScores = {}
            self.itAvId = None
            self.tagBack = 1

        return

    def delete(self):
        self.notify.debug('delete')
        del self.gameFSM
        DistributedMinigameAI.delete(self)

    def setGameReady(self):
        self.notify.debug('setGameReady')
        DistributedMinigameAI.setGameReady(self)
        for avId in self.avIdList:
            self.treasureScores[avId] = 0

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
        self.gameFSM.request('cleanup')
        DistributedMinigameAI.gameOver(self)

    def enterInactive(self):
        self.notify.debug('enterInactive')

    def exitInactive(self):
        pass

    def enterPlay(self):
        self.notify.debug('enterPlay')
        self.b_setIt(random.choice(self.avIdList))
        taskMgr.doMethodLater(self.DURATION, self.timerExpired, self.taskName('gameTimer'))
        self.tagTreasurePlanner = TagTreasurePlannerAI(self.zoneId, self.treasureGrabCallback)
        self.tagTreasurePlanner.placeRandomTreasure()
        self.tagTreasurePlanner.placeRandomTreasure()
        self.tagTreasurePlanner.placeRandomTreasure()
        self.tagTreasurePlanner.placeRandomTreasure()
        self.tagTreasurePlanner.start()

    def timerExpired(self, task):
        self.notify.debug('timer expired')
        self.gameOver()
        return Task.done

    def exitPlay(self):
        taskMgr.remove(self.taskName('gameTimer'))
        taskMgr.remove(self.taskName('tagBack'))
        taskMgr.remove(self.taskName('clearTagBack'))
        self.tagTreasurePlanner.stop()
        self.tagTreasurePlanner.deleteAllTreasuresNow()
        del self.tagTreasurePlanner

    def enterCleanup(self):
        self.notify.debug('enterCleanup')
        self.gameFSM.request('inactive')

    def exitCleanup(self):
        pass

    def treasureGrabCallback(self, avId):
        if avId not in self.avIdList:
            self.air.writeServerEvent('suspicious', avId, 'TagGameAI.treasureGrabCallback non-player avId')
            return
        self.treasureScores[avId] += 2
        self.notify.debug('treasureGrabCallback: ' + str(avId) + ' grabbed a treasure, new score: ' + str(self.treasureScores[avId]))
        self.scoreDict[avId] = self.treasureScores[avId]
        treasureScoreParams = []
        for avId in self.avIdList:
            treasureScoreParams.append(self.treasureScores[avId])

        self.sendUpdate('setTreasureScore', [treasureScoreParams])

    def clearTagBack(self, task):
        self.tagBack = 1
        return Task.done

    def tag(self, taggedAvId):
        taggedAvatar = simbase.air.doId2do.get(taggedAvId)
        if taggedAvatar == None:
            self.air.writeServerEvent('suspicious', taggedAvId, 'TagGameAI.tag invalid taggedAvId')
            return
        itAvId = self.air.getAvatarIdFromSender()
        if self.tagBack:
            self.notify.debug('tag: ' + str(itAvId) + ' tagged: ' + str(taggedAvId))
            if self.itAvId == itAvId:
                self.b_setIt(taggedAvId)
            else:
                self.notify.warning('Got tag message from avatar that is not IT')
                return
            self.tagBack = 0
            taskMgr.doMethodLater(2.0, self.clearTagBack, self.taskName('clearTagBack'))
        return

    def b_setIt(self, avId):
        self.d_setIt(avId)
        self.setIt(avId)

    def d_setIt(self, avId):
        self.sendUpdate('setIt', [avId])

    def setIt(self, avId):
        self.itAvId = avId
