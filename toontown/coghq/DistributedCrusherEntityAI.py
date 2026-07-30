from otp.level import DistributedEntityAI
from direct.directnotify import DirectNotifyGlobal

class DistributedCrusherEntityAI(DistributedEntityAI.DistributedEntityAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedCrusherEntityAI')

    def __init__(self, level, entId):
        self.isCrusher = 0
        self.crushCell = None
        DistributedEntityAI.DistributedEntityAI.__init__(self, level, entId)
        self.crushMsg = self.getUniqueName('crusherDoCrush')
        return

    def generate(self):
        DistributedEntityAI.DistributedEntityAI.generate(self)
        self.setActiveCrushCell()

    def delete(self):
        self.ignoreAll()
        DistributedEntityAI.DistributedEntityAI.delete(self)

    def destroy(self):
        self.notify.info('destroy entity %s' % self.entId)
        if self.crushCell != None:
            self.crushCell.unregisterCrusher(self.entId)
            self.crushCell = None
        DistributedEntityAI.DistributedEntityAI.destroy(self)
        return

    def setActiveCrushCell(self):
        self.notify.debug('setActiveCrushCell, entId: %d' % self.entId)
        if self.crushCellId != None:
            self.crushCell = self.level.entities.get(self.crushCellId, None)
            if self.crushCell == None:
                self.accept(self.level.getEntityCreateEvent(self.crushCellId), self.setActiveCrushCell)
            else:
                self.isCrusher = 1
                self.crushCell.registerCrusher(self.entId)
        return

    def sendCrushMsg(self, axis=0):
        if self.isCrusher:
            messenger.send(self.crushMsg, [self.entId, axis])

    def getPosition(self):
        if hasattr(self, 'pos'):
            return self.pos
