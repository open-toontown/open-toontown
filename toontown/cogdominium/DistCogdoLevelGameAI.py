from direct.directnotify.DirectNotifyGlobal import directNotify
from otp.level.DistributedLevelAI import DistributedLevelAI
from toontown.cogdominium.DistCogdoGameAI import DistCogdoGameAI
from toontown.cogdominium.CogdoEntityCreatorAI import CogdoEntityCreatorAI
from toontown.cogdominium.CogdoLevelGameBase import CogdoLevelGameBase

class DistCogdoLevelGameAI(CogdoLevelGameBase, DistCogdoGameAI, DistributedLevelAI):
    notify = directNotify.newCategory('DistCogdoLevelGameAI')

    def __init__(self, air, interior):
        DistCogdoGameAI.__init__(self, air, interior)
        DistributedLevelAI.__init__(self, air, self.zoneId, 0, self.getToonIds())

    def generate(self):
        self.notify.info('loading spec')
        spec = self.getLevelSpec()
        if __dev__:
            self.notify.info('creating entity type registry')
            typeReg = self.getEntityTypeReg()
            spec.setEntityTypeReg(typeReg)

        DistributedLevelAI.generate(self, spec)
        DistCogdoGameAI.generate(self)
        if __dev__:
            self.startHandleEdits()

    def createEntityCreator(self):
        return CogdoEntityCreatorAI(level = self)

    def _levelControlsRequestDelete(self):
        return False

    def requestDelete(self):
        DistCogdoGameAI.requestDelete(self)

    def delete(self):
        if __dev__:
            self.stopHandleEdits()

        DistCogdoGameAI.delete(self)
        DistributedLevelAI.delete(self, deAllocZone = False)
