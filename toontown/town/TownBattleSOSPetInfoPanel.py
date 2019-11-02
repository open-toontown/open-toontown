from pandac.PandaModules import *
from direct.fsm import StateData
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from toontown.toonbase import TTLocalizer
from toontown.pets import Pet, PetTricks, PetDetailPanel
from toontown.speedchat import TTSCPetTrickMenu
from otp.speedchat import SpeedChatGlobals, SCSettings
from otp.otpbase import OTPLocalizer

class TownBattleSOSPetInfoPanel(StateData.StateData):

    def __init__(self, doneEvent):
        StateData.StateData.__init__(self, doneEvent)

    def load(self):
        gui = loader.loadModel('phase_3.5/models/gui/PetControlPannel')
        guiScale = 0.116
        guiPos = (0, 0, 0)
        self.frame = DirectFrame(image=gui, scale=guiScale, pos=guiPos, relief=None)
        self.frame.hide()
        disabledImageColor = Vec4(0.6, 0.6, 0.6, 1)
        text0Color = Vec4(1, 1, 1, 1)
        text1Color = Vec4(0.5, 1, 0.5, 1)
        text2Color = Vec4(1, 1, 0.5, 1)
        text3Color = Vec4(0.6, 0.6, 0.6, 1)
        self.closeButton = DirectButton(parent=self.frame, image=(gui.find('**/CancelButtonUp'), gui.find('**/CancelButtonDown'), gui.find('**/CancelButtonRollover')), relief=None, command=self.__handleClose)
        self.feedButton = DirectButton(parent=self.frame, image=(gui.find('**/ButtonFeedUp'),
         gui.find('**/ButtonFeedDown'),
         gui.find('**/ButtonFeedRollover'),
         gui.find('**/ButtonFeedUp')), geom=gui.find('**/PetControlFeedIcon'), image3_color=disabledImageColor, relief=None, text=TTLocalizer.PetPanelFeed, text_scale=0.5, text0_fg=text0Color, text1_fg=text1Color, text2_fg=text2Color, text3_fg=text3Color, text_pos=(-0.5, 2.8), text_align=TextNode.ALeft)
        self.feedButton['state'] = DGG.DISABLED
        self.callButton = DirectButton(parent=self.frame, image=(gui.find('**/ButtonGoToUp'),
         gui.find('**/ButtonGoToDown'),
         gui.find('**/ButtonGoToRollover'),
         gui.find('**/ButtonGoToUp')), geom=gui.find('**/PetControlGoToIcon'), image3_color=disabledImageColor, relief=None, text=TTLocalizer.PetPanelCall, text0_fg=text0Color, text1_fg=text1Color, text2_fg=text2Color, text3_fg=text3Color, text_scale=0.5, text_pos=(-0.5, 1.3), text_align=TextNode.ALeft)
        self.callButton['state'] = DGG.DISABLED
        self.scratchButton = DirectButton(parent=self.frame, image=(gui.find('**/ButtonScratchUp'),
         gui.find('**/ButtonScratchDown'),
         gui.find('**/ButtonScratchRollover'),
         gui.find('**/ButtonScratchUp')), geom=gui.find('**/PetControlScratchIcon'), image3_color=disabledImageColor, relief=None, text=TTLocalizer.PetPanelScratch, text0_fg=text0Color, text1_fg=text1Color, text2_fg=text2Color, text3_fg=text3Color, text_scale=0.5, text_pos=(-0.5, 2.05), text_align=TextNode.ALeft)
        self.scratchButton['state'] = DGG.DISABLED
        self.callOwnerButton = DirectButton(parent=self.frame, image=(gui.find('**/PetControlToonButtonUp'), gui.find('**/PetControlToonButtonDown'), gui.find('**/PetControlToonButtonRollover')), geom=gui.find('**/PetControlToonIcon'), geom3_color=disabledImageColor, relief=None, image3_color=disabledImageColor, text=('',
         TTLocalizer.PetPanelOwner,
         TTLocalizer.PetPanelOwner,
         ''), text_fg=text2Color, text_shadow=(0, 0, 0, 1), text_scale=0.35, text_pos=(0.3, 1.1), text_align=TextNode.ACenter, command=self.__handleDetail)
        self.callOwnerButton['state'] = DGG.DISABLED
        self.detailButton = DirectButton(parent=self.frame, image=(gui.find('**/PetControlToonButtonUp1'), gui.find('**/PetControlToonButtonDown1'), gui.find('**/PetControlToonButtonRollover1')), geom=gui.find('**/PetBattleIcon'), geom3_color=disabledImageColor, relief=None, pos=(0, 0, 0), image3_color=disabledImageColor, text=('',
         TTLocalizer.PetPanelDetail,
         TTLocalizer.PetPanelDetail,
         ''), text_fg=text2Color, text_shadow=(0, 0, 0, 1), text_scale=0.35, text_pos=(0.3, 1.1), text_align=TextNode.ACenter, command=self.__handleDetail)
        self.detailButton['state'] = DGG.NORMAL
        gui.removeNode()
        self.nameLabel = None
        self.trickMenu = TTSCPetTrickMenu.TTSCPetTrickMenu()
        self.settings = SCSettings.SCSettings(eventPrefix='')
        self.trickMenu.privSetSettingsRef(self.settings)
        self.trickMenuEventName = self.trickMenu.getEventName(SpeedChatGlobals.SCStaticTextMsgEvent)
        self.trickMenu.setScale(0.055)
        self.trickMenu.setBin('gui-popup', 0)
        self.trickMenu.finalizeAll()
        localAvatar.chatMgr.chatInputSpeedChat.whisperAvatarId = None
        self.petDetailPanel = None
        return

    def unload(self):
        self.frame.destroy()
        del self.frame
        self.frame = None
        if hasattr(self, 'petView'):
            self.petView.removeNode()
            del self.petView
        if hasattr(self, 'petModel'):
            self.petModel.delete()
            del self.petModel
        del self.closeButton
        del self.feedButton
        del self.callButton
        del self.scratchButton
        del self.callOwnerButton
        del self.detailButton
        self.trickMenu.destroy()
        del self.trickMenu
        del self.petDetailPanel
        return

    def enter(self, petProxyId):
        self.petProxyId = petProxyId
        if not base.cr.doId2do.has_key(petProxyId):
            self.notify.warning('petProxyId %s not in doId2do!' % petProxyId)
            return
        self.petProxy = base.cr.doId2do[petProxyId]
        self.__fillPetInfo(self.petProxy)
        self.frame.show()
        self.accept(self.trickMenuEventName, self.__handleTrickMenuEvent)
        self.trickMenu.reparentTo(aspect2dp, DGG.FOREGROUND_SORT_INDEX)
        localAvatar.chatMgr.chatInputSpeedChat.whisperAvatarId = None
        self.detailButton['state'] = DGG.NORMAL
        return

    def exit(self):
        self.ignore(self.trickMenuEventName)
        self.trickMenu.reparentTo(hidden)
        self.petProxy = None
        if self.petDetailPanel != None:
            self.petDetailPanel.cleanup()
            self.petDetailPanel = None
        self.frame.hide()
        return

    def __handleTrickMenuEvent(self, textId):
        if PetTricks.ScId2trickId.has_key(textId):
            trickId = PetTricks.ScId2trickId[textId]
            doneStatus = {'mode': 'OK',
             'trickId': trickId}
            messenger.send(self.doneEvent, [doneStatus])
            self.detailButton['state'] = DGG.NORMAL

    def __handleClose(self):
        doneStatus = {'mode': 'Back'}
        messenger.send(self.doneEvent, [doneStatus])

    def __handleCall(self):
        doneStatus = {'mode': 'OK',
         'trickId': 0}
        messenger.send(self.doneEvent, [doneStatus])

    def __handleDetailDone(self):
        if self.petDetailPanel != None:
            self.petDetailPanel.cleanup()
            self.petDetailPanel = None
        self.detailButton['state'] = DGG.NORMAL
        return

    def __handleDetail(self):
        self.petDetailPanel = PetDetailPanel.PetDetailPanel(pet=self.petProxy, closeCallback=self.__handleDetailDone, parent=self.frame)
        self.detailButton['state'] = DGG.DISABLED

    def __fillPetInfo(self, avatar):
        self.notify.debug('__fillPetInfo(): doId=%s' % avatar.doId)
        if self.nameLabel == None:
            self.petView = self.frame.attachNewNode('petView')
            self.petView.setPos(0, 0, 5.4)
            self.petModel = Pet.Pet(forGui=1)
            self.petModel.setDNA(avatar.getDNA())
            self.petModel.fitAndCenterHead(3.575, forGui=1)
            self.petModel.reparentTo(self.petView)
            self.petModel.enterNeutralHappy()
            self.petModel.startBlink()
            self.nameLabel = DirectLabel(parent=self.frame, pos=(0, 0, 5.2), relief=None, text=avatar.getName(), text_font=avatar.getFont(), text_fg=Vec4(0, 0, 0, 1), text_pos=(0, 0), text_scale=0.4, text_wordwrap=7.5, text_shadow=(1, 1, 1, 1))
            self.stateLabel = DirectLabel(parent=self.frame, pos=(0.7, 0, 3.5), relief=None, text='', text_font=avatar.getFont(), text_fg=Vec4(0, 0, 0, 1), text_scale=0.4, text_wordwrap=7.5, text_shadow=(1, 1, 1, 1))
        self.__refreshPetInfo(avatar)
        return

    def __refreshPetInfo(self, avatar):
        self.notify.debug('__refreshPetInfo(): doId=%s' % avatar.doId)
        avatar.updateOfflineMood()
        mood = avatar.getDominantMood()
        self.stateLabel['text'] = TTLocalizer.PetMoodAdjectives[mood]
        self.nameLabel['text'] = avatar.getName()
