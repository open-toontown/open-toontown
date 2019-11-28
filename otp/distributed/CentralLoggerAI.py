from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI


class CentralLoggerAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('CentralLoggerAI')
