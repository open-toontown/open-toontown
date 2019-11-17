from direct.directnotify import DirectNotifyGlobal
from otp.login.LoginBase import LoginBase
from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.MsgTypes import *

class LoginAstronAccount(LoginBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('LoginAstronAccount')

    def __init__(self, cr):
        LoginBase.__init__(self, cr)

    def authorize(self, username, password):
        pass

    def sendLoginMsg(self):
        datagram = PyDatagram()
        datagram.addUint16(CLIENT_HELLO)
        datagram.addUint32(self.cr.hashVal)
        datagram.addString(self.cr.serverVersion)
        self.cr.send(datagram)

    def supportsRelogin(self):
        if __debug__:
            return 1
        return 0

    def supportsAuthenticateDelete(self):
        return 0
