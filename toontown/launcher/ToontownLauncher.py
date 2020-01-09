import os
import sys
import time

ltime = 1 and time.localtime()
logSuffix = '%02d%02d%02d_%02d%02d%02d' % (ltime[0] - 2000,  ltime[1], ltime[2],
                                           ltime[3], ltime[4], ltime[5])

logfile = 'toontownD-' + logSuffix + '.log'

class LogAndOutput:
    def __init__(self, orig, log):
        self.orig = orig
        self.log = log

    def write(self, str):
        self.log.write(str)
        self.log.flush()
        self.orig.write(str)
        self.orig.flush()

    def flush(self):
        self.log.flush()
        self.orig.flush()

log = open(logfile, 'a')
logOut = LogAndOutput(sys.__stdout__, log)
logErr = LogAndOutput(sys.__stderr__, log)
sys.stdout = logOut
sys.stderr = logErr

print('\n\nStarting Toontown...')

if 1:
    print('Current time: ' + time.asctime(time.localtime(time.time())) + ' ' + time.tzname[0])
    print('sys.path = ', sys.path)
    print('sys.argv = ', sys.argv)

from otp.launcher.LauncherBase import LauncherBase
from otp.otpbase import OTPLauncherGlobals
from panda3d.core import *
from toontown.toonbase import TTLocalizer

class ToontownLauncher(LauncherBase):
    GameName = 'Toontown'
    LauncherPhases = [3, 3.5, 4, 5, 5.5, 6, 7, 8, 9, 10, 11, 12, 13]
    TmpOverallMap = [0.25, 0.15, 0.12, 0.17, 0.08, 0.07, 0.05, 0.05, 0.017,
                     0.011, 0.01, 0.012, 0.01]
    RegistryKey = 'Software\\Disney\\Disney Online\\Toontown'
    ForegroundSleepTime = 0.01
    Localizer = TTLocalizer
    VerifyFiles = 1
    DecompressMultifiles = True

    def __init__(self):
        if sys.argv[2] == 'Phase2.py':
            sys.argv = sys.argv[:1] + sys.argv[3:]
        if len(sys.argv) == 5 or len(sys.argv) == 6:
            self.gameServer = sys.argv[2]
            self.accountServer = sys.argv[3]
            self.testServerFlag = int(sys.argv[4])
        else:
            print('Error: Launcher: incorrect number of parameters')
            sys.exit()

        self.toontownBlueKey = 'TOONTOWN_BLUE'
        self.toontownPlayTokenKey = 'TOONTOWN_PLAYTOKEN'
        self.launcherMessageKey = 'LAUNCHER_MESSAGE'
        self.game1DoneKey = 'GAME1_DONE'
        self.game2DoneKey = 'GAME2_DONE'
        self.tutorialCompleteKey = 'TUTORIAL_DONE'
        self.toontownRegistryKey = 'Software\\Disney\\Disney Online\\Toontown'
        if self.testServerFlag:
            self.toontownRegistryKey = '%s%s' % (self.toontownRegistryKey, 'Test')
        self.toontownRegistryKey = '%s%s' % (self.toontownRegistryKey, self.getProductName())
        LauncherBase.__init__(self)
        self.webAcctParams = 'WEB_ACCT_PARAMS'
        self.parseWebAcctParams()
        self.mainLoop()

    def getValue(self, key, default=None):
        try:
            return self.getRegistry(key, default)
        except:
            return self.getRegistry(key)

    def setValue(self, key, value):
        self.setRegistry(key, value)

    def getVerifyFiles(self):
        return 1

    def getTestServerFlag(self):
        return self.testServerFlag

    def getGameServer(self):
        return self.gameServer

    def getLogFileName(self):
        return 'toontown'

    def parseWebAcctParams(self):
        s = config.GetString('fake-web-acct-params', '')
        if not s:
            s = self.getRegistry(self.webAcctParams)
        self.setRegistry(self.webAcctParams, '')
        l = s.split('&')
        length = len(l)
        dict = {}
        for index in range(0, len(l)):
            args = l[index].split('=')
            if len(args) == 3:
                [name, value] = args[-2:]
                dict[name] = int(value)
            elif len(args) == 2:
                [name, value] = args
                dict[name] = int(value)

        self.secretNeedsParentPasswordKey = 1
        if 'secretsNeedsParentPassword' in dict:
            self.secretNeedsParentPasswordKey = dict['secretsNeedsParentPassword']
        else:
            self.notify.warning('no secretNeedsParentPassword token in webAcctParams')
        self.notify.info('secretNeedsParentPassword = %d' % self.secretNeedsParentPasswordKey)

        self.chatEligibleKey = 0
        if 'chatEligible' in dict:
            self.chatEligibleKey = dict['chatEligible']
        else:
            self.notify.warning('no chatEligible token in webAcctParams')
        self.notify.info('chatEligibleKey = %d' % self.chatEligibleKey)

    def getBlue(self):
        blue = self.getValue(self.toontownBlueKey)
        self.setValue(self.toontownBlueKey, '')
        if blue == 'NO BLUE':
            blue = None
        return blue

    def getPlayToken(self):
        playToken = self.getValue(self.toontownPlayTokenKey)
        self.setValue(self.toontownPlayTokenKey, '')
        if playToken == 'NO PLAYTOKEN':
            playToken = None
        return playToken

    def setRegistry(self, name, value):
        if not self.WIN32:
            return

        t = type(value)
        if t == int:
            WindowsRegistry.setIntValue(self.toontownRegistryKey, name, value)
        elif t == str:
            WindowsRegistry.setStringValue(self.toontownRegistryKey, name, value)
        else:
            self.notify.warning('setRegistry: Invalid type for registry value: ' + repr(value))

    def getRegistry(self, name, missingValue=None):
        self.notify.info('getRegistry%s' % ((name, missingValue),))
        if not self.WIN32:
            if missingValue == None:
                missingValue = ''
            value = os.environ.get(name, missingValue)
            try:
                value = int(value)
            except: pass
            return value

        t = WindowsRegistry.getKeyType(self.toontownRegistryKey, name)
        if t == WindowsRegistry.TInt:
            if missingValue == None:
                missingValue = 0
            return WindowsRegistry.getIntValue(self.toontownRegistryKey,
                                                name, missingValue)
        elif t == WindowsRegistry.TString:
            if missingValue == None:
                missingValue = ''
            return WindowsRegistry.getStringValue(self.toontownRegistryKey,
                                                    name, missingValue)
        else:
            return missingValue

    def getCDDownloadPath(self, origPath, serverFilePath):
        return '%s/%s%s/CD_%d/%s' % (origPath, self.ServerVersion, self.ServerVersionSuffix, self.fromCD, serverFilePath)

    def getDownloadPath(self, origPath, serverFilePath):
        return '%s/%s%s/%s' % (origPath, self.ServerVersion, self.ServerVersionSuffix, serverFilePath)

    def getPercentPatchComplete(self, bytesWritten):
        if self.totalPatchDownload:
            return LauncherBase.getPercentPatchComplete(self, bytesWritten)
        else:
            return 0

    def hashIsValid(self, serverHash, hashStr):
        return serverHash.setFromDec(hashStr) or serverHash.setFromHex(hashStr)

    def launcherMessage(self, msg):
        LauncherBase.launcherMessage(self, msg)
        self.setRegistry(self.launcherMessageKey, msg)

    def getAccountServer(self):
        return self.accountServer

    def setTutorialComplete(self):
        self.setRegistry(self.tutorialCompleteKey, 0)

    def getTutorialComplete(self):
        return self.getRegistry(self.tutorialCompleteKey, 0)

    def getGame2Done(self):
        return self.getRegistry(self.game2DoneKey, 0)

    def setPandaErrorCode(self, code):
        self.pandaErrorCode = code
        if self.WIN32:
            self.notify.info('setting panda error code to %s' % code)
            exitCode2exitPage = {
                OTPLauncherGlobals.ExitEnableChat: 'chat',
                OTPLauncherGlobals.ExitSetParentPassword: 'setparentpassword',
                OTPLauncherGlobals.ExitPurchase: 'purchase'}
            if code in exitCode2exitPage:
                self.setRegistry('EXIT_PAGE', exitCode2exitPage[code])
                self.setRegistry(self.PandaErrorCodeKey, 0)
            else:
                self.setRegistry(self.PandaErrorCodeKey, code)
        else:
            LauncherBase.setPandaErrorCode(self, code)

    def getNeedPwForSecretKey(self):
        return self.secretNeedsParentPasswordKey

    def getParentPasswordSet(self):
        return self.chatEligibleKey

    def MakeNTFSFilesGlobalWriteable(self, pathToSet=None):
        if not self.WIN32:
            return
        LauncherBase.MakeNTFSFilesGlobalWriteable(self, pathToSet)

    def startGame(self):
        try:
            os.remove('Phase3.py')
        except: pass

        import Phase3

        self.newTaskManager()

        from direct.showbase.EventManagerGlobal import eventMgr
        eventMgr.restart()

        from toontown.toonbase import ToontownStart
