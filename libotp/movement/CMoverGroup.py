from direct.directnotify import DirectNotifyGlobal


class CMoverGroup:
    notify = DirectNotifyGlobal.directNotify.newCategory('CMoverGroup')

    def __init__(self):
        self.dt = 1.0
        self.dtClock = globalClock.getFrameTime()
        self.cMovers = {}

    def setDt(self, dt):
        self.dt = dt
        if self.dt == -1.0:
            clockDelta = globalClock.getFrameTime()
            self.dt = clockDelta - self.dtClock
            self.dtClock = clockDelta

    def resetDt(self):
        self.dt = 1.0
        self.dtClock = globalClock.getFrameTime()

    def addCMover(self, name, cMover):
        if not cMover:
            return

        self.removeCMover(name)
        self.cMovers[name] = cMover

    def removeCMover(self, name):
        if name in self.cMovers:
            del self.cMovers[name]

    def processCImpulsesAndIntegrate(self):
        if self.dt == -1.0:
            clockDelta = globalClock.getFrameTime()
            self.dt = clockDelta - self.dtClock
            self.dtClock = clockDelta

        for cMover in list(self.cMovers.values()):
            cMover.processCImpulses(self.dt)
            cMover.integrate()
