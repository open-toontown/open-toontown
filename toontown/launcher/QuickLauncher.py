import sys
import os
import time
import string
import bz2
import random
from direct.showbase.MessengerGlobal import *
from direct.showbase.DirectObject import DirectObject
from direct.showbase.EventManagerGlobal import *
from direct.task.TaskManagerGlobal import *
from direct.task.Task import Task
from direct.directnotify.DirectNotifyGlobal import *
from pandac.PandaModules import *
from otp.launcher.LauncherBase import LauncherBase
from toontown.toonbase import TTLocalizer

class QuickLauncher(LauncherBase):
    GameName = 'Toontown'
    ArgCount = 3
    LauncherPhases = [1,
     2,
     3,
     3.5,
     4,
     5,
     5.5,
     6,
     7,
     8,
     9,
     10,
     11,
     12,
     13]
    TmpOverallMap = [0.01,
     0.01,
     0.23,
     0.15,
     0.12,
     0.17,
     0.08,
     0.07,
     0.05,
     0.05,
     0.017,
     0.011,
     0.01,
     0.012,
     0.01]
    ForegroundSleepTime = 0.001
    Localizer = TTLocalizer
    DecompressMultifiles = True
    launcherFileDbFilename = 'patcher.ver?%s' % random.randint(1, 1000000000)
    CompressionExt = 'bz2'
    PatchExt = 'pch'

    def __init__(self):
        print('Running: ToontownQuickLauncher')
        self.toontownBlueKey = 'TOONTOWN_BLUE'
        self.launcherMessageKey = 'LAUNCHER_MESSAGE'
        self.game1DoneKey = 'GAME1_DONE'
        self.game2DoneKey = 'GAME2_DONE'
        self.tutorialCompleteKey = 'TUTORIAL_DONE'
        LauncherBase.__init__(self)
        self.useTTSpecificLogin = config.GetBool('tt-specific-login', 0)
        if self.useTTSpecificLogin:
            self.toontownPlayTokenKey = 'LOGIN_TOKEN'
        else:
            self.toontownPlayTokenKey = 'PLAYTOKEN'
        print('useTTSpecificLogin=%s' % self.useTTSpecificLogin)
        self.contentDir = '/'
        self.serverDbFileHash = HashVal()
        self.launcherFileDbHash = HashVal()
        self.DECREASE_BANDWIDTH = 0
        self.httpChannel.setDownloadThrottle(0)
        self.webAcctParams = 'WEB_ACCT_PARAMS'
        self.parseWebAcctParams()
        self.showPhase = -1
        self.maybeStartGame()
        self.mainLoop()

    def addDownloadVersion(self, serverFilePath):
        url = URLSpec(self.downloadServer)
        origPath = url.getPath()
        if origPath[-1] == '/':
            url.setPath('%s%s' % (origPath, serverFilePath))
        else:
            url.setPath('%s/%s' % (origPath, serverFilePath))
        return url

    def downloadLauncherFileDbDone(self):
        settings = {}
        for line in self.ramfile.readlines():
            if line.find('=') >= 0:
                key, value = line.strip().split('=')
                settings[key] = value

        self.requiredInstallFiles = []
        if sys.platform == 'win32':
            fileList = settings['REQUIRED_INSTALL_FILES']
        elif sys.platform == 'darwin':
            fileList = settings['REQUIRED_INSTALL_FILES_OSX']
        else:
            self.notify.warning('Unknown sys.platform: %s' % sys.platform)
            fileList = settings['REQUIRED_INSTALL_FILES']
        for fileDesc in fileList.split():
            fileName, flag = fileDesc.split(':')
            directions = BitMask32(flag)
            extract = directions.getBit(0)
            required = directions.getBit(1)
            optionalDownload = directions.getBit(2)
            self.notify.info('fileName: %s, flag:=%s directions=%s, extract=%s required=%s optDownload=%s' % (fileName,
             flag,
             directions,
             extract,
             required,
             optionalDownload))
            if required:
                self.requiredInstallFiles.append(fileName)

        self.notify.info('requiredInstallFiles: %s' % self.requiredInstallFiles)
        self.mfDetails = {}
        for mfName in self.requiredInstallFiles:
            currentVer = settings['FILE_%s.current' % mfName]
            details = settings['FILE_%s.%s' % (mfName, currentVer)]
            size, hash = details.split()
            self.mfDetails[mfName] = (currentVer, int(size), hash)
            self.notify.info('mfDetails[%s] = %s' % (mfName, self.mfDetails[mfName]))

        self.resumeInstall()

    def resumeMultifileDownload(self):
        curVer, expectedSize, expectedMd5 = self.mfDetails[self.currentMfname]
        localFilename = Filename(self.topDir, Filename('_%s.%s.%s' % (self.currentMfname, curVer, self.CompressionExt)))
        serverFilename = '%s%s.%s.%s' % (self.contentDir,
         self.currentMfname,
         curVer,
         self.CompressionExt)
        if localFilename.exists():
            fileSize = localFilename.getFileSize()
            self.notify.info('Previous partial download exists for: %s size=%s' % (localFilename.cStr(), fileSize))
            self.downloadMultifile(serverFilename, localFilename, self.currentMfname, self.downloadMultifileDone, 0, fileSize, self.downloadMultifileWriteToDisk)
        else:
            self.downloadMultifile(serverFilename, localFilename, self.currentMfname, self.downloadMultifileDone, 0, 0, self.downloadMultifileWriteToDisk)

    def resumeInstall(self):
        for self.currentPhaseIndex in range(len(self.LauncherPhases)):
            self.currentPhase = self.LauncherPhases[self.currentPhaseIndex]
            self.currentPhaseName = self.Localizer.LauncherPhaseNames[self.currentPhase]
            self.currentMfname = 'phase_%s.mf' % self.currentPhase
            if sys.platform == 'darwin' and (self.currentMfname == 'phase_1.mf' or self.currentMfname == 'phase_2.mf'):
                self.currentMfname = 'phase_%sOSX.mf' % self.currentPhase
            if self.currentMfname in self.requiredInstallFiles:
                self.requiredInstallFiles.remove(self.currentMfname)
            else:
                self.notify.warning('avoiding crash ValueError: list.remove(x): x not in list')
            curVer, expectedSize, expectedMd5 = self.mfDetails[self.currentMfname]
            self.curPhaseFile = Filename(self.topDir, Filename(self.currentMfname))
            self.notify.info('working on: %s' % self.curPhaseFile)
            if self.curPhaseFile.exists():
                self.notify.info('file exists')
                fileSize = self.curPhaseFile.getFileSize()
                clientMd5 = HashVal()
                clientMd5.hashFile(self.curPhaseFile)
                self.notify.info('clientMd5: %s expectedMd5: %s' % (clientMd5, expectedMd5))
                self.notify.info('clientSize: %s expectedSize: %s' % (fileSize, expectedSize))
                if fileSize == expectedSize and clientMd5.asHex() == expectedMd5:
                    self.notify.info('file is up to date')
                    self.finalizePhase()
                    continue
                else:
                    self.notify.info('file is not valid')
                    self.resumeMultifileDownload()
                    return
            else:
                self.notify.info('file does not exist - start download')
                self.resumeMultifileDownload()
                return

        if not self.requiredInstallFiles:
            self.notify.info('ALL PHASES COMPLETE')
            messenger.send('launcherAllPhasesComplete')
            self.cleanup()
            return
        raise Exception('Some phases not listed in LauncherPhases: %s' % self.requiredInstallFiles)

    def getDecompressMultifile(self, mfname):
        if not self.DecompressMultifiles:
            self.decompressMultifileDone()
        elif 1:
            self.notify.info('decompressMultifile: Decompressing multifile: ' + mfname)
            curVer, expectedSize, expectedMd5 = self.mfDetails[self.currentMfname]
            localFilename = Filename(self.topDir, Filename('_%s.%s.%s' % (mfname, curVer, self.CompressionExt)))
            self.decompressMultifile(mfname, localFilename, self.decompressMultifileDone)
        else:
            self.notify.info('decompressMultifile: Multifile already decompressed: %s' % mfname)
            self.decompressMultifileDone()

    def decompressMultifile(self, mfname, localFilename, callback):
        self.notify.info('decompressMultifile: request: ' + localFilename.cStr())
        self.launcherMessage(self.Localizer.LauncherDecompressingFile % {'name': self.currentPhaseName,
         'current': self.currentPhaseIndex,
         'total': self.numPhases})
        task = Task(self.decompressMultifileTask)
        task.mfname = mfname
        task.mfFilename = Filename(self.topDir, Filename('_' + task.mfname))
        task.mfFile = open(task.mfFilename.toOsSpecific(), 'wb')
        task.localFilename = localFilename
        task.callback = callback
        task.lastUpdate = 0
        task.decompressor = bz2.BZ2File(localFilename.toOsSpecific(), 'rb')
        taskMgr.add(task, 'launcher-decompressMultifile')

    def decompressMultifileTask(self, task):
        data = task.decompressor.read(8192)
        if data:
            task.mfFile.write(data)
            now = self.getTime()
            if now - task.lastUpdate >= self.UserUpdateDelay:
                task.lastUpdate = now
                curSize = task.mfFilename.getFileSize()
                curVer, expectedSize, expectedMd5 = self.mfDetails[self.currentMfname]
                progress = curSize / float(expectedSize)
                self.launcherMessage(self.Localizer.LauncherDecompressingPercent % {'name': self.currentPhaseName,
                 'current': self.currentPhaseIndex,
                 'total': self.numPhases,
                 'percent': int(round(progress * 100))})
                percentProgress = int(round(progress * self.decompressPercentage))
                totalPercent = self.downloadPercentage + percentProgress
                self.setPercentPhaseComplete(self.currentPhase, totalPercent)
            self.foregroundSleep()
            return Task.cont
        else:
            task.mfFile.close()
            task.decompressor.close()
            unlinked = task.localFilename.unlink()
            if not unlinked:
                self.notify.warning('unlink failed on file: %s' % task.localFilename.cStr())
            realMf = Filename(self.topDir, Filename(self.currentMfname))
            renamed = task.mfFilename.renameTo(realMf)
            if not renamed:
                self.notify.warning('rename failed on file: %s' % task.mfFilename.cStr())
            self.launcherMessage(self.Localizer.LauncherDecompressingPercent % {'name': self.currentPhaseName,
             'current': self.currentPhaseIndex,
             'total': self.numPhases,
             'percent': 100})
            totalPercent = self.downloadPercentage + self.decompressPercentage
            self.setPercentPhaseComplete(self.currentPhase, totalPercent)
            self.notify.info('decompressMultifileTask: Decompress multifile done: ' + task.localFilename.cStr())
            if self.dldb:
                self.dldb.setClientMultifileDecompressed(task.mfname)
            del task.decompressor
            task.callback()
            del task.callback
            return Task.done

    def decompressMultifileDone(self):
        self.finalizePhase()
        self.notify.info('Done updating multifiles in phase: ' + repr((self.currentPhase)))
        self.progressSoFar += int(round(self.phaseOverallMap[self.currentPhase] * 100))
        self.notify.info('progress so far ' + repr((self.progressSoFar)))
        messenger.send('phaseComplete-' + repr((self.currentPhase)))
        self.resumeInstall()

    def finalizePhase(self):
        mfFilename = Filename(self.topDir, Filename(self.currentMfname))
        self.MakeNTFSFilesGlobalWriteable(mfFilename)
        vfs = VirtualFileSystem.getGlobalPtr()
        vfs.mount(mfFilename, '.', VirtualFileSystem.MFReadOnly)
        self.setPercentPhaseComplete(self.currentPhase, 100)

    def getValue(self, key, default = None):
        return os.environ.get(key, default)

    def setValue(self, key, value):
        os.environ[key] = str(value)

    def getVerifyFiles(self):
        return config.GetInt('launcher-verify', 0)

    def getTestServerFlag(self):
        return self.getValue('IS_TEST_SERVER', 0)

    def getGameServer(self):
        return self.getValue('GAME_SERVER', '')

    def getLogFileName(self):
        return 'toontown'

    def parseWebAcctParams(self):
        s = config.GetString('fake-web-acct-params', '')
        if not s:
            s = self.getRegistry(self.webAcctParams)
        self.notify.info('webAcctParams = %s' % s)
        self.setRegistry(self.webAcctParams, '')
        l = s.split('&')
        length = len(l)
        dict = {}
        for index in range(0, len(l)):
            args = l[index].split('=')
            if len(args) == 3:
                name, value = args[-2:]
                dict[name] = int(value)
            elif len(args) == 2:
                name, value = args
                dict[name] = int(value)

        if 'secretsNeedsParentPassword' in dict and 1:
            self.secretNeedsParentPasswordKey = dict['secretsNeedsParentPassword']
            self.notify.info('secretNeedsParentPassword = %d' % self.secretNeedsParentPasswordKey)
        else:
            self.notify.warning('no secretNeedsParentPassword token in webAcctParams')

        if 'chatEligible' in dict:
            self.chatEligibleKey = dict['chatEligible']
            self.notify.info('chatEligibleKey = %d' % self.chatEligibleKey)
        else:
            self.notify.warning('no chatEligible token in webAcctParams')

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
        self.notify.info('self.VISTA = %s' % self.VISTA)
        self.notify.info('checking env' % os.environ)
        if missingValue == None:
            missingValue = ''
        value = os.environ.get(name, missingValue)
        try:
            value = int(value)
        except:
            pass

        return value

    def getCDDownloadPath(self, origPath, serverFilePath):
        return '%s/%s/CD_%d/%s' % (origPath,
         self.ServerVersion,
         self.fromCD,
         serverFilePath)

    def getDownloadPath(self, origPath, serverFilePath):
        return '%s/%s' % (origPath, serverFilePath)

    def hashIsValid(self, serverHash, hashStr):
        return serverHash.setFromDec(hashStr)

    def getAccountServer(self):
        return self.getValue('ACCOUNT_SERVER', '')

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

    def canLeaveFirstIsland(self):
        return self.getPhaseComplete(4)

    def startGame(self):
        self.newTaskManager()
        eventMgr.restart()
        from toontown.toonbase import ToontownStart
