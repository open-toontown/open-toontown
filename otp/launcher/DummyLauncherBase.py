from pandac.PandaModules import *
import string
from direct.showbase.MessengerGlobal import *
from direct.showbase.DirectObject import DirectObject
from direct.showbase.EventManagerGlobal import *
from direct.task.TaskManagerGlobal import *
from direct.task.Task import Task

class DummyLauncherBase:

    def __init__(self):
        self.logPrefix = ''
        self._downloadComplete = False
        self.phaseComplete = {}
        for phase in self.LauncherPhases:
            self.phaseComplete[phase] = 0

        self.firstPhase = self.LauncherPhases[0]
        self.finalPhase = self.LauncherPhases[-1]
        self.launcherFileDbHash = HashVal()
        self.serverDbFileHash = HashVal()
        self.setPandaErrorCode(0)
        self.setServerVersion('dev')

    def isDummy(self):
        return 1

    def startFakeDownload(self):
        if ConfigVariableBool('fake-downloads', 0).getValue():
            duration = ConfigVariableDouble('fake-download-duration', 60).getValue()
            self.fakeDownload(duration)
        else:
            for phase in self.LauncherPhases:
                self.phaseComplete[phase] = 100

            self.downloadDoneTask(None)
        return

    def isTestServer(self):
        return base.config.GetBool('is-test-server', 0)

    def setPhaseCompleteArray(self, newPhaseComplete):
        self.phaseComplete = newPhaseComplete

    def setPhaseComplete(self, phase, percent):
        self.phaseComplete[phase] = percent

    def getPhaseComplete(self, phase):
        return self.phaseComplete[phase] >= 100

    def setPandaWindowOpen(self):
        self.windowOpen = 1

    def setPandaErrorCode(self, code):
        self.pandaErrorCode = code

    def getPandaErrorCode(self):
        return self.pandaErrorCode

    def setDisconnectDetailsNormal(self):
        self.disconnectCode = 0
        self.disconnectMsg = 'normal'

    def setDisconnectDetails(self, newCode, newMsg):
        self.disconnectCode = newCode
        self.disconnectMsg = newMsg

    def setServerVersion(self, version):
        self.ServerVersion = version

    def getServerVersion(self):
        return self.ServerVersion

    def getIsNewInstallation(self):
        return base.config.GetBool('new-installation', 0)

    def setIsNotNewInstallation(self):
        pass

    def getLastLogin(self):
        if hasattr(self, 'lastLogin'):
            return self.lastLogin
        return ''

    def setLastLogin(self, login):
        self.lastLogin = login

    def setUserLoggedIn(self):
        self.userLoggedIn = 1

    def setPaidUserLoggedIn(self):
        self.paidUserLoggedIn = 1

    def getGameServer(self):
        return '206.16.11.19'

    def getAccountServer(self):
        return ''

    def getDeployment(self):
        return 'US'

    def getBlue(self):
        return None

    def getPlayToken(self):
        return None

    def getDISLToken(self):
        return None

    def fakeDownloadPhaseTask(self, task):
        percentComplete = min(100, int(round(task.time / float(task.timePerPhase) * 100)))
        self.setPhaseComplete(task.phase, percentComplete)
        messenger.send('launcherPercentPhaseComplete', [task.phase,
         percentComplete,
         0,
         0])
        if percentComplete >= 100.0:
            messenger.send('phaseComplete-' + repr((task.phase)))
            return Task.done
        else:
            return Task.cont

    def downloadDoneTask(self, task):
        self._downloadComplete = True
        messenger.send('launcherAllPhasesComplete')
        return Task.done

    def fakeDownload(self, timePerPhase):
        self.phaseComplete = {1: 100,
         2: 100,
         3: 0,
         3.5: 0,
         4: 0,
         5: 0,
         5.5: 0,
         6: 0,
         7: 0,
         8: 0,
         9: 0,
         10: 0,
         11: 0,
         12: 0,
         13: 0}
        phaseTaskList = []
        firstPhaseIndex = self.LauncherPhases.index(self.firstPhase)
        for phase in self.LauncherPhases[firstPhaseIndex:]:
            phaseTask = Task(self.fakeDownloadPhaseTask, 'phaseDownload' + str(phase))
            phaseTask.timePerPhase = timePerPhase
            phaseTask.phase = phase
            phaseTaskList.append(phaseTask)

        phaseTaskList.append(Task(self.downloadDoneTask))
        downloadSequence = Task.sequence(*phaseTaskList)
        taskMgr.remove('downloadSequence')
        taskMgr.add(downloadSequence, 'downloadSequence')
