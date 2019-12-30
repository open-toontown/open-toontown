from pandac.PandaModules import *
from libotp import *
from . import FriendsListPanel
from . import FriendInviter
from . import FriendInvitee
from . import FriendNotifier
from direct.directnotify import DirectNotifyGlobal
from toontown.toon import ToonTeleportPanel
from toontown.friends import ToontownFriendSecret
from toontown.pets import PetAvatarPanel
from toontown.toon import ToonAvatarPanel
from toontown.toon import PlayerInfoPanel
from toontown.suit import SuitAvatarPanel
from toontown.toon import ToonDNA
from toontown.toon import ToonAvatarDetailPanel
from toontown.toon import PlayerDetailPanel
from toontown.toonbase import ToontownGlobals
from toontown.toon import Toon
from . import FriendHandle
from otp.otpbase import OTPGlobals

class FriendsListManager:
    notify = DirectNotifyGlobal.directNotify.newCategory('FriendsListManager')

    def __init__(self):
        self.avatarPanel = None
        self._preserveFriendsList = False
        self._entered = False
        self.friendsRequestQueue = []
        return

    def load(self):
        base.cr.friendManager.setGameSpecificFunction(self.processQueuedRequests)
        self.accept(OTPGlobals.AvatarNewFriendAddEvent, self.__friendAdded)

    def unload(self):
        base.cr.friendManager.setGameSpecificFunction(None)
        self.exitFLM()
        if self.avatarPanel:
            del self.avatarPanel
        FriendInviter.unloadFriendInviter()
        ToonAvatarDetailPanel.unloadAvatarDetail()
        ToonTeleportPanel.unloadTeleportPanel()
        return

    def enterFLM(self):
        self.notify.debug('FriendsListManager: enterFLM()')
        if self._preserveFriendsList:
            self._preserveFriendsList = 0
            return
        self._entered = True
        self.accept('openFriendsList', self.__openFriendsList)
        self.accept('clickedNametag', self.__handleClickedNametag)
        self.accept('clickedNametagPlayer', self.__handleClickedNametagPlayer)
        base.localAvatar.setFriendsListButtonActive(1)
        NametagGlobals.setMasterNametagsActive(1)
        self.accept('gotoAvatar', self.__handleGotoAvatar)
        self.accept('friendAvatar', self.__handleFriendAvatar)
        self.accept('avatarDetails', self.__handleAvatarDetails)
        self.accept('playerDetails', self.__handlePlayerDetails)
        self.accept('friendInvitation', self.__handleFriendInvitation)
        self.accept(OTPGlobals.PlayerFriendInvitationEvent, self.__handlePlayerFriendInvitation)
        if base.cr.friendManager:
            base.cr.friendManager.setAvailable(1)

    def exitFLM(self):
        self.notify.debug('FriendsListManager: exitFLM()')
        if self._preserveFriendsList:
            return
        if not self._entered:
            return
        self._entered = False
        self.ignore('openFriendsList')
        self.ignore('clickedNametag')
        self.ignore('clickedNametagPlayer')
        base.localAvatar.setFriendsListButtonActive(0)
        NametagGlobals.setMasterNametagsActive(0)
        if self.avatarPanel:
            self.avatarPanel.cleanup()
            self.avatarPanel = None
        self.ignore('gotoAvatar')
        self.ignore('friendAvatar')
        self.ignore('avatarDetails')
        self.ignore('playerDetails')
        FriendsListPanel.hideFriendsList()
        ToontownFriendSecret.hideFriendSecret()
        if base.cr.friendManager:
            base.cr.friendManager.setAvailable(0)
        self.ignore('friendInvitation')
        FriendInviter.hideFriendInviter()
        ToonAvatarDetailPanel.hideAvatarDetail()
        ToonTeleportPanel.hideTeleportPanel()
        return

    def __openFriendsList(self):
        FriendsListPanel.showFriendsList()

    def __handleClickedNametag(self, avatar, playerId = None):
        self.notify.debug('__handleClickedNametag. doId = %s' % avatar.doId)
        if avatar.isPet():
            self.avatarPanel = PetAvatarPanel.PetAvatarPanel(avatar)
        elif isinstance(avatar, Toon.Toon) or isinstance(avatar, FriendHandle.FriendHandle):
            if hasattr(self, 'avatarPanel'):
                if self.avatarPanel:
                    if not hasattr(self.avatarPanel, 'getAvId') or self.avatarPanel.getAvId() == avatar.doId:
                        if not self.avatarPanel.isHidden():
                            if self.avatarPanel.getType() == 'toon':
                                return
            self.avatarPanel = ToonAvatarPanel.ToonAvatarPanel(avatar, playerId)
        else:
            self.avatarPanel = SuitAvatarPanel.SuitAvatarPanel(avatar)

    def __handleClickedNametagPlayer(self, avatar, playerId, showType = 1):
        self.notify.debug('__handleClickedNametagPlayer PlayerId%s' % playerId)
        if showType == 1:
            if hasattr(self, 'avatarPanel'):
                if self.avatarPanel:
                    if not hasattr(self.avatarPanel, 'getPlayerId') or self.avatarPanel.getPlayerId() == playerId:
                        if not self.avatarPanel.isHidden():
                            if self.avatarPanel.getType() == 'player':
                                return
            self.avatarPanel = PlayerInfoPanel.PlayerInfoPanel(playerId)
        elif isinstance(avatar, Toon.Toon) or isinstance(avatar, FriendHandle.FriendHandle):
            if hasattr(self, 'avatarPanel'):
                if self.avatarPanel:
                    if not hasattr(self.avatarPanel, 'getAvId') or self.avatarPanel.getAvId() == avatar.doId:
                        if not self.avatarPanel.isHidden():
                            if self.avatarPanel.getType() == 'toon':
                                return
            self.avatarPanel = ToonAvatarPanel.ToonAvatarPanel(avatar, playerId)

    def __handleGotoAvatar(self, avId, avName, avDisableName):
        ToonTeleportPanel.showTeleportPanel(avId, avName, avDisableName)

    def __handleFriendAvatar(self, avId, avName, avDisableName):
        FriendInviter.showFriendInviter(avId, avName, avDisableName)

    def __handleFriendInvitation(self, avId, avName, inviterDna, context):
        dna = ToonDNA.ToonDNA()
        dna.makeFromNetString(inviterDna)
        if not base.cr.avatarFriendsManager.checkIgnored(avId):
            FriendInvitee.FriendInvitee(avId, avName, dna, context)

    def __handlePlayerFriendInvitation(self, avId, avName, inviterDna = None, context = None):
        self.notify.debug('incoming switchboard friend event')
        self.friendsRequestQueue.append((avId,
         avName,
         inviterDna,
         context))
        if base.cr.friendManager.getAvailable():
            self.processQueuedRequests()

    def processQueuedRequests(self):
        if len(self.friendsRequestQueue):
            request = self.friendsRequestQueue.pop(0)
            self.__processFriendRequest(request[0], request[1], request[2], request[3])

    def __processFriendRequest(self, avId, avName, inviterDna = None, context = None):
        self.notify.debug('__handleAvatarFriendInvitation')
        askerToon = base.cr.doId2do.get(avId)
        if askerToon:
            self.notify.debug('got toon')
            dna = askerToon.getStyle()
            if not base.cr.avatarFriendsManager.checkIgnored(avId):
                FriendInvitee.FriendInvitee(avId, avName, dna, context)
        else:
            self.notify.debug('no toon')

    def __handleAvatarDetails(self, avId, avName, playerId = None):
        ToonAvatarDetailPanel.showAvatarDetail(avId, avName, playerId)

    def __handlePlayerDetails(self, avId, avName, playerId = None):
        PlayerDetailPanel.showPlayerDetail(avId, avName, playerId)

    def preserveFriendsList(self):
        self.notify.debug('Preserving Friends List')
        self._preserveFriendsList = True

    def __friendAdded(self, avId):
        if FriendInviter.globalFriendInviter != None:
            messenger.send('FriendsListManagerAddEvent', [avId])
        else:
            friendToon = base.cr.doId2do.get(avId)
            if friendToon:
                print('got toon')
                dna = friendToon.getStyle()
                FriendNotifier.FriendNotifier(avId, friendToon.getName(), dna, None)
        return
