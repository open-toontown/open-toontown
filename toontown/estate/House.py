from pandac.PandaModules import *
from toontown.toonbase.ToonBaseGlobal import *
from direct.directnotify import DirectNotifyGlobal
from toontown.hood import Place
from direct.showbase import DirectObject
from direct.fsm import StateData
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from direct.task import Task
from otp.distributed.TelemetryLimiter import RotationLimitToH, TLGatherAllAvs
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer

class House(Place.Place):
    notify = DirectNotifyGlobal.directNotify.newCategory('House')

    def __init__(self, loader, avId, parentFSMState, doneEvent):
        Place.Place.__init__(self, loader, doneEvent)
        self.id = ToontownGlobals.MyEstate
        self.ownersAvId = avId
        self.dnaFile = 'phase_7/models/modules/toon_interior'
        self.isInterior = 1
        self.tfaDoneEvent = 'tfaDoneEvent'
        self.oldStyle = None
        self.fsm = ClassicFSM.ClassicFSM('House', [State.State('start', self.enterStart, self.exitStart, ['doorIn', 'teleportIn', 'tutorial']),
         State.State('walk', self.enterWalk, self.exitWalk, ['sit',
          'stickerBook',
          'doorOut',
          'DFA',
          'teleportOut',
          'quest',
          'purchase',
          'closet',
          'banking',
          'phone',
          'stopped']),
         State.State('sit', self.enterSit, self.exitSit, ['walk']),
         State.State('stickerBook', self.enterStickerBook, self.exitStickerBook, ['walk',
          'DFA',
          'sit',
          'doorOut',
          'teleportOut',
          'quest',
          'purchase',
          'closet',
          'banking',
          'phone',
          'stopped']),
         State.State('DFA', self.enterDFA, self.exitDFA, ['DFAReject', 'teleportOut', 'doorOut']),
         State.State('DFAReject', self.enterDFAReject, self.exitDFAReject, ['walk']),
         State.State('doorIn', self.enterDoorIn, self.exitDoorIn, ['walk']),
         State.State('doorOut', self.enterDoorOut, self.exitDoorOut, ['walk']),
         State.State('teleportIn', self.enterTeleportIn, self.exitTeleportIn, ['walk']),
         State.State('teleportOut', self.enterTeleportOut, self.exitTeleportOut, ['teleportIn']),
         State.State('quest', self.enterQuest, self.exitQuest, ['walk', 'doorOut']),
         State.State('tutorial', self.enterTutorial, self.exitTutorial, ['walk', 'quest']),
         State.State('purchase', self.enterPurchase, self.exitPurchase, ['walk', 'doorOut']),
         State.State('closet', self.enterCloset, self.exitCloset, ['walk']),
         State.State('banking', self.enterBanking, self.exitBanking, ['walk']),
         State.State('phone', self.enterPhone, self.exitPhone, ['walk']),
         State.State('stopped', self.enterStopped, self.exitStopped, ['walk']),
         State.State('final', self.enterFinal, self.exitFinal, ['start', 'teleportIn'])], 'start', 'final')
        self.parentFSMState = parentFSMState
        return

    def load(self):
        Place.Place.load(self)
        self.parentFSMState.addChild(self.fsm)

    def unload(self):
        Place.Place.unload(self)
        self.parentFSMState.removeChild(self.fsm)
        del self.parentFSMState
        del self.fsm
        ModelPool.garbageCollect()
        TexturePool.garbageCollect()

    def enter(self, requestStatus):
        self.zoneId = requestStatus['zoneId']
        self.fsm.enterInitialState()
        messenger.send('enterHouse')
        self.accept('doorDoneEvent', self.handleDoorDoneEvent)
        self.accept('DistributedDoor_doorTrigger', self.handleDoorTrigger)
        self._telemLimiter = TLGatherAllAvs('House', RotationLimitToH)
        NametagGlobals.setMasterArrowsOn(1)
        self.fsm.request(requestStatus['how'], [requestStatus])

    def exit(self):
        self.ignoreAll()
        if hasattr(self, 'fsm'):
            self.fsm.requestFinalState()
        self._telemLimiter.destroy()
        del self._telemLimiter
        messenger.send('exitHouse')
        NametagGlobals.setMasterArrowsOn(0)

    def setState(self, state):
        if hasattr(self, 'fsm'):
            self.fsm.request(state)

    def getZoneId(self):
        return self.zoneId

    def enterTutorial(self, requestStatus):
        self.fsm.request('walk')
        base.localAvatar.b_setParent(ToontownGlobals.SPRender)
        globalClock.tick()
        base.transitions.irisIn()
        messenger.send('enterTutorialInterior')

    def exitTutorial(self):
        pass

    def enterTeleportIn(self, requestStatus):
        base.localAvatar.setPosHpr(2.5, 11.5, ToontownGlobals.FloorOffset, 45.0, 0.0, 0.0)
        Place.Place.enterTeleportIn(self, requestStatus)

    def enterTeleportOut(self, requestStatus):
        Place.Place.enterTeleportOut(self, requestStatus, self.__teleportOutDone)

    def __teleportOutDone(self, requestStatus):
        if hasattr(self, 'fsm'):
            self.fsm.requestFinalState()
        self.notify.debug('House: teleportOutDone: requestStatus = %s' % requestStatus)
        hoodId = requestStatus['hoodId']
        zoneId = requestStatus['zoneId']
        avId = requestStatus['avId']
        shardId = requestStatus['shardId']
        if hoodId == ToontownGlobals.MyEstate and zoneId == self.getZoneId():
            self.fsm.request('teleportIn', [requestStatus])
        elif hoodId == ToontownGlobals.MyEstate:
            self.getEstateZoneAndGoHome(requestStatus)
        else:
            self.doneStatus = requestStatus
            messenger.send(self.doneEvent, [self.doneStatus])

    def goHomeFailed(self, task):
        self.notifyUserGoHomeFailed()
        self.ignore('setLocalEstateZone')
        self.doneStatus['avId'] = -1
        self.doneStatus['zoneId'] = self.getZoneId()
        self.fsm.request('teleportIn', [self.doneStatus])
        return Task.done

    def exitTeleportOut(self):
        Place.Place.exitTeleportOut(self)

    def enterPurchase(self):
        Place.Place.enterPurchase(self)

    def exitPurchase(self):
        Place.Place.exitPurchase(self)

    def enterCloset(self):
        base.localAvatar.b_setAnimState('neutral', 1)
        self.accept('teleportQuery', self.handleTeleportQuery)
        base.localAvatar.setTeleportAvailable(1)
        base.localAvatar.laffMeter.start()
        base.localAvatar.obscureMoveFurnitureButton(1)
        base.localAvatar.startSleepWatch(self.__handleFallingAsleepCloset)
        self.enablePeriodTimer()

    def __handleFallingAsleepCloset(self, arg):
        if hasattr(self, 'fsm'):
            self.fsm.request('walk')
        messenger.send('closetAsleep')
        base.localAvatar.forceGotoSleep()

    def exitCloset(self):
        base.localAvatar.setTeleportAvailable(0)
        self.ignore('teleportQuery')
        base.localAvatar.laffMeter.stop()
        base.localAvatar.obscureMoveFurnitureButton(-1)
        base.localAvatar.stopSleepWatch()
        self.disablePeriodTimer()

    def enterBanking(self):
        Place.Place.enterBanking(self)

    def exitBanking(self):
        Place.Place.exitBanking(self)
