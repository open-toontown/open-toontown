from direct.distributed.DistributedNodeAI import DistributedNodeAI
from direct.distributed.ClockDelta import *
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from direct.fsm import StateData
from direct.distributed.ClockDelta import *
from toontown.safezone import CheckersBoard

class DistributedCheckersAI(DistributedNodeAI):

    def __init__(self, air, parent, name, x, y, z, h, p, r):
        DistributedNodeAI.__init__(self, air)
        self.name = name
        self.air = air
        self.setPos(x, y, z)
        self.setHpr(h, p, r)
        self.myPos = (
         x, y, z)
        self.myHpr = (h, p, r)
        self.board = CheckersBoard.CheckersBoard()
        self.parent = self.air.doId2do[parent]
        self.parentDo = parent
        self.wantStart = []
        self.playersPlaying = []
        self.playersSitting = 0
        self.playersTurn = 1
        self.movesMade = 0
        self.playerNum = 1
        self.hasWon = False
        self.playersGamePos = [
         None, None]
        self.wantTimer = True
        self.timerEnd = 0
        self.turnEnd = 0
        self.playersObserving = []
        self.winLaffPoints = 20
        self.movesRequiredToWin = 10
        self.zoneId = self.air.allocateZone()
        self.generateOtpObject(air.districtId, self.zoneId, optionalFields=['setX', 'setY', 'setZ', 'setH', 'setP', 'setR'])
        self.parent.setCheckersZoneId(self.zoneId)
        self.startingPositions = [
         [
          0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], [20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]]
        self.kingPositions = [[31, 30, 29, 28], [0, 1, 2, 3]]
        self.timerStart = None
        self.fsm = ClassicFSM.ClassicFSM('Checkers', [
         State.State('waitingToBegin', self.enterWaitingToBegin, self.exitWaitingToBegin, [
          'playing']),
         State.State('playing', self.enterPlaying, self.exitPlaying, [
          'gameOver']),
         State.State('gameOver', self.enterGameOver, self.exitGameOver, [
          'waitingToBegin'])], 'waitingToBegin', 'waitingToBegin')
        self.fsm.enterInitialState()
        return

    def announceGenerate(self):
        self.parent.setGameDoId(self.doId)

    def getTableDoId(self):
        return self.parentDo

    def delete(self):
        self.fsm.requestFinalState()
        self.board.delete()
        del self.fsm
        DistributedNodeAI.delete(self)

    def informGameOfPlayer(self):
        self.playersSitting += 1
        if self.playersSitting < 2:
            self.timerEnd = 0
        else:
            if self.playersSitting == 2:
                self.timerEnd = globalClock.getRealTime() + 20
                self.parent.isAccepting = False
                self.parent.sendUpdate('setIsPlaying', [1])
            else:
                if self.playersSitting > 2:
                    pass
        self.sendUpdate('setTimer', [globalClockDelta.localToNetworkTime(self.timerEnd)])

    def informGameOfPlayerLeave(self):
        self.playersSitting -= 1
        if self.playersSitting < 2 and self.fsm.getCurrentState().getName() == 'waitingToBegin':
            self.timerEnd = 0
            self.parent.isAccepting = True
            self.parent.sendUpdate('setIsPlaying', [0])

        if self.playersSitting > 2 and self.fsm.getCurrentState().getName() == 'waitingToBegin':
            pass
        else:
            self.timerEnd = 0
        if self.timerEnd != 0:
            self.sendUpdate('setTimer', [globalClockDelta.localToNetworkTime(self.timerEnd)])
        else:
            self.sendUpdate('setTimer', [0])

    def setGameCountdownTime(self):
        self.timerEnd = globalClock.getRealTime() + 10

    def setTurnCountdownTime(self):
        self.turnEnd = globalClock.getRealTime() + 40

    def getTimer(self):
        if self.timerEnd != 0:
            return 0
        else:
            return 0

    def getTurnTimer(self):
        return globalClockDelta.localToNetworkTime(self.turnEnd)

    def requestTimer(self):
        avId = self.air.getAvatarIdFromSender()
        self.sendUpdateToAvatarId(avId, 'setTimer', [globalClockDelta.localToNetworkTime(self.timerEnd)])

    def handlePlayerExit(self, avId):
        if avId in self.wantStart:
            self.wantStart.remove(avId)
        if self.fsm.getCurrentState().getName() == 'playing':
            gamePos = self.playersGamePos.index(avId)
            self.playersGamePos[gamePos] = None
            self.fsm.request('gameOver')
        return

    def handleEmptyGame(self):
        self.movesMade = 0
        self.playersTurn = 1
        self.playerNum = 1
        self.fsm.request('waitingToBegin')
        self.parent.isAccepting = True

    def requestWin(self):
        avId = self.air.getAvatarIdFromSender()

    def distributeLaffPoints(self):
        for x in self.parent.seats:
            if x != None:
                av = self.air.doId2do.get(x)
                av.toonUp(self.winLaffPoints)

        return

    def enterWaitingToBegin(self):
        self.setGameCountdownTime()
        self.parent.isAccepting = True

    def exitWaitingToBegin(self):
        self.turnEnd = 0

    def enterPlaying(self):
        self.parent.isAccepting = False
        for x in self.playersGamePos:
            if x != None:
                self.playersTurn = self.playersGamePos.index(x)
                self.d_sendTurn(self.playersTurn + 1)
                break

        self.setTurnCountdownTime()
        self.sendUpdate('setTurnTimer', [globalClockDelta.localToNetworkTime(self.turnEnd)])
        return

    def exitPlaying(self):
        pass

    def enterGameOver(self):
        self.timerEnd = 0
        isAccepting = True
        self.parent.handleGameOver()
        self.playersObserving = []
        self.playersTurn = 1
        self.playerNum = 1
        self.clearBoard()
        self.sendGameState([])
        self.movesMade = 0
        self.playersGamePos = [None, None, None, None, None, None]
        self.parent.isAccepting = True
        self.fsm.request('waitingToBegin')
        return

    def exitGameOver(self):
        pass

    def requestBegin(self):
        avId = self.air.getAvatarIdFromSender()
        if avId not in self.wantStart:
            self.wantStart.append(avId)
        numPlayers = 0
        for x in self.parent.seats:
            if x != None:
                numPlayers = numPlayers + 1

        if len(self.wantStart) == numPlayers and numPlayers >= 2:
            self.d_gameStart(avId)
            self.parent.sendIsPlaying()
        return

    def d_gameStart(self, avId):
        for x in self.playersObserving:
            self.sendUpdateToAvatarId(x, 'gameStart', [255])

        zz = 0
        numPlayers = 0
        for x in self.parent.seats:
            if x != None:
                numPlayers += 1
                self.playersPlaying.append(x)

        if numPlayers == 2:
            player1 = self.playersPlaying[0]
            self.sendUpdateToAvatarId(player1, 'gameStart', [1])
            self.playersGamePos[0] = player1
            for x in self.startingPositions[0]:
                self.board.setState(x, 1)

            player2 = self.playersPlaying[1]
            self.sendUpdateToAvatarId(player2, 'gameStart', [2])
            self.playersGamePos[1] = player2
            for x in self.startingPositions[1]:
                self.board.setState(x, 2)

        self.sendGameState([])
        self.wantStart = []
        self.fsm.request('playing')
        self.parent.getTableState()
        return

    def d_sendTurn(self, playersTurn):
        self.sendUpdate('sendTurn', [playersTurn])

    def advancePlayerTurn(self):
        if self.playersTurn == 0:
            self.playersTurn = 1
            self.playerNum = 2
        else:
            self.playerNum = 1
            self.playersTurn = 0

    def requestMove(self, moveList):
        if self.checkLegalMoves(moveList) == True:
            self.makeMove(moveList)
            self.advancePlayerTurn()
            self.d_sendTurn(self.playersTurn + 1)
            self.setTurnCountdownTime()
            self.sendUpdate('setTurnTimer', [globalClockDelta.localToNetworkTime(self.turnEnd)])
        else:
            avId = self.air.getAvatarIdFromSender()
            self.sendUpdateToAvatarId(avId, 'illegalMove', [])
            self.air.writeServerEvent('suspicious', avId, 'has requested an illegal move in Regular checkers - not possible')

    def checkLegalMoves(self, moveList):
        if self.board.squareList[moveList[0]].getState() >= 3:
            moveType = 'king'
        else:
            moveType = 'normal'
        if len(moveList) == 2:
            firstSquare = self.board.squareList[moveList[0]]
            secondSquare = self.board.squareList[moveList[1]]
            if self.checkLegalMove(firstSquare, secondSquare, moveType) == True:
                return True
            else:
                for x in range(len(moveList) - 1):
                    y = self.checkLegalJump(self.board.getSquare(moveList[x]), self.board.getSquare(moveList[x + 1]), moveType)
                    if y == False:
                        return False
                    else:
                        return True
                    return False

        elif len(moveList) > 2:
            for x in range(len(moveList) - 1):
                y = self.checkLegalJump(self.board.getSquare(moveList[x]), self.board.getSquare(moveList[x + 1]), moveType)
                if y == False:
                    return False

            return True

    def makeMove(self, moveList):
        for x in range(len(moveList) - 1):
            firstSquare = self.board.squareList[moveList[x]]
            secondSquare = self.board.squareList[moveList[x + 1]]
            if firstSquare.getNum() in secondSquare.getAdjacent():
                break
            index = firstSquare.jumps.index(secondSquare.getNum())
            self.board.squareList[firstSquare.getAdjacent()[index]].setState(0)

        haveMoved = False
        squareState = self.board.squareList[moveList[0]].getState()
        if squareState <= 2:
            piecetype = 'normal'
            if squareState == 1:
                playerNum = 1
            else:
                playerNum = 2
        else:
            piecetype = 'king'
            if squareState == 3:
                playerNum = 1
            else:
                playerNum = 2
        if piecetype == 'normal':
            lastElement = moveList[len(moveList) - 1]
            if playerNum == 1:
                if lastElement in self.kingPositions[0]:
                    self.board.squareList[moveList[0]].setState(0)
                    self.board.squareList[lastElement].setState(3)
                    haveMoved = True
                    self.sendGameState(moveList)
            elif lastElement in self.kingPositions[1]:
                self.board.squareList[moveList[0]].setState(0)
                self.board.squareList[lastElement].setState(4)
                haveMoved = True
                self.sendGameState(moveList)
        if haveMoved == False:
            spot1 = self.board.squareList[moveList[0]].getState()
            self.board.squareList[moveList[0]].setState(0)
            self.board.squareList[moveList[len(moveList) - 1]].setState(spot1)
            self.sendGameState(moveList)
        temp = self.playerNum
        self.playerNum = 1
        if self.hasWon == True:
            return
        if self.hasPeicesAndMoves(1, 3) == False:
            self.parent.announceWinner('Checkers', self.playersPlaying[1])
            self.fsm.request('gameOver')
            self.hasWon = True
            return
        self.playerNum = temp
        temp = self.playerNum
        self.playerNum = 2
        if self.hasPeicesAndMoves(2, 4) == False:
            self.parent.announceWinner('Checkers', self.playersPlaying[0])
            self.fsm.request('gameOver')
            self.hasWon = True
            return
        self.playerNum = temp

    def hasPeicesAndMoves(self, normalNum, kingNum):
        for x in self.board.squareList:
            if x.getState() == normalNum:
                if self.existsLegalMovesFrom(x.getNum(), 'normal') == True:
                    return True
                if self.existsLegalJumpsFrom(x.getNum(), 'normal') == True:
                    return True
            elif x.getState() == kingNum:
                if self.existsLegalMovesFrom(x.getNum(), 'king') == True:
                    return True
                if self.existsLegalJumpsFrom(x.getNum(), 'king') == True:
                    return True

        return False

    def getState(self):
        return self.fsm.getCurrentState().getName()

    def getName(self):
        return self.name

    def getGameState(self):
        return [
         self.board.getStates(), []]

    def sendGameState(self, moveList):
        gameState = self.board.getStates()
        self.sendUpdate('setGameState', [gameState, moveList])

    def clearBoard(self):
        for x in self.board.squareList:
            x.setState(0)

    def getPosHpr(self):
        return self.posHpr

    def existsLegalJumpsFrom(self, index, peice):
        if peice == 'king':
            for x in range(4):
                if self.board.squareList[index].getAdjacent()[x] != None and self.board.squareList[index].getJumps()[x] != None:
                    adj = self.board.squareList[self.board.squareList[index].getAdjacent()[x]]
                    jump = self.board.squareList[self.board.squareList[index].getJumps()[x]]
                    if adj.getState() == 0:
                        pass
                    elif adj.getState() == self.playerNum or adj.getState() == self.playerNum + 2:
                        pass
                    elif jump.getState() == 0:
                        return True

            return False
        else:
            if peice == 'normal':
                if self.playerNum == 1:
                    moveForward = [
                     1, 2]
                else:
                    if self.playerNum == 2:
                        moveForward = [
                         0, 3]
                for x in moveForward:
                    if self.board.squareList[index].getAdjacent()[x] != None and self.board.squareList[index].getJumps()[x] != None:
                        adj = self.board.squareList[self.board.squareList[index].getAdjacent()[x]]
                        jump = self.board.squareList[self.board.squareList[index].getJumps()[x]]
                        if adj.getState() == 0:
                            pass
                        elif adj.getState() == self.playerNum or adj.getState() == self.playerNum + 2:
                            pass
                        elif jump.getState() == 0:
                            return True

                return False
        return

    def existsLegalMovesFrom(self, index, peice):
        if peice == 'king':
            for x in self.board.squareList[index].getAdjacent():
                if x != None:
                    if self.board.squareList[x].getState() == 0:
                        return True

            return False
        else:
            if peice == 'normal':
                if self.playerNum == 1:
                    moveForward = [
                     1, 2]
                else:
                    if self.playerNum == 2:
                        moveForward = [
                         0, 3]
                for x in moveForward:
                    if self.board.squareList[index].getAdjacent()[x] != None:
                        adj = self.board.squareList[self.board.squareList[index].getAdjacent()[x]]
                        if adj.getState() == 0:
                            return True

                return False
        return

    def existsLegalJumpsFrom(self, index, peice):
        if peice == 'king':
            for x in range(4):
                if self.board.squareList[index].getAdjacent()[x] != None and self.board.squareList[index].getJumps()[x] != None:
                    adj = self.board.squareList[self.board.squareList[index].getAdjacent()[x]]
                    jump = self.board.squareList[self.board.squareList[index].getJumps()[x]]
                    if adj.getState() == 0:
                        pass
                    elif adj.getState() == self.playerNum or adj.getState() == self.playerNum + 2:
                        pass
                    elif jump.getState() == 0:
                        return True

            return False
        else:
            if peice == 'normal':
                if self.playerNum == 1:
                    moveForward = [
                     1, 2]
                else:
                    if self.playerNum == 2:
                        moveForward = [
                         0, 3]
                for x in moveForward:
                    if self.board.squareList[index].getAdjacent()[x] != None and self.board.squareList[index].getJumps()[x] != None:
                        adj = self.board.squareList[self.board.squareList[index].getAdjacent()[x]]
                        jump = self.board.squareList[self.board.squareList[index].getJumps()[x]]
                        if adj.getState() == 0:
                            pass
                        elif adj.getState() == self.playerNum or adj.getState() == self.playerNum + 2:
                            pass
                        elif jump.getState() == 0:
                            return True

                return False
        return

    def checkLegalMove(self, firstSquare, secondSquare, peice):
        if self.playerNum == 1:
            moveForward = [
             1, 2]
        else:
            moveForward = [
             0, 3]
        if peice == 'king':
            for x in range(4):
                if firstSquare.getAdjacent()[x] != None:
                    if self.board.squareList[firstSquare.getAdjacent()[x]].getState() == 0:
                        return True

            return False
        else:
            if peice == 'normal':
                for x in moveForward:
                    if firstSquare.getAdjacent()[x] != None:
                        if self.board.squareList[firstSquare.getAdjacent()[x]].getState() == 0:
                            return True

                return False
        return

    def checkLegalJump(self, firstSquare, secondSquare, peice):
        if self.playerNum == 1:
            moveForward = [
             1, 2]
            opposingPeices = [2, 4]
        else:
            moveForward = [
             0, 3]
            opposingPeices = [1, 3]
        if peice == 'king':
            if secondSquare.getNum() in firstSquare.getJumps():
                index = firstSquare.getJumps().index(secondSquare.getNum())
                if self.board.squareList[firstSquare.getAdjacent()[index]].getState() in opposingPeices:
                    return True
                else:
                    return False
        else:
            if peice == 'normal':
                if secondSquare.getNum() in firstSquare.getJumps():
                    index = firstSquare.getJumps().index(secondSquare.getNum())
                    if index in moveForward:
                        if self.board.squareList[firstSquare.getAdjacent()[index]].getState() in opposingPeices:
                            return True
                        else:
                            return False
                    else:
                        return False
                else:
                    return False
