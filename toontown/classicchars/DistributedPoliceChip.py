from direct.showbase.ShowBaseGlobal import *
from . import DistributedCCharBase
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM
from direct.fsm import State
from . import CharStateDatas
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from . import DistributedChip

class DistributedPoliceChip(DistributedChip.DistributedChip):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPoliceChip')

    def __init__(self, cr):
        try:
            self.DistributedChip_initialized
        except:
            self.DistributedChip_initialized = 1
            DistributedCCharBase.DistributedCCharBase.__init__(self, cr, TTLocalizer.PoliceChip, 'pch')
            self.fsm = ClassicFSM.ClassicFSM(self.getName(), [State.State('Off', self.enterOff, self.exitOff, ['Neutral']), State.State('Neutral', self.enterNeutral, self.exitNeutral, ['Walk']), State.State('Walk', self.enterWalk, self.exitWalk, ['Neutral'])], 'Off', 'Off')
            self.fsm.enterInitialState()
            self.handleHolidays()
            self.nametag.setName(TTLocalizer.Chip)
