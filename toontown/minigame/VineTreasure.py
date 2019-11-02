from direct.showbase.DirectObject import DirectObject
from toontown.toonbase.ToontownGlobals import *
from direct.directnotify import DirectNotifyGlobal

class VineTreasure(DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('VineTreasure')
    RADIUS = 1.7

    def __init__(self, model, pos, serialNum, gameId):
        self.serialNum = serialNum
        center = model.getBounds().getCenter()
        center = Point3(0, 0, 0)
        self.nodePath = model.copyTo(render)
        self.nodePath.setPos(pos[0] - center[0], 0 - center[1], pos[2] - center[2])
        self.nodePath.setScale(0.25)
        self.sphereName = 'treasureSphere-%s-%s' % (gameId, self.serialNum)
        self.collSphere = CollisionSphere(center[0], center[1], center[2], self.RADIUS)
        self.collSphere.setTangible(0)
        self.collNode = CollisionNode(self.sphereName)
        self.collNode.setIntoCollideMask(WallBitmask)
        self.collNode.addSolid(self.collSphere)
        self.collNodePath = render.attachNewNode(self.collNode)
        self.collNodePath.setPos(pos[0] - center[0], 0 - center[1], pos[2] - center[2])
        self.collNodePath.hide()
        self.accept('enter' + self.sphereName, self.__handleEnterSphere)
        self.nodePath.flattenLight()

    def destroy(self):
        self.ignoreAll()
        self.nodePath.removeNode()
        del self.nodePath
        del self.collSphere
        self.collNodePath.removeNode()
        del self.collNodePath
        del self.collNode

    def __handleEnterSphere(self, collEntry):
        self.ignoreAll()
        self.notify.debug('treasuerGrabbed')
        messenger.send('VineTreasureGrabbed', [self.serialNum])

    def showGrab(self):
        self.nodePath.hide()
        self.collNodePath.hide()
        self.collNode.setIntoCollideMask(BitMask32(0))
