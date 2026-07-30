from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectUD import DistributedObjectUD

class AvatarFriendsManagerUD(DistributedObjectUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('AvatarFriendsManagerUD')
