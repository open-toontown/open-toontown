from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State
from direct.showbase.ShowBaseGlobal import *

from toontown.hood import TTHood
from toontown.toonbase import ToontownGlobals, TTLocalizer

from . import CharStateDatas, DistributedCCharBase, DistributedDaisy


class DistributedSockHopDaisy(DistributedDaisy.DistributedDaisy):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedSockHopDaisy')

    def __init__(self, cr):
        try:
            self.DistributedSockHopDaisy_initialized
        except:
            self.DistributedSockHopDaisy_initialized = 1
            DistributedCCharBase.DistributedCCharBase.__init__(self, cr, TTLocalizer.SockHopDaisy, 'shdd')
            self.fsm = ClassicFSM.ClassicFSM(self.getName(), [State.State('Off', self.enterOff, self.exitOff, ['Neutral']), State.State('Neutral', self.enterNeutral, self.exitNeutral, ['Walk']), State.State('Walk', self.enterWalk, self.exitWalk, ['Neutral'])], 'Off', 'Off')
            self.fsm.enterInitialState()
            self.nametag.setName(TTLocalizer.Daisy)
            self.handleHolidays()
