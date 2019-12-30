from pandac.PandaModules import *
from direct.distributed.ClockDelta import *
from direct.interval.IntervalGlobal import *
from .ElevatorConstants import *
from .ElevatorUtils import *
from . import DistributedElevatorFSM
from toontown.toonbase import ToontownGlobals
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM
from direct.fsm import State
from toontown.hood import ZoneUtil
from toontown.toonbase import TTLocalizer
from direct.fsm.FSM import FSM
from direct.task import Task

class DistributedElevatorFloor(DistributedElevatorFSM.DistributedElevatorFSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedElevatorFloor')
    defaultTransitions = {'Off': ['Opening', 'Closed'],
     'Opening': ['WaitEmpty',
                 'WaitCountdown',
                 'Opening',
                 'Closing'],
     'WaitEmpty': ['WaitCountdown', 'Closing'],
     'WaitCountdown': ['WaitEmpty',
                       'AllAboard',
                       'Closing',
                       'WaitCountdown'],
     'AllAboard': ['WaitEmpty', 'Closing'],
     'Closing': ['Closed',
                 'WaitEmpty',
                 'Closing',
                 'Opening'],
     'Closed': ['Opening']}
    id = 0

    def __init__(self, cr):
        DistributedElevatorFSM.DistributedElevatorFSM.__init__(self, cr)
        FSM.__init__(self, 'ElevatorFloor_%s_FSM' % self.id)
        self.type = ELEVATOR_STAGE
        self.countdownTime = ElevatorData[self.type]['countdown']
        self.nametag = None
        self.currentFloor = -1
        self.isLocked = 0
        self.isEntering = 0
        self.doorOpeningFlag = 0
        self.doorsNeedToClose = 0
        self.wantState = 0
        self.latch = None
        self.lastState = self.state
        return

    def setupElevator2(self):
        self.elevatorModel = loader.loadModel('phase_4/models/modules/elevator')
        self.elevatorModel.reparentTo(hidden)
        self.elevatorModel.setScale(1.05)
        self.leftDoor = self.elevatorModel.find('**/left-door')
        self.rightDoor = self.elevatorModel.find('**/right-door')
        self.elevatorModel.find('**/light_panel').removeNode()
        self.elevatorModel.find('**/light_panel_frame').removeNode()
        if self.isSetup:
            self.elevatorSphereNodePath.removeNode()
        DistributedElevatorFSM.DistributedElevatorFSM.setupElevator(self)

    def setupElevator(self):
        self.elevatorModel = loader.loadModel('phase_11/models/lawbotHQ/LB_ElevatorScaled')
        if not self.elevatorModel:
            self.notify.error('No Elevator Model in DistributedElevatorFloor.setupElevator. Please inform JML. Fool!')
        self.leftDoor = self.elevatorModel.find('**/left-door')
        if self.leftDoor.isEmpty():
            self.leftDoor = self.elevatorModel.find('**/left_door')
        self.rightDoor = self.elevatorModel.find('**/right-door')
        if self.rightDoor.isEmpty():
            self.rightDoor = self.elevatorModel.find('**/right_door')
        DistributedElevatorFSM.DistributedElevatorFSM.setupElevator(self)

    def generate(self):
        DistributedElevatorFSM.DistributedElevatorFSM.generate(self)

    def announceGenerate(self):
        DistributedElevatorFSM.DistributedElevatorFSM.announceGenerate(self)
        if self.latch:
            self.notify.info('Setting latch in announce generate')
            self.setLatch(self.latch)

    def __placeElevator(self):
        self.notify.debug('PLACING ELEVATOR FOOL!!')
        if self.isEntering:
            elevatorNode = render.find('**/elevator_origin')
            if not elevatorNode.isEmpty():
                self.elevatorModel.setPos(0, 0, 0)
                self.elevatorModel.reparentTo(elevatorNode)
            else:
                self.notify.debug('NO NODE elevator_origin!!')
        else:
            elevatorNode = render.find('**/SlidingDoor')
            if not elevatorNode.isEmpty():
                self.elevatorModel.setPos(0, 10, -15)
                self.elevatorModel.setH(180)
                self.elevatorModel.reparentTo(elevatorNode)
            else:
                self.notify.debug('NO NODE SlidingDoor!!')

    def setLatch(self, markerId):
        self.notify.info('Setting latch')
        marker = self.cr.doId2do.get(markerId)
        self.latchRequest = self.cr.relatedObjectMgr.requestObjects([markerId], allCallback=self.set2Latch, timeout=5)
        self.latch = markerId

    def set2Latch(self, taskMgrFooler = None):
        if hasattr(self, 'cr'):
            marker = self.cr.doId2do.get(self.latch)
            if marker:
                self.elevatorModel.reparentTo(marker)
                return
            taskMgr.doMethodLater(10.0, self._repart2Marker, 'elevatorfloor-markerReparent')
            self.notify.warning('Using backup, do method later version of latch')

    def _repart2Marker(self, taskFoolio = 0):
        if hasattr(self, 'cr'):
            marker = self.cr.doId2do.get(self.latch)
            if marker:
                self.elevatorModel.reparentTo(marker)
            else:
                self.notify.error('could not find latch even in defered try')

    def setPos(self, x, y, z):
        self.elevatorModel.setPos(x, y, z)

    def setH(self, H):
        self.elevatorModel.setH(H)

    def delete(self):
        DistributedElevatorFSM.DistributedElevatorFSM.delete(self)
        self.elevatorModel.removeNode()
        del self.elevatorModel
        self.ignore('LawOffice_Spec_Loaded')
        self.ignoreAll()

    def disable(self):
        DistributedElevatorFSM.DistributedElevatorFSM.disable(self)

    def setEntranceId(self, entranceId):
        self.entranceId = entranceId
        if self.entranceId == 0:
            self.elevatorModel.setPosHpr(62.74, -85.31, 0.0, 2.0, 0.0, 0.0)
        elif self.entranceId == 1:
            self.elevatorModel.setPosHpr(-162.25, 26.43, 0.0, 269.0, 0.0, 0.0)
        else:
            self.notify.error('Invalid entranceId: %s' % entranceId)

    def gotBldg(self, buildingList):
        pass

    def setFloor(self, floorNumber):
        if self.currentFloor >= 0:
            if self.bldg.floorIndicator[self.currentFloor]:
                self.bldg.floorIndicator[self.currentFloor].setColor(LIGHT_OFF_COLOR)
        if floorNumber >= 0:
            if self.bldg.floorIndicator[floorNumber]:
                self.bldg.floorIndicator[floorNumber].setColor(LIGHT_ON_COLOR)
        self.currentFloor = floorNumber

    def handleEnterSphere(self, collEntry):
        self.cr.playGame.getPlace().detectedElevatorCollision(self)

    def handleEnterElevator(self):
        if base.localAvatar.hp > 0:
            toon = base.localAvatar
            self.sendUpdate('requestBoard', [])
        else:
            self.notify.warning('Tried to board elevator with hp: %d' % base.localAvatar.hp)

    def enterWaitEmpty(self, ts):
        self.lastState = self.state
        self.elevatorSphereNodePath.unstash()
        self.forceDoorsOpen()
        self.accept(self.uniqueName('enterelevatorSphere'), self.handleEnterSphere)
        self.accept(self.uniqueName('enterElevatorOK'), self.handleEnterElevator)
        DistributedElevatorFSM.DistributedElevatorFSM.enterWaitEmpty(self, ts)

    def exitWaitEmpty(self):
        self.lastState = self.state
        self.elevatorSphereNodePath.stash()
        self.ignore(self.uniqueName('enterelevatorSphere'))
        self.ignore(self.uniqueName('enterElevatorOK'))
        DistributedElevatorFSM.DistributedElevatorFSM.exitWaitEmpty(self)

    def enterWaitCountdown(self, ts):
        self.lastState = self.state
        DistributedElevatorFSM.DistributedElevatorFSM.enterWaitCountdown(self, ts)
        self.forceDoorsOpen()
        self.accept(self.uniqueName('enterElevatorOK'), self.handleEnterElevator)
        self.startCountdownClock(self.countdownTime, ts)

    def exitWaitCountdown(self):
        self.lastState = self.state
        self.ignore(self.uniqueName('enterElevatorOK'))
        DistributedElevatorFSM.DistributedElevatorFSM.exitWaitCountdown(self)

    def enterClosing(self, ts):
        self.lastState = self.state
        taskMgr.doMethodLater(1.0, self._delayIris, 'delayedIris')
        DistributedElevatorFSM.DistributedElevatorFSM.enterClosing(self, ts)

    def _delayIris(self, tskfooler = 0):
        base.transitions.irisOut(1.0)
        base.localAvatar.pauseGlitchKiller()
        return Task.done

    def kickToonsOut(self):
        if not self.localToonOnBoard:
            zoneId = self.cr.playGame.hood.hoodId
            self.cr.playGame.getPlace().fsm.request('teleportOut', [{'loader': ZoneUtil.getLoaderName(zoneId),
              'where': ZoneUtil.getToonWhereName(zoneId),
              'how': 'teleportIn',
              'hoodId': zoneId,
              'zoneId': zoneId,
              'shardId': None,
              'avId': -1}])
        return

    def exitClosing(self):
        self.lastState = self.state
        DistributedElevatorFSM.DistributedElevatorFSM.exitClosing(self)

    def enterClosed(self, ts):
        self.lastState = self.state
        self.forceDoorsClosed()
        self.__doorsClosed(self.getZoneId())

    def exitClosed(self):
        self.lastState = self.state
        DistributedElevatorFSM.DistributedElevatorFSM.exitClosed(self)

    def enterOff(self):
        self.lastState = self.state
        if self.wantState == 'closed':
            self.demand('Closing')
        elif self.wantState == 'waitEmpty':
            self.demand('WaitEmpty')
        DistributedElevatorFSM.DistributedElevatorFSM.enterOff(self)

    def exitOff(self):
        self.lastState = self.state
        DistributedElevatorFSM.DistributedElevatorFSM.exitOff(self)

    def enterOpening(self, ts):
        self.lastState = self.state
        DistributedElevatorFSM.DistributedElevatorFSM.enterOpening(self, ts)

    def exitOpening(self):
        DistributedElevatorFSM.DistributedElevatorFSM.exitOpening(self)
        self.kickEveryoneOut()

    def getZoneId(self):
        return 0

    def setBldgDoId(self, bldgDoId):
        self.bldg = None
        self.setupElevator()
        return

    def getElevatorModel(self):
        return self.elevatorModel

    def kickEveryoneOut(self):
        bailFlag = 0
        for avId, slot in list(self.boardedAvIds.items()):
            self.emptySlot(slot, avId, bailFlag, globalClockDelta.getRealNetworkTime())
            if avId == base.localAvatar.doId:
                pass

    def __doorsClosed(self, zoneId):
        pass

    def onDoorCloseFinish(self):
        pass

    def setLocked(self, locked):
        self.isLocked = locked
        if locked:
            if self.state == 'WaitEmpty':
                self.request('Closing')
            if self.countFullSeats() == 0:
                self.wantState = 'closed'
            else:
                self.wantState = 'opening'
        else:
            self.wantState = 'waitEmpty'
            if self.state == 'Closed':
                self.request('Opening')

    def getLocked(self):
        return self.isLocked

    def setEntering(self, entering):
        self.isEntering = entering

    def getEntering(self):
        return self.isEntering

    def forceDoorsOpen(self):
        openDoors(self.leftDoor, self.rightDoor)

    def forceDoorsClosed(self):
        if self.openDoors.isPlaying():
            self.doorsNeedToClose = 1
        else:
            self.closeDoors.finish()
            closeDoors(self.leftDoor, self.rightDoor)

    def enterOff(self):
        self.lastState = self.state

    def exitOff(self):
        pass

    def setLawOfficeInteriorZone(self, zoneId):
        if self.localToonOnBoard:
            hoodId = self.cr.playGame.hood.hoodId
            doneStatus = {'loader': 'cogHQLoader',
             'where': 'factoryInterior',
             'how': 'teleportIn',
             'zoneId': zoneId,
             'hoodId': hoodId}
            self.cr.playGame.getPlace().elevator.signalDone(doneStatus)
