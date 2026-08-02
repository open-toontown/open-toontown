from panda3d.core import *

# Write some code here and press f12 :3
# You have access to reference global vars (mainly base)
from otp.otpbase.OTPLocalizerEnglish import EmoteFuncDict
base.localAvatar.playEmote(EmoteFuncDict['Dance'], 1, None)
base.localAvatar.broadcastHpString('i did it mom im cheating', 1, 1, 1)
