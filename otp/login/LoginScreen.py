import json
import os
import time
from datetime import datetime
from pandac.PandaModules import *
from direct.distributed.MsgTypes import *
from direct.gui.DirectGui import *
from direct.fsm import StateData
from direct.fsm import ClassicFSM
from direct.fsm import State
from direct.directnotify import DirectNotifyGlobal
from direct.task import Task
from otp.otpgui import OTPDialog
from otp.otpbase import OTPLocalizer
from otp.otpbase import OTPGlobals
from otp.uberdog.AccountDetailRecord import AccountDetailRecord, SubDetailRecord
from . import TTAccount
from . import GuiScreen

class LoginScreen(StateData.StateData, GuiScreen.GuiScreen):
    AutoLoginName = base.config.GetString('%s-auto-login%s' % (game.name, os.getenv('otp_client', '')), '')
    AutoLoginPassword = base.config.GetString('%s-auto-password%s' % (game.name, os.getenv('otp_client', '')), '')
    notify = DirectNotifyGlobal.directNotify.newCategory('LoginScreen')
    ActiveEntryColor = Vec4(1, 1, 1, 1)
    InactiveEntryColor = Vec4(0.8, 0.8, 0.8, 1)

    def __init__(self, cr, doneEvent):
        self.notify.debug('__init__')
        StateData.StateData.__init__(self, doneEvent)
        GuiScreen.GuiScreen.__init__(self)
        self.cr = cr
        self.loginInterface = self.cr.loginInterface
        self.userName = ''
        self.password = ''
        self.fsm = ClassicFSM.ClassicFSM('LoginScreen', [State.State('off', self.enterOff, self.exitOff, ['login', 'waitForLoginResponse']),
         State.State('login', self.enterLogin, self.exitLogin, ['waitForLoginResponse', 'login', 'showLoginFailDialog']),
         State.State('showLoginFailDialog', self.enterShowLoginFailDialog, self.exitShowLoginFailDialog, ['login', 'showLoginFailDialog']),
         State.State('waitForLoginResponse', self.enterWaitForLoginResponse, self.exitWaitForLoginResponse, ['login', 'showLoginFailDialog', 'showConnectionProblemDialog']),
         State.State('showConnectionProblemDialog', self.enterShowConnectionProblemDialog, self.exitShowConnectionProblemDialog, ['login'])], 'off', 'off')
        self.fsm.enterInitialState()

    def load(self):
        self.notify.debug('load')
        masterScale = 0.8
        textScale = 0.1 * masterScale
        entryScale = 0.08 * masterScale
        lineHeight = 0.21 * masterScale
        buttonScale = 1.15 * masterScale
        buttonLineHeight = 0.14 * masterScale
        self.frame = DirectFrame(parent=aspect2d, relief=None, sortOrder=20)
        self.frame.hide()
        linePos = -0.26
        self.nameLabel = DirectLabel(parent=self.frame, relief=None, pos=(-0.21, 0, linePos), text=OTPLocalizer.LoginScreenUserName, text_scale=textScale, text_align=TextNode.ARight)
        self.nameEntry = DirectEntry(parent=self.frame, relief=DGG.SUNKEN, borderWidth=(0.1, 0.1), scale=entryScale, pos=(-0.125, 0.0, linePos), width=OTPGlobals.maxLoginWidth, numLines=1, focus=0, cursorKeys=1)
        linePos -= lineHeight
        self.passwordLabel = DirectLabel(parent=self.frame, relief=None, pos=(-0.21, 0, linePos), text=OTPLocalizer.LoginScreenPassword, text_scale=textScale, text_align=TextNode.ARight)
        self.passwordEntry = DirectEntry(parent=self.frame, relief=DGG.SUNKEN, borderWidth=(0.1, 0.1), scale=entryScale, pos=(-0.125, 0.0, linePos), width=OTPGlobals.maxLoginWidth, numLines=1, focus=0, cursorKeys=1, obscured=1, command=self.__handleLoginPassword)
        linePos -= lineHeight
        buttonImageScale = (1.7, 1.1, 1.1)
        self.loginButton = DirectButton(parent=self.frame, relief=DGG.RAISED, borderWidth=(0.01, 0.01), pos=(0, 0, linePos), scale=buttonScale, text=OTPLocalizer.LoginScreenLogin, text_scale=0.06, text_pos=(0, -0.02), command=self.__handleLoginButton)
        linePos -= buttonLineHeight
        self.createAccountButton = DirectButton(parent=self.frame, relief=DGG.RAISED, borderWidth=(0.01, 0.01), pos=(0, 0, linePos), scale=buttonScale, text=OTPLocalizer.LoginScreenCreateAccount, text_scale=0.06, text_pos=(0, -0.02), command=self.__handleCreateAccount)
        linePos -= buttonLineHeight
        self.quitButton = DirectButton(parent=self.frame, relief=DGG.RAISED, borderWidth=(0.01, 0.01), pos=(0, 0, linePos), scale=buttonScale, text=OTPLocalizer.LoginScreenQuit, text_scale=0.06, text_pos=(0, -0.02), command=self.__handleQuit)
        linePos -= buttonLineHeight
        self.dialogDoneEvent = 'loginDialogAck'
        dialogClass = OTPGlobals.getGlobalDialogClass()
        self.dialog = dialogClass(dialogName='loginDialog', doneEvent=self.dialogDoneEvent, message='', style=OTPDialog.Acknowledge, sortOrder=DGG.NO_FADE_SORT_INDEX + 100)
        self.dialog.hide()
        self.failDialog = DirectFrame(parent=aspect2dp, relief=DGG.RAISED, borderWidth=(0.01, 0.01), pos=(0, 0.1, 0), text='', text_scale=0.08, text_pos=(0.0, 0.3), text_wordwrap=15, sortOrder=DGG.NO_FADE_SORT_INDEX)
        linePos = -.05
        self.failTryAgainButton = DirectButton(parent=self.failDialog, relief=DGG.RAISED, borderWidth=(0.01, 0.01), pos=(0, 0, linePos), scale=0.9, text=OTPLocalizer.LoginScreenTryAgain, text_scale=0.06, text_pos=(0, -.02), command=self.__handleFailTryAgain)
        linePos -= buttonLineHeight
        self.failCreateAccountButton = DirectButton(parent=self.failDialog, relief=DGG.RAISED, borderWidth=(0.01, 0.01), pos=(0, 0, linePos), scale=0.9, text=OTPLocalizer.LoginScreenCreateAccount, text_scale=0.06, text_pos=(0, -.02), command=self.__handleFailCreateAccount)
        linePos -= buttonLineHeight
        self.failDialog.hide()
        self.connectionProblemDialogDoneEvent = 'loginConnectionProblemDlgAck'
        dialogClass = OTPGlobals.getGlobalDialogClass()
        self.connectionProblemDialog = dialogClass(dialogName='connectionProblemDialog', doneEvent=self.connectionProblemDialogDoneEvent, message='', style=OTPDialog.Acknowledge, sortOrder=DGG.NO_FADE_SORT_INDEX + 100)
        self.connectionProblemDialog.hide()
        return

    def unload(self):
        self.notify.debug('unload')
        self.nameEntry.destroy()
        self.passwordEntry.destroy()
        self.failTryAgainButton.destroy()
        self.failCreateAccountButton.destroy()
        self.createAccountButton.destroy()
        self.loginButton.destroy()
        self.quitButton.destroy()
        self.dialog.cleanup()
        del self.dialog
        self.failDialog.destroy()
        del self.failDialog
        self.connectionProblemDialog.cleanup()
        del self.connectionProblemDialog
        self.frame.destroy()
        del self.fsm
        del self.loginInterface
        del self.cr

    def enter(self):
        if self.cr.blue:
            self.userName = 'blue'
            self.password = self.cr.blue
            self.fsm.request('waitForLoginResponse')
        elif self.cr.playToken:
            self.userName = '*'
            self.password = self.cr.playToken
            self.fsm.request('waitForLoginResponse')
        elif hasattr(self.cr, 'DISLToken') and self.cr.DISLToken:
            self.userName = '*'
            self.password = self.cr.DISLToken
            self.fsm.request('waitForLoginResponse')
        elif self.AutoLoginName:
            self.userName = self.AutoLoginName
            self.password = self.AutoLoginPassword
            self.fsm.request('waitForLoginResponse')
        else:
            self.fsm.request('login')

    def exit(self):
        self.frame.hide()
        self.ignore(self.dialogDoneEvent)
        self.fsm.requestFinalState()

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def enterLogin(self):
        self.cr.resetPeriodTimer(None)
        self.userName = ''
        self.password = ''
        self.userName = launcher.getLastLogin()
        if self.userName and self.nameEntry.get():
            if self.userName != self.nameEntry.get():
                self.userName = ''
        self.frame.show()
        self.nameEntry.enterText(self.userName)
        self.passwordEntry.enterText(self.password)
        self.focusList = [self.nameEntry, self.passwordEntry]
        focusIndex = 0
        if self.userName:
            focusIndex = 1
        self.startFocusMgmt(startFocus=focusIndex)
        return

    def exitLogin(self):
        self.stopFocusMgmt()

    def enterShowLoginFailDialog(self, msg):
        base.transitions.fadeScreen(0.5)
        self.failDialog['text'] = msg
        self.failDialog.show()

    def __handleFailTryAgain(self):
        self.fsm.request('login')

    def __handleFailCreateAccount(self):
        messenger.send(self.doneEvent, [{'mode': 'createAccount'}])

    def __handleFailNoNewAccountsAck(self):
        self.dialog.hide()
        self.fsm.request('showLoginFailDialog', [self.failDialog['text']])

    def exitShowLoginFailDialog(self):
        base.transitions.noTransitions()
        self.failDialog.hide()

    def __handleLoginPassword(self, password):
        if password != '':
            if self.nameEntry.get() != '':
                self.__handleLoginButton()

    def __handleLoginButton(self):
        self.removeFocus()
        self.userName = self.nameEntry.get()
        self.password = self.passwordEntry.get()
        if self.userName == '':
            self.dialog.setMessage(OTPLocalizer.LoginScreenLoginPrompt)
            self.dialog.show()
            self.acceptOnce(self.dialogDoneEvent, self.__handleEnterLoginAck)
        else:
            self.fsm.request('waitForLoginResponse')

    def __handleQuit(self):
        self.removeFocus()
        messenger.send(self.doneEvent, [{'mode': 'quit'}])

    def __handleCreateAccount(self):
        self.removeFocus()
        messenger.send(self.doneEvent, [{'mode': 'createAccount'}])

    def enterWaitForLoginResponse(self):
        self.cr.handler = self.handleWaitForLoginResponse
        self.cr.userName = self.userName
        self.cr.password = self.password
        try:
            error = self.loginInterface.authorize(self.userName, self.password)
        except TTAccount.TTAccountException as e:
            self.fsm.request('showConnectionProblemDialog', [str(e)])
            return

        if error:
            self.notify.info(error)
            freeTimeExpired = self.loginInterface.getErrorCode() == 10
            if freeTimeExpired:
                self.cr.logAccountInfo()
                messenger.send(self.doneEvent, [{'mode': 'freeTimeExpired'}])
            else:
                self.fsm.request('showLoginFailDialog', [error])
        else:
            self.loginInterface.sendLoginMsg()
            self.waitForDatabaseTimeout(requestName='WaitForLoginResponse')

    def exitWaitForLoginResponse(self):
        self.cleanupWaitingForDatabase()
        self.cr.handler = None
        return

    def enterShowConnectionProblemDialog(self, msg):
        self.connectionProblemDialog.setMessage(msg)
        self.connectionProblemDialog.show()
        self.acceptOnce(self.connectionProblemDialogDoneEvent, self.__handleConnectionProblemAck)

    def __handleConnectionProblemAck(self):
        self.connectionProblemDialog.hide()
        self.fsm.request('login')

    def exitShowConnectionProblemDialog(self):
        pass

    if not config.GetBool('astron-support', True):
        def handleWaitForLoginResponse(self, msgType, di):
            if msgType == CLIENT_LOGIN_2_RESP:
                self.handleLoginResponseMsg2(di)
            elif msgType == CLIENT_LOGIN_RESP:
                self.handleLoginResponseMsg(di)
            elif msgType == CLIENT_LOGIN_3_RESP:
                self.handleLoginResponseMsg3(di)
            elif msgType == CLIENT_LOGIN_TOONTOWN_RESP:
                self.handleLoginToontownResponse(di)
            else:
                self.cr.handleMessageType(msgType, di)
    else:
        def handleWaitForLoginResponse(self, msgType, di):
            if msgType == CLIENT_HELLO_RESP:
                self.handleHelloResp()
            else:
                self.cr.handleMessageType(msgType, di)

        def handleHelloResp(self):
            self.cr.startHeartbeat()
            self.cr.astronLoginManager.handleRequestLogin()

    def getExtendedErrorMsg(self, errorString):
        prefix = 'Bad DC Version Compare'
        if len(errorString) < len(prefix):
            return errorString
        if errorString[:len(prefix)] == prefix:
            return '%s%s' % (errorString, ', address=%s' % base.cr.getServerAddress())
        return errorString

    def handleLoginResponseMsg3(self, di):
        now = time.time()
        returnCode = di.getInt8()
        errorString = self.getExtendedErrorMsg(di.getString())
        self.notify.info('Login response return code %s' % returnCode)
        if returnCode != 0:
            self.notify.info('Login failed: %s' % errorString)
            messenger.send(self.doneEvent, [{'mode': 'reject'}])
            return
        accountDetailRecord = AccountDetailRecord()
        accountDetailRecord.openChatEnabled = di.getString() == 'YES'
        accountDetailRecord.createFriendsWithChat = di.getString() == 'YES'
        chatCodeCreation = di.getString()
        accountDetailRecord.chatCodeCreation = chatCodeCreation == 'YES'
        parentControlledChat = chatCodeCreation == 'PARENT'
        access = di.getString()
        if access == 'VELVET':
            access = OTPGlobals.AccessVelvetRope
        elif access == 'FULL':
            access = OTPGlobals.AccessFull
        else:
            self.notify.warning('Unknown access: %s' % access)
            access = OTPGlobals.AccessUnknown
        accountDetailRecord.piratesAccess = access
        accountDetailRecord.familyAccountId = di.getInt32()
        accountDetailRecord.playerAccountId = di.getInt32()
        accountDetailRecord.playerName = di.getString()
        accountDetailRecord.playerNameApproved = di.getInt8()
        accountDetailRecord.maxAvatars = di.getInt32()
        self.cr.openChatAllowed = accountDetailRecord.openChatEnabled
        self.cr.secretChatAllowed = accountDetailRecord.chatCodeCreation or parentControlledChat
        self.cr.setIsPaid(accountDetailRecord.piratesAccess)
        self.userName = accountDetailRecord.playerName
        self.cr.userName = accountDetailRecord.playerName
        accountDetailRecord.numSubs = di.getUint16()
        for i in range(accountDetailRecord.numSubs):
            subDetailRecord = SubDetailRecord()
            subDetailRecord.subId = di.getUint32()
            subDetailRecord.subOwnerId = di.getUint32()
            subDetailRecord.subName = di.getString()
            subDetailRecord.subActive = di.getString()
            access = di.getString()
            if access == 'VELVET':
                access = OTPGlobals.AccessVelvetRope
            elif access == 'FULL':
                access = OTPGlobals.AccessFull
            else:
                access = OTPGlobals.AccessUnknown
            subDetailRecord.subAccess = access
            subDetailRecord.subLevel = di.getUint8()
            subDetailRecord.subNumAvatars = di.getUint8()
            subDetailRecord.subNumConcur = di.getUint8()
            subDetailRecord.subFounder = di.getString() == 'YES'
            accountDetailRecord.subDetails[subDetailRecord.subId] = subDetailRecord

        accountDetailRecord.WLChatEnabled = di.getString() == 'YES'
        if accountDetailRecord.WLChatEnabled:
            self.cr.whiteListChatEnabled = 1
        else:
            self.cr.whiteListChatEnabled = 0
        self.notify.info('End of DISL token parse')
        if base.logPrivateInfo:
            self.notify.info('accountDetailRecord: %s' % accountDetailRecord)
        self.cr.accountDetailRecord = accountDetailRecord
        self.__handleLoginSuccess()

    def handleLoginResponseMsg2(self, di):
        self.notify.debug('handleLoginResponseMsg2')
        if base.logPrivateInfo:
            if self.notify.getDebug():
                dgram = di.getDatagram()
                dgram.dumpHex(ostream)
        now = time.time()
        returnCode = di.getUint8()
        errorString = self.getExtendedErrorMsg(di.getString())
        self.userName = di.getString()
        self.cr.userName = self.userName
        accountDetailRecord = AccountDetailRecord()
        self.cr.accountDetailRecord = accountDetailRecord
        canChat = di.getUint8()
        self.cr.secretChatAllowed = canChat
        if base.logPrivateInfo:
            self.notify.info('Chat from game server login: %s' % canChat)
        sec = di.getUint32()
        usec = di.getUint32()
        serverTime = sec + usec / 1000000.0
        self.cr.serverTimeUponLogin = serverTime
        self.cr.clientTimeUponLogin = now
        self.cr.globalClockRealTimeUponLogin = globalClock.getRealTime()
        if hasattr(self.cr, 'toontownTimeManager'):
            self.cr.toontownTimeManager.updateLoginTimes(serverTime, now, self.cr.globalClockRealTimeUponLogin)
        serverDelta = serverTime - now
        self.cr.setServerDelta(serverDelta)
        self.notify.setServerDelta(serverDelta, 28800)
        self.isPaid = di.getUint8()
        self.cr.setIsPaid(self.isPaid)
        if self.isPaid:
            launcher.setPaidUserLoggedIn()
        if base.logPrivateInfo:
            self.notify.info('Paid from game server login: %s' % self.isPaid)
        self.cr.resetPeriodTimer(None)
        if di.getRemainingSize() >= 4:
            minutesRemaining = di.getInt32()
            if base.logPrivateInfo:
                self.notify.info('Minutes remaining from server %s' % minutesRemaining)
            if base.logPrivateInfo:
                if minutesRemaining >= 0:
                    self.notify.info('Spawning period timer')
                    self.cr.resetPeriodTimer(minutesRemaining * 60)
                elif self.isPaid:
                    self.notify.warning('Negative minutes remaining for paid user (?)')
                else:
                    self.notify.warning('Not paid, but also negative minutes remaining (?)')
        elif base.logPrivateInfo:
            self.notify.info('Minutes remaining not returned from server; not spawning period timer')
        familyStr = di.getString()
        WhiteListResponse = di.getString()
        if WhiteListResponse == 'YES':
            self.cr.whiteListChatEnabled = 1
        else:
            self.cr.whiteListChatEnabled = 0
        if di.getRemainingSize() > 0:
            self.cr.accountDays = self.parseAccountDays(di.getInt32())
        else:
            self.cr.accountDays = 100000
        if di.getRemainingSize() > 0:
            self.lastLoggedInStr = di.getString()
            self.notify.info('last logged in = %s' % self.lastLoggedInStr)
        else:
            self.lastLoggedInStr = ''
        self.cr.lastLoggedIn = datetime.now()
        if hasattr(self.cr, 'toontownTimeManager'):
            self.cr.lastLoggedIn = self.cr.toontownTimeManager.convertStrToToontownTime(self.lastLoggedInStr)
        self.cr.withParentAccount = False
        self.notify.info('Login response return code %s' % returnCode)
        if returnCode == 0:
            self.__handleLoginSuccess()
        elif returnCode == -13:
            self.notify.info('Period Time Expired')
            self.fsm.request('showLoginFailDialog', [OTPLocalizer.LoginScreenPeriodTimeExpired])
        else:
            self.notify.info('Login failed: %s' % errorString)
            messenger.send(self.doneEvent, [{'mode': 'reject'}])
        return

    def handleLoginResponseMsg(self, di):
        self.notify.debug('handleLoginResponseMsg1')
        if base.logPrivateInfo:
            if self.notify.getDebug():
                dgram = di.getDatagram()
                dgram.dumpHex(ostream)
        now = time.time()
        accountDetailRecord = AccountDetailRecord()
        self.cr.accountDetailRecord = accountDetailRecord
        returnCode = di.getUint8()
        accountCode = di.getUint32()
        errorString = self.getExtendedErrorMsg(di.getString())
        sec = di.getUint32()
        usec = di.getUint32()
        serverTime = sec + usec / 1000000.0
        serverDelta = serverTime - now
        self.cr.serverTimeUponLogin = serverTime
        self.cr.clientTimeUponLogin = now
        self.cr.globalClockRealTimeUponLogin = globalClock.getRealTime()
        if hasattr(self.cr, 'toontownTimeManager'):
            self.cr.toontownTimeManager.updateLoginTimes(serverTime, now, self.cr.globalClockRealTimeUponLogin)
        self.cr.setServerDelta(serverDelta)
        self.notify.setServerDelta(serverDelta, 28800)
        if di.getRemainingSize() > 0:
            self.cr.accountDays = self.parseAccountDays(di.getInt32())
        else:
            self.cr.accountDays = 100000
        if di.getRemainingSize() > 0:
            WhiteListResponse = di.getString()
        else:
            WhiteListResponse = 'NO'
        if WhiteListResponse == 'YES':
            self.cr.whiteListChatEnabled = 1
        else:
            self.cr.whiteListChatEnabled = 0
        self.lastLoggedInStr = base.config.GetString('last-logged-in', '')
        self.cr.lastLoggedIn = datetime.now()
        if hasattr(self.cr, 'toontownTimeManager'):
            self.cr.lastLoggedIn = self.cr.toontownTimeManager.convertStrToToontownTime(self.lastLoggedInStr)
        self.cr.withParentAccount = base.config.GetBool('dev-with-parent-account', 0)
        self.notify.info('Login response return code %s' % returnCode)
        if returnCode == 0:
            self.__handleLoginSuccess()
        elif returnCode == 12:
            self.notify.info('Bad password')
            self.fsm.request('showLoginFailDialog', [OTPLocalizer.LoginScreenBadPassword])
        elif returnCode == 14:
            self.notify.info('Bad word in user name')
            self.fsm.request('showLoginFailDialog', [OTPLocalizer.LoginScreenInvalidUserName])
        elif returnCode == 129:
            self.notify.info('Username not found')
            self.fsm.request('showLoginFailDialog', [OTPLocalizer.LoginScreenUserNameNotFound])
        else:
            self.notify.info('Login failed: %s' % errorString)
            messenger.send(self.doneEvent, [{'mode': 'reject'}])

    def __handleLoginSuccess(self):
        self.cr.logAccountInfo()
        launcher.setGoUserName(self.userName)
        launcher.setLastLogin(self.userName)
        launcher.setUserLoggedIn()
        if self.loginInterface.freeTimeExpires == -1:
            launcher.setPaidUserLoggedIn()
        if self.loginInterface.needToSetParentPassword():
            messenger.send(self.doneEvent, [{'mode': 'getChatPassword'}])
        else:
            messenger.send(self.doneEvent, [{'mode': 'success'}])

    def __handleEnterLoginAck(self):
        self.dialog.hide()
        self.fsm.request('login')

    def __handleNoNewAccountsAck(self):
        self.dialog.hide()
        self.fsm.request('login')

    def parseAccountDays(self, accountDays):
        result = 100000
        if accountDays >= 0:
            result = accountDays
        else:
            self.notify.warning('account days is negative %s' % accountDays)
        self.notify.debug('result=%s' % result)
        return result

    if not config.GetBool('astron-support', True):
        def handleLoginToontownResponse(self, di):
            self.notify.debug("handleLoginToontownResponse")
            if 1:
                if base.logPrivateInfo:
                    dgram = di.getDatagram()
                    dgram.dumpHex(ostream)
            now = time.time()
            returnCode = di.getUint8()
            respString = di.getString()
            errorString = self.getExtendedErrorMsg(respString)
            self.accountNumber = di.getUint32()
            self.cr.DISLIdFromLogin = self.accountNumber
            self.accountName = di.getString()
            self.accountNameApproved = di.getUint8()
            accountDetailRecord = AccountDetailRecord()
            self.cr.accountDetailRecord = accountDetailRecord
            self.openChatEnabled = di.getString() == "YES"
            createFriendsWithChat = di.getString()
            canChat = createFriendsWithChat == "YES" or createFriendsWithChat == "CODE"
            self.cr.secretChatAllowed = canChat
            if base.logPrivateInfo:
                self.notify.info("CREATE_FRIENDS_WITH_CHAT from game server login: %s %s" % (createFriendsWithChat, canChat))
            self.chatCodeCreationRule = di.getString()
            self.cr.chatChatCodeCreationRule = self.chatCodeCreationRule
            if base.logPrivateInfo:
                self.notify.info("Chat code creation rule = %s" % self.chatCodeCreationRule)
            self.cr.secretChatNeedsParentPassword = self.chatCodeCreationRule == "PARENT"
            sec = di.getUint32()
            usec = di.getUint32()
            serverTime = sec + (usec/1000000.0)
            self.cr.serverTimeUponLogin = serverTime
            self.cr.clientTimeUponLogin = now
            self.cr.globalClockRealTimeUponLogin = globalClock.getRealTime()
            if hasattr(self.cr, "toontownTimeManager"):
                self.cr.toontownTimeManager.updateLoginTimes(serverTime, now, self.cr.globalClockRealTimeUponLogin)
            serverDelta = serverTime - now
            self.cr.setServerDelta(serverDelta)
            self.notify.setServerDelta(serverDelta, 28800)
            access = di.getString()
            self.isPaid = access == "FULL"
            self.cr.parentPasswordSet = self.isPaid
            self.cr.setIsPaid(self.isPaid)
            if self.isPaid:
                launcher.setPaidUserLoggedIn()
            if base.logPrivateInfo:
                self.notify.info("Paid from game server login: %s" % self.isPaid)
            WhiteListResponse = di.getString()
            if WhiteListResponse == "YES":
                self.cr.whiteListChatEnabled = 1
            else:
                self.cr.whiteListChatEnabled = 0
            self.lastLoggedInStr = di.getString()
            self.cr.lastLoggedIn = datetime.now()
            if hasattr(self.cr, "toontownTimeManager"):
                self.cr.lastLoggedIn = self.cr.toontownTimeManager.convertStrToToontownTime(self.lastLoggedInStr)
            if di.getRemainingSize() > 0:
                self.cr.accountDays = self.parseAccountDays(di.getInt32())
            else:
                self.cr.accountDays = 100000
            self.toonAccountType = di.getString()
            if self.toonAccountType == "WITH_PARENT_ACCOUNT":
                self.cr.withParentAccount = True
            elif self.toonAccountType == "NO_PARENT_ACCOUNT":
                self.cr.withParentAccount = False
            else:
                self.notify.error("unknown toon account type %s" % self.toonAccountType)
            if base.logPrivateInfo:
                self.notify.info("toonAccountType=%s" % self.toonAccountType)
            self.userName = di.getString()
            self.cr.userName = self.userName
            self.notify.info("Login response return code %s" % returnCode)
            if returnCode == 0:
                self.__handleLoginSuccess()
            elif returnCode == -13:
                self.notify.info("Period Time Expired")
                self.fsm.request("showLoginFailDialog", [OTPLocalizer.LoginScreenPeriodTimeExpired])
            else:
                self.notify.info("Login failed: %s" % errorString)
                messenger.send(self.doneEvent, [{'mode': 'reject'}])
    else:
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
                self.__handleLoginSuccess()
            elif returnCode == -13:
                self.notify.info("Period Time Expired")
                self.fsm.request("showLoginFailDialog", [OTPLocalizer.LoginScreenPeriodTimeExpired])
            else:
                self.notify.info("Login failed: %s" % errorString)
                messenger.send(self.doneEvent, [{'mode': 'reject'}])
