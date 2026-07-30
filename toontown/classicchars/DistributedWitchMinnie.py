from panda3d.core import *

from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State

from toontown.classicchars import DistributedMinnie
from toontown.toonbase import ToontownGlobals, TTLocalizer

from . import CharStateDatas, DistributedCCharBase


class DistributedWitchMinnie(DistributedMinnie.DistributedMinnie):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedWitchMinnie')

    def __init__(self, cr):
        try:
            self.DistributedMinnie_initialized
        except:
            self.DistributedMinnie_initialized = 1
            DistributedCCharBase.DistributedCCharBase.__init__(self, cr, TTLocalizer.WitchMinnie, 'wmn')
            self.fsm = ClassicFSM.ClassicFSM(self.getName(), [State.State('Off', self.enterOff, self.exitOff, ['Neutral']), State.State('Neutral', self.enterNeutral, self.exitNeutral, ['Walk']), State.State('Walk', self.enterWalk, self.exitWalk, ['Neutral'])], 'Off', 'Off')
            self.fsm.enterInitialState()
            self.nametag.setName(TTLocalizer.Minnie)

    def walkSpeed(self):
        return ToontownGlobals.WitchMinnieSpeed
