from direct.directnotify import DirectNotifyGlobal
from . import DistributedScavengerHuntTarget


class DistributedTrickOrTreatTarget(DistributedScavengerHuntTarget.DistributedScavengerHuntTarget):
    """
    Upon hearing the 'Trick or Treat!' phrase, it stops listening for
    a few seconds in order to screen repeated attempts during high lag periods.
    """

    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedTrickOrTreatTarget')

    def __init__(self, cr):
        DistributedScavengerHuntTarget.DistributedScavengerHuntTarget.__init__(self, cr)

    # go ahead and start listening to speedchat
    def phraseSaid(self, phraseId):
        self.notify.debug("Checking if phrase was said")
        helpPhrase = 10003  # 'Trick or Treat!'

        def reset():
            self.triggered = False

        if phraseId == helpPhrase and not self.triggered:
            self.triggered = True
            self.attemptScavengerHunt()
            taskMgr.doMethodLater(self.triggerDelay, reset, 'ScavengerHunt-phrase-reset', extraArgs=[])
