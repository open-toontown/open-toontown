from panda3d.core import *

from otp.otpbase.OTPTimer import OTPTimer


class ToontownTimer(OTPTimer):

    def __init__(self, useImage = True, highlightNearEnd = True):
        OTPTimer.__init__(self, useImage, highlightNearEnd)
        self.initialiseoptions(ToontownTimer)

    def getImage(self):
        if ToontownTimer.ClockImage == None:
            model = loader.loadModel('phase_3.5/models/gui/clock_gui')
            ToontownTimer.ClockImage = model.find('**/alarm_clock')
            model.removeNode()
        return ToontownTimer.ClockImage
