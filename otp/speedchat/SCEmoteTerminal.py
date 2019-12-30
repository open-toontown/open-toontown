from direct.gui.DirectGui import *
from .SCTerminal import SCTerminal
from otp.otpbase.OTPLocalizer import EmoteList, EmoteWhispers
from otp.avatar import Emote
SCEmoteMsgEvent = 'SCEmoteMsg'
SCEmoteNoAccessEvent = 'SCEmoteNoAccess'

def decodeSCEmoteWhisperMsg(emoteId, avName):
    if emoteId >= len(EmoteWhispers):
        return None
    return EmoteWhispers[emoteId] % avName


class SCEmoteTerminal(SCTerminal):

    def __init__(self, emoteId):
        SCTerminal.__init__(self)
        self.emoteId = emoteId
        if not self.__ltHasAccess():
            self.text = '?'
        else:
            self.text = EmoteList[self.emoteId]

    def __ltHasAccess(self):
        try:
            lt = base.localAvatar
            return lt.emoteAccess[self.emoteId]
        except:
            return 0

    def __emoteEnabled(self):
        if self.isWhispering():
            return 1
        return Emote.globalEmote.isEnabled(self.emoteId)

    def finalize(self, dbArgs = {}):
        if not self.isDirty():
            return
        args = {}
        if not self.__ltHasAccess() or not self.__emoteEnabled():
            args.update({'rolloverColor': (0, 0, 0, 0),
             'pressedColor': (0, 0, 0, 0),
             'rolloverSound': None,
             'text_fg': self.getColorScheme().getTextDisabledColor() + (1,)})
        if not self.__ltHasAccess():
            args.update({'text_align': TextNode.ACenter})
        elif not self.__emoteEnabled():
            args.update({'clickSound': None})
        self.lastEmoteEnableState = self.__emoteEnabled()
        args.update(dbArgs)
        SCTerminal.finalize(self, dbArgs=args)
        return

    def __emoteEnableStateChanged(self):
        if self.isDirty():
            self.notify.info("skipping __emoteEnableStateChanged; we're marked as dirty")
            return
        elif not hasattr(self, 'button'):
            self.notify.error('SCEmoteTerminal is not marked as dirty, but has no button!')
        btn = self.button
        if self.__emoteEnabled():
            rolloverColor = self.getColorScheme().getRolloverColor() + (1,)
            pressedColor = self.getColorScheme().getPressedColor() + (1,)
            btn.frameStyle[DGG.BUTTON_ROLLOVER_STATE].setColor(*rolloverColor)
            btn.frameStyle[DGG.BUTTON_DEPRESSED_STATE].setColor(*pressedColor)
            btn.updateFrameStyle()
            btn['text_fg'] = self.getColorScheme().getTextColor() + (1,)
            btn['rolloverSound'] = DGG.getDefaultRolloverSound()
            btn['clickSound'] = DGG.getDefaultClickSound()
        else:
            btn.frameStyle[DGG.BUTTON_ROLLOVER_STATE].setColor(0, 0, 0, 0)
            btn.frameStyle[DGG.BUTTON_DEPRESSED_STATE].setColor(0, 0, 0, 0)
            btn.updateFrameStyle()
            btn['text_fg'] = self.getColorScheme().getTextDisabledColor() + (1,)
            btn['rolloverSound'] = None
            btn['clickSound'] = None
        return

    def enterVisible(self):
        SCTerminal.enterVisible(self)
        if self.__ltHasAccess():
            if hasattr(self, 'lastEmoteEnableState'):
                if self.lastEmoteEnableState != self.__emoteEnabled():
                    self.invalidate()
            if not self.isWhispering():
                self.accept(Emote.globalEmote.EmoteEnableStateChanged, self.__emoteEnableStateChanged)

    def exitVisible(self):
        SCTerminal.exitVisible(self)
        self.ignore(Emote.globalEmote.EmoteEnableStateChanged)

    def handleSelect(self):
        if not self.__ltHasAccess():
            messenger.send(self.getEventName(SCEmoteNoAccessEvent))
        elif self.__emoteEnabled():
            SCTerminal.handleSelect(self)
            messenger.send(self.getEventName(SCEmoteMsgEvent), [self.emoteId])
