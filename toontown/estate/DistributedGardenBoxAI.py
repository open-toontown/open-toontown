from otp.ai.AIBase import *
from . import DistributedLawnDecorAI
from direct.directnotify import DirectNotifyGlobal
from . import GardenGlobals

from direct.showbase.ShowBase import *

class DistributedGardenBoxAI(DistributedLawnDecorAI.DistributedLawnDecorAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPlantBaseAI')

    GardenBoxModelA = None
    GardenBoxModelC = None
    GardenBoxModelD = None


    def __init__(self, typeIndex = 0, ownerIndex = 0, plot = 0):
        DistributedLawnDecorAI.DistributedLawnDecorAI.__init__(self, simbase.air, ownerIndex, plot)
        self.typeIndex = typeIndex
        self.occupied = False
        self.dummyRender = NodePath('dummyRender')
        #self.dummySelf = NodePath('dummySelf')
        self.workPath = NodePath('workPath')
        #self.dummySelf.reparentTo(self.dummyRender)
        self.reparentTo(self.dummyRender)
        self.workPath.reparentTo(self)
        self.plotModel = None
        self.boxNode  = None
        self.coll = None

    def delete(self):
        if self.coll:
            self.coll.removeNode()
            del self.coll
        if self.boxNode:
            self.boxNode.removeNode()
            del self.boxNode
        if self.workPath:
            self.workPath.removeNode()
            del self.workPath
        if self.dummyRender:
            self.dummyRender.removeNode()
            del self.dummyRender
        DistributedLawnDecorAI.DistributedLawnDecorAI.delete(self)

    def setEstateId(self, zoneId):
        DistributedLawnDecorAI.DistributedLawnDecorAI.setEstateId(self, zoneId)



    def setupPetCollision(self):
        #adding petcollision after setting the estateId since we need access to the EstateGeom
        if simbase.wantPets:

            if not DistributedGardenBoxAI.GardenBoxModelA:
                DistributedGardenBoxAI.GardenBoxModelA = loader.loadModel("phase_5.5/models/estate/planterA.bam")
            if not DistributedGardenBoxAI.GardenBoxModelC:
                DistributedGardenBoxAI.GardenBoxModelC = loader.loadModel("phase_5.5/models/estate/planterC.bam")
            if not DistributedGardenBoxAI.GardenBoxModelD:
                DistributedGardenBoxAI.GardenBoxModelD = loader.loadModel("phase_5.5/models/estate/planterD.bam")

            if self.typeIndex == GardenGlobals.BOX_THREE:
                coll = DistributedGardenBoxAI.GardenBoxModelA.find('**/collision')
            elif self.typeIndex == GardenGlobals.BOX_TWO:
                coll = DistributedGardenBoxAI.GardenBoxModelC.find('**/collision')
            else :
                coll = DistributedGardenBoxAI.GardenBoxModelD.find('**/collision2')

            estate = simbase.air.doId2do[self.estateId]
            boxNode = estate.petColls.attachNewNode(
                'esPlot_%s' % self.plot)
            boxNode.setPos(self.getPos())
            boxNode.setHpr(self.getHpr())
            boxNode.setScale(2.0, 1.5, 3.0)
            boxNode.setZ(-3)
            self.coll = coll.instanceTo(boxNode)

            self.boxNode = boxNode


    def getBoxPos(self, index):
        if self.typeIndex == GardenGlobals.BOX_THREE:
            offset = -3.42 + (index * 3.56)
        elif self.typeIndex == GardenGlobals.BOX_TWO:
            offset = -1.8 + (index * 3.6)
        else:
            offset = 0
        #self.dummySelf.setPos(self.getPos())
        self.workPath.setX(offset)
        returnPos = self.workPath.getPos(self.dummyRender)
        return returnPos

    def getTypeIndex(self):
        return self.typeIndex


