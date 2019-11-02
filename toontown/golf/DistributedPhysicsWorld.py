from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from pandac.PandaModules import *
from math import *
import math
from direct.fsm.FSM import FSM
from toontown.minigame import ArrowKeys
from direct.showbase import PythonUtil
from direct.showutil import Rope
from direct.task import Task
from direct.distributed.ClockDelta import *
import BuildGeometry
from toontown.golf import GolfGlobals
from toontown.golf import PhysicsWorldBase
import random, time
from direct.interval.SoundInterval import SoundInterval

def scalp(vec, scal):
    vec0 = vec[0] * scal
    vec1 = vec[1] * scal
    vec2 = vec[2] * scal
    vec = Vec3(vec0, vec1, vec2)


def length(vec):
    return sqrt(vec[0] ** 2 + vec[1] ** 2 + vec[2] ** 2)


class DistributedPhysicsWorld(DistributedObject.DistributedObject, PhysicsWorldBase.PhysicsWorldBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPhysicsWorld')

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        PhysicsWorldBase.PhysicsWorldBase.__init__(self, 1)
        self.accept('ode toggle contacts', self.__handleToggleContacts)
        self.physicsSfxDict = {}

    def generate(self):
        DistributedObject.DistributedObject.generate(self)
        self.setupSimulation()
        self.startSim()

    def delete(self):
        DistributedObject.DistributedObject.delete(self)
        PhysicsWorldBase.PhysicsWorldBase.delete(self)
        taskMgr.remove('simulation task')
        self.ignoreAll()
        for index in self.physicsSfxDict:
            sfxPair = self.physicsSfxDict[index]
            sfxPair[0].stop()
            sfxPair[1].finish()

        self.physicsSfxDict = None
        return

    def clientCommonObject(self, type, commonId, pos, hpr, sizeX, sizeY, moveDistance):
        data = self.createCommonObject(type, commonId, pos, hpr, sizeX, sizeY, moveDistance)
        index = data[1]
        if type == 3:
            cross = self.commonObjectDict[commonId][2]
            for pair in self.odePandaRelationList:
                pandaNodePathGeom = pair[0]
                odeBody = pair[1]
                if odeBody == cross:
                    base.sfxPlayer.setCutoffDistance(240)
                    self.notify.debug('nodePath = %s' % pandaNodePathGeom)
                    windmillSfx = loader.loadSfx('phase_6/audio/sfx/Golf_Windmill_Loop.wav')
                    windMillSoundInterval = SoundInterval(windmillSfx, node=pandaNodePathGeom, listenerNode=base.camera, seamlessLoop=True, volume=0.5)
                    windMillSoundInterval.loop()
                    self.physicsSfxDict[index] = (windmillSfx, windMillSoundInterval)
                    break

        elif type == 4:
            box = self.commonObjectDict[commonId][2]
            for pair in self.odePandaRelationList:
                pandaNodePathGeom = pair[0]
                odeBody = pair[1]
                if odeBody == box:
                    self.notify.debug('nodePath = %s' % pandaNodePathGeom)
                    moverSfx = loader.loadSfx('phase_6/audio/sfx/Golf_Moving_Barrier.mp3')
                    moverSoundInterval = SoundInterval(moverSfx, node=pandaNodePathGeom, listenerNode=base.camera, seamlessLoop=True, volume=0.5)
                    moverSoundInterval.start()
                    self.physicsSfxDict[index] = (moverSfx, moverSoundInterval, index)
                    break

    def commonObjectEvent(self, key, model, type, force, event):
        self.notify.debug('commonObjectForceEvent key %s model %s type %s force %s event %s' % (key,
         model,
         type,
         force,
         event))
        if type == 4:
            if event > 0:
                self.physicsSfxDict[key][1].start()

    def setCommonObjects(self, objectData):
        self.useCommonObjectData(objectData)

    def upSendCommonObjects(self):
        self.sendUpdate('upSetCommonObjects', [self.getCommonObjectData()])

    def __handleToggleContacts(self, message = None):
        if self.showContacts:
            self.showContacts = 0
        else:
            self.showContacts = 1
