from . import ActiveCellAI
from direct.directnotify import DirectNotifyGlobal

class CrusherCellAI(ActiveCellAI.ActiveCellAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('CrusherCellAI')

    def __init__(self, level, entId):
        ActiveCellAI.ActiveCellAI.__init__(self, level, entId)
        self.crushers = []
        self.crushables = []

    def destroy(self):
        self.notify.info('destroy entity %s' % self.entId)
        for entId in self.crushers:
            self.unregisterCrusher(entId)

        ActiveCellAI.ActiveCellAI.destroy(self)

    def registerCrusher(self, entId):
        if entId not in self.crushers:
            ent = self.level.entities.get(entId, None)
            if ent:
                self.crushers.append(entId)
                self.accept(ent.crushMsg, self.doCrush)
        return

    def unregisterCrusher(self, entId):
        if entId in self.crushers:
            self.crushers.remove(entId)
            if not hasattr(self, 'level'):
                self.notify.error("unregisterCrusher(%s): CrusherCellAI %s has no attrib 'level'" % (entId, self.entId))
            ent = self.level.entities.get(entId, None)
            if ent:
                self.ignore(ent.crushMsg)
        return

    def registerCrushable(self, entId):
        if entId not in self.crushables:
            self.crushables.append(entId)

    def unregisterCrushable(self, entId):
        if entId in self.crushables:
            self.crushables.remove(entId)

    def doCrush(self, crusherId, axis):
        self.notify.debug('doCrush %s' % crusherId)
        for occupantId in self.occupantIds:
            if occupantId in self.crushables:
                crushObj = self.level.entities.get(occupantId, None)
                if crushObj:
                    crushObj.doCrush(crusherId, axis)
                else:
                    self.notify.warning("couldn't find crushable object %d" % self.occupantId)

        return

    def updateCrushables(self):
        for id in self.crushables:
            crushable = self.level.entities.get(id, None)
            if crushable:
                crushable.updateGrid()

        return
