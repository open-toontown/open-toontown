from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI


class DistributedKartPadAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedKartPadAI')

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)
        self.area = None

    def setArea(self, area):
        self.area = area

    def getArea(self):
        return self.area
