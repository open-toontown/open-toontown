from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI


class DistributedKartPadAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedKartPadAI')

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)
        self.area = None
        self.startingBlocks = []
        self.index = -1

    def setArea(self, area):
        self.area = area

    def getArea(self):
        return self.area

    def addStartingBlock(self, startingBlock):
        self.startingBlocks.append(startingBlock)

    def addAvBlock(self, avId, startingBlock, paid):
        pass

    def removeAvBlock(self, avId, startingBlock):
        pass

    def kartMovieDone(self):
        pass
