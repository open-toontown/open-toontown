from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectUD import DistributedObjectUD

class DistributedToonUD(DistributedObjectUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedToonUD')
