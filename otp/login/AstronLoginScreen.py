import json
import time
from datetime import datetime

from direct.directnotify import DirectNotifyGlobal
from direct.distributed.MsgTypes import *

from otp.login.LoginScreen import LoginScreen
from otp.otpbase import OTPLocalizer
from otp.uberdog.AccountDetailRecord import AccountDetailRecord


class AstronLoginScreen(LoginScreen):
    notify = DirectNotifyGlobal.directNotify.newCategory('AstronLoginScreen')

    def handleWaitForLoginResponse(self, msgType, di):
        if msgType == CLIENT_HELLO_RESP:
            # Now we can start the heartbeat:
            self.cr.startHeartbeat()

            # Send the login request:
            self.cr.astronLoginManager.handleRequestLogin(self.doneEvent)
        else:
            self.cr.handleMessageType(msgType, di)

    def handleLoginToontownResponse(self, responseBlob):
        self.notify.debug("handleLoginToontownResponse")
        responseData = json.loads(responseBlob)
        now = time.time()
        returnCode = responseData.get('returnCode')
        respString = responseData.get('respString')
        errorString = self.getExtendedErrorMsg(respString)
        self.accountNumber = responseData.get('accountNumber')
        self.cr.DISLIdFromLogin = self.accountNumber
        accountDetailRecord = AccountDetailRecord()
        self.cr.accountDetailRecord = accountDetailRecord
        createFriendsWithChat = responseData.get('createFriendsWithChat')
        canChat = createFriendsWithChat == "YES" or createFriendsWithChat == "CODE"
        self.cr.secretChatAllowed = canChat
        if base.logPrivateInfo:
            self.notify.info("CREATE_FRIENDS_WITH_CHAT from game server login: %s %s" % (createFriendsWithChat, canChat))
        self.chatCodeCreationRule = responseData.get('chatCodeCreationRule')
        self.cr.chatChatCodeCreationRule = self.chatCodeCreationRule
        if base.logPrivateInfo:
            self.notify.info("Chat code creation rule = %s" % self.chatCodeCreationRule)
        self.cr.secretChatNeedsParentPassword = self.chatCodeCreationRule == "PARENT"
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
        self.isPaid = access == "FULL"
        self.cr.parentPasswordSet = self.isPaid
        self.cr.setIsPaid(self.isPaid)
        if self.isPaid:
            launcher.setPaidUserLoggedIn()
        if base.logPrivateInfo:
            self.notify.info("Paid from game server login: %s" % self.isPaid)
        WhiteListResponse = responseData.get('WhiteListResponse')
        if WhiteListResponse == "YES":
            self.cr.whiteListChatEnabled = 1
        else:
            self.cr.whiteListChatEnabled = 0
        self.lastLoggedInStr = responseData.get('lastLoggedInStr')
        self.cr.lastLoggedIn = datetime.now()
        if hasattr(self.cr, "toontownTimeManager"):
            self.cr.lastLoggedIn = self.cr.toontownTimeManager.convertStrToToontownTime(self.lastLoggedInStr)
        accountDaysFromServer = responseData.get('accountDays')
        if accountDaysFromServer is not None:
            self.cr.accountDays = self.parseAccountDays(accountDaysFromServer)
        else:
            self.cr.accountDays = 100000
        self.toonAccountType = responseData.get('toonAccountType')
        if self.toonAccountType == "WITH_PARENT_ACCOUNT":
            self.cr.withParentAccount = True
        elif self.toonAccountType == "NO_PARENT_ACCOUNT":
            self.cr.withParentAccount = False
        else:
            self.notify.error("unknown toon account type %s" % self.toonAccountType)
        if base.logPrivateInfo:
            self.notify.info("toonAccountType=%s" % self.toonAccountType)
        self.userName = responseData.get('userName')
        self.cr.userName = self.userName
        self.notify.info("Login response return code %s" % returnCode)
        if returnCode == 0:
            self._LoginScreen__handleLoginSuccess()
        elif returnCode == -13:
            self.notify.info("Period Time Expired")
            self.fsm.request("showLoginFailDialog", [OTPLocalizer.LoginScreenPeriodTimeExpired])
        else:
            self.notify.info("Login failed: %s" % errorString)
            messenger.send(self.doneEvent, [{'mode': 'reject'}])
