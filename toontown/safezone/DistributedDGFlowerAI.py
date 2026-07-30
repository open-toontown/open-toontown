from otp.ai.AIBase import *
from toontown.toonbase.ToontownGlobals import *
from direct.distributed.ClockDelta import *
from direct.distributed import DistributedObjectAI
from direct.task import Task
HEIGHT_DELTA = 0.5
MAX_HEIGHT = 10.0
MIN_HEIGHT = 2.0

class DistributedDGFlowerAI(DistributedObjectAI.DistributedObjectAI):

    def __init__(self, air):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.height = MIN_HEIGHT
        self.avList = []
        return None

    def delete(self):
        DistributedObjectAI.DistributedObjectAI.delete(self)

    def start(self):
        return None

    def avatarEnter(self):
        avId = self.air.getAvatarIdFromSender()
        if avId not in self.avList:
            self.avList.append(avId)
            if self.height + HEIGHT_DELTA <= MAX_HEIGHT:
                self.height += HEIGHT_DELTA
                self.sendUpdate('setHeight', [self.height])

    def avatarExit(self):
        avId = self.air.getAvatarIdFromSender()
        if avId in self.avList:
            self.avList.remove(avId)
            if self.height - HEIGHT_DELTA >= MIN_HEIGHT:
                self.height -= HEIGHT_DELTA
                self.sendUpdate('setHeight', [self.height])
