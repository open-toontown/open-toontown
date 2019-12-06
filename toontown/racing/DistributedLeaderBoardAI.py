from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI


class DistributedLeaderBoardAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedLeaderBoardAI')

    def __init__(self, air, name, x, y, z, h, p, r):
        DistributedObjectAI.__init__(self, air)
        self.name = name
        self.posHpr = (x, y, z, h, p, r)

    def getName(self):
        return self.name

    def getPosHpr(self):
        return self.posHpr

    def subscribeTo(self, subscription):
        pass  # TODO
