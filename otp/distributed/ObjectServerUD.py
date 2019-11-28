from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectUD import DistributedObjectUD


class ObjectServerUD(DistributedObjectUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('ObjectServerUD')
