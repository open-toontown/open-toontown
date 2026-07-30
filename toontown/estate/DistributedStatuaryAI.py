from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI

class DistributedStatuaryAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedStatuaryAI')
