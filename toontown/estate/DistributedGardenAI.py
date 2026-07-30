from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI

class DistributedGardenAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedGardenAI')
