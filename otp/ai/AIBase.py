from panda3d.core import *
from direct.directnotify.DirectNotifyGlobal import *
from direct.showbase.MessengerGlobal import *
from direct.showbase.BulletinBoardGlobal import *
from direct.task.TaskManagerGlobal import *
from direct.showbase.JobManagerGlobal import *
from direct.showbase.EventManagerGlobal import *
from direct.showbase.PythonUtil import *
from otp.otpbase import PythonUtil
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
        __builtins__['__dev__'] = ConfigVariableBool('want-dev', 0).getValue()
        __builtins__['__astron__'] = ConfigVariableBool('astron-support', 1).getValue()
        __builtins__['__execWarnings__'] = ConfigVariableBool('want-exec-warnings', 0).getValue()
        logStackDump = (ConfigVariableBool('log-stack-dump', (not __debug__)).getValue() or ConfigVariableBool('ai-log-stack-dump', (not __debug__)).getValue())
        uploadStackDump = ConfigVariableBool('upload-stack-dump', 0).getValue()
        if logStackDump or uploadStackDump:
            ExceptionVarDump.install(logStackDump, uploadStackDump)
        if ConfigVariableBool('use-vfs', 1).getValue():
            vfs = VirtualFileSystem.getGlobalPtr()
        else:
            vfs = None
        self.wantTk = ConfigVariableBool('want-tk', 0).getValue()
        self.AISleep = ConfigVariableDouble('ai-sleep', 0.04).getValue()
        self.AIRunningNetYield = ConfigVariableBool('ai-running-net-yield', 0).getValue()
        self.AIForceSleep = ConfigVariableBool('ai-force-sleep', 0).getValue()
        self.eventMgr = eventMgr
        self.messenger = messenger
        self.bboard = bulletinBoard
        self.taskMgr = taskMgr
        Task.TaskManager.taskTimerVerbose = ConfigVariableBool('task-timer-verbose', 0).getValue()
        Task.TaskManager.extendedExceptions = ConfigVariableBool('extended-exceptions', 0).getValue()
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
        AIBase.notify.info('__astron__ == %s' % __astron__)
        PythonUtil.recordFunctorCreationStacks()
        __builtins__['wantTestObject'] = ConfigVariableBool('want-test-object', 0).getValue()
        self.wantStats = ConfigVariableBool('want-pstats', 0).getValue()
        Task.TaskManager.pStatsTasks = ConfigVariableBool('pstats-tasks', 0).getValue()
        taskMgr.resumeFunc = PStatClient.resumeAfterPause
        defaultValue = 1
        if __dev__:
            defaultValue = 0
        wantFakeTextures = ConfigVariableBool('want-fake-textures-ai', defaultValue).getValue()
        if wantFakeTextures:
            loadPrcFileData('aibase', 'textures-header-only 1')
        self.wantPets = ConfigVariableBool('want-pets', 1).getValue()
        if self.wantPets:
            if game.name == 'toontown':
                from toontown.pets import PetConstants
                self.petMoodTimescale = ConfigVariableDouble('pet-mood-timescale', 1.0).getValue()
                self.petMoodDriftPeriod = ConfigVariableDouble('pet-mood-drift-period', PetConstants.MoodDriftPeriod).getValue()
                self.petThinkPeriod = ConfigVariableDouble('pet-think-period', PetConstants.ThinkPeriod).getValue()
                self.petMovePeriod = ConfigVariableDouble('pet-move-period', PetConstants.MovePeriod).getValue()
                self.petPosBroadcastPeriod = ConfigVariableDouble('pet-pos-broadcast-period', PetConstants.PosBroadcastPeriod).getValue()
        self.wantBingo = ConfigVariableBool('want-fish-bingo', 1).getValue()
        self.wantKarts = ConfigVariableBool('wantKarts', 1).getValue()
        self.newDBRequestGen = ConfigVariableBool('new-database-request-generate', 1).getValue()
        self.waitShardDelete = ConfigVariableBool('wait-shard-delete', 1).getValue()
        self.blinkTrolley = ConfigVariableBool('blink-trolley', 0).getValue()
        self.fakeDistrictPopulations = ConfigVariableBool('fake-district-populations', 0).getValue()
        self.wantSwitchboard = ConfigVariableBool('want-switchboard', 0).getValue()
        self.wantSwitchboardHacks = ConfigVariableBool('want-switchboard-hacks', 0).getValue()
        self.GEMdemoWhisperRecipientDoid = ConfigVariableBool('gem-demo-whisper-recipient-doid', 0).getValue()
        self.sqlAvailable = ConfigVariableBool('sql-available', 1).getValue()
        self.createStats()
        self.restart()
        return

    def setupCpuAffinities(self, minChannel):
        if game.name == 'uberDog':
            affinityMask = ConfigVariableInt('uberdog-cpu-affinity-mask', -1).getValue()
        else:
            affinityMask = ConfigVariableInt('ai-cpu-affinity-mask', -1).getValue()
        if affinityMask != -1:
            TrueClock.getGlobalPtr().setCpuAffinity(affinityMask)
        else:
            autoAffinity = ConfigVariableBool('auto-single-cpu-affinity', 0).getValue()
            if game.name == 'uberDog':
                affinity = ConfigVariableInt('uberdog-cpu-affinity', -1).getValue()
                if autoAffinity and affinity == -1:
                    affinity = 2
            else:
                affinity = ConfigVariableInt('ai-cpu-affinity', -1).getValue()
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
