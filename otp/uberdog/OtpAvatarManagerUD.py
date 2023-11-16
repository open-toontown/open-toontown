from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectUD import DistributedObjectUD


class OtpAvatarManagerUD(DistributedObjectUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('OtpAvatarManagerUD')
