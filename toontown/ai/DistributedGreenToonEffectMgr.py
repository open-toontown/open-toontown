from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObject
from direct.interval.IntervalGlobal import *
from otp.speedchat import SpeedChatGlobals
from toontown.toonbase import TTLocalizer

class DistributedGreenToonEffectMgr(DistributedObject.DistributedObject):
    """Green toon client implementation; turn a toon green if
    they say 'It's easy to be green!' to Eugene during the Ires of March event."""
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedGreenToonEffectMgr')

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)

        def phraseSaid(phraseId):
            greenPhrase = 30450
            if phraseId == greenPhrase:
                self.addGreenToonEffect()

        self.accept(SpeedChatGlobals.SCStaticTextMsgEvent, phraseSaid)

    def announceGenerate(self):
        DistributedObject.DistributedObject.announceGenerate(self)
        self.notify.debug("announceGenerate()")

    def delete(self):
        self.ignore(SpeedChatGlobals.SCStaticTextMsgEvent)
        DistributedObject.DistributedObject.delete(self)

    def addGreenToonEffect(self):
        self.notify.debug("addGreenToonEffect()")
        av = base.localAvatar
        self.sendUpdate('addGreenToonEffect', [])
        msgTrack = Sequence(Func(av.setSystemMessage, 0, TTLocalizer.GreenToonEffectMsg))
        msgTrack.start()
