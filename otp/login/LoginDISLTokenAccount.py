from direct.showbase.ShowBaseGlobal import *
from direct.distributed.MsgTypes import *
from direct.directnotify import DirectNotifyGlobal
from . import LoginBase
from direct.distributed.PyDatagram import PyDatagram

class LoginDISLTokenAccount(LoginBase.LoginBase):

    def __init__(self, cr):
        LoginBase.LoginBase.__init__(self, cr)

    def supportsRelogin(self):
        return 0

    def authorize(self, loginName, password):
        self.loginName = loginName
        self.DISLToken = password

    def sendLoginMsg(self):
        cr = self.cr
        datagram = PyDatagram()
        datagram.addUint16(CLIENT_LOGIN_3)
        datagram.addString(self.DISLToken)
        datagram.addString(cr.serverVersion)
        datagram.addUint32(cr.hashVal)
        datagram.addInt32(CLIENT_LOGIN_3_DISL_TOKEN)
        datagram.addString(cr.validateDownload)
        datagram.addString(cr.wantMagicWords)
        cr.send(datagram)

    def supportsParentPassword(self):
        return 0

    def supportsAuthenticateDelete(self):
        return 0
