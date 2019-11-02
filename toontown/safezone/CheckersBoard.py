

class CheckersBoard:

    def __init__(self):
        self.squareList = []
        for x in range(32):
            self.squareList.append(CheckersTile(x))

        self.squareList[0].setAdjacent([None,
         None,
         4,
         None])
        self.squareList[1].setAdjacent([None,
         4,
         5,
         None])
        self.squareList[2].setAdjacent([None,
         5,
         6,
         None])
        self.squareList[3].setAdjacent([None,
         6,
         7,
         None])
        self.squareList[4].setAdjacent([0,
         8,
         9,
         1])
        self.squareList[5].setAdjacent([1,
         9,
         10,
         2])
        self.squareList[6].setAdjacent([2,
         10,
         11,
         3])
        self.squareList[7].setAdjacent([3,
         11,
         None,
         None])
        self.squareList[8].setAdjacent([None,
         None,
         12,
         4])
        self.squareList[9].setAdjacent([4,
         12,
         13,
         5])
        self.squareList[10].setAdjacent([5,
         13,
         14,
         6])
        self.squareList[11].setAdjacent([6,
         14,
         15,
         7])
        self.squareList[12].setAdjacent([8,
         16,
         17,
         9])
        self.squareList[13].setAdjacent([9,
         17,
         18,
         10])
        self.squareList[14].setAdjacent([10,
         18,
         19,
         11])
        self.squareList[15].setAdjacent([11,
         19,
         None,
         None])
        self.squareList[16].setAdjacent([None,
         None,
         20,
         12])
        self.squareList[17].setAdjacent([12,
         20,
         21,
         13])
        self.squareList[18].setAdjacent([13,
         21,
         22,
         14])
        self.squareList[19].setAdjacent([14,
         22,
         23,
         15])
        self.squareList[20].setAdjacent([16,
         24,
         25,
         17])
        self.squareList[21].setAdjacent([17,
         25,
         26,
         18])
        self.squareList[22].setAdjacent([18,
         26,
         27,
         19])
        self.squareList[23].setAdjacent([19,
         27,
         None,
         None])
        self.squareList[24].setAdjacent([None,
         None,
         28,
         20])
        self.squareList[25].setAdjacent([20,
         28,
         29,
         21])
        self.squareList[26].setAdjacent([21,
         29,
         30,
         22])
        self.squareList[27].setAdjacent([22,
         30,
         31,
         23])
        self.squareList[28].setAdjacent([24,
         None,
         None,
         25])
        self.squareList[29].setAdjacent([25,
         None,
         None,
         26])
        self.squareList[30].setAdjacent([26,
         None,
         None,
         27])
        self.squareList[31].setAdjacent([27,
         None,
         None,
         None])
        self.squareList[0].setJumps([None,
         None,
         9,
         None])
        self.squareList[1].setJumps([None,
         8,
         10,
         None])
        self.squareList[2].setJumps([None,
         9,
         11,
         None])
        self.squareList[3].setJumps([None,
         10,
         None,
         None])
        self.squareList[4].setJumps([None,
         None,
         13,
         None])
        self.squareList[5].setJumps([None,
         12,
         14,
         None])
        self.squareList[6].setJumps([None,
         13,
         15,
         None])
        self.squareList[7].setJumps([None,
         14,
         None,
         None])
        self.squareList[8].setJumps([None,
         None,
         17,
         1])
        self.squareList[9].setJumps([0,
         16,
         18,
         2])
        self.squareList[10].setJumps([1,
         17,
         19,
         3])
        self.squareList[11].setJumps([2,
         18,
         None,
         None])
        self.squareList[12].setJumps([None,
         None,
         21,
         5])
        self.squareList[13].setJumps([4,
         20,
         22,
         6])
        self.squareList[14].setJumps([5,
         21,
         23,
         7])
        self.squareList[15].setJumps([6,
         22,
         None,
         None])
        self.squareList[16].setJumps([None,
         None,
         25,
         9])
        self.squareList[17].setJumps([8,
         24,
         26,
         10])
        self.squareList[18].setJumps([9,
         25,
         27,
         11])
        self.squareList[19].setJumps([10,
         26,
         None,
         None])
        self.squareList[20].setJumps([None,
         None,
         29,
         13])
        self.squareList[21].setJumps([12,
         28,
         30,
         14])
        self.squareList[22].setJumps([13,
         29,
         31,
         15])
        self.squareList[23].setJumps([14,
         30,
         None,
         None])
        self.squareList[24].setJumps([None,
         None,
         None,
         17])
        self.squareList[25].setJumps([16,
         None,
         None,
         18])
        self.squareList[26].setJumps([17,
         None,
         None,
         19])
        self.squareList[27].setJumps([18,
         None,
         None,
         None])
        self.squareList[28].setJumps([None,
         None,
         None,
         21])
        self.squareList[29].setJumps([20,
         None,
         None,
         22])
        self.squareList[30].setJumps([21,
         None,
         None,
         23])
        self.squareList[31].setJumps([22,
         None,
         None,
         None])
        return

    def delete(self):
        for x in self.squareList:
            x.delete()

        del self.squareList

    def getSquare(self, arrayLoc):
        return self.squareList[arrayLoc]

    def getState(self, squareNum):
        return self.squareList[squareNum].getState()

    def setState(self, squareNum, newState):
        self.squareList[squareNum].setState(newState)

    def getAdjacent(self, squareNum):
        return self.squareList[squareNum].adjacent

    def getStates(self):
        retList = []
        for x in range(32):
            retList.append(self.squareList[x].getState())

        return retList

    def setStates(self, squares):
        y = 0
        for x in range(32):
            self.squareList[x].setState(squares[x])

    def getJumps(self, squareNum):
        return self.squareList[squareNum].jumps


class CheckersTile:

    def __init__(self, tileNum):
        self.tileNum = tileNum
        self.state = 0
        self.adjacent = []
        self.jumps = []

    def delete(self):
        del self.tileNum
        del self.state
        del self.adjacent

    def setJumps(self, jumpList):
        for x in jumpList:
            self.jumps.append(x)

    def getJumps(self):
        return self.jumps

    def setAdjacent(self, adjList):
        for x in adjList:
            self.adjacent.append(x)

    def getAdjacent(self):
        return self.adjacent

    def setState(self, newState):
        self.state = newState

    def getState(self):
        return self.state

    def getNum(self):
        return self.tileNum
