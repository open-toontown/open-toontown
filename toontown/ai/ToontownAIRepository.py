from direct.directnotify import DirectNotifyGlobal
from direct.distributed.PyDatagram import *
from toontown.distributed.ToontownInternalRepository import ToontownInternalRepository
from toontown.distributed.ToontownDistrictAI import ToontownDistrictAI
from otp.distributed.OtpDoGlobals import *

class ToontownAIRepository(ToontownInternalRepository):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToontownAIRepository')

    def __init__(self, baseChannel, serverId, districtName):
        ToontownInternalRepository.__init__(self, baseChannel, serverId, dcSuffix='AI')
        self.districtName = districtName
        self.districtId = None
        self.district = None

    def handleConnected(self):
        ToontownInternalRepository.handleConnected(self)

        # Generate our district...
        self.districtId = self.allocateChannel()
        self.district = ToontownDistrictAI(self)
        self.district.setName(self.districtName)
        self.district.generateWithRequiredAndId(self.districtId, self.getGameDoId(), OTP_ZONE_ID_DISTRICTS)

        # Claim ownership of that district...
        self.district.setAI(self.ourChannel)

        # Make our district available, and we're done.
        self.district.b_setAvailable(True)
        self.notify.info('Done.')
