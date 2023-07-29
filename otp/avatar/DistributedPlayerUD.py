from otp.avatar.DistributedAvatarUD import DistributedAvatarUD
from direct.directnotify.DirectNotifyGlobal import directNotify

class DistributedPlayerUD(DistributedAvatarUD):
    notify = directNotify.newCategory('DistributedPlayerUD')