from toontown.hood import ZeroAnimatedProp
from toontown.toonbase import ToontownGlobals
from direct.directnotify import DirectNotifyGlobal

class MailboxZeroAnimatedProp(ZeroAnimatedProp.ZeroAnimatedProp):
    notify = DirectNotifyGlobal.directNotify.newCategory('MailboxZeroAnimatedProp')
    PauseTimeMult = base.config.GetFloat('zero-pause-mult', 1.0)
    PhaseInfo = {0: ('tt_a_ara_dod_mailbox_firstMoveFlagSpin1', 40 * PauseTimeMult),
     1: (('tt_a_ara_dod_mailbox_firstMoveStruggle', 'tt_a_ara_dod_mailbox_firstMoveJump'), 20 * PauseTimeMult),
     2: ('tt_a_ara_dod_mailbox_firstMoveFlagSpin2', 10 * PauseTimeMult),
     3: ('tt_a_ara_dod_mailbox_firstMoveFlagSpin3', 8 * PauseTimeMult),
     4: ('tt_a_ara_dod_mailbox_firstMoveJumpSummersault', 6 * PauseTimeMult),
     5: ('tt_a_ara_dod_mailbox_firstMoveJumpFall', 4 * PauseTimeMult),
     6: ('tt_a_ara_dod_mailbox_firstMoveJump3Summersaults', 2 * PauseTimeMult)}

    def __init__(self, node):
        ZeroAnimatedProp.ZeroAnimatedProp.__init__(self, node, 'mailbox', self.PhaseInfo, ToontownGlobals.MAILBOX_ZERO_HOLIDAY)
