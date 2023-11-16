from direct.directnotify import DirectNotifyGlobal

from toontown.classicchars import DistributedPlutoAI
from toontown.safezone import BRTreasurePlannerAI, DistributedTrolleyAI
from toontown.toon import DistributedNPCFishermanAI
from toontown.toonbase import ToontownGlobals

from . import HoodDataAI


class BRHoodDataAI(HoodDataAI.HoodDataAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('BRHoodDataAI')

    def __init__(self, air, zoneId=None):
        hoodId = ToontownGlobals.TheBrrrgh
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
        self.treasurePlanner = BRTreasurePlannerAI.BRTreasurePlannerAI(self.zoneId)
        self.treasurePlanner.start()
        self.classicChar = DistributedPlutoAI.DistributedPlutoAI(self.air)
        self.classicChar.generateWithRequired(self.zoneId)
        self.classicChar.start()
        self.addDistObj(self.classicChar)
