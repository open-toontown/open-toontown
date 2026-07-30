from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI

class DistributedChangingStatuaryAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedChangingStatuaryAI')
