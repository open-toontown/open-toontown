from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObject
from toontown.speedchat.TTSCIndexedTerminal import TTSCIndexedMsgEvent
import DistributedScavengerHuntTarget

class DistributedWinterCarolingTarget(DistributedScavengerHuntTarget.DistributedScavengerHuntTarget):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedWinterCarolingTarget')

    def __init__(self, cr):
        DistributedScavengerHuntTarget.DistributedScavengerHuntTarget.__init__(self, cr)

    def setupListenerDetails(self):
        self.triggered = False
        self.triggerDelay = 15
        self.accept(TTSCIndexedMsgEvent, self.phraseSaid)

    def phraseSaid(self, phraseId):
        self.notify.debug('Checking if phrase was said')
        helpPhrases = []
        for i in range(6):
            helpPhrases.append(30220 + i)

        def reset():
            self.triggered = False

        if phraseId in helpPhrases and not self.triggered:
            self.triggered = True
            self.attemptScavengerHunt()
            taskMgr.doMethodLater(self.triggerDelay, reset, 'ScavengerHunt-phrase-reset', extraArgs=[])
