from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI

class DistributedToonStatuaryAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedToonStatuaryAI')
