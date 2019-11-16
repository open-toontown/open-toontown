import json
from datetime import datetime
import time

from direct.distributed.DistributedObjectGlobal import DistributedObjectGlobal
from direct.directnotify import DirectNotifyGlobal
from otp.uberdog.AccountDetailRecord import AccountDetailRecord
from otp.distributed.PotentialAvatar import PotentialAvatar

class AstronLoginManager(DistributedObjectGlobal):
    notify = DirectNotifyGlobal.directNotify.newCategory('AstronLoginManager')

    def __init__(self, cr):
        DistributedObjectGlobal.__init__(self, cr)
        self.doneEvent = None

    def handleRequestLogin(self, doneEvent):
        self.doneEvent = doneEvent
        playToken = self.cr.playToken or 'dev'
        self.sendRequestLogin(playToken)

    def sendRequestLogin(self, playToken):
        self.sendUpdate('requestLogin', [playToken])

    def loginResponse(self, responseBlob):
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
        chatCodeCreationRule = responseData.get('chatCodeCreationRule')
        self.cr.chatChatCodeCreationRule = chatCodeCreationRule
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
        self.userName = responseData.get('userName')
        self.cr.userName = self.userName
        self.notify.info("Login response return code %s" % returnCode)
        if returnCode == 0:
            self.__handleLoginSuccess()
        elif returnCode == -13:
            self.notify.info("Period Time Expired")
            messenger.send(self.doneEvent, [{'mode': 'reject'}])
        else:
            self.notify.info("Login failed: %s" % errorString)
            messenger.send(self.doneEvent, [{'mode': 'reject'}])

    def __handleLoginSuccess(self):
        self.cr.logAccountInfo()
        launcher.setGoUserName(self.userName)
        launcher.setLastLogin(self.userName)
        launcher.setUserLoggedIn()
        if self.cr.loginInterface.freeTimeExpires == -1:
            launcher.setPaidUserLoggedIn()
        if self.cr.loginInterface.needToSetParentPassword():
            messenger.send(self.doneEvent, [{'mode': 'getChatPassword'}])
        else:
            messenger.send(self.doneEvent, [{'mode': 'success'}])

    def getExtendedErrorMsg(self, errorString):
        prefix = 'Bad DC Version Compare'
        if len(errorString) < len(prefix):
            return errorString
        if errorString[:len(prefix)] == prefix:
            return '%s%s' % (errorString, ', address=%s' % self.cr.getServerAddress())
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
