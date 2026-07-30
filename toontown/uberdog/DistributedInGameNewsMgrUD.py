from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectUD import DistributedObjectUD

class DistributedInGameNewsMgrUD(DistributedObjectUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedInGameNewsMgrUD')
