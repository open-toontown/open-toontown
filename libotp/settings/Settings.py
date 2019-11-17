class Settings:
    GL = 0
    DX7 = 1
    DX8 = 5

    @staticmethod
    def readSettings():
        pass  # todo

    @staticmethod
    def writeSettings():
        pass  # lol not yet

    @staticmethod
    def getWindowedMode():
        return 1

    @staticmethod
    def setMusic(_):
        pass

    @staticmethod
    def getMusic():
        return 1

    @staticmethod
    def setSfx(_):
        pass

    @staticmethod
    def getSfx():
        return 1

    @staticmethod
    def setToonChatSounds(_):
        pass

    @staticmethod
    def getToonChatSounds():
        return 1

    @staticmethod
    def getMusicVolume():
        return 1

    @staticmethod
    def getSfxVolume():
        return 1

    @staticmethod
    def getResolution():
        return 1

    @staticmethod
    def getEmbeddedMode():
        return 0

    @staticmethod
    def doSavedSettingsExist():
        return 0

    @staticmethod
    def setAcceptingNewFriends(_):
        pass

    @staticmethod
    def getAcceptingNewFriends():
        return 1

    @staticmethod
    def setAcceptingNonFriendWhispers(_):
        pass

    @staticmethod
    def getAcceptingNonFriendWhispers():
        return 1
