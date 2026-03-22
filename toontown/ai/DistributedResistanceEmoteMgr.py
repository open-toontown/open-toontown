from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedObject
from direct.interval.IntervalGlobal import *
from otp.speedchat import SpeedChatGlobals
from otp.otpbase.OTPLocalizerEnglish import EmoteFuncDict
from toontown.toonbase import TTLocalizer

RESIST_INDEX = EmoteFuncDict["Resistance Salute"]


class DistributedResistanceEmoteMgr(DistributedObject.DistributedObject):
    """Resistance emote client implementation; turn a cat into a black cat if
    they say 'Do you need help?' to Whispering Willow during the promotion for Cashbot HQ."""
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedResistanceEmoteMgr')

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)

        # go ahead and start listening to speedchat
        def phraseSaid(phraseId):
            helpPhrase = 513
            if phraseId == helpPhrase:
                self.addResistanceEmote()

        self.accept(SpeedChatGlobals.SCStaticTextMsgEvent, phraseSaid)

    def announceGenerate(self):
        DistributedObject.DistributedObject.announceGenerate(self)
        self.notify.debug("announceGenerate()")

    def delete(self):
        # stop listening to speed chat
        self.ignore(SpeedChatGlobals.SCStaticTextMsgEvent)
        DistributedObject.DistributedObject.delete(self)

    # do the event
    def addResistanceEmote(self):
        self.notify.debug("addResistanceEmote()")
        av = base.localAvatar
        # make sure they haven't already done this
        if not av.emoteAccess[RESIST_INDEX]:
            self.sendUpdate('addResistanceEmote', [])

            msgTrack = Sequence(
                Wait(1),
                Func(av.setSystemMessage, 0, TTLocalizer.ResistanceEmote1),
                Wait(3),
                Func(av.setSystemMessage, 0, TTLocalizer.ResistanceEmote2),
                Wait(4),
                Func(av.setSystemMessage, 0, TTLocalizer.ResistanceEmote3),
            )
            msgTrack.start()
