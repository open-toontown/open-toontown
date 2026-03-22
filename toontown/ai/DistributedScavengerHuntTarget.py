from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObject
from otp.speedchat import SpeedChatGlobals


class DistributedScavengerHuntTarget(DistributedObject.DistributedObject):
    """
    Upon the occurence of some event, it stops listening for
    a few seconds in order to screen repeated attempts during high lag periods.
    """

    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedScavengerHuntTarget')

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)

    def setupListenerDetails(self):
        self.triggered = False
        self.triggerDelay = 15  # Seconds to disable the listener

        self.accept(SpeedChatGlobals.SCCustomMsgEvent, self.phraseSaid)

    # go ahead and start listening to speedchat
    def phraseSaid(self, phraseId):
        self.notify.debug("Checking if phrase was said")
        helpPhrase = 10003  # 'Trick or Treat!'

        def reset():
            self.triggered = False
            # self.accept(SpeedChatGlobals.SCCustomMsgEvent, phraseSaid)

        if phraseId == helpPhrase and not self.triggered:
            self.triggered = True
            self.attemptScavengerHunt()
            # self.ignore(SpeedChatGlobals.SCCustomMsgEvent)
            taskMgr.doMethodLater(self.triggerDelay, reset, 'ScavengerHunt-phrase-reset', extraArgs=[])

    def announceGenerate(self):
        DistributedObject.DistributedObject.announceGenerate(self)
        DistributedScavengerHuntTarget.notify.debug('announceGenerate')

        self.setupListenerDetails()

    def delete(self):
        # stop listening to speed chat
        self.ignoreAll()
        taskMgr.remove('ScavengerHunt-phrase-reset')
        DistributedObject.DistributedObject.delete(self)

    # do the event
    def attemptScavengerHunt(self):
        self.notify.debug("attemptScavengerHunt()")
        self.sendUpdate('attemptScavengerHunt', [])
