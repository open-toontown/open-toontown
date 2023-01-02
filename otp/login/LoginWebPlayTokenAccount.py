from panda3d.core import *
from direct.directnotify import DirectNotifyGlobal
from . import LoginTTAccount

class LoginWebPlayTokenAccount(LoginTTAccount.LoginTTAccount):
    notify = DirectNotifyGlobal.directNotify.newCategory('LoginWebPlayTokenAccount')

    def supportsRelogin(self):
        return 0

    def createAccount(self, loginName, password, data):
        pass

    def authorize(self, loginName, password):
        self.playToken = password
        self.playTokenIsEncrypted = 1
        self.freeTimeExpires = -1
        self.cr.freeTimeExpiresAt = self.freeTimeExpires

    def createBilling(self, loginName, password, data):
        pass

    def setParentPassword(self, loginName, password, parentPassword):
        pass

    def supportsParentPassword(self):
        return 1

    def changePassword(self, loginName, password, newPassword):
        pass

    def requestPwdReminder(self, email = None, acctName = None):
        pass

    def cancelAccount(self, loginName, password):
        pass

    def getAccountData(self, loginName, password):
        pass

    def getErrorCode(self):
        if 'response' not in self:
            return 0
        return self.response.getInt('errorCode', 0)

    def needToSetParentPassword(self):
        return 0
