from panda3d.core import *
from direct.distributed.MsgTypes import *
from direct.directnotify import DirectNotifyGlobal
from . import LoginTTAccount
from direct.distributed.PyDatagram import PyDatagram

class LoginTTSpecificDevAccount(LoginTTAccount.LoginTTAccount):
    notify = DirectNotifyGlobal.directNotify.newCategory('LoginTTSpecificDevAccount')

    def __init__(self, cr):
        LoginTTAccount.LoginTTAccount.__init__(self, cr)

    def createAccount(self, loginName, password, data):
        self.loginName = loginName
        self.password = password
        self.createFlag = 1
        self.cr.freeTimeExpiresAt = -1
        self.cr.setIsPaid(1)
        return None

    def authorize(self, loginName, password):
        self.loginName = loginName
        self.password = password
        self.createFlag = 0
        self.cr.freeTimeExpiresAt = -1
        self.cr.setIsPaid(1)
        return None

    def supportsRelogin(self):
        return 1

    def sendLoginMsg(self):
        cr = self.cr
        tokenString = ''
        access = ConfigVariableString('force-paid-status', '').getValue()
        if access == '':
            access = 'FULL'
        elif access == 'paid':
            access = 'FULL'
        elif access == 'unpaid':
            access = 'VELVET_ROPE'
        elif access == 'VELVET':
            access = 'VELVET_ROPE'
        else:
            self.notify.error("don't know what to do with force-paid-status %s" % access)
        tokenString += 'TOONTOWN_ACCESS=%s&' % access
        tokenString += 'TOONTOWN_GAME_KEY=%s&' % self.loginName
        wlChatEnabled = 'YES'
        if ConfigVariableString('otp-whitelist', 'YES').getValue() == 'NO':
            wlChatEnabled = 'NO'
        tokenString += 'WL_CHAT_ENABLED=%s &' % wlChatEnabled
        openChatEnabled = 'NO'
        if cr.openChatAllowed:
            openChatEnabled = 'YES'
        tokenString += 'OPEN_CHAT_ENABLED=%s&' % openChatEnabled
        createFriendsWithChat = 'NO'
        if cr.allowSecretChat:
            createFriendsWithChat = 'CODE'
        tokenString += 'CREATE_FRIENDS_WITH_CHAT=%s&' % createFriendsWithChat
        chatCodeCreationRule = 'No'
        if cr.allowSecretChat:
            if ConfigVariableBool('secret-chat-needs-parent-password', 0).getValue():
                chatCodeCreationRule = 'PARENT'
            else:
                chatCodeCreationRule = 'YES'
        tokenString += 'CHAT_CODE_CREATION_RULE=%s&' % chatCodeCreationRule
        DISLID = ConfigVariableInt('fake-DISL-PlayerAccountId', 0).getValue()
        if not DISLID:
            NameStringId = 'DISLID_%s' % self.loginName
            DISLID = ConfigVariableInt(NameStringId, 0).getValue()
        tokenString += 'ACCOUNT_NUMBER=%d&' % DISLID
        tokenString += 'ACCOUNT_NAME=%s&' % self.loginName
        tokenString += 'GAME_USERNAME=%s&' % self.loginName
        tokenString += 'ACCOUNT_NAME_APPROVED=TRUE&'
        tokenString += 'FAMILY_NUMBER=&'
        tokenString += 'Deployment=US&'
        withParentAccount = ConfigVariableBool('dev-with-parent-account', 0).getValue()
        if withParentAccount:
            tokenString += 'TOON_ACCOUNT_TYPE=WITH_PARENT_ACCOUNT&'
        else:
            tokenString += 'TOON_ACCOUNT_TYPE=NO_PARENT_ACCOUNT&'
        tokenString += 'valid=true'
        self.notify.info('tokenString=\n%s' % tokenString)
        datagram = PyDatagram()
        datagram.addUint16(CLIENT_LOGIN_TOONTOWN)
        playToken = tokenString
        datagram.addString(playToken)
        datagram.addString('dev')
        datagram.addUint32(cr.hashVal)
        datagram.addUint32(4)
        magicWords = ConfigVariableString('want-magic-words', '').getValue()
        datagram.addString(magicWords)
        cr.send(datagram)

    def resendPlayToken(self):
        pass

    def requestPwdReminder(self, email = None, acctName = None):
        return 0

    def getAccountData(self, loginName, password):
        return 'Unsupported'

    def supportsParentPassword(self):
        return 1

    def supportsAuthenticateDelete(self):
        return 1

    def enableSecretFriends(self, loginName, password, parentPassword, enable = 1):
        return (password == parentPassword, None)

    def needToSetParentPassword(self):
        return False
