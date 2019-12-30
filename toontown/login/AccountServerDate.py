from pandac.PandaModules import *
from otp.login.HTTPUtil import *
from direct.directnotify import DirectNotifyGlobal
from otp.login import TTAccount
from . import DateObject
from . import TTDateObject
import time

class AccountServerDate:
    notify = DirectNotifyGlobal.directNotify.newCategory('AccountServerDate')

    def __init__(self):
        self.__grabbed = 0

    def getServer(self):
        return TTAccount.getAccountServer().cStr()

    def grabDate(self, force = 0):
        if self.__grabbed and not force:
            self.notify.debug('using cached account server date')
            return
        if base.cr.accountOldAuth or base.config.GetBool('use-local-date', 0):
            self.__useLocalClock()
            return
        url = URLSpec(self.getServer())
        url.setPath('/getDate.php')
        self.notify.debug('grabbing account server date from %s' % url.cStr())
        response = getHTTPResponse(url, http)
        if response[0] != 'ACCOUNT SERVER DATE':
            self.notify.debug('invalid response header')
            raise UnexpectedResponse('unexpected response, response=%s' % response)
        try:
            epoch = int(response[1])
        except ValueError as e:
            self.notify.debug(str(e))
            raise UnexpectedResponse('unexpected response, response=%s' % response)

        timeTuple = time.gmtime(epoch)
        self.year = timeTuple[0]
        self.month = timeTuple[1]
        self.day = timeTuple[2]
        base.cr.dateObject = TTDateObject.TTDateObject(self)
        self.__grabbed = 1

    def __useLocalClock(self):
        self.month = base.cr.dateObject.getMonth()
        self.year = base.cr.dateObject.getYear()
        self.day = base.cr.dateObject.getDay()

    def getMonth(self):
        return self.month

    def getYear(self):
        return self.year

    def getDay(self):
        return self.day
