from pandac.PandaModules import Vec4, BitMask32, Quat, Point3, NodePath
from pandac.PandaModules import OdePlaneGeom, OdeBody, OdeSphereGeom, OdeMass, OdeUtil, OdeBoxGeom
from direct.directnotify import DirectNotifyGlobal
from toontown.minigame import DistributedMinigamePhysicsWorld
from toontown.minigame import IceGameGlobals
from toontown.golf import BuildGeometry
MetersToFeet = 3.2808399
FeetToMeters = 1.0 / MetersToFeet

class DistributedIceWorld(DistributedMinigamePhysicsWorld.DistributedMinigamePhysicsWorld):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedMinigamePhysicsWorld')
    floorCollideId = 1
    floorMask = BitMask32(floorCollideId)
    wallCollideId = 1 << 1
    wallMask = BitMask32(wallCollideId)
    obstacleCollideId = 1 << 2
    obstacleMask = BitMask32(obstacleCollideId)
    tireCollideIds = [1 << 8,
     1 << 9,
     1 << 10,
     1 << 11]
    tire0Mask = BitMask32(tireCollideIds[0])
    tire1Mask = BitMask32(tireCollideIds[1])
    tire2Mask = BitMask32(tireCollideIds[2])
    tire3Mask = BitMask32(tireCollideIds[3])
    allTiresMask = tire0Mask | tire1Mask | tire2Mask | tire3Mask
    tireMasks = (tire0Mask,
     tire1Mask,
     tire2Mask,
     tire3Mask)
    tireDensity = 1
    tireSurfaceType = 0
    iceSurfaceType = 1
    fenceSurfaceType = 2

    def __init__(self, cr):
        DistributedMinigamePhysicsWorld.DistributedMinigamePhysicsWorld.__init__(self, cr)

    def delete(self):
        DistributedMinigamePhysicsWorld.DistributedMinigamePhysicsWorld.delete(self)
        if hasattr(self, 'floor'):
            self.floor = None
        return

    def setupSimulation(self):
        DistributedMinigamePhysicsWorld.DistributedMinigamePhysicsWorld.setupSimulation(self)
        self.world.setGravity(0, 0, -32.174)
        self.world.setAutoDisableFlag(1)
        self.world.setAutoDisableLinearThreshold(0.5 * MetersToFeet)
        self.world.setAutoDisableAngularThreshold(OdeUtil.getInfinity())
        self.world.setAutoDisableSteps(10)
        self.world.setCfm(1e-05 * MetersToFeet)
        self.world.initSurfaceTable(3)
        self.world.setSurfaceEntry(0, 1, 0.2, 0, 0, 0, 0, 0, 0.1)
        self.world.setSurfaceEntry(0, 0, 0.1, 0.9, 0.1, 0, 0, 0, 0)
        self.world.setSurfaceEntry(0, 2, 0.9, 0.9, 0.1, 0, 0, 0, 0)
        self.floor = OdePlaneGeom(self.space, Vec4(0.0, 0.0, 1.0, -20.0))
        self.floor.setCollideBits(self.allTiresMask)
        self.floor.setCategoryBits(self.floorMask)
        self.westWall = OdePlaneGeom(self.space, Vec4(1.0, 0.0, 0.0, IceGameGlobals.MinWall[0]))
        self.westWall.setCollideBits(self.allTiresMask)
        self.westWall.setCategoryBits(self.wallMask)
        self.space.setSurfaceType(self.westWall, self.fenceSurfaceType)
        self.space.setCollideId(self.westWall, self.wallCollideId)
        self.eastWall = OdePlaneGeom(self.space, Vec4(-1.0, 0.0, 0.0, -IceGameGlobals.MaxWall[0]))
        self.eastWall.setCollideBits(self.allTiresMask)
        self.eastWall.setCategoryBits(self.wallMask)
        self.space.setSurfaceType(self.eastWall, self.fenceSurfaceType)
        self.space.setCollideId(self.eastWall, self.wallCollideId)
        self.southWall = OdePlaneGeom(self.space, Vec4(0.0, 1.0, 0.0, IceGameGlobals.MinWall[1]))
        self.southWall.setCollideBits(self.allTiresMask)
        self.southWall.setCategoryBits(self.wallMask)
        self.space.setSurfaceType(self.southWall, self.fenceSurfaceType)
        self.space.setCollideId(self.southWall, self.wallCollideId)
        self.northWall = OdePlaneGeom(self.space, Vec4(0.0, -1.0, 0.0, -IceGameGlobals.MaxWall[1]))
        self.northWall.setCollideBits(self.allTiresMask)
        self.northWall.setCategoryBits(self.wallMask)
        self.space.setSurfaceType(self.northWall, self.fenceSurfaceType)
        self.space.setCollideId(self.northWall, self.wallCollideId)
        self.floorTemp = OdePlaneGeom(self.space, Vec4(0.0, 0.0, 1.0, 0.0))
        self.floorTemp.setCollideBits(self.allTiresMask)
        self.floorTemp.setCategoryBits(self.floorMask)
        self.space.setSurfaceType(self.floorTemp, self.iceSurfaceType)
        self.space.setCollideId(self.floorTemp, self.floorCollideId)
        self.space.setAutoCollideWorld(self.world)
        self.space.setAutoCollideJointGroup(self.contactgroup)
        self.totalPhysicsSteps = 0

    def createTire(self, tireIndex):
        if tireIndex < 0 or tireIndex >= len(self.tireMasks):
            self.notify.error('invalid tireIndex %s' % tireIndex)
        self.notify.debug('create tireindex %s' % tireIndex)
        zOffset = 0
        body = OdeBody(self.world)
        mass = OdeMass()
        mass.setSphere(self.tireDensity, IceGameGlobals.TireRadius)
        body.setMass(mass)
        body.setPosition(IceGameGlobals.StartingPositions[tireIndex][0], IceGameGlobals.StartingPositions[tireIndex][1], IceGameGlobals.StartingPositions[tireIndex][2])
        body.setAutoDisableDefaults()
        geom = OdeSphereGeom(self.space, IceGameGlobals.TireRadius)
        self.space.setSurfaceType(geom, self.tireSurfaceType)
        self.space.setCollideId(geom, self.tireCollideIds[tireIndex])
        self.massList.append(mass)
        self.geomList.append(geom)
        geom.setCollideBits(self.allTiresMask | self.wallMask | self.floorMask | self.obstacleMask)
        geom.setCategoryBits(self.tireMasks[tireIndex])
        geom.setBody(body)
        if self.notify.getDebug():
            self.notify.debug('tire geom id')
            geom.write()
            self.notify.debug(' -')
        if self.canRender:
            testTire = render.attachNewNode('tire holder %d' % tireIndex)
            smileyModel = NodePath()
            if not smileyModel.isEmpty():
                smileyModel.setScale(IceGameGlobals.TireRadius)
                smileyModel.reparentTo(testTire)
                smileyModel.setAlphaScale(0.5)
                smileyModel.setTransparency(1)
            testTire.setPos(IceGameGlobals.StartingPositions[tireIndex])
            tireModel = loader.loadModel('phase_4/models/minigames/ice_game_tire')
            tireHeight = 1
            tireModel.setZ(-IceGameGlobals.TireRadius + 0.01)
            tireModel.reparentTo(testTire)
            self.odePandaRelationList.append((testTire, body))
        else:
            testTire = None
            self.bodyList.append((None, body))
        return (testTire, body, geom)

    def placeBodies(self):
        for pair in self.odePandaRelationList:
            pandaNodePathGeom = pair[0]
            odeBody = pair[1]
            if pandaNodePathGeom:
                pandaNodePathGeom.setPos(odeBody.getPosition())
                pandaNodePathGeom.setQuat(Quat(odeBody.getQuaternion()[0], odeBody.getQuaternion()[1], odeBody.getQuaternion()[2], odeBody.getQuaternion()[3]))
                pandaNodePathGeom.setP(0)
                pandaNodePathGeom.setR(0)
                newQuat = pandaNodePathGeom.getQuat()
                odeBody.setQuaternion(newQuat)

    def postStep(self):
        DistributedMinigamePhysicsWorld.DistributedMinigamePhysicsWorld.postStep(self)
        self.placeBodies()
        self.totalPhysicsSteps += 1

    def createObstacle(self, pos, obstacleIndex, cubicObstacle):
        if cubicObstacle:
            return self.createCubicObstacle(pos, obstacleIndex)
        else:
            return self.createCircularObstacle(pos, obstacleIndex)

    def createCircularObstacle(self, pos, obstacleIndex):
        self.notify.debug('create obstacleindex %s' % obstacleIndex)
        geom = OdeSphereGeom(self.space, IceGameGlobals.TireRadius)
        geom.setCollideBits(self.allTiresMask)
        geom.setCategoryBits(self.obstacleMask)
        self.space.setCollideId(geom, self.obstacleCollideId)
        tireModel = loader.loadModel('phase_4/models/minigames/ice_game_tirestack')
        tireHeight = 1
        tireModel.setPos(pos)
        tireModel.reparentTo(render)
        geom.setPosition(tireModel.getPos())
        tireModel.setZ(0)
        return tireModel

    def createCubicObstacle(self, pos, obstacleIndex):
        self.notify.debug('create obstacleindex %s' % obstacleIndex)
        sideLength = IceGameGlobals.TireRadius * 2
        geom = OdeBoxGeom(self.space, sideLength, sideLength, sideLength)
        geom.setCollideBits(self.allTiresMask)
        geom.setCategoryBits(self.obstacleMask)
        self.space.setCollideId(geom, self.obstacleCollideId)
        tireModel = loader.loadModel('phase_4/models/minigames/ice_game_crate')
        tireModel.setPos(pos)
        tireModel.reparentTo(render)
        geom.setPosition(tireModel.getPos())
        tireModel.setZ(0)
        return tireModel
