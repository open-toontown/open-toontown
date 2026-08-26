import datetime
from panda3d.core import *
from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObject

class StreetSign(DistributedObject.DistributedObject):
    RedownloadTaskName = 'RedownloadStreetSign'
    StreetSignFileName = config.GetString('street-sign-filename', 'texture.jpg')
    StreetSignBaseDir = config.GetString('street-sign-base-dir', 'sign')
    StreetSignUrl = base.config.GetString('street-sign-url', 'http://cdn.toontown.disney.go.com/toontown/en/street-signs/img/')
    notify = DirectNotifyGlobal.directNotify.newCategory('StreetSign')

    def __init__(self):
        self.downloadingStreetSign = False
        self.percentDownloaded = 0.0
        self.startDownload = datetime.datetime.now()
        self.endDownload = datetime.datetime.now()
        self.notify.info('Street sign url is %s' % self.StreetSignUrl)
        self.redownloadStreetSign()

    def replaceTexture(self):
        searchPath = DSearchPath()
        searchPath.appendDirectory(self.directory)

    def redownloadStreetSign(self):
        self.precentDownload = 0.0
        self.startRedownload = datetime.datetime.now()
        self.downloadingStreetSign = True
        Filename(self.StreetSignBaseDir + '/.').makeDir()
        http = HTTPClient.getGlobalPtr()
        self.url = self.StreetSignUrl + self.StreetSignFileName
        self.ch = http.makeChannel(True)
        localFilename = Filename(self.StreetSignBaseDir, self.StreetSignFileName)
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
                    self.notify.info('Street Sign is up to date')
        if outOfDate and self.ch.isValid():
            self.ch.beginGetDocument(doc)
            self.ch.downloadToFile(localFilename)
            taskMgr.add(self.downloadStreetSignTask, self.RedownloadTaskName)

    def downloadStreetSignTask(self, task):
        if self.ch.run():
            return task.cont
        doc = self.ch.getDocumentSpec()
        date = ''
        if doc.hasDate():
            date = doc.getDate().getString()
        if not self.ch.isValid():
            self.redownloadingStreetSign = False
            return task.done
        self.notify.info('Down downloading street sign')
        return task.done
