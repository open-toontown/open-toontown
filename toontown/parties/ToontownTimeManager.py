import time
from datetime import datetime, timedelta
import pytz
from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import TTLocalizer

class ToontownTimeManager(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownTimeManager')
    ClockFormat = '%I:%M:%S %p'
    formatStr = '%Y-%m-%d %H:%M:%S'

    def __init__(self, serverTimeUponLogin = 0, clientTimeUponLogin = 0, globalClockRealTimeUponLogin = 0):
        try:
            self.serverTimeZoneString = base.config.GetString('server-timezone', TTLocalizer.TimeZone)
        except:
            try:
                self.serverTimeZoneString = simbase.config.GetString('server-timezone', TTLocalizer.TimeZone)
            except:
                notify.error('ToontownTimeManager does not have access to base or simbase.')

        self.serverTimeZone = pytz.timezone(self.serverTimeZoneString)
        self.updateLoginTimes(serverTimeUponLogin, clientTimeUponLogin, globalClockRealTimeUponLogin)
        self.debugSecondsAdded = 0

    def updateLoginTimes(self, serverTimeUponLogin, clientTimeUponLogin, globalClockRealTimeUponLogin):
        self.serverTimeUponLogin = serverTimeUponLogin
        self.clientTimeUponLogin = clientTimeUponLogin
        self.globalClockRealTimeUponLogin = globalClockRealTimeUponLogin
        naiveTime = datetime.utcfromtimestamp(self.serverTimeUponLogin)
        self.utcServerDateTime = naiveTime.replace(tzinfo=pytz.utc)
        self.serverDateTime = datetime.fromtimestamp(self.serverTimeUponLogin, self.serverTimeZone)

    def getCurServerDateTime(self):
        secondsPassed = globalClock.getRealTime() - self.globalClockRealTimeUponLogin + self.debugSecondsAdded
        curDateTime = self.serverTimeZone.normalize(self.serverDateTime + timedelta(seconds=secondsPassed))
        return curDateTime

    def getRelativeServerDateTime(self, timeOffset):
        secondsPassed = globalClock.getRealTime() - self.globalClockRealTimeUponLogin + self.debugSecondsAdded
        secondsPassed += timeOffset
        curDateTime = self.serverTimeZone.normalize(self.serverDateTime + timedelta(seconds=secondsPassed))
        return curDateTime

    def getCurServerDateTimeForComparison(self):
        secondsPassed = globalClock.getRealTime() - self.globalClockRealTimeUponLogin + self.debugSecondsAdded
        curDateTime = self.serverDateTime + timedelta(seconds=secondsPassed)
        curDateTime = curDateTime.replace(tzinfo=self.serverTimeZone)
        return curDateTime

    def getCurServerTimeStr(self):
        curDateTime = self.getCurServerDateTime()
        result = curDateTime.strftime(self.ClockFormat)
        if result[0] == '0':
            result = result[1:]
        return result

    def setDebugSecondsAdded(self, moreSeconds):
        self.debugSecondsAdded = moreSeconds

    def debugTest(self):
        startTime = datetime.today()
        serverTzInfo = self.serverTimeZone
        startTime = startTime.replace(tzinfo=serverTzInfo)
        self.notify.info('startTime = %s' % startTime)
        serverTime = self.getCurServerDateTime()
        self.notify.info('serverTime = %s' % serverTime)
        result = startTime <= serverTime
        self.notify.info('start < serverTime %s' % result)
        startTime1MinAgo = startTime + timedelta(minutes=-1)
        self.notify.info('startTime1MinAgo = %s' % startTime1MinAgo)
        result2 = startTime1MinAgo <= serverTime
        self.notify.info('startTime1MinAgo < serverTime %s' % result2)
        serverTimeForComparison = self.getCurServerDateTimeForComparison()
        self.notify.info('serverTimeForComparison = %s' % serverTimeForComparison)
        result3 = startTime1MinAgo <= serverTimeForComparison
        self.notify.info('startTime1MinAgo < serverTimeForComparison %s' % result3)

    def convertStrToToontownTime(self, dateStr):
        curDateTime = self.getCurServerDateTime()
        try:
            curDateTime = datetime.fromtimestamp(time.mktime(time.strptime(dateStr, self.formatStr)), self.serverTimeZone)
            curDateTime = self.serverTimeZone.normalize(curDateTime)
        except:
            self.notify.warning('error parsing date string=%s' % dateStr)

        result = curDateTime
        return result

    def convertUtcStrToToontownTime(self, dateStr):
        curDateTime = self.getCurServerDateTime()
        try:
            timeTuple = time.strptime(dateStr, self.formatStr)
            utcDateTime = datetime(timeTuple[0], timeTuple[1], timeTuple[2], timeTuple[3], timeTuple[4], timeTuple[5], timeTuple[6], pytz.utc)
            curDateTime = utcDateTime.astimezone(self.serverTimeZone)
            curDateTime = self.serverTimeZone.normalize(curDateTime)
        except:
            self.notify.warning('error parsing date string=%s' % dateStr)

        result = curDateTime
        return result
