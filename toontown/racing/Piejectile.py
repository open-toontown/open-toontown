import math
import random
from direct.showbase.PythonUtil import *
from direct.showbase.DirectObject import DirectObject
from direct.task import Task
from pandac.PandaModules import *
from direct.fsm import FSM
from direct.distributed import DistributedSmoothNode
from otp.avatar import ShadowCaster
from otp.otpbase import OTPGlobals
from toontown.racing.FlyingGag import FlyingGag
from toontown.battle import MovieUtil

class Piejectile(DirectObject, FlyingGag):
    physicsCalculationsPerSecond = 60
    maxPhysicsDt = 1.0
    physicsDt = 1.0 / float(physicsCalculationsPerSecond)
    maxPhysicsFrames = maxPhysicsDt * physicsCalculationsPerSecond

    def __init__(self, sourceId, targetId, type, name):
        FlyingGag.__init__(self, 'flyingGag', base.race.pie)
        self.billboard = False
        self.race = base.race
        self.scale = 1
        self.imHitMult = 1
        self.wallCollideTrack = None
        self.curSpeed = 0
        self.acceleration = 0
        self.count = 0
        self.name = name
        self.physicsObj = None
        self.ownerId = sourceId
        self.targetId = targetId
        self.ownerAv = None
        self.ownerKart = None
        self.hasTarget = 0
        self.deleting = 0
        self.d2t = 0
        self.lastD2t = 0
        self.startTime = globalClock.getFrameTime()
        self.timeRatio = 0
        self.maxTime = 8
        self.rotH = randFloat(-360, 360)
        self.rotP = randFloat(-90, 90)
        self.rotR = randFloat(-90, 90)
        print('generating Pie %s' % self.name)
        self.ownerKart = base.cr.doId2do.get(base.race.kartMap.get(sourceId, None), None)
        if targetId != 0:
            self.targetKart = base.cr.doId2do.get(base.race.kartMap.get(targetId, None), None)
            self.hasTarget = 1
        if self.ownerId == localAvatar.doId:
            startPos = self.ownerKart.getPos(render)
        else:
            startPos = self.ownerKart.getPos(render)
        self.setPos(startPos[0], startPos[1], startPos[2])
        self.__setupCollisions()
        self.setupPhysics()
        self.__enableCollisions()
        self.forward = NodePath('forward')
        self.forward.setPos(0, 1, 0)
        self.splatTaskName = 'splatTask %s' % self.name
        if self.hasTarget:
            self.splatTask = taskMgr.doMethodLater(self.maxTime, self.splat, self.splatTaskName)
        else:
            self.splatTask = taskMgr.doMethodLater(self.maxTime / 2.5, self.splat, self.splatTaskName)
        self.reparentTo(render)
        return

    def delete(self):
        print('removing piejectile')
        taskMgr.remove(self.taskName)
        self.__undoCollisions()
        self.physicsMgr.clearLinearForces()
        FlyingGag.delete(self)
        self.deleting = 1
        self.ignoreAll()

    def remove(self):
        self.delete()

    def setAvId(self, avId):
        self.avId = avId

    def setRace(self, doId):
        self.race = base.cr.doId2do.get(doId)

    def setOwnerId(self, ownerId):
        self.ownerId = ownerId

    def setType(self, type):
        self.type = type

    def setPos(self, x, y, z):
        DistributedSmoothNode.DistributedSmoothNode.setPos(self, x, y, z)

    def getVelocity(self):
        return self.actorNode.getPhysicsObject().getVelocity()

    def setupPhysics(self):
        self.physicsMgr = PhysicsManager()
        self.physicsEpoch = globalClock.getFrameTime()
        self.lastPhysicsFrame = 0
        integrator = LinearEulerIntegrator()
        self.physicsMgr.attachLinearIntegrator(integrator)
        fn = ForceNode('windResistance')
        fnp = NodePath(fn)
        fnp.reparentTo(render)
        windResistance = LinearFrictionForce(0.2)
        fn.addForce(windResistance)
        self.physicsMgr.addLinearForce(windResistance)
        self.windResistance = windResistance
        fn = ForceNode('engine')
        fnp = NodePath(fn)
        fnp.reparentTo(self)
        engine = LinearVectorForce(0, 0, 3)
        fn.addForce(engine)
        self.physicsMgr.addLinearForce(engine)
        self.engine = engine
        self.physicsMgr.attachPhysicalNode(self.node())
        self.physicsObj = self.actorNode.getPhysicsObject()
        ownerAv = base.cr.doId2do[self.ownerId]
        ownerVel = self.ownerKart.getVelocity()
        ownerSpeed = ownerVel.length()
        rotMat = Mat3.rotateMatNormaxis(self.ownerKart.getH(), Vec3.up())
        ownerHeading = rotMat.xform(Vec3.forward())
        throwSpeed = 50
        throwVel = ownerHeading * throwSpeed
        throwVelCast = Vec3(throwVel[0], throwVel[1], throwVel[2] + 50)
        self.actorNode.getPhysicsObject().setVelocity(self.ownerKart.getVelocity() + throwVelCast)
        lookPoint = render.getRelativePoint(self.ownerKart, Point3(0, 10, 0))
        self.lookAt(lookPoint)
        self.taskName = 'updatePhysics%s' % self.name
        taskMgr.add(self.__updatePhysics, self.taskName, priority=25)

    def checkTargetDistance(self):
        if self.hasTarget:
            return self.getDistance(self.targetKart)
        else:
            return 0

    def splatTarget(self):
        if self.targetId == base.localAvatar.getDoId() and base.race.localKart:
            base.race.localKart.splatPie()
        self.race.effectManager.addSplatEffect(spawner=self.targetKart, parent=self.targetKart)
        taskMgr.remove(self.splatTaskName)
        self.remove()

    def splat(self, optional = None):
        self.race.effectManager.addSplatEffect(spawner=self)
        taskMgr.remove(self.splatTaskName)
        self.remove()

    def __updatePhysics(self, task):
        if self.deleting:
            return Task.done
        self.timeRatio = (globalClock.getFrameTime() - self.startTime) / self.maxTime
        self.windResistance.setCoef(0.2 + 0.8 * self.timeRatio)
        if base.cr.doId2do.get(self.targetId) == None:
            self.hasTarget = 0
        self.lastD2t = self.d2t
        self.d2t = self.checkTargetDistance()
        if self.hasTarget:
            targetDistance = self.d2t
            distMax = 100
            if self.d2t > distMax:
                targetDistance = distMax
            targetVel = self.targetKart.getVelocity()
            targetPos = self.targetKart.getPos()
            targetAim = Point3(targetPos[0] + targetVel[0] * (targetDistance / distMax), targetPos[1] + targetVel[1] * (targetDistance / distMax), targetPos[2] + targetVel[2] * (targetDistance / distMax))
            self.lookAt(targetPos)
        if self.d2t < 7 and self.hasTarget:
            self.splatTarget()
            return Task.done
        self.count += 1
        dt = globalClock.getDt()
        physicsFrame = int((globalClock.getFrameTime() - self.physicsEpoch) * self.physicsCalculationsPerSecond)
        numFrames = min(physicsFrame - self.lastPhysicsFrame, self.maxPhysicsFrames)
        self.lastPhysicsFrame = physicsFrame
        if self.hasTarget:
            targetVel = self.targetKart.getVelocity()
            targetSpeed = targetVel.length()
            if self.d2t - 10 * self.physicsDt > self.lastD2t:
                self.engine.setVector(Vec3(0, 150 + 150 * self.timeRatio + targetSpeed * (1.0 + 1.0 * self.timeRatio) + self.d2t * (1.0 + 1.0 * self.timeRatio), 12))
            else:
                self.engine.setVector(Vec3(0, 10 + 10 * self.timeRatio + targetSpeed * (0.5 + 0.5 * self.timeRatio) + self.d2t * (0.5 + 0.5 * self.timeRatio), 12))
        else:
            self.engine.setVector(Vec3(0, 100, 3))
        for i in range(numFrames):
            pitch = self.gagNode.getP()
            self.gagNode.setP(pitch + self.rotH * self.physicsDt)
            roll = self.gagNode.getR()
            self.gagNode.setR(roll + self.rotP * self.physicsDt)
            heading = self.gagNode.getH()
            self.gagNode.setH(heading + self.rotR * self.physicsDt)
            self.physicsMgr.doPhysics(self.physicsDt)

        if self.count % 60 == 0:
            pass
        return Task.cont

    def __setupCollisions(self):
        self.cWallTrav = CollisionTraverser('ProjectileWall')
        self.cWallTrav.setRespectPrevTransform(True)
        self.collisionNode = CollisionNode(self.name)
        self.collisionNode.setFromCollideMask(OTPGlobals.WallBitmask)
        self.collisionNode.setIntoCollideMask(BitMask32.allOff())
        cs = CollisionSphere(0, 0, 0, 7)
        self.collisionNode.addSolid(cs)
        sC = self.attachNewNode(self.collisionNode)
        self.collisionNodePath = NodePath(self.collisionNode)
        self.wallHandler = CollisionHandlerPusher()
        base.cTrav.addCollider(sC, self.wallHandler)
        self.wallHandler.addCollider(self.collisionNodePath, self)
        cRay = CollisionRay(0.0, 0.0, 40000.0, 0.0, 0.0, -1.0)
        pieFloorRayName = 'pieFloorRay%s' % self.name
        cRayNode = CollisionNode(pieFloorRayName)
        cRayNode.addSolid(cRay)
        cRayNode.setFromCollideMask(OTPGlobals.FloorBitmask)
        cRayNode.setIntoCollideMask(BitMask32.allOff())
        self.cRayNodePath = self.attachNewNode(cRayNode)
        self.lifter = CollisionHandlerGravity()
        self.lifter.setGravity(32.174 * 3.0)
        self.lifter.setOffset(OTPGlobals.FloorOffset)
        self.lifter.setReach(40.0)
        self.lifter.addCollider(self.cRayNodePath, self)
        base.cTrav.addCollider(self.cRayNodePath, self.lifter)

    def __undoCollisions(self):
        base.cTrav.removeCollider(self.cRayNodePath)

    def __enableCollisions(self):
        self.cQueue = []
        self.cRays = NodePath('stickProjectileToFloor')
        self.cRays.reparentTo(self.gag)
        x = self.gag.getX()
        y = self.gag.getY()
        rayNode = CollisionNode('floorcast')
        ray = CollisionRay(x, y, 40000.0, 0.0, 0.0, -1.0)
        rayNode.addSolid(ray)
        rayNode.setFromCollideMask(OTPGlobals.FloorBitmask)
        rayNode.setIntoCollideMask(BitMask32.allOff())
        rayNodePath = self.cRays.attachNewNode(rayNode)
        cQueue = CollisionHandlerQueue()
        self.cWallTrav.addCollider(rayNodePath, cQueue)
        self.cQueue.append(cQueue)
        self.collisionNodePath.reparentTo(self)
