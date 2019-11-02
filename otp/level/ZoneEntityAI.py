import ZoneEntityBase

class ZoneEntityAI(ZoneEntityBase.ZoneEntityBase):

    def __init__(self, level, entId):
        ZoneEntityBase.ZoneEntityBase.__init__(self, level, entId)
        self.setZoneId(self.level.air.allocateZone())

    def destroy(self):
        if not self.isUberZone():
            self.level.air.deallocateZone(self.getZoneId())
        ZoneEntityBase.ZoneEntityBase.destroy(self)
