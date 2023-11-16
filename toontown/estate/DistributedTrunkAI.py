from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI


class DistributedTrunkAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedTrunkAI')
