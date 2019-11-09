from direct.directnotify import DirectNotifyGlobal
from otp.distributed.OTPInternalRepository import OTPInternalRepository

class ToontownInternalRepository(OTPInternalRepository):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownInternalRepository')

    def __init__(self, baseChannel, serverId=None, dcFileNames=None, dcSuffix='AI', connectMethod=None, threadedNet=None):
        OTPInternalRepository.__init__(self, baseChannel, serverId, dcFileNames, dcSuffix, connectMethod, threadedNet)
