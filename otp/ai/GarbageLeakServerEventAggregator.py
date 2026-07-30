from direct.showbase.DirectObject import DirectObject
from direct.showbase import GarbageReport

class GarbageLeakServerEventAggregator(DirectObject):

    def __init__(self, cr):
        self.cr = cr
        self._doLaterName = None
        self._sentLeakDesc2num = {}
        self._curLeakDesc2num = {}
        self.accept(GarbageReport.GarbageCycleCountAnnounceEvent, self._handleCycleCounts)
        return

    def destroy(self):
        self._stopSending()
        self.ignoreAll()
        del self.cr

    def _handleCycleCounts(self, desc2num):
        self._curLeakDesc2num = desc2num
        self._startSending()

    def _startSending(self):
        if not self._doLaterName:
            self._sendLeaks()
            self._doLaterName = uniqueName('%s-sendGarbageLeakInfo' % self.__class__.__name__)
            self.doMethodLater(60 * 60.0, self._sendLeaks, self._doLaterName)

    def _stopSending(self):
        if self._doLaterName:
            self.removeTask(self._doLaterName)
        self._doLaterName = None
        return

    def _sendLeaks(self, task = None):
        for desc, curNum in self._curLeakDesc2num.items():
            self._sentLeakDesc2num.setdefault(desc, 0)
            num = curNum - self._sentLeakDesc2num[desc]
            if num > 0:
                base.cr.timeManager.d_setClientGarbageLeak(num, desc)
                self._sentLeakDesc2num[desc] = curNum

        if task:
            return task.again
