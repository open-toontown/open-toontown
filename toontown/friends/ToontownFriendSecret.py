from panda3d.core import *

from direct.directnotify import DirectNotifyGlobal
from direct.gui.DirectGui import *

from otp.friends import FriendSecret
from otp.friends.FriendSecret import (AccountSecret, AvatarSecret, BothSecrets, globalFriendSecret, hideFriendSecret,
                                      showFriendSecret, unloadFriendSecret)
from otp.otpbase import OTPLocalizer

from toontown.toonbase import TTLocalizer


def openFriendSecret(secretType):
    global globalFriendSecret
    if globalFriendSecret != None:
        globalFriendSecret.unload()
    globalFriendSecret = ToontownFriendSecret(secretType)
    globalFriendSecret.enter()
    return


FriendSecret.openFriendSecret = openFriendSecret

class ToontownFriendSecret(FriendSecret.FriendSecret):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownFriendSecret')

    def __init__(self, secretType):
        FriendSecret.FriendSecret.__init__(self, secretType)
        self.initialiseoptions(ToontownFriendSecret)

    def makeFriendTypeButtons(self):
        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        self.avatarButton = DirectButton(parent=self, image=(buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr')), relief=None, text=TTLocalizer.FriendInviterToon, text_scale=0.07, text_pos=(0.0, -0.1), pos=(-0.35, 0.0, -0.05), command=self._FriendSecret__handleAvatar)
        avatarText = DirectLabel(parent=self, relief=None, pos=Vec3(0.35, 0, -0.3), text=TTLocalizer.FriendInviterToonFriendInfo, text_fg=(0, 0, 0, 1), text_pos=(0, 0), text_scale=0.055, text_align=TextNode.ACenter)
        avatarText.reparentTo(self.avatarButton.stateNodePath[2])
        self.avatarButton.hide()
        self.accountButton = DirectButton(parent=self, image=(buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr')), relief=None, text=TTLocalizer.FriendInviterPlayer, text_scale=0.07, text_pos=(0.0, -0.1), pos=(0.35, 0.0, -0.05), command=self._FriendSecret__handleAccount)
        accountText = DirectLabel(parent=self, relief=None, pos=Vec3(-0.35, 0, -0.3), text=TTLocalizer.FriendInviterPlayerFriendInfo, text_fg=(0, 0, 0, 1), text_pos=(0, 0), text_scale=0.055, text_align=TextNode.ACenter)
        accountText.reparentTo(self.accountButton.stateNodePath[2])
        self.accountButton.hide()
        buttons.removeNode()
        return

    def __determineSecret(self):
        if self.secretType == BothSecrets:
            self._FriendSecret__cleanupFirstPage()
            self.ok1.hide()
            self.changeOptions.hide()
            self.nextText['text'] = TTLocalizer.FriendInviterBegin
            self.nextText.setPos(0, 0, 0.3)
            self.nextText.show()
            self.avatarButton.show()
            self.accountButton.show()
            self.cancel.show()
        else:
            self._FriendSecret__getSecret()
