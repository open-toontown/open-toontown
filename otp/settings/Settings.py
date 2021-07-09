import json
import os


class Settings:

    def __init__(self):
        self.__settings = {}
        self.__filename = 'useropt.json'

    def doSavedSettingsExist(self):
        return os.path.exists(self.__filename)

    def readSettings(self):
        if not self.doSavedSettingsExist():
            self.__settings = {}
            return

        try:
            with open(self.__filename, 'r') as f:
                self.__settings = json.load(f)
        except:
            self.__settings = {}

    def writeSettings(self):
        with open(self.__filename, 'w+') as f:
            json.dump(self.__settings, f, indent=4)

    def updateSetting(self, setting, value):
        self.__settings[setting] = value

    def getSetting(self, setting, default=None):
        return self.__settings.get(setting, default)
