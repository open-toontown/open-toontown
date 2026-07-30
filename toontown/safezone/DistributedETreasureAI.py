from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI

class DistributedETreasureAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedETreasureAI')
