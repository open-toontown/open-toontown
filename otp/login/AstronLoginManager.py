import json
import time
from datetime import datetime

from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectGlobal import DistributedObjectGlobal

from otp.uberdog.AccountDetailRecord import AccountDetailRecord


class AstronLoginManager(DistributedObjectGlobal):
    notify = DirectNotifyGlobal.directNotify.newCategory('AstronLoginManager')

    def __init__(self, cr):
        DistributedObjectGlobal.__init__(self, cr)
        self.doneEvent = None
        self._callback = None
        self.userName = ''

    def handleRequestLogin(self, doneEvent):
        self.doneEvent = doneEvent
        playToken = self.cr.playToken or 'dev'
        self.sendRequestLogin(playToken)

    def sendRequestLogin(self, playToken):
        self.sendUpdate('requestLogin', [playToken])

    def loginResponse(self, responseBlob):
        self.notify.debug("loginResponse")
        responseData = json.loads(responseBlob)
        now = time.time()
        returnCode = responseData.get('returnCode')
        respString = responseData.get('respString')
        errorString = self.getExtendedErrorMsg(respString)
        accountNumber = responseData.get('accountNumber')
        self.cr.DISLIdFromLogin = accountNumber
        accountDetailRecord = AccountDetailRecord()
        self.cr.accountDetailRecord = accountDetailRecord
        createFriendsWithChat = responseData.get('createFriendsWithChat')
        canChat = createFriendsWithChat == "YES" or createFriendsWithChat == "CODE"
        self.cr.secretChatAllowed = canChat
        if base.logPrivateInfo:
            self.notify.info("CREATE_FRIENDS_WITH_CHAT from game server login: %s %s" % (createFriendsWithChat, canChat))
        chatCodeCreationRule = responseData.get('chatCodeCreationRule')
        self.cr.chatChatCodeCreationRule = chatCodeCreationRule
        if base.logPrivateInfo:
            self.notify.info("Chat code creation rule = %s" % chatCodeCreationRule)
        self.cr.secretChatNeedsParentPassword = chatCodeCreationRule == "PARENT"
        serverTime = responseData.get('serverTime')
        self.cr.serverTimeUponLogin = serverTime
        self.cr.clientTimeUponLogin = now
        self.cr.globalClockRealTimeUponLogin = globalClock.getRealTime()
        if hasattr(self.cr, "toontownTimeManager"):
            self.cr.toontownTimeManager.updateLoginTimes(serverTime, now, self.cr.globalClockRealTimeUponLogin)
        serverDelta = serverTime - now
        self.cr.setServerDelta(serverDelta)
        self.notify.setServerDelta(serverDelta, 28800)
        access = responseData.get('access')
        isPaid = access == "FULL"
        self.cr.parentPasswordSet = isPaid
        self.cr.setIsPaid(isPaid)
        if isPaid:
            launcher.setPaidUserLoggedIn()
        if base.logPrivateInfo:
            self.notify.info("Paid from game server login: %s" % isPaid)
        WhiteListResponse = responseData.get('WhiteListResponse')
        if WhiteListResponse == "YES":
            self.cr.whiteListChatEnabled = 1
        else:
            self.cr.whiteListChatEnabled = 0
        lastLoggedInStr = responseData.get('lastLoggedInStr')
        self.cr.lastLoggedIn = datetime.now()
        if hasattr(self.cr, "toontownTimeManager"):
            self.cr.lastLoggedIn = self.cr.toontownTimeManager.convertStrToToontownTime(lastLoggedInStr)
        accountDaysFromServer = responseData.get('accountDays')
        if accountDaysFromServer is not None:
            self.cr.accountDays = self.parseAccountDays(accountDaysFromServer)
        else:
            self.cr.accountDays = 100000
        toonAccountType = responseData.get('toonAccountType')
        if toonAccountType == "WITH_PARENT_ACCOUNT":
            self.cr.withParentAccount = True
        elif toonAccountType == "NO_PARENT_ACCOUNT":
            self.cr.withParentAccount = False
        else:
            self.notify.error("unknown toon account type %s" % toonAccountType)
        if base.logPrivateInfo:
            self.notify.info("toonAccountType=%s" % toonAccountType)
        self.userName = responseData.get('userName')
        self.cr.userName = self.userName
        self.notify.info("Login response return code %s" % returnCode)
        if returnCode == 0:
            self.__handleLoginSuccess()
        elif returnCode == -13:
            self.notify.info("Period Time Expired")
            self.cr.loginScreen.request("showLoginFailDialog", [OTPLocalizer.LoginScreenPeriodTimeExpired])
        else:
            self.notify.info("Login failed: %s" % errorString)
            messenger.send(self.doneEvent, [{'mode': 'reject'}])

    def __handleLoginSuccess(self):
        self.cr.logAccountInfo()
        launcher.setGoUserName(self.userName)
        launcher.setLastLogin(self.userName)
        launcher.setUserLoggedIn()
        if self.cr.loginScreen.loginInterface.freeTimeExpires == -1:
            launcher.setPaidUserLoggedIn()
        if self.cr.loginScreen.loginInterface.needToSetParentPassword():
            messenger.send(self.doneEvent, [{'mode': 'getChatPassword'}])
        else:
            messenger.send(self.doneEvent, [{'mode': 'success'}])

    def getExtendedErrorMsg(self, errorString):
        prefix = 'Bad DC Version Compare'
        if len(errorString) < len(prefix):
            return errorString
        if errorString[:len(prefix)] == prefix:
            return '%s%s' % (errorString, ', address=%s' % base.cr.getServerAddress())
        return errorString

    def parseAccountDays(self, accountDays):
        result = 100000
        if accountDays >= 0:
            result = accountDays
        else:
            self.notify.warning('account days is negative %s' % accountDays)
        self.notify.debug('result=%s' % result)
        return result

    def sendRequestAvatarList(self):
        self.sendUpdate('requestAvatarList')

    def avatarListResponse(self, avatarList):
        self.cr.handleAvatarListResponse(avatarList)

    def sendCreateAvatar(self, avDNA, avName, avPosition):
        # avName isn't used. Sad!
        self.sendUpdate('createAvatar', [avDNA.makeNetString(), avPosition])

    def createAvatarResponse(self, avId):
        messenger.send('nameShopCreateAvatarDone', [avId])

    def sendSetNamePattern(self, avId, p1, f1, p2, f2, p3, f3, p4, f4, callback):
        self._callback = callback
        self.sendUpdate('setNamePattern', [avId, p1, f1, p2, f2, p3, f3, p4, f4])

    def namePatternAnswer(self, avId, status):
        self._callback(avId, status)

    def sendSetNameTyped(self, avId, name, callback):
        self._callback = callback
        self.sendUpdate('setNameTyped', [avId, name])

    def nameTypedResponse(self, avId, status):
        self._callback(avId, status)

    def sendAcknowledgeAvatarName(self, avId, callback):
        self._callback = callback
        self.sendUpdate('acknowledgeAvatarName', [avId])

    def acknowledgeAvatarNameResponse(self):
        self._callback()

    def sendRequestRemoveAvatar(self, avId):
        self.sendUpdate('requestRemoveAvatar', [avId])

    def sendRequestPlayAvatar(self, avId):
        self.sendUpdate('requestPlayAvatar', [avId])
