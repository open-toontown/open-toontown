from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI

class DistributedWinterCarolingTargetAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedWinterCarolingTargetAI')
