from pandac.PandaModules import Vec3, NodePath
from direct.distributed.ClockDelta import globalClockDelta
from otp.avatar.SpeedMonitor import SpeedMonitor
from toontown.cogdominium.CogdoMaze import CogdoMazeFactory
from toontown.cogdominium.DistCogdoMazeGameBase import DistCogdoMazeGameBase
from .DistCogdoGameAI import DistCogdoGameAI
from . import CogdoMazeGameGlobals as Globals
cogdoMazeTimeScoreRatio = 0.5
cogdoMazePerfectTime = 90
cogdoMazeMaxTime = 210
cogdoMazePickupScoreRatio = 0.7

class DistCogdoMazeGameAI(DistCogdoGameAI, DistCogdoMazeGameBase):
    notify = directNotify.newCategory('DistCogdoMazeGameAI')
    TimerExpiredTaskName = 'CMG_TimerExpiredTask'
    TimeoutTimerTaskName = 'CMG_timeoutTimerTask'
    CountdownTimerTaskName = 'CMG_countdownTimerTask'
    AnnounceGameDoneTimerTaskName = 'CMG_AnnounceGameDoneTimerTask'
    SkipCogdoGames = simbase.config.GetBool('skip-cogdo-game', 0)

    def __init__(self, air, id):
        DistCogdoGameAI.__init__(self, air, id)
        self.doorIsOpen = False
        self.toonsInDoor = []
        self.pickups = []
        self.pickupsDropped = 0
        self.maxPickups = 0
        self.numPickedUp = 0
        self.suits = {}
        self.lastRequestId = None
        self.requestStartTime = globalClock.getFrameTime()
        self.requestCount = None
        self.jokeLastRequestId = None
        self.jokeRequestStartTime = globalClock.getFrameTime()
        self.jokeRequestCount = None
        if __debug__ and simbase.config.GetBool('schellgames-dev', True):
            self.accept('onCodeReload', self.__sgOnCodeReload)

    def setExteriorZone(self, exteriorZone):
        DistCogdoGameAI.setExteriorZone(self, exteriorZone)
        self.difficulty = self.getDifficulty()
        self.createSuits()

    def createSuits(self):
        serialNum = 0
        self._numSuits = []
        extraSuits = 0
        for i in range(len(Globals.NumSuits)):
            extraSuits = int(round(self.difficulty * Globals.SuitsModifier[i]))
            self._numSuits.append(Globals.NumSuits[i] + extraSuits)

        self.bosses = self._numSuits[0]
        for i in range(self._numSuits[0]):
            self.suits[serialNum] = Globals.SuitData[Globals.SuitTypes.Boss]['hp']
            serialNum += 1

        for i in range(self._numSuits[1]):
            self.suits[serialNum] = Globals.SuitData[Globals.SuitTypes.FastMinion]['hp']
            serialNum += 1

        for i in range(self._numSuits[2]):
            self.suits[serialNum] = Globals.SuitData[Globals.SuitTypes.SlowMinion]['hp']
            serialNum += 1

        self._totalSuits = serialNum
        self.maxPickups = self._numSuits[0] * Globals.SuitData[0]['memos']
        self.maxPickups += self._numSuits[1] * Globals.SuitData[1]['memos']
        self.maxPickups += self._numSuits[2] * Globals.SuitData[2]['memos']

    def generate(self):
        DistCogdoGameAI.generate(self)
        mazeFactory = self.createMazeFactory(self.createRandomNumGen())
        waterCoolerList = []
        mazeModel = mazeFactory._loadAndBuildMazeModel()
        for waterCooler in mazeModel.findAllMatches('**/*waterCooler'):
            waterCoolerList.append((waterCooler.getPos(mazeModel), waterCooler.getHpr(mazeModel)))

        waterCoolerList.sort()
        baseNp = NodePath('base')
        rotNp = baseNp.attachNewNode('rot')
        childNp = rotNp.attachNewNode('child')
        childNp.setPos(*Globals.WaterCoolerTriggerOffset)
        self._waterCoolerPosList = []
        for (pos, hpr) in waterCoolerList:
            rotNp.setHpr(hpr)
            offset = childNp.getPos(baseNp)
            self._waterCoolerPosList.append(pos + offset)

        self._speedMonitor = SpeedMonitor('cogdoMazeGame-%s' % self.doId)
        self._toonId2speedToken = {}

    def delete(self):
        self.ignoreAll()
        self._speedMonitor.destroy()
        DistCogdoGameAI.delete(self)

    def isDoorOpen(self):
        return self.doorIsOpen

    def isToonInDoor(self, toonId):
        return toonId in self.toonsInDoor

    def areAllToonsInDoor(self):
        return self.getNumPlayers() == len(self.toonsInDoor)

    def getCurrentNetworkTime(self):
        return globalClockDelta.localToNetworkTime(globalClock.getRealTime())

    def suitHit(self, suitType, suitNum):
        avId = simbase.air.getAvatarIdFromSender()
        toon = simbase.air.doId2do.get(avId)
        if not toon:
            simbase.air.writeServerEvent('suspicious', avId, 'CogdoMazeGame.suitHit: toon not present?')
            return False

        result = True
        if self.lastRequestId == avId:
            self.requestCount += 1
            now = globalClock.getFrameTime()
            elapsed = now - self.requestStartTime
            if elapsed > 10:
                self.requestCount = 1
                self.requestStartTime = now
            else:
                secondsPerGrab = elapsed / self.requestCount
                if self.requestCount >= 3 and secondsPerGrab <= 0.4:
                    simbase.air.writeServerEvent('suspicious', avId, 'suitHit %s suits in %s seconds' % (self.requestCount, elapsed))
                    if simbase.config.GetBool('want-ban-cogdo-maze-suit-hit', False):
                        toon.ban('suitHit %s suits in %s seconds' % (self.requestCount, elapsed))

                    result = False

        else:
            self.lastRequestId = avId
            self.requestCount = 1
            self.requestStartTime = globalClock.getFrameTime()
        if result:
            self.suits[suitNum] -= 1
            hp = self.suits[suitNum]
            if hp <= 0:
                self.suitDestroyed(suitType, suitNum)

        return result

    def suitDestroyed(self, suitType, suitNum):
        if suitType == Globals.SuitTypes.Boss:
            self.bosses -= 1
            if self.bosses <= 0:
                self.openDoor()

        self.createPickups(suitType)
        del self.suits[suitNum]

    def createPickups(self, suitType):
        for i in range(Globals.SuitData[suitType]['memos']):
            self.pickups.append(self.pickupsDropped)
            self.pickupsDropped += 1

    def _removeToonFromGame(self, toonId):
        if self.fsm.getCurrentState().getName() == 'Game':
            if toonId not in self._toonId2speedToken:
                simbase.air.writeServerEvent('avoid_crash', toonId, 'CogdoMazeGame._removeToonFromGame: toon not in _toonId2speedToken')
            else:
                token = self._toonId2speedToken.pop(toonId)
                self._speedMonitor.removeNodepath(token)
            if self.areAllToonsInDoor():
                self._handleGameFinished()

    def handleToonDisconnected(self, toonId):
        DistCogdoGameAI.handleToonDisconnected(self, toonId)
        self._removeToonFromGame(toonId)

    def handleToonWentSad(self, toonId):
        DistCogdoGameAI.handleToonWentSad(self, toonId)
        self._removeToonFromGame(toonId)

    def getNumSuits(self):
        return list(self._numSuits)

    def d_broadcastPickup(self, senderId, pickupNum, networkTime):
        self.sendUpdate('pickUp', [
            senderId,
            pickupNum,
            networkTime])

    def requestAction(self, action, data):
        senderId = self.air.getAvatarIdFromSender()
        if not self._validateSenderId(senderId):
            return False

        if self.fsm.getCurrentState().getName() != 'Game':
            self.logSuspiciousEvent(senderId, 'CogdoMazeGameAI.requestAction outside of Game state')
            return False

        if action == Globals.GameActions.EnterDoor:
            if not self.doorIsOpen:
                self.logSuspiciousEvent(senderId, "CogdoMazeGameAI.requestAction(EnterDoor): door isn't open yet")
            elif senderId not in self.toonsInDoor:
                self.toonsInDoor.append(senderId)
                self.d_broadcastDoAction(action, senderId)
                if self.areAllToonsInDoor():
                    self._handleGameFinished()

            else:
                self.logSuspiciousEvent(senderId, 'CogdoMazeGameAI.requestAction: toon already in door')
        elif action == Globals.GameActions.RevealDoor:
            self.d_broadcastDoAction(action, senderId)
        else:
            self.logSuspiciousEvent(senderId, 'CogdoMazeGameAI.requestAction: invalid action %s' % action)

    def d_broadcastDoAction(self, action, data = 0, networkTime = 0):
        self.sendUpdate('doAction', [
            action,
            data,
            networkTime])

    def requestUseGag(self, x, y, h, networkTime):
        senderId = self.air.getAvatarIdFromSender()
        if not self._validateSenderId(senderId):
            return False

        if self.fsm.getCurrentState().getName() != 'Game':
            self.logSuspiciousEvent(senderId, 'CogdoMazeGameAI.requestUseGag outside of Game state')
            return False

        self.d_broadcastToonUsedGag(senderId, x, y, h, networkTime)

    def d_broadcastToonUsedGag(self, toonId, x, y, h, networkTime):
        self.sendUpdate('toonUsedGag', [
            toonId,
            x,
            y,
            h,
            networkTime])

    def requestSuitHitByGag(self, suitType, suitNum):
        senderId = self.air.getAvatarIdFromSender()
        if not self._validateSenderId(senderId):
            return False

        if self.fsm.getCurrentState().getName() != 'Game':
            self.logSuspiciousEvent(senderId, 'CogdoMazeGameAI.requestSuitHitByGag outside of Game state')
            return False

        if suitType not in Globals.SuitTypes:
            self.logSuspiciousEvent(senderId, 'CogdoMazeGameAI.requestSuitHitByGag: invalid suit type %s' % suitType)
            return False

        if suitNum not in list(self.suits.keys()):
            self.logSuspiciousEvent(senderId, 'CogdoMazeGameAI.requestSuitHitByGag: invalid suit num %s' % suitNum)
            return False

        resultValid = self.suitHit(suitType, suitNum)
        if resultValid:
            self.d_broadcastSuitHitByGag(senderId, suitType, suitNum)

    def d_broadcastSuitHitByGag(self, toonId, suitType, suitNum):
        self.sendUpdate('suitHitByGag', [
            toonId,
            suitType,
            suitNum])

    def requestHitBySuit(self, suitType, suitNum, networkTime):
        senderId = self.air.getAvatarIdFromSender()
        if not self._validateSenderId(senderId):
            return False

        if self.fsm.getCurrentState().getName() != 'Game':
            self.logSuspiciousEvent(senderId, 'CogdoMazeGameAI.requestHitBySuit outside of Game state')
            return False

        if suitType not in Globals.SuitTypes:
            self.logSuspiciousEvent(senderId, 'CogdoMazeGameAI.requestHitBySuit: invalid suit type %s' % suitType)
            return False

        if suitNum not in list(self.suits.keys()):
            self.logSuspiciousEvent(senderId, 'CogdoMazeGameAI.requestHitBySuit: invalid suit num %s' % suitNum)
            return False

        toon = self.air.doId2do[senderId]
        self.d_broadcastToonHitBySuit(senderId, suitType, suitNum, networkTime)
        damage = Globals.SuitData[suitType]['toonDamage']
        damage += int(round(damage * Globals.DamageModifier * self.difficulty))
        toon.takeDamage(damage, quietly = 0)

    def d_broadcastToonHitBySuit(self, toonId, suitType, suitNum, networkTime):
        self.sendUpdate('toonHitBySuit', [
            toonId,
            suitType,
            suitNum,
            networkTime])

    def requestHitByDrop(self):
        senderId = self.air.getAvatarIdFromSender()
        if not self._validateSenderId(senderId):
            return False

        if self.fsm.getCurrentState().getName() != 'Game':
            self.logSuspiciousEvent(senderId, 'CogdoMazeGameAI.requestHitByDrop outside of Game state')
            return False

        toon = self.air.doId2do[senderId]
        self.d_broadcastToonHitByDrop(senderId)
        if Globals.DropDamage > 0:
            damage = Globals.DropDamage
            damage += int(round(damage * Globals.DamageModifier * self.difficulty))
            toon.takeDamage(damage, quietly = 0)

    def d_broadcastToonHitByDrop(self, toonId):
        self.sendUpdate('toonHitByDrop', [
            toonId])

    def requestGag(self, waterCoolerIndex):
        senderId = self.air.getAvatarIdFromSender()
        if not self._validateSenderId(senderId):
            return False

        if self.fsm.getCurrentState().getName() != 'Game':
            self.logSuspiciousEvent(senderId, 'CogdoMazeGameAI.requestGag outside of Game state')
            return False

        if waterCoolerIndex >= len(self._waterCoolerPosList):
            self.logSuspiciousEvent(senderId, 'CogdoMazeGameAI.requestGag: invalid waterCoolerIndex')
            return

        wcPos = self._waterCoolerPosList[waterCoolerIndex]
        toon = self.air.doId2do.get(senderId)
        if not toon:
            self.logSuspiciousEvent(senderId, 'CogdoMazeGameAI.requestGag: toon not present')
            return

        distance = (toon.getPos() - wcPos).length()
        threshold = (Globals.WaterCoolerTriggerRadius + Globals.PlayerCollisionRadius) * 1.05
        if distance > threshold:
            self._toonHackingRequestGag(senderId)
            return

        self.d_broadcastHasGag(senderId, self.getCurrentNetworkTime())

    def d_broadcastHasGag(self, senderId, networkTime):
        self.sendUpdate('hasGag', [
            senderId,
            networkTime])

    def requestPickUp(self, pickupNum):
        senderId = self.air.getAvatarIdFromSender()
        if not self._validateSenderId(senderId):
            return False

        if self.fsm.getCurrentState().getName() != 'Game':
            self.logSuspiciousEvent(senderId, 'CogdoMazeGameAI.requestPickUp outside of Game state')
            return False

        if pickupNum not in self.pickups:
            self.logSuspiciousEvent(senderId, 'CogdoMazeGameAI.requestPickUp: invalid pickupNum %s' % pickupNum)
            return False

        toon = simbase.air.doId2do.get(senderId)
        if not toon:
            simbase.air.writeServerEvent('suspicious', senderId, 'CogdoMazeGame.requestPickUp: toon not present?')
            return False

        result = True
        if self.jokeLastRequestId == senderId:
            self.jokeRequestCount += 1
            now = globalClock.getFrameTime()
            elapsed = now - self.jokeRequestStartTime
            if elapsed > 10:
                self.jokeRequestCount = 1
                self.jokeRequestStartTime = now
            else:
                secondsPerGrab = elapsed / self.jokeRequestCount
                if self.jokeRequestCount >= 4 and secondsPerGrab <= 0.03:
                    simbase.air.writeServerEvent('suspicious', senderId, 'requestPickup %s jokes in %s seconds' % (self.jokeRequestCount, elapsed))
                    if simbase.config.GetBool('want-ban-cogdo-maze-request-pickup', False):
                        toon.ban('requestPickup %s jokes in %s seconds' % (self.jokeRequestCount, elapsed))

                    result = False

        else:
            self.jokeLastRequestId = senderId
            self.jokeRequestCount = 1
            self.jokeRequestStartTime = globalClock.getFrameTime()
        if result:
            self.numPickedUp += 1
            self.pickups.remove(pickupNum)
            self.d_broadcastPickup(senderId, pickupNum, self.getCurrentNetworkTime())

    def enterGame(self):
        DistCogdoGameAI.enterGame(self)
        endTime = Globals.SecondsUntilTimeout - (globalClock.getRealTime() - self.getStartTime())
        self._countdownTimerTask = taskMgr.doMethodLater(endTime - Globals.SecondsForTimeAlert, self.handleCountdownTimer, self.taskName(DistCogdoMazeGameAI.CountdownTimerTaskName), [])
        self._startGameTimer()
        self._timeoutTimerTask = taskMgr.doMethodLater(endTime, self.handleEndGameTimerExpired, self.taskName(DistCogdoMazeGameAI.TimeoutTimerTaskName), [])
        if self.SkipCogdoGames:
            self.fsm.request('Finish')

        for toonId in self.getToonIds():
            toon = self.air.doId2do.get(toonId)
            if toon:
                token = self._speedMonitor.addNodepath(toon)
                self._toonId2speedToken[toonId] = token
                self._speedMonitor.setSpeedLimit(token, config.GetFloat('cogdo-maze-speed-limit', Globals.ToonRunSpeed * 1.1), Functor(self._toonOverSpeedLimit, toonId))

    def _toonOverSpeedLimit(self, toonId, speed):
        self._bootPlayerForHacking(toonId, 'speeding in cogdo maze game (%.2f feet/sec)' % speed, config.GetBool('want-ban-cogdo-maze-speeding', 0))

    def _toonHackingRequestGag(self, toonId):
        simbase.air.writeServerEvent('suspicious', toonId, 'CogdoMazeGame: toon caught hacking requestGag')
        self._bootPlayerForHacking(toonId, 'hacking cogdo maze game requestGag', config.GetBool('want-ban-cogdo-maze-requestgag-hacking', 0))

    def _bootPlayerForHacking(self, toonId, reason, wantBan):
        toon = simbase.air.doId2do.get(toonId)
        if not toon:
            simbase.air.writeServerEvent('suspicious', toonId, 'CogdoMazeGame._bootPlayerForHacking(%s): toon not present' % (reason,))
            return

        if wantBan:
            toon.ban(reason)

    def _removeEndGameTimerTask(self):
        if hasattr(self, '_gameTimerExpiredTask'):
            taskMgr.remove(self._gameTimerExpiredTask)
            del self._gameTimerExpiredTask

    def _removeTimeoutTimerTask(self):
        if hasattr(self, '_timeoutTimerTask'):
            taskMgr.remove(self._timeoutTimerTask)
            del self._timeoutTimerTask

    def _removeCountdownTimerTask(self):
        if hasattr(self, '_countdownTimerTask'):
            taskMgr.remove(self._countdownTimerTask)
            del self._countdownTimerTask

    def _startGameTimer(self):
        self.d_broadcastDoAction(Globals.GameActions.Countdown, networkTime = self.getCurrentNetworkTime())

    def openDoor(self):
        self._removeTimeoutTimerTask()
        self._removeCountdownTimerTask()
        self.doorIsOpen = True
        self.d_broadcastDoAction(Globals.GameActions.OpenDoor, networkTime = self.getCurrentNetworkTime())
        self._gameTimerExpiredTask = taskMgr.doMethodLater(Globals.SecondsUntilGameEnds, self.handleEndGameTimerExpired, self.taskName(DistCogdoMazeGameAI.TimerExpiredTaskName), [])

    def handleCountdownTimer(self):
        self.d_broadcastDoAction(Globals.GameActions.TimeAlert, networkTime = self.getCurrentNetworkTime())

    def handleEndGameTimerExpired(self):
        self._handleGameFinished()

    def exitGame(self):
        DistCogdoGameAI.exitGame(self)
        for (toonId, token) in self._toonId2speedToken.items():
            self._speedMonitor.removeNodepath(token)

        self._toonId2speedToken = {}
        self._removeTimeoutTimerTask()
        self._removeEndGameTimerTask()

    def enterFinish(self):
        DistCogdoGameAI.enterFinish(self)
        if self.numPickedUp > self.maxPickups:
            self.logSuspiciousEvent(0, 'CogdoMazeGameAI: collected more memos than possible: %s, players: %s' % (self.numPickedUp, self.getToonIds()))

        time = globalClock.getRealTime() - self.getStartTime()
        adjustedTime = min(max(time - cogdoMazePerfectTime, 0), cogdoMazeMaxTime)
        timeScore = 1 - adjustedTime / cogdoMazeMaxTime
        pickupScore = 0
        if self.maxPickups:
            pickupScore = float(self.numPickedUp) / self.maxPickups

        weightedPickup = pickupScore * cogdoMazePickupScoreRatio
        weightedTime = timeScore * cogdoMazeTimeScoreRatio
        score = min(weightedPickup + weightedTime, 1.0)
        self.air.writeServerEvent('CogdoMazeGame', self._interior.toons, 'Memos: %s/%s Weighted Memos: %s Time: %s Weighted Time: %s Score: %s' % (self.numPickedUp, self.maxPickups, weightedPickup, time, weightedTime, score))
        self.setScore(score)
        self._announceGameDoneTask = taskMgr.doMethodLater(Globals.FinishDurationSeconds, self.announceGameDone, self.taskName(DistCogdoMazeGameAI.AnnounceGameDoneTimerTaskName), [])

    def exitFinish(self):
        DistCogdoGameAI.exitFinish(self)
        taskMgr.remove(self._announceGameDoneTask)
        del self._announceGameDoneTask
