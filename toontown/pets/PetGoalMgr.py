from pandac.PandaModules import *
from direct.directnotify import DirectNotifyGlobal
from direct.showbase import DirectObject
from direct.showbase.PythonUtil import randFloat, lerp
from toontown.pets import PetConstants
import random

class PetGoalMgr(DirectObject.DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('PetGoalMgr')

    def __init__(self, pet):
        self.pet = pet
        self.goals = {}
        self._hasTrickGoal = False
        self.primaryGoal = None
        self.primaryStartT = 0
        if __dev__:
            self.pscSetup = PStatCollector('App:Show code:petThink:UpdatePriorities:Setup')
            self.pscFindPrimary = PStatCollector('App:Show code:petThink:UpdatePriorities:FindPrimary')
            self.pscSetPrimary = PStatCollector('App:Show code:petThink:UpdatePriorities:SetPrimary')
        return

    def destroy(self):
        if __dev__:
            del self.pscSetup
            del self.pscFindPrimary
            del self.pscSetPrimary
        goals = list(self.goals.keys())
        for goal in goals:
            self.removeGoal(goal)
            goal.destroy()

        del self.goals

    def hasTrickGoal(self):
        return self._hasTrickGoal

    def _setHasTrickGoal(self, hasTrickGoal):
        self._hasTrickGoal = hasTrickGoal

    def addGoal(self, goal):
        self.goals[goal] = None
        goal.setGoalMgr(self)
        return

    def removeGoal(self, goal):
        if self.primaryGoal == goal:
            self._setPrimaryGoal(None)
        goal.clearGoalMgr()
        del self.goals[goal]
        return

    def updatePriorities(self):
        if len(self.goals) == 0:
            return
        if __dev__:
            self.pscSetup.start()
        if self.primaryGoal is None:
            highestPriority = -99999.0
            candidates = []
        else:
            highestPriority = self.primaryGoal.getPriority()
            candidates = [self.primaryGoal]
            decayDur = PetConstants.PrimaryGoalDecayDur
            priFactor = PetConstants.PrimaryGoalScale
            elapsed = min(decayDur, globalClock.getFrameTime() - self.primaryStartT)
            highestPriority *= lerp(priFactor, 1.0, elapsed / decayDur)
        if __dev__:
            self.pscSetup.stop()
        if __dev__:
            self.pscFindPrimary.start()
        for goal in self.goals:
            thisPri = goal.getPriority()
            if thisPri >= highestPriority:
                if thisPri > highestPriority:
                    highestPriority = thisPri
                    candidates = [goal]
                else:
                    candidates.append(goal)

        if __dev__:
            self.pscFindPrimary.stop()
        if __dev__:
            self.pscSetPrimary.start()
        newPrimary = random.choice(candidates)
        if self.primaryGoal != newPrimary:
            self.pet.notify.debug('new goal: %s, priority=%s' % (newPrimary.__class__.__name__, highestPriority))
            self._setPrimaryGoal(newPrimary)
        if __dev__:
            self.pscSetPrimary.stop()
        return

    def _setPrimaryGoal(self, goal):
        if self.primaryGoal == goal:
            return
        if self.primaryGoal is not None:
            self.primaryGoal.fsm.request('background')
        self.primaryGoal = goal
        self.primaryStartT = globalClock.getFrameTime()
        if goal is not None:
            goal.fsm.request('foreground')
        return

    def _handlePrimaryGoalDone(self):
        self._setPrimaryGoal(None)
        return

    def __repr__(self):
        string = '%s' % self.__class__.__name__
        string += '\n Primary: %s' % self.primaryGoal
        goalPairs = []
        for goal in self.goals:
            goalPairs.append((goal.getPriority(), goal))

        goalPairs.sort()
        goalPairs.reverse()
        for goalPair in goalPairs:
            string += '\n  %s' % goalPair[1]

        return string
