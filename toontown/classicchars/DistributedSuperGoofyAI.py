from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI

class DistributedSuperGoofyAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedSuperGoofyAI')
