from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from direct.distributed import ClockDelta
from direct.showbase.PythonUtil import lerp
import math
from direct.directnotify import DirectNotifyGlobal
from pandac.PandaModules import NodePath
from direct.task import Task
from toontown.toonbase import ToontownGlobals
from direct.distributed import DistributedObject
from direct.distributed import DistributedNode
from direct.showbase import PythonUtil
from otp.avatar import ShadowCaster
import random
from otp.otpbase import OTPGlobals
from toontown.estate import GardenGlobals

def recurseParent(intoNode, ParentName):
    parent = intoNode.getParent(0)
    if not parent or parent.getName() == 'render':
        return 0
    elif parent.getName() == ParentName:
        return 1
    else:
        return recurseParent(parent, ParentName)


class DistributedLawnDecor(DistributedNode.DistributedNode, NodePath, ShadowCaster.ShadowCaster):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedLawnDecor')

    def __init__(self, cr):
        DistributedNode.DistributedNode.__init__(self, cr)
        NodePath.__init__(self, 'decor')
        ShadowCaster.ShadowCaster.__init__(self, False)
        self.plantPath = NodePath('plantPath')
        self.plantPath.reparentTo(self)
        self.defaultModel = 'phase_9/models/cogHQ/woodCrateB'
        self.messageName = None
        self.model = None
        self.colSphereNode = None
        self.rotateNode = None
        self.collSphereOffset = 0.0
        self.collSphereRadius = 1.0
        self.stickUp = 0.0
        self.movieNode = None
        self.shadowJoint = None
        self.shadowScale = 1
        self.expectingReplacement = 0
        self.movie = None
        return

    def setHeading(self, h):
        self.notify.debug('setting h')
        DistributedNode.DistributedNode.setH(self, h)

    def generateInit(self):
        self.notify.debug('generateInit')
        DistributedNode.DistributedNode.generateInit(self)

    def generate(self):
        self.notify.debug('generate')
        self.reparentTo(render)
        DistributedNode.DistributedNode.generate(self)

    def announceGenerate(self):
        self.notify.debug('announceGenerate')
        DistributedNode.DistributedNode.announceGenerate(self)
        self.doModelSetup()
        self.loadModel()
        self.setupShadow()
        self.makeMovieNode()
        self.stick2Ground()
        self.setupCollision()

    def doModelSetup(self):
        pass

    def disable(self):
        self.notify.debug('disable')
        self.finishMovies()
        self.handleExitPlot()
        self.ignoreAll()
        DistributedNode.DistributedNode.disable(self)
        if hasattr(self, 'nodePath'):
            self.nodePath.detachNode()

    def delete(self):
        self.notify.debug('delete')
        ShadowCaster.ShadowCaster.delete(self)
        self.unloadModel()
        DistributedNode.DistributedNode.delete(self)

    def loadModel(self):
        if not self.rotateNode:
            self.rotateNode = self.plantPath.attachNewNode('rotate')
        self.model = None
        if __dev__:
            self.model = loader.loadModel(self.defaultModel)
            self.model.setScale(0.4, 0.4, 0.1)
            self.model.reparentTo(self.rotateNode)
        return

    def setupShadow(self):
        self.shadowJoint = self.rotateNode.attachNewNode('shadow')
        self.initializeDropShadow(False)
        self.shadowJoint.setScale(self.shadowScale)
        self.setActiveShadow()

    def makeMovieNode(self):
        self.movieNode = self.rotateNode.attachNewNode('moviePos')
        self.movieNode.setPos(0, -3, 0)

    def setupCollision(self):
        self.messageName = self.uniqueName('enterplotSphere')
        self.messageStartName = self.uniqueName('plotSphere')
        self.exitMessageName = self.uniqueName('exitplotSphere')
        if self.collSphereOffset <= 0.1:
            colSphere = CollisionSphere(0, 0, 0, self.collSphereRadius)
        else:
            colSphere = CollisionTube(0, -self.collSphereOffset, 0, 0, self.collSphereOffset, 0, self.collSphereRadius)
        colSphere.setTangible(0)
        colNode = CollisionNode(self.messageStartName)
        colNode.addSolid(colSphere)
        colSphereNode = self.attachNewNode(colNode)
        self.colSphereNode = colSphereNode
        self.accept(self.messageName, self.handleEnterPlot)
        self.accept(self.exitMessageName, self.handleExitPlot)

    def handleEnterPlot(self, optional = None):
        self.notify.debug('handleEnterPlot %d' % self.doId)
        self.sendUpdate('plotEntered', [])

    def handleExitPlot(self, optional = None):
        if base.localAvatar.inGardenAction == self:
            base.localAvatar.handleEndPlantInteraction(self, replacement=self.expectingReplacement)

    def handleWatering(self):
        self.handleExitPlot()
        base.localAvatar.removeShovelRelatedDoId(self.doId)

    def unloadModel(self):
        if self.model:
            self.model.removeNode()
            del self.model
            self.model = None
        if hasattr(self, 'nodePath') and self.nodePath:
            self.nodePath.removeNode()
            self.nodePath = None
        taskMgr.remove(self.uniqueName('adjust tree'))
        return

    def setPos(self, x, y, z):
        DistributedNode.DistributedNode.setPos(self, x, y, z)
        self.stick2Ground()

    def setPosition(self, x, y, z):
        DistributedNode.DistributedNode.setPos(self, x, y, z)
        self.stick2Ground()

    def stick2Ground(self, taskfooler = 0):
        if self.isEmpty():
            return Task.done
        testPath = NodePath('testPath')
        testPath.reparentTo(render)
        cRay = CollisionRay(0.0, 0.0, 40000.0, 0.0, 0.0, -1.0)
        cRayNode = CollisionNode(self.uniqueName('estate-FloorRay'))
        cRayNode.addSolid(cRay)
        cRayNode.setFromCollideMask(OTPGlobals.FloorBitmask)
        cRayNode.setIntoCollideMask(BitMask32.allOff())
        cRayNodePath = testPath.attachNewNode(cRayNode)
        queue = CollisionHandlerQueue()
        picker = CollisionTraverser()
        picker.addCollider(cRayNodePath, queue)
        if self.movieNode:
            testPath.setPos(self.movieNode.getX(render), self.movieNode.getY(render), 0)
            picker.traverse(render)
            if queue.getNumEntries() > 0:
                queue.sortEntries()
                for index in range(queue.getNumEntries()):
                    entry = queue.getEntry(index)
                    if recurseParent(entry.getIntoNode(), 'terrain_DNARoot'):
                        self.movieNode.setZ(entry.getSurfacePoint(self)[2])

        testPath.setPos(self.getX(), self.getY(), 0)
        picker.traverse(render)
        if queue.getNumEntries() > 0:
            queue.sortEntries()
            for index in range(queue.getNumEntries()):
                entry = queue.getEntry(index)
                if recurseParent(entry.getIntoNode(), 'terrain_DNARoot'):
                    self.setZ(entry.getSurfacePoint(render)[2] + self.stickUp + 0.1)
                    self.stickParts()
                    return Task.done

        taskMgr.doMethodLater(1.0, self.stick2Ground, uniqueName('groundsticker'))
        return Task.done

    def stickParts(self):
        pass

    def setPlot(self, plot):
        self.plot = plot

    def setH(self, h):
        DistributedNode.DistributedNode.setH(self, h)

    def getPlot(self):
        return self.plot

    def setOwnerIndex(self, index):
        self.ownerIndex = index

    def getOwnerIndex(self):
        return self.ownerIndex

    def getOwnerId(self):
        retval = 0
        estate = base.cr.doFind('DistributedEstate')
        if estate and hasattr(estate, 'idList') and estate.idList:
            if self.ownerIndex < len(estate.idList):
                retval = estate.idList[self.ownerIndex]
        return retval

    def canBePicked(self):
        retval = True
        self.notify.debug('base.localAvatar.doId : %s' % base.localAvatar.doId)
        self.notify.debug('self.getOwnerId : %s ' % self.getOwnerId())
        self.notify.debug("statue's DoId : %s " % self.doId)
        if not hasattr(base, 'localAvatar') or not base.localAvatar.doId == self.getOwnerId():
            retval = False
        return retval

    def allowedToPick(self):
        return True

    def unlockPick(self):
        return True

    def handleRemove(self):
        if not self.canBePicked():
            self.notify.debug("I don't own this item, just returning")
            return
        base.localAvatar.hideShovelButton()
        base.localAvatar.hideWateringCanButton()
        self.startInteraction()
        self.sendUpdate('removeItem', [])

    def generateToonMoveTrack(self, toon):
        node = NodePath('tempNode')
        displacement = Vec3(toon.getPos(render) - self.getPos(render))
        displacement.setZ(0)
        displacement.normalize()
        movieDistance = self.movieNode.getDistance(self.rotateNode)
        displacement *= movieDistance
        node.reparentTo(render)
        node.setPos(displacement + self.getPos(render))
        node.lookAt(self)
        heading = PythonUtil.fitDestAngle2Src(toon.getH(render), node.getH(render))
        hpr = toon.getHpr(render)
        hpr.setX(heading)
        finalX = node.getX(render)
        finalY = node.getY(render)
        finalZ = node.getZ(render)
        node.removeNode()
        toonTrack = Sequence(Parallel(ActorInterval(toon, 'walk', loop=True, duration=1), Parallel(LerpPosInterval(toon, 1.0, Point3(finalX, finalY, toon.getZ(render)), fluid=True, bakeInStart=False)), LerpHprInterval(toon, 1.0, hpr=hpr)), Func(toon.loop, 'neutral'))
        return toonTrack

    def unprint(self, string):
        print string

    def startInteraction(self):
        place = base.cr.playGame.getPlace()
        if place:
            place.detectedGardenPlotUse()
            base.localAvatar.setInGardenAction(self)

    def finishInteraction(self):
        if hasattr(base.cr.playGame.getPlace(), 'detectedGardenPlotDone'):
            base.cr.playGame.getPlace().detectedGardenPlotDone()
            self.notify.debug('done interaction')
        else:
            self.notify.warning('base.cr.playGame.getPlace() does not have detectedGardenPlotDone')
        if hasattr(base, 'localAvatar'):
            base.localAvatar.handleEndPlantInteraction(self)

    def startCamIval(self, avId):
        track = Sequence()
        if avId == localAvatar.doId:
            track = Sequence(Func(base.localAvatar.disableSmartCameraViews), Func(base.localAvatar.setCameraPosForPetInteraction))
        return track

    def stopCamIval(self, avId):
        track = Sequence()
        if avId == localAvatar.doId:
            track = Sequence(Func(base.localAvatar.unsetCameraPosForPetInteraction), Wait(0.8), Func(base.localAvatar.enableSmartCameraViews))
        return track

    def canBeWatered(self):
        return 0

    def getShovelAction(self):
        return None

    def getShovelCommand(self):
        return None

    def canBePlanted(self):
        return 0

    def movieDone(self):
        self.sendUpdate('movieDone', [])

    def setMovie(self, mode, avId):
        if mode == GardenGlobals.MOVIE_FINISHPLANTING:
            self.doFinishPlantingTrack(avId)
        elif mode == GardenGlobals.MOVIE_REMOVE:
            self.doDigupTrack(avId)

    def finishMovies(self):
        if self.movie:
            self.movie.finish()
            self.movie = None
        return

    def doDigupTrack(self, avId):
        toon = base.cr.doId2do.get(avId)
        if not toon:
            return
        self.finishMovies()
        self.model.setTransparency(1)
        self.model.setAlphaScale(1)
        shovel = toon.attachShovel()
        shovel.hide()
        moveTrack = self.generateToonMoveTrack(toon)
        digupTrack = self.generateDigupTrack(toon)
        self.movie = Sequence(self.startCamIval(avId), moveTrack, Func(shovel.show), digupTrack)
        if avId == localAvatar.doId:
            self.expectingReplacement = 1
            self.movie.append(Func(self.movieDone))
        self.movie.start()

    def generateDigupTrack(self, toon):
        sound = loader.loadSfx('phase_5.5/audio/sfx/burrow.mp3')
        sound.setPlayRate(0.5)
        pos = self.model.getPos()
        pos.setZ(pos[2] - 1)
        track = Parallel()
        track.append(Sequence(ActorInterval(toon, 'start-dig'), Parallel(ActorInterval(toon, 'loop-dig', loop=1, duration=5.13), Sequence(Wait(0.25), SoundInterval(sound, node=toon, duration=0.55), Wait(0.8), SoundInterval(sound, node=toon, duration=0.55), Wait(1.35), SoundInterval(sound, node=toon, duration=0.55))), ActorInterval(toon, 'start-dig', playRate=-1), LerpFunc(self.model.setAlphaScale, fromData=1, toData=0, duration=1), Func(toon.loop, 'neutral'), Func(toon.detachShovel)))
        return track

    def doFinishPlantingTrack(self, avId):
        toon = base.cr.doId2do.get(avId)
        if not toon:
            return
        self.finishMovies()
        self.movie = Sequence()
        if avId == localAvatar.doId:
            self.startInteraction()
        if self.model:
            self.model.setTransparency(1)
            self.model.setAlphaScale(0)
            self.movie.append(LerpFunc(self.model.setAlphaScale, fromData=0, toData=1, duration=3))
        self.movie.append(self.stopCamIval(avId))
        self.movie.append(Func(toon.detachShovel))
        self.movie.append(Func(toon.loop, 'neutral'))
        if avId == localAvatar.doId:
            self.movie.append(Func(self.finishInteraction))
            self.movie.append(Func(self.movieDone))
            if hasattr(self, 'doResultDialog'):
                self.movie.append(Func(self.doResultDialog))
        self.movie.start()

    def interactionDenied(self, avId):
        if avId == localAvatar.doId:
            self.finishInteraction()
