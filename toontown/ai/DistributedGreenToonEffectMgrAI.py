from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObjectAI
from otp.otpbase import OTPGlobals
import time

# Update timer

EFFECT = OTPGlobals.CEGreenToon
DURATION = 8640

class DistributedGreenToonEffectMgrAI(DistributedObjectAI.DistributedObjectAI):
    """GreenToon effect ai implementation. This object sits in zone 5819 ('Green Bean Jeans'
    interior) and will activate the greenToon effect for anyone who says 'It's easy to be green!' to Eugene
    during the Ides Of March event."""

    notify = DirectNotifyGlobal.directNotify.newCategory(
        'DistributedGreenToonEffectMgrAI')

    def __init__(self, air):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)

    # do the event
    def addGreenToonEffect(self):
        avId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(avId)

        if not av:
            DistributedGreenToonEffectMgrAI.notify.warning(
                'Tried to add Green Toon effect to av %s, but they left' % avId)
        else:
            DistributedGreenToonEffectMgrAI.notify.warning(
                'Activating Green Toon effect for av %s' % avId)
            expireTime = (int)(time.time() / 60 + 0.5) + DURATION
            av.b_setCheesyEffect(EFFECT, 0, expireTime)

