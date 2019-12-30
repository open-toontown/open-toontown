from otp.ai.AIBase import *
from direct.directnotify import DirectNotifyGlobal
from otp.level import DistributedEntityAI
from . import StomperGlobals
from direct.distributed import ClockDelta

class DistributedStomperPairAI(DistributedEntityAI.DistributedEntityAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedStomperAI')

    def __init__(self, level, entId):
        DistributedEntityAI.DistributedEntityAI.__init__(self, level, entId)
        self.stompers = [None, None]
        self.hitPtsTaken = 3
        return

    def generate(self):
        DistributedEntityAI.DistributedEntityAI.generate(self)

    def delete(self):
        DistributedEntityAI.DistributedEntityAI.delete(self)

    def setChildren(self, doIds):
        for id in doIds:
            self.children = simbase.air.doId2do[id]

        self.sendUpdate('setChildren', [doIds])

    def setSquash(self):
        avId = self.air.getAvatarIdFromSender()
        av = simbase.air.doId2do.get(avId)
        if av:
            av.takeDamage(self.hitPtsTaken)
