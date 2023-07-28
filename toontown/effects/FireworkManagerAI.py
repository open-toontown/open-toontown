from direct.directnotify import DirectNotifyGlobal
import random
from direct.task import Task
from . import DistributedFireworkShowAI
from toontown.ai import HolidayBaseAI
from . import FireworkShow
from toontown.toonbase.ToontownGlobals import DonaldsDock, ToontownCentral, \
    TheBrrrgh, MinniesMelodyland, DaisyGardens, OutdoorZone, GoofySpeedway, DonaldsDreamland
import time

class FireworkManagerAI(HolidayBaseAI.HolidayBaseAI):
    """
    Manages Fireworks holidays
    """

    notify = DirectNotifyGlobal.directNotify.newCategory('FireworkManagerAI')

    zoneToStyleDict = {
        # Donald's Dock
        DonaldsDock : 5,
        # Toontown Central
        ToontownCentral : 0,
        # The Brrrgh
        TheBrrrgh : 4,
        # Minnie's Melodyland
        MinniesMelodyland : 3,
        # Daisy Gardens
        DaisyGardens : 1,
        # Acorn Acres
        OutdoorZone : 0,
        # GS
        GoofySpeedway : 0,
        # Donald's Dreamland
        DonaldsDreamland : 2,
        }

    def __init__(self, air, holidayId):
        HolidayBaseAI.HolidayBaseAI.__init__(self, air, holidayId)
        # Dict from zone to DistFireworkShow objects
        self.fireworkShows = {}
        self.waitTaskName = 'waitStartFireworkShows'

    def start(self):
        self.notify.info("Starting firework holiday: %s" % (time.ctime()))
        self.waitForNextShow()

    def stop(self):
        self.notify.info("Stopping firework holiday: %s" % (time.ctime()))
        taskMgr.remove(self.waitTaskName)
        self.stopAllShows()

    def startAllShows(self, task):
        for hood in self.air.hoods:
            showType = self.zoneToStyleDict.get(hood.canonicalHoodId)
            if showType is not None:
                self.startShow(hood.zoneId, showType)
            
        self.waitForNextShow()
        return Task.done

    def waitForNextShow(self):
        currentTime = time.localtime()
        currentMin = currentTime[4]
        currentSec = currentTime[5]
        waitTime = ((60 - currentMin) * 60) - currentSec
        self.notify.debug("Waiting %s seconds until next show" % (waitTime))
        taskMgr.doMethodLater(waitTime, self.startAllShows, self.waitTaskName)

    def startShow(self, zone, showType = -1, magicWord = 0):
        """
        Start a show of showType in this zone.
        Returns 1 if a show was successfully started.
        Warns and returns 0 if a show was already running in this zone.
        There can only be one show per zone.
        """
        if zone in self.fireworkShows:
            self.notify.warning("startShow: already running a show in zone: %s" % (zone))
            return 0        
        self.notify.debug("startShow: zone: %s showType: %s" % (zone, showType))
        # Create a show, passing ourselves in so it can tell us when
        # the show is over
        show = DistributedFireworkShowAI.DistributedFireworkShowAI(self.air, self)
        show.generateWithRequired(zone)
        self.fireworkShows[zone] = show
        # Currently needed to support legacy fireworks
        if simbase.air.config.GetBool('want-old-fireworks', 0) or magicWord == 1:
            show.d_startShow(showType, showType)
        else:
            show.d_startShow(self.holidayId, showType)
        # Success!
        return 1

    def stopShow(self, zone):
        """
        Stop a firework show in this zone.
        Returns 1 if it did stop a show, warns and returns 0 if there is not one
        """
        if zone not in self.fireworkShows:
            self.notify.warning("stopShow: no show running in zone: %s" % (zone))
            return 0
        self.notify.debug("stopShow: zone: %s" % (zone))
        show = self.fireworkShows[zone]
        del self.fireworkShows[zone]
        show.requestDelete()
        # Success!
        return 1

    def stopAllShows(self):
        """
        Stop all firework shows this manager knows about in all zones.
        Returns number of shows stopped by this command.
        """
        numStopped = 0
        for zone, show in list(self.fireworkShows.items()):
            self.notify.debug("stopAllShows: zone: %s" % (zone))
            show.requestDelete()
            numStopped += 1
        self.fireworkShows.clear()
        return numStopped

    def isShowRunning(self, zone):
        """
        Is there currently a show running in this zone?
        """
        return zone in self.fireworkShows
        
