from direct.distributed import DistributedObjectAI
from otp.level import DistributedLevelAI
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from toontown.coghq import StageLayout, DistributedStageRoomAI
from toontown.coghq import BattleExperienceAggregatorAI
from toontown.building import DistributedElevatorFloorAI
from pandac.PandaModules import *

class DistributedStageAI(DistributedObjectAI.DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedStageAI')

    def __init__(self, air, stageId, zoneId, floorNum, avIds, layoutIndex, battleExpAggreg=None):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.stageId = stageId
        self.zoneId = zoneId
        self.floorNum = floorNum
        self.avIds = avIds
        self.elevatorList = []
        self.setLayoutIndex(layoutIndex)
        self.battleExpAggreg = battleExpAggreg
        self.puzzelReward = 5

    def generate(self):
        DistributedObjectAI.DistributedObjectAI.generate(self)
        self.notify.info('generate %s, id=%s, floor=%s' % (self.doId, self.stageId, self.floorNum))
        self.layout = StageLayout.StageLayout(self.stageId, self.floorNum, self.layoutIndex)
        self.rooms = []
        if self.battleExpAggreg is None:
            self.battleExpAggreg = BattleExperienceAggregatorAI.BattleExperienceAggregatorAI()
        for i in range(self.layout.getNumRooms()):
            room = DistributedStageRoomAI.DistributedStageRoomAI(self.air, self.stageId, self.doId, self.zoneId, self.layout.getRoomId(i), i * 2, self.avIds, self.battleExpAggreg)
            room.generateWithRequired(self.zoneId)
            self.rooms.append(room)

        roomDoIds = []
        for room in self.rooms:
            roomDoIds.append(room.doId)

        self.sendUpdate('setRoomDoIds', [roomDoIds])
        self.placeElevatorsOnMarkers()
        if __dev__:
            simbase.stage = self
        description = '%s|%s|%s' % (self.stageId, self.floorNum, self.avIds)
        for avId in self.avIds:
            self.air.writeServerEvent('stageEntered', avId, description)

        return

    def requestDelete(self):
        self.notify.info('requestDelete: %s' % self.doId)
        if hasattr(self, 'rooms'):
            for room in self.rooms:
                room.requestDelete()

        if hasattr(self, 'elevatorList'):
            for elevator in self.elevatorList:
                elevator.requestDelete()

        DistributedObjectAI.DistributedObjectAI.requestDelete(self)

    def delete(self):
        self.notify.info('delete: %s' % self.doId)
        if __dev__:
            if hasattr(simbase, 'stage') and simbase.stage is self:
                del simbase.stage
        self.air.deallocateZone(self.zoneId)
        if hasattr(self, 'elevatorList'):
            del self.elevatorList
        if hasattr(self, 'rooms'):
            del self.rooms
        if hasattr(self, 'layout'):
            del self.layout
        if hasattr(self, 'battleExpAggreg'):
            del self.battleExpAggreg
        DistributedObjectAI.DistributedObjectAI.delete(self)

    def getTaskZoneId(self):
        return self.stageId

    def placeElevatorsOnMarkers(self):
        for room in self.rooms:
            if room.entType2ids['elevatorMarker']:
                for markerId in room.entType2ids['elevatorMarker']:
                    marker = room.getEntity(markerId)
                    newElevator = DistributedElevatorFloorAI.DistributedElevatorFloorAI(self.air, self.doId, self, self.avIds, marker.doId)
                    newElevator.generateWithRequired(self.zoneId)
                    self.elevatorList.append(newElevator)

    def allToonsGone(self):
        self.notify.info('allToonsGone')
        self.requestDelete()

    def getZoneId(self):
        return self.zoneId

    def getStageId(self):
        return self.stageId

    def getFloorNum(self):
        return self.floorNum

    def setLayoutIndex(self, layoutIndex):
        self.layoutIndex = layoutIndex

    def getLayoutIndex(self):
        return self.layoutIndex

    def startNextFloor(self):
        floor = self.floorNum + 1
        StageZone = self.air.allocateZone()
        Stage = DistributedStageAI(self.air, self.stageId, StageZone, floor, self.avIds, self.layoutIndex, self.battleExpAggreg)
        Stage.generateWithRequired(StageZone)
        for avId in self.avIds:
            self.sendUpdateToAvatarId(avId, 'setStageZone', [StageZone])

        self.requestDelete()

    def elevatorAlert(self, avId):
        self.sendUpdate('elevatorAlert', [avId])

    def increasePuzzelReward(self):
        self.puzzelReward += 5
        if self.puzzelReward > 10:
            self.puzzelReward = 10

    def resetPuzzelReward(self):
        self.puzzelReward = 5

    def getPuzzelReward(self):
        return self.puzzelReward
