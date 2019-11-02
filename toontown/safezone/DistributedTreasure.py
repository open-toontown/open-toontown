from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from toontown.toonbase.ToontownGlobals import *
from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal

class DistributedTreasure(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedTreasure')

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        self.av = None
        self.treasureFlyTrack = None
        self.modelPath = None
        self.nodePath = None
        self.dropShadow = None
        self.modelFindString = None
        self.grabSoundPath = None
        self.rejectSoundPath = 'phase_4/audio/sfx/ring_miss.mp3'
        self.playSoundForRemoteToons = 1
        self.scale = 1.0
        self.shadow = 1
        self.fly = 1
        self.zOffset = 0.0
        self.billboard = 0
        return

    def disable(self):
        self.ignoreAll()
        self.nodePath.detachNode()
        DistributedObject.DistributedObject.disable(self)

    def delete(self):
        if self.treasureFlyTrack:
            self.treasureFlyTrack.finish()
            self.treasureFlyTrack = None
        DistributedObject.DistributedObject.delete(self)
        self.nodePath.removeNode()
        return

    def announceGenerate(self):
        DistributedObject.DistributedObject.announceGenerate(self)
        self.loadModel(self.modelPath, self.modelFindString)
        self.startAnimation()
        self.nodePath.wrtReparentTo(render)
        self.accept(self.uniqueName('entertreasureSphere'), self.handleEnterSphere)

    def handleEnterSphere(self, collEntry = None):
        localAvId = base.localAvatar.getDoId()
        if not self.fly:
            self.handleGrab(localAvId)
        self.d_requestGrab()

    def d_requestGrab(self):
        self.sendUpdate('requestGrab', [])

    def getSphereRadius(self):
        return 2.0

    def loadModel(self, modelPath, modelFindString = None):
        self.grabSound = base.loadSfx(self.grabSoundPath)
        self.rejectSound = base.loadSfx(self.rejectSoundPath)
        if self.nodePath == None:
            self.makeNodePath()
        else:
            self.treasure.getChildren().detach()
        model = loader.loadModel(modelPath)
        if modelFindString != None:
            model = model.find('**/' + modelFindString)
        model.instanceTo(self.treasure)
        return

    def makeNodePath(self):
        self.nodePath = NodePath(self.uniqueName('treasure'))
        if self.billboard:
            self.nodePath.setBillboardPointEye()
        self.nodePath.setScale(0.9 * self.scale)
        self.treasure = self.nodePath.attachNewNode('treasure')
        if self.shadow:
            if not self.dropShadow:
                self.dropShadow = loader.loadModel('phase_3/models/props/drop_shadow')
                self.dropShadow.setColor(0, 0, 0, 0.5)
                self.dropShadow.setPos(0, 0, 0.025)
                self.dropShadow.setScale(0.4 * self.scale)
                self.dropShadow.flattenLight()
            self.dropShadow.reparentTo(self.nodePath)
        collSphere = CollisionSphere(0, 0, 0, self.getSphereRadius())
        collSphere.setTangible(0)
        collNode = CollisionNode(self.uniqueName('treasureSphere'))
        collNode.setIntoCollideMask(WallBitmask)
        collNode.addSolid(collSphere)
        self.collNodePath = self.nodePath.attachNewNode(collNode)
        self.collNodePath.stash()

    def getParentNodePath(self):
        return render

    def setPosition(self, x, y, z):
        if not self.nodePath:
            self.makeNodePath()
        self.nodePath.reparentTo(self.getParentNodePath())
        self.nodePath.setPos(x, y, z + self.zOffset)
        self.collNodePath.unstash()

    def setGrab(self, avId):
        if avId == 0:
            return
        if self.fly or avId != base.localAvatar.getDoId():
            self.handleGrab(avId)

    def setReject(self):
        if self.treasureFlyTrack:
            self.treasureFlyTrack.finish()
            self.treasureFlyTrack = None
        base.playSfx(self.rejectSound, node=self.nodePath)
        self.treasureFlyTrack = Sequence(LerpColorScaleInterval(self.nodePath, 0.8, colorScale=VBase4(0, 0, 0, 0), startColorScale=VBase4(1, 1, 1, 1), blendType='easeIn'), LerpColorScaleInterval(self.nodePath, 0.2, colorScale=VBase4(1, 1, 1, 1), startColorScale=VBase4(0, 0, 0, 0), blendType='easeOut'), name=self.uniqueName('treasureFlyTrack'))
        self.treasureFlyTrack.start()
        return

    def handleGrab(self, avId):
        self.collNodePath.stash()
        self.avId = avId
        if self.cr.doId2do.has_key(avId):
            av = self.cr.doId2do[avId]
            self.av = av
        else:
            self.nodePath.detachNode()
            return
        if self.playSoundForRemoteToons or self.avId == base.localAvatar.getDoId():
            base.playSfx(self.grabSound, node=self.nodePath)
        if not self.fly:
            self.nodePath.detachNode()
            return
        self.nodePath.wrtReparentTo(av)
        if self.treasureFlyTrack:
            self.treasureFlyTrack.finish()
            self.treasureFlyTrack = None
        avatarGoneName = self.av.uniqueName('disable')
        self.accept(avatarGoneName, self.handleUnexpectedExit)
        flytime = 1.0
        track = Sequence(LerpPosInterval(self.nodePath, flytime, pos=Point3(0, 0, 3), startPos=self.nodePath.getPos(), blendType='easeInOut'), Func(self.nodePath.detachNode), Func(self.ignore, avatarGoneName))
        if self.shadow:
            self.treasureFlyTrack = Sequence(HideInterval(self.dropShadow), track, ShowInterval(self.dropShadow), name=self.uniqueName('treasureFlyTrack'))
        else:
            self.treasureFlyTrack = Sequence(track, name=self.uniqueName('treasureFlyTrack'))
        self.treasureFlyTrack.start()
        return

    def handleUnexpectedExit(self):
        self.notify.warning('While getting treasure, ' + str(self.avId) + ' disconnected.')
        if self.treasureFlyTrack:
            self.treasureFlyTrack.finish()
            self.treasureFlyTrack = None
        return

    def getStareAtNodeAndOffset(self):
        return (self.nodePath, Point3())

    def startAnimation(self):
        pass
