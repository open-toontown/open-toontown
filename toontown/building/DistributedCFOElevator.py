from . import DistributedElevator
from . import DistributedBossElevator
from .ElevatorConstants import *
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import TTLocalizer

class DistributedCFOElevator(DistributedBossElevator.DistributedBossElevator):

    def __init__(self, cr):
        DistributedBossElevator.DistributedBossElevator.__init__(self, cr)
        self.type = ELEVATOR_CFO
        self.countdownTime = ElevatorData[self.type]['countdown']

    def setupElevator(self):
        self.elevatorModel = loader.loadModel('phase_10/models/cogHQ/CFOElevator')
        self.leftDoor = self.elevatorModel.find('**/left_door')
        self.rightDoor = self.elevatorModel.find('**/right_door')
        geom = base.cr.playGame.hood.loader.geom
        locator = geom.find('**/elevator_locator')
        self.elevatorModel.reparentTo(locator)
        DistributedElevator.DistributedElevator.setupElevator(self)

    def getDestName(self):
        return TTLocalizer.ElevatorCashBotBoss
