from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectUD import DistributedObjectUD


class TTSpeedchatRelayUD(DistributedObjectUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('TTSpeedchatRelayUD')
