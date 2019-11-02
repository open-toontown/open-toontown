import math
from pandac.PandaModules import CollisionSphere, CollisionNode, Vec3, Point3, deg2Rad
from direct.interval.IntervalGlobal import Sequence, Func, Parallel, ActorInterval, Wait, Parallel, LerpHprInterval, ProjectileInterval, LerpPosInterval
from direct.directnotify import DirectNotifyGlobal
from toontown.building import ElevatorConstants
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.safezone import DistributedGolfKart
from toontown.building import DistributedElevatorExt
from toontown.building import ElevatorConstants
from toontown.distributed import DelayDelete
from direct.showbase import PythonUtil
from toontown.building import BoardingGroupShow

class DistributedCogKart(DistributedElevatorExt.DistributedElevatorExt):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedCogKart')
    JumpOutOffsets = ((6.5, -2, -0.025),
     (-6.5, -2, -0.025),
     (3.75, 5, -0.025),
     (-3.75, 5, -0.025))

    def __init__(self, cr):
        DistributedElevatorExt.DistributedElevatorExt.__init__(self, cr)
        self.type = ElevatorConstants.ELEVATOR_COUNTRY_CLUB
        self.kartModelPath = 'phase_12/models/bossbotHQ/Coggolf_cart3.bam'
        self.leftDoor = None
        self.rightDoor = None
        self.fillSlotTrack = None
        return

    def generate(self):
        DistributedElevatorExt.DistributedElevatorExt.generate(self)
        self.loader = self.cr.playGame.hood.loader
        if self.loader:
            self.notify.debug('Loader has been loaded')
            self.notify.debug(str(self.loader))
        else:
            self.notify.debug('Loader has not been loaded')
        self.golfKart = render.attachNewNode('golfKartNode')
        self.kart = loader.loadModel(self.kartModelPath)
        self.kart.setPos(0, 0, 0)
        self.kart.setScale(1)
        self.kart.reparentTo(self.golfKart)
        self.golfKart.reparentTo(self.loader.geom)
        self.wheels = self.kart.findAllMatches('**/wheelNode*')
        self.numWheels = self.wheels.getNumPaths()

    def announceGenerate(self):
        DistributedElevatorExt.DistributedElevatorExt.announceGenerate(self)
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

    def delete(self):
        DistributedElevatorExt.DistributedElevatorExt.delete(self)
        if hasattr(self, 'elevatorFSM'):
            del self.elevatorFSM

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

    def setColor(self, r, g, b):
        pass

    def getElevatorModel(self):
        return self.golfKart

    def enterWaitEmpty(self, ts):
        DistributedElevatorExt.DistributedElevatorExt.enterWaitEmpty(self, ts)

    def exitWaitEmpty(self):
        DistributedElevatorExt.DistributedElevatorExt.exitWaitEmpty(self)

    def forceDoorsOpen(self):
        pass

    def forceDoorsClosed(self):
        pass

    def setPosHpr(self, x, y, z, h, p, r):
        self.startingPos = Vec3(x, y, z)
        self.enteringPos = Vec3(x, y, z - 10)
        self.startingHpr = Vec3(h, 0, 0)
        self.golfKart.setPosHpr(x, y, z, h, 0, 0)

    def enterClosing(self, ts):
        if self.localToonOnBoard:
            elevator = self.getPlaceElevator()
            if elevator:
                elevator.fsm.request('elevatorClosing')
        self.closeDoors.start(ts)

    def enterClosed(self, ts):
        self.forceDoorsClosed()
        self.kartDoorsClosed(self.getZoneId())

    def kartDoorsClosed(self, zoneId):
        if self.localToonOnBoard:
            hoodId = ZoneUtil.getHoodId(zoneId)
            doneStatus = {'loader': 'suitInterior',
             'where': 'suitInterior',
             'hoodId': hoodId,
             'zoneId': zoneId,
             'shardId': None}
            elevator = self.elevatorFSM
            del self.elevatorFSM
            elevator.signalDone(doneStatus)
        return

    def setCountryClubInteriorZone(self, zoneId):
        if self.localToonOnBoard:
            hoodId = self.cr.playGame.hood.hoodId
            countryClubId = self.countryClubId
            if bboard.has('countryClubIdOverride'):
                countryClubId = bboard.get('countryClubIdOverride')
            doneStatus = {'loader': 'cogHQLoader',
             'where': 'countryClubInterior',
             'how': 'teleportIn',
             'zoneId': zoneId,
             'countryClubId': self.countryClubId,
             'hoodId': hoodId}
            self.cr.playGame.getPlace().elevator.signalDone(doneStatus)

    def setCountryClubInteriorZoneForce(self, zoneId):
        place = self.cr.playGame.getPlace()
        if place:
            place.fsm.request('elevator', [self, 1])
            hoodId = self.cr.playGame.hood.hoodId
            countryClubId = self.countryClubId
            if bboard.has('countryClubIdOverride'):
                countryClubId = bboard.get('countryClubIdOverride')
            doneStatus = {'loader': 'cogHQLoader',
             'where': 'countryClubInterior',
             'how': 'teleportIn',
             'zoneId': zoneId,
             'countryClubId': self.countryClubId,
             'hoodId': hoodId}
            if hasattr(place, 'elevator') and place.elevator:
                place.elevator.signalDone(doneStatus)
            else:
                self.notify.warning("setMintInteriorZoneForce: Couldn't find playGame.getPlace().elevator, zoneId: %s" % zoneId)
        else:
            self.notify.warning("setCountryClubInteriorZoneForce: Couldn't find playGame.getPlace(), zoneId: %s" % zoneId)

    def setCountryClubId(self, countryClubId):
        self.countryClubId = countryClubId

    def getZoneId(self):
        return 0

    def fillSlot(self, index, avId, wantBoardingShow = 0):
        self.notify.debug('%s.fillSlot(%s, %s, ... %s)' % (self.doId,
         index,
         avId,
         globalClock.getRealTime()))
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
            self.deferredSlots.append((index, avId, wantBoardingShow))
        else:
            if avId == base.localAvatar.getDoId():
                place = base.cr.playGame.getPlace()
                if not place:
                    return
                elevator = self.getPlaceElevator()
                if elevator == None:
                    place.fsm.request('elevator')
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
            toon.wrtReparentTo(self.golfKart)
            sitStartDuration = toon.getDuration('sit-start')
            jumpTrack = self.generateToonJumpTrack(toon, index)
            track = Sequence(jumpTrack, Func(toon.setAnimState, 'Sit', 1.0), Func(self.clearToonTrack, avId), name=toon.uniqueName('fillElevator'), autoPause=1)
            if wantBoardingShow:
                boardingTrack, boardingTrackType = self.getBoardingTrack(toon, index, True)
                track = Sequence(boardingTrack, track)
                if avId == base.localAvatar.getDoId():
                    cameraWaitTime = 2.5
                    if boardingTrackType == BoardingGroupShow.TRACK_TYPE_RUN:
                        cameraWaitTime = 0.5
                    cameraTrack = Sequence(Wait(cameraWaitTime), cameraTrack)
            if self.canHideBoardingQuitBtn(avId):
                track = Sequence(Func(localAvatar.boardingParty.groupPanel.disableQuitButton), track)
            if avId == base.localAvatar.getDoId():
                track = Parallel(cameraTrack, track)
            track.delayDelete = DelayDelete.DelayDelete(toon, 'CogKart.fillSlot')
            self.storeToonTrack(avId, track)
            track.start()
            self.fillSlotTrack = track
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
        jumpTrack = Sequence(Parallel(toonJumpTrack, Sequence(Wait(1), toonSitTrack)))
        return jumpTrack

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
            track = Sequence(jumpOutTrack, Func(self.notifyToonOffElevator, toon), Func(self.clearToonTrack, avId), name=toon.uniqueName('emptyElevator'), autoPause=1)
            if self.canHideBoardingQuitBtn(avId):
                track.append(Func(localAvatar.boardingParty.groupPanel.enableQuitButton))
                track.append(Func(localAvatar.boardingParty.enableGoButton))
            track.delayDelete = DelayDelete.DelayDelete(toon, 'CogKart.emptySlot')
            self.storeToonTrack(toon.doId, track)
            track.start()
            if avId == base.localAvatar.getDoId():
                messenger.send('exitElevator')
            if avId in self.boardedAvIds:
                del self.boardedAvIds[avId]
        else:
            self.notify.warning('toon: ' + str(avId) + " doesn't exist, and" + ' cannot exit the elevator!')
        return

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
        DistributedElevatorExt.DistributedElevatorExt.startCountdownClock(self, countdownTime, ts)
        self.clock.setH(self.clock.getH() + 180)

    def rejectBoard(self, avId, reason = 0):
        print 'rejectBoard %s' % reason
        if hasattr(base.localAvatar, 'elevatorNotifier'):
            if reason == ElevatorConstants.REJECT_SHUFFLE:
                base.localAvatar.elevatorNotifier.showMe(TTLocalizer.ElevatorHoppedOff)
            elif reason == ElevatorConstants.REJECT_MINLAFF:
                base.localAvatar.elevatorNotifier.showMe(TTLocalizer.KartMinLaff % self.minLaff)
            elif reason == ElevatorConstants.REJECT_PROMOTION:
                base.localAvatar.elevatorNotifier.showMe(TTLocalizer.BossElevatorRejectMessage)
            elif reason == ElevatorConstants.REJECT_NOT_YET_AVAILABLE:
                base.localAvatar.elevatorNotifier.showMe(TTLocalizer.NotYetAvailable)
        doneStatus = {'where': 'reject'}
        elevator = self.getPlaceElevator()
        if elevator:
            elevator.signalDone(doneStatus)

    def getDestName(self):
        if self.countryClubId == ToontownGlobals.BossbotCountryClubIntA:
            return TTLocalizer.ElevatorBossBotCourse0
        elif self.countryClubId == ToontownGlobals.BossbotCountryClubIntB:
            return TTLocalizer.ElevatorBossBotCourse1
        elif self.countryClubId == ToontownGlobals.BossbotCountryClubIntC:
            return TTLocalizer.ElevatorBossBotCourse2
