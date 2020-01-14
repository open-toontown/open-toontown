from .PlayingCard import PlayingCardNodePath
from . import PlayingCardGlobals
from pandac.PandaModules import NodePath, Vec3
from direct.interval.IntervalGlobal import LerpHprInterval, Parallel, SoundInterval

class PairingGameCard(PlayingCardNodePath):
    DoIntervalDefault = True
    FlipTime = 0.25
    UseDifferentCardColors = True
    CardColors = [(0.933594, 0.265625, 0.28125, 1.0),
     (0.550781, 0.824219, 0.324219, 1.0),
     (0.347656, 0.820312, 0.953125, 1.0),
     (0.460938, 0.378906, 0.824219, 1.0),
     (0.710938, 0.234375, 0.4375, 1.0),
     (0.285156, 0.328125, 0.726562, 1.0),
     (0.242188, 0.742188, 0.515625, 1.0),
     (0.96875, 0.691406, 0.699219, 1.0),
     (0.996094, 0.957031, 0.597656, 1.0),
     (0.992188, 0.480469, 0.167969, 1.0)]

    def __init__(self, value):
        style = PlayingCardGlobals.Styles[0]
        PlayingCardNodePath.__init__(self, style, value)
        self.enterCallback = None
        self.exitCallback = None
        return

    def load(self):
        oneCard = loader.loadModel('phase_4/models/minigames/garden_sign_memory')
        prop = self.attachNewNode('prop')
        PlayingCardGlobals.getImage(self.style, self.suit, self.rank).copyTo(prop)
        prop.setScale(7)
        oneCard.find('**/glow').removeNode()
        cs = oneCard.find('**/collision')
        for solidIndex in range(cs.node().getNumSolids()):
            cs.node().modifySolid(solidIndex).setTangible(False)

        cs.node().setName('cardCollision-%d' % self.value)
        sign = oneCard.find('**/sign1')
        if self.UseDifferentCardColors:
            index = self.rank % len(self.CardColors)
            color = self.CardColors[index]
            sign.setColorScale(*color)
        prop.setPos(0.0, 0.0, 0.08)
        prop.setP(-90)
        prop.reparentTo(oneCard)
        oneCard.reparentTo(self)
        cardBack = oneCard.find('**/sign2')
        cardBack.setColorScale(0.12, 0.35, 0.5, 1.0)
        cardModel = loader.loadModel('phase_3.5/models/gui/playingCard')
        logo = cardModel.find('**/logo')
        logo.reparentTo(self)
        logo.setScale(0.45)
        logo.setP(90)
        logo.setZ(0.025)
        logo.setX(-0.05)
        logo.setH(180)
        cardModel.removeNode()
        self.setR(0)
        self.setScale(2.5)
        self.flipIval = None
        self.turnUpSound = base.loader.loadSfx('phase_4/audio/sfx/MG_pairing_card_flip_face_up.ogg')
        self.turnDownSound = base.loader.loadSfx('phase_4/audio/sfx/MG_pairing_card_flip_face_down.ogg')
        return

    def unload(self):
        self.clearFlipIval()
        self.removeNode()
        del self.turnUpSound
        del self.turnDownSound

    def turnUp(self, doInterval = DoIntervalDefault):
        self.faceUp = 1
        if doInterval:
            self.clearFlipIval()
            self.flipIval = Parallel(LerpHprInterval(self, self.FlipTime, Vec3(0, 0, 0)), SoundInterval(self.turnUpSound, node=self, listenerNode=base.localAvatar, cutOff=240))
            self.flipIval.start()
        else:
            self.setR(0)

    def clearFlipIval(self):
        if self.flipIval:
            self.flipIval.finish()
            self.flipIval = None
        return

    def turnDown(self, doInterval = DoIntervalDefault):
        self.faceUp = 0
        if doInterval:
            self.clearFlipIval()
            self.flipIval = Parallel(LerpHprInterval(self, self.FlipTime, Vec3(0, 0, 180)), SoundInterval(self.turnDownSound, node=self, listenerNode=base.localAvatar, cutOff=240))
            self.flipIval.start()
        else:
            self.setR(180)
