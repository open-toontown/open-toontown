from direct.directnotify import DirectNotifyGlobal
from otp.login.LoginBase import LoginBase

class LoginAstronAccount(LoginBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('LoginAstronAccount')

    def __init__(self, cr):
        LoginBase.__init__(self, cr)

    def authorize(self, username, password):
        self.notify.info(username)
        self.notify.info(password)

    def sendLoginMsg(self):
        self.notify.info('LOG ME IN!!!!!!!!!!!!')

    def supportsRelogin(self):
        if __debug__:
            return 1
        return 0
