from direct.controls.GravityWalker import GravityWalker
from panda3d.core import CollisionSphere, CollisionNode, BitMask32, CollisionHandlerEvent, CollisionRay, CollisionHandlerGravity, CollisionHandlerFluidPusher, CollisionHandlerPusher
from toontown.toonbase import ToontownGlobals
from otp.otpbase import OTPGlobals

class CogdoFlyingCollisions(GravityWalker):
    wantFloorSphere = 0

    def __init__(self):
        GravityWalker.__init__(self, gravity=0.0)

    def initializeCollisions(self, collisionTraverser, avatarNodePath, avatarRadius = 1.4, floorOffset = 1.0, reach = 1.0):
        self.cHeadSphereNodePath = None
        self.cFloorEventSphereNodePath = None
        self.setupHeadSphere(avatarNodePath)
        self.setupFloorEventSphere(avatarNodePath, ToontownGlobals.FloorEventBitmask, avatarRadius)
        GravityWalker.initializeCollisions(self, collisionTraverser, avatarNodePath, avatarRadius, floorOffset, reach)
        return

    def setupWallSphere(self, bitmask, avatarRadius):
        self.avatarRadius = avatarRadius
        cSphere = CollisionSphere(0.0, 0.0, self.avatarRadius + 0.75, self.avatarRadius)
        cSphereNode = CollisionNode('Flyer.cWallSphereNode')
        cSphereNode.addSolid(cSphere)
        cSphereNodePath = self.avatarNodePath.attachNewNode(cSphereNode)
        cSphereNode.setFromCollideMask(bitmask)
        cSphereNode.setIntoCollideMask(BitMask32.allOff())
        if config.GetBool('want-fluid-pusher', 0):
            self.pusher = CollisionHandlerFluidPusher()
        else:
            self.pusher = CollisionHandlerPusher()
        self.pusher.addCollider(cSphereNodePath, self.avatarNodePath)
        self.cWallSphereNodePath = cSphereNodePath

    def setupEventSphere(self, bitmask, avatarRadius):
        self.avatarRadius = avatarRadius
        cSphere = CollisionSphere(0.0, 0.0, self.avatarRadius + 0.75, self.avatarRadius * 1.04)
        cSphere.setTangible(0)
        cSphereNode = CollisionNode('Flyer.cEventSphereNode')
        cSphereNode.addSolid(cSphere)
        cSphereNodePath = self.avatarNodePath.attachNewNode(cSphereNode)
        cSphereNode.setFromCollideMask(bitmask)
        cSphereNode.setIntoCollideMask(BitMask32.allOff())
        self.event = CollisionHandlerEvent()
        self.event.addInPattern('enter%in')
        self.event.addOutPattern('exit%in')
        self.cEventSphereNodePath = cSphereNodePath

    def setupRay(self, bitmask, floorOffset, reach):
        cRay = CollisionRay(0.0, 0.0, 3.0, 0.0, 0.0, -1.0)
        cRayNode = CollisionNode('Flyer.cRayNode')
        cRayNode.addSolid(cRay)
        self.cRayNodePath = self.avatarNodePath.attachNewNode(cRayNode)
        cRayNode.setFromCollideMask(bitmask)
        cRayNode.setIntoCollideMask(BitMask32.allOff())
        self.lifter = CollisionHandlerGravity()
        self.lifter.setLegacyMode(self._legacyLifter)
        self.lifter.setGravity(self.getGravity(0))
        self.lifter.addInPattern('%fn-enter-%in')
        self.lifter.addAgainPattern('%fn-again-%in')
        self.lifter.addOutPattern('%fn-exit-%in')
        self.lifter.setOffset(floorOffset)
        self.lifter.setReach(reach)
        self.lifter.addCollider(self.cRayNodePath, self.avatarNodePath)

    def setupHeadSphere(self, avatarNodePath):
        collSphere = CollisionSphere(0, 0, 0, 1)
        collSphere.setTangible(1)
        collNode = CollisionNode('Flyer.cHeadCollSphere')
        collNode.setFromCollideMask(ToontownGlobals.CeilingBitmask)
        collNode.setIntoCollideMask(BitMask32.allOff())
        collNode.addSolid(collSphere)
        self.cHeadSphereNodePath = avatarNodePath.attachNewNode(collNode)
        self.cHeadSphereNodePath.setZ(base.localAvatar.getHeight() + 1.0)
        self.headCollisionEvent = CollisionHandlerEvent()
        self.headCollisionEvent.addInPattern('%fn-enter-%in')
        self.headCollisionEvent.addOutPattern('%fn-exit-%in')
        base.cTrav.addCollider(self.cHeadSphereNodePath, self.headCollisionEvent)

    def setupFloorEventSphere(self, avatarNodePath, bitmask, avatarRadius):
        cSphere = CollisionSphere(0.0, 0.0, 0.0, 0.75)
        cSphereNode = CollisionNode('Flyer.cFloorEventSphere')
        cSphereNode.addSolid(cSphere)
        cSphereNodePath = avatarNodePath.attachNewNode(cSphereNode)
        cSphereNode.setFromCollideMask(bitmask)
        cSphereNode.setIntoCollideMask(BitMask32.allOff())
        self.floorCollisionEvent = CollisionHandlerEvent()
        self.floorCollisionEvent.addInPattern('%fn-enter-%in')
        self.floorCollisionEvent.addAgainPattern('%fn-again-%in')
        self.floorCollisionEvent.addOutPattern('%fn-exit-%in')
        base.cTrav.addCollider(cSphereNodePath, self.floorCollisionEvent)
        self.cFloorEventSphereNodePath = cSphereNodePath

    def deleteCollisions(self):
        GravityWalker.deleteCollisions(self)
        if self.cHeadSphereNodePath != None:
            base.cTrav.removeCollider(self.cHeadSphereNodePath)
            self.cHeadSphereNodePath.detachNode()
            self.cHeadSphereNodePath = None
            self.headCollisionsEvent = None
        if self.cFloorEventSphereNodePath != None:
            base.cTrav.removeCollider(self.cFloorEventSphereNodePath)
            self.cFloorEventSphereNodePath.detachNode()
            self.cFloorEventSphereNodePath = None
            self.floorCollisionEvent = None
        self.cRayNodePath.detachNode()
        del self.cRayNodePath
        self.cEventSphereNodePath.detachNode()
        del self.cEventSphereNodePath
        return

    def setCollisionsActive(self, active = 1):
        if self.collisionsActive != active:
            if self.cHeadSphereNodePath != None:
                base.cTrav.removeCollider(self.cHeadSphereNodePath)
                if active:
                    base.cTrav.addCollider(self.cHeadSphereNodePath, self.headCollisionEvent)
            if self.cFloorEventSphereNodePath != None:
                base.cTrav.removeCollider(self.cFloorEventSphereNodePath)
                if active:
                    base.cTrav.addCollider(self.cFloorEventSphereNodePath, self.floorCollisionEvent)
        GravityWalker.setCollisionsActive(self, active)
        return

    def enableAvatarControls(self):
        pass

    def disableAvatarControls(self):
        pass

    def handleAvatarControls(self, task):
        pass
