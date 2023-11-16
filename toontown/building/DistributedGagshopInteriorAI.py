from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObjectAI


class DistributedGagshopInteriorAI(DistributedObjectAI.DistributedObjectAI):

    def __init__(self, block, air, zoneId):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.block = block
        self.zoneId = zoneId

    def getZoneIdAndBlock(self):
        r = [
         self.zoneId, self.block]
        return r
