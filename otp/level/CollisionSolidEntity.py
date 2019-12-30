from pandac.PandaModules import *
from otp.otpbase import OTPGlobals
from direct.directnotify import DirectNotifyGlobal
from . import BasicEntities

class CollisionSolidEntity(BasicEntities.NodePathEntity):
    notify = DirectNotifyGlobal.directNotify.newCategory('CollisionSolidEntity')

    def __init__(self, level, entId):
        self.collNodePath = None
        BasicEntities.NodePathEntity.__init__(self, level, entId)
        self.initSolid()
        return

    def destroy(self):
        self.destroySolid()
        BasicEntities.NodePathEntity.destroy(self)

    def initSolid(self):
        self.destroySolid()
        if self.solidType == 'sphere':
            solid = CollisionSphere(0, 0, 0, self.radius)
        else:
            solid = CollisionTube(0, 0, 0, 0, 0, self.length, self.radius)
        node = CollisionNode(self.getUniqueName(self.__class__.__name__))
        node.addSolid(solid)
        node.setCollideMask(OTPGlobals.WallBitmask)
        self.collNodePath = self.attachNewNode(node)
        if __dev__:
            if self.showSolid:
                self.showCS()
            else:
                self.hideCS()

    def destroySolid(self):
        if self.collNodePath is not None:
            self.collNodePath.removeNode()
            self.collNodePath = None
        return

    if __dev__:

        def attribChanged(self, attrib, value):
            print('attribChanged')
            self.initSolid()
