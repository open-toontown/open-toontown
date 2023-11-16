import random

from panda3d.core import *
from panda3d.otp import *

from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State
from direct.interval.IntervalGlobal import *

from otp.avatar import Emote

from toontown.battle import SuitBattleGlobals
from toontown.battle.BattleBase import *
from toontown.coghq import DistributedLevelBattle
from toontown.suit import SuitDNA
from toontown.toon import TTEmote
from toontown.toonbase import ToontownGlobals


class DistributedBattleFactory(DistributedLevelBattle.DistributedLevelBattle):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBattleFactory')

    def __init__(self, cr):
        DistributedLevelBattle.DistributedLevelBattle.__init__(self, cr)
        self.fsm.addState(State.State('FactoryReward', self.enterFactoryReward, self.exitFactoryReward, ['Resume']))
        offState = self.fsm.getStateNamed('Off')
        offState.addTransition('FactoryReward')
        playMovieState = self.fsm.getStateNamed('PlayMovie')
        playMovieState.addTransition('FactoryReward')

    def enterFactoryReward(self, ts):
        self.notify.info('enterFactoryReward()')
        self.disableCollision()
        self.delayDeleteMembers()
        if self.hasLocalToon():
            NametagGlobals.setMasterArrowsOn(0)
            if self.bossBattle:
                messenger.send('localToonConfrontedForeman')
        self.movie.playReward(ts, self.uniqueName('building-reward'), self.__handleFactoryRewardDone)

    def __handleFactoryRewardDone(self):
        self.notify.info('Factory reward done')
        if self.hasLocalToon():
            self.d_rewardDone(base.localAvatar.doId)
        self.movie.resetReward()
        self.fsm.request('Resume')

    def exitFactoryReward(self):
        self.notify.info('exitFactoryReward()')
        self.movie.resetReward(finish=1)
        self._removeMembersKeep()
        NametagGlobals.setMasterArrowsOn(1)
