from otp.ai.AIBase import *
from toontown.toonbase import ToontownGlobals
from direct.distributed.ClockDelta import *
from toontown.building.ElevatorConstants import *
from toontown.building import DistributedElevatorExtAI
from direct.fsm import ClassicFSM
from direct.fsm import State
from direct.task import Task
from . import CogDisguiseGlobals

class DistributedMintElevatorExtAI(DistributedElevatorExtAI.DistributedElevatorExtAI):

    def __init__(self, air, bldg, mintId, antiShuffle=0, minLaff=0):
        DistributedElevatorExtAI.DistributedElevatorExtAI.__init__(self, air, bldg, antiShuffle=antiShuffle, minLaff=minLaff)
        self.mintId = mintId
        self.cogDept = ToontownGlobals.cogHQZoneId2deptIndex(self.mintId)
        self.type = ELEVATOR_MINT
        self.countdownTime = ElevatorData[self.type]['countdown']

    def getMintId(self):
        return self.mintId

    def avIsOKToBoard(self, av):
        if not DistributedElevatorExtAI.DistributedElevatorExtAI.avIsOKToBoard(self, av):
            return False
        return True

    def elevatorClosed(self):
        numPlayers = self.countFullSeats()
        if numPlayers > 0:
            players = []
            for i in self.seats:
                if i not in [None, 0]:
                    players.append(i)

            mintZone = self.bldg.createMint(self.mintId, players)
            for seatIndex in range(len(self.seats)):
                avId = self.seats[seatIndex]
                if avId:
                    self.sendUpdateToAvatarId(avId, 'setMintInteriorZone', [
                     mintZone])
                    self.clearFullNow(seatIndex)

        else:
            self.notify.warning('The elevator left, but was empty.')
        self.fsm.request('closed')
        return

    def enterClosed(self):
        DistributedElevatorExtAI.DistributedElevatorExtAI.enterClosed(self)
        self.fsm.request('opening')

    def sendAvatarsToDestination(self, avIdList):
        if len(avIdList) > 0:
            mintZone = self.bldg.createMint(self.mintId, avIdList)
            for avId in avIdList:
                if avId:
                    self.sendUpdateToAvatarId(avId, 'setMintInteriorZoneForce', [
                     mintZone])
