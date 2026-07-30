from otp.ai.AIBase import *
from toontown.toonbase import ToontownGlobals
from direct.distributed.ClockDelta import *
from .ElevatorConstants import *
from . import DistributedElevatorAI
from direct.fsm import ClassicFSM
from direct.fsm import State
from direct.task import Task
from direct.directnotify import DirectNotifyGlobal

class DistributedElevatorExtAI(DistributedElevatorAI.DistributedElevatorAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedElevatorExtAI')

    def __init__(self, air, bldg, numSeats=4, antiShuffle=0, minLaff=0, fSkipOpening=False):
        DistributedElevatorAI.DistributedElevatorAI.__init__(self, air, bldg, numSeats, antiShuffle=antiShuffle, minLaff=minLaff, fSkipOpening=fSkipOpening)
        self.anyToonsBailed = 0
        self.boardingParty = None
        return

    def delete(self):
        for seatIndex in range(len(self.seats)):
            avId = self.seats[seatIndex]
            if avId:
                self.clearFullNow(seatIndex)
                self.clearEmptyNow(seatIndex)

        DistributedElevatorAI.DistributedElevatorAI.delete(self)

    def d_setFloor(self, floorNumber):
        self.sendUpdate('setFloor', [floorNumber])

    def acceptBoarder(self, avId, seatIndex, wantBoardingShow=0):
        DistributedElevatorAI.DistributedElevatorAI.acceptBoarder(self, avId, seatIndex, wantBoardingShow)
        self.acceptOnce(self.air.getAvatarExitEvent(avId), self.__handleUnexpectedExit, extraArgs=[avId])
        self.fsm.request('waitCountdown')

    def __handleUnexpectedExit(self, avId):
        self.notify.warning('Avatar: ' + str(avId) + ' has exited unexpectedly')
        seatIndex = self.findAvatar(avId)
        if seatIndex == None:
            pass
        else:
            self.clearFullNow(seatIndex)
            self.clearEmptyNow(seatIndex)
            if self.countFullSeats() == 0:
                self.fsm.request('waitEmpty')
        return

    def acceptExiter(self, avId):
        seatIndex = self.findAvatar(avId)
        if seatIndex == None:
            pass
        else:
            self.clearFullNow(seatIndex)
            bailFlag = 0
            timeToSend = self.countdownTime
            if self.antiShuffle:
                myTask = taskMgr.getTasksNamed(self.uniqueName('countdown-timer'))[0]
                timeLeft = myTask.wakeTime - globalClock.getFrameTime()
                timeLeft = max(0, timeLeft)
                timeToSet = timeLeft + 10.0
                timeToSet = min(timeLeft + 10.0, self.countdownTime)
                self.setCountdown(timeToSet)
                timeToSend = timeToSet
                self.sendUpdate('emptySlot' + str(seatIndex), [
                 avId, 1, globalClockDelta.getRealNetworkTime(), timeToSend])
            else:
                if self.anyToonsBailed == 0:
                    bailFlag = 1
                    self.resetCountdown()
                    self.anyToonsBailed = 1
                    self.sendUpdate('emptySlot' + str(seatIndex), [
                     avId, bailFlag, globalClockDelta.getRealNetworkTime(), timeToSend])
                else:
                    self.sendUpdate('emptySlot' + str(seatIndex), [
                     avId, bailFlag, globalClockDelta.getRealNetworkTime(), timeToSend])
            if self.countFullSeats() == 0:
                self.fsm.request('waitEmpty')
            taskMgr.doMethodLater(TOON_EXIT_ELEVATOR_TIME, self.clearEmptyNow, self.uniqueName('clearEmpty-%s' % seatIndex), extraArgs=(seatIndex,))
        return

    def enterOpening(self):
        DistributedElevatorAI.DistributedElevatorAI.enterOpening(self)
        taskMgr.doMethodLater(ElevatorData[ELEVATOR_NORMAL]['openTime'], self.waitEmptyTask, self.uniqueName('opening-timer'))

    def waitEmptyTask(self, task):
        self.fsm.request('waitEmpty')
        return Task.done

    def enterWaitEmpty(self):
        DistributedElevatorAI.DistributedElevatorAI.enterWaitEmpty(self)
        self.anyToonsBailed = 0

    def enterWaitCountdown(self):
        DistributedElevatorAI.DistributedElevatorAI.enterWaitCountdown(self)
        taskMgr.doMethodLater(self.countdownTime, self.timeToGoTask, self.uniqueName('countdown-timer'))

    def timeToGoTask(self, task):
        if self.countFullSeats() > 0:
            self.fsm.request('allAboard')
        else:
            self.fsm.request('waitEmpty')
        return Task.done

    def resetCountdown(self):
        taskMgr.remove(self.uniqueName('countdown-timer'))
        taskMgr.doMethodLater(self.countdownTime, self.timeToGoTask, self.uniqueName('countdown-timer'))

    def setCountdown(self, timeToSet):
        taskMgr.remove(self.uniqueName('countdown-timer'))
        taskMgr.doMethodLater(timeToSet, self.timeToGoTask, self.uniqueName('countdown-timer'))

    def enterAllAboard(self):
        DistributedElevatorAI.DistributedElevatorAI.enterAllAboard(self)
        currentTime = globalClock.getRealTime()
        elapsedTime = currentTime - self.timeOfBoarding
        self.notify.debug('elapsed time: ' + str(elapsedTime))
        waitTime = max(TOON_BOARD_ELEVATOR_TIME - elapsedTime, 0)
        waitTime += self.getBoardingShowTimeLeft()
        taskMgr.doMethodLater(waitTime, self.closeTask, self.uniqueName('waitForAllAboard'))

    def getBoardingShowTimeLeft(self):
        currentTime = globalClock.getRealTime()
        timeLeft = 0.0
        if hasattr(self, 'timeOfGroupBoarding') and self.timeOfGroupBoarding:
            elapsedTime = currentTime - self.timeOfGroupBoarding
            timeLeft = max(MAX_GROUP_BOARDING_TIME - elapsedTime, 0)
            if timeLeft > MAX_GROUP_BOARDING_TIME:
                timeLeft = 0.0
        return timeLeft

    def closeTask(self, task):
        if self.countFullSeats() > 0:
            self.fsm.request('closing')
        else:
            self.fsm.request('waitEmpty')
        return Task.done

    def enterClosing(self):
        DistributedElevatorAI.DistributedElevatorAI.enterClosing(self)
        taskMgr.doMethodLater(ElevatorData[ELEVATOR_NORMAL]['closeTime'], self.elevatorClosedTask, self.uniqueName('closing-timer'))

    def elevatorClosedTask(self, task):
        self.elevatorClosed()
        return Task.done

    def _createInterior(self):
        self.bldg.createSuitInterior()

    def elevatorClosed(self):
        numPlayers = self.countFullSeats()
        if numPlayers > 0:
            self._createInterior()
            for seatIndex in range(len(self.seats)):
                avId = self.seats[seatIndex]
                if avId:
                    self.clearFullNow(seatIndex)

        else:
            self.notify.warning('The elevator left, but was empty.')
        self.fsm.request('closed')

    def requestExit(self, *args):
        self.notify.debug('requestExit')
        avId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(avId)
        if self.boardingParty and self.boardingParty.getGroupLeader(avId) and avId:
            if avId == self.boardingParty.getGroupLeader(avId):
                memberIds = self.boardingParty.getGroupMemberList(avId)
                for memberId in memberIds:
                    member = simbase.air.doId2do.get(memberId)
                    if member:
                        if self.accepting:
                            self.acceptingExitersHandler(memberId)
                        else:
                            self.rejectingExitersHandler(memberId)

            else:
                self.rejectingExitersHandler(avId)
        else:
            if av:
                newArgs = (
                 avId,) + args
                if self.accepting:
                    self.acceptingExitersHandler(*newArgs)
                else:
                    self.rejectingExitersHandler(*newArgs)
            else:
                self.notify.warning('avId: %s does not exist, but tried to exit an elevator' % avId)
            return
