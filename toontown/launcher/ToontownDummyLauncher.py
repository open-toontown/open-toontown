from direct.directnotify import DirectNotifyGlobal
from otp.launcher.DummyLauncherBase import DummyLauncherBase
from toontown.launcher.ToontownLauncher import ToontownLauncher

class ToontownDummyLauncher(DummyLauncherBase, ToontownLauncher):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownDummyLauncher')

    def __init__(self):
        DummyLauncherBase.__init__(self)
        self.setPhaseComplete(1, 100)
        self.setPhaseComplete(2, 100)
        self.setPhaseComplete(3, 100)
        self.windowOpen = 0
        self.firstPhase = 3.5
        self.goUserName = ''
        self.periodTimeRemainingKey = 'PERIOD_TIME_REMAINING'
        self.reg = {}
        self.startFakeDownload()

    def getReferrerCode(self):
        return None

    def setRegistry(self, name, value):
        print('setRegistry[%s] = %s' % (name, value))
        self.reg[name] = value

    def getRegistry(self, name, defaultValue = None):
        if name in self.reg:
            value = self.reg[name]
        else:
            value = defaultValue
        print('getRegistry[%s] = %s' % (name, value))
        return value

    def getGame2Done(self):
        return 1

    def recordPeriodTimeRemaining(self, secondsRemaining):
        self.setRegistry(self.periodTimeRemainingKey, secondsRemaining)

    def getGoUserName(self):
        return self.goUserName

    def setGoUserName(self, userName):
        self.goUserName = userName

    def getParentPasswordSet(self):
        return 0

    def getNeedPwForSecretKey(self):
        return 0
