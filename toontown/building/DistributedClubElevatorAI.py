from otp.ai.AIBase import *
from toontown.toonbase import ToontownGlobals
from direct.distributed.ClockDelta import *
from toontown.building import ElevatorConstants
from toontown.building import DistributedElevatorFSMAI
from direct.task import Task
from direct.directnotify import DirectNotifyGlobal
from direct.fsm.FSM import FSM

class DistributedClubElevatorAI(DistributedElevatorFSMAI.DistributedElevatorFSMAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedElevatorFloorAI')
    defaultTransitions = {'Off': ['Opening', 'Closed'], 'Opening': ['WaitEmpty', 'WaitCountdown', 'Opening', 'Closing'], 'WaitEmpty': ['WaitCountdown', 'Closing', 'WaitEmpty'], 'WaitCountdown': ['WaitEmpty', 'AllAboard', 'Closing', 'WaitCountdown'], 'AllAboard': ['WaitEmpty', 'Closing'], 'Closing': ['Closed', 'WaitEmpty', 'Closing', 'Opening'], 'Closed': ['Opening']}
    id = 0
    DoBlockedRoomCheck = simbase.config.GetBool('elevator-blocked-rooms-check', 1)

    def __init__(self, air, lawOfficeId, bldg, avIds, markerId=None, numSeats=4, antiShuffle=0, minLaff=0):
        DistributedElevatorFSMAI.DistributedElevatorFSMAI.__init__(self, air, bldg, numSeats, antiShuffle=antiShuffle, minLaff=minLaff)
        FSM.__init__(self, 'ElevatorFloor_%s_FSM' % self.id)
        self.type = ElevatorConstants.ELEVATOR_COUNTRY_CLUB
        self.countdownTime = ElevatorConstants.ElevatorData[self.type]['countdown']
        self.lawOfficeId = lawOfficeId
        self.anyToonsBailed = 0
        self.avIds = avIds
        self.isEntering = 0
        self.isLocked = 0
        self.setLocked(0)
        self.wantState = None
        self.latchRoom = None
        self.setLatch(markerId)
        self.zoneId = bldg.zoneId
        return

    def generate(self):
        DistributedElevatorFSMAI.DistributedElevatorFSMAI.generate(self)

    def generateWithRequired(self, zoneId):
        self.zoneId = zoneId
        DistributedElevatorFSMAI.DistributedElevatorFSMAI.generateWithRequired(self, self.zoneId)

    def delete(self):
        for seatIndex in range(len(self.seats)):
            avId = self.seats[seatIndex]
            if avId:
                self.clearFullNow(seatIndex)
                self.clearEmptyNow(seatIndex)

        DistributedElevatorFSMAI.DistributedElevatorFSMAI.delete(self)

    def getEntranceId(self):
        return self.entranceId

    def d_setFloor(self, floorNumber):
        self.sendUpdate('setFloor', [floorNumber])

    def avIsOKToBoard(self, av):
        return av.hp > 0 and self.accepting and not self.isLocked

    def acceptBoarder(self, avId, seatIndex):
        DistributedElevatorFSMAI.DistributedElevatorFSMAI.acceptBoarder(self, avId, seatIndex)
        self.acceptOnce(self.air.getAvatarExitEvent(avId), self.__handleUnexpectedExit, extraArgs=[avId])
        if self.state == 'WaitEmpty' and self.countFullSeats() < self.countAvsInZone():
            self.request('WaitCountdown')
            self.bldg.elevatorAlert(avId)
        elif self.state in ('WaitCountdown', 'WaitEmpty') and self.countFullSeats() >= self.countAvsInZone():
            taskMgr.doMethodLater(ElevatorConstants.TOON_BOARD_ELEVATOR_TIME, self.goAllAboard, self.quickBoardTask)

    def countAvsInZone(self):
        matchingZones = 0
        for avId in self.bldg.avIds:
            av = self.air.doId2do.get(avId)
            if av:
                if av.zoneId == self.bldg.zoneId:
                    matchingZones += 1

        return matchingZones

    def goAllAboard(self, throwAway=1):
        self.request('Closing')
        return Task.done

    def __handleUnexpectedExit(self, avId):
        self.notify.warning('Avatar: ' + str(avId) + ' has exited unexpectedly')
        seatIndex = self.findAvatar(avId)
        if seatIndex == None:
            pass
        else:
            self.clearFullNow(seatIndex)
            self.clearEmptyNow(seatIndex)
            if self.countFullSeats() == 0:
                self.request('WaitEmpty')
        return

    def acceptExiter(self, avId):
        seatIndex = self.findAvatar(avId)
        if seatIndex == None:
            pass
        else:
            self.clearFullNow(seatIndex)
            bailFlag = 0
            if self.anyToonsBailed == 0:
                bailFlag = 1
                self.resetCountdown()
                self.anyToonsBailed = 1
            self.sendUpdate('emptySlot' + str(seatIndex), [
             avId, bailFlag, globalClockDelta.getRealNetworkTime()])
            if self.countFullSeats() == 0:
                self.request('WaitEmpty')
            taskMgr.doMethodLater(ElevatorConstants.TOON_EXIT_ELEVATOR_TIME, self.clearEmptyNow, self.uniqueName('clearEmpty-%s' % seatIndex), extraArgs=(seatIndex,))
        return

    def enterOpening(self):
        self.d_setState('Opening')
        DistributedElevatorFSMAI.DistributedElevatorFSMAI.enterOpening(self)
        taskMgr.doMethodLater(ElevatorConstants.ElevatorData[ElevatorConstants.ELEVATOR_NORMAL]['openTime'], self.waitEmptyTask, self.uniqueName('opening-timer'))

    def exitOpening(self):
        DistributedElevatorFSMAI.DistributedElevatorFSMAI.exitOpening(self)
        if self.isLocked:
            self.wantState = 'closed'
        if self.wantState == 'closed':
            self.demand('Closing')

    def waitEmptyTask(self, task):
        self.request('WaitEmpty')
        return Task.done

    def enterWaitEmpty(self):
        self.lastState = self.state
        for i in range(len(self.seats)):
            self.seats[i] = None

        print(self.seats)
        if self.wantState == 'closed':
            self.demand('Closing')
        else:
            self.d_setState('WaitEmpty')
            self.accepting = 1
        return

    def enterWaitCountdown(self):
        self.lastState = self.state
        DistributedElevatorFSMAI.DistributedElevatorFSMAI.enterWaitCountdown(self)
        taskMgr.doMethodLater(self.countdownTime, self.timeToGoTask, self.uniqueName('countdown-timer'))
        if self.lastState == 'WaitCountdown':
            pass

    def timeToGoTask(self, task):
        if self.countFullSeats() > 0:
            self.request('AllAboard')
        else:
            self.request('WaitEmpty')
        return Task.done

    def resetCountdown(self):
        taskMgr.remove(self.uniqueName('countdown-timer'))
        taskMgr.doMethodLater(self.countdownTime, self.timeToGoTask, self.uniqueName('countdown-timer'))

    def enterAllAboard(self):
        DistributedElevatorFSMAI.DistributedElevatorFSMAI.enterAllAboard(self)
        currentTime = globalClock.getRealTime()
        elapsedTime = currentTime - self.timeOfBoarding
        self.notify.debug('elapsed time: ' + str(elapsedTime))
        waitTime = max(ElevatorConstants.TOON_BOARD_ELEVATOR_TIME - elapsedTime, 0)
        taskMgr.doMethodLater(waitTime, self.closeTask, self.uniqueName('waitForAllAboard'))

    def closeTask(self, task):
        if self.countFullSeats() >= 1:
            self.request('Closing')
        else:
            self.request('WaitEmpty')
        return Task.done

    def enterClosing(self):
        if self.countFullSeats() > 0:
            self.sendUpdate('kickToonsOut')
        DistributedElevatorFSMAI.DistributedElevatorFSMAI.enterClosing(self)
        taskMgr.doMethodLater(ElevatorConstants.ElevatorData[ElevatorConstants.ELEVATOR_STAGE]['closeTime'], self.elevatorClosedTask, self.uniqueName('closing-timer'))
        self.d_setState('Closing')

    def elevatorClosedTask(self, task):
        self.elevatorClosed()
        return Task.done

    def elevatorClosed(self):
        if self.isLocked:
            self.request('Closed')
            return
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
                    pass

            self.bldg.startNextFloor()
        else:
            self.notify.warning('The elevator left, but was empty.')
        self.request('Closed')
        return

    def setLocked(self, locked):
        self.isLocked = locked
        if locked:
            if self.state == 'WaitEmpty':
                self.request('Closing')
            if self.countFullSeats() == 0:
                self.wantState = 'closed'
            else:
                self.wantState = 'opening'
        else:
            self.wantState = 'waitEmpty'
            if self.state == 'Closed':
                self.request('Opening')

    def getLocked(self):
        return self.isLocked

    def unlock(self):
        if self.isLocked:
            self.setLocked(0)

    def lock(self):
        if not self.isLocked:
            self.setLocked(1)

    def start(self):
        self.quickBoardTask = self.uniqueName('quickBoard')
        self.request('Opening')

    def beClosed(self):
        pass

    def setEntering(self, entering):
        self.isEntering = entering

    def getEntering(self):
        return self.isEntering

    def enterClosed(self):
        DistributedElevatorFSMAI.DistributedElevatorFSMAI.enterClosed(self)
        if self.wantState == 'closed':
            pass
        else:
            self.demand('Opening')

    def enterOff(self):
        self.lastState = self.state
        if self.wantState == 'closed':
            self.demand('Closing')
        else:
            if self.wantState == 'waitEmpty':
                self.demand('WaitEmpty')

    def setPos(self, pointPos):
        self.sendUpdate('setPos', [pointPos[0], pointPos[1], pointPos[2]])

    def setH(self, H):
        self.sendUpdate('setH', [H])

    def setLatch(self, markerId):
        self.latch = markerId

    def getLatch(self):
        return self.latch

    def checkBoard(self, av):
        if av.hp < self.minLaff:
            return ElevatorConstants.REJECT_MINLAFF
        if self.DoBlockedRoomCheck and self.bldg:
            if hasattr(self.bldg, 'blockedRooms'):
                if self.bldg.blockedRooms:
                    return ElevatorConstants.REJECT_BLOCKED_ROOM
        return 0
