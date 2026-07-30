from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectUD import DistributedObjectUD

class SnapshotRendererUD(DistributedObjectUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('SnapshotRendererUD')
