from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI


class AstronAccountAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('AstronAccountAI')
