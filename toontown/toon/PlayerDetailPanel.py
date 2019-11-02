from pandac.PandaModules import *
from toontown.toonbase.ToontownGlobals import *
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.showbase import DirectObject
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from direct.directnotify import DirectNotifyGlobal
import DistributedToon
from toontown.friends import FriendInviter
import ToonTeleportPanel
from toontown.toonbase import TTLocalizer
from toontown.hood import ZoneUtil
from toontown.toonbase.ToontownBattleGlobals import Tracks, Levels
globalAvatarDetail = None

def showPlayerDetail(avId, avName, playerId = None):
    global globalAvatarDetail
    if globalAvatarDetail != None:
        globalAvatarDetail.cleanup()
        globalAvatarDetail = None
    globalAvatarDetail = PlayerDetailPanel(avId, avName, playerId)
    return


def hidePlayerDetail():
    global globalAvatarDetail
    if globalAvatarDetail != None:
        globalAvatarDetail.cleanup()
        globalAvatarDetail = None
    return


def unloadPlayerDetail():
    global globalAvatarDetail
    if globalAvatarDetail != None:
        globalAvatarDetail.cleanup()
        globalAvatarDetail = None
    return


class PlayerDetailPanel(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToonAvatarDetailPanel')

    def __init__(self, avId, avName, playerId = None, parent = aspect2dp, **kw):
        self.playerId = playerId
        self.isPlayer = 0
        self.playerInfo = None
        if playerId:
            self.isPlayer = 1
            if base.cr.playerFriendsManager.playerId2Info.has_key(playerId):
                self.playerInfo = base.cr.playerFriendsManager.playerId2Info[playerId]
                if not self.playerInfo.onlineYesNo:
                    avId = None
            else:
                avId = None
        self.avId = avId
        self.avName = avName
        self.avatar = None
        self.createdAvatar = None
        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        gui = loader.loadModel('phase_3.5/models/gui/avatar_panel_gui')
        detailPanel = gui.find('**/avatarInfoPanel')
        textScale = 0.132
        textWrap = 10.4
        if self.playerId:
            textScale = 0.1
            textWrap = 18.0
        optiondefs = (('pos', (0.525, 0.0, 0.525), None),
         ('scale', 0.5, None),
         ('relief', None, None),
         ('image', detailPanel, None),
         ('image_color', GlobalDialogColor, None),
         ('text', '', None),
         ('text_wordwrap', textWrap, None),
         ('text_scale', textScale, None),
         ('text_pos', (-0.125, 0.75), None))
        self.defineoptions(kw, optiondefs)
        DirectFrame.__init__(self, parent)
        self.dataText = DirectLabel(self, text='', text_scale=0.085, text_align=TextNode.ALeft, text_wordwrap=15, relief=None, pos=(-0.85, 0.0, 0.725))
        if self.avId:
            self.avText = DirectLabel(self, text=TTLocalizer.PlayerToonName % {'toonname': self.avName}, text_scale=0.09, text_align=TextNode.ALeft, text_wordwrap=15, relief=None, pos=(-0.85, 0.0, 0.56))
            guiButton = loader.loadModel('phase_3/models/gui/quit_button')
            self.gotoToonButton = DirectButton(parent=self, relief=None, image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')), image_scale=1.15, text=TTLocalizer.PlayerShowToon, text_scale=0.08, text_pos=(0.0, -0.02), textMayChange=0, pos=(0.43, 0, 0.415), command=self.__showToon)
        ToonTeleportPanel.hideTeleportPanel()
        FriendInviter.hideFriendInviter()
        self.bCancel = DirectButton(self, image=(buttons.find('**/CloseBtn_UP'), buttons.find('**/CloseBtn_DN'), buttons.find('**/CloseBtn_Rllvr')), relief=None, text=TTLocalizer.AvatarDetailPanelCancel, text_scale=0.05, text_pos=(0.12, -0.01), pos=(-0.865, 0.0, -0.765), scale=2.0, command=self.__handleCancel)
        self.bCancel.show()
        self.initialiseoptions(PlayerDetailPanel)
        self.__showData()
        buttons.removeNode()
        gui.removeNode()
        return

    def cleanup(self):
        if self.createdAvatar:
            self.avatar.delete()
            self.createdAvatar = None
        self.destroy()
        return

    def __handleCancel(self):
        unloadPlayerDetail()

    def __showData(self):
        if self.isPlayer and self.playerInfo:
            if self.playerInfo.onlineYesNo:
                someworld = self.playerInfo.location
            else:
                someworld = TTLocalizer.OfflineLocation
            text = TTLocalizer.AvatarDetailPanelPlayer % {'player': self.playerInfo.playerName,
             'world': someworld}
        else:
            text = TTLocalizer.AvatarDetailPanelOffline
        self.dataText['text'] = text

    def __showToon(self):
        messenger.send('wakeup')
        hasManager = hasattr(base.cr, 'playerFriendsManager')
        handle = base.cr.identifyFriend(self.avId)
        if not handle and hasManager:
            handle = base.cr.playerFriendsManager.getAvHandleFromId(self.avId)
        if handle != None:
            self.notify.info("Clicked on name in friend's list. doId = %s" % handle.doId)
            messenger.send('clickedNametagPlayer', [handle, self.playerId, 0])
        return
