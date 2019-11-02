from otp.otpbase import OTPLocalizer
import types

class Emote:
    EmoteClear = -1
    EmoteEnableStateChanged = 'EmoteEnableStateChanged'

    def __init__(self):
        self.emoteFunc = None
        return

    def isEnabled(self, index):
        if isinstance(index, types.StringType):
            index = OTPLocalizer.EmoteFuncDict[index]
        if self.emoteFunc == None:
            return 0
        elif self.emoteFunc[index][1] == 0:
            return 1
        return 0


globalEmote = None
