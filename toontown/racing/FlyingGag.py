from pandac.PandaModules import *
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from otp.avatar.ShadowCaster import ShadowCaster

class FlyingGag(NodePath, ShadowCaster):

    def __init__(self, name, geom = None):
        an = ActorNode('flyingGagAN')
        NodePath.__init__(self, an)
        self.actorNode = an
        self.gag = None
        self.gagNode = None
        ShadowCaster.__init__(self, False)
        if geom:
            self.gagNode = self.attachNewNode('PieNode')
            self.gag = geom.copyTo(self.gagNode)
            self.gag.setScale(3)
            self.gagNode.setHpr(0, -45, 0)
            self.gagNode.setPos(0, 0, 2)
            self.initializeDropShadow()
            self.setActiveShadow()
            self.dropShadow.setPos(0, 0, 2)
            self.dropShadow.setScale(3)
        return

    def delete(self):
        ShadowCaster.delete(self)
        NodePath.remove(self)
        self.gag = None
        return

    def getGeomNode(self):
        return self.gag
