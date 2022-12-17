from direct.showbase.DirectObject import DirectObject
from direct.showbase import GarbageReport

class GarbageLeakServerEventAggregatorAI(DirectObject):
    ClientLeakEvent = 'LeakAggregator-ClientGarbageLeakReceived'
    def __init__(self, air):
        self.air = air
        self._eventFreq = config.GetFloat('garbage-leak-server-event-frequency', 60 * 60.)
        self._doLaterName = None
        self._sentLeakDesc2num = {}
        self._curLeakDesc2num = {}
        self.accept(GarbageReport.GarbageCycleCountAnnounceEvent,
                    self._handleCycleCounts)
        self._clientStartFDC = None
        self._doLaterNameClient = None
        self._sentClientDesc2num = {}
        self._curClientDesc2num = {}
        self.accept(self.ClientLeakEvent, self._handleClientCycleCount)

    def destroy(self):
        self.ignoreAll()
        self._clientStartFDC.destroy()
        self._stopSending()
        self._stopSendingClientLeaks()
        del self.air

    def _handleCycleCounts(self, desc2num):
        self._curLeakDesc2num = desc2num
        self._startSending()

    def _handleClientCycleCount(self, num, description):
        self._curClientDesc2num.setdefault(description, 0)
        self._curClientDesc2num[description] += num
        if not self._clientStartFDC:
            # do an FDC to allow other concurrent client events to make it in, for dev/testing
            self._clientStartFDC = FrameDelayedCall(
                uniqueName('%s-startClientSend' % self.__class__.__name__),
                self._startSendingClientLeaks)

    def _startSending(self):
        if not self._doLaterName:
            self._sendLeaks()
            self._doLaterName = uniqueName('%s-sendGarbageServerEvents' % self.__class__.__name__)
            self.doMethodLater(self._eventFreq, self._sendLeaks, self._doLaterName)

    def _stopSending(self):
        self.removeTask(self._doLaterName)
        self._doLaterName = None
        
    def _sendLeaks(self, task=None):
        # only send the number of occurences of each leak that
        # we haven't already sent
        for desc, curNum in self._curLeakDesc2num.iteritems():
            self._sentLeakDesc2num.setdefault(desc, 0)
            num = curNum - self._sentLeakDesc2num[desc]
            if num > 0:
                if hasattr(self.air, 'districtId'):
                    who = self.air.districtId
                    eventName = 'ai-garbage'
                else:
                    who = self.air.ourChannel
                    eventName = 'ud-garbage'
                self.air.writeServerEvent(eventName, who, '%s|%s' % (num, desc))
                self._sentLeakDesc2num[desc] = curNum
        if task:
            return task.again

    def _startSendingClientLeaks(self):
        if not self._doLaterNameClient:
            self._sendClientLeaks()
            self._doLaterNameClient = uniqueName(
                '%s-sendClientGarbageServerEvents' % self.__class__.__name__)
            self.doMethodLater(self._eventFreq, self._sendClientLeaks, self._doLaterNameClient)

    def _stopSendingClientLeaks(self):
        self.removeTask(self._doLaterNameClient)
        self._doLaterNameClient = None
        
    def _sendClientLeaks(self, task=None):
        # only send the number of occurences of each leak that
        # we haven't already sent
        for desc, curNum in self._curClientDesc2num.iteritems():
            self._sentClientDesc2num.setdefault(desc, 0)
            num = curNum - self._sentClientDesc2num[desc]
            if num > 0:
                self.air.writeServerEvent('client-garbage', self.air.districtId, '%s|%s' % (num, desc))
                self._sentClientDesc2num[desc] = curNum
        if task:
            return task.again
