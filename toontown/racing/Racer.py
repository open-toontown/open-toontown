class Racer:

    def __init__(self, race, air, avId, zoneId):
        self.race = race
        self.air = air
        self.avId = avId
        self.zoneId = zoneId
        self.avatar = self.air.doId2do.get(self.avId)
        self.avatar.takeOutKart(self.zoneId)
        self.kart = self.avatar.kart
        self.finished = False
        self.exitEvent = self.air.getAvatarExitEvent(self.avId)
