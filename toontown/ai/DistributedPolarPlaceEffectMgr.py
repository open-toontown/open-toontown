from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObject
from direct.interval.IntervalGlobal import *
from otp.speedchat import SpeedChatGlobals
from toontown.toonbase import TTLocalizer


class DistributedPolarPlaceEffectMgr(DistributedObject.DistributedObject):
    """PolarPlace effect client implementation; make the toon large and white if
    they say 'Howdy!' to Paula Behr in during the promotion for Lawbot HQ."""

    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPolarPlaceEffectMgr')

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)

        # go ahead and start listening to speedchat
        def phraseSaid(phraseId):
            helpPhrase = 104
            if phraseId == helpPhrase:
                self.addPolarPlaceEffect()

        self.accept(SpeedChatGlobals.SCStaticTextMsgEvent, phraseSaid)

    def announceGenerate(self):
        DistributedObject.DistributedObject.announceGenerate(self)
        self.notify.debug("announceGenerate()")

    def delete(self):
        # stop listening to speed chat
        self.ignore(SpeedChatGlobals.SCStaticTextMsgEvent)
        DistributedObject.DistributedObject.delete(self)

    # do the event
    def addPolarPlaceEffect(self):
        self.notify.debug("addPolarPlaceEffect()")
        av = base.localAvatar
        self.sendUpdate('addPolarPlaceEffect', [])

        msgTrack = Sequence(
            Func(av.setSystemMessage, 0, TTLocalizer.PolarPlaceEffect1),
            Wait(2),
            Func(av.setSystemMessage, 0, TTLocalizer.PolarPlaceEffect2),
            Wait(4),
            Func(av.setSystemMessage, 0, TTLocalizer.PolarPlaceEffect3),
        )
        msgTrack.start()
