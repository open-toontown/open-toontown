from toontown.coghq import LaserGameBase
from direct.distributed import ClockDelta
from direct.task import Task
import random

class LaserGameMineSweeper(LaserGameBase.LaserGameBase):

    def __init__(self, funcSuccess, funcFail, funcSendGrid, funcSetGrid):
        LaserGameBase.LaserGameBase.__init__(self, funcSuccess, funcFail, funcSendGrid, funcSetGrid)
        self.setGridSize(7, 7)
        self.blankGrid()

    def win(self):
        if not self.finshed:
            self.blankGrid()
            self.funcSendGrid()

        LaserGameBase.LaserGameBase.win(self)

    def lose(self):
        if not self.finshed:
            self.revealAll()
            self.funcSendGrid()

        LaserGameBase.LaserGameBase.lose(self)

    def startGrid(self):
        LaserGameBase.LaserGameBase.startGrid(self)
        self.hiddenData = []
        for i in range(0, self.gridNumX):
            self.hiddenData.append([
                0] * self.gridNumY)

        numBombs = int(self.gridNumX * self.gridNumY / 8)
        numBombs += 1
        bomb = 0
        sanity = 1000
        if numBombs > 1:
            while bomb < numBombs and sanity:
                sanity -= 1
                column = random.randint(0, self.gridNumX - 1)
                row = random.randint(1, self.gridNumY - 1)
                if self.hiddenData[column][row] != 12 and self.neighborSum(column, row) < 2 and self.rowSum(row) < numBombs / 3:
                    self.hiddenData[column][row] = 12
                    bomb += 1

        for column in range(0, self.gridNumX):
            for row in range(0, self.gridNumY):
                if self.hiddenData[column][row] == 12:
                    self.gridData[column][row] = 11
                else:
                    self.gridData[column][row] = 10

    def hit(self, hitX, hitY, oldx = -1, oldy = -1):
        if self.finshed:
            return

        if self.hiddenData[hitX][hitY] == 12:
            self.gridData[hitX][hitY] = 12
        else:
            self.neighborReveal(hitX, hitY)
        self.funcSendGrid()

    def revealAll(self):
        for column in range(0, self.gridNumX):
            for row in range(0, self.gridNumY):
                self.neighborReveal(column, row, 1)

    def neighborReveal(self, hitX, hitY, showBomb = 0):
        if showBomb and self.gridData[hitX][hitY] == 11:
            self.gridData[hitX][hitY] = 12

        if self.gridData[hitX][hitY] != 10:
            return

        self.gridData[hitX][hitY] = self.neighborSum(hitX, hitY)
        if self.neighborSum(hitX, hitY) == 0:
            if hitX > 0 and hitY > 0:
                self.neighborReveal(hitX - 1, hitY - 1)

            if hitY > 0:
                self.neighborReveal(hitX, hitY - 1)

            if hitX < self.gridNumX - 1 and hitY > 0:
                self.neighborReveal(hitX + 1, hitY - 1)

            if hitX > 0:
                self.neighborReveal(hitX - 1, hitY)

            if hitX < self.gridNumX - 1:
                self.neighborReveal(hitX + 1, hitY)

            if hitX > 0 and hitY < self.gridNumY - 1:
                self.neighborReveal(hitX - 1, hitY + 1)

            if hitY < self.gridNumY - 1:
                self.neighborReveal(hitX, hitY + 1)

            if hitX < self.gridNumX - 1 and hitY < self.gridNumY - 1:
                self.neighborReveal(hitX + 1, hitY + 1)

    def rowSum(self, y):
        sum = 0
        for i in range(0, self.gridNumX - 1):
            if self.hiddenData[i][y] == 12:
                sum += 1

        return sum

    def neighborSum(self, hitX, hitY):
        sum = 0
        if hitX > 0 and hitY > 0:
            if self.hiddenData[hitX - 1][hitY - 1] == 12:
                sum += 1

        if hitY > 0:
            if self.hiddenData[hitX][hitY - 1] == 12:
                sum += 1

        if hitX < self.gridNumX - 1 and hitY > 0:
            if self.hiddenData[hitX + 1][hitY - 1] == 12:
                sum += 1

        if hitX > 0:
            if self.hiddenData[hitX - 1][hitY] == 12:
                sum += 1

        if hitX < self.gridNumX - 1:
            if self.hiddenData[hitX + 1][hitY] == 12:
                sum += 1

        if hitX > 0 and hitY < self.gridNumY - 1:
            if self.hiddenData[hitX - 1][hitY + 1] == 12:
                sum += 1

        if hitY < self.gridNumY - 1:
            if self.hiddenData[hitX][hitY + 1] == 12:
                sum += 1

        if hitX < self.gridNumX - 1 and hitY < self.gridNumY - 1:
            if self.hiddenData[hitX + 1][hitY + 1] == 12:
                sum += 1

        return sum
