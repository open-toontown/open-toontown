from direct.interval.IntervalGlobal import *
from otp.level import BasicEntities
import MovingPlatform
from pandac.PandaModules import Vec3

class GearEntity(BasicEntities.NodePathEntity):
    ModelPaths = {'factory': 'phase_9/models/cogHQ/FactoryGearB',
     'mint': 'phase_10/models/cashbotHQ/MintGear'}

    def __init__(self, level, entId):
        self.modelType = 'factory'
        self.entInitialized = False
        BasicEntities.NodePathEntity.__init__(self, level, entId)
        self.entInitialized = True
        self.initGear()

    def destroy(self):
        self.destroyGear()
        BasicEntities.NodePathEntity.destroy(self)

    def initGear(self):
        if hasattr(self, 'in_initGear'):
            return
        self.in_initGear = True
        self.destroyGear()
        model = loader.loadModel(GearEntity.ModelPaths[self.modelType])
        self.gearParent = self.attachNewNode('gearParent-%s' % self.entId)
        if self.orientation == 'horizontal':
            vertNodes = model.findAllMatches('**/VerticalCollisions')
            for node in vertNodes:
                node.stash()

            mPlat = MovingPlatform.MovingPlatform()
            mPlat.setupCopyModel(self.getParentToken(), model, 'HorizontalFloor')
            model = mPlat
        else:
            horizNodes = model.findAllMatches('**/HorizontalCollisions')
            for node in horizNodes:
                node.stash()

            model.setZ(0.15)
            model.flattenLight()
        model.setScale(self.gearScale)
        model.flattenLight()
        model.setScale(self.getScale())
        self.setScale(1)
        model.flattenLight()
        if self.orientation == 'vertical':
            self.gearParent.setP(-90)
        self.model = model
        self.model.reparentTo(self.gearParent)
        self.startRotate()
        del self.in_initGear

    def destroyGear(self):
        self.stopRotate()
        if hasattr(self, 'model'):
            if isinstance(self.model, MovingPlatform.MovingPlatform):
                self.model.destroy()
            else:
                self.model.removeNode()
            del self.model
        if hasattr(self, 'gearParent'):
            self.gearParent.removeNode()
            del self.gearParent

    def startRotate(self):
        self.stopRotate()
        try:
            ivalDur = 360.0 / self.degreesPerSec
        except ZeroDivisionError:
            pass
        else:
            hOffset = 360.0
            if ivalDur < 0.0:
                ivalDur = -ivalDur
                hOffset = -hOffset
            self.rotateIval = LerpHprInterval(self.model, ivalDur, Vec3(hOffset, 0, 0), startHpr=Vec3(0, 0, 0), name='gearRot-%s' % self.entId)
            self.rotateIval.loop()
            self.rotateIval.setT(globalClock.getFrameTime() - self.level.startTime + ivalDur * self.phaseShift)

    def stopRotate(self):
        if hasattr(self, 'rotateIval'):
            self.rotateIval.pause()
            del self.rotateIval

    if __dev__:

        def setDegreesPerSec(self, degreesPerSec):
            if self.entInitialized:
                self.degreesPerSec = degreesPerSec
                self.startRotate()

        def setPhaseShift(self, phaseShift):
            if self.entInitialized:
                self.phaseShift = phaseShift
                self.startRotate()

        def attribChanged(self, attrib, value):
            self.destroyGear()
            self.initGear()

        def setScale(self, *args):
            BasicEntities.NodePathEntity.setScale(self, *args)
            if self.entInitialized:
                self.initGear()

        def setSx(self, *args):
            BasicEntities.NodePathEntity.setSx(self, *args)
            if self.entInitialized:
                self.initGear()

        def setSy(self, *args):
            BasicEntities.NodePathEntity.setSy(self, *args)
            if self.entInitialized:
                self.initGear()

        def setSz(self, *args):
            BasicEntities.NodePathEntity.setSz(self, *args)
            if self.entInitialized:
                self.initGear()
