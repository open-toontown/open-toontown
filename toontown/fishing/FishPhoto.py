from direct.directnotify import DirectNotifyGlobal
from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
import FishGlobals

class DirectRegion(NodePath):
    notify = DirectNotifyGlobal.directNotify.newCategory('DirectRegion')

    def __init__(self, parent = aspect2d):
        NodePath.__init__(self)
        self.assign(parent.attachNewNode('DirectRegion'))

    def destroy(self):
        self.unload()

    def setBounds(self, *bounds):
        self.bounds = bounds

    def setColor(self, *colors):
        self.color = colors

    def show(self):
        pass

    def hide(self):
        pass

    def load(self):
        if not hasattr(self, 'cRender'):
            self.cRender = NodePath('fishSwimRender')
            self.fishSwimCamera = self.cRender.attachNewNode('fishSwimCamera')
            self.cCamNode = Camera('fishSwimCam')
            self.cLens = PerspectiveLens()
            self.cLens.setFov(40, 40)
            self.cLens.setNear(0.1)
            self.cLens.setFar(100.0)
            self.cCamNode.setLens(self.cLens)
            self.cCamNode.setScene(self.cRender)
            self.fishSwimCam = self.fishSwimCamera.attachNewNode(self.cCamNode)
            cm = CardMaker('displayRegionCard')
            apply(cm.setFrame, self.bounds)
            self.card = card = self.attachNewNode(cm.generate())
            apply(card.setColor, self.color)
            newBounds = card.getTightBounds()
            ll = render2d.getRelativePoint(card, newBounds[0])
            ur = render2d.getRelativePoint(card, newBounds[1])
            newBounds = [ll.getX(),
             ur.getX(),
             ll.getZ(),
             ur.getZ()]
            newBounds = map(lambda x: max(0.0, min(1.0, (x + 1.0) / 2.0)), newBounds)
            self.cDr = base.win.makeDisplayRegion(*newBounds)
            self.cDr.setSort(10)
            self.cDr.setClearColor(card.getColor())
            self.cDr.setClearDepthActive(1)
            self.cDr.setClearColorActive(1)
            self.cDr.setCamera(self.fishSwimCam)
        return self.cRender

    def unload(self):
        if hasattr(self, 'cRender'):
            base.win.removeDisplayRegion(self.cDr)
            del self.cRender
            del self.fishSwimCamera
            del self.cCamNode
            del self.cLens
            del self.fishSwimCam
            del self.cDr


class FishPhoto(NodePath):
    notify = DirectNotifyGlobal.directNotify.newCategory('FishPhoto')

    def __init__(self, fish = None, parent = aspect2d):
        NodePath.__init__(self)
        self.assign(parent.attachNewNode('FishPhoto'))
        self.fish = fish
        self.actor = None
        self.sound = None
        self.soundTrack = None
        self.track = None
        self.fishFrame = None
        return

    def destroy(self):
        self.hide()
        if hasattr(self, 'background'):
            del self.background
        self.fish = None
        del self.soundTrack
        del self.track
        return

    def update(self, fish):
        self.fish = fish

    def setSwimBounds(self, *bounds):
        self.swimBounds = bounds

    def setSwimColor(self, *colors):
        self.swimColor = colors

    def load(self):
        pass

    def makeFishFrame(self, actor):
        actor.setDepthTest(1)
        actor.setDepthWrite(1)
        if not hasattr(self, 'fishDisplayRegion'):
            self.fishDisplayRegion = DirectRegion(parent=self)
            apply(self.fishDisplayRegion.setBounds, self.swimBounds)
            apply(self.fishDisplayRegion.setColor, self.swimColor)
        frame = self.fishDisplayRegion.load()
        pitch = frame.attachNewNode('pitch')
        rotate = pitch.attachNewNode('rotate')
        scale = rotate.attachNewNode('scale')
        actor.reparentTo(scale)
        bMin, bMax = actor.getTightBounds()
        center = (bMin + bMax) / 2.0
        actor.setPos(-center[0], -center[1], -center[2])
        genus = self.fish.getGenus()
        fishInfo = FishGlobals.FishFileDict.get(genus, FishGlobals.FishFileDict[-1])
        fishPos = fishInfo[5]
        if fishPos:
            actor.setPos(fishPos[0], fishPos[1], fishPos[2])
        scale.setScale(fishInfo[6])
        rotate.setH(fishInfo[7])
        pitch.setP(fishInfo[8])
        pitch.setY(2)
        return frame

    def show(self, showBackground = 0):
        messenger.send('wakeup')
        if self.fishFrame:
            self.actor.cleanup()
            if hasattr(self, 'fishDisplayRegion'):
                self.fishDisplayRegion.unload()
            self.hide()
        self.actor = self.fish.getActor()
        self.actor.setTwoSided(1)
        self.fishFrame = self.makeFishFrame(self.actor)
        if showBackground:
            if not hasattr(self, 'background'):
                background = loader.loadModel('phase_3.5/models/gui/stickerbook_gui')
                background = background.find('**/Fish_BG')
                self.background = background
            self.background.setPos(0, 15, 0)
            self.background.setScale(11)
            self.background.reparentTo(self.fishFrame)
        self.sound, loop, delay, playRate = self.fish.getSound()
        if playRate is not None:
            self.actor.setPlayRate(playRate, 'intro')
            self.actor.setPlayRate(playRate, 'swim')
        introDuration = self.actor.getDuration('intro')
        track = Parallel(Sequence(Func(self.actor.play, 'intro'), Wait(introDuration), Func(self.actor.loop, 'swim')))
        if self.sound:
            soundTrack = Sequence(Wait(delay), Func(self.sound.play))
            if loop:
                duration = max(introDuration, self.sound.length())
                soundTrack.append(Wait(duration - delay))
                track.append(Func(soundTrack.loop))
                self.soundTrack = soundTrack
            else:
                track.append(soundTrack)
        self.track = track
        self.track.start()
        return

    def hide(self):
        if hasattr(self, 'fishDisplayRegion'):
            self.fishDisplayRegion.unload()
        if self.actor:
            self.actor.stop()
        if self.sound:
            self.sound.stop()
            self.sound = None
        if self.soundTrack:
            self.soundTrack.pause()
            self.soundTrack = None
        if self.track:
            self.track.pause()
            self.track = None
        return
