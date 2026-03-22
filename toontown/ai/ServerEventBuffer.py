"""ServerEventBuffer: buffers up information for multiple server events and writes single event"""

class ServerEventBuffer:
    """Buffers up events that you want to be logged in the server event log."""
    def __init__(self, air, name, avId, period=None):
        # name is the name of the event that we'll be writing to the server
        # period in minutes
        self.air = air
        self.name = name
        self.avId = avId
        if period is None:
            # every 6 hours
            period = 6*60.
        self.period = period
        self.lastFlushTime = None

    def destroy(self):
        self.flush()

    def flush(self):
        # subclasses, override this and call down
        self.lastFlushTime = None

    def writeEvent(self, msg):
        self.air.writeServerEvent(self.name, self.avId, msg)

    def considerFlush(self):
        # if we haven't logged in a while, don't immediately flush out the
        # first event
        if self.lastFlushTime is None:
            self.lastFlushTime = globalClock.getFrameTime()
        elif ((globalClock.getFrameTime() - self.lastFlushTime) >
              (self.period*60.)):
            self.flush()


class ServerEventAccumulator(ServerEventBuffer):
    # counts # of times a particular event occurs
    def __init__(self, air, name, avId, period=None):
        ServerEventBuffer.__init__(self, air, name, avId, period)
        self.count = 0

    def flush(self):
        ServerEventBuffer.flush(self)
        if not self.count:
            return
        self.writeEvent("%s" % self.count)
        self.count = 0

    def addEvent(self):
        self.count += 1
        self.considerFlush()


class ServerEventMultiAccumulator(ServerEventBuffer):
    # counts # of times multiple related events occur
    def __init__(self, air, name, avId, period=None):
        ServerEventBuffer.__init__(self, air, name, avId, period)
        # eventName:count
        self.events = {}

    def flush(self):
        ServerEventBuffer.flush(self)
        if not len(self.events):
            return
        msg = ""
        eventNames = list(self.events.keys())
        eventNames.sort()
        for eventName in eventNames:
            msg += "%s:%s" % (eventName, self.events[eventName])
            if eventName != eventNames[-1]:
                msg += ','
        self.writeEvent(msg)
        self.events = {}

    def addEvent(self, eventName):
        self.events.setdefault(eventName, 0)
        self.events[eventName] += 1
        self.considerFlush()
