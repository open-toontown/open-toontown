from direct.directnotify import DirectNotifyGlobal

from otp.level import BasicEntities


class DistributedCrusherEntity(BasicEntities.DistributedNodePathEntity):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedCrusherEntity')

    def __init__(self, cr):
        BasicEntities.DistributedNodePathEntity.__init__(self, cr)

    def announceGenerate(self):
        BasicEntities.DistributedNodePathEntity.announceGenerate(self)
        self.crushMsg = self.getUniqueName('crushMsg')
