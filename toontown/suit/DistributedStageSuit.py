import string

from panda3d.core import *

from direct.actor import Actor
from direct.directnotify import DirectNotifyGlobal
from direct.task import Task

from otp.avatar import Avatar

from toontown.battle import BattleProps, SuitBattleGlobals
from toontown.suit import DistributedFactorySuit
from toontown.suit.Suit import *
from toontown.toonbase import ToontownGlobals, TTLocalizer

from . import SuitDNA


class DistributedStageSuit(DistributedFactorySuit.DistributedFactorySuit):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedStageSuit')

    def setCogSpec(self, spec):
        self.spec = spec
        self.setPos(spec['pos'])
        self.setH(spec['h'])
        self.originalPos = spec['pos']
        self.escapePos = spec['pos']
        self.pathEntId = spec['path']
        self.behavior = spec['behavior']
        self.skeleton = spec['skeleton']
        self.boss = spec['boss']
        self.revives = spec.get('revives')
        if self.reserve:
            self.reparentTo(hidden)
        else:
            self.doReparent()
