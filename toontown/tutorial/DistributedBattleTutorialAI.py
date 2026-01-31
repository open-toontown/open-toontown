from toontown.battle import DistributedBattleAI
from toontown.battle import DistributedBattleBaseAI
from direct.directnotify import DirectNotifyGlobal

class DistributedBattleTutorialAI(DistributedBattleAI.DistributedBattleAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBattleTutorialAI')
    
    def __init__(self, air, battleMgr, pos, suit, toonId, zoneId,
                 finishCallback=None, maxSuits=4, interactivePropTrackBonus = -1):
        """__init__(air, battleMgr, pos, suit, toonId, zoneId,
                 finishCallback, maxSuits)
        """
        DistributedBattleAI.DistributedBattleAI.__init__(
            self, air, battleMgr, pos, suit, toonId, zoneId,
            finishCallback, maxSuits, tutorialFlag=1)

    # There is no timer in the tutorial... The reward movie is random length.
    def startRewardTimer(self):
        pass

    #def handleRewardDone(self):
    #    DistributedBattleAI.DistributedBattleAI.handleRewardDone(self)
        
