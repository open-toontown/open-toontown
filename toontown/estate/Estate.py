from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from toontown.toonbase.ToonBaseGlobal import *
from toontown.toonbase.ToontownGlobals import *
from direct.gui.DirectGui import *
from direct.distributed.ClockDelta import *
from toontown.hood import Place
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State
from direct.task.Task import Task
from toontown.toonbase import TTLocalizer
import random
from direct.showbase import PythonUtil
from toontown.hood import Place
from toontown.hood import SkyUtil
from toontown.pets import PetTutorial
from direct.controls.GravityWalker import GravityWalker
from otp.distributed.TelemetryLimiter import RotationLimitToH, TLGatherAllAvs, TLNull
import HouseGlobals

class Estate(Place.Place):
    notify = DirectNotifyGlobal.directNotify.newCategory('Estate')

    def __init__(self, loader, avId, zoneId, parentFSMState, doneEvent):
        Place.Place.__init__(self, None, doneEvent)
        self.id = MyEstate
        self.avId = avId
        self.zoneId = zoneId
        self.loader = loader
        self.cameraSubmerged = -1
        self.toonSubmerged = -1
        self.fsm = ClassicFSM.ClassicFSM('Estate', [State.State('init', self.enterInit, self.exitInit, ['final',
          'teleportIn',
          'doorIn',
          'walk']),
         State.State('petTutorial', self.enterPetTutorial, self.exitPetTutorial, ['walk']),
         State.State('walk', self.enterWalk, self.exitWalk, ['final',
          'sit',
          'stickerBook',
          'options',
          'quest',
          'fishing',
          'mailbox',
          'stopped',
          'DFA',
          'trialerFA',
          'doorOut',
          'push',
          'pet']),
         State.State('stopped', self.enterStopped, self.exitStopped, ['walk', 'teleportOut']),
         State.State('sit', self.enterSit, self.exitSit, ['walk']),
         State.State('push', self.enterPush, self.exitPush, ['walk']),
         State.State('stickerBook', self.enterStickerBook, self.exitStickerBook, ['walk',
          'sit',
          'quest',
          'fishing',
          'mailbox',
          'stopped',
          'doorOut',
          'push',
          'pet',
          'DFA',
          'trialerFA']),
         State.State('teleportIn', self.enterTeleportIn, self.exitTeleportIn, ['walk', 'petTutorial']),
         State.State('teleportOut', self.enterTeleportOut, self.exitTeleportOut, ['teleportIn', 'walk', 'final']),
         State.State('doorIn', self.enterDoorIn, self.exitDoorIn, ['walk']),
         State.State('doorOut', self.enterDoorOut, self.exitDoorOut, ['final', 'walk']),
         State.State('final', self.enterFinal, self.exitFinal, ['teleportIn']),
         State.State('quest', self.enterQuest, self.exitQuest, ['walk']),
         State.State('fishing', self.enterFishing, self.exitFishing, ['walk', 'stopped']),
         State.State('mailbox', self.enterMailbox, self.exitMailbox, ['walk', 'stopped']),
         State.State('stopped', self.enterStopped, self.exitStopped, ['walk']),
         State.State('pet', self.enterPet, self.exitPet, ['walk', 'trialerFA']),
         State.State('trialerFA', self.enterTrialerFA, self.exitTrialerFA, ['trialerFAReject', 'DFA']),
         State.State('trialerFAReject', self.enterTrialerFAReject, self.exitTrialerFAReject, ['walk']),
         State.State('DFA', self.enterDFA, self.exitDFA, ['DFAReject', 'teleportOut']),
         State.State('DFAReject', self.enterDFAReject, self.exitDFAReject, ['walk'])], 'init', 'final')
        self.fsm.enterInitialState()
        self.doneEvent = doneEvent
        self.parentFSMState = parentFSMState
        return

    def delete(self):
        self.unload()

    def load(self):
        Place.Place.load(self)
        self.fog = Fog('EstateFog')
        taskMgr.add(self.__checkCameraUnderwater, 'estate-check-cam-underwater')
        path = self.loader.geom.find('**/Path')
        path.setBin('ground', 10, 1)
        self.parentFSMState.addChild(self.fsm)

    def unload(self):
        self.ignoreAll()
        self.notify.info('remove estate-check-toon-underwater to TaskMgr in unload()')
        taskMgr.remove('estate-check-toon-underwater')
        taskMgr.remove('estate-check-cam-underwater')
        self.parentFSMState.removeChild(self.fsm)
        del self.fsm
        self.fog = None
        Place.Place.unload(self)
        return

    def enter(self, requestStatus):
        hoodId = requestStatus['hoodId']
        zoneId = requestStatus['zoneId']
        newsManager = base.cr.newsManager
        if config.GetBool('want-estate-telemetry-limiter', 1):
            limiter = TLGatherAllAvs('Estate', RotationLimitToH)
        else:
            limiter = TLNull()
        self._telemLimiter = limiter
        if newsManager:
            holidayIds = base.cr.newsManager.getDecorationHolidayId()
            if (ToontownGlobals.HALLOWEEN_COSTUMES in holidayIds or ToontownGlobals.SPOOKY_COSTUMES in holidayIds) and self.loader.hood.spookySkyFile:
                lightsOff = Sequence(LerpColorScaleInterval(base.cr.playGame.hood.loader.geom, 0.1, Vec4(0.55, 0.55, 0.65, 1)), Func(self.loader.hood.startSpookySky))
                lightsOff.start()
            else:
                self.loader.hood.startSky()
                lightsOn = LerpColorScaleInterval(base.cr.playGame.hood.loader.geom, 0.1, Vec4(1, 1, 1, 1))
                lightsOn.start()
        else:
            self.loader.hood.startSky()
            lightsOn = LerpColorScaleInterval(base.cr.playGame.hood.loader.geom, 0.1, Vec4(1, 1, 1, 1))
            lightsOn.start()
        self.loader.hood.sky.setFogOff()
        self.__setFaintFog()
        for i in self.loader.nodeList:
            self.loader.enterAnimatedProps(i)

        self.loader.geom.reparentTo(render)
        if hasattr(base.cr, 'newsManager') and base.cr.newsManager:
            holidayIds = base.cr.newsManager.getHolidayIdList()
            if ToontownGlobals.APRIL_FOOLS_COSTUMES in holidayIds or ToontownGlobals.SILLYMETER_EXT_HOLIDAY in holidayIds:
                self.startAprilFoolsControls()
        self.accept('doorDoneEvent', self.handleDoorDoneEvent)
        self.accept('DistributedDoor_doorTrigger', self.handleDoorTrigger)
        self.fsm.request(requestStatus['how'], [requestStatus])

    def startAprilFoolsControls(self):
        if isinstance(base.localAvatar.controlManager.currentControls, GravityWalker):
            base.localAvatar.controlManager.currentControls.setGravity(32.174 * 0.75)

    def stopAprilFoolsControls(self):
        if isinstance(base.localAvatar.controlManager.currentControls, GravityWalker):
            base.localAvatar.controlManager.currentControls.setGravity(32.174 * 2.0)

    def exit(self):
        base.localAvatar.stopChat()
        if hasattr(base.cr, 'newsManager') and base.cr.newsManager:
            holidayIds = base.cr.newsManager.getHolidayIdList()
            if ToontownGlobals.APRIL_FOOLS_COSTUMES in holidayIds or ToontownGlobals.SILLYMETER_EXT_HOLIDAY in holidayIds:
                self.stopAprilFoolsControls()
        self._telemLimiter.destroy()
        del self._telemLimiter
        if hasattr(self, 'fsm'):
            self.fsm.requestFinalState()
        self.loader.geom.reparentTo(hidden)
        for i in self.loader.nodeList:
            self.loader.exitAnimatedProps(i)

        self.loader.hood.stopSky()
        render.setFogOff()
        base.cr.cache.flush()

    def __setZoneId(self, zoneId):
        self.zoneId = zoneId

    def detectedMailboxCollision(self):
        self.fsm.request('mailbox')

    def detectedGardenPlotUse(self):
        if hasattr(self, 'fsm'):
            self.fsm.request('stopped')

    def detectedGardenPlotDone(self):
        if hasattr(self, 'fsm'):
            self.fsm.request('walk')

    def detectedFlowerSellUse(self):
        if hasattr(self, 'fsm'):
            self.fsm.request('stopped')

    def detectedFlowerSellDone(self):
        if hasattr(self, 'fsm'):
            self.fsm.request('walk')

    def doRequestLeave(self, requestStatus):
        self.fsm.request('trialerFA', [requestStatus])

    def enterInit(self):
        pass

    def exitInit(self):
        pass

    def enterPetTutorial(self, bDummy = True):
        self.notify.info('remove estate-check-toon-underwater to TaskMgr in enterPetTutorial()')
        taskMgr.remove('estate-check-toon-underwater')
        self.petTutorialDoneEvent = 'PetTutorialDone'
        self.acceptOnce(self.petTutorialDoneEvent, self.petTutorialDone)
        self.petTutorial = PetTutorial.PetTutorial(self.petTutorialDoneEvent)

    def exitPetTutorial(self):
        self.notify.info('add estate-check-toon-underwater to TaskMgr in exitPetTutorial()')
        if hasattr(self, 'fsm'):
            taskMgr.add(self.__checkToonUnderwater, 'estate-check-toon-underwater')
        if hasattr(self, 'petTutorial') and self.petTutorial is not None:
            self.petTutorial.destroy()
        return

    def petTutorialDone(self):
        self.ignore(self.petTutorialDoneEvent)
        self.petTutorial.destroy()
        self.petTutorial = None
        self.fsm.request('walk', [1])
        return

    def enterMailbox(self):
        Place.Place.enterPurchase(self)
        base.localAvatar.startSleepWatch(self.__handleFallingAsleepMailbox)
        self.enablePeriodTimer()

    def __handleFallingAsleepMailbox(self, arg):
        if hasattr(self, 'fsm'):
            self.fsm.request('walk')
        messenger.send('mailboxAsleep')
        base.localAvatar.forceGotoSleep()

    def exitMailbox(self):
        Place.Place.exitPurchase(self)
        base.localAvatar.stopSleepWatch()
        self.disablePeriodTimer()

    def enterTeleportIn(self, requestStatus):
        self._etiToken = self.addSetZoneCompleteCallback(Functor(self._teleportToHouse, requestStatus))
        Place.Place.enterTeleportIn(self, requestStatus)

    def _teleportToHouse(self, requestStatus):
        try:
            houseDo = base.cr.doId2do.get(base.localAvatar.houseId)
            house = houseDo.house
            pos = house.getPos(render)
            base.localAvatar.detachNode()
            base.localAvatar.setPosHpr(house, 17, 3, 0, 125, 0, 0)
        except:
            x, y, z, h, p, r = HouseGlobals.defaultEntryPoint
            base.localAvatar.detachNode()
            base.localAvatar.setPosHpr(render, x, y, z, h, p, r)

        base.localAvatar.setScale(1, 1, 1)
        self.toonSubmerged = -1
        self.notify.info('remove estate-check-toon-underwater to TaskMgr in enterTeleportIn()')
        taskMgr.remove('estate-check-toon-underwater')
        if base.wantPets:
            if base.localAvatar.hasPet() and not base.localAvatar.bPetTutorialDone:
                self.nextState = 'petTutorial'

    def teleportInDone(self):
        self.notify.debug('teleportInDone')
        self.toonSubmerged = -1
        if self.nextState is not 'petTutorial':
            self.notify.info('add estate-check-toon-underwater to TaskMgr in teleportInDone()')
            if hasattr(self, 'fsm'):
                taskMgr.add(self.__checkToonUnderwater, 'estate-check-toon-underwater')
        Place.Place.teleportInDone(self)

    def exitTeleportIn(self):
        self.removeSetZoneCompleteCallback(self._etiToken)
        Place.Place.exitTeleportIn(self)

    def enterTeleportOut(self, requestStatus):
        Place.Place.enterTeleportOut(self, requestStatus, self.__teleportOutDone)

    def __teleportOutDone(self, requestStatus):
        if hasattr(self, 'fsm'):
            self.fsm.requestFinalState()
        hoodId = requestStatus['hoodId']
        zoneId = requestStatus['zoneId']
        avId = requestStatus['avId']
        shardId = requestStatus['shardId']
        if hoodId == ToontownGlobals.MyEstate and zoneId == self.getZoneId() and shardId == None:
            self.fsm.request('teleportIn', [requestStatus])
        elif hoodId == ToontownGlobals.MyEstate and shardId == None:
            self.doneStatus = requestStatus
            self.getEstateZoneAndGoHome(requestStatus)
        else:
            self.doneStatus = requestStatus
            messenger.send(self.doneEvent, [self.doneStatus])
        return

    def goHomeFailed(self, task):
        self.notifyUserGoHomeFailed()
        self.ignore('setLocalEstateZone')
        self.doneStatus['avId'] = -1
        self.doneStatus['zoneId'] = self.getZoneId()
        self.fsm.request('teleportIn', [self.doneStatus])
        return Task.done

    def exitTeleportOut(self):
        Place.Place.exitTeleportOut(self)

    def exitDoorIn(self):
        self.toonSubmerged = -1
        self.notify.info('add estate-check-toon-underwater to TaskMgr in exitDoorIn()')
        if hasattr(self, 'fsm'):
            taskMgr.add(self.__checkToonUnderwater, 'estate-check-toon-underwater')
        Place.Place.exitDoorIn(self)

    def getZoneId(self):
        if self.zoneId:
            return self.zoneId
        else:
            self.notify.warning('no zone id available')

    def __checkCameraUnderwater(self, task):
        if camera.getZ(render) < -1.2:
            self.__submergeCamera()
        else:
            self.__emergeCamera()
        return Task.cont

    def __checkToonUnderwater(self, task):
        if base.localAvatar.getZ() < -4.0:
            self.__submergeToon()
        else:
            self.__emergeToon()
        return Task.cont

    def __submergeCamera(self):
        if self.cameraSubmerged == 1:
            return
        self.__setUnderwaterFog()
        base.playSfx(self.loader.underwaterSound, looping=1, volume=0.8)
        self.cameraSubmerged = 1
        self.walkStateData.setSwimSoundAudible(1)

    def __emergeCamera(self):
        if self.cameraSubmerged == 0:
            return
        self.loader.underwaterSound.stop()
        self.loader.hood.sky.setFogOff()
        self.__setFaintFog()
        self.cameraSubmerged = 0
        self.walkStateData.setSwimSoundAudible(0)

    def forceUnderWater(self):
        self.toonSubmerged = 0
        self.__submergeToon()

    def __submergeToon(self):
        if self.toonSubmerged == 1:
            return
        self.notify.debug('continuing in __submergeToon')
        if hasattr(self, 'loader') and self.loader:
            base.playSfx(self.loader.submergeSound)
        if base.config.GetBool('disable-flying-glitch') == 0:
            self.fsm.request('walk')
        self.walkStateData.fsm.request('swimming', [self.loader.swimSound])
        pos = base.localAvatar.getPos(render)
        base.localAvatar.d_playSplashEffect(pos[0], pos[1], -2.3)
        self.toonSubmerged = 1

    def __emergeToon(self):
        if self.toonSubmerged == 0:
            return
        self.notify.debug('continuing in __emergeToon')
        if hasattr(self, 'walkStateData'):
            self.walkStateData.fsm.request('walking')
        self.toonSubmerged = 0
        if hasattr(base.cr, 'newsManager') and base.cr.newsManager:
            holidayIds = base.cr.newsManager.getHolidayIdList()
            if ToontownGlobals.APRIL_FOOLS_COSTUMES in holidayIds or ToontownGlobals.SILLYMETER_EXT_HOLIDAY in holidayIds:
                self.startAprilFoolsControls()
            else:
                self.stopAprilFoolsControls()

    def __setUnderwaterFog(self):
        if base.wantFog:
            self.fog.setColor(Vec4(0.0, 0.0, 0.6, 1.0))
            self.fog.setLinearRange(0.1, 100.0)
            render.setFog(self.fog)
            self.loader.hood.sky.setFog(self.fog)

    def __setWhiteFog(self):
        if base.wantFog:
            self.fog.setColor(Vec4(0.8, 0.8, 0.8, 1.0))
            self.fog.setLinearRange(0.0, 400.0)
            render.setFog(self.fog)
            self.loader.hood.sky.setFog(self.fog)

    def __setFaintFog(self):
        if base.wantFog:
            self.fog.setColor(Vec4(0.8, 0.8, 0.8, 1.0))
            self.fog.setLinearRange(0.0, 700.0)
            render.setFog(self.fog)
