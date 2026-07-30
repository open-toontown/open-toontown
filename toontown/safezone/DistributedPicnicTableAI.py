from direct.distributed.DistributedNodeAI import DistributedNodeAI
from direct.distributed.ClockDelta import *
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from direct.fsm import StateData
from toontown.safezone import DistributedChineseCheckersAI
from toontown.safezone import DistributedCheckersAI
from toontown.safezone import DistributedFindFourAI

class DistributedPicnicTableAI(DistributedNodeAI):

    def __init__(self, air, zone, name, x, y, z, h, p, r):
        DistributedNodeAI.__init__(self, air)
        self.name = name
        self.air = air
        self.seats = [
         None, None, None, None, None, None]
        self.setPos(x, y, z)
        self.setHpr(h, p, r)
        self.playersSitting = 0
        self.myPos = (
         x, y, z)
        self.myHpr = (h, p, r)
        self.playerIdList = []
        self.checkersZoneId = None
        self.generateOtpObject(air.districtId, zone, optionalFields=['setX', 'setY', 'setZ', 'setH', 'setP', 'setR'])
        self.observers = []
        self.allowPickers = []
        self.hasPicked = False
        self.game = None
        self.gameDoId = None
        self.isAccepting = True
        return

    def announceGenerate(self):
        pass

    def delete(self):
        DistributedNodeAI.delete(self)
        self.game = None
        self.gameDoId = None
        return

    def setGameDoId(self, doId):
        self.gameDoId = doId
        self.game = self.air.doId2do.get(doId)

    def requestTableState(self):
        avId = self.air.getAvatarIdFromSender()
        self.getTableState()

    def getTableState(self):
        tableStateList = []
        for x in self.seats:
            if x == None:
                tableStateList.append(0)
            else:
                tableStateList.append(x)

        if self.game and self.game.fsm.getCurrentState().getName() == 'playing':
            self.sendUpdate('setTableState', [tableStateList, 1])
        else:
            self.sendUpdate('setTableState', [tableStateList, 0])
        return

    def sendIsPlaying(self):
        if self.game.fsm.getCurrentState().getName() == 'playing':
            self.sendUpdate('setIsPlaying', [1])
        else:
            self.sendUpdate('setIsPlaying', [0])

    def announceWinner(self, gameName, avId):
        self.sendUpdate('announceWinner', [gameName, avId])
        self.gameDoId = None
        self.game = None
        return

    def requestJoin(self, si, x, y, z, h, p, r):
        avId = self.air.getAvatarIdFromSender()
        if self.findAvatar(avId) != None:
            self.notify.warning('Ignoring multiple requests from %s to board.' % avId)
            return
        av = self.air.doId2do.get(avId)
        if av:
            if av.hp > 0 and self.isAccepting and self.seats[si] == None:
                self.notify.debug('accepting boarder %d' % avId)
                self.acceptBoarder(avId, si, x, y, z, h, p, r)
            else:
                self.notify.debug('rejecting boarder %d' % avId)
                self.sendUpdateToAvatarId(avId, 'rejectJoin', [])
        else:
            self.notify.warning('avid: %s does not exist, but tried to board a picnicTable' % avId)
        return

    def acceptBoarder(self, avId, seatIndex, x, y, z, h, p, r):
        self.notify.debug('acceptBoarder %d' % avId)
        if self.findAvatar(avId) != None:
            return
        isEmpty = True
        for xx in self.seats:
            if xx != None:
                isEmpty = False
                break

        if isEmpty == True or self.hasPicked == False:
            self.sendUpdateToAvatarId(avId, 'allowPick', [])
            self.allowPickers.append(avId)
        if self.hasPicked == True:
            self.sendUpdateToAvatarId(avId, 'setZone', [self.game.zoneId])
        self.seats[seatIndex] = avId
        self.acceptOnce(self.air.getAvatarExitEvent(avId), self.__handleUnexpectedExit, extraArgs=[avId])
        self.timeOfBoarding = globalClock.getRealTime()
        if self.game:
            self.game.informGameOfPlayer()
        self.sendUpdate('fillSlot', [
         avId, seatIndex, x, y, z, h, p, r, globalClockDelta.localToNetworkTime(self.timeOfBoarding), self.doId])
        self.getTableState()
        return

    def requestPickedGame(self, gameNum):
        avId = self.air.getAvatarIdFromSender()
        if self.hasPicked == False and avId in self.allowPickers:
            self.hasPicked = True
            numPickers = len(self.allowPickers)
            self.allowPickers = []
            self.pickGame(gameNum)
            if self.game:
                for x in range(numPickers):
                    self.game.informGameOfPlayer()

    def pickGame(self, gameNum):
        x = 0
        for x in self.seats:
            if x != None:
                x += 1

        if gameNum == 1:
            if simbase.config.GetBool('want-chinese', 0):
                self.game = DistributedChineseCheckersAI.DistributedChineseCheckersAI(self.air, self.doId, 'chinese', self.getX(), self.getY(), self.getZ() + 2.83, self.getH(), self.getP(), self.getR())
                self.sendUpdate('setZone', [self.game.zoneId])
        else:
            if gameNum == 2:
                if x <= 2:
                    if simbase.config.GetBool('want-checkers', 0):
                        self.game = DistributedCheckersAI.DistributedCheckersAI(self.air, self.doId, 'checkers', self.getX(), self.getY(), self.getZ() + 2.83, self.getH(), self.getP(), self.getR())
                        self.sendUpdate('setZone', [self.game.zoneId])
            else:
                if x <= 2:
                    if simbase.config.GetBool('want-findfour', 0):
                        self.game = DistributedFindFourAI.DistributedFindFourAI(self.air, self.doId, 'findFour', self.getX(), self.getY(), self.getZ() + 2.83, self.getH(), self.getP(), self.getR())
                        self.sendUpdate('setZone', [self.game.zoneId])
        return

    def requestZone(self):
        avId = self.air.getAvatarIdFromSender()
        self.sendUpdateToAvatarId(avId, 'setZone', [self.game.zoneId])

    def requestGameZone(self):
        if self.hasPicked == True:
            avId = self.air.getAvatarIdFromSender()
            if self.game:
                self.game.playersObserving.append(avId)
            self.observers.append(avId)
            self.acceptOnce(self.air.getAvatarExitEvent(avId), self.handleObserverExit, extraArgs=[avId])
            if self.game:
                if self.game.fsm.getCurrentState().getName() == 'playing':
                    self.sendUpdateToAvatarId(avId, 'setGameZone', [self.checkersZoneId, 1])
                else:
                    self.sendUpdateToAvatarId(avId, 'setGameZone', [self.checkersZoneId, 0])

    def leaveObserve(self):
        avId = self.air.getAvatarIdFromSender()
        if self.game:
            if avId in self.game.playersObserving:
                self.game.playersObserving.remove(avId)

    def handleObserverExit(self, avId):
        if self.game and avId in self.game.playersObserving:
            if self.game:
                self.game.playersObserving.remove(avId)
                self.ignore(self.air.getAvatarExitEvent(avId))

    def requestExit(self):
        self.notify.debug('requestExit')
        avId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(avId)
        if av:
            if self.countFullSeats() > 0:
                self.acceptExiter(avId)
            else:
                self.notify.debug('Player tried to exit after AI already kicked everyone out')
        else:
            self.notify.warning('avId: %s does not exist, but tried to exit picnicTable' % avId)

    def acceptExiter(self, avId):
        seatIndex = self.findAvatar(avId)
        if seatIndex == None:
            if avId in self.observers:
                self.sendUpdateToAvatarId(avId, 'emptySlot', [avId, 255, globalClockDelta.getRealNetworkTime()])
        else:
            self.seats[seatIndex] = None
            self.ignore(self.air.getAvatarExitEvent(avId))
            self.sendUpdate('emptySlot', [
             avId, seatIndex, globalClockDelta.getRealNetworkTime()])
            self.getTableState()
            numActive = 0
            for x in self.seats:
                if x != None:
                    numActive = numActive + 1

            if self.game:
                self.game.informGameOfPlayerLeave()
                self.game.handlePlayerExit(avId)
            if numActive == 0:
                self.isAccepting = True
                if self.game:
                    self.game.handleEmptyGame()
                    self.game.requestDelete()
                    self.game = None
                    self.hasPicked = False
        return

    def __handleUnexpectedExit(self, avId):
        self.notify.warning('Avatar: ' + str(avId) + ' has exited unexpectedly')
        seatIndex = self.findAvatar(avId)
        if seatIndex == None:
            pass
        else:
            self.seats[seatIndex] = None
            self.ignore(self.air.getAvatarExitEvent(avId))
            if self.game:
                self.game.informGameOfPlayerLeave()
                self.game.handlePlayerExit(avId)
                self.hasPicked = False
            self.getTableState()
            numActive = 0
            for x in self.seats:
                if x != None:
                    numActive = numActive + 1

            if numActive == 0 and self.game:
                simbase.air.deallocateZone(self.game.zoneId)
                self.game.requestDelete()
                self.game = None
                self.gameDoId = None
        return

    def informGameOfPlayerExit(self, avId):
        self.game.handlePlayerExit(avId)

    def handleGameOver(self):
        for x in self.observers:
            self.acceptExiter(x)
            self.observers.remove(x)

        if self.game:
            self.game.playersObserving = []
        for x in self.seats:
            if x != None:
                self.acceptExiter(x)

        self.game = None
        self.gameDoId = None
        self.hasPicked = False
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

    def findAvailableSeat(self):
        for i in range(len(self.seats)):
            if self.seats[i] == None:
                return i

        return

    def setCheckersZoneId(self, zoneId):
        self.checkersZoneId = zoneId
