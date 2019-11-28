from direct.directnotify import DirectNotifyGlobal
from direct.distributed.MsgTypes import *

from otp.login.LoginScreen import LoginScreen


class AstronLoginScreen(LoginScreen):
    notify = DirectNotifyGlobal.directNotify.newCategory('AstronLoginScreen')

    def handleWaitForLoginResponse(self, msgType, di):
        if msgType == CLIENT_HELLO_RESP:
            # Now we can start the heartbeat:
            self.cr.startHeartbeat()
            self.cr.astronLoginManager.handleRequestLogin(self.doneEvent)
        else:
            self.cr.handleMessageType(msgType, di)
