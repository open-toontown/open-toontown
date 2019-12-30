from pandac.PandaModules import *
from otp.otpbase.OTPGlobals import *
from direct.gui.DirectGui import *
from .MultiPageTextFrame import *
from direct.directnotify import DirectNotifyGlobal
from otp.otpbase import OTPLocalizer
from otp.otpgui import OTPDialog

class PrivacyPolicyTextPanel(getGlobalDialogClass()):
    notify = DirectNotifyGlobal.directNotify.newCategory('PrivacyPolicyTextPanel')

    def __init__(self, doneEvent, hidePageNum = 0, pageChangeCallback = None, textList = []):
        dialogClass = getGlobalDialogClass()
        dialogClass.__init__(self, parent=aspect2d, dialogName='privacyPolicyTextDialog', doneEvent=doneEvent, okButtonText=OTPLocalizer.PrivacyPolicyClose, style=OTPDialog.Acknowledge, text='', topPad=1.5, sidePad=1.2, pos=(0, 0, -.55), scale=0.9)
        self.privacyPolicyText = MultiPageTextFrame(parent=self, textList=textList, hidePageNum=hidePageNum, pageChangeCallback=pageChangeCallback, pos=(0, 0, 0.7), width=2.4, height=1.5)
        self['image'] = self['image']
        self['image_pos'] = (0, 0, 0.65)
        self['image_scale'] = (2.7, 1, 1.9)
        closeButton = self.getChild(0)
        closeButton.setZ(-.13)


class PrivacyPolicyPanel(getGlobalDialogClass()):
    notify = DirectNotifyGlobal.directNotify.newCategory('PrivacyPolicyPanel')

    def __init__(self, doneEvent, hidePageNum = 0, pageChangeCallback = None, textList = 1):
        dialogClass = getGlobalDialogClass()
        dialogClass.__init__(self, parent=aspect2d, dialogName='privacyPolicyDialog', doneEvent=doneEvent, okButtonText=OTPLocalizer.PrivacyPolicyClose, style=OTPDialog.Acknowledge, text='', topPad=1.5, sidePad=1.2, pos=(0, 0, -.15), scale=0.6)
        self.chatPrivacyPolicy = None
        self.fsm = ClassicFSM.ClassicFSM('privacyPolicyPanel', [State.State('off', self.enterOff, self.exitOff),
         State.State('version1Adult', self.enterVersion1Adult, self.exitPrivacyPolicy),
         State.State('version1Kids', self.enterVersion1Kids, self.exitPrivacyPolicy),
         State.State('version2Adult', self.enterVersion2Adult, self.exitPrivacyPolicy),
         State.State('version2Kids', self.enterVersion2Kids, self.exitPrivacyPolicy)], 'off', 'off')
        self.fsm.enterInitialState()
        guiButton = loader.loadModel('phase_3/models/gui/quit_button')
        moreButtonImage = (guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR'))
        DirectFrame(self, pos=(-0.4, 0.1, 0.4), relief=None, text=OTPLocalizer.PrivacyPolicyText_Intro, text_align=TextNode.ALeft, text_wordwrap=28, text_scale=0.09, text_pos=(-0.82, 1.0), textMayChange=0)
        textScale = 0.05
        buttonFrame = DirectFrame(self, pos=(0.0, 0.1, 0.0), scale=1.4, relief=None)
        DirectButton(buttonFrame, image=moreButtonImage, image_scale=(1.75, 1.0, 1.0), relief=None, text=OTPLocalizer.ActivateChatPrivacyPolicy_Button1A, text_scale=textScale, text_pos=(0, -0.01), textMayChange=0, pos=(-0.45, 0.0, 0.4), command=self.__handlePrivacyPolicy, extraArgs=['version1Adult'])
        DirectButton(buttonFrame, image=moreButtonImage, image_scale=(1.75, 1.0, 1.0), relief=None, text=OTPLocalizer.ActivateChatPrivacyPolicy_Button1K, text_scale=textScale, text_pos=(0, -0.01), textMayChange=0, pos=(-0.45, 0.0, 0.2), command=self.__handlePrivacyPolicy, extraArgs=['version1Kids'])
        DirectButton(buttonFrame, image=moreButtonImage, image_scale=(1.75, 1.0, 1.0), relief=None, text=OTPLocalizer.ActivateChatPrivacyPolicy_Button2A, text_scale=textScale, text_pos=(0, -0.01), textMayChange=0, pos=(0.45, 0.0, 0.4), command=self.__handlePrivacyPolicy, extraArgs=['version2Adult'])
        DirectButton(buttonFrame, image=moreButtonImage, image_scale=(1.75, 1.0, 1.0), relief=None, text=OTPLocalizer.ActivateChatPrivacyPolicy_Button2K, text_scale=textScale, text_pos=(0, -0.01), textMayChange=0, pos=(0.45, 0.0, 0.2), command=self.__handlePrivacyPolicy, extraArgs=['version2Kids'])
        self['image'] = self['image']
        self['image_pos'] = (0, 0, 0.65)
        self['image_scale'] = (2.7, 1, 1.9)
        closeButton = self.getChild(0)
        closeButton.setZ(-.13)
        return

    def delete(self):
        self.ignoreAll()
        del self.fsm
        if self.chatPrivacyPolicy:
            self.chatPrivacyPolicy.destroy()
            self.chatPrivacyPolicy = None
        return

    def __handlePrivacyPolicy(self, state, *oooo):
        self.fsm.request(state)

    def __privacyPolicyTextDone(self):
        self.exitPrivacyPolicy()

    def enterPrivacyPolicy(self, textList):
        if self.chatPrivacyPolicy == None:
            self.chatPrivacyPolicy = PrivacyPolicyTextPanel('privacyPolicyTextDone', textList=textList)
        self.chatPrivacyPolicy.show()
        self.acceptOnce('privacyPolicyTextDone', self.__privacyPolicyTextDone)
        return

    def exitPrivacyPolicy(self):
        self.ignore('privacyPolicyTextDone')
        if self.chatPrivacyPolicy:
            cleanupDialog('privacyPolicyTextDialog')
            self.chatPrivacyPolicy = None
        return

    def enterVersion1Adult(self):
        self.enterPrivacyPolicy(OTPLocalizer.PrivacyPolicyText_1A)

    def enterVersion1Kids(self):
        self.enterPrivacyPolicy(OTPLocalizer.PrivacyPolicyText_1K)

    def enterVersion2Adult(self):
        self.enterPrivacyPolicy(OTPLocalizer.PrivacyPolicyText_2A)

    def enterVersion2Kids(self):
        self.enterPrivacyPolicy(OTPLocalizer.PrivacyPolicyText_2K)

    def enterOff(self):
        self.ignoreAll()
        self.exitPrivacyPolicy()

    def exitOff(self):
        pass
