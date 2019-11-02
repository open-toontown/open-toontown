from direct.directnotify import DirectNotifyGlobal
from pandac.PandaModules import ConfigVariableBool
from direct.task import Task
from string import maketrans
import cPickle
import os
import sys
import anydbm
import time

class DataStore:
    QueryTypes = []
    QueryTypes = dict(zip(QueryTypes, range(len(QueryTypes))))

    @classmethod
    def addQueryTypes(cls, typeStrings):
        superTypes = zip(cls.QueryTypes.values(), cls.QueryTypes.keys())
        superTypes.sort()
        newTypes = [ item[1] for item in superTypes ] + typeStrings
        newTypes = dict(zip(newTypes, range(1 + len(newTypes))))
        return newTypes

    notify = DirectNotifyGlobal.directNotify.newCategory('DataStore')
    wantAnyDbm = ConfigVariableBool('want-ds-anydbm', 1).getValue()

    def __init__(self, filepath, writePeriod = 300, writeCountTrigger = 100):
        self.filepath = filepath
        self.writePeriod = writePeriod
        self.writeCountTrigger = writeCountTrigger
        self.writeCount = 0
        self.data = None
        self.className = self.__class__.__name__
        if self.wantAnyDbm:
            self.filepath += '-anydbm'
            self.notify.debug('anydbm default module used: %s ' % anydbm._defaultmod.__name__)
        self.open()
        return

    def readDataFromFile(self):
        if self.wantAnyDbm:
            try:
                if os.path.exists(self.filepath):
                    self.data = anydbm.open(self.filepath, 'w')
                    self.notify.debug('Opening existing anydbm database at: %s.' % (self.filepath,))
                else:
                    self.data = anydbm.open(self.filepath, 'c')
                    self.notify.debug('Creating new anydbm database at: %s.' % (self.filepath,))
            except anydbm.error:
                self.notify.warning('Cannot open anydbm database at: %s.' % (self.filepath,))

        else:
            try:
                file = open(self.filepath + '.bu', 'r')
                self.notify.debug('Opening backup pickle data file at %s.' % (self.filepath + '.bu',))
                if os.path.exists(self.filepath):
                    os.remove(self.filepath)
            except IOError:
                try:
                    file = open(self.filepath, 'r')
                    self.notify.debug('Opening old pickle data file at %s..' % (self.filepath,))
                except IOError:
                    file = None
                    self.notify.debug('New pickle data file will be written to %s.' % (self.filepath,))

            if file:
                data = cPickle.load(file)
                file.close()
                self.data = data
            else:
                self.data = {}
        return

    def writeDataToFile(self):
        if self.data is not None:
            self.notify.debug('Data is now synced with disk at %s' % self.filepath)
            if self.wantAnyDbm:
                self.data.sync()
            else:
                try:
                    backuppath = self.filepath + '.bu'
                    if os.path.exists(self.filepath):
                        os.rename(self.filepath, backuppath)
                    outfile = open(self.filepath, 'w')
                    cPickle.dump(self.data, outfile)
                    outfile.close()
                    if os.path.exists(backuppath):
                        os.remove(backuppath)
                except EnvironmentError:
                    self.notify.warning(str(sys.exc_info()[1]))

        else:
            self.notify.warning('No data to write. Aborting sync.')
        return

    def syncTask(self, task):
        task.timeElapsed += globalClock.getDt()
        if task.timeElapsed > self.writePeriod:
            if self.writeCount:
                self.writeDataToFile()
                self.resetWriteCount()
            task.timeElapsed = 0.0
        if self.writeCount > self.writeCountTrigger:
            self.writeDataToFile()
            self.resetWriteCount()
            task.timeElapsed = 0.0
        return Task.cont

    def incrementWriteCount(self):
        self.writeCount += 1

    def resetWriteCount(self):
        self.writeCount = 0

    def close(self):
        if self.data is not None:
            self.writeDataToFile()
            if self.wantAnyDbm:
                self.data.close()
            taskMgr.remove('%s-syncTask' % (self.className,))
            self.data = None
        return

    def open(self):
        self.close()
        self.readDataFromFile()
        self.resetWriteCount()
        taskMgr.remove('%s-syncTask' % (self.className,))
        t = taskMgr.add(self.syncTask, '%s-syncTask' % (self.className,))
        t.timeElapsed = 0.0

    def reset(self):
        self.destroy()
        self.open()

    def destroy(self):
        self.close()
        if self.wantAnyDbm:
            lt = time.asctime(time.localtime())
            trans = maketrans(': ', '__')
            t = lt.translate(trans)
            head, tail = os.path.split(self.filepath)
            newFileName = 'UDStoreBak' + t
            if os.path.exists(self.filepath):
                try:
                    os.rename(tail, newFileName)
                    uber.air.writeServerEvent('Uberdog data store Info', 0, 'Creating backup of file: %s saving as: %s' % (tail, newFileName))
                except:
                    uber.air.writeServerEvent('Uberdog data store Info', 0, 'Unable to create backup of file: %s ' % tail)

            else:
                files = os.listdir(head)
                for file in files:
                    if file.find(tail) > -1:
                        filename, ext = os.path.splitext(file)
                        try:
                            os.rename(file, newFileName + ext)
                            uber.air.writeServerEvent('Uberdog data store Info', 0, 'Creating backup of file: %s saving as: %s' % (file, newFileName + ext))
                        except:
                            uber.air.writeServerEvent('Uberdog data store Info', 0, 'Unable to create backup of file: %s ' % newFileName + ext)

        else:
            if os.path.exists(self.filepath + '.bu'):
                os.remove(self.filepath + '.bu')
            if os.path.exists(self.filepath):
                os.remove(self.filepath)

    def query(self, query):
        if self.data is not None:
            qData = cPickle.loads(query)
            results = self.handleQuery(qData)
            qResults = cPickle.dumps(results)
        else:
            results = None
            qResults = cPickle.dumps(results)
        return qResults

    def handleQuery(self, query):
        results = None
        return results
