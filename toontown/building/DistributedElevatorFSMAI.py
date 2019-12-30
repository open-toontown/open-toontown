from otp.ai.AIBase import *
from toontown.toonbase import ToontownGlobals
from direct.distributed.ClockDelta import *
from .ElevatorConstants import *
from direct.distributed import DistributedObjectAI
from direct.task import Task
from direct.directnotify import DirectNotifyGlobal
from direct.fsm.FSM import FSM

class DistributedElevatorFSMAI(DistributedObjectAI.DistributedObjectAI, FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedElevatorFSMAI')
    defaultTransitions = {'Off': ['Opening', 'Closed'], 'Opening': ['WaitEmpty', 'WaitCountdown', 'Opening', 'Closing'], 'WaitEmpty': ['WaitCountdown', 'Closing'], 'WaitCountdown': ['WaitEmpty', 'AllAboard', 'Closing'], 'AllAboard': ['WaitEmpty', 'Closing'], 'Closing': ['Closed', 'WaitEmpty', 'Closing', 'Opening'], 'Closed': ['Opening']}
    id = 0

    def __init__(self, air, bldg, numSeats=4, antiShuffle=0, minLaff=0):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        FSM.__init__(self, 'Elevator_%s_FSM' % self.id)
        self.type = ELEVATOR_NORMAL
        self.countdownTime = ElevatorData[self.type]['countdown']
        self.bldg = bldg
        self.bldgDoId = bldg.getDoId()
        self.seats = []
        for seat in range(numSeats):
            self.seats.append(None)

        self.accepting = 0
        self.setAntiShuffle(antiShuffle)
        self.setMinLaff(minLaff)
        if self.antiShuffle:
            if not hasattr(simbase.air, 'elevatorTripId'):
                simbase.air.elevatorTripId = 1
            self.elevatorTripId = simbase.air.elevatorTripId
            simbase.air.elevatorTripId += 1
        else:
            self.elevatorTripId = 0
        return

    def delete(self):
        del self.bldg
        self.ignoreAll()
        DistributedObjectAI.DistributedObjectAI.delete(self)

    def generate(self):
        DistributedObjectAI.DistributedObjectAI.generate(self)
        self.start()

    def getBldgDoId(self):
        return self.bldgDoId

    def findAvailableSeat(self):
        for i in range(len(self.seats)):
            if self.seats[i] == None:
                return i

        return

    def findAvatar(self, avId):
        for i in range(len(self.seats)):
            if self.seats[i] == avId:
                return i

        return None

    def countFullSeats(self):
        avCounter = 0
        for i in self.seats:
            if i:
                avCounter += 1

        return avCounter

    def countOpenSeats(self):
        openSeats = 0
        for i in range(len(self.seats)):
            if self.seats[i] == None:
                openSeats += 1

        return openSeats

    def rejectingBoardersHandler(self, avId, reason=0):
        self.rejectBoarder(avId, reason)

    def rejectBoarder(self, avId, reason=0):
        self.sendUpdateToAvatarId(avId, 'rejectBoard', [avId, reason])

    def acceptingBoardersHandler(self, avId, reason=0):
        self.notify.debug('acceptingBoardersHandler')
        seatIndex = self.findAvailableSeat()
        if seatIndex == None:
            self.rejectBoarder(avId, REJECT_NOSEAT)
        else:
            self.acceptBoarder(avId, seatIndex)
        return

    def acceptBoarder(self, avId, seatIndex):
        self.notify.debug('acceptBoarder')
        if self.findAvatar(avId) != None:
            return
        self.seats[seatIndex] = avId
        self.timeOfBoarding = globalClock.getRealTime()
        self.sendUpdate('fillSlot' + str(seatIndex), [
         avId])
        return

    def rejectingExitersHandler(self, avId):
        self.rejectExiter(avId)

    def rejectExiter(self, avId):
        pass

    def acceptingExitersHandler(self, avId):
        self.acceptExiter(avId)

    def clearEmptyNow(self, seatIndex):
        self.sendUpdate('emptySlot' + str(seatIndex), [
         0, 0, globalClockDelta.getRealNetworkTime()])

    def clearFullNow(self, seatIndex):
        avId = self.seats[seatIndex]
        if avId == None:
            self.notify.warning('Clearing an empty seat index: ' + str(seatIndex) + ' ... Strange...')
        else:
            self.seats[seatIndex] = None
            self.sendUpdate('fillSlot' + str(seatIndex), [
             0])
            self.ignore(self.air.getAvatarExitEvent(avId))
        return

    def d_setState(self, state):
        self.sendUpdate('setState', [state, globalClockDelta.getRealNetworkTime()])

    def getState(self):
        return self.state

    def avIsOKToBoard(self, av):
        return av.hp > self.minLaff and self.accepting

    def checkBoard(self, av):
        if av.hp < self.minLaff:
            return REJECT_MINLAFF
        return 0

    def requestBoard(self, *args):
        self.notify.debug('requestBoard')
        avId = self.air.getAvatarIdFromSender()
        if self.findAvatar(avId) != None:
            self.notify.warning('Ignoring multiple requests from %s to board.' % avId)
            return
        av = self.air.doId2do.get(avId)
        if av:
            newArgs = (
             avId,) + args
            boardResponse = self.checkBoard(av)
            newArgs = (avId,) + args + (boardResponse,)
            if boardResponse == 0:
                self.acceptingBoardersHandler(*newArgs)
            else:
                self.rejectingBoardersHandler(*newArgs)
        else:
            self.notify.warning('avid: %s does not exist, but tried to board an elevator' % avId)
        return

    def requestExit(self, *args):
        if hasattr(self, 'air'):
            self.notify.debug('requestExit')
            avId = self.air.getAvatarIdFromSender()
            av = self.air.doId2do.get(avId)
            if av:
                newArgs = (
                 avId,) + args
                if self.accepting:
                    self.acceptingExitersHandler(*newArgs)
                else:
                    self.rejectingExitersHandler(*newArgs)
            else:
                self.notify.warning('avId: %s does not exist, but tried to exit an elevator' % avId)

    def start(self):
        self.open()

    def enterOff(self):
        self.accepting = 0
        self.timeOfBoarding = None
        if hasattr(self, 'doId'):
            for seatIndex in range(len(self.seats)):
                taskMgr.remove(self.uniqueName('clearEmpty-' + str(seatIndex)))

        return

    def exitOff(self):
        self.accepting = 0

    def open(self):
        self.request('Opening')

    def enterOpening(self):
        self.d_setState('Opening')
        self.accepting = 0
        for seat in self.seats:
            seat = None

        return

    def exitOpening(self):
        self.accepting = 0
        taskMgr.remove(self.uniqueName('opening-timer'))

    def enterWaitCountdown(self):
        self.d_setState('WaitCountdown')
        self.accepting = 1

    def exitWaitCountdown(self):
        print('exit wait countdown')
        self.accepting = 0
        taskMgr.remove(self.uniqueName('countdown-timer'))
        self.newTrip()

    def enterAllAboard(self):
        self.accepting = 0

    def exitAllAboard(self):
        self.accepting = 0
        taskMgr.remove(self.uniqueName('waitForAllAboard'))

    def enterClosing(self):
        self.d_setState('Closing')
        self.accepting = 0

    def exitClosing(self):
        self.accepting = 0
        taskMgr.remove(self.uniqueName('closing-timer'))

    def enterClosed(self):
        if hasattr(self, 'doId'):
            print(self.doId)
        self.d_setState('Closed')

    def exitClosed(self):
        pass

    def enterWaitEmpty(self):
        for i in range(len(self.seats)):
            self.seats[i] = None

        print(self.seats)
        self.d_setState('WaitEmpty')
        self.accepting = 1
        return

    def exitWaitEmpty(self):
        self.accepting = 0

    def setElevatorTripId(self, id):
        self.elevatorTripId = id

    def getElevatorTripId(self):
        return self.elevatorTripId

    def newTrip(self):
        if self.antiShuffle:
            self.elevatorTripId = simbase.air.elevatorTripId
            if simbase.air.elevatorTripId > 2100000000:
                simbase.air.elevatorTripId = 1
            simbase.air.elevatorTripId += 1
            self.sendUpdate('setElevatorTripId', [self.elevatorTripId])

    def setAntiShuffle(self, antiShuffle):
        self.antiShuffle = antiShuffle

    def getAntiShuffle(self):
        return self.antiShuffle

    def setMinLaff(self, minLaff):
        self.minLaff = minLaff

    def getMinLaff(self):
        return self.minLaff
