from . import ScavengerHuntMgrAI
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from toontown.ai import DistributedTrickOrTreatTargetAI
from otp.otpbase import OTPGlobals

import time

GOALS = {
    0 : 2649,   # TTC
    1 : 1834,   # DD
    2 : 4835,   # MM
    3 : 5620,   # DG
    4 : 3707,   # BR
    5 : 9619,   # DL
    }

# This dictionary defines the milestones for this scavenger hunt
MILESTONES = {
    0: ((0, 1, 2, 3, 4, 5), 'All Trick-or-Treat goals found'),
    }

class TrickOrTreatMgrAI(ScavengerHuntMgrAI.ScavengerHuntMgrAI):
    """
    This is the TrickOrTreat manager that extends the scanvenger hunt
    by providing unique rewards and milestones.
    """

    notify = DirectNotifyGlobal.directNotify.newCategory('TrickOrTreatMgrAI')

    def __init__(self, air, holidayId):
        ScavengerHuntMgrAI.ScavengerHuntMgrAI.__init__(self, air, holidayId)

    def createListeners(self):
        """
        Create the listeners that will look for an event in the relavent zone
        """
        for id in list(self.goals.keys()):
            mgrAI = DistributedTrickOrTreatTargetAI.DistributedTrickOrTreatTargetAI(self.air,
                                                                                self.hunt,
                                                                                id,
                                                                                self,
                                                                                )
            self.targets[id] = mgrAI
            self.targets[id].generateWithRequired(self.goals[id])

    @property
    def goals(self):
        return GOALS

    @property
    def milestones(self):
        return MILESTONES

    def huntCompletedReward(self, avId, goal, firstTime = False):
        """
        Reward the Toon for completing the TrickOrTreat with
        a pumpkin head
        """
        if firstTime:
            self.air.writeServerEvent('pumpkinHeadEarned', avId, 'Trick-or-Treat scavenger hunt complete.')

        av = self.air.doId2do.get(avId)
        localTime = time.localtime()
        date = (localTime[0],
                localTime[1],
                localTime[2],
                localTime[6],
                )

        from toontown.ai import HolidayManagerAI
        endTime = HolidayManagerAI.HolidayManagerAI.holidays[self.holidayId].getEndTime(date)
        endTime += ToontownGlobals.TOT_REWARD_END_OFFSET_AMOUNT

        if not av:
            self.notify.warning(
                'Tried to send milestone feedback to av %s, but they left' % avId)
        else:
            av.b_setCheesyEffect(OTPGlobals.CEPumpkin, 0, (time.time()/60)+1)
            #av.b_setCheesyEffect(OTPGlobals.CEPumpkin, 0, endTime/60)

    def huntGoalAlreadyFound(self, avId):
        """
        This goal has already been found
        """
        av = self.air.doId2do.get(avId)
        if not av:
            self.notify.warning(
                'Tried to send goal feedback to av %s, but they left' % avId)
        else:
            av.sendUpdate('trickOrTreatTargetMet', [0])

    def huntGoalFound(self, avId, goal):
        """
        One of the goals in the milestone were found,
        so we reward the toon.
        """
        av = self.air.doId2do.get(avId)
        # Do all the updates at once
        av.addMoney(ToontownGlobals.TOT_REWARD_JELLYBEAN_AMOUNT)
        self.avatarCompletedGoal(avId, goal)
        # Start jellybean reward effect
        av.sendUpdate('trickOrTreatTargetMet', [ToontownGlobals.TOT_REWARD_JELLYBEAN_AMOUNT])