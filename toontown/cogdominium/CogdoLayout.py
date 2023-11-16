from direct.directnotify import DirectNotifyGlobal


class CogdoLayout:
    notify = DirectNotifyGlobal.directNotify.newCategory('CogdoLayout')

    def __init__(self, numFloors):
        self._numFloors = numFloors

    def getNumGameFloors(self):
        return self._numFloors

    def hasBossBattle(self):
        return self._numFloors >= 1

    def getNumFloors(self):
        if self.hasBossBattle():
            return self._numFloors + 1
        else:
            return self._numFloors

    def getBossBattleFloor(self):
        if not self.hasBossBattle():
            self.notify.error('getBossBattleFloor(): cogdo has no boss battle')
        return self.getNumFloors() - 1
