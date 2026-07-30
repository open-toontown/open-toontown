from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI

class DistributedJailbirdDaleAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedJailbirdDaleAI')
