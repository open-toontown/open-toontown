from otp.otpbase import OTPGlobals
from .CogdoFlyingShadowPlacer import CogdoFlyingShadowPlacer

def loadMockup(fileName, dmodelsAlt = 'coffin'):
    try:
        model = loader.loadModel(fileName)
    except IOError:
        model = loader.loadModel('phase_4/models/props/%s' % dmodelsAlt)

    return model


def swapAvatarShadowPlacer(avatar, name):
    avatar.setActiveShadow(0)
    avatar.deleteDropShadow()
    avatar.initializeDropShadow()
    if avatar.shadowPlacer:
        avatar.shadowPlacer.delete()
        avatar.shadowPlacer = None
    shadowPlacer = CogdoFlyingShadowPlacer(base.shadowTrav, avatar.dropShadow, OTPGlobals.WallBitmask, OTPGlobals.FloorBitmask, name)
    avatar.shadowPlacer = shadowPlacer
    avatar.setActiveShadow(0)
    avatar.setActiveShadow(1)
    return
