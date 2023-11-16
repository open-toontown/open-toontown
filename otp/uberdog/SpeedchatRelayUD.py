from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectUD import DistributedObjectUD


class SpeedchatRelayUD(DistributedObjectUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('SpeedchatRelayUD')
