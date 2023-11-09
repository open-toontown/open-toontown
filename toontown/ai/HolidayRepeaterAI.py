"""
The holidayRepeaterAI class repeats an existing holiday 
over an infinite period of time
"""

from toontown.toonbase import ToontownGlobals
from direct.directnotify import DirectNotifyGlobal
from . import HolidayBaseAI
from toontown.spellbook import ToontownMagicWordManagerAI

scaleFactor = 12
restartWaitTime = 60
aiInitTime = 2.5

class HolidayRepeaterAI(HolidayBaseAI.HolidayBaseAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('HolidayRepeaterAI')
    
    def __init__(self, air, holidayId, startAndEndTuple, testHolidays):
        HolidayBaseAI.HolidayBaseAI.__init__(self, air, holidayId)
        
        self.testHolidays = testHolidays
        
        self.testHolidayStates = {}
        
        self.aiInitialized = 0
        
    def start(self):
        """
        Immediately start running the test holidays on a loop
        """
        if not hasattr(self.air, "holidayManager"):
            taskMgr.doMethodLater(restartWaitTime, self.startLoop, "WaitForAir")
            self.notify.warning("holidayManager not yet created")
            return
        elif self.aiInitialized == 0:
            taskMgr.doMethodLater(aiInitTime, self.startLoop, "WaitForAir")
            self.aiInitialized = 1
            
        for holiday in list(self.testHolidays.keys()):
            # Set the holiday state to show that it has not yet begun
            if self.air.holidayManager.isHolidayRunning(holiday):
                self.air.holidayManager.endHoliday(holiday, True)
            self.testHolidayStates[holiday] = -1            
            nextStepIn = self.testHolidays[holiday][0]            
            taskMgr.doMethodLater(nextStepIn*scaleFactor, self.handleNewHolidayState, "testHoliday_" + str(holiday), extraArgs=[holiday])
            
    def startLoop(self, task):
        self.start()
        return task.done
            
    def handleNewHolidayState(self, holiday):
        nextStepIn = -1
        self.testHolidayStates[holiday] = self.testHolidayStates[holiday] + 1
        curState = self.testHolidayStates[holiday]
        if curState == 0:
            if self.air.holidayManager.isHolidayRunning(holiday):
                self.air.holidayManager.endHoliday(holiday, True)
            self.notify.debug("Starting holiday: %s" %holiday)
            simbase.air.newsManager.sendSystemMessage("Holiday " + str(holiday) + " started")
            nextStepIn = self.testHolidays[holiday][(curState+1)] - self.testHolidays[holiday][curState]
            self.air.holidayManager.startHoliday(holiday, testMode = 1)            
        elif len(self.testHolidays[holiday]) == (curState+1):
            self.notify.debug("Ending holiday: %s" %holiday)
            simbase.air.newsManager.sendSystemMessage("Holiday " + str(holiday) + " ended")
            self.air.holidayManager.endHoliday(holiday, True)
            self.testHolidayStates[holiday] = -1
        else:
            self.notify.debug("Forcing holiday: %s to phase: %s" %(holiday, curState))
            simbase.air.newsManager.sendSystemMessage("Holiday " + str(holiday) + " is in phase "+str(curState))
            nextStepIn = self.testHolidays[holiday][(curState+1)] - self.testHolidays[holiday][curState]
            self.air.holidayManager.forcePhase(holiday, curState)
        if nextStepIn == -1:
            count = 0
            for holiday in list(self.testHolidayStates.keys()):
                if self.testHolidayStates[holiday] == -1:
                    count = count+1
            if count == len(self.testHolidays):
                self.notify.debug("Finished hoiday cycle")
                simbase.air.newsManager.sendSystemMessage("Holiday cycle complete: "+ str(self.holidayId))
                taskMgr.doMethodLater(restartWaitTime, self.startLoop, "RepeatHolidays")
        else:
            taskMgr.doMethodLater(nextStepIn*scaleFactor, self.handleNewHolidayState, "testHoliday_" + str(holiday), extraArgs=[holiday])
            
    def stop(self):
        """
        End all the Test  holidays
        """
        for holiday in list(self.testHolidays.keys()):
            if taskMgr.hasTaskNamed("testHoliday_" + str(holiday)):
                taskMgr.remove("testHoliday_" + str(holiday))
            self.air.holidayManager.endHoliday(holiday, True)
            