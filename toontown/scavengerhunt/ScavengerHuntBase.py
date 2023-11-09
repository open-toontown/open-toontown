#from direct.directnotify import DirectNotifyGlobal
class ScavengerHuntBase:
    """
    Base class for all hunts. There is enough functionality here
    such that you shouldn't need to subclass it, though.
    """

    def __init__(self,scavengerHuntId, scavengerHuntType):
        self.id = scavengerHuntId
        self.type = scavengerHuntType
        self.goals = set()
        self.milestones = {}
        
    def defineGoals(self,goalIds):
        """
        Accepts a list of Goal identifiers.  This could be something as
        simple as a range of integers corresponding to the goals in the
        hunt.
        """
        self.goals = set(goalIds)

    def defineMilestones(self,milestones = []):
        """
        Accepts a list with items of the format:
        [milestoneId,[goal1,goal2,goal3,...]]
        """
        for id,stone in milestones:
            self.milestones[frozenset(stone)] = id

    def getRecentMilestonesHit(self,goals,mostRecentGoal):
        """
        Given a list of goals, and the most recent goal added to that
        list, return a list of milestone ids which that latest goal would
        trigger.
        """
        milestones = []

        for milestone in list(self.milestones.keys()):
            if mostRecentGoal in milestone and milestone.issubset(goals):
                milestones.append(self.milestones[milestone])
        return milestones


    def getAllMilestonesHit(self,goals):
        """
        Return a list of milestone ids which are satisfied by the Goals listed
        in goals.
        """
        milestones = []

        for milestone in list(self.milestones.keys()):
            if(milestone.issubset(goals)):
                milestones.append(self.milestones[milestone])
                                
        return milestones
        

    





    
        
