from pandac.PandaModules import *
from direct.distributed.ClockDelta import *
from direct.interval.IntervalGlobal import *
from ElevatorConstants import *
from ElevatorUtils import *
import DistributedElevator
from toontown.toonbase import ToontownGlobals
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM
from direct.fsm import State
from toontown.hood import ZoneUtil
from toontown.toonbase import TTLocalizer
from toontown.toontowngui import TeaserPanel

class DistributedElevatorExt(DistributedElevator.DistributedElevator):

    def __init__(self, cr):
        DistributedElevator.DistributedElevator.__init__(self, cr)
        self.nametag = None
        self.currentFloor = -1
        return

    def setupElevator(self):
        if self.isSetup:
            self.elevatorSphereNodePath.removeNode()
        self.leftDoor = self.bldg.leftDoor
        self.rightDoor = self.bldg.rightDoor
        DistributedElevator.DistributedElevator.setupElevator(self)
        self.setupNametag()

    def disable(self):
        self.clearNametag()
        DistributedElevator.DistributedElevator.disable(self)

    def setupNametag(self):
        if self.nametag == None:
            self.nametag = NametagGroup()
            self.nametag.setFont(ToontownGlobals.getBuildingNametagFont())
            if TTLocalizer.BuildingNametagShadow:
                self.nametag.setShadow(*TTLocalizer.BuildingNametagShadow)
            self.nametag.setContents(Nametag.CName)
            self.nametag.setColorCode(NametagGroup.CCSuitBuilding)
            self.nametag.setActive(0)
            self.nametag.setAvatar(self.getElevatorModel())
            name = self.cr.playGame.dnaStore.getTitleFromBlockNumber(self.bldg.block)
            if not name:
                name = TTLocalizer.CogsInc
            else:
                name += TTLocalizer.CogsIncExt
            self.nametag.setName(name)
            self.nametag.manage(base.marginManager)
        return

    def clearNametag(self):
        if self.nametag != None:
            self.nametag.unmanage(base.marginManager)
            self.nametag.setAvatar(NodePath())
            self.nametag = None
        return

    def getBldgDoorOrigin(self):
        return self.bldg.getSuitDoorOrigin()

    def gotBldg(self, buildingList):
        self.bldgRequest = None
        self.bldg = buildingList[0]
        if not self.bldg:
            self.notify.error('setBldgDoId: elevator %d cannot find bldg %d!' % (self.doId, self.bldgDoId))
            return
        if self.getBldgDoorOrigin():
            self.bossLevel = self.bldg.getBossLevel()
            self.setupElevator()
        else:
            self.notify.warning('setBldgDoId: elevator %d cannot find suitDoorOrigin for bldg %d!' % (self.doId, bldgDoId))
        return

    def setFloor(self, floorNumber):
        if self.currentFloor >= 0:
            if self.bldg.floorIndicator[self.currentFloor]:
                self.bldg.floorIndicator[self.currentFloor].setColor(LIGHT_OFF_COLOR)
        if floorNumber >= 0:
            if self.bldg.floorIndicator[floorNumber]:
                self.bldg.floorIndicator[floorNumber].setColor(LIGHT_ON_COLOR)
        self.currentFloor = floorNumber

    def handleEnterSphere(self, collEntry):
        self.notify.debug('Entering Elevator Sphere....')
        if hasattr(localAvatar, 'boardingParty') and localAvatar.boardingParty and localAvatar.boardingParty.getGroupLeader(localAvatar.doId) and localAvatar.boardingParty.getGroupLeader(localAvatar.doId) != localAvatar.doId:
            base.localAvatar.elevatorNotifier.showMe(TTLocalizer.ElevatorGroupMember)
        elif self.allowedToEnter(self.zoneId):
            self.cr.playGame.getPlace().detectedElevatorCollision(self)
        else:
            place = base.cr.playGame.getPlace()
            if place:
                place.fsm.request('stopped')
            self.dialog = TeaserPanel.TeaserPanel(pageName='cogHQ', doneFunc=self.handleOkTeaser)

    def handleEnterElevator(self):
        if hasattr(localAvatar, 'boardingParty') and localAvatar.boardingParty and localAvatar.boardingParty.getGroupLeader(localAvatar.doId):
            if localAvatar.boardingParty.getGroupLeader(localAvatar.doId) == localAvatar.doId:
                localAvatar.boardingParty.handleEnterElevator(self)
        elif self.elevatorTripId and localAvatar.lastElevatorLeft == self.elevatorTripId:
            self.rejectBoard(base.localAvatar.doId, REJECT_SHUFFLE)
        elif base.localAvatar.hp > 0:
            toon = base.localAvatar
            self.sendUpdate('requestBoard', [])
        else:
            self.notify.warning('Tried to board elevator with hp: %d' % base.localAvatar.hp)

    def enterWaitEmpty(self, ts):
        self.elevatorSphereNodePath.unstash()
        self.forceDoorsOpen()
        self.accept(self.uniqueName('enterelevatorSphere'), self.handleEnterSphere)
        self.accept(self.uniqueName('enterElevatorOK'), self.handleEnterElevator)
        DistributedElevator.DistributedElevator.enterWaitEmpty(self, ts)

    def exitWaitEmpty(self):
        self.elevatorSphereNodePath.stash()
        self.ignore(self.uniqueName('enterelevatorSphere'))
        self.ignore(self.uniqueName('enterElevatorOK'))
        DistributedElevator.DistributedElevator.exitWaitEmpty(self)

    def enterWaitCountdown(self, ts):
        DistributedElevator.DistributedElevator.enterWaitCountdown(self, ts)
        self.forceDoorsOpen()
        self.accept(self.uniqueName('enterElevatorOK'), self.handleEnterElevator)
        self.startCountdownClock(self.countdownTime, ts)

    def exitWaitCountdown(self):
        self.ignore(self.uniqueName('enterElevatorOK'))
        DistributedElevator.DistributedElevator.exitWaitCountdown(self)

    def getZoneId(self):
        return self.bldg.interiorZoneId

    def getElevatorModel(self):
        return self.bldg.getSuitElevatorNodePath()
