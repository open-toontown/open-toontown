from direct.directnotify.DirectNotifyGlobal import directNotify
from otp.avatar import AvatarDetail
from toontown.toon import DistributedToon

class ToonDetail(AvatarDetail.AvatarDetail):
    notify = directNotify.newCategory('ToonDetail')

    def getDClass(self):
        return 'DistributedToon'

    def createHolder(self):
        toon = DistributedToon.DistributedToon(base.cr, bFake=True)
        toon.forceAllowDelayDelete()
        return toon
