import datetime
from panda3d.core import *
from direct.directnotify import DirectNotifyGlobal
from direct.showbase.DirectObject import DirectObject
from otp.chat.WhiteList import WhiteList
from toontown.toonbase import TTLocalizer

class TTWhiteList(WhiteList, DirectObject):
    RedownloadTaskName = 'RedownloadWhitelistTask'
    WhitelistBaseDir = ConfigVariableString('whitelist-base-dir', '').value
    WhitelistStageDir = ConfigVariableString('whitelist-stage-dir', 'whitelist').value
    WhitelistOverHttp = ConfigVariableBool('whitelist-over-http', False).value
    WhitelistFileName = ConfigVariableString('whitelist-filename', 'twhitelist.dat').value

    def __init__(self):
        DirectObject.__init__(self)
        self.redownloadingWhitelist = False
        self.startRedownload = datetime.datetime.now()
        self.endRedownload = datetime.datetime.now()
        self.percentDownloaded = 0.0
        self.notify = DirectNotifyGlobal.directNotify.newCategory('TTWhiteList')
        vfs = VirtualFileSystem.getGlobalPtr()
        filename = Filename('twhitelist.dat')
        searchPath = DSearchPath()
        if __debug__:
            searchPath.appendDirectory(Filename('resources/phase_3/etc'))
        found = vfs.resolveFilename(filename, searchPath)
        if not found:
            self.notify.info("Couldn't find whitelist data file!")
        data = vfs.readFile(filename, 1)
        lines = data.split(b'\n')
        WhiteList.__init__(self, lines)
        self.defaultWord = TTLocalizer.ChatGarblerDefault[0]
        if self.WhitelistOverHttp:
            self.redownloadWhitelist()
            self.accept('updateWhitelist', self.handleNewWhitelist)

    def unload(self):
        if self.WhitelistOverHttp:
            self.ignore('updateWhitelist')
            self.removeDownloadingTextTask()

    def redownloadWhitelist(self):
        if not self.WhitelistOverHttp:
            return
        self.percentDownload = 0.0
        self.notify.info('starting redownloadWhitelist')
        self.startRedownload = datetime.datetime.now()
        self.redownloadingWhitelist = True
        self.addDownloadingTextTask()
        self.whitelistUrl = self.getWhitelistUrl()
        self.whitelistDir = Filename(self.findWhitelistDir())
        Filename(self.whitelistDir + '/.').makeDir()
        http = HTTPClient.getGlobalPtr()
        self.url = self.whitelistUrl + self.WhitelistFileName
        self.ch = http.makeChannel(True)
        localFilename = Filename(self.whitelistDir, 'twhitelist.dat')
        self.ch.getHeader(DocumentSpec(self.url))
        size = self.ch.getFileSize()
        doc = self.ch.getDocumentSpec()
        localSize = localFilename.getFileSize()
        outOfDate = True
        if size == localSize:
            if doc.hasDate():
                date = doc.getDate()
                localDate = HTTPDate(localFilename.getTimestamp())
                if localDate.compareTo(date) > 0:
                    outOfDate = False
                    self.notify.info('Whitelist is up to date')
        taskMgr.remove(self.RedownloadTaskName)
        if outOfDate and self.ch.isValid():
            self.ch.beginGetDocument(doc)
            self.ch.downloadToFile(localFilename)
            taskMgr.add(self.downloadWhitelistTask, self.RedownloadTaskName)
        else:
            self.updateWhitelist()

    def getWhitelistUrl(self):
        result = ConfigVariableString('fallback-whitelist-url', 'http://cdn.toontown.disney.go.com/toontown/en/').value
        override = ConfigVariableString('whitelist-url', '').value
        if override:
            self.notify.info('got an override url,  using %s for the whitelist' % override)
            result = override
        else:
            try:
                launcherUrl = base.launcher.getValue('GAME_WHITELIST_URL', '')
                if launcherUrl:
                    result = launcherUrl
                    self.notify.info('got GAME_WHITELIST_URL from launcher using %s' % result)
                else:
                    self.notify.info('blank GAME_WHITELIST_URL from launcher, using %s' % result)
            except:
                self.notify.warning('got exception getting GAME_WHITELIST_URL from launcher, using %s' % result)

        return result

    def addDownloadingTextTask(self):
        self.removeDownloadingTextTask()
        task = taskMgr.doMethodLater(1, self.loadingTextTask, 'WhitelistDownloadingTextTask')
        task.startTime = globalClock.getFrameTime()
        self.loadingTextTask(task)

    def removeDownloadingTextTask(self):
        taskMgr.remove('WhitelistDownloadingTextTask')

    def loadingTextTask(self, task):
        timeIndex = int(globalClock.getFrameTime() - task.startTime) % 3
        timeStrs = (TTLocalizer.NewsPageDownloadingNews0, TTLocalizer.NewsPageDownloadingNews1, TTLocalizer.NewsPageDownloadingNews2)
        textToDisplay = timeStrs[timeIndex] % int(self.percentDownloaded * 100)
        return task.again

    def findWhitelistDir(self):
        if self.WhitelistOverHttp:
            return self.WhitelistStageDir
        return None

    def downloadWhitelistTask(self, task):
        if self.ch.run():
            return task.cont
        doc = self.ch.getDocumentSpec()
        date = ''
        if doc.hasDate():
            date = doc.getDate().getString()
        if not self.ch.isValid():
            self.notify.warning('Unable to download %s' % self.url)
            self.redownloadingWhitelist = False
            return task.done
        self.notify.info('Done downloading whitelist file')
        self.updateWhitelist()
        return task.done

    def updateWhitelist(self):
        localFilename = Filename(self.whitelistDir, 'twhitelist.dat')
        if not localFilename.exists():
            return
        data = vfs.readFile(localFilename, 1)
        lines = data.split(b'\n')
        self.words = []
        for line in lines:
            self.words.append(line.strip(b'\n\r').lower())

        self.words.sort()
        self.numWords = len(self.words)
        self.defaultWord = TTLocalizer.ChatGarblerDefault[0]

    def handleNewWhitelist(self):
        self.redownloadWhitelist()
