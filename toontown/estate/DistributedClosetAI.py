from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI


class DistributedClosetAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedClosetAI')
