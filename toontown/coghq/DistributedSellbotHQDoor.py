from direct.directnotify import DirectNotifyGlobal
from toontown.coghq import DistributedCogHQDoor
from toontown.toonbase import TTLocalizer
from . import CogDisguiseGlobals

class DistributedSellbotHQDoor(DistributedCogHQDoor.DistributedCogHQDoor):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedSellbotHQDoor')

    def __init__(self, cr):
        DistributedCogHQDoor.DistributedCogHQDoor.__init__(self, cr)

    def informPlayer(self, suitType):
        self.notify.debugStateCall(self)
        if suitType == CogDisguiseGlobals.suitTypes.NoSuit:
            popupMsg = TTLocalizer.SellbotRentalSuitMessage
        elif suitType == CogDisguiseGlobals.suitTypes.NoMerits:
            popupMsg = TTLocalizer.SellbotCogSuitNoMeritsMessage
        elif suitType == CogDisguiseGlobals.suitTypes.FullSuit:
            popupMsg = TTLocalizer.SellbotCogSuitHasMeritsMessage
        else:
            popupMsg = TTLocalizer.FADoorCodes_SB_DISGUISE_INCOMPLETE
        localAvatar.elevatorNotifier.showMeWithoutStopping(popupMsg, pos=(0, 0, 0.26), ttDialog=True)
        localAvatar.elevatorNotifier.setOkButton()
        localAvatar.elevatorNotifier.doneButton.setZ(-0.3)
