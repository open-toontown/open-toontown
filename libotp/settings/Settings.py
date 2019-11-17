class Settings:
    GL = 0
    DX7 = 1
    DX8 = 5

    @staticmethod
    def readSettings():
        pass  # todo

    @staticmethod
    def getWindowedMode():
        return 1

    @staticmethod
    def getMusic():
        return 1

    @staticmethod
    def getSfx():
        return 1

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
    def getAcceptingNewFriends():
        return 1

    @staticmethod
    def getAcceptingNonFriendWhispers():
        return 1
