from panda3d.core import *
from direct.interval.IntervalGlobal import *
from toontown.suit import DistributedLawbotBoss
from direct.directnotify import DirectNotifyGlobal
from toontown.coghq import CogHQBossBattle

class LawbotHQBossBattle(CogHQBossBattle.CogHQBossBattle):
    notify = DirectNotifyGlobal.directNotify.newCategory('LawbotHQBossBattle')

    def __init__(self, loader, parentFSM, doneEvent):
        CogHQBossBattle.CogHQBossBattle.__init__(self, loader, parentFSM, doneEvent)
        self.teleportInPosHpr = (88, -214, 0, 210, 0, 0)

    def load(self):
        CogHQBossBattle.CogHQBossBattle.load(self)

    def unload(self):
        CogHQBossBattle.CogHQBossBattle.unload(self)

    def enter(self, requestStatus):
        CogHQBossBattle.CogHQBossBattle.enter(self, requestStatus, DistributedLawbotBoss.OneBossCog)

    def exit(self):
        CogHQBossBattle.CogHQBossBattle.exit(self)
