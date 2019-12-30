from pandac.PandaModules import *
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
from otp.distributed.TelemetryLimiter import RotationLimitToH, TLGatherAllAvs, TLNull
from toontown.hood import Place
from toontown.hood import SkyUtil
from toontown.parties import PartyPlanner
from toontown.parties.DistributedParty import DistributedParty

class Party(Place.Place):
    notify = DirectNotifyGlobal.directNotify.newCategory('Party')

    def __init__(self, loader, avId, zoneId, parentFSMState, doneEvent):
        Place.Place.__init__(self, None, doneEvent)
        self.id = PartyHood
        self.avId = avId
        self.zoneId = zoneId
        self.loader = loader
        self.musicShouldPlay = False
        self.partyPlannerDoneEvent = 'partyPlannerGuiDone'
        self.fsm = ClassicFSM.ClassicFSM('Party', [State.State('init', self.enterInit, self.exitInit, ['final', 'teleportIn', 'walk']),
         State.State('walk', self.enterWalk, self.exitWalk, ['final',
          'sit',
          'stickerBook',
          'options',
          'quest',
          'fishing',
          'stopped',
          'DFA',
          'trialerFA',
          'push',
          'activity']),
         State.State('stopped', self.enterStopped, self.exitStopped, ['walk', 'teleportOut']),
         State.State('sit', self.enterSit, self.exitSit, ['walk']),
         State.State('push', self.enterPush, self.exitPush, ['walk']),
         State.State('partyPlanning', self.enterPartyPlanning, self.exitPartyPlanning, ['DFA', 'teleportOut']),
         State.State('stickerBook', self.enterStickerBook, self.exitStickerBook, ['walk',
          'sit',
          'quest',
          'fishing',
          'stopped',
          'activity',
          'push',
          'DFA',
          'trialerFA']),
         State.State('teleportIn', self.enterTeleportIn, self.exitTeleportIn, ['walk', 'partyPlanning']),
         State.State('teleportOut', self.enterTeleportOut, self.exitTeleportOut, ['teleportIn', 'walk', 'final']),
         State.State('died', self.enterDied, self.exitDied, ['walk', 'final']),
         State.State('final', self.enterFinal, self.exitFinal, ['teleportIn']),
         State.State('quest', self.enterQuest, self.exitQuest, ['walk']),
         State.State('fishing', self.enterFishing, self.exitFishing, ['walk', 'stopped']),
         State.State('activity', self.enterActivity, self.exitActivity, ['walk', 'stopped']),
         State.State('stopped', self.enterStopped, self.exitStopped, ['walk']),
         State.State('trialerFA', self.enterTrialerFA, self.exitTrialerFA, ['trialerFAReject', 'DFA']),
         State.State('trialerFAReject', self.enterTrialerFAReject, self.exitTrialerFAReject, ['walk']),
         State.State('DFA', self.enterDFA, self.exitDFA, ['DFAReject', 'teleportOut']),
         State.State('DFAReject', self.enterDFAReject, self.exitDFAReject, ['walk'])], 'init', 'final')
        self.fsm.enterInitialState()
        self.doneEvent = doneEvent
        self.parentFSMState = parentFSMState
        self.isPartyEnding = False
        self.accept('partyStateChanged', self.setPartyState)
        return

    def delete(self):
        self.unload()

    def load(self):
        self.fog = Fog('PartyFog')
        Place.Place.load(self)
        if hasattr(base.localAvatar, 'aboutToPlanParty') and base.localAvatar.aboutToPlanParty:
            if not hasattr(self, 'partyPlanner') or self.partyPlanner is None:
                self.partyPlanner = PartyPlanner.PartyPlanner(self.partyPlannerDoneEvent)
        self.parentFSMState.addChild(self.fsm)
        return

    def unload(self):
        if hasattr(self, 'partyPlanner'):
            self.ignore(self.partyPlannerDoneEvent)
            self.partyPlanner.close()
            del self.partyPlanner
        self.__removePartyHat()
        self.fog = None
        self.ignoreAll()
        self.parentFSMState.removeChild(self.fsm)
        del self.fsm
        Place.Place.unload(self)
        return

    def enter(self, requestStatus):
        hoodId = requestStatus['hoodId']
        zoneId = requestStatus['zoneId']
        if config.GetBool('want-party-telemetry-limiter', 1):
            limiter = TLGatherAllAvs('Party', RotationLimitToH)
        else:
            limiter = TLNull()
        self._telemLimiter = limiter
        self.loader.hood.startSky()
        for i in self.loader.nodeList:
            self.loader.enterAnimatedProps(i)

        self.loader.geom.reparentTo(render)
        self.fsm.request(requestStatus['how'], [requestStatus])
        self.playMusic()

    def playMusic(self):
        if not hasattr(base, 'partyHasJukebox') or not base.partyHasJukebox:
            base.playMusic(self.loader.music, looping=1, volume=1)

    def exit(self):
        base.localAvatar.stopChat()
        if hasattr(self, 'fsm'):
            self.fsm.requestFinalState()
        self.loader.geom.reparentTo(hidden)
        for i in self.loader.nodeList:
            self.loader.exitAnimatedProps(i)

        self._telemLimiter.destroy()
        del self._telemLimiter
        self.loader.hood.stopSky()
        render.setFogOff()
        base.cr.cache.flush()
        self.loader.music.stop()
        self.notify.debug('exit')
        self.ignoreAll()

    def __setZoneId(self, zoneId):
        self.zoneId = zoneId

    def doRequestLeave(self, requestStatus):
        self.fsm.request('trialerFA', [requestStatus])

    def enterInit(self):
        pass

    def exitInit(self):
        pass

    def enterPartyPlanning(self, requestStatus):
        base.localAvatar.aboutToPlanParty = False
        self.accept(self.partyPlannerDoneEvent, self.handlePartyPlanningDone)

    def handlePartyPlanningDone(self):
        self.ignore(self.partyPlannerDoneEvent)
        self.partyPlanner.close()
        del self.partyPlanner
        messenger.send('deallocateZoneIdFromPlannedParty', [base.localAvatar.zoneId])
        hoodId = base.localAvatar.lastHood
        self.fsm.request('teleportOut', [{'avId': -1,
          'zoneId': hoodId,
          'shardId': None,
          'how': 'teleportIn',
          'hoodId': hoodId,
          'loader': 'safeZoneLoader',
          'where': 'playground'}])
        return

    def exitPartyPlanning(self):
        pass

    def enterTeleportIn(self, requestStatus):
        self._partyTiToken = None
        if hasattr(base, 'distributedParty'):
            self.__updateLocalAvatarTeleportIn(requestStatus)
        elif hasattr(base.localAvatar, 'aboutToPlanParty') and base.localAvatar.aboutToPlanParty:
            self.__updateLocalAvatarTeleportIn(requestStatus)
        else:
            self.acceptOnce(DistributedParty.generatedEvent, self.__updateLocalAvatarTeleportIn, [requestStatus])
        return

    def exitTeleportIn(self):
        Place.Place.exitTeleportIn(self)
        self.removeSetZoneCompleteCallback(self._partyTiToken)

    def __updateLocalAvatarTeleportIn(self, requestStatus):
        self.ignore(DistributedParty.generatedEvent)
        if hasattr(base, 'distributedParty'):
            x, y, z = base.distributedParty.getClearSquarePos()
            self.accept('generate-' + str(base.distributedParty.partyInfo.hostId), self.__setPartyHat)
            self.__setPartyHat()
        else:
            x, y, z = (0.0, 0.0, 0.1)
        base.localAvatar.detachNode()
        base.localAvatar.setPos(render, x, y, z)
        base.localAvatar.lookAt(0.0, 0.0, 0.1)
        base.localAvatar.setScale(1, 1, 1)
        Place.Place.enterTeleportIn(self, requestStatus)
        if hasattr(base, 'distributedParty') and base.distributedParty:
            self.setPartyState(base.distributedParty.getPartyState())
        if hasattr(base.localAvatar, 'aboutToPlanParty') and base.localAvatar.aboutToPlanParty:
            self._partyTiToken = self.addSetZoneCompleteCallback(Functor(self._partyTeleportInPostZoneComplete, requestStatus), 150)

    def _partyTeleportInPostZoneComplete(self, requestStatus):
        self.nextState = 'partyPlanning'

    def __setPartyHat(self, doId = None):
        if hasattr(base, 'distributedParty'):
            if base.distributedParty.partyInfo.hostId in base.cr.doId2do:
                host = base.cr.doId2do[base.distributedParty.partyInfo.hostId]
                if hasattr(host, 'gmIcon') and host.gmIcon:
                    host.removeGMIcon()
                    host.setGMPartyIcon()
                else:
                    base.distributedParty.partyHat.reparentTo(host.nametag.getNameIcon())

    def __removePartyHat(self):
        if hasattr(base, 'distributedParty'):
            if base.distributedParty.partyInfo.hostId in base.cr.doId2do:
                host = base.cr.doId2do[base.distributedParty.partyInfo.hostId]
                if hasattr(host, 'gmIcon') and host.gmIcon:
                    host.removeGMIcon()
                    host.setGMIcon()

    def enterTeleportOut(self, requestStatus):
        Place.Place.enterTeleportOut(self, requestStatus, self.__teleportOutDone)

    def __teleportOutDone(self, requestStatus):
        if hasattr(self, 'fsm'):
            self.fsm.requestFinalState()
        hoodId = requestStatus['hoodId']
        zoneId = requestStatus['zoneId']
        avId = requestStatus['avId']
        shardId = requestStatus['shardId']
        if hoodId == ToontownGlobals.PartyHood and zoneId == self.getZoneId() and shardId == None:
            self.fsm.request('teleportIn', [requestStatus])
        elif hoodId == ToontownGlobals.MyEstate:
            self.doneStatus = requestStatus
            self.getEstateZoneAndGoHome(requestStatus)
        else:
            self.doneStatus = requestStatus
            messenger.send(self.doneEvent, [self.doneStatus])
        return

    def goHomeFailed(self, task):
        self.notifyUserGoHomeFailed()
        self.doneStatus['avId'] = -1
        self.doneStatus['zoneId'] = self.getZoneId()
        self.fsm.request('teleportIn', [self.doneStatus])
        return Task.done

    def exitTeleportOut(self):
        Place.Place.exitTeleportOut(self)

    def getZoneId(self):
        if self.zoneId:
            return self.zoneId
        else:
            self.notify.warning('no zone id available')

    def enterActivity(self, setAnimState = True):
        if setAnimState:
            base.localAvatar.b_setAnimState('neutral', 1)
        self.accept('teleportQuery', self.handleTeleportQuery)
        base.localAvatar.setTeleportAvailable(False)
        base.localAvatar.laffMeter.start()

    def exitActivity(self):
        base.localAvatar.setTeleportAvailable(True)
        self.ignore('teleportQuery')
        base.localAvatar.laffMeter.stop()

    def setPartyState(self, partyState):
        self.isPartyEnding = partyState

    def handleTeleportQuery(self, fromAvatar, toAvatar):
        if self.isPartyEnding:
            teleportNotify.debug('party ending, sending teleportResponse')
            fromAvatar.d_teleportResponse(toAvatar.doId, 0, toAvatar.defaultShard, base.cr.playGame.getPlaceId(), self.getZoneId())
        elif base.config.GetBool('want-tptrack', False):
            if toAvatar == localAvatar:
                localAvatar.doTeleportResponse(fromAvatar, toAvatar, toAvatar.doId, 1, toAvatar.defaultShard, base.cr.playGame.getPlaceId(), self.getZoneId(), fromAvatar.doId)
            else:
                self.notify.warning('handleTeleportQuery toAvatar.doId != localAvatar.doId' % (toAvatar.doId, localAvatar.doId))
        else:
            fromAvatar.d_teleportResponse(toAvatar.doId, 1, toAvatar.defaultShard, base.cr.playGame.getPlaceId(), self.getZoneId())
