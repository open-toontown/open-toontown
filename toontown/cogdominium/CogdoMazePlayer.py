from pandac.PandaModules import Point3, NodePath
from direct.fsm.FSM import FSM
from direct.interval.IntervalGlobal import ProjectileInterval, Track, ActorInterval
from direct.interval.IntervalGlobal import Func, Sequence, Parallel
from CogdoMazeGameObjects import CogdoMazeSplattable
import CogdoMazeGameGlobals as Globals
import CogdoUtil
import random

class CogdoMazePlayer(FSM, CogdoMazeSplattable):
    notify = directNotify.newCategory('CogdoMazePlayer')
    _key = None
    GagHitEventName = 'CogdoMazePlayer_GagHit'
    RemovedEventName = 'CogdoMazePlayer_Removed'

    def __init__(self, id, toon):
        FSM.__init__(self, 'CogdoMazePlayer')
        CogdoMazeSplattable.__init__(self, toon, '%s-%i' % (Globals.PlayerCollisionName, id), 0.5)
        self.id = id
        self.toon = toon
        self.defaultTransitions = {'Off': ['Ready'],
         'Ready': ['Normal', 'Off'],
         'Normal': ['Hit', 'Done', 'Off'],
         'Hit': ['Normal', 'Done', 'Off'],
         'Done': ['Off']}
        self.toon.reparentTo(render)
        self.gagModel = CogdoUtil.loadMazeModel('waterBalloon')
        self.equippedGag = None
        self._toonHitSfx = base.cogdoGameAudioMgr.createSfx('toonHit', self.toon)
        self._throwSfx = base.cogdoGameAudioMgr.createSfxIval('throw')
        self.accept(toon.getDisableEvent(), self.removed)
        self.request('Off')
        return

    def destroy(self):
        if self.equippedGag:
            self.removeGag()
        del self._toonHitSfx
        del self._throwSfx
        CogdoMazeSplattable.destroy(self)

    def enterOff(self):
        self.toon.setAnimState('Happy', 1.0)
        self.toon.setSpeed(0, 0)

    def exitOff(self):
        pass

    def enterReady(self):
        pass

    def exitReady(self):
        pass

    def enterNormal(self):
        self.toon.startSmooth()
        if self.equippedGag is not None:
            self.equippedGag.unstash()
        return

    def exitNormal(self):
        self.toon.stopSmooth()
        if self.equippedGag is not None:
            self.equippedGag.stash()
        return

    def enterHit(self, elapsedTime = 0.0):
        animationInfo = Globals.ToonAnimationInfo['hit']
        self._hitIval = self._getToonAnimationIval(animationInfo[0], duration=animationInfo[1], startFrame=animationInfo[2], nextState='Normal')
        self._hitIval.start(elapsedTime)
        self._toonHitSfx.play()

    def exitHit(self):
        self._hitIval.pause()
        del self._hitIval
        if self.equippedGag is not None:
            self.toon.setAnimState('Catching', 1.0)
        else:
            self.toon.setAnimState('Happy', 1.0)
        return

    def enterDone(self):
        self.toon.setAnimState('off', 1.0)

    def filterDone(self, request, args):
        if request == 'Done':
            return None
        else:
            return self.defaultFilter(request, args)
        return None

    def exitDone(self):
        pass

    def handleGameStart(self):
        self.accept(Globals.GagCollisionName + '-into-' + self.gagCollisionName, self.handleGagHit)

    def hitByDrop(self):
        if self.state == 'Normal':
            self.request('Hit')
        if self.equippedGag != None:
            self.removeGag()
        return

    def handleGagHit(self, collEntry):
        gagNodePath = collEntry.getFromNodePath().getParent()
        messenger.send(self.GagHitEventName, [self.toon.doId, gagNodePath])

    def hitByGag(self):
        self.doSplat()

    def equipGag(self):
        if self.equippedGag != None:
            return
        self.toon.setAnimState('Catching')
        holdingGag = self.gagModel.copyTo(self.toon.leftHand)
        holdingGag.setScale(Globals.GagPickupScale)
        color = random.choice(Globals.GagColors)
        holdingGag.setColorScale(color)
        holdingGag.setZ(-0.2)
        holdingGag.setX(self.toon, 0)
        holdingGag.setHpr(0, 0, 0)
        self.equippedGag = holdingGag
        return

    def removeGag(self):
        if self.equippedGag is None:
            return
        self.toon.setAnimState('Happy')
        self.equippedGag.detachNode()
        self.equippedGag = None
        return

    def createThrowGag(self, gag):
        throwGag = gag.copyTo(NodePath('gag'))
        return throwGag

    def removed(self):
        messenger.send(self.RemovedEventName, [self])

    def showToonThrowingGag(self, heading, pos):
        gag = self.equippedGag
        if gag is None:
            return
        self.removeGag()
        tossTrack, flyTrack, object = self.getThrowInterval(gag, pos[0], pos[1], pos[2], heading, 0, 0)

        def matchRunningAnim(toon = self.toon):
            toon.playingAnim = None
            toon.setSpeed(toon.forwardSpeed, toon.rotateSpeed)
            return

        newTossTrack = Sequence(tossTrack, Func(matchRunningAnim))
        throwTrack = Parallel(newTossTrack, flyTrack)
        throwTrack.start(0)
        return object

    def completeThrow(self):
        self.toon.loop('neutral')

    def getThrowInterval(self, gag, x, y, z, h, p, r):
        toon = self.toon
        flyGag = self.createThrowGag(gag)
        throwSoundIval = self._throwSfx
        if throwSoundIval.isPlaying():
            throwSoundIval.finish()
        throwSoundIval.node = toon
        toonThrowIval1 = ActorInterval(toon, 'throw', startFrame=Globals.ThrowStartFrame, endFrame=Globals.ThrowEndFrame, playRate=Globals.ThrowPlayRate, partName='torso')
        toss = Track((0, Sequence(Func(toon.setPosHpr, x, y, z, h, p, r), Func(gag.reparentTo, toon.rightHand), Func(gag.setPosHpr, 0, 0, 0, 0, 0, 0), toonThrowIval1)), (toonThrowIval1.getDuration(), Parallel(Func(gag.detachNode), Sequence(ActorInterval(toon, 'throw', startFrame=Globals.ThrowEndFrame + 1, playRate=Globals.ThrowPlayRate, partName='torso'), Func(self.completeThrow)))))

        def getEndPos(toon = toon):
            return render.getRelativePoint(toon, Point3(0, Globals.ThrowDistance, 0))

        fly = Track((0, throwSoundIval), (toonThrowIval1.getDuration(), Sequence(Func(flyGag.reparentTo, render), Func(flyGag.setPosHpr, toon, 0.52, 0.97, 2.24, 0, -45, 0), ProjectileInterval(flyGag, endPos=getEndPos, duration=Globals.ThrowDuration), Func(flyGag.detachNode))))
        return (toss, fly, flyGag)

    def _getToonAnimationIval(self, animName, startFrame = 0, duration = 1, nextState = None):
        totalFrames = self.toon.getNumFrames(animName)
        frames = totalFrames - 1 - startFrame
        frameRate = self.toon.getFrameRate(animName)
        newRate = frames / duration
        playRate = newRate / frameRate
        ival = Sequence(ActorInterval(self.toon, animName, startTime=startFrame / newRate, endTime=totalFrames / newRate, playRate=playRate))
        if nextState is not None:

            def done():
                self.request(nextState)

            ival.append(Func(done))
        return ival
