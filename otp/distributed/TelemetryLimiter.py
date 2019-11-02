from direct.showbase.DirectObject import DirectObject
from otp.avatar.DistributedPlayer import DistributedPlayer
from direct.task.Task import Task

class TelemetryLimiter(DirectObject):
    TaskName = 'TelemetryLimiterEnforce'
    LeakDetectEventName = 'telemetryLimiter'

    def __init__(self):
        self._objs = {}
        self._task = taskMgr.add(self._enforceLimits, self.TaskName, priority=40)

    def destroy(self):
        taskMgr.remove(self._task)
        del self._objs

    def getNumObjs(self):
        return len(self._objs)

    def addObj(self, obj):
        id = obj.getTelemetryLimiterId()
        self._objs[id] = obj
        self.accept(self._getDummyEventName(obj), self._dummyEventHandler)

    def _getDummyEventName(self, obj):
        return '%s-%s-%s-%s' % (self.LeakDetectEventName,
         obj.getTelemetryLimiterId(),
         id(obj),
         obj.__class__.__name__)

    def _dummyEventHandler(self, *args, **kargs):
        pass

    def removeObj(self, obj):
        id = obj.getTelemetryLimiterId()
        self._objs.pop(id)
        self.ignore(self._getDummyEventName(obj))

    def _enforceLimits(self, task = None):
        for obj in self._objs.itervalues():
            obj.enforceTelemetryLimits()

        return Task.cont


class TelemetryLimit:

    def __call__(self, obj):
        pass


class RotationLimitToH(TelemetryLimit):

    def __init__(self, pConst = 0.0, rConst = 0.0):
        self._pConst = pConst
        self._rConst = rConst

    def __call__(self, obj):
        obj.setHpr(obj.getH(), self._pConst, self._rConst)


class TLNull:

    def __init__(self, *limits):
        pass

    def destroy(self):
        pass


class TLGatherAllAvs(DirectObject):

    def __init__(self, name, *limits):
        self._name = name
        self._avs = {}
        self._limits = makeList(limits)
        self._avId2limits = {}
        avs = base.cr.doFindAllInstances(DistributedPlayer)
        for av in avs:
            self._handlePlayerArrive(av)

        self.accept(DistributedPlayer.GetPlayerGenerateEvent(), self._handlePlayerArrive)
        self.accept(DistributedPlayer.GetPlayerNetworkDeleteEvent(), self._handlePlayerLeave)

    def _handlePlayerArrive(self, av):
        if av is not localAvatar:
            self._avs[av.doId] = av
            limitList = []
            for limit in self._limits:
                l = limit()
                limitList.append(l)
                av.addTelemetryLimit(l)

            self._avId2limits[av.doId] = limitList
            base.cr.telemetryLimiter.addObj(av)

    def _handlePlayerLeave(self, av):
        if av is not localAvatar:
            base.cr.telemetryLimiter.removeObj(av)
            for limit in self._avId2limits[av.doId]:
                av.removeTelemetryLimit(limit)

            del self._avId2limits[av.doId]
            del self._avs[av.doId]

    def destroy(self):
        self.ignoreAll()
        while len(self._avs):
            self._handlePlayerLeave(self._avs.values()[0])

        del self._avs
        del self._limits
        del self._avId2limits
