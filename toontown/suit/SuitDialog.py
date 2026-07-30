import random
from direct.directnotify import DirectNotifyGlobal
from otp.otpbase import OTPLocalizer
from toontown.toonbase import TTLocalizer
notify = DirectNotifyGlobal.directNotify.newCategory('SuitDialog')

def getBrushOffIndex(suitName):
    if suitName in SuitBrushOffs:
        brushoffs = SuitBrushOffs[suitName]
    else:
        brushoffs = SuitBrushOffs[None]
    num = len(brushoffs)
    chunk = 100 / num
    randNum = random.randint(0, 99)
    count = chunk
    for i in range(num):
        if randNum < count:
            return i
        count += chunk

    notify.error('getBrushOffs() - no brush off found!')
    return


def getBrushOffText(suitName, index):
    if suitName in SuitBrushOffs:
        brushoffs = SuitBrushOffs[suitName]
    else:
        brushoffs = SuitBrushOffs[None]
    return brushoffs[index]


SuitBrushOffs = OTPLocalizer.SuitBrushOffs
