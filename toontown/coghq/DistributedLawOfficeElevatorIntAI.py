from otp.ai.AIBase import *
from toontown.toonbase import ToontownGlobals
from direct.distributed.ClockDelta import *
from toontown.building.ElevatorConstants import *
from toontown.building import DistributedElevatorFloorAI
from toontown.building import DistributedElevatorAI
from direct.fsm import ClassicFSM
from direct.fsm import State
from direct.task import Task

class DistributedLawOfficeElevatorIntAI(DistributedElevatorFloorAI.DistributedElevatorFloorAI):

    def __init__(self, air, lawOfficeId, bldg, avIds):
        DistributedElevatorFloorAI.DistributedElevatorFloorAI.__init__(self, air, bldg, avIds)
        self.lawOfficeId = lawOfficeId

    def getEntranceId(self):
        return self.entranceId

    def elevatorClosed(self):
        numPlayers = self.countFullSeats()
        if numPlayers > 0:
            players = []
            for i in self.seats:
                if i not in [None, 0]:
                    players.append(i)

            sittingAvIds = []
            for seatIndex in range(len(self.seats)):
                avId = self.seats[seatIndex]
                if avId:
                    sittingAvIds.append(avId)

            for avId in self.avIds:
                if avId not in sittingAvIds:
                    print('THIS AV ID %s IS NOT ON BOARD' % avId)

            self.bldg.startNextFloor()
        else:
            self.notify.warning('The elevator left, but was empty.')
        self.fsm.request('closed')
        return

    def enterClosed(self):
        print('DistributedLawOfficeElevatorIntAI.elevatorClosed %s' % self.doId)
        DistributedElevatorFloorAI.DistributedElevatorFloorAI.enterClosed(self)
        if not self.hasOpenedLocked or not self.isLocked:
            self.fsm.request('opening')
            if self.isLocked:
                self.hasOpenedLocked = 1
