from otp.ai.AIBase import *
from direct.interval.IntervalGlobal import *
from direct.directnotify import DirectNotifyGlobal
from direct.distributed import ClockDelta
from direct.task import Task
from otp.level import DistributedEntityAI
from otp.level import BasicEntities
from toontown.coghq import BattleBlockerAI
from direct.distributed.ClockDelta import *
from toontown.toonbase import ToontownBattleGlobals
from .GolfGreenGameGlobals import *
import random, time

class DistributedGolfGreenGameAI(BattleBlockerAI.BattleBlockerAI, NodePath, BasicEntities.NodePathAttribs):

    def __init__(self, level, entId):
        BattleBlockerAI.BattleBlockerAI.__init__(self, level, entId)
        random.seed(time.time() * entId)
        node = hidden.attachNewNode('DistributedLaserFieldAI')
        NodePath.__init__(self, node)
        if not hasattr(self, 'switchId'):
            self.switchId = 0
        self.gridScale = 1
        self.enabled = 1
        self.hasShownSuits = 0
        self.healReady = 1
        self.playedSound = 0
        self.canButton = 1
        self.allBoardsClear = 0
        self.challengeDefeated = False
        self.title = 'MemTag: This is a golfGreenGame %s' % random.random()
        self.translateData = {}
        self.translateData['r'] = 0
        self.translateData['b'] = 1
        self.translateData['g'] = 2
        self.translateData['w'] = 3
        self.translateData['k'] = 4
        self.translateData['l'] = 5
        self.translateData['y'] = 6
        self.translateData['o'] = 7
        self.translateData['a'] = 8
        self.translateData['s'] = 9
        self.translateData['R'] = 10
        self.translateData['B'] = 11
        self.preData = []
        self.boardList = []
        self.joinedToons = []
        self.everJoinedToons = []
        self.startTime = None
        self.totalTime = 1180.0
        self.DamageOnFailure = 20.0
        return

    def announceGenerate(self):
        BattleBlockerAI.BattleBlockerAI.announceGenerate(self)
        self.totalTime = self.timeToPlay
        numToons = 0
        if hasattr(self, 'level'):
            numToons = len(self.level.presentAvIds)
        numBoards = self.puzzleBase + numToons * self.puzzlePerPlayer
        boardSelect = list(range(0, len(gameBoards)))
        didGetLast = 1
        for index in range(numBoards):
            choice = random.choice(boardSelect)
            if not didGetLast:
                didGetLast = 1
                choice = len(gameBoards) - 1
            self.preData.append(gameBoards[choice])
            boardSelect.remove(choice)
            self.boardList.append([[], index, index, None])

        self.boardData = []
        self.attackPatterns = []
        self.processPreData()
        return

    def processPreData(self):
        for board in self.preData:
            x = []
            for rowIndex in range(1, len(board)):
                for columnIndex in range(len(board[rowIndex])):
                    color = self.translateData.get(board[rowIndex][columnIndex])
                    if color != None:
                        x.append((len(board[rowIndex]) - (columnIndex + 1), rowIndex - 1, color))

            self.boardData.append(x)

        for board in self.preData:
            attackString = board[0]
            attackPattern = []
            for ball in attackString:
                color = self.translateData.get(ball)
                if color or color == 0:
                    place = random.choice(list(range(0, len(attackPattern) + 1)))
                    attackPattern.insert(place, color)
                    place = random.choice(list(range(0, len(attackPattern) + 1)))
                    attackPattern.insert(place, color)

            self.attackPatterns.append(attackPattern)

        return

    def startTimer(self):
        self.startTime = globalClockDelta.getFrameNetworkTime()
        taskMgr.doMethodLater(self.totalTime, self.__handleTimeOut, self.taskName('GolfGreenGameTimeout'))
        self.sendUpdate('setTimerStart', [self.totalTime, self.startTime])

    def __printTime(self, task):
        print('Time Left %s' % self.getTimeLeft())
        taskMgr.doMethodLater(1.0, self.__printTime, self.taskName('GolfGreenGameTimeout Print'))
        return task.done

    def __handleTimeOut(self, task=None):
        taskMgr.remove(self.taskName('GolfGreenGameTimeout'))
        self.__handleFinsihed(0)
        return task.done

    def getTimeLeft(self):
        if self.startTime == None:
            return self.totalTime
        else:
            timePassed = globalClockDelta.localElapsedTime(self.startTime)
            timeLeft = self.totalTime - timePassed
            return timeLeft
        return

    def choosePattern(self):
        dataSize = len(self.boardData)
        indexChoice = int(random.random() * dataSize)
        boardToAssign = None
        for boardIndex in range(len(self.boardList)):
            board = self.boardList[boardIndex]
            if self.boardList[boardIndex][0] == 'closed':
                pass
            elif boardToAssign == None or len(self.boardList[boardIndex][0]) < len(self.boardList[boardToAssign][0]):
                boardToAssign = boardIndex
            elif len(self.boardList[boardIndex][0]) == len(self.boardList[boardToAssign][0]):
                choice = random.choice(list(range(2)))
                if choice:
                    boardToAssign = boardIndex

        if boardToAssign == None:
            pass
        return boardToAssign

    def checkForAssigned(self, avId):
        for index in range(len(self.boardList)):
            board = self.boardList[index]
            if board[0] == 'closed':
                pass
            elif avId in board[0]:
                return index

        return None

    def leaveGame(self):
        senderId = self.air.getAvatarIdFromSender()
        if senderId in self.joinedToons:
            self.joinedToons.remove(senderId)
            self.sendUpdate('acceptJoin', [self.totalTime, self.startTime, self.joinedToons])
        for boardDatum in self.boardList:
            if boardDatum[0] == 'closed':
                pass
            elif senderId in boardDatum[0]:
                boardDatum[0].remove(senderId)

    def requestJoin(self):
        if self.allBoardsClear:
            self.sendUpdate('acceptJoin', [0.0, 0.0, [0]])
            return
        senderId = self.air.getAvatarIdFromSender()
        if senderId not in self.joinedToons:
            if self.startTime == None:
                self.startTimer()
            self.joinedToons.append(senderId)
            if senderId not in self.everJoinedToons:
                self.everJoinedToons.append(senderId)
            self.sendUpdate('acceptJoin', [self.totalTime, self.startTime, self.joinedToons])
            self.sendScoreData()
        return

    def requestBoard(self, boardVerify):
        senderId = self.air.getAvatarIdFromSender()
        assigned = self.checkForAssigned(senderId)
        if assigned != None:
            if self.boardList[assigned][0] == 'closed':
                return
            if boardVerify:
                toon = simbase.air.doId2do.get(senderId)
                if toon:
                    self.addGag(senderId)
                    self.sendUpdate('helpOthers', [senderId])
                for avId in self.boardList[assigned][0]:
                    if avId != senderId:
                        self.sendUpdateToAvatarId(avId, 'boardCleared', [senderId])

                self.boardList[assigned][0] = 'closed'
                self.boardList[assigned][3] = senderId
                self.sendScoreData()
            else:
                self.boardList[assigned][0].remove(senderId)
        boardIndex = self.choosePattern()
        if boardIndex == None:
            self.__handleFinsihed(1)
        else:
            self.boardList[boardIndex][0].append(senderId)
            self.sendUpdateToAvatarId(senderId, 'startBoard', [self.boardData[self.boardList[boardIndex][1]], self.attackPatterns[self.boardList[boardIndex][2]]])
        return

    def addGag(self, avId):
        av = simbase.air.doId2do.get(avId)
        if av:
            level = ToontownBattleGlobals.LAST_REGULAR_GAG_LEVEL
            track = int(random.random() * ToontownBattleGlobals.NUM_GAG_TRACKS)
            while not av.hasTrackAccess(track):
                track = int(random.random() * ToontownBattleGlobals.NUM_GAG_TRACKS)

            maxGags = av.getMaxCarry()
            av.inventory.calcTotalProps()
            numGags = av.inventory.totalProps
            numReward = min(1, maxGags - numGags)
            while numReward > 0 and level >= 0:
                result = av.inventory.addItem(track, level)
                if result <= 0:
                    level -= 1
                else:
                    numReward -= 1
                    self.sendUpdateToAvatarId(avId, 'informGag', [track, level])

            av.d_setInventory(av.inventory.makeNetString())

    def __handleFinsihed(self, success):
        self.allBoardsClear = 1
        self.sendUpdate('signalDone', [success])
        self.switchFire()
        taskMgr.remove(self.taskName('GolfGreenGameTimeout'))
        if success:
            for avId in self.joinedToons:
                self.addGag(avId)
                toon = simbase.air.doId2do.get(avId)
                timeleft = int(self.getTimeLeft())
                if toon and timeleft > 0:
                    toon.toonUp(timeleft)

        else:
            roomId = self.getLevelDoId()
            room = simbase.air.doId2do.get(roomId)
            if room:
                playerIds = self.everJoinedToons
                for avId in playerIds:
                    av = simbase.air.doId2do.get(avId)
                    if av:
                        av.takeDamage(self.DamageOnFailure, quietly=0)
                        room.sendUpdate('forceOuch', [self.DamageOnFailure])

        if not self.challengeDefeated:
            self.challengeDefeated = True
            roomId = self.getLevelDoId()
            room = simbase.air.doId2do.get(roomId)
            if room:
                self.challengeDefeated = True
                room.challengeDefeated()
                eventName = self.getOutputEventName()
                messenger.send(eventName, [1])

    def switchFire(self):
        if self.switchId != 0:
            switch = self.level.getEntity(self.switchId)
            if switch:
                switch.setIsOn(1)

    def generate(self):
        BattleBlockerAI.BattleBlockerAI.generate(self)
        if self.switchId != 0:
            self.accept(self.getOutputEventName(self.switchId), self.reactToSwitch)
        self.detectName = 'golfGreenGame %s' % self.doId
        taskMgr.doMethodLater(1.0, self.__detect, self.detectName)
        self.setPos(self.pos)
        self.setHpr(self.hpr)

    def registerBlocker(self):
        BattleBlockerAI.BattleBlockerAI.registerBlocker(self)
        if hasattr(self, 'hideSuits'):
            self.hideSuits()

    def delete(self):
        taskMgr.remove(self.detectName)
        self.ignoreAll()
        BattleBlockerAI.BattleBlockerAI.delete(self)

    def destroy(self):
        self.notify.info('destroy entity(laserField) %s' % self.entId)
        BattleBlockerAI.BattleBlockerAI.destroy(self)

    def __detect(self, task):
        isThereAnyToons = False
        if hasattr(self, 'level'):
            toonInRange = 0
            for avId in self.level.presentAvIds:
                if avId in self.air.doId2do:
                    av = self.air.doId2do[avId]
                    isThereAnyToons = True
                    distance = self.getDistance(av)

            if isThereAnyToons:
                taskMgr.doMethodLater(1.0, self.__detect, self.detectName)
                self.__run()
        return Task.done

    def __run(self):
        pass

    def reactToSwitch(self, on):
        pass

    def setBattleFinished(self):
        BattleBlockerAI.BattleBlockerAI.setBattleFinished(self)
        messenger.send(self.getOutputEventName(), [1])
        self.switchFire()

    def sendScoreData(self):
        total = len(self.boardList)
        closed = 0
        scoreDict = {}
        for board in self.boardList:
            if board[0] == 'closed':
                closed += 1
                if board[3] not in scoreDict:
                    scoreDict[board[3]] = 1
                else:
                    scoreDict[board[3]] += 1

        outList = []
        for key in scoreDict:
            score = scoreDict[key]
            outList.append([key, score])

        self.sendUpdate('scoreData', [total, closed, outList])
