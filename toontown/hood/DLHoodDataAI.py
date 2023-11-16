from direct.directnotify import DirectNotifyGlobal

from toontown.classicchars import DistributedDonaldAI
from toontown.safezone import ButterflyGlobals, DistributedTrolleyAI, DLTreasurePlannerAI
from toontown.toonbase import ToontownGlobals

from . import HoodDataAI


class DLHoodDataAI(HoodDataAI.HoodDataAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DLHoodDataAI')

    def __init__(self, air, zoneId=None):
        hoodId = ToontownGlobals.DonaldsDreamland
        if zoneId == None:
            zoneId = hoodId
        HoodDataAI.HoodDataAI.__init__(self, air, zoneId, hoodId)
        return

    def startup(self):
        HoodDataAI.HoodDataAI.startup(self)
        trolley = DistributedTrolleyAI.DistributedTrolleyAI(self.air)
        trolley.generateWithRequired(self.zoneId)
        trolley.start()
        self.addDistObj(trolley)
        self.treasurePlanner = DLTreasurePlannerAI.DLTreasurePlannerAI(self.zoneId)
        self.treasurePlanner.start()
        self.classicChar = DistributedDonaldAI.DistributedDonaldAI(self.air)
        self.classicChar.generateWithRequired(self.zoneId)
        self.classicChar.start()
        self.addDistObj(self.classicChar)
