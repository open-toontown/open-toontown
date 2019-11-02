

class DistCogdoGameBase:

    def local2GameTime(self, timestamp):
        return timestamp - self._startTime

    def game2LocalTime(self, timestamp):
        return timestamp + self._startTime

    def getCurrentGameTime(self):
        return self.local2GameTime(globalClock.getFrameTime())
