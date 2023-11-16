from direct.directnotify import DirectNotifyGlobal

from toontown.hood import ZeroAnimatedProp
from toontown.toonbase import ToontownGlobals


class TrashcanZeroAnimatedProp(ZeroAnimatedProp.ZeroAnimatedProp):
    notify = DirectNotifyGlobal.directNotify.newCategory('TrashcanZeroAnimatedProp')
    PauseTimeMult = base.config.GetFloat('zero-pause-mult', 1.0)
    PhaseInfo = {0: ('tt_a_ara_dga_trashcan_firstMoveLidFlip1', 40 * PauseTimeMult),
     1: ('tt_a_ara_dga_trashcan_firstMoveStruggle', 20 * PauseTimeMult),
     2: ('tt_a_ara_dga_trashcan_firstMoveLidFlip2', 10 * PauseTimeMult),
     3: ('tt_a_ara_dga_trashcan_firstMoveJump', 8 * PauseTimeMult),
     4: ('tt_a_ara_dga_trashcan_firstMoveLidFlip3', 6 * PauseTimeMult),
     5: ('tt_a_ara_dga_trashcan_firstMoveJumpHit', 4 * PauseTimeMult),
     6: ('tt_a_ara_dga_trashcan_firstMoveJumpJuggle', 2 * PauseTimeMult)}

    def __init__(self, node):
        ZeroAnimatedProp.ZeroAnimatedProp.__init__(self, node, 'trashcan', self.PhaseInfo, ToontownGlobals.TRASHCAN_ZERO_HOLIDAY)
