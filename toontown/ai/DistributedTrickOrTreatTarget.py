from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObject
from otp.speedchat import SpeedChatGlobals
import DistributedScavengerHuntTarget

class DistributedTrickOrTreatTarget(DistributedScavengerHuntTarget.DistributedScavengerHuntTarget):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedTrickOrTreatTarget')

    def __init__(self, cr):
        DistributedScavengerHuntTarget.DistributedScavengerHuntTarget.__init__(self, cr)

    def phraseSaid(self, phraseId):
        self.notify.debug('Checking if phrase was said')
        helpPhrase = 10003

        def reset():
            self.triggered = False

        if phraseId == helpPhrase and not self.triggered:
            self.triggered = True
            self.attemptScavengerHunt()
            taskMgr.doMethodLater(self.triggerDelay, reset, 'ScavengerHunt-phrase-reset', extraArgs=[])
