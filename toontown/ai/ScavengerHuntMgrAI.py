from direct.directnotify import DirectNotifyGlobal
from direct.interval.IntervalGlobal import *
from toontown.ai import HolidayBaseAI
from otp.otpbase import OTPGlobals
from toontown.toonbase import ToontownGlobals
from toontown.hood import ZoneUtil
from toontown.ai import DistributedScavengerHuntTargetAI
from toontown.scavengerhunt.ScavengerHuntBase import ScavengerHuntBase
from toontown.uberdog.DataStoreAIClient import DataStoreAIClient
from toontown.uberdog import DataStoreGlobals

import time
import pickle

# This dictionary defines the relationship between the scavenger hunt goal id and the zone where the goal is located.
# goalId: zoneId
GOALS = {
    # 0 : 2649,   # TTC    
    # 1 : 1834,   # DD
    # 2 : 4835,   # MM
    # 3 : 5620,   # DG
    # 4 : 3707,   # BR
    # 5 : 9619,   # DL
    0 : 1000,
    1 : 2000,
    }

# This dictionary defines the milestones for this scavenger hunt
MILESTONES = {
    #0: (GOALS.keys(), 'All Trick-or-Treat goals found'),
    0: ((0, 1), 'All Scavenger hunt goals found'),
    }

class ScavengerHuntMgrAI(HolidayBaseAI.HolidayBaseAI):
    """
    This is the main Scavenger hunt holiday class.  It will create
    several distributed listeners in selected zones.  These listeners
    will wait for a toon to trigger something; for example an SC event.
    """

    notify = DirectNotifyGlobal.directNotify.newCategory(
        'ScavengerHuntMgrAI')

    PostName = 'ScavangerHunt'

    def __init__(self, air, holidayId):
        HolidayBaseAI.HolidayBaseAI.__init__(self, air, holidayId)
        self.hunt = None
        self.targets = {}
        self.storeClient = DataStoreAIClient(air,
                                             DataStoreGlobals.SH,
                                             self.receiveScavengerHuntResults)
    
    @property
    def goals(self):
        return GOALS
    
    @property
    def milestones(self):
        return MILESTONES
        
    def start(self):
        # Create a unique id for this hunt based on it's start date and time
        localTime = time.localtime()
        date = (localTime[0],
                localTime[1],
                localTime[2],
                localTime[6],
                )
        from toontown.ai import HolidayManagerAI
        startTime = HolidayManagerAI.HolidayManagerAI.holidays[self.holidayId].getStartTime(date)
        scavengerHuntId = abs(hash(time.ctime(startTime)))

        # Create the hunt
        self.hunt = ScavengerHuntBase(scavengerHuntId, self.holidayId)
        self.hunt.defineGoals(list(self.goals.keys()))
        # Send a list with one item in it: [0, (0, 1, 2, 3, 4, 5)]
        # This milestone defines the end of the hunt.

        self.hunt.defineMilestones((x[0],x[1][0]) for x in list(self.milestones.items()))
        
        self.createListeners()
            
        # let the holiday system know we started
        bboard.post(ScavengerHuntMgrAI.PostName)

        # make sure the uberdog data store is up for this hunt
        self.storeClient.openStore()
        
    def createListeners(self):
        """
        Create the listeners that will look for an event in the relavent zone
        """
        for id in list(self.goals.keys()):
            mgrAI = DistributedScavengerHuntTargetAI.DistributedScavengerHuntTargetAI(self.air,
                                                                                self.hunt,
                                                                                id,
                                                                                self,
                                                                                )
            self.targets[id] = mgrAI
            self.targets[id].generateWithRequired(self.goals[id])
                                                                             

    def stop(self):
        # let the holiday system know we stopped
        bboard.remove(ScavengerHuntMgrAI.PostName)
        # remove the targetAI's and their distributed counterparts
        for zone in list(self.goals.keys()):
            self.targets[zone].requestDelete()
        
        self.storeClient.closeStore()

    def avatarAttemptingGoal(self, avId, goal):
        # We need to know what goals have already been completed
        # in order to proceed.  Ask the Uberdog for the data.
        # We send the goal since when the Uberdog responds we
        # still need to match the new goal with the avId.
        queryData = (avId, goal)
        self.sendScavengerHuntQuery('GetGoals', queryData)

    def avatarCompletedGoal(self, avId, goal):
        # This will ask the Uberdog to add this new goal
        # to the avId's completed list.
        queryData = (avId, goal)
        self.sendScavengerHuntQuery('AddGoal', queryData)

    def sendScavengerHuntQuery(self, qTypeString, qData):
        # send a finalized query to the Uberdog.
        self.storeClient.sendQuery(qTypeString, qData)
        
    def receiveScavengerHuntResults(self, results):
        # This function handles the result message from
        # the Uberdog.  See the ScavengerHuntDataStore
        # class to see data format.

        # Indicates that the qId was invalid for this store.
        # Should never really happen
        if results == None:
            return
        else:
            # extract the queryId, and translate it to it's string
            qId, data = results            
            qType = self.storeClient.getQueryTypeString(qId)
            
            # We're receiving an avatar's new goal and list of completed goals
            if qType == 'GetGoals':
                avId, goal, done_goals = data
                # See what needs to be done
                self.__handleResult(avId, done_goals, goal)
            # The goal was successfully added to this avId
            elif qType == 'AddGoal':
                avId, = data

    def __handleResult(self, avId, done_goals, goal):
        # This is where we check to see if the goal has already been completed.
        # If it's already done, let the client know.  Otherwise, check to see
        # if the scavenger hunt is complete and respond accordingly.
        if goal in done_goals:
            ScavengerHuntMgrAI.notify.debug(
                repr(avId)+' already found Scavenger hunt target '+repr(goal)+': '+repr(self.goals.get(goal, 'INVALID GOAL ID IN '+self.PostName)))
            av = self.air.doId2do.get(avId)
            
            milestoneIds = self.hunt.getRecentMilestonesHit(done_goals+[goal], goal)

            if milestoneIds:
                for id in milestoneIds:
                    ScavengerHuntMgrAI.notify.debug(
                        repr(avId)+' hit milestone ' + repr(id) + ': ' + self.milestones.get(milestoneIds[id], [None, 'Undefined milestone id in '+self.PostName])[1])
                        
                    if (id == 0): # handle found all targets
                        self.huntCompletedReward(avId, goal)
                    else:
                        self.huntGoalFound(avId, goal)
            else:            
                self.huntGoalAlreadyFound(avId)
        elif 0 <= goal <= len(list(self.goals.keys())):
            ScavengerHuntMgrAI.notify.debug(
                repr(avId)+' found Scavenger hunt target '+repr(goal))
            av = self.air.doId2do.get(avId)
            
            if not av:
                ScavengerHuntMgrAI.notify.warning(
                    'Tried to send goal feedback to av %s, but they left' % avId)
            else:
                milestoneIds = self.hunt.getRecentMilestonesHit(done_goals+[goal], goal)

                if milestoneIds:
                    for id in milestoneIds:
                        ScavengerHuntMgrAI.notify.debug(
                            repr(avId)+' hit milestone ' + repr(id) + ': ' + self.milestones.get(milestoneIds[id], [None, 'Undefined milestone id in '+self.PostName])[1])

                        if (id == 0): # handle found all targets
                            # Wait for the goal found reward to complete
                            taskMgr.doMethodLater(10, self.huntCompletedReward, repr(avId)+'-huntCompletedReward', extraArgs = [avId, goal, True])
                            self.huntGoalFound(avId, goal)
                else:
                    self.huntGoalFound(avId, goal)

    def huntCompletedReward(self, avId, goal, firstTime = False):
        """
        Reward the Toon
        """
        pass
            
    def huntGoalAlreadyFound(self, avId):
        """
        This goal has already been found
        """
        pass 
            
    def huntGoalFound(self, avId, goal):
        """
        One of the goals in the milestone were found,
        so we reward the toon.
        """
        pass 