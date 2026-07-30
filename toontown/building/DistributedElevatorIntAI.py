from otp.ai.AIBase import *
from toontown.toonbase import ToontownGlobals
from direct.distributed.ClockDelta import *
from toontown.building.ElevatorConstants import *
import copy
from toontown.building import DistributedElevatorAI
from direct.fsm import ClassicFSM
from direct.fsm import State
from direct.task import Task
from direct.directnotify import DirectNotifyGlobal
from toontown.battle import BattleBase

class DistributedElevatorIntAI(DistributedElevatorAI.DistributedElevatorAI):

    def __init__(self, air, bldg, avIds):
        DistributedElevatorAI.DistributedElevatorAI.__init__(self, air, bldg)
        self.countdownTime = simbase.config.GetFloat('int-elevator-timeout', INTERIOR_ELEVATOR_COUNTDOWN_TIME)
        self.avIds = copy.copy(avIds)
        for avId in avIds:
            self.acceptOnce(self.air.getAvatarExitEvent(avId), self.__handleAllAvsUnexpectedExit, extraArgs=[avId])

    def checkBoard(self, av):
        result = 0
        if av.doId not in self.avIds:
            result = REJECT_NOSEAT
        else:
            result = DistributedElevatorAI.DistributedElevatorAI.checkBoard(self, av)
        return result

    def acceptBoarder(self, avId, seatIndex, wantBoardingShow=0):
        DistributedElevatorAI.DistributedElevatorAI.acceptBoarder(self, avId, seatIndex, wantBoardingShow)
        self.__closeIfNecessary()

    def __closeIfNecessary(self):
        numFullSeats = self.countFullSeats()
        if not numFullSeats <= len(self.avIds):
            self.notify.warning('we are about to crash. self.seats=%s self.avIds=%s' % (self.seats, self.avIds))
        if numFullSeats == len(self.avIds):
            self.fsm.request('allAboard')

    def __handleAllAvsUnexpectedExit(self, avId):
        self.notify.warning('Avatar: ' + str(avId) + ' has exited unexpectedly')
        seatIndex = self.findAvatar(avId)
        avIdCount = self.avIds.count(avId)
        if avIdCount == 1:
            self.avIds.remove(avId)
        else:
            if avIdCount == 0:
                self.notify.warning("Strange... %d exited unexpectedly, but I don't have them on my list." % avId)
            else:
                self.notify.error('This list is screwed up! %s' % self.avIds)
        if seatIndex == None:
            self.notify.debug('%d is not boarded, but exited' % avId)
        else:
            self.clearFullNow(seatIndex)
            self.clearEmptyNow(seatIndex)
        self.__closeIfNecessary()
        return

    def acceptExiter(self, avId):
        seatIndex = self.findAvatar(avId)
        if seatIndex == None:
            pass
        else:
            self.clearFullNow(seatIndex)
            self.sendUpdate('emptySlot' + str(seatIndex), [
             avId, 0, globalClockDelta.getRealNetworkTime(), self.countdownTime])
            taskMgr.doMethodLater(TOON_EXIT_ELEVATOR_TIME, self.clearEmptyNow, self.uniqueName('clearEmpty-%s' % seatIndex), extraArgs=(seatIndex,))
        return

    def d_forcedExit(self, avId):
        self.sendUpdateToAvatarId(avId, 'forcedExit', [avId])

    def requestBuildingExit(self):
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug('requestBuildingExit from %d' % avId)
        if self.accepting:
            if avId in self.avIds:
                self.avIds.remove(avId)
                self.__closeIfNecessary()
            else:
                self.notify.warning('avId: %s not known, but tried to exit the building' % avId)

    def enterOpening(self):
        DistributedElevatorAI.DistributedElevatorAI.enterOpening(self)
        taskMgr.doMethodLater(ElevatorData[ELEVATOR_NORMAL]['openTime'], self.waitCountdownTask, self.uniqueName('opening-timer'))

    def waitCountdownTask(self, task):
        self.fsm.request('waitCountdown')
        return Task.done

    def enterWaitCountdown(self):
        DistributedElevatorAI.DistributedElevatorAI.enterWaitCountdown(self)
        taskMgr.doMethodLater(self.countdownTime + BattleBase.SERVER_BUFFER_TIME, self.timeToGoTask, self.uniqueName('countdown-timer'))

    def timeToGoTask(self, task):
        self.allAboard()
        return Task.done

    def allAboard(self):
        if len(self.avIds) == 0:
            self.bldg.handleAllAboard([None, None, None, None])
        else:
            self.fsm.request('allAboard')
        return

    def enterAllAboard(self):
        for avId in self.avIds:
            if self.findAvatar(avId) == None:
                self.d_forcedExit(avId)

        DistributedElevatorAI.DistributedElevatorAI.enterAllAboard(self)
        if self.timeOfBoarding != None:
            currentTime = globalClock.getRealTime()
            elapsedTime = currentTime - self.timeOfBoarding
            self.notify.debug('elapsed time: ' + str(elapsedTime))
            waitTime = max(TOON_BOARD_ELEVATOR_TIME - elapsedTime, 0)
            taskMgr.doMethodLater(waitTime, self.closeTask, self.uniqueName('waitForAllAboard'))
        else:
            self.fsm.request('closing')
        return

    def closeTask(self, task):
        self.fsm.request('closing')
        return Task.done

    def enterClosing(self):
        DistributedElevatorAI.DistributedElevatorAI.enterClosing(self)
        taskMgr.doMethodLater(ElevatorData[ELEVATOR_NORMAL]['closeTime'] + BattleBase.SERVER_BUFFER_TIME, self.elevatorClosedTask, self.uniqueName('closing-timer'))

    def elevatorClosedTask(self, task):
        self.fsm.request('closed')
        return Task.done

    def __doorsClosed(self):
        self.bldg.handleAllAboard(self.seats)
        self.fsm.request('closed')

    def enterClosed(self):
        DistributedElevatorAI.DistributedElevatorAI.enterClosed(self)
        self.__doorsClosed()
