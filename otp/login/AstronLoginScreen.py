from direct.directnotify import DirectNotifyGlobal
from otp.login.LoginScreen import LoginScreen
from direct.distributed.MsgTypes import *

class AstronLoginScreen(LoginScreen):
    def handleWaitForLoginResponse(self, msgType, di):
        if msgType == CLIENT_HELLO_RESP:
            # Now we can start the heartbeat:
            self.cr.startHeartbeat()
        else:
            self.cr.handleMessageType(msgType, di)
