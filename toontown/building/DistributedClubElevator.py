from pandac.PandaModules import *
from direct.distributed.ClockDelta import *
from direct.interval.IntervalGlobal import *
from toontown.building import ElevatorConstants
from toontown.building import ElevatorUtils
from toontown.building import DistributedElevatorFSM
from toontown.toonbase import ToontownGlobals
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM
from direct.fsm import State
from toontown.hood import ZoneUtil
from toontown.toonbase import TTLocalizer
from direct.fsm.FSM import FSM
from direct.task import Task
from toontown.distributed import DelayDelete
from direct.showbase import PythonUtil

class DistributedClubElevator(DistributedElevatorFSM.DistributedElevatorFSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedClubElevator')
    JumpOutOffsets = ((3, 5, 0),
     (1.5, 4, 0),
     (-1.5, 4, 0),
     (-3, 4, 0))
    defaultTransitions = {'Off': ['Opening', 'Closed'],
     'Opening': ['WaitEmpty',
                 'WaitCountdown',
                 'Opening',
                 'Closing'],
     'WaitEmpty': ['WaitCountdown', 'Closing', 'Off'],
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
        FSM.__init__(self, 'ElevatorClub_%s_FSM' % self.id)
        self.type = ElevatorConstants.ELEVATOR_COUNTRY_CLUB
        self.countdownTime = ElevatorConstants.ElevatorData[self.type]['countdown']
        self.nametag = None
        self.currentFloor = -1
        self.isLocked = 0
        self.isEntering = 0
        self.doorOpeningFlag = 0
        self.doorsNeedToClose = 0
        self.wantState = 0
        self.latch = None
        self.lastState = self.state
        self.kartModelPath = 'phase_12/models/bossbotHQ/Coggolf_cart3.bam'
        self.leftDoor = None
        self.rightDoor = None
        self.__toonTracks = {}
        return

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
        self.loader = self.cr.playGame.hood.loader
        self.golfKart = render.attachNewNode('golfKartNode')
        self.kart = loader.loadModel(self.kartModelPath)
        self.kart.setPos(0, 0, 0)
        self.kart.setScale(1)
        self.kart.reparentTo(self.golfKart)
        self.wheels = self.kart.findAllMatches('**/wheelNode*')
        self.numWheels = self.wheels.getNumPaths()
        self.setPosHpr(0, 0, 0, 0, 0, 0)

    def announceGenerate(self):
        DistributedElevatorFSM.DistributedElevatorFSM.announceGenerate(self)
        if self.latch:
            self.notify.info('Setting latch in announce generate')
            self.setLatch(self.latch)
        angle = self.startingHpr[0]
        angle -= 90
        radAngle = deg2Rad(angle)
        unitVec = Vec3(math.cos(radAngle), math.sin(radAngle), 0)
        unitVec *= 45.0
        self.endPos = self.startingPos + unitVec
        self.endPos.setZ(0.5)
        dist = Vec3(self.endPos - self.enteringPos).length()
        wheelAngle = dist / (4.8 * 1.4 * math.pi) * 360
        self.kartEnterAnimateInterval = Parallel(LerpHprInterval(self.wheels[0], 5.0, Vec3(self.wheels[0].getH(), wheelAngle, self.wheels[0].getR())), LerpHprInterval(self.wheels[1], 5.0, Vec3(self.wheels[1].getH(), wheelAngle, self.wheels[1].getR())), LerpHprInterval(self.wheels[2], 5.0, Vec3(self.wheels[2].getH(), wheelAngle, self.wheels[2].getR())), LerpHprInterval(self.wheels[3], 5.0, Vec3(self.wheels[3].getH(), wheelAngle, self.wheels[3].getR())), name='CogKartAnimate')
        trolleyExitTrack1 = Parallel(LerpPosInterval(self.golfKart, 5.0, self.endPos), self.kartEnterAnimateInterval, name='CogKartExitTrack')
        self.trolleyExitTrack = Sequence(trolleyExitTrack1)
        self.trolleyEnterTrack = Sequence(LerpPosInterval(self.golfKart, 5.0, self.startingPos, startPos=self.enteringPos))
        self.closeDoors = Sequence(self.trolleyExitTrack, Func(self.onDoorCloseFinish))
        self.openDoors = Sequence(self.trolleyEnterTrack)
        self.setPos(0, 0, 0)

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
        self.latchRequest = None
        if hasattr(self, 'cr'):
            marker = self.cr.doId2do.get(self.latch)
            if marker:
                self.getElevatorModel().reparentTo(marker)
                return
            taskMgr.doMethodLater(10.0, self._repart2Marker, 'elevatorfloor-markerReparent')
            self.notify.warning('Using backup, do method later version of latch')
        return

    def _repart2Marker(self, taskFoolio = 0):
        if hasattr(self, 'cr') and self.cr:
            marker = self.cr.doId2do.get(self.latch)
            if marker:
                self.getElevatorModel().reparentTo(marker)
            else:
                self.notify.error('could not find latch even in defered try')

    def setPos(self, x, y, z):
        self.getElevatorModel().setPos(x, y, z)

    def setH(self, H):
        self.getElevatorModel().setH(H)

    def delete(self):
        self.request('Off')
        DistributedElevatorFSM.DistributedElevatorFSM.delete(self)
        self.getElevatorModel().removeNode()
        del self.golfKart
        self.ignore('LawOffice_Spec_Loaded')
        self.ignoreAll()

    def disable(self):
        self.request('Off')
        self.clearToonTracks()
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
        self.setupElevatorKart()
        return

    def setupElevatorKart(self):
        collisionRadius = ElevatorConstants.ElevatorData[self.type]['collRadius']
        self.elevatorSphere = CollisionSphere(0, 0, 0, collisionRadius)
        self.elevatorSphere.setTangible(1)
        self.elevatorSphereNode = CollisionNode(self.uniqueName('elevatorSphere'))
        self.elevatorSphereNode.setIntoCollideMask(ToontownGlobals.WallBitmask)
        self.elevatorSphereNode.addSolid(self.elevatorSphere)
        self.elevatorSphereNodePath = self.getElevatorModel().attachNewNode(self.elevatorSphereNode)
        self.elevatorSphereNodePath.hide()
        self.elevatorSphereNodePath.reparentTo(self.getElevatorModel())
        self.elevatorSphereNodePath.stash()
        self.boardedAvIds = {}
        self.finishSetup()

    def getElevatorModel(self):
        return self.elevatorModel

    def kickEveryoneOut(self):
        bailFlag = 0
        for avId, slot in self.boardedAvIds.items():
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
        pass

    def forceDoorsClosed(self):
        pass

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

    def getElevatorModel(self):
        return self.golfKart

    def setPosHpr(self, x, y, z, h, p, r):
        self.startingPos = Vec3(x, y, z)
        self.enteringPos = Vec3(x, y, z - 10)
        self.startingHpr = Vec3(h, 0, 0)
        self.golfKart.setPosHpr(x, y, z, h, 0, 0)

    def fillSlot(self, index, avId):
        self.notify.debug('%s.fillSlot(%s, %s, ...)' % (self.doId, index, avId))
        request = self.toonRequests.get(index)
        if request:
            self.cr.relatedObjectMgr.abortRequest(request)
            del self.toonRequests[index]
        if avId == 0:
            pass
        elif not self.cr.doId2do.has_key(avId):
            func = PythonUtil.Functor(self.gotToon, index, avId)
            self.toonRequests[index] = self.cr.relatedObjectMgr.requestObjects([avId], allCallback=func)
        elif not self.isSetup:
            self.deferredSlots.append((index, avId))
        else:
            if avId == base.localAvatar.getDoId():
                self.localToonOnBoard = 1
                elevator = self.getPlaceElevator()
                elevator.fsm.request('boarding', [self.getElevatorModel()])
                elevator.fsm.request('boarded')
            toon = self.cr.doId2do[avId]
            toon.stopSmooth()
            toon.wrtReparentTo(self.golfKart)
            sitStartDuration = toon.getDuration('sit-start')
            jumpTrack = self.generateToonJumpTrack(toon, index)
            track = Sequence(jumpTrack, Func(toon.setAnimState, 'Sit', 1.0), Func(self.clearToonTrack, avId), name=toon.uniqueName('fillElevator'), autoPause=1)
            track.delayDelete = DelayDelete.DelayDelete(toon, 'fillSlot')
            self.storeToonTrack(avId, track)
            track.start()
            self.boardedAvIds[avId] = None
        return

    def generateToonJumpTrack(self, av, seatIndex):
        av.pose('sit', 47)
        hipOffset = av.getHipsParts()[2].getPos(av)

        def getToonJumpTrack(av, seatIndex):

            def getJumpDest(av = av, node = self.golfKart):
                dest = Point3(0, 0, 0)
                if hasattr(self, 'golfKart') and self.golfKart:
                    dest = Vec3(self.golfKart.getPos(av.getParent()))
                    seatNode = self.golfKart.find('**/seat' + str(seatIndex + 1))
                    dest += seatNode.getPos(self.golfKart)
                    dna = av.getStyle()
                    dest -= hipOffset
                    if seatIndex < 2:
                        dest.setY(dest.getY() + 2 * hipOffset.getY())
                    dest.setZ(dest.getZ() + 0.1)
                else:
                    self.notify.warning('getJumpDestinvalid golfKart, returning (0,0,0)')
                return dest

            def getJumpHpr(av = av, node = self.golfKart):
                hpr = Point3(0, 0, 0)
                if hasattr(self, 'golfKart') and self.golfKart:
                    hpr = self.golfKart.getHpr(av.getParent())
                    if seatIndex < 2:
                        hpr.setX(hpr.getX() + 180)
                    else:
                        hpr.setX(hpr.getX())
                    angle = PythonUtil.fitDestAngle2Src(av.getH(), hpr.getX())
                    hpr.setX(angle)
                else:
                    self.notify.warning('getJumpHpr invalid golfKart, returning (0,0,0)')
                return hpr

            toonJumpTrack = Parallel(ActorInterval(av, 'jump'), Sequence(Wait(0.43), Parallel(LerpHprInterval(av, hpr=getJumpHpr, duration=0.9), ProjectileInterval(av, endPos=getJumpDest, duration=0.9))))
            return toonJumpTrack

        def getToonSitTrack(av):
            toonSitTrack = Sequence(ActorInterval(av, 'sit-start'), Func(av.loop, 'sit'))
            return toonSitTrack

        toonJumpTrack = getToonJumpTrack(av, seatIndex)
        toonSitTrack = getToonSitTrack(av)
        jumpTrack = Sequence(Parallel(toonJumpTrack, Sequence(Wait(1), toonSitTrack)), Func(av.wrtReparentTo, self.golfKart))
        return jumpTrack

    def emptySlot(self, index, avId, bailFlag, timestamp):
        if avId == 0:
            pass
        elif not self.isSetup:
            newSlots = []
            for slot in self.deferredSlots:
                if slot[0] != index:
                    newSlots.append(slot)

            self.deferredSlots = newSlots
        elif self.cr.doId2do.has_key(avId):
            if bailFlag == 1 and hasattr(self, 'clockNode'):
                if timestamp < self.countdownTime and timestamp >= 0:
                    self.countdown(self.countdownTime - timestamp)
                else:
                    self.countdown(self.countdownTime)
            toon = self.cr.doId2do[avId]
            toon.stopSmooth()
            sitStartDuration = toon.getDuration('sit-start')
            jumpOutTrack = self.generateToonReverseJumpTrack(toon, index)
            track = Sequence(jumpOutTrack, Func(self.clearToonTrack, avId), Func(self.notifyToonOffElevator, toon), name=toon.uniqueName('emptyElevator'), autoPause=1)
            track.delayDelete = DelayDelete.DelayDelete(toon, 'ClubElevator.emptySlot')
            self.storeToonTrack(avId, track)
            track.start()
            if avId == base.localAvatar.getDoId():
                messenger.send('exitElevator')
            if avId in self.boardedAvIds:
                del self.boardedAvIds[avId]
        else:
            self.notify.warning('toon: ' + str(avId) + " doesn't exist, and" + ' cannot exit the elevator!')

    def generateToonReverseJumpTrack(self, av, seatIndex):
        self.notify.debug('av.getH() = %s' % av.getH())

        def getToonJumpTrack(av, destNode):

            def getJumpDest(av = av, node = destNode):
                dest = node.getPos(av.getParent())
                dest += Vec3(*self.JumpOutOffsets[seatIndex])
                return dest

            def getJumpHpr(av = av, node = destNode):
                hpr = node.getHpr(av.getParent())
                hpr.setX(hpr.getX() + 180)
                angle = PythonUtil.fitDestAngle2Src(av.getH(), hpr.getX())
                hpr.setX(angle)
                return hpr

            toonJumpTrack = Parallel(ActorInterval(av, 'jump'), Sequence(Wait(0.1), Parallel(ProjectileInterval(av, endPos=getJumpDest, duration=0.9))))
            return toonJumpTrack

        toonJumpTrack = getToonJumpTrack(av, self.golfKart)
        jumpTrack = Sequence(toonJumpTrack, Func(av.loop, 'neutral'), Func(av.wrtReparentTo, render))
        return jumpTrack

    def startCountdownClock(self, countdownTime, ts):
        DistributedElevatorFSM.DistributedElevatorFSM.startCountdownClock(self, countdownTime, ts)
        self.clock.setH(self.clock.getH() + 180)

    def storeToonTrack(self, avId, track):
        self.clearToonTrack(avId)
        self.__toonTracks[avId] = track

    def clearToonTrack(self, avId):
        oldTrack = self.__toonTracks.get(avId)
        if oldTrack:
            oldTrack.pause()
            if self.__toonTracks.get(avId):
                DelayDelete.cleanupDelayDeletes(self.__toonTracks[avId])
                del self.__toonTracks[avId]

    def clearToonTracks(self):
        keyList = []
        for key in self.__toonTracks:
            keyList.append(key)

        for key in keyList:
            if self.__toonTracks.has_key(key):
                self.clearToonTrack(key)
