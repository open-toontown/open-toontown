from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectUD import DistributedObjectUD

class DistributedCpuInfoMgrUD(DistributedObjectUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedCpuInfoMgrUD')
