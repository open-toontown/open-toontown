import Entity

class VisibilityBlocker:

    def __init__(self):
        self.__nextSetZoneDoneEvent = None
        return

    def destroy(self):
        self.cancelUnblockVis()

    def requestUnblockVis(self):
        if self.__nextSetZoneDoneEvent is None:
            self.__nextSetZoneDoneEvent = self.level.cr.getNextSetZoneDoneEvent()
            self.acceptOnce(self.__nextSetZoneDoneEvent, self.okToUnblockVis)
            self.level.forceSetZoneThisFrame()
        return

    def cancelUnblockVis(self):
        if self.__nextSetZoneDoneEvent is not None:
            self.ignore(self.__nextSetZoneDoneEvent)
            self.__nextSetZoneDoneEvent = None
        return

    def isWaitingForUnblockVis(self):
        return self.__nextSetZoneDoneEvent is not None

    def okToUnblockVis(self):
        self.cancelUnblockVis()
