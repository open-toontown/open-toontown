from toontown.battle import BattleManagerAI
from direct.directnotify import DirectNotifyGlobal
from . import DistributedBattleTutorialAI

class TutorialBattleManagerAI(BattleManagerAI.BattleManagerAI):

    notify = DirectNotifyGlobal.directNotify.newCategory('TutorialBattleManagerAI')

    def __init__(self, air):
        BattleManagerAI.BattleManagerAI.__init__(self, air)
        self.battleConstructor = DistributedBattleTutorialAI.DistributedBattleTutorialAI
