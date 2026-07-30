from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI


class CatalogManagerAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('CatalogManagerAI')

    def startCatalog(self):
        pass

    def deliverCatalogFor(self, _):
        pass
