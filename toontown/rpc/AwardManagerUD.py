from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectUD import DistributedObjectUD


class AwardManagerUD(DistributedObjectUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('AwardManagerUD')
