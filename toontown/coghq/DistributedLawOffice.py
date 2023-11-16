import random

from panda3d.core import *

from direct.directnotify import DirectNotifyGlobal
from direct.distributed.ClockDelta import *
from direct.distributed.DistributedObject import DistributedObject
from direct.interval.IntervalGlobal import *

from otp.level import DistributedLevel, LevelConstants, LevelSpec

from toontown.coghq import FactoryCameraViews
from toontown.toonbase import TTLocalizer
from toontown.toonbase.ToontownGlobals import *

from . import FactoryEntityCreator, FactorySpecs, LawOfficeBase

if __dev__:
    from otp.level import EditorGlobals

class DistributedLawOffice(DistributedObject, LawOfficeBase.LawOfficeBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedLawOffice')

    def __init__(self, cr):
        DistributedObject.__init__(self, cr)
        LawOfficeBase.LawOfficeBase.__init__(self)
        self.suitIds = []
        self.suits = []
        self.reserveSuits = []
        self.joiningReserves = []
        self.suitsInitialized = 0
        self.goonClipPlanes = {}
        self.level = None
        return

    def generate(self):
        self.notify.debug('generate')
        self.accept('lawOfficeFloorDone', self.handleFloorDone)

    def delete(self):
        base.localAvatar.chatMgr.chatInputSpeedChat.removeFactoryMenu()
        self.ignore('lawOfficeFloorDone')

    def setLawOfficeId(self, id):
        LawOfficeBase.LawOfficeBase.setLawOfficeId(self, id)

    def levelAnnounceGenerate(self):
        self.notify.debug('levelAnnounceGenerate')

    def handleSOSPanel(self, panel):
        avIds = []
        for avId in self.avIdList:
            if base.cr.doId2do.get(avId):
                avIds.append(avId)

        panel.setFactoryToonIdList(avIds)

    def handleFloorDone(self):
        self.sendUpdate('readyForNextFloor')

    def disable(self):
        self.notify.debug('disable')
        base.localAvatar.setCameraCollisionsCanMove(0)

    def getTaskZoneId(self):
        return self.lawOfficeId

    def startSignal(self):
        base.camera.setScale(base.localAvatar.getScale())
        localAvatar.setCameraFov(DefaultCameraFov)
        base.camera.clearMat()
