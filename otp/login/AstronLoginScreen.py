from direct.directnotify import DirectNotifyGlobal
from otp.login.LoginScreen import LoginScreen

class AstronLoginScreen(LoginScreen):
    def handleWaitForLoginResponse(self, msgType, di):
        self.cr.handleMessageType(msgType, di)
