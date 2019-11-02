from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from direct.actor import Actor
from otp.avatar import Avatar
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from direct.fsm import FSM
from direct.fsm import State
from toontown.toonbase import TTLocalizer
from toontown.battle import BattleParticles
import Suit
from direct.task.Task import Task
import SuitDNA
from toontown.battle import BattleProps
from direct.showbase.PythonUtil import Functor
import string
import types
GenericModel = 'phase_9/models/char/bossCog'
ModelDict = {'s': 'phase_9/models/char/sellbotBoss',
 'm': 'phase_10/models/char/cashbotBoss',
 'l': 'phase_11/models/char/lawbotBoss',
 'c': 'phase_12/models/char/bossbotBoss'}
AnimList = ('Ff_speech', 'ltTurn2Wave', 'wave', 'Ff_lookRt', 'turn2Fb', 'Ff_neutral', 'Bb_neutral', 'Ff2Bb_spin', 'Bb2Ff_spin', 'Fb_neutral', 'Bf_neutral', 'Fb_firstHit', 'Fb_downNeutral', 'Fb_downHit', 'Fb_fall', 'Fb_down2Up', 'Fb_downLtSwing', 'Fb_downRtSwing', 'Fb_DownThrow', 'Fb_UpThrow', 'Fb_jump', 'golf_swing')

class BossCog(Avatar.Avatar):
    notify = DirectNotifyGlobal.directNotify.newCategory('BossCog')
    healthColors = Suit.Suit.healthColors
    healthGlowColors = Suit.Suit.healthGlowColors

    def __init__(self):
        Avatar.Avatar.__init__(self)
        self.setFont(ToontownGlobals.getSuitFont())
        self.setPlayerType(NametagGroup.CCSuit)
        self.setPickable(0)
        self.doorA = None
        self.doorB = None
        self.bubbleL = None
        self.bubbleR = None
        self.raised = 1
        self.forward = 1
        self.happy = 1
        self.dizzy = 0
        self.nowRaised = 1
        self.nowForward = 1
        self.nowHappy = 1
        self.currentAnimIval = None
        self.queuedAnimIvals = []
        self.treadsLeftPos = 0
        self.treadsRightPos = 0
        self.healthBar = None
        self.healthCondition = 0
        self.animDoneEvent = 'BossCogAnimDone'
        self.animIvalName = 'BossCogAnimIval'
        return

    def delete(self):
        Avatar.Avatar.delete(self)
        self.removeHealthBar()
        self.setDizzy(0)
        self.stopAnimate()
        if self.doorA:
            self.doorA.request('Off')
            self.doorB.request('Off')
            self.doorA = None
            self.doorB = None
        return

    def setDNAString(self, dnaString):
        self.dna = SuitDNA.SuitDNA()
        self.dna.makeFromNetString(dnaString)
        self.setDNA(self.dna)

    def setDNA(self, dna):
        if self.style:
            pass
        else:
            self.style = dna
            self.generateBossCog()
            self.initializeDropShadow()
            if base.wantNametags:
                self.initializeNametag3d()

    def generateBossCog(self):
        self.throwSfx = loader.loadSfx('phase_9/audio/sfx/CHQ_VP_frisbee_gears.mp3')
        self.swingSfx = loader.loadSfx('phase_9/audio/sfx/CHQ_VP_swipe.mp3')
        self.spinSfx = loader.loadSfx('phase_9/audio/sfx/CHQ_VP_spin.mp3')
        self.rainGearsSfx = loader.loadSfx('phase_9/audio/sfx/CHQ_VP_raining_gears.mp3')
        self.swishSfx = loader.loadSfx('phase_5/audio/sfx/General_throw_miss.mp3')
        self.boomSfx = loader.loadSfx('phase_3.5/audio/sfx/ENC_cogfall_apart.mp3')
        self.deathSfx = loader.loadSfx('phase_9/audio/sfx/CHQ_VP_big_death.mp3')
        self.upSfx = loader.loadSfx('phase_9/audio/sfx/CHQ_VP_raise_up.mp3')
        self.downSfx = loader.loadSfx('phase_9/audio/sfx/CHQ_VP_collapse.mp3')
        self.reelSfx = loader.loadSfx('phase_9/audio/sfx/CHQ_VP_reeling_backwards.mp3')
        self.birdsSfx = loader.loadSfx('phase_4/audio/sfx/SZ_TC_bird1.mp3')
        self.dizzyAlert = loader.loadSfx('phase_5/audio/sfx/AA_sound_aoogah.mp3')
        self.grunt = loader.loadSfx('phase_9/audio/sfx/Boss_COG_VO_grunt.mp3')
        self.murmur = loader.loadSfx('phase_9/audio/sfx/Boss_COG_VO_murmur.mp3')
        self.statement = loader.loadSfx('phase_9/audio/sfx/Boss_COG_VO_statement.mp3')
        self.question = loader.loadSfx('phase_9/audio/sfx/Boss_COG_VO_question.mp3')
        self.dialogArray = [self.grunt,
         self.murmur,
         self.statement,
         self.question,
         self.statement,
         self.statement]
        dna = self.style
        filePrefix = ModelDict[dna.dept]
        self.loadModel(GenericModel + '-legs-zero', 'legs')
        self.loadModel(filePrefix + '-torso-zero', 'torso')
        self.loadModel(filePrefix + '-head-zero', 'head')
        self.twoFaced = dna.dept == 's'
        self.attach('head', 'torso', 'joint34')
        self.attach('torso', 'legs', 'joint_pelvis')
        self.rotateNode = self.attachNewNode('rotate')
        geomNode = self.getGeomNode()
        geomNode.reparentTo(self.rotateNode)
        self.frontAttack = self.rotateNode.attachNewNode('frontAttack')
        self.frontAttack.setPos(0, -10, 10)
        self.frontAttack.setScale(2)
        self.setHeight(26)
        self.nametag3d.setScale(2)
        for partName in ('legs', 'torso', 'head'):
            animDict = {}
            for anim in AnimList:
                animDict[anim] = '%s-%s-%s' % (GenericModel, partName, anim)

            self.loadAnims(animDict, partName)

        self.stars = BattleProps.globalPropPool.getProp('stun')
        self.stars.setPosHprScale(7, 0, 0, 0, 0, -90, 3, 3, 3)
        self.stars.loop('stun')
        self.pelvis = self.getPart('torso')
        self.pelvisForwardHpr = VBase3(0, 0, 0)
        self.pelvisReversedHpr = VBase3(-180, 0, 0)
        self.neck = self.getPart('head')
        self.neckForwardHpr = VBase3(0, 0, 0)
        self.neckReversedHpr = VBase3(0, -540, 0)
        self.axle = self.find('**/joint_axle')
        self.doorA = self.__setupDoor('**/joint_doorFront', 'doorA', self.doorACallback, VBase3(0, 0, 0), VBase3(0, 0, -80), CollisionPolygon(Point3(5, -4, 0.32), Point3(0, -4, 0), Point3(0, 4, 0), Point3(5, 4, 0.32)))
        self.doorB = self.__setupDoor('**/joint_doorRear', 'doorB', self.doorBCallback, VBase3(0, 0, 0), VBase3(0, 0, 80), CollisionPolygon(Point3(-5, 4, 0.84), Point3(0, 4, 0), Point3(0, -4, 0), Point3(-5, -4, 0.84)))
        treadsModel = loader.loadModel('%s-treads' % GenericModel)
        treadsModel.reparentTo(self.axle)
        self.treadsLeft = treadsModel.find('**/right_tread')
        self.treadsRight = treadsModel.find('**/left_tread')
        self.doorA.request('Closed')
        self.doorB.request('Closed')

    def initializeBodyCollisions(self, collIdStr):
        Avatar.Avatar.initializeBodyCollisions(self, collIdStr)
        if not self.ghostMode:
            self.collNode.setCollideMask(self.collNode.getIntoCollideMask() | ToontownGlobals.PieBitmask)

    def generateHealthBar(self):
        self.removeHealthBar()
        chestNull = self.find('**/joint_lifeMeter')
        if chestNull.isEmpty():
            return
        model = loader.loadModel('phase_3.5/models/gui/matching_game_gui')
        button = model.find('**/minnieCircle')
        button.setScale(6.0)
        button.setP(-20)
        button.setColor(self.healthColors[0])
        button.reparentTo(chestNull)
        self.healthBar = button
        glow = BattleProps.globalPropPool.getProp('glow')
        glow.reparentTo(self.healthBar)
        glow.setScale(0.28)
        glow.setPos(-0.005, 0.01, 0.015)
        glow.setColor(self.healthGlowColors[0])
        button.flattenLight()
        self.healthBarGlow = glow
        self.healthCondition = 0

    def updateHealthBar(self):
        if self.healthBar == None:
            return
        health = 1.0 - float(self.bossDamage) / float(self.bossMaxDamage)
        if health > 0.95:
            condition = 0
        elif health > 0.7:
            condition = 1
        elif health > 0.3:
            condition = 2
        elif health > 0.05:
            condition = 3
        elif health > 0.0:
            condition = 4
        else:
            condition = 5
        if self.healthCondition != condition:
            if condition == 4:
                blinkTask = Task.loop(Task(self.__blinkRed), Task.pause(0.75), Task(self.__blinkGray), Task.pause(0.1))
                taskMgr.add(blinkTask, self.uniqueName('blink-task'))
            elif condition == 5:
                if self.healthCondition == 4:
                    taskMgr.remove(self.uniqueName('blink-task'))
                blinkTask = Task.loop(Task(self.__blinkRed), Task.pause(0.25), Task(self.__blinkGray), Task.pause(0.1))
                taskMgr.add(blinkTask, self.uniqueName('blink-task'))
            else:
                self.healthBar.setColor(self.healthColors[condition], 1)
                self.healthBarGlow.setColor(self.healthGlowColors[condition], 1)
            self.healthCondition = condition
        return

    def __blinkRed(self, task):
        self.healthBar.setColor(self.healthColors[3], 1)
        self.healthBarGlow.setColor(self.healthGlowColors[3], 1)
        if self.healthCondition == 5:
            self.healthBar.setScale(1.17)
        return Task.done

    def __blinkGray(self, task):
        self.healthBar.setColor(self.healthColors[4], 1)
        self.healthBarGlow.setColor(self.healthGlowColors[4], 1)
        if self.healthCondition == 5:
            self.healthBar.setScale(1.0)
        return Task.done

    def removeHealthBar(self):
        if self.healthBar:
            self.healthBar.removeNode()
            self.healthBar = None
        if self.healthCondition == 4 or self.healthCondition == 5:
            taskMgr.remove(self.uniqueName('blink-task'))
        self.healthCondition = 0
        return

    def reverseHead(self):
        self.neck.setHpr(self.neckReversedHpr)

    def forwardHead(self):
        self.neck.setHpr(self.neckForwardHpr)

    def reverseBody(self):
        self.pelvis.setHpr(self.pelvisReversedHpr)

    def forwardBody(self):
        self.pelvis.setHpr(self.pelvisForwardHpr)

    def getShadowJoint(self):
        return self.getGeomNode()

    def getNametagJoints(self):
        return []

    def getDialogueArray(self):
        return self.dialogArray

    def doorACallback(self, isOpen):
        pass

    def doorBCallback(self, isOpen):
        pass

    def __rollTreadsInterval(self, object, start = 0, duration = 0, rate = 1):

        def rollTexMatrix(t, object = object):
            object.setTexOffset(TextureStage.getDefault(), t, 0)

        return LerpFunctionInterval(rollTexMatrix, fromData=start, toData=start + rate * duration, duration=duration)

    def rollLeftTreads(self, duration, rate):
        start = self.treadsLeftPos
        self.treadsLeftPos += duration * rate
        return self.__rollTreadsInterval(self.treadsLeft, start=start, duration=duration, rate=rate)

    def rollRightTreads(self, duration, rate):
        start = self.treadsRightPos
        self.treadsRightPos += duration * rate
        return self.__rollTreadsInterval(self.treadsRight, start=start, duration=duration, rate=rate)

    class DoorFSM(FSM.FSM):

        def __init__(self, name, animate, callback, openedHpr, closedHpr, uniqueName):
            FSM.FSM.__init__(self, name)
            self.animate = animate
            self.callback = callback
            self.openedHpr = openedHpr
            self.closedHpr = closedHpr
            self.uniqueName = uniqueName
            self.ival = 0
            self.openSfx = loader.loadSfx('phase_9/audio/sfx/CHQ_VP_door_open.mp3')
            self.closeSfx = loader.loadSfx('phase_9/audio/sfx/CHQ_VP_door_close.mp3')
            self.request('Closed')

        def filterOpening(self, request, args):
            if request == 'close':
                return 'Closing'
            return self.defaultFilter(request, args)

        def enterOpening(self):
            intervalName = self.uniqueName('open-%s' % self.animate.getName())
            self.callback(0)
            ival = Parallel(SoundInterval(self.openSfx, node=self.animate, volume=0.2), self.animate.hprInterval(1, self.openedHpr, blendType='easeInOut'), Sequence(Wait(0.2), Func(self.callback, 1)), name=intervalName)
            ival.start()
            self.ival = ival

        def exitOpening(self):
            self.ival.pause()
            self.ival = None
            return

        def filterOpened(self, request, args):
            if request == 'close':
                return 'Closing'
            return self.defaultFilter(request, args)

        def enterOpened(self):
            self.animate.setHpr(self.openedHpr)
            self.callback(1)

        def filterClosing(self, request, args):
            if request == 'open':
                return 'Opening'
            return self.defaultFilter(request, args)

        def enterClosing(self):
            intervalName = self.uniqueName('close-%s' % self.animate.getName())
            self.callback(1)
            ival = Parallel(SoundInterval(self.closeSfx, node=self.animate, volume=0.2), self.animate.hprInterval(1, self.closedHpr, blendType='easeInOut'), Sequence(Wait(0.8), Func(self.callback, 0)), name=intervalName)
            ival.start()
            self.ival = ival

        def exitClosing(self):
            self.ival.pause()
            self.ival = None
            return

        def filterClosed(self, request, args):
            if request == 'open':
                return 'Opening'
            return self.defaultFilter(request, args)

        def enterClosed(self):
            self.animate.setHpr(self.closedHpr)
            self.callback(0)

    def __setupDoor(self, jointName, name, callback, openedHpr, closedHpr, cPoly):
        joint = self.find(jointName)
        children = joint.getChildren()
        animate = joint.attachNewNode(name)
        children.reparentTo(animate)
        cnode = CollisionNode('BossZap')
        cnode.setCollideMask(ToontownGlobals.PieBitmask | ToontownGlobals.WallBitmask | ToontownGlobals.CameraBitmask)
        cnode.addSolid(cPoly)
        animate.attachNewNode(cnode)
        fsm = self.DoorFSM(name, animate, callback, openedHpr, closedHpr, self.uniqueName)
        return fsm

    def doAnimate(self, anim = None, now = 0, queueNeutral = 1, raised = None, forward = None, happy = None):
        if now:
            self.stopAnimate()
        if not self.twoFaced:
            happy = 1
        if raised == None:
            raised = self.raised
        if forward == None:
            forward = self.forward
        if happy == None:
            happy = self.happy
        if now:
            self.raised = raised
            self.forward = forward
            self.happy = happy
        if self.currentAnimIval == None:
            self.accept(self.animDoneEvent, self.__getNextAnim)
        else:
            queueNeutral = 0
        ival, changed = self.__getAnimIval(anim, raised, forward, happy)
        if changed or queueNeutral:
            self.queuedAnimIvals.append((ival,
             self.raised,
             self.forward,
             self.happy))
            if self.currentAnimIval == None:
                self.__getNextAnim()
        return

    def stopAnimate(self):
        self.ignore(self.animDoneEvent)
        self.queuedAnimIvals = []
        if self.currentAnimIval:
            self.currentAnimIval.setDoneEvent('')
            self.currentAnimIval.finish()
            self.currentAnimIval = None
        self.raised = self.nowRaised
        self.forward = self.nowForward
        self.happy = self.nowHappy
        return

    def __getNextAnim(self):
        if self.queuedAnimIvals:
            ival, raised, forward, happy = self.queuedAnimIvals[0]
            del self.queuedAnimIvals[0]
        else:
            ival, changed = self.__getAnimIval(None, self.raised, self.forward, self.happy)
            raised = self.raised
            forward = self.forward
            happy = self.happy
        if self.currentAnimIval:
            self.currentAnimIval.setDoneEvent('')
            self.currentAnimIval.finish()
        self.currentAnimIval = ival
        self.currentAnimIval.start()
        self.nowRaised = raised
        self.nowForward = forward
        self.nowHappy = happy
        return

    def __getAnimIval(self, anim, raised, forward, happy):
        ival, changed = self.__doGetAnimIval(anim, raised, forward, happy)
        seq = Sequence(ival, name=self.animIvalName)
        seq.setDoneEvent(self.animDoneEvent)
        return (seq, changed)

    def __doGetAnimIval(self, anim, raised, forward, happy):
        if raised == self.raised and forward == self.forward and happy == self.happy:
            return (self.getAnim(anim), anim != None)
        startsHappy = self.happy
        endsHappy = self.happy
        ival = Sequence()
        if raised and not self.raised:
            upIval = self.getAngryActorInterval('Fb_down2Up')
            if self.forward:
                ival = upIval
            else:
                ival = Sequence(Func(self.reverseBody), upIval, Func(self.forwardBody))
            ival = Parallel(SoundInterval(self.upSfx, node=self), ival)
        if forward != self.forward:
            if forward:
                animName = 'Bb2Ff_spin'
            else:
                animName = 'Ff2Bb_spin'
            ival = Sequence(ival, ActorInterval(self, animName))
            startsHappy = 1
            endsHappy = 1
        startNeckHpr = self.neckForwardHpr
        endNeckHpr = self.neckForwardHpr
        if self.happy != startsHappy:
            startNeckHpr = self.neckReversedHpr
        if happy != endsHappy:
            endNeckHpr = self.neckReversedHpr
        if startNeckHpr != endNeckHpr:
            ival = Sequence(Func(self.neck.setHpr, startNeckHpr), ParallelEndTogether(ival, Sequence(self.neck.hprInterval(0.5, endNeckHpr, startHpr=startNeckHpr, blendType='easeInOut'), Func(self.neck.setHpr, self.neckForwardHpr))))
        elif endNeckHpr != self.neckForwardHpr:
            ival = Sequence(Func(self.neck.setHpr, startNeckHpr), ival, Func(self.neck.setHpr, self.neckForwardHpr))
        if not raised and self.raised:
            downIval = self.getAngryActorInterval('Fb_down2Up', playRate=-1)
            if forward:
                ival = Sequence(ival, downIval)
            else:
                ival = Sequence(ival, Func(self.reverseBody), downIval, Func(self.forwardBody))
            ival = Parallel(SoundInterval(self.downSfx, node=self), ival)
        self.raised = raised
        self.forward = forward
        self.happy = happy
        if anim != None:
            ival = Sequence(ival, self.getAnim(anim))
        return (ival, 1)

    def setDizzy(self, dizzy):
        if dizzy and not self.dizzy:
            base.playSfx(self.dizzyAlert)
        self.dizzy = dizzy
        if dizzy:
            self.stars.reparentTo(self.neck)
            base.playSfx(self.birdsSfx, looping=1)
        else:
            self.stars.detachNode()
            self.birdsSfx.stop()

    def getAngryActorInterval(self, animName, **kw):
        if self.happy:
            ival = Sequence(Func(self.reverseHead), ActorInterval(self, animName, **kw), Func(self.forwardHead))
        else:
            ival = ActorInterval(self, animName, **kw)
        return ival

    def getAnim(self, anim):
        ival = None
        if anim == None:
            partName = None
            if self.happy:
                animName = 'Ff_neutral'
            else:
                animName = 'Fb_neutral'
            if self.raised:
                ival = ActorInterval(self, animName)
            else:
                ival = Parallel(ActorInterval(self, animName, partName=['torso', 'head']), ActorInterval(self, 'Fb_downNeutral', partName='legs'))
            if not self.forward:
                ival = Sequence(Func(self.reverseBody), ival, Func(self.forwardBody))
        elif anim == 'down2Up':
            ival = Parallel(SoundInterval(self.upSfx, node=self), self.getAngryActorInterval('Fb_down2Up'))
            self.raised = 1
        elif anim == 'up2Down':
            ival = Parallel(SoundInterval(self.downSfx, node=self), self.getAngryActorInterval('Fb_down2Up', playRate=-1))
            self.raised = 0
        elif anim == 'throw':
            self.doAnimate(None, raised=1, happy=0, queueNeutral=0)
            ival = Parallel(Sequence(SoundInterval(self.throwSfx, node=self), duration=0), self.getAngryActorInterval('Fb_UpThrow'))
        elif anim == 'hit':
            if self.raised:
                self.raised = 0
                ival = self.getAngryActorInterval('Fb_firstHit')
            else:
                ival = self.getAngryActorInterval('Fb_downHit')
            ival = Parallel(SoundInterval(self.reelSfx, node=self), ival)
        elif anim == 'ltSwing' or anim == 'rtSwing':
            self.doAnimate(None, raised=0, happy=0, queueNeutral=0)
            if anim == 'ltSwing':
                ival = Sequence(Track((0, self.getAngryActorInterval('Fb_downLtSwing')), (0.9, SoundInterval(self.swingSfx, node=self)), (1, Func(self.bubbleL.unstash))), Func(self.bubbleL.stash))
            else:
                ival = Sequence(Track((0, self.getAngryActorInterval('Fb_downRtSwing')), (0.9, SoundInterval(self.swingSfx, node=self)), (1, Func(self.bubbleR.unstash))), Func(self.bubbleR.stash))
        elif anim == 'frontAttack':
            self.doAnimate(None, raised=1, happy=0, queueNeutral=0)
            pe = BattleParticles.loadParticleFile('bossCogFrontAttack.ptf')
            ival = Sequence(Func(self.reverseHead), ActorInterval(self, 'Bb2Ff_spin'), Func(self.forwardHead))
            if self.forward:
                ival = Sequence(Func(self.reverseBody), ParallelEndTogether(ival, self.pelvis.hprInterval(0.5, self.pelvisForwardHpr, blendType='easeInOut')))
            ival = Sequence(Track((0, ival), (0, SoundInterval(self.spinSfx, node=self)), (0.9, Parallel(SoundInterval(self.rainGearsSfx, node=self), ParticleInterval(pe, self.frontAttack, worldRelative=0, duration=1.5, cleanup=True), duration=0)), (1.9, Func(self.bubbleF.unstash))), Func(self.bubbleF.stash))
            self.forward = 1
            self.happy = 0
            self.raised = 1
        elif anim == 'areaAttack':
            if self.twoFaced:
                self.doAnimate(None, raised=1, happy=0, queueNeutral=0)
            else:
                self.doAnimate(None, raised=1, happy=1, queueNeutral=1)
            ival = Parallel(ActorInterval(self, 'Fb_jump'), Sequence(SoundInterval(self.swishSfx, duration=1.1, node=self), SoundInterval(self.boomSfx, duration=1.9)), Sequence(Wait(1.21), Func(self.announceAreaAttack)))
            if self.twoFaced:
                self.happy = 0
            else:
                self.happy = 1
            self.raised = 1
        elif anim == 'Fb_fall':
            ival = Parallel(ActorInterval(self, 'Fb_fall'), Sequence(SoundInterval(self.reelSfx, node=self), SoundInterval(self.deathSfx)))
        elif isinstance(anim, types.StringType):
            ival = ActorInterval(self, anim)
        else:
            ival = anim
        return ival
