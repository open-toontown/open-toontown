import os

class ModuleList:
    serverDataFolder = simbase.config.GetString('server-data-folder', '')

    def __init__(self):
        self.moduleWhitelistFilename = self.getWhitelistFilename()
        self.moduleBlacklistFilename = self.getBlacklistFilename()
        self.loadBlacklistFile()
        self.loadWhitelistFile()

    def getWhitelistFilename(self):
        result = '%s.moduleWhiteList' % self.serverDataFolder
        return result

    def getBlacklistFilename(self):
        result = '%s.moduleBlackList' % self.serverDataFolder
        return result

    def loadBlacklistFile(self):
        try:
            file = open(self.moduleBlacklistFilename + '.bu', 'r')
            if os.path.exists(self.moduleBlacklistFilename):
                os.remove(self.moduleBlacklistFilename)
        except IOError:
            try:
                file = open(self.moduleBlacklistFilename, 'r')
            except IOError:
                return set()

        file.seek(0)
        moduleFile = self.loadFrom(file)
        file.close()
        result = self.loadFrom(moduleFile)
        self.moduleBlacklist = result
        return result

    def loadWhitelistFile(self):
        try:
            file = open(self.moduleWhitelistFilename + '.bu', 'r')
            if os.path.exists(self.moduleWhitelistFilename):
                os.remove(self.moduleWhitelistFilename)
        except IOError:
            try:
                file = open(self.moduleWhitelistFilename, 'r')
            except IOError:
                return set()

        file.seek(0)
        moduleFile = self.loadFrom(file)
        file.close()
        result = self.loadFrom(moduleFile)
        self.moduleWhitelist = result
        return result

    def loadFrom(self, file):
        result = set()
        try:
            for module in file:
                module = module.strip()
                if module:
                    result.add(module)

        except EOFError:
            pass

        return result

    def updateWhitelistFile(self):
        try:
            backup = self.getWhitelistFilename() + '.bu'
            if os.path.exists(self.getWhitelistFilename()):
                os.rename(self.getWhitelistFilename(), backup)
            file = open(self.getWhitelistFilename(), 'w')
            file.seek(0)
            for whiteModule in self.moduleWhitelist:
                file.write(whiteModule + '\n')

            file.close()
            if os.path.exists(backup):
                os.remove(backup)
        except EnvironmentError:
            self.notify.warning(str(sys.exc_info()[1]))

    def updateBlacklistFile(self):
        try:
            backup = self.getBlacklistFilename() + '.bu'
            if os.path.exists(self.getBlacklistFilename()):
                os.rename(self.getBlacklistFilename(), backup)
            file = open(self.getBlacklistFilename(), 'w')
            file.seek(0)
            for blackModule in self.moduleBlacklist:
                file.write(blackModule + '\n')

            file.close()
            if os.path.exists(backup):
                os.remove(backup)
        except EnvironmentError:
            self.notify.warning(str(sys.exc_info()[1]))
