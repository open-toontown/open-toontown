from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI

class TTCodeRedemptionMgrAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('TTCodeRedemptionMgrAI')
