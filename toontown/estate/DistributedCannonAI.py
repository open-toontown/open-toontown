from toontown.toonbase import ToontownGlobals
from direct.distributed.ClockDelta import *
from direct.fsm import ClassicFSM
from direct.fsm import State
from direct.task import Task
from toontown.minigame import CannonGameGlobals
from direct.distributed import DistributedObjectAI
from toontown.minigame import Trajectory
from . import CannonGlobals

class DistributedCannonAI(DistributedObjectAI.DistributedObjectAI):
    notify = directNotify.newCategory('DistributedCannonAI')

    def __init__(self, air, estateId, targetId, x, y, z, h, p, r):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.posHpr = [x,
         y,
         z,
         h,
         p,
         r]
        self.avId = 0
        self.estateId = estateId
        self.timeoutTask = None
        self.targetId = targetId
        self.cannonBumperPos = list(ToontownGlobals.PinballCannonBumperInitialPos)
        return

    def delete(self):
        self.ignoreAll()
        self.__stopTimeout()
        DistributedObjectAI.DistributedObjectAI.delete(self)

    def requestEnter(self):
        avId = self.air.getAvatarIdFromSender()
        if self.avId == 0:
            self.avId = avId
            self.__stopTimeout()
            self.setMovie(CannonGlobals.CANNON_MOVIE_LOAD, self.avId)
            self.acceptOnce(self.air.getAvatarExitEvent(avId), self.__handleUnexpectedExit, extraArgs=[avId])
            self.acceptOnce('bootAvFromEstate-' + str(avId), self.__handleBootMessage, extraArgs=[avId])
            self.__startTimeout(CannonGlobals.CANNON_TIMEOUT)
        else:
            self.air.writeServerEvent('suspicious', avId, 'DistributedCannonAI.requestEnter cannon already occupied')
            self.notify.warning('requestEnter() - cannon already occupied')
            self.sendUpdateToAvatarId(avId, 'requestExit', [])

    def setMovie(self, mode, avId):
        self.avId = avId
        self.sendUpdate('setMovie', [mode, avId])

    def getCannonBumperPos(self):
        self.notify.debug('---------getCannonBumperPos %s' % self.cannonBumperPos)
        return self.cannonBumperPos

    def requestBumperMove(self, x, y, z):
        self.cannonBumperPos = [x, y, z]
        self.sendUpdate('setCannonBumperPos', [x, y, z])

    def getPosHpr(self):
        return self.posHpr

    def getEstateId(self):
        return self.estateId

    def getTargetId(self):
        return self.targetId

    def setCannonPosition(self, zRot, angle):
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug('setCannonPosition: ' + str(avId) + ': zRot=' + str(zRot) + ', angle=' + str(angle))
        self.sendUpdate('updateCannonPosition', [avId, zRot, angle])

    def setCannonLit(self, zRot, angle):
        avId = self.air.getAvatarIdFromSender()
        self.__stopTimeout()
        self.notify.debug('setCannonLit: ' + str(avId) + ': zRot=' + str(zRot) + ', angle=' + str(angle))
        fireTime = CannonGameGlobals.FUSE_TIME
        self.sendUpdate('setCannonWillFire', [avId,
         fireTime,
         zRot,
         angle,
         globalClockDelta.getRealNetworkTime()])

    def setLanded(self):
        self.ignore(self.air.getAvatarExitEvent(self.avId))
        self.setMovie(CannonGlobals.CANNON_MOVIE_LANDED, 0)
        self.avId = 0

    def setActive(self, active):
        if active < 0 or active > 1:
            self.air.writeServerEvent('suspicious', active, 'DistributedCannon.setActive value should be 0-1 range')
            return
        self.active = active
        self.sendUpdate('setActiveState', [active])

    def __startTimeout(self, timeLimit):
        self.__stopTimeout()
        self.timeoutTask = taskMgr.doMethodLater(timeLimit, self.__handleTimeout, self.taskName('timeout'))

    def __stopTimeout(self):
        if self.timeoutTask != None:
            taskMgr.remove(self.timeoutTask)
            self.timeoutTask = None
        return

    def __handleTimeout(self, task):
        self.notify.debug('Timeout expired!')
        self.__doExit()
        return Task.done

    def __handleUnexpectedExit(self, avId):
        self.notify.warning('avatar:' + str(avId) + ' has exited unexpectedly')
        self.__doExit()

    def __handleBootMessage(self, avId):
        self.notify.warning('avatar:' + str(avId) + ' got booted ')
        self.__doExit()

    def __doExit(self):
        self.setMovie(CannonGlobals.CANNON_MOVIE_FORCE_EXIT, self.avId)
