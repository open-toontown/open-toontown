from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObjectAI
from otp.otpbase import OTPGlobals
import time

EFFECT = OTPGlobals.CEBigWhite
DURATION = 60
HOOD = 3000

class DistributedPolarPlaceEffectMgrAI(DistributedObjectAI.DistributedObjectAI):
    """PolarPlace effect ai implementation. This object sits in zone 3821 ('Hibernation Vacations'
    interior) and will activate the polarPlace effect for anyone who says 'Howdy!' to Paula Behr
    during the promotion for Lawbot HQ."""

    notify = DirectNotifyGlobal.directNotify.newCategory(
        'DistributedPolarPlaceEffectMgrAI')
    
    def __init__(self, air):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)

    # do the event
    def addPolarPlaceEffect(self):
        avId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(avId)
        if not av:
            DistributedPolarPlaceEffectMgrAI.notify.warning(
                'Tried to add Polar Place effect to av %s, but they left' % avId)
        else:
            DistributedPolarPlaceEffectMgrAI.notify.warning(
                'Activating Polar Place effect for av %s' % avId)
            expireTime = (int)(time.time() / 60 + 0.5) + DURATION
            av.b_setCheesyEffect(EFFECT, HOOD, expireTime)
            
