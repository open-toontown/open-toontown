from . import DistributedBossElevatorAI
from .ElevatorConstants import *


class DistributedCJElevatorAI(DistributedBossElevatorAI.DistributedBossElevatorAI):

    def __init__(self, air, bldg, zone, antiShuffle=0, minLaff=0):
        DistributedBossElevatorAI.DistributedBossElevatorAI.__init__(self, air, bldg, zone, antiShuffle=antiShuffle, minLaff=0)
        self.type = ELEVATOR_CJ
        self.countdownTime = ElevatorData[self.type]['countdown']
