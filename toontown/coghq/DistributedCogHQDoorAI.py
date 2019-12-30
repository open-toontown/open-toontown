from otp.ai.AIBaseGlobal import *
from direct.distributed.ClockDelta import *
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM
from toontown.building import DistributedDoorAI
from direct.fsm import State
from toontown.toonbase import ToontownGlobals
from . import CogDisguiseGlobals
from toontown.building import FADoorCodes
from toontown.building import DoorTypes
from toontown.toonbase import ToontownAccessAI

class DistributedCogHQDoorAI(DistributedDoorAI.DistributedDoorAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedCogHQDoorAI')

    def __init__(self, air, blockNumber, doorType, destinationZone, doorIndex=0, lockValue=FADoorCodes.SB_DISGUISE_INCOMPLETE, swing=3):
        DistributedDoorAI.DistributedDoorAI.__init__(self, air, blockNumber, doorType, doorIndex, lockValue, swing)
        self.destinationZone = destinationZone

    def requestEnter(self):
        avatarID = self.air.getAvatarIdFromSender()
        allowed = 0
        dept = ToontownGlobals.cogHQZoneId2deptIndex(self.destinationZone)
        av = self.air.doId2do.get(avatarID)
        if av:
            if self.doorType == DoorTypes.EXT_COGHQ and self.isLockedDoor():
                parts = av.getCogParts()
                if CogDisguiseGlobals.isSuitComplete(parts, dept):
                    allowed = 1
                else:
                    allowed = 0
            else:
                allowed = 1

        if not ToontownAccessAI.canAccess(avatarID, self.zoneId, 'DistributedCogHQDoorAI.requestEnter'):
            allowed = 0

        if not allowed:
            self.sendReject(avatarID, self.isLockedDoor())
        else:
            self.enqueueAvatarIdEnter(avatarID)
            self.sendUpdateToAvatarId(avatarID, 'setOtherZoneIdAndDoId', [
                self.destinationZone,
                self.otherDoor.getDoId()])

    def requestExit(self):
        avatarID = self.air.getAvatarIdFromSender()
        if avatarID in self.avatarsWhoAreEntering:
            del self.avatarsWhoAreEntering[avatarID]
        if avatarID not in self.avatarsWhoAreExiting:
            dept = ToontownGlobals.cogHQZoneId2deptIndex(self.destinationZone)
            self.avatarsWhoAreExiting[avatarID] = 1
            self.sendUpdate('avatarExit', [avatarID])
            self.openDoor(self.exitDoorFSM)
            if self.lockedDoor:
                av = self.air.doId2do[avatarID]
                if self.doorType == DoorTypes.EXT_COGHQ:
                    av.b_setCogIndex(-1)
                else:
                    av.b_setCogIndex(dept)
