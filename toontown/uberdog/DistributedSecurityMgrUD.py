from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectUD import DistributedObjectUD

class DistributedSecurityMgrUD(DistributedObjectUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedSecurityMgrUD')
