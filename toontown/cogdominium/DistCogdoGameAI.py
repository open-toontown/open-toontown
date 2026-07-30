from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.ClockDelta import globalClockDelta
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from direct.fsm import ClassicFSM, State
from toontown.cogdominium import CogdoGameConsts
from toontown.cogdominium.DistCogdoGameBase import DistCogdoGameBase
from otp.ai.Barrier import Barrier

class SadCallbackToken:
    pass


class DistCogdoGameAI(DistCogdoGameBase, DistributedObjectAI):
    notify = directNotify.newCategory('DistCogdoGameAI')
    EndlessCogdoGames = simbase.config.GetBool('endless-cogdo-games', 0)

    def __init__(self, air, interior):
        DistributedObjectAI.__init__(self, air)
        self._interior = interior
        self.loadFSM = ClassicFSM.ClassicFSM('DistCogdoGameAI.loaded', [
            State.State('NotLoaded', self.enterNotLoaded, self.exitNotLoaded, [
                'Loaded']),
            State.State('Loaded', self.enterLoaded, self.exitLoaded, [
                'NotLoaded'])], 'NotLoaded', 'NotLoaded')
        self.loadFSM.enterInitialState()
        self.fsm = ClassicFSM.ClassicFSM('DistCogdoGameAI', [
            State.State('Visible', self.enterVisible, self.exitVisible, [
                'Intro']),
            State.State('Intro', self.enterIntro, self.exitIntro, [
                'Game']),
            State.State('Game', self.enterGame, self.exitGame, [
                'Finish']),
            State.State('Finish', self.enterFinish, self.exitFinish, [
                'Off']),
            State.State('Off', self.enterOff, self.exitOff, [
                'Visible'])], 'Off', 'Off')
        self.fsm.enterInitialState()
        self.difficultyOverride = None
        self.exteriorZoneOverride = None

    def setExteriorZone(self, exteriorZone):
        self.exteriorZone = exteriorZone

    def logSuspiciousEvent(self, avId, msg):
        self.air.writeServerEvent('suspicious', avId, msg)

    def generate(self):
        DistributedObjectAI.generate(self)
        self._sadToken2callback = {}
        self.notify.debug('difficulty: %s, safezoneId: %s' % (self.getDifficulty(), self.getSafezoneId()))

    def getInteriorId(self):
        return self._interior.doId

    def getExteriorZone(self):
        return self.exteriorZone

    def getDroneCogDNA(self):
        return self._interior.getDroneCogDNA()

    def getToonIds(self):
        toonIds = []
        for toonId in self._interior.getToons()[0]:
            if toonId:
                toonIds.append(toonId)

        return toonIds

    def getNumPlayers(self):
        return len(self.getToonIds())

    def requestDelete(self):
        self.fsm.requestFinalState()
        self.loadFSM.requestFinalState()
        self._sadToken2callback = None
        DistributedObjectAI.requestDelete(self)

    def delete(self):
        self._interior = None
        self.fsm = None
        self.loadFSM = None
        DistributedObjectAI.delete(self)

    def makeVisible(self):
        self.loadFSM.request('Loaded')
        self.fsm.request('Visible')

    def start(self):
        self.fsm.request('Intro')

    def markStartTime(self):
        self._startTime = globalClock.getRealTime()

    def getStartTime(self):
        return self._startTime

    def markFinishTime(self):
        self._finishTime = globalClock.getRealTime()

    def getFinishTime(self):
        return self._finishTime

    def setDifficultyOverrides(self, difficultyOverride, exteriorZoneOverride):
        self.difficultyOverride = difficultyOverride
        if self.difficultyOverride is not None:
            self.difficultyOverride = CogdoGameConsts.QuantizeDifficultyOverride(difficultyOverride)

        self.exteriorZoneOverride = exteriorZoneOverride

    def getDifficultyOverrides(self):
        response = [
            self.difficultyOverride,
            self.exteriorZoneOverride]
        if response[0] is None:
            response[0] = CogdoGameConsts.NoDifficultyOverride
        else:
            response[0] *= CogdoGameConsts.DifficultyOverrideMult
            response[0] = int(response[0])
        if response[1] is None:
            response[1] = CogdoGameConsts.NoExteriorZoneOverride

        return response

    def getDifficulty(self):
        if self.difficultyOverride is not None:
            return self.difficultyOverride

        if hasattr(self.air, 'cogdoGameDifficulty'):
            return float(self.air.cogdoGameDifficulty)

        return CogdoGameConsts.getDifficulty(self.getSafezoneId())

    def getSafezoneId(self):
        if self.exteriorZoneOverride is not None:
            return self.exteriorZoneOverride

        if hasattr(self.air, 'cogdoGameSafezoneId'):
            return CogdoGameConsts.getSafezoneId(self.air.cogdoGameSafezoneId)

        return CogdoGameConsts.getSafezoneId(self.exteriorZone)

    def _validateSenderId(self, senderId):
        if senderId in self.getToonIds():
            return True

        self._reportSuspiciousEvent(senderId, 'Not currently playing CogDo Game.')
        return False

    def _reportSuspiciousEvent(self, senderId, message):
        self.logSuspiciousEvent(senderId, message)

    def handleToonDisconnected(self, toonId):
        self.notify.debug('handleToonDisconnected: %s' % toonId)
        self.sendUpdate('setToonDisconnect', [
            toonId])

    def handleToonWentSad(self, toonId):
        self.notify.debug('handleToonWentSad: %s' % toonId)
        self.sendUpdate('setToonSad', [
            toonId])
        if self._sadToken2callback is not None:
            callbacks = list(self._sadToken2callback.values())
            for callback in callbacks:
                callback(toonId)

    def _registerSadCallback(self, callback):
        token = SadCallbackToken()
        self._sadToken2callback[token] = callback
        return token

    def _unregisterSadCallback(self, token):
        self._sadToken2callback.pop(token)

    def enterNotLoaded(self):
        pass

    def exitNotLoaded(self):
        pass

    def enterLoaded(self):
        pass

    def exitLoaded(self):
        pass

    def enterOff(self):
        self.ignore('cogdoGameEnd')

    def exitOff(self):
        self._wasEnded = False
        self.accept('cogdoGameEnd', self._handleGameEnd)

    def enterVisible(self):
        self.sendUpdate('setVisible', [])

    def exitVisible(self):
        pass

    def enterIntro(self):
        self.sendUpdate('setIntroStart', [])
        self._introBarrier = Barrier('intro', self.uniqueName('intro'), self.getToonIds(), 1 << 20, doneFunc = self._handleIntroBarrierDone)
        self._sadToken = self._registerSadCallback(self._handleSadToonDuringIntro)

    def exitIntro(self):
        self._unregisterSadCallback(self._sadToken)
        self._sadToken = None
        self._introBarrier.cleanup()
        self._introBarrier = None

    def _handleSadToonDuringIntro(self, toonId):
        self._introBarrier.clear(toonId)

    def setAvatarReady(self):
        senderId = self.air.getAvatarIdFromSender()
        if senderId not in self.getToonIds():
            self.logSuspiciousEvent(senderId, 'CogdoGameAI.setAvatarReady: unknown avatar')
            return

        if hasattr(self, '_introBarrier') and self._introBarrier:
            self._introBarrier.clear(senderId)

    def _handleIntroBarrierDone(self, avIds):
        self.fsm.request('Game')

    def enterGame(self):
        self.markStartTime()
        self.sendUpdate('setGameStart', [
            globalClockDelta.localToNetworkTime(self.getStartTime())])

    def exitGame(self):
        pass

    def _handleGameFinished(self, overrideEndless = False):
        if overrideEndless or not (self.EndlessCogdoGames):
            self.fsm.request('Finish')

    def _handleGameEnd(self):
        self._wasEnded = True
        if self.fsm.getCurrentState().getName() == 'Off':
            self.fsm.request('Intro')

        if self.fsm.getCurrentState().getName() == 'Intro':
            self.fsm.request('Game')

        self._handleGameFinished(overrideEndless = True)
        self.announceGameDone()

    def wasEnded(self):
        return self._wasEnded

    def enterFinish(self):
        self.markFinishTime()
        self.sendUpdate('setGameFinish', [
            globalClockDelta.localToNetworkTime(self.getFinishTime())])

    def exitFinish(self):
        pass

    def setScore(self, score):
        self._interior._setGameScore(score)

    def isDoorOpen(self):
        return True

    def isToonInDoor(self, toonId):
        return True

    def announceGameDone(self):
        self._interior._gameDone()
