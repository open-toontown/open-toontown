from .ElevatorConstants import *
from . import DistributedBossElevatorAI

class DistributedBBElevatorAI(DistributedBossElevatorAI.DistributedBossElevatorAI):

    def __init__(self, air, bldg, zone, antiShuffle=0, minLaff=0):
        DistributedBossElevatorAI.DistributedBossElevatorAI.__init__(self, air, bldg, zone, antiShuffle=antiShuffle, minLaff=0)
        self.type = ELEVATOR_BB
        self.countdownTime = ElevatorData[self.type]['countdown']

    def checkBoard(self, av):
        result = 0
        if simbase.config.GetBool('allow-ceo-elevator', 1):
            result = DistributedBossElevatorAI.DistributedBossElevatorAI.checkBoard(self, av)
        else:
            result = REJECT_NOT_YET_AVAILABLE
        return result
