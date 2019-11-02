from pandac.PandaModules import *
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from otp.avatar import ShadowCaster

class DroppedGag(NodePath, ShadowCaster.ShadowCaster):

    def __init__(self, name, geom):
        NodePath.__init__(self, name)
        ShadowCaster.ShadowCaster.__init__(self, False)
        self.gag = geom.copyTo(self)
        self.initializeDropShadow()
        self.setActiveShadow()
        self.dropShadow.setScale(1)

    def delete(self):
        ShadowCaster.ShadowCaster.delete(self)
        NodePath.removeNode(self)
        self.gag = None
        return

    def getGeomNode(self):
        return self.gag
