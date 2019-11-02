import DistributedTreasureAI
from toontown.toonbase import ToontownGlobals

class DistributedSZTreasureAI(DistributedTreasureAI.DistributedTreasureAI):

    def __init__(self, air, treasurePlanner, x, y, z):
        DistributedTreasureAI.DistributedTreasureAI.__init__(self, air, treasurePlanner, x, y, z)
        self.healAmount = treasurePlanner.healAmount

    def validAvatar(self, av):
        return av.hp >= -1 and av.hp < av.maxHp

    def d_setGrab(self, avId):
        DistributedTreasureAI.DistributedTreasureAI.d_setGrab(self, avId)
        if self.air.doId2do.has_key(avId):
            av = self.air.doId2do[avId]
            if self.validAvatar(av):
                if av.hp == -1:
                    av.hp = 0
                if simbase.air.holidayManager.currentHolidays.has_key(ToontownGlobals.VALENTINES_DAY):
                    av.toonUp(self.healAmount * 2)
                else:
                    av.toonUp(self.healAmount)
