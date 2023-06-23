from . import DistributedTreasureAI
from toontown.toonbase import ToontownGlobals

class DistributedSZTreasureAI(DistributedTreasureAI.DistributedTreasureAI):

    # Noah Hensley
    # This class is the parent for all other Distributed Treasure AI classes for playgrounds

    def __init__(self, air, treasurePlanner, x, y, z, isBoss = False):
        DistributedTreasureAI.DistributedTreasureAI.__init__(self, air, treasurePlanner, x, y, z)
        self.healAmount = treasurePlanner.healAmount

        # Noah Hensley
        self.isBoss = isBoss
        if not self.isBoss:
            self.hoodId = treasurePlanner.hoodId
        else:
            self.hoodId = None  # Just to ensure this class always has a hoodId member variable

    def validAvatar(self, av):
        return av.hp >= -1 and av.hp < av.maxHp

    def d_setGrab(self, avId):
        DistributedTreasureAI.DistributedTreasureAI.d_setGrab(self, avId)
        if avId in self.air.doId2do:
            av = self.air.doId2do[avId]
            if self.validAvatar(av):
                # Noah Hensley
                if not self.isBoss:
                    av.incrementHoodTreasuresObtained(self.hoodId)
                    av.incrementTreasuresObtained()
                if av.hp == -1:
                    av.hp = 0
                if ToontownGlobals.VALENTINES_DAY in simbase.air.holidayManager.currentHolidays:
                    av.toonUp(self.healAmount * 2)
                else:
                    av.toonUp(self.healAmount)

