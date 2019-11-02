from DistributedMinigameAI import *
from toontown.ai.ToonBarrier import *
from direct.fsm import ClassicFSM, State
from direct.fsm import State
import CatchGameGlobals
import MinigameGlobals

class DistributedCatchGameAI(DistributedMinigameAI):

    def __init__(self, air, minigameId):
        try:
            self.DistributedCatchGameAI_initialized
        except:
            self.DistributedCatchGameAI_initialized = 1
            DistributedMinigameAI.__init__(self, air, minigameId)
            self.gameFSM = ClassicFSM.ClassicFSM('DistributedCatchGameAI', [State.State('inactive', self.enterInactive, self.exitInactive, ['play']), State.State('play', self.enterPlay, self.exitPlay, ['cleanup']), State.State('cleanup', self.enterCleanup, self.exitCleanup, ['inactive'])], 'inactive', 'inactive')
            self.addChildGameFSM(self.gameFSM)

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
        self.notify.debug('fruits: %s, fruits caught: %s' % (self.numFruits, self.fruitsCaught))
        perfect = self.fruitsCaught >= self.numFruits
        for avId in self.avIdList:
            self.scoreDict[avId] = max(1, int(self.scoreDict[avId] / 2))
            if perfect:
                self.notify.debug('PERFECT GAME!')
                self.scoreDict[avId] += round(self.numFruits / 4.0)
                self.logAllPerfect()

        self.gameFSM.request('cleanup')
        DistributedMinigameAI.gameOver(self)

    def enterInactive(self):
        self.notify.debug('enterInactive')

    def exitInactive(self):
        pass

    def enterPlay(self):
        self.notify.debug('enterPlay')
        self.caughtList = [0] * 100
        table = CatchGameGlobals.NumFruits[self.numPlayers - 1]
        self.numFruits = table[self.getSafezoneId()]
        self.notify.debug('numFruits: %s' % self.numFruits)
        self.fruitsCaught = 0

        def allToonsDone(self = self):
            self.notify.debug('allToonsDone')
            self.sendUpdate('setEveryoneDone')
            if not CatchGameGlobals.EndlessGame:
                self.gameOver()

        def handleTimeout(avIds, self = self):
            self.notify.debug('handleTimeout: avatars %s did not report "done"' % avIds)
            self.setGameAbort()

        self.doneBarrier = ToonBarrier('waitClientsDone', self.uniqueName('waitClientsDone'), self.avIdList, CatchGameGlobals.GameDuration + MinigameGlobals.latencyTolerance, allToonsDone, handleTimeout)

    def exitPlay(self):
        del self.caughtList
        self.doneBarrier.cleanup()
        del self.doneBarrier

    def claimCatch(self, objNum, DropObjTypeId):
        if self.gameFSM.getCurrentState().getName() != 'play':
            return
        if DropObjTypeId < 0 or DropObjTypeId >= len(CatchGameGlobals.DOTypeId2Name):
            self.air.writeServerEvent('warning', DropObjTypeId, 'CatchGameAI.claimCatch DropObjTypeId out of range')
            return
        if objNum < 0 or objNum > 5000 or objNum >= 2 * len(self.caughtList):
            self.air.writeServerEvent('warning', objNum, 'CatchGameAI.claimCatch objNum is too high or negative')
            return
        if objNum >= len(self.caughtList):
            self.caughtList += [0] * len(self.caughtList)
        if not self.caughtList[objNum]:
            self.caughtList[objNum] = 1
            avId = self.air.getAvatarIdFromSender()
            self.sendUpdate('setObjectCaught', [avId, objNum])
            objName = CatchGameGlobals.DOTypeId2Name[DropObjTypeId]
            self.notify.debug('avatar %s caught object %s: %s' % (avId, objNum, objName))
            if CatchGameGlobals.Name2DropObjectType[objName].good:
                self.scoreDict[avId] += 1
                self.fruitsCaught += 1

    def reportDone(self):
        if not self.gameFSM or not self.gameFSM.getCurrentState() or self.gameFSM.getCurrentState().getName() != 'play':
            return
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug('reportDone: avatar %s is done' % avId)
        self.doneBarrier.clear(avId)

    def enterCleanup(self):
        self.notify.debug('enterCleanup')
        self.gameFSM.request('inactive')

    def exitCleanup(self):
        pass
