from pandac.PandaModules import VBase3
from direct.showbase.RandomNumGen import RandomNumGen

class MazeBase:

    def __init__(self, model, mazeData, cellWidth, parent = None):
        if parent is None:
            parent = render
        self.width = mazeData['width']
        self.height = mazeData['height']
        self.originTX = mazeData['originX']
        self.originTY = mazeData['originY']
        self.collisionTable = mazeData['collisionTable']
        self._initialCellWidth = cellWidth
        self.cellWidth = self._initialCellWidth
        self.maze = model
        self.maze.setPos(0, 0, 0)
        self.maze.reparentTo(parent)
        self.maze.stash()
        return

    def destroy(self):
        self.maze.removeNode()
        del self.maze

    def onstage(self):
        self.maze.unstash()

    def offstage(self):
        self.maze.stash()

    def setScale(self, xy = 1, z = 1):
        self.maze.setScale(VBase3(xy, xy, z))
        self.cellWidth = self._initialCellWidth * xy

    def isWalkable(self, tX, tY, rejectList = ()):
        if tX <= 0 or tY <= 0 or tX >= self.width or tY >= self.height:
            return 0
        return not self.collisionTable[tY][tX] and not self.collisionTable[tY - 1][tX] and not self.collisionTable[tY][tX - 1] and not self.collisionTable[tY - 1][tX - 1] and (tX, tY) not in rejectList

    def tile2world(self, TX, TY):
        return [(TX - self.originTX) * self.cellWidth, (TY - self.originTY) * self.cellWidth]

    def world2tile(self, x, y):
        return [int(x / self.cellWidth + self.originTX), int(y / self.cellWidth + self.originTY)]

    def world2tileClipped(self, x, y):
        coords = [int(x / self.cellWidth + self.originTX), int(y / self.cellWidth + self.originTY)]
        coords[0] = min(max(coords[0], 0), self.width - 1)
        coords[1] = min(max(coords[1], 0), self.height - 1)
        return coords

    def doOrthoCollisions(self, oldPos, newPos):
        offset = newPos - oldPos
        WALL_OFFSET = 1.0
        curX = oldPos[0]
        curY = oldPos[1]
        curTX, curTY = self.world2tile(curX, curY)

        def calcFlushCoord(curTile, newTile, centerTile):
            EPSILON = 0.01
            if newTile > curTile:
                return (newTile - centerTile) * self.cellWidth - EPSILON - WALL_OFFSET
            else:
                return (curTile - centerTile) * self.cellWidth + WALL_OFFSET

        offsetX = offset[0]
        offsetY = offset[1]
        WALL_OFFSET_X = WALL_OFFSET
        if offsetX < 0:
            WALL_OFFSET_X = -WALL_OFFSET_X
        WALL_OFFSET_Y = WALL_OFFSET
        if offsetY < 0:
            WALL_OFFSET_Y = -WALL_OFFSET_Y
        newX = curX + offsetX + WALL_OFFSET_X
        newY = curY
        newTX, newTY = self.world2tile(newX, newY)
        if newTX != curTX:
            if self.collisionTable[newTY][newTX] == 1:
                offset.setX(calcFlushCoord(curTX, newTX, self.originTX) - curX)
        newX = curX
        newY = curY + offsetY + WALL_OFFSET_Y
        newTX, newTY = self.world2tile(newX, newY)
        if newTY != curTY:
            if self.collisionTable[newTY][newTX] == 1:
                offset.setY(calcFlushCoord(curTY, newTY, self.originTY) - curY)
        offsetX = offset[0]
        offsetY = offset[1]
        newX = curX + offsetX + WALL_OFFSET_X
        newY = curY + offsetY + WALL_OFFSET_Y
        newTX, newTY = self.world2tile(newX, newY)
        if self.collisionTable[newTY][newTX] == 1:
            cX = calcFlushCoord(curTX, newTX, self.originTX)
            cY = calcFlushCoord(curTY, newTY, self.originTY)
            if abs(cX - curX) < abs(cY - curY):
                offset.setX(cX - curX)
            else:
                offset.setY(cY - curY)
        return oldPos + offset

    def createRandomSpotsList(self, numSpots, randomNumGen):
        randomNumGen = RandomNumGen(randomNumGen)
        width = self.width
        height = self.height
        halfWidth = int(width / 2)
        halfHeight = int(height / 2)
        quadrants = [(0,
          0,
          halfWidth - 1,
          halfHeight - 1),
         (halfWidth,
          0,
          width - 1,
          halfHeight - 1),
         (0,
          halfHeight,
          halfWidth - 1,
          height - 1),
         (halfWidth,
          halfHeight,
          width - 1,
          height - 1)]
        spotsTaken = []

        def getEmptySpotInQuadrant(quadrant):
            tX = -1
            tY = -1
            while tX < 0 or not self.isWalkable(tX, tY, spotsTaken):
                tX = randomNumGen.randint(quadrant[0], quadrant[2])
                tY = randomNumGen.randint(quadrant[1], quadrant[3])

            spot = (tX, tY)
            spotsTaken.append(spot)
            return spot

        def getSpotList(length):
            randomNumGen.shuffle(quadrants)
            l = []
            remaining = length
            for quadrant in quadrants:
                for u in range(int(length / 4)):
                    l.append(getEmptySpotInQuadrant(quadrant))

                remaining -= int(length / 4)

            for u in range(remaining):
                quadrant = quadrants[randomNumGen.randint(0, len(quadrants) - 1)]
                l.append(getEmptySpotInQuadrant(quadrant))

            return l

        if type(numSpots) == tuple or type(numSpots) == list:
            spots = []
            for i in numSpots:
                spots.append(getSpotList(i))

            return spots
        return getSpotList(numSpots)
