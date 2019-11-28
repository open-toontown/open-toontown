from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI


class ObjectServerAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('ObjectServerAI')
