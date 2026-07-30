from direct.interval.IntervalGlobal import *
from direct.distributed.ClockDelta import *
from .ElevatorConstants import *
from . import ElevatorUtils
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import ToontownBattleGlobals
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State
from direct.distributed import DistributedObject
from direct.fsm import State
from toontown.battle import BattleBase
from toontown.hood import ZoneUtil

class DistributedSuitInterior(DistributedObject.DistributedObject):
    id = 0

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        self.toons = []
        self.activeIntervals = {}
        self.openSfx = base.loader.loadSfx('phase_5/audio/sfx/elevator_door_open.ogg')
        self.closeSfx = base.loader.loadSfx('phase_5/audio/sfx/elevator_door_close.ogg')
        self.suits = []
        self.reserveSuits = []
        self.joiningReserves = []
        self.distBldgDoId = None
        self.currentFloor = -1
        self.numFloors = None
        self.elevatorName = self.__uniqueName('elevator')
        self.floorModel = None
        self.elevatorOutOpen = 0
        self.BottomFloor_SuitPositions = [Point3(0, 15, 0),
         Point3(10, 20, 0),
         Point3(-7, 24, 0),
         Point3(-10, 0, 0)]
        self.BottomFloor_SuitHs = [75,
         170,
         -91,
         -44]
        self.Cubicle_SuitPositions = [Point3(0, 18, 0),
         Point3(10, 12, 0),
         Point3(-9, 11, 0),
         Point3(-3, 13, 0)]
        self.Cubicle_SuitHs = [170,
         56,
         -52,
         10]
        self.BossOffice_SuitPositions = [Point3(0, 15, 0),
         Point3(10, 20, 0),
         Point3(-10, 6, 0),
         Point3(-17, 34, 11)]
        self.BossOffice_SuitHs = [170,
         120,
         12,
         38]
        self.waitMusic = base.loader.loadMusic('phase_7/audio/bgm/encntr_toon_winning_indoor.ogg')
        self.elevatorMusic = base.loader.loadMusic('phase_7/audio/bgm/tt_elevator.ogg')
        self.fsm = ClassicFSM.ClassicFSM('DistributedSuitInterior', [State.State('WaitForAllToonsInside', self.enterWaitForAllToonsInside, self.exitWaitForAllToonsInside, ['Elevator']),
         State.State('Elevator', self.enterElevator, self.exitElevator, ['Battle']),
         State.State('Battle', self.enterBattle, self.exitBattle, ['Resting', 'Reward', 'ReservesJoining']),
         State.State('ReservesJoining', self.enterReservesJoining, self.exitReservesJoining, ['Battle']),
         State.State('Resting', self.enterResting, self.exitResting, ['Elevator']),
         State.State('Reward', self.enterReward, self.exitReward, ['Off']),
         State.State('Off', self.enterOff, self.exitOff, ['Elevator', 'WaitForAllToonsInside', 'Battle'])], 'Off', 'Off')
        self.fsm.enterInitialState()
        return

    def __uniqueName(self, name):
        DistributedSuitInterior.id += 1
        return name + '%d' % DistributedSuitInterior.id

    def generate(self):
        DistributedObject.DistributedObject.generate(self)
        self.announceGenerateName = self.uniqueName('generate')
        self.accept(self.announceGenerateName, self.handleAnnounceGenerate)
        self.elevatorModelIn = loader.loadModel('phase_4/models/modules/elevator')
        self.leftDoorIn = self.elevatorModelIn.find('**/left-door')
        self.rightDoorIn = self.elevatorModelIn.find('**/right-door')
        self.elevatorModelOut = loader.loadModel('phase_4/models/modules/elevator')
        self.leftDoorOut = self.elevatorModelOut.find('**/left-door')
        self.rightDoorOut = self.elevatorModelOut.find('**/right-door')

    def setElevatorLights(self, elevatorModel):
        npc = elevatorModel.findAllMatches('**/floor_light_?;+s')
        for i in range(npc.getNumPaths()):
            np = npc.getPath(i)
            floor = int(np.getName()[-1:]) - 1
            if floor == self.currentFloor:
                np.setColor(LIGHT_ON_COLOR)
            elif floor < self.numFloors:
                np.setColor(LIGHT_OFF_COLOR)
            else:
                np.hide()

    def handleAnnounceGenerate(self, obj):
        self.ignore(self.announceGenerateName)
        self.sendUpdate('setAvatarJoined', [])

    def disable(self):
        self.fsm.requestFinalState()
        self.__cleanupIntervals()
        self.ignoreAll()
        self.__cleanup()
        DistributedObject.DistributedObject.disable(self)

    def delete(self):
        del self.waitMusic
        del self.elevatorMusic
        del self.openSfx
        del self.closeSfx
        del self.fsm
        base.localAvatar.inventory.setBattleCreditMultiplier(1)
        DistributedObject.DistributedObject.delete(self)

    def __cleanup(self):
        self.toons = []
        self.suits = []
        self.reserveSuits = []
        self.joiningReserves = []
        if self.elevatorModelIn != None:
            self.elevatorModelIn.removeNode()
        if self.elevatorModelOut != None:
            self.elevatorModelOut.removeNode()
        if self.floorModel != None:
            self.floorModel.removeNode()
        self.leftDoorIn = None
        self.rightDoorIn = None
        self.leftDoorOut = None
        self.rightDoorOut = None
        return

    def __addToon(self, toon):
        self.accept(toon.uniqueName('disable'), self.__handleUnexpectedExit, extraArgs=[toon])

    def __handleUnexpectedExit(self, toon):
        self.notify.warning('handleUnexpectedExit() - toon: %d' % toon.doId)
        self.__removeToon(toon, unexpected=1)

    def __removeToon(self, toon, unexpected = 0):
        if self.toons.count(toon) == 1:
            self.toons.remove(toon)
        self.ignore(toon.uniqueName('disable'))

    def __finishInterval(self, name):
        if name in self.activeIntervals:
            interval = self.activeIntervals[name]
            if interval.isPlaying():
                interval.finish()

    def __cleanupIntervals(self):
        for interval in list(self.activeIntervals.values()):
            interval.finish()

        self.activeIntervals = {}

    def __closeInElevator(self):
        self.leftDoorIn.setPos(3.5, 0, 0)
        self.rightDoorIn.setPos(-3.5, 0, 0)

    def getZoneId(self):
        return self.zoneId

    def setZoneId(self, zoneId):
        self.zoneId = zoneId

    def getExtZoneId(self):
        return self.extZoneId

    def setExtZoneId(self, extZoneId):
        self.extZoneId = extZoneId

    def getDistBldgDoId(self):
        return self.distBldgDoId

    def setDistBldgDoId(self, distBldgDoId):
        self.distBldgDoId = distBldgDoId

    def setNumFloors(self, numFloors):
        self.numFloors = numFloors

    def setToons(self, toonIds, hack):
        self.toonIds = toonIds
        oldtoons = self.toons
        self.toons = []
        for toonId in toonIds:
            if toonId != 0:
                if toonId in self.cr.doId2do:
                    toon = self.cr.doId2do[toonId]
                    toon.stopSmooth()
                    self.toons.append(toon)
                    if oldtoons.count(toon) == 0:
                        self.__addToon(toon)
                else:
                    self.notify.warning('setToons() - no toon: %d' % toonId)

        for toon in oldtoons:
            if self.toons.count(toon) == 0:
                self.__removeToon(toon)

    def setSuits(self, suitIds, reserveIds, values):
        oldsuits = self.suits
        self.suits = []
        self.joiningReserves = []
        for suitId in suitIds:
            if suitId in self.cr.doId2do:
                suit = self.cr.doId2do[suitId]
                self.suits.append(suit)
                suit.fsm.request('Battle')
                suit.buildingSuit = 1
                suit.reparentTo(render)
                if oldsuits.count(suit) == 0:
                    self.joiningReserves.append(suit)
            else:
                self.notify.warning('setSuits() - no suit: %d' % suitId)

        self.reserveSuits = []
        for index in range(len(reserveIds)):
            suitId = reserveIds[index]
            if suitId in self.cr.doId2do:
                suit = self.cr.doId2do[suitId]
                self.reserveSuits.append((suit, values[index]))
            else:
                self.notify.warning('setSuits() - no suit: %d' % suitId)

        if len(self.joiningReserves) > 0:
            self.fsm.request('ReservesJoining')

    def setState(self, state, timestamp):
        self.fsm.request(state, [globalClockDelta.localElapsedTime(timestamp)])

    def d_elevatorDone(self):
        self.sendUpdate('elevatorDone', [])

    def d_reserveJoinDone(self):
        self.sendUpdate('reserveJoinDone', [])

    def enterOff(self, ts = 0):
        return None

    def exitOff(self):
        return None

    def enterWaitForAllToonsInside(self, ts = 0):
        return None

    def exitWaitForAllToonsInside(self):
        return None

    def __playElevator(self, ts, name, callback):
        SuitHs = []
        SuitPositions = []
        if self.floorModel:
            self.floorModel.removeNode()
        if self.currentFloor == 0:
            self.floorModel = loader.loadModel('phase_7/models/modules/suit_interior')
            SuitHs = self.BottomFloor_SuitHs
            SuitPositions = self.BottomFloor_SuitPositions
        elif self.currentFloor == self.numFloors - 1:
            self.floorModel = loader.loadModel('phase_7/models/modules/boss_suit_office')
            SuitHs = self.BossOffice_SuitHs
            SuitPositions = self.BossOffice_SuitPositions
        else:
            self.floorModel = loader.loadModel('phase_7/models/modules/cubicle_room')
            SuitHs = self.Cubicle_SuitHs
            SuitPositions = self.Cubicle_SuitPositions
        self.floorModel.reparentTo(render)
        elevIn = self.floorModel.find('**/elevator-in')
        elevOut = self.floorModel.find('**/elevator-out')
        for index in range(len(self.suits)):
            self.suits[index].setPos(SuitPositions[index])
            if len(self.suits) > 2:
                self.suits[index].setH(SuitHs[index])
            else:
                self.suits[index].setH(170)
            self.suits[index].loop('neutral')

        for toon in self.toons:
            toon.reparentTo(self.elevatorModelIn)
            index = self.toonIds.index(toon.doId)
            toon.setPos(ElevatorPoints[index][0], ElevatorPoints[index][1], ElevatorPoints[index][2])
            toon.setHpr(180, 0, 0)
            toon.loop('neutral')

        self.elevatorModelIn.reparentTo(elevIn)
        self.leftDoorIn.setPos(3.5, 0, 0)
        self.rightDoorIn.setPos(-3.5, 0, 0)
        self.elevatorModelOut.reparentTo(elevOut)
        self.leftDoorOut.setPos(3.5, 0, 0)
        self.rightDoorOut.setPos(-3.5, 0, 0)
        camera.reparentTo(self.elevatorModelIn)
        camera.setH(180)
        camera.setPos(0, 14, 4)
        base.playMusic(self.elevatorMusic, looping=1, volume=0.8)
        track = Sequence(ElevatorUtils.getRideElevatorInterval(ELEVATOR_NORMAL), ElevatorUtils.getOpenInterval(self, self.leftDoorIn, self.rightDoorIn, self.openSfx, None, type=ELEVATOR_NORMAL), Func(camera.wrtReparentTo, render))
        for toon in self.toons:
            track.append(Func(toon.wrtReparentTo, render))

        track.append(Func(callback))
        track.start(ts)
        self.activeIntervals[name] = track
        return

    def enterElevator(self, ts = 0):
        self.currentFloor += 1
        self.cr.playGame.getPlace().currentFloor = self.currentFloor
        self.setElevatorLights(self.elevatorModelIn)
        self.setElevatorLights(self.elevatorModelOut)
        self.__playElevator(ts, self.elevatorName, self.__handleElevatorDone)
        mult = ToontownBattleGlobals.getCreditMultiplier(self.currentFloor)
        base.localAvatar.inventory.setBattleCreditMultiplier(mult)

    def __handleElevatorDone(self):
        self.d_elevatorDone()

    def exitElevator(self):
        self.elevatorMusic.stop()
        self.__finishInterval(self.elevatorName)
        return None

    def __playCloseElevatorOut(self, name):
        track = Sequence(Wait(SUIT_LEAVE_ELEVATOR_TIME), Parallel(SoundInterval(self.closeSfx), LerpPosInterval(self.leftDoorOut, ElevatorData[ELEVATOR_NORMAL]['closeTime'], ElevatorUtils.getLeftClosePoint(ELEVATOR_NORMAL), startPos=Point3(0, 0, 0), blendType='easeOut'), LerpPosInterval(self.rightDoorOut, ElevatorData[ELEVATOR_NORMAL]['closeTime'], ElevatorUtils.getRightClosePoint(ELEVATOR_NORMAL), startPos=Point3(0, 0, 0), blendType='easeOut')))
        track.start()
        self.activeIntervals[name] = track

    def enterBattle(self, ts = 0):
        if self.elevatorOutOpen == 1:
            self.__playCloseElevatorOut(self.uniqueName('close-out-elevator'))
            camera.setPos(0, -15, 6)
            camera.headsUp(self.elevatorModelOut)
        return None

    def exitBattle(self):
        if self.elevatorOutOpen == 1:
            self.__finishInterval(self.uniqueName('close-out-elevator'))
            self.elevatorOutOpen = 0
        return None

    def __playReservesJoining(self, ts, name, callback):
        index = 0
        for suit in self.joiningReserves:
            suit.reparentTo(render)
            suit.setPos(self.elevatorModelOut, Point3(ElevatorPoints[index][0], ElevatorPoints[index][1], ElevatorPoints[index][2]))
            index += 1
            suit.setH(180)
            suit.loop('neutral')

        track = Sequence(Func(camera.wrtReparentTo, self.elevatorModelOut), Func(camera.setPos, Point3(0, -8, 2)), Func(camera.setHpr, Vec3(0, 10, 0)), Parallel(SoundInterval(self.openSfx), LerpPosInterval(self.leftDoorOut, ElevatorData[ELEVATOR_NORMAL]['closeTime'], Point3(0, 0, 0), startPos=ElevatorUtils.getLeftClosePoint(ELEVATOR_NORMAL), blendType='easeOut'), LerpPosInterval(self.rightDoorOut, ElevatorData[ELEVATOR_NORMAL]['closeTime'], Point3(0, 0, 0), startPos=ElevatorUtils.getRightClosePoint(ELEVATOR_NORMAL), blendType='easeOut')), Wait(SUIT_HOLD_ELEVATOR_TIME), Func(camera.wrtReparentTo, render), Func(callback))
        track.start(ts)
        self.activeIntervals[name] = track

    def enterReservesJoining(self, ts = 0):
        self.__playReservesJoining(ts, self.uniqueName('reserves-joining'), self.__handleReserveJoinDone)
        return None

    def __handleReserveJoinDone(self):
        self.joiningReserves = []
        self.elevatorOutOpen = 1
        self.d_reserveJoinDone()

    def exitReservesJoining(self):
        self.__finishInterval(self.uniqueName('reserves-joining'))
        return None

    def enterResting(self, ts = 0):
        base.playMusic(self.waitMusic, looping=1, volume=0.7)
        self.__closeInElevator()

    def exitResting(self):
        self.waitMusic.stop()

    def enterReward(self, ts = 0):
        base.localAvatar.b_setParent(ToontownGlobals.SPHidden)
        request = {'loader': ZoneUtil.getBranchLoaderName(self.extZoneId),
         'where': ZoneUtil.getToonWhereName(self.extZoneId),
         'how': 'elevatorIn',
         'hoodId': ZoneUtil.getHoodId(self.extZoneId),
         'zoneId': self.extZoneId,
         'shardId': None,
         'avId': -1,
         'bldgDoId': self.distBldgDoId}
        messenger.send('DSIDoneEvent', [request])
        return

    def exitReward(self):
        return None
