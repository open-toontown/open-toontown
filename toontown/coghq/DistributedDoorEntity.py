from pandac.PandaModules import *
from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from direct.distributed.ClockDelta import *
from toontown.toonbase import ToontownGlobals
from direct.directnotify import DirectNotifyGlobal
import DistributedDoorEntityBase
from direct.fsm import FourState
from direct.fsm import ClassicFSM
from otp.level import DistributedEntity
from toontown.toonbase import TTLocalizer
from otp.level import BasicEntities
from direct.fsm import State
from otp.level import VisibilityBlocker

class DistributedDoorEntityLock(DistributedDoorEntityBase.LockBase, FourState.FourState):
    slideLeft = Vec3(-7.5, 0.0, 0.0)
    slideRight = Vec3(7.5, 0.0, 0.0)

    def __init__(self, door, lockIndex, lockedNodePath, leftNodePath, rightNodePath, stateIndex):
        self.door = door
        self.lockIndex = lockIndex
        self.lockedNodePath = lockedNodePath
        self.leftNodePath = leftNodePath
        self.rightNodePath = rightNodePath
        self.initialStateIndex = stateIndex
        FourState.FourState.__init__(self, self.stateNames, self.stateDurations)

    def delete(self):
        self.takedown()
        del self.door

    def setup(self):
        self.setLockState(self.initialStateIndex)
        del self.initialStateIndex

    def takedown(self):
        if self.track is not None:
            self.track.pause()
            self.track = None
        for i in self.states.keys():
            del self.states[i]

        self.states = []
        self.fsm = None
        return

    def setLockState(self, stateIndex):
        if self.stateIndex != stateIndex:
            state = self.states.get(stateIndex)
            if state is not None:
                self.fsm.request(state)
        return

    def isUnlocked(self):
        return self.isOn()

    def enterState1(self):
        FourState.FourState.enterState1(self)
        beat = self.duration * 0.05
        slideSfx = base.loadSfx('phase_9/audio/sfx/CHQ_FACT_arms_retracting.mp3')
        self.setTrack(Sequence(Wait(beat * 2.0), Parallel(SoundInterval(slideSfx, node=self.door.node, volume=0.8), Sequence(ShowInterval(self.leftNodePath), ShowInterval(self.rightNodePath), Parallel(LerpPosInterval(nodePath=self.leftNodePath, other=self.lockedNodePath, duration=beat * 16.0, pos=Vec3(0.0), blendType='easeIn'), LerpPosInterval(nodePath=self.rightNodePath, other=self.lockedNodePath, duration=beat * 16.0, pos=Vec3(0.0), blendType='easeIn')), HideInterval(self.leftNodePath), HideInterval(self.rightNodePath), ShowInterval(self.lockedNodePath)))))

    def enterState2(self):
        FourState.FourState.enterState2(self)
        self.setTrack(None)
        self.leftNodePath.setPos(self.lockedNodePath, Vec3(0.0))
        self.rightNodePath.setPos(self.lockedNodePath, Vec3(0.0))
        self.leftNodePath.hide()
        self.rightNodePath.hide()
        self.lockedNodePath.show()
        return

    def enterState3(self):
        FourState.FourState.enterState3(self)
        unlockSfx = base.loadSfx('phase_9/audio/sfx/CHQ_FACT_door_unlock.mp3')
        slideSfx = base.loadSfx('phase_9/audio/sfx/CHQ_FACT_arms_retracting.mp3')
        beat = self.duration * 0.05
        self.setTrack(Sequence(Wait(beat * 2), Parallel(SoundInterval(unlockSfx, node=self.door.node, volume=0.8), SoundInterval(slideSfx, node=self.door.node, volume=0.8), Sequence(HideInterval(self.lockedNodePath), ShowInterval(self.leftNodePath), ShowInterval(self.rightNodePath), Parallel(LerpPosInterval(nodePath=self.leftNodePath, other=self.lockedNodePath, duration=beat * 16, pos=self.slideLeft, blendType='easeOut'), LerpPosInterval(nodePath=self.rightNodePath, other=self.lockedNodePath, duration=beat * 16, pos=self.slideRight, blendType='easeOut')), HideInterval(self.leftNodePath), HideInterval(self.rightNodePath)))))

    def enterState4(self):
        FourState.FourState.enterState4(self)
        self.setTrack(None)
        self.leftNodePath.setPos(self.lockedNodePath, self.slideLeft)
        self.rightNodePath.setPos(self.lockedNodePath, self.slideRight)
        self.leftNodePath.hide()
        self.rightNodePath.hide()
        self.lockedNodePath.hide()
        return


class DistributedDoorEntity(DistributedDoorEntityBase.DistributedDoorEntityBase, DistributedEntity.DistributedEntity, BasicEntities.NodePathAttribsProxy, FourState.FourState, VisibilityBlocker.VisibilityBlocker):

    def __init__(self, cr):
        self.innerDoorsTrack = None
        self.isVisReady = 0
        self.isOuterDoorOpen = 0
        DistributedEntity.DistributedEntity.__init__(self, cr)
        FourState.FourState.__init__(self, self.stateNames, self.stateDurations)
        VisibilityBlocker.VisibilityBlocker.__init__(self)
        self.locks = []
        return

    def generate(self):
        DistributedEntity.DistributedEntity.generate(self)

    def announceGenerate(self):
        self.doorNode = hidden.attachNewNode('door-%s' % self.entId)
        DistributedEntity.DistributedEntity.announceGenerate(self)
        BasicEntities.NodePathAttribsProxy.initNodePathAttribs(self)
        self.setup()

    def disable(self):
        self.takedown()
        self.doorNode.removeNode()
        del self.doorNode
        DistributedEntity.DistributedEntity.disable(self)

    def delete(self):
        DistributedEntity.DistributedEntity.delete(self)

    def setup(self):
        self.setupDoor()
        for i in self.locks:
            i.setup()

        self.accept('exit%s' % (self.getName(),), self.exitTrigger)
        self.acceptAvatar()
        if __dev__:
            self.initWantDoors()

    def takedown(self):
        if __dev__:
            self.shutdownWantDoors()
        self.ignoreAll()
        if self.track is not None:
            self.track.finish()
        self.track = None
        if self.innerDoorsTrack is not None:
            self.innerDoorsTrack.finish()
        self.innerDoorsTrack = None
        for i in self.locks:
            i.takedown()

        self.locks = []
        self.fsm = None
        for i in self.states.keys():
            del self.states[i]

        self.states = []
        return

    setUnlock0Event = DistributedDoorEntityBase.stubFunction
    setUnlock1Event = DistributedDoorEntityBase.stubFunction
    setUnlock2Event = DistributedDoorEntityBase.stubFunction
    setUnlock3Event = DistributedDoorEntityBase.stubFunction
    setIsOpenEvent = DistributedDoorEntityBase.stubFunction
    setIsLock0Unlocked = DistributedDoorEntityBase.stubFunction
    setIsLock1Unlocked = DistributedDoorEntityBase.stubFunction
    setIsLock2Unlocked = DistributedDoorEntityBase.stubFunction
    setIsLock3Unlocked = DistributedDoorEntityBase.stubFunction
    setIsOpen = DistributedDoorEntityBase.stubFunction
    setSecondsOpen = DistributedDoorEntityBase.stubFunction

    def acceptAvatar(self):
        self.accept('enter%s' % (self.getName(),), self.enterTrigger)

    def rejectInteract(self):
        DistributedEntity.DistributedEntity.rejectInteract(self)
        self.acceptAvatar()

    def avatarExit(self, avatarId):
        DistributedEntity.DistributedEntity.avatarExit(self, avatarId)
        self.acceptAvatar()

    def enterTrigger(self, args = None):
        messenger.send('DistributedInteractiveEntity_enterTrigger')
        self.sendUpdate('requestOpen')

    def exitTrigger(self, args = None):
        messenger.send('DistributedInteractiveEntity_exitTrigger')

    def okToUnblockVis(self):
        VisibilityBlocker.VisibilityBlocker.okToUnblockVis(self)
        self.isVisReady = 1
        self.openInnerDoors()

    def changedOnState(self, isOn):
        messenger.send(self.getOutputEventName(), [not isOn])

    def setLocksState(self, stateBits):
        lock0 = stateBits & 15
        lock1 = (stateBits & 240) >> 4
        lock2 = (stateBits & 3840) >> 8
        if self.isGenerated():
            self.locks[0].setLockState(lock0)
            self.locks[1].setLockState(lock1)
            self.locks[2].setLockState(lock2)
        else:
            self.initialLock0StateIndex = lock0
            self.initialLock1StateIndex = lock1
            self.initialLock2StateIndex = lock2

    def setDoorState(self, stateIndex, timeStamp):
        self.stateTime = globalClockDelta.localElapsedTime(timeStamp)
        if self.isGenerated():
            if self.stateIndex != stateIndex:
                state = self.states.get(stateIndex)
                if state is not None:
                    self.fsm.request(state)
        else:
            self.initialState = stateIndex
            self.initialStateTimestamp = timeStamp
        return

    def getName(self):
        return 'switch-%s' % str(self.entId)

    def getNodePath(self):
        if hasattr(self, 'doorNode'):
            return self.doorNode
        return None

    def setupDoor(self):
        model = loader.loadModel('phase_9/models/cogHQ/CogDoorHandShake')
        if model:
            doorway = model.find('**/Doorway1')
            rootNode = self.doorNode.attachNewNode(self.getName() + '-root')
            rootNode.setPos(self.pos)
            rootNode.setHpr(self.hpr)
            rootNode.setScale(self.scale)
            rootNode.setColor(self.color)
            change = rootNode.attachNewNode('changePos')
            doorway.reparentTo(change)
            self.node = rootNode
            self.node.show()
            self.locks.append(DistributedDoorEntityLock(self,
                                                        0,
                                                        doorway.find('**/Slide_One_Closed'),
                                                        doorway.find('**/Slide_One_Left_Open'),
                                                        doorway.find('**/Slide_One_Right_Open'),
                                                        self.initialLock0StateIndex))
            self.locks.append(DistributedDoorEntityLock(self,
                                                        1,
                                                        doorway.find('**/Slide_Two_Closed'),
                                                        doorway.find('**/Slide_Two_Left_Open'),
                                                        doorway.find('**/Slide_Two_Right_Open'),
                                                        self.initialLock1StateIndex))
            self.locks.append(DistributedDoorEntityLock(self,
                                                        2,
                                                        doorway.find('**/Slide_Three_Closed'),
                                                        doorway.find('**/Slide_Three_Left_Open'),
                                                        doorway.find('**/Slide_Three_Right_Open'),
                                                        self.initialLock2StateIndex))

            del self.initialLock0StateIndex
            del self.initialLock1StateIndex
            del self.initialLock2StateIndex

            door = doorway.find('doortop')
            if door.isEmpty():
                print 'doortop hack'
                door = doorway.attachNewNode('doortop')
                doorway.find('doortop1').reparentTo(door)
                doorway.find('doortop2').reparentTo(door)

            rootNode = self.doorNode.attachNewNode(self.getName() + '-topDoor')
            rootNode.setPos(self.pos)
            rootNode.setHpr(self.hpr)
            rootNode.setScale(self.scale)
            rootNode.setColor(self.color)
            change = rootNode.attachNewNode('changePos')
            door.reparentTo(change)
            self.doorTop = rootNode
            self.doorTop.show()

            rootNode = self.doorTop.getParent().attachNewNode(self.getName() + '-leftDoor')
            change = rootNode.attachNewNode('change')
            door = doorway.find('**/doorLeft')
            door = door.reparentTo(change)
            self.doorLeft = rootNode
            self.doorLeft.show()
            change.setPos(self.pos)
            change.setHpr(self.hpr)
            change.setScale(self.scale)
            change.setColor(self.color)

            door = doorway.find('doorbottom')
            if door.isEmpty():
                print 'doorbottom hack'
                door = doorway.attachNewNode('doorbottom')
                doorway.find('doorbottom1').reparentTo(door)
                doorway.find('doorbottom2').reparentTo(door)

            change = render.attachNewNode('changePos')
            door.reparentTo(change)
            rootNode = self.doorNode.attachNewNode(self.getName() + '-bottomDoor')
            rootNode.setPos(self.pos)
            rootNode.setHpr(self.hpr)
            rootNode.setScale(self.scale)
            rootNode.setColor(self.color)
            change.reparentTo(rootNode)
            self.doorBottom = rootNode
            self.doorBottom.show()

            rootNode = self.doorTop.getParent().attachNewNode(self.getName() + '-rightDoor')
            change = rootNode.attachNewNode('change')
            door = doorway.find('**/doorRight')
            door = door.reparentTo(change)
            self.doorRight = rootNode
            self.doorRight.show()
            change.setPos(self.pos)
            change.setHpr(self.hpr)
            change.setScale(self.scale)
            change.setColor(self.color)

            collision = self.doorLeft.find('**/doorLeft_collision1')
            collision.setName(self.getName())
            collision = self.doorLeft.find('**/doorLeft_collision2')
            collision.setName(self.getName())
            collision = self.doorRight.find('**/doorRight_collision1')
            collision.setName(self.getName())
            collision = self.doorRight.find('**/doorRight_collision2')
            collision.setName(self.getName())
            collision = self.doorLeft.find('**/doorLeft_innerCollision')
            collision.setName(self.getName())
            self.leftInnerCollision = collision
            collision = self.doorRight.find('**/doorRight_innerCollision')
            collision.setName(self.getName())
            self.rightInnerCollision = collision

            if 1:
                pass
            else:
                radius = 8.0
                cSphere = CollisionSphere(0.0, 0.0, 0.0, radius)
                cSphere.setTangible(0)
                cSphereNode = CollisionNode(self.getName())
                cSphereNode.addSolid(cSphere)
                cSphereNode.setFromCollideMask(BitMask32.allOff())
                cSphereNode.setIntoCollideMask(ToontownGlobals.WallBitmask)
                self.cSphereNodePath = self.node.attachNewNode(cSphereNode)

            if 1:
                self.node.flattenMedium()
                self.doorTop.flattenMedium()
                self.doorBottom.flattenMedium()
                self.doorLeft.flattenMedium()
                self.doorRight.flattenMedium()

        self.setDoorState(self.initialState, self.initialStateTimestamp)
        del self.initialState
        del self.initialStateTimestamp

    def setInnerDoorsTrack(self, track):
        if self.innerDoorsTrack is not None:
            self.innerDoorsTrack.pause()
            self.innerDoorsTrack = None
        if track is not None:
            track.start(0.0)
            self.innerDoorsTrack = track
        return

    def openInnerDoors(self):
        print 'openInnerDoors'
        if not self.level.complexVis() or self.isOuterDoorOpen and (not self.isVisBlocker or self.isVisReady):
            print 'openInnerDoors stage Two'
            duration = self.duration
            slideSfx = base.loadSfx('phase_9/audio/sfx/CHQ_FACT_door_open_sliding.mp3')
            finalSfx = base.loadSfx('phase_9/audio/sfx/CHQ_FACT_door_open_final.mp3')
            moveDistance = 8.0
            self.setInnerDoorsTrack(Sequence(Func(self.leftInnerCollision.unstash), Func(self.rightInnerCollision.unstash), Parallel(SoundInterval(slideSfx, node=self.node, duration=duration * 0.4, volume=0.8), LerpPosInterval(nodePath=self.doorLeft, duration=duration * 0.4, pos=Vec3(-moveDistance, 0.0, 0.0), blendType='easeOut'), LerpPosInterval(nodePath=self.doorRight, duration=duration * 0.4, pos=Vec3(moveDistance, 0.0, 0.0), blendType='easeOut'), Sequence(Wait(duration * 0.375), SoundInterval(finalSfx, node=self.node, duration=1.0, volume=0.8))), Func(self.doorLeft.stash), Func(self.doorRight.stash)))

    def closeInnerDoors(self):
        duration = self.duration
        slideSfx = base.loadSfx('phase_9/audio/sfx/CHQ_FACT_door_open_sliding.mp3')
        finalSfx = base.loadSfx('phase_9/audio/sfx/CHQ_FACT_door_open_final.mp3')
        moveDistance = 8.0
        self.setInnerDoorsTrack(Sequence(Func(self.doorLeft.unstash), Func(self.doorRight.unstash), Parallel(SoundInterval(slideSfx, node=self.node, duration=duration * 0.4, volume=0.8), LerpPosInterval(nodePath=self.doorLeft, duration=duration * 0.4, pos=Vec3(0.0), blendType='easeIn'), LerpPosInterval(nodePath=self.doorRight, duration=duration * 0.4, pos=Vec3(0.0), blendType='easeIn'), Sequence(Wait(duration * 0.375), SoundInterval(finalSfx, node=self.node, duration=1.0, volume=0.8))), Func(self.leftInnerCollision.stash), Func(self.rightInnerCollision.stash)))

    def setisOuterDoorOpen(self, isOpen):
        self.isOuterDoorOpen = isOpen

    def enterState1(self):
        print 'doors enter state 1'
        FourState.FourState.enterState1(self)
        self.isOuterDoorOpen = 0
        if self.isVisBlocker:
            if not self.isVisReady:
                self.requestUnblockVis()
        else:
            self.okToUnblockVis()
        duration = self.duration
        slideSfx = base.loadSfx('phase_9/audio/sfx/CHQ_FACT_door_open_sliding.mp3')
        finalSfx = base.loadSfx('phase_9/audio/sfx/CHQ_FACT_door_open_final.mp3')
        moveDistance = 8.0
        self.setTrack(Sequence(Wait(duration * 0.1), Parallel(SoundInterval(slideSfx, node=self.node, duration=duration * 0.4, volume=0.8), LerpPosInterval(nodePath=self.doorTop, duration=duration * 0.4, pos=Vec3(0.0, 0.0, moveDistance), blendType='easeOut'), LerpPosInterval(nodePath=self.doorBottom, duration=duration * 0.4, pos=Vec3(0.0, 0.0, -moveDistance), blendType='easeOut'), Sequence(Wait(duration * 0.375), SoundInterval(finalSfx, node=self.node, duration=1.0, volume=0.8))), Func(self.doorTop.stash), Func(self.doorBottom.stash), Func(self.setisOuterDoorOpen, 1), Func(self.openInnerDoors)))

    def enterState2(self):
        FourState.FourState.enterState2(self)
        self.isOuterDoorOpen = 1
        self.setTrack(None)
        moveDistance = 7.5
        (self.doorTop.setPos(Vec3(0.0, 0.0, moveDistance)),)
        (self.doorBottom.setPos(Vec3(0.0, 0.0, -moveDistance)),)
        self.doorTop.stash()
        self.doorBottom.stash()
        if not self.isVisBlocker or not self.isWaitingForUnblockVis():
            self.setInnerDoorsTrack(None)
            self.doorLeft.setPos(Vec3(-moveDistance, 0.0, 0.0))
            self.doorRight.setPos(Vec3(moveDistance, 0.0, 0.0))
            self.doorLeft.stash()
            self.doorRight.stash()
        return

    def exitState2(self):
        FourState.FourState.exitState2(self)
        self.cancelUnblockVis()

    def enterState3(self):
        FourState.FourState.enterState3(self)
        duration = self.duration
        slideSfx = base.loadSfx('phase_9/audio/sfx/CHQ_FACT_door_open_sliding.mp3')
        finalSfx = base.loadSfx('phase_9/audio/sfx/CHQ_FACT_door_open_final.mp3')
        self.setTrack(Sequence(Wait(duration * 0.1),
                               Func(self.closeInnerDoors),
                               Wait(duration * 0.4),
                               Func(self.doorTop.unstash),
                               Func(self.doorBottom.unstash),
                               Parallel(SoundInterval(slideSfx, node=self.node, duration=duration*0.4, volume=0.8),
                                        LerpPosInterval(nodePath=self.doorTop, duration=duration*0.4, pos=Vec3(0.0), blendType='easeIn'),
                                        LerpPosInterval(nodePath=self.doorBottom, duration=duration*0.4, pos=Vec3(0.0), blendType='easeIn'),
                                        Sequence(Wait(duration*0.375),
                                                 SoundInterval(finalSfx, node=self.node, duration=duration*0.4, volume=0.8))),
                               Func(self.setisOuterDoorOpen, 0)))

    def enterState4(self):
        FourState.FourState.enterState4(self)
        self.setisOuterDoorOpen(0)
        self.isVisReady = 0
        self.setTrack(None)
        self.doorTop.unstash()
        self.doorBottom.unstash()
        self.doorTop.setPos(Vec3(0.0))
        self.doorBottom.setPos(Vec3(0.0))
        self.setInnerDoorsTrack(None)
        self.leftInnerCollision.stash()
        self.rightInnerCollision.stash()
        self.doorLeft.unstash()
        self.doorRight.unstash()
        self.doorLeft.setPos(Vec3(0.0))
        self.doorRight.setPos(Vec3(0.0))


    if __dev__:
        def initWantDoors(self):
            self.accept('wantDoorsChanged', self.onWantDoorsChanged)
            self.onWantDoorsChanged()

        def shutdownWantDoors(self):
            self.ignore('wantDoorsChanged')

        def onWantDoorsChanged(self):
            if self.level.levelMgrEntity.wantDoors:
                self.getNodePath().unstash()
            else:
                self.getNodePath().stash()

        def attribChanged(self, attrib, value):
            self.takedown()
            self.setup()
