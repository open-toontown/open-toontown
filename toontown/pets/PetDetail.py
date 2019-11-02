from direct.directnotify import DirectNotifyGlobal
from otp.avatar import AvatarDetail
from toontown.pets import DistributedPet

class PetDetail(AvatarDetail.AvatarDetail):
    notify = DirectNotifyGlobal.directNotify.newCategory('PetDetail')

    def getDClass(self):
        return 'DistributedPet'

    def createHolder(self):
        pet = DistributedPet.DistributedPet(base.cr, bFake=True)
        pet.forceAllowDelayDelete()
        pet.generateInit()
        pet.generate()
        return pet
