from . import DistributedElevator
from . import DistributedBossElevator
from .ElevatorConstants import *
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import TTLocalizer

class DistributedCJElevator(DistributedBossElevator.DistributedBossElevator):

    def __init__(self, cr):
        DistributedBossElevator.DistributedBossElevator.__init__(self, cr)
        self.type = ELEVATOR_CJ
        self.countdownTime = ElevatorData[self.type]['countdown']

    def setupElevator(self):
        self.elevatorModel = loader.loadModel('phase_11/models/lawbotHQ/LB_Elevator')
        self.leftDoor = self.elevatorModel.find('**/left-door')
        if self.leftDoor.isEmpty():
            self.leftDoor = self.elevatorModel.find('**/left_door')
        self.rightDoor = self.elevatorModel.find('**/right-door')
        if self.rightDoor.isEmpty():
            self.rightDoor = self.elevatorModel.find('**/right_door')
        geom = base.cr.playGame.hood.loader.geom
        locator = geom.find('**/elevator_locator')
        self.elevatorModel.reparentTo(locator)
        DistributedElevator.DistributedElevator.setupElevator(self)

    def getDestName(self):
        return TTLocalizer.ElevatorLawBotBoss
