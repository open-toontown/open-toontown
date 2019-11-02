from pandac.PandaModules import *
from direct.distributed.ClockDelta import *
from direct.task.Task import Task
from direct.interval.IntervalGlobal import *
from TrolleyConstants import *
from direct.gui.DirectGui import *
from toontown.toonbase import TTLocalizer
from direct.distributed import DistributedNode
from direct.distributed.ClockDelta import globalClockDelta
from ChineseCheckersBoard import ChineseCheckersBoard
from direct.fsm import ClassicFSM, State
from direct.fsm import StateData
from toontown.distributed import DelayDelete
from toontown.toonbase.ToontownTimer import ToontownTimer
from toontown.toonbase import ToontownGlobals
from direct.distributed.ClockDelta import *
from otp.otpbase import OTPGlobals
from direct.showbase import PythonUtil

class DistributedChineseCheckers(DistributedNode.DistributedNode):

    def __init__(self, cr):
        NodePath.__init__(self, 'DistributedChineseCheckers')
        DistributedNode.DistributedNode.__init__(self, cr)
        self.cr = cr
        self.reparentTo(render)
        self.boardNode = loader.loadModel('phase_6/models/golf/checker_game.bam')
        self.boardNode.reparentTo(self)
        self.board = ChineseCheckersBoard()
        self.playerTags = render.attachNewNode('playerTags')
        self.playerTagList = []
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
        self.moveList = []
        self.mySquares = []
        self.playerSeats = None
        self.accept('mouse1', self.mouseClick)
        self.traverser = base.cTrav
        self.pickerNode = CollisionNode('mouseRay')
        self.pickerNP = camera.attachNewNode(self.pickerNode)
        self.pickerNode.setFromCollideMask(ToontownGlobals.WallBitmask)
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
        self.playerColors = [Vec4(0, 0.9, 0, 1),
         Vec4(0.9, 0.9, 0, 1),
         Vec4(0.45, 0, 0.45, 1),
         Vec4(0.2, 0.4, 0.8, 1),
         Vec4(1, 0.45, 1, 1),
         Vec4(0.8, 0, 0, 1)]
        self.tintConstant = Vec4(0.25, 0.25, 0.25, 0)
        self.ghostConstant = Vec4(0, 0, 0, 0.5)
        self.startingPositions = [[0,
          1,
          2,
          3,
          4,
          5,
          6,
          7,
          8,
          9],
         [10,
          11,
          12,
          13,
          23,
          24,
          25,
          35,
          36,
          46],
         [65,
          75,
          76,
          86,
          87,
          88,
          98,
          99,
          100,
          101],
         [111,
          112,
          113,
          114,
          115,
          116,
          117,
          118,
          119,
          120],
         [74,
          84,
          85,
          95,
          96,
          97,
          107,
          108,
          109,
          110],
         [19,
          20,
          21,
          22,
          32,
          33,
          34,
          44,
          45,
          55]]
        self.nonOpposingPositions = []
        self.knockSound = base.loadSfx('phase_5/audio/sfx/GUI_knock_1.mp3')
        self.clickSound = base.loadSfx('phase_3/audio/sfx/GUI_balloon_popup.mp3')
        self.moveSound = base.loadSfx('phase_6/audio/sfx/CC_move.mp3')
        self.accept('stoppedAsleep', self.handleSleep)
        from direct.fsm import ClassicFSM, State
        self.fsm = ClassicFSM.ClassicFSM('ChineseCheckers', [State.State('waitingToBegin', self.enterWaitingToBegin, self.exitWaitingToBegin, ['playing', 'gameOver']), State.State('playing', self.enterPlaying, self.exitPlaying, ['gameOver']), State.State('gameOver', self.enterGameOver, self.exitGameOver, ['waitingToBegin'])], 'waitingToBegin', 'waitingToBegin')
        x = self.boardNode.find('**/locators')
        self.locatorList = x.getChildren()
        tempList = []
        for x in range(0, 121):
            self.locatorList[x].setTag('GamePeiceLocator', '%d' % x)
            tempList.append(self.locatorList[x].attachNewNode(CollisionNode('picker%d' % x)))
            tempList[x].node().addSolid(CollisionSphere(0, 0, 0, 0.115))

        for z in self.locatorList:
            y = loader.loadModel('phase_6/models/golf/checker_marble.bam')
            z.setColor(0, 0, 0, 0)
            y.reparentTo(z)

        return

    def setName(self, name):
        self.name = name

    def announceGenerate(self):
        DistributedNode.DistributedNode.announceGenerate(self)
        if self.table.fsm.getCurrentState().getName() != 'observing':
            if base.localAvatar.doId in self.table.tableState:
                self.seatPos = self.table.tableState.index(base.localAvatar.doId)
        self.playerTags.setPos(self.getPos())

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
        self.cleanPlayerTags()
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
        self.cleanPlayerTags()
        del self.playerTags
        del self.playerTagList
        self.playerSeats = None
        self.yourTurnBlinker.finish()
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
                self.clockNode.setPos(-.74, 0, -0.2)
                if self.isMyTurn:
                    self.clockNode.countdown(timeLeft, self.doRandomMove)
                else:
                    self.clockNode.countdown(timeLeft, self.doNothing)
                self.clockNode.show()
        return

    def gameStart(self, playerNum):
        if playerNum != 255:
            self.playerNum = playerNum
            self.playerColor = self.playerColors[playerNum - 1]
            self.moveCameraForGame()
            playerPos = playerNum - 1
            import copy
            self.nonOpposingPositions = copy.deepcopy(self.startingPositions)
            if playerPos == 0:
                self.nonOpposingPositions.pop(0)
                self.opposingPositions = self.nonOpposingPositions.pop(2)
            elif playerPos == 1:
                self.nonOpposingPositions.pop(1)
                self.opposingPositions = self.nonOpposingPositions.pop(3)
            elif playerPos == 2:
                self.nonOpposingPositions.pop(2)
                self.opposingPositions = self.nonOpposingPositions.pop(4)
            elif playerPos == 3:
                self.nonOpposingPositions.pop(3)
                self.opposingPositions = self.nonOpposingPositions.pop(0)
            elif playerPos == 4:
                self.nonOpposingPositions.pop(4)
                self.opposingPositions = self.nonOpposingPositions.pop(1)
            elif playerPos == 5:
                self.nonOpposingPositions.pop(5)
                self.opposingPositions = self.nonOpposingPositions.pop(2)
        self.fsm.request('playing')

    def sendTurn(self, playersTurn):
        self.playersTurnBlinker.finish()
        if self.fsm.getCurrentState().getName() == 'playing':
            if self.playerSeats == None:
                self.sendUpdate('requestSeatPositions', [])
            else:
                if playersTurn == self.playerNum:
                    self.isMyTurn = True
                self.enableTurnScreenText(playersTurn)
                self.playersTurnBlinker = Sequence()
                origColor = self.playerColors[playersTurn - 1]
                self.playersTurnBlinker.append(LerpColorInterval(self.playerTagList[self.playerSeats.index(playersTurn)], 0.4, origColor - self.tintConstant - self.ghostConstant, origColor))
                self.playersTurnBlinker.append(LerpColorInterval(self.playerTagList[self.playerSeats.index(playersTurn)], 0.4, origColor, origColor - self.tintConstant - self.ghostConstant))
                self.playersTurnBlinker.loop()
        return

    def announceSeatPositions(self, playerPos):
        self.playerSeats = playerPos
        for x in range(6):
            pos = self.table.seats[x].getPos(render)
            renderedPeice = loader.loadModel('phase_6/models/golf/checker_marble.bam')
            renderedPeice.reparentTo(self.playerTags)
            renderedPeice.setPos(pos)
            renderedPeice.setScale(1.5)
            if x == 1:
                renderedPeice.setZ(renderedPeice.getZ() + 3.3)
                renderedPeice.setScale(1.3)
            elif x == 4:
                renderedPeice.setZ(renderedPeice.getZ() + 3.3)
                renderedPeice.setScale(1.45)
            else:
                renderedPeice.setZ(renderedPeice.getZ() + 3.3)
            renderedPeice.hide()

        self.playerTagList = self.playerTags.getChildren()
        for x in playerPos:
            if x != 0:
                self.playerTagList[playerPos.index(x)].setColor(self.playerColors[x - 1])
                self.playerTagList[playerPos.index(x)].show()

    def cleanPlayerTags(self):
        for x in self.playerTagList:
            x.removeNode()

        self.playerTagList = []
        self.playerTags.removeNode()

    def moveCameraForGame(self):
        if self.table.cameraBoardTrack.isPlaying():
            self.table.cameraBoardTrack.finish()
        rotation = 0
        if self.seatPos > 2:
            if self.playerNum == 1:
                rotation = 180
            elif self.playerNum == 2:
                rotation = -120
            elif self.playerNum == 3:
                rotation = -60
            elif self.playerNum == 4:
                rotation = 0
            elif self.playerNum == 5:
                rotation = 60
            elif self.playerNum == 6:
                rotation = 120
        elif self.playerNum == 1:
            rotation = 0
        elif self.playerNum == 2:
            rotation = 60
        elif self.playerNum == 3:
            rotation = 120
        elif self.playerNum == 4:
            rotation = 180
        elif self.playerNum == 5:
            rotation = -120
        elif self.playerNum == 6:
            rotation = -60
        if rotation == 60 or rotation == -60:
            int = LerpHprInterval(self.boardNode, 2.5, Vec3(rotation, self.boardNode.getP(), self.boardNode.getR()), self.boardNode.getHpr())
        elif rotation == 120 or rotation == -120:
            int = LerpHprInterval(self.boardNode, 3.5, Vec3(rotation, self.boardNode.getP(), self.boardNode.getR()), self.boardNode.getHpr())
        else:
            int = LerpHprInterval(self.boardNode, 4.2, Vec3(rotation, self.boardNode.getP(), self.boardNode.getR()), self.boardNode.getHpr())
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
        self.cleanPlayerTags()
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
        self.exitButton = DirectButton(relief=None, text=TTLocalizer.ChineseCheckersGetUpButton, text_fg=(1, 1, 0.65, 1), text_pos=(0, -.23), text_scale=0.8, image=(self.upButton, self.downButton, self.rolloverButton), image_color=(1, 0, 0, 1), image_scale=(20, 1, 11), pos=(0.92, 0, 0.4), scale=0.15, command=lambda self = self: self.exitButtonPushed())
        return

    def enableScreenText(self):
        defaultPos = (-.8, -0.4)
        if self.playerNum == 1:
            message = TTLocalizer.ChineseCheckersColorG
            color = self.playerColors[0]
        elif self.playerNum == 2:
            message = TTLocalizer.ChineseCheckersColorY
            color = self.playerColors[1]
        elif self.playerNum == 3:
            message = TTLocalizer.ChineseCheckersColorP
            color = self.playerColors[2]
        elif self.playerNum == 4:
            message = TTLocalizer.ChineseCheckersColorB
            color = self.playerColors[3]
        elif self.playerNum == 5:
            message = TTLocalizer.ChineseCheckersColorPink
            color = self.playerColors[4]
        elif self.playerNum == 6:
            message = TTLocalizer.ChineseCheckersColorR
            color = self.playerColors[5]
        else:
            message = TTLocalizer.ChineseCheckersColorO
            color = Vec4(0.0, 0.0, 0.0, 1.0)
            defaultPos = (-.8, -0.4)
        self.screenText = OnscreenText(text=message, pos=defaultPos, scale=0.1, fg=color, align=TextNode.ACenter, mayChange=1)

    def enableStartButton(self):
        self.startButton = DirectButton(relief=None, text=TTLocalizer.ChineseCheckersStartButton, text_fg=(1, 1, 0.65, 1), text_pos=(0, -.23), text_scale=0.6, image=(self.upButton, self.downButton, self.rolloverButton), image_color=(1, 0, 0, 1), image_scale=(20, 1, 11), pos=(0.92, 0, 0.1), scale=0.15, command=lambda self = self: self.startButtonPushed())
        return

    def enableLeaveButton(self):
        self.leaveButton = DirectButton(relief=None, text=TTLocalizer.ChineseCheckersQuitButton, text_fg=(1, 1, 0.65, 1), text_pos=(0, -.13), text_scale=0.5, image=(self.upButton, self.downButton, self.rolloverButton), image_color=(1, 0, 0, 1), image_scale=(20, 1, 11), pos=(0.92, 0, 0.4), scale=0.15, command=lambda self = self: self.exitButtonPushed())
        return

    def enableTurnScreenText(self, player):
        self.yourTurnBlinker.finish()
        playerOrder = [1,
         4,
         2,
         5,
         3,
         6]
        message1 = TTLocalizer.ChineseCheckersIts
        if self.turnText != None:
            self.turnText.destroy()
        if player == self.playerNum:
            message2 = TTLocalizer.ChineseCheckersYourTurn
            color = (0, 0, 0, 1)
        elif player == 1:
            message2 = TTLocalizer.ChineseCheckersGreenTurn
            color = self.playerColors[0]
        elif player == 2:
            message2 = TTLocalizer.ChineseCheckersYellowTurn
            color = self.playerColors[1]
        elif player == 3:
            message2 = TTLocalizer.ChineseCheckersPurpleTurn
            color = self.playerColors[2]
        elif player == 4:
            message2 = TTLocalizer.ChineseCheckersBlueTurn
            color = self.playerColors[3]
        elif player == 5:
            message2 = TTLocalizer.ChineseCheckersPinkTurn
            color = self.playerColors[4]
        elif player == 6:
            message2 = TTLocalizer.ChineseCheckersRedTurn
            color = self.playerColors[5]
        self.turnText = OnscreenText(text=message1 + message2, pos=(-0.8, -0.5), scale=0.092, fg=color, align=TextNode.ACenter, mayChange=1)
        if player == self.playerNum:
            self.yourTurnBlinker = Sequence()
            self.yourTurnBlinker.append(LerpScaleInterval(self.turnText, 0.6, 1.045, 1))
            self.yourTurnBlinker.append(LerpScaleInterval(self.turnText, 0.6, 1, 1.045))
            self.yourTurnBlinker.loop()
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
        if self.isMyTurn == True and self.inGame == True:
            mpos = base.mouseWatcherNode.getMouse()
            self.pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY())
            self.traverser.traverse(render)
            if self.myHandler.getNumEntries() > 0:
                self.myHandler.sortEntries()
                pickedObj = self.myHandler.getEntry(0).getIntoNodePath()
                pickedObj = pickedObj.getNetTag('GamePeiceLocator')
                if pickedObj:
                    self.handleClicked(int(pickedObj))

    def handleClicked(self, index):
        self.sound = Sequence(SoundInterval(self.clickSound))
        if self.moveList == []:
            if index not in self.mySquares:
                return
            self.moveList.append(index)
            if index in self.opposingPositions:
                self.isOpposing = True
            else:
                self.isOpposing = False
            self.blinker = Sequence()
            self.blinker.append(LerpColorInterval(self.locatorList[index], 0.7, self.playerColor - self.tintConstant, self.playerColor))
            self.blinker.append(LerpColorInterval(self.locatorList[index], 0.7, self.playerColor, self.playerColor - self.tintConstant))
            self.blinker.loop()
            self.sound.start()
        elif self.board.squareList[index].getState() == self.playerNum:
            for x in self.moveList:
                self.locatorList[x].setColor(1, 1, 1, 1)
                self.locatorList[x].hide()

            self.blinker.finish()
            self.blinker = Sequence()
            self.blinker.append(LerpColorInterval(self.locatorList[index], 0.7, self.playerColor - self.tintConstant, self.playerColor))
            self.blinker.append(LerpColorInterval(self.locatorList[index], 0.7, self.playerColor, self.playerColor - self.tintConstant))
            self.blinker.loop()
            self.sound.start()
            self.locatorList[self.moveList[0]].setColor(self.playerColor)
            self.locatorList[self.moveList[0]].show()
            self.moveList = []
            self.moveList.append(index)
            if index in self.opposingPositions:
                self.isOpposing = True
            else:
                self.isOpposing = False
        elif self.board.squareList[index].getState() != 0:
            return
        else:
            if len(self.moveList) == 1 and self.board.squareList[index].getState() == 0:
                if index in self.board.squareList[self.moveList[0]].getAdjacent():
                    for x in self.nonOpposingPositions:
                        if index in x:
                            return

                    self.moveList.append(index)
                    self.blinker.finish()
                    self.d_requestMove(self.moveList)
                    self.moveList = []
                    self.isMyTurn = False
                    self.sound.start()
            if len(self.moveList) >= 1:
                if index == self.moveList[len(self.moveList) - 1]:
                    for x in self.nonOpposingPositions:
                        if index in x:
                            return

                    if self.existsLegalJumpsFrom(index) == True:
                        self.blinker.finish()
                        self.d_requestMove(self.moveList)
                        self.moveList = []
                        self.isMyTurn = False
                        self.sound.start()
                elif self.checkLegalMove(self.board.getSquare(self.moveList[len(self.moveList) - 1]), self.board.getSquare(index)) == True:
                    if index not in self.board.squareList[self.moveList[len(self.moveList) - 1]].getAdjacent():
                        for x in self.nonOpposingPositions:
                            if self.existsLegalJumpsFrom(index) == False:
                                if index in x:
                                    return

                        self.moveList.append(index)
                        self.locatorList[index].setColor(self.playerColor - self.tintConstant - self.ghostConstant)
                        self.locatorList[index].show()
                        self.sound.start()
                        if self.existsLegalJumpsFrom(index) == False:
                            self.blinker.finish()
                            self.d_requestMove(self.moveList)
                            self.moveList = []
                            self.isMyTurn = False

    def existsLegalJumpsFrom(self, index):
        for x in self.board.squareList[index].getAdjacent():
            if x == None:
                pass
            elif x in self.moveList:
                pass
            elif self.board.getState(x) == 0:
                pass
            elif self.board.squareList[x].getAdjacent()[self.board.squareList[index].getAdjacent().index(x)] == None:
                pass
            elif self.board.getState(self.board.squareList[x].getAdjacent()[self.board.squareList[index].getAdjacent().index(x)]) == 0 and self.board.squareList[x].getAdjacent()[self.board.squareList[index].getAdjacent().index(x)] not in self.moveList:
                return True

        return False

    def checkLegalMove(self, firstSquare, secondSquare):
        if secondSquare.getNum() in firstSquare.getAdjacent():
            return True
        else:
            for x in firstSquare.getAdjacent():
                if x == None:
                    pass
                elif self.board.squareList[x].getState() == 0:
                    pass
                elif self.board.squareList[x].getAdjacent()[firstSquare.getAdjacent().index(x)] == secondSquare.getNum():
                    return True

            return False
        return

    def d_requestMove(self, moveList):
        self.sendUpdate('requestMove', [moveList])

    def setGameState(self, tableState, moveList):
        if moveList != []:
            self.animatePeice(tableState, moveList)
        else:
            self.updateGameState(tableState)

    def updateGameState(self, squares):
        self.board.setStates(squares)
        self.mySquares = []
        messenger.send('wakeup')
        for x in range(121):
            self.locatorList[x].clearColor()
            owner = self.board.squareList[x].getState()
            if owner == self.playerNum:
                self.mySquares.append(x)
            if owner == 0:
                self.locatorList[x].hide()
            else:
                self.locatorList[x].show()
            if owner == 1:
                self.locatorList[x].setColor(self.playerColors[0])
            elif owner == 2:
                self.locatorList[x].setColor(self.playerColors[1])
            elif owner == 3:
                self.locatorList[x].setColor(self.playerColors[2])
            elif owner == 4:
                self.locatorList[x].setColor(self.playerColors[3])
            elif owner == 5:
                self.locatorList[x].setColor(self.playerColors[4])
            elif owner == 6:
                self.locatorList[x].setColor(self.playerColors[5])

        self.mySquares.sort()
        self.checkForWin()

    def animatePeice(self, tableState, moveList):
        messenger.send('wakeup')
        gamePeiceForAnimation = loader.loadModel('phase_6/models/golf/checker_marble.bam')
        gamePeiceForAnimation.setColor(self.locatorList[moveList[0]].getColor())
        gamePeiceForAnimation.reparentTo(self.boardNode)
        gamePeiceForAnimation.setPos(self.locatorList[moveList[0]].getPos())
        self.locatorList[moveList[0]].hide()
        checkersPeiceTrack = Sequence()
        length = len(moveList)
        for x in range(length - 1):
            checkersPeiceTrack.append(Parallel(SoundInterval(self.moveSound), ProjectileInterval(gamePeiceForAnimation, endPos=self.locatorList[moveList[x + 1]].getPos(), duration=0.5)))

        checkersPeiceTrack.append(Func(gamePeiceForAnimation.removeNode))
        checkersPeiceTrack.append(Func(self.updateGameState, tableState))
        checkersPeiceTrack.start()

    def checkForWin(self):
        if self.playerNum == 1:
            if self.mySquares == self.startingPositions[3]:
                self.sendUpdate('requestWin', [])
        elif self.playerNum == 2:
            if self.mySquares == self.startingPositions[4]:
                self.sendUpdate('requestWin', [])
        elif self.playerNum == 3:
            if self.mySquares == self.startingPositions[5]:
                self.sendUpdate('requestWin', [])
        elif self.playerNum == 4:
            if self.mySquares == self.startingPositions[0]:
                self.sendUpdate('requestWin', [])
        elif self.playerNum == 5:
            if self.mySquares == self.startingPositions[1]:
                self.sendUpdate('requestWin', [])
        elif self.playerNum == 6:
            if self.mySquares == self.startingPositions[2]:
                self.sendUpdate('requestWin', [])

    def announceWin(self, avId):
        self.fsm.request('gameOver')

    def doRandomMove(self):
        if len(self.moveList) >= 2:
            self.blinker.finish()
            self.d_requestMove(self.moveList)
            self.moveList = []
            self.isMyTurn = False
            self.playSound = Sequence(SoundInterval(self.knockSound))
            self.playSound.start()
        else:
            import random
            move = []
            foundLegal = False
            self.blinker.pause()
            self.numRandomMoves += 1
            while not foundLegal:
                x = random.randint(0, 9)
                for y in self.board.getAdjacent(self.mySquares[x]):
                    if y != None and self.board.getState(y) == 0:
                        for zz in self.nonOpposingPositions:
                            if y not in zz:
                                move.append(self.mySquares[x])
                                move.append(y)
                                foundLegal = True
                                break

                        break

            if move == []:
                pass
            playSound = Sequence(SoundInterval(self.knockSound))
            playSound.start()
            self.d_requestMove(move)
            self.moveList = []
            self.isMyTurn = False
            if self.numRandomMoves >= 5:
                self.exitButtonPushed()
        return

    def doNothing(self):
        pass
