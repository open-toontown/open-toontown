from direct.showbase.DirectObject import DirectObject
from toontown.toonbase.ToontownGlobals import *
from direct.directnotify import DirectNotifyGlobal
from pandac.PandaModules import *
from . import VineGameGlobals

class VineSpider(NodePath, DirectObject):
    RADIUS = 1.7

    def __init__(self):
        NodePath.__init__(self, 'VineSpider')
        DirectObject.__init__(self)
        pos = Point3(0, 0, 0)
        serialNum = 0
        gameId = 0
        self.serialNum = serialNum
        gameAssets = loader.loadModel('phase_4/models/minigames/vine_game')
        spider2 = gameAssets.find('**/spider_3')
        spider1 = gameAssets.find('**/spider_2')
        seqNode = SequenceNode('spider')
        seqNode.addChild(spider1.node())
        seqNode.addChild(spider2.node())
        seqNode.setFrameRate(2)
        seqNode.loop(False)
        self.spiderModel = self.attachNewNode(seqNode)
        self.spiderModel.reparentTo(self)
        gameAssets.removeNode()
        self.spiderModelIcon = self.attachNewNode('spiderIcon')
        self.spiderModel.copyTo(self.spiderModelIcon)
        regularCamMask = BitMask32.bit(0)
        self.spiderModelIcon.hide(regularCamMask)
        self.spiderModelIcon.show(VineGameGlobals.RadarCameraBitmask)
        self.spiderModel.setScale(0.2)
        self.spiderModelIcon.setScale(0.75)
        self.setPos(-100, 0, 0)
        center = Point3(0, 0, 0)
        self.sphereName = 'spiderSphere-%s-%s' % (gameId, self.serialNum)
        self.collSphere = CollisionSphere(center[0], center[1], center[2], self.RADIUS)
        self.collSphere.setTangible(0)
        self.collNode = CollisionNode(self.sphereName)
        self.collNode.setIntoCollideMask(VineGameGlobals.SpiderBitmask)
        self.collNode.addSolid(self.collSphere)
        self.collNodePath = self.attachNewNode(self.collNode)
        self.collNodePath.hide()
        self.accept('enter' + self.sphereName, self.__handleEnterSphere)
        self.reparentTo(render)

    def destroy(self):
        self.ignoreAll()
        self.spiderModel.removeNode()
        del self.spiderModel
        del self.collSphere
        self.collNodePath.removeNode()
        del self.collNodePath
        del self.collNode
        self.removeNode()

    def __handleEnterSphere(self, collEntry):
        print('VineSpider.__handleEnterSphere')
        print(collEntry)
        self.ignoreAll()
        self.notify.debug('treasuerGrabbed')
        messenger.send('VineSpiderGrabbed', [self.serialNum])

    def showGrab(self):
        self.reparentTo(hidden)
        self.collNode.setIntoCollideMask(BitMask32(0))
