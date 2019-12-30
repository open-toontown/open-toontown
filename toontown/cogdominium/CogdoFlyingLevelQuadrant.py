import math
from direct.directutil import Mopath
from pandac.PandaModules import NodePath, Point3, Vec4
from .CogdoFlyingObjects import CogdoFlyingPlatform
from . import CogdoFlyingGameGlobals as Globals

class CogdoFlyingLevelQuadrant:
    notify = directNotify.newCategory('CogdoFlyingLevelQuadrant')

    def __init__(self, serialNum, model, level, parent):
        self.serialNum = serialNum
        self._model = model
        self._level = level
        self._root = NodePath('Quadrant' + repr(serialNum))
        self._model.reparentTo(self._root)
        self._root.reparentTo(parent)
        self._visible = True
        self.platforms = {}
        self.gatherables = []
        self.obstacles = []
        self._playing = False
        self._obstaclesRoot = NodePath('obstacles')
        self._obstaclesRoot.reparentTo(self._root)
        self._initObstacles(self._obstaclesRoot)
        self._gatherablesRoot = NodePath('gatherables')
        self._gatherablesRoot.reparentTo(self._root)
        self._initGatherables(self._gatherablesRoot)
        self._platformsRoot = NodePath('platforms')
        self._platformsRoot.reparentTo(self._model)
        self._initPlatforms(self._platformsRoot)
        self._optimize()
        self.place()

    def _optimize(self):
        lightCones = NodePath('lightCones')
        for np in self._platformsRoot.findAllMatches('**/*lightCone*'):
            np.wrtReparentTo(lightCones)

        lightCones.reparentTo(self._model)
        node = self._model.find('**/ducts')
        if not node.isEmpty():
            node.flattenStrong()
            for np in node.getChildren():
                np.wrtReparentTo(self._model)

        node = self._model.find('**/nests')
        if not node.isEmpty():
            for np in node.getChildren():
                np.flattenStrong()
                np.wrtReparentTo(self._model)

        for np in self._model.findAllMatches('**/*LayerStack*'):
            np.wrtReparentTo(self._model)

        for np in self._model.find('**/static').getChildren():
            np.wrtReparentTo(self._model)

        self._model.flattenMedium()

    def _initPlatforms(self, parent):
        platformModels = self._model.findAllMatches('**/%s' % Globals.Level.PlatformName)
        for platformModel in platformModels:
            platform = CogdoFlyingPlatform(platformModel, parent=parent)
            self.platforms[platform.getName()] = platform

    def _destroyPlatforms(self):
        for platform in list(self.platforms.values()):
            platform.destroy()

        del self.platforms

    def _initGatherables(self, parent):
        self.generateGatherables(self._model, parent=parent)
        if Globals.Level.SpawnLaffPowerupsInNests:
            self.generateNestPowerups(self._model, parent=parent)

    def generateNestPowerups(self, gatherableModel, parent):
        nests = gatherableModel.findAllMatches('**/%s;+s' % Globals.Level.LegalEagleNestName)
        for nest in nests:
            offset = Globals.Level.LaffPowerupNestOffset
            pickup = self._level.gatherableFactory.createPowerup(Globals.Level.GatherableTypes.LaffPowerup)
            pickup.reparentTo(parent)
            pickup.setPos(parent, nest.getPos(parent) + offset)
            if Globals.Level.AddSparkleToPowerups:
                sparkles = self._level.gatherableFactory.createSparkles(Vec4(1, 1, 1, 1), Vec4(1, 1, 0, 1), 10.0)
                sparkles.reparentTo(pickup)
                sparkles.setPos(0, 0, 1)
                sparkles.start()
            self.gatherables.append(pickup)

    def generateGatherables(self, gatherableModel, parent = None, spread = Globals.Level.GatherablesDefaultSpread):
        parent = parent or self._root
        mopath = Mopath.Mopath(name='gatherables')

        def generateMemos():
            gatherPaths = gatherableModel.findAllMatches('**/%s' % Globals.Level.GatherablesPathName)
            for gatherPath in gatherPaths:
                mopath.loadNodePath(gatherPath)
                t = 0.0
                while t < mopath.getMaxT():
                    pickup = self._level.gatherableFactory.createMemo()
                    pickup.reparentTo(parent)
                    mopath.goTo(pickup, t)
                    self.gatherables.append(pickup)
                    t += spread

                gatherPath.removeNode()

            angleSpread = 360.0 / Globals.Level.NumMemosInRing
            gatherPaths = gatherableModel.findAllMatches('**/%s' % Globals.Level.GatherablesRingName)
            for gatherPath in gatherPaths:
                mopath.loadNodePath(gatherPath)
                t = 0.0
                while t < mopath.getMaxT():
                    angle = 0
                    r = 3
                    while angle < 360.0:
                        pickup = self._level.gatherableFactory.createMemo()
                        pickup.reparentTo(parent)
                        mopath.goTo(pickup, t)
                        pickup.setX(parent, pickup.getX() + r * math.cos(math.radians(angle)))
                        pickup.setZ(parent, pickup.getZ() + r * math.sin(math.radians(angle)))
                        self.gatherables.append(pickup)
                        angle += angleSpread

                    t += spread + 0.5

                gatherPath.removeNode()

        def generatePropellers():
            gatherables = gatherableModel.findAllMatches('**/%s' % Globals.Level.PropellerName)
            for gatherable in gatherables:
                pickup = self._level.gatherableFactory.createPropeller()
                pickup.reparentTo(gatherable.getParent())
                pickup.setPos(parent, gatherable.getPos(parent))
                self.gatherables.append(pickup)
                gatherable.removeNode()

        def generatePowerUps():
            for powerupType, locName in Globals.Level.PowerupType2Loc.items():
                if powerupType == Globals.Level.GatherableTypes.LaffPowerup and Globals.Level.IgnoreLaffPowerups:
                    continue
                gatherables = gatherableModel.findAllMatches('**/%s' % locName)
                for gatherable in gatherables:
                    pickup = self._level.gatherableFactory.createPowerup(powerupType)
                    pickup.reparentTo(parent)
                    pickup.setPos(parent, gatherable.getPos(parent))
                    if Globals.Level.AddSparkleToPowerups:
                        sparkles = self._level.gatherableFactory.createSparkles(Vec4(1, 1, 1, 1), Vec4(1, 1, 0, 1), 10.0)
                        sparkles.reparentTo(pickup)
                        sparkles.setPos(0, 0, 1)
                        sparkles.start()
                    self.gatherables.append(pickup)
                    gatherable.removeNode()

        generateMemos()
        generatePropellers()
        generatePowerUps()

    def _initObstacles(self, parent):

        def initWhirlwinds():
            obstacles = self._root.findAllMatches('**/%s' % Globals.Level.WhirlwindName)
            for obstacleLoc in obstacles:
                motionPath = self._model.find('**/%s%s' % (obstacleLoc.getName(), Globals.Level.WhirlwindPathName))
                if motionPath.isEmpty():
                    motionPath = None
                obstacle = self._level.obstacleFactory.createWhirlwind(motionPath=motionPath)
                obstacle.model.reparentTo(parent)
                obstacle.model.setPos(parent, obstacleLoc.getPos(parent))
                self.obstacles.append(obstacle)
                obstacleLoc.removeNode()

            return

        def initStreamers():
            obstacles = self._model.findAllMatches('**/%s' % Globals.Level.StreamerName)
            for obstacleLoc in obstacles:
                obstacle = self._level.obstacleFactory.createFan()
                obstacle.model.reparentTo(parent)
                obstacle.model.setPos(parent, obstacleLoc.getPos(parent))
                obstacle.model.setHpr(parent, obstacleLoc.getHpr(parent))
                obstacle.model.setScale(parent, obstacleLoc.getScale(parent))
                obstacle.setBlowDirection()
                if Globals.Level.AddParticlesToStreamers:
                    particles = self._level.obstacleFactory.createStreamerParticles(Vec4(1, 1, 1, 1), Vec4(1, 1, 1, 1), 10.0)
                    particles.reparentTo(obstacle.model)
                    particles.start()
                self.obstacles.append(obstacle)
                obstacleLoc.removeNode()

        def initWalkingMinions():
            motionPaths = self._model.findAllMatches('**/%s' % Globals.Level.MinionWalkingPathName)
            for motionPath in motionPaths:
                obstacle = self._level.obstacleFactory.createWalkingMinion(motionPath=motionPath)
                obstacle.model.reparentTo(parent)
                obstacle.model.setPos(parent, motionPath.getPos(parent))
                self.obstacles.append(obstacle)

        def initFlyingMinions():
            motionPaths = self._model.findAllMatches('**/%s' % Globals.Level.MinionFlyingPathName)
            for motionPath in motionPaths:
                obstacle = self._level.obstacleFactory.createFlyingMinion(motionPath=motionPath)
                obstacle.model.reparentTo(parent)
                obstacle.model.setPos(parent, motionPath.getPos(parent))
                self.obstacles.append(obstacle)

        initWhirlwinds()
        initStreamers()
        initWalkingMinions()
        initFlyingMinions()

    def place(self):
        self._root.setPos(0, self._level.convertQuadNumToY(self.serialNum), 0)

    def destroy(self):
        if self._visible:
            self.offstage()
        self._destroyPlatforms()
        for obstacle in self.obstacles:
            obstacle.destroy()

        for gatherable in self.gatherables:
            gatherable.destroy()

        self._root.removeNode()
        del self._root
        del self._gatherablesRoot
        del self._obstaclesRoot
        del self._platformsRoot
        del self._level

    def onstage(self, elapsedTime = 0.0):
        if self._visible:
            return
        self._root.unstash()
        for obstacle in self.obstacles:
            obstacle.startMoving(elapsedTime)

        for gatherable in self.gatherables:
            gatherable.show()

        self._visible = True

    def offstage(self):
        if not self._visible:
            return
        self._root.stash()
        for obstacle in self.obstacles:
            obstacle.stopMoving()

        for gatherable in self.gatherables:
            gatherable.hide()

        self._visible = False

    def update(self, dt):
        if self._visible:
            for gatherable in self.gatherables:
                gatherable.update(dt)

            for obstacle in self.obstacles:
                obstacle.update(dt)

    def getModel(self):
        return self._root
