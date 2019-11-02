from pandac.PandaModules import NodePath, Plane, Vec3, Point3
from pandac.PandaModules import CollisionPlane, CollisionNode
from direct.showbase.RandomNumGen import RandomNumGen
from direct.showbase.DirectObject import DirectObject
from direct.showbase.PythonUtil import bound as clamp
import CogdoUtil
import CogdoFlyingGameGlobals as Globals
from CogdoFlyingLevelQuadrant import CogdoFlyingLevelQuadrant
from CogdoFlyingObjects import CogdoFlyingGatherableFactory, CogdoFlyingPlatform, CogdoFlyingLevelFog
from CogdoFlyingObstacles import CogdoFlyingObtacleFactory
from CogdoGameExit import CogdoGameExit
from otp.otpbase import OTPGlobals

class CogdoFlyingLevel(DirectObject):
    notify = directNotify.newCategory('CogdoFlyingLevel')

    def __init__(self, parent, frameModel, startPlatformModel, endPlatformModel, quadLengthUnits, quadVisibilityAhead, quadVisibiltyBehind):
        self.parent = parent
        self.quadLengthUnits = quadLengthUnits
        self._halfQuadLengthUnits = quadLengthUnits / 2.0
        self.quadVisibiltyAhead = quadVisibilityAhead
        self.quadVisibiltyBehind = quadVisibiltyBehind
        self._frameModel = frameModel
        self.root = NodePath('CogdoFlyingLevel')
        self.quadrantRoot = NodePath('QuadrantsRoot')
        self.quadrantRoot.reparentTo(self.root)
        self._startPlatformModel = startPlatformModel
        self._startPlatformModel.reparentTo(self.root)
        self._startPlatformModel.setZ(Globals.Level.StartPlatformHeight)
        self._endPlatformModel = endPlatformModel
        self._endPlatformModel.reparentTo(self.root)
        self._endPlatformModel.setZ(Globals.Level.EndPlatformHeight)
        self.wallR = self._frameModel.find('**/wallR')
        self.wallL = self._frameModel.find('**/wallL')
        self._exit = CogdoGameExit()
        self._exit.reparentTo(self._endPlatformModel)
        loc = self._endPlatformModel.find('**/exit_loc')
        offset = loc.getPos(render)
        self._exit.setPos(render, offset)
        self.quadrants = []
        self.visibleQuadIndices = []
        self._numQuads = 0
        self._currentQuadNum = -1
        self._camera = None
        self._initCollisions()
        self.upLimit = self._frameModel.find('**/limit_up').getZ(render)
        self.downLimit = self._frameModel.find('**/limit_down').getZ(render)
        self.leftLimit = self._frameModel.find('**/limit_left').getX(render) - 30.0
        self.rightLimit = self._frameModel.find('**/limit_right').getX(render) + 30.0
        self.backLimit = -self.quadLengthUnits
        self.forwardLimit = self.quadLengthUnits * 20
        self._frameModel.flattenStrong()
        self.gatherableFactory = CogdoFlyingGatherableFactory()
        self.obstacleFactory = CogdoFlyingObtacleFactory()
        return

    def getExit(self):
        return self._exit

    def getBounds(self):
        return ((self.leftLimit, self.rightLimit), (self.backLimit, self.forwardLimit), (self.downLimit, self.upLimit))

    def getGatherable(self, serialNum):
        for quadrant in self.quadrants:
            for gatherable in quadrant.gatherables:
                if gatherable.serialNum == serialNum:
                    return gatherable

        return None

    def ready(self):
        self.gatherableFactory.destroy()
        del self.gatherableFactory
        self.obstacleFactory.destroy()
        del self.obstacleFactory
        self._initStartEndPlatforms()
        self._frameModel.reparentTo(self.root)
        self.root.reparentTo(self.parent)
        self.root.stash()

    def _initStartEndPlatforms(self):
        self.startPlatform = CogdoFlyingPlatform(self._startPlatformModel, Globals.Level.PlatformTypes.StartPlatform)
        self.endPlatform = CogdoFlyingPlatform(self._endPlatformModel, Globals.Level.PlatformTypes.EndPlatform)
        self._endPlatformModel.setY(self.convertQuadNumToY(self._numQuads))
        self.backLimit = self._startPlatformModel.getY(render) - Globals.Level.StartPlatformLength * 0.7
        self.forwardLimit = self._endPlatformModel.getY(render) + Globals.Level.EndPlatformLength * 0.7

    def _initCollisions(self):
        self.collPlane = CollisionPlane(Plane(Vec3(0, 0, 1.0), Point3(0, 0, 10)))
        self.collPlane.setTangible(0)
        self.collNode = CollisionNode('fogPlane')
        self.collNode.setIntoCollideMask(OTPGlobals.FloorBitmask)
        self.collNode.addSolid(self.collPlane)
        self.collNodePath = self.root.attachNewNode(self.collNode)
        self.collNodePath.hide()

    def destroy(self):
        del self.collPlane
        self.collNodePath.removeNode()
        del self.collNodePath
        del self.collNode
        for quadrant in self.quadrants:
            quadrant.destroy()

        self._exit.destroy()
        del self._exit
        self.root.removeNode()
        del self.root

    def onstage(self):
        self.root.unstash()
        self.update(0.0)

    def offstage(self):
        self.root.stash()

    def start(self, startTime = 0.0):
        self._startTime = startTime

    def stop(self):
        pass

    def getLength(self):
        return self.quadLengthUnits * self.getNumQuadrants()

    def appendQuadrant(self, model):
        quadrant = CogdoFlyingLevelQuadrant(self._numQuads, model, self, self.root)
        if self._numQuads == 0:
            quadrant.generateGatherables(self._startPlatformModel)
        quadrant.offstage()
        self.quadrants.append(quadrant)
        self._numQuads = len(self.quadrants)

    def getNumQuadrants(self):
        return self._numQuads

    def setCamera(self, camera):
        self._camera = camera

    def getCameraActualQuadrant(self):
        camY = self._camera.getY(render)
        y = self.root.getY(render)
        return self.convertYToQuadNum(camY - y)

    def update(self, dt = 0.0):
        if self._camera is None:
            return
        quadNum = clamp(self.getCameraActualQuadrant(), 0, self._numQuads - 1)
        if quadNum < self._numQuads:
            self.quadrants[quadNum].update(dt)
            if quadNum + 1 < self._numQuads:
                self.quadrants[quadNum + 1].update(dt)
            if quadNum != self._currentQuadNum:
                self._switchToQuadrant(quadNum)
        return

    def _switchToQuadrant(self, quadNum):
        self.visibleQuadIndices = []
        if quadNum >= 0:
            if quadNum > 0:
                self.quadrants[max(quadNum - self.quadVisibiltyBehind, 0)].onstage()
            for i in range(quadNum, min(quadNum + self.quadVisibiltyAhead + 1, self._numQuads)):
                self.quadrants[i].onstage()
                self.visibleQuadIndices.append(i)
                if i == 0:
                    self.startPlatform.onstage()
                elif i == self._numQuads - 1:
                    self.endPlatform.onstage()

        self._currentQuadNum = quadNum
        for i in range(0, max(self._currentQuadNum - self.quadVisibiltyBehind, 0)) + range(min(self._currentQuadNum + self.quadVisibiltyAhead + 1, self._numQuads), self._numQuads):
            self.quadrants[i].offstage()
            if i == 0:
                self.startPlatform.offstage()
            elif i == self._numQuads - 1:
                self.endPlatform.offstage()

    def convertQuadNumToY(self, quadNum):
        return quadNum * self.quadLengthUnits

    def convertYToQuadNum(self, y):
        return int(y / self.quadLengthUnits)

    def convertCenterYToQuadNum(self, y):
        return self.convertYToQuadNum(y + self._halfQuadLengthUnits)


class CogdoFlyingLevelFactory:

    def __init__(self, parent, quadLengthUnits, quadVisibilityAhead, quadVisibiltyBehind, rng = None):
        self.parent = parent
        self.quadLengthUnits = quadLengthUnits
        self.quadVisibiltyAhead = quadVisibilityAhead
        self.quadVisibiltyBehind = quadVisibiltyBehind
        self._rng = rng or RandomNumGen(1)
        self._level = None
        return

    def loadAndBuildLevel(self, safezoneId):
        levelNode = NodePath('level')
        frameModel = CogdoUtil.loadFlyingModel('level')
        startPlatformModel = CogdoUtil.loadFlyingModel('levelStart')
        endPlatformModel = CogdoUtil.loadFlyingModel('levelEnd')
        for fan in frameModel.findAllMatches('**/*wallFan'):
            fan.flattenStrong()

        frameModel.find('**/fogOpaque').setBin('background', 1)
        frameModel.find('**/ceiling').setBin('background', 2)
        frameModel.find('**/fogTranslucent_bm').setBin('fixed', 1)
        frameModel.find('**/wallR').setBin('opaque', 2)
        frameModel.find('**/wallL').setBin('opaque', 2)
        frameModel.find('**/fogTranslucent_top').setBin('fixed', 2)
        frameModel.getChildren().reparentTo(levelNode)
        levelNode.hide()
        self._level = CogdoFlyingLevel(self.parent, levelNode, startPlatformModel, endPlatformModel, self.quadLengthUnits, self.quadVisibiltyAhead, self.quadVisibiltyBehind)
        if Globals.Dev.WantTempLevel:
            quads = Globals.Dev.DevQuadsOrder
        else:
            levelInfo = Globals.Level.DifficultyOrder[safezoneId]
            quads = []
            for difficulty in levelInfo:
                quadList = Globals.Level.QuadsByDifficulty[difficulty]
                quads.append(quadList[self._rng.randint(0, len(quadList) - 1)])

        for i in quads:
            filePath = CogdoUtil.getModelPath('quadrant%i' % i, 'flying')
            quadModel = loader.loadModel(filePath)
            for np in quadModel.findAllMatches('**/*lightCone*'):
                CogdoUtil.initializeLightCone(np, 'fixed', 3)

            self._level.appendQuadrant(quadModel)

        self._level.ready()

    def createLevel(self, safezoneId = 2000):
        if self._level is None:
            self.loadAndBuildLevel(safezoneId)
        return self._level

    def createLevelFog(self):
        if self._level is None:
            self.loadAndBuildLevel()
        return CogdoFlyingLevelFog(self._level)
