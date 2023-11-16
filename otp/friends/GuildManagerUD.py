from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectUD import DistributedObjectUD


class GuildManagerUD(DistributedObjectUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('GuildManagerUD')
