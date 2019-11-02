from otp.otpgui.OTPDialog import *

class TTDialog(OTPDialog):

    def __init__(self, parent = None, style = NoButtons, **kw):
        self.path = 'phase_3/models/gui/dialog_box_buttons_gui'
        OTPDialog.__init__(self, parent, style, **kw)
        self.initialiseoptions(TTDialog)


class TTGlobalDialog(GlobalDialog):

    def __init__(self, message = '', doneEvent = None, style = NoButtons, okButtonText = OTPLocalizer.DialogOK, cancelButtonText = OTPLocalizer.DialogCancel, **kw):
        self.path = 'phase_3/models/gui/dialog_box_buttons_gui'
        GlobalDialog.__init__(self, message, doneEvent, style, okButtonText, cancelButtonText, **kw)
        self.initialiseoptions(TTGlobalDialog)
