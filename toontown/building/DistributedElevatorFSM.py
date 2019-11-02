from pandac.PandaModules import *
from direct.distributed.ClockDelta import *
from direct.interval.IntervalGlobal import *
from ElevatorConstants import *
from ElevatorUtils import *
from direct.showbase import PythonUtil
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM
from direct.distributed import DistributedObject
from direct.fsm import State
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals
from direct.task.Task import Task
from toontown.hood import ZoneUtil
from direct.fsm.FSM import FSM

class DistributedElevatorFSM(DistributedObject.DistributedObject, FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedElevator')
    defaultTransitions = {'Off': ['Opening', 'Closed', 'Off'],
     'Opening': ['WaitEmpty',
                 'WaitCountdown',
                 'Opening',
                 'Closing'],
     'WaitEmpty': ['WaitCountdown', 'Closing', 'Off'],
     'WaitCountdown': ['WaitEmpty', 'AllAboard', 'Closing'],
     'AllAboard': ['WaitEmpty', 'Closing'],
     'Closing': ['Closed',
                 'WaitEmpty',
                 'Closing',
                 'Opening'],
     'Closed': ['Opening']}
    id = 0

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        FSM.__init__(self, 'Elevator_%s_FSM' % self.id)
        self.bldgRequest = None
        self.toonRequests = {}
        self.deferredSlots = []
        self.localToonOnBoard = 0
        self.boardedAvIds = {}
        self.openSfx = base.loadSfx('phase_5/audio/sfx/elevator_door_open.mp3')
        self.finalOpenSfx = None
        self.closeSfx = base.loadSfx('phase_5/audio/sfx/elevator_door_close.mp3')
        self.elevatorFSM = None
        self.finalCloseSfx = None
        self.elevatorPoints = ElevatorPoints
        self.type = ELEVATOR_NORMAL
        self.countdownTime = ElevatorData[self.type]['countdown']
        self.isSetup = 0
        self.__preSetupState = None
        self.bigElevator = 0
        self.offTrack = [None,
         None,
         None,
         None]
        self.boardingParty = None
        return

    def generate(self):
        DistributedObject.DistributedObject.generate(self)

    def setBoardingParty(self, party):
        self.boardingParty = party

    def setupElevator(self):
        collisionRadius = ElevatorData[self.type]['collRadius']
        self.elevatorSphere = CollisionSphere(0, 5, 0, collisionRadius)
        self.elevatorSphere.setTangible(0)
        self.elevatorSphereNode = CollisionNode(self.uniqueName('elevatorSphere'))
        self.elevatorSphereNode.setIntoCollideMask(ToontownGlobals.WallBitmask)
        self.elevatorSphereNode.addSolid(self.elevatorSphere)
        self.elevatorSphereNodePath = self.getElevatorModel().attachNewNode(self.elevatorSphereNode)
        self.elevatorSphereNodePath.hide()
        self.elevatorSphereNodePath.reparentTo(self.getElevatorModel())
        self.elevatorSphereNodePath.stash()
        self.boardedAvIds = {}
        self.openDoors = getOpenInterval(self, self.leftDoor, self.rightDoor, self.openSfx, self.finalOpenSfx, self.type)
        self.closeDoors = getCloseInterval(self, self.leftDoor, self.rightDoor, self.closeSfx, self.finalCloseSfx, self.type)
        self.openDoors = Sequence(self.openDoors, Func(self.onDoorOpenFinish))
        self.closeDoors = Sequence(self.closeDoors, Func(self.onDoorCloseFinish))
        self.finishSetup()

    def finishSetup(self):
        self.isSetup = 1
        if self.__preSetupState:
            self.request(self.__preSetupState, 0)
            self.__preSetupState = None
        for slot in self.deferredSlots:
            self.fillSlot(*slot)

        self.deferredSlots = []
        return

    def disable(self):
        for track in self.offTrack:
            if track:
                if track.isPlaying():
                    track.pause()
                    track = None

        if self.bldgRequest:
            self.cr.relatedObjectMgr.abortRequest(self.bldgRequest)
            self.bldgRequest = None
        for request in self.toonRequests.values():
            self.cr.relatedObjectMgr.abortRequest(request)

        self.toonRequests = {}
        if hasattr(self, 'openDoors'):
            self.openDoors.pause()
        if hasattr(self, 'closeDoors'):
            self.closeDoors.pause()
        self.request('off')
        DistributedObject.DistributedObject.disable(self)
        return

    def delete(self):
        for track in self.offTrack:
            if track:
                if track.isPlaying():
                    track.pause()
                    track = None

        self.ignoreAll()
        if self.isSetup:
            self.elevatorSphereNodePath.removeNode()
            del self.elevatorSphereNodePath
            del self.elevatorSphereNode
            del self.elevatorSphere
            del self.bldg
            del self.leftDoor
            del self.rightDoor
            del self.openDoors
            del self.closeDoors
        del self.openSfx
        del self.closeSfx
        self.isSetup = 0
        DistributedObject.DistributedObject.delete(self)
        return

    def setBldgDoId(self, bldgDoId):
        self.bldgDoId = bldgDoId
        self.bldgRequest = self.cr.relatedObjectMgr.requestObjects([bldgDoId], allCallback=self.gotBldg, timeout=2)

    def gotBldg(self, buildingList):
        self.bldgRequest = None
        self.bldg = buildingList[0]
        if not self.bldg:
            self.notify.error('setBldgDoId: elevator %d cannot find bldg %d!' % (self.doId, self.bldgDoId))
            return
        self.setupElevator()
        return

    def gotToon(self, index, avId, toonList):
        request = self.toonRequests.get(index)
        if request:
            del self.toonRequests[index]
            self.fillSlot(index, avId)
        else:
            self.notify.error('gotToon: already had got toon in slot %s.' % index)

    def setState(self, state, timestamp):
        if self.isSetup:
            self.request(state, globalClockDelta.localElapsedTime(timestamp))
        else:
            self.__preSetupState = state

    def fillSlot0(self, avId):
        self.fillSlot(0, avId)

    def fillSlot1(self, avId):
        self.fillSlot(1, avId)

    def fillSlot2(self, avId):
        self.fillSlot(2, avId)

    def fillSlot3(self, avId):
        self.fillSlot(3, avId)

    def fillSlot4(self, avId):
        self.fillSlot(4, avId)

    def fillSlot5(self, avId):
        self.fillSlot(5, avId)

    def fillSlot6(self, avId):
        self.fillSlot(6, avId)

    def fillSlot7(self, avId):
        self.fillSlot(7, avId)

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
            toon.setZ(self.getElevatorModel(), self.getScaledPoint(index)[2])
            toon.setShadowHeight(0)
            if toon.isDisguised:
                toon.suit.loop('walk')
                animFunc = Func(toon.suit.loop, 'neutral')
            else:
                toon.setAnimState('run', 1.0)
                animFunc = Func(toon.setAnimState, 'neutral', 1.0)
            toon.headsUp(self.getElevatorModel(), apply(Point3, self.getScaledPoint(index)))
            track = Sequence(LerpPosInterval(toon, TOON_BOARD_ELEVATOR_TIME * 0.75, apply(Point3, self.getScaledPoint(index)), other=self.getElevatorModel()), LerpHprInterval(toon, TOON_BOARD_ELEVATOR_TIME * 0.25, Point3(180, 0, 0), other=self.getElevatorModel()), animFunc, name=toon.uniqueName('fillElevator'), autoPause=1)
            track.start()
            self.boardedAvIds[avId] = index

    def emptySlot0(self, avId, bailFlag, timestamp):
        self.emptySlot(0, avId, bailFlag, timestamp)

    def emptySlot1(self, avId, bailFlag, timestamp):
        self.emptySlot(1, avId, bailFlag, timestamp)

    def emptySlot2(self, avId, bailFlag, timestamp):
        self.emptySlot(2, avId, bailFlag, timestamp)

    def emptySlot3(self, avId, bailFlag, timestamp):
        self.emptySlot(3, avId, bailFlag, timestamp)

    def emptySlot4(self, avId, bailFlag, timestamp):
        self.emptySlot(4, avId, bailFlag, timestamp)

    def emptySlot5(self, avId, bailFlag, timestamp):
        self.emptySlot(5, avId, bailFlag, timestamp)

    def emptySlot6(self, avId, bailFlag, timestamp):
        self.emptySlot(6, avId, bailFlag, timestamp)

    def emptySlot7(self, avId, bailFlag, timestamp):
        self.emptySlot(7, avId, bailFlag, timestamp)

    def notifyToonOffElevator(self, toon):
        if self.cr:
            toon.setAnimState('neutral', 1.0)
            if toon == base.localAvatar:
                print 'moving the local toon off the elevator'
                doneStatus = {'where': 'exit'}
                elevator = self.getPlaceElevator()
                elevator.signalDone(doneStatus)
                self.localToonOnBoard = 0
            else:
                toon.startSmooth()
            return

    def emptySlot(self, index, avId, bailFlag, timestamp):
        print 'Emptying slot: %d for %d' % (index, avId)
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
            if toon.isDisguised:
                toon.suit.loop('walk')
                animFunc = Func(toon.suit.loop, 'neutral')
            else:
                toon.setAnimState('run', 1.0)
                animFunc = Func(toon.setAnimState, 'neutral', 1.0)
            if self.offTrack[index]:
                if self.offTrack[index].isPlaying():
                    self.offTrack[index].finish()
                    self.offTrack[index] = None
            self.offTrack[index] = Sequence(LerpPosInterval(toon, TOON_EXIT_ELEVATOR_TIME, Point3(0, -ElevatorData[self.type]['collRadius'], 0), startPos=apply(Point3, self.getScaledPoint(index)), other=self.getElevatorModel()), animFunc, Func(self.notifyToonOffElevator, toon), name=toon.uniqueName('emptyElevator'), autoPause=1)
            if avId == base.localAvatar.getDoId():
                messenger.send('exitElevator')
                scale = base.localAvatar.getScale()
                self.offTrack[index].append(Func(base.camera.setScale, scale))
            self.offTrack[index].start()
            if avId in self.boardedAvIds:
                del self.boardedAvIds[avId]
        else:
            self.notify.warning('toon: ' + str(avId) + " doesn't exist, and" + ' cannot exit the elevator!')
        return

    def handleEnterSphere(self, collEntry):
        self.notify.debug('Entering Elevator Sphere....')
        print 'FSMhandleEnterSphere elevator%s avatar%s' % (self.elevatorTripId, localAvatar.lastElevatorLeft)
        if self.elevatorTripId and localAvatar.lastElevatorLeft == self.elevatorTripId:
            self.rejectBoard(base.localAvatar.doId, REJECT_SHUFFLE)
        elif base.localAvatar.hp > 0:
            self.cr.playGame.getPlace().detectedElevatorCollision(self)
            toon = base.localAvatar
            self.sendUpdate('requestBoard', [])

    def rejectBoard(self, avId, reason = 0):
        print 'rejectBoard %s' % reason
        if hasattr(base.localAvatar, 'elevatorNotifier'):
            if reason == REJECT_SHUFFLE:
                base.localAvatar.elevatorNotifier.showMe(TTLocalizer.ElevatorHoppedOff)
            elif reason == REJECT_MINLAFF:
                base.localAvatar.elevatorNotifier.showMe(TTLocalizer.ElevatorMinLaff % self.minLaff)
            elif reason == REJECT_PROMOTION:
                base.localAvatar.elevatorNotifier.showMe(TTLocalizer.BossElevatorRejectMessage)
            elif reason == REJECT_BLOCKED_ROOM:
                base.localAvatar.elevatorNotifier.showMe(TTLocalizer.ElevatorBlockedRoom)
        doneStatus = {'where': 'reject'}
        elevator = self.getPlaceElevator()
        if elevator:
            elevator.signalDone(doneStatus)

    def timerTask(self, task):
        countdownTime = int(task.duration - task.time)
        timeStr = str(countdownTime)
        if self.clockNode.getText() != timeStr:
            self.clockNode.setText(timeStr)
        if task.time >= task.duration:
            return Task.done
        else:
            return Task.cont

    def countdown(self, duration):
        countdownTask = Task(self.timerTask)
        countdownTask.duration = duration
        taskMgr.remove(self.uniqueName('elevatorTimerTask'))
        return taskMgr.add(countdownTask, self.uniqueName('elevatorTimerTask'))

    def handleExitButton(self):
        self.sendUpdate('requestExit')

    def enterWaitCountdown(self, ts):
        self.elevatorSphereNodePath.unstash()
        self.accept(self.uniqueName('enterelevatorSphere'), self.handleEnterSphere)
        self.accept('elevatorExitButton', self.handleExitButton)
        self.lastState = self.state

    def exitWaitCountdown(self):
        self.elevatorSphereNodePath.stash()
        self.ignore(self.uniqueName('enterelevatorSphere'))
        self.ignore('elevatorExitButton')
        self.ignore('localToonLeft')
        taskMgr.remove(self.uniqueName('elevatorTimerTask'))
        self.clock.removeNode()
        del self.clock
        del self.clockNode

    def enterClosing(self, ts):
        if self.localToonOnBoard:
            elevator = self.getPlaceElevator()
        if self.closeDoors.isPlaying() or self.lastState == 'closed' or self.openDoors.isPlaying():
            self.doorsNeedToClose = 1
        else:
            self.doorsNeedToClose = 0
        self.closeDoors.start(ts)

    def exitClosing(self):
        pass

    def onDoorOpenFinish(self):
        pass

    def onDoorCloseFinish(self):
        for avId in self.boardedAvIds.keys():
            av = self.cr.doId2do.get(avId)
            if av is not None:
                if av.getParent().compareTo(self.getElevatorModel()) == 0:
                    av.detachNode()

        return

    def enterClosed(self, ts):
        self.__doorsClosed(self.getZoneId())

    def exitClosed(self):
        pass

    def forceDoorsOpen(self):
        openDoors(self.leftDoor, self.rightDoor)

    def forceDoorsClosed(self):
        self.closeDoors.finish()
        closeDoors(self.leftDoor, self.rightDoor)

    def enterOff(self):
        self.lastState = self.state

    def exitOff(self):
        pass

    def enterWaitEmpty(self, ts):
        self.lastState = self.state

    def exitWaitEmpty(self):
        pass

    def enterOpening(self, ts):
        self.openDoors.start(ts)
        self.lastState = self.state

    def exitOpening(self):
        pass

    def startCountdownClock(self, countdownTime, ts):
        self.clockNode = TextNode('elevatorClock')
        self.clockNode.setFont(ToontownGlobals.getSignFont())
        self.clockNode.setAlign(TextNode.ACenter)
        self.clockNode.setTextColor(0.5, 0.5, 0.5, 1)
        self.clockNode.setText(str(int(countdownTime)))
        self.clock = self.getElevatorModel().attachNewNode(self.clockNode)
        self.clock.setPosHprScale(0, 4.4, 6.0, 0, 0, 0, 2.0, 2.0, 2.0)
        if ts < countdownTime:
            self.countdown(countdownTime - ts)

    def __doorsClosed(self, zoneId):
        if self.localToonOnBoard:
            self.localAvatar.stopGlitchKiller()
            hoodId = ZoneUtil.getHoodId(zoneId)
            loader = 'suitInterior'
            where = 'suitInterior'
            if base.cr.wantCogdominiums:
                loader = 'cogdoInterior'
                where = 'cogdoInterior'
            doneStatus = {'loader': loader,
             'where': where,
             'hoodId': hoodId,
             'zoneId': zoneId,
             'shardId': None}
            elevator = self.elevatorFSM
            del self.elevatorFSM
            elevator.signalDone(doneStatus)
        return

    def getElevatorModel(self):
        self.notify.error('getElevatorModel: pure virtual -- inheritors must override')

    def getPlaceElevator(self):
        place = self.cr.playGame.getPlace()
        if not hasattr(place, 'elevator'):
            self.notify.warning("Place was in state '%s' instead of Elevator." % place.state)
            place.detectedElevatorCollision(self)
            return None
        return place.elevator

    def getScaledPoint(self, index):
        point = self.elevatorPoints[index]
        return point

    def setElevatorTripId(self, id):
        self.elevatorTripId = id

    def getElevatorTripId(self):
        return self.elevatorTripId

    def setAntiShuffle(self, antiShuffle):
        self.antiShuffle = antiShuffle

    def getAntiShuffle(self):
        return self.antiShuffle

    def setMinLaff(self, minLaff):
        self.minLaff = minLaff

    def getMinLaff(self):
        return self.minLaff

    def getDestName(self):
        return None
