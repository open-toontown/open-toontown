from pandac.PandaModules import *
from direct.directnotify import DirectNotifyGlobal
from . import DistributedDoorAI, DistributedHQInteriorAI, FADoorCodes, DoorTypes
from toontown.toon import NPCToons
from toontown.quest import Quests

class HQBuildingAI:

    def __init__(self, air, exteriorZone, interiorZone, blockNumber):
        self.air = air
        self.exteriorZone = exteriorZone
        self.interiorZone = interiorZone
        self.setup(blockNumber)

    def cleanup(self):
        for npc in self.npcs:
            npc.requestDelete()

        del self.npcs
        self.door0.requestDelete()
        del self.door0
        self.door1.requestDelete()
        del self.door1
        self.insideDoor0.requestDelete()
        del self.insideDoor0
        self.insideDoor1.requestDelete()
        del self.insideDoor1
        self.interior.requestDelete()
        del self.interior

    def setup(self, blockNumber):
        self.interior = DistributedHQInteriorAI.DistributedHQInteriorAI(blockNumber, self.air, self.interiorZone)
        self.npcs = NPCToons.createNpcsInZone(self.air, self.interiorZone)
        self.interior.generateWithRequired(self.interiorZone)
        door0 = DistributedDoorAI.DistributedDoorAI(self.air, blockNumber, DoorTypes.EXT_HQ, doorIndex=0)
        door1 = DistributedDoorAI.DistributedDoorAI(self.air, blockNumber, DoorTypes.EXT_HQ, doorIndex=1)
        insideDoor0 = DistributedDoorAI.DistributedDoorAI(self.air, blockNumber, DoorTypes.INT_HQ, doorIndex=0)
        insideDoor1 = DistributedDoorAI.DistributedDoorAI(self.air, blockNumber, DoorTypes.INT_HQ, doorIndex=1)
        door0.setOtherDoor(insideDoor0)
        insideDoor0.setOtherDoor(door0)
        door1.setOtherDoor(insideDoor1)
        insideDoor1.setOtherDoor(door1)
        door0.zoneId = self.exteriorZone
        door1.zoneId = self.exteriorZone
        insideDoor0.zoneId = self.interiorZone
        insideDoor1.zoneId = self.interiorZone
        door0.generateWithRequired(self.exteriorZone)
        door1.generateWithRequired(self.exteriorZone)
        door0.sendUpdate('setDoorIndex', [door0.getDoorIndex()])
        door1.sendUpdate('setDoorIndex', [door1.getDoorIndex()])
        insideDoor0.generateWithRequired(self.interiorZone)
        insideDoor1.generateWithRequired(self.interiorZone)
        insideDoor0.sendUpdate('setDoorIndex', [insideDoor0.getDoorIndex()])
        insideDoor1.sendUpdate('setDoorIndex', [insideDoor1.getDoorIndex()])
        self.door0 = door0
        self.door1 = door1
        self.insideDoor0 = insideDoor0
        self.insideDoor1 = insideDoor1

    def isSuitBlock(self):
        return 0

    def isSuitBuilding(self):
        return 0

    def isCogdo(self):
        return 0

    def isEstablishedSuitBlock(self):
        return 0
