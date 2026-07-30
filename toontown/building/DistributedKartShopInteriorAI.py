from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI

class DistributedKartShopInteriorAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedKartShopInteriorAI')

    def __init__(self, block, air, zoneId):
        DistributedObjectAI.__init__(self, air)
        self.block = block
        self.zoneId = zoneId

    def generate(self):
        DistributedObjectAI.generate(self)

    def getZoneIdAndBlock(self):
        return [
         self.zoneId, self.block]
