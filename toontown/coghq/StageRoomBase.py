from toontown.toonbase import ToontownGlobals

class StageRoomBase:

    def __init__(self):
        pass

    def setStageId(self, stageId):
        self.stageId = stageId
        self.cogTrack = ToontownGlobals.cogHQZoneId2dept(stageId)

    def setRoomId(self, roomId):
        self.roomId = roomId

    def getCogTrack(self):
        return self.cogTrack

    if __dev__:

        def getEntityTypeReg(self):
            from . import FactoryEntityTypes
            from otp.level import EntityTypeRegistry
            typeReg = EntityTypeRegistry.EntityTypeRegistry(FactoryEntityTypes)
            return typeReg
