from pandac.PandaModules import NodePath, BillboardEffect, Vec3, Point3, TextureStage, TransparencyAttrib, DecalEffect, VBase4
from direct.fsm import FSM
from direct.gui.DirectGui import DirectFrame, DGG
from direct.interval.IntervalGlobal import LerpScaleInterval, LerpColorScaleInterval, Parallel, Sequence, Wait

class DinerStatusIndicator(NodePath.NodePath, FSM.FSM):

    def __init__(self, parent, pos = None, scale = None):
        NodePath.NodePath.__init__(self, 'DinerStatusIndicator')
        if parent:
            self.reparentTo(parent)
        if pos:
            self.setPos(pos)
        if scale:
            self.setScale(scale)
        self.loadAssets()
        FSM.FSM.__init__(self, 'DinerStatusIndicator')
        self.activeIval = None
        return

    def delete(self):
        if self.activeIval:
            self.activeIval.pause()
            self.activeIval = None
        self.angryIcon.removeNode()
        self.hungryIcon.removeNode()
        self.eatingIcon.removeNode()
        self.removeNode()
        return

    def loadAssets(self):
        iconsFile = loader.loadModel('phase_12/models/bossbotHQ/BanquetIcons')
        self.angryIcon, self.angryMeter = self.loadIcon(iconsFile, '**/Anger')
        self.hungryIcon, self.hungryMeter = self.loadIcon(iconsFile, '**/Hunger')
        self.eatingIcon, self.eatingMeter = self.loadIcon(iconsFile, '**/Food')
        self.angryMeter.hide()
        iconsFile.removeNode()

    def loadIcon(self, iconsFile, name):
        retVal = iconsFile.find(name)
        retVal.setBillboardAxis()
        retVal.reparentTo(self)
        dark = retVal.copyTo(NodePath())
        dark.reparentTo(retVal)
        dark.setColor(0.5, 0.5, 0.5, 1)
        retVal.setEffect(DecalEffect.make())
        retVal.setTransparency(TransparencyAttrib.MAlpha, 1)
        ll, ur = dark.getTightBounds()
        center = retVal.attachNewNode('center')
        center.setPos(0, 0, ll[2])
        dark.wrtReparentTo(center)
        dark.setTexProjector(TextureStage.getDefault(), center, retVal)
        retVal.hide()
        return (retVal, center)

    def enterEating(self, timeToFinishFood):
        self.eatingIcon.show()
        self.activeIval = self.createMeterInterval(self.eatingIcon, self.eatingMeter, timeToFinishFood)
        self.activeIval.start()

    def exitEating(self):
        if self.activeIval:
            self.activeIval.finish()
            self.activeIval = None
        self.eatingIcon.hide()
        return

    def enterHungry(self, timeToFinishFood):
        self.hungryIcon.show()
        self.activeIval = self.createMeterInterval(self.hungryIcon, self.hungryMeter, timeToFinishFood)
        self.activeIval.start()

    def exitHungry(self):
        if self.activeIval:
            self.activeIval.finish()
            self.activeIval = None
        self.hungryIcon.hide()
        return

    def enterAngry(self):
        self.angryIcon.show()

    def exitAngry(self):
        self.angryIcon.hide()
        if self.activeIval:
            self.activeIval.finish()
            self.activeIval = None
        return

    def enterDead(self):
        pass

    def exitDead(self):
        pass

    def enterInactive(self):
        pass

    def exitInactive(self):
        pass

    def createMeterInterval(self, icon, meter, time):
        ivalDarkness = LerpScaleInterval(meter, time, scale=Vec3(1, 1, 1), startScale=Vec3(1, 0.001, 0.001))
        flashingTrack = Sequence()
        flashDuration = 10
        if time > flashDuration:
            flashingTrack.append(Wait(time - flashDuration))
            for i in xrange(10):
                flashingTrack.append(Parallel(LerpColorScaleInterval(icon, 0.5, VBase4(1, 0, 0, 1)), icon.scaleInterval(0.5, 1.25)))
                flashingTrack.append(Parallel(LerpColorScaleInterval(icon, 0.5, VBase4(1, 1, 1, 1)), icon.scaleInterval(0.5, 1)))

        retIval = Parallel(ivalDarkness, flashingTrack)
        return retIval
