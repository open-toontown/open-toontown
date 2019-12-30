

class ServerEventBuffer:

    def __init__(self, air, name, avId, period = None):
        self.air = air
        self.name = name
        self.avId = avId
        if period is None:
            period = 6 * 60.0
        self.period = period
        self.lastFlushTime = None
        return

    def destroy(self):
        self.flush()

    def flush(self):
        self.lastFlushTime = None
        return

    def writeEvent(self, msg):
        self.air.writeServerEvent(self.name, self.avId, msg)

    def considerFlush(self):
        if self.lastFlushTime is None:
            self.lastFlushTime = globalClock.getFrameTime()
        elif globalClock.getFrameTime() - self.lastFlushTime > self.period * 60.0:
            self.flush()
        return


class ServerEventAccumulator(ServerEventBuffer):

    def __init__(self, air, name, avId, period = None):
        ServerEventBuffer.__init__(self, air, name, avId, period)
        self.count = 0

    def flush(self):
        ServerEventBuffer.flush(self)
        if not self.count:
            return
        self.writeEvent('%s' % self.count)
        self.count = 0

    def addEvent(self):
        self.count += 1
        self.considerFlush()


class ServerEventMultiAccumulator(ServerEventBuffer):

    def __init__(self, air, name, avId, period = None):
        ServerEventBuffer.__init__(self, air, name, avId, period)
        self.events = {}

    def flush(self):
        ServerEventBuffer.flush(self)
        if not len(self.events):
            return
        msg = ''
        eventNames = list(self.events.keys())
        eventNames.sort()
        for eventName in eventNames:
            msg += '%s:%s' % (eventName, self.events[eventName])
            if eventName != eventNames[-1]:
                msg += ','

        self.writeEvent(msg)
        self.events = {}

    def addEvent(self, eventName):
        self.events.setdefault(eventName, 0)
        self.events[eventName] += 1
        self.considerFlush()
