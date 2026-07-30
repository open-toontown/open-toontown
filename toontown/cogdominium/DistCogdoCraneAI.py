from panda3d.core import *
from direct.distributed import DistributedObjectAI
from toontown.toonbase import ToontownGlobals
from otp.otpbase import OTPGlobals
from direct.fsm import FSM

class DistCogdoCraneAI(DistributedObjectAI.DistributedObjectAI, FSM.FSM):

    def __init__(self, air, craneGame, index):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        FSM.FSM.__init__(self, 'DistCogdoCraneAI')
        self.craneGame = craneGame
        self.index = index
        self.avId = 0
        self.objectId = 0

    def getCraneGameId(self):
        return self.craneGame.doId

    def getIndex(self):
        return self.index

    def generate(self):
        DistributedObjectAI.DistributedObjectAI.generate(self)
        self.request('Free')

    def d_setState(self, state, avId):
        self.sendUpdate('setState', [
            state,
            avId])

    def enterOff(self):
        pass

    def exitOff(self):
        pass

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
