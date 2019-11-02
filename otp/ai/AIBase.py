from pandac.PandaModules import *
from direct.directnotify.DirectNotifyGlobal import *
from direct.showbase.MessengerGlobal import *
from direct.showbase.BulletinBoardGlobal import *
from direct.task.TaskManagerGlobal import *
from direct.showbase.JobManagerGlobal import *
from direct.showbase.EventManagerGlobal import *
from direct.showbase.PythonUtil import *
from direct.showbase import PythonUtil
from direct.interval.IntervalManager import ivalMgr
from direct.task import Task
from direct.showbase import EventManager
from direct.showbase import ExceptionVarDump
import math
import sys
import time
import gc

class AIBase:
    notify = directNotify.newCategory('AIBase')

    def __init__(self):
        self.config = getConfigShowbase()
        __builtins__['__dev__'] = self.config.GetBool('want-dev', 0)
        logStackDump = (self.config.GetBool('log-stack-dump', (not __dev__)) or self.config.GetBool('ai-log-stack-dump', (not __dev__)))
        uploadStackDump = self.config.GetBool('upload-stack-dump', 0)
        if logStackDump or uploadStackDump:
            ExceptionVarDump.install(logStackDump, uploadStackDump)
        if self.config.GetBool('use-vfs', 1):
            vfs = VirtualFileSystem.getGlobalPtr()
        else:
            vfs = None
        self.wantTk = self.config.GetBool('want-tk', 0)
        self.AISleep = self.config.GetFloat('ai-sleep', 0.04)
        self.AIRunningNetYield = self.config.GetBool('ai-running-net-yield', 0)
        self.AIForceSleep = self.config.GetBool('ai-force-sleep', 0)
        self.eventMgr = eventMgr
        self.messenger = messenger
        self.bboard = bulletinBoard
        self.taskMgr = taskMgr
        Task.TaskManager.taskTimerVerbose = self.config.GetBool('task-timer-verbose', 0)
        Task.TaskManager.extendedExceptions = self.config.GetBool('extended-exceptions', 0)
        self.sfxManagerList = None
        self.musicManager = None
        self.jobMgr = jobMgr
        self.hidden = NodePath('hidden')
        self.graphicsEngine = GraphicsEngine()
        globalClock = ClockObject.getGlobalClock()
        self.trueClock = TrueClock.getGlobalPtr()
        globalClock.setRealTime(self.trueClock.getShortTime())
        globalClock.setAverageFrameRateInterval(30.0)
        globalClock.tick()
        taskMgr.globalClock = globalClock
        __builtins__['ostream'] = Notify.out()
        __builtins__['globalClock'] = globalClock
        __builtins__['vfs'] = vfs
        __builtins__['hidden'] = self.hidden
        AIBase.notify.info('__dev__ == %s' % __dev__)
        PythonUtil.recordFunctorCreationStacks()
        __builtins__['wantTestObject'] = self.config.GetBool('want-test-object', 0)
        self.wantStats = self.config.GetBool('want-pstats', 0)
        Task.TaskManager.pStatsTasks = self.config.GetBool('pstats-tasks', 0)
        taskMgr.resumeFunc = PStatClient.resumeAfterPause
        defaultValue = 1
        if __dev__:
            defaultValue = 0
        wantFakeTextures = self.config.GetBool('want-fake-textures-ai', defaultValue)
        if wantFakeTextures:
            loadPrcFileData('aibase', 'textures-header-only 1')
        self.wantPets = self.config.GetBool('want-pets', 1)
        if self.wantPets:
            if game.name == 'toontown':
                from toontown.pets import PetConstants
                self.petMoodTimescale = self.config.GetFloat('pet-mood-timescale', 1.0)
                self.petMoodDriftPeriod = self.config.GetFloat('pet-mood-drift-period', PetConstants.MoodDriftPeriod)
                self.petThinkPeriod = self.config.GetFloat('pet-think-period', PetConstants.ThinkPeriod)
                self.petMovePeriod = self.config.GetFloat('pet-move-period', PetConstants.MovePeriod)
                self.petPosBroadcastPeriod = self.config.GetFloat('pet-pos-broadcast-period', PetConstants.PosBroadcastPeriod)
        self.wantBingo = self.config.GetBool('want-fish-bingo', 1)
        self.wantKarts = self.config.GetBool('wantKarts', 1)
        self.newDBRequestGen = self.config.GetBool('new-database-request-generate', 1)
        self.waitShardDelete = self.config.GetBool('wait-shard-delete', 1)
        self.blinkTrolley = self.config.GetBool('blink-trolley', 0)
        self.fakeDistrictPopulations = self.config.GetBool('fake-district-populations', 0)
        self.wantSwitchboard = self.config.GetBool('want-switchboard', 0)
        self.wantSwitchboardHacks = self.config.GetBool('want-switchboard-hacks', 0)
        self.GEMdemoWhisperRecipientDoid = self.config.GetBool('gem-demo-whisper-recipient-doid', 0)
        self.sqlAvailable = self.config.GetBool('sql-available', 1)
        self.createStats()
        self.restart()
        return

    def setupCpuAffinities(self, minChannel):
        if game.name == 'uberDog':
            affinityMask = self.config.GetInt('uberdog-cpu-affinity-mask', -1)
        else:
            affinityMask = self.config.GetInt('ai-cpu-affinity-mask', -1)
        if affinityMask != -1:
            TrueClock.getGlobalPtr().setCpuAffinity(affinityMask)
        else:
            autoAffinity = self.config.GetBool('auto-single-cpu-affinity', 0)
            if game.name == 'uberDog':
                affinity = self.config.GetInt('uberdog-cpu-affinity', -1)
                if autoAffinity and affinity == -1:
                    affinity = 2
            else:
                affinity = self.config.GetInt('ai-cpu-affinity', -1)
                if autoAffinity and affinity == -1:
                    affinity = 1
            if affinity != -1:
                TrueClock.getGlobalPtr().setCpuAffinity(1 << affinity)
            elif autoAffinity:
                if game.name == 'uberDog':
                    channelSet = int(minChannel / 1000000)
                    channelSet -= 240
                    affinity = channelSet + 3
                    TrueClock.getGlobalPtr().setCpuAffinity(1 << affinity % 4)

    def taskManagerDoYield(self, frameStartTime, nextScheuledTaksTime):
        minFinTime = frameStartTime + self.MaxEpockSpeed
        if nextScheuledTaksTime > 0 and nextScheuledTaksTime < minFinTime:
            minFinTime = nextScheuledTaksTime
        delta = minFinTime - globalClock.getRealTime()
        while delta > 0.002:
            time.sleep(delta)
            delta = minFinTime - globalClock.getRealTime()

    def createStats(self, hostname = None, port = None):
        if not self.wantStats:
            return False
        if PStatClient.isConnected():
            PStatClient.disconnect()
        if hostname is None:
            hostname = ''
        if port is None:
            port = -1
        PStatClient.connect(hostname, port)
        return PStatClient.isConnected()

    def __sleepCycleTask(self, task):
        time.sleep(self.AISleep)
        return Task.cont

    def __resetPrevTransform(self, state):
        PandaNode.resetAllPrevTransform()
        return Task.cont

    def __ivalLoop(self, state):
        ivalMgr.step()
        return Task.cont

    def __igLoop(self, state):
        self.graphicsEngine.renderFrame()
        return Task.cont

    def shutdown(self):
        self.taskMgr.remove('ivalLoop')
        self.taskMgr.remove('igLoop')
        self.taskMgr.remove('aiSleep')
        self.eventMgr.shutdown()

    def restart(self):
        self.shutdown()
        self.taskMgr.add(self.__resetPrevTransform, 'resetPrevTransform', priority=-51)
        self.taskMgr.add(self.__ivalLoop, 'ivalLoop', priority=20)
        self.taskMgr.add(self.__igLoop, 'igLoop', priority=50)
        if self.AISleep >= 0 and (not self.AIRunningNetYield or self.AIForceSleep):
            self.taskMgr.add(self.__sleepCycleTask, 'aiSleep', priority=55)
        self.eventMgr.restart()

    def getRepository(self):
        return self.air

    def run(self):
        self.taskMgr.run()
