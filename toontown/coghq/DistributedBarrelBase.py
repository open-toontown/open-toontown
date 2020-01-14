from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from toontown.toonbase.ToontownGlobals import *
from toontown.coghq import BarrelBase
from otp.level import BasicEntities
from direct.directnotify import DirectNotifyGlobal

class DistributedBarrelBase(BasicEntities.DistributedNodePathEntity, BarrelBase.BarrelBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBarrelBase')

    def __init__(self, cr):
        self.rewardPerGrabMax = 0
        BasicEntities.DistributedNodePathEntity.__init__(self, cr)
        self.grabSoundPath = 'phase_4/audio/sfx/SZ_DD_treasure.ogg'
        self.rejectSoundPath = 'phase_4/audio/sfx/ring_miss.ogg'
        self.animTrack = None
        self.shadow = 0
        self.barrelScale = 0.5
        self.sphereRadius = 3.2
        self.playSoundForRemoteToons = 1
        self.gagNode = None
        self.gagModel = None
        self.barrel = None
        return

    def disable(self):
        BasicEntities.DistributedNodePathEntity.disable(self)
        self.ignoreAll()
        if self.animTrack:
            self.animTrack.pause()
            self.animTrack = None
        return

    def generate(self):
        BasicEntities.DistributedNodePathEntity.generate(self)

    def delete(self):
        BasicEntities.DistributedNodePathEntity.delete(self)
        self.gagNode.removeNode()
        del self.gagNode
        if self.barrel:
            self.barrel.removeNode()
            del self.barrel
            self.barrel = None
        return

    def announceGenerate(self):
        BasicEntities.DistributedNodePathEntity.announceGenerate(self)
        self.setTag('doId', str(self.getDoId()))
        self.loadModel()
        self.collSphere = CollisionSphere(0, 0, 0, self.sphereRadius)
        self.collSphere.setTangible(0)
        self.collNode = CollisionNode(self.uniqueName('barrelSphere'))
        self.collNode.setIntoCollideMask(WallBitmask)
        self.collNode.addSolid(self.collSphere)
        self.collNodePath = self.barrel.attachNewNode(self.collNode)
        self.collNodePath.hide()
        self.applyLabel()
        self.accept(self.uniqueName('enterbarrelSphere'), self.handleEnterSphere)

    def loadModel(self):
        self.grabSound = base.loader.loadSfx(self.grabSoundPath)
        self.rejectSound = base.loader.loadSfx(self.rejectSoundPath)
        self.barrel = loader.loadModel('phase_4/models/cogHQ/gagTank')
        self.barrel.setScale(self.barrelScale)
        self.barrel.reparentTo(self)
        dcsNode = self.barrel.find('**/gagLabelDCS')
        dcsNode.setColor(0.15, 0.15, 0.1)
        self.gagNode = self.barrel.attachNewNode('gagNode')
        self.gagNode.setPosHpr(0.0, -2.62, 4.0, 0, 0, 0)
        self.gagNode.setColorScale(0.7, 0.7, 0.6, 1)

    def handleEnterSphere(self, collEntry = None):
        localAvId = base.localAvatar.getDoId()
        self.d_requestGrab()

    def d_requestGrab(self):
        self.sendUpdate('requestGrab', [])

    def setGrab(self, avId):
        self.notify.debug('handleGrab %s' % avId)
        self.avId = avId
        if avId == base.localAvatar.doId:
            self.ignore(self.uniqueName('entertreasureSphere'))
            self.barrel.setColorScale(0.5, 0.5, 0.5, 1)
        if self.playSoundForRemoteToons or self.avId == base.localAvatar.getDoId():
            base.playSfx(self.grabSound)
        if self.animTrack:
            self.animTrack.finish()
            self.animTrack = None
        flytime = 1.0
        self.animTrack = Sequence(LerpScaleInterval(self.barrel, 0.2, 1.1 * self.barrelScale, blendType='easeInOut'), LerpScaleInterval(self.barrel, 0.2, self.barrelScale, blendType='easeInOut'), Func(self.resetBarrel), name=self.uniqueName('animTrack'))
        self.animTrack.start()
        return

    def setReject(self):
        self.notify.debug('I was rejected!!!!!')

    def resetBarrel(self):
        self.barrel.setScale(self.barrelScale)
        self.accept(self.uniqueName('entertreasureSphere'), self.handleEnterSphere)
