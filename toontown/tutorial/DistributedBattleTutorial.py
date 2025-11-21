from toontown.battle import DistributedBattle
from direct.directnotify import DirectNotifyGlobal
from toontown.tutorial.BattleTutorialHelper import BattleTutorialHelper

class DistributedBattleTutorial(DistributedBattle.DistributedBattle):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBattleTutorial')

    def __init__(self, cr):
        DistributedBattle.DistributedBattle.__init__(self, cr)
        self.battleTutorialHelper = None

    def generate(self):
        DistributedBattle.DistributedBattle.generate(self)
        # Create battle tutorial helper
        self.battleTutorialHelper = BattleTutorialHelper(self)
        
    def disable(self):
        if self.battleTutorialHelper:
            self.battleTutorialHelper.stop()
            self.battleTutorialHelper = None
        DistributedBattle.DistributedBattle.disable(self)

    def enterFaceOff(self, ts=0):
        DistributedBattle.DistributedBattle.enterFaceOff(self, ts)
        if self.battleTutorialHelper:
            self.battleTutorialHelper.start()
            messenger.send('battle-start')
    
    def exitFaceOff(self):
        """Clean up tutorial helper when exiting faceoff"""
        if self.battleTutorialHelper:
            self.battleTutorialHelper.stop()
        DistributedBattle.DistributedBattle.exitFaceOff(self)
    
    def enterReward(self, ts=0):
        """Clean up tutorial helper when entering reward"""
        if self.battleTutorialHelper:
            self.battleTutorialHelper.stop()
        DistributedBattle.DistributedBattle.enterReward(self, ts)
    
    def enterResume(self):
        """Clean up tutorial helper when resuming"""
        if self.battleTutorialHelper:
            self.battleTutorialHelper.stop()
        DistributedBattle.DistributedBattle.enterResume(self)

    def playReward(self, ts):
        if self.battleTutorialHelper:
            self.battleTutorialHelper.stop()
        self.movie.playTutorialReward(ts, self.uniqueName('reward'), self.handleRewardDone)
    
    def cleanupBattle(self):
        """Ensure tutorial helper is cleaned up"""
        if self.battleTutorialHelper:
            self.battleTutorialHelper.stop()
        DistributedBattle.DistributedBattle.cleanupBattle(self)
