from toontown.coghq import LaserGameBase
from direct.distributed import ClockDelta
from direct.task import Task
import random

class LaserGameDrag(LaserGameBase.LaserGameBase):

    def __init__(self, funcSuccess, funcFail, funcSendGrid, funcSetGrid):
        LaserGameBase.LaserGameBase.__init__(self, funcSuccess, funcFail, funcSendGrid, funcSetGrid)
        self.setGridSize(6, 6)
        self.blankGrid()
        self.symbolList = [
            16,
            13,
            17]

    def win(self):
        if not self.finshed:
            self.blankGrid()
            self.funcSendGrid()

        LaserGameBase.LaserGameBase.win(self)

    def lose(self):
        self.blankGrid()
        self.funcSendGrid()
        LaserGameBase.LaserGameBase.lose(self)

    def startGrid(self):
        LaserGameBase.LaserGameBase.startGrid(self)
        for column in range(0, self.gridNumX):
            for row in range(0, self.gridNumY):
                tile = 0
                self.gridData[column][row] = tile

        for column in range(0, self.gridNumX):
            self.gridData[column][self.gridNumY - 1] = 12

        for symbol in self.symbolList:
            finished = 0
            while finished == 0:
                numTris = 4
                tris = 0
                sanity = 1000
                if numTris >= 1:
                    while tris < numTris and sanity:
                        sanity -= 1
                        column = random.randint(0, self.gridNumX - 1)
                        row = random.randint(1, self.gridNumY - 1)
                        if self.gridData[column][row] == 0:
                            self.gridData[column][row] = symbol
                            tris += 1

                if self.checkFor3(symbol):
                    self.clearIndex(symbol)
                    finished = 0
                else:
                    finished = 1

    def hit(self, hitX, hitY, oldx = -1, oldy = -1):
        if self.finshed:
            return

        if oldx >= 0 and oldy >= 0:
            if self.gridData[hitX][hitY] == 0:
                if self.gridData[oldx][oldy] in self.symbolList:
                    self.gridData[hitX][hitY] = self.gridData[oldx][oldy]
                    self.gridData[oldx][oldy] = 0

        for index in self.symbolList:
            if self.checkFor3(index):
                self.clearIndex(index)

        if self.checkForWin():
            self.win()
        else:
            self.funcSendGrid()

    def checkFor3(self, index):
        numInARow = 0
        for posX in range(0, self.gridNumX):
            for posY in range(0, self.gridNumY):
                if self.gridData[posX][posY] == index:
                    numInARow += 1
                    if numInARow >= 3:
                        return 1
                else:
                    numInARow = 0

            numInARow = 0

        numInARow = 0
        for posY in range(0, self.gridNumY):
            for posX in range(0, self.gridNumX):
                if self.gridData[posX][posY] == index:
                    numInARow += 1
                    if numInARow >= 3:
                        return 1
                else:
                    numInARow = 0

            numInARow = 0

        return 0

    def clearIndex(self, index):
        for posX in range(0, self.gridNumX):
            for posY in range(0, self.gridNumY):
                if self.gridData[posX][posY] == index:
                    self.gridData[posX][posY] = 0

    def checkForClear(self, index):
        for posX in range(0, self.gridNumX):
            for posY in range(0, self.gridNumY):
                if self.gridData[posX][posY] == index:
                    return 0

        return 1

    def checkForWin(self):
        for symbol in self.symbolList:
            if not self.checkForClear(symbol):
                return 0

        return 1
