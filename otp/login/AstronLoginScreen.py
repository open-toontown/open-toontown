from direct.directnotify import DirectNotifyGlobal
from otp.login.LoginScreen import LoginScreen
if astronSupport:
    from direct.distributed.MsgTypes import *
else:
    from otp.distributed.OTPMsgTypes import *

class AstronLoginScreen(LoginScreen):

    def handleWaitForLoginResponse(self, msgType, di):
        if msgType == CLIENT_HELLO_RESP:
            # Now we can start the heartbeat:
            self.cr.startHeartbeat()
            self.cr.astronLoginManager.handleRequestLogin(self.doneEvent)
        else:
            self.cr.handleMessageType(msgType, di)
