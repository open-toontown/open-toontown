from pandac.PandaModules import NodePath
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from toontown.estate import DistributedStatuary
from toontown.estate import GardenGlobals

class DistributedChangingStatuary(DistributedStatuary.DistributedStatuary):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedChangingStatuary')

    def __init__(self, cr):
        self.notify.debug('constructing DistributedChangingStatuary')
        DistributedStatuary.DistributedStatuary.__init__(self, cr)

    def loadModel(self):
        self.rotateNode = self.plantPath.attachNewNode('rotate')
        self.model = loader.loadModel(self.modelPath)
        colNode = self.model.find('**/+CollisionNode')
        if not colNode.isEmpty():
            score, multiplier = ToontownGlobals.PinballScoring[ToontownGlobals.PinballStatuary]
            if self.pinballScore:
                score = self.pinballScore[0]
                multiplier = self.pinballScore[1]
            scoreNodePath = NodePath('statuary-%d-%d' % (score, multiplier))
            colNode.setName('statuaryCol')
            scoreNodePath.reparentTo(colNode.getParent())
            colNode.reparentTo(scoreNodePath)
        self.model.setScale(self.worldScale)
        self.model.reparentTo(self.rotateNode)
        self.hideParts()
        self.stick2Ground()

    def hideParts(self):
        stage = -1
        attrib = GardenGlobals.PlantAttributes[self.typeIndex]
        growthThresholds = attrib['growthThresholds']
        for index, threshold in enumerate(growthThresholds):
            if self.growthLevel < threshold:
                stage = index
                break

        if stage == -1:
            stage = len(growthThresholds)
        self.notify.debug('growth Stage=%d' % stage)
        for index in xrange(len(growthThresholds) + 1):
            if index != stage:
                partName = '**/growthStage_%d' % index
                self.notify.debug('trying to remove %s' % partName)
                hideThis = self.model.find(partName)
                if not hideThis.isEmpty():
                    hideThis.removeNode()

    def setupShadow(self):
        DistributedStatuary.DistributedStatuary.setupShadow(self)
        self.hideShadow()

    def setGrowthLevel(self, growthLevel):
        self.growthLevel = growthLevel
        if self.model:
            self.model.removeNode()
            self.loadModel()
