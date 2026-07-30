from panda3d.core import *
from direct.directnotify import DirectNotifyGlobal
from . import DistributedDoorAI
from . import DistributedHQInteriorAI
from . import FADoorCodes
from . import DoorTypes
from toontown.toon import NPCToons
from toontown.quest import Quests
from toontown.toonbase import TTLocalizer

# This is not a distributed class... It just owns and manages some distributed
# classes.

class TutorialHQBuildingAI:
    def __init__(self, air, exteriorZone, interiorZone, blockNumber):
        # While this is not a distributed object, it needs to know about
        # the repository.
        self.air = air
        self.exteriorZone = exteriorZone
        self.interiorZone = interiorZone
        
        self.setup(blockNumber)

    def cleanup(self):
        self.interior.requestDelete()
        del self.interior
        self.npc.requestDelete()
        del self.npc
        self.door0.requestDelete()
        del self.door0
        self.door1.requestDelete()
        del self.door1
        self.insideDoor0.requestDelete()
        del self.insideDoor0
        self.insideDoor1.requestDelete()
        del self.insideDoor1
        return

    def setup(self, blockNumber):
        # The interior
        self.interior=DistributedHQInteriorAI.DistributedHQInteriorAI(
            blockNumber, self.air, self.interiorZone)

        # We do not use a standard npc toon here becuase these npcs are created on
        # the fly for as many tutorials as we need. The interior zone is not known
        # until the ai allocates a zone, so we fabricate the description here.
        desc = (self.interiorZone, TTLocalizer.TutorialHQOfficerName, ('dls', 'ms', 'm', 'm', 6,0,6,6,0,10,0,10,2,9), "m", 1, 0)
        self.npc = NPCToons.createNPC(self.air, Quests.ToonHQ, desc,
                                      self.interiorZone,
                                      questCallback=self.unlockInsideDoor1)
        # Flag npc as part of tutorial
        self.npc.setTutorial(1)

        self.interior.generateWithRequired(self.interiorZone)
        # Outside door 0. Locked til you defeat the Flunky:
        door0=DistributedDoorAI.DistributedDoorAI(
            self.air, blockNumber, DoorTypes.EXT_HQ,
            doorIndex=0,
            lockValue=FADoorCodes.DEFEAT_FLUNKY_HQ)
        # Outside door 1. Always locked.
        door1=DistributedDoorAI.DistributedDoorAI(
            self.air, blockNumber, DoorTypes.EXT_HQ,
            doorIndex=1,
            lockValue=FADoorCodes.GO_TO_PLAYGROUND)
        # Inside door 0. Always locked, but the message will change.
        insideDoor0=DistributedDoorAI.DistributedDoorAI(
            self.air,
            blockNumber,
            DoorTypes.INT_HQ,
            doorIndex=0,
            lockValue=FADoorCodes.TALK_TO_HQ)
        # Inside door 1. Locked til you get your HQ reward.
        insideDoor1=DistributedDoorAI.DistributedDoorAI(
            self.air,
            blockNumber,
            DoorTypes.INT_HQ,
            doorIndex=1,
            lockValue=FADoorCodes.TALK_TO_HQ)
        # Tell them about each other:
        door0.setOtherDoor(insideDoor0)
        insideDoor0.setOtherDoor(door0)
        door1.setOtherDoor(insideDoor1)
        insideDoor1.setOtherDoor(door1)
        # Put them in the right zones
        door0.zoneId=self.exteriorZone
        door1.zoneId=self.exteriorZone
        insideDoor0.zoneId=self.interiorZone
        insideDoor1.zoneId=self.interiorZone
        # Now that they both now about each other, generate them:
        door0.generateWithRequired(self.exteriorZone)
        door1.generateWithRequired(self.exteriorZone)
        door0.sendUpdate("setDoorIndex", [door0.getDoorIndex()])
        door1.sendUpdate("setDoorIndex", [door1.getDoorIndex()])
        insideDoor0.generateWithRequired(self.interiorZone)
        insideDoor1.generateWithRequired(self.interiorZone)
        insideDoor0.sendUpdate("setDoorIndex", [insideDoor0.getDoorIndex()])
        insideDoor1.sendUpdate("setDoorIndex", [insideDoor1.getDoorIndex()])
        # keep track of them:
        self.door0=door0
        self.door1=door1
        self.insideDoor0=insideDoor0
        self.insideDoor1=insideDoor1
        # hide the periscope
        self.interior.setTutorial(1)
        return
       
    def unlockDoor(self, door):
        door.setDoorLock(FADoorCodes.UNLOCKED)

    def battleOverCallback(self):
        # There is an if statement here because it is possible for
        # the callback to get called after cleanup has already taken
        # place.
        if hasattr(self, "door0"):
            self.unlockDoor(self.door0)

    # This callback type happens to give zoneId. We don't need it.
    def unlockInsideDoor1(self):
        # There is an if statement here because it is possible for
        # the callback to get called after cleanup has already taken
        # place.
        if hasattr(self, "insideDoor1"):
            self.unlockDoor(self.insideDoor1)
        # Change the message on this locked door to tell you to go
        # through the other door. Maybe this door should not be
        # here at all?
        if hasattr(self, "insideDoor0"):
            self.insideDoor0.setDoorLock(FADoorCodes.WRONG_DOOR_HQ)