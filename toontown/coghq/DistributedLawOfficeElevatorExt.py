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

class DistributedLawOfficeElevatorExt(DistributedElevatorExt.DistributedElevatorExt):

    def __init__(self, cr):
        DistributedElevatorExt.DistributedElevatorExt.__init__(self, cr)
        self.type = ELEVATOR_OFFICE

    def generate(self):
        DistributedElevatorExt.DistributedElevatorExt.generate(self)

    def delete(self):
        self.elevatorModel.removeNode()
        del self.elevatorModel
        DistributedElevatorExt.DistributedElevatorExt.delete(self)

    def setEntranceId(self, entranceId):
        self.entranceId = entranceId
        geom = self.cr.playGame.hood.loader.geom
        locator = geom.find('**/elevator_origin_%s' % entranceId)
        if locator:
            self.elevatorModel.setPosHpr(locator, 0, 0, 0, 0, 0, 0)
        else:
            self.notify.error('No origin found for originId: %s' % entranceId)
        entranceId2zoneId = {0: ToontownGlobals.LawbotStageIntA,
         1: ToontownGlobals.LawbotStageIntB,
         2: ToontownGlobals.LawbotStageIntC,
         3: ToontownGlobals.LawbotStageIntD}
        self.intZoneId = entranceId2zoneId[entranceId]
        locator = geom.find('**/elevator_signorigin_%s' % entranceId)
        backgroundGeom = geom.find('**/ElevatorFrameFront_%d' % entranceId)
        backgroundGeom.node().setEffect(DecalEffect.make())
        signText = DirectGui.OnscreenText(text=TextEncoder.upper(TTLocalizer.GlobalStreetNames[self.intZoneId][-1]), font=ToontownGlobals.getSuitFont(), scale=2, fg=(0.87, 0.87, 0.87, 1), mayChange=False, parent=backgroundGeom)
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

    def setLawOfficeInteriorZone(self, zoneId):
        if self.localToonOnBoard:
            hoodId = self.cr.playGame.hood.hoodId
            doneStatus = {'loader': 'cogHQLoader',
             'where': 'stageInterior',
             'how': 'teleportIn',
             'zoneId': zoneId,
             'hoodId': hoodId,
             'stageId': self.intZoneId}
            self.cr.playGame.getPlace().elevator.signalDone(doneStatus)

    def setLawOfficeInteriorZoneForce(self, zoneId):
        place = self.cr.playGame.getPlace()
        if place:
            place.fsm.request('elevator', [self, 1])
            hoodId = self.cr.playGame.hood.hoodId
            doneStatus = {'loader': 'cogHQLoader',
             'where': 'stageInterior',
             'how': 'teleportIn',
             'zoneId': zoneId,
             'hoodId': hoodId,
             'stageId': self.intZoneId}
            if hasattr(place, 'elevator') and place.elevator:
                place.elevator.signalDone(doneStatus)
            else:
                self.notify.warning("setMintInteriorZoneForce: Couldn't find playGame.getPlace().elevator, zoneId: %s" % zoneId)
        else:
            self.notify.warning("setLawOfficeInteriorZoneForce: Couldn't find playGame.getPlace(), zoneId: %s" % zoneId)

    def getDestName(self):
        if self.intZoneId == ToontownGlobals.LawbotStageIntA:
            return TTLocalizer.ElevatorLawBotCourse0
        elif self.intZoneId == ToontownGlobals.LawbotStageIntB:
            return TTLocalizer.ElevatorLawBotCourse1
        elif self.intZoneId == ToontownGlobals.LawbotStageIntC:
            return TTLocalizer.ElevatorLawBotCourse2
        elif self.intZoneId == ToontownGlobals.LawbotStageIntD:
            return TTLocalizer.ElevatorLawBotCourse3
