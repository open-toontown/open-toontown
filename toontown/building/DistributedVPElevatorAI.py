from .ElevatorConstants import *
from . import DistributedBossElevatorAI
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals

class DistributedVPElevatorAI(DistributedBossElevatorAI.DistributedBossElevatorAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedVPElevatorAI')

    def __init__(self, air, bldg, zone, antiShuffle=0, minLaff=0):
        DistributedBossElevatorAI.DistributedBossElevatorAI.__init__(self, air, bldg, zone, antiShuffle=antiShuffle, minLaff=minLaff)
        self.type = ELEVATOR_VP
        self.countdownTime = ElevatorData[self.type]['countdown']

    def checkBoard(self, av):
        dept = ToontownGlobals.cogHQZoneId2deptIndex(self.zone)
        boardingResult = 0
        if av.hp < self.minLaff:
            boardingResult = REJECT_MINLAFF
        if not av.readyForPromotion(dept):
            boardingResult = REJECT_PROMOTION
        if ToontownGlobals.SELLBOT_NERF_HOLIDAY in self.air.holidayManager.currentHolidays:
            boardingResult = 0
        return boardingResult
