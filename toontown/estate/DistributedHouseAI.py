from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI

class DistributedHouseAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedHouseAI')
