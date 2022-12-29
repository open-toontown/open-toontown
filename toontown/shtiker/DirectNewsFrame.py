import os
import datetime
import functools
from panda3d.core import Filename, DSearchPath, ConfigVariableString, ConfigVariableBool
from panda3d.core import HTTPClient, Ramfile, DocumentSpec
from direct.showbase import DirectObject
from direct.gui.DirectGui import DirectFrame, DGG
from direct.directnotify import DirectNotifyGlobal
from direct.showbase import AppRunnerGlobal
from toontown.shtiker import IssueFrame
from toontown.shtiker import IssueFrameV2
from toontown.toonbase import TTLocalizer

class DirectNewsFrame(DirectObject.DirectObject):
    TaskName = 'HtmlViewUpdateTask'
    TaskChainName = 'RedownladTaskChain'
    RedownloadTaskName = 'RedownloadNewsTask'
    NewsBaseDir = ConfigVariableString('news-base-dir', '/httpNews').value
    NewsStageDir = ConfigVariableString('news-stage-dir', 'news').value
    FrameDimensions = (-1.30666637421,
     1.30666637421,
     -0.751666665077,
     0.751666665077)
    notify = DirectNotifyGlobal.directNotify.newCategory('DirectNewsFrame')
    NewsIndexFilename = ConfigVariableString('news-index-filename', 'http_news_index.txt').value
    NewsOverHttp = ConfigVariableBool('news-over-http', True).value
    CacheIndexFilename = 'cache_index.txt'
    SectionIdents = ['hom',
     'new',
     'evt',
     'tot',
     'att',
     'tnr']

    def __init__(self, parent = aspect2d):
        DirectObject.DirectObject.__init__(self)
        self.accept('newsSnapshot', self.doSnapshot)
        self.active = False
        self.parent = parent
        self.issues = []
        self.accept('newsChangeWeek', self.changeWeek)
        self.curIssueIndex = 0
        self.strFilenames = None
        self.redownloadingNews = False
        self.startRedownload = datetime.datetime.now()
        self.endRedownload = datetime.datetime.now()
        self.load()
        self.percentDownloaded = 0.0
        self.numIssuesExpected = 0
        self.needsParseNews = True
        self.newsIndexEntries = []
        if self.NewsOverHttp:
            self.redownloadNews()
        self.accept('newIssueOut', self.handleNewIssueOut)
        self.accept('clientCleanup', self.handleClientCleanup)
        return

    def parseNewsContent(self):
        if not self.needsParseNews:
            return
        self.needsParseNews = False
        result = False
        newsDir = self.findNewsDir()
        if newsDir:
            allHomeFiles = self.getAllHomeFilenames(newsDir)
            self.notify.debug('len allHomeFiles = %s' % len(allHomeFiles))
            self.numIssuesExpected = len(allHomeFiles)
            if allHomeFiles:
                for myIssueIndex, oneHomeFile in enumerate(allHomeFiles):
                    if type(oneHomeFile) == type(''):
                        justFilename = oneHomeFile
                    else:
                        justFilename = oneHomeFile.getFilename().getBasename()
                    self.notify.debug('parseNewContent %s' % justFilename)
                    parts = justFilename.split('_')
                    dateStr = parts[3]
                    majorVer, minorVer = self.calcIssueVersion(dateStr)
                    if majorVer == 1:
                        oneIssue = IssueFrame.IssueFrame(self.backFrame, newsDir, dateStr, myIssueIndex, len(allHomeFiles), self.strFilenames)
                    elif majorVer == 2:
                        oneIssue = IssueFrameV2.IssueFrameV2(self.backFrame, newsDir, dateStr, myIssueIndex, len(allHomeFiles), self.strFilenames, self.newsIndexEntries)
                    else:
                        self.notify.warning('Dont know how to handle version %s, asuming v2' % majorVer)
                        oneIssue = IssueFrameV2.IssueFrameV2(self.backFrame, newsDir, dateStr, myIssueIndex, len(allHomeFiles), self.strFilenames, self.newsIndexEntries)
                    oneIssue.hide()
                    self.issues.append(oneIssue)

                if self.issues:
                    self.issues[-1].show()
                    self.curIssueIndex = len(self.issues) - 1
                    result = True
        if hasattr(base.cr, 'inGameNewsMgr') and base.cr.inGameNewsMgr:
            self.createdTime = base.cr.inGameNewsMgr.getLatestIssue()
            self.notify.debug('setting created time to latest issue %s' % self.createdTime)
        else:
            self.createdTime = base.cr.toontownTimeManager.getCurServerDateTime()
            self.notify.debug('setting created time cur server time %s' % self.createdTime)
        return result

    def getAllHomeFilenames(self, newsDir):
        self.notify.debug('getAllHomeFilenames')
        newsDirAsFile = vfs.getFile(Filename(newsDir))
        fileList = newsDirAsFile.scanDirectory()
        fileNames = fileList.getFiles()
        self.notify.debug('filenames=%s' % str(fileNames))
        homeFileNames = set([])
        for name in fileNames:
            self.notify.debug('processing %s' % name)
            baseName = name.getFilename().getBasename()
            self.notify.debug('baseName=%s' % baseName)
            if 'hom1.' in baseName:
                homeFileNames.add(name)
            else:
                self.notify.debug('hom1. not in baseName')

        if not homeFileNames:
            self.notify.warning('couldnt find hom1. in %s' % fileNames)
            self.setErrorMessage(TTLocalizer.NewsPageNoIssues)
            return []

        def fileCmp(fileA, fileB):
            return fileA.getFilename().compareTo(fileB.getFilename())

        homeFileNames = list(homeFileNames)
        homeFileNames.sort(key=functools.cmp_to_key(fileCmp))
        self.notify.debug('returned homeFileNames=%s' % homeFileNames)
        return homeFileNames

    def findNewsDir(self):
        if self.NewsOverHttp:
            return self.NewsStageDir
        searchPath = DSearchPath()
        if AppRunnerGlobal.appRunner:
            searchPath.appendDirectory(Filename.expandFrom('$TT_3_5_ROOT/phase_3.5/models/news'))
        else:
            basePath = os.path.expandvars('$TTMODELS') or './ttmodels'
            searchPath.appendDirectory(Filename.fromOsSpecific(basePath + '/built/' + self.NewsBaseDir))
            searchPath.appendDirectory(Filename(self.NewsBaseDir))
        pfile = Filename(self.NewsIndexFilename)
        found = vfs.resolveFilename(pfile, searchPath)
        if not found:
            self.notify.warning('findNewsDir - no path: %s' % self.NewsIndexFilename)
            self.setErrorMessage(TTLocalizer.NewsPageErrorDownloadingFile % self.NewsIndexFilename)
            return None
        self.notify.debug('found index file %s' % pfile)
        realDir = pfile.getDirname()
        return realDir

    def load(self):
        self.loadBackground()

    def loadBackground(self):
        upsellBackground = loader.loadModel('phase_3.5/models/gui/tt_m_gui_ign_newsStatusBackground')
        imageScaleX = self.FrameDimensions[1] - self.FrameDimensions[0]
        imageScaleY = self.FrameDimensions[3] - self.FrameDimensions[2]
        self.backFrame = DirectFrame(parent=self.parent, image=upsellBackground, image_scale=(imageScaleX, 1, imageScaleY), frameColor=(1, 1, 1, 0), frameSize=self.FrameDimensions, pos=(0, 0, 0), relief=DGG.FLAT, text=TTLocalizer.NewsPageDownloadingNews1, text_scale=0.06, text_pos=(0, -0.4))

    def addDownloadingTextTask(self):
        self.removeDownloadingTextTask()
        task = taskMgr.doMethodLater(1, self.loadingTextTask, 'DirectNewsFrameDownloadingTextTask')
        task.startTime = globalClock.getFrameTime()
        self.loadingTextTask(task)

    def removeDownloadingTextTask(self):
        taskMgr.remove('DirectNewsFrameDownloadingTextTask')

    def loadMainPage(self):
        self.mainFrame = DirectFrame(parent=self.backFrame, frameSize=self.FrameDimensions, frameColor=(1, 0, 0, 1))

    def activate(self):
        if hasattr(self, 'createdTime') and self.createdTime < base.cr.inGameNewsMgr.getLatestIssue() and self.NewsOverHttp and not self.redownloadingNews:
            self.redownloadNews()
        else:
            self.addDownloadingTextTask()
        if self.needsParseNews and not self.redownloadingNews:
            self.parseNewsContent()
        self.active = True

    def deactivate(self):
        self.removeDownloadingTextTask()
        self.active = False

    def unload(self):
        self.removeDownloadingTextTask()
        result = taskMgr.remove(self.RedownloadTaskName)
        self.ignore('newsSnapshot')
        self.ignore('newsChangeWeek')
        self.ignore('newIssueOut')
        self.ignore('clientCleanup')

    def handleClientCleanup(self):
        pass

    def doSnapshot(self):
        pass

    def changeWeek(self, issueIndex):
        if 0 <= issueIndex and issueIndex < len(self.issues):
            self.issues[self.curIssueIndex].hide()
            self.issues[issueIndex].show()
            self.curIssueIndex = issueIndex

    def loadingTextTask(self, task):
        timeIndex = int(globalClock.getFrameTime() - task.startTime) % 3
        timeStrs = (TTLocalizer.NewsPageDownloadingNews0, TTLocalizer.NewsPageDownloadingNews1, TTLocalizer.NewsPageDownloadingNews2)
        textToDisplay = timeStrs[timeIndex] % int(self.percentDownloaded * 100)
        if self.backFrame['text'] != textToDisplay:
            if TTLocalizer.NewsPageDownloadingNewsSubstr in self.backFrame['text']:
                self.backFrame['text'] = textToDisplay
        return task.again

    def setErrorMessage(self, errText):
        self.backFrame['text'] = errText

    def redownloadNews(self):
        if self.redownloadingNews:
            self.notify.warning('averting potential crash redownloadNews called twice, just returning')
            return
        self.percentDownloaded = 0.0
        self.notify.info('starting redownloadNews')
        self.startRedownload = datetime.datetime.now()
        self.redownloadingNews = True
        self.addDownloadingTextTask()
        for issue in self.issues:
            issue.destroy()

        self.issues = []
        self.curIssueIndex = 0
        self.strFilenames = None
        self.needsParseNews = True
        self.newsUrl = self.getInGameNewsUrl()
        self.newsDir = Filename(self.findNewsDir())
        Filename(self.newsDir + '/.').makeDir()
        http = HTTPClient.getGlobalPtr()
        self.url = self.newsUrl + self.NewsIndexFilename
        self.ch = http.makeChannel(True)
        self.ch.beginGetDocument(self.url)
        self.rf = Ramfile()
        self.ch.downloadToRam(self.rf)
        taskMgr.remove(self.RedownloadTaskName)
        taskMgr.add(self.downloadIndexTask, self.RedownloadTaskName)
        return

    def downloadIndexTask(self, task):
        if self.ch.run():
            return task.cont
        if not self.ch.isValid():
            self.notify.warning('Unable to download %s' % self.url)
            self.redownloadingNews = False
            return task.done
        self.newsFiles = []
        filename = self.rf.readline()
        while filename:
            filename = filename.decode('utf-8').strip()
            if filename:
                self.newsFiles.append(filename)
            filename = self.rf.readline()

        del self.rf
        self.newsFiles.sort()
        self.newsIndexEntries = list(self.newsFiles)
        self.notify.info('Server lists %s news files' % len(self.newsFiles))
        self.notify.debug('self.newsIndexEntries=%s' % self.newsIndexEntries)
        self.readNewsCache()
        for basename in os.listdir(self.newsDir.toOsSpecific()):
            if basename != self.CacheIndexFilename and basename not in self.newsCache:
                junk = Filename(self.newsDir, basename)
                self.notify.info('Removing %s' % junk)
                junk.unlink()

        self.nextNewsFile = 0
        return self.downloadNextFile(task)

    def downloadNextFile(self, task):
        while self.nextNewsFile < len(self.newsFiles) and 'aaver' in self.newsFiles[self.nextNewsFile]:
            self.nextNewsFile += 1

        if self.nextNewsFile >= len(self.newsFiles):
            self.notify.info('Done downloading news.')
            self.percentDownloaded = 1
            del self.newsFiles
            del self.nextNewsFile
            del self.newsUrl
            del self.newsDir
            del self.ch
            del self.url
            if hasattr(self, 'filename'):
                del self.filename
            self.redownloadingNews = False
            if self.active:
                self.parseNewsContent()
            return task.done
        self.percentDownloaded = float(self.nextNewsFile) / float(len(self.newsFiles))
        self.filename = self.newsFiles[self.nextNewsFile]
        self.nextNewsFile += 1
        self.url = self.newsUrl + self.filename
        localFilename = Filename(self.newsDir, self.filename)
        self.notify.info('testing for %s' % localFilename.getFullpath())
        doc = DocumentSpec(self.url)
        if self.filename in self.newsCache:
            size, date = self.newsCache[self.filename]
            if date and localFilename.exists() and (size == 0 or localFilename.getFileSize() == size):
                doc.setDate(date)
                doc.setRequestMode(doc.RMNewer)
        self.ch.beginGetDocument(doc)
        self.ch.downloadToFile(localFilename)
        taskMgr.remove(self.RedownloadTaskName)
        taskMgr.add(self.downloadCurrentFileTask, self.RedownloadTaskName)

    def downloadCurrentFileTask(self, task):
        if self.ch.run():
            return task.cont
        if self.ch.getStatusCode() == 304:
            self.notify.info('already cached: %s' % self.filename)
            return self.downloadNextFile(task)
        localFilename = Filename(self.newsDir, self.filename)
        if not self.ch.isValid():
            self.notify.warning('Unable to download %s' % self.url)
            localFilename.unlink()
            if self.filename in self.newsCache:
                del self.newsCache[self.filename]
                self.saveNewsCache()
            return self.downloadNextFile(task)
        self.notify.info('downloaded %s' % self.filename)
        size = self.ch.getFileSize()
        doc = self.ch.getDocumentSpec()
        date = ''
        if doc.hasDate():
            date = doc.getDate().getString()
        self.newsCache[self.filename] = (size, date)
        self.saveNewsCache()
        return self.downloadNextFile(task)

    def readNewsCache(self):
        cacheIndexFilename = Filename(self.newsDir, self.CacheIndexFilename)
        self.newsCache = {}
        if cacheIndexFilename.isRegularFile():
            file = open(cacheIndexFilename.toOsSpecific(), 'r')
            for line in file.readlines():
                line = line.strip()
                keywords = line.split('\t')
                if len(keywords) == 3:
                    filename, size, date = keywords
                    if filename in self.newsFiles:
                        try:
                            size = int(size)
                        except ValueError:
                            size = 0

                        self.newsCache[filename] = (size, date)

    def saveNewsCache(self):
        cacheIndexFilename = Filename(self.newsDir, self.CacheIndexFilename)
        try:
            file = open(cacheIndexFilename.toOsSpecific(), 'w')
        except IOError as e:
            self.notify.warning('error opening news cache file %s: %s' % (cacheIndexFilename, str(e)))
            return

        for filename, (size, date) in list(self.newsCache.items()):
            print('%s\t%s\t%s' % (filename, size, date), file=file)

    def handleNewIssueOut(self):
        if hasattr(self, 'createdTime') and base.cr.inGameNewsMgr.getLatestIssue() < self.createdTime:
            self.createdTime = base.cr.inGameNewsMgr.getLatestIssue()
        elif self.NewsOverHttp and not self.redownloadingNews:
            if not self.active:
                self.redownloadNews()

    def getInGameNewsUrl(self):
        result = ConfigVariableString('fallback-news-url', 'http://cdn.toontown.disney.go.com/toontown/en/gamenews/').value
        override = ConfigVariableString('in-game-news-url', '').value
        if override:
            self.notify.info('got an override url,  using %s for in game news' % override)
            result = override
        else:
            try:
                launcherUrl = base.launcher.getValue('GAME_IN_GAME_NEWS_URL', '')
                if launcherUrl:
                    result = launcherUrl
                    self.notify.info('got GAME_IN_GAME_NEWS_URL from launcher using %s' % result)
                else:
                    self.notify.info('blank GAME_IN_GAME_NEWS_URL from launcher, using %s' % result)
            except:
                self.notify.warning('got exception getting GAME_IN_GAME_NEWS_URL from launcher, using %s' % result)

        return result

    def calcIssueVersion(self, dateStr):
        majorVer = 1
        minorVer = 0
        for entry in self.newsIndexEntries:
            if 'aaver' in entry and dateStr in entry:
                parts = entry.split('_')
                if len(parts) > 5:
                    try:
                        majorVer = int(parts[5])
                    except:
                        self.notify.warning('could not int %s' % parts[5])

                else:
                    self.notify.warning('expected more than 5 parts in %s' % entry)
                if len(parts) > 6:
                    try:
                        minorVer = int(parts[6])
                    except:
                        self.notify.warning('could not int %s' % parts[6])

                else:
                    self.notify.warning('expected more than 6 parts in %s' % entry)
                break

        return (majorVer, minorVer)
