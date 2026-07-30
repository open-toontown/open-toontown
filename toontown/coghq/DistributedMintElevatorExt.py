from direct.distributed.ClockDelta import *
from direct.interval.IntervalGlobal import *
from toontown.building.ElevatorConstants import *
from toontown.building.ElevatorUtils import *
from toontown.building import DistributedElevatorExt
from toontown.building import DistributedElevator
from toontown.toonbase import ToontownGlobals
from direct.fsm import ClassicFSM
from direct.fsm import State
from direct.gui import DirectGui
from toontown.hood import ZoneUtil
from toontown.toonbase import TTLocalizer
from toontown.toontowngui import TTDialog
from . import CogDisguiseGlobals

class DistributedMintElevatorExt(DistributedElevatorExt.DistributedElevatorExt):

    def __init__(self, cr):
        DistributedElevatorExt.DistributedElevatorExt.__init__(self, cr)
        self.type = ELEVATOR_MINT
        self.countdownTime = ElevatorData[self.type]['countdown']

    def generate(self):
        DistributedElevatorExt.DistributedElevatorExt.generate(self)

    def delete(self):
        self.elevatorModel.removeNode()
        del self.elevatorModel
        DistributedElevatorExt.DistributedElevatorExt.delete(self)

    def setMintId(self, mintId):
        self.mintId = mintId
        mintId2originId = {ToontownGlobals.CashbotMintIntA: 1,
         ToontownGlobals.CashbotMintIntB: 2,
         ToontownGlobals.CashbotMintIntC: 0}
        originId = mintId2originId[self.mintId]
        geom = self.cr.playGame.hood.loader.geom
        locator = geom.find('**/elevator_origin_%s' % originId)
        if locator:
            self.elevatorModel.setPosHpr(locator, 0, 0, 0, 0, 0, 0)
        else:
            self.notify.error('No origin found for originId: %s' % originId)
        locator = geom.find('**/elevator_signorigin_%s' % originId)
        backgroundGeom = geom.find('**/ElevatorFrameFront_%d' % originId)
        backgroundGeom.node().setEffect(DecalEffect.make())
        signText = DirectGui.OnscreenText(text=TextEncoder.upper(TTLocalizer.GlobalStreetNames[mintId][-1]), font=ToontownGlobals.getSuitFont(), scale=TTLocalizer.DMEEsignText, fg=(0.87, 0.87, 0.87, 1), mayChange=False, parent=backgroundGeom)
        signText.setPosHpr(locator, 0, 0, 0, 0, 0, 0)
        signText.setDepthWrite(0)

    def setupElevator(self):
        self.elevatorModel = loader.loadModel('phase_10/models/cogHQ/mintElevator')
        self.elevatorModel.reparentTo(render)
        self.leftDoor = self.elevatorModel.find('**/left_door')
        self.rightDoor = self.elevatorModel.find('**/right_door')
        DistributedElevator.DistributedElevator.setupElevator(self)
        self.elevatorSphereNodePath.setY(-1.42)

    def getElevatorModel(self):
        return self.elevatorModel

    def setBldgDoId(self, bldgDoId):
        self.bldg = None
        self.setupElevator()
        return

    def getZoneId(self):
        return 0

    def __doorsClosed(self, zoneId):
        pass

    def setMintInteriorZone(self, zoneId):
        if self.localToonOnBoard:
            hoodId = self.cr.playGame.hood.hoodId
            mintId = self.mintId
            if bboard.has('mintIdOverride'):
                mintId = bboard.get('mintIdOverride')
            doneStatus = {'loader': 'cogHQLoader',
             'where': 'mintInterior',
             'how': 'teleportIn',
             'zoneId': zoneId,
             'mintId': self.mintId,
             'hoodId': hoodId}
            self.cr.playGame.getPlace().elevator.signalDone(doneStatus)

    def setMintInteriorZoneForce(self, zoneId):
        place = self.cr.playGame.getPlace()
        if place:
            place.fsm.request('elevator', [self, 1])
            hoodId = self.cr.playGame.hood.hoodId
            mintId = self.mintId
            if bboard.has('mintIdOverride'):
                mintId = bboard.get('mintIdOverride')
            doneStatus = {'loader': 'cogHQLoader',
             'where': 'mintInterior',
             'how': 'teleportIn',
             'zoneId': zoneId,
             'mintId': self.mintId,
             'hoodId': hoodId}
            if hasattr(place, 'elevator') and place.elevator:
                place.elevator.signalDone(doneStatus)
            else:
                self.notify.warning("setMintInteriorZoneForce: Couldn't find playGame.getPlace().elevator, zoneId: %s" % zoneId)
        else:
            self.notify.warning("setMintInteriorZoneForce: Couldn't find playGame.getPlace(), zoneId: %s" % zoneId)

    def rejectBoard(self, avId, reason = 0):
        DistributedElevatorExt.DistributedElevatorExt.rejectBoard(self, avId, reason)

    def __handleRejectAck(self):
        doneStatus = self.rejectDialog.doneStatus
        if doneStatus != 'ok':
            self.notify.error('Unrecognized doneStatus: ' + str(doneStatus))
        doneStatus = {'where': 'reject'}
        self.cr.playGame.getPlace().elevator.signalDone(doneStatus)
        self.rejectDialog.cleanup()
        del self.rejectDialog

    def getDestName(self):
        if self.mintId == ToontownGlobals.CashbotMintIntA:
            return TTLocalizer.ElevatorCashBotMint0
        elif self.mintId == ToontownGlobals.CashbotMintIntB:
            return TTLocalizer.ElevatorCashBotMint1
        elif self.mintId == ToontownGlobals.CashbotMintIntC:
            return TTLocalizer.ElevatorCashBotMint2
