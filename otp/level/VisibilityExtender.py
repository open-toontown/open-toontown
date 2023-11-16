from . import Entity


class VisibilityExtender(Entity.Entity):

    def __init__(self, level, entId):
        Entity.Entity.__init__(self, level, entId)
        self.initVisExt()

    def initVisExt(self):
        self.extended = 0
        self.zoneEntId = self.getZoneEntId()
        self.eventName = None
        if self.event is not None:
            self.eventName = self.getOutputEventName(self.event)
            self.accept(self.eventName, self.handleEvent)
        return

    def destroyVisExt(self):
        if self.eventName is not None:
            self.ignore(self.eventName)
        if self.extended:
            self.retract()
        return

    def handleEvent(self, doExtend):
        if doExtend:
            if not self.extended:
                self.extend()
        elif self.extended:
            self.retract()

    def extend(self):
        zoneEnt = self.level.getEntity(self.getZoneEntId())
        zoneEnt.incrementRefCounts(self.newZones)
        self.extended = 1
        self.level.handleVisChange()

    def retract(self):
        zoneEnt = self.level.getEntity(self.getZoneEntId())
        zoneEnt.decrementRefCounts(self.newZones)
        self.extended = 0
        self.level.handleVisChange()

    def destroy(self):
        self.destroyVisExt()
        Entity.Entity.destroy(self)

    if __dev__:

        def setNewZones(self, newZones):
            extended = self.extended
            self.destroyVisExt()
            self.newZones = newZones
            self.initVisExt()
            if extended:
                self.extend()

        def attribChanged(self, *args):
            extended = self.extended
            self.destroyVisExt()
            self.initVisExt()
            if extended:
                self.extend()
