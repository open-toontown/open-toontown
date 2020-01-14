from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from toontown.toonbase.ToontownGlobals import *
from .CrateGlobals import *
from direct.showbase.PythonUtil import fitSrcAngle2Dest
from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from . import MovingPlatform
from direct.task.Task import Task
from . import DistributedCrushableEntity

class DistributedCrate(DistributedCrushableEntity.DistributedCrushableEntity):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedCrate')
    UP_KEY = 'arrow_up'
    DOWN_KEY = 'arrow_down'
    LEFT_KEY = 'arrow_left'
    RIGHT_KEY = 'arrow_right'
    ModelPaths = ('phase_9/models/cogHQ/woodCrateB', 'phase_10/models/cashbotHQ/CBWoodCrate')

    def __init__(self, cr):
        DistributedCrushableEntity.DistributedCrushableEntity.__init__(self, cr)
        self.initNodePath()
        self.modelType = 0
        self.crate = None
        self.gridSize = 3.0
        self.tContact = 0
        self.tStick = 0.01
        self.moveTrack = None
        self.avMoveTrack = None
        self.avPushTrack = None
        self.crate = None
        self.crushTrack = None
        self.isLocalToon = 0
        self.stuckToCrate = 0
        self.upPressed = 0
        self.isPushing = 0
        self.creakSound = loader.loadSfx('phase_9/audio/sfx/CHQ_FACT_crate_effort.ogg')
        self.pushSound = loader.loadSfx('phase_9/audio/sfx/CHQ_FACT_crate_sliding.ogg')
        return

    def disable(self):
        self.ignoreAll()
        if self.moveTrack:
            self.moveTrack.pause()
            del self.moveTrack
        if self.avMoveTrack:
            self.avMoveTrack.pause()
            del self.avMoveTrack
        if self.avPushTrack:
            self.avPushTrack.pause()
            del self.avPushTrack
        if self.crate:
            self.crate.destroy()
            del self.crate
        if self.crushTrack:
            self.crushTrack.pause()
            del self.crushTrack
        taskMgr.remove(self.taskName('crushTask'))
        if self.pushable:
            self.__listenForCollisions(0)
            self.ignore('arrow_up')
            self.ignore('arrow_up-up')
        DistributedCrushableEntity.DistributedCrushableEntity.disable(self)

    def delete(self):
        DistributedCrushableEntity.DistributedCrushableEntity.delete(self)
        del self.creakSound
        del self.pushSound

    def generateInit(self):
        DistributedCrushableEntity.DistributedCrushableEntity.generateInit(self)

    def generate(self):
        DistributedCrushableEntity.DistributedCrushableEntity.generate(self)

    def announceGenerate(self):
        self.notify.debug('announceGenerate')
        DistributedCrushableEntity.DistributedCrushableEntity.announceGenerate(self)
        self.loadModel()
        self.modCrateCollisions()
        if self.pushable:
            self.__listenForCollisions(1)
            self.accept('arrow_up', self.__upKeyPressed)

    def modCrateCollisions(self):
        cNode = self.find('**/wall')
        cNode.setName(self.uniqueName('crateCollision'))
        cNode.setZ(-.8)
        colNode = self.find('**/collision')
        floor = colNode.find('**/MovingPlatform*')
        floor2 = floor.copyTo(colNode)
        floor2.setZ(-.8)

    def __upKeyPressed(self):
        self.ignore('arrow_up')
        self.accept('arrow_up-up', self.__upKeyReleased)
        self.upPressed = 1

    def __upKeyReleased(self):
        self.ignore('arrow_up-up')
        self.accept('arrow_up', self.__upKeyPressed)
        self.upPressed = 0
        if self.stuckToCrate:
            self.__resetStick()

    def loadModel(self):
        crateModel = loader.loadModel(DistributedCrate.ModelPaths[self.modelType])
        self.crate = MovingPlatform.MovingPlatform()
        self.crate.setupCopyModel(self.getParentToken(), crateModel, 'floor')
        self.setScale(1.0)
        self.crate.setScale(self.scale)
        self.crate.reparentTo(self)
        self.crate.flattenLight()

    def setScale(self, scale):
        if self.crate:
            self.crate.setScale(scale)

    def __listenForCollisions(self, on):
        if on:
            self.accept(self.uniqueName('entercrateCollision'), self.handleCollision)
        else:
            self.ignore(self.uniqueName('entercrateCollision'))

    def setPosition(self, x, y, z):
        self.setPos(x, y, z)

    def handleCollision(self, collEntry = None):
        if not self.upPressed:
            return
        crateNormal = Vec3(collEntry.getSurfaceNormal(self))
        relativeVec = base.localAvatar.getRelativeVector(self, crateNormal)
        relativeVec.normalize()
        worldVec = render.getRelativeVector(self, crateNormal)
        worldVec.normalize()
        offsetVec = Vec3(base.localAvatar.getPos(render) - self.getPos(render))
        offsetVec.normalize()
        offsetDot = offsetVec[0] * worldVec[0] + offsetVec[1] * worldVec[1]
        self.notify.debug('offsetDot = %s, world = %s, rel = %s' % (offsetDot, worldVec, offsetVec))
        if relativeVec.getY() < -0.7 and offsetDot > 0.9 and offsetVec.getZ() < 0.05:
            self.getCrateSide(crateNormal)
            self.tContact = globalClock.getFrameTime()
            self.__listenForCollisions(0)
            self.__listenForCancelEvents(1)
            self.__startStickTask(crateNormal, base.localAvatar.getPos(render))

    def setReject(self):
        self.notify.debug('setReject')
        self.sentRequest = 0
        if self.stuckToCrate:
            self.__resetStick()

    def __startStickTask(self, crateNormal, toonPos):
        self.__killStickTask()
        self.stuckToCrate = 1
        sTask = Task(self.__stickTask)
        sTask.crateNormal = crateNormal
        sTask.toonPos = toonPos
        taskMgr.add(sTask, self.taskName('stickTask'))

    def __killStickTask(self):
        taskMgr.remove(self.taskName('stickTask'))

    def __stickTask(self, task):
        tElapsed = globalClock.getFrameTime() - self.tContact
        if tElapsed > self.tStick:
            lToon = base.localAvatar
            self.isLocalToon = 1
            crateNormal = task.crateNormal
            crateWidth = 2.75 * self.scale
            offset = crateWidth + 1.5 + TorsoToOffset[lToon.style.torso]
            newPos = crateNormal * offset
            if self.avPushTrack:
                self.avPushTrack.pause()
            place = base.cr.playGame.getPlace()
            newHpr = CrateHprs[self.crateSide]
            h = lToon.getH(self)
            h = fitSrcAngle2Dest(h, newHpr[0])
            startHpr = Vec3(h, 0, 0)
            self.avPushTrack = Sequence(LerpPosHprInterval(lToon, 0.25, newPos, newHpr, startHpr=startHpr, other=self, blendType='easeInOut'), Func(place.fsm.request, 'push'), Func(self.__sendPushRequest, task.crateNormal), SoundInterval(self.creakSound, node=self))
            self.avPushTrack.start()
            return Task.done
        else:
            pos = task.toonPos
            base.localAvatar.setPos(task.toonPos)
            return Task.cont

    def getCrateSide(self, crateNormal):
        for i in range(len(CrateNormals)):
            dotP = CrateNormals[i].dot(crateNormal)
            if dotP > 0.9:
                self.crateSide = i

    def __sendPushRequest(self, crateNormal):
        self.notify.debug('__sendPushRequest')
        if self.crateSide != None:
            self.sentRequest = 1
            self.sendUpdate('requestPush', [self.crateSide])
        else:
            self.notify.debug("didn't send request")
        return

    def __listenForCancelEvents(self, on):
        self.notify.debug('%s, __listenForCancelEvents(%s)' % (self.doId, on))
        if on:
            self.accept('arrow_down', self.__resetStick)
            self.accept('arrow_left', self.__resetStick)
            self.accept('arrow_right', self.__resetStick)
        else:
            self.ignore('arrow_down')
            self.ignore('arrow_left')
            self.ignore('arrow_right')

    def setMoveTo(self, avId, x0, y0, z0, x1, y1, z1):
        self.notify.debug('setMoveTo')
        self.__moveCrateTo(Vec3(x0, y0, z0), Vec3(x1, y1, z1))
        isLocal = base.localAvatar.doId == avId
        if isLocal and self.stuckToCrate or not isLocal:
            self.__moveAvTo(avId, Vec3(x0, y0, z0), Vec3(x1, y1, z1))

    def __moveCrateTo(self, startPos, endPos):
        if self.moveTrack:
            self.moveTrack.finish()
            self.moveTrack = None
        self.moveTrack = Parallel(Sequence(LerpPosInterval(self, T_PUSH, endPos, startPos=startPos, fluid=1)), SoundInterval(self.creakSound, node=self), SoundInterval(self.pushSound, node=self, duration=T_PUSH, volume=0.2))
        self.moveTrack.start()
        return

    def __moveAvTo(self, avId, startPos, endPos):
        if self.avMoveTrack:
            self.avMoveTrack.finish()
            self.avMoveTrack = None
        av = base.cr.doId2do.get(avId)
        if av:
            avMoveTrack = Sequence()
            moveDir = endPos - startPos
            crateNormal = startPos - endPos
            crateNormal.normalize()
            crateWidth = 2.75 * self.scale
            offset = crateWidth + 1.5 + TorsoToOffset[av.style.torso]
            toonOffset = crateNormal * offset
            avMoveTrack.append(Sequence(LerpPosInterval(av, T_PUSH, toonOffset, startPos=toonOffset, other=self)))
            self.avMoveTrack = avMoveTrack
            self.avMoveTrack.start()
        return

    def __resetStick(self):
        self.notify.debug('__resetStick')
        self.__killStickTask()
        self.__listenForCancelEvents(0)
        self.__listenForCollisions(1)
        self.sendUpdate('setDone')
        if self.avPushTrack:
            self.avPushTrack.pause()
            del self.avPushTrack
            self.avPushTrack = None
        if self.avMoveTrack:
            self.avMoveTrack.pause()
            del self.avMoveTrack
            self.avMoveTrack = None
        base.cr.playGame.getPlace().fsm.request('walk')
        self.crateSide = None
        self.crateNormal = None
        self.isLocalToon = 0
        self.stuckToCrate = 0
        return

    def playCrushMovie(self, crusherId, axis):
        self.notify.debug('playCrushMovie')
        taskMgr.remove(self.taskName('crushTask'))
        taskMgr.add(self.crushTask, self.taskName('crushTask'), extraArgs=(crusherId, axis), priority=25)

    def crushTask(self, crusherId, axis):
        crusher = self.level.entities.get(crusherId, None)
        if crusher:
            crusherHeight = crusher.model.getPos(self)[2]
            maxHeight = self.pos[2] + self.scale
            minHeight = crusher.getPos(self)[2]
            minScale = minHeight / maxHeight
            self.notify.debug('cHeight= %s' % crusherHeight)
            if crusherHeight < maxHeight and crusherHeight >= minHeight:
                if crusherHeight == minHeight:
                    self.setScale(Vec3(1.2, 1.2, minScale))
                    taskMgr.doMethodLater(2, self.setScale, 'resetScale', extraArgs=(1,))
                    return Task.done
                else:
                    k = crusherHeight / maxHeight
                    sx = min(1 / k, 0.2)
                    self.setScale(Vec3(1 + sx, 1 + sx, k))
        return Task.cont

    def originalTry(self, axis):
        tSquash = 0.4
        if self.crushTrack:
            self.crushTrack.finish()
            del self.crushTrack
            self.crushTrack = None
        self.crushTrack = Sequence(LerpScaleInterval(self, tSquash, VBase3(1.2, 1.2, 0.25), blendType='easeInOut'), LerpColorScaleInterval(self, 2.0, VBase4(1, 1, 1, 0), blendType='easeInOut'), Wait(2.0), LerpScaleInterval(self, 0.1, VBase3(1, 1, 1), blendType='easeInOut'), LerpColorScaleInterval(self, 0.1, VBase4(1, 1, 1, 0), blendType='easeInOut'))
        self.crushTrack.start()
        return
