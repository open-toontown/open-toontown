from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectUD import DistributedObjectUD


class DistributedAvatarUD(DistributedObjectUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedAvatarUD')
