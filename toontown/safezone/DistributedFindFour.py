from pandac.PandaModules import *
from direct.distributed.ClockDelta import *
from direct.task.Task import Task
from direct.interval.IntervalGlobal import *
from .TrolleyConstants import *
from direct.gui.DirectGui import *
from toontown.toonbase import TTLocalizer
from direct.distributed import DistributedNode
from direct.distributed.ClockDelta import globalClockDelta
from .ChineseCheckersBoard import ChineseCheckersBoard
from direct.fsm import ClassicFSM, State
from direct.fsm import StateData
from toontown.toonbase.ToontownTimer import ToontownTimer
from toontown.toonbase import ToontownGlobals
from direct.distributed.ClockDelta import *
from otp.otpbase import OTPGlobals
from direct.showbase import PythonUtil
from random import *

class DistributedFindFour(DistributedNode.DistributedNode):

    def __init__(self, cr):
        NodePath.__init__(self, 'DistributedFindFour')
        DistributedNode.DistributedNode.__init__(self, cr)
        self.cr = cr
        self.reparentTo(render)
        self.boardNode = loader.loadModel('phase_6/models/golf/findfour_game.bam')
        self.boardNode.reparentTo(self)
        self.board = [[0,
          0,
          0,
          0,
          0,
          0,
          0],
         [0,
          0,
          0,
          0,
          0,
          0,
          0],
         [0,
          0,
          0,
          0,
          0,
          0,
          0],
         [0,
          0,
          0,
          0,
          0,
          0,
          0],
         [0,
          0,
          0,
          0,
          0,
          0,
          0],
         [0,
          0,
          0,
          0,
          0,
          0,
          0]]
        self.exitButton = None
        self.inGame = False
        self.waiting = True
        self.startButton = None
        self.playerNum = None
        self.turnText = None
        self.isMyTurn = False
        self.wantTimer = True
        self.leaveButton = None
        self.screenText = None
        self.turnText = None
        self.exitButton = None
        self.numRandomMoves = 0
        self.blinker = Sequence()
        self.playersTurnBlinker = Sequence()
        self.yourTurnBlinker = Sequence()
        self.winningSequence = Sequence()
        self.moveSequence = Sequence()
        self.moveList = []
        self.mySquares = []
        self.playerSeats = None
        self.moveCol = None
        self.move = None
        self.accept('mouse1', self.mouseClick)
        self.traverser = base.cTrav
        self.pickerNode = CollisionNode('mouseRay')
        self.pickerNP = camera.attachNewNode(self.pickerNode)
        self.pickerNode.setFromCollideMask(BitMask32(4096))
        self.pickerRay = CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)
        self.myHandler = CollisionHandlerQueue()
        self.traverser.addCollider(self.pickerNP, self.myHandler)
        self.buttonModels = loader.loadModel('phase_3.5/models/gui/inventory_gui')
        self.upButton = self.buttonModels.find('**//InventoryButtonUp')
        self.downButton = self.buttonModels.find('**/InventoryButtonDown')
        self.rolloverButton = self.buttonModels.find('**/InventoryButtonRollover')
        self.clockNode = ToontownTimer()
        self.clockNode.setPos(1.16, 0, -0.83)
        self.clockNode.setScale(0.3)
        self.clockNode.hide()
        self.tintConstant = Vec4(0.25, 0.25, 0.25, 0)
        self.ghostConstant = Vec4(0, 0, 0, 0.5)
        self.knockSound = base.loader.loadSfx('phase_5/audio/sfx/GUI_knock_1.ogg')
        self.clickSound = base.loader.loadSfx('phase_3/audio/sfx/GUI_balloon_popup.ogg')
        self.moveSound = base.loader.loadSfx('phase_6/audio/sfx/CC_move.ogg')
        self.accept('stoppedAsleep', self.handleSleep)
        from direct.fsm import ClassicFSM, State
        self.fsm = ClassicFSM.ClassicFSM('ChineseCheckers', [State.State('waitingToBegin', self.enterWaitingToBegin, self.exitWaitingToBegin, ['playing', 'gameOver']), State.State('playing', self.enterPlaying, self.exitPlaying, ['gameOver']), State.State('gameOver', self.enterGameOver, self.exitGameOver, ['waitingToBegin'])], 'waitingToBegin', 'waitingToBegin')
        startLoc = self.boardNode.find('**/locators')
        self.locatorList = startLoc.getChildren()
        self.startingPositions = self.locatorList.pop(0)
        self.startingPositions = self.startingPositions.getChildren()
        instancePiece = self.boardNode.find('**/pieces')
        tempList = []
        for x in range(7):
            self.startingPositions[x].setTag('StartLocator', '%d' % x)
            collNode = CollisionNode('startpicker%d' % x)
            collNode.setIntoCollideMask(BitMask32(4096))
            tempList.append(self.startingPositions[x].attachNewNode(collNode))
            tempList[x].node().addSolid(CollisionTube(0, 0, 0.23, 0, 0, -.23, 0.2))

        for z in self.startingPositions:
            y = instancePiece.copyTo(z)
            for val in y.getChildren():
                val.hide()

        tempList = []
        for x in range(42):
            self.locatorList[x].setTag('GamePeiceLocator', '%d' % x)
            collNode = CollisionNode('startpicker%d' % x)
            collNode.setIntoCollideMask(BitMask32(4096))
            tempList.append(self.locatorList[x].attachNewNode(collNode))
            tempList[x].node().addSolid(CollisionSphere(0, 0, 0, 0.2))

        for z in self.locatorList:
            y = instancePiece.copyTo(z)
            for val in y.getChildren():
                val.hide()

        dummyHide = instancePiece.getParent().attachNewNode('DummyHider')
        instancePiece.reparentTo(dummyHide)
        dummyHide.hide()
        return

    def setName(self, name):
        self.name = name

    def announceGenerate(self):
        DistributedNode.DistributedNode.announceGenerate(self)
        if self.table.fsm.getCurrentState().getName() != 'observing':
            if base.localAvatar.doId in self.table.tableState:
                self.seatPos = self.table.tableState.index(base.localAvatar.doId)
                if self.seatPos <= 2:
                    for x in self.startingPositions:
                        x.setH(0)

                    for x in self.locatorList:
                        x.setH(0)

                else:
                    for x in self.startingPositions:
                        x.setH(180)

                    for x in self.locatorList:
                        x.setH(180)

            self.moveCameraForGame()
        else:
            self.seatPos = self.table.seatBumpForObserve
            if self.seatPos > 2:
                for x in self.startingPositions:
                    x.setH(180)

                for x in self.locatorList:
                    x.setH(180)

            self.moveCameraForGame()

    def handleSleep(self, task = None):
        if self.fsm.getCurrentState().getName() == 'waitingToBegin':
            self.exitButtonPushed()
        if task != None:
            task.done
        return

    def setTableDoId(self, doId):
        self.tableDoId = doId
        self.table = self.cr.doId2do[doId]
        self.table.setTimerFunc(self.startButtonPushed)
        self.fsm.enterInitialState()
        self.table.setGameDoId(self.doId)

    def disable(self):
        DistributedNode.DistributedNode.disable(self)
        if self.leaveButton:
            self.leaveButton.destroy()
            self.leavebutton = None
        if self.screenText:
            self.screenText.destroy()
            self.screenText = None
        if self.turnText:
            self.turnText.destroy()
            self.turnText = None
        self.clockNode.stop()
        self.clockNode.hide()
        self.ignore('mouse1')
        self.ignore('stoppedAsleep')
        self.fsm = None
        taskMgr.remove('playerTurnTask')
        return

    def delete(self):
        DistributedNode.DistributedNode.delete(self)
        self.table.gameDoId = None
        self.table.game = None
        if self.exitButton:
            self.exitButton.destroy()
        if self.startButton:
            self.startButton.destroy()
        self.clockNode.stop()
        self.clockNode.hide()
        self.table.startButtonPushed = None
        self.ignore('mouse1')
        self.ignore('stoppedAsleep')
        self.fsm = None
        self.table = None
        self.winningSequence.finish()
        taskMgr.remove('playerTurnTask')
        return

    def getTimer(self):
        self.sendUpdate('requestTimer', [])

    def setTimer(self, timerEnd):
        if self.fsm.getCurrentState() != None and self.fsm.getCurrentState().getName() == 'waitingToBegin' and not self.table.fsm.getCurrentState().getName() == 'observing':
            self.clockNode.stop()
            time = globalClockDelta.networkToLocalTime(timerEnd)
            timeLeft = int(time - globalClock.getRealTime())
            if timeLeft > 0 and timerEnd != 0:
                if timeLeft > 60:
                    timeLeft = 60
                self.clockNode.setPos(1.16, 0, -0.83)
                self.clockNode.countdown(timeLeft, self.startButtonPushed)
                self.clockNode.show()
            else:
                self.clockNode.stop()
                self.clockNode.hide()
        return

    def setTurnTimer(self, turnEnd):
        if self.fsm.getCurrentState() != None and self.fsm.getCurrentState().getName() == 'playing':
            self.clockNode.stop()
            time = globalClockDelta.networkToLocalTime(turnEnd)
            timeLeft = int(time - globalClock.getRealTime())
            if timeLeft > 0:
                self.clockNode.setPos(0.64, 0, -0.27)
                self.clockNode.countdown(timeLeft, self.doRandomMove)
                self.clockNode.show()
        return

    def gameStart(self, playerNum):
        if playerNum != 255:
            self.playerNum = playerNum
            if self.playerNum == 1:
                self.playerColorString = 'Red'
            else:
                self.playerColorString = 'Yellow'
            self.moveCameraForGame()
        self.fsm.request('playing')

    def sendTurn(self, playersTurn):
        if self.fsm.getCurrentState().getName() == 'playing':
            if playersTurn == self.playerNum:
                self.isMyTurn = True
                taskMgr.add(self.turnTask, 'playerTurnTask')
            self.enableTurnScreenText(playersTurn)

    def illegalMove(self):
        self.exitButtonPushed()

    def moveCameraForGame(self):
        if self.table.cameraBoardTrack.isPlaying():
            self.table.cameraBoardTrack.pause()
        rotation = 0
        if self.seatPos <= 2:
            position = self.table.seats[1].getPos()
            position = position + Vec3(0, -8, 12.8)
            int = LerpPosHprInterval(camera, 2, position, Vec3(0, -38, 0), camera.getPos(), camera.getHpr())
        else:
            position = self.table.seats[4].getPos()
            position = position + Vec3(0, -8, 12.8)
            if camera.getH() < 0:
                int = LerpPosHprInterval(camera, 2, position, Vec3(-180, -20, 0), camera.getPos(), camera.getHpr())
            else:
                int = LerpPosHprInterval(camera, 2, position, Vec3(180, -20, 0), camera.getPos(), camera.getHpr())
        int.start()

    def enterWaitingToBegin(self):
        if self.table.fsm.getCurrentState().getName() != 'observing':
            self.enableExitButton()
            self.enableStartButton()

    def exitWaitingToBegin(self):
        if self.exitButton:
            self.exitButton.destroy()
            self.exitButton = None
        if self.startButton:
            self.startButton.destroy()
            self.exitButton = None
        self.clockNode.stop()
        self.clockNode.hide()
        return

    def enterPlaying(self):
        self.inGame = True
        self.enableScreenText()
        if self.table.fsm.getCurrentState().getName() != 'observing':
            self.enableLeaveButton()

    def exitPlaying(self):
        self.inGame = False
        if self.leaveButton:
            self.leaveButton.destroy()
            self.leavebutton = None
        self.playerNum = None
        if self.screenText:
            self.screenText.destroy()
            self.screenText = None
        if self.turnText:
            self.turnText.destroy()
            self.turnText = None
        self.clockNode.stop()
        self.clockNode.hide()
        return

    def enterGameOver(self):
        pass

    def exitGameOver(self):
        pass

    def exitWaitCountdown(self):
        self.__disableCollisions()
        self.ignore('trolleyExitButton')
        self.clockNode.reset()

    def enableExitButton(self):
        self.exitButton = DirectButton(relief=None, text=TTLocalizer.ChineseCheckersGetUpButton, text_fg=(1, 1, 0.65, 1), text_pos=(0, -.23), text_scale=0.8, image=(self.upButton, self.downButton, self.rolloverButton), image_color=(1, 0, 0, 1), image_scale=(20, 1, 11), pos=(0.92, 0, 0.8), scale=0.15, command=lambda self = self: self.exitButtonPushed())
        return

    def enableScreenText(self):
        defaultPos = (-.7, -0.29)
        if self.playerNum == 1:
            message = 'You are Red'
            color = Vec4(1, 0, 0, 1)
        elif self.playerNum == 2:
            message = 'You are Yellow'
            color = Vec4(1, 1, 0, 1)
        else:
            message = TTLocalizer.CheckersObserver
            color = Vec4(0, 0, 0, 1)
        self.screenText = OnscreenText(text=message, pos=defaultPos, scale=0.1, fg=color, align=TextNode.ACenter, mayChange=1)

    def enableStartButton(self):
        self.startButton = DirectButton(relief=None, text=TTLocalizer.ChineseCheckersStartButton, text_fg=(1, 1, 0.65, 1), text_pos=(0, -.23), text_scale=0.6, image=(self.upButton, self.downButton, self.rolloverButton), image_color=(1, 0, 0, 1), image_scale=(20, 1, 11), pos=(0.92, 0, 0.57), scale=0.15, command=lambda self = self: self.startButtonPushed())
        return

    def enableLeaveButton(self):
        self.leaveButton = DirectButton(relief=None, text=TTLocalizer.ChineseCheckersQuitButton, text_fg=(1, 1, 0.65, 1), text_pos=(0, -.13), text_scale=0.5, image=(self.upButton, self.downButton, self.rolloverButton), image_color=(1, 0, 0, 1), image_scale=(20, 1, 11), pos=(0.92, 0, 0.8), scale=0.15, command=lambda self = self: self.exitButtonPushed())
        return

    def enableTurnScreenText(self, player):
        playerOrder = [1,
         4,
         2,
         5,
         3,
         6]
        message1 = TTLocalizer.CheckersIts
        if self.turnText != None:
            self.turnText.destroy()
        if player == self.playerNum:
            message2 = TTLocalizer.ChineseCheckersYourTurn
            color = (0, 0, 0, 1)
        elif player == 1:
            message2 = "Red's Turn"
            color = (1, 0, 0, 1)
        elif player == 2:
            message2 = "Yellow's Turn"
            color = (1, 1, 0, 1)
        self.turnText = OnscreenText(text=message1 + message2, pos=(-0.7, -0.39), scale=0.092, fg=color, align=TextNode.ACenter, mayChange=1)
        return

    def startButtonPushed(self):
        self.sendUpdate('requestBegin')
        self.startButton.hide()
        self.clockNode.stop()
        self.clockNode.hide()

    def exitButtonPushed(self):
        self.fsm.request('gameOver')
        self.table.fsm.request('off')
        self.clockNode.stop()
        self.clockNode.hide()
        self.table.sendUpdate('requestExit')

    def mouseClick(self):
        messenger.send('wakeup')
        if self.isMyTurn == True and self.inGame == True and not self.moveSequence.isPlaying():
            if self.moveCol != None:
                self.d_requestMove(self.moveCol)
                self.moveCol = None
                self.isMyTurn = False
                taskMgr.remove('playerTurnTask')
        return

    def handleClicked(self, index):
        pass

    def turnTask(self, task):
        if base.mouseWatcherNode.hasMouse() == False:
            return task.cont
        if self.isMyTurn == False:
            return task.cont
        if self.moveSequence.isPlaying():
            return task.cont
        mpos = base.mouseWatcherNode.getMouse()
        self.pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY())
        self.traverser.traverse(render)
        if self.myHandler.getNumEntries() > 0:
            self.myHandler.sortEntries()
            pickedObj = self.myHandler.getEntry(0).getIntoNodePath()
            pickedObj = pickedObj.getNetTag('StartLocator')
            if pickedObj:
                colVal = int(pickedObj)
                if colVal == self.moveCol:
                    return task.cont
                if self.board[0][colVal] == 0:
                    if self.moveCol != None:
                        for x in self.startingPositions[self.moveCol].getChild(1).getChildren():
                            x.hide()

                    self.moveCol = colVal
                    if self.playerNum == 1:
                        self.startingPositions[self.moveCol].getChild(1).getChild(2).show()
                    elif self.playerNum == 2:
                        self.startingPositions[self.moveCol].getChild(1).getChild(3).show()
        return task.cont

    def d_requestMove(self, moveCol):
        self.sendUpdate('requestMove', [moveCol])

    def setGameState(self, tableState, moveCol, movePos, turn):
        messenger.send('wakeup')
        if self.table.fsm.getCurrentState().getName() == 'observing':
            isBlank = True
            for x in range(7):
                if self.board[5][x] != 0:
                    isBlank = False
                    break

            gameBlank = True
            for x in range(7):
                if tableState[5][x] != 0:
                    gameBlank = False
                    break

            if isBlank == True and gameBlank == False:
                for x in range(6):
                    for y in range(7):
                        self.board[x][y] = tableState[x][y]

                self.updateGameState()
                return
        if moveCol == 0 and movePos == 0 and turn == 0:
            for x in range(6):
                for y in range(7):
                    self.board[x][y] = tableState[x][y]

            self.updateGameState()
        else:
            self.animatePeice(tableState, moveCol, movePos, turn)
        didIWin = self.checkForWin()
        if didIWin != None:
            self.sendUpdate('requestWin', [didIWin])
        return

    def updateGameState(self):
        for x in range(6):
            for y in range(7):
                for z in self.locatorList[x * 7 + y].getChild(1).getChildren():
                    z.hide()

        for x in range(6):
            for y in range(7):
                state = self.board[x][y]
                if state == 1:
                    self.locatorList[x * 7 + y].getChild(1).getChild(0).show()
                elif state == 2:
                    self.locatorList[x * 7 + y].getChild(1).getChild(1).show()

    def checkForWin(self):
        for x in range(6):
            for y in range(7):
                if self.board[x][y] == self.playerNum:
                    if self.checkHorizontal(x, y, self.playerNum) == True:
                        return [x, y]
                    elif self.checkVertical(x, y, self.playerNum) == True:
                        return [x, y]
                    elif self.checkDiagonal(x, y, self.playerNum) == True:
                        return [x, y]

        return None

    def announceWinnerPosition(self, x, y, winDirection, playerNum):
        self.isMyturn = False
        if self.turnText:
            self.turnText.hide()
        self.clockNode.stop()
        self.clockNode.hide()
        if winDirection == 0:
            blinkList = self.findHorizontal(x, y, playerNum)
        elif winDirection == 1:
            blinkList = self.findVertical(x, y, playerNum)
        elif winDirection == 2:
            blinkList = self.findDiagonal(x, y, playerNum)
        if blinkList != []:
            print(blinkList)
            val0 = x * 7 + y
            x = blinkList[0][0]
            y = blinkList[0][1]
            val1 = x * 7 + y
            x = blinkList[1][0]
            y = blinkList[1][1]
            val2 = x * 7 + y
            x = blinkList[2][0]
            y = blinkList[2][1]
            val3 = x * 7 + y
            self.winningSequence = Sequence()
            downBlinkerParallel = Parallel(LerpColorInterval(self.locatorList[val0], 0.3, Vec4(0.5, 0.5, 0.5, 0.5), Vec4(1, 1, 1, 1)), LerpColorInterval(self.locatorList[val1], 0.3, Vec4(0.5, 0.5, 0.5, 0.5), Vec4(1, 1, 1, 1)), LerpColorInterval(self.locatorList[val2], 0.3, Vec4(0.5, 0.5, 0.5, 0.5), Vec4(1, 1, 1, 1)), LerpColorInterval(self.locatorList[val3], 0.3, Vec4(0.5, 0.5, 0.5, 0.5), Vec4(1, 1, 1, 1)))
            upBlinkerParallel = Parallel(LerpColorInterval(self.locatorList[val0], 0.3, Vec4(1, 1, 1, 1), Vec4(0.5, 0.5, 0.5, 0.5)), LerpColorInterval(self.locatorList[val1], 0.3, Vec4(1, 1, 1, 1), Vec4(0.5, 0.5, 0.5, 0.5)), LerpColorInterval(self.locatorList[val2], 0.3, Vec4(1, 1, 1, 1), Vec4(0.5, 0.5, 0.5, 0.5)), LerpColorInterval(self.locatorList[val3], 0.3, Vec4(1, 1, 1, 1), Vec4(0.5, 0.5, 0.5, 0.5)))
            self.winningSequence.append(downBlinkerParallel)
            self.winningSequence.append(upBlinkerParallel)
            self.winningSequence.loop()

    def tie(self):
        self.tieSequence = Sequence(autoFinish=1)
        self.clockNode.stop()
        self.clockNode.hide()
        self.isMyTurn = False
        self.moveSequence.finish()
        if self.turnText:
            self.turnText.hide()
        for x in range(41):
            self.tieSequence.append(Parallel(LerpColorInterval(self.locatorList[x], 0.15, Vec4(0.5, 0.5, 0.5, 0.5), Vec4(1, 1, 1, 1)), LerpColorInterval(self.locatorList[x], 0.15, Vec4(1, 1, 1, 1), Vec4(0.5, 0.5, 0.5, 0.5))))

        whisper = WhisperPopup('This Find Four game has resulted in a Tie!', OTPGlobals.getInterfaceFont(), WhisperPopup.WTNormal)
        whisper.manage(base.marginManager)
        self.tieSequence.start()

    def hideChildren(self, nodeList):
        pass

    def animatePeice(self, tableState, moveCol, movePos, turn):
        messenger.send('wakeup')
        for x in range(6):
            for y in range(7):
                self.board[x][y] = tableState[x][y]

        pos = self.startingPositions[moveCol].getPos()
        if turn == 0:
            peice = self.startingPositions[moveCol].getChild(1).getChildren()[2]
            peice.show()
        elif turn == 1:
            peice = self.startingPositions[moveCol].getChild(1).getChildren()[3]
            peice.show()
        self.moveSequence = Sequence()
        startPos = self.startingPositions[moveCol].getPos()
        arrayLoc = movePos * 7 + moveCol
        self.moveSequence.append(LerpPosInterval(self.startingPositions[moveCol], 1.5, self.locatorList[arrayLoc].getPos(self), startPos))
        self.moveSequence.append(Func(peice.hide))
        self.moveSequence.append(Func(self.startingPositions[moveCol].setPos, startPos))
        self.moveSequence.append(Func(self.updateGameState))
        self.moveSequence.start()

    def announceWin(self, avId):
        self.fsm.request('gameOver')

    def doRandomMove(self):
        if self.isMyTurn:
            if self.moveCol != None:
                self.d_requestMove(self.moveCol)
                self.moveCol = None
                self.isMyTurn = False
                taskMgr.remove('playerTurnTask')
            else:
                hasfound = False
                while hasfound == False:
                    x = randint(0, 6)
                    if self.board[0][x] == 0:
                        self.d_requestMove(x)
                        self.moveCol = None
                        self.isMyTurn = False
                        taskMgr.remove('playerTurnTask')
                        hasfound = True

        return

    def doNothing(self):
        pass

    def checkHorizontal(self, rVal, cVal, playerNum):
        if cVal == 3:
            for x in range(1, 4):
                if self.board[rVal][cVal - x] != playerNum:
                    break
                if self.board[rVal][cVal - x] == playerNum and x == 3:
                    return True

            for x in range(1, 4):
                if self.board[rVal][cVal + x] != playerNum:
                    break
                if self.board[rVal][cVal + x] == playerNum and x == 3:
                    return True

            return False
        elif cVal == 2:
            for x in range(1, 4):
                if self.board[rVal][cVal + x] != playerNum:
                    break
                if self.board[rVal][cVal + x] == playerNum and x == 3:
                    return True

            return False
        elif cVal == 4:
            for x in range(1, 4):
                if self.board[rVal][cVal - x] != playerNum:
                    break
                if self.board[rVal][cVal - x] == playerNum and x == 3:
                    return True

            return False
        else:
            return False

    def checkVertical(self, rVal, cVal, playerNum):
        if rVal == 2:
            for x in range(1, 4):
                if self.board[rVal + x][cVal] != playerNum:
                    break
                if self.board[rVal + x][cVal] == playerNum and x == 3:
                    return True

            return False
        elif rVal == 3:
            for x in range(1, 4):
                if self.board[rVal - x][cVal] != playerNum:
                    break
                if self.board[rVal - x][cVal] == playerNum and x == 3:
                    return True

            return False
        else:
            return False

    def checkDiagonal(self, rVal, cVal, playerNum):
        if cVal <= 2:
            if rVal == 2:
                for x in range(1, 4):
                    if self.board[rVal + x][cVal + x] != playerNum:
                        break
                    if self.board[rVal + x][cVal + x] == playerNum and x == 3:
                        return True

                return False
            elif rVal == 3:
                for x in range(1, 4):
                    if self.board[rVal - x][cVal + x] != playerNum:
                        break
                    if self.board[rVal - x][cVal + x] == playerNum and x == 3:
                        return True

                return False
        elif cVal >= 4:
            if rVal == 2:
                for x in range(1, 4):
                    if self.board[rVal + x][cVal - x] != playerNum:
                        break
                    if self.board[rVal + x][cVal - x] == playerNum and x == 3:
                        return True

                return False
            elif rVal == 3:
                for x in range(1, 4):
                    if self.board[rVal - x][cVal - x] != playerNum:
                        break
                    if self.board[rVal - x][cVal - x] == playerNum and x == 3:
                        return True

                return False
        elif rVal == 3 or rVal == 4 or rVal == 5:
            for x in range(1, 4):
                if self.board[rVal - x][cVal - x] != playerNum:
                    break
                if self.board[rVal - x][cVal - x] == playerNum and x == 3:
                    return True

            for x in range(1, 4):
                if self.board[rVal - x][cVal - x] != playerNum:
                    break
                if self.board[rVal - x][cVal - x] == playerNum and x == 3:
                    return True

            return False
        elif rVal == 0 or rVal == 1 or rVal == 2:
            for x in range(1, 4):
                if self.board[rVal + x][cVal - x] != playerNum:
                    break
                if self.board[rVal + x][cVal - x] == playerNum and x == 3:
                    return True

            for x in range(1, 4):
                if self.board[rVal + x][cVal + x] != playerNum:
                    break
                if self.board[rVal + x][cVal + x] == playerNum and x == 3:
                    return True

            return False
        return False

    def findHorizontal(self, rVal, cVal, playerNum):
        if cVal == 3:
            retList = []
            for x in range(1, 4):
                retList.append([rVal, cVal - x])
                if self.board[rVal][cVal - x] != playerNum:
                    retList = []
                    break
                if self.board[rVal][cVal - x] == playerNum and x == 3:
                    return retList

            for x in range(1, 4):
                retList.append([rVal, cVal + x])
                if self.board[rVal][cVal + x] != playerNum:
                    retList = []
                    break
                if self.board[rVal][cVal + x] == playerNum and x == 3:
                    return retList

            return []
        elif cVal == 2:
            retList = []
            for x in range(1, 4):
                retList.append([rVal, cVal + x])
                if self.board[rVal][cVal + x] != playerNum:
                    retList = []
                    break
                if self.board[rVal][cVal + x] == playerNum and x == 3:
                    return retList

            return []
        elif cVal == 4:
            retList = []
            for x in range(1, 4):
                retList.append([rVal, cVal - x])
                if self.board[rVal][cVal - x] != playerNum:
                    retList = []
                    break
                if self.board[rVal][cVal - x] == playerNum and x == 3:
                    return retList

            return []
        else:
            return []

    def findVertical(self, rVal, cVal, playerNum):
        if rVal == 2:
            retList = []
            for x in range(1, 4):
                retList.append([rVal + x, cVal])
                if self.board[rVal + x][cVal] != playerNum:
                    retList = []
                    break
                if self.board[rVal + x][cVal] == playerNum and x == 3:
                    return retList

            return []
        elif rVal == 3:
            retList = []
            for x in range(1, 4):
                retList.append([rVal - x, cVal])
                if self.board[rVal - x][cVal] != playerNum:
                    retList = []
                    break
                if self.board[rVal - x][cVal] == playerNum and x == 3:
                    return retList

            return []
        else:
            return []

    def findDiagonal(self, rVal, cVal, playerNum):
        retList = []
        if cVal <= 2:
            if rVal == 2:
                for x in range(1, 4):
                    retList.append([rVal + x, cVal + x])
                    if self.board[rVal + x][cVal + x] != playerNum:
                        retList = []
                        break
                    if self.board[rVal + x][cVal + x] == playerNum and x == 3:
                        return retList

                return []
            elif rVal == 3:
                for x in range(1, 4):
                    retList.append([rVal - x, cVal + x])
                    if self.board[rVal - x][cVal + x] != playerNum:
                        retList = []
                        break
                    if self.board[rVal - x][cVal + x] == playerNum and x == 3:
                        return retList

                return []
        elif cVal >= 4:
            if rVal == 2:
                for x in range(1, 4):
                    retList.append([rVal + x, cVal - x])
                    if self.board[rVal + x][cVal - x] != playerNum:
                        retList = []
                        break
                    if self.board[rVal + x][cVal - x] == playerNum and x == 3:
                        return retList

                return []
            elif rVal == 3:
                for x in range(1, 4):
                    retList.append([rVal - x, cVal - x])
                    if self.board[rVal - x][cVal - x] != playerNum:
                        retList = []
                        break
                    if self.board[rVal - x][cVal - x] == playerNum and x == 3:
                        return retList

                return []
        elif rVal == 3 or rVal == 4 or rVal == 5:
            for x in range(1, 4):
                retList.append([rVal - x, cVal - x])
                if self.board[rVal - x][cVal - x] != playerNum:
                    retList = []
                    break
                if self.board[rVal - x][cVal - x] == playerNum and x == 3:
                    return retList

            for x in range(1, 4):
                retList.append([rVal + x, cVal - x])
                if self.board[rVal + x][cVal - x] != playerNum:
                    retList = []
                    break
                if self.board[rVal + x][cVal - x] == playerNum and x == 3:
                    return retList

            return []
        elif rVal == 0 or rVal == 1 or rVal == 2:
            for x in range(1, 4):
                retList.append([rVal + x, cVal - x])
                if self.board[rVal + x][cVal - x] != playerNum:
                    retList = []
                    break
                if self.board[rVal + x][cVal - x] == playerNum and x == 3:
                    return retList

            for x in range(1, 4):
                retList.append([rVal + x, cVal + x])
                if self.board[rVal + x][cVal + x] != playerNum:
                    retList = []
                    break
                if self.board[rVal + x][cVal + x] == playerNum and x == 3:
                    return retList

            return []
        return []
