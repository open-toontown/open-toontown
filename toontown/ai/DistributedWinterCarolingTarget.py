from direct.directnotify import DirectNotifyGlobal
from toontown.speedchat.TTSCIndexedTerminal import TTSCIndexedMsgEvent
from . import DistributedScavengerHuntTarget


class DistributedWinterCarolingTarget(DistributedScavengerHuntTarget.DistributedScavengerHuntTarget):
    """
    Upon hearing a musical phrase, it stops listening for
    a few seconds in order to screen repeated attempts during high lag periods.
    """

    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedWinterCarolingTarget')

    def __init__(self, cr):
        DistributedScavengerHuntTarget.DistributedScavengerHuntTarget.__init__(self, cr)

    def setupListenerDetails(self):
        self.triggered = False
        self.triggerDelay = 15  # Seconds to disable the listener
        self.accept(TTSCIndexedMsgEvent, self.phraseSaid)

        # go ahead and start listening to speedchat

    def phraseSaid(self, phraseId):
        self.notify.debug("Checking if phrase was said")
        helpPhrases = []
        for i in range(6):
            helpPhrases.append(60220 + i)

        def reset():
            self.triggered = False

        if phraseId in helpPhrases and not self.triggered:
            self.triggered = True
            self.attemptScavengerHunt()
            taskMgr.doMethodLater(self.triggerDelay, reset, 'ScavengerHunt-phrase-reset', extraArgs=[])
