from direct.directnotify import DirectNotifyGlobal
from toontown.fishing import BingoGlobals
from toontown.fishing import BingoCardBase

class NormalBingo(BingoCardBase.BingoCardBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('NormalBingo')

    def __init__(self, cardSize = BingoGlobals.CARD_SIZE, rowSize = BingoGlobals.CARD_ROWS, colSize = BingoGlobals.CARD_COLS):
        BingoCardBase.BingoCardBase.__init__(self, cardSize, rowSize, colSize)
        self.gameType = BingoGlobals.NORMAL_CARD

    def checkForWin(self, id):
        rowId = int(id / BingoGlobals.CARD_ROWS)
        colId = id % BingoGlobals.CARD_COLS
        rowResult = self.rowCheck(rowId)
        colResult = self.colCheck(colId)
        fDiagResult = self.fDiagCheck(id)
        bDiagResult = self.bDiagCheck(id)
        if rowResult or colResult or fDiagResult or bDiagResult:
            return BingoGlobals.WIN
        return BingoGlobals.NO_UPDATE

    def checkForColor(self, id):
        return 1

    def checkForBingo(self):
        id = self.cardSize / 2
        if self.checkForWin(id):
            return BingoGlobals.WIN
        for i in range(BingoGlobals.CARD_ROWS):
            if i != BingoGlobals.CARD_ROWS / 2:
                rowResult = self.rowCheck(i)
                colResult = self.colCheck(i)
                if rowResult | colResult:
                    return BingoGlobals.WIN

        return BingoGlobals.NO_UPDATE
