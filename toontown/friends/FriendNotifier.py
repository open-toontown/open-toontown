from pandac.PandaModules import *
from toontown.toonbase.ToontownGlobals import *
from direct.showbase import DirectObject
from direct.directnotify import DirectNotifyGlobal
from toontown.toontowngui import TTDialog
from otp.otpbase import OTPLocalizer
from toontown.toontowngui import ToonHeadDialog
from direct.gui.DirectGui import DGG
from otp.otpbase import OTPGlobals

class FriendNotifier(ToonHeadDialog.ToonHeadDialog):
    notify = DirectNotifyGlobal.directNotify.newCategory('FriendNotifier')

    def __init__(self, avId, avName, avDNA, context, **kw):
        self.avId = avId
        self.avName = avName
        self.avDNA = avDNA
        self.context = context
        text = OTPLocalizer.FriendNotifictation % self.avName
        style = TTDialog.Acknowledge
        buttonText = [OTPLocalizer.FriendInviteeOK, OTPLocalizer.FriendInviteeOK]
        command = self.__handleButton
        optiondefs = (('dialogName', 'FriendInvitee', None),
         ('text', text, None),
         ('style', style, None),
         ('buttonText', buttonText, None),
         ('command', command, None),
         ('image_color', (1.0, 0.89, 0.77, 1.0), None),
         ('geom_scale', 0.2, None),
         ('geom_pos', (-0.1, 0, -0.025), None),
         ('pad', (0.075, 0.075), None),
         ('topPad', 0, None),
         ('midPad', 0, None),
         ('pos', (0.45, 0, 0.75), None),
         ('scale', 0.75, None))
        self.defineoptions(kw, optiondefs)
        ToonHeadDialog.ToonHeadDialog.__init__(self, self.avDNA)
        self.initialiseoptions(FriendNotifier)
        self.show()
        return

    def cleanup(self):
        print 'cleanup calling!'
        ToonHeadDialog.ToonHeadDialog.cleanup(self)

    def __handleButton(self, value):
        if value == DGG.DIALOG_OK:
            pass
        self.context = None
        self.cleanup()
        return

    def __handleOhWell(self, value):
        self.cleanup()

    def __handleCancelFromAbove(self, context = None):
        if context == None or context == self.context:
            self.context = None
            self.cleanup()
        return
