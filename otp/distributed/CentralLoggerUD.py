from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectUD import DistributedObjectUD


class CentralLoggerUD(DistributedObjectUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('CentralLoggerUD')
