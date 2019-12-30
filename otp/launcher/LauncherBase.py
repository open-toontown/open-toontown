import sys
import os
import time
import string
import builtins
from panda3d.core import *
from direct.showbase.MessengerGlobal import *
from direct.showbase.DirectObject import DirectObject
from direct.showbase.EventManagerGlobal import *
from direct.task.MiniTask import MiniTask, MiniTaskManager
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
    ArgCount = 6
    LauncherPhases = [1,
     2,
     3,
     4]
    TmpOverallMap = [0.25,
     0.25,
     0.25,
     0.25]
    BANDWIDTH_ARRAY = [1800,
     3600,
     4200,
     6600,
     8000,
     12000,
     16000,
     24000,
     32000,
     48000,
     72000,
     96000,
     128000,
     192000,
     250000,
     500000,
     750000,
     1000000,
     1250000,
     1500000,
     1750000,
     2000000,
     3000000,
     4000000,
     6000000,
     8000000,
     10000000,
     12000000,
     14000000,
     16000000,
     24000000,
     32000000,
     48000000,
     64000000,
     96000000,
     128000000,
     256000000,
     512000000,
     1024000000]
    win32con_FILE_PERSISTENT_ACLS = 8
    InstallDirKey = 'INSTALL_DIR'
    GameLogFilenameKey = 'GAMELOG_FILENAME'
    PandaWindowOpenKey = 'PANDA_WINDOW_OPEN'
    PandaErrorCodeKey = 'PANDA_ERROR_CODE'
    NewInstallationKey = 'IS_NEW_INSTALLATION'
    LastLoginKey = 'LAST_LOGIN'
    UserLoggedInKey = 'USER_LOGGED_IN'
    PaidUserLoggedInKey = 'PAID_USER_LOGGED_IN'
    ReferrerKey = 'REFERRER_CODE'
    PeriodTimeRemainingKey = 'PERIOD_TIME_REMAINING'
    PeriodNameKey = 'PERIOD_NAME'
    SwidKey = 'SWID'
    PatchCDKey = 'FROM_CD'
    DISLTokenKey = 'DISLTOKEN'
    ProxyServerKey = 'PROXY_SERVER'
    ProxyDirectHostsKey = 'PROXY_DIRECT_HOSTS'
    launcherFileDbFilename = 'launcherFileDb'
    webLauncherFlag = False

    def __init__(self):
        self.started = False
        self.taskMgrStarted = False
        self._downloadComplete = False
        self.pandaErrorCode = 0
        self.WIN32 = os.name == 'nt'
        if self.WIN32:
            self.VISTA = sys.getwindowsversion()[3] == 2 and sys.getwindowsversion()[0] == 6
        else:
            self.VISTA = 0
        ltime = time.localtime()
        logSuffix = '%02d%02d%02d_%02d%02d%02d' % (ltime[0] - 2000,
            ltime[1],
            ltime[2],
            ltime[3],
            ltime[4],
            ltime[5])
        logPrefix = ''
        if not self.WIN32:
            logPrefix = os.environ.get('LOGFILE_PREFIX', '')
        logfile = logPrefix + self.getLogFileName() + '-' + logSuffix + '.log'
        self.errorfile = 'errorCode'
        log = open(logfile, 'a')
        logOut = LogAndOutput(sys.__stdout__, log)
        logErr = LogAndOutput(sys.__stderr__, log)
        sys.stdout = logOut
        sys.stderr = logErr
        if sys.platform == 'darwin':
            os.system('/usr/sbin/system_profiler >>' + logfile)
        elif sys.platform == 'linux2':
            os.system('cat /proc/cpuinfo >>' + logfile)
            os.system('cat /proc/meminfo >>' + logfile)
            os.system('/sbin/ifconfig -a >>' + logfile)
        print('\n\nStarting %s...' % self.GameName)
        print('Current time: ' + time.asctime(time.localtime(time.time())) + ' ' + time.tzname[0])
        print('sys.path = ', sys.path)
        print('sys.argv = ', sys.argv)
        if len(sys.argv) >= self.ArgCount:
            Configrc_args = sys.argv[self.ArgCount - 1]
            print("generating configrc using: '" + Configrc_args + "'")
        else:
            Configrc_args = ''
            print('generating standard configrc')
        if 'PRC_EXECUTABLE_ARGS' in os.environ:
            print('PRC_EXECUTABLE_ARGS is set to: ' + os.environ['PRC_EXECUTABLE_ARGS'])
            print('Resetting PRC_EXECUTABLE_ARGS')
        ExecutionEnvironment.setEnvironmentVariable('PRC_EXECUTABLE_ARGS', '-stdout ' + Configrc_args)
        if 'CONFIG_CONFIG' in os.environ:
            print('CONFIG_CONFIG is set to: ' + os.environ['CONFIG_CONFIG'])
            print('Resetting CONFIG_CONFIG')
        os.environ['CONFIG_CONFIG'] = ':_:configdir_.:configpath_:configname_Configrc.exe:configexe_1:configargs_-stdout ' + Configrc_args
        cpMgr = ConfigPageManager.getGlobalPtr()
        cpMgr.reloadImplicitPages()
        launcherConfig = getConfigExpress()
        builtins.config = launcherConfig
        if config.GetBool('log-private-info', 0):
            print('os.environ = ', os.environ)
        elif '__COMPAT_LAYER' in os.environ:
            print('__COMPAT_LAYER = %s' % (os.environ['__COMPAT_LAYER'],))
        self.miniTaskMgr = MiniTaskManager()
        self.VerifyFiles = self.getVerifyFiles()
        self.setServerVersion(launcherConfig.GetString('server-version', 'no_version_set'))
        self.ServerVersionSuffix = launcherConfig.GetString('server-version-suffix', '')
        self.UserUpdateDelay = launcherConfig.GetFloat('launcher-user-update-delay', 0.5)
        self.TELEMETRY_BANDWIDTH = launcherConfig.GetInt('launcher-telemetry-bandwidth', 2000)
        self.INCREASE_THRESHOLD = launcherConfig.GetFloat('launcher-increase-threshold', 0.75)
        self.DECREASE_THRESHOLD = launcherConfig.GetFloat('launcher-decrease-threshold', 0.5)
        self.BPS_WINDOW = launcherConfig.GetFloat('launcher-bps-window', 8.0)
        self.DECREASE_BANDWIDTH = launcherConfig.GetBool('launcher-decrease-bandwidth', 1)
        self.MAX_BANDWIDTH = launcherConfig.GetInt('launcher-max-bandwidth', 0)
        self.nout = MultiplexStream()
        Notify.ptr().setOstreamPtr(self.nout, 0)
        self.nout.addFile(Filename(logfile))
        if launcherConfig.GetBool('console-output', 0):
            self.nout.addStandardOutput()
            sys.stdout.console = True
            sys.stderr.console = True
        self.notify = directNotify.newCategory('Launcher')
        self.clock = TrueClock.getGlobalPtr()
        self.logPrefix = logPrefix
        self.testServerFlag = self.getTestServerFlag()
        self.notify.info('isTestServer: %s' % self.testServerFlag)
        downloadServerString = launcherConfig.GetString('download-server', '')
        if downloadServerString:
            self.notify.info('Overriding downloadServer to %s.' % downloadServerString)
        else:
            downloadServerString = self.getValue('DOWNLOAD_SERVER', '')
        self.notify.info('Download Server List %s' % downloadServerString)
        self.downloadServerList = []
        for name in string.split(downloadServerString, ';'):
            url = URLSpec(name, 1)
            self.downloadServerList.append(url)

        self.nextDownloadServerIndex = 0
        self.getNextDownloadServer()
        self.gameServer = self.getGameServer()
        self.notify.info('Game Server %s' % self.gameServer)
        self.downloadServerRetries = 3
        self.multifileRetries = 1
        self.curMultifileRetry = 0
        self.downloadServerRetryPause = 1
        self.bandwidthIndex = len(self.BANDWIDTH_ARRAY) - 1
        self.everIncreasedBandwidth = 0
        self.goUserName = ''
        self.downloadPercentage = 90
        self.decompressPercentage = 5
        self.extractPercentage = 4
        self.lastLauncherMsg = None
        self.topDir = Filename.fromOsSpecific(self.getValue(self.InstallDirKey, '.'))
        self.setRegistry(self.GameLogFilenameKey, logfile)
        tmpVal = self.getValue(self.PatchCDKey)
        if tmpVal == None:
            self.fromCD = 0
        else:
            self.fromCD = tmpVal
        self.notify.info('patch directory is ' + repr((self.fromCD)))
        self.dbDir = self.topDir
        self.patchDir = self.topDir
        self.mfDir = self.topDir
        self.contentDir = 'content/'
        self.clientDbFilename = 'client.ddb'
        self.compClientDbFilename = self.clientDbFilename + '.pz'
        self.serverDbFilename = 'server.ddb'
        self.compServerDbFilename = self.serverDbFilename + '.pz'
        self.serverDbFilePath = self.contentDir + self.compServerDbFilename
        self.clientStarterDbFilePath = self.contentDir + self.compClientDbFilename
        self.progressFilename = 'progress'
        self.overallComplete = 0
        self.progressSoFar = 0
        self.patchExtension = 'pch'
        self.scanForHacks()
        self.firstPhase = self.LauncherPhases[0]
        self.finalPhase = self.LauncherPhases[-1]
        self.showPhase = 3.5
        self.numPhases = len(self.LauncherPhases)
        self.phaseComplete = {}
        self.phaseNewDownload = {}
        self.phaseOverallMap = {}
        tmpOverallMap = self.TmpOverallMap
        tmpPhase3Map = [0.001,
            0.996,
            0.0,
            0.0,
            0.003]
        phaseIdx = 0
        for phase in self.LauncherPhases:
            percentPhaseCompleteKey = 'PERCENT_PHASE_COMPLETE_' + repr(phase)
            self.setRegistry(percentPhaseCompleteKey, 0)
            self.phaseComplete[phase] = 0
            self.phaseNewDownload[phase] = 0
            self.phaseOverallMap[phase] = tmpOverallMap[phaseIdx]
            phaseIdx += 1

        self.patchList = []
        self.reextractList = []
        self.byteRate = 0
        self.byteRateRequested = 0
        self.resetBytesPerSecond()
        self.dldb = None
        self.currentMfname = None
        self.currentPhaseIndex = 0
        self.currentPhase = self.LauncherPhases[self.currentPhaseIndex]
        self.currentPhaseName = self.Localizer.LauncherPhaseNames[self.currentPhaseIndex]
        if self.getServerVersion() == 'no_version_set':
            self.setPandaErrorCode(10)
            self.notify.info('Aborting, Configrc did not run!')
            sys.exit()
        self.launcherMessage(self.Localizer.LauncherStartingMessage)
        self.http = HTTPClient()
        if self.http.getProxySpec() == '':
            self.http.setProxySpec(self.getValue(self.ProxyServerKey, ''))
            self.http.setDirectHostSpec(self.getValue(self.ProxyDirectHostsKey, ''))
        self.notify.info('Proxy spec is: %s' % self.http.getProxySpec())
        if self.http.getDirectHostSpec() != '':
            self.notify.info('Direct hosts list is: %s' % self.http.getDirectHostSpec())
        self.httpChannel = self.http.makeChannel(0)
        self.httpChannel.setDownloadThrottle(1)
        connOk = 0
        while not connOk:
            proxies = self.http.getProxiesForUrl(self.downloadServer)
            if proxies == 'DIRECT':
                self.notify.info('No proxy for download.')
            else:
                self.notify.info('Download proxy: %s' % proxies)
            testurl = self.addDownloadVersion(self.launcherFileDbFilename)
            connOk = self.httpChannel.getHeader(DocumentSpec(testurl))
            statusCode = self.httpChannel.getStatusCode()
            statusString = self.httpChannel.getStatusString()
            if not connOk:
                self.notify.warning('Could not contact download server at %s' % testurl.cStr())
                self.notify.warning('Status code = %s %s' % (statusCode, statusString))
                if statusCode == 407 or statusCode == 1407 or statusCode == HTTPChannel.SCSocksNoAcceptableLoginMethod:
                    self.setPandaErrorCode(3)
                elif statusCode == 404:
                    self.setPandaErrorCode(13)
                elif statusCode < 100:
                    self.setPandaErrorCode(4)
                elif statusCode > 1000:
                    self.setPandaErrorCode(9)
                else:
                    self.setPandaErrorCode(6)
                if not self.getNextDownloadServer():
                    sys.exit()

        self.notify.info('Download server: %s' % self.downloadServer.cStr())
        if self.notify.getDebug():
            self.accept('page_up', self.increaseBandwidth)
            self.accept('page_down', self.decreaseBandwidth)
        self.httpChannel.setPersistentConnection(1)
        self.foreground()
        self.prepareClient()
        self.setBandwidth()
        self.downloadLauncherFileDb()
        return

    def getTime(self):
        return self.clock.getShortTime()

    def isDummy(self):
        return 0

    def getNextDownloadServer(self):
        if self.nextDownloadServerIndex >= len(self.downloadServerList):
            self.downloadServer = None
            return 0
        self.downloadServer = self.downloadServerList[self.nextDownloadServerIndex]
        self.notify.info('Using download server %s.' % self.downloadServer.cStr())
        self.nextDownloadServerIndex += 1
        return 1

    def getProductName(self):
        config = getConfigExpress()
        productName = config.GetString('product-name', '')
        if productName and productName != 'DisneyOnline-US':
            productName = '_%s' % productName
        else:
            productName = ''
        return productName

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

    def handleInitiateFatalError(self, errorCode):
        self.notify.warning('handleInitiateFatalError: ' + errorToText(errorCode))
        sys.exit()

    def handleDecompressFatalError(self, task, errorCode):
        self.notify.warning('handleDecompressFatalError: ' + errorToText(errorCode))
        self.miniTaskMgr.remove(task)
        self.handleGenericMultifileError()

    def handleDecompressWriteError(self, task, errorCode):
        self.notify.warning('handleDecompressWriteError: ' + errorToText(errorCode))
        self.miniTaskMgr.remove(task)
        self.handleGenericMultifileError()

    def handleDecompressZlibError(self, task, errorCode):
        self.notify.warning('handleDecompressZlibError: ' + errorToText(errorCode))
        self.miniTaskMgr.remove(task)
        self.handleGenericMultifileError()

    def handleExtractFatalError(self, task, errorCode):
        self.notify.warning('handleExtractFatalError: ' + errorToText(errorCode))
        self.miniTaskMgr.remove(task)
        self.handleGenericMultifileError()

    def handleExtractWriteError(self, task, errorCode):
        self.notify.warning('handleExtractWriteError: ' + errorToText(errorCode))
        self.miniTaskMgr.remove(task)
        self.handleGenericMultifileError()

    def handlePatchFatalError(self, task, errorCode):
        self.notify.warning('handlePatchFatalError: ' + errorToText(errorCode))
        self.miniTaskMgr.remove(task)
        self.handleGenericMultifileError()

    def handlePatchWriteError(self, task, errorCode):
        self.notify.warning('handlePatchWriteError: ' + errorToText(errorCode))
        self.miniTaskMgr.remove(task)
        self.handleGenericMultifileError()

    def handleDownloadFatalError(self, task):
        self.notify.warning('handleDownloadFatalError: status code = %s %s' % (self.httpChannel.getStatusCode(), self.httpChannel.getStatusString()))
        self.miniTaskMgr.remove(task)
        statusCode = self.httpChannel.getStatusCode()
        if statusCode == 404:
            self.setPandaErrorCode(5)
        elif statusCode < 100:
            self.setPandaErrorCode(4)
        else:
            self.setPandaErrorCode(6)
        if not self.getNextDownloadServer():
            sys.exit()

    def handleDownloadWriteError(self, task):
        self.notify.warning('handleDownloadWriteError.')
        self.miniTaskMgr.remove(task)
        self.setPandaErrorCode(2)
        sys.exit()

    def handleGenericMultifileError(self):
        if not self.currentMfname:
            sys.exit()
        if self.curMultifileRetry < self.multifileRetries:
            self.notify.info('recover attempt: %s / %s' % (self.curMultifileRetry, self.multifileRetries))
            self.curMultifileRetry += 1
            self.notify.info('downloadPatchDone: Recovering from error.' + ' Deleting files in: ' + self.currentMfname)
            self.dldb.setClientMultifileIncomplete(self.currentMfname)
            self.dldb.setClientMultifileSize(self.currentMfname, 0)
            self.notify.info('downloadPatchDone: Recovering from error.' + ' redownloading: ' + self.currentMfname)
            self.httpChannel.reset()
            self.getMultifile(self.currentMfname)
        else:
            self.setPandaErrorCode(6)
            self.notify.info('handleGenericMultifileError: Failed to download multifile')
            sys.exit()

    def foregroundSleep(self):
        if not self.backgrounded:
            time.sleep(self.ForegroundSleepTime)

    def forceSleep(self):
        if not self.backgrounded:
            time.sleep(3.0)

    def addDownloadVersion(self, serverFilePath):
        url = URLSpec(self.downloadServer)
        origPath = url.getPath()
        if origPath and origPath[-1] == '/':
            origPath = origPath[:-1]
        if self.fromCD:
            url.setPath(self.getCDDownloadPath(origPath, serverFilePath))
        else:
            url.setPath(self.getDownloadPath(origPath, serverFilePath))
        self.notify.info('***' + url.cStr())
        return url

    def download(self, serverFilePath, localFilename, callback, callbackProgress):
        self.launcherMessage(self.Localizer.LauncherDownloadFile % {'name': self.currentPhaseName,
         'current': self.currentPhaseIndex,
         'total': self.numPhases})
        task = MiniTask(self.downloadTask)
        task.downloadRam = 0
        task.serverFilePath = serverFilePath
        task.serverFileURL = self.addDownloadVersion(serverFilePath)
        self.notify.info('Download request: %s' % task.serverFileURL.cStr())
        task.callback = callback
        task.callbackProgress = callbackProgress
        task.lastUpdate = 0
        self.resetBytesPerSecond()
        task.localFilename = localFilename
        self.httpChannel.beginGetDocument(DocumentSpec(task.serverFileURL))
        self.httpChannel.downloadToFile(task.localFilename)
        self.miniTaskMgr.add(task, 'launcher-download')

    def downloadRam(self, serverFilePath, callback):
        self.ramfile = Ramfile()
        task = MiniTask(self.downloadTask)
        task.downloadRam = 1
        task.serverFilePath = serverFilePath
        task.serverFileURL = self.addDownloadVersion(serverFilePath)
        self.notify.info('Download request: %s' % task.serverFileURL.cStr())
        task.callback = callback
        task.callbackProgress = None
        task.lastUpdate = 0
        self.resetBytesPerSecond()
        self.httpChannel.beginGetDocument(DocumentSpec(task.serverFileURL))
        self.httpChannel.downloadToRam(self.ramfile)
        self.miniTaskMgr.add(task, 'launcher-download')
        return

    def downloadTask(self, task):
        self.maybeStartGame()
        if self.httpChannel.run():
            now = self.getTime()
            if now - task.lastUpdate >= self.UserUpdateDelay:
                task.lastUpdate = now
                self.testBandwidth()
                if task.callbackProgress:
                    task.callbackProgress(task)
                bytesWritten = self.httpChannel.getBytesDownloaded()
                totalBytes = self.httpChannel.getFileSize()
                if totalBytes:
                    pct = int(round(bytesWritten / float(totalBytes) * 100))
                    self.launcherMessage(self.Localizer.LauncherDownloadFilePercent % {'name': self.currentPhaseName,
                     'current': self.currentPhaseIndex,
                     'total': self.numPhases,
                     'percent': pct})
                else:
                    self.launcherMessage(self.Localizer.LauncherDownloadFileBytes % {'name': self.currentPhaseName,
                     'current': self.currentPhaseIndex,
                     'total': self.numPhases,
                     'bytes': bytesWritten})
            self.foregroundSleep()
            return task.cont
        statusCode = self.httpChannel.getStatusCode()
        statusString = self.httpChannel.getStatusString()
        self.notify.info('HTTP status %s: %s' % (statusCode, statusString))
        if self.httpChannel.isValid() and self.httpChannel.isDownloadComplete():
            bytesWritten = self.httpChannel.getBytesDownloaded()
            totalBytes = self.httpChannel.getFileSize()
            if totalBytes:
                pct = int(round(bytesWritten / float(totalBytes) * 100))
                self.launcherMessage(self.Localizer.LauncherDownloadFilePercent % {'name': self.currentPhaseName,
                 'current': self.currentPhaseIndex,
                 'total': self.numPhases,
                 'percent': pct})
            else:
                self.launcherMessage(self.Localizer.LauncherDownloadFileBytes % {'name': self.currentPhaseName,
                 'current': self.currentPhaseIndex,
                 'total': self.numPhases,
                 'bytes': bytesWritten})
            self.notify.info('downloadTask: Download done: %s' % task.serverFileURL.cStr())
            task.callback()
            del task.callback
            return task.done
        else:
            if statusCode == HTTPChannel.SCDownloadOpenError or statusCode == HTTPChannel.SCDownloadWriteError:
                self.handleDownloadWriteError(task)
            elif statusCode == HTTPChannel.SCLostConnection:
                gotBytes = self.httpChannel.getBytesDownloaded()
                self.notify.info('Connection lost while downloading; got %s bytes.  Reconnecting.' % gotBytes)
                if task.downloadRam:
                    self.downloadRam(task.serverFilePath, task.callback)
                else:
                    self.download(task.serverFilePath, task.localFilename, task.callback, None)
            else:
                if self.httpChannel.isValid():
                    self.notify.info('Unexpected situation: no error status, but %s incompletely downloaded.' % task.serverFileURL.cStr())
                self.handleDownloadFatalError(task)
                if task.downloadRam:
                    self.downloadRam(task.serverFilePath, task.callback)
                else:
                    self.download(task.serverFilePath, task.localFilename, task.callback, None)
            return task.done
        return

    def downloadMultifile(self, serverFilename, localFilename, mfname, callback, totalSize, currentSize, callbackProgress):
        if currentSize != 0 and currentSize == totalSize:
            callback()
            return
        self.launcherMessage(self.Localizer.LauncherDownloadFile % {'name': self.currentPhaseName,
         'current': self.currentPhaseIndex,
         'total': self.numPhases})
        task = MiniTask(self.downloadMultifileTask)
        mfURL = self.addDownloadVersion(serverFilename)
        task.mfURL = mfURL
        self.notify.info('downloadMultifile: %s ' % task.mfURL.cStr())
        task.callback = callback
        task.callbackProgress = callbackProgress
        task.lastUpdate = 0
        self.httpChannel.getHeader(DocumentSpec(task.mfURL))
        if self.httpChannel.isFileSizeKnown():
            task.totalSize = self.httpChannel.getFileSize()
        else:
            task.totalSize = totalSize
        self.resetBytesPerSecond()
        task.serverFilename = serverFilename
        task.localFilename = localFilename
        task.mfname = mfname
        if currentSize != 0:
            if task.totalSize == currentSize:
                self.notify.info('already have full file! Skipping download.')
                callback()
                return
            self.httpChannel.beginGetSubdocument(DocumentSpec(task.mfURL), currentSize, task.totalSize)
            self.httpChannel.downloadToFile(task.localFilename, True)
        else:
            self.httpChannel.beginGetDocument(DocumentSpec(task.mfURL))
            self.httpChannel.downloadToFile(task.localFilename)
        self._addMiniTask(task, 'launcher-download-multifile')

    def downloadPatchSimpleProgress(self, task):
        startingByte = self.httpChannel.getFirstByteDelivered()
        bytesDownloaded = self.httpChannel.getBytesDownloaded()
        bytesWritten = startingByte + bytesDownloaded
        totalBytes = self.httpChannel.getFileSize()
        percentPatchComplete = int(round(bytesWritten / float(totalBytes) * self.downloadPercentage))
        self.setPercentPhaseComplete(self.currentPhase, percentPatchComplete)

    def getPercentPatchComplete(self, bytesWritten):
        return int(round((self.patchDownloadSoFar + bytesWritten) / float(self.totalPatchDownload) * self.downloadPercentage))

    def downloadPatchOverallProgress(self, task):
        startingByte = self.httpChannel.getFirstByteDelivered()
        bytesDownloaded = self.httpChannel.getBytesDownloaded()
        bytesWritten = startingByte + bytesDownloaded
        percentPatchComplete = self.getPercentPatchComplete(bytesWritten)
        self.setPercentPhaseComplete(self.currentPhase, percentPatchComplete)

    def downloadMultifileWriteToDisk(self, task):
        self.maybeStartGame()
        startingByte = self.httpChannel.getFirstByteDelivered()
        bytesDownloaded = self.httpChannel.getBytesDownloaded()
        bytesWritten = startingByte + bytesDownloaded
        if self.dldb:
            self.dldb.setClientMultifileSize(task.mfname, bytesWritten)
        percentComplete = 0
        if task.totalSize != 0:
            percentComplete = int(round(bytesWritten / float(task.totalSize) * self.downloadPercentage))
        self.setPercentPhaseComplete(self.currentPhase, percentComplete)

    def downloadMultifileTask(self, task):
        task.totalSize = self.httpChannel.getFileSize()
        if self.httpChannel.run():
            now = self.getTime()
            if now - task.lastUpdate >= self.UserUpdateDelay:
                task.lastUpdate = now
                self.testBandwidth()
                if task.callbackProgress:
                    task.callbackProgress(task)
                startingByte = self.httpChannel.getFirstByteDelivered()
                bytesDownloaded = self.httpChannel.getBytesDownloaded()
                bytesWritten = startingByte + bytesDownloaded
                percentComplete = 0
                if task.totalSize != 0:
                    percentComplete = int(round(100.0 * bytesWritten / float(task.totalSize)))
                self.launcherMessage(self.Localizer.LauncherDownloadFilePercent % {'name': self.currentPhaseName,
                 'current': self.currentPhaseIndex,
                 'total': self.numPhases,
                 'percent': percentComplete})
            self.foregroundSleep()
            return task.cont
        statusCode = self.httpChannel.getStatusCode()
        statusString = self.httpChannel.getStatusString()
        self.notify.info('HTTP status %s: %s' % (statusCode, statusString))
        if self.httpChannel.isValid() and self.httpChannel.isDownloadComplete():
            if task.callbackProgress:
                task.callbackProgress(task)
            self.notify.info('done: %s' % task.mfname)
            if self.dldb:
                self.dldb.setClientMultifileComplete(task.mfname)
            task.callback()
            del task.callback
            return task.done
        else:
            if statusCode == HTTPChannel.SCDownloadOpenError or statusCode == HTTPChannel.SCDownloadWriteError:
                self.handleDownloadWriteError(task)
            elif statusCode == HTTPChannel.SCLostConnection:
                startingByte = self.httpChannel.getFirstByteDelivered()
                bytesDownloaded = self.httpChannel.getBytesDownloaded()
                bytesWritten = startingByte + bytesDownloaded
                self.notify.info('Connection lost while downloading; got %s bytes.  Reconnecting.' % bytesDownloaded)
                self.downloadMultifile(task.serverFilename, task.localFilename, task.mfname, task.callback, task.totalSize, bytesWritten, task.callbackProgress)
            elif (statusCode == 416 or statusCode == HTTPChannel.SCDownloadInvalidRange) and self.httpChannel.getFirstByteRequested() != 0:
                self.notify.info('Invalid subrange; redownloading entire file.')
                self.downloadMultifile(task.serverFilename, task.localFilename, task.mfname, task.callback, task.totalSize, 0, task.callbackProgress)
            else:
                if self.httpChannel.isValid():
                    self.notify.info('Unexpected situation: no error status, but %s incompletely downloaded.' % task.mfname)
                self.handleDownloadFatalError(task)
                self.downloadMultifile(task.serverFilename, task.localFilename, task.mfname, task.callback, task.totalSize, 0, task.callbackProgress)
            return task.done

    def decompressFile(self, localFilename, callback):
        self.notify.info('decompress: request: ' + localFilename.cStr())
        self.launcherMessage(self.Localizer.LauncherDecompressingFile % {'name': self.currentPhaseName,
         'current': self.currentPhaseIndex,
         'total': self.numPhases})
        task = MiniTask(self.decompressFileTask)
        task.localFilename = localFilename
        task.callback = callback
        task.lastUpdate = 0
        task.decompressor = Decompressor()
        errorCode = task.decompressor.initiate(task.localFilename)
        if errorCode > 0:
            self._addMiniTask(task, 'launcher-decompressFile')
        else:
            self.handleInitiateFatalError(errorCode)

    def decompressFileTask(self, task):
        errorCode = task.decompressor.run()
        if errorCode == EUOk:
            now = self.getTime()
            if now - task.lastUpdate >= self.UserUpdateDelay:
                task.lastUpdate = now
                progress = task.decompressor.getProgress()
                self.launcherMessage(self.Localizer.LauncherDecompressingPercent % {'name': self.currentPhaseName,
                 'current': self.currentPhaseIndex,
                 'total': self.numPhases,
                 'percent': int(round(progress * 100))})
            self.foregroundSleep()
            return task.cont
        elif errorCode == EUSuccess:
            self.launcherMessage(self.Localizer.LauncherDecompressingPercent % {'name': self.currentPhaseName,
             'current': self.currentPhaseIndex,
             'total': self.numPhases,
             'percent': 100})
            self.notify.info('decompressTask: Decompress done: ' + task.localFilename.cStr())
            del task.decompressor
            task.callback()
            del task.callback
            return task.done
        elif errorCode == EUErrorAbort:
            self.handleDecompressFatalError(task, errorCode)
            return task.done
        elif errorCode == EUErrorWriteOutOfFiles or errorCode == EUErrorWriteDiskFull or errorCode == EUErrorWriteDiskSectorNotFound or errorCode == EUErrorWriteOutOfMemory or errorCode == EUErrorWriteSharingViolation or errorCode == EUErrorWriteDiskFault or errorCode == EUErrorWriteDiskNotFound:
            self.handleDecompressWriteError(task, errorCode)
            return task.done
        elif errorCode == EUErrorZlib:
            self.handleDecompressZlibError(task, errorCode)
            return task.done
        elif errorCode > 0:
            self.notify.warning('decompressMultifileTask: Unknown success return code: ' + errorToText(errorCode))
            return task.cont
        else:
            self.notify.warning('decompressMultifileTask: Unknown return code: ' + errorToText(errorCode))
            self.handleDecompressFatalError(task, errorCode)
            return task.done

    def decompressMultifile(self, mfname, localFilename, callback):
        self.notify.info('decompressMultifile: request: ' + localFilename.cStr())
        self.launcherMessage(self.Localizer.LauncherDecompressingFile % {'name': self.currentPhaseName,
         'current': self.currentPhaseIndex,
         'total': self.numPhases})
        task = MiniTask(self.decompressMultifileTask)
        task.mfname = mfname
        task.localFilename = localFilename
        task.callback = callback
        task.lastUpdate = 0
        task.decompressor = Decompressor()
        errorCode = task.decompressor.initiate(task.localFilename)
        if errorCode > 0:
            self._addMiniTask(task, 'launcher-decompressMultifile')
        else:
            self.handleInitiateFatalError(errorCode)

    def decompressMultifileTask(self, task):
        errorCode = task.decompressor.run()
        if errorCode == EUOk:
            now = self.getTime()
            if now - task.lastUpdate >= self.UserUpdateDelay:
                task.lastUpdate = now
                progress = task.decompressor.getProgress()
                self.launcherMessage(self.Localizer.LauncherDecompressingPercent % {'name': self.currentPhaseName,
                 'current': self.currentPhaseIndex,
                 'total': self.numPhases,
                 'percent': int(round(progress * 100))})
                percentProgress = int(round(progress * self.decompressPercentage))
                totalPercent = self.downloadPercentage + percentProgress
                self.setPercentPhaseComplete(self.currentPhase, totalPercent)
            self.foregroundSleep()
            return task.cont
        elif errorCode == EUSuccess:
            self.launcherMessage(self.Localizer.LauncherDecompressingPercent % {'name': self.currentPhaseName,
             'current': self.currentPhaseIndex,
             'total': self.numPhases,
             'percent': 100})
            totalPercent = self.downloadPercentage + self.decompressPercentage
            self.setPercentPhaseComplete(self.currentPhase, totalPercent)
            self.notify.info('decompressMultifileTask: Decompress multifile done: ' + task.localFilename.cStr())
            self.dldb.setClientMultifileDecompressed(task.mfname)
            del task.decompressor
            task.callback()
            del task.callback
            return task.done
        elif errorCode == EUErrorAbort:
            self.handleDecompressFatalError(task, errorCode)
            return task.done
        elif errorCode == EUErrorWriteOutOfFiles or errorCode == EUErrorWriteDiskFull or errorCode == EUErrorWriteDiskSectorNotFound or errorCode == EUErrorWriteOutOfMemory or errorCode == EUErrorWriteSharingViolation or errorCode == EUErrorWriteDiskFault or errorCode == EUErrorWriteDiskNotFound:
            self.handleDecompressWriteError(task, errorCode)
            return task.done
        elif errorCode == EUErrorZlib:
            self.handleDecompressZlibError(task, errorCode)
            return task.done
        elif errorCode > 0:
            self.notify.warning('decompressMultifileTask: Unknown success return code: ' + errorToText(errorCode))
            return task.cont
        else:
            self.notify.warning('decompressMultifileTask: Unknown return code: ' + errorToText(errorCode))
            self.handleDecompressFatalError(task, errorCode)
            return task.done

    def extract(self, mfname, localFilename, destDir, callback):
        self.notify.info('extract: request: ' + localFilename.cStr() + ' destDir: ' + destDir.cStr())
        self.launcherMessage(self.Localizer.LauncherExtractingFile % {'name': self.currentPhaseName,
         'current': self.currentPhaseIndex,
         'total': self.numPhases})
        task = MiniTask(self.extractTask)
        task.mfname = mfname
        task.localFilename = localFilename
        task.destDir = destDir
        task.callback = callback
        task.lastUpdate = 0
        task.extractor = Extractor()
        task.extractor.setExtractDir(task.destDir)
        if not task.extractor.setMultifile(task.localFilename):
            self.setPandaErrorCode(6)
            self.notify.info('extract: Unable to open multifile %s' % task.localFilename.cStr())
            sys.exit()
        numFiles = self.dldb.getServerNumFiles(mfname)
        for i in range(numFiles):
            subfile = self.dldb.getServerFileName(mfname, i)
            if not task.extractor.requestSubfile(Filename(subfile)):
                self.setPandaErrorCode(6)
                self.notify.info('extract: Unable to find subfile %s in multifile %s' % (subfile, mfname))
                sys.exit()

        self.notify.info('Extracting %d subfiles from multifile %s.' % (numFiles, mfname))
        self._addMiniTask(task, 'launcher-extract')

    def extractTask(self, task):
        errorCode = task.extractor.step()
        if errorCode == EUOk:
            now = self.getTime()
            if now - task.lastUpdate >= self.UserUpdateDelay:
                task.lastUpdate = now
                progress = task.extractor.getProgress()
                self.launcherMessage(self.Localizer.LauncherExtractingPercent % {'name': self.currentPhaseName,
                 'current': self.currentPhaseIndex,
                 'total': self.numPhases,
                 'percent': int(round(progress * 100.0))})
                percentProgress = int(round(progress * self.extractPercentage))
                totalPercent = self.downloadPercentage + self.decompressPercentage + percentProgress
                self.setPercentPhaseComplete(self.currentPhase, totalPercent)
            self.foregroundSleep()
            return task.cont
        elif errorCode == EUSuccess:
            self.launcherMessage(self.Localizer.LauncherExtractingPercent % {'name': self.currentPhaseName,
             'current': self.currentPhaseIndex,
             'total': self.numPhases,
             'percent': 100})
            totalPercent = self.downloadPercentage + self.decompressPercentage + self.extractPercentage
            self.setPercentPhaseComplete(self.currentPhase, totalPercent)
            self.notify.info('extractTask: Extract multifile done: ' + task.localFilename.cStr())
            self.dldb.setClientMultifileExtracted(task.mfname)
            del task.extractor
            task.callback()
            del task.callback
            return task.done
        elif errorCode == EUErrorAbort:
            self.handleExtractFatalError(task, errorCode)
            return task.done
        elif errorCode == EUErrorFileEmpty:
            self.handleExtractFatalError(task, errorCode)
            return task.done
        elif errorCode == EUErrorWriteOutOfFiles or errorCode == EUErrorWriteDiskFull or errorCode == EUErrorWriteDiskSectorNotFound or errorCode == EUErrorWriteOutOfMemory or errorCode == EUErrorWriteSharingViolation or errorCode == EUErrorWriteDiskFault or errorCode == EUErrorWriteDiskNotFound:
            self.handleExtractWriteError(task, errorCode)
            return task.done
        elif errorCode > 0:
            self.notify.warning('extractTask: Unknown success return code: ' + errorToText(errorCode))
            return task.cont
        else:
            self.notify.warning('extractTask: Unknown error return code: ' + errorToText(errorCode))
            self.handleExtractFatalError(task, errorCode)
            return task.done

    def patch(self, patchFile, patcheeFile, callback):
        self.notify.info('patch: request: ' + patchFile.cStr() + ' patchee: ' + patcheeFile.cStr())
        self.launcherMessage(self.Localizer.LauncherPatchingFile % {'name': self.currentPhaseName,
         'current': self.currentPhaseIndex,
         'total': self.numPhases})
        task = MiniTask(self.patchTask)
        task.patchFile = patchFile
        task.patcheeFile = patcheeFile
        task.callback = callback
        task.lastUpdate = 0
        task.patcher = Patcher()
        errorCode = task.patcher.initiate(task.patchFile, task.patcheeFile)
        if errorCode > 0:
            self._addMiniTask(task, 'launcher-patch')
        else:
            self.handleInitiateFatalError(errorCode)

    def patchTask(self, task):
        errorCode = task.patcher.run()
        if errorCode == EUOk:
            now = self.getTime()
            if now - task.lastUpdate >= self.UserUpdateDelay:
                task.lastUpdate = now
                progress = task.patcher.getProgress()
                self.launcherMessage(self.Localizer.LauncherPatchingPercent % {'name': self.currentPhaseName,
                 'current': self.currentPhaseIndex,
                 'total': self.numPhases,
                 'percent': int(round(progress * 100.0))})
            self.foregroundSleep()
            return task.cont
        elif errorCode == EUSuccess:
            self.launcherMessage(self.Localizer.LauncherPatchingPercent % {'name': self.currentPhaseName,
             'current': self.currentPhaseIndex,
             'total': self.numPhases,
             'percent': 100})
            self.notify.info('patchTask: Patch done: ' + task.patcheeFile.cStr())
            del task.patcher
            task.callback()
            del task.callback
            return task.done
        elif errorCode == EUErrorAbort:
            self.handlePatchFatalError(task, errorCode)
            return task.done
        elif errorCode == EUErrorFileEmpty:
            self.handlePatchFatalError(task, errorCode)
            return task.done
        elif errorCode == EUErrorWriteOutOfFiles or errorCode == EUErrorWriteDiskFull or errorCode == EUErrorWriteDiskSectorNotFound or errorCode == EUErrorWriteOutOfMemory or errorCode == EUErrorWriteSharingViolation or errorCode == EUErrorWriteDiskFault or errorCode == EUErrorWriteDiskNotFound:
            self.handlePatchWriteError(task, errorCode)
            return task.done
        elif errorCode > 0:
            self.notify.warning('patchTask: Unknown success return code: ' + errorToText(errorCode))
            return task.cont
        else:
            self.notify.warning('patchTask: Unknown error return code: ' + errorToText(errorCode))
            self.handlePatchFatalError(task, errorCode)
            return task.done

    def getProgressSum(self, phase):
        sum = 0
        for i in range(0, len(self.linesInProgress)):
            if self.linesInProgress[i].find(phase) > -1:
                nameSizeTuple = self.linesInProgress[i].split()
                numSize = nameSizeTuple[1].split('L')
                sum += string.atoi(numSize[0])

        return sum

    def readProgressFile(self):
        localFilename = Filename(self.dbDir, Filename(self.progressFilename))
        if not localFilename.exists():
            self.notify.warning('File does not exist: %s' % localFilename.cStr())
            self.linesInProgress = []
        else:
            f = open(localFilename.toOsSpecific())
            self.linesInProgress = f.readlines()
            f.close()
            localFilename.unlink()
        self.progressSum = 0
        token = 'phase_'
        self.progressSum = self.getProgressSum(token)
        self.progressSum -= self.getProgressSum(token + '2')
        self.notify.info('total phases to be downloaded = ' + repr((self.progressSum)))
        self.checkClientDbExists()

    def prepareClient(self):
        self.notify.info('prepareClient: Preparing client for install')
        if not self.topDir.exists():
            self.notify.info('prepareClient: Creating top directory: ' + self.topDir.cStr())
            os.makedirs(self.topDir.toOsSpecific())
        if not self.dbDir.exists():
            self.notify.info('prepareClient: Creating db directory: ' + self.dbDir.cStr())
            os.makedirs(self.dbDir.toOsSpecific())
        if not self.patchDir.exists():
            self.notify.info('prepareClient: Creating patch directory: ' + self.patchDir.cStr())
            os.makedirs(self.patchDir.toOsSpecific())
        if not self.mfDir.exists():
            self.notify.info('prepareClient: Creating mf directory: ' + self.mfDir.cStr())
            os.makedirs(self.mfDir.toOsSpecific())

    def downloadLauncherFileDb(self):
        self.notify.info('Downloading launcherFileDb')
        self.downloadRam(self.launcherFileDbFilename, self.downloadLauncherFileDbDone)

    def downloadLauncherFileDbDone(self):
        self.launcherFileDbHash = HashVal()
        self.launcherFileDbHash.hashRamfile(self.ramfile)
        if self.VerifyFiles:
            self.notify.info('Validating Launcher files')
            for fileDesc in self.ramfile.readlines():
                try:
                    filename, hashStr = fileDesc.split(' ', 1)
                except:
                    self.notify.info('Invalid line: "%s"' % fileDesc)
                    self.failLauncherFileDb('No hash in launcherFileDb')

                serverHash = HashVal()
                if not self.hashIsValid(serverHash, hashStr):
                    self.notify.info('Not a valid hash string: "%s"' % hashStr)
                    self.failLauncherFileDb('Invalid hash in launcherFileDb')
                localHash = HashVal()
                localFilename = Filename(self.topDir, Filename(filename))
                localHash.hashFile(localFilename)
                if localHash != serverHash:
                    self.failLauncherFileDb('%s does not match expected version.' % filename)

        self.downloadServerDbFile()

    def failLauncherFileDb(self, string):
        self.notify.info(string)
        self.setPandaErrorCode(15)
        sys.exit()

    def downloadServerDbFile(self):
        self.notify.info('Downloading server db file')
        self.launcherMessage(self.Localizer.LauncherDownloadServerFileList)
        self.downloadRam(self.serverDbFilePath, self.downloadServerDbFileDone)

    def downloadServerDbFileDone(self):
        self.serverDbFileHash = HashVal()
        self.serverDbFileHash.hashRamfile(self.ramfile)
        self.readProgressFile()

    def checkClientDbExists(self):
        clientFilename = Filename(self.dbDir, Filename(self.clientDbFilename))
        if clientFilename.exists():
            self.notify.info('Client Db exists')
            self.createDownloadDb()
        else:
            self.notify.info('Client Db does not exist')
            self.downloadClientDbStarterFile()

    def downloadClientDbStarterFile(self):
        self.notify.info('Downloading Client Db starter file')
        localFilename = Filename(self.dbDir, Filename(self.compClientDbFilename))
        self.download(self.clientStarterDbFilePath, localFilename, self.downloadClientDbStarterFileDone, None)
        return

    def downloadClientDbStarterFileDone(self):
        localFilename = Filename(self.dbDir, Filename(self.compClientDbFilename))
        decompressor = Decompressor()
        decompressor.decompress(localFilename)
        self.createDownloadDb()

    def createDownloadDb(self):
        self.notify.info('Creating downloadDb')
        self.launcherMessage(self.Localizer.LauncherCreatingDownloadDb)
        clientFilename = Filename(self.dbDir, Filename(self.clientDbFilename))
        self.notify.info('Client file name: ' + clientFilename.cStr())
        self.launcherMessage(self.Localizer.LauncherDownloadClientFileList)
        serverFile = self.ramfile
        decompressor = Decompressor()
        decompressor.decompress(serverFile)
        self.notify.info('Finished decompress')
        self.dldb = DownloadDb(serverFile, clientFilename)
        self.notify.info('created download db')
        self.launcherMessage(self.Localizer.LauncherFinishedDownloadDb)
        self.currentPhase = self.LauncherPhases[0]
        self.currentPhaseIndex = 1
        self.currentPhaseName = self.Localizer.LauncherPhaseNames[self.currentPhase]
        self.updatePhase(self.currentPhase)

    def maybeStartGame(self):
        if not self.started and self.currentPhase >= self.showPhase:
            self.started = True
            self.notify.info('maybeStartGame: starting game')
            self.launcherMessage(self.Localizer.LauncherStartingGame)
            self.background()
            builtins.launcher = self
            self.startGame()

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

    def _addMiniTask(self, task, name):
        if not self.miniTaskMgr:
            self.notify.info('Restarting mini task manager.')
            self.miniTaskMgr = MiniTaskManager()
            from direct.task.TaskManagerGlobal import taskMgr
            taskMgr.remove('miniTaskManager')
            taskMgr.add(self._stepMiniTaskManager, 'miniTaskManager')
        self.miniTaskMgr.add(task, name)

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
            if hasattr(__builtin__, 'base'):
                base.destroy()
            self.notify.info('Normal exit.')
            raise
        except:
            self.setPandaErrorCode(12)
            self.notify.warning('Handling Python exception.')
            if hasattr(__builtin__, 'base') and getattr(base, 'cr', None):
                if base.cr.timeManager:
                    from otp.otpbase import OTPGlobals
                    base.cr.timeManager.setDisconnectReason(OTPGlobals.DisconnectPythonError)
                    base.cr.timeManager.setExceptionInfo()
                base.cr.sendDisconnect()
            if hasattr(__builtin__, 'base'):
                base.destroy()
            self.notify.info('Exception exit.\n')
            import traceback
            traceback.print_exc()
            sys.exit()

        return

    def updatePhase(self, phase):
        self.notify.info('Updating multifiles in phase: ' + repr(phase))
        self.setPercentPhaseComplete(self.currentPhase, 0)
        self.phaseMultifileNames = []
        numfiles = self.dldb.getServerNumMultifiles()
        for i in range(self.dldb.getServerNumMultifiles()):
            mfname = self.dldb.getServerMultifileName(i)
            if self.dldb.getServerMultifilePhase(mfname) == phase:
                self.phaseMultifileNames.append(mfname)

        self.updateNextMultifile()

    def updateNextMultifile(self):
        if len(self.phaseMultifileNames) > 0:
            self.currentMfname = self.phaseMultifileNames.pop()
            self.curMultifileRetry = 0
            self.getMultifile(self.currentMfname)
        else:
            if self.currentMfname is None:
                self.notify.warning('no multifile found! See below for debug info:')
                for i in range(self.dldb.getServerNumMultifiles()):
                    mfname = self.dldb.getServerMultifileName(i)
                    phase = self.dldb.getServerMultifilePhase(mfname)
                    print(i, mfname, phase)

                self.handleGenericMultifileError()
            decompressedMfname = os.path.splitext(self.currentMfname)[0]
            localFilename = Filename(self.mfDir, Filename(decompressedMfname))
            nextIndex = self.LauncherPhases.index(self.currentPhase) + 1
            if nextIndex < len(self.LauncherPhases):
                self.MakeNTFSFilesGlobalWriteable(localFilename)
            else:
                self.MakeNTFSFilesGlobalWriteable()
            vfs = VirtualFileSystem.getGlobalPtr()
            vfs.mount(localFilename, '.', VirtualFileSystem.MFReadOnly)
            self.setPercentPhaseComplete(self.currentPhase, 100)
            self.notify.info('Done updating multifiles in phase: ' + repr((self.currentPhase)))
            self.progressSoFar += int(round(self.phaseOverallMap[self.currentPhase] * 100))
            self.notify.info('progress so far ' + repr((self.progressSoFar)))
            messenger.send('phaseComplete-' + repr((self.currentPhase)))
            if nextIndex < len(self.LauncherPhases):
                self.currentPhase = self.LauncherPhases[nextIndex]
                self.currentPhaseIndex = nextIndex + 1
                self.currentPhaseName = self.Localizer.LauncherPhaseNames[self.currentPhase]
                self.updatePhase(self.currentPhase)
            else:
                self.notify.info('ALL PHASES COMPLETE')
                self.maybeStartGame()
                messenger.send('launcherAllPhasesComplete')
                self.cleanup()
        return

    def isDownloadComplete(self):
        return self._downloadComplete

    def updateMultifileDone(self):
        self.updateNextMultifile()

    def downloadMultifileDone(self):
        self.getDecompressMultifile(self.currentMfname)

    def getMultifile(self, mfname):
        self.notify.info('Downloading multifile: ' + mfname)
        if not self.dldb.clientMultifileExists(mfname):
            self.maybeStartGame()
            self.notify.info('Multifile does not exist in client db,' + 'creating new record: ' + mfname)
            self.dldb.addClientMultifile(mfname)
            curHash = self.dldb.getServerMultifileHash(mfname)
            self.dldb.setClientMultifileHash(mfname, curHash)
            localFilename = Filename(self.mfDir, Filename(mfname))
            if localFilename.exists():
                curSize = localFilename.getFileSize()
                self.dldb.setClientMultifileSize(mfname, curSize)
                if curSize == self.dldb.getServerMultifileSize(mfname):
                    self.dldb.setClientMultifileComplete(mfname)
        decompressedMfname = os.path.splitext(mfname)[0]
        decompressedFilename = Filename(self.mfDir, Filename(decompressedMfname))
        if (not self.dldb.clientMultifileComplete(mfname) or not self.dldb.clientMultifileDecompressed(mfname)) and decompressedFilename.exists():
            clientMd5 = HashVal()
            clientMd5.hashFile(decompressedFilename)
            clientVer = self.dldb.getVersion(Filename(decompressedMfname), clientMd5)
            if clientVer != -1:
                self.notify.info('Decompressed multifile is already on disk and correct: %s (version %s)' % (mfname, clientVer))
                self.dldb.setClientMultifileComplete(mfname)
                self.dldb.setClientMultifileDecompressed(mfname)
                compressedFilename = Filename(self.mfDir, Filename(mfname))
                compressedFilename.unlink()
                extractedOk = True
                numFiles = self.dldb.getServerNumFiles(mfname)
                for i in range(numFiles):
                    subfile = self.dldb.getServerFileName(mfname, i)
                    fn = Filename(self.mfDir, Filename(subfile))
                    if fn.compareTimestamps(decompressedFilename) <= 0:
                        extractedOk = False
                        break

                if extractedOk:
                    self.notify.info('Multifile appears to have been extracted already.')
                    self.dldb.setClientMultifileExtracted(mfname)
        if not self.dldb.clientMultifileComplete(mfname) or not decompressedFilename.exists():
            self.maybeStartGame()
            currentSize = self.dldb.getClientMultifileSize(mfname)
            totalSize = self.dldb.getServerMultifileSize(mfname)
            localFilename = Filename(self.mfDir, Filename(mfname))
            if not localFilename.exists():
                currentSize = 0
            else:
                currentSize = min(currentSize, localFilename.getFileSize())
            if currentSize == 0:
                self.notify.info('Multifile has not been started, ' + 'downloading new file: ' + mfname)
                curHash = self.dldb.getServerMultifileHash(mfname)
                self.dldb.setClientMultifileHash(mfname, curHash)
                self.phaseNewDownload[self.currentPhase] = 1
                self.downloadMultifile(self.contentDir + mfname, localFilename, mfname, self.downloadMultifileDone, totalSize, 0, self.downloadMultifileWriteToDisk)
            else:
                clientHash = self.dldb.getClientMultifileHash(mfname)
                serverHash = self.dldb.getServerMultifileHash(mfname)
                if clientHash.eq(serverHash):
                    self.notify.info('Multifile is not complete, finishing download for %s, size = %s / %s' % (mfname, currentSize, totalSize))
                    self.downloadMultifile(self.contentDir + mfname, localFilename, mfname, self.downloadMultifileDone, totalSize, currentSize, self.downloadMultifileWriteToDisk)
                elif self.curMultifileRetry < self.multifileRetries:
                    self.notify.info('recover attempt: %s / %s' % (self.curMultifileRetry, self.multifileRetries))
                    self.curMultifileRetry += 1
                    self.notify.info('Multifile is not complete, and is out of date. ' + 'Restarting download with newest multifile')
                    self.dldb.setClientMultifileIncomplete(self.currentMfname)
                    self.dldb.setClientMultifileSize(self.currentMfname, 0)
                    self.dldb.setClientMultifileHash(self.currentMfname, serverHash)
                    self.getMultifile(self.currentMfname)
                else:
                    self.setPandaErrorCode(6)
                    self.notify.info('getMultifile: Failed to download multifile')
                    sys.exit()
        else:
            self.notify.info('Multifile already complete: ' + mfname)
            self.downloadMultifileDone()

    def updateMultifileDone(self):
        self.updateNextMultifile()

    def downloadMultifileDone(self):
        self.getDecompressMultifile(self.currentMfname)

    def getMultifile(self, mfname):
        self.notify.info('Downloading multifile: ' + mfname)
        if not self.dldb.clientMultifileExists(mfname):
            self.maybeStartGame()
            self.notify.info('Multifile does not exist in client db,' + 'creating new record: ' + mfname)
            self.dldb.addClientMultifile(mfname)
            if self.DecompressMultifiles:
                curHash = self.dldb.getServerMultifileHash(mfname)
                self.dldb.setClientMultifileHash(mfname, curHash)
                localFilename = Filename(self.mfDir, Filename(mfname))
                if localFilename.exists():
                    curSize = localFilename.getFileSize()
                    self.dldb.setClientMultifileSize(mfname, curSize)
                    if curSize == self.dldb.getServerMultifileSize(mfname):
                        self.dldb.setClientMultifileComplete(mfname)
        decompressedMfname = os.path.splitext(mfname)[0]
        decompressedFilename = Filename(self.mfDir, Filename(decompressedMfname))
        if self.DecompressMultifiles:
            if (not self.dldb.clientMultifileComplete(mfname) or not self.dldb.clientMultifileDecompressed(mfname)) and decompressedFilename.exists():
                clientMd5 = HashVal()
                clientMd5.hashFile(decompressedFilename)
                clientVer = self.dldb.getVersion(Filename(decompressedMfname), clientMd5)
                if clientVer != -1:
                    self.notify.info('Decompressed multifile is already on disk and correct: %s (version %s)' % (mfname, clientVer))
                    self.dldb.setClientMultifileComplete(mfname)
                    self.dldb.setClientMultifileDecompressed(mfname)
                    compressedFilename = Filename(self.mfDir, Filename(mfname))
                    compressedFilename.unlink()
                    extractedOk = True
                    numFiles = self.dldb.getServerNumFiles(mfname)
                    for i in range(numFiles):
                        subfile = self.dldb.getServerFileName(mfname, i)
                        fn = Filename(self.mfDir, Filename(subfile))
                        if fn.compareTimestamps(decompressedFilename) <= 0:
                            extractedOk = False
                            break

                    if extractedOk:
                        self.notify.info('Multifile appears to have been extracted already.')
                        self.dldb.setClientMultifileExtracted(mfname)
        if not self.dldb.clientMultifileComplete(mfname) or not decompressedFilename.exists():
            self.maybeStartGame()
            currentSize = self.dldb.getClientMultifileSize(mfname)
            totalSize = self.dldb.getServerMultifileSize(mfname)
            localFilename = Filename(self.mfDir, Filename(mfname))
            if not localFilename.exists():
                currentSize = 0
            if currentSize == 0:
                self.notify.info('Multifile has not been started, ' + 'downloading new file: ' + mfname)
                curHash = self.dldb.getServerMultifileHash(mfname)
                self.dldb.setClientMultifileHash(mfname, curHash)
                self.phaseNewDownload[self.currentPhase] = 1
                self.downloadMultifile(self.contentDir + mfname, localFilename, mfname, self.downloadMultifileDone, totalSize, 0, self.downloadMultifileWriteToDisk)
            else:
                clientHash = self.dldb.getClientMultifileHash(mfname)
                serverHash = self.dldb.getServerMultifileHash(mfname)
                if clientHash.eq(serverHash):
                    self.notify.info('Multifile is not complete, finishing download for %s, size = %s / %s' % (mfname, currentSize, totalSize))
                    self.downloadMultifile(self.contentDir + mfname, localFilename, mfname, self.downloadMultifileDone, totalSize, currentSize, self.downloadMultifileWriteToDisk)
                elif self.curMultifileRetry < self.multifileRetries:
                    self.notify.info('recover attempt: %s / %s' % (self.curMultifileRetry, self.multifileRetries))
                    self.curMultifileRetry += 1
                    self.notify.info('Multifile is not complete, and is out of date. ' + 'Restarting download with newest multifile')
                    self.dldb.setClientMultifileIncomplete(self.currentMfname)
                    self.dldb.setClientMultifileSize(self.currentMfname, 0)
                    if self.DecompressMultifiles:
                        self.dldb.setClientMultifileHash(self.currentMfname, serverHash)
                    self.getMultifile(self.currentMfname)
                else:
                    self.setPandaErrorCode(6)
                    self.notify.info('getMultifile: Failed to download multifile')
                    sys.exit()
        else:
            self.notify.info('Multifile already complete: ' + mfname)
            self.downloadMultifileDone()

    def getDecompressMultifile(self, mfname):
        if not self.DecompressMultifiles:
            self.decompressMultifileDone()
        elif not self.dldb.clientMultifileDecompressed(mfname):
            self.maybeStartGame()
            self.notify.info('decompressMultifile: Decompressing multifile: ' + mfname)
            localFilename = Filename(self.mfDir, Filename(mfname))
            self.decompressMultifile(mfname, localFilename, self.decompressMultifileDone)
        else:
            self.notify.info('decompressMultifile: Multifile already decompressed: ' + mfname)
            self.decompressMultifileDone()

    def decompressMultifileDone(self):
        if self.phaseNewDownload[self.currentPhase]:
            self.setPercentPhaseComplete(self.currentPhase, 95)
        self.extractMultifile(self.currentMfname)

    def extractMultifile(self, mfname):
        if not self.dldb.clientMultifileExtracted(mfname):
            self.maybeStartGame()
            self.notify.info('extractMultifile: Extracting multifile: ' + mfname)
            decompressedMfname = os.path.splitext(mfname)[0]
            localFilename = Filename(self.mfDir, Filename(decompressedMfname))
            destDir = Filename(self.topDir)
            self.notify.info('extractMultifile: Extracting: ' + localFilename.cStr() + ' to: ' + destDir.cStr())
            self.extract(mfname, localFilename, destDir, self.extractMultifileDone)
        else:
            self.notify.info('extractMultifile: Multifile already extracted: ' + mfname)
            self.extractMultifileDone()

    def extractMultifileDone(self):
        if self.phaseNewDownload[self.currentPhase]:
            self.setPercentPhaseComplete(self.currentPhase, 99)
        self.notify.info('extractMultifileDone: Finished updating multifile: ' + self.currentMfname)
        self.patchMultifile()

    def getPatchFilename(self, fname, currentVersion):
        return fname + '.v' + repr(currentVersion) + '.' + self.patchExtension

    def downloadPatches(self):
        if len(self.patchList) > 0:
            self.currentPatch, self.currentPatchee, self.currentPatchVersion = self.patchList.pop()
            self.notify.info(self.contentDir)
            self.notify.info(self.currentPatch)
            patchFile = self.currentPatch + '.pz'
            serverPatchFilePath = self.contentDir + patchFile
            self.notify.info(serverPatchFilePath)
            localPatchFilename = Filename(self.patchDir, Filename(patchFile))
            if self.currentPhase > 3:
                self.download(serverPatchFilePath, localPatchFilename, self.downloadPatchDone, self.downloadPatchSimpleProgress)
            else:
                self.download(serverPatchFilePath, localPatchFilename, self.downloadPatchDone, self.downloadPatchOverallProgress)
        else:
            self.notify.info('applyNextPatch: Done patching multifile: ' + repr((self.currentPhase)))
            self.patchDone()

    def downloadPatchDone(self):
        self.patchDownloadSoFar += self.httpChannel.getBytesDownloaded()
        self.notify.info('downloadPatchDone: Decompressing patch file: ' + self.currentPatch + '.pz')
        self.decompressFile(Filename(self.patchDir, Filename(self.currentPatch + '.pz')), self.decompressPatchDone)

    def decompressPatchDone(self):
        self.notify.info('decompressPatchDone: Patching file: ' + self.currentPatchee + ' from ver: ' + repr((self.currentPatchVersion)))
        patchFile = Filename(self.patchDir, Filename(self.currentPatch))
        patchFile.setBinary()
        patchee = Filename(self.mfDir, Filename(self.currentPatchee))
        patchee.setBinary()
        self.patch(patchFile, patchee, self.downloadPatches)

    def patchDone(self):
        self.notify.info('patchDone: Patch successful')
        del self.currentPatch
        del self.currentPatchee
        del self.currentPatchVersion
        decompressedMfname = os.path.splitext(self.currentMfname)[0]
        localFilename = Filename(self.mfDir, Filename(decompressedMfname))
        destDir = Filename(self.topDir)
        self.extract(self.currentMfname, localFilename, destDir, self.updateMultifileDone)

    def startReextractingFiles(self):
        self.notify.info('startReextractingFiles: Reextracting ' + repr((len(self.reextractList))) + ' files for multifile: ' + self.currentMfname)
        self.launcherMessage(self.Localizer.LauncherRecoverFiles)
        self.currentMfile = Multifile()
        decompressedMfname = os.path.splitext(self.currentMfname)[0]
        self.currentMfile.openRead(Filename(self.mfDir, Filename(decompressedMfname)))
        self.reextractNextFile()

    def reextractNextFile(self):
        failure = 0
        while not failure and len(self.reextractList) > 0:
            currentReextractFile = self.reextractList.pop()
            subfileIndex = self.currentMfile.findSubfile(currentReextractFile)
            if subfileIndex >= 0:
                destFilename = Filename(self.topDir, Filename(currentReextractFile))
                result = self.currentMfile.extractSubfile(subfileIndex, destFilename)
                if not result:
                    self.notify.warning('reextractNextFile: Failure on reextract.')
                    failure = 1
            else:
                self.notify.warning('reextractNextFile: File not found in multifile: ' + repr(currentReextractFile))
                failure = 1

        if failure:
            sys.exit()
        self.notify.info('reextractNextFile: Done reextracting files for multifile: ' + repr((self.currentPhase)))
        del self.currentMfile
        self.updateMultifileDone()

    def patchMultifile(self):
        self.launcherMessage(self.Localizer.LauncherCheckUpdates % {'name': self.currentPhaseName,
         'current': self.currentPhaseIndex,
         'total': self.numPhases})
        self.notify.info('patchMultifile: Checking for patches on multifile: ' + self.currentMfname)
        self.patchList = []
        clientMd5 = HashVal()
        decompressedMfname = os.path.splitext(self.currentMfname)[0]
        localFilename = Filename(self.mfDir, Filename(decompressedMfname))
        clientMd5.hashFile(localFilename)
        clientVer = self.dldb.getVersion(Filename(decompressedMfname), clientMd5)
        if clientVer == 1:
            self.patchAndHash()
            return
        elif clientVer == -1:
            self.notify.info('patchMultifile: Invalid hash for file: ' + self.currentMfname)
            self.maybeStartGame()
            if self.curMultifileRetry < self.multifileRetries:
                self.notify.info('recover attempt: %s / %s' % (self.curMultifileRetry, self.multifileRetries))
                self.curMultifileRetry += 1
                self.notify.info('patchMultifile: Restarting download with newest multifile')
                self.dldb.setClientMultifileIncomplete(self.currentMfname)
                self.dldb.setClientMultifileSize(self.currentMfname, 0)
                self.getMultifile(self.currentMfname)
            else:
                self.setPandaErrorCode(6)
                self.notify.info('patchMultifile: Failed to download multifile')
                sys.exit()
            return
        elif clientVer > 1:
            self.notify.info('patchMultifile: Old version for multifile: ' + self.currentMfname + ' Client ver: ' + repr(clientVer))
            self.maybeStartGame()
            self.totalPatchDownload = 0
            self.patchDownloadSoFar = 0
            for ver in range(1, clientVer):
                patch = self.getPatchFilename(decompressedMfname, ver + 1)
                patchee = decompressedMfname
                patchVersion = ver + 1
                self.patchList.append((patch, patchee, patchVersion))
                if self.currentPhase == 3:
                    self.totalPatchDownload += self.getProgressSum(patch)

            self.notify.info('total patch to be downloaded = ' + repr((self.totalPatchDownload)))
            self.downloadPatches()
            return

    def patchAndHash(self):
        self.reextractList = []
        self.PAHClean = 1
        self.PAHNumFiles = self.dldb.getServerNumFiles(self.currentMfname)
        self.PAHFileCounter = 0
        if self.PAHNumFiles > 0:
            task = MiniTask(self.patchAndHashTask)
            task.cleanCallback = self.updateMultifileDone
            task.uncleanCallback = self.startReextractingFiles
            self._addMiniTask(task, 'patchAndHash')
        else:
            self.updateMultifileDone()

    def patchAndHashTask(self, task):
        self.launcherMessage(self.Localizer.LauncherVerifyPhase)
        if self.PAHFileCounter == self.PAHNumFiles:
            if self.PAHClean:
                task.cleanCallback()
            else:
                task.uncleanCallback()
            return task.done
        else:
            i = self.PAHFileCounter
            self.PAHFileCounter += 1
        fname = self.dldb.getServerFileName(self.currentMfname, i)
        fnameFilename = Filename(self.topDir, Filename(fname))
        if not os.path.exists(fnameFilename.toOsSpecific()):
            self.notify.info('patchAndHash: File not found: ' + fname)
            self.reextractList.append(fname)
            self.PAHClean = 0
            return task.cont
        if self.VerifyFiles and self.dldb.hasVersion(Filename(fname)):
            clientMd5 = HashVal()
            clientMd5.hashFile(fnameFilename)
            clientVer = self.dldb.getVersion(Filename(fname), clientMd5)
            if clientVer == 1:
                return task.cont
            else:
                self.notify.info('patchAndHash: Invalid hash for file: ' + fname)
                self.reextractList.append(fname)
                self.PAHClean = 0
        return task.cont

    def launcherMessage(self, msg):
        if msg != self.lastLauncherMsg:
            self.lastLauncherMsg = msg
            self.notify.info(msg)

    def isTestServer(self):
        return self.testServerFlag

    def recordPeriodTimeRemaining(self, secondsRemaining):
        self.setValue(self.PeriodTimeRemainingKey, int(secondsRemaining))

    def recordPeriodName(self, periodName):
        self.setValue(self.PeriodNameKey, periodName)

    def recordSwid(self, swid):
        self.setValue(self.SwidKey, swid)

    def getGoUserName(self):
        return self.goUserName

    def setGoUserName(self, userName):
        self.goUserName = userName

    def getInstallDir(self):
        return self.topDir.cStr()

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

    def setServerVersion(self, version):
        self.ServerVersion = version

    def getServerVersion(self):
        return self.ServerVersion

    def getIsNewInstallation(self):
        result = self.getValue(self.NewInstallationKey, 1)
        result = base.config.GetBool('new-installation', result)
        return result

    def setIsNotNewInstallation(self):
        self.setValue(self.NewInstallationKey, 0)

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
        percentDone = self.phaseComplete[phase]
        return percentDone == 100

    def setPercentPhaseComplete(self, phase, percent):
        self.notify.info('phase updating %s, %s' % (phase, percent))
        oldPercent = self.phaseComplete[phase]
        if oldPercent != percent:
            self.phaseComplete[phase] = percent
            messenger.send('launcherPercentPhaseComplete', [phase,
             percent,
             self.getBandwidth(),
             self.byteRate])
            percentPhaseCompleteKey = 'PERCENT_PHASE_COMPLETE_' + repr(phase)
            self.setRegistry(percentPhaseCompleteKey, percent)
            self.overallComplete = int(round(percent * self.phaseOverallMap[phase])) + self.progressSoFar
            self.setRegistry('PERCENT_OVERALL_COMPLETE', self.overallComplete)

    def getPercentPhaseComplete(self, phase):
        return self.phaseComplete[phase]
        dr = finalRequested - startRequested
        if dt <= 0.0:
            return -1
        self.byteRate = db / dt
        self.byteRateRequested = dr / dt
        return self.byteRate

    def addPhasePostProcess(self, phase, func, taskChain = 'default'):
        if self.getPhaseComplete(phase):
            func()
            return
        self.acceptOnce('phaseComplete-%s' % phase, func)

    def testBandwidth(self):
        self.recordBytesPerSecond()
        byteRate = self.getBytesPerSecond()
        if byteRate < 0:
            return
        if byteRate >= self.getBandwidth() * self.INCREASE_THRESHOLD:
            self.increaseBandwidth(byteRate)
        elif byteRate < self.byteRateRequested * self.DECREASE_THRESHOLD:
            self.decreaseBandwidth(byteRate)

    def getBandwidth(self):
        if self.backgrounded:
            bandwidth = self.BANDWIDTH_ARRAY[self.bandwidthIndex] - self.TELEMETRY_BANDWIDTH
        else:
            bandwidth = self.BANDWIDTH_ARRAY[self.bandwidthIndex]
        if self.MAX_BANDWIDTH > 0:
            bandwidth = min(bandwidth, self.MAX_BANDWIDTH)
        return bandwidth

    def increaseBandwidth(self, targetBandwidth = None):
        maxBandwidthIndex = len(self.BANDWIDTH_ARRAY) - 1
        if self.bandwidthIndex == maxBandwidthIndex:
            self.notify.debug('increaseBandwidth: Already at maximum bandwidth')
            return 0
        self.bandwidthIndex += 1
        self.everIncreasedBandwidth = 1
        self.setBandwidth()
        return 1

    def decreaseBandwidth(self, targetBandwidth = None):
        if not self.DECREASE_BANDWIDTH:
            return 0
        if self.backgrounded and self.everIncreasedBandwidth:
            return 0
        if self.bandwidthIndex == 0:
            return 0
        else:
            self.bandwidthIndex -= 1
            if targetBandwidth:
                while self.bandwidthIndex > 0 and self.BANDWIDTH_ARRAY[self.bandwidthIndex] > targetBandwidth:
                    self.bandwidthIndex -= 1

            self.setBandwidth()
            return 1

    def setBandwidth(self):
        self.resetBytesPerSecond()
        self.httpChannel.setMaxBytesPerSecond(self.getBandwidth())

    def resetBytesPerSecond(self):
        self.bpsList = []

    def recordBytesPerSecond(self):
        bytesDownloaded = self.httpChannel.getBytesDownloaded()
        bytesRequested  = self.httpChannel.getBytesRequested()
        t = self.getTime()
        self.bpsList.append((t, bytesDownloaded, bytesRequested))
        while 1:
            if len(self.bpsList) == 0:
                break
            ft, fb, fr = self.bpsList[0]
            if ft < t-self.BPS_WINDOW:
                self.bpsList.pop(0)
            else:
                break

    def getBytesPerSecond(self):
        if len(self.bpsList) < 2:
            return -1
        startTime, startBytes, startRequested = self.bpsList[0]
        finalTime, finalBytes, finalRequested = self.bpsList[-1]
        dt = finalTime - startTime
        db = finalBytes - startBytes
        dr = finalRequested - startRequested
        if dt <= 0.0:
            return -1
        self.byteRate = db / dt
        self.byteRateRequested = dr / dt
        return self.byteRate

    def testBandwidth(self):
        self.recordBytesPerSecond()
        byteRate = self.getBytesPerSecond()
        if byteRate < 0:
            return
        if byteRate >= self.getBandwidth() * self.INCREASE_THRESHOLD:
            self.increaseBandwidth(byteRate)
        elif byteRate < self.byteRateRequested * self.DECREASE_THRESHOLD:
            self.decreaseBandwidth(byteRate)

    def getBandwidth(self):
        if self.backgrounded:
            bandwidth = self.BANDWIDTH_ARRAY[self.bandwidthIndex] - self.TELEMETRY_BANDWIDTH
        else:
            bandwidth = self.BANDWIDTH_ARRAY[self.bandwidthIndex]
        if self.MAX_BANDWIDTH > 0:
            bandwidth = min(bandwidth, self.MAX_BANDWIDTH)
        return bandwidth

    def increaseBandwidth(self, targetBandwidth = None):
        maxBandwidthIndex = len(self.BANDWIDTH_ARRAY) - 1
        if self.bandwidthIndex == maxBandwidthIndex:
            return 0
        self.bandwidthIndex += 1
        self.everIncreasedBandwidth = 1
        self.setBandwidth()
        return 1

    def decreaseBandwidth(self, targetBandwidth = None):
        if not self.DECREASE_BANDWIDTH:
            return 0
        if self.backgrounded and self.everIncreasedBandwidth:
            return 0
        if self.bandwidthIndex == 0:
            return 0
        else:
            self.bandwidthIndex -= 1
            if targetBandwidth:
                while self.bandwidthIndex > 0 and self.BANDWIDTH_ARRAY[self.bandwidthIndex] > targetBandwidth:
                    self.bandwidthIndex -= 1

            self.setBandwidth()
            return 1

    def setBandwidth(self):
        self.resetBytesPerSecond()
        self.httpChannel.setMaxBytesPerSecond(self.getBandwidth())

    def MakeNTFSFilesGlobalWriteable(self, pathToSet = None):
        if not self.WIN32:
            return
        import win32api
        if pathToSet == None:
            pathToSet = self.getInstallDir()
        else:
            pathToSet = pathToSet.cStr() + '*'
        DrivePath = pathToSet[0:3]
        try:
            volname, volsernum, maxfilenamlen, sysflags, filesystemtype = win32api.GetVolumeInformation(DrivePath)
        except:
            return

        if self.win32con_FILE_PERSISTENT_ACLS & sysflags:
            self.notify.info('NTFS detected, making files global writeable\n')
            win32dir = win32api.GetWindowsDirectory()
            cmdLine = win32dir + '\\system32\\cacls.exe "' + pathToSet + '" /T /E /C /G Everyone:F > nul'
            os.system(cmdLine)
        return

    def cleanup(self):
        self.notify.info('cleanup: cleaning up Launcher')
        self.ignoreAll()
        del self.clock
        del self.dldb
        del self.httpChannel
        del self.http

    def scanForHacks(self):
        if not self.WIN32:
            return
        import winreg
        hacksInstalled = {}
        hacksRunning = {}
        hackName = ['!xSpeed.net', 'A Speeder', 'Speed Gear']
        knownHacksRegistryKeys = {
            hackName[0] : [
                [winreg.HKEY_LOCAL_MACHINE, 'Software\\Microsoft\\Windows\\CurrentVersion\\Run\\!xSpeed'],
                [winreg.HKEY_CURRENT_USER, 'Software\\!xSpeednethy'],
                [winreg.HKEY_CURRENT_USER, 'Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\MenuOrder\\Start Menu\\Programs\\!xSpeednet'],
                [winreg.HKEY_LOCAL_MACHINE, 'Software\\Gentee\\Paths\\!xSpeednet'],
                [winreg.HKEY_LOCAL_MACHINE, 'Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\!xSpeed.net 2.0']],
            hackName[1] : [
                [winreg.HKEY_CURRENT_USER, 'Software\\aspeeder'],
                [winreg.HKEY_LOCAL_MACHINE, 'Software\\aspeeder'],
                [winreg.HKEY_LOCAL_MACHINE, 'Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\aspeeder']]
        }
        try:
            for prog in list(knownHacksRegistryKeys.keys()):
                for key in knownHacksRegistryKeys[prog]:
                    try:
                        h = winreg.OpenKey(key[0], key[1])
                        hacksInstalled[prog] = 1
                        winreg.CloseKey(h)
                        break
                    except:
                        pass
        except:
            pass
        knownHacksMUI = {'!xspeednet': hackName[0], 'aspeeder': hackName[1], 'speed gear': hackName[2]}
        i = 0
        try:
            rh = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Software\\Microsoft\\Windows\\ShellNoRoam\\MUICache')
            while 1:
                name, value, type = winreg.EnumValue(rh, i)
                i += 1
                if type == 1:
                    val = value.lower()
                    for hackprog in knownHacksMUI:
                        if val.find(hackprog) != -1:
                            hacksInstalled[knownHacksMUI[hackprog]] = 1
                            break
            winreg.CloseKey(rh)
        except:
            pass

        try:
            import otp.launcher.procapi
        except:
            pass
        else:
            knownHacksExe = {'!xspeednet.exe': hackName[0], 'aspeeder.exe': hackName[1], 'speedgear.exe': hackName[2]}
            try:
                for p in procapi.getProcessList():
                    pname = p.name
                    if pname in knownHacksExe:
                        hacksRunning[knownHacksExe[pname]] = 1
            except:
                pass

        if len(hacksInstalled) > 0:
            self.notify.info("Third party programs installed:")
            for hack in list(hacksInstalled.keys()):
                self.notify.info(hack)

        if len(hacksRunning) > 0:
            self.notify.info("Third party programs running:")
            for hack in list(hacksRunning.keys()):
                self.notify.info(hack)
            self.setPandaErrorCode(8)
            sys.exit()

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
