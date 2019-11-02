from toontown.hood import ZeroAnimatedProp
from toontown.toonbase import ToontownGlobals
from direct.directnotify import DirectNotifyGlobal

class HydrantZeroAnimatedProp(ZeroAnimatedProp.ZeroAnimatedProp):
    notify = DirectNotifyGlobal.directNotify.newCategory('HydrantZeroAnimatedProp')
    PauseTimeMult = base.config.GetFloat('zero-pause-mult', 1.0)
    PhaseInfo = {0: ('tt_a_ara_ttc_hydrant_firstMoveArmUp1', 40 * PauseTimeMult),
     1: ('tt_a_ara_ttc_hydrant_firstMoveStruggle', 20 * PauseTimeMult),
     2: ('tt_a_ara_ttc_hydrant_firstMoveArmUp2', 10 * PauseTimeMult),
     3: ('tt_a_ara_ttc_hydrant_firstMoveJump', 8 * PauseTimeMult),
     4: ('tt_a_ara_ttc_hydrant_firstMoveJumpBalance', 6 * PauseTimeMult),
     5: ('tt_a_ara_ttc_hydrant_firstMoveArmUp3', 4 * PauseTimeMult),
     6: ('tt_a_ara_ttc_hydrant_firstMoveJumpSpin', 2 * PauseTimeMult)}

    def __init__(self, node):
        ZeroAnimatedProp.ZeroAnimatedProp.__init__(self, node, 'hydrant', self.PhaseInfo, ToontownGlobals.HYDRANT_ZERO_HOLIDAY)
