from pandac.PandaModules import *
from direct.gui.DirectGui import *
from direct.showbase import DirectObject
from . import Avatar
from direct.distributed import DistributedObject

class AvatarPanel(DirectObject.DirectObject):
    currentAvatarPanel = None

    def __init__(self, avatar, FriendsListPanel = None):
        if AvatarPanel.currentAvatarPanel:
            AvatarPanel.currentAvatarPanel.cleanup()
        AvatarPanel.currentAvatarPanel = self
        self.friendsListShown = False
        self.FriendsListPanel = FriendsListPanel
        if FriendsListPanel:
            self.friendsListShown = FriendsListPanel.isFriendsListShown()
            FriendsListPanel.hideFriendsList()
        if avatar:
            self.avatar = avatar
            self.avName = avatar.getName()
        else:
            self.avatar = None
            self.avName = 'Player'
        if hasattr(avatar, 'uniqueName'):
            self.avId = avatar.doId
            self.avDisableName = avatar.uniqueName('disable')
            self.avGenerateName = avatar.uniqueName('generate')
            self.avHpChangeName = avatar.uniqueName('hpChange')
            if self.avId in base.cr.doId2do:
                self.avatar = base.cr.doId2do[self.avId]
        else:
            self.avDisableName = None
            self.avGenerateName = None
            self.avHpChangeName = None
            self.avId = None
        if self.avDisableName:
            self.accept(self.avDisableName, self.__handleDisableAvatar)
        return

    def cleanup(self):
        if AvatarPanel.currentAvatarPanel != self:
            return
        if self.avDisableName:
            self.ignore(self.avDisableName)
        if self.avGenerateName:
            self.ignore(self.avGenerateName)
        if self.avHpChangeName:
            self.ignore(self.avHpChangeName)
        AvatarPanel.currentAvatarPanel = None
        return

    def __handleClose(self):
        self.cleanup()
        AvatarPanel.currentAvatarPanel = None
        if self.friendsListShown:
            self.FriendsListPanel.showFriendsList()
        return

    def __handleDisableAvatar(self):
        if AvatarPanel.currentAvatarPanel:
            AvatarPanel.currentAvatarPanel.handleDisableAvatar()
        else:
            self.handleDisableAvatar()

    def handleDisableAvatar(self):
        self.cleanup()
        AvatarPanel.currentAvatarPanel = None
        return

    def isHidden(self):
        return 1

    def getType(self):
        return None
