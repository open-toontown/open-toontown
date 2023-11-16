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


class DistributedStageBattle(DistributedLevelBattle.DistributedLevelBattle):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedStageBattle')

    def __init__(self, cr):
        DistributedLevelBattle.DistributedLevelBattle.__init__(self, cr)
        self.fsm.addState(State.State('StageReward', self.enterStageReward, self.exitStageReward, ['Resume']))
        offState = self.fsm.getStateNamed('Off')
        offState.addTransition('StageReward')
        playMovieState = self.fsm.getStateNamed('PlayMovie')
        playMovieState.addTransition('StageReward')

    def enterStageReward(self, ts):
        self.notify.debug('enterStageReward()')
        self.disableCollision()
        self.delayDeleteMembers()
        if self.hasLocalToon():
            NametagGlobals.setMasterArrowsOn(0)
            if self.bossBattle:
                messenger.send('localToonConfrontedStageBoss')
        self.movie.playReward(ts, self.uniqueName('building-reward'), self.__handleStageRewardDone)

    def __handleStageRewardDone(self):
        self.notify.debug('stage reward done')
        if self.hasLocalToon():
            self.d_rewardDone(base.localAvatar.doId)
        self.movie.resetReward()
        self.fsm.request('Resume')

    def exitStageReward(self):
        self.notify.debug('exitStageReward()')
        self.movie.resetReward(finish=1)
        self._removeMembersKeep()
        NametagGlobals.setMasterArrowsOn(1)
