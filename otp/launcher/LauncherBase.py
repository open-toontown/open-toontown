import sys
import os
import time
import builtins
from panda3d.core import *
from direct.showbase import DConfig
from direct.showbase.DirectObject import DirectObject
from direct.task.MiniTask import MiniTaskManager
from direct.directnotify.DirectNotifyGlobal import *

class LogAndOutput:

    def __init__(self, orig, log):
        self.orig = orig
        self.log = log
        self.console = False

    def write(self, str):
        self.log.write(str)
        self.log.flush()
        if self.console:
            self.orig.write(str)
            self.orig.flush()

    def flush(self):
        self.log.flush()
        self.orig.flush()


class LauncherBase(DirectObject):
    GameName = 'game'
    GameLogFilenameKey = 'GAMELOG_FILENAME'
    PandaWindowOpenKey = 'PANDA_WINDOW_OPEN'
    PandaErrorCodeKey = 'PANDA_ERROR_CODE'
    LastLoginKey = 'LAST_LOGIN'
    UserLoggedInKey = 'USER_LOGGED_IN'
    PaidUserLoggedInKey = 'PAID_USER_LOGGED_IN'
    ReferrerKey = 'REFERRER_CODE'
    PeriodTimeRemainingKey = 'PERIOD_TIME_REMAINING'
    DISLTokenKey = 'DISLTOKEN'

    def __init__(self):
        self.started = False
        self.taskMgrStarted = False
        self._downloadComplete = True
        self.pandaErrorCode = 0
        ltime = time.localtime()
        logSuffix = '%02d%02d%02d_%02d%02d%02d' % (ltime[0] - 2000,
            ltime[1],
            ltime[2],
            ltime[3],
            ltime[4],
            ltime[5])
        logPrefix = self.getLogFileName() + '-'
        if not os.path.exists('logs/'):
            os.makedirs('logs/')
        logfile = os.path.join('logs', logPrefix + logSuffix + '.log')
        self.errorfile = 'errorCode'
        log = open(logfile, 'a')
        logOut = LogAndOutput(sys.__stdout__, log)
        logErr = LogAndOutput(sys.__stderr__, log)
        sys.stdout = logOut
        sys.stderr = logErr
        print('\n\nStarting %s...' % self.GameName)
        print('Current time: ' + time.asctime(time.localtime(time.time())) + ' ' + time.tzname[0])
        print('sys.path = ', sys.path)
        print('sys.argv = ', sys.argv)
        if ConfigVariableBool('log-private-info', 0).value:
            print('os.environ = ', os.environ)
        self.miniTaskMgr = MiniTaskManager()
        self.nout = MultiplexStream()
        Notify.ptr().setOstreamPtr(self.nout, 0)
        self.nout.addFile(Filename(logfile))
        if ConfigVariableBool('console-output', 0).value:
            self.nout.addStandardOutput()
            sys.stdout.console = True
            sys.stderr.console = True
        self.notify = directNotify.newCategory('Launcher')
        self.logPrefix = logPrefix
        self.testServerFlag = self.getTestServerFlag()
        self.notify.info('isTestServer: %s' % self.testServerFlag)
        gameServer = self.getGameServer() or '127.0.0.1'
        self.notify.info('Game Server %s' % gameServer)
        self.goUserName = ''
        self.lastLauncherMsg = None
        self.setRegistry(self.GameLogFilenameKey, logfile)
        self.showPhase = 3.5
        self.currentPhase = 4
        serverVersion = ConfigVariableString('server-version', 'no_version_set').value
        if serverVersion == 'no_version_set':
            self.setPandaErrorCode(10)
            self.notify.info('Aborting, config did not load!')
            sys.exit()
        self.launcherMessage(self.Localizer.LauncherStartingMessage)
        self.http = HTTPClient()
        self.foreground()

    def isDummy(self):
        return 0

    def background(self):
        self.notify.info('background: Launcher now operating in background')
        self.backgrounded = 1

    def foreground(self):
        self.notify.info('foreground: Launcher now operating in foreground')
        self.backgrounded = 0

    def setRegistry(self, key, value):
        self.notify.info('DEPRECATED setRegistry: %s = %s' % (key, value))

    def getRegistry(self, key):
        self.notify.info('DEPRECATED getRegistry: %s' % key)
        return None

    def maybeStartGame(self):
        if not self.started and self.currentPhase >= self.showPhase:
            self.started = True
            self.notify.info('maybeStartGame: starting game')
            self.launcherMessage(self.Localizer.LauncherStartingGame)
            self.background()
            builtins.launcher = self
            self.startGame()
            self.cleanup()

    def _runTaskManager(self):
        if not self.taskMgrStarted:
            self.miniTaskMgr.run()
            self.notify.info('Switching task managers.')
        taskMgr.run()

    def _stepMiniTaskManager(self, task):
        self.miniTaskMgr.step()
        if self.miniTaskMgr.taskList:
            return task.cont
        self.notify.info('Stopping mini task manager.')
        self.miniTaskMgr = None
        return task.done

    def newTaskManager(self):
        self.taskMgrStarted = True
        if self.miniTaskMgr.running:
            self.miniTaskMgr.stop()
        from direct.task.TaskManagerGlobal import taskMgr
        taskMgr.remove('miniTaskManager')
        taskMgr.add(self._stepMiniTaskManager, 'miniTaskManager')

    def mainLoop(self):
        try:
            self._runTaskManager()
        except SystemExit:
            if hasattr(builtins, 'base'):
                base.destroy()
            self.notify.info('Normal exit.')
            raise
        except:
            self.setPandaErrorCode(12)
            self.notify.warning('Handling Python exception.')
            if hasattr(builtins, 'base') and getattr(base, 'cr', None):
                if base.cr.timeManager:
                    from otp.otpbase import OTPGlobals
                    base.cr.timeManager.setDisconnectReason(OTPGlobals.DisconnectPythonError)
                    base.cr.timeManager.setExceptionInfo()
                base.cr.sendDisconnect()
            if hasattr(builtins, 'base'):
                base.destroy()
            self.notify.info('Exception exit.\n')
            import traceback
            traceback.print_exc()
            sys.exit()

    def isDownloadComplete(self):
        return self._downloadComplete

    def launcherMessage(self, msg):
        if msg != self.lastLauncherMsg:
            self.lastLauncherMsg = msg
            self.notify.info(msg)

    def isTestServer(self):
        return self.testServerFlag

    def recordPeriodTimeRemaining(self, secondsRemaining):
        self.setValue(self.PeriodTimeRemainingKey, int(secondsRemaining))

    def getGoUserName(self):
        return self.goUserName

    def setGoUserName(self, userName):
        self.goUserName = userName

    def setPandaWindowOpen(self):
        self.setValue(self.PandaWindowOpenKey, 1)

    def setPandaErrorCode(self, code):
        self.notify.info('setting panda error code to %s' % code)
        self.pandaErrorCode = code
        errorLog = open(self.errorfile, 'w')
        errorLog.write(str(code) + '\n')
        errorLog.flush()
        errorLog.close()

    def getPandaErrorCode(self):
        return self.pandaErrorCode

    def setDisconnectDetailsNormal(self):
        self.notify.info('Setting Disconnect Details normal')
        self.disconnectCode = 0
        self.disconnectMsg = 'normal'

    def setDisconnectDetails(self, newCode, newMsg):
        self.notify.info('New Disconnect Details: %s - %s ' % (newCode, newMsg))
        self.disconnectCode = newCode
        self.disconnectMsg = newMsg

    def getLastLogin(self):
        return self.getValue(self.LastLoginKey, '')

    def setLastLogin(self, login):
        self.setValue(self.LastLoginKey, login)

    def setUserLoggedIn(self):
        self.setValue(self.UserLoggedInKey, '1')

    def setPaidUserLoggedIn(self):
        self.setValue(self.PaidUserLoggedInKey, '1')

    def getReferrerCode(self):
        return self.getValue(self.ReferrerKey, None)

    def getPhaseComplete(self, phase):
        return True

    def getPercentPhaseComplete(self, phase):
        return 100

    def cleanup(self):
        self.notify.info('cleanup: cleaning up Launcher')
        self.ignoreAll()
        del self.http

    def getBlue(self):
        return None

    def getPlayToken(self):
        return None

    def getDISLToken(self):
        DISLToken = self.getValue(self.DISLTokenKey)
        self.setValue(self.DISLTokenKey, '')
        if DISLToken == 'NO DISLTOKEN':
            DISLToken = None
        return DISLToken
