import random
from direct.showbase.DirectObject import DirectObject
from direct.interval.IntervalGlobal import LerpFunc, ActorInterval, LerpPosInterval
from direct.interval.MetaInterval import Sequence
from direct.directutil import Mopath
from direct.showbase import PythonUtil
from pandac.PandaModules import *
from toontown.toonbase import ToontownGlobals
from toontown.suit import Suit
from toontown.suit import SuitDNA
from toontown.battle import BattleProps
import CogdoUtil
import CogdoFlyingGameGlobals as Globals
from CogdoFlyingUtil import swapAvatarShadowPlacer
from direct.particles import ParticleEffect
from direct.particles import Particles
from direct.particles import ForceGroup

class CogdoFlyingObtacleFactory:

    def __init__(self):
        self._index = -1
        self._whirlwindModel = CogdoUtil.loadFlyingModel('whirlwind').find('**/whirlwind')
        self._fanModel = CogdoUtil.loadFlyingModel('streamer').find('**/streamer')

    def destroy(self):
        self._whirlwindModel.removeNode()
        del self._whirlwindModel
        self._fanModel.removeNode()
        del self._fanModel
        if Globals.Level.AddParticlesToStreamers:
            self.f.cleanup()
            del self.f

    def createFan(self):
        self._index += 1
        return CogdoFlyingFan(self._index, self._fanModel)

    def createFlyingMinion(self, motionPath = None):
        self._index += 1
        return CogdoFlyingMinionFlying(self._index, motionPath=motionPath)

    def createWalkingMinion(self, motionPath = None):
        self._index += 1
        return CogdoFlyingMinionWalking(self._index, motionPath=motionPath)

    def createWhirlwind(self, motionPath = None):
        self._index += 1
        return CogdoFlyingWhirlwind(self._index, self._whirlwindModel, motionPath=motionPath)

    def createStreamerParticles(self, color1, color2, amp):
        self.f = ParticleEffect.ParticleEffect('streamer_particles')
        p0 = Particles.Particles('particles-1')
        p0.setFactory('PointParticleFactory')
        p0.setRenderer('SparkleParticleRenderer')
        p0.setEmitter('RingEmitter')
        p0.setPoolSize(80)
        p0.setBirthRate(0.05)
        p0.setLitterSize(100)
        p0.setLitterSpread(0)
        p0.factory.setLifespanBase(3.0)
        p0.factory.setLifespanSpread(0.5)
        p0.factory.setMassBase(1.0)
        p0.factory.setMassSpread(0.0)
        p0.factory.setTerminalVelocityBase(5.0)
        p0.factory.setTerminalVelocitySpread(1.0)
        p0.renderer.setAlphaMode(BaseParticleRenderer.PRALPHAOUT)
        p0.renderer.setUserAlpha(1.0)
        p0.renderer.setCenterColor(color1)
        p0.renderer.setEdgeColor(color2)
        p0.renderer.setBirthRadius(0.3)
        p0.renderer.setDeathRadius(0.3)
        p0.renderer.setLifeScale(SparkleParticleRenderer.SPNOSCALE)
        p0.emitter.setEmissionType(BaseParticleEmitter.ETRADIATE)
        p0.emitter.setAmplitude(0)
        p0.emitter.setAmplitudeSpread(0)
        f0 = ForceGroup.ForceGroup('Gravity')
        force0 = LinearVectorForce(Vec3(0.0, 0.0, 10.0), 1.0, 0)
        force0.setVectorMasks(1, 1, 1)
        force0.setActive(1)
        f0.addForce(force0)
        self.f.addForceGroup(f0)
        p0.emitter.setRadius(5.0)
        self.f.addParticles(p0)
        self.f.setPos(0, 0, 0)
        self.f.setHpr(0, 0, 0)
        return self.f


class CogdoFlyingObstacle(DirectObject):
    EnterEventName = 'CogdoFlyingObstacle_Enter'
    ExitEventName = 'CogdoFlyingObstacle_Exit'
    MotionTypes = PythonUtil.Enum(('BackForth', 'Loop'))

    def __init__(self, type, index, model, collSolid, motionPath = None, motionPattern = None, blendMotion = True, instanceModel = True):
        self.type = type
        self.index = index
        name = 'CogdoFlyingObstacle-%s-%i' % (self.type, self.index)
        if instanceModel:
            self.model = NodePath(name)
            model.instanceTo(self.model)
        else:
            self.model = model
            self.model.setName(name)
        self.currentT = 0.0
        self.direction = 1.0
        self.collNode = None
        self._initCollisions(name, collSolid)
        self.motionPath = motionPath
        self.motionPattern = motionPattern
        self.motionSequence = None
        if blendMotion:
            blendType = 'easeInOut'
        else:
            blendType = 'noBlend'
        if motionPath is not None:

            def moveObstacle(value):
                self.motionPath.goTo(self.model, value)

            self.motionPath = Mopath.Mopath(name='obstacle-%i' % self.index)
            self.motionPath.loadNodePath(motionPath)
            dur = self.motionPath.getMaxT()
            self.motionSequence = Sequence(name='%s.obstacle-%i-motionSequence' % (self.__class__.__name__, self.index))
            movePart1 = LerpFunc(moveObstacle, fromData=0.0, toData=self.motionPath.getMaxT(), duration=dur, blendType=blendType)
            self.motionSequence.append(movePart1)
            if self.motionPattern == CogdoFlyingObstacle.MotionTypes.BackForth:
                movePart2 = LerpFunc(moveObstacle, fromData=self.motionPath.getMaxT(), toData=0.0, duration=dur, blendType=blendType)
                self.motionSequence.append(movePart2)
        return

    def _initCollisions(self, name, collSolid):
        self.collName = name
        self.collSolid = collSolid
        self.collSolid.setTangible(0)
        self.collNode = CollisionNode(self.collName)
        self.collNode.setIntoCollideMask(ToontownGlobals.WallBitmask)
        self.collNode.addSolid(self.collSolid)
        self.collNodePath = self.model.attachNewNode(self.collNode)
        self.collNodePath.hide()
        self.accept('enter' + self.collName, self._handleEnterCollision)
        self.accept('exit' + self.collName, self._handleExitCollision)

    def disable(self):
        if self.collNode is not None:
            self.collNode.setIntoCollideMask(BitMask32(0))
        return

    def enable(self):
        if self.collNode is not None:
            self.collNode.setIntoCollideMask(ToontownGlobals.WallBitmask)
        return

    def startMoving(self, elapsedTime = 0.0):
        if self.motionSequence is not None:
            self.motionSequence.loop()
            self.motionSequence.setT(elapsedTime % self.motionSequence.getDuration())
        return

    def stopMoving(self):
        if self.motionSequence is not None:
            self.motionSequence.pause()
        return

    def destroy(self):
        self.ignoreAll()
        if self.motionSequence is not None:
            self.motionSequence.clearToInitial()
            del self.motionSequence
        del self.collSolid
        self.collNodePath.removeNode()
        del self.collNodePath
        del self.collNode
        self.model.removeNode()
        del self.model
        del self.motionPath
        return

    def update(self, dt):
        pass

    def hide(self):
        self.ignoreAll()
        self.model.hide()
        self.collNode.setIntoCollideMask(BitMask32(0))

    def _handleEnterCollision(self, collEntry):
        messenger.send(CogdoFlyingObstacle.EnterEventName, [self, collEntry])

    def _handleExitCollision(self, collEntry):
        messenger.send(CogdoFlyingObstacle.ExitEventName, [self, collEntry])


from pandac.PandaModules import TransformState

class CogdoFlyingWhirlwind(CogdoFlyingObstacle):

    def __init__(self, index, model, motionPath = None):
        collSolid = CollisionTube(0, 0, 0, 0, 0, Globals.Gameplay.WhirlwindCollisionTubeHeight, Globals.Gameplay.WhirlwindCollisionTubeRadius)
        CogdoFlyingObstacle.__init__(self, Globals.Level.ObstacleTypes.Whirlwind, index, model, collSolid, motionPath=motionPath, motionPattern=CogdoFlyingObstacle.MotionTypes.BackForth)
        self.t = 0.0
        self._initModel()

    def _initModel(self):
        self.model.setDepthWrite(False)
        self._texStage = self.model.findTextureStage('*')
        self._soundIval = base.cogdoGameAudioMgr.createSfxIval('whirlwind', source=self.model)
        self.model.setBin('transparent', self.index)

    def startMoving(self, elapsedTime):
        CogdoFlyingObstacle.startMoving(self, elapsedTime)
        self.t = 0.0
        self._soundIval.loop()

    def update(self, dt):
        self.t += dt
        trans = TransformState.makePos((self.t, -self.t, 0))
        self.model.setTexTransform(self._texStage, trans)
        trans = TransformState.makePos((self.t * 2.0, -self.t * 2.0, 0))

    def stopMoving(self):
        CogdoFlyingObstacle.stopMoving(self)
        self._soundIval.pause()

    def destroy(self):
        self._soundIval.clearToInitial()
        del self._soundIval
        CogdoFlyingObstacle.destroy(self)


class CogdoFlyingMinion(CogdoFlyingObstacle):

    def __init__(self, index, collSolid, motionPath = None):
        self.prop = None
        self.suit = Suit.Suit()
        d = SuitDNA.SuitDNA()
        d.newSuit(Globals.Gameplay.MinionDnaName)
        self.suit.setDNA(d)
        self.suit.setScale(Globals.Gameplay.MinionScale)
        swapAvatarShadowPlacer(self.suit, 'minion-%sShadowPlacer' % index)
        self.mopathNodePath = NodePath('mopathNodePath')
        self.suit.reparentTo(self.mopathNodePath)
        CogdoFlyingObstacle.__init__(self, Globals.Level.ObstacleTypes.Minion, index, self.mopathNodePath, collSolid, motionPath=motionPath, motionPattern=CogdoFlyingObstacle.MotionTypes.Loop, blendMotion=False, instanceModel=False)
        self.lastPos = None
        self.suit.loop('neutral')
        return

    def attachPropeller(self):
        if self.prop is None:
            self.prop = BattleProps.globalPropPool.getProp('propeller')
            head = self.suit.find('**/joint_head')
            self.prop.reparentTo(head)
        return

    def detachPropeller(self):
        if self.prop:
            self.prop.cleanup()
            self.prop.removeNode()
            self.prop = None
        return

    def startMoving(self, elapsedTime):
        CogdoFlyingObstacle.startMoving(self, elapsedTime)

    def stopMoving(self):
        CogdoFlyingObstacle.stopMoving(self)

    def update(self, dt):
        CogdoFlyingObstacle.update(self, dt)
        self.currPos = self.mopathNodePath.getPos()
        if self.lastPos != None:
            vec = self.currPos - self.lastPos
            self.mopathNodePath.lookAt(self.currPos + vec)
        self.mopathNodePath.setP(0)
        self.lastPos = self.mopathNodePath.getPos()
        return

    def destroy(self):
        self.mopathNodePath.removeNode()
        del self.mopathNodePath
        self.suit.cleanup()
        self.suit.removeNode()
        self.suit.delete()
        CogdoFlyingObstacle.destroy(self)


class CogdoFlyingMinionFlying(CogdoFlyingMinion):

    def __init__(self, index, motionPath = None):
        radius = Globals.Gameplay.FlyingMinionCollisionRadius
        offset = Globals.Gameplay.FlyingMinionCollisionHeightOffset
        collSolid = CollisionSphere(0, 0, offset, radius)
        CogdoFlyingMinion.__init__(self, index, collSolid, motionPath)
        self.attachPropeller()
        self.propTrack = Sequence(ActorInterval(self.prop, 'propeller', startFrame=0, endFrame=14))
        dur = Globals.Gameplay.FlyingMinionFloatTime
        offset = Globals.Gameplay.FlyingMinionFloatOffset
        suitPos = self.suit.getPos()
        upperPos = suitPos + Point3(0.0, 0.0, offset / 2.0)
        lowerPos = suitPos + Point3(0.0, 0.0, -offset / 2.0)
        self.floatSequence = Sequence(LerpPosInterval(self.suit, dur / 4.0, startPos=suitPos, pos=upperPos, blendType='easeInOut'), LerpPosInterval(self.suit, dur / 2.0, startPos=upperPos, pos=lowerPos, blendType='easeInOut'), LerpPosInterval(self.suit, dur / 4.0, startPos=lowerPos, pos=suitPos, blendType='easeInOut'), name='%s.floatSequence%i' % (self.__class__.__name__, self.index))

    def startMoving(self, elapsedTime):
        CogdoFlyingMinion.startMoving(self, elapsedTime)
        self.floatSequence.loop(elapsedTime)
        self.propTrack.loop(elapsedTime)
        self.suit.pose('landing', 0)

    def stopMoving(self):
        CogdoFlyingMinion.stopMoving(self)
        self.floatSequence.clearToInitial()
        self.propTrack.pause()

    def destroy(self):
        self.floatSequence.clearToInitial()
        del self.floatSequence
        self.propTrack.clearToInitial()
        del self.propTrack
        CogdoFlyingMinion.destroy(self)


class CogdoFlyingMinionWalking(CogdoFlyingMinion):

    def __init__(self, index, motionPath = None):
        radius = Globals.Gameplay.WalkingMinionCollisionRadius
        offset = Globals.Gameplay.WalkingMinionCollisionHeightOffset
        collSolid = CollisionSphere(0, 0, offset, radius)
        CogdoFlyingMinion.__init__(self, index, collSolid, motionPath)

    def startMoving(self, elapsedTime):
        CogdoFlyingMinion.startMoving(self, elapsedTime)
        self.suit.loop('walk')

    def stopMoving(self):
        CogdoFlyingMinion.stopMoving(self)
        self.suit.loop('neutral')


class CogdoFlyingFan(CogdoFlyingObstacle):

    def __init__(self, index, model, motionPath = None):
        collSolid = CollisionTube(0, 0, 0, 0, 0, Globals.Gameplay.FanCollisionTubeHeight, Globals.Gameplay.FanCollisionTubeRadius)
        CogdoFlyingObstacle.__init__(self, Globals.Level.ObstacleTypes.Fan, index, model, collSolid)
        self.streamers = self.model.findAllMatches('**/streamer*')
        self._initIntervals()

    def _initIntervals(self):
        self.streamerIvals = []
        minDur = Globals.Gameplay.FanStreamerMinDuration
        maxDur = Globals.Gameplay.FanStreamerMaxDuration
        for streamer in self.streamers:
            dur = random.uniform(minDur, maxDur)
            streamerLerp = LerpFunc(streamer.setH, fromData=0.0, toData=360.0, duration=dur, name='%s.streamerLerp%i-%s' % (self.__class__.__name__, self.index, streamer.getName()))
            self.streamerIvals.append(streamerLerp)

    def startMoving(self, elapsedTime = 0.0):
        CogdoFlyingObstacle.startMoving(self, elapsedTime)
        timeDelay = 0.0
        maxDur = Globals.Gameplay.FanStreamerMaxDuration
        for ival in self.streamerIvals:
            taskName = 'delayedStreamerSpinTask-fan-%i-%s' % (self.index, ival.getName())
            taskMgr.doMethodLater(timeDelay, ival.loop, taskName, extraArgs=[])
            timeDelay += maxDur / (len(self.streamers) - 1)

    def stopMoving(self):
        CogdoFlyingObstacle.stopMoving(self)
        taskMgr.removeTasksMatching('delayedStreamerSpinTask-fan-%i*' % self.index)
        for streamerLerp in self.streamerIvals:
            streamerLerp.pause()

    def setBlowDirection(self):
        tempNodePath = NodePath('temp')
        tempNodePath.reparentTo(self.model)
        tempNodePath.setPos(0, 0, 1)
        self.blowVec = tempNodePath.getPos(render) - self.model.getPos(render)
        self.blowVec.normalize()
        tempNodePath.removeNode()
        del tempNodePath

    def getBlowDirection(self):
        return Vec3(self.blowVec)

    def destroy(self):
        taskMgr.removeTasksMatching('delayedStreamerSpinTask-fan-%i*' % self.index)
        for streamerLerp in self.streamerIvals:
            streamerLerp.clearToInitial()

        del self.streamerIvals[:]
        CogdoFlyingObstacle.destroy(self)
        del self.blowVec
