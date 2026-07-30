from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectUD import DistributedObjectUD

class TTPlayerFriendsManagerUD(DistributedObjectUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('TTPlayerFriendsManagerUD')
