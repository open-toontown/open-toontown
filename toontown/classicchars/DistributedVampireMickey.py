from panda3d.core import *

from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State

from toontown.classicchars import DistributedMickey
from toontown.toonbase import ToontownGlobals, TTLocalizer

from . import CharStateDatas, DistributedCCharBase


class DistributedVampireMickey(DistributedMickey.DistributedMickey):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedVampireMickey')

    def __init__(self, cr):
        try:
            self.DistributedMickey_initialized
        except:
            self.DistributedMickey_initialized = 1
            DistributedCCharBase.DistributedCCharBase.__init__(self, cr, TTLocalizer.VampireMickey, 'vmk')
            self.fsm = ClassicFSM.ClassicFSM(self.getName(), [State.State('Off', self.enterOff, self.exitOff, ['Neutral']), State.State('Neutral', self.enterNeutral, self.exitNeutral, ['Walk']), State.State('Walk', self.enterWalk, self.exitWalk, ['Neutral'])], 'Off', 'Off')
            self.fsm.enterInitialState()
            self.nametag.setName(TTLocalizer.Mickey)

    def walkSpeed(self):
        return ToontownGlobals.VampireMickeySpeed
