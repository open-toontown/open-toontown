

class DropScheduler:

    def __init__(self, gameDuration, firstDropDelay, dropPeriod, maxDropDuration, fasterDropDelay, fasterDropPeriodMult, startTime = None):
        self.gameDuration = gameDuration
        self.firstDropDelay = firstDropDelay
        self._dropPeriod = dropPeriod
        self.maxDropDuration = maxDropDuration
        self.fasterDropDelay = fasterDropDelay
        self.fasterDropPeriodMult = fasterDropPeriodMult
        if startTime is None:
            startTime = 0
        self._startTime = startTime
        self.curT = self._startTime + self.firstDropDelay
        return

    def getT(self):
        return self.curT

    def getDuration(self):
        return self.gameDuration

    def getDropPeriod(self):
        delay = self._dropPeriod
        if self.curT - self._startTime >= self.fasterDropDelay:
            delay *= self.fasterDropPeriodMult
        return delay

    def doneDropping(self, continuous = None):
        landTime = self.getT() - self._startTime + self.maxDropDuration
        if continuous is None:
            continuous = False
        else:
            continuous = True
        if continuous:
            maxTime = self.gameDuration + self.maxDropDuration
        else:
            maxTime = self.gameDuration + self.getDropPeriod()
        return landTime >= maxTime

    def skipPercent(self, percent):
        numSkips = 0
        while True:
            prevT = self.curT
            self.stepT()
            if self.curT >= percent * self.gameDuration:
                self.curT = prevT
                break
            else:
                numSkips += 1

        return numSkips

    def stepT(self):
        self.curT += self.getDropPeriod()


class ThreePhaseDropScheduler(DropScheduler):

    def __init__(self, gameDuration, firstDropDelay, dropPeriod, maxDropDuration, slowerDropPeriodMult, normalDropDelay, fasterDropDelay, fasterDropPeriodMult, startTime = None):
        self._slowerDropPeriodMult = slowerDropPeriodMult
        self._normalDropDelay = normalDropDelay
        DropScheduler.__init__(self, gameDuration, firstDropDelay, dropPeriod, maxDropDuration, fasterDropDelay, fasterDropPeriodMult, startTime)

    def getDropPeriod(self):
        delay = self._dropPeriod
        if self.curT - self._startTime < self._normalDropDelay:
            delay *= self._slowerDropPeriodMult
        elif self.curT - self._startTime >= self.fasterDropDelay:
            delay *= self.fasterDropPeriodMult
        return delay
