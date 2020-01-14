import math
from direct.actor.Actor import Actor
from direct.interval.ActorInterval import ActorInterval
from direct.interval.MetaInterval import Sequence, Parallel
from direct.interval.FunctionInterval import Func, Wait
from direct.interval.SoundInterval import SoundInterval
from direct.interval.LerpInterval import LerpScaleInterval, LerpFunc
from direct.showbase.PythonUtil import bound as clamp
from direct.task import Task
from direct.fsm.FSM import FSM
from pandac.PandaModules import CollisionTube, CollisionNode, CollisionSphere
from pandac.PandaModules import Point3, Vec4, NodePath, TextNode, Mat4
from toontown.toonbase import ToontownGlobals
from toontown.battle.BattleProps import globalPropPool
from toontown.battle.BattleSounds import globalBattleSoundCache
from . import PartyGlobals

class PartyCogManager:

    def __init__(self):
        self.cogs = []

    def generateCog(self, parentNode, bounceSpeed = 3, bounceHeight = 1, rotateSpeed = 1, heightShift = 1, xMoveSpeed = 0, xMoveDistance = 0, bounceOffset = 0):
        cog = PartyCog(parentNode, len(self.cogs), bounceSpeed, bounceHeight, rotateSpeed, heightShift, xMoveSpeed, xMoveDistance, bounceOffset)
        self.cogs.append(cog)
        return cog

    def unload(self):
        for cog in self.cogs:
            cog.unload()

    def updateDistances(self, distances):
        for i in range(len(distances)):
            self.cogs[i].updateDistance(distances[i])


class PartyCog(FSM):
    notify = directNotify.newCategory('PartyCog')
    HpTextGenerator = TextNode('HpTextGenerator')
    hpText = None
    height = 7

    def __init__(self, parentNode, id, bounceSpeed = 3, bounceHeight = 1, rotateSpeed = 1, heightShift = 1, xMoveSpeed = 0, xMoveDistance = 0, bounceOffset = 0):
        self.id = id
        FSM.__init__(self, 'PartyCogFSM-%d' % self.id)
        self.showFacingStatus = False
        self.xMoveSpeed = xMoveSpeed
        self.xMoveDistance = xMoveDistance
        self.heightShift = heightShift
        self.bounceSpeed = bounceSpeed
        self.bounceHeight = bounceHeight
        self.rotateSpeed = rotateSpeed
        self.parentNode = parentNode
        self.bounceOffset = bounceOffset
        self.hitInterval = None
        self.kaboomTrack = None
        self.resetRollIval = None
        self.netTimeSentToStartByHit = 0
        self.load()
        self.request('Down')
        return

    def load(self):
        self.root = NodePath('PartyCog-%d' % self.id)
        self.root.reparentTo(self.parentNode)
        path = 'phase_13/models/parties/cogPinata_'
        self.actor = Actor(path + 'actor', {'idle': path + 'idle_anim',
         'down': path + 'down_anim',
         'up': path + 'up_anim',
         'bodyHitBack': path + 'bodyHitBack_anim',
         'bodyHitFront': path + 'bodyHitFront_anim',
         'headHitBack': path + 'headHitBack_anim',
         'headHitFront': path + 'headHitFront_anim'})
        self.actor.reparentTo(self.root)
        self.temp_transform = Mat4()
        self.head_locator = self.actor.attachNewNode('temphead')
        self.bodyColl = CollisionTube(0, 0, 1, 0, 0, 5.75, 0.75)
        self.bodyColl.setTangible(1)
        self.bodyCollNode = CollisionNode('PartyCog-%d-Body-Collision' % self.id)
        self.bodyCollNode.setCollideMask(ToontownGlobals.PieBitmask)
        self.bodyCollNode.addSolid(self.bodyColl)
        self.bodyCollNodePath = self.root.attachNewNode(self.bodyCollNode)
        self.headColl = CollisionTube(0, 0, 3, 0, 0, 3.0, 1.5)
        self.headColl.setTangible(1)
        self.headCollNode = CollisionNode('PartyCog-%d-Head-Collision' % self.id)
        self.headCollNode.setCollideMask(ToontownGlobals.PieBitmask)
        self.headCollNode.addSolid(self.headColl)
        self.headCollNodePath = self.root.attachNewNode(self.headCollNode)
        self.arm1Coll = CollisionSphere(1.65, 0, 3.95, 1.0)
        self.arm1Coll.setTangible(1)
        self.arm1CollNode = CollisionNode('PartyCog-%d-Arm1-Collision' % self.id)
        self.arm1CollNode.setCollideMask(ToontownGlobals.PieBitmask)
        self.arm1CollNode.addSolid(self.arm1Coll)
        self.arm1CollNodePath = self.root.attachNewNode(self.arm1CollNode)
        self.arm2Coll = CollisionSphere(-1.65, 0, 3.45, 1.0)
        self.arm2Coll.setTangible(1)
        self.arm2CollNode = CollisionNode('PartyCog-%d-Arm2-Collision' % self.id)
        self.arm2CollNode.setCollideMask(ToontownGlobals.PieBitmask)
        self.arm2CollNode.addSolid(self.arm2Coll)
        self.arm2CollNodePath = self.root.attachNewNode(self.arm2CollNode)
        splatName = 'splat-creampie'
        self.splat = globalPropPool.getProp(splatName)
        self.splat.setBillboardPointEye()
        self.splatType = globalPropPool.getPropType(splatName)
        self.pieHitSound = globalBattleSoundCache.getSound('AA_wholepie_only.ogg')
        self.upSound = globalBattleSoundCache.getSound('AV_jump_to_side.ogg')
        self.hole = loader.loadModel('phase_13/models/parties/cogPinataHole')
        self.hole.setTransparency(True)
        self.hole.setP(-90.0)
        self.hole.setScale(3)
        self.hole.setBin('ground', 3)
        self.hole.reparentTo(self.parentNode)

    def unload(self):
        self.request('Off')
        self.clearHitInterval()
        if self.hole is not None:
            self.hole.removeNode()
            self.hole = None
        if self.actor is not None:
            self.actor.cleanup()
            self.actor.removeNode()
            self.actor = None
        if self.root is not None:
            self.root.removeNode()
            self.root = None
        if self.kaboomTrack is not None and self.kaboomTrack.isPlaying():
            self.kaboomTrack.finish()
        self.kaboomTrack = None
        if self.resetRollIval is not None and self.resetRollIval.isPlaying():
            self.resetRollIval.finish()
        self.resetRollIval = None
        if self.hitInterval is not None and self.hitInterval.isPlaying():
            self.hitInterval.finish()
        self.hitInterval = None
        del self.upSound
        del self.pieHitSound
        return

    def enterStatic(self):
        pass

    def exitStatic(self):
        pass

    def enterActive(self, startTime):
        self.root.setR(0.0)
        updateTask = Task.Task(self.updateTask)
        updateTask.startTime = startTime
        taskMgr.add(updateTask, 'PartyCog.update-%d' % self.id)

    def exitActive(self):
        taskMgr.remove('PartyCog.update-%d' % self.id)
        taskMgr.remove('PartyCog.bounceTask-%d' % self.id)
        self.clearHitInterval()
        self.resetRollIval = self.root.hprInterval(0.5, Point3(self.root.getH(), 0.0, 0.0), blendType='easeInOut')
        self.resetRollIval.start()
        self.actor.stop()

    def enterDown(self):
        if self.oldState == 'Off':
            downAnimControl = self.actor.getAnimControl('down')
            self.actor.pose('down', downAnimControl.getNumFrames() - 1)
            return
        self.clearHitInterval()
        startScale = self.hole.getScale()
        endScale = Point3(5, 5, 5)
        self.hitInterval = Sequence(LerpFunc(self.setAlongSpline, duration=1.0, fromData=self.currentT, toData=0.0), LerpScaleInterval(self.hole, duration=0.175, scale=endScale, startScale=startScale, blendType='easeIn'), Parallel(SoundInterval(self.upSound, volume=0.6, node=self.actor, cutOff=PartyGlobals.PARTY_COG_CUTOFF), ActorInterval(self.actor, 'down', loop=0)), LerpScaleInterval(self.hole, duration=0.175, scale=Point3(3, 3, 3), startScale=endScale, blendType='easeOut'))
        self.hitInterval.start()

    def exitDown(self):
        self.root.setR(0.0)
        self.root.setH(0.0)
        self.targetDistance = 0.0
        self.targetFacing = 0.0
        self.currentT = 0.0
        self.setAlongSpline(0.0)
        self.clearHitInterval()
        startScale = self.hole.getScale()
        endScale = Point3(5, 5, 5)
        self.hitInterval = Sequence(LerpScaleInterval(self.hole, duration=0.175, scale=endScale, startScale=startScale, blendType='easeIn'), Parallel(SoundInterval(self.upSound, volume=0.6, node=self.actor, cutOff=PartyGlobals.PARTY_COG_CUTOFF), ActorInterval(self.actor, 'up', loop=0)), Func(self.actor.loop, 'idle'), LerpScaleInterval(self.hole, duration=0.175, scale=Point3(3, 3, 3), startScale=endScale, blendType='easeOut'))
        self.hitInterval.start()

    def filterDown(self, request, args):
        if request == 'Down':
            return None
        else:
            return self.defaultFilter(request, args)
        return None

    def setEndPoints(self, start, end, amplitude = 1.7):
        self.sinAmplitude = amplitude
        self.sinPeriod = (end.getX() - start.getX()) / 2
        self.sinDisplacement = start.getY()
        self.startPoint = start
        self.endPoint = end
        self.currentT = 0.0
        self.targetDistance = 0.0
        self.currentFacing = 0.0
        self.targetFacing = 0.0
        self.setAlongSpline(self.currentT)
        self.hole.setPos(self.root.getPos())
        self.hole.setZ(0.02)

    def rockBackAndForth(self, task):
        t = task.startTime + task.time
        angle = math.sin(t) * 20.0
        self.root.setR(angle)
        return task.cont

    def updateDistance(self, distance):
        self.targetDistance = clamp(distance, -1.0, 1.0)

    def updateTask(self, task):
        self.rockBackAndForth(task)
        if self.targetDistance > self.currentT:
            self.currentT += min(0.01, self.targetDistance - self.currentT)
            self.setAlongSpline(self.currentT)
        elif self.targetDistance < self.currentT:
            self.currentT += max(-0.01, self.targetDistance - self.currentT)
            self.setAlongSpline(self.currentT)
        if self.currentT < 0.0:
            self.targetFacing = -90.0
        elif self.currentT > 0.0:
            self.targetFacing = 90.0
        else:
            self.targetFacing = 0.0
        if self.targetFacing > self.currentFacing:
            self.currentFacing += min(10, self.targetFacing - self.currentFacing)
        elif self.targetFacing < self.currentFacing:
            self.currentFacing += max(-10, self.targetFacing - self.currentFacing)
        self.root.setH(self.currentFacing)
        return task.cont

    def setAlongSpline(self, t):
        t = t + 1.0
        dist = (self.endPoint.getX() - self.startPoint.getX()) / 2.0
        x = self.startPoint.getX() + t * dist
        y = self.startPoint.getY() - math.sin(t * 2 * math.pi) * self.sinAmplitude
        self.root.setPos(x, y, 0)

    def startBounce(self):
        taskMgr.add(self.bounce, 'PartyCog.bounceTask-%d' % self.id)

    def bounce(self, task):
        self.root.setZ(math.sin((self.bounceOffset + task.time) * self.bounceSpeed) * self.bounceHeight + self.heightShift)
        return task.cont

    def setPos(self, position):
        self.root.setPos(position)

    def respondToPieHit(self, timestamp, position, hot = False, direction = 1.0):
        if self.netTimeSentToStartByHit < timestamp:
            self.__showSplat(position, direction, hot)
            if self.netTimeSentToStartByHit < timestamp:
                self.netTimeSentToStartByHit = timestamp
        else:
            self.notify.debug('respondToPieHit self.netTimeSentToStartByHit = %s' % self.netTimeSentToStartByHit)

    def clearHitInterval(self):
        if self.hitInterval is not None and self.hitInterval.isPlaying():
            self.hitInterval.clearToInitial()
        return

    def __showSplat(self, position, direction, hot = False):
        if self.kaboomTrack is not None and self.kaboomTrack.isPlaying():
            self.kaboomTrack.finish()
        self.clearHitInterval()
        splatName = 'splat-creampie'
        self.splat = globalPropPool.getProp(splatName)
        self.splat.setBillboardPointEye()
        self.splat.reparentTo(render)
        self.splat.setPos(self.root, position)
        self.splat.setAlphaScale(1.0)
        if not direction == 1.0:
            self.splat.setColorScale(PartyGlobals.CogActivitySplatColors[0])
            if self.currentFacing > 0.0:
                facing = 'HitFront'
            else:
                facing = 'HitBack'
        else:
            self.splat.setColorScale(PartyGlobals.CogActivitySplatColors[1])
            if self.currentFacing > 0.0:
                facing = 'HitBack'
            else:
                facing = 'HitFront'
        if hot:
            targetscale = 0.75
            part = 'head'
        else:
            targetscale = 0.5
            part = 'body'

        def setSplatAlpha(amount):
            self.splat.setAlphaScale(amount)

        self.hitInterval = Sequence(ActorInterval(self.actor, part + facing, loop=0), Func(self.actor.loop, 'idle'))
        self.hitInterval.start()
        self.kaboomTrack = Parallel(SoundInterval(self.pieHitSound, volume=1.0, node=self.actor, cutOff=PartyGlobals.PARTY_COG_CUTOFF), Sequence(Func(self.splat.showThrough), Parallel(Sequence(LerpScaleInterval(self.splat, duration=0.175, scale=targetscale, startScale=Point3(0.1, 0.1, 0.1), blendType='easeOut'), Wait(0.175)), Sequence(Wait(0.1), LerpFunc(setSplatAlpha, duration=1.0, fromData=1.0, toData=0.0, blendType='easeOut'))), Func(self.splat.cleanup), Func(self.splat.removeNode)))
        self.kaboomTrack.start()
        return

    def showHitScore(self, number, scale = 1):
        if number <= 0:
            return
        if self.hpText:
            self.hideHitScore()
        self.HpTextGenerator.setFont(ToontownGlobals.getSignFont())
        if number < 0:
            self.HpTextGenerator.setText(str(number))
        else:
            self.HpTextGenerator.setText('+' + str(number))
        self.HpTextGenerator.clearShadow()
        self.HpTextGenerator.setAlign(TextNode.ACenter)
        r = 1
        g = 1
        b = 0
        a = 1
        self.HpTextGenerator.setTextColor(r, g, b, a)
        self.hpTextNode = self.HpTextGenerator.generate()
        self.hpText = render.attachNewNode(self.hpTextNode)
        self.hpText.setScale(scale)
        self.hpText.setBillboardPointEye()
        self.hpText.setBin('fixed', 100)
        self.hpText.setPos(self.root, 0, 0, self.height / 2)
        seq = Task.sequence(self.hpText.lerpPos(Point3(self.root.getX(render), self.root.getY(render), self.root.getZ(render) + self.height + 1.0), 0.25, blendType='easeOut'), Task.pause(0.25), self.hpText.lerpColor(Vec4(r, g, b, a), Vec4(r, g, b, 0), 0.1), Task.Task(self.__hideHitScoreTask))
        taskMgr.add(seq, 'PartyCogHpText' + str(self.id))

    def __hideHitScoreTask(self, task):
        self.hideHitScore()
        return Task.done

    def hideHitScore(self):
        if self.hpText:
            taskMgr.remove('PartyCogHpText' + str(self.id))
            self.hpText.removeNode()
            self.hpText = None
        return

    def getHeadLocation(self):
        self.actor.getJoints(jointName='head')[0].getNetTransform(self.temp_transform)
        self.head_locator.setMat(self.temp_transform)
        return self.head_locator.getZ(self.root)
