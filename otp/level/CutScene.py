from direct.showbase import DirectObject
from direct.directnotify import DirectNotifyGlobal
from . import BasicEntities
from pandac.PandaModules import *
from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from direct.distributed.ClockDelta import *
from toontown.toonbase import ToontownGlobals
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM

def nothing(self, track, subjectNodePath, duration):
    return track


def irisInOut(self, track, subjectNodePath, duration):
    track.append(Sequence(Func(base.transitions.irisOut, 0.5), Func(base.transitions.irisIn, 1.5), Wait(duration), Func(base.transitions.irisOut, 1.0), Func(base.transitions.irisIn, 0.5)))
    return track


def letterBox(self, track, subjectNodePath, duration):
    track.append(Sequence(Wait(duration)))
    return track


def foo1(self, track, subjectNodePath, duration):
    track.append(Sequence(Func(base.localAvatar.stopUpdateSmartCamera), PosHprInterval(camera, other=subjectNodePath, pos=Point3(-2, -35, 7.5), hpr=VBase3(-7, 0, 0)), LerpPosHprInterval(nodePath=camera, other=subjectNodePath, duration=duration, pos=Point3(2, -22, 7.5), hpr=VBase3(4, 0, 0), blendType='easeInOut'), PosHprInterval(camera, other=subjectNodePath, pos=Point3(0, -28, 7.5), hpr=VBase3(0, 0, 0)), Func(base.localAvatar.startUpdateSmartCamera)))
    return track


def doorUnlock(self, track, subjectNodePath, duration):
    track.append(Sequence(Func(base.localAvatar.stopUpdateSmartCamera), PosHprInterval(camera, other=self, pos=Point3(-2, -35, 7.5), hpr=VBase3(-7, 0, 0)), LerpPosHprInterval(nodePath=camera, other=self, duration=duration, pos=Point3(2, -22, 7.5), hpr=VBase3(4, 0, 0), blendType='easeInOut'), PosHprInterval(camera, other=self, pos=Point3(0, -28, 7.5), hpr=VBase3(0, 0, 0)), Func(base.localAvatar.startUpdateSmartCamera)))
    return track


class CutScene(BasicEntities.NodePathEntity, DirectObject.DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('CutScene')
    effects = {'nothing': nothing,
     'irisInOut': irisInOut,
     'letterBox': letterBox}
    motions = {'foo1': foo1,
     'doorUnlock': doorUnlock}

    def __init__(self, level, entId):
        DirectObject.DirectObject.__init__(self)
        BasicEntities.NodePathEntity.__init__(self, level, entId)
        self.track = None
        self.setEffect(self.effect)
        self.setMotion(self.motion)
        self.subjectNodePath = render.attachNewNode('CutScene')
        self.subjectNodePath.setPos(self.pos)
        self.subjectNodePath.setHpr(self.hpr)
        self.setStartStop(self.startStopEvent)
        return

    def destroy(self):
        self.ignore(self.startStopEvent)
        self.startStopEvent = None
        BasicEntities.NodePathEntity.destroy(self)
        return

    def setEffect(self, effect):
        self.effect = effect
        self.getEffect = self.effects[effect]

    def setMotion(self, motion):
        self.motionType = motion
        self.getMotion = self.motions[motion]

    def setSubjectNodePath(self, subjectNodePath):
        self.subjectNodePath = subjectNodePath

    def startOrStop(self, start):
        trackName = 'cutSceneTrack-%d' % (id(self),)
        if start:
            if self.track:
                self.track.finish()
                self.track = None
            track = Parallel(name=trackName)
            track = self.getEffect(self, track, self.subjectNodePath, self.duration)
            track = self.getMotion(self, track, self.subjectNodePath, self.duration)
            track = Sequence(Wait(0.4), track)
            track.start(0.0)
            self.track = track
        elif self.track:
            self.track.pause()
            self.track = None
            base.localAvatar.startUpdateSmartCamera()
        return

    def setStartStop(self, event):
        if self.startStopEvent:
            self.ignore(self.startStopEvent)
        self.startStopEvent = self.getOutputEventName(event)
        if self.startStopEvent:
            self.accept(self.startStopEvent, self.startOrStop)

    def getName(self):
        return 'switch-%s' % (self.entId,)
