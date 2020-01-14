from pandac.PandaModules import *
from direct.distributed.ClockDelta import *
from direct.task.Task import Task
from direct.interval.IntervalGlobal import *
from .TrolleyConstants import *
from toontown.golf import GolfGlobals
from toontown.toonbase import ToontownGlobals
from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from toontown.distributed import DelayDelete
from direct.task.Task import Task
from direct.showbase import PythonUtil
from toontown.toontowngui import TeaserPanel
from toontown.toon import ToonDNA
from toontown.hood import ZoneUtil

class DistributedGolfKart(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedGolfKart')
    SeatOffsets = ((0.5, -0.5, 0),
     (-0.5, -0.5, 0),
     (0.5, 0.5, 0),
     (-0.5, 0.5, 0))
    JumpOutOffsets = ((3, 5, 0),
     (1.5, 4, 0),
     (-1.5, 4, 0),
     (-3, 4, 0))
    KART_ENTER_TIME = 400

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
        self.trolleyAwaySfx = base.loader.loadSfx('phase_4/audio/sfx/SZ_trolley_away.ogg')
        self.trolleyBellSfx = base.loader.loadSfx('phase_4/audio/sfx/SZ_trolley_bell.ogg')
        self.__toonTracks = {}
        self.avIds = [0,
         0,
         0,
         0]
        self.kartModelPath = 'phase_6/models/golf/golf_cart3.bam'

    def generate(self):
        DistributedObject.DistributedObject.generate(self)
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
        trolleyExitBellInterval = SoundInterval(self.trolleyBellSfx, node=self.golfKart)
        trolleyExitAwayInterval = SoundInterval(self.trolleyAwaySfx, node=self.golfKart)

    def announceGenerate(self):
        DistributedObject.DistributedObject.announceGenerate(self)
        self.golfKartSphereNode = self.golfKart.attachNewNode(CollisionNode('golfkart_sphere_%d' % self.getDoId()))
        self.golfKartSphereNode.node().addSolid(CollisionSphere(0, 0, 0, 2))
        angle = self.startingHpr[0]
        angle -= 90
        radAngle = deg2Rad(angle)
        unitVec = Vec3(math.cos(radAngle), math.sin(radAngle), 0)
        unitVec *= 45.0
        self.endPos = self.startingPos + unitVec
        dist = Vec3(self.endPos - self.enteringPos).length()
        wheelAngle = dist / (4.8 * 1.4 * math.pi) * 360
        self.kartEnterAnimateInterval = Parallel(LerpHprInterval(self.wheels[0], 5.0, Vec3(self.wheels[0].getH(), wheelAngle, self.wheels[0].getR())), LerpHprInterval(self.wheels[1], 5.0, Vec3(self.wheels[1].getH(), wheelAngle, self.wheels[1].getR())), LerpHprInterval(self.wheels[2], 5.0, Vec3(self.wheels[2].getH(), wheelAngle, self.wheels[2].getR())), LerpHprInterval(self.wheels[3], 5.0, Vec3(self.wheels[3].getH(), wheelAngle, self.wheels[3].getR())), name='KartAnimate')
        trolleyExitTrack1 = Parallel(LerpPosInterval(self.golfKart, 5.0, self.endPos), self.kartEnterAnimateInterval, name='KartExitTrack')
        self.trolleyExitTrack = Sequence(trolleyExitTrack1, Func(self.hideSittingToons))
        self.trolleyEnterTrack = Sequence(LerpPosInterval(self.golfKart, 5.0, self.startingPos, startPos=self.enteringPos))

    def disable(self):
        DistributedObject.DistributedObject.disable(self)
        self.fsm.request('off')
        self.clearToonTracks()
        del self.wheels
        del self.numWheels
        del self.golfKartSphereNode
        self.notify.debug('Deleted self loader ' + str(self.getDoId()))
        del self.loader
        self.golfKart.removeNode()
        self.kart.removeNode()
        del self.kart
        del self.golfKart
        self.trolleyEnterTrack.pause()
        self.trolleyEnterTrack = None
        del self.kartEnterAnimateInterval
        del self.trolleyEnterTrack
        self.trolleyExitTrack.pause()
        self.trolleyExitTrack = None
        del self.trolleyExitTrack
        return

    def delete(self):
        self.notify.debug('Golf kart getting deleted: %s' % self.getDoId())
        del self.trolleyAwaySfx
        del self.trolleyBellSfx
        DistributedObject.DistributedObject.delete(self)
        del self.fsm

    def setState(self, state, timestamp):
        self.fsm.request(state, [globalClockDelta.localElapsedTime(timestamp)])

    def handleEnterTrolleySphere(self, collEntry):
        self.notify.debug('Entering Trolley Sphere....')
        self.loader.place.detectedTrolleyCollision()

    def allowedToEnter(self):
        if hasattr(base, 'ttAccess') and base.ttAccess and base.ttAccess.canAccess():
            return True
        return False

    def handleEnterGolfKartSphere(self, collEntry):
        self.notify.debug('Entering Golf Kart Sphere.... %s' % self.getDoId())
        if self.allowedToEnter():
            self.loader.place.detectedGolfKartCollision(self)
        else:
            place = base.cr.playGame.getPlace()
            if place:
                place.fsm.request('stopped')
            self.dialog = TeaserPanel.TeaserPanel(pageName='golf', doneFunc=self.handleOkTeaser)

    def handleOkTeaser(self):
        self.dialog.destroy()
        del self.dialog
        place = base.cr.playGame.getPlace()
        if place:
            place.fsm.request('walk')

    def handleEnterTrolley(self):
        toon = base.localAvatar
        self.sendUpdate('requestBoard', [])

    def handleEnterGolfKart(self):
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
        self.avIds[index] = avId
        if avId == 0:
            pass
        else:
            if avId == base.localAvatar.getDoId():
                self.loader.place.trolley.fsm.request('boarding', [self.golfKart])
                self.localToonOnBoard = 1
            if avId == base.localAvatar.getDoId():
                self.loader.place.trolley.fsm.request('boarded')
            if avId in self.cr.doId2do:
                toon = self.cr.doId2do[avId]
                toon.stopSmooth()
                toon.wrtReparentTo(self.golfKart)
                sitStartDuration = toon.getDuration('sit-start')
                jumpTrack = self.generateToonJumpTrack(toon, index)
                track = Sequence(jumpTrack, Func(toon.setAnimState, 'Sit', 1.0), Func(self.clearToonTrack, avId), name=toon.uniqueName('fillTrolley'), autoPause=1)
                track.delayDelete = DelayDelete.DelayDelete(toon, 'GolfKart.fillSlot')
                self.storeToonTrack(avId, track)
                track.start()
            else:
                self.notify.warning('toon: ' + str(avId) + " doesn't exist, and" + ' cannot board the trolley!')

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
            self.loader.place.trolley.handleOffTrolley()
            self.localToonOnBoard = 0
        else:
            toon.startSmooth()

    def emptySlot(self, index, avId, timestamp):
        if avId == 0:
            pass
        else:
            self.avIds[index] = 0
            if avId in self.cr.doId2do:
                toon = self.cr.doId2do[avId]
                toon.stopSmooth()
                sitStartDuration = toon.getDuration('sit-start')
                jumpOutTrack = self.generateToonReverseJumpTrack(toon, index)
                track = Sequence(jumpOutTrack, Func(self.notifyToonOffTrolley, toon), Func(self.clearToonTrack, avId), name=toon.uniqueName('emptyTrolley'), autoPause=1)
                track.delayDelete = DelayDelete.DelayDelete(toon, 'GolfKart.emptySlot')
                self.storeToonTrack(avId, track)
                track.start()
                if avId == base.localAvatar.getDoId():
                    self.loader.place.trolley.fsm.request('exiting')
            else:
                self.notify.warning('toon: ' + str(avId) + " doesn't exist, and" + ' cannot exit the trolley!')

    def rejectBoard(self, avId):
        self.loader.place.trolley.handleRejectBoard()

    def setMinigameZone(self, zoneId, minigameId):
        self.localToonOnBoard = 0
        messenger.send('playMinigame', [zoneId, minigameId])

    def setGolfZone(self, zoneId, courseId):
        self.localToonOnBoard = 0
        messenger.send('playGolf', [zoneId, courseId])

    def __enableCollisions(self):
        self.accept('entertrolley_sphere', self.handleEnterTrolleySphere)
        self.accept('enterTrolleyOK', self.handleEnterTrolley)
        self.accept('entergolfkart_sphere_%d' % self.getDoId(), self.handleEnterGolfKartSphere)
        self.accept('enterGolfKartOK_%d' % self.getDoId(), self.handleEnterGolfKart)
        self.golfKartSphereNode.setCollideMask(ToontownGlobals.WallBitmask)

    def __disableCollisions(self):
        self.ignore('entertrolley_sphere')
        self.ignore('enterTrolleyOK')
        self.ignore('entergolfkart_sphere_%d' % self.getDoId())
        self.ignore('enterTrolleyOK_%d' % self.getDoId())
        self.ignore('enterGolfKartOK_%d' % self.getDoId())
        self.golfKartSphereNode.setCollideMask(BitMask32(0))

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
        self.clock = self.golfKart.attachNewNode(self.clockNode)
        self.clock.setBillboardAxis()
        self.clock.setPosHprScale(0, -1, 7.0, -0.0, 0.0, 0.0, 2.0, 2.0, 2.0)
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
        taskMgr.remove(self.uniqueName('golfKartTimerTask'))
        return taskMgr.add(countdownTask, self.uniqueName('golfKartTimerTask'))

    def handleExitButton(self):
        self.sendUpdate('requestExit')

    def exitWaitCountdown(self):
        self.__disableCollisions()
        self.ignore('trolleyExitButton')
        taskMgr.remove(self.uniqueName('golfKartTimerTask'))
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

    def getStareAtNodeAndOffset(self):
        return (self.golfKart, Point3(0, 0, 4))

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

    def setGolfCourse(self, golfCourse):
        self.golfCourse = golfCourse

    def setPosHpr(self, x, y, z, h, p, r):
        self.startingPos = Vec3(x, y, z)
        self.enteringPos = Vec3(x, y, z - 10)
        self.startingHpr = Vec3(h, 0, 0)
        self.golfKart.setPosHpr(x, y, z, h, 0, 0)

    def setColor(self, r, g, b):
        kartBody = self.kart.find('**/main_body')
        kartBody.setColor(r / 255.0, g / 255.0, b / 255.0, 1)
        cartBase = self.kart.find('**/cart_base*')
        red = r / 255.0
        green = g / 255.0
        blue = b / 255.0
        if red >= green and red > blue:
            s = (red - blue) / float(red)
            v = red
            if green > blue:
                h = (green - blue) / (red - blue)
            else:
                h = (green - blue) / (red - green)
        elif green >= blue:
            s = (green - blue) / float(green)
            v = green
            if red > blue:
                h = 2 + (blue - red) / (green - blue)
            else:
                h = 2 + (blue - red) / (green - red)
        else:
            if red > green:
                s = (blue - green) / blue
                h = 4 + (red - green) / (blue - green)
            else:
                s = (blue - red) / blue
                h = 4 + (red - green) / (blue - red)
            v = blue
        if h < 0:
            h *= 60
            h += 360
            h /= 60
        s /= 3
        if s == 0:
            red = green = blue = v
        else:
            i = int(h)
            f = h - i
            p = v * (1 - s)
            q = v * (1 - s * f)
            t = v * (1 - s * (1 - f))
            if i == 0:
                red = v
                green = t
                blue = p
            elif i == 1:
                red = q
                green = v
                blue = p
            elif i == 2:
                red = p
                green = v
                blue = t
            elif i == 3:
                red = p
                green = q
                blue = v
            elif i == 4:
                red = t
                green = p
                blue = v
            elif i == 5:
                red = v
                green = p
                blue = q
        cartBase.setColorScale(red, green, blue, 1)

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

    def hideSittingToons(self):
        for avId in self.avIds:
            if avId:
                av = base.cr.doId2do.get(avId)
                if av:
                    av.hide()
