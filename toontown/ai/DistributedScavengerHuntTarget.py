from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObject
from otp.speedchat import SpeedChatGlobals

class DistributedScavengerHuntTarget(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedScavengerHuntTarget')

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)

    def setupListenerDetails(self):
        self.triggered = False
        self.triggerDelay = 15
        self.accept(SpeedChatGlobals.SCCustomMsgEvent, self.phraseSaid)

    def phraseSaid(self, phraseId):
        self.notify.debug('Checking if phrase was said')
        helpPhrase = 10003

        def reset():
            self.triggered = False

        if phraseId == helpPhrase and not self.triggered:
            self.triggered = True
            self.attemptScavengerHunt()
            taskMgr.doMethodLater(self.triggerDelay, reset, 'ScavengerHunt-phrase-reset', extraArgs=[])

    def announceGenerate(self):
        DistributedObject.DistributedObject.announceGenerate(self)
        DistributedScavengerHuntTarget.notify.debug('announceGenerate')
        self.setupListenerDetails()

    def delete(self):
        self.ignoreAll()
        taskMgr.remove('ScavengerHunt-phrase-reset')
        DistributedObject.DistributedObject.delete(self)

    def attemptScavengerHunt(self):
        DistributedScavengerHuntTarget.notify.debug('attempScavengerHunt')
        self.sendUpdate('attemptScavengerHunt', [])
