from panda3d.core import *
from panda3d.physics import *
from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObject
from direct.task import Task
from direct.task.TaskManagerGlobal import taskMgr
from direct.showbase.ShowBaseGlobal import globalClock
from toontown.toonbase import ToontownGlobals


class DistributedTTCCraneSandbox(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedTTCCraneSandbox')

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        self.ttcCraneSandbox = True
        self.cranes = {}
        self.safes = {}
        self.heldObject = None
        self.physicsMgr = None
        self.geom = None
        self.magnet = None
        self.craneArm = None
        self.controls = None
        self.stick = None
        self.safe = None
        self.cableTex = None
        self.lightning = None
        return

    def announceGenerate(self):
        DistributedObject.DistributedObject.announceGenerate(self)
        self.cr.ttcCraneSandboxBossId = self.doId
        self.startLoad()

    def startLoad(self):
        self.magnet = loader.loadModel('phase_10/models/cogHQ/CBMagnet.bam')
        self.craneArm = loader.loadModel('phase_10/models/cogHQ/CBCraneArm.bam')
        self.controls = loader.loadModel('phase_10/models/cogHQ/CBCraneControls.bam')
        self.stick = loader.loadModel('phase_10/models/cogHQ/CBCraneStick.bam')
        self.safe = loader.loadModel('phase_10/models/cogHQ/CBSafe.bam')
        self.lightning = loader.loadModel('phase_10/models/cogHQ/CBLightning.bam')
        self.cableTex = self.craneArm.findTexture('MagnetControl')
        self.geom = NodePath('ttc-crane-sandbox-geom')
        plane = CollisionPlane(Plane(Vec3(0, 0, 1), Point3(0, 0, -120)))
        planeNode = CollisionNode('dropPlane')
        planeNode.addSolid(plane)
        planeNode.setCollideMask(ToontownGlobals.PieBitmask)
        self.geom.attachNewNode(planeNode)
        self.geom.reparentTo(render)
        self.physicsMgr = PhysicsManager()
        integrator = LinearEulerIntegrator()
        self.physicsMgr.attachLinearIntegrator(integrator)
        fn = ForceNode('gravity')
        self.fnp = self.geom.attachNewNode(fn)
        gravity = LinearVectorForce(0, 0, -32)
        fn.addForce(gravity)
        self.physicsMgr.addLinearForce(gravity)
        taskMgr.add(self.__doPhysics, self.uniqueName('physics'), priority=25)

    def __doPhysics(self, task):
        dt = globalClock.getDt()
        self.physicsMgr.doPhysics(dt)
        return Task.cont

    def disable(self):
        taskMgr.remove(self.uniqueName('physics'))
        self.ttcCraneSandbox = False
        if getattr(self.cr, 'ttcCraneSandboxBossId', None) == self.doId:
            self.cr.ttcCraneSandboxBossId = None
        if self.physicsMgr:
            self.physicsMgr.clearLinearForces()
        if getattr(self, 'fnp', None):
            self.fnp.removeNode()
            self.fnp = None
        if self.geom:
            self.geom.removeNode()
            self.geom = None
        self.magnet = None
        self.craneArm = None
        self.controls = None
        self.stick = None
        self.safe = None
        self.cableTex = None
        self.lightning = None
        DistributedObject.DistributedObject.disable(self)

    def toCraneMode(self):
        place = self.cr.playGame.getPlace()
        if place and hasattr(place, 'fsm'):
            place.setState('crane')

    def toFinalBattleMode(self):
        pass
