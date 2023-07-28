from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObjectAI
from . import DistributedScavengerHuntTargetAI

class DistributedWinterCarolingTargetAI(DistributedScavengerHuntTargetAI.DistributedScavengerHuntTargetAI):
    """
    This class is instanced several times by WinterCarolingManagerAI.  Each one sits in
    in its assigned zone and listens for the client to say an SC
    phrase.
    """

    notify = DirectNotifyGlobal.directNotify.newCategory(
        'DistributedScavengerHuntTargetAI')
    
    def __init__(self, air, hunt, goal, totMgr):
        DistributedScavengerHuntTargetAI.DistributedScavengerHuntTargetAI.__init__(self,  \
                                                                                                            air, hunt, goal, totMgr)

    def attemptScavengerHunt(self):
        avId = self.air.getAvatarIdFromSender()
        self.shMgr.avatarAttemptingGoal(avId, self.goal)
    
