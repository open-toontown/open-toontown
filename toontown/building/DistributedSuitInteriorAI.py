from toontown.toonbase.ToontownBattleGlobals import *
from otp.ai.AIBaseGlobal import *
from direct.distributed.ClockDelta import *
from toontown.building.ElevatorConstants import *
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State
from direct.distributed import DistributedObjectAI
from direct.fsm import State
from toontown.battle import DistributedBattleBldgAI
from toontown.battle import BattleBase
from direct.task import Timer
from toontown.building import DistributedElevatorIntAI
import copy

class DistributedSuitInteriorAI(DistributedObjectAI.DistributedObjectAI):

    def __init__(self, air, elevator):
        self.air = air
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.extZoneId, self.zoneId = elevator.bldg.getExteriorAndInteriorZoneId()
        self.numFloors = elevator.bldg.planner.numFloors
        self.avatarExitEvents = []
        self.toons = []
        self.toonSkillPtsGained = {}
        self.toonExp = {}
        self.toonOrigQuests = {}
        self.toonItems = {}
        self.toonOrigMerits = {}
        self.toonMerits = {}
        self.toonParts = {}
        self.helpfulToons = []
        self.currentFloor = 0
        self.topFloor = self.numFloors - 1
        self.bldg = elevator.bldg
        self.elevator = elevator
        self.suits = []
        self.activeSuits = []
        self.reserveSuits = []
        self.joinedReserves = []
        self.suitsKilled = []
        self.suitsKilledPerFloor = []
        self.battle = None
        self.timer = Timer.Timer()
        self.responses = {}
        self.ignoreResponses = 0
        self.ignoreElevatorDone = 0
        self.ignoreReserveJoinDone = 0
        self.toonIds = copy.copy(elevator.seats)
        for toonId in self.toonIds:
            if toonId != None:
                self.__addToon(toonId)

        self.savedByMap = {}
        self.fsm = ClassicFSM.ClassicFSM('DistributedSuitInteriorAI', [
         State.State('WaitForAllToonsInside', self.enterWaitForAllToonsInside, self.exitWaitForAllToonsInside, [
          'Elevator']),
         State.State('Elevator', self.enterElevator, self.exitElevator, [
          'Battle']),
         State.State('Battle', self.enterBattle, self.exitBattle, [
          'ReservesJoining', 'BattleDone']),
         State.State('ReservesJoining', self.enterReservesJoining, self.exitReservesJoining, [
          'Battle']),
         State.State('BattleDone', self.enterBattleDone, self.exitBattleDone, [
          'Resting', 'Reward']),
         State.State('Resting', self.enterResting, self.exitResting, [
          'Elevator']),
         State.State('Reward', self.enterReward, self.exitReward, [
          'Off']),
         State.State('Off', self.enterOff, self.exitOff, [
          'WaitForAllToonsInside'])], 'Off', 'Off', onUndefTransition=ClassicFSM.ClassicFSM.ALLOW)
        self.fsm.enterInitialState()
        return

    def delete(self):
        self.ignoreAll()
        self.toons = []
        self.toonIds = []
        self.fsm.requestFinalState()
        del self.fsm
        del self.bldg
        del self.elevator
        self.timer.stop()
        del self.timer
        self.__cleanupFloorBattle()
        taskName = self.taskName('deleteInterior')
        taskMgr.remove(taskName)
        DistributedObjectAI.DistributedObjectAI.delete(self)

    def __handleUnexpectedExit(self, toonId):
        self.notify.warning('toon: %d exited unexpectedly' % toonId)
        self.__removeToon(toonId)
        if len(self.toons) == 0:
            self.timer.stop()
            if self.fsm.getCurrentState().getName() == 'Resting':
                pass
            elif self.battle == None:
                self.bldg.deleteSuitInterior()
        return

    def __addToon(self, toonId):
        if toonId not in self.air.doId2do:
            self.notify.warning('addToon() - no toon for doId: %d' % toonId)
            return
        event = self.air.getAvatarExitEvent(toonId)
        self.avatarExitEvents.append(event)
        self.accept(event, self.__handleUnexpectedExit, extraArgs=[toonId])
        self.toons.append(toonId)
        self.responses[toonId] = 0

    def __removeToon(self, toonId):
        if self.toons.count(toonId):
            self.toons.remove(toonId)
        if self.toonIds.count(toonId):
            self.toonIds[self.toonIds.index(toonId)] = None
        if toonId in self.responses:
            del self.responses[toonId]
        event = self.air.getAvatarExitEvent(toonId)
        if self.avatarExitEvents.count(event):
            self.avatarExitEvents.remove(event)
        self.ignore(event)
        return

    def __resetResponses(self):
        self.responses = {}
        for toon in self.toons:
            self.responses[toon] = 0

        self.ignoreResponses = 0

    def __allToonsResponded(self):
        for toon in self.toons:
            if self.responses[toon] == 0:
                return 0

        self.ignoreResponses = 1
        return 1

    def getZoneId(self):
        return self.zoneId

    def getExtZoneId(self):
        return self.extZoneId

    def getDistBldgDoId(self):
        return self.bldg.getDoId()

    def getNumFloors(self):
        return self.numFloors

    def d_setToons(self):
        self.sendUpdate('setToons', self.getToons())

    def getToons(self):
        sendIds = []
        for toonId in self.toonIds:
            if toonId == None:
                sendIds.append(0)
            else:
                sendIds.append(toonId)

        return [sendIds, 0]

    def d_setSuits(self):
        self.sendUpdate('setSuits', self.getSuits())

    def getSuits(self):
        suitIds = []
        for suit in self.activeSuits:
            suitIds.append(suit.doId)

        reserveIds = []
        values = []
        for info in self.reserveSuits:
            reserveIds.append(info[0].doId)
            values.append(info[1])

        return [suitIds, reserveIds, values]

    def b_setState(self, state):
        self.d_setState(state)
        self.setState(state)

    def d_setState(self, state):
        stime = globalClock.getRealTime() + BattleBase.SERVER_BUFFER_TIME
        self.sendUpdate('setState', [state, globalClockDelta.localToNetworkTime(stime)])

    def setState(self, state):
        self.fsm.request(state)

    def getState(self):
        return [
         self.fsm.getCurrentState().getName(), globalClockDelta.getRealNetworkTime()]

    def setAvatarJoined(self):
        avId = self.air.getAvatarIdFromSender()
        if self.toons.count(avId) == 0:
            self.air.writeServerEvent('suspicious', avId, 'DistributedSuitInteriorAI.setAvatarJoined from toon not in %s.' % self.toons)
            self.notify.warning('setAvatarJoined() - av: %d not in list' % avId)
            return
        avatar = self.air.doId2do.get(avId)
        if avatar != None:
            self.savedByMap[avId] = (
             avatar.getName(), avatar.dna.asTuple())
        self.responses[avId] += 1
        if self.__allToonsResponded():
            self.fsm.request('Elevator')
        return

    def elevatorDone(self):
        toonId = self.air.getAvatarIdFromSender()
        if self.ignoreResponses == 1:
            return
        else:
            if self.fsm.getCurrentState().getName() != 'Elevator':
                self.notify.warning('elevatorDone() - in state: %s' % self.fsm.getCurrentState().getName())
                return
            else:
                if self.toons.count(toonId) == 0:
                    self.notify.warning('elevatorDone() - toon not in toon list: %d' % toonId)
                    return
        self.responses[toonId] += 1
        if self.__allToonsResponded() and self.ignoreElevatorDone == 0:
            self.b_setState('Battle')

    def reserveJoinDone(self):
        toonId = self.air.getAvatarIdFromSender()
        if self.ignoreResponses == 1:
            return
        else:
            if self.fsm.getCurrentState().getName() != 'ReservesJoining':
                self.notify.warning('reserveJoinDone() - in state: %s' % self.fsm.getCurrentState().getName())
                return
            else:
                if self.toons.count(toonId) == 0:
                    self.notify.warning('reserveJoinDone() - toon not in list: %d' % toonId)
                    return
        self.responses[toonId] += 1
        if self.__allToonsResponded() and self.ignoreReserveJoinDone == 0:
            self.b_setState('Battle')

    def enterOff(self):
        return None

    def exitOff(self):
        return None

    def enterWaitForAllToonsInside(self):
        self.__resetResponses()
        return None

    def exitWaitForAllToonsInside(self):
        self.__resetResponses()
        return None

    def enterElevator(self):
        suitHandles = self.bldg.planner.genFloorSuits(self.currentFloor)
        self.suits = suitHandles['activeSuits']
        self.activeSuits = []
        for suit in self.suits:
            self.activeSuits.append(suit)

        self.reserveSuits = suitHandles['reserveSuits']
        self.d_setToons()
        self.d_setSuits()
        self.__resetResponses()
        self.d_setState('Elevator')
        self.timer.startCallback(BattleBase.ELEVATOR_T + ElevatorData[ELEVATOR_NORMAL]['openTime'] + BattleBase.SERVER_BUFFER_TIME, self.__serverElevatorDone)
        return None

    def __serverElevatorDone(self):
        self.ignoreElevatorDone = 1
        self.b_setState('Battle')

    def exitElevator(self):
        self.timer.stop()
        self.__resetResponses()
        return None

    def __createFloorBattle(self):
        if self.currentFloor == self.topFloor:
            bossBattle = 1
        else:
            bossBattle = 0
        self.battle = DistributedBattleBldgAI.DistributedBattleBldgAI(self.air, self.zoneId, self.__handleRoundDone, self.__handleBattleDone, bossBattle=bossBattle)
        self.battle.suitsKilled = self.suitsKilled
        self.battle.suitsKilledPerFloor = self.suitsKilledPerFloor
        self.battle.battleCalc.toonSkillPtsGained = self.toonSkillPtsGained
        self.battle.toonExp = self.toonExp
        self.battle.toonOrigQuests = self.toonOrigQuests
        self.battle.toonItems = self.toonItems
        self.battle.toonOrigMerits = self.toonOrigMerits
        self.battle.toonMerits = self.toonMerits
        self.battle.toonParts = self.toonParts
        self.battle.helpfulToons = self.helpfulToons
        self.battle.setInitialMembers(self.toons, self.suits)
        self.battle.generateWithRequired(self.zoneId)
        mult = getCreditMultiplier(self.currentFloor)
        if self.air.suitInvasionManager.getInvading():
            mult *= getInvasionMultiplier()
        self.battle.battleCalc.setSkillCreditMultiplier(mult)

    def __cleanupFloorBattle(self):
        for suit in self.suits:
            self.notify.debug('cleaning up floor suit: %d' % suit.doId)
            if suit.isDeleted():
                self.notify.debug('whoops, suit %d is deleted.' % suit.doId)
            else:
                suit.requestDelete()

        self.suits = []
        self.reserveSuits = []
        self.activeSuits = []
        if self.battle != None:
            self.battle.requestDelete()
        self.battle = None
        return

    def __handleRoundDone(self, toonIds, totalHp, deadSuits):
        totalMaxHp = 0
        for suit in self.suits:
            totalMaxHp += suit.maxHP

        for suit in deadSuits:
            self.activeSuits.remove(suit)

        if len(self.reserveSuits) > 0 and len(self.activeSuits) < 4:
            self.joinedReserves = []
            hpPercent = 100 - totalHp / totalMaxHp * 100.0
            for info in self.reserveSuits:
                if info[1] <= hpPercent and len(self.activeSuits) < 4:
                    self.suits.append(info[0])
                    self.activeSuits.append(info[0])
                    self.joinedReserves.append(info)

            for info in self.joinedReserves:
                self.reserveSuits.remove(info)

            if len(self.joinedReserves) > 0:
                self.fsm.request('ReservesJoining')
                self.d_setSuits()
                return
        if len(self.activeSuits) == 0:
            self.fsm.request('BattleDone', [toonIds])
        else:
            self.battle.resume()

    def __handleBattleDone(self, zoneId, toonIds):
        if len(toonIds) == 0:
            taskName = self.taskName('deleteInterior')
            taskMgr.doMethodLater(10, self.__doDeleteInterior, taskName)
        else:
            if self.currentFloor == self.topFloor:
                self.setState('Reward')
            else:
                self.b_setState('Resting')

    def __doDeleteInterior(self, task):
        self.bldg.deleteSuitInterior()

    def enterBattle(self):
        if self.battle == None:
            self.__createFloorBattle()
            self.elevator.d_setFloor(self.currentFloor)
        return None

    def exitBattle(self):
        return None

    def enterReservesJoining(self):
        self.__resetResponses()
        self.timer.startCallback(ElevatorData[ELEVATOR_NORMAL]['openTime'] + SUIT_HOLD_ELEVATOR_TIME + BattleBase.SERVER_BUFFER_TIME, self.__serverReserveJoinDone)
        return None

    def __serverReserveJoinDone(self):
        self.ignoreReserveJoinDone = 1
        self.b_setState('Battle')

    def exitReservesJoining(self):
        self.timer.stop()
        self.__resetResponses()
        for info in self.joinedReserves:
            self.battle.suitRequestJoin(info[0])

        self.battle.resume()
        self.joinedReserves = []
        return None

    def enterBattleDone(self, toonIds):
        if len(toonIds) != len(self.toons):
            deadToons = []
            for toon in self.toons:
                if toonIds.count(toon) == 0:
                    deadToons.append(toon)

            for toon in deadToons:
                self.__removeToon(toon)

        self.d_setToons()
        if len(self.toons) == 0:
            self.bldg.deleteSuitInterior()
        else:
            if self.currentFloor == self.topFloor:
                self.battle.resume(self.currentFloor, topFloor=1)
            else:
                self.battle.resume(self.currentFloor, topFloor=0)
        return None

    def exitBattleDone(self):
        self.__cleanupFloorBattle()
        return None

    def __handleEnterElevator(self):
        self.fsm.request('Elevator')

    def enterResting(self):
        self.intElevator = DistributedElevatorIntAI.DistributedElevatorIntAI(self.air, self, self.toons)
        self.intElevator.generateWithRequired(self.zoneId)
        return None

    def handleAllAboard(self, seats):
        if not hasattr(self, 'fsm'):
            return
        if __dev__:
            pass
        else:
            currState = self.fsm.getCurrentState().getName()
            if not currState == 'Resting':
                avId = self.air.getAvatarIdFromSender()
                self.air.writeServerEvent('suspicious', avId, 'unexpected state for DistributedSuitInteriorAI.handleAllAboard(). Current State = %s.' % currState)
                self.notify.warning('unexpected state for DistributedSuitInteriorAI.handleAllAboard(). Current State = %s' % currState)
                return
        numOfEmptySeats = seats.count(None)
        if numOfEmptySeats == 4:
            self.bldg.deleteSuitInterior()
            return
        else:
            if numOfEmptySeats >= 0 and numOfEmptySeats <= 3:
                pass
            else:
                self.error('Bad number of empty seats: %s' % numOfEmptySeats)
        for toon in self.toons:
            if seats.count(toon) == 0:
                self.__removeToon(toon)

        self.toonIds = copy.copy(seats)
        self.toons = []
        for toonId in self.toonIds:
            if toonId != None:
                self.toons.append(toonId)

        self.d_setToons()
        self.currentFloor += 1
        self.fsm.request('Elevator')
        return None

    def exitResting(self):
        self.intElevator.requestDelete()
        del self.intElevator
        return None

    def enterReward(self):
        victors = self.toonIds[:]
        savedBy = []
        for v in victors:
            tuple = self.savedByMap.get(v)
            if tuple:
                savedBy.append([v, tuple[0], tuple[1]])

        self.bldg.fsm.request('waitForVictors', [victors, savedBy])
        self.d_setState('Reward')
        return None

    def exitReward(self):
        return None
