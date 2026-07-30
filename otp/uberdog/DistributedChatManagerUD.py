from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectUD import DistributedObjectUD

class DistributedChatManagerUD(DistributedObjectUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedChatManagerUD')
