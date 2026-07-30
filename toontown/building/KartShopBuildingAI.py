from direct.directnotify import DirectNotifyGlobal
from panda3d.core import *
from toontown.building import FADoorCodes, DoorTypes
from toontown.building.DistributedDoorAI import DistributedDoorAI
from toontown.building.DistributedKartShopInteriorAI import DistributedKartShopInteriorAI
from toontown.hood import ZoneUtil
from toontown.toon import NPCToons
from toontown.toonbase import ToontownGlobals
if __debug__:
    import pdb

class KartShopBuildingAI:
    notify = DirectNotifyGlobal.directNotify.newCategory('KartShopBuildingAI')

    def __init__(self, air, exteriorZone, interiorZone, blockNumber):
        self.air = air
        self.exteriorZone = exteriorZone
        self.interiorZone = interiorZone
        self.setup(blockNumber)

    def cleanup(self):
        for npc in self.npcs:
            npc.requestDelete()

        del self.npcs
        self.outsideDoor0.requestDelete()
        self.outsideDoor1.requestDelete()
        self.insideDoor0.requestDelete()
        self.insideDoor1.requestDelete()
        del self.outsideDoor0
        del self.insideDoor0
        del self.outsideDoor1
        del self.insideDoor1
        self.kartShopInterior.requestDelete()
        del self.kartShopInterior

    def setup(self, blockNumber):
        self.kartShopInterior = DistributedKartShopInteriorAI(blockNumber, self.air, self.interiorZone)
        self.npcs = NPCToons.createNpcsInZone(self.air, self.interiorZone)
        self.kartShopInterior.generateWithRequired(self.interiorZone)
        self.outsideDoor0 = DistributedDoorAI(self.air, blockNumber, DoorTypes.EXT_KS, doorIndex=1)
        self.outsideDoor1 = DistributedDoorAI(self.air, blockNumber, DoorTypes.EXT_KS, doorIndex=2)
        self.insideDoor0 = DistributedDoorAI(self.air, blockNumber, DoorTypes.INT_KS, doorIndex=1)
        self.insideDoor1 = DistributedDoorAI(self.air, blockNumber, DoorTypes.INT_KS, doorIndex=2)
        self.outsideDoor0.setOtherDoor(self.insideDoor0)
        self.outsideDoor1.setOtherDoor(self.insideDoor1)
        self.insideDoor0.setOtherDoor(self.outsideDoor0)
        self.insideDoor1.setOtherDoor(self.outsideDoor1)
        self.outsideDoor0.zoneId = self.exteriorZone
        self.outsideDoor1.zoneId = self.exteriorZone
        self.insideDoor0.zoneId = self.interiorZone
        self.insideDoor1.zoneId = self.interiorZone
        self.outsideDoor0.generateWithRequired(self.exteriorZone)
        self.outsideDoor1.generateWithRequired(self.exteriorZone)
        self.insideDoor0.generateWithRequired(self.interiorZone)
        self.insideDoor1.generateWithRequired(self.interiorZone)
        self.outsideDoor0.sendUpdate('setDoorIndex', [self.outsideDoor0.getDoorIndex()])
        self.outsideDoor1.sendUpdate('setDoorIndex', [self.outsideDoor1.getDoorIndex()])
        self.insideDoor0.sendUpdate('setDoorIndex', [self.insideDoor0.getDoorIndex()])
        self.insideDoor1.sendUpdate('setDoorIndex', [self.insideDoor1.getDoorIndex()])
