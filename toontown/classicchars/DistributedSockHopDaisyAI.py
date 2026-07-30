from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI

class DistributedSockHopDaisyAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedSockHopDaisyAI')
