from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectUD import DistributedObjectUD


class StatusDatabaseUD(DistributedObjectUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('StatusDatabaseUD')
