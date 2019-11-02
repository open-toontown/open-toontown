from pandac.PandaModules import *
import Playground
from direct.task.Task import Task
import random
from direct.fsm import ClassicFSM, State
from direct.actor import Actor
from toontown.toonbase import ToontownGlobals
from direct.directnotify import DirectNotifyGlobal
from toontown.hood import Place

class DDPlayground(Playground.Playground):
    notify = DirectNotifyGlobal.directNotify.newCategory('DDPlayground')

    def __init__(self, loader, parentFSM, doneEvent):
        Playground.Playground.__init__(self, loader, parentFSM, doneEvent)
        self.cameraSubmerged = -1
        self.toonSubmerged = -1
        self.activityFsm = ClassicFSM.ClassicFSM('Activity', [State.State('off', self.enterOff, self.exitOff, ['OnBoat']), State.State('OnBoat', self.enterOnBoat, self.exitOnBoat, ['off'])], 'off', 'off')
        self.activityFsm.enterInitialState()

    def load(self):
        Playground.Playground.load(self)

    def unload(self):
        del self.activityFsm
        Playground.Playground.unload(self)

    def enter(self, requestStatus):
        self.nextSeagullTime = 0
        taskMgr.add(self.__seagulls, 'dd-seagulls')
        self.loader.hood.setWhiteFog()
        Playground.Playground.enter(self, requestStatus)

    def exit(self):
        Playground.Playground.exit(self)
        taskMgr.remove('dd-check-toon-underwater')
        taskMgr.remove('dd-check-cam-underwater')
        taskMgr.remove('dd-seagulls')
        self.loader.hood.setNoFog()

    def enterStart(self):
        self.cameraSubmerged = 0
        self.toonSubmerged = 0
        taskMgr.add(self.__checkToonUnderwater, 'dd-check-toon-underwater')
        taskMgr.add(self.__checkCameraUnderwater, 'dd-check-cam-underwater')

    def enterDoorOut(self):
        taskMgr.remove('dd-check-toon-underwater')

    def exitDoorOut(self):
        pass

    def enterDoorIn(self, requestStatus):
        Playground.Playground.enterDoorIn(self, requestStatus)
        taskMgr.add(self.__checkToonUnderwater, 'dd-check-toon-underwater')

    def __checkCameraUnderwater(self, task):
        if camera.getZ(render) < 1.0:
            self.__submergeCamera()
        else:
            self.__emergeCamera()
        return Task.cont

    def __checkToonUnderwater(self, task):
        if base.localAvatar.getZ() < -2.3314585:
            self.__submergeToon()
        else:
            self.__emergeToon()
        return Task.cont

    def __submergeCamera(self):
        if self.cameraSubmerged == 1:
            return
        self.loader.hood.setUnderwaterFog()
        base.playSfx(self.loader.underwaterSound, looping=1, volume=0.8)
        self.loader.seagullSound.stop()
        taskMgr.remove('dd-seagulls')
        self.cameraSubmerged = 1
        self.walkStateData.setSwimSoundAudible(1)

    def __emergeCamera(self):
        if self.cameraSubmerged == 0:
            return
        self.loader.hood.setWhiteFog()
        self.loader.underwaterSound.stop()
        self.nextSeagullTime = random.random() * 8.0
        taskMgr.add(self.__seagulls, 'dd-seagulls')
        self.cameraSubmerged = 0
        self.walkStateData.setSwimSoundAudible(0)

    def __submergeToon(self):
        if self.toonSubmerged == 1:
            return
        base.playSfx(self.loader.submergeSound)
        if base.config.GetBool('disable-flying-glitch') == 0:
            self.fsm.request('walk')
        self.walkStateData.fsm.request('swimming', [self.loader.swimSound])
        pos = base.localAvatar.getPos(render)
        base.localAvatar.d_playSplashEffect(pos[0], pos[1], 1.675)
        self.toonSubmerged = 1

    def __emergeToon(self):
        if self.toonSubmerged == 0:
            return
        self.walkStateData.fsm.request('walking')
        self.toonSubmerged = 0

    def __seagulls(self, task):
        if task.time < self.nextSeagullTime:
            return Task.cont
        base.playSfx(self.loader.seagullSound)
        self.nextSeagullTime = task.time + random.random() * 4.0 + 8.0
        return Task.cont

    def enterTeleportIn(self, requestStatus):
        self.toonSubmerged = -1
        taskMgr.remove('dd-check-toon-underwater')
        Playground.Playground.enterTeleportIn(self, requestStatus)

    def teleportInDone(self):
        self.toonSubmerged = -1
        taskMgr.add(self.__checkToonUnderwater, 'dd-check-toon-underwater')
        Playground.Playground.teleportInDone(self)

    def enterOff(self):
        return None

    def exitOff(self):
        return None

    def enterOnBoat(self):
        base.localAvatar.b_setParent(ToontownGlobals.SPDonaldsBoat)
        base.playSfx(self.loader.waterSound, looping=1)

    def exitOnBoat(self):
        base.localAvatar.b_setParent(ToontownGlobals.SPRender)
        self.loader.waterSound.stop()
