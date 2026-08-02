import json
import os

_WRITE_TASK = 'persist-useropt-json'


class Settings:

    def __init__(self):
        self.__settings = {}
        self.__filename = self._resolveFilename()

    def _resolveFilename(self):
        """Always store next to the game executable / main dir, not the process cwd."""
        try:
            from panda3d.core import ExecutionEnvironment, Filename
            md = ExecutionEnvironment.getEnvironmentVariable('MAIN_DIR')
            if md:
                return Filename(md, 'useropt.json').to_os_specific()
        except Exception:
            pass
        return os.path.abspath(os.path.join(os.getcwd(), 'useropt.json'))

    def doSavedSettingsExist(self):
        return os.path.exists(self.__filename)

    def readSettings(self):
        if not self.doSavedSettingsExist():
            legacy = os.path.abspath(os.path.join(os.getcwd(), 'useropt.json'))
            if legacy != os.path.abspath(self.__filename) and os.path.isfile(legacy):
                try:
                    with open(legacy, 'r') as f:
                        self.__settings = json.load(f)
                    self.writeSettings()
                except Exception:
                    self.__settings = {}
            else:
                self.__settings = {}
            return

        try:
            with open(self.__filename, 'r') as f:
                self.__settings = json.load(f)
        except Exception:
            self.__settings = {}

    def writeSettings(self):
        try:
            from direct.task.TaskManagerGlobal import taskMgr
            taskMgr.remove(_WRITE_TASK)
        except Exception:
            pass
        dn = os.path.dirname(self.__filename)
        if dn and not os.path.isdir(dn):
            try:
                os.makedirs(dn, exist_ok=True)
            except Exception:
                pass
        tmp = self.__filename + '.tmp'
        try:
            with open(tmp, 'w') as f:
                json.dump(self.__settings, f, indent=4)
            if os.path.exists(self.__filename):
                os.replace(tmp, self.__filename)
            else:
                os.rename(tmp, self.__filename)
        except Exception:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass

    def _schedulePersist(self):
        try:
            from direct.task.TaskManagerGlobal import taskMgr
            taskMgr.remove(_WRITE_TASK)
            taskMgr.doMethodLater(0.15, self._persistTask, _WRITE_TASK)
        except Exception:
            self.writeSettings()

    def _persistTask(self, task):
        self.writeSettings()
        return task.done

    def updateSetting(self, setting, value):
        self.__settings[setting] = value
        self._schedulePersist()

    def getSetting(self, setting, default=None):
        return self.__settings.get(setting, default)
