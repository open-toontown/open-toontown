from direct.distributed.ClockDelta import *
from direct.distributed import DistributedObjectAI
from toontown.minigame import Trajectory
from toontown.estate import DistributedCannonAI
from toontown.estate import CannonGlobals
from toontown.minigame import CannonGameGlobals

class DistributedLawbotCannonAI(DistributedObjectAI.DistributedObjectAI):
    notify = directNotify.newCategory('DistributedLawbotCannonAI')

    def __init__(self, air, lawbotBoss, index, x, y, z, h, p, r):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.index = index
        self.posHpr = [x, y, z, h, p, r]
        self.boss = lawbotBoss
        self.bossId = lawbotBoss.doId
        self.avId = 0

    def delete(self):
        self.ignoreAll()
        DistributedObjectAI.DistributedObjectAI.delete(self)

    def getBossCogId(self):
        return self.boss.doId

    def getIndex(self):
        return self.index

    def getPosHpr(self):
        return self.posHpr

    def canEnterCannon(self):
        avId = self.air.getAvatarIdFromSender()
        if self.boss.getCannonBallsLeft(avId) == 0:
            return False
        if not self.boss.state == 'BattleTwo':
            return False
        if not (self.avId == 0 or self.avId == avId):
            return False
        return True

    def requestEnter(self):
        avId = self.air.getAvatarIdFromSender()
        if not self.canEnterCannon():
            return
        if self.avId == 0 or self.avId == avId:
            self.avId = avId
            self.boss.toonEnteredCannon(self.avId, self.index)
            cannonBallsLeft = self.boss.getCannonBallsLeft(avId)
            self.setMovie(CannonGlobals.CANNON_MOVIE_LOAD, self.avId, cannonBallsLeft)
            self.acceptOnce(self.air.getAvatarExitEvent(avId), self.__handleUnexpectedExit, extraArgs=[avId])
        else:
            self.air.writeServerEvent('suspicious', avId, 'DistributedLawbotCannonAI.requestEnter cannon already occupied')
            self.notify.warning('requestEnter() - cannon already occupied')

    def setMovie(self, mode, avId, extraInfo):
        self.avId = avId
        self.sendUpdate('setMovie', [mode, avId, extraInfo])

    def __handleUnexpectedExit(self, avId):
        self.notify.warning('avatar:' + str(avId) + ' has exited unexpectedly')
        self.__doExit()

    def __doExit(self):
        self.setMovie(CannonGlobals.CANNON_MOVIE_FORCE_EXIT, self.avId, 0)
        self.avId = 0

    def requestLeave(self):
        avId = self.air.getAvatarIdFromSender()
        if self.avId != 0:
            self.__doExit()
        else:
            self.air.writeServerEvent('suspicious', avId, 'DistributedCannonAI.requestLeave cannon not occupied')
            self.notify.warning('requestLeave() - cannon not occupied')

    def setCannonPosition(self, zRot, angle):
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug('setCannonPosition: ' + str(avId) + ': zRot=' + str(zRot) + ', angle=' + str(angle))
        self.sendUpdate('updateCannonPosition', [avId, zRot, angle])

    def setLanded(self):
        self.ignore(self.air.getAvatarExitEvent(self.avId))
        if self.canEnterCannon():
            self.requestEnter()
        else:
            self.setMovie(CannonGlobals.CANNON_MOVIE_LANDED, 0, 0)

    def setCannonLit(self, zRot, angle):
        if not self.boss.state == 'BattleTwo':
            self.notify.debug('ignoring setCannonList since boss in state %s' % self.boss.state)
            return
        avId = self.air.getAvatarIdFromSender()
        if self.boss.getCannonBallsLeft(avId) == 0:
            self.notify.debug('ignoring setCannonList since no balls left for %s' % avId)
            return
        self.notify.debug('setCannonLit: ' + str(avId) + ': zRot=' + str(zRot) + ', angle=' + str(angle))
        fireTime = CannonGameGlobals.FUSE_TIME
        self.sendUpdate('setCannonWillFire', [avId, fireTime, zRot, angle, globalClockDelta.getRealNetworkTime()])
        self.boss.decrementCannonBallsLeft(avId)
