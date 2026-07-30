from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectUD import DistributedObjectUD

class TTCodeRedemptionMgrUD(DistributedObjectUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('TTCodeRedemptionMgrUD')
