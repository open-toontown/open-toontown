from otp.level import DistributedEntityAI
from toontown.coghq import MoleFieldBase
from direct.distributed.ClockDelta import globalClockDelta
from direct.directnotify import DirectNotifyGlobal

class DistributedMoleFieldAI(DistributedEntityAI.DistributedEntityAI, MoleFieldBase.MoleFieldBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedMoleFieldAI')

    def __init__(self, level, entId):
        DistributedEntityAI.DistributedEntityAI.__init__(self, level, entId)
        self.whackedMoles = {}
        self.numMolesWhacked = 0
        self.roundsFailed = 0
        self.started = 0
        self.challengeDefeated = False

    def announceGenerate(self):
        DistributedEntityAI.DistributedEntityAI.announceGenerate(self)
        self.numMoles = self.numSquaresX * self.numSquaresY
        self.moleFieldEndTimeTaskName = self.uniqueName('moleFieldEndTime')
        self.GameDuration = self.timeToPlay
        numToons = 0
        if hasattr(self, 'level'):
            numToons = len(self.level.presentAvIds)
        self.moleTarget = self.molesBase + self.molesPerPlayer * numToons

    def delete(self):
        DistributedEntityAI.DistributedEntityAI.delete(self)
        self.removeAllTasks()

    def setClientTriggered(self):
        if not hasattr(self, 'gameStartTime'):
            self.gameStartTime = globalClock.getRealTime()
        if not self.started:
            self.b_setGameStart(globalClockDelta.localToNetworkTime(self.gameStartTime), self.moleTarget, self.timeToPlay)
            self.started = 1

    def b_setGameStart(self, timestamp, moleTarget, timeToPlay):
        self.d_setGameStart(timestamp, moleTarget, timeToPlay)
        self.setGameStart(timestamp)

    def d_setGameStart(self, timestamp, moleTarget, timeToPlay):
        self.notify.debug('BASE: Sending setGameStart')
        self.sendUpdate('setGameStart', [timestamp, moleTarget, timeToPlay])

    def setGameStart(self, timestamp):
        self.GameDuration = self.timeToPlay
        self.notify.debug('BASE: setGameStart')
        self.prepareForGameStartOrRestart()

    def prepareForGameStartOrRestart(self):
        self.GameDuration = self.timeToPlay
        self.scheduleMoles()
        self.whackedMoles = {}
        self.doMethodLater(self.timeToPlay, self.gameEndingTimeHit, self.moleFieldEndTimeTaskName)

    def whackedMole(self, moleIndex, popupNum):
        validMoleWhack = False
        if moleIndex in self.whackedMoles:
            if self.whackedMoles[moleIndex] < popupNum:
                validMoleWhack = True
        else:
            self.whackedMoles[moleIndex] = popupNum
            validMoleWhack = True
        if validMoleWhack:
            self.numMolesWhacked += 1
            self.sendUpdate('updateMole', [moleIndex, self.WHACKED])
            self.sendUpdate('setScore', [self.numMolesWhacked])
        self.checkForTargetReached()

    def whackedBomb(self, moleIndex, popupNum, timestamp):
        senderId = self.air.getAvatarIdFromSender()
        self.sendUpdate('reportToonHitByBomb', [senderId, moleIndex, timestamp])

    def checkForTargetReached(self):
        if self.numMolesWhacked >= self.moleTarget:
            if not self.challengeDefeated:
                self.forceChallengeDefeated()

    def forceChallengeDefeated(self, pityWin=False):
        self.challengeDefeated = True
        self.removeTask(self.moleFieldEndTimeTaskName)
        roomId = self.getLevelDoId()
        room = simbase.air.doId2do.get(roomId)
        if room:
            self.challengeDefeated = True
            room.challengeDefeated()
            eventName = self.getOutputEventName()
            messenger.send(eventName, [1])
            if pityWin:
                self.sendUpdate('setPityWin')

    def gameEndingTimeHit(self, task):
        if self.numMolesWhacked < self.moleTarget and self.roundsFailed < 4:
            roomId = self.getLevelDoId()
            room = simbase.air.doId2do.get(roomId)
            self.roundsFailed += 1
            self.restartGame()
        else:
            if self.roundsFailed >= 4:
                if not self.challengeDefeated:
                    self.forceChallengeDefeated(pityWin=True)

    def damageMe(self):
        roomId = self.getLevelDoId()
        room = simbase.air.doId2do.get(roomId)
        if not room:
            return
        senderId = self.air.getAvatarIdFromSender()
        av = simbase.air.doId2do.get(senderId)
        playerIds = room.presentAvIds
        if av and senderId in playerIds:
            av.takeDamage(self.DamageOnFailure, quietly=0)
            room.sendUpdate('forceOuch', [self.DamageOnFailure])

    def restartGame(self):
        if not hasattr(self, 'entId'):
            return
        self.gameStartTime = globalClock.getRealTime()
        self.started = 0
        self.b_setGameStart(globalClockDelta.localToNetworkTime(self.gameStartTime), self.moleTarget, self.timeToPlay)

    def getScore(self):
        return self.numMolesWhacked
