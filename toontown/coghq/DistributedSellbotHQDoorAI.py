from direct.directnotify import DirectNotifyGlobal
from toontown.coghq import DistributedCogHQDoorAI
from toontown.building import FADoorCodes, DoorTypes
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import ToontownAccessAI
import CogDisguiseGlobals
from otp.otpbase import OTPGlobals

class DistributedSellbotHQDoorAI(DistributedCogHQDoorAI.DistributedCogHQDoorAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedSellbotHQDoorAI')

    def __init__(self, air, blockNumber, doorType, destinationZone, doorIndex = 0, lockValue = FADoorCodes.SB_DISGUISE_INCOMPLETE, swing = 3):
        self.notify.debugStateCall(self)
        DistributedCogHQDoorAI.DistributedCogHQDoorAI.__init__(self, air, blockNumber, doorType, destinationZone, doorIndex, lockValue, swing)

    def requestEnter(self):
        avatarID = self.air.getAvatarIdFromSender()
        (allowed, suitType) = self.__getAccessLevel(avatarID)
        if not allowed:
            self.sendReject(avatarID, self.isLockedDoor())
        else:
            self.enqueueAvatarIdEnter(avatarID)
            self.sendUpdateToAvatarId(avatarID, 'setOtherZoneIdAndDoId', [
                self.destinationZone,
                self.otherDoor.getDoId()])
            if ToontownGlobals.SELLBOT_NERF_HOLIDAY in self.air.holidayManager.currentHolidays:
                self.sendUpdateToAvatarId(avatarID, 'informPlayer', [
                    suitType])

    def __getAccessLevel(self, avatarID):
        av = self.air.doId2do.get(avatarID)
        allowed = 0
        suitType = -1
        if av:
            if self.doorType == DoorTypes.EXT_COGHQ and self.isLockedDoor():
                parts = av.getCogParts()
                dept = ToontownGlobals.cogHQZoneId2deptIndex(self.destinationZone)
                if CogDisguiseGlobals.isPaidSuitComplete(av, parts, dept):
                    if av.getCogMerits()[dept] >= CogDisguiseGlobals.getTotalMerits(av, dept):
                        suitType = CogDisguiseGlobals.suitTypes.FullSuit
                    else:
                        suitType = CogDisguiseGlobals.suitTypes.NoMerits
                    allowed = 1
                else:
                    suitType = CogDisguiseGlobals.suitTypes.NoSuit
                if ToontownGlobals.SELLBOT_NERF_HOLIDAY in self.air.holidayManager.currentHolidays:
                    allowed = 1

            else:
                allowed = 1

        if not ToontownAccessAI.canAccess(avatarID, self.zoneId, 'DistributedSellbotHQDoorAI.__getAccessLevel'):
            allowed = 0

        return (allowed, suitType)
