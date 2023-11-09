from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObjectAI

class DistributedScavengerHuntTargetAI(DistributedObjectAI.DistributedObjectAI):
    """
    This class is instanced several times by ScavengerHuntManagerAI.  Each one sits in
    in its assigned zone and listens for an event on the client
    """

    notify = DirectNotifyGlobal.directNotify.newCategory(
        'DistributedScavengerHuntTargetAI')
    
    def __init__(self, air, hunt, goal, shMgr):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.goal = goal
        self.shMgr = shMgr

    def attemptScavengerHunt(self):
        avId = self.air.getAvatarIdFromSender()
        self.shMgr.avatarAttemptingGoal(avId, self.goal)
    
