from pandac.PandaModules import *
from direct.distributed.ClockDelta import *
from direct.interval.IntervalGlobal import *
from .ElevatorConstants import *
from .ElevatorUtils import *
from direct.showbase import PythonUtil
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State
from direct.distributed import DistributedObject
from direct.fsm import State
from toontown.toonbase import TTLocalizer, ToontownGlobals
from direct.task.Task import Task
from toontown.distributed import DelayDelete
from toontown.hood import ZoneUtil
from toontown.toontowngui import TeaserPanel
from toontown.building import BoardingGroupShow

class DistributedElevator(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedElevator')
    JumpOutOffsets = JumpOutOffsets

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        self.bldgRequest = None
        self.toonRequests = {}
        self.deferredSlots = []
        self.localToonOnBoard = 0
        self.boardedAvIds = {}
        self.openSfx = base.loader.loadSfx('phase_5/audio/sfx/elevator_door_open.ogg')
        self.finalOpenSfx = None
        self.closeSfx = base.loader.loadSfx('phase_5/audio/sfx/elevator_door_close.ogg')
        self.elevatorFSM = None
        self.finalCloseSfx = None
        self.elevatorPoints = ElevatorPoints
        self.fillSlotTrack = None
        self.type = ELEVATOR_NORMAL
        self.countdownTime = ElevatorData[self.type]['countdown']
        self.__toonTracks = {}
        self.fsm = ClassicFSM.ClassicFSM('DistributedElevator', [State.State('off', self.enterOff, self.exitOff, ['opening',
          'waitEmpty',
          'waitCountdown',
          'closing',
          'closed']),
         State.State('opening', self.enterOpening, self.exitOpening, ['waitEmpty', 'waitCountdown']),
         State.State('waitEmpty', self.enterWaitEmpty, self.exitWaitEmpty, ['waitCountdown']),
         State.State('waitCountdown', self.enterWaitCountdown, self.exitWaitCountdown, ['waitEmpty', 'closing']),
         State.State('closing', self.enterClosing, self.exitClosing, ['closed', 'waitEmpty']),
         State.State('closed', self.enterClosed, self.exitClosed, ['opening'])], 'off', 'off')
        self.fsm.enterInitialState()
        self.isSetup = 0
        self.__preSetupState = None
        self.bigElevator = 0
        return

    def generate(self):
        DistributedObject.DistributedObject.generate(self)

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
        self.closeDoors = Sequence(self.closeDoors, Func(self.onDoorCloseFinish))
        self.finishSetup()

    def finishSetup(self):
        self.isSetup = 1
        self.offsetNP = self.getElevatorModel().attachNewNode('dummyNP')
        if self.__preSetupState:
            self.fsm.request(self.__preSetupState, [0])
            self.__preSetupState = None
        for slot in self.deferredSlots:
            self.fillSlot(*slot)

        self.deferredSlots = []
        return

    def disable(self):
        if self.bldgRequest:
            self.cr.relatedObjectMgr.abortRequest(self.bldgRequest)
            self.bldgRequest = None
        for request in list(self.toonRequests.values()):
            self.cr.relatedObjectMgr.abortRequest(request)

        self.toonRequests = {}
        if hasattr(self, 'openDoors'):
            self.openDoors.pause()
        if hasattr(self, 'closeDoors'):
            self.closeDoors.pause()
        self.clearToonTracks()
        self.fsm.request('off')
        DistributedObject.DistributedObject.disable(self)
        return

    def delete(self):
        if self.isSetup:
            self.elevatorSphereNodePath.removeNode()
            del self.elevatorSphereNodePath
            del self.elevatorSphereNode
            del self.elevatorSphere
            del self.bldg
            if self.leftDoor:
                del self.leftDoor
            if self.rightDoor:
                del self.rightDoor
            if hasattr(self, 'openDoors'):
                del self.openDoors
            if hasattr(self, 'closeDoors'):
                del self.closeDoors
        del self.fsm
        del self.openSfx
        del self.closeSfx
        self.isSetup = 0
        self.fillSlotTrack = None
        self.offsetNP.removeNode()
        if hasattr(base.localAvatar, 'elevatorNotifier'):
            base.localAvatar.elevatorNotifier.cleanup()
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
            self.fsm.request(state, [globalClockDelta.localElapsedTime(timestamp)])
        else:
            self.__preSetupState = state

    def fillSlot0(self, avId, wantBoardingShow):
        self.fillSlot(0, avId, wantBoardingShow)

    def fillSlot1(self, avId, wantBoardingShow):
        self.fillSlot(1, avId, wantBoardingShow)

    def fillSlot2(self, avId, wantBoardingShow):
        self.fillSlot(2, avId, wantBoardingShow)

    def fillSlot3(self, avId, wantBoardingShow):
        self.fillSlot(3, avId, wantBoardingShow)

    def fillSlot4(self, avId, wantBoardingShow):
        self.fillSlot(4, avId, wantBoardingShow)

    def fillSlot5(self, avId, wantBoardingShow):
        self.fillSlot(5, avId, wantBoardingShow)

    def fillSlot6(self, avId, wantBoardingShow):
        self.fillSlot(6, avId, wantBoardingShow)

    def fillSlot7(self, avId, wantBoardingShow):
        self.fillSlot(7, avId, wantBoardingShow)

    def fillSlot(self, index, avId, wantBoardingShow = 0):
        self.notify.debug('%s.fillSlot(%s, %s, ...)' % (self.doId, index, avId))
        request = self.toonRequests.get(index)
        if request:
            self.cr.relatedObjectMgr.abortRequest(request)
            del self.toonRequests[index]
        if avId == 0:
            pass
        elif avId not in self.cr.doId2do:
            func = PythonUtil.Functor(self.gotToon, index, avId)
            self.toonRequests[index] = self.cr.relatedObjectMgr.requestObjects([avId], allCallback=func)
        elif not self.isSetup:
            self.deferredSlots.append((index, avId, wantBoardingShow))
        else:
            if avId == base.localAvatar.getDoId():
                place = base.cr.playGame.getPlace()
                if not place:
                    return
                place.detectedElevatorCollision(self)
                elevator = self.getPlaceElevator()
                if elevator == None:
                    if place.fsm.hasStateNamed('elevator'):
                        place.fsm.request('elevator')
                    elif place.fsm.hasStateNamed('Elevator'):
                        place.fsm.request('Elevator')
                    elevator = self.getPlaceElevator()
                if not elevator:
                    return
                self.localToonOnBoard = 1
                if hasattr(localAvatar, 'boardingParty') and localAvatar.boardingParty:
                    localAvatar.boardingParty.forceCleanupInviteePanel()
                    localAvatar.boardingParty.forceCleanupInviterPanels()
                if hasattr(base.localAvatar, 'elevatorNotifier'):
                    base.localAvatar.elevatorNotifier.cleanup()
                cameraTrack = Sequence()
                cameraTrack.append(Func(elevator.fsm.request, 'boarding', [self.getElevatorModel()]))
                cameraTrack.append(Func(elevator.fsm.request, 'boarded'))
            toon = self.cr.doId2do[avId]
            toon.stopSmooth()
            if not wantBoardingShow:
                toon.setZ(self.getElevatorModel(), self.elevatorPoints[index][2])
                toon.setShadowHeight(0)
            if toon.isDisguised:
                animInFunc = Sequence(Func(toon.suit.loop, 'walk'))
                animFunc = Sequence(Func(toon.setAnimState, 'neutral', 1.0), Func(toon.suit.loop, 'neutral'))
            else:
                animInFunc = Sequence(Func(toon.setAnimState, 'run', 1.0))
                animFunc = Func(toon.setAnimState, 'neutral', 1.0)
            toon.headsUp(self.getElevatorModel(), Point3(*self.elevatorPoints[index]))
            track = Sequence(animInFunc, LerpPosInterval(toon, TOON_BOARD_ELEVATOR_TIME * 0.75, Point3(*self.elevatorPoints[index]), other=self.getElevatorModel()), LerpHprInterval(toon, TOON_BOARD_ELEVATOR_TIME * 0.25, Point3(180, 0, 0), other=self.getElevatorModel()), Func(self.clearToonTrack, avId), animFunc, name=toon.uniqueName('fillElevator'), autoPause=1)
            if wantBoardingShow:
                boardingTrack, boardingTrackType = self.getBoardingTrack(toon, index, False)
                track = Sequence(boardingTrack, track)
                if avId == base.localAvatar.getDoId():
                    cameraWaitTime = 2.5
                    if boardingTrackType == BoardingGroupShow.TRACK_TYPE_RUN:
                        cameraWaitTime = 0.5
                    elif boardingTrackType == BoardingGroupShow.TRACK_TYPE_POOF:
                        cameraWaitTime = 1
                    cameraTrack = Sequence(Wait(cameraWaitTime), cameraTrack)
            if self.canHideBoardingQuitBtn(avId):
                track = Sequence(Func(localAvatar.boardingParty.groupPanel.disableQuitButton), track)
            if avId == base.localAvatar.getDoId():
                track = Parallel(cameraTrack, track)
            track.delayDelete = DelayDelete.DelayDelete(toon, 'Elevator.fillSlot')
            self.storeToonTrack(avId, track)
            track.start()
            self.fillSlotTrack = track
            self.boardedAvIds[avId] = None
        return

    def emptySlot0(self, avId, bailFlag, timestamp, time):
        self.emptySlot(0, avId, bailFlag, timestamp, time)

    def emptySlot1(self, avId, bailFlag, timestamp, time):
        self.emptySlot(1, avId, bailFlag, timestamp, time)

    def emptySlot2(self, avId, bailFlag, timestamp, time):
        self.emptySlot(2, avId, bailFlag, timestamp, time)

    def emptySlot3(self, avId, bailFlag, timestamp, time):
        self.emptySlot(3, avId, bailFlag, timestamp, time)

    def emptySlot4(self, avId, bailFlag, timestamp, time):
        self.emptySlot(4, avId, bailFlag, timestamp, time)

    def emptySlot5(self, avId, bailFlag, timestamp, time):
        self.emptySlot(5, avId, bailFlag, timestamp)

    def emptySlot6(self, avId, bailFlag, timestamp, time):
        self.emptySlot(6, avId, bailFlag, timestamp, time)

    def emptySlot7(self, avId, bailFlag, timestamp, time):
        self.emptySlot(7, avId, bailFlag, timestamp, time)

    def notifyToonOffElevator(self, toon):
        toon.setAnimState('neutral', 1.0)
        if toon == base.localAvatar:
            doneStatus = {'where': 'exit'}
            elevator = self.getPlaceElevator()
            if elevator:
                elevator.signalDone(doneStatus)
            self.localToonOnBoard = 0
        else:
            toon.startSmooth()

    def emptySlot(self, index, avId, bailFlag, timestamp, timeSent = 0):
        if self.fillSlotTrack:
            self.fillSlotTrack.finish()
            self.fillSlotTrack = None
        if avId == 0:
            pass
        elif not self.isSetup:
            newSlots = []
            for slot in self.deferredSlots:
                if slot[0] != index:
                    newSlots.append(slot)

            self.deferredSlots = newSlots
        else:
            timeToSet = self.countdownTime
            if timeSent > 0:
                timeToSet = timeSent
            if avId in self.cr.doId2do:
                if bailFlag == 1 and hasattr(self, 'clockNode'):
                    if timestamp < timeToSet and timestamp >= 0:
                        self.countdown(timeToSet - timestamp)
                    else:
                        self.countdown(timeToSet)
                toon = self.cr.doId2do[avId]
                toon.stopSmooth()
                if toon.isDisguised:
                    toon.suit.loop('walk')
                    animFunc = Func(toon.suit.loop, 'neutral')
                else:
                    toon.setAnimState('run', 1.0)
                    animFunc = Func(toon.setAnimState, 'neutral', 1.0)
                track = Sequence(LerpPosInterval(toon, TOON_EXIT_ELEVATOR_TIME, Point3(*self.JumpOutOffsets[index]), other=self.getElevatorModel()), animFunc, Func(self.notifyToonOffElevator, toon), Func(self.clearToonTrack, avId), name=toon.uniqueName('emptyElevator'), autoPause=1)
                if self.canHideBoardingQuitBtn(avId):
                    track.append(Func(localAvatar.boardingParty.groupPanel.enableQuitButton))
                    track.append(Func(localAvatar.boardingParty.enableGoButton))
                track.delayDelete = DelayDelete.DelayDelete(toon, 'Elevator.emptySlot')
                self.storeToonTrack(avId, track)
                track.start()
                if avId == base.localAvatar.getDoId():
                    messenger.send('exitElevator')
                if avId in self.boardedAvIds:
                    del self.boardedAvIds[avId]
            else:
                self.notify.warning('toon: ' + str(avId) + " doesn't exist, and" + ' cannot exit the elevator!')
        return

    def allowedToEnter(self, zoneId = None):
        allowed = False
        if hasattr(base, 'ttAccess') and base.ttAccess:
            if zoneId:
                allowed = base.ttAccess.canAccess(zoneId)
            else:
                allowed = base.ttAccess.canAccess()
        return allowed

    def handleEnterSphere(self, collEntry):
        self.notify.debug('Entering Elevator Sphere....')
        if self.allowedToEnter(self.zoneId):
            if self.elevatorTripId and localAvatar.lastElevatorLeft == self.elevatorTripId:
                self.rejectBoard(base.localAvatar.doId, REJECT_SHUFFLE)
            elif base.localAvatar.hp > 0:
                self.cr.playGame.getPlace().detectedElevatorCollision(self)
                toon = base.localAvatar
                self.sendUpdate('requestBoard', [])
        else:
            place = base.cr.playGame.getPlace()
            if place:
                place.fsm.request('stopped')
            self.dialog = TeaserPanel.TeaserPanel(pageName='cogHQ', doneFunc=self.handleOkTeaser)

    def handleOkTeaser(self):
        self.dialog.destroy()
        del self.dialog
        place = base.cr.playGame.getPlace()
        if place:
            place.fsm.request('walk')

    def rejectBoard(self, avId, reason = 0):
        print('rejectBoard %s' % reason)
        if hasattr(base.localAvatar, 'elevatorNotifier'):
            if reason == REJECT_SHUFFLE:
                base.localAvatar.elevatorNotifier.showMe(TTLocalizer.ElevatorHoppedOff)
            elif reason == REJECT_MINLAFF:
                base.localAvatar.elevatorNotifier.showMe(TTLocalizer.ElevatorMinLaff % self.minLaff)
            elif reason == REJECT_PROMOTION:
                base.localAvatar.elevatorNotifier.showMe(TTLocalizer.BossElevatorRejectMessage)
            elif reason == REJECT_NOT_YET_AVAILABLE:
                base.localAvatar.elevatorNotifier.showMe(TTLocalizer.NotYetAvailable)
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
        localAvatar.lastElevatorLeft = self.elevatorTripId
        self.sendUpdate('requestExit')

    def enterWaitCountdown(self, ts):
        self.elevatorSphereNodePath.unstash()
        self.accept(self.uniqueName('enterelevatorSphere'), self.handleEnterSphere)
        self.accept('elevatorExitButton', self.handleExitButton)

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
            if elevator:
                elevator.fsm.request('elevatorClosing')
        self.closeDoors.start(ts)

    def exitClosing(self):
        pass

    def onDoorCloseFinish(self):
        for avId in list(self.boardedAvIds.keys()):
            av = self.cr.doId2do.get(avId)
            if av is not None:
                if av.getParent().compareTo(self.getElevatorModel()) == 0:
                    av.detachNode()

        self.boardedAvIds = {}
        return

    def enterClosed(self, ts):
        self.forceDoorsClosed()
        self.__doorsClosed(self.getZoneId())

    def exitClosed(self):
        pass

    def forceDoorsOpen(self):
        openDoors(self.leftDoor, self.rightDoor)

    def forceDoorsClosed(self):
        self.closeDoors.finish()
        closeDoors(self.leftDoor, self.rightDoor)

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def enterWaitEmpty(self, ts):
        pass

    def exitWaitEmpty(self):
        pass

    def enterOpening(self, ts):
        self.openDoors.start(ts)

    def exitOpening(self):
        pass

    def startCountdownClock(self, countdownTime, ts):
        self.clockNode = TextNode('elevatorClock')
        self.clockNode.setFont(ToontownGlobals.getSignFont())
        self.clockNode.setAlign(TextNode.ACenter)
        self.clockNode.setTextColor(0.5, 0.5, 0.5, 1)
        self.clockNode.setText(str(int(countdownTime)))
        self.clock = self.getElevatorModel().attachNewNode(self.clockNode)
        self.clock.setPosHprScale(0, 2.0, 7.5, 0, 0, 0, 2.0, 2.0, 2.0)
        if ts < countdownTime:
            self.countdown(countdownTime - ts)

    def _getDoorsClosedInfo(self):
        return ('suitInterior', 'suitInterior')

    def __doorsClosed(self, zoneId):
        if self.localToonOnBoard:
            hoodId = ZoneUtil.getHoodId(zoneId)
            loader, where = self._getDoorsClosedInfo()
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
        if place:
            if hasattr(place, 'elevator'):
                return place.elevator
            else:
                self.notify.warning("Place was in state '%s' instead of Elevator." % place.fsm.getCurrentState().getName())
                place.detectedElevatorCollision(self)
        else:
            self.notify.warning("Place didn't exist")
        return None

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
            if key in self.__toonTracks:
                self.clearToonTrack(key)

    def getDestName(self):
        return None

    def getOffsetPos(self, seatIndex = 0):
        return self.JumpOutOffsets[seatIndex]

    def getOffsetPosWrtToonParent(self, toon, seatIndex = 0):
        self.offsetNP.setPos(Point3(*self.getOffsetPos(seatIndex)))
        return self.offsetNP.getPos(toon.getParent())

    def getOffsetPosWrtRender(self, seatIndex = 0):
        self.offsetNP.setPos(Point3(*self.getOffsetPos(seatIndex)))
        return self.offsetNP.getPos(render)

    def canHideBoardingQuitBtn(self, avId):
        if avId == localAvatar.doId and hasattr(localAvatar, 'boardingParty') and localAvatar.boardingParty and localAvatar.boardingParty.groupPanel:
            return True
        else:
            return False

    def getBoardingTrack(self, toon, seatIndex, wantToonRotation):
        self.boardingGroupShow = BoardingGroupShow.BoardingGroupShow(toon)
        track, trackType = self.boardingGroupShow.getBoardingTrack(self.getElevatorModel(), self.getOffsetPosWrtToonParent(toon, seatIndex), self.getOffsetPosWrtRender(seatIndex), wantToonRotation)
        return (track, trackType)
