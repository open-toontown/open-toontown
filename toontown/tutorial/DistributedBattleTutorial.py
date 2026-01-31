from direct.directnotify import DirectNotifyGlobal
from toontown.battle import DistributedBattle


class DistributedBattleTutorial(DistributedBattle.DistributedBattle):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBattleTutorial')

    def startTimer(self, ts=0):
        # Instead of starting the countdown,
        # hide the clock!
        self.townBattle.timer.hide()

    def playReward(self, ts):
        self.movie.playTutorialReward(ts, self.uniqueName('reward'),
                                      self.handleRewardDone)
