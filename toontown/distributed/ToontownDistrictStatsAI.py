from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI

class ToontownDistrictStatsAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownDistrictStatsAI')

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)
        self.toontownDistrictId = 0
        self.avatarCount = 0
        self.newAvatarCount = 0

    def settoontownDistrictId(self, toontownDistrictId):
        self.toontownDistrictId = toontownDistrictId

    def d_settoontownDistrictId(self, toontownDistrictId):
        self.sendUpdate('settoontownDistrictId', [toontownDistrictId])

    def b_settoontownDistrictId(self, toontownDistrictId):
        self.settoontownDistrictId(toontownDistrictId)
        self.d_settoontownDistrictId(toontownDistrictId)

    def gettoontownDistrictId(self):
        return self.toontownDistrictId

    def setAvatarCount(self, avatarCount):
        self.avatarCount = avatarCount

    def d_setAvatarCount(self, avatarCount):
        self.sendUpdate('setAvatarCount', [avatarCount])

    def b_setAvatarCount(self, avatarCount):
        self.setAvatarCount(avatarCount)
        self.d_setAvatarCount(avatarCount)

    def getAvatarCount(self):
        return self.avatarCount

    def setNewAvatarCount(self, newAvatarCount):
        self.newAvatarCount = newAvatarCount

    def d_setNewAvatarCount(self, newAvatarCount):
        self.sendUpdate('setNewAvatarCount', [newAvatarCount])

    def b_setNewAvatarCount(self, newAvatarCount):
        self.setNewAvatarCount(newAvatarCount)
        self.d_setNewAvatarCount(newAvatarCount)

    def getNewAvatarCount(self):
        return self.newAvatarCount
