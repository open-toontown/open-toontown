from pandac.PandaModules import NodePath, VBase4
from direct.showbase.DirectObject import DirectObject
from direct.showbase.RandomNumGen import RandomNumGen
from toontown.minigame.MazeBase import MazeBase
from . import CogdoMazeGameGlobals as Globals
from .CogdoMazeGameObjects import CogdoMazeWaterCooler
from . import CogdoMazeData
from . import CogdoUtil

class CogdoMaze(MazeBase, DirectObject):

    def __init__(self, model, data, cellWidth):
        MazeBase.__init__(self, model, data, cellWidth)
        self._initWaterCoolers()
        self.elevatorPos = self.maze.find('**/elevator_loc').getPos(render)
        self.exitPos = self.maze.find('**/exit_loc').getPos(render)
        self.maze.flattenStrong()
        self._clearColor = VBase4(base.win.getClearColor())
        self._clearColor.setW(1.0)
        base.win.setClearColor(VBase4(0.0, 0.0, 0.0, 1.0))
        if __debug__ and base.config.GetBool('cogdomaze-dev', False):
            self._initCollisionVisuals()

    def _initWaterCoolers(self):
        self._waterCoolers = []
        self._waterCoolerRoot = NodePath('WaterCoolerRoot')
        self._waterCoolerRoot.reparentTo(render)
        models = []
        for model in self.maze.findAllMatches('**/*waterCooler'):
            model.wrtReparentTo(render)
            models.append((model.getPos(self.maze), model.getHpr(self.maze), model))

        models.sort()
        i = 0
        for pos, hpr, model in models:
            wc = CogdoMazeWaterCooler(i, model)
            wc.wrtReparentTo(self._waterCoolerRoot)
            wc.setPos(pos)
            wc.setHpr(hpr)
            self._waterCoolers.append(wc)
            i += 1

        self._waterCoolerRoot.stash()

    def getWaterCoolers(self):
        return self._waterCoolers

    def isAccessible(self, tX, tY):
        if tX < 0 or tY < 0 or tX >= self.width or tY >= self.height:
            return 0
        return self.collisionTable[tY][tX] != 1

    def destroy(self):
        for waterCooler in self._waterCoolers:
            waterCooler.destroy()

        del self._waterCoolers
        self._waterCoolerRoot.removeNode()
        del self._waterCoolerRoot
        base.win.setClearColor(self._clearColor)
        del self._clearColor
        MazeBase.destroy(self)
        if __debug__ and hasattr(self, '_cubes'):
            self.ignoreAll()
            self._cubes.removeNode()
            del self._cubes

    def onstage(self):
        MazeBase.onstage(self)
        self._waterCoolerRoot.unstash()

    def offstage(self):
        self._waterCoolerRoot.stash()
        MazeBase.offstage(self)


BARRIER_DATA_RIGHT = 1
BARRIER_DATA_TOP = 1

class CogdoMazeFactory:

    def __init__(self, randomNumGen, width, height, frameWallThickness = Globals.FrameWallThickness, cogdoMazeData = CogdoMazeData):
        self._rng = RandomNumGen(randomNumGen)
        self.width = width
        self.height = height
        self.frameWallThickness = frameWallThickness
        self._cogdoMazeData = cogdoMazeData
        self.quadrantSize = self._cogdoMazeData.QuadrantSize
        self.cellWidth = self._cogdoMazeData.QuadrantCellWidth

    def getMazeData(self):
        if not hasattr(self, '_data'):
            self._generateMazeData()
        return self._data

    def createCogdoMaze(self, flattenModel = True):
        if not hasattr(self, '_maze'):
            self._loadAndBuildMazeModel(flatten=flattenModel)
        return CogdoMaze(self._model, self._data, self.cellWidth)

    def _gatherQuadrantData(self):
        self.openBarriers = []
        barrierItems = list(range(Globals.TotalBarriers))
        self._rng.shuffle(barrierItems)
        for i in barrierItems[0:len(barrierItems) - Globals.NumBarriers]:
            self.openBarriers.append(i)

        self.quadrantData = []
        quadrantKeys = list(self._cogdoMazeData.QuadrantCollisions.keys())
        self._rng.shuffle(quadrantKeys)
        i = 0
        for y in range(self.height):
            for x in range(self.width):
                key = quadrantKeys[i]
                collTable = self._cogdoMazeData.QuadrantCollisions[key]
                angle = self._cogdoMazeData.QuadrantAngles[self._rng.randint(0, len(self._cogdoMazeData.QuadrantAngles) - 1)]
                self.quadrantData.append((key, collTable[angle], angle))
                i += 1
                if x * y >= self._cogdoMazeData.NumQuadrants:
                    i = 0

    def _generateBarrierData(self):
        data = []
        for y in range(self.height):
            data.append([])
            for x in range(self.width):
                if x == self.width - 1:
                    ax = -1
                else:
                    ax = 1
                if y == self.height - 1:
                    ay = -1
                else:
                    ay = 1
                data[y].append([ax, ay])

        dirUp = 0
        dirDown = 1
        dirLeft = 2
        dirRight = 3

        def getAvailableDirections(ax, ay, ignore = None):
            dirs = []
            if ax - 1 >= 0 and data[ay][ax - 1][BARRIER_DATA_RIGHT] == 1 and (ax, ay) != ignore:
                dirs.append(dirLeft)
            if ax + 1 < self.width and data[ay][ax][BARRIER_DATA_RIGHT] == 1 and (ax, ay) != ignore:
                dirs.append(dirRight)
            if ay - 1 >= 0 and data[ay - 1][ax][BARRIER_DATA_TOP] == 1 and (ax, ay) != ignore:
                dirs.append(dirDown)
            if ay + 1 < self.height and data[ay][ax][BARRIER_DATA_TOP] == 1 and (ax, ay) != ignore:
                dirs.append(dirUp)
            return dirs

        visited = []

        def tryVisitNeighbor(ax, ay, ad):
            if ad == dirUp:
                if data[ay][ax] in visited:
                    return None
                visited.append(data[ay][ax])
                data[ay][ax][BARRIER_DATA_TOP] = 0
                ay += 1
            elif ad == dirDown:
                if data[ay - 1][ax] in visited:
                    return None
                visited.append(data[ay - 1][ax])
                data[ay - 1][ax][BARRIER_DATA_TOP] = 0
                ay -= 1
            elif ad == dirLeft:
                if data[ay][ax - 1] in visited:
                    return None
                visited.append(data[ay][ax - 1])
                data[ay][ax - 1][BARRIER_DATA_RIGHT] = 0
                ax -= 1
            elif ad == dirRight:
                if data[ay][ax] in visited:
                    return None
                visited.append(data[ay][ax])
                data[ay][ax][BARRIER_DATA_RIGHT] = 0
                ax += 1
            return (ax, ay)

        def openBarriers(x, y):
            dirs = getAvailableDirections(x, y)
            for dir in dirs:
                next = tryVisitNeighbor(x, y, dir)
                if next is not None:
                    openBarriers(*next)

            return

        x = self._rng.randint(0, self.width - 1)
        y = self._rng.randint(0, self.height - 1)
        openBarriers(x, y)
        self._barrierData = data
        return

    def _generateMazeData(self):
        if not hasattr(self, 'quadrantData'):
            self._gatherQuadrantData()
        self._data = {}
        self._data['width'] = (self.width + 1) * self.frameWallThickness + self.width * self.quadrantSize
        self._data['height'] = (self.height + 1) * self.frameWallThickness + self.height * self.quadrantSize
        self._data['originX'] = int(self._data['width'] / 2)
        self._data['originY'] = int(self._data['height'] / 2)
        collisionTable = []
        horizontalWall = [ 1 for x in range(self._data['width']) ]
        collisionTable.append(horizontalWall)
        for i in range(0, len(self.quadrantData), self.width):
            for y in range(self.quadrantSize):
                row = [1]
                for x in range(i, i + self.width):
                    if x == 1 and y < self.quadrantSize / 2 - 2:
                        newData = []
                        for j in self.quadrantData[x][1][y]:
                            if j == 0:
                                newData.append(2)
                            else:
                                newData.append(j + 0)

                        row += newData + [1]
                    else:
                        row += self.quadrantData[x][1][y] + [1]

                collisionTable.append(row)

            collisionTable.append(horizontalWall[:])

        barriers = Globals.MazeBarriers
        for i in range(len(barriers)):
            for coords in barriers[i]:
                collisionTable[coords[1]][coords[0]] = 0

        y = self._data['originY']
        for x in range(len(collisionTable[y])):
            if collisionTable[y][x] == 0:
                collisionTable[y][x] = 2

        x = self._data['originX']
        for y in range(len(collisionTable)):
            if collisionTable[y][x] == 0:
                collisionTable[y][x] = 2

        self._data['collisionTable'] = collisionTable

    def _loadAndBuildMazeModel(self, flatten = False):
        self.getMazeData()
        self._model = NodePath('CogdoMazeModel')
        levelModel = CogdoUtil.loadMazeModel('level')
        self.quadrants = []
        quadrantUnitSize = int(self.quadrantSize * self.cellWidth)
        frameActualSize = self.frameWallThickness * self.cellWidth
        size = quadrantUnitSize + frameActualSize
        halfWidth = int(self.width / 2)
        halfHeight = int(self.height / 2)
        i = 0
        for y in range(self.height):
            for x in range(self.width):
                ax = (x - halfWidth) * size
                ay = (y - halfHeight) * size
                extension = ''
                if hasattr(getBase(), 'air'):
                    extension = '.bam'
                filepath = self.quadrantData[i][0] + extension
                angle = self.quadrantData[i][2]
                m = self._createQuadrant(filepath, i, angle, quadrantUnitSize)
                m.setPos(ax, ay, 0)
                m.reparentTo(self._model)
                self.quadrants.append(m)
                i += 1

        quadrantHalfUnitSize = quadrantUnitSize * 0.5
        barrierModel = CogdoUtil.loadMazeModel('grouping_blockerDivider').find('**/divider')
        y = 3
        for x in range(self.width):
            if x == (self.width - 1) / 2:
                continue
            ax = (x - halfWidth) * size
            ay = (y - halfHeight) * size - quadrantHalfUnitSize - (self.cellWidth - 0.5)
            b = NodePath('barrier')
            barrierModel.instanceTo(b)
            b.setPos(ax, ay, 0)
            b.reparentTo(self._model)

        offset = self.cellWidth - 0.5
        for x in (0, 3):
            for y in range(self.height):
                ax = (x - halfWidth) * size - quadrantHalfUnitSize - frameActualSize + offset
                ay = (y - halfHeight) * size
                b = NodePath('barrier')
                barrierModel.instanceTo(b)
                b.setPos(ax, ay, 0)
                b.setH(90)
                b.reparentTo(self._model)

            offset -= 2.0

        barrierModel.removeNode()
        levelModel.getChildren().reparentTo(self._model)
        for np in self._model.findAllMatches('**/*lightCone*'):
            CogdoUtil.initializeLightCone(np, 'fixed', 3)

        if flatten:
            self._model.flattenStrong()
        return self._model

    def _createQuadrant(self, filepath, serialNum, angle, size):
        root = NodePath('QuadrantRoot-%i' % serialNum)
        quadrant = loader.loadModel(filepath)
        quadrant.getChildren().reparentTo(root)
        root.setH(angle)
        return root
