from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI

class GuildManagerAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('GuildManagerAI')
