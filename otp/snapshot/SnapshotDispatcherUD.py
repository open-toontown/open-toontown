from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectUD import DistributedObjectUD

class SnapshotDispatcherUD(DistributedObjectUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('SnapshotDispatcherUD')
