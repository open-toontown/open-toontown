from panda3d.core import DecalEffect, DepthWriteAttrib
from direct.directnotify import DirectNotifyGlobal
from toontown.building import DistributedBuilding

class DistributedAnimBuilding(DistributedBuilding.DistributedBuilding):

    def __init__(self, cr):
        DistributedBuilding.DistributedBuilding.__init__(self, cr)

    def enterToon(self, ts):
        DistributedBuilding.DistributedBuilding.enterToon(self, ts)
        self.fixEffects()

    def fixEffects(self):
        nodes = self.getNodePaths()
        for curNode in nodes:
            mf = curNode.find('**/*mesh_front*')
            sign_joint = curNode.find('**/sign_origin_joint')
            if not sign_joint.isEmpty():
                self.notify.debug('I found sign_origin_joint 1')
            if not mf.isEmpty():
                sign = mf.find('**/sign')
                mf.clearEffect(DecalEffect.getClassType())
                if not sign.isEmpty():
                    sign.setDepthWrite(1, 1)
                    sign.setEffect(DecalEffect.make())
                    sign_joint = curNode.find('**/sign_origin_joint')
                    allSignJoints = curNode.findAllMatches('**/sign_origin_joint')
                    num = allSignJoints.getNumPaths()
                    if num:
                        sign_joint = allSignJoints.getPath(num - 1)
                    if not sign_joint.isEmpty():
                        self.notify.debug('I found sign_origin_joint 2')
                        sign.wrtReparentTo(sign_joint)

    def setupNametag(self):
        if not self.wantsNametag():
            return
        DistributedBuilding.DistributedBuilding.setupNametag(self)

    def getSbSearchString(self):
        result = 'landmarkBlocks/sb' + str(self.block) + ':*animated_building_*_DNARoot'
        return result

    def adjustSbNodepathScale(self, nodePath):
        nodePath.setScale(0.543667, 1, 1)

    def animToToon(self, timeStamp):
        DistributedBuilding.DistributedBuilding.animToToon(self, timeStamp)
        self.fixEffects()
