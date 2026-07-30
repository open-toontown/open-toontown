from toontown.toonbase import ToontownGlobals


class CountryClubRoomBase:

    def __init__(self):
        pass

    def setCountryClubId(self, countryClubId):
        self.countryClubId = countryClubId
        self.cogTrack = ToontownGlobals.cogHQZoneId2dept(countryClubId)

    def setRoomId(self, roomId):
        self.roomId = roomId

    def getCogTrack(self):
        return self.cogTrack

    if __dev__:

        def getCountryClubEntityTypeReg(self):
            from otp.level import EntityTypeRegistry

            from . import FactoryEntityTypes
            typeReg = EntityTypeRegistry.EntityTypeRegistry(FactoryEntityTypes)
            return typeReg
