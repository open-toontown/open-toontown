from direct.showbase.DirectObject import DirectObject
from toontown.toonbase.ToontownGlobals import *
from direct.directnotify import DirectNotifyGlobal
from direct.interval.IntervalGlobal import *
from toontown.minigame import ToonBlitzGlobals
from toontown.estate.GardenGlobals import BeanColors
import random

class TwoDTreasure(DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('TwoDTreasure')
    RADIUS = 1.3

    def __init__(self, treasureMgr, index, pos, value, isEnemyGenerated, model):
        self.game = treasureMgr.section.sectionMgr.game
        self.index = index
        self.value = value
        self.isEnemyGenerated = isEnemyGenerated
        center = model.getBounds().getCenter()
        center = Point3(0, 0, 0)
        treasureName = 'treasure-' + str(index)
        model.setScale(2.5)
        self.model = NodePath(treasureName)
        self.nodePath = model.copyTo(self.model)
        self.appearEffect = None
        self.flash = None
        glowParticle = self.game.assetMgr.particleGlow
        self.glowCard = glowParticle.copyTo(self.model)
        self.glowCard2 = glowParticle.copyTo(self.glowCard)
        self.glowCard.setPos(0, 0.1, 0)
        self.glowCard.setColor(model.getColor())
        self.glowCard.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd, ColorBlendAttrib.OIncomingAlpha, ColorBlendAttrib.OOne))
        self.glowCard2.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd, ColorBlendAttrib.OIncomingAlpha, ColorBlendAttrib.OOne))
        self.glowScalIval = Sequence(LerpScaleInterval(self.glowCard, 0.4, scale=4.1, startScale=4.9), LerpScaleInterval(self.glowCard, 0.4, scale=4.9, startScale=4.1))
        self.glowScalIval.loop()
        self.modelScalIval = Sequence(LerpScaleInterval(self.model, 0.4, scale=1.0, startScale=1.03), LerpScaleInterval(self.model, 0.4, scale=1.03, startScale=1.0))
        self.modelScalIval.loop()
        self.sphereName = 'treasureSphere-%s-%s' % (self.game.doId, self.index)
        self.collSphere = CollisionSphere(center[0], center[1], center[2], self.RADIUS)
        self.collSphere.setTangible(0)
        self.collNode = CollisionNode(self.sphereName)
        self.collNode.setIntoCollideMask(WallBitmask)
        self.collNode.addSolid(self.collSphere)
        self.collNodePath = self.model.attachNewNode(self.collNode)
        self.collNodePath.hide()
        self.accept('enter' + self.sphereName, self.__handleEnterSphere)
        self.model.setPos(pos[0] - center[0], 0 - center[1], pos[2] - center[2])
        self.nodePath.flattenLight()
        if self.isEnemyGenerated:
            self.flash = glowParticle.copyTo(self.model)
            self.flash.reparentTo(treasureMgr.treasuresNP)
            self.flash.setPos(self.model.getX(), self.model.getY() - 0.2, self.model.getZ())
            self.flash.setScale(6)
            self.flash.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd, ColorBlendAttrib.OIncomingAlpha, ColorBlendAttrib.OOne))
            self.hideTreasure()
        return

    def destroy(self):
        self.game = None
        self.ignoreAll()
        if self.glowScalIval:
            self.glowScalIval.finish()
            del self.glowScalIval
        if self.modelScalIval:
            self.modelScalIval.finish()
            del self.modelScalIval
        if self.appearEffect:
            self.appearEffect.finish()
            del self.appearEffect
        if self.flash:
            self.flash.removeNode()
            del self.flash
        self.nodePath.removeNode()
        del self.nodePath
        del self.collSphere
        self.collNodePath.removeNode()
        del self.collNodePath
        del self.collNode
        self.model.removeNode()
        del self.model
        return

    def setRandomColor(self):
        beanIndex = random.randint(0, len(BeanColors) - 1)
        colors = BeanColors[beanIndex]
        self.model.setColor(colors[0] / 255.0, colors[1] / 255.0, colors[2] / 255.0)

    def __handleEnterSphere(self, cevent):
        self.ignoreAll()
        self.notify.debug('treasuerGrabbed')
        sectionIndex = int(cevent.getIntoNodePath().getName()[-5:-3])
        treasureIndex = int(cevent.getIntoNodePath().getName()[-2:])
        messenger.send('twoDTreasureGrabbed', [sectionIndex, treasureIndex])

    def hideTreasure(self):
        self.model.hide()
        self.collNode.setIntoCollideMask(BitMask32(0))
        if self.isEnemyGenerated:
            self.flash.hide()

    def showTreasure(self):
        self.model.show()
        self.collNode.setIntoCollideMask(WallBitmask)
        if self.isEnemyGenerated:
            self.flash.show()

    def setTreasurePos(self, pos):
        self.model.setPos(pos)
        if self.isEnemyGenerated:
            self.flash.setPos(self.model.getX(), self.model.getY() - 0.2, self.model.getZ())

    def popupEnemyTreasure(self):
        modelFadeIn = LerpFunc(self.model.setAlphaScale, duration=0.5)
        flashFadeOut = LerpFunc(self.flash.setAlphaScale, fromData=1, toData=0, duration=0.5)
        self.appearEffect = Sequence(Wait(2.4), Func(self.showTreasure), Parallel(modelFadeIn, flashFadeOut, Func(base.playSfx, self.game.assetMgr.sparkleSound)))
        self.appearEffect.start()
