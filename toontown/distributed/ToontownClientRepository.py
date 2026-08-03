from panda3d.core import *
from direct.distributed.ClockDelta import *
from direct.gui.DirectGui import *
from direct.interval.IntervalGlobal import ivalMgr
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.PyDatagramIterator import PyDatagramIterator
from direct.fsm import State
from direct.showbase.PythonUtil import Functor, ScratchPad
from otp.avatar import Avatar
from otp.distributed import OTPClientRepository
from otp.distributed import PotentialAvatar
from otp.distributed.OtpDoGlobals import *
from otp.distributed import OtpDoGlobals
from otp.otpbase import OTPGlobals
from otp.otpbase import OTPLocalizer
from otp.otpbase import OTPLauncherGlobals
from otp.avatar.Avatar import teleportNotify
from toontown.toonbase.ToonBaseGlobal import *
from toontown.toonbase.ToontownGlobals import *
from toontown.launcher.DownloadForceAcknowledge import *
from toontown.distributed import DelayDelete
from toontown.friends import FriendHandle
from toontown.friends import FriendsListPanel
from toontown.friends import ToontownFriendSecret
from toontown.login import DateObject
from toontown.login import AvatarChooser
from toontown.makeatoon import MakeAToon
from toontown.pets import DistributedPet, PetDetail, PetHandle
from toontown.toonbase import TTLocalizer
from toontown.toontowngui import TTDialog
from toontown.toon import LocalToon
from toontown.toon import ToonDNA
from toontown.distributed import ToontownDistrictStats
from toontown.parties import ToontownTimeManager
from toontown.toon import Toon, DistributedToon
from .ToontownMsgTypes import *
from . import HoodMgr
from . import PlayGame
from toontown.toontowngui import ToontownLoadingBlocker
from toontown.hood import StreetSign
import faulthandler

class ToontownClientRepository(OTPClientRepository.OTPClientRepository):
    SupportTutorial = 1
    GameGlobalsId = OTP_DO_ID_TOONTOWN
    SetZoneDoneEvent = 'TCRSetZoneDone'
    EmuSetZoneDoneEvent = 'TCREmuSetZoneDone'
    SetInterest = 'Set'
    ClearInterest = 'Clear'
    ClearInterestDoneEvent = 'TCRClearInterestDone'
    KeepSubShardObjects = False

    def __init__(self, serverVersion, launcher = None):
        OTPClientRepository.OTPClientRepository.__init__(self, serverVersion, launcher, playGame=PlayGame.PlayGame)
        # Pick-a-Toon TTC revamp: keep a preloaded TTC backdrop alive across
        # the set-avatar transition, then hand it off to PlayGame.
        self._keepPickAToonBackdrop = False
        # Paired with OTPClientRepository.enterPlayGame: only endBulkLoad if we began.
        self._localAvatarPlayGameBulkLoadActive = False
        self._playerAvDclass = self.dclassesByName['DistributedToon']
        setInterfaceFont(TTLocalizer.InterfaceFont)
        setSignFont(TTLocalizer.SignFont)
        setFancyFont(TTLocalizer.FancyFont)
        nameTagFontIndex = 0
        for font in TTLocalizer.NametagFonts:
            setNametagFont(nameTagFontIndex, TTLocalizer.NametagFonts[nameTagFontIndex])
            nameTagFontIndex += 1

        self.toons = {}
        if self.http.getVerifySsl() != HTTPClient.VSNoVerify:
            self.http.setVerifySsl(HTTPClient.VSNoDateCheck)
        #prepareAvatar(self.http)
        self.__forbidCheesyEffects = 0
        self.friendManager = None
        self.speedchatRelay = None
        self.trophyManager = None
        self.bankManager = None
        self.catalogManager = None
        self.welcomeValleyManager = None
        self.newsManager = None
        self.wantStreetSign = ConfigVariableBool('want-street-sign', 0).value
        if self.wantStreetSign:
            self.streetSign = None
        self.distributedDistrict = None
        self.partyManager = None
        self.inGameNewsMgr = None
        self.whitelistMgr = None
        self.toontownTimeManager = ToontownTimeManager.ToontownTimeManager()
        self.avatarFriendsManager = self.generateGlobalObject(OtpDoGlobals.OTP_DO_ID_AVATAR_FRIENDS_MANAGER, 'AvatarFriendsManager')
        self.playerFriendsManager = self.generateGlobalObject(OtpDoGlobals.OTP_DO_ID_PLAYER_FRIENDS_MANAGER, 'TTPlayerFriendsManager')
        self.speedchatRelay = self.generateGlobalObject(OtpDoGlobals.OTP_DO_ID_TOONTOWN_SPEEDCHAT_RELAY, 'TTSpeedchatRelay')
        self.deliveryManager = self.generateGlobalObject(OtpDoGlobals.OTP_DO_ID_TOONTOWN_DELIVERY_MANAGER, 'DistributedDeliveryManager')
        if ConfigVariableBool('want-code-redemption', 1).value:
            self.codeRedemptionManager = self.generateGlobalObject(OtpDoGlobals.OTP_DO_ID_TOONTOWN_CODE_REDEMPTION_MANAGER, 'TTCodeRedemptionMgr')
        if self.wantStreetSign:
            self.streetSign = None
        self.furnitureManager = None
        self.objectManager = None
        self.magicWordManager = None
        self.friendsMap = {}
        self.friendsOnline = {}
        self.friendsMapPending = 0
        self.friendsListError = 0
        self.friendPendingChatSettings = {}
        self.elderFriendsMap = {}
        self.__queryAvatarMap = {}
        self.dateObject = DateObject.DateObject()
        self.hoodMgr = HoodMgr.HoodMgr(self)
        self.setZonesEmulated = 0
        self.old_setzone_interest_handle = None
        self._setZoneOpSerial = 0
        self.setZoneQueue = Queue()
        self.accept(ToontownClientRepository.SetZoneDoneEvent, self._handleEmuSetZoneDone)
        self.previousInterestZones = None
        self._deletedSubShardDoIds = set()
        self.toonNameDict = {}
        self.gameFSM.addState(State.State('skipTutorialRequest', self.enterSkipTutorialRequest, self.exitSkipTutorialRequest, ['playGame', 'gameOff', 'tutorialQuestion']))
        state = self.gameFSM.getStateNamed('waitOnEnterResponses')
        state.addTransition('skipTutorialRequest')
        state = self.gameFSM.getStateNamed('playGame')
        state.addTransition('skipTutorialRequest')
        self.wantCogdominiums = ConfigVariableBool('want-cogdominiums', 1).value
        self.wantEmblems = ConfigVariableBool('want-emblems', 0).value
        if ConfigVariableBool('tt-node-check', 0).value:
            for species in ToonDNA.toonSpeciesTypes:
                for head in ToonDNA.getHeadList(species):
                    for torso in ToonDNA.toonTorsoTypes:
                        for legs in ToonDNA.toonLegTypes:
                            for gender in ('m', 'f'):
                                print('species: %s, head: %s, torso: %s, legs: %s, gender: %s' % (species,
                                 head,
                                 torso,
                                 legs,
                                 gender))
                                dna = ToonDNA.ToonDNA()
                                dna.newToon((head,
                                 torso,
                                 legs,
                                 gender))
                                toon = Toon.Toon()
                                try:
                                    toon.setDNA(dna)
                                except Exception as e:
                                    print(e)

        return

    def congratulations(self, avatarChoice):
        self.acceptedScreen = loader.loadModel('phase_3/models/gui/toon_council')
        self.acceptedScreen.setScale(0.667)
        self.acceptedScreen.reparentTo(aspect2d)
        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        self.acceptedBanner = DirectLabel(parent=self.acceptedScreen, relief=None, text=OTPLocalizer.CRNameCongratulations, text_scale=0.18, text_fg=Vec4(0.6, 0.1, 0.1, 1), text_pos=(0, 0.05), text_font=getMinnieFont())
        newName = avatarChoice.approvedName
        self.acceptedText = DirectLabel(parent=self.acceptedScreen, relief=None, text=OTPLocalizer.CRNameAccepted % newName, text_scale=0.125, text_fg=Vec4(0, 0, 0, 1), text_pos=(0, -0.15))
        self.okButton = DirectButton(parent=self.acceptedScreen, image=(buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr')), relief=None, text='Ok', scale=1.5, text_scale=0.05, text_pos=(0.0, -0.1), pos=(0, 0, -1), command=self.__handleCongrats, extraArgs=[avatarChoice])
        buttons.removeNode()
        base.transitions.noFade()
        return

    def __handleCongrats(self, avatarChoice):
        self.acceptedBanner.destroy()
        self.acceptedText.destroy()
        self.okButton.destroy()
        self.acceptedScreen.removeNode()
        del self.acceptedScreen
        del self.okButton
        del self.acceptedText
        del self.acceptedBanner
        if not __astron__:
            datagram = PyDatagram()
            datagram.addUint16(CLIENT_SET_WISHNAME_CLEAR)
            datagram.addUint32(avatarChoice.id)
            datagram.addUint8(1)
            self.send(datagram)
            self.loginFSM.request('waitForSetAvatarResponse', [avatarChoice])
        else:
            self.astronLoginManager.sendAcknowledgeAvatarName(avatarChoice.id,
                                                              lambda: self.loginFSM.request('waitForSetAvatarResponse', [avatarChoice]))

    def betterlucknexttime(self, avList, index):
        self.rejectDoneEvent = 'rejectDone'
        self.rejectDialog = TTDialog.TTGlobalDialog(doneEvent=self.rejectDoneEvent, message=TTLocalizer.NameShopNameRejected, style=TTDialog.Acknowledge)
        self.rejectDialog.show()
        self.acceptOnce(self.rejectDoneEvent, self.__handleReject, [avList, index])
        base.transitions.noFade()

    def __handleReject(self, avList, index):
        self.rejectDialog.cleanup()
        if not __astron__:
            datagram = PyDatagram()
            datagram.addUint16(CLIENT_SET_WISHNAME_CLEAR)
        avid = 0
        for k in avList:
            if k.position == index:
                avid = k.id

        if avid == 0:
            self.notify.error('Avatar rejected not found in avList.  Index is: ' + str(index))
        if not __astron__:
            datagram.addUint32(avid)
            datagram.addUint8(0)
            self.send(datagram)
            self.loginFSM.request('waitForAvatarList')
        else:
            self.astronLoginManager.sendAcknowledgeAvatarName(avid, lambda: self.loginFSM.request('waitForAvatarList'))

    def enterChooseAvatar(self, avList):
        ModelPool.garbageCollect()
        TexturePool.garbageCollect()
        self.sendSetAvatarIdMsg(0)
        self.clearFriendState()
        self.__preloadPickAToonTTCBackdrop()
        # Modern launcher transition: keep the new loading screen up through
        # server connect, then transition out into Pick-a-Toon.
        try:
            ml = getattr(base, 'modernLoading', None)
            if ml:
                ml.set_title('Toontown', 'Pick-a-Toon')
                ml.set_status('Loading Pick-a-Toon…')
                ml.set_progress(72)
                base.graphicsEngine.renderFrame()
        except Exception:
            pass
        if self.music == None and base.musicManagerIsValid:
            self.music = base.musicManager.getSound('phase_3/audio/bgm/tt_theme.ogg')
            if self.music:
                self.music.setLoop(1)
                self.music.setVolume(0.9)
                self.music.play()
        base.playMusic(self.music, looping=1, volume=0.9, interrupt=None)
        self.handler = self.handleMessageType
        self.avChoiceDoneEvent = 'avatarChooserDone'
        self.avChoice = AvatarChooser.AvatarChooser(avList, self.loginFSM, self.avChoiceDoneEvent)
        self.avChoice.load(self.isPaid())
        self.avChoice.enter()
        self.accept(self.avChoiceDoneEvent, self.__handleAvatarChooserDone, [avList])
        # Legacy download blocker can still be used for phase downloads, but
        # default to the modern overlay if present.
        try:
            ml = getattr(base, 'modernLoading', None)
            if ml:
                ml.set_status('Ready.')
                ml.set_progress(100)
                ml.transition_out()
            else:
                if ConfigVariableBool('want-gib-loader', 1).value:
                    self.loadingBlocker = ToontownLoadingBlocker.ToontownLoadingBlocker(avList)
        except Exception:
            if ConfigVariableBool('want-gib-loader', 1).value:
                self.loadingBlocker = ToontownLoadingBlocker.ToontownLoadingBlocker(avList)
        return

    def __handleAvatarChooserDone(self, avList, doneStatus):
        done = doneStatus['mode']
        if done == 'exit':
            self.cleanupPickAToonTTCBackdrop()
            if not launcher.isDummy():
                if not self.isPaid():
                    self.loginFSM.request('shutdown', [OTPLauncherGlobals.ExitUpsell])
                else:
                    self.loginFSM.request('shutdown')
            else:
                self.loginFSM.request('shutdown')
            return
        index = self.avChoice.getChoice()
        for av in avList:
            if av.position == index:
                avatarChoice = av
                self.notify.info('================')
                self.notify.info('Chose avatar id: %s' % av.id)
                self.notify.info('Chose avatar name: %s' % av.name)
                dna = ToonDNA.ToonDNA()
                dna.makeFromNetString(av.dna)
                if base.logPrivateInfo:
                    self.notify.info('Chose avatar dna: %s' % (dna.asTuple(),))
                    self.notify.info('Chose avatar position: %s' % av.position)
                    self.notify.info('isPaid: %s' % self.isPaid())
                    self.notify.info('freeTimeLeft: %s' % self.freeTimeLeft())
                    self.notify.info('allowSecretChat: %s' % self.allowSecretChat())
                self.notify.info('================')

        if done == 'chose':
            self.avChoice.exit()
            if avatarChoice.approvedName != '':
                self.cleanupPickAToonTTCBackdrop()
                self.congratulations(avatarChoice)
                avatarChoice.approvedName = ''
            elif avatarChoice.rejectedName != '':
                self.cleanupPickAToonTTCBackdrop()
                avatarChoice.rejectedName = ''
                self.betterlucknexttime(avList, index)
            else:
                # Keep the preloaded TTC backdrop so entering PlayGame can reuse
                # it and spawn immediately into the already-loaded scene.
                self._keepPickAToonBackdrop = True
                self.loginFSM.request('waitForSetAvatarResponse', [avatarChoice])
        elif done == 'nameIt':
            self._keepPickAToonBackdrop = False
            self.cleanupPickAToonTTCBackdrop()
            self.accept('downloadAck-response', self.__handleDownloadAck, [avList, index])
            self.downloadAck = DownloadForceAcknowledge('downloadAck-response')
            self.downloadAck.enter(4)
        elif done == 'create':
            self._keepPickAToonBackdrop = False
            self.cleanupPickAToonTTCBackdrop()
            self.loginFSM.request('createAvatar', [avList, index])
        elif done == 'delete':
            self._keepPickAToonBackdrop = False
            self.cleanupPickAToonTTCBackdrop()
            self.loginFSM.request('waitForDeleteAvatarResponse', [avatarChoice])

    def __handleDownloadAck(self, avList, index, doneStatus):
        if doneStatus['mode'] == 'complete':
            self.goToPickAName(avList, index)
        else:
            self.loginFSM.request('chooseAvatar', [avList])
        self.downloadAck.exit()
        self.downloadAck = None
        self.ignore('downloadAck-response')
        return

    def exitChooseAvatar(self):
        self.handler = None
        self.avChoice.exit()
        self.avChoice.unload()
        self.avChoice = None
        self.ignore(self.avChoiceDoneEvent)
        # If the user picked a toon, keep the backdrop alive across the
        # set-avatar transition so PlayGame can reuse it.
        if not getattr(self, '_keepPickAToonBackdrop', False):
            self.cleanupPickAToonTTCBackdrop()
        return

    def __preloadPickAToonTTCBackdrop(self):
        """
        Revamp: Render the Pick-a-Toon UI on top of a live Toontown Central
        safezone backdrop. This intentionally loads only the hood geometry/sky,
        and does NOT enter the playground state (which requires a localAvatar).
        """
        try:
            if not ConfigVariableBool('want-pick-a-toon-ttc-backdrop', 0).value:
                return
        except Exception:
            return
        # Track whether the backdrop could not be created, so Pick-a-Toon can
        # fall back to legacy background art instead of a blank/grey screen.
        try:
            self._pickAToonTTCBackdropFailed = False
        except Exception:
            pass
        if getattr(self, '_pickAToonTTCBackdrop', None):
            return
        try:
            from toontown.toonbase import ToontownGlobals
            from toontown.hood import TTHood
        except Exception:
            return

        try:
            # Ensure PlayGame has a DNA store ready for hood loading.
            self.playGame.loadDnaStore()
        except Exception:
            # If this fails, just skip the backdrop (picker still works).
            return

        hoodId = ToontownGlobals.ToontownCentral
        requestStatus = {
            'loader': 'safeZoneLoader',
            'where': 'playground',
            'how': 'teleportIn',
            'hoodId': hoodId,
            'zoneId': hoodId,
            'shardId': None,
            'avId': -1,
        }

        # Important: some Panda3D NodePath operations can assert in C++ (not raise
        # Python exceptions). Be very defensive here to avoid hard crashes or
        # "Assertion failed: !is_empty()" spew. If anything is missing/empty,
        # mark failed and let Pick-a-Toon fall back to legacy art.
        hood = None
        try:
            hood = TTHood.TTHood(self.playGame.fsm, self.playGame.hoodDoneEvent, self.playGame.dnaStore, hoodId)
            hood.load()
            try:
                hood.startSky()
            except Exception:
                pass
            hood.loadLoader(requestStatus)

            geom = None
            try:
                if hasattr(hood, 'loader') and hasattr(hood.loader, 'geom'):
                    geom = hood.loader.geom
            except Exception:
                geom = None

            if not geom or geom.isEmpty():
                try:
                    self._pickAToonTTCBackdropFailed = True
                except Exception:
                    pass
                try:
                    hood.unload()
                except Exception:
                    pass
                return

            try:
                geom.reparentTo(render)
            except Exception:
                try:
                    self._pickAToonTTCBackdropFailed = True
                except Exception:
                    pass
                try:
                    hood.unload()
                except Exception:
                    pass
                return

            # Apply outdoor lighting only if enabled and safe.
            self._pickAToonTTCBackdropHasLighting = False
            try:
                if ConfigVariableBool('pick-a-toon-ttc-backdrop-want-lighting', 0).value:
                    from toontown.hood import OutdoorLighting
                    OutdoorLighting.begin(geom, 'playground', hoodId=hoodId)
                    self._pickAToonTTCBackdropHasLighting = True
            except Exception:
                self._pickAToonTTCBackdropHasLighting = False

            # Camera pose while picking (safe best-effort).
            try:
                base.disableMouse()
                if getattr(base, 'camera', None) and not base.camera.isEmpty():
                    base.camera.reparentTo(render)
                    base.camera.setPos(0, -70, 28)
                    base.camera.setHpr(0, -10, 0)
            except Exception:
                pass

            self._pickAToonTTCBackdrop = hood
            self._pickAToonTTCBackdropRequestStatus = requestStatus
        except Exception:
            try:
                self._pickAToonTTCBackdropFailed = True
            except Exception:
                pass
            try:
                if hood:
                    hood.unload()
            except Exception:
                pass
            self._pickAToonTTCBackdrop = None
            self._pickAToonTTCBackdropRequestStatus = None
            self._pickAToonTTCBackdropHasLighting = False

    def cleanupPickAToonTTCBackdrop(self):
        hood = getattr(self, '_pickAToonTTCBackdrop', None)
        if not hood:
            return
        try:
            if getattr(self, '_pickAToonTTCBackdropHasLighting', False) and hasattr(hood, 'loader') and hasattr(hood.loader, 'geom'):
                from toontown.hood import OutdoorLighting
                OutdoorLighting.end(hood.loader.geom)
        except Exception:
            pass
        try:
            hood.stopSky()
        except Exception:
            pass
        try:
            hood.unload()
        except Exception:
            pass
        self._pickAToonTTCBackdrop = None
        self._pickAToonTTCBackdropRequestStatus = None
        self._pickAToonTTCBackdropHasLighting = False
        # The backdrop TTHood used playGame.dnaStore. hood.unload() calls
        # dnaStore.resetHood() and drops the Hood's reference, but PlayGame still
        # keeps the same DNAStorage. loadDnaStore() only runs when dnaStore is
        # missing — so the next real hood load would reuse a half-reset store
        # and mix neighborhoods (assertions / instant exit). Force a full reset.
        try:
            self.playGame.unloadDnaStore()
        except Exception:
            pass

    def goToPickAName(self, avList, index):
        self.avChoice.exit()
        self.loginFSM.request('createAvatar', [avList, index])

    def enterCreateAvatar(self, avList, index, newDNA = None):
        if self.music:
            self.music.stop()
            self.music = None
        if newDNA != None:
            self.newPotAv = PotentialAvatar.PotentialAvatar('deleteMe', ['',
             '',
             '',
             ''], newDNA.makeNetString(), index, 1)
            avList.append(self.newPotAv)
        base.transitions.noFade()
        self.avCreate = MakeAToon.MakeAToon(self.loginFSM, avList, 'makeAToonComplete', index, self.isPaid())
        self.avCreate.load()
        self.avCreate.enter()
        if not __astron__:
            self.handler = self.handleCreateAvatar
        self.accept('makeAToonComplete', self.__handleMakeAToon, [avList, index])
        self.accept('nameShopCreateAvatar', self.sendCreateAvatarMsg)
        self.accept('nameShopPost', self.relayMessage)
        return

    def relayMessage(self, dg):
        self.send(dg)

    def handleCreateAvatar(self, msgType, di):
        if msgType == CLIENT_CREATE_AVATAR_RESP or msgType == CLIENT_SET_NAME_PATTERN_ANSWER or msgType == CLIENT_SET_WISHNAME_RESP:
            self.avCreate.ns.nameShopHandler(msgType, di)
        else:
            self.handleMessageType(msgType, di)

    def __handleMakeAToon(self, avList, avPosition):
        done = self.avCreate.getDoneStatus()
        if done == 'cancel':
            if hasattr(self, 'newPotAv'):
                if self.newPotAv in avList:
                    avList.remove(self.newPotAv)
            self.avCreate.exit()
            self.loginFSM.request('chooseAvatar', [avList])
        elif done == 'created':
            self.avCreate.exit()
            if not base.launcher or base.launcher.getPhaseComplete(3.5):
                for i in avList:
                    if i.position == avPosition:
                        newPotAv = i

                self.loginFSM.request('waitForSetAvatarResponse', [newPotAv])
            else:
                self.loginFSM.request('chooseAvatar', [avList])
        else:
            self.notify.error('Invalid doneStatus from MakeAToon: ' + str(done))

    def exitCreateAvatar(self):
        self.ignore('makeAToonComplete')
        self.ignore('nameShopPost')
        self.ignore('nameShopCreateAvatar')
        self.avCreate.unload()
        self.avCreate = None
        self.handler = None
        if hasattr(self, 'newPotAv'):
            del self.newPotAv
        return

    if not __astron__:
        def handleAvatarResponseMsg(self, di):
            self.cleanupWaitingForDatabase()
            avatarId = di.getUint32()
            returnCode = di.getUint8()
            if returnCode == 0:
                dclass = self.dclassesByName['DistributedToon']
                NametagGlobals.setMasterArrowsOn(0)
                # Revamp: when using the Pick-a-Toon TTC backdrop, avoid putting
                # up a blocking loading screen while generating localAvatar.
                if not getattr(self, '_keepPickAToonBackdrop', False):
                    loader.beginBulkLoad('localAvatarPlayGame', OTPLocalizer.CREnteringToontown, 400, 1, TTLocalizer.TIP_GENERAL)
                    self._localAvatarPlayGameBulkLoadActive = True
                else:
                    self._localAvatarPlayGameBulkLoadActive = False
                localAvatar = LocalToon.LocalToon(self)
                localAvatar.dclass = dclass
                base.localAvatar = localAvatar
                __builtins__['localAvatar'] = base.localAvatar
                NametagGlobals.setToon(base.localAvatar)
                localAvatar.doId = avatarId
                self.localAvatarDoId = avatarId
                parentId = None
                zoneId = None
                localAvatar.setLocation(parentId, zoneId)
                localAvatar.generateInit()
                localAvatar.generate()
                localAvatar.updateAllRequiredFields(dclass, di)
                self.doId2do[avatarId] = localAvatar
                localAvatar.initInterface()
                self.sendGetFriendsListRequest()
                self.loginFSM.request('playingGame')
            else:
                self.notify.error('Bad avatar: return code %d' % returnCode)
            return
    else:
        def handleAvatarResponseMsg(self, avatarId, di):
            self.cleanupWaitingForDatabase()
            dclass = self.dclassesByName['DistributedToon']
            NametagGlobals.setMasterArrowsOn(0)
            # Revamp: when using the Pick-a-Toon TTC backdrop, avoid putting
            # up a blocking loading screen while generating localAvatar.
            if not getattr(self, '_keepPickAToonBackdrop', False):
                loader.beginBulkLoad('localAvatarPlayGame', OTPLocalizer.CREnteringToontown, 400, 1, TTLocalizer.TIP_GENERAL)
                self._localAvatarPlayGameBulkLoadActive = True
            else:
                self._localAvatarPlayGameBulkLoadActive = False
            localAvatar = LocalToon.LocalToon(self)
            localAvatar.dclass = dclass
            base.localAvatar = localAvatar
            __builtins__['localAvatar'] = base.localAvatar
            NametagGlobals.setToon(base.localAvatar)
            localAvatar.doId = avatarId
            self.localAvatarDoId = avatarId
            parentId = None
            zoneId = None
            localAvatar.setLocation(parentId, zoneId)
            localAvatar.generateInit()
            localAvatar.generate()
            dclass.receiveUpdateBroadcastRequiredOwner(localAvatar, di)
            localAvatar.announceGenerate()
            localAvatar.postGenerateMessage()
            self.doId2do[avatarId] = localAvatar
            localAvatar.initInterface()
            self.sendGetFriendsListRequest()
            self.loginFSM.request('playingGame')

    def getAvatarDetails(self, avatar, func, *args):
        pad = ScratchPad()
        pad.func = func
        pad.args = args
        pad.avatar = avatar
        pad.delayDelete = DelayDelete.DelayDelete(avatar, 'getAvatarDetails')
        avId = avatar.doId
        self.__queryAvatarMap[avId] = pad
        self.__sendGetAvatarDetails(avId)

    def cancelAvatarDetailsRequest(self, avatar):
        avId = avatar.doId
        if avId in self.__queryAvatarMap:
            pad = self.__queryAvatarMap.pop(avId)
            pad.delayDelete.destroy()

    def __sendGetAvatarDetails(self, avId):
        datagram = PyDatagram()
        avatar = self.__queryAvatarMap[avId].avatar
        datagram.addUint16(avatar.getRequestID())
        datagram.addUint32(avId)
        self.send(datagram)

    def handleGetAvatarDetailsResp(self, di):
        avId = di.getUint32()
        returnCode = di.getUint8()
        self.notify.info('Got query response for avatar %d, code = %d.' % (avId, returnCode))
        try:
            pad = self.__queryAvatarMap[avId]
        except:
            self.notify.warning('Received unexpected or outdated details for avatar %d.' % avId)
            return

        del self.__queryAvatarMap[avId]
        gotData = 0
        if returnCode != 0:
            self.notify.warning('No information available for avatar %d.' % avId)
        else:
            dclassName = pad.args[0]
            dclass = self.dclassesByName[dclassName]
            pad.avatar.updateAllRequiredFields(dclass, di)
            gotData = 1
        if isinstance(pad.func, str):
            messenger.send(pad.func, list((gotData, pad.avatar) + pad.args))
        else:
            pad.func(*(gotData, pad.avatar) + pad.args)
        pad.delayDelete.destroy()

    def enterPlayingGame(self, *args, **kArgs):
        OTPClientRepository.OTPClientRepository.enterPlayingGame(self, *args, **kArgs)
        # Once we are in-game, we no longer need the "keep" latch.
        self._keepPickAToonBackdrop = False
        # Use the correct hoodId and avatarId when entering the shard.
        # Passing -1 here can break downstream zone-load flow and make it
        # look like the client "freezes" during shard entry.
        from toontown.hood import ZoneUtil
        zoneId = base.localAvatar.defaultZone
        hoodId = ZoneUtil.getHoodId(zoneId)
        avId = base.localAvatar.getDoId()
        self.gameFSM.request('waitOnEnterResponses', [None, hoodId, zoneId, avId])
        self._userLoggingOut = False
        
        if self.wantStreetSign and not self.streetSign:
            self.streetSign = StreetSign.StreetSign()
        return

    def exitPlayingGame(self):
        ivalMgr.interrupt()
        if self.objectManager != None:
            self.objectManager.destroy()
            self.objectManager = None
        ToontownFriendSecret.unloadFriendSecret()
        FriendsListPanel.unloadFriendsList()
        messenger.send('cancelFriendInvitation')
        base.removeGlitchMessage()
        taskMgr.remove('avatarRequestQueueTask')
        OTPClientRepository.OTPClientRepository.exitPlayingGame(self)
        if hasattr(base, 'localAvatar'):
            camera.reparentTo(render)
            camera.setPos(0, 0, 0)
            camera.setHpr(0, 0, 0)
            del self.doId2do[base.localAvatar.getDoId()]
            if base.localAvatar.getDelayDeleteCount() != 0:
                self.notify.error('could not delete localAvatar, delayDeletes=%s' % (base.localAvatar.getDelayDeleteNames(),))
            base.localAvatar.deleteOrDelay()
            base.localAvatar.detectLeaks()
            NametagGlobals.setToon(base.cam)
            del base.localAvatar
            del __builtins__['localAvatar']
        loader.abortBulkLoad()
        base.transitions.noTransitions()
        if self._userLoggingOut:
            self.detectLeaks(okTasks=[], okEvents=['destroy-ToontownLoadingScreenTitle', 'destroy-ToontownLoadingScreenTip', 'destroy-ToontownLoadingScreenWaitBar'])
        return

    def enterGameOff(self):
        OTPClientRepository.OTPClientRepository.enterGameOff(self)

    def enterWaitOnEnterResponses(self, shardId, hoodId, zoneId, avId):
        self.resetDeletedSubShardDoIds()
        # Pick-a-Toon preloads TTC behind the chooser. If the avatar's last
        # location was not TTC playground, we must drop that backdrop before
        # shard entry — otherwise TTC and the real hood both load (assertions).
        try:
            from toontown.hood import ZoneUtil
            pre = getattr(self, '_pickAToonTTCBackdrop', None)
            if pre:
                canon = ZoneUtil.getCanonicalZoneId(zoneId)
                loaderName = ZoneUtil.getLoaderName(zoneId)
                reuseBackdrop = canon == ToontownCentral and loaderName == 'safeZoneLoader'
                if not reuseBackdrop:
                    self.cleanupPickAToonTTCBackdrop()
        except Exception:
            pass
        OTPClientRepository.OTPClientRepository.enterWaitOnEnterResponses(self, shardId, hoodId, zoneId, avId)

    def enterSkipTutorialRequest(self, hoodId, zoneId, avId):
        self.handlerArgs = {'hoodId': hoodId,
         'zoneId': zoneId,
         'avId': avId}
        if not __astron__:
            self.handler = self.handleTutorialQuestion
        self.__requestSkipTutorial(hoodId, zoneId, avId)

    def __requestSkipTutorial(self, hoodId, zoneId, avId):
        self.notify.debug('requesting skip tutorial')
        self.acceptOnce('skipTutorialAnswered', self.__handleSkipTutorialAnswered, [hoodId, zoneId, avId])
        messenger.send('requestSkipTutorial')
        self.waitForDatabaseTimeout(requestName='RequestSkipTutorial')

    def __handleSkipTutorialAnswered(self, hoodId, zoneId, avId, allOk):
        if allOk:
            hoodId = self.handlerArgs['hoodId']
            zoneId = self.handlerArgs['zoneId']
            avId = self.handlerArgs['avId']
            self.gameFSM.request('playGame', [hoodId, zoneId, avId])
        else:
            self.notify.warning('allOk is false on skip tutorial, forcing the tutorial.')
            self.gameFSM.request('tutorialQuestion', [hoodId, zoneId, avId])

    def exitSkipTutorialRequest(self):
        self.cleanupWaitingForDatabase()
        self.handler = None
        self.handlerArgs = None
        self.ignore('skipTutorialAnswered')
        return

    def enterTutorialQuestion(self, hoodId, zoneId, avId):
        if not __astron__:
            self.handler = self.handleTutorialQuestion
        self.__requestTutorial(hoodId, zoneId, avId)

    def handleTutorialQuestion(self, msgType, di):
        if msgType == CLIENT_CREATE_OBJECT_REQUIRED:
            self.handleGenerateWithRequired(di)
        elif msgType == CLIENT_CREATE_OBJECT_REQUIRED_OTHER:
            self.handleGenerateWithRequiredOther(di)
        elif msgType == CLIENT_OBJECT_UPDATE_FIELD:
            self.handleUpdateField(di)
        elif msgType == CLIENT_OBJECT_DISABLE_RESP:
            self.handleDisable(di)
        elif msgType == CLIENT_OBJECT_DELETE_RESP:
            self.handleDelete(di)
        elif msgType == CLIENT_GET_FRIEND_LIST_RESP:
            self.handleGetFriendsList(di)
        elif msgType == CLIENT_GET_FRIEND_LIST_EXTENDED_RESP:
            self.handleGetFriendsListExtended(di)
        elif msgType == CLIENT_FRIEND_ONLINE:
            self.handleFriendOnline(di)
        elif msgType == CLIENT_FRIEND_OFFLINE:
            self.handleFriendOffline(di)
        elif msgType == CLIENT_GET_AVATAR_DETAILS_RESP:
            self.handleGetAvatarDetailsResp(di)
        else:
            self.handleMessageType(msgType, di)

    def __requestTutorial(self, hoodId, zoneId, avId):
        # On this Astron stack the client-side TutorialManager (a district
        # object) may never generate, so 'requestTutorial' would have no
        # listener and the AI could never answer -- the client would stall
        # ~75s and then throw the "Lost connection" prompt. If the tutorial
        # manager never showed up, skip the tutorial and go straight into
        # the game (same path as an avatar that already acked it).
        if ConfigVariableBool('skip-tutorial-if-unavailable', True).value and not messenger.whoAccepts('requestTutorial'):
            self.notify.info('TutorialManager not available; skipping tutorial.')
            self.gameFSM.request('playGame', [hoodId, zoneId, avId])
            return
        self.notify.debug('requesting tutorial')
        self.acceptOnce('startTutorial', self.__handleStartTutorial, [avId])
        messenger.send('requestTutorial')
        self.waitForDatabaseTimeout(requestName='RequestTutorial')
        # Safety net: even if the TutorialManager is present, the AI may
        # never answer the request. Rather than stall ~75s into the
        # "Lost connection" prompt, skip into the game after a timeout.
        taskMgr.doMethodLater(ConfigVariableDouble('tutorial-request-timeout', 25.0).value,
                              self.__tutorialRequestTimeout, 'tutorialRequestTimeout',
                              extraArgs=[hoodId, zoneId, avId])

    def __tutorialRequestTimeout(self, hoodId, zoneId, avId):
        taskMgr.remove('tutorialRequestTimeout')
        if self.gameFSM.getCurrentState().getName() == 'tutorialQuestion':
            self.notify.info('Tutorial request timed out; skipping tutorial.')
            self.cleanupWaitingForDatabase()
            self.gameFSM.request('playGame', [hoodId, zoneId, avId])
        return Task.done

    def __handleStartTutorial(self, avId, zoneId):
        self.gameFSM.request('playGame', [Tutorial, zoneId, avId])

    def exitTutorialQuestion(self):
        self.cleanupWaitingForDatabase()
        self.handler = None
        self.handlerArgs = None
        self.ignore('startTutorial')
        taskMgr.remove('waitingForTutorial')
        taskMgr.remove('tutorialRequestTimeout')
        return

    def enterSwitchShards(self, shardId, hoodId, zoneId, avId):
        OTPClientRepository.OTPClientRepository.enterSwitchShards(self, shardId, hoodId, zoneId, avId)
        self.handler = self.handleCloseShard

    def exitSwitchShards(self):
        OTPClientRepository.OTPClientRepository.exitSwitchShards(self)
        self.ignore(ToontownClientRepository.ClearInterestDoneEvent)
        self.handler = None
        return

    def enterCloseShard(self, loginState = None):
        OTPClientRepository.OTPClientRepository.enterCloseShard(self, loginState)
        self.handler = self.handleCloseShard
        self._removeLocalAvFromStateServer()

    if not __astron__:
        def handleCloseShard(self, msgType, di):
            if msgType == CLIENT_CREATE_OBJECT_REQUIRED:
                di2 = PyDatagramIterator(di)
                parentId = di2.getUint32()
                if self._doIdIsOnCurrentShard(parentId):
                    return
            elif msgType == CLIENT_CREATE_OBJECT_REQUIRED_OTHER:
                di2 = PyDatagramIterator(di)
                parentId = di2.getUint32()
                if self._doIdIsOnCurrentShard(parentId):
                    return
            elif msgType == CLIENT_OBJECT_UPDATE_FIELD:
                di2 = PyDatagramIterator(di)
                doId = di2.getUint32()
                if self._doIdIsOnCurrentShard(doId):
                    return
            self.handleMessageType(msgType, di)
    else:
        def handleCloseShard(self, msgType, di):
            if msgType == CLIENT_ENTER_OBJECT_REQUIRED:
                di2 = PyDatagramIterator(di)
                parentId = di2.getUint32()
                if self._doIdIsOnCurrentShard(parentId):
                    return
            elif msgType == CLIENT_ENTER_OBJECT_REQUIRED_OTHER:
                di2 = PyDatagramIterator(di)
                parentId = di2.getUint32()
                if self._doIdIsOnCurrentShard(parentId):
                    return
            elif msgType == CLIENT_OBJECT_SET_FIELD:
                di2 = PyDatagramIterator(di)
                doId = di2.getUint32()
                if self._doIdIsOnCurrentShard(doId):
                    return
            self.handleMessageType(msgType, di)

    def _logFailedDisable(self, doId, ownerView):
        if doId not in self.doId2do and doId in self._deletedSubShardDoIds:
            return
        OTPClientRepository.OTPClientRepository._logFailedDisable(self, doId, ownerView)

    def exitCloseShard(self):
        OTPClientRepository.OTPClientRepository.exitCloseShard(self)
        self.ignore(ToontownClientRepository.ClearInterestDoneEvent)
        self.handler = None
        return

    def isShardInterestOpen(self):
        return self.old_setzone_interest_handle is not None or self.uberZoneInterest is not None

    def resetDeletedSubShardDoIds(self):
        self._deletedSubShardDoIds.clear()

    def dumpAllSubShardObjects(self):
        if self.KeepSubShardObjects:
            return
        isNotLive = not base.cr.isLive()
        if isNotLive:
            try:
                localAvatar
            except:
                self.notify.info('dumpAllSubShardObjects')
            else:
                self.notify.info('dumpAllSubShardObjects: defaultShard is %s' % localAvatar.defaultShard)

            ignoredClasses = ('TimeManager', 'DistributedDistrict', 'FriendManager', 'NewsManager', 'ToontownMagicWordManager', 'WelcomeValleyManager', 'DistributedTrophyMgr', 'CatalogManager', 'DistributedBankMgr', 'EstateManager', 'RaceManager', 'SafeZoneManager', 'DeleteManager', 'TutorialManager', 'ToontownDistrict', 'DistributedDeliveryManager', 'DistributedPartyManager', 'AvatarFriendsManager', 'InGameNewsMgr', 'WhitelistMgr', 'TTCodeRedemptionMgr')
        messenger.send('clientCleanup')
        for avId, pad in list(self.__queryAvatarMap.items()):
            pad.delayDelete.destroy()

        self.__queryAvatarMap = {}
        delayDeleted = []
        doIds = list(self.doId2do.keys())
        for doId in doIds:
            obj = self.doId2do[doId]
            if isNotLive:
                ignoredClass = obj.__class__.__name__ in ignoredClasses
                if not ignoredClass and obj.parentId != localAvatar.defaultShard:
                    self.notify.info('dumpAllSubShardObjects: %s %s parent %s is not defaultShard' % (obj.__class__.__name__, obj.doId, obj.parentId))
            if obj.parentId == localAvatar.defaultShard and obj is not localAvatar:
                if obj.neverDisable:
                    if isNotLive:
                        if not ignoredClass:
                            self.notify.warning('dumpAllSubShardObjects: neverDisable set for %s %s' % (obj.__class__.__name__, obj.doId))
                else:
                    self.deleteObject(doId)
                    self._deletedSubShardDoIds.add(doId)
                    if obj.getDelayDeleteCount() != 0:
                        delayDeleted.append(obj)

        delayDeleteLeaks = []
        for obj in delayDeleted:
            if obj.getDelayDeleteCount() != 0:
                delayDeleteLeaks.append(obj)

        if len(delayDeleteLeaks):
            s = 'dumpAllSubShardObjects:'
            for obj in delayDeleteLeaks:
                s += '\n  could not delete %s (%s), delayDeletes=%s' % (safeRepr(obj), itype(obj), obj.getDelayDeleteNames())

            self.notify.error(s)
        if isNotLive:
            self.notify.info('dumpAllSubShardObjects: doIds left: %s' % list(self.doId2do.keys()))

    def _removeCurrentShardInterest(self, callback):
        if self.old_setzone_interest_handle is None:
            self.notify.warning('removeToontownShardInterest: no shard interest open')
            callback()
            return
        self.acceptOnce(ToontownClientRepository.ClearInterestDoneEvent, Functor(self._tcrRemoveUberZoneInterest, callback))
        self._removeEmulatedSetZone(ToontownClientRepository.ClearInterestDoneEvent)
        return

    def _tcrRemoveUberZoneInterest(self, callback):
        self.acceptOnce(ToontownClientRepository.ClearInterestDoneEvent, Functor(self._tcrRemoveShardInterestDone, callback))
        self.removeInterest(self.uberZoneInterest, ToontownClientRepository.ClearInterestDoneEvent)

    def _tcrRemoveShardInterestDone(self, callback):
        self.uberZoneInterest = None
        callback()
        return

    def _doIdIsOnCurrentShard(self, doId):
        if doId == base.localAvatar.defaultShard:
            return True
        do = self.getDo(doId)
        if do:
            if do.parentId == base.localAvatar.defaultShard:
                return True
        return False

    def _wantShardListComplete(self):
        print(self.activeDistrictMap)
        if self._shardsAreReady():
            self._noShardsRetries = 0
            self.acceptOnce(ToontownDistrictStats.EventName(), self.shardDetailStatsComplete)
            ToontownDistrictStats.refresh()
        else:
            self.loginFSM.request('noShards')

    def shardDetailStatsComplete(self):
        self.loginFSM.request('waitForAvatarList')

    def exitWaitForShardList(self):
        self.ignore(ToontownDistrictStats.EventName())
        OTPClientRepository.OTPClientRepository.exitWaitForShardList(self)

    def fillUpFriendsMap(self):
        if self.isFriendsMapComplete():
            return 1
        if not self.friendsMapPending and not self.friendsListError:
            self.notify.warning('Friends list stale; fetching new list.')
            self.sendGetFriendsListRequest()
        return 0

    def isFriend(self, doId):
        for friendId, flags in base.localAvatar.friendsList:
            if friendId == doId:
                self.identifyFriend(doId)
                return 1

        return 0

    def isAvatarFriend(self, doId):
        for friendId, flags in base.localAvatar.friendsList:
            if friendId == doId:
                self.identifyFriend(doId)
                return 1

        return 0

    def getFriendFlags(self, doId):
        for friendId, flags in base.localAvatar.friendsList:
            if friendId == doId:
                return flags

        return 0

    def isFriendOnline(self, doId):
        return doId in self.friendsOnline

    def addAvatarToFriendsList(self, avatar):
        self.friendsMap[avatar.doId] = avatar

    def identifyFriend(self, doId, source = None):
        if doId in self.friendsMap:
            teleportNotify.debug('friend %s in friendsMap' % doId)
            return self.friendsMap[doId]
        avatar = None
        if doId in self.doId2do:
            teleportNotify.debug('found friend %s in doId2do' % doId)
            avatar = self.doId2do[doId]
        elif self.cache.contains(doId):
            teleportNotify.debug('found friend %s in cache' % doId)
            avatar = self.cache.dict[doId]
        elif self.playerFriendsManager.getAvHandleFromId(doId):
            teleportNotify.debug('found friend %s in playerFriendsManager' % doId)
            avatar = base.cr.playerFriendsManager.getAvHandleFromId(doId)
        else:
            self.notify.warning("Don't know who friend %s is." % doId)
            return
        if not ((isinstance(avatar, DistributedToon.DistributedToon) and avatar.__class__ is DistributedToon.DistributedToon) or isinstance(avatar, DistributedPet.DistributedPet)):
            self.notify.warning('friendsNotify%s: invalid friend object %s' % (choice(source, '(%s)' % source, ''), doId))
            return
        if base.wantPets:
            if avatar.isPet():
                if avatar.bFake:
                    handle = PetHandle.PetHandle(avatar)
                else:
                    handle = avatar
            else:
                handle = FriendHandle.FriendHandle(doId, avatar.getName(), avatar.style, avatar.getPetId())
        else:
            handle = FriendHandle.FriendHandle(doId, avatar.getName(), avatar.style, '')
        teleportNotify.debug('adding %s to friendsMap' % doId)
        self.friendsMap[doId] = handle
        return handle

    def identifyPlayer(self, pId):
        return base.cr.playerFriendsManager.getFriendInfo(pId)

    def identifyAvatar(self, doId):
        if doId in self.doId2do:
            return self.doId2do[doId]
        else:
            return self.identifyFriend(doId)

    def isFriendsMapComplete(self):
        for friendId, flags in base.localAvatar.friendsList:
            if self.identifyFriend(friendId) == None:
                return 0

        if base.wantPets and base.localAvatar.hasPet():
            print(str(self.friendsMap))
            print(str(base.localAvatar.getPetId() in self.friendsMap))
            if (base.localAvatar.getPetId() in self.friendsMap) == None:
                return 0
        return 1

    def removeFriend(self, avatarId):
        base.localAvatar.sendUpdate('friendsNotify', [base.localAvatar.doId, 1], sendToId=avatarId)
        datagram = PyDatagram()
        datagram.addUint16(CLIENT_REMOVE_FRIEND)
        datagram.addUint32(avatarId)
        self.send(datagram)
        self.estateMgr.removeFriend(base.localAvatar.doId, avatarId)
        for pair in base.localAvatar.friendsList:
            friendId = pair[0]
            if friendId == avatarId:
                base.localAvatar.friendsList.remove(pair)
                return

    def clearFriendState(self):
        self.friendsMap = {}
        self.friendsOnline = {}
        self.friendsMapPending = 0
        self.friendsListError = 0

    def sendGetFriendsListRequest(self):
        if __astron__:
            print('sendGetFriendsListRequest TODO')
        else:
            self.friendsMapPending = 1
            self.friendsListError = 0
            datagram = PyDatagram()
            datagram.addUint16(CLIENT_GET_FRIEND_LIST)
            self.send(datagram)

    def cleanPetsFromFriendsMap(self):
        for objId, obj in list(self.friendsMap.items()):
            from toontown.pets import DistributedPet
            if isinstance(obj, DistributedPet.DistributedPet):
                print('Removing %s reference from the friendsMap' % obj.getName())
                del self.friendsMap[objId]

    def removePetFromFriendsMap(self):
        doId = base.localAvatar.getPetId()
        if doId and doId in self.friendsMap:
            del self.friendsMap[doId]

    def addPetToFriendsMap(self, callback = None):
        doId = base.localAvatar.getPetId()
        if not doId or doId in self.friendsMap:
            if callback:
                callback()
            return

        def petDetailsCallback(petAvatar):
            handle = PetHandle.PetHandle(petAvatar)
            self.friendsMap[doId] = handle
            petAvatar.disable()
            petAvatar.delete()
            if callback:
                callback()
            if self._proactiveLeakChecks:
                petAvatar.detectLeaks()

        PetDetail.PetDetail(doId, petDetailsCallback)

    def handleGetFriendsList(self, di):
        error = di.getUint8()
        if error:
            self.notify.warning('Got error return from friends list.')
            self.friendsListError = 1
        else:
            count = di.getUint16()
            for i in range(0, count):
                doId = di.getUint32()
                name = di.getString()
                dnaString = di.getBlob()
                dna = ToonDNA.ToonDNA()
                dna.makeFromNetString(dnaString)
                petId = di.getUint32()
                handle = FriendHandle.FriendHandle(doId, name, dna, petId)
                self.friendsMap[doId] = handle
                if doId in self.friendsOnline:
                    self.friendsOnline[doId] = handle
                if doId in self.friendPendingChatSettings:
                    self.notify.debug('calling setCommonAndWL %s' % str(self.friendPendingChatSettings[doId]))
                    handle.setCommonAndWhitelistChatFlags(*self.friendPendingChatSettings[doId])

            if base.wantPets and base.localAvatar.hasPet():

                def handleAddedPet():
                    self.friendsMapPending = 0
                    messenger.send('friendsMapComplete')

                self.addPetToFriendsMap(handleAddedPet)
                return
        self.friendsMapPending = 0
        messenger.send('friendsMapComplete')

    def handleGetFriendsListExtended(self, di):
        avatarHandleList = []
        error = di.getUint8()
        if error:
            self.notify.warning('Got error return from friends list extended.')
        else:
            count = di.getUint16()
            for i in range(0, count):
                abort = 0
                doId = di.getUint32()
                name = di.getString()
                if name == '':
                    abort = 1
                dnaString = di.getString()
                if dnaString == '':
                    abort = 1
                else:
                    dna = ToonDNA.ToonDNA()
                    dna.makeFromNetString(dnaString)
                petId = di.getUint32()
                if not abort:
                    handle = FriendHandle.FriendHandle(doId, name, dna, petId)
                    avatarHandleList.append(handle)

        if avatarHandleList:
            messenger.send('gotExtraFriendHandles', [avatarHandleList])

    def handleFriendOnline(self, di):
        doId = di.getUint32()
        commonChatFlags = 0
        whitelistChatFlags = 0
        if di.getRemainingSize() > 0:
            commonChatFlags = di.getUint8()
        if di.getRemainingSize() > 0:
            whitelistChatFlags = di.getUint8()
        self.notify.debug('Friend %d now online. common=%d whitelist=%d' % (doId, commonChatFlags, whitelistChatFlags))
        if doId not in self.friendsOnline:
            self.friendsOnline[doId] = self.identifyFriend(doId)
            messenger.send('friendOnline', [doId, commonChatFlags, whitelistChatFlags])
            if not self.friendsOnline[doId]:
                self.friendPendingChatSettings[doId] = (commonChatFlags, whitelistChatFlags)

    def handleFriendOffline(self, di):
        doId = di.getUint32()
        self.notify.debug('Friend %d now offline.' % doId)
        try:
            del self.friendsOnline[doId]
            messenger.send('friendOffline', [doId])
        except:
            pass

    def getFirstBattle(self):
        from toontown.battle import DistributedBattleBase
        for dobj in list(self.doId2do.values()):
            if isinstance(dobj, DistributedBattleBase.DistributedBattleBase):
                return dobj

    def forbidCheesyEffects(self, forbid):
        wasAllowed = self.__forbidCheesyEffects != 0
        if forbid:
            self.__forbidCheesyEffects += 1
        else:
            self.__forbidCheesyEffects -= 1
        isAllowed = self.__forbidCheesyEffects != 0
        if wasAllowed != isAllowed:
            for av in Avatar.Avatar.ActiveAvatars:
                if hasattr(av, 'reconsiderCheesyEffect'):
                    av.reconsiderCheesyEffect()

            base.localAvatar.reconsiderCheesyEffect()

    def areCheesyEffectsAllowed(self):
        return self.__forbidCheesyEffects == 0

    def getNextSetZoneDoneEvent(self):
        return '%s-%s' % (ToontownClientRepository.EmuSetZoneDoneEvent, self.setZonesEmulated + 1)

    def getLastSetZoneDoneEvent(self):
        return '%s-%s' % (ToontownClientRepository.EmuSetZoneDoneEvent, self.setZonesEmulated)

    def getQuietZoneLeftEvent(self):
        return 'leftQuietZone-%s' % (id(self),)

    def sendSetZoneMsg(self, zoneId, visibleZoneList = None):
        event = self.getNextSetZoneDoneEvent()
        self.setZonesEmulated += 1
        self._setZoneOpSerial += 1
        parentId = base.localAvatar.defaultShard
        self.sendSetLocation(base.localAvatar.doId, parentId, zoneId)
        localAvatar.setLocation(parentId, zoneId)
        interestZones = zoneId
        if visibleZoneList is not None:
            interestZones = visibleZoneList
        # Include a serial so timeout tasks can be uniquely named/cancelled.
        self._addInterestOpToQueue(ToontownClientRepository.SetInterest, [parentId, interestZones, 'OldSetZoneEmulator', self._setZoneOpSerial], event)
        return

    def resetInterestStateForConnectionLoss(self):
        OTPClientRepository.OTPClientRepository.resetInterestStateForConnectionLoss(self)
        self.old_setzone_interest_handle = None
        self.setZoneQueue.clear()
        return

    def _removeEmulatedSetZone(self, doneEvent):
        self._addInterestOpToQueue(ToontownClientRepository.ClearInterest, None, doneEvent)
        return

    def _addInterestOpToQueue(self, op, args, event):
        self.setZoneQueue.push([op, args, event])
        if len(self.setZoneQueue) == 1:
            self._sendNextSetZone()

    def _sendNextSetZone(self):
        op, args, event = self.setZoneQueue.top()
        if op == ToontownClientRepository.SetInterest:
            parentId, interestZones, name, serial = args
            if self.old_setzone_interest_handle == None:
                if interestZones == []:
                    # Empty zones at startup, don't do anything to save bandwidth, just send the event.
                    self._handleEmuSetZoneDone()
                    return
                self.old_setzone_interest_handle = self.addInterest(parentId, interestZones, name, ToontownClientRepository.SetZoneDoneEvent)
            else:
                if type(interestZones) == list:
                    interestZones.sort()
                if self.previousInterestZones == interestZones:
                    # Don't do anything to save bandwidth, just send the event.
                    self._handleEmuSetZoneDone()
                    return
                else:
                    self.alterInterest(self.old_setzone_interest_handle, parentId, interestZones, name, ToontownClientRepository.SetZoneDoneEvent)
            self.previousInterestZones = interestZones

            # Diagnostic escape hatch: if the server never responds to the
            # set-zone interest (DONE_INTEREST), forcibly advance instead of
            # hard-freezing in quiet zone. This is opt-in via PRC.
            if ConfigVariableBool('force-setzone-done', 0).value:
                try:
                    self.notify.warning('[ShardDbg] force-setzone-done=1; bypassing DONE_INTEREST wait for set-zone interest')
                except Exception:
                    pass
                try:
                    if ConfigVariableBool('shard-debug', 0).value:
                        self.notify.info(f'[ShardDbg] force-setzone-done calling _handleEmuSetZoneDone; event={event!r} serial={serial} parentId={parentId} zones={interestZones!r}')
                except Exception:
                    pass
                self._handleEmuSetZoneDone()
                try:
                    if ConfigVariableBool('shard-debug', 0).value:
                        self.notify.info('[ShardDbg] force-setzone-done returned from _handleEmuSetZoneDone')
                except Exception:
                    pass
                return

            # Safety net: if the server never sends DONE_INTEREST for this
            # zone interest, don't hard-freeze the client. We'll force the
            # set-zone completion event after a timeout.
            try:
                timeout = ConfigVariableDouble('setzone-interest-timeout', 15.0).value
            except Exception:
                timeout = 15.0
            taskName = f'setZoneInterestTimeout-{serial}'
            taskMgr.remove(taskName)
            taskMgr.doMethodLater(timeout, self._forceEmuSetZoneDone, taskName, extraArgs=[taskName])
            try:
                if ConfigVariableBool('shard-debug', 0).value:
                    self.notify.info(f'[ShardDbg] armed setZone timeout {timeout:.1f}s task={taskName}')
                    # If we hard-wedge, try to get Python stacks anyway.
                    # Note: output destination is controlled by OTPClientRepository's faulthandler setup.
                    faulthandler.dump_traceback_later(timeout + 5.0, repeat=False)
            except Exception:
                pass
        elif op == ToontownClientRepository.ClearInterest:
            self.removeInterest(self.old_setzone_interest_handle, ToontownClientRepository.SetZoneDoneEvent)
            self.old_setzone_interest_handle = None
            self.previousInterestZones = None
        else:
            self.notify.error('unknown setZone op: %s' % op)
        return

    def _forceEmuSetZoneDone(self, taskName):
        # If we already advanced, ignore.
        if self.setZoneQueue.isEmpty():
            return Task.done
        try:
            self.notify.warning(f'[ShardDbg] setZone interest timed out ({taskName}); forcing {ToontownClientRepository.SetZoneDoneEvent}')
        except Exception:
            pass
        self._handleEmuSetZoneDone()
        return Task.done

    def _handleEmuSetZoneDone(self):
        try:
            if ConfigVariableBool('shard-debug', 0).value:
                self.notify.info('[ShardDbg] _handleEmuSetZoneDone.enter')
        except Exception:
            pass
        # This can be invoked both by the normal DONE_INTEREST event path
        # and by our force-setzone-done/timeout safety nets. If the queue was
        # already advanced, ignore duplicate callbacks.
        if self.setZoneQueue.isEmpty():
            try:
                if ConfigVariableBool('shard-debug', 0).value:
                    self.notify.warning('[ShardDbg] _handleEmuSetZoneDone called but setZoneQueue is empty; ignoring')
            except Exception:
                pass
            return

        op, args, event = self.setZoneQueue.pop()
        queueIsEmpty = self.setZoneQueue.isEmpty()
        # Cancel any pending timeout for the setzone operation we just completed.
        try:
            if op == ToontownClientRepository.SetInterest and args and len(args) >= 4:
                taskMgr.remove(f'setZoneInterestTimeout-{args[3]}')
        except Exception:
            pass
        if event is not None:
            if not base.killInterestResponse:
                try:
                    if ConfigVariableBool('shard-debug', 0).value:
                        self.notify.info(f'[ShardDbg] _handleEmuSetZoneDone sending {event!r}')
                except Exception:
                    pass
                messenger.send(event)
                try:
                    if ConfigVariableBool('shard-debug', 0).value:
                        self.notify.info(f'[ShardDbg] _handleEmuSetZoneDone sent {event!r}')
                except Exception:
                    pass
            elif not hasattr(self, '_dontSendSetZoneDone'):
                import random
                if random.random() < 0.05:
                    self._dontSendSetZoneDone = True
                else:
                    messenger.send(event)
        if not queueIsEmpty:
            self._sendNextSetZone()
        try:
            if ConfigVariableBool('shard-debug', 0).value:
                self.notify.info('[ShardDbg] _handleEmuSetZoneDone.exit')
        except Exception:
            pass
        return

    def _isPlayerDclass(self, dclass):
        return dclass == self._playerAvDclass

    def _isValidPlayerLocation(self, parentId, zoneId):
        if not self.distributedDistrict:
            return False
        if parentId != self.distributedDistrict.doId:
            return False
        if parentId == self.distributedDistrict.doId and zoneId == OTPGlobals.UberZone:
            return False
        return True

    def sendQuietZoneRequest(self):
        if __astron__:
            self.sendSetZoneMsg(OTPGlobals.QuietZone, [])
        else:
            self.sendSetZoneMsg(OTPGlobals.QuietZone)

    if not __astron__:
        def handleQuietZoneGenerateWithRequired(self, di):
            parentId = di.getUint32()
            zoneId = di.getUint32()
            classId = di.getUint16()
            doId = di.getUint32()
            dclass = self.dclassesByNumber[classId]
            if dclass.getClassDef().neverDisable:
                dclass.startGenerate()
                distObj = self.generateWithRequiredFields(dclass, doId, di, parentId, zoneId)
                dclass.stopGenerate()

        def handleQuietZoneGenerateWithRequiredOther(self, di):
            parentId = di.getUint32()
            zoneId = di.getUint32()
            classId = di.getUint16()
            doId = di.getUint32()
            dclass = self.dclassesByNumber[classId]
            if dclass.getClassDef().neverDisable:
                dclass.startGenerate()
                distObj = self.generateWithRequiredOtherFields(dclass, doId, di, parentId, zoneId)
                dclass.stopGenerate()
    else:
        def handleQuietZoneGenerateWithRequired(self, di):
            doId = di.getUint32()
            parentId = di.getUint32()
            zoneId = di.getUint32()
            classId = di.getUint16()
            dclass = self.dclassesByNumber[classId]
            if dclass.getClassDef().neverDisable:
                dclass.startGenerate()
                distObj = self.generateWithRequiredFields(dclass, doId, di, parentId, zoneId)
                dclass.stopGenerate()

        def handleQuietZoneGenerateWithRequiredOther(self, di):
            doId = di.getUint32()
            parentId = di.getUint32()
            zoneId = di.getUint32()
            classId = di.getUint16()
            dclass = self.dclassesByNumber[classId]
            if dclass.getClassDef().neverDisable:
                dclass.startGenerate()
                distObj = self.generateWithRequiredOtherFields(dclass, doId, di, parentId, zoneId)
                dclass.stopGenerate()

        def handleGenerateWithRequiredOtherOwner(self, di):
            # OwnerViews are only used for LocalToon in Toontown.
            if self.loginFSM.getCurrentState().getName() == 'waitForSetAvatarResponse':
                doId = di.getUint32()
                parentId = di.getUint32()
                zoneId = di.getUint32()
                classId = di.getUint16()
                self.handleAvatarResponseMsg(doId, di)

    def handleQuietZoneUpdateField(self, di):
        di2 = DatagramIterator(di)
        doId = di2.getUint32()
        if doId in self.deferredDoIds:
            args, deferrable, dg0, updates = self.deferredDoIds[doId]
            dclass = args[2]
            if not dclass.getClassDef().neverDisable:
                return
        else:
            do = self.getDo(doId)
            if do:
                if not do.neverDisable:
                    return
        OTPClientRepository.OTPClientRepository.handleUpdateField(self, di)

    def handleDelete(self, di):
        doId = di.getUint32()
        self.deleteObject(doId)

    def deleteObject(self, doId, ownerView = False):
        if doId in self.doId2do:
            obj = self.doId2do[doId]
            del self.doId2do[doId]
            obj.deleteOrDelay()
            if obj.getDelayDeleteCount() <= 0:
                obj.detectLeaks()
        elif self.cache.contains(doId):
            self.cache.delete(doId)
        else:
            self.notify.warning('Asked to delete non-existent DistObj ' + str(doId))

    def _abandonShard(self):
        for doId, obj in list(self.doId2do.items()):
            if obj.parentId == localAvatar.defaultShard and obj is not localAvatar:
                self.deleteObject(doId)

    def askAvatarKnown(self, avId):
        if not hasattr(base, 'localAvatar'):
            return 0
        for friendPair in base.localAvatar.friendsList:
            if friendPair[0] == avId:
                return 1

        return 0

    def requestAvatarInfo(self, avId):
        if avId == 0:
            return
        datagram = PyDatagram()
        datagram.addUint16(CLIENT_GET_FRIEND_LIST_EXTENDED)
        datagram.addUint16(1)
        datagram.addUint32(avId)
        base.cr.send(datagram)

    def queueRequestAvatarInfo(self, avId):
        removeTask = 0
        if not hasattr(self, 'avatarInfoRequests'):
            self.avatarInfoRequests = []
        if self.avatarInfoRequests:
            taskMgr.remove('avatarRequestQueueTask')
        if avId not in self.avatarInfoRequests:
            self.avatarInfoRequests.append(avId)
        taskMgr.doMethodLater(0.1, self.sendAvatarInfoRequests, 'avatarRequestQueueTask')

    def sendAvatarInfoRequests(self, task = None):
        print('Sending request Queue for AV Handles')
        if not hasattr(self, 'avatarInfoRequests'):
            return
        if len(self.avatarInfoRequests) == 0:
            return
        datagram = PyDatagram()
        datagram.addUint16(CLIENT_GET_FRIEND_LIST_EXTENDED)
        datagram.addUint16(len(self.avatarInfoRequests))
        for avId in self.avatarInfoRequests:
            datagram.addUint32(avId)

        base.cr.send(datagram)
