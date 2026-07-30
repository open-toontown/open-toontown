from panda3d.core import *

from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State

from toontown.classicchars import DistributedGoofySpeedway
from toontown.toonbase import ToontownGlobals, TTLocalizer

from . import CharStateDatas, DistributedCCharBase


class DistributedSuperGoofy(DistributedGoofySpeedway.DistributedGoofySpeedway):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedSuperGoofy')

    def __init__(self, cr):
        try:
            self.DistributedGoofySpeedway_initialized
        except:
            self.DistributedGoofySpeedway_initialized = 1
            DistributedCCharBase.DistributedCCharBase.__init__(self, cr, TTLocalizer.SuperGoofy, 'sg')
            self.fsm = ClassicFSM.ClassicFSM(self.getName(), [State.State('Off', self.enterOff, self.exitOff, ['Neutral']), State.State('Neutral', self.enterNeutral, self.exitNeutral, ['Walk']), State.State('Walk', self.enterWalk, self.exitWalk, ['Neutral'])], 'Off', 'Off')
            self.fsm.enterInitialState()
            self.nametag.setName(TTLocalizer.Goofy)

    def walkSpeed(self):
        return ToontownGlobals.SuperGoofySpeed
