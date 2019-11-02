from pandac.PandaModules import *
from direct.distributed import DistributedObjectAI
from toontown.toonbase import ToontownGlobals
from otp.otpbase import OTPGlobals
from direct.fsm import FSM

class DistributedCashbotBossCraneAI(DistributedObjectAI.DistributedObjectAI, FSM.FSM):

    def __init__(self, air, boss, index):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        FSM.FSM.__init__(self, 'DistributedCashbotBossCraneAI')
        self.boss = boss
        self.index = index
        cn = CollisionNode('controls')
        cs = CollisionSphere(0, -6, 0, 6)
        cn.addSolid(cs)
        self.goonShield = NodePath(cn)
        self.goonShield.setPosHpr(*ToontownGlobals.CashbotBossCranePosHprs[self.index])
        self.avId = 0
        self.objectId = 0

    def getBossCogId(self):
        return self.boss.doId

    def getIndex(self):
        return self.index

    def d_setState(self, state, avId):
        self.sendUpdate('setState', [state, avId])

    def requestControl(self):
        avId = self.air.getAvatarIdFromSender()
        if avId in self.boss.involvedToons and self.avId == 0:
            craneId = self.__getCraneId(avId)
            if craneId == 0:
                self.request('Controlled', avId)

    def requestFree(self):
        avId = self.air.getAvatarIdFromSender()
        if avId == self.avId:
            self.request('Free')

    def removeToon(self, avId):
        if avId == self.avId:
            self.request('Free')

    def __getCraneId(self, avId):
        if self.boss and self.boss.cranes != None:
            for crane in self.boss.cranes:
                if crane.avId == avId:
                    return crane.doId

        return 0

    def enterOff(self):
        self.goonShield.detachNode()

    def exitOff(self):
        self.goonShield.reparentTo(self.boss.scene)

    def enterControlled(self, avId):
        self.avId = avId
        self.d_setState('C', avId)

    def exitControlled(self):
        if self.objectId:
            obj = self.air.doId2do[self.objectId]
            obj.request('Dropped', self.avId, self.doId)

    def enterFree(self):
        self.avId = 0
        self.d_setState('F', 0)

    def exitFree(self):
        pass
