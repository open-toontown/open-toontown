import sys
from direct.showbase import DirectObject
from direct.showbase.PythonUtil import traceFunctionCall
from otp.otpbase import OTPGlobals
from otp.otpbase import OTPLocalizer
from toontown.toonbase import TTLocalizer
from toontown.toontowngui import TeaserPanel
from direct.directnotify import DirectNotifyGlobal
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from otp.chat import ChatManager
from .TTChatInputSpeedChat import TTChatInputSpeedChat
from .TTChatInputNormal import TTChatInputNormal
from .TTChatInputWhiteList import TTChatInputWhiteList

class HackedDirectRadioButton(DirectCheckButton):

    def __init__(self, parent = None, **kw):
        optiondefs = ()
        self.defineoptions(kw, optiondefs)
        DirectCheckButton.__init__(self, parent)
        self.initialiseoptions(HackedDirectRadioButton)

    def commandFunc(self, event):
        if self['indicatorValue']:
            self['indicatorValue'] = 0
        DirectCheckButton.commandFunc(self, event)


class ToontownChatManager(ChatManager.ChatManager):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownChatManager')

    def __init__(self, cr, localAvatar):
        gui = loader.loadModel('phase_3.5/models/gui/chat_input_gui')
        self.normalButton = DirectButton(image=(gui.find('**/ChtBx_ChtBtn_UP'), gui.find('**/ChtBx_ChtBtn_DN'), gui.find('**/ChtBx_ChtBtn_RLVR')), pos=(-1.2647, 0, 0.928), scale=1.179, relief=None, image_color=Vec4(1, 1, 1, 1), text=('', OTPLocalizer.ChatManagerChat, OTPLocalizer.ChatManagerChat), text_align=TextNode.ALeft, text_scale=TTLocalizer.TCMnormalButton, text_fg=Vec4(1, 1, 1, 1), text_shadow=Vec4(0, 0, 0, 1), text_pos=(-0.0525, -0.09), textMayChange=0, sortOrder=DGG.FOREGROUND_SORT_INDEX, command=self.__normalButtonPressed)
        self.normalButton.hide()
        self.openScSfx = loader.loadSfx('phase_3.5/audio/sfx/GUI_quicktalker.ogg')
        self.openScSfx.setVolume(0.6)
        self.scButton = DirectButton(image=(gui.find('**/ChtBx_ChtBtn_UP'), gui.find('**/ChtBx_ChtBtn_DN'), gui.find('**/ChtBx_ChtBtn_RLVR')), pos=TTLocalizer.TCMscButtonPos, scale=1.179, relief=None, image_color=Vec4(0.75, 1, 0.6, 1), text=('', OTPLocalizer.GlobalSpeedChatName, OTPLocalizer.GlobalSpeedChatName), text_scale=TTLocalizer.TCMscButton, text_fg=Vec4(1, 1, 1, 1), text_shadow=Vec4(0, 0, 0, 1), text_pos=(0, -0.09), textMayChange=0, sortOrder=DGG.FOREGROUND_SORT_INDEX, command=self.__scButtonPressed, clickSound=self.openScSfx)
        self.scButton.hide()
        self.whisperFrame = DirectFrame(parent=aspect2dp, relief=None, image=DGG.getDefaultDialogGeom(), image_scale=(0.45, 0.45, 0.45), image_color=OTPGlobals.GlobalDialogColor, pos=(-0.4, 0, 0.754), text=OTPLocalizer.ChatManagerWhisperTo, text_wordwrap=7.0, text_scale=TTLocalizer.TCMwhisperFrame, text_fg=Vec4(0, 0, 0, 1), text_pos=(0, 0.14), textMayChange=1, sortOrder=DGG.FOREGROUND_SORT_INDEX)
        self.whisperFrame.hide()
        self.whisperButton = DirectButton(parent=self.whisperFrame, image=(gui.find('**/ChtBx_ChtBtn_UP'), gui.find('**/ChtBx_ChtBtn_DN'), gui.find('**/ChtBx_ChtBtn_RLVR')), pos=(-0.125, 0, -0.1), scale=1.179, relief=None, image_color=Vec4(1, 1, 1, 1), text=('',
         OTPLocalizer.ChatManagerChat,
         OTPLocalizer.ChatManagerChat,
         ''), image3_color=Vec4(0.6, 0.6, 0.6, 0.6), text_scale=TTLocalizer.TCMwhisperButton, text_fg=(0, 0, 0, 1), text_pos=(0, -0.09), textMayChange=0, command=self.__whisperButtonPressed)
        self.whisperScButton = DirectButton(parent=self.whisperFrame, image=(gui.find('**/ChtBx_ChtBtn_UP'), gui.find('**/ChtBx_ChtBtn_DN'), gui.find('**/ChtBx_ChtBtn_RLVR')), pos=(0.0, 0, -0.1), scale=1.179, relief=None, image_color=Vec4(0.75, 1, 0.6, 1), text=('',
         OTPLocalizer.GlobalSpeedChatName,
         OTPLocalizer.GlobalSpeedChatName,
         ''), image3_color=Vec4(0.6, 0.6, 0.6, 0.6), text_scale=TTLocalizer.TCMwhisperScButton, text_fg=(0, 0, 0, 1), text_pos=(0, -0.09), textMayChange=0, command=self.__whisperScButtonPressed)
        self.whisperCancelButton = DirectButton(parent=self.whisperFrame, image=(gui.find('**/CloseBtn_UP'), gui.find('**/CloseBtn_DN'), gui.find('**/CloseBtn_Rllvr')), pos=(0.125, 0, -0.1), scale=1.179, relief=None, text=('', OTPLocalizer.ChatManagerCancel, OTPLocalizer.ChatManagerCancel), text_scale=0.05, text_fg=(0, 0, 0, 1), text_pos=(0, -0.09), textMayChange=0, command=self.__whisperCancelPressed)
        gui.removeNode()
        ChatManager.ChatManager.__init__(self, cr, localAvatar)
        self.defaultToWhiteList = base.config.GetBool('white-list-is-default', 1)
        self.chatInputSpeedChat = TTChatInputSpeedChat(self)
        self.normalPos = Vec3(-1.083, 0, 0.804)
        self.whisperPos = Vec3(0.0, 0, 0.71)
        self.speedChatPlusPos = Vec3(-0.35, 0, 0.71)
        self.chatInputWhiteList = TTChatInputWhiteList()
        if self.defaultToWhiteList:
            self.chatInputNormal = self.chatInputWhiteList
            self.chatInputNormal.setPos(self.normalPos)
            self.chatInputNormal.desc = 'chatInputNormal'
        else:
            self.chatInputNormal = TTChatInputNormal(self)
        self.chatInputWhiteList.setPos(self.speedChatPlusPos)
        self.chatInputWhiteList.desc = 'chatInputWhiteList'
        return

    def delete(self):
        ChatManager.ChatManager.delete(self)
        loader.unloadModel('phase_3.5/models/gui/chat_input_gui')
        self.normalButton.destroy()
        del self.normalButton
        self.scButton.destroy()
        del self.scButton
        del self.openScSfx
        self.whisperFrame.destroy()
        del self.whisperFrame
        self.whisperButton.destroy()
        del self.whisperButton
        self.whisperScButton.destroy()
        del self.whisperScButton
        self.whisperCancelButton.destroy()
        del self.whisperCancelButton
        self.chatInputWhiteList.destroy()
        del self.chatInputWhiteList

    def sendSCResistanceChatMessage(self, textId):
        messenger.send('chatUpdateSCResistance', [textId])
        self.announceSCChat()

    def sendSCSingingChatMessage(self, textId):
        messenger.send('chatUpdateSCSinging', [textId])
        self.announceSCChat()

    def sendSCSingingWhisperMessage(self, textId):
        pass

    def sendSCToontaskChatMessage(self, taskId, toNpcId, toonProgress, msgIndex):
        messenger.send('chatUpdateSCToontask', [taskId,
         toNpcId,
         toonProgress,
         msgIndex])
        self.announceSCChat()

    def sendSCToontaskWhisperMessage(self, taskId, toNpcId, toonProgress, msgIndex, whisperAvatarId, toPlayer):
        if toPlayer:
            base.talkAssistant.sendPlayerWhisperToonTaskSpeedChat(taskId, toNpcId, toonProgress, msgIndex, whisperAvatarId)
        else:
            messenger.send('whisperUpdateSCToontask', [taskId,
             toNpcId,
             toonProgress,
             msgIndex,
             whisperAvatarId])

    def enterOpenChatWarning(self):
        if self.openChatWarning == None:
            buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
            buttonImage = (buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr'))
            self.openChatWarning = DirectFrame(parent=aspect2dp, pos=(0.0, 0.1, 0.2), relief=None, image=DGG.getDefaultDialogGeom(), image_color=OTPGlobals.GlobalDialogColor, image_scale=(1.2, 1.0, 1.4), text=OTPLocalizer.OpenChatWarning, text_wordwrap=19, text_scale=TTLocalizer.TCMopenChatWarning, text_pos=(0.0, 0.575), textMayChange=0)
            DirectButton(self.openChatWarning, image=buttonImage, relief=None, text=OTPLocalizer.OpenChatWarningOK, text_scale=0.05, text_pos=(0.0, -0.1), textMayChange=0, pos=(0.0, 0.0, -0.55), command=self.__handleOpenChatWarningOK)
            buttons.removeNode()
        self.openChatWarning.show()
        normObs, scObs = self.isObscured()
        if not scObs:
            self.scButton.show()
        if not normObs:
            self.normalButton.show()
        return

    def enterMainMenu(self):
        self.chatInputNormal.setPos(self.normalPos)
        if self.chatInputWhiteList.isActive():
            self.notify.debug('enterMainMenu calling checkObscured')
            ChatManager.ChatManager.checkObscurred(self)
        else:
            ChatManager.ChatManager.enterMainMenu(self)

    def exitOpenChatWarning(self):
        self.openChatWarning.hide()
        self.scButton.hide()

    def enterUnpaidChatWarning(self):
        self.forceHidePayButton = False
        if base.cr.productName in ['DisneyOnline-UK',
         'JP',
         'DE',
         'BR',
         'FR']:
            directFrameText = OTPLocalizer.PaidParentPasswordUKWarning
            payButtonText = OTPLocalizer.PaidParentPasswordUKWarningSet
            directButtonText = OTPLocalizer.PaidParentPasswordUKWarningContinue
        else:
            directFrameText = OTPLocalizer.PaidNoParentPasswordWarning
            payButtonText = OTPLocalizer.PaidNoParentPasswordWarningSet
            directButtonText = OTPLocalizer.PaidNoParentPasswordWarningContinue
            if 'QuickLauncher' not in str(base.cr.launcher.__class__) and not base.cr.isPaid():
                directFrameText = OTPLocalizer.UnpaidNoParentPasswordWarning
                self.forceHidePayButton = True
        if self.unpaidChatWarning == None:
            guiButton = loader.loadModel('phase_3/models/gui/quit_button')
            buttonImage = (guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR'))
            self.unpaidChatWarning = DirectFrame(parent=aspect2dp, pos=(0.0, 0.1, 0.4), relief=None, image=DGG.getDefaultDialogGeom(), image_color=OTPGlobals.GlobalDialogColor, image_scale=(1.2, 1.0, 0.8), text=directFrameText, text_wordwrap=TTLocalizer.TCMunpaidChatWarningWordwrap, text_scale=TTLocalizer.TCMunpaidChatWarning, text_pos=TTLocalizer.TCMunpaidChatWarningPos, textMayChange=0)
            self.payButton = DirectButton(self.unpaidChatWarning, image=buttonImage, relief=None, text=payButtonText, image_scale=(1.75, 1, 1.15), text_scale=TTLocalizer.TCMpayButton, text_pos=(0, -0.02), textMayChange=0, pos=TTLocalizer.TCMpayButtonPos, command=self.__handleUnpaidChatWarningPay)
            DirectButton(self.unpaidChatWarning, image=buttonImage, relief=None, text=directButtonText, textMayChange=0, image_scale=(1.75, 1, 1.15), text_scale=0.06, text_pos=(0, -0.02), pos=TTLocalizer.TCMdirectButtonTextPos, command=self.__handleUnpaidChatWarningContinue)
            guiButton.removeNode()
        if base.localAvatar.cantLeaveGame or self.forceHidePayButton:
            self.payButton.hide()
        else:
            self.payButton.show()
        if base.cr.productName not in ['ES',
         'JP',
         'DE',
         'BR',
         'FR']:
            self.unpaidChatWarning.show()
        else:
            place = base.cr.playGame.getPlace()
            if place:
                place.fsm.request('stopped')
            self.teaser = TeaserPanel.TeaserPanel('secretChat', self.__handleUnpaidChatWarningDone)
            if base.localAvatar.inTutorial:
                self.teaser.hidePay()
        normObs, scObs = self.isObscured()
        if not scObs:
            self.scButton.show()
        if not normObs:
            self.normalButton.show()
        return

    def exitUnpaidChatWarning(self):
        if self.unpaidChatWarning:
            self.unpaidChatWarning.hide()
        self.scButton.hide()

    def enterNoSecretChatAtAll(self):
        if self.noSecretChatAtAll == None:
            buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
            okButtonImage = (buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr'))
            self.noSecretChatAtAll = DirectFrame(parent=aspect2dp, pos=(0.0, 0.1, 0.2), relief=None, image=DGG.getDefaultDialogGeom(), image_color=OTPGlobals.GlobalDialogColor, image_scale=(1.4, 1.0, 1.1), text=OTPLocalizer.NoSecretChatAtAll, text_wordwrap=20, textMayChange=0, text_scale=0.06, text_pos=(0, 0.3))
            DirectLabel(parent=self.noSecretChatAtAll, relief=None, pos=(0, 0, 0.4), text=OTPLocalizer.NoSecretChatAtAllTitle, textMayChange=0, text_scale=0.08)
            DirectButton(self.noSecretChatAtAll, image=okButtonImage, relief=None, text=OTPLocalizer.NoSecretChatAtAllOK, text_scale=0.05, text_pos=(0.0, -0.1), textMayChange=0, pos=(0.0, 0.0, -0.4), command=self.__handleNoSecretChatAtAllOK)
            buttons.removeNode()
        self.noSecretChatAtAll.show()
        return

    def exitNoSecretChatAtAll(self):
        self.noSecretChatAtAll.hide()

    def enterNoSecretChatWarning(self, passwordOnly = 0):
        if not passwordOnly:
            warningText = OTPLocalizer.NoSecretChatWarning
        else:
            warningText = OTPLocalizer.ChangeSecretFriendsOptionsWarning
        if self.noSecretChatWarning == None:
            buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
            nameBalloon = loader.loadModel('phase_3/models/props/chatbox_input')
            okButtonImage = (buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr'))
            cancelButtonImage = (buttons.find('**/CloseBtn_UP'), buttons.find('**/CloseBtn_DN'), buttons.find('**/CloseBtn_Rllvr'))
            if base.cr.productName != 'Terra-DMC':
                okPos = (-0.22, 0.0, -0.35)
                textPos = (0, 0.25)
                okCommand = self.__handleNoSecretChatWarningOK
            else:
                self.passwordEntry = None
                okPos = (0, 0, -0.35)
                textPos = (0, 0.125)
                okCommand = self.__handleNoSecretChatWarningCancel
            self.noSecretChatWarning = DirectFrame(parent=aspect2dp, pos=(0.0, 0.1, 0.2), relief=None, image=DGG.getDefaultDialogGeom(), image_color=OTPGlobals.GlobalDialogColor, image_scale=(1.4, 1.0, 1.0), text=warningText, text_wordwrap=20, text_scale=0.055, text_pos=textPos, textMayChange=1)
            DirectButton(self.noSecretChatWarning, image=okButtonImage, relief=None, text=OTPLocalizer.NoSecretChatWarningOK, text_scale=0.05, text_pos=(0.0, -0.1), textMayChange=0, pos=okPos, command=okCommand)
            DirectLabel(parent=self.noSecretChatWarning, relief=None, pos=(0, 0, 0.35), text=OTPLocalizer.NoSecretChatWarningTitle, textMayChange=0, text_scale=0.08)
            if base.cr.productName != 'Terra-DMC':
                self.passwordLabel = DirectLabel(parent=self.noSecretChatWarning, relief=None, pos=(-0.07, 0.0, -0.2), text=OTPLocalizer.ParentPassword, text_scale=0.06, text_align=TextNode.ARight, textMayChange=0)
                self.passwordEntry = DirectEntry(parent=self.noSecretChatWarning, relief=None, image=nameBalloon, image1_color=(0.8, 0.8, 0.8, 1.0), scale=0.064, pos=(0.0, 0.0, -0.2), width=OTPGlobals.maxLoginWidth, numLines=1, focus=1, cursorKeys=1, obscured=1, command=self.__handleNoSecretChatWarningOK)
                DirectButton(self.noSecretChatWarning, image=cancelButtonImage, relief=None, text=OTPLocalizer.NoSecretChatWarningCancel, text_scale=0.05, text_pos=(0.0, -0.1), textMayChange=1, pos=(0.2, 0.0, -0.35), command=self.__handleNoSecretChatWarningCancel)
            buttons.removeNode()
            nameBalloon.removeNode()
        else:
            self.noSecretChatWarning['text'] = warningText
            if self.passwordEntry:
                self.passwordEntry['focus'] = 1
                self.passwordEntry.enterText('')
        self.noSecretChatWarning.show()
        return

    def exitNoSecretChatWarning(self):
        self.noSecretChatWarning.hide()

    def enterActivateChat(self):
        if self.activateChatGui == None:
            guiButton = loader.loadModel('phase_3/models/gui/quit_button')
            buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
            okButtonImage = (buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr'))
            cancelButtonImage = (buttons.find('**/CloseBtn_UP'), buttons.find('**/CloseBtn_DN'), buttons.find('**/CloseBtn_Rllvr'))
            moreButtonImage = (guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR'))
            nameShopGui = loader.loadModel('phase_3/models/gui/nameshop_gui')
            circle = nameShopGui.find('**/namePanelCircle')
            self.activateChatGui = DirectFrame(parent=aspect2dp, pos=(0.0, 0.1, 0.2), relief=None, image=DGG.getDefaultDialogGeom(), image_color=OTPGlobals.GlobalDialogColor, image_scale=(1.8, 1.0, 1.6), text=OTPLocalizer.ActivateChat, text_align=TextNode.ALeft, text_wordwrap=33, text_scale=TTLocalizer.TCMactivateChatGui, text_pos=(-0.82, 0.58), textMayChange=0)
            innerCircle = circle.copyTo(hidden)
            innerCircle.setPos(0, 0, 0.2)
            self.c1b = circle.copyTo(self.activateChatGui, -1)
            self.c1b.setColor(0, 0, 0, 1)
            self.c1b.setPos(-0.8, 0, 0.29)
            self.c1b.setScale(0.4)
            c1f = circle.copyTo(self.c1b)
            c1f.setColor(1, 1, 1, 1)
            c1f.setScale(0.8)
            self.c2b = circle.copyTo(self.activateChatGui, -2)
            self.c2b.setColor(0, 0, 0, 1)
            self.c2b.setPos(-0.8, 0, 0.14)
            self.c2b.setScale(0.4)
            c2f = circle.copyTo(self.c2b)
            c2f.setColor(1, 1, 1, 1)
            c2f.setScale(0.8)
            self.c3b = circle.copyTo(self.activateChatGui, -2)
            self.c3b.setColor(0, 0, 0, 1)
            self.c3b.setPos(-0.8, 0, -0.01)
            self.c3b.setScale(0.4)
            c3f = circle.copyTo(self.c3b)
            c3f.setColor(1, 1, 1, 1)
            c3f.setScale(0.8)
            DirectLabel(self.activateChatGui, relief=None, text=OTPLocalizer.ActivateChatTitle, text_align=TextNode.ACenter, text_scale=0.07, text_pos=(0, 0.7), textMayChange=0)
            if base.cr.productName != 'JP':
                DirectButton(self.activateChatGui, image=moreButtonImage, image_scale=(1.25, 1.0, 1.0), relief=None, text=OTPLocalizer.ActivateChatMoreInfo, text_scale=0.06, text_pos=(0, -0.02), textMayChange=0, pos=(0.0, 0.0, -0.7), command=self.__handleActivateChatMoreInfo)
            self.dcb1 = HackedDirectRadioButton(parent=self.activateChatGui, relief=None, scale=0.1, boxImage=innerCircle, boxImageScale=2.5, boxImageColor=VBase4(0, 0.25, 0.5, 1), boxRelief=None, pos=(-0.745, 0, 0.297), command=self.__updateCheckBoxen, extraArgs=[1])
            self.dcb2 = HackedDirectRadioButton(parent=self.activateChatGui, relief=None, scale=0.1, boxImage=innerCircle, boxImageScale=2.5, boxImageColor=VBase4(0, 0.25, 0.5, 1), boxRelief=None, pos=(-0.745, 0, 0.147), command=self.__updateCheckBoxen, extraArgs=[2])
            self.dcb3 = HackedDirectRadioButton(parent=self.activateChatGui, relief=None, scale=0.1, boxImage=innerCircle, boxImageScale=2.5, boxImageColor=VBase4(0, 0.25, 0.5, 1), boxRelief=None, pos=(-0.745, 0, -0.003), command=self.__updateCheckBoxen, extraArgs=[3])
            DirectButton(self.activateChatGui, image=okButtonImage, relief=None, text=OTPLocalizer.ActivateChatYes, text_scale=0.05, text_pos=(0.0, -0.1), textMayChange=0, pos=(-0.35, 0.0, -0.27), command=self.__handleActivateChatYes)
            DirectButton(self.activateChatGui, image=cancelButtonImage, relief=None, text=OTPLocalizer.ActivateChatNo, text_scale=0.05, text_pos=(0.0, -0.1), textMayChange=0, pos=(0.35, 0.0, -0.27), command=self.__handleActivateChatNo)
            guiButton.removeNode()
            buttons.removeNode()
            nameShopGui.removeNode()
            innerCircle.removeNode()
        self.__initializeCheckBoxen()
        self.activateChatGui.show()
        return

    def __initializeCheckBoxen(self):
        if base.cr.secretChatAllowed and not base.cr.secretChatNeedsParentPassword:
            self.dcb1['indicatorValue'] = 0
            self.dcb2['indicatorValue'] = 0
            self.dcb3['indicatorValue'] = 1
        elif base.cr.secretChatAllowed and base.cr.secretChatNeedsParentPassword:
            self.dcb1['indicatorValue'] = 0
            self.dcb2['indicatorValue'] = 1
            self.dcb3['indicatorValue'] = 0
        else:
            self.dcb1['indicatorValue'] = 1
            self.dcb2['indicatorValue'] = 0
            self.dcb3['indicatorValue'] = 0

    def __updateCheckBoxen(self, value, checkBox):
        if value == 0:
            return
        if checkBox == 1:
            self.dcb2['indicatorValue'] = 0
            self.dcb3['indicatorValue'] = 0
        elif checkBox == 2:
            self.dcb1['indicatorValue'] = 0
            self.dcb3['indicatorValue'] = 0
        else:
            self.dcb1['indicatorValue'] = 0
            self.dcb2['indicatorValue'] = 0

    def exitActivateChat(self):
        self.activateChatGui.hide()

    def enterSecretChatActivated(self, mode = 2):
        if mode == 0:
            modeText = OTPLocalizer.SecretChatDeactivated
        elif mode == 1:
            modeText = OTPLocalizer.RestrictedSecretChatActivated
        else:
            modeText = OTPLocalizer.SecretChatActivated
        if self.secretChatActivated == None:
            guiButton = loader.loadModel('phase_3/models/gui/quit_button')
            optionsButtonImage = (guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR'))
            buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
            buttonImage = (buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr'))
            self.secretChatActivated = DirectFrame(parent=aspect2dp, pos=(0.0, 0.1, 0.4), relief=None, image=DGG.getDefaultDialogGeom(), image_color=OTPGlobals.GlobalDialogColor, image_scale=(1.0, 1.0, 0.8), text=modeText, text_align=TextNode.ACenter, text_wordwrap=14, text_scale=TTLocalizer.TCMsecretChatActivated, text_pos=(0, 0.25))
            DirectButton(self.secretChatActivated, image=buttonImage, relief=None, text=OTPLocalizer.SecretChatActivatedOK, text_scale=0.05, text_pos=(0.0, -0.1), textMayChange=0, pos=(0.0, 0.0, -0.1), command=self.__handleSecretChatActivatedOK)
            buttons.removeNode()
            guiButton.removeNode()
        else:
            self.secretChatActivated['text'] = modeText
        self.secretChatActivated.show()
        return

    def exitSecretChatActivated(self):
        self.secretChatActivated.hide()

    def enterProblemActivatingChat(self):
        if self.problemActivatingChat == None:
            buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
            buttonImage = (buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr'))
            self.problemActivatingChat = DirectFrame(parent=aspect2dp, pos=(0.0, 0.1, 0.4), relief=None, image=DGG.getDefaultDialogGeom(), image_color=OTPGlobals.GlobalDialogColor, image_scale=(1.2, 1.0, 0.9), text='', text_align=TextNode.ALeft, text_wordwrap=18, text_scale=0.06, text_pos=(-0.5, 0.28), textMayChange=1)
            DirectButton(self.problemActivatingChat, image=buttonImage, relief=None, text=OTPLocalizer.ProblemActivatingChatOK, text_scale=0.05, text_pos=(0.0, -0.1), textMayChange=0, pos=(0.0, 0.0, -0.28), command=self.__handleProblemActivatingChatOK)
            buttons.removeNode()
        self.problemActivatingChat.show()
        return

    def exitProblemActivatingChat(self):
        self.problemActivatingChat.hide()

    def __normalButtonPressed(self):
        if base.config.GetBool('want-qa-regression', 0):
            self.notify.info('QA-REGRESSION: CHAT: Speedchat Plus')
        messenger.send('wakeup')
        if base.cr.productName in ['DisneyOnline-US', 'ES']:
            if base.cr.whiteListChatEnabled:
                self.fsm.request('normalChat')
            elif not base.cr.isParentPasswordSet():
                self.paidNoParentPassword = 1
                self.fsm.request('unpaidChatWarning')
            elif not base.cr.allowSecretChat():
                self.fsm.request('noSecretChatAtAllAndNoWhitelist')
            elif not base.localAvatar.canChat():
                self.fsm.request('openChatWarning')
            else:
                self.fsm.request('normalChat')
        elif base.cr.productName == 'Terra-DMC':
            if not base.cr.allowSecretChat():
                self.fsm.request('noSecretChatWarning')
            elif not base.localAvatar.canChat():
                self.fsm.request('openChatWarning')
            else:
                self.fsm.request('normalChat')
        elif base.cr.productName in ['DisneyOnline-UK',
         'DisneyOnline-AP',
         'JP',
         'BR',
         'FR']:
            if base.cr.whiteListChatEnabled:
                self.fsm.request('normalChat')
            elif not base.cr.isParentPasswordSet():
                self.paidNoParentPassword = 1
                self.fsm.request('unpaidChatWarning')
            elif not base.cr.allowSecretChat():
                self.paidNoParentPassword = 1
                self.fsm.request('unpaidChatWarning')
            elif not base.localAvatar.canChat():
                self.fsm.request('openChatWarning')
            else:
                self.fsm.request('normalChat')
        else:
            print('ChatManager: productName: %s not recognized' % base.cr.productName)

    def __scButtonPressed(self):
        if base.config.GetBool('want-qa-regression', 0):
            self.notify.info('QA-REGRESSION: CHAT: Speedchat')
        messenger.send('wakeup')
        if self.fsm.getCurrentState().getName() == 'speedChat':
            self.fsm.request('mainMenu')
        else:
            self.fsm.request('speedChat')

    def __whisperButtonPressed(self, avatarName, avatarId, playerId):
        messenger.send('wakeup')
        playerInfo = None
        if playerId:
            playerInfo = base.cr.playerFriendsManager.getFriendInfo(playerId)
        if playerInfo:
            if playerInfo.understandableYesNo:
                self.fsm.request('whisperChatPlayer', [avatarName, playerId])
                return
        if avatarId:
            self.fsm.request('whisperChat', [avatarName, avatarId])
        return

    def enterNormalChat(self):
        result = ChatManager.ChatManager.enterNormalChat(self)
        if result == None:
            self.notify.warning('something went wrong in enterNormalChat, falling back to main menu')
            self.fsm.request('mainMenu')
        return

    def enterWhisperChatPlayer(self, avatarName, playerId):
        result = ChatManager.ChatManager.enterWhisperChatPlayer(self, avatarName, playerId)
        self.chatInputNormal.setPos(self.whisperPos)
        if result == None:
            self.notify.warning('something went wrong in enterWhisperChatPlayer, falling back to main menu')
            self.fsm.request('mainMenu')
        return

    def enterWhisperChat(self, avatarName, avatarId):
        result = ChatManager.ChatManager.enterWhisperChat(self, avatarName, avatarId)
        self.chatInputNormal.setPos(self.whisperPos)
        if result == None:
            self.notify.warning('something went wrong in enterWhisperChat, falling back to main menu')
            self.fsm.request('mainMenu')
        return

    def enterNoSecretChatAtAllAndNoWhitelist(self):
        if self.noSecretChatAtAllAndNoWhitelist == None:
            buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
            okButtonImage = (buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr'))
            self.noSecretChatAtAllAndNoWhitelist = DirectFrame(parent=aspect2dp, pos=(0.0, 0.1, 0.05), relief=None, image=DGG.getDefaultDialogGeom(), image_color=OTPGlobals.GlobalDialogColor, image_scale=(1.4, 1.0, 1.58), text=OTPLocalizer.NoSecretChatAtAllAndNoWhitelist, text_wordwrap=20, textMayChange=0, text_scale=0.06, text_pos=(0, 0.55))
            DirectLabel(parent=self.noSecretChatAtAllAndNoWhitelist, relief=None, pos=(0, 0, 0.67), text=OTPLocalizer.NoSecretChatAtAllAndNoWhitelistTitle, textMayChange=0, text_scale=0.08)
            DirectButton(self.noSecretChatAtAllAndNoWhitelist, image=okButtonImage, relief=None, text=OTPLocalizer.NoSecretChatAtAllOK, text_scale=0.05, text_pos=(0.0, -0.1), textMayChange=0, pos=(0.0, 0.0, -0.64), command=self.__handleNoSecretChatAtAllOK)
            buttons.removeNode()
        self.noSecretChatAtAllAndNoWhitelist.show()
        return

    def exitNoSecretChatAtAllAndNoWhitelist(self):
        self.noSecretChatAtAllAndNoWhitelist.hide()

    def enterTrueFriendTeaserPanel(self):
        self.previousStateBeforeTeaser = None
        place = base.cr.playGame.getPlace()
        if place:
            if place.fsm.hasStateNamed('stopped'):
                self.previousStateBeforeTeaser = place.fsm.getCurrentState().getName()
                place.fsm.request('stopped')
            else:
                self.notify.warning("Enter: %s has no 'stopped' state." % place)
        self.teaser = TeaserPanel.TeaserPanel(pageName='secretChat', doneFunc=self.handleOkTeaser)
        return

    def exitTrueFriendTeaserPanel(self):
        self.teaser.destroy()
        place = base.cr.playGame.getPlace()
        if place:
            if place.fsm.hasStateNamed('stopped'):
                if self.previousStateBeforeTeaser:
                    place.fsm.request(self.previousStateBeforeTeaser, force=1)
                else:
                    place.fsm.request('walk')
            else:
                self.notify.warning("Exit: %s has no 'stopped' state." % place)

    def handleOkTeaser(self):
        self.fsm.request('mainMenu')

    def __whisperScButtonPressed(self, avatarName, avatarId, playerId):
        if base.config.GetBool('want-qa-regression', 0):
            self.notify.info('QA-REGRESSION: CHAT: Whisper')
        messenger.send('wakeup')
        hasManager = hasattr(base.cr, 'playerFriendsManager')
        transientFriend = 0
        if hasManager:
            transientFriend = base.cr.playerFriendsManager.askTransientFriend(avatarId)
            if transientFriend:
                playerId = base.cr.playerFriendsManager.findPlayerIdFromAvId(avatarId)
        if avatarId and not transientFriend:
            if self.fsm.getCurrentState().getName() == 'whisperSpeedChat':
                self.fsm.request('whisper', [avatarName, avatarId, playerId])
            else:
                self.fsm.request('whisperSpeedChat', [avatarId])
        elif playerId:
            if self.fsm.getCurrentState().getName() == 'whisperSpeedChatPlayer':
                self.fsm.request('whisper', [avatarName, avatarId, playerId])
            else:
                self.fsm.request('whisperSpeedChatPlayer', [playerId])

    def __whisperCancelPressed(self):
        self.fsm.request('mainMenu')

    def __handleOpenChatWarningOK(self):
        self.fsm.request('mainMenu')

    def __handleUnpaidChatWarningDone(self):
        place = base.cr.playGame.getPlace()
        if place:
            place.handleBookClose()
        self.fsm.request('mainMenu')

    def __handleUnpaidChatWarningContinue(self):
        self.fsm.request('mainMenu')

    def __handleUnpaidChatWarningPay(self):
        if base.cr.isWebPlayToken():
            self.fsm.request('leaveToPayDialog')
        else:
            self.fsm.request('mainMenu')

    def __handleNoSecretChatAtAllOK(self):
        self.fsm.request('mainMenu')

    def __handleNoSecretChatWarningOK(self, *args):
        password = self.passwordEntry.get()
        tt = base.cr.loginInterface
        okflag, message = tt.authenticateParentPassword(base.cr.userName, base.cr.password, password)
        if okflag:
            self.fsm.request('activateChat')
        elif message:
            self.fsm.request('problemActivatingChat')
            self.problemActivatingChat['text'] = OTPLocalizer.ProblemActivatingChat % message
        else:
            self.noSecretChatWarning['text'] = OTPLocalizer.NoSecretChatWarningWrongPassword
            self.passwordEntry['focus'] = 1
            self.passwordEntry.enterText('')

    def __handleNoSecretChatWarningCancel(self):
        self.fsm.request('mainMenu')

    def __handleActivateChatYes(self):
        password = self.passwordEntry.get()
        tt = base.cr.loginInterface
        if self.dcb1['indicatorValue']:
            base.cr.secretChatAllowed = 0
            mode = 0
        elif self.dcb2['indicatorValue']:
            base.cr.secretChatAllowed = 1
            base.cr.secretChatNeedsParentPassword = 1
            mode = 1
        else:
            base.cr.secretChatAllowed = 1
            base.cr.secretChatNeedsParentPassword = 0
            mode = 2
        okflag, message = tt.enableSecretFriends(base.cr.userName, base.cr.password, password)
        if okflag:
            tt.resendPlayToken()
            self.fsm.request('secretChatActivated', [mode])
        else:
            if message == None:
                message = 'Parent Password was invalid.'
            self.fsm.request('problemActivatingChat')
            self.problemActivatingChat['text'] = OTPLocalizer.ProblemActivatingChat % message
        return

    def __handleActivateChatMoreInfo(self):
        self.fsm.request('chatMoreInfo')

    def __handleActivateChatNo(self):
        self.fsm.request('mainMenu')

    def __handleSecretChatActivatedOK(self):
        self.fsm.request('mainMenu')

    def __handleSecretChatActivatedChangeOptions(self):
        self.fsm.request('activateChat')

    def __handleProblemActivatingChatOK(self):
        self.fsm.request('mainMenu')

    def messageSent(self):
        pass

    def deactivateChat(self):
        pass
