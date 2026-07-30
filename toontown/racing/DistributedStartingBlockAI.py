from otp.ai.AIBase import *
from toontown.toonbase import ToontownGlobals
from direct.distributed.ClockDelta import *
from direct.distributed import DistributedObjectAI
from toontown.building.ElevatorConstants import *
from toontown.building import DistributedElevatorExtAI
from direct.fsm import ClassicFSM
from direct.fsm import State
from direct.showbase.DirectObject import DirectObject
from toontown.racing.KartShopGlobals import KartGlobals
if __debug__:
    import pdb

class DistributedStartingBlockAI(DistributedObjectAI.DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedStartingBlockAI')

    def __init__(self, air, kartPad, x, y, z, h, p, r, padLocationId):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.avId = 0
        self.isActive = True
        self.kartPad = kartPad
        self.unexpectedEvent = None
        self.padLocationId = padLocationId
        self.posHpr = (x, y, z, h, p, r)
        self.currentMovie = None
        return

    def delete(self):
        self.avId = 0
        self.kartPad = None
        DistributedObjectAI.DistributedObjectAI.delete(self)
        return

    def getPadDoId(self):
        return self.kartPad.getDoId()

    def getPadLocationId(self):
        return self.padLocationId

    def getPosHpr(self):
        return self.posHpr

    def setActive(self, isActive):
        self.isActive = isActive

    def requestEnter(self, paid):
        avId = self.air.getAvatarIdFromSender()
        if self.isActive and self.avId == 0:
            success = self.kartPad.addAvBlock(avId, self, paid)
            self.notify.debug('requestEnter: avId %s wants to enter the kart block.' % avId)
            if success == KartGlobals.ERROR_CODE.success:
                self.avId = avId
                self.isActive = False
                self.unexpectedEvent = self.air.getAvatarExitEvent(self.avId)
                self.acceptOnce(self.unexpectedEvent, self.unexpectedExit)
                self.d_setOccupied(self.avId)
                self.d_setMovie(KartGlobals.ENTER_MOVIE)
            else:
                self.sendUpdateToAvatarId(avId, 'rejectEnter', [success])
        else:
            if hasattr(self.kartPad, 'state') and self.kartPad.state in ['WaitBoarding', 'AllAboard']:
                errorCode = KartGlobals.ERROR_CODE.eBoardOver
            else:
                errorCode = KartGlobals.ERROR_CODE.eOccupied
            self.sendUpdateToAvatarId(avId, 'rejectEnter', [errorCode])

    def requestExit(self):
        avId = self.air.getAvatarIdFromSender()
        self.notify.debug('requestExit: avId %s wants to exit the Kart Block.' % avId)
        success = self.validate(avId, self.avId == avId, 'requestExit: avId is not occupying this kart block.')
        if not success:
            return
        self.normalExit()

    def movieFinished(self):
        if self.currentMovie == KartGlobals.EXIT_MOVIE:
            self.cleanupAvatar()
        self.currentMovie = None
        if not self.kartPad:
            self.handleUnexpectedCleanup()
            return
        self.kartPad.kartMovieDone()
        return

    def cleanupAvatar(self):
        self.ignore(self.unexpectedEvent)
        if not self.kartPad:
            self.handleUnexpectedCleanup()
            return
        self.kartPad.removeAvBlock(self.avId, self)
        self.avId = 0
        self.isActive = True
        self.d_setOccupied(0)

    def handleUnexpectedCleanup(self):
        self.notify.warning('KartPad has already been cleaned up')
        from toontown.hood import GSHoodDataAI
        if hasattr(simbase.air, 'hoods') and simbase.air.hoods:
            for hood in simbase.air.hoods:
                if isinstance(hood, GSHoodDataAI.GSHoodDataAI):
                    hood.logPossibleRaceCondition(self)

    def normalExit(self):
        self.d_setMovie(KartGlobals.EXIT_MOVIE)

    def raceExit(self):
        self.cleanupAvatar()
        self.movieFinished()

    def unexpectedExit(self):
        self.cleanupAvatar()
        self.movieFinished()
        self.unexpectedEvent = None
        return

    def d_setOccupied(self, avId):
        self.sendUpdate('setOccupied', [avId])

    def d_setMovie(self, mode):
        self.currentMovie = mode
        self.sendUpdate('setMovie', [mode])


class DistributedViewingBlockAI(DistributedStartingBlockAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedViewingBlockAI')

    def __init__(self, air, kartPad, x, y, z, h, p, r, padLocationId):
        DistributedStartingBlockAI.__init__(self, air, kartPad, x, y, z, h, p, r, padLocationId)

    def delete(self):
        DistributedStartingBlockAI.delete(self)
