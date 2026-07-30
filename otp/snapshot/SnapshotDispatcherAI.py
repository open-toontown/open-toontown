from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI

class SnapshotDispatcherAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('SnapshotDispatcherAI')
