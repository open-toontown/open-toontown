from panda3d.core import *
from direct.showbase.DirectObject import DirectObject
from otp.otpbase import OTPGlobals

class PositionExaminer(DirectObject, NodePath):

    def __init__(self):
        try:
            self.__initialized
            return
        except:
            self.__initialized = 1

        NodePath.__init__(self, hidden.attachNewNode('PositionExaminer'))
        self.cRay = CollisionRay(0.0, 0.0, 6.0, 0.0, 0.0, -1.0)
        self.cRayNode = CollisionNode('cRayNode')
        self.cRayNode.addSolid(self.cRay)
        self.cRayNodePath = self.attachNewNode(self.cRayNode)
        self.cRayNodePath.hide()
        self.cRayBitMask = OTPGlobals.FloorBitmask
        self.cRayNode.setFromCollideMask(self.cRayBitMask)
        self.cRayNode.setIntoCollideMask(BitMask32.allOff())
        self.cSphere = CollisionSphere(0.0, 0.0, 0.0, 1.5)
        self.cSphereNode = CollisionNode('cSphereNode')
        self.cSphereNode.addSolid(self.cSphere)
        self.cSphereNodePath = self.attachNewNode(self.cSphereNode)
        self.cSphereNodePath.hide()
        self.cSphereBitMask = OTPGlobals.WallBitmask
        self.cSphereNode.setFromCollideMask(self.cSphereBitMask)
        self.cSphereNode.setIntoCollideMask(BitMask32.allOff())
        self.ccLine = CollisionSegment(0.0, 0.0, 0.0, 1.0, 0.0, 0.0)
        self.ccLineNode = CollisionNode('ccLineNode')
        self.ccLineNode.addSolid(self.ccLine)
        self.ccLineNodePath = self.attachNewNode(self.ccLineNode)
        self.ccLineNodePath.hide()
        self.ccLineBitMask = OTPGlobals.CameraBitmask
        self.ccLineNode.setFromCollideMask(self.ccLineBitMask)
        self.ccLineNode.setIntoCollideMask(BitMask32.allOff())
        self.cRayTrav = CollisionTraverser('PositionExaminer.cRayTrav')
        self.cRayTrav.setRespectPrevTransform(False)
        self.cRayQueue = CollisionHandlerQueue()
        self.cRayTrav.addCollider(self.cRayNodePath, self.cRayQueue)
        self.cSphereTrav = CollisionTraverser('PositionExaminer.cSphereTrav')
        self.cSphereTrav.setRespectPrevTransform(False)
        self.cSphereQueue = CollisionHandlerQueue()
        self.cSphereTrav.addCollider(self.cSphereNodePath, self.cSphereQueue)
        self.ccLineTrav = CollisionTraverser('PositionExaminer.ccLineTrav')
        self.ccLineTrav.setRespectPrevTransform(False)
        self.ccLineQueue = CollisionHandlerQueue()
        self.ccLineTrav.addCollider(self.ccLineNodePath, self.ccLineQueue)

    def delete(self):
        del self.cRay
        del self.cRayNode
        self.cRayNodePath.removeNode()
        del self.cRayNodePath
        del self.cSphere
        del self.cSphereNode
        self.cSphereNodePath.removeNode()
        del self.cSphereNodePath
        del self.ccLine
        del self.ccLineNode
        self.ccLineNodePath.removeNode()
        del self.ccLineNodePath
        del self.cRayTrav
        del self.cRayQueue
        del self.cSphereTrav
        del self.cSphereQueue
        del self.ccLineTrav
        del self.ccLineQueue

    def consider(self, node, pos, eyeHeight):
        self.reparentTo(node)
        self.setPos(pos)
        result = None
        self.cRayTrav.traverse(render)
        if self.cRayQueue.getNumEntries() != 0:
            self.cRayQueue.sortEntries()
            floorPoint = self.cRayQueue.getEntry(0).getSurfacePoint(self.cRayNodePath)
            if abs(floorPoint[2]) <= 4.0:
                pos += floorPoint
                self.setPos(pos)
                self.cSphereTrav.traverse(render)
                if self.cSphereQueue.getNumEntries() == 0:
                    self.ccLine.setPointA(0, 0, eyeHeight)
                    self.ccLine.setPointB(-pos[0], -pos[1], eyeHeight)
                    self.ccLineTrav.traverse(render)
                    if self.ccLineQueue.getNumEntries() == 0:
                        result = pos
        self.reparentTo(hidden)
        self.cRayQueue.clearEntries()
        self.cSphereQueue.clearEntries()
        self.ccLineQueue.clearEntries()
        return result
