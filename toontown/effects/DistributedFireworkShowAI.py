from otp.ai.AIBaseGlobal import *
from direct.distributed import DistributedObjectAI
from direct.directnotify import DirectNotifyGlobal
from direct.distributed import ClockDelta
from .FireworkShow import FireworkShow
from .FireworkShows import getShowDuration
import random
from direct.task import Task

class DistributedFireworkShowAI(DistributedObjectAI.DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedFireworkShowAI')

    def __init__(self, air, fireworkMgr = None):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.fireworkMgr = fireworkMgr
        self.eventId = None
        self.style = None
        self.timestamp = None
        self.throwAwayShow = FireworkShow()
        return

    def delete(self):
        del self.throwAwayShow
        taskMgr.remove(self.taskName('waitForShowDone'))
        DistributedObjectAI.DistributedObjectAI.delete(self)

    def d_startShow(self, eventId, style):
        timestamp = ClockDelta.globalClockDelta.getRealNetworkTime()
        self.eventId = eventId
        self.style = style
        self.timestamp = timestamp
        self.sendUpdate('startShow', (self.eventId, self.style, self.timestamp))
        if simbase.air.config.GetBool('want-old-fireworks', 0):
            duration = getShowDuration(self.eventId, self.style)
            taskMgr.doMethodLater(duration, self.fireworkShowDone, self.taskName('waitForShowDone'))
        else:
            duration = self.throwAwayShow.getShowDuration(self.eventId)
            duration += 20.0
            taskMgr.doMethodLater(duration, self.fireworkShowDone, self.taskName('waitForShowDone'))

    def fireworkShowDone(self, task):
        self.notify.debug('fireworkShowDone')
        if self.fireworkMgr:
            self.fireworkMgr.stopShow(self.zoneId)
        return Task.done

    def requestFirework(self, x, y, z, style, color1, color2):
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug('requestFirework: avId: %s, style: %s' % (avId, style))
        if self.fireworkMgr:
            if self.fireworkMgr.isShowRunning(self.zoneId):
                self.d_shootFirework(x, y, z, style, color1, color2)
        else:
            self.d_shootFirework(x, y, z, style, color1, color2)

    def d_shootFirework(self, x, y, z, style, color1, color2):
        self.sendUpdate('shootFirework', (x,
         y,
         z,
         style,
         color1,
         color2))
