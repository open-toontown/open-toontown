from pandac.PandaModules import *
from toontown.toonbase.ToontownGlobals import *
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.showbase import DirectObject
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from direct.directnotify import DirectNotifyGlobal
from . import DistributedToon
from toontown.friends import FriendInviter
from . import ToonTeleportPanel
from toontown.toonbase import TTLocalizer
from toontown.hood import ZoneUtil
from toontown.toonbase.ToontownBattleGlobals import Tracks, Levels
globalAvatarDetail = None

def showAvatarDetail(avId, avName, playerId = None):
    global globalAvatarDetail
    if globalAvatarDetail != None:
        globalAvatarDetail.cleanup()
        globalAvatarDetail = None
    playerId = base.cr.playerFriendsManager.findPlayerIdFromAvId(avId)
    globalAvatarDetail = ToonAvatarDetailPanel(avId, avName, playerId)
    return


def hideAvatarDetail():
    global globalAvatarDetail
    if globalAvatarDetail != None:
        globalAvatarDetail.cleanup()
        globalAvatarDetail = None
    return


def unloadAvatarDetail():
    global globalAvatarDetail
    if globalAvatarDetail != None:
        globalAvatarDetail.cleanup()
        globalAvatarDetail = None
    return


class ToonAvatarDetailPanel(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToonAvatarDetailPanel')

    def __init__(self, avId, avName, playerId = None, parent = aspect2dp, **kw):
        print('ToonAvatarDetailPanel %s' % playerId)
        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        gui = loader.loadModel('phase_3.5/models/gui/avatar_panel_gui')
        detailPanel = gui.find('**/avatarInfoPanel')
        self.playerId = playerId
        textScale = 0.095
        textWrap = 16.4
        self.playerInfo = None
        if self.playerId:
            self.playerInfo = base.cr.playerFriendsManager.playerId2Info.get(playerId)
        optiondefs = (('pos', (0.525, 0.0, 0.525), None),
         ('scale', 0.5, None),
         ('relief', None, None),
         ('image', detailPanel, None),
         ('image_color', GlobalDialogColor, None),
         ('text', '', None),
         ('text_wordwrap', textWrap, None),
         ('text_scale', textScale, None),
         ('text_pos', (-0.125, 0.775), None))
        self.defineoptions(kw, optiondefs)
        DirectFrame.__init__(self, parent)
        self.dataText = DirectLabel(self, text='', text_scale=0.09, text_align=TextNode.ALeft, text_wordwrap=15, relief=None, pos=(-0.85, 0.0, 0.645))
        self.avId = avId
        self.avName = avName
        self.avatar = None
        self.createdAvatar = None
        self.fsm = ClassicFSM.ClassicFSM('ToonAvatarDetailPanel', [State.State('off', self.enterOff, self.exitOff, ['begin']),
         State.State('begin', self.enterBegin, self.exitBegin, ['query', 'data', 'off']),
         State.State('query', self.enterQuery, self.exitQuery, ['data', 'invalid', 'off']),
         State.State('data', self.enterData, self.exitData, ['off']),
         State.State('invalid', self.enterInvalid, self.exitInvalid, ['off'])], 'off', 'off')
        ToonTeleportPanel.hideTeleportPanel()
        FriendInviter.hideFriendInviter()
        self.bCancel = DirectButton(self, image=(buttons.find('**/CloseBtn_UP'), buttons.find('**/CloseBtn_DN'), buttons.find('**/CloseBtn_Rllvr')), image_scale=1.1, relief=None, text=TTLocalizer.AvatarDetailPanelCancel, text_scale=TTLocalizer.TADPbCancel, text_pos=(0.12, -0.01), pos=TTLocalizer.TADPbCancelPos, scale=2.0, command=self.__handleCancel)
        self.bCancel.hide()
        self.initialiseoptions(ToonAvatarDetailPanel)
        self.fsm.enterInitialState()
        self.fsm.request('begin')
        buttons.removeNode()
        gui.removeNode()
        return

    def cleanup(self):
        if self.fsm:
            self.fsm.request('off')
            self.fsm = None
            base.cr.cancelAvatarDetailsRequest(self.avatar)
        if self.createdAvatar:
            self.avatar.delete()
            self.createdAvatar = None
        self.destroy()
        return

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def enterBegin(self):
        myId = base.localAvatar.doId
        self['text'] = self.avName
        if self.avId == myId:
            self.avatar = base.localAvatar
            self.createdAvatar = 0
            self.fsm.request('data')
        else:
            self.fsm.request('query')

    def exitBegin(self):
        pass

    def enterQuery(self):
        self.dataText['text'] = TTLocalizer.AvatarDetailPanelLookup % self.avName
        self.bCancel.show()
        self.avatar = base.cr.doId2do.get(self.avId)
        if self.avatar != None and not self.avatar.ghostMode:
            self.createdAvatar = 0
        else:
            self.avatar = DistributedToon.DistributedToon(base.cr)
            self.createdAvatar = 1
            self.avatar.doId = self.avId
            self.avatar.forceAllowDelayDelete()
        base.cr.getAvatarDetails(self.avatar, self.__handleAvatarDetails, 'DistributedToon')
        return

    def exitQuery(self):
        self.bCancel.hide()

    def enterData(self):
        self.bCancel['text'] = TTLocalizer.AvatarDetailPanelClose
        self.bCancel.show()
        self.__showData()

    def exitData(self):
        self.bCancel.hide()

    def enterInvalid(self):
        self.dataText['text'] = TTLocalizer.AvatarDetailPanelFailedLookup % self.avName

    def exitInvalid(self):
        self.bCancel.hide()

    def __handleCancel(self):
        unloadAvatarDetail()

    def __handleAvatarDetails(self, gotData, avatar, dclass):
        if not self.fsm or avatar != self.avatar:
            self.notify.warning('Ignoring unexpected request for avatar %s' % avatar.doId)
            return
        if gotData:
            self.fsm.request('data')
        else:
            self.fsm.request('invalid')

    def __showData(self):
        av = self.avatar
        online = 1
        if base.cr.isFriend(self.avId):
            online = base.cr.isFriendOnline(self.avId)
        if online:
            shardName = base.cr.getShardName(av.defaultShard)
            hoodName = base.cr.hoodMgr.getFullnameFromId(av.lastHood)
            if ZoneUtil.isWelcomeValley(av.lastHood):
                shardName = '%s (%s)' % (TTLocalizer.WelcomeValley[-1], shardName)
            if self.playerInfo:
                guiButton = loader.loadModel('phase_3/models/gui/quit_button')
                self.gotoAvatarButton = DirectButton(parent=self, relief=None, image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')), image_scale=1.1, text=TTLocalizer.AvatarShowPlayer, text_scale=0.07, text_pos=(0.0, -0.02), textMayChange=0, pos=(0.44, 0, 0.41), command=self.__showAvatar)
                text = TTLocalizer.AvatarDetailPanelOnlinePlayer % {'district': shardName,
                 'location': hoodName,
                 'player': self.playerInfo.playerName}
            else:
                text = TTLocalizer.AvatarDetailPanelOnline % {'district': shardName,
                 'location': hoodName}
        else:
            text = TTLocalizer.AvatarDetailPanelOffline
        self.dataText['text'] = text
        self.__updateTrackInfo()
        self.__updateTrophyInfo()
        self.__updateLaffInfo()
        return

    def __showAvatar(self):
        messenger.send('wakeup')
        hasManager = hasattr(base.cr, 'playerFriendsManager')
        handle = base.cr.identifyFriend(self.avId)
        if not handle and hasManager:
            handle = base.cr.playerFriendsManager.getAvHandleFromId(self.avId)
        if handle != None:
            self.notify.info("Clicked on name in friend's list. doId = %s" % handle.doId)
            messenger.send('clickedNametagPlayer', [handle, self.playerId, 1])
        return

    def __updateLaffInfo(self):
        avatar = self.avatar
        messenger.send('updateLaffMeter', [avatar, avatar.hp, avatar.maxHp])

    def __updateTrackInfo(self):
        xOffset = -0.501814
        xSpacing = 0.1835
        yOffset = 0.1
        ySpacing = -0.115
        inventory = self.avatar.inventory
        inventoryModels = loader.loadModel('phase_3.5/models/gui/inventory_gui')
        buttonModel = inventoryModels.find('**/InventoryButtonUp')
        for track in range(0, len(Tracks)):
            DirectLabel(parent=self, relief=None, text=TextEncoder.upper(TTLocalizer.BattleGlobalTracks[track]), text_scale=TTLocalizer.TADPtrackLabel, text_align=TextNode.ALeft, pos=(-0.9, 0, TTLocalizer.TADtrackLabelPosZ + track * ySpacing))
            if self.avatar.hasTrackAccess(track):
                curExp, nextExp = inventory.getCurAndNextExpValues(track)
                for item in range(0, len(Levels[track])):
                    level = Levels[track][item]
                    if curExp >= level:
                        numItems = inventory.numItem(track, item)
                        if numItems == 0:
                            image_color = Vec4(0.5, 0.5, 0.5, 1)
                            geom_color = Vec4(0.2, 0.2, 0.2, 0.5)
                        else:
                            image_color = Vec4(0, 0.6, 1, 1)
                            geom_color = None
                        DirectLabel(parent=self, image=buttonModel, image_scale=(0.92, 1, 1), image_color=image_color, geom=inventory.invModels[track][item], geom_color=geom_color, geom_scale=0.6, relief=None, pos=(xOffset + item * xSpacing, 0, yOffset + track * ySpacing))
                    else:
                        break

        return

    def __updateTrophyInfo(self):
        if self.createdAvatar:
            return
        if self.avatar.trophyScore >= TrophyStarLevels[2]:
            color = TrophyStarColors[2]
        elif self.avatar.trophyScore >= TrophyStarLevels[1]:
            color = TrophyStarColors[1]
        elif self.avatar.trophyScore >= TrophyStarLevels[0]:
            color = TrophyStarColors[0]
        else:
            color = None
        if color:
            gui = loader.loadModel('phase_3.5/models/gui/avatar_panel_gui')
            star = gui.find('**/avatarStar')
            self.star = DirectLabel(parent=self, image=star, image_color=color, pos=(0.610165, 0, -0.760678), scale=0.9, relief=None)
            gui.removeNode()
        return
