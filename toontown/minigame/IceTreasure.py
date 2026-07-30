from panda3d.core import Point3, CollisionSphere, CollisionNode, BitMask32
from direct.interval.IntervalGlobal import Sequence, LerpScaleInterval, Parallel, Func, SoundInterval
from direct.directnotify import DirectNotifyGlobal
from direct.showbase.DirectObject import DirectObject
from toontown.toonbase import ToontownGlobals
from toontown.battle import BattleParticles

class IceTreasure(DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('IceTreasure')
    RADIUS = 1.0

    def __init__(self, model, pos, serialNum, gameId, penalty = False):
        self.serialNum = serialNum
        self.penalty = penalty
        center = model.getBounds().getCenter()
        center = Point3(0, 0, 0)
        self.nodePath = model.copyTo(render)
        self.nodePath.setPos(pos[0] - center[0], pos[1] - center[1], pos[2] - center[2])
        self.nodePath.setZ(0)
        self.notify.debug('newPos = %s' % self.nodePath.getPos())
        if self.penalty:
            self.sphereName = 'penaltySphere-%s-%s' % (gameId, self.serialNum)
        else:
            self.sphereName = 'treasureSphere-%s-%s' % (gameId, self.serialNum)
        self.collSphere = CollisionSphere(center[0], center[1], center[2], self.RADIUS)
        self.collSphere.setTangible(0)
        self.collNode = CollisionNode(self.sphereName)
        self.collNode.setIntoCollideMask(ToontownGlobals.PieBitmask)
        self.collNode.addSolid(self.collSphere)
        self.collNodePath = render.attachNewNode(self.collNode)
        self.collNodePath.setPos(pos[0] - center[0], pos[1] - center[1], pos[2] - center[2])
        self.collNodePath.hide()
        self.track = None
        if self.penalty:
            self.tip = self.nodePath.find('**/fusetip')
            sparks = BattleParticles.createParticleEffect(file='icetnt')
            self.sparksEffect = sparks
            sparks.start(self.tip)
            self.penaltyGrabSound = loader.loadSfx('phase_4/audio/sfx/MG_cannon_fire_alt.ogg')
            self.penaltyGrabSound.setVolume(0.75)
            kaboomAttachPoint = self.nodePath.attachNewNode('kaboomAttach')
            kaboomAttachPoint.setZ(3)
            self.kaboom = loader.loadModel('phase_4/models/minigames/ice_game_kaboom')
            self.kaboom.reparentTo(kaboomAttachPoint)
            self.kaboom.setScale(2.0)
            self.kaboom.setBillboardPointEye()
        return

    def destroy(self):
        self.ignoreAll()
        if self.penalty:
            self.sparksEffect.cleanup()
            if self.track:
                self.track.finish()
        self.nodePath.removeNode()
        del self.nodePath
        del self.collSphere
        self.collNodePath.removeNode()
        del self.collNodePath
        del self.collNode

    def showGrab(self):
        self.nodePath.hide()
        self.collNodePath.hide()
        self.collNode.setIntoCollideMask(BitMask32(0))
        if self.penalty:
            self.track = Parallel(SoundInterval(self.penaltyGrabSound), Sequence(Func(self.kaboom.showThrough), LerpScaleInterval(self.kaboom, duration=0.5, scale=Point3(10, 10, 10), blendType='easeOut'), Func(self.kaboom.hide)))
            self.track.start()
