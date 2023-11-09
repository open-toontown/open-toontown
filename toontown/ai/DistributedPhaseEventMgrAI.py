import datetime
from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObjectAI

class DistributedPhaseEventMgrAI(DistributedObjectAI.DistributedObjectAI):
    """Distributed Object to tell the client what phase we're in."""
    
    notify = DirectNotifyGlobal.directNotify.newCategory(
        'DistributedPhaseEventMgrAI')
    
    def __init__(self, air, startAndEndTimes, phaseDates):
        """Construct ourself and calc required fields."""
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.startAndEndTimes = startAndEndTimes
        self.phaseDates = phaseDates
        self.curPhase = -1
        self.calcCurPhase();
        self.isRunning = False
        self.calcIsRunning()
        # we seem to be starting 5 seconds before the start time
        self.isRunning = True
        
    def getDates(self):
        """
        Send over the startAndEndTimes and the phaseDates
        """
        holidayDates = []
        holidayDates.append(self.startAndEndTimes[-1].start)
        for phaseDate in self.phaseDates:
            holidayDates.append(phaseDate)
        holidayDates.append(self.startAndEndTimes[-1].end)
        
        holidayDatesList = []
        for holidayDate in holidayDates:
            holidayDatesList.append((holidayDate.year, holidayDate.month, holidayDate.day, \
                                                holidayDate.hour, holidayDate.minute, holidayDate.second))
                                                
        return holidayDatesList

    def announceGenerate(self):
        self.notify.debugStateCall(self)
        self.switchPhaseTaskName = self.uniqueName("switchPhase")
        self.setupNextPhase()
        
    def calcCurPhase(self):
        self.notify.debugStateCall(self)
        myTime = datetime.datetime.today()
        result = self.getNumPhases()-1
        for index, phaseDate in enumerate( self.phaseDates):
            if myTime < phaseDate:
                result = index
                break
        self.curPhase = result

    def calcIsRunning(self):
        self.notify.debugStateCall(self)
        myTime = datetime.datetime.today()
        foundInBetween = False
        for startAndEnd in self.startAndEndTimes:
            if startAndEnd.isInBetween(myTime):
                foundInBetween = True
                break
        self.isRunning = foundInBetween
        # note we will get deleted when the holiday stops

    def setupNextPhase(self):
        """Setup a task to force us to go to the next phase if needed."""
        self.notify.debugStateCall(self)
        curTime = datetime.datetime.today()
        endTime = self.getPhaseEndTime(self.curPhase)
        if curTime < endTime:
            duration = endTime - curTime
            waitTime = (duration.days * 60 *60 * 24) + duration.seconds + \
                                duration.microseconds * 0.000001
            self.notify.debug("startingNextPhase in %s" % waitTime)
            self.startSwitchPhaseTask(waitTime)
        else:
            self.notify.warning("at phase %s, endTime is in the past %s, not starting task to switch" % (self.curPhase, endTime))
        pass

    def startSwitchPhaseTask(self, waitTime):
        """Startup our doMethodLater to switch to the next phase."""
        self.notify.debugStateCall(self)
        taskMgr.doMethodLater(waitTime, self.doSwitchPhase, self.switchPhaseTaskName)

    def stopSwitchPhaseTask(self):
        """Stop our switch phase task."""
        self.notify.debugStateCall(self)
        taskMgr.removeTask(self.switchPhaseTaskName)

    def doSwitchPhase(self, task):
        """We've waited long enough actually switch the phase now."""
        self.notify.debugStateCall(self)
        if self.curPhase < 0:
            self.notify.warning("doSwitchPhase doing nothing as curPhase=%s" % self.curPhase)
        elif self.curPhase == self.getNumPhases()-1:
            self.notify.debug("at last phase doing nothing")
        else:
            self.b_setCurPhase(self.curPhase+1)
            self.notify.debug("switching phase, newPhase=%d" % self.curPhase)
            self.setupNextPhase()
        return task.done
    
    
    def getPhaseEndTime(self, phase):
        """Return a date time on when this phase will end."""
        self.notify.debugStateCall(self)
        result = datetime.datetime.today() 
        if (0<=phase) and (phase < (self.getNumPhases() - 1)):
            result =self.phaseDates[phase]
        elif phase == self.getNumPhases() - 1:
            result = self.startAndEndTimes[-1].end
        else:
            self.notify.warning("getPhaseEndTime got invalid phase %s returning now" % phase)
            
        return result

    def getNumPhases(self):
        """Return how many phases we have."""
        result =  len(self.phaseDates) + 1
        return result   

    def getCurPhase(self):
        return self.curPhase

    def getIsRunning(self):
        return self.isRunning

    def setCurPhase(self, newPhase):
        self.notify.debugStateCall(self)
        self.curPhase = newPhase

    def d_setCurPhase(self, newPhase):
        self.sendUpdate("setCurPhase", [newPhase])

    def b_setCurPhase(self, newPhase):
        self.setCurPhase(newPhase)
        self.d_setCurPhase(newPhase)

    def forcePhase(self, newPhase):
        """Magic word is forcing us to a new phase."""
        self.notify.debugStateCall(self)
        if newPhase >= self.getNumPhases():
            self.notify.warning("ignoring newPhase %s" % newPhase)
            return
        self.b_setCurPhase(newPhase)
        
