from otp.ai.AIBaseGlobal import *
from pandac.PandaModules import *
from direct.distributed import DistributedObjectAI
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals

class NewsManagerAI(DistributedObjectAI.DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory("NewsManagerAI")

    def __init__(self, air):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.everyoneChats = simbase.config.GetBool("everyone-chats", 0)
        self.weeklyCalendarHolidays = []
        self.yearlyCalendarHolidays = []
        self.oncelyCalendarHolidays = []
        self.relativelyCalendarHolidays = []
        self.multipleStartHolidays = []
        
    def generate(self):
        DistributedObjectAI.DistributedObjectAI.generate(self)
        self.accept("avatarEntered", self.__handleAvatarEntered)
        self.accept("avatarExited", self.__handleAvatarExited)

    def __handleAvatarEntered(self, avatar):
        if self.air.suitInvasionManager.getInvading():
            # Let this poor avatar who just came in the game know that there
            # is a Cog Invasion taking place
            cogType, skeleton = self.air.suitInvasionManager.getCogType()
            numRemaining = self.air.suitInvasionManager.getNumCogsRemaining()
            self.sendAvatarInvasionStatus(avatar.getDoId(), cogType, numRemaining, skeleton)

        
        # let them know about all holidays actually...
        self.sendUpdateToAvatarId(avatar.getDoId(), "holidayNotify", [])
        
        if self.everyoneChats:
            avatar.d_setCommonChatFlags(ToontownGlobals.CommonChat)

    def __handleAvatarExited(self, avatar = None):
        pass

    def invasionBegin(self, cogType, numRemaining, skeleton):
        self.sendUpdate("setInvasionStatus",
                        [ToontownGlobals.SuitInvasionBegin, cogType, numRemaining, skeleton])

    def invasionEnd(self, cogType, numRemaining, skeleton):
        self.sendUpdate("setInvasionStatus",
                        [ToontownGlobals.SuitInvasionEnd, cogType, numRemaining, skeleton])

    def invasionUpdate(self, cogType, numRemaining, skeleton):
        # Broadcast an invasion update to all players
        self.sendUpdate("setInvasionStatus",
                        [ToontownGlobals.SuitInvasionUpdate, cogType, numRemaining, skeleton])

    def sendAvatarInvasionStatus(self, avId, cogType, numRemaining, skeleton):
        # Send an invasion update to only one avatar
        self.sendUpdateToAvatarId(avId, "setInvasionStatus",
                                  [ToontownGlobals.SuitInvasionBulletin, cogType, numRemaining, skeleton])
    
    def sendSystemMessage(self, message, style = 0):
        # Use news manager to broadcast a system message to all the clients
        self.sendUpdate("sendSystemMessage", [message, style])

    def d_setHolidayIdList(self, holidayIdList):
        self.sendUpdate("setHolidayIdList", [holidayIdList])

    def bingoWin(self, zoneId):
        self.sendUpdate("setBingoWin", [0])

    def bingoStart(self):
        self.sendUpdate("setBingoStart", [])

    def bingoEnd(self):
        self.sendUpdate("setBingoEnd", [])

    def circuitRaceStart(self):
        self.sendUpdate("setCircuitRaceStart", [])

    def circuitRaceEnd(self):
        self.sendUpdate("setCircuitRaceEnd", [])

    def trolleyHolidayStart(self):
        self.sendUpdate("setTrolleyHolidayStart", [])

    def trolleyHolidayEnd(self):
        self.sendUpdate("setTrolleyHolidayEnd", [])
        
    def trolleyWeekendStart(self):
        self.sendUpdate("setTrolleyWeekendStart", [])

    def trolleyWeekendEnd(self):
        self.sendUpdate("setTrolleyWeekendEnd", [])

    def roamingTrialerWeekendStart(self):
        self.sendUpdate("setRoamingTrialerWeekendStart", [])

    def roamingTrialerWeekendEnd(self):
        self.sendUpdate("setRoamingTrialerWeekendEnd", [])

    def addWeeklyCalendarHoliday(self, holidayId, dayOfTheWeek):
        """Add a new weekly holiday displayed in the calendar."""
        self.weeklyCalendarHolidays.append((holidayId, dayOfTheWeek))

    def getWeeklyCalendarHolidays(self):
        """Return our list of weekly calendar holidays."""
        return self.weeklyCalendarHolidays

    def sendWeeklyCalendarHolidays(self):
        """Force a send of the weekly calendar holidays."""
        self.sendUpdate("setWeeklyCalendarHolidays", [self.weeklyCalendarHolidays])

    def addYearlyCalendarHoliday(self, holidayId, firstStartTime, lastEndTime):
        """Add a new yearly holiday."""
        # Note the holiday can have breaks in it.  e.g. no bloodsucker invasion
        # happens between 3 and 6 pm on halloween, however for simplicity
        # we just note the first time it will happen, and the last end time for it
        self.yearlyCalendarHolidays.append((holidayId, firstStartTime, lastEndTime))

    def getYearlyCalendarHolidays(self):
        """Return our list of yearly calendar holidays."""
        return self.yearlyCalendarHolidays

    def sendYearlyCalendarHolidays(self):
        """Force a send of the yearly calendar holidays."""
        self.sendUpdate("setYearlyCalendarHolidays", [self.yearlyCalendarHolidays])

    def addOncelyCalendarHoliday(self, holidayId, firstStartTime, lastEndTime):
        """Add a new oncely holiday."""
        # Note the holiday can have breaks in it.  e.g. no bloodsucker invasion
        # happens between 3 and 6 pm on halloween, however for simplicity
        # we just note the first time it will happen, and the last end time for it
        self.oncelyCalendarHolidays.append((holidayId, firstStartTime, lastEndTime))

    def getOncelyCalendarHolidays(self):
        """Return our list of oncely calendar holidays."""
        return self.oncelyCalendarHolidays

    def addMultipleStartHoliday(self, holidayId, startAndEndList):
        """A a new multiple start holiday."""
        # For a oncely holiday where we want to use only one holiday id
        # but it becomes useful to expose the multiple start times
        self.multipleStartHolidays.append((holidayId, startAndEndList))

    def getMultipleStartHolidays(self):
        """Return our list of multiple start holidays."""
        return self.multipleStartHolidays

    def sendMultipleStartHolidays(self):
        """Force a send of the oncely calendar holidays."""
        self.sendUpdate("setMultipleStartHolidays", [self.multipleStartHolidays])

    def sendOncelyCalendarHolidays(self):
        """Force a send of the oncely calendar holidays."""
        self.sendUpdate("setOncelyCalendarHolidays", [self.oncelyCalendarHolidays])
        
    def addRelativelyCalendarHoliday(self, holidayId, firstStartTime, lastEndTime):
        """Add a new oncely holiday."""
        # Note the holiday can have breaks in it.  e.g. no bloodsucker invasion
        # happens between 3 and 6 pm on halloween, however for simplicity
        # we just note the first time it will happen, and the last end time for it
        self.relativelyCalendarHolidays.append((holidayId, firstStartTime, lastEndTime))

    def getRelativelyCalendarHolidays(self):
        """Return our list of Relatively calendar holidays."""
        return self.relativelyCalendarHolidays

    def sendRelativelyCalendarHolidays(self):
        """Force a send of the Relatively calendar holidays."""
        self.sendUpdate("setRelativelyCalendarHolidays", [self.relativelyCalendarHolidays])

