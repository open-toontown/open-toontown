from panda3d.core import *
from direct.showbase.PythonUtil import reduceAngle
from otp.movement import Impulse
from otp.otpbase import OTPGlobals

class PetSphere(Impulse.Impulse):
    SerialNum = 0

    def __init__(self, petRadius, collTrav):
        Impulse.Impulse.__init__(self)
        self.serialNum = PetSphere.SerialNum
        PetSphere.SerialNum += 1
        self.petRadius = petRadius
        self.collTrav = collTrav

    def _setMover(self, mover):
        Impulse.Impulse._setMover(self, mover)
        self.cSphere = CollisionSphere(0.0, 0.0, 0.0, self.petRadius)
        cSphereNode = CollisionNode('PetSphere')
        cSphereNode.addSolid(self.cSphere)
        self.cSphereNodePath = hidden.attachNewNode(cSphereNode)
        self.cSphereNodePath.reparentTo(self.nodePath)
        cSphereNode.setFromCollideMask(OTPGlobals.WallBitmask)
        cSphereNode.setIntoCollideMask(OTPGlobals.WallBitmask)
        self.pusher = CollisionHandlerPusher()
        self.pusher.setHorizontal(1)
        self.pusher.setInPattern('enter%in')
        self.pusher.setOutPattern('exit%in')
        self.pusher.addCollider(self.cSphereNodePath, self.nodePath)
        self.pusher.addInPattern(self._getCollisionEvent())
        self.collTrav.addCollider(self.cSphereNodePath, self.pusher)
        self.accept(self._getCollisionEvent(), self._handleCollision)

    def _clearMover(self, mover):
        self.ignore(self._getCollisionEvent())
        self.collTrav.removeCollider(self.cSphereNodePath)
        del self.cSphere
        del self.pusher
        del self.collTrav
        self.cSphereNodePath.removeNode()
        del self.cSphereNodePath

    def _getCollisionEvent(self):
        return 'petSphereColl-%s' % self.serialNum

    def _handleCollision(self, collEntry):
        messenger.send(self.mover.getCollisionEventName(), [collEntry])
