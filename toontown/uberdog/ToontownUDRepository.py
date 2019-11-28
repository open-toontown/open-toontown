from direct.directnotify import DirectNotifyGlobal

from otp.distributed.DistributedDirectoryAI import DistributedDirectoryAI
from otp.distributed.OtpDoGlobals import *
from toontown.distributed.ToontownInternalRepository import ToontownInternalRepository


# TODO: Remove Astron dependence.

class ToontownUDRepository(ToontownInternalRepository):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownUDRepository')

    def __init__(self, baseChannel, serverId):
        ToontownInternalRepository.__init__(self, baseChannel, serverId, dcSuffix='UD')
        self.astronLoginManager = None

    def handleConnected(self):
        ToontownInternalRepository.handleConnected(self)

        # Create our root object.
        self.notify.info('Creating root object (%d)...' % self.getGameDoId())
        rootObj = DistributedDirectoryAI(self)
        rootObj.generateWithRequiredAndId(self.getGameDoId(), 0, 0)

        # Create our global objects.
        self.notify.info('Creating global objects...')
        self.createGlobals()

        self.notify.info('UberDOG server is ready.')

    def createGlobals(self):
        # Create our Astron login manager...
        self.astronLoginManager = self.generateGlobalObject(OTP_DO_ID_ASTRON_LOGIN_MANAGER, 'AstronLoginManager')
