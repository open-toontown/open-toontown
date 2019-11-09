from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI

class DistributedProjectileAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedProjectileAI')
