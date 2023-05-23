from panda3d.core import *
from direct.gui.DirectGui import *
from panda3d.core import *
from toontown.toonbase import ToontownGlobals
from direct.showbase import DirectObject
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from direct.directnotify import DirectNotifyGlobal
from otp.avatar.Avatar import teleportNotify
from . import ToonAvatarDetailPanel
from toontown.toonbase import TTLocalizer
from toontown.hood import ZoneUtil
globalTeleport = None

def showTeleportPanel(avId, avName, avDisableName):
    # Noah Hensley
    print("TEST - showTeleportPanel has been initialized")
    
    global globalTeleport
    if globalTeleport != None:
        globalTeleport.cleanup()
        globalTeleport = None
    globalTeleport = ToonTeleportPanel(avId, avName, avDisableName)
    return


def hideTeleportPanel():
    # Noah Hensley
    print("TEST - hideTeleportPanel has been initialized")
    
    global globalTeleport
    if globalTeleport != None:
        globalTeleport.cleanup()
        globalTeleport = None
    return


def unloadTeleportPanel():
    # Noah Hensley
    print("TEST - unloadTeleportPanel has been initialized")
    
    global globalTeleport
    if globalTeleport != None:
        globalTeleport.cleanup()
        globalTeleport = None
    return


class ToonTeleportPanel(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToonTeleportPanel')

    def __init__(self, avId, avName, avDisableName):
        # Noah Hensley
        print("TEST - ToonTeleportPanel has been initialized")

        DirectFrame.__init__(self, pos=(0.3, 0.1, 0.65), image_color=ToontownGlobals.GlobalDialogColor, image_scale=(1.0, 1.0, 0.6), text='', text_wordwrap=13.5, text_scale=0.06, text_pos=(0.0, 0.18))
        messenger.send('releaseDirector')
        self['image'] = DGG.getDefaultDialogGeom()
        self.avId = avId
        self.avName = avName
        self.avDisableName = avDisableName
        self.fsm = ClassicFSM.ClassicFSM('ToonTeleportPanel', [
            State.State('off',
                self.enterOff,
                self.exitOff),
            State.State('begin',
                self.enterBegin,
                self.exitBegin),
            State.State('checkAvailability',
                self.enterCheckAvailability,
                self.exitCheckAvailability),
            State.State('notAvailable',
                self.enterNotAvailable,
                self.exitNotAvailable),
            State.State('ignored',
                self.enterIgnored,
                self.exitIgnored),
            State.State('notOnline',
                self.enterNotOnline,
                self.exitNotOnline),
            State.State('wentAway',
                self.enterWentAway,
                self.exitWentAway),
            State.State('self',
                self.enterSelf,
                self.exitSelf),
            State.State('unknownHood',
                self.enterUnknownHood,
                self.exitUnknownHood),
            State.State('unavailableHood',
                self.enterUnavailableHood,
                self.exitUnavailableHood),
            State.State('otherShard',
                self.enterOtherShard,
                self.exitOtherShard),
            State.State('teleport',
                self.enterTeleport,
                self.exitTeleport)],
            'off', 'off')
        from toontown.friends import FriendInviter
        FriendInviter.hideFriendInviter()
        ToonAvatarDetailPanel.hideAvatarDetail()
        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        self.bOk = DirectButton(self, image=(buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr')), relief=None, text=TTLocalizer.TeleportPanelOK, text_scale=0.05, text_pos=(0.0, -0.1), pos=(0.0, 0.0, -0.1), command=self.__handleOk)
        self.bOk.hide()
        self.bCancel = DirectButton(self, image=(buttons.find('**/CloseBtn_UP'), buttons.find('**/CloseBtn_DN'), buttons.find('**/CloseBtn_Rllvr')), relief=None, text=TTLocalizer.TeleportPanelCancel, text_scale=0.05, text_pos=(0.0, -0.1), pos=(0.0, 0.0, -0.1), command=self.__handleCancel)
        self.bCancel.hide()
        self.bYes = DirectButton(self, image=(buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr')), relief=None, text=TTLocalizer.TeleportPanelYes, text_scale=0.05, text_pos=(0.0, -0.1), pos=(-0.15, 0.0, -0.15), command=self.__handleYes)
        self.bYes.hide()
        self.bNo = DirectButton(self, image=(buttons.find('**/CloseBtn_UP'), buttons.find('**/CloseBtn_DN'), buttons.find('**/CloseBtn_Rllvr')), relief=None, text=TTLocalizer.TeleportPanelNo, text_scale=0.05, text_pos=(0.0, -0.1), pos=(0.15, 0.0, -0.15), command=self.__handleNo)
        self.bNo.hide()
        buttons.removeNode()
        self.accept(self.avDisableName, self.__handleDisableAvatar)
        self.show()
        self.fsm.enterInitialState()
        self.fsm.request('begin')
        return

    def cleanup(self):
        # Noah Hensley
        print("TEST - cleanup has been called")

        self.fsm.request('off')
        del self.fsm
        self.ignore(self.avDisableName)
        self.destroy()

    def enterOff(self):
        # Noah Hensley
        print("TEST - enterOff has been called")

        pass

    def exitOff(self):
        # Noah Hensley
        print("TEST - exitOff has been called")

        pass

    def enterBegin(self):
        # Noah Hensley
        print("TEST - enterBegin has been called")

        myId = base.localAvatar.doId
        hasManager = hasattr(base.cr, 'playerFriendsManager')
        if self.avId == myId:
            self.fsm.request('self')
        elif self.avId in base.cr.doId2do:
            self.fsm.request('checkAvailability')
        elif base.cr.isFriend(self.avId):
            if base.cr.isFriendOnline(self.avId):
                self.fsm.request('checkAvailability')
            else:
                self.fsm.request('notOnline')
        elif hasManager and base.cr.playerFriendsManager.getAvHandleFromId(self.avId):
            id = base.cr.playerFriendsManager.findPlayerIdFromAvId(self.avId)
            info = base.cr.playerFriendsManager.getFriendInfo(id)
            if info:
                if info.onlineYesNo:
                    self.fsm.request('checkAvailability')
                else:
                    self.fsm.request('notOnline')
            else:
                self.fsm.request('wentAway')
        else:
            self.fsm.request('wentAway')

    def exitBegin(self):
        # Noah Hensley
        print("TEST - exitBegin has been called")

        pass

    def enterCheckAvailability(self):
        # Noah Hensley
        print("TEST - enterCheckAvailability has been called")

        myId = base.localAvatar.getDoId()
        base.localAvatar.d_teleportQuery(myId, sendToId=self.avId)
        self['text'] = TTLocalizer.TeleportPanelCheckAvailability % self.avName
        self.accept('teleportResponse', self.__teleportResponse)
        self.bCancel.show()

    def exitCheckAvailability(self):
        # Noah Hensley
        print("TEST - exitCheckAvailability has been called")

        self.ignore('teleportResponse')
        self.bCancel.hide()

    def enterNotAvailable(self):
        # Noah Hensley
        print("TEST - enterNotAvailable has been called")

        self['text'] = TTLocalizer.TeleportPanelNotAvailable % self.avName
        self.bOk.show()

    def exitNotAvailable(self):
        # Noah Hensley
        print("TEST - exitNotAvailable has been called")

        self.bOk.hide()

    def enterIgnored(self):
        # Noah Hensley
        print("TEST - enterIgnored has been called")

        self['text'] = TTLocalizer.TeleportPanelNotAvailable % self.avName
        self.bOk.show()

    def exitIgnored(self):
        # Noah Hensley
        print("TEST - exitIgnored has been called")

        self.bOk.hide()

    def enterNotOnline(self):
        # Noah Hensley
        print("TEST - enterNotOnline has been called")

        self['text'] = TTLocalizer.TeleportPanelNotOnline % self.avName
        self.bOk.show()

    def exitNotOnline(self):
        # Noah Hensley
        print("TEST - exitNotOnline has been called")

        self.bOk.hide()

    def enterWentAway(self):
        # Noah Hensley
        print("TEST - enterWentAway has been called")

        self['text'] = TTLocalizer.TeleportPanelWentAway % self.avName
        self.bOk.show()

    def exitWentAway(self):
        # Noah Hensley
        print("TEST - exitWentAway has been called")

        self.bOk.hide()

    def enterUnknownHood(self, hoodId):
        # Noah Hensley
        print("TEST - exitUnknownHood has been called")

        self['text'] = TTLocalizer.TeleportPanelUnknownHood % base.cr.hoodMgr.getFullnameFromId(hoodId)
        self.bOk.show()

    def exitUnknownHood(self):
        # Noah Hensley
        print("TEST - exitUnknownHood has been called")

        self.bOk.hide()

    def enterUnavailableHood(self, hoodId):
        # Noah Hensley
        print("TEST - enterUnavailableHood has been called")

        self['text'] = TTLocalizer.TeleportPanelUnavailableHood % base.cr.hoodMgr.getFullnameFromId(hoodId)
        self.bOk.show()

    def exitUnavailableHood(self):
        # Noah Hensley
        print("TEST - exitUnavailableHood has been called")

        self.bOk.hide()

    def enterSelf(self):
        # Noah Hensley
        print("TEST - enterSelf has been called")

        self['text'] = TTLocalizer.TeleportPanelDenySelf
        self.bOk.show()

    def exitSelf(self):
        # Noah Hensley
        print("TEST - exitSelf has been called")

        self.bOk.hide()

    def enterOtherShard(self, shardId, hoodId, zoneId):
        # Noah Hensley
        print("TEST - enterOtherShard has been called")

        shardName = base.cr.getShardName(shardId)
        if shardName is None:
            self.fsm.request('notAvailable')
            return
        myShardName = base.cr.getShardName(base.localAvatar.defaultShard)
        pop = None
        for shard in base.cr.listActiveShards():
            if shard[0] == shardId:
                pop = shard[2]

        if pop and pop > localAvatar.shardPage.midPop:
            self.notify.warning('Entering full shard: issuing performance warning')
            self['text'] = TTLocalizer.TeleportPanelBusyShard % {'avName': self.avName}
        else:
            self['text'] = TTLocalizer.TeleportPanelOtherShard % {'avName': self.avName,
             'shardName': shardName,
             'myShardName': myShardName}
        self.bYes.show()
        self.bNo.show()
        self.shardId = shardId
        self.hoodId = hoodId
        self.zoneId = zoneId
        return

    def exitOtherShard(self):
        # Noah Hensley
        print("TEST - exitOtherShard has been called")

        self.bYes.hide()
        self.bNo.hide()

    def enterTeleport(self, shardId, hoodId, zoneId):
        # Noah Hensley
        print("TEST - enterTeleport has been called")

        teleportNotify.debug('enterTeleport%s' % ((shardId, hoodId, zoneId),))
        hoodsVisited = base.localAvatar.hoodsVisited
        canonicalHoodId = ZoneUtil.getCanonicalZoneId(hoodId)
        if hoodId == ToontownGlobals.MyEstate:
            teleportNotify.debug('enterTeleport: estate')
            if shardId == base.localAvatar.defaultShard:
                shardId = None
            place = base.cr.playGame.getPlace()
            place.requestTeleport(hoodId, zoneId, shardId, self.avId)
            unloadTeleportPanel()
        elif canonicalHoodId not in hoodsVisited + ToontownGlobals.HoodsAlwaysVisited:
            teleportNotify.debug('enterTeleport: unknownHood')
            self.fsm.request('unknownHood', [hoodId])
        elif canonicalHoodId not in base.cr.hoodMgr.getAvailableZones():
            print('hoodId %d not ready' % hoodId)
            self.fsm.request('unavailableHood', [hoodId])
        else:
            if shardId == base.localAvatar.defaultShard:
                shardId = None
            teleportNotify.debug('enterTeleport: requesting teleport')
            place = base.cr.playGame.getPlace()
            place.requestTeleport(hoodId, zoneId, shardId, self.avId)
            unloadTeleportPanel()
        return

    def exitTeleport(self):
        # Noah Hensley
        print("TEST - exitTeleport has been called")
        pass

    def __handleOk(self):
        # Noah Hensley
        print("TEST - __handleOk has been called")

        unloadTeleportPanel()

    def __handleCancel(self):
        # Noah Hensley
        print("TEST - __handleCancel has been called")

        unloadTeleportPanel()

    def __handleYes(self):
        # Noah Hensley
        print("TEST - __handleYes has been called")

        self.fsm.request('teleport', [self.shardId, self.hoodId, self.zoneId])

    def __handleNo(self):
        # Noah Hensley
        print("TEST - __handleNo has been called")

        unloadTeleportPanel()

    def __teleportResponse(self, avId, available, shardId, hoodId, zoneId):
        # Noah Hensley
        print("TEST - __handleResponse has been called")

        teleportNotify.debug('__teleportResponse%s' % ((avId,
          available,
          shardId,
          hoodId,
          zoneId),))
        if avId != self.avId:
            return
        if available == 0:
            teleportNotify.debug('__teleportResponse: not available')
            self.fsm.request('notAvailable')
        elif available == 2:
            teleportNotify.debug('__teleportResponse: ignored')
            self.fsm.request('ignored')
        elif shardId != base.localAvatar.defaultShard:
            teleportNotify.debug('__teleportResponse: otherShard')
            self.fsm.request('otherShard', [shardId, hoodId, zoneId])
        else:
            teleportNotify.debug('__teleportResponse: teleport')
            self.fsm.request('teleport', [shardId, hoodId, zoneId])

    def __handleDisableAvatar(self):
        # Noah Hensley
        print("TEST - __handleDisableAvatar has been called")

        self.fsm.request('wentAway')
