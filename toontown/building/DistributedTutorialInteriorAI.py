from toontown.toonbase.ToontownGlobals import *
from otp.ai.AIBaseGlobal import *
from direct.distributed.ClockDelta import *

from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObjectAI
from toontown.toon import NPCToons

class DistributedTutorialInteriorAI(DistributedObjectAI.DistributedObjectAI):

    if __debug__:
        notify = DirectNotifyGlobal.directNotify.newCategory('DistributedTutorialInteriorAI')

    def __init__(self, *args):
        """Supports both Astron (air) construction and manual (block, air, zoneId, building, npcId) construction."""
        if len(args) == 1:
            air = args[0]
            block = 0
            zoneId = 0
            building = None
            npcId = 0
        else:
            block, air, zoneId, building, npcId = args[:5]
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.block = block
        self.zoneId = zoneId
        self.building = building
        self.tutorialNpcId = npcId


        # Make any npcs that may be in this interior zone
        # If there are none specified, this will just be an empty list
        self.npcs = NPCToons.createNpcsInZone(air, zoneId) if zoneId else []

    def setZoneIdAndBlock(self, zoneId, block):
        self.zoneId = zoneId
        self.block = block
        if not getattr(self, 'npcs', None):
            self.npcs = NPCToons.createNpcsInZone(self.air, zoneId) if zoneId else []

    def delete(self):
        self.ignoreAll()
        for npc in self.npcs:
            npc.requestDelete()
        del self.npcs
        del self.building
        DistributedObjectAI.DistributedObjectAI.delete(self)

    def getZoneIdAndBlock(self):
        return [self.zoneId, self.block]

    def getTutorialNpcId(self):
        return self.tutorialNpcId