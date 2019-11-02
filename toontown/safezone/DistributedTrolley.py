from pandac.PandaModules import *
from direct.distributed.ClockDelta import *
from direct.task.Task import Task
from direct.interval.IntervalGlobal import *
from TrolleyConstants import *
from toontown.toonbase import ToontownGlobals
from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from toontown.distributed import DelayDelete
from direct.task.Task import Task
from toontown.hood import ZoneUtil
from toontown.toontowngui import TeaserPanel

class DistributedTrolley(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedTrolley')

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        self.localToonOnBoard = 0
        self.trolleyCountdownTime = base.config.GetFloat('trolley-countdown-time', TROLLEY_COUNTDOWN_TIME)
        self.fsm = ClassicFSM.ClassicFSM('DistributedTrolley', [State.State('off', self.enterOff, self.exitOff, ['entering',
          'waitEmpty',
          'waitCountdown',
          'leaving']),
         State.State('entering', self.enterEntering, self.exitEntering, ['waitEmpty']),
         State.State('waitEmpty', self.enterWaitEmpty, self.exitWaitEmpty, ['waitCountdown']),
         State.State('waitCountdown', self.enterWaitCountdown, self.exitWaitCountdown, ['waitEmpty', 'leaving']),
         State.State('leaving', self.enterLeaving, self.exitLeaving, ['entering'])], 'off', 'off')
        self.fsm.enterInitialState()
        self.trolleyAwaySfx = base.loadSfx('phase_4/audio/sfx/SZ_trolley_away.mp3')
        self.trolleyBellSfx = base.loadSfx('phase_4/audio/sfx/SZ_trolley_bell.mp3')
        self.__toonTracks = {}

    def generate(self):
        DistributedObject.DistributedObject.generate(self)
        self.loader = self.cr.playGame.hood.loader
        self.trolleyStation = self.loader.geom.find('**/*trolley_station*')
        self.trolleyCar = self.trolleyStation.find('**/trolley_car')
        self.trolleySphereNode = self.trolleyStation.find('**/trolley_sphere').node()
        exitFog = Fog('TrolleyExitFog')
        exitFog.setColor(0.0, 0.0, 0.0)
        exitFog.setLinearOnsetPoint(30.0, 14.0, 0.0)
        exitFog.setLinearOpaquePoint(37.0, 14.0, 0.0)
        exitFog.setLinearFallback(70.0, 999.0, 1000.0)
        self.trolleyExitFog = self.trolleyStation.attachNewNode(exitFog)
        self.trolleyExitFogNode = exitFog
        enterFog = Fog('TrolleyEnterFog')
        enterFog.setColor(0.0, 0.0, 0.0)
        enterFog.setLinearOnsetPoint(0.0, 14.0, 0.0)
        enterFog.setLinearOpaquePoint(-7.0, 14.0, 0.0)
        enterFog.setLinearFallback(70.0, 999.0, 1000.0)
        self.trolleyEnterFog = self.trolleyStation.attachNewNode(enterFog)
        self.trolleyEnterFogNode = enterFog
        self.trolleyCar.setFogOff()
        self.keys = self.trolleyCar.findAllMatches('**/key')
        self.numKeys = self.keys.getNumPaths()
        self.keyInit = []
        self.keyRef = []
        for i in range(self.numKeys):
            key = self.keys[i]
            key.setTwoSided(1)
            ref = self.trolleyCar.attachNewNode('key' + `i` + 'ref')
            ref.iPosHpr(key)
            self.keyRef.append(ref)
            self.keyInit.append(key.getTransform())

        self.frontWheels = self.trolleyCar.findAllMatches('**/front_wheels')
        self.numFrontWheels = self.frontWheels.getNumPaths()
        self.frontWheelInit = []
        self.frontWheelRef = []
        for i in range(self.numFrontWheels):
            wheel = self.frontWheels[i]
            ref = self.trolleyCar.attachNewNode('frontWheel' + `i` + 'ref')
            ref.iPosHpr(wheel)
            self.frontWheelRef.append(ref)
            self.frontWheelInit.append(wheel.getTransform())

        self.backWheels = self.trolleyCar.findAllMatches('**/back_wheels')
        self.numBackWheels = self.backWheels.getNumPaths()
        self.backWheelInit = []
        self.backWheelRef = []
        for i in range(self.numBackWheels):
            wheel = self.backWheels[i]
            ref = self.trolleyCar.attachNewNode('backWheel' + `i` + 'ref')
            ref.iPosHpr(wheel)
            self.backWheelRef.append(ref)
            self.backWheelInit.append(wheel.getTransform())

        trolleyAnimationReset = Func(self.resetAnimation)
        trolleyEnterStartPos = Point3(-20, 14, -1)
        trolleyEnterEndPos = Point3(15, 14, -1)
        trolleyEnterPos = Sequence(name='TrolleyEnterPos')
        if base.wantFog:
            trolleyEnterPos.append(Func(self.trolleyCar.setFog, self.trolleyEnterFogNode))
        trolleyEnterPos.append(self.trolleyCar.posInterval(TROLLEY_ENTER_TIME, trolleyEnterEndPos, startPos=trolleyEnterStartPos, blendType='easeOut'))
        if base.wantFog:
            trolleyEnterPos.append(Func(self.trolleyCar.setFogOff))
        trolleyEnterTrack = Sequence(trolleyAnimationReset, trolleyEnterPos, name='trolleyEnter')
        keyAngle = round(TROLLEY_ENTER_TIME) * 360
        dist = Vec3(trolleyEnterEndPos - trolleyEnterStartPos).length()
        wheelAngle = dist / (2.0 * math.pi * 0.95) * 360
        trolleyEnterAnimateInterval = LerpFunctionInterval(self.animateTrolley, duration=TROLLEY_ENTER_TIME, blendType='easeOut', extraArgs=[keyAngle, wheelAngle], name='TrolleyAnimate')
        trolleyEnterSoundTrack = SoundInterval(self.trolleyAwaySfx, node=self.trolleyCar)
        self.trolleyEnterTrack = Parallel(trolleyEnterTrack, trolleyEnterAnimateInterval, trolleyEnterSoundTrack)
        trolleyExitStartPos = Point3(15, 14, -1)
        trolleyExitEndPos = Point3(50, 14, -1)
        trolleyExitPos = Sequence(name='TrolleyExitPos')
        if base.wantFog:
            trolleyExitPos.append(Func(self.trolleyCar.setFog, self.trolleyExitFogNode))
        trolleyExitPos.append(self.trolleyCar.posInterval(TROLLEY_EXIT_TIME, trolleyExitEndPos, startPos=trolleyExitStartPos, blendType='easeIn'))
        if base.wantFog:
            trolleyExitPos.append(Func(self.trolleyCar.setFogOff))
        trolleyExitBellInterval = SoundInterval(self.trolleyBellSfx, node=self.trolleyCar)
        trolleyExitAwayInterval = SoundInterval(self.trolleyAwaySfx, node=self.trolleyCar)
        keyAngle = round(TROLLEY_EXIT_TIME) * 360
        dist = Vec3(trolleyExitEndPos - trolleyExitStartPos).length()
        wheelAngle = dist / (2.0 * math.pi * 0.95) * 360
        trolleyExitAnimateInterval = LerpFunctionInterval(self.animateTrolley, duration=TROLLEY_EXIT_TIME, blendType='easeIn', extraArgs=[keyAngle, wheelAngle], name='TrolleyAnimate')
        self.trolleyExitTrack = Parallel(trolleyExitPos, trolleyExitBellInterval, trolleyExitAwayInterval, trolleyExitAnimateInterval, name=self.uniqueName('trolleyExit'))

    def disable(self):
        DistributedObject.DistributedObject.disable(self)
        self.fsm.request('off')
        self.clearToonTracks()
        self.trolleyExitFog.removeNode()
        del self.trolleyExitFog
        del self.trolleyExitFogNode
        self.trolleyEnterFog.removeNode()
        del self.trolleyEnterFog
        del self.trolleyEnterFogNode
        del self.loader
        self.trolleyEnterTrack.pause()
        self.trolleyEnterTrack = None
        del self.trolleyEnterTrack
        self.trolleyExitTrack.pause()
        self.trolleyExitTrack = None
        del self.trolleyExitTrack
        del self.trolleyStation
        del self.trolleyCar
        del self.keys
        del self.numKeys
        del self.keyInit
        del self.keyRef
        del self.frontWheels
        del self.numFrontWheels
        del self.frontWheelInit
        del self.frontWheelRef
        del self.backWheels
        del self.numBackWheels
        del self.backWheelInit
        del self.backWheelRef
        return

    def delete(self):
        del self.trolleyAwaySfx
        del self.trolleyBellSfx
        DistributedObject.DistributedObject.delete(self)
        del self.fsm

    def setState(self, state, timestamp):
        self.fsm.request(state, [globalClockDelta.localElapsedTime(timestamp)])

    def allowedToEnter(self):
        if hasattr(base, 'ttAccess') and base.ttAccess and base.ttAccess.canAccess():
            return True
        return False

    def handleOkTeaser(self):
        self.dialog.destroy()
        del self.dialog
        place = base.cr.playGame.getPlace()
        if place:
            place.fsm.request('walk')

    def handleEnterTrolleySphere(self, collEntry):
        self.notify.debug('Entering Trolley Sphere....')
        if base.localAvatar.getPos(render).getZ() < self.trolleyCar.getPos(render).getZ():
            return
        if self.allowedToEnter():
            self.loader.place.detectedTrolleyCollision()
        else:
            place = base.cr.playGame.getPlace()
            if place:
                place.fsm.request('stopped')
            self.dialog = TeaserPanel.TeaserPanel(pageName='minigames', doneFunc=self.handleOkTeaser)

    def handleEnterTrolley(self):
        toon = base.localAvatar
        self.sendUpdate('requestBoard', [])

    def fillSlot0(self, avId):
        self.fillSlot(0, avId)

    def fillSlot1(self, avId):
        self.fillSlot(1, avId)

    def fillSlot2(self, avId):
        self.fillSlot(2, avId)

    def fillSlot3(self, avId):
        self.fillSlot(3, avId)

    def fillSlot(self, index, avId):
        if avId == 0:
            pass
        else:
            if avId == base.localAvatar.getDoId():
                if not (self.fsm.getCurrentState().getName() == 'waitEmpty' or self.fsm.getCurrentState().getName() == 'waitCountdown'):
                    self.notify.warning("Can't board the trolley while in the '%s' state." % self.fsm.getCurrentState().getName())
                    self.loader.place.fsm.request('walk')
                    return
                if hasattr(self.loader.place, 'trolley') and self.loader.place.trolley:
                    self.loader.place.trolley.fsm.request('boarding', [self.trolleyCar])
                    self.localToonOnBoard = 1
                    self.loader.place.trolley.fsm.request('boarded')
                else:
                    self.notify.warning("Can't board the trolley because it doesn't exist")
                    self.sendUpdate('requestExit')
            if self.cr.doId2do.has_key(avId):
                toon = self.cr.doId2do[avId]
                toon.stopSmooth()
                toon.wrtReparentTo(self.trolleyCar)
                toon.setAnimState('run', 1.0)
                toon.headsUp(-5, -4.5 + index * 3, 1.4)
                sitStartDuration = toon.getDuration('sit-start')
                track = Sequence(LerpPosInterval(toon, TOON_BOARD_TIME * 0.75, Point3(-5, -4.5 + index * 3, 1.4)), LerpHprInterval(toon, TOON_BOARD_TIME * 0.25, Point3(90, 0, 0)), Parallel(Sequence(Wait(sitStartDuration * 0.25), LerpPosInterval(toon, sitStartDuration * 0.25, Point3(-3.9, -4.5 + index * 3, 3.0))), ActorInterval(toon, 'sit-start')), Func(toon.setAnimState, 'Sit', 1.0), Func(self.clearToonTrack, avId), name=toon.uniqueName('fillTrolley'), autoPause=1)
                track.delayDelete = DelayDelete.DelayDelete(toon, 'Trolley.fillSlot')
                self.storeToonTrack(avId, track)
                track.start()
            else:
                DistributedTrolley.notify.warning('toon: ' + str(avId) + " doesn't exist, and" + ' cannot board the trolley!')

    def emptySlot0(self, avId, timestamp):
        self.emptySlot(0, avId, timestamp)

    def emptySlot1(self, avId, timestamp):
        self.emptySlot(1, avId, timestamp)

    def emptySlot2(self, avId, timestamp):
        self.emptySlot(2, avId, timestamp)

    def emptySlot3(self, avId, timestamp):
        self.emptySlot(3, avId, timestamp)

    def notifyToonOffTrolley(self, toon):
        toon.setAnimState('neutral', 1.0)
        if toon == base.localAvatar:
            if hasattr(self.loader.place, 'trolley') and self.loader.place.trolley:
                self.loader.place.trolley.handleOffTrolley()
            self.localToonOnBoard = 0
        else:
            toon.startSmooth()

    def emptySlot(self, index, avId, timestamp):
        if avId == 0:
            pass
        elif self.cr.doId2do.has_key(avId):
            toon = self.cr.doId2do[avId]
            toon.setHpr(self.trolleyCar, 90, 0, 0)
            toon.wrtReparentTo(render)
            toon.stopSmooth()
            sitStartDuration = toon.getDuration('sit-start')
            track = Sequence(Parallel(ActorInterval(toon, 'sit-start', startTime=sitStartDuration, endTime=0.0), Sequence(Wait(sitStartDuration * 0.5), LerpPosInterval(toon, sitStartDuration * 0.25, Point3(-5, -4.5 + index * 3, 1.4), other=self.trolleyCar))), Func(toon.setAnimState, 'run', 1.0), LerpPosInterval(toon, TOON_EXIT_TIME, Point3(21 - index * 3, -5, 0.02), other=self.trolleyStation), Func(self.notifyToonOffTrolley, toon), Func(self.clearToonTrack, avId), name=toon.uniqueName('emptyTrolley'), autoPause=1)
            track.delayDelete = DelayDelete.DelayDelete(toon, 'Trolley.emptySlot')
            self.storeToonTrack(avId, track)
            track.start()
            if avId == base.localAvatar.getDoId() and hasattr(self.loader.place, 'trolley') and self.loader.place.trolley:
                self.loader.place.trolley.fsm.request('exiting')
        else:
            DistributedTrolley.notify.warning('toon: ' + str(avId) + " doesn't exist, and" + ' cannot exit the trolley!')

    def rejectBoard(self, avId):
        self.loader.place.trolley.handleRejectBoard()

    def setMinigameZone(self, zoneId, minigameId):
        self.localToonOnBoard = 0
        messenger.send('playMinigame', [zoneId, minigameId])

    def __enableCollisions(self):
        self.accept('entertrolley_sphere', self.handleEnterTrolleySphere)
        self.accept('enterTrolleyOK', self.handleEnterTrolley)
        self.trolleySphereNode.setCollideMask(ToontownGlobals.WallBitmask)

    def __disableCollisions(self):
        self.ignore('entertrolley_sphere')
        self.ignore('enterTrolleyOK')
        self.trolleySphereNode.setCollideMask(BitMask32(0))

    def enterOff(self):
        return None

    def exitOff(self):
        return None

    def enterEntering(self, ts):
        self.trolleyEnterTrack.start(ts)

    def exitEntering(self):
        self.trolleyEnterTrack.finish()

    def enterWaitEmpty(self, ts):
        self.__enableCollisions()

    def exitWaitEmpty(self):
        self.__disableCollisions()

    def enterWaitCountdown(self, ts):
        self.__enableCollisions()
        self.accept('trolleyExitButton', self.handleExitButton)
        self.clockNode = TextNode('trolleyClock')
        self.clockNode.setFont(ToontownGlobals.getSignFont())
        self.clockNode.setAlign(TextNode.ACenter)
        self.clockNode.setTextColor(0.9, 0.1, 0.1, 1)
        self.clockNode.setText('10')
        self.clock = self.trolleyStation.attachNewNode(self.clockNode)
        self.clock.setBillboardAxis()
        self.clock.setPosHprScale(15.86, 13.82, 11.68, -0.0, 0.0, 0.0, 3.02, 3.02, 3.02)
        if ts < self.trolleyCountdownTime:
            self.countdown(self.trolleyCountdownTime - ts)

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
        taskMgr.remove('trolleyTimerTask')
        return taskMgr.add(countdownTask, 'trolleyTimerTask')

    def handleExitButton(self):
        self.sendUpdate('requestExit')

    def exitWaitCountdown(self):
        self.__disableCollisions()
        self.ignore('trolleyExitButton')
        taskMgr.remove('trolleyTimerTask')
        self.clock.removeNode()
        del self.clock
        del self.clockNode

    def enterLeaving(self, ts):
        self.trolleyExitTrack.start(ts)
        if self.localToonOnBoard:
            if hasattr(self.loader.place, 'trolley') and self.loader.place.trolley:
                self.loader.place.trolley.fsm.request('trolleyLeaving')

    def exitLeaving(self):
        self.trolleyExitTrack.finish()

    def animateTrolley(self, t, keyAngle, wheelAngle):
        for i in range(self.numKeys):
            key = self.keys[i]
            ref = self.keyRef[i]
            key.setH(ref, t * keyAngle)

        for i in range(self.numFrontWheels):
            frontWheel = self.frontWheels[i]
            ref = self.frontWheelRef[i]
            frontWheel.setH(ref, t * wheelAngle)

        for i in range(self.numBackWheels):
            backWheel = self.backWheels[i]
            ref = self.backWheelRef[i]
            backWheel.setH(ref, t * wheelAngle)

    def resetAnimation(self):
        for i in range(self.numKeys):
            self.keys[i].setTransform(self.keyInit[i])

        for i in range(self.numFrontWheels):
            self.frontWheels[i].setTransform(self.frontWheelInit[i])

        for i in range(self.numBackWheels):
            self.backWheels[i].setTransform(self.backWheelInit[i])

    def getStareAtNodeAndOffset(self):
        return (self.trolleyCar, Point3(0, 0, 4))

    def storeToonTrack(self, avId, track):
        self.clearToonTrack(avId)
        self.__toonTracks[avId] = track

    def clearToonTrack(self, avId):
        oldTrack = self.__toonTracks.get(avId)
        if oldTrack:
            oldTrack.pause()
            DelayDelete.cleanupDelayDeletes(oldTrack)
            del self.__toonTracks[avId]

    def clearToonTracks(self):
        keyList = []
        for key in self.__toonTracks:
            keyList.append(key)

        for key in keyList:
            if self.__toonTracks.has_key(key):
                self.clearToonTrack(key)
