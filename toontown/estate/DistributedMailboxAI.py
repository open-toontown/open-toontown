from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI

class DistributedMailboxAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedMailboxAI')
