from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI


class SnapshotRendererAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('SnapshotRendererAI')
