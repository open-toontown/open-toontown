import random
from direct.distributed.ClockDelta import globalClockDelta
from .DistCogdoGameAI import DistCogdoGameAI
from . import CogdoFlyingGameGlobals as Globals

class DistCogdoFlyingGameAI(DistCogdoGameAI):
    notify = directNotify.newCategory('DistCogdoFlyingGameAI')
    EagleExitCooldownTaskName = 'CFG_EagleExitCooldownTask-%s'
    InvulBuffRemoveTaskName = 'CFG_InvulBuffRemoveTask-%s'
    AnnounceGameDoneTimerTaskName = 'CFG_AnnounceGameDoneTimerTask'

    def __init__(self, air, id):
        DistCogdoGameAI.__init__(self, air, id)
        self.toonsOnEndPlatform = []
        self.toonsInWinState = []
        self.eagleId2targetIds = {}
        self.pickups = []
        self.memoCount = 0
        self.toonId2buffList = {}
        self.broadcastedGotoWinState = False
        self.broadcastedGameFinished = False
        self._gameState = False
        if __debug__ and simbase.config.GetBool('schellgames-dev', True):
            self.accept('onCodeReload', self._DistCogdoFlyingGameAI__sgOnCodeReload)

    def getLegalEagleAttackRoundTime(self, fromCooldown = False):
        time = 0.0
        time += Globals.LegalEagle.LiftOffTime
        time += Globals.LegalEagle.LockOnTime
        time += Globals.LegalEagle.ChargeUpTime
        time += Globals.LegalEagle.PreAttackTime
        time += Globals.LegalEagle.PostAttackTime
        time += Globals.LegalEagle.RetreatToSkyTime
        time += Globals.LegalEagle.CooldownTime
        if fromCooldown:
            time += Globals.LegalEagle.ExtraPostCooldownTime

        return time

    def delete(self):
        self.ignoreAll()
        DistCogdoGameAI.delete(self)

    def areAllToonsOnPlatform(self):
        if self.getNumPlayers() == 0:
            return False

        return self.getNumPlayers() == len(self.toonsOnEndPlatform)

    def areAllToonsInWinState(self):
        if self.getNumPlayers() == 0:
            return False

        return self.getNumPlayers() == len(self.toonsInWinState)

    def getCurrentNetworkTime(self):
        return globalClockDelta.localToNetworkTime(globalClock.getRealTime())

    def addBuff(self, toonId, pickupType):
        if toonId in self.toonId2buffList:
            buffList = self.toonId2buffList[toonId]
            if pickupType in buffList:
                return 0
            else:
                buffList.append(pickupType)
        else:
            self.toonId2buffList[toonId] = [
                pickupType]
        return 1

    def removeBuff(self, toonId, pickupType):
        if toonId in self.toonId2buffList:
            buffList = self.toonId2buffList[toonId]
            if pickupType in buffList:
                buffList.remove(pickupType)
                return 1

        return 0

    def isBuffOnToon(self, toonId, pickupType):
        if toonId in self.toonId2buffList:
            buffList = self.toonId2buffList[toonId]
            if pickupType in buffList:
                return 1

        return 0

    def updateGotoWinState(self):
        if not (self.broadcastedGotoWinState) and self.areAllToonsOnPlatform():
            self.forceDebuffAll()
            self.broadcastedGotoWinState = True
            self.d_broadcastDoAction(Globals.AI.GameActions.GotoWinState)

    def updateGameFinished(self):
        if not (self.broadcastedGameFinished) and self.areAllToonsInWinState():
            self.broadcastedGameFinished = True
            self._handleGameFinished()

    def _isPlayingGame(self, senderId):
        if self._gameState:
            return True
        elif self.fsm.getCurrentState() not in ('Finish',):
            self._reportSuspiciousEvent(senderId, 'Client %s has made a game action request from illegal state: %s.' % (senderId, self.fsm.getCurrentState()))

        return False

    def requestAction(self, action, data):
        senderId = self.air.getAvatarIdFromSender()
        if not self._validateSenderId(senderId) or not self._isPlayingGame(senderId):
            return False

        av = simbase.air.doId2do.get(senderId)
        if action == Globals.AI.GameActions.LandOnWinPlatform:
            if senderId not in self.toonsOnEndPlatform:
                self.toonsOnEndPlatform.append(senderId)
                self.d_broadcastDoAction(action, senderId)
                self.updateGotoWinState()
            else:
                self._reportSuspiciousEvent(senderId, 'Client %s has landed on the win platform twice.' % senderId)
        elif action == Globals.AI.GameActions.WinStateFinished:
            if senderId not in self.toonsInWinState:
                self.toonsInWinState.append(senderId)
                self.d_broadcastDoAction(action, senderId)
                self.updateGameFinished()
            else:
                self._reportSuspiciousEvent(senderId, 'Client %s wants to exit from the win state multiple times.' % senderId)
        elif action == Globals.AI.GameActions.HitWhirlwind:
            if Globals.Dev.Invincibility != True:
                self.damageToon(av, Globals.AI.SafezoneId2WhirlwindDamage)

        elif action == Globals.AI.GameActions.HitLegalEagle:
            if Globals.Dev.Invincibility != True:
                self.damageToon(av, Globals.AI.SafezoneId2LegalEagleDamage)

        elif action == Globals.AI.GameActions.HitMinion:
            if Globals.Dev.Invincibility != True:
                self.damageToon(av, Globals.AI.SafezoneId2MinionDamage)

        elif action == Globals.AI.GameActions.RequestEnterEagleInterest:
            self.b_toonSetAsEagleTarget(senderId, data, self.getCurrentNetworkTime())
        elif action == Globals.AI.GameActions.RequestExitEagleInterest:
            self.b_toonClearAsEagleTarget(senderId, data, self.getCurrentNetworkTime())
        elif action == Globals.AI.GameActions.RanOutOfTimePenalty:
            self.memoCount = 0
        elif action == Globals.AI.GameActions.Died:
            self.toonDied(av)
            self.sendUpdate('toonDied', [
                senderId,
                self.getCurrentNetworkTime()])
        elif action == Globals.AI.GameActions.Spawn:
            self.sendUpdate('toonSpawn', [
                senderId,
                self.getCurrentNetworkTime()])
        elif action == Globals.AI.GameActions.SetBlades:
            if data in Globals.Gameplay.FuelStates:
                self.sendUpdate('toonSetBlades', [
                    senderId,
                    data])
            else:
                self._reportSuspiciousEvent(senderId, "Client %s has requested a fuel state that doesn't exist:%s." % (senderId, data))
        elif action == Globals.AI.GameActions.BladeLost:
            self.sendUpdate('toonBladeLost', [
                senderId])
        else:
            self._reportSuspiciousEvent(senderId, 'Client %s has made an illegal game action request: %s.' % (senderId, action))

    def requestPickUp(self, pickupNum, pickupType):
        senderId = self.air.getAvatarIdFromSender()
        if not self._validateSenderId(senderId) or not self._isPlayingGame(senderId):
            return False

        if pickupType not in Globals.Level.GatherableTypes:
            self._reportSuspiciousEvent(senderId, 'Client %s has requested an illegal pickup type: %s.' % (senderId, pickupType))
            return False

        if pickupType == Globals.Level.GatherableTypes.Memo:
            if pickupNum not in self.pickups:
                self.pickups.append(pickupNum)
                self.memoCount += 1
                self.d_broadcastPickup(senderId, pickupNum, self.getCurrentNetworkTime())

        else:
            self.d_broadcastPickup(senderId, pickupNum, self.getCurrentNetworkTime())
            if pickupType == Globals.Level.GatherableTypes.LaffPowerup:
                self.pickedUpLaffPowerup(senderId)
            elif pickupType == Globals.Level.GatherableTypes.InvulPowerup:
                self.pickedUpInvulPowerup(senderId)

    def damageToon(self, av, damageDict):
        safezoneId = self.getSafezoneId()
        if safezoneId in damageDict:
            av.takeDamage(damageDict[safezoneId], quietly = 0)
        else:
            self.notify.warning('Safezone Id: %s is not in flying game damage dictionary' % safezoneId)

    def toonDied(self, av):
        if Globals.Dev.Invincibility != True:
            self.damageToon(av, Globals.AI.SafezoneId2DeathDamage)

    def d_broadcastDoAction(self, action, data = 0):
        self.sendUpdate('doAction', [
            action,
            data])

    def b_broadcastDebuffPowerup(self, senderId, pickupType):
        if self.removeBuff(senderId, pickupType):
            self.d_broadcastDebuffPowerup(senderId, pickupType)

    def d_broadcastDebuffPowerup(self, senderId, pickupType):
        self.sendUpdate('debuffPowerup', [
            senderId,
            pickupType,
            self.getCurrentNetworkTime()])

    def pickedUpLaffPowerup(self, senderId):
        av = simbase.air.doId2do.get(senderId)
        if av:
            if av.hp > 0 and av.hp < av.maxHp:
                safezoneId = self.getSafezoneId()
                if safezoneId in Globals.Gameplay.SafezoneId2LaffPickupHealAmount:
                    av.toonUp(Globals.Gameplay.SafezoneId2LaffPickupHealAmount[safezoneId])
                else:
                    self.notify.warning('Safezone Id: %s is not in SafezoneId2LaffPickupHealAmount' % safezoneId)

    def pickedUpInvulPowerup(self, senderId):
        taskMgr.remove(self.uniqueName(DistCogdoFlyingGameAI.InvulBuffRemoveTaskName % senderId))
        self.addBuff(senderId, Globals.Level.GatherableTypes.InvulPowerup)
        taskMgr.doMethodLater(Globals.Gameplay.InvulBuffTime, self.b_broadcastDebuffPowerup, self.uniqueName(DistCogdoFlyingGameAI.InvulBuffRemoveTaskName % senderId), extraArgs = [
            senderId,
            Globals.Level.GatherableTypes.InvulPowerup])

    def forceDebuffAll(self):
        tasks = taskMgr.getTasksMatching(DistCogdoFlyingGameAI.InvulBuffRemoveTaskName % '*')
        for task in tasks:
            taskMgr.remove(task.getName())

        for toonId in self.toonId2buffList:
            buffList = self.toonId2buffList[toonId][:]
            for buff in buffList:
                self.b_broadcastDebuffPowerup(toonId, buff)

    def d_broadcastPickup(self, senderId, pickupNum, networkTime):
        self.sendUpdate('pickUp', [
            senderId,
            pickupNum,
            networkTime])

    def b_toonSetAsEagleTarget(self, toonId, eagleId, networkTime):
        if eagleId not in self.eagleId2targetIds:
            self.eagleId2targetIds[eagleId] = [
                toonId]
            if not taskMgr.hasTaskNamed(DistCogdoFlyingGameAI.EagleExitCooldownTaskName % eagleId):
                taskMgr.doMethodLater(self.getLegalEagleAttackRoundTime(), self.d_broadcastEagleExitCooldown, self.uniqueName(DistCogdoFlyingGameAI.EagleExitCooldownTaskName % eagleId), extraArgs = [
                    eagleId])

            self.d_broadcastToonSetAsEagleTarget(toonId, eagleId, networkTime)
        else:
            self.eagleId2targetIds[eagleId].append(toonId)

    def b_toonClearAsEagleTarget(self, toonId, eagleId, networkTime):
        if eagleId in self.eagleId2targetIds:
            toonIds = self.eagleId2targetIds[eagleId]
            toonIds.remove(toonId)
            self.d_broadcastToonClearAsEagleTarget(toonId, eagleId, networkTime)
            if len(toonIds) == 0:
                del self.eagleId2targetIds[eagleId]
            else:
                index = random.randint(0, len(toonIds) - 1)
                self.d_broadcastToonSetAsEagleTarget(toonIds[index], eagleId, networkTime)

    def d_broadcastEagleExitCooldown(self, eagleId):
        self.sendUpdate('eagleExitCooldown', [
            eagleId,
            self.getCurrentNetworkTime()])
        if eagleId in self.eagleId2targetIds:
            taskMgr.remove(self.uniqueName(DistCogdoFlyingGameAI.EagleExitCooldownTaskName % eagleId))
            if eagleId in self.eagleId2targetIds:
                taskMgr.doMethodLater(self.getLegalEagleAttackRoundTime(fromCooldown = True), self.d_broadcastEagleExitCooldown, self.uniqueName(DistCogdoFlyingGameAI.EagleExitCooldownTaskName % eagleId), extraArgs = [
                    eagleId])

    def d_broadcastToonSetAsEagleTarget(self, toonId, eagleId, networkTime):
        self.sendUpdate('toonSetAsEagleTarget', [
            toonId,
            eagleId,
            networkTime])

    def d_broadcastToonClearAsEagleTarget(self, toonId, eagleId, networkTime):
        self.sendUpdate('toonClearAsEagleTarget', [
            toonId,
            eagleId,
            networkTime])

    def enterGame(self):
        DistCogdoGameAI.enterGame(self)
        self._gameState = True

    def handleGameTimerExpired(self):
        self._handleGameFinished()

    def handleToonDisconnected(self, toonId):
        DistCogdoGameAI.handleToonDisconnected(self, toonId)
        if toonId in self.toonsOnEndPlatform:
            self.toonsOnEndPlatform.remove(toonId)

        if toonId in self.toonsInWinState:
            self.toonsInWinState.remove(toonId)

        self.updateGotoWinState()
        self.updateGameFinished()

    def handleToonWentSad(self, toonId):
        DistCogdoGameAI.handleToonWentSad(self, toonId)
        if toonId in self.toonsOnEndPlatform:
            self.toonsOnEndPlatform.remove(toonId)

        if toonId in self.toonsInWinState:
            self.toonsInWinState.remove(toonId)

        self.updateGotoWinState()
        self.updateGameFinished()

    def exitGame(self):
        self._gameState = False
        DistCogdoGameAI.exitGame(self)
        if hasattr(self, '_gameTimerExpiredTask'):
            taskMgr.remove(self._gameTimerExpiredTask)
            del self._gameTimerExpiredTask

        taskMgr.removeTasksMatching(DistCogdoFlyingGameAI.InvulBuffRemoveTaskName % '*')
        taskMgr.removeTasksMatching(DistCogdoFlyingGameAI.EagleExitCooldownTaskName % '*')
        for toonId in self.toonId2buffList:
            del self.toonId2buffList[toonId][:]

        self.toonId2buffList.clear()
        self.eagleId2targetIds.clear()
        del self.pickups[:]
        del self.toonsOnEndPlatform[:]
        del self.toonsInWinState[:]

    def enterFinish(self):
        DistCogdoGameAI.enterFinish(self)
        self.ignoreAll()
        self._announceGameDoneTask = taskMgr.doMethodLater(Globals.Gameplay.FinishDurationSeconds, self.announceGameDone, self.taskName(DistCogdoFlyingGameAI.AnnounceGameDoneTimerTaskName), [])

    def exitFinish(self):
        DistCogdoGameAI.exitFinish(self)
        taskMgr.remove(self._announceGameDoneTask)
        del self._announceGameDoneTask
