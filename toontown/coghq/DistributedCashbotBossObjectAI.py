from panda3d.core import *
from direct.distributed import DistributedSmoothNodeAI
from toontown.toonbase import ToontownGlobals
from otp.otpbase import OTPGlobals
from direct.fsm import FSM
from direct.task import Task

class DistributedCashbotBossObjectAI(DistributedSmoothNodeAI.DistributedSmoothNodeAI, FSM.FSM):
    wantsWatchDrift = 1

    def __init__(self, air, boss):
        DistributedSmoothNodeAI.DistributedSmoothNodeAI.__init__(self, air)
        FSM.FSM.__init__(self, 'DistributedCashbotBossObjectAI')
        self.boss = boss
        self.reparentTo(self.boss.scene)
        self.avId = 0
        self.craneId = 0

    def cleanup(self):
        self.detachNode()
        self.stopWaitFree()

    def delete(self):
        self.cleanup()
        DistributedSmoothNodeAI.DistributedSmoothNodeAI.delete(self)

    def startWaitFree(self, delayTime):
        waitFreeEvent = self.uniqueName('waitFree')
        taskMgr.remove(waitFreeEvent)
        taskMgr.doMethodLater(delayTime, self.doFree, waitFreeEvent)

    def stopWaitFree(self):
        waitFreeEvent = self.uniqueName('waitFree')
        taskMgr.remove(waitFreeEvent)

    def doFree(self, task):
        if not self.isDeleted():
            self.demand('Free')
            p = self.getPos()
            h = self.getH()
            self.d_setPosHpr(p[0], p[1], 0, h, 0, 0)
        return Task.done

    def getBossCogId(self):
        return self.boss.doId

    def d_setObjectState(self, state, avId, craneId):
        self.sendUpdate('setObjectState', [state, avId, craneId])

    def requestGrab(self):
        avId = self.air.getAvatarIdFromSender()
        if self.state != 'Grabbed' and self.state != 'Off':
            craneId, objectId = self.__getCraneAndObject(avId)
            if craneId != 0 and objectId == 0:
                self.demand('Grabbed', avId, craneId)
                return
        self.sendUpdateToAvatarId(avId, 'rejectGrab', [])

    def requestDrop(self):
        avId = self.air.getAvatarIdFromSender()
        if avId == self.avId and self.state == 'Grabbed':
            craneId, objectId = self.__getCraneAndObject(avId)
            if craneId != 0 and objectId == self.doId:
                self.demand('Dropped', avId, craneId)

    def hitFloor(self):
        avId = self.air.getAvatarIdFromSender()
        if avId == self.avId and self.state == 'Dropped':
            self.demand('SlidingFloor', avId)

    def requestFree(self, x, y, z, h):
        avId = self.air.getAvatarIdFromSender()
        if avId == self.avId:
            self.setPosHpr(x, y, 0, h, 0, 0)
            self.demand('WaitFree')

    def hitBoss(self, impact):
        pass

    def removeToon(self, avId):
        if avId == self.avId:
            self.doFree(None)
        return

    def __getCraneAndObject(self, avId):
        if self.boss and self.boss.cranes != None:
            for crane in self.boss.cranes:
                if crane.avId == avId:
                    return (crane.doId, crane.objectId)

        return (0, 0)

    def __setCraneObject(self, craneId, objectId):
        if self.air:
            crane = self.air.doId2do.get(craneId)
            if crane:
                crane.objectId = objectId

    def enterGrabbed(self, avId, craneId):
        self.avId = avId
        self.craneId = craneId
        self.__setCraneObject(self.craneId, self.doId)
        self.d_setObjectState('G', avId, craneId)

    def exitGrabbed(self):
        self.__setCraneObject(self.craneId, 0)

    def enterDropped(self, avId, craneId):
        self.avId = avId
        self.craneId = craneId
        self.d_setObjectState('D', avId, craneId)
        self.startWaitFree(10)

    def exitDropped(self):
        self.stopWaitFree()

    def enterSlidingFloor(self, avId):
        self.avId = avId
        self.d_setObjectState('s', avId, 0)
        if self.wantsWatchDrift:
            self.startWaitFree(5)

    def exitSlidingFloor(self):
        self.stopWaitFree()

    def enterWaitFree(self):
        self.avId = 0
        self.craneId = 0
        self.startWaitFree(1)

    def exitWaitFree(self):
        self.stopWaitFree()

    def enterFree(self):
        self.avId = 0
        self.craneId = 0
        self.d_setObjectState('F', 0, 0)

    def exitFree(self):
        pass
