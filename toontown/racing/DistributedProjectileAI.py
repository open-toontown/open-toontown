#Okay, so what do we need functionally here?
#1. the ability for this to have distributed movement (created by AI, controlled by AI)
#2. The ability to move onto the curve
#3. The ability to move off the curve to hit a player.
from pandac.PandaModules import *
from direct.distributed import DistributedSmoothNodeAI


class DistributedProjectileAI(DistributedSmoothNodeAI.DistributedSmoothNodeAI, NodePath):
    def __init__(self, air, race, avId):
        DistributedSmoothNodeAI.DistributedSmoothNodeAI.__init__(self, air)
        NodePath.__init__(self, "Projectile")
        self.avId=avId
        self.air=air
        self.race=race
        self.toon=self.air.doId2do[self.avId]

    def announceGenerate(self):
        DistributedSmoothNodeAI.DistributedSmoothNodeAI.announceGenerate(self)
        self.name = self.uniqueName('projectile')
        self.posHprBroadcastName = self.uniqueName('projectileBroadcast')

        self.geom=loader.loadModel("models/smiley")
        self.geom.reparentTo(self)
        self.reparentTo(self.race.geom)

        self.startPosHprBroadCast()
        self.geom.setPos(self.toon.kart.getPos())


        self.setupPhysics()
        #self.__enableCollisions()


    def generate(self):
        DistributedSmoothNodeAI.DistributedSmoothNodeAI.generate(self)
        self.name = self.uniqueName('projectile')
        self.posHprBroadcastName = self.uniqueName('projectileBroadcast')

        self.geom=loader.loadModel("models/smiley")
        self.geom.reparentTo(self)
        self.reparentTo(self.race.geom)

        self.startPosHprBroadcast()
        self.setPos(self.toon.kart.getPos())


        self.setupPhysics()
        #self.__enableCollisions()


    def delete(self):
        DistributedSmoothNodeAI.DistributedSmoothNodeAI.delete(self)


    def getAvatar(self):
        return self.avId

    def setupPhysics(self):

        ###########################################################
        # Set up all the physics forces
        self.physicsMgr = PhysicsManager()
        integrator = LinearEulerIntegrator()
        self.physicsMgr.attachLinearIntegrator(integrator)

        #create an engine force
        fn = ForceNode("engine")
        fnp = NodePath(fn)
        fnp.reparentTo(self)
        engine = LinearVectorForce(0, 0, 0)
        fn.addForce(engine)
        self.physicsMgr.addLinearForce(engine)
        self.engine = engine
