from direct.controls.ControlManager import CollisionHandlerRayStart
from direct.directnotify import DirectNotifyGlobal
from pandac.PandaModules import *
from direct.task.Task import Task
from direct.showbase.DirectObject import DirectObject
from direct.showbase.ShadowPlacer import ShadowPlacer

class CogdoFlyingShadowPlacer(ShadowPlacer):

    def __init__(self, cTrav, shadowNodePath, wallCollideMask, floorCollideMask, name):
        ShadowPlacer.__init__(self, cTrav, shadowNodePath, wallCollideMask, floorCollideMask)
        self.name = name

    def setup(self, cTrav, shadowNodePath, wallCollideMask, floorCollideMask):
        if not cTrav:
            base.initShadowTrav()
            cTrav = base.shadowTrav
        self.cTrav = cTrav
        self.shadowNodePath = shadowNodePath
        floorOffset = 0.025
        self.cRay = CollisionRay(0.0, 0.0, 1.0, 0.0, 0.0, -1.0)
        cRayNode = CollisionNode('shadowPlacer')
        cRayNode.addSolid(self.cRay)
        self.cRayNodePath = NodePath(cRayNode)
        self.cRayBitMask = floorCollideMask
        cRayNode.setFromCollideMask(self.cRayBitMask)
        cRayNode.setIntoCollideMask(BitMask32.allOff())
        self.queue = CollisionHandlerQueue()

    def update(self):
        self.cTrav.traverse(render)
        self.queue.sortEntries()
        if self.queue.getNumEntries() > 0:
            entry = self.queue.getEntry(0)
            pos = entry.getSurfacePoint(render)
            self.shadowNodePath.setPos(render, pos)
        return Task.cont

    def delete(self):
        self.off()
        del self.cTrav
        del self.shadowNodePath
        del self.cRay
        self.cRayNodePath.removeNode()
        del self.cRayNodePath
        del self.queue

    def on(self):
        if self.isActive:
            return
        self.cRayNodePath.reparentTo(self.shadowNodePath.getParent())
        self.cTrav.addCollider(self.cRayNodePath, self.queue)
        self.isActive = 1
        taskMgr.add(self.update, 'ShadowPlacer.update.%s' % self.name, -45, extraArgs=[])

    def off(self):
        if not self.isActive:
            return
        didIt = self.cTrav.removeCollider(self.cRayNodePath)
        self.oneTimeCollide()
        self.cRayNodePath.detachNode()
        self.isActive = 0
        taskMgr.remove('ShadowPlacer.update.%s' % self.name)

    def oneTimeCollide(self):
        tempCTrav = CollisionTraverser('oneTimeCollide')
        tempCTrav.addCollider(self.cRayNodePath, self.queue)
        tempCTrav.traverse(render)
