from otp.ai.AIBase import *
from toontown.toonbase import ToontownGlobals
from direct.distributed.ClockDelta import *
from .ElevatorConstants import *
from . import DistributedElevatorAI, DistributedElevatorExtAI
from direct.fsm import ClassicFSM
from direct.fsm import State
from direct.task import Task
from direct.directnotify import DirectNotifyGlobal
from toontown.suit import DistributedSellbotBossAI

class DistributedBossElevatorAI(DistributedElevatorExtAI.DistributedElevatorExtAI):

    def __init__(self, air, bldg, zone, antiShuffle=0, minLaff=0):
        DistributedElevatorExtAI.DistributedElevatorExtAI.__init__(self, air, bldg, numSeats=8, antiShuffle=antiShuffle, minLaff=minLaff)
        self.zone = zone
        self.type = ELEVATOR_VP
        self.countdownTime = ElevatorData[self.type]['countdown']

    def elevatorClosed(self):
        numPlayers = self.countFullSeats()
        if numPlayers > 0:
            bossZone = self.bldg.createBossOffice(self.seats)
            for seatIndex in range(len(self.seats)):
                avId = self.seats[seatIndex]
                if avId:
                    self.sendUpdateToAvatarId(avId, 'setBossOfficeZone', [
                     bossZone])
                    self.clearFullNow(seatIndex)

        else:
            self.notify.warning('The elevator left, but was empty.')
        self.fsm.request('closed')

    def sendAvatarsToDestination(self, avIdList):
        if len(avIdList) > 0:
            bossZone = self.bldg.createBossOffice(avIdList)
            for avId in avIdList:
                if avId:
                    self.sendUpdateToAvatarId(avId, 'setBossOfficeZoneForce', [
                     bossZone])

    def enterClosing(self):
        DistributedElevatorAI.DistributedElevatorAI.enterClosing(self)
        taskMgr.doMethodLater(ElevatorData[self.type]['closeTime'], self.elevatorClosedTask, self.uniqueName('closing-timer'))

    def enterClosed(self):
        DistributedElevatorExtAI.DistributedElevatorExtAI.enterClosed(self)
        self.fsm.request('opening')

    def enterOpening(self):
        DistributedElevatorAI.DistributedElevatorAI.enterOpening(self)
        taskMgr.doMethodLater(ElevatorData[self.type]['openTime'], self.waitEmptyTask, self.uniqueName('opening-timer'))

    def checkBoard(self, av):
        dept = ToontownGlobals.cogHQZoneId2deptIndex(self.zone)
        if av.hp < self.minLaff:
            return REJECT_MINLAFF
        if not av.readyForPromotion(dept):
            return REJECT_PROMOTION
        return 0

    def requestBoard(self, *args):
        self.notify.debug('requestBoard')
        avId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(avId)
        if av:
            boardResponse = self.checkBoard(av)
            newArgs = (avId,) + args + (boardResponse,)
            if boardResponse == 0:
                self.acceptingBoardersHandler(*newArgs)
            else:
                self.rejectingBoardersHandler(*newArgs)
        else:
            self.notify.warning('avid: %s does not exist, but tried to board an elevator' % avId)
