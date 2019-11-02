from pandac.PandaModules import Vec3, Vec4, Point3, TextNode, VBase4
from direct.gui.DirectGui import DirectFrame, DirectButton, DirectLabel, DirectScrolledList, DirectCheckButton
from direct.gui import DirectGuiGlobals
from direct.showbase import DirectObject
from direct.showbase import PythonUtil
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.parties import PartyGlobals
from toontown.parties.PartyInfo import PartyInfo
from toontown.parties import PartyUtils
from toontown.parties.PartyEditorGridSquare import PartyEditorGridSquare

class PartyEditorGrid:
    notify = directNotify.newCategory('PartyEditorGrid')

    def __init__(self, partyEditor):
        self.partyEditor = partyEditor
        self.initGrid()
        self.lastActivityIdPlaced = None
        return

    def initGrid(self):
        self.grid = [[None,
          None,
          None,
          None,
          None,
          None,
          True,
          True,
          True,
          True,
          True,
          None,
          None,
          None,
          None,
          None,
          None,
          None],
         [None,
          None,
          None,
          None,
          None,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          None,
          None,
          None,
          None,
          None,
          None],
         [None,
          None,
          None,
          None,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          None,
          None,
          None,
          None,
          None],
         [None,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          None,
          None,
          None,
          None],
         [None,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True],
         [True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True],
         [True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True],
         [True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True],
         [True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True],
         [None,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True],
         [None,
          None,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          None],
         [None,
          None,
          None,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          None,
          None],
         [None,
          None,
          None,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          None,
          None],
         [None,
          None,
          None,
          None,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          None,
          None,
          None],
         [None,
          None,
          None,
          None,
          None,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          None,
          None,
          None]]
        for y in range(len(self.grid)):
            for x in range(len(self.grid[0])):
                if self.grid[y][x]:
                    self.grid[y][x] = PartyEditorGridSquare(self.partyEditor, x, y)

        return None

    def getActivitiesOnGrid(self):
        activities = []
        for y in range(len(self.grid)):
            for x in range(len(self.grid[0])):
                if self.grid[y][x] and self.grid[y][x].gridElement:
                    if not self.grid[y][x].gridElement.isDecoration:
                        activityTuple = self.grid[y][x].gridElement.getActivityTuple(x, y)
                        if activityTuple not in activities:
                            activities.append(activityTuple)

        return activities

    def getActivitiesElementsOnGrid(self):
        activities = []
        activityElems = []
        for y in range(len(self.grid)):
            for x in range(len(self.grid[0])):
                if self.grid[y][x] and self.grid[y][x].gridElement:
                    if not self.grid[y][x].gridElement.isDecoration:
                        activityTuple = self.grid[y][x].gridElement.getActivityTuple(x, y)
                        if activityTuple not in activities:
                            activities.append(activityTuple)
                            activityElems.append(self.grid[y][x].gridElement)

        return activityElems

    def getDecorationsOnGrid(self):
        decorations = []
        for y in range(len(self.grid)):
            for x in range(len(self.grid[0])):
                if self.grid[y][x] and self.grid[y][x].gridElement:
                    if self.grid[y][x].gridElement.isDecoration:
                        decorationTuple = self.grid[y][x].gridElement.getDecorationTuple(x, y)
                        if decorationTuple not in decorations:
                            decorations.append(decorationTuple)

        return decorations

    def getGridSquare(self, x, y):
        if y < 0 or y >= PartyGlobals.PartyEditorGridSize[1]:
            return None
        if x < 0 or x >= PartyGlobals.PartyEditorGridSize[0]:
            return None
        return self.grid[y][x]

    def checkGridSquareForAvailability(self, gridSquare, size):
        xOffsetLow, xOffsetHigh, yOffset = self.getXYOffsets(size)
        for y in range(int(gridSquare.y - size[1] / 2), int(gridSquare.y + size[1] / 2) + yOffset):
            for x in range(int(gridSquare.x - size[0] / 2) + xOffsetLow, int(gridSquare.x + size[0] / 2) + xOffsetHigh):
                testGridSquare = self.getGridSquare(x, y)
                if testGridSquare is None:
                    return False
                if testGridSquare.gridElement is not None:
                    return False

        return True

    def getClearGridSquare(self, size, desiredXY = None):
        if desiredXY is not None:
            x = desiredXY[0]
            y = desiredXY[1]
            if self.grid[y][x] is not None:
                if self.checkGridSquareForAvailability(self.grid[y][x], size):
                    return self.grid[y][x]
        for y in range(PartyGlobals.PartyEditorGridSize[1]):
            for x in range(PartyGlobals.PartyEditorGridSize[0]):
                if self.grid[y][x] is not None:
                    if self.checkGridSquareForAvailability(self.grid[y][x], size):
                        return self.grid[y][x]

        return

    def getXYOffsets(self, size):
        if size[0] % 2 == 0:
            xOffsetLow = 1
            xOffsetHigh = 1
        else:
            xOffsetLow = 0
            xOffsetHigh = 1
        if size[1] % 2 == 0:
            yOffset = 0
        else:
            yOffset = 1
        return (xOffsetLow, xOffsetHigh, yOffset)

    def registerNewElement(self, gridElement, centerGridSquare, size):
        xOffsetLow, xOffsetHigh, yOffset = self.getXYOffsets(size)
        for y in range(int(centerGridSquare.y - size[1] / 2), int(centerGridSquare.y + size[1] / 2) + yOffset):
            for x in range(int(centerGridSquare.x - size[0] / 2) + xOffsetLow, int(centerGridSquare.x + size[0] / 2) + xOffsetHigh):
                testGridSquare = self.getGridSquare(x, y)
                if testGridSquare is None:
                    return False
                if testGridSquare.gridElement is not None:
                    return False
                else:
                    testGridSquare.gridElement = gridElement
                    if not gridElement.isDecoration:
                        self.lastActivityIdPlaced = gridElement.id

        return

    def removeElement(self, centerGridSquare, size):
        xOffsetLow, xOffsetHigh, yOffset = self.getXYOffsets(size)
        for y in range(int(centerGridSquare.y - size[1] / 2), int(centerGridSquare.y + size[1] / 2) + yOffset):
            for x in range(int(centerGridSquare.x - size[0] / 2) + xOffsetLow, int(centerGridSquare.x + size[0] / 2) + xOffsetHigh):
                testGridSquare = self.getGridSquare(x, y)
                if testGridSquare is None:
                    return False
                if testGridSquare.gridElement is None:
                    return False
                else:
                    testGridSquare.gridElement = None

        return

    def destroy(self):
        self.partyEditor = None
        for y in range(len(self.grid)):
            for x in range(len(self.grid[0])):
                if self.grid[y][x]:
                    self.grid[y][x].destroy()

        del self.grid
        return
