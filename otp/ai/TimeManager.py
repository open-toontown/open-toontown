from pandac.PandaModules import *
from direct.showbase.DirectObject import *
from direct.distributed.ClockDelta import *
from direct.task import Task
from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from otp.otpbase import OTPGlobals
from direct.showbase import PythonUtil
from otp.otpbase.PythonUtil import describeException
from direct.showbase import GarbageReport
import base64
import time
import os
import sys
import re

class TimeManager(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('TimeManager')
    neverDisable = 1

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        self.updateFreq = base.config.GetFloat('time-manager-freq', 1800)
        self.minWait = base.config.GetFloat('time-manager-min-wait', 10)
        self.maxUncertainty = base.config.GetFloat('time-manager-max-uncertainty', 1)
        self.maxAttempts = base.config.GetInt('time-manager-max-attempts', 5)
        self.extraSkew = base.config.GetInt('time-manager-extra-skew', 0)
        if self.extraSkew != 0:
            self.notify.info('Simulating clock skew of %0.3f s' % self.extraSkew)
        self.reportFrameRateInterval = base.config.GetDouble('report-frame-rate-interval', 300.0)
        self.talkResult = 0
        self.thisContext = -1
        self.nextContext = 0
        self.attemptCount = 0
        self.start = 0
        self.lastAttempt = -self.minWait * 2
        self.setFrameRateInterval(self.reportFrameRateInterval)
        self._numClientGarbage = 0

    def generate(self):
        self._gotFirstTimeSync = False
        if self.cr.timeManager != None:
            self.cr.timeManager.delete()
        self.cr.timeManager = self
        DistributedObject.DistributedObject.generate(self)
        self.accept(OTPGlobals.SynchronizeHotkey, self.handleHotkey)
        self.accept('clock_error', self.handleClockError)
        if __dev__ and base.config.GetBool('enable-garbage-hotkey', 0):
            self.accept(OTPGlobals.DetectGarbageHotkey, self.handleDetectGarbageHotkey)
        if self.updateFreq > 0:
            self.startTask()
        return

    def announceGenerate(self):
        DistributedObject.DistributedObject.announceGenerate(self)
        self.synchronize('TimeManager.announceGenerate')

    def gotInitialTimeSync(self):
        return self._gotFirstTimeSync

    def disable(self):
        self.ignore(OTPGlobals.SynchronizeHotkey)
        if __dev__:
            self.ignore(OTPGlobals.DetectGarbageHotkey)
        self.ignore('clock_error')
        self.stopTask()
        taskMgr.remove('frameRateMonitor')
        if self.cr.timeManager == self:
            self.cr.timeManager = None
        del self._gotFirstTimeSync
        DistributedObject.DistributedObject.disable(self)
        return

    def delete(self):
        self.ignore(OTPGlobals.SynchronizeHotkey)
        self.ignore(OTPGlobals.DetectGarbageHotkey)
        self.ignore('clock_error')
        self.stopTask()
        taskMgr.remove('frameRateMonitor')
        if self.cr.timeManager == self:
            self.cr.timeManager = None
        DistributedObject.DistributedObject.delete(self)
        return

    def startTask(self):
        self.stopTask()
        taskMgr.doMethodLater(self.updateFreq, self.doUpdate, 'timeMgrTask')

    def stopTask(self):
        taskMgr.remove('timeMgrTask')

    def doUpdate(self, task):
        self.synchronize('timer')
        taskMgr.doMethodLater(self.updateFreq, self.doUpdate, 'timeMgrTask')
        return Task.done

    def handleHotkey(self):
        self.lastAttempt = -self.minWait * 2
        if self.synchronize('user hotkey'):
            self.talkResult = 1
        else:
            base.localAvatar.setChatAbsolute('Too soon.', CFSpeech | CFTimeout)

    def handleClockError(self):
        self.synchronize('clock error')

    def synchronize(self, description):
        now = globalClock.getRealTime()
        if now - self.lastAttempt < self.minWait:
            self.notify.debug('Not resyncing (too soon): %s' % description)
            return 0
        self.talkResult = 0
        self.thisContext = self.nextContext
        self.attemptCount = 0
        self.nextContext = self.nextContext + 1 & 255
        self.notify.info('Clock sync: %s' % description)
        self.start = now
        self.lastAttempt = now
        self.sendUpdate('requestServerTime', [self.thisContext])
        return 1

    def serverTime(self, context, timestamp, timeOfDay):
        end = globalClock.getRealTime()
        aiTimeSkew = timeOfDay - self.cr.getServerTimeOfDay()
        if context != self.thisContext:
            self.notify.info('Ignoring TimeManager response for old context %d' % context)
            return
        elapsed = end - self.start
        self.attemptCount += 1
        self.notify.info('Clock sync roundtrip took %0.3f ms' % (elapsed * 1000.0))
        self.notify.info('AI time delta is %s from server delta' % PythonUtil.formatElapsedSeconds(aiTimeSkew))
        average = (self.start + end) / 2.0 - self.extraSkew
        uncertainty = (end - self.start) / 2.0 + abs(self.extraSkew)
        globalClockDelta.resynchronize(average, timestamp, uncertainty)
        self.notify.info('Local clock uncertainty +/- %.3f s' % globalClockDelta.getUncertainty())
        if globalClockDelta.getUncertainty() > self.maxUncertainty:
            if self.attemptCount < self.maxAttempts:
                self.notify.info('Uncertainty is too high, trying again.')
                self.start = globalClock.getRealTime()
                self.sendUpdate('requestServerTime', [self.thisContext])
                return
            self.notify.info('Giving up on uncertainty requirement.')
        if self.talkResult:
            base.localAvatar.setChatAbsolute('latency %0.0f ms, sync \xc2\xb1%0.0f ms' % (elapsed * 1000.0, globalClockDelta.getUncertainty() * 1000.0), CFSpeech | CFTimeout)
        self._gotFirstTimeSync = True
        messenger.send('gotTimeSync')

    def setDisconnectReason(self, disconnectCode):
        self.notify.info('Client disconnect reason %s.' % disconnectCode)
        self.sendUpdate('setDisconnectReason', [disconnectCode])

    def setExceptionInfo(self):
        info = describeException()
        self.notify.info('Client exception: %s' % info)
        self.sendUpdate('setExceptionInfo', [info])
        self.cr.flush()

    def setStackDump(self, dump):
        self.notify.debug('Stack dump: %s' % fastRepr(dump))
        maxLen = 900
        dataLeft = base64.b64encode(dump)
        index = 0
        while dataLeft:
            if len(dataLeft) >= maxLen:
                data = dataLeft[:maxLen]
                dataLeft = dataLeft[maxLen:]
            else:
                data = dataLeft
                dataLeft = None
            self.sendUpdate('setStackDump', [index, data])
            index += 1
            self.cr.flush()

        return

    def d_setSignature(self, signature, hash, pyc):
        self.sendUpdate('setSignature', [signature, hash, pyc])

    def sendCpuInfo(self):
        if not base.pipe:
            return
        di = base.pipe.getDisplayInformation()
        if di.getNumCpuCores() == 0 and hasattr(base.pipe, 'lookupCpuData'):
            base.pipe.lookupCpuData()
            di = base.pipe.getDisplayInformation()
        di.updateCpuFrequency(0)
        try:
            cacheStatus = preloadCache()
        except NameError:
            cacheStatus = ''

        ooghz = 1e-09
        cpuSpeed = (di.getMaximumCpuFrequency() * ooghz, di.getCurrentCpuFrequency() * ooghz)
        numCpuCores = di.getNumCpuCores()
        numLogicalCpus = di.getNumLogicalCpus()
        info = '%s|%s|%d|%d|%s|%s cpus' % (di.getCpuVendorString(),
         di.getCpuBrandString(),
         di.getCpuVersionInformation(),
         di.getCpuBrandIndex(),
         '%0.03f,%0.03f' % cpuSpeed,
         '%d,%d' % (numCpuCores, numLogicalCpus))
        print('cpu info: %s' % info)
        self.sendUpdate('setCpuInfo', [info, cacheStatus])

    def setFrameRateInterval(self, frameRateInterval):
        if frameRateInterval == 0:
            return
        if not base.frameRateMeter:
            maxFrameRateInterval = base.config.GetDouble('max-frame-rate-interval', 30.0)
            globalClock.setAverageFrameRateInterval(min(frameRateInterval, maxFrameRateInterval))
        taskMgr.remove('frameRateMonitor')
        taskMgr.doMethodLater(frameRateInterval, self.frameRateMonitor, 'frameRateMonitor')

    def frameRateMonitor(self, task):
        from otp.avatar.Avatar import Avatar
        vendorId = 0
        deviceId = 0
        processMemory = 0
        pageFileUsage = 0
        physicalMemory = 0
        pageFaultCount = 0
        osInfo = (os.name,
         0,
         0,
         0)
        cpuSpeed = (0, 0)
        numCpuCores = 0
        numLogicalCpus = 0
        apiName = 'None'
        if getattr(base, 'pipe', None):
            di = base.pipe.getDisplayInformation()
            if di.getDisplayState() == DisplayInformation.DSSuccess:
                vendorId = di.getVendorId()
                deviceId = di.getDeviceId()
            di.updateMemoryInformation()
            oomb = 1.0 / (1024.0 * 1024.0)
            processMemory = di.getProcessMemory() * oomb
            pageFileUsage = di.getPageFileUsage() * oomb
            physicalMemory = di.getPhysicalMemory() * oomb
            pageFaultCount = di.getPageFaultCount() / 1000.0
            osInfo = (os.name,
             di.getOsPlatformId(),
             di.getOsVersionMajor(),
             di.getOsVersionMinor())
            if sys.platform == 'darwin':
                osInfo = self.getMacOsInfo(osInfo)
            di.updateCpuFrequency(0)
            ooghz = 1e-09
            cpuSpeed = (di.getMaximumCpuFrequency() * ooghz, di.getCurrentCpuFrequency() * ooghz)
            numCpuCores = di.getNumCpuCores()
            numLogicalCpus = di.getNumLogicalCpus()
            apiName = base.pipe.getInterfaceName()
        self.d_setFrameRate(max(0, globalClock.getAverageFrameRate()), max(0, globalClock.calcFrameRateDeviation()), len(Avatar.ActiveAvatars), base.locationCode or '', max(0, time.time() - base.locationCodeChanged), max(0, globalClock.getRealTime()), base.gameOptionsCode, vendorId, deviceId, processMemory, pageFileUsage, physicalMemory, pageFaultCount, osInfo, cpuSpeed, numCpuCores, numLogicalCpus, apiName)
        return task.again

    def d_setFrameRate(self, fps, deviation, numAvs, locationCode, timeInLocation, timeInGame, gameOptionsCode, vendorId, deviceId, processMemory, pageFileUsage, physicalMemory, pageFaultCount, osInfo, cpuSpeed, numCpuCores, numLogicalCpus, apiName):
        info = '%0.1f fps|%0.3fd|%s avs|%s|%d|%d|%s|0x%04x|0x%04x|%0.1fMB|%0.1fMB|%0.1fMB|%d|%s|%s|%s cpus|%s' % (fps,
         deviation,
         numAvs,
         locationCode,
         timeInLocation,
         timeInGame,
         gameOptionsCode,
         vendorId,
         deviceId,
         processMemory,
         pageFileUsage,
         physicalMemory,
         pageFaultCount,
         '%s.%d.%d.%d' % osInfo,
         '%0.03f,%0.03f' % cpuSpeed,
         '%d,%d' % (numCpuCores, numLogicalCpus),
         apiName)
        print('frame rate: %s' % info)
        self.sendUpdate('setFrameRate', [fps,
         deviation,
         numAvs,
         locationCode,
         timeInLocation,
         timeInGame,
         gameOptionsCode,
         vendorId,
         deviceId,
         processMemory,
         pageFileUsage,
         physicalMemory,
         pageFaultCount,
         osInfo,
         cpuSpeed,
         numCpuCores,
         numLogicalCpus,
         apiName])

    if __dev__:

        def handleDetectGarbageHotkey(self):
            self._numClientGarbage = GarbageReport.b_checkForGarbageLeaks(wantReply=True)
            if self._numClientGarbage:
                s = '%s client garbage cycles found, see log' % self._numClientGarbage
            else:
                s = '0 client garbage cycles found'
            localAvatar.setChatAbsolute(s, CFSpeech | CFTimeout)

        def d_checkForGarbageLeaks(self, wantReply):
            self.sendUpdate('checkForGarbageLeaks', [wantReply])

        def setNumAIGarbageLeaks(self, numLeaks):
            if self._numClientGarbage and numLeaks:
                s = '%s client and %s AI garbage cycles found, see logs' % (self._numClientGarbage, numLeaks)
            elif numLeaks:
                s = '0 client and %s AI garbage cycles found, see log' % numLeaks
            else:
                s = '0 client and 0 AI garbage cycles found'
            localAvatar.setChatAbsolute(s, CFSpeech | CFTimeout)

    def d_setClientGarbageLeak(self, num, description):
        self.sendUpdate('setClientGarbageLeak', [num, description])

    def getMacOsInfo(self, defaultOsInfo):
        result = defaultOsInfo
        try:
            theFile = open('/System/Library/CoreServices/SystemVersion.plist')
        except IOError:
            pass
        else:
            key = re.search('<key>ProductUserVisibleVersion</key>\\s*' + '<string>(.*?)</string>', theFile.read())
            theFile.close()
            if key is not None:
                try:
                    verString = key.group(1)
                    parts = verString.split('.')
                    major = int(parts[0])
                    minor = int(parts[1])
                    bugfix = int(parts[2])
                    result = (sys.platform,
                     bugfix,
                     major,
                     minor)
                except Exception as e:
                    self.notify.debug('getMacOsInfo %s' % str(e))

        self.notify.debug('getMacOsInfo returning %s' % str(result))
        return result
