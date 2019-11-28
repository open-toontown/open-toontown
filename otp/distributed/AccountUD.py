from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectUD import DistributedObjectUD


class AccountUD(DistributedObjectUD):
    notify = DirectNotifyGlobal.directNotify.newCategory('AccountUD')
