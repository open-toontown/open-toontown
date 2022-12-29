import os
from direct.showbase.EventManagerGlobal import *
from panda3d.core import *
from otp.launcher.LauncherBase import LauncherBase
from toontown.toonbase import TTLocalizer

class QuickLauncher(LauncherBase):
    GameName = 'Toontown'
    Localizer = TTLocalizer

    def __init__(self):
        print('Running: ToontownQuickLauncher')
        self.toontownBlueKey = 'TOONTOWN_BLUE'
        LauncherBase.__init__(self)
        self.useTTSpecificLogin = ConfigVariableBool('tt-specific-login', 0).value
        if self.useTTSpecificLogin:
            self.toontownPlayTokenKey = 'LOGIN_TOKEN'
        else:
            self.toontownPlayTokenKey = 'PLAYTOKEN'
        print('useTTSpecificLogin=%s' % self.useTTSpecificLogin)
        self.secretNeedsParentPasswordKey = False
        self.chatEligibleKey = True
        self.showPhase = -1
        self.maybeStartGame()
        self.mainLoop()

    def getValue(self, key, default = None):
        return os.environ.get(key, default)

    def setValue(self, key, value):
        os.environ[key] = str(value)

    def getTestServerFlag(self):
        return self.getValue('IS_TEST_SERVER', 0)

    def getGameServer(self):
        return self.getValue('GAME_SERVER', '')

    def getLogFileName(self):
        return 'toontown'

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
        pass

    def getRegistry(self, name, missingValue = None):
        self.notify.info('getRegistry %s' % ((name, missingValue),))
        self.notify.info('checking env' % os.environ)
        if missingValue == None:
            missingValue = ''
        value = os.environ.get(name, missingValue)
        try:
            value = int(value)
        except:
            pass

        return value

    def getGame2Done(self):
        return True

    def getNeedPwForSecretKey(self):
        if self.useTTSpecificLogin:
            self.notify.info('getNeedPwForSecretKey using tt-specific-login')
            try:
                if base.cr.chatChatCodeCreationRule == 'PARENT':
                    return True
                else:
                    return False
            except:
                return True

        else:
            return self.secretNeedsParentPasswordKey

    def getParentPasswordSet(self):
        if self.useTTSpecificLogin:
            self.notify.info('getParentPasswordSet using tt-specific-login')
            try:
                if base.cr.isPaid():
                    return True
                else:
                    return False
            except:
                return False

        else:
            return self.chatEligibleKey

    def startGame(self):
        self.newTaskManager()
        eventMgr.restart()
        from toontown.toonbase import ToontownStart
