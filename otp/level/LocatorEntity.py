from . import Entity, BasicEntities
from pandac.PandaModules import NodePath
from direct.directnotify import DirectNotifyGlobal

class LocatorEntity(Entity.Entity, NodePath):
    notify = DirectNotifyGlobal.directNotify.newCategory('LocatorEntity')

    def __init__(self, level, entId):
        node = hidden.attachNewNode('LocatorEntity-%s' % entId)
        NodePath.__init__(self, node)
        Entity.Entity.__init__(self, level, entId)
        self.doReparent()

    def destroy(self):
        Entity.Entity.destroy(self)
        self.removeNode()

    def getNodePath(self):
        return self

    def doReparent(self):
        if self.searchPath != '':
            parent = self.level.geom.find(self.searchPath)
            if parent.isEmpty():
                LocatorEntity.notify.warning("could not find '%s'" % self.searchPath)
                self.reparentTo(hidden)
            else:
                self.reparentTo(parent)

    if __dev__:

        def attribChanged(self, attrib, value):
            self.doReparent()
