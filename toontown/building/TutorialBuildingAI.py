from panda3d.core import *
from direct.directnotify import DirectNotifyGlobal
from . import DistributedDoorAI
from . import DistributedTutorialInteriorAI
from . import FADoorCodes
from . import DoorTypes
from toontown.toon import NPCToons
from toontown.toonbase import TTLocalizer

# This is not a distributed class... It just owns and manages some distributed
# classes.

class TutorialBuildingAI:
    def __init__(self, air, exteriorZone, interiorZone, blockNumber):
        # While this is not a distributed object, it needs to know about
        # the repository.
        self.air = air
        self.exteriorZone = exteriorZone
        self.interiorZone = interiorZone
        
        # This is because we are "pretending" to be a DistributedBuilding.
        # The DistributedTutorialInterior takes a peek at savedBy. It really
        # should make a function call. Perhaps TutorialBuildingAI and
        # DistributedBuildingAI should inherit from each other somehow,
        # but I can't see an easy way to do that.
        self.savedBy = None
        
        self.setup(blockNumber)

    def cleanup(self):
        self.interior.requestDelete()
        del self.interior
        self.door.requestDelete()
        del self.door
        self.insideDoor.requestDelete()
        del self.insideDoor
        self.gagShopNPC.requestDelete()
        del self.gagShopNPC
        return

    def setup(self, blockNumber):
        # Put an NPC in here. Give him id# 20000. When he has assigned
        # his quest, he will unlock the interior door.
        self.gagShopNPC = NPCToons.createNPC(
            self.air, 20000,
            (self.interiorZone,
             TTLocalizer.NPCToonNames[20000],
             ("dll" ,"ms" ,"m" ,"m" ,7 ,0 ,7 ,7 ,2 ,6 ,2 ,6 ,2 ,16), "m", 1, NPCToons.NPC_REGULAR),
            self.interiorZone,
            questCallback=self.unlockInteriorDoor)
        # Flag him as being part of tutorial
        self.gagShopNPC.setTutorial(1)
        npcId = self.gagShopNPC.getDoId()
        # Toon interior (with tutorial flag set to 1)
        self.interior=DistributedTutorialInteriorAI.DistributedTutorialInteriorAI(
            blockNumber, self.air, self.interiorZone, self, npcId)
        self.interior.generateWithRequired(self.interiorZone)
        # Outside door:
        door=DistributedDoorAI.DistributedDoorAI(self.air, blockNumber,
                                                 DoorTypes.EXT_STANDARD,
                                                 lockValue=FADoorCodes.DEFEAT_FLUNKY_TOM)
        # Inside door. Locked until you get your gags.
        insideDoor=DistributedDoorAI.DistributedDoorAI(
            self.air,
            blockNumber,
            DoorTypes.INT_STANDARD,
            lockValue=FADoorCodes.TALK_TO_TOM)
        # Tell them about each other:
        door.setOtherDoor(insideDoor)
        insideDoor.setOtherDoor(door)
        door.zoneId=self.exteriorZone
        insideDoor.zoneId=self.interiorZone
        # Now that they both now about each other, generate them:
        door.generateWithRequired(self.exteriorZone)
        #door.sendUpdate("setDoorIndex", [door.getDoorIndex()])
        insideDoor.generateWithRequired(self.interiorZone)
        #insideDoor.sendUpdate("setDoorIndex", [door.getDoorIndex()])
        # keep track of them:
        self.door=door
        self.insideDoor=insideDoor
        return
       
    def unlockInteriorDoor(self):
        self.insideDoor.setDoorLock(FADoorCodes.UNLOCKED)

    def battleOverCallback(self):
        # There is an if statement here because it is possible for
        # the callback to get called after cleanup has already taken
        # place.
        if hasattr(self, "door"):
            self.door.setDoorLock(FADoorCodes.TALK_TO_HQ_TOM)