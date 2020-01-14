from pandac.PandaModules import *
from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from direct.distributed.ClockDelta import *
from . import MovingPlatform
from toontown.toonbase import ToontownGlobals
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM
from . import DistributedSwitch
from toontown.toonbase import TTLocalizer

class DistributedButton(DistributedSwitch.DistributedSwitch):
    countdownSeconds = 3.0

    def __init__(self, cr):
        self.countdownTrack = None
        DistributedSwitch.DistributedSwitch.__init__(self, cr)
        return

    def setSecondsOn(self, secondsOn):
        self.secondsOn = secondsOn

    def avatarExit(self, avatarId):
        DistributedSwitch.DistributedSwitch.avatarExit(self, avatarId)
        if self.secondsOn != -1.0 and self.secondsOn > 0.0 and self.countdownSeconds > 0.0 and self.countdownSeconds < self.secondsOn and self.fsm.getCurrentState().getName() == 'playing':
            track = self.switchCountdownTrack()
            if track is not None:
                track.start(0.0)
                self.countdownTrack = track
        return

    def setupSwitch(self):
        model = loader.loadModel('phase_9/models/cogHQ/CogDoor_Button')
        if model:
            buttonBase = model.find('**/buttonBase')
            change = render.attachNewNode('changePos')
            buttonBase.reparentTo(change)
            rootNode = render.attachNewNode(self.getName() + '-buttonBase_root')
            change.reparentTo(rootNode)
            self.buttonFrameNode = rootNode
            self.buttonFrameNode.show()
            button = model.find('**/button')
            change = render.attachNewNode('change')
            button.reparentTo(change)
            rootNode = render.attachNewNode(self.getName() + '-button_root')
            rootNode.setColor(self.color)
            change.reparentTo(rootNode)
            self.buttonNode = rootNode
            self.buttonNode.show()
            self.buttonFrameNode.reparentTo(self)
            self.buttonNode.reparentTo(self)
            if 1:
                radius = 0.5
                cSphere = CollisionSphere(0.0, 0.0, radius, radius)
                cSphere.setTangible(0)
                cSphereNode = CollisionNode(self.getName())
                cSphereNode.addSolid(cSphere)
                cSphereNode.setCollideMask(ToontownGlobals.WallBitmask)
                self.cSphereNodePath = rootNode.attachNewNode(cSphereNode)
            if 1:
                collisionFloor = button.find('**/collision_floor')
                if collisionFloor.isEmpty():
                    top = 0.475
                    size = 0.5
                    floor = CollisionPolygon(Point3(-size, -size, top),
                                             Point3( size, -size, top),
                                             Point3( size,  size, top),
                                             Point3(-size,  size, top))
                    floor.setTangible(1)
                    floorNode = CollisionNode('collision_floor')
                    floorNode.addSolid(floor)
                    collisionFloor = button.attachNewNode(floorNode)
                else:
                    change = collisionFloor.getParent().attachNewNode('changeFloor')
                    change.setScale(0.5, 0.5, 1.0)
                    collisionFloor.reparentTo(change)
                collisionFloor.node().setFromCollideMask(BitMask32.allOff())
                collisionFloor.node().setIntoCollideMask(ToontownGlobals.FloorBitmask)
            self.buttonFrameNode.flattenMedium()
            self.buttonNode.flattenMedium()

    def delete(self):
        DistributedSwitch.DistributedSwitch.delete(self)

    def enterTrigger(self, args = None):
        DistributedSwitch.DistributedSwitch.enterTrigger(self, args)

    def exitTrigger(self, args = None):
        DistributedSwitch.DistributedSwitch.exitTrigger(self, args)

    def switchOnTrack(self):
        onSfx = base.loader.loadSfx('phase_9/audio/sfx/CHQ_FACT_switch_pressed.ogg')
        duration = 0.8
        halfDur = duration * 0.5
        pos = Vec3(0.0, 0.0, -0.2)
        color = Vec4(0.0, 1.0, 0.0, 1.0)
        track = Sequence(Func(self.setIsOn, 1), Parallel(SoundInterval(onSfx, node=self.node, volume=0.9), LerpPosInterval(nodePath=self.buttonNode, duration=duration, pos=pos, blendType='easeInOut'), Sequence(Wait(halfDur), LerpColorInterval(nodePath=self.buttonNode, duration=halfDur, color=color, override=1, blendType='easeOut'))))
        return track

    def switchCountdownTrack(self):
        wait = self.secondsOn - self.countdownSeconds
        countDownSfx = base.loader.loadSfx('phase_9/audio/sfx/CHQ_FACT_switch_depressed.ogg')
        track = Parallel(
            SoundInterval(countDownSfx),
            Sequence(
                Wait(wait),
                Wait(0.5),
                LerpColorInterval(nodePath=self.buttonNode, duration=0.1, color=self.color, override=1, blendType='easeIn'),
                LerpColorInterval(nodePath=self.buttonNode, duration=0.1, color=Vec4(0.0, 1.0, 0.0, 1.0), override=1, blendType='easeOut'),
                Wait(0.5),
                LerpColorInterval(nodePath=self.buttonNode, duration=0.1, color=self.color, override=1, blendType='easeIn'),
                LerpColorInterval(nodePath=self.buttonNode, duration=0.1, color=Vec4(0.0, 1.0, 0.0, 1.0), override=1, blendType='easeOut'),
                Wait(0.4),
                LerpColorInterval(nodePath=self.buttonNode, duration=0.1, color=self.color, override=1, blendType='easeIn'),
                LerpColorInterval(nodePath=self.buttonNode, duration=0.1, color=Vec4(0.0, 1.0, 0.0, 1.0), override=1, blendType='easeOut'),
                Wait(0.3),
                LerpColorInterval(nodePath=self.buttonNode, duration=0.1, color=self.color, override=1, blendType='easeIn'),
                LerpColorInterval(nodePath=self.buttonNode, duration=0.1, color=Vec4(0.0, 1.0, 0.0, 1.0), override=1, blendType='easeOut'),
                Wait(0.2),
                LerpColorInterval(nodePath=self.buttonNode, duration=0.1, color=self.color, override=1, blendType='easeIn'),
                LerpColorInterval(nodePath=self.buttonNode, duration=0.1, override=1, color=Vec4(0.0, 1.0, 0.0, 1.0), blendType='easeOut'),
                Wait(0.1)))
        return track

    def switchOffTrack(self):
        offSfx = base.loader.loadSfx('phase_9/audio/sfx/CHQ_FACT_switch_popup.ogg')
        duration = 1.0
        halfDur = duration * 0.5
        pos = Vec3(0.0)
        track = Sequence(Parallel(SoundInterval(offSfx, node=self.node, volume=1.0), LerpPosInterval(nodePath=self.buttonNode, duration=duration, pos=pos, blendType='easeInOut'), Sequence(Wait(halfDur), LerpColorInterval(nodePath=self.buttonNode, duration=halfDur, color=self.color, override=1, blendType='easeIn'))), Func(self.setIsOn, 0))
        return track

    def exitPlaying(self):
        if self.countdownTrack:
            self.countdownTrack.finish()
        self.countdownTrack = None
        DistributedSwitch.DistributedSwitch.exitPlaying(self)
