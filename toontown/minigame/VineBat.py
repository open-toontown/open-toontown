from direct.showbase.DirectObject import DirectObject
from toontown.toonbase.ToontownGlobals import *
from direct.directnotify import DirectNotifyGlobal
from pandac.PandaModules import *
import VineGameGlobals
from direct.interval.SoundInterval import SoundInterval

class VineBat(NodePath, DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('VineBat')
    notify.setDebug(True)
    RADIUS = 1.7

    def __init__(self, batIndex, timeToTraverseField):
        NodePath.__init__(self, 'VineBat')
        DirectObject.__init__(self)
        pos = Point3(0, 0, 0)
        serialNum = 0
        gameId = 0
        self.serialNum = serialNum
        self.batIndex = batIndex
        self.timeToTraverseField = timeToTraverseField
        gameAssets = loader.loadModel('phase_4/models/minigames/vine_game')
        bat3 = gameAssets.find('**/bat3')
        bat2 = gameAssets.find('**/bat2')
        bat1 = gameAssets.find('**/bat__1')
        seqNode = SequenceNode.SequenceNode('bat')
        seqNode.addChild(bat1.node())
        seqNode.addChild(bat2.node())
        seqNode.addChild(bat3.node())
        seqNode.setFrameRate(12)
        seqNode.pingpong(False)
        self.batModel = self.attachNewNode(seqNode)
        self.batModel.reparentTo(self)
        gameAssets.removeNode()
        self.batModelIcon = self.attachNewNode('batIcon')
        self.batModel.copyTo(self.batModelIcon)
        regularCamMask = BitMask32.bit(0)
        self.batModelIcon.hide(regularCamMask)
        self.batModelIcon.show(VineGameGlobals.RadarCameraBitmask)
        self.batModelIcon.setScale(0.55)
        self.batModel.setScale(0.15)
        self.setPos(-100, 0, 0)
        center = Point3(0, 0, 0)
        self.sphereName = 'batSphere-%s-%s' % (gameId, self.serialNum)
        self.collSphere = CollisionSphere(center[0], center[1], center[2], self.RADIUS)
        self.collSphere.setTangible(0)
        self.collNode = CollisionNode(self.sphereName)
        self.collNode.setIntoCollideMask(VineGameGlobals.SpiderBitmask)
        self.collNode.addSolid(self.collSphere)
        self.collNodePath = self.attachNewNode(self.collNode)
        self.collNodePath.hide()
        self.accept('enter' + self.sphereName, self.__handleEnterSphere)
        self.screechSfx = base.loadSfx('phase_4/audio/sfx/MG_sfx_vine_game_bat_shriek_3.mp3')
        self.flySfx = base.loadSfx('phase_4/audio/sfx/MG_sfx_vine_game_bat_flying_lp.wav')
        self.oldCutoffDistance = base.sfxPlayer.getCutoffDistance()
        base.sfxPlayer.setCutoffDistance(240)
        self.soundInterval = SoundInterval(self.flySfx, node=self, listenerNode=base.localAvatar, seamlessLoop=True, volume=0.5, cutOff=240)
        self.reparentTo(render)
        self.startedFlying = False
        self.warnedForThisLap = False
        startX = VineGameGlobals.VineXIncrement * VineGameGlobals.NumVines
        endX = -VineGameGlobals.VineXIncrement
        self.velocity = float(startX - endX) / self.timeToTraverseField
        self.warnDistance = 35

    def destroy(self):
        self.ignoreAll()
        self.batModel.removeNode()
        del self.batModel
        del self.collSphere
        self.collNodePath.removeNode()
        del self.collNodePath
        del self.collNode
        self.removeNode()
        self.soundInterval.finish()
        del self.soundInterval
        del self.flySfx
        del self.screechSfx
        base.sfxPlayer.setCutoffDistance(self.oldCutoffDistance)

    def __handleEnterSphere(self, collEntry):
        self.ignoreAll()
        self.notify.debug('treasuerGrabbed')
        messenger.send('VineBatGrabbed', [self.serialNum])

    def showGrab(self):
        self.reparentTo(hidden)
        self.collNode.setIntoCollideMask(BitMask32(0))

    def startFlying(self):
        self.startedFlying = True
        self.soundInterval.loop()

    def stopFlying(self):
        self.flySfx.setVolume(0)
        self.soundInterval.finish()

    def startLap(self):
        self.warnedForThisLap = False

    def checkScreech(self):
        distance = base.localAvatar.getDistance(self)
        if distance < self.warnDistance:
            if self.getX(render) > base.localAvatar.getX(render):
                if not self.warnedForThisLap:
                    self.screechSfx.play()
                    self.warnedForThisLap = True
