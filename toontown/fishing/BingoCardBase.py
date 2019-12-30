from direct.directnotify import DirectNotifyGlobal
from toontown.fishing import FishGlobals
from toontown.fishing import BingoGlobals
from direct.showbase import RandomNumGen
from math import ceil, pow

class BingoCardBase:
    notify = DirectNotifyGlobal.directNotify.newCategory('BingoCardBase')

    def __init__(self, cardSize = BingoGlobals.CARD_SIZE, rowSize = BingoGlobals.CARD_ROWS, colSize = BingoGlobals.CARD_COLS):
        self.rowSize = rowSize
        self.colSize = colSize
        self.cardSize = cardSize
        self.cellList = []
        self.gameType = None
        self.gameState = 1 << self.cardSize / 2
        return

    def destroy(self):
        del self.cellList

    def generateCard(self, tileSeed, zoneId):
        rng = RandomNumGen.RandomNumGen(tileSeed)
        fishList = FishGlobals.getPondGeneraList(zoneId)
        emptyCells = self.cardSize - 1 - len(fishList)
        rodId = 0
        for i in range(emptyCells):
            fish = FishGlobals.getRandomFishVitals(zoneId, rodId, rng)
            while not fish[0]:
                fish = FishGlobals.getRandomFishVitals(zoneId, rodId, rng)

            fishList.append((fish[1], fish[2]))
            rodId += 1
            if rodId > 4:
                rodId = 0

        for index in range(self.cardSize):
            if index != self.cardSize / 2:
                choice = rng.randrange(0, len(fishList))
                self.cellList.append(fishList.pop(choice))
            else:
                self.cellList.append((None, None))

        return None

    def getGameType(self):
        return self.gameType

    def getGameState(self):
        return self.gameState

    def getCardSize(self):
        return self.cardSize

    def getRowSize(self):
        return self.rowSize

    def getColSize(self):
        return self.colSize

    def setGameState(self, state):
        self.gameState = state

    def clearCellList(self):
        del self.cellList
        self.cellList = []

    def cellUpdateCheck(self, id, genus, species):
        if id >= self.cardSize:
            self.notify.warning('cellUpdateCheck: Invalid Cell Id %s. Id greater than Card Size.')
            return
        elif id < 0:
            self.notify.warning('cellUpdateCheck: Invalid Cell Id %s. Id less than zero.')
            return
        fishTuple = (genus, species)
        if self.cellList[id][0] == genus or fishTuple == FishGlobals.BingoBoot:
            self.gameState = self.gameState | 1 << id
            if self.checkForWin(id):
                return BingoGlobals.WIN
            return BingoGlobals.UPDATE
        return BingoGlobals.NO_UPDATE

    def checkForWin(self, id):
        pass

    def rowCheck(self, rowId):
        for colId in range(self.colSize):
            if not self.gameState & 1 << self.rowSize * rowId + colId:
                return 0

        return 1

    def colCheck(self, colId):
        for rowId in range(self.rowSize):
            if not self.gameState & 1 << self.rowSize * rowId + colId:
                return 0

        return 1

    def fDiagCheck(self, id):
        checkNum = self.rowSize + 1
        if not id % checkNum:
            for i in range(self.rowSize):
                if not self.gameState & 1 << i * checkNum:
                    return 0

            return 1
        else:
            return 0

    def bDiagCheck(self, id):
        checkNum = self.rowSize - 1
        if not id % checkNum and not id == self.cardSize - 1:
            for i in range(self.rowSize):
                if not self.gameState & 1 << i * checkNum + checkNum:
                    return 0

            return 1
        return 0

    def cellCheck(self, id):
        if self.gameState & 1 << id:
            return 1
        return 0

    def onRow(self, row, id):
        if int(id / self.rowSize) == row:
            return 1
        return 0

    def onCol(self, col, id):
        if id % BingoGlobals.CARD_COLS == col:
            return 1
        return 0

    def onFDiag(self, id):
        checkNum = self.rowSize + 1
        if not id % checkNum:
            return 1
        return 0

    def onBDiag(self, id):
        checkNum = self.rowSize - 1
        if not id % checkNum:
            return 1
        return 0
