from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI


class OtpAvatarManagerAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('OtpAvatarManagerAI')
