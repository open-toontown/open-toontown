from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI

class DistributedGardenBoxAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedGardenBoxAI')
