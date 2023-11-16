from panda3d.core import *

from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State

from toontown.classicchars import DistributedPluto
from toontown.toonbase import ToontownGlobals, TTLocalizer

from . import CharStateDatas, DistributedCCharBase


class DistributedWesternPluto(DistributedPluto.DistributedPluto):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedWesternPluto')

    def __init__(self, cr):
        try:
            self.DistributedPluto_initialized
        except:
            self.DistributedPluto_initialized = 1
            DistributedCCharBase.DistributedCCharBase.__init__(self, cr, TTLocalizer.WesternPluto, 'wp')
            self.fsm = ClassicFSM.ClassicFSM('DistributedWesternPluto', [State.State('Off', self.enterOff, self.exitOff, ['Neutral']), State.State('Neutral', self.enterNeutral, self.exitNeutral, ['Walk']), State.State('Walk', self.enterWalk, self.exitWalk, ['Neutral'])], 'Off', 'Off')
            self.fsm.enterInitialState()
            self.nametag.setName(TTLocalizer.Pluto)

    def walkSpeed(self):
        return ToontownGlobals.WesternPlutoSpeed
