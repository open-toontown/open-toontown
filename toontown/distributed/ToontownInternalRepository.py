from direct.directnotify import DirectNotifyGlobal
from otp.distributed.OTPInternalRepository import OTPInternalRepository
from otp.distributed.OtpDoGlobals import *

class ToontownInternalRepository(OTPInternalRepository):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownInternalRepository')
    GameGlobalsId = OTP_DO_ID_TOONTOWN

    def __init__(self, baseChannel, serverId=None, dcFileNames=None, dcSuffix='AI', connectMethod=None, threadedNet=None):
        OTPInternalRepository.__init__(self, baseChannel, serverId, dcFileNames, dcSuffix, connectMethod, threadedNet)

    def _isValidPlayerLocation(self, parentId, zoneId):
        if zoneId < 1000 and zoneId != 1:
            return False

        return True
