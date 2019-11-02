from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from pandac.PandaModules import *
from otp.avatar import Avatar
from toontown.hood import ZoneUtil
from toontown.launcher import DownloadForceAcknowledge
from toontown.safezone.SafeZoneLoader import SafeZoneLoader
from toontown.safezone.OZPlayground import OZPlayground
from direct.actor import Actor
from direct.interval.IntervalGlobal import *
import random
from toontown.distributed import DelayDelete
from direct.distributed.ClockDelta import *
from otp.otpbase import OTPGlobals
import copy
from toontown.effects import Bubbles
import random
if (__debug__):
    import pdb

class OZSafeZoneLoader(SafeZoneLoader):

    def __init__(self, hood, parentFSM, doneEvent):
        SafeZoneLoader.__init__(self, hood, parentFSM, doneEvent)
        self.musicFile = 'phase_6/audio/bgm/OZ_SZ.mid'
        self.activityMusicFile = 'phase_6/audio/bgm/GS_KartShop.mid'
        self.dnaFile = 'phase_6/dna/outdoor_zone_sz.dna'
        self.safeZoneStorageDNAFile = 'phase_6/dna/storage_OZ_sz.dna'
        self.__toonTracks = {}
        del self.fsm
        self.fsm = ClassicFSM.ClassicFSM('SafeZoneLoader', [State.State('start', self.enterStart, self.exitStart, ['quietZone', 'playground', 'toonInterior']),
         State.State('playground', self.enterPlayground, self.exitPlayground, ['quietZone', 'golfcourse']),
         State.State('toonInterior', self.enterToonInterior, self.exitToonInterior, ['quietZone']),
         State.State('quietZone', self.enterQuietZone, self.exitQuietZone, ['playground', 'toonInterior', 'golfcourse']),
         State.State('golfcourse', self.enterGolfCourse, self.exitGolfCourse, ['quietZone', 'playground']),
         State.State('final', self.enterFinal, self.exitFinal, ['start'])], 'start', 'final')

    def load(self):
        self.done = 0
        self.geyserTrack = None
        SafeZoneLoader.load(self)
        self.birdSound = map(base.loadSfx, ['phase_4/audio/sfx/SZ_TC_bird1.mp3', 'phase_4/audio/sfx/SZ_TC_bird2.mp3', 'phase_4/audio/sfx/SZ_TC_bird3.mp3'])
        self.underwaterSound = base.loadSfx('phase_4/audio/sfx/AV_ambient_water.mp3')
        self.swimSound = base.loadSfx('phase_4/audio/sfx/AV_swim_single_stroke.mp3')
        self.submergeSound = base.loadSfx('phase_5.5/audio/sfx/AV_jump_in_water.mp3')
        geyserPlacer = self.geom.find('**/geyser*')
        waterfallPlacer = self.geom.find('**/waterfall*')
        binMgr = CullBinManager.getGlobalPtr()
        binMgr.addBin('water', CullBinManager.BTFixed, 29)
        binMgr = CullBinManager.getGlobalPtr()
        self.water = self.geom.find('**/water1*')
        self.water.setTransparency(1)
        self.water.setColorScale(1.0, 1.0, 1.0, 1.0)
        self.water.setBin('water', 51, 1)
        pool = self.geom.find('**/pPlane5*')
        pool.setTransparency(1)
        pool.setColorScale(1.0, 1.0, 1.0, 1.0)
        pool.setBin('water', 50, 1)
        self.geyserModel = loader.loadModel('phase_6/models/golf/golf_geyser_model')
        self.geyserSound = loader.loadSfx('phase_6/audio/sfx/OZ_Geyser.mp3')
        self.geyserSoundInterval = SoundInterval(self.geyserSound, node=geyserPlacer, listenerNode=base.camera, seamlessLoop=False, volume=1.0, cutOff=120)
        self.geyserSoundNoToon = loader.loadSfx('phase_6/audio/sfx/OZ_Geyser_No_Toon.mp3')
        self.geyserSoundNoToonInterval = SoundInterval(self.geyserSoundNoToon, node=geyserPlacer, listenerNode=base.camera, seamlessLoop=False, volume=1.0, cutOff=120)
        if self.geyserModel:
            self.geyserActor = Actor.Actor(self.geyserModel)
            self.geyserActor.loadAnims({'idle': 'phase_6/models/golf/golf_geyser'})
            self.geyserActor.reparentTo(render)
            self.geyserActor.setPlayRate(8.6, 'idle')
            self.geyserActor.loop('idle')
            self.geyserActor.setDepthWrite(0)
            self.geyserActor.setTwoSided(True, 11)
            self.geyserActor.setColorScale(1.0, 1.0, 1.0, 1.0)
            self.geyserActor.setBin('fixed', 0)
            mesh = self.geyserActor.find('**/mesh_tide1')
            joint = self.geyserActor.find('**/uvj_WakeWhiteTide1')
            mesh.setTexProjector(mesh.findTextureStage('default'), joint, self.geyserActor)
            self.geyserActor.setPos(geyserPlacer.getPos())
            self.geyserActor.setZ(geyserPlacer.getZ() - 100.0)
            self.geyserPos = geyserPlacer.getPos()
            self.geyserPlacer = geyserPlacer
            self.startGeyser()
            base.sfxPlayer.setCutoffDistance(160)
            self.geyserPoolSfx = loader.loadSfx('phase_6/audio/sfx/OZ_Geyser_BuildUp_Loop.wav')
            self.geyserPoolSoundInterval = SoundInterval(self.geyserPoolSfx, node=self.geyserPlacer, listenerNode=base.camera, seamlessLoop=True, volume=1.0, cutOff=120)
            self.geyserPoolSoundInterval.loop()
            self.bubbles = Bubbles.Bubbles(self.geyserPlacer, render)
            self.bubbles.renderParent.setDepthWrite(0)
            self.bubbles.start()
        self.collBase = render.attachNewNode('collisionBase')
        self.geyserCollSphere = CollisionSphere(0, 0, 0, 7.5)
        self.geyserCollSphere.setTangible(1)
        self.geyserCollNode = CollisionNode('barrelSphere')
        self.geyserCollNode.setIntoCollideMask(OTPGlobals.WallBitmask)
        self.geyserCollNode.addSolid(self.geyserCollSphere)
        self.geyserNodePath = self.collBase.attachNewNode(self.geyserCollNode)
        self.geyserNodePath.setPos(self.geyserPos[0], self.geyserPos[1], self.geyserPos[2] - 100.0)
        self.waterfallModel = loader.loadModel('phase_6/models/golf/golf_waterfall_model')
        if self.waterfallModel:
            self.waterfallActor = Actor.Actor(self.waterfallModel)
            self.waterfallActor.loadAnims({'idle': 'phase_6/models/golf/golf_waterfall'})
            self.waterfallActor.reparentTo(render)
            self.waterfallActor.setPlayRate(3.5, 'idle')
            self.waterfallActor.loop('idle')
            mesh = self.waterfallActor.find('**/mesh_tide1')
            joint = self.waterfallActor.find('**/uvj_WakeWhiteTide1')
            mesh.setTexProjector(mesh.findTextureStage('default'), joint, self.waterfallActor)
        self.waterfallActor.setPos(waterfallPlacer.getPos())
        self.accept('clientLogout', self._handleLogout)
        return

    def exit(self):
        self.clearToonTracks()
        SafeZoneLoader.exit(self)
        self.ignore('clientLogout')

    def startGeyser(self, task = None):
        if hasattr(base.cr, 'DTimer') and base.cr.DTimer:
            self.geyserCycleTime = 20.0
            useTime = base.cr.DTimer.getTime()
            timeToNextGeyser = 20.0 - useTime % 20.0
            taskMgr.doMethodLater(timeToNextGeyser, self.doGeyser, 'geyser Task')
        else:
            taskMgr.doMethodLater(5.0, self.startGeyser, 'start geyser Task')

    def doGeyser(self, task = None):
        if not self.done:
            self.setGeyserAnim()
            useTime = base.cr.DTimer.getTime()
            timeToNextGeyser = 20.0 - useTime % 20.0
            taskMgr.doMethodLater(timeToNextGeyser, self.doGeyser, 'geyser Task')
        return task.done

    def restoreLocal(self, task = None):
        place = base.cr.playGame.getPlace()
        if place:
            place.fsm.request('walk')
        base.localAvatar.setTeleportAvailable(1)
        base.localAvatar.collisionsOn()
        base.localAvatar.dropShadow.show()

    def restoreRemote(self, remoteAv, task = None):
        if remoteAv in Avatar.Avatar.ActiveAvatars:
            remoteAv.startSmooth()
            remoteAv.dropShadow.show()

    def setGeyserAnim(self, task = None):
        if self.done:
            return
        maxSize = 0.4 * random.random() + 0.75
        time = 1.0
        self.geyserTrack = Sequence()
        upPos = Vec3(self.geyserPos[0], self.geyserPos[1], self.geyserPos[2])
        downPos = Vec3(self.geyserPos[0], self.geyserPos[1], self.geyserPos[2] - 8.0)
        avList = copy.copy(Avatar.Avatar.ActiveAvatars)
        avList.append(base.localAvatar)
        playSound = 0
        for av in avList:
            distance = self.geyserPlacer.getDistance(av)
            if distance < 7.0:
                place = base.cr.playGame.getPlace()
                local = 0
                avPos = av.getPos()
                upToon = Vec3(avPos[0], avPos[1], maxSize * self.geyserPos[2] + 40.0)
                midToon = Vec3(avPos[0], avPos[1], maxSize * self.geyserPos[2] + 30.0)
                downToon = Vec3(avPos[0], avPos[1], self.geyserPos[2])
                returnPoints = [(7, 7),
                 (8, 0),
                 (-8, 3),
                 (-7, 7),
                 (3, -7),
                 (0, 8),
                 (-10, 0),
                 (8, -3),
                 (5, 8),
                 (-8, 5),
                 (-1, 7)]
                pick = int((float(av.doId) - 11.0) / 13.0 % len(returnPoints))
                returnChoice = returnPoints[pick]
                toonReturn = Vec3(self.geyserPos[0] + returnChoice[0], self.geyserPos[1] + returnChoice[1], self.geyserPos[2] - 1.5)
                topTrack = Sequence()
                av.dropShadow.hide()
                playSound = 1
                if av == base.localAvatar:
                    base.cr.playGame.getPlace().setState('fishing')
                    base.localAvatar.setTeleportAvailable(0)
                    base.localAvatar.collisionsOff()
                    local = 1
                else:
                    topTrack.delayDeletes = [DelayDelete.DelayDelete(av, 'OZSafeZoneLoader.setGeyserAnim')]
                    av.stopSmooth()
                animTrack = Parallel()
                toonTrack = Sequence()
                toonTrack.append(Wait(0.5))
                animTrack.append(ActorInterval(av, 'jump-idle', loop=1, endTime=11.5 * time))
                animTrack.append(ActorInterval(av, 'neutral', loop=0, endTime=0.25 * time))
                holder = render.attachNewNode('toon hold')
                base.holder = holder
                toonPos = av.getPos(render)
                toonHpr = av.getHpr(render)
                print 'av Pos %s' % av.getPos()
                base.toonPos = toonPos
                holder.setPos(toonPos)
                av.reparentTo(holder)
                av.setPos(0, 0, 0)
                lookAt = 180
                toonH = (lookAt + toonHpr[0]) % 360
                newHpr = Vec3(toonH, toonHpr[1], toonHpr[2])
                if toonH < 180:
                    lookIn = Vec3(0 + lookAt, -30, 0)
                else:
                    lookIn = Vec3(360 + lookAt, -30, 0)
                print 'Camera Hprs toon %s; lookIn %s; final %s' % (newHpr, lookIn, lookIn - newHpr)
                if local == 1:
                    camPosOriginal = camera.getPos()
                    camHprOriginal = camera.getHpr()
                    camParentOriginal = camera.getParent()
                    cameraPivot = holder.attachNewNode('camera pivot')
                    chooseHeading = random.choice([-10.0, 15.0, 40.0])
                    cameraPivot.setHpr(chooseHeading, -20.0, 0.0)
                    cameraArm = cameraPivot.attachNewNode('camera arm')
                    cameraArm.setPos(0.0, -23.0, 3.0)
                    camPosStart = Point3(0.0, 0.0, 0.0)
                    camHprStart = Vec3(0.0, 0.0, 0.0)
                    self.changeCamera(cameraArm, camPosStart, camHprStart)
                    cameraTrack = Sequence()
                    cameraTrack.append(Wait(11.0 * time))
                    cameraTrack.append(Func(self.changeCamera, camParentOriginal, camPosOriginal, camHprOriginal))
                    cameraTrack.start()
                moveTrack = Sequence()
                moveTrack.append(Wait(0.5))
                moveTrack.append(LerpPosInterval(holder, 3.0 * time, pos=upToon, startPos=downToon, blendType='easeOut'))
                moveTrack.append(LerpPosInterval(holder, 2.0 * time, pos=midToon, startPos=upToon, blendType='easeInOut'))
                moveTrack.append(LerpPosInterval(holder, 1.0 * time, pos=upToon, startPos=midToon, blendType='easeInOut'))
                moveTrack.append(LerpPosInterval(holder, 2.0 * time, pos=midToon, startPos=upToon, blendType='easeInOut'))
                moveTrack.append(LerpPosInterval(holder, 1.0 * time, pos=upToon, startPos=midToon, blendType='easeInOut'))
                moveTrack.append(LerpPosInterval(holder, 2.5 * time, pos=toonReturn, startPos=upToon, blendType='easeIn'))
                animTrack.append(moveTrack)
                animTrack.append(toonTrack)
                topTrack.append(animTrack)
                topTrack.append(Func(av.setPos, toonReturn))
                topTrack.append(Func(av.reparentTo, render))
                topTrack.append(Func(holder.remove))
                if local == 1:
                    topTrack.append(Func(self.restoreLocal))
                else:
                    topTrack.append(Func(self.restoreRemote, av))
                topTrack.append(Func(self.clearToonTrack, av.doId))
                self.storeToonTrack(av.doId, topTrack)
                topTrack.start()

        self.geyserTrack.append(Func(self.doPrint, 'geyser start'))
        self.geyserTrack.append(Func(self.geyserNodePath.setPos, self.geyserPos[0], self.geyserPos[1], self.geyserPos[2]))
        self.geyserTrack.append(Parallel(LerpScaleInterval(self.geyserActor, 2.0 * time, 0.75, 0.01), LerpPosInterval(self.geyserActor, 2.0 * time, pos=downPos, startPos=downPos)))
        self.geyserTrack.append(Parallel(LerpScaleInterval(self.geyserActor, time, maxSize, 0.75), LerpPosInterval(self.geyserActor, time, pos=upPos, startPos=downPos)))
        self.geyserTrack.append(Parallel(LerpScaleInterval(self.geyserActor, 2.0 * time, 0.75, maxSize), LerpPosInterval(self.geyserActor, 2.0 * time, pos=downPos, startPos=upPos)))
        self.geyserTrack.append(Parallel(LerpScaleInterval(self.geyserActor, time, maxSize, 0.75), LerpPosInterval(self.geyserActor, time, pos=upPos, startPos=downPos)))
        self.geyserTrack.append(Parallel(LerpScaleInterval(self.geyserActor, 2.0 * time, 0.75, maxSize), LerpPosInterval(self.geyserActor, 2.0 * time, pos=downPos, startPos=upPos)))
        self.geyserTrack.append(Parallel(LerpScaleInterval(self.geyserActor, time, maxSize, 0.75), LerpPosInterval(self.geyserActor, time, pos=upPos, startPos=downPos)))
        self.geyserTrack.append(Parallel(LerpScaleInterval(self.geyserActor, 4.0 * time, 0.01, maxSize), LerpPosInterval(self.geyserActor, 4.0 * time, pos=downPos, startPos=upPos)))
        self.geyserTrack.append(Func(self.geyserNodePath.setPos, self.geyserPos[0], self.geyserPos[1], self.geyserPos[2] - 100.0))
        self.geyserTrack.append(Func(self.doPrint, 'geyser end'))
        self.geyserTrack.start()
        if playSound:
            self.geyserSoundInterval.start()
        else:
            self.geyserSoundNoToonInterval.start()

    def changeCamera(self, newParent, newPos, newHpr):
        camera.reparentTo(newParent)
        camera.setPosHpr(newPos, newHpr)

    def doPrint(self, thing):
        return 0
        print thing

    def unload(self):
        del self.birdSound
        SafeZoneLoader.unload(self)
        self.done = 1
        self.collBase.remove()
        if self.geyserTrack:
            self.geyserTrack.finish()
        self.geyserTrack = None
        self.geyserActor.cleanup()
        self.geyserModel.remove()
        self.waterfallActor.cleanup()
        self.waterfallModel.remove()
        self.bubbles.destroy()
        del self.bubbles
        self.geyserPoolSoundInterval.finish()
        self.geyserPoolSfx.stop()
        self.geyserPoolSfx = None
        self.geyserPoolSoundInterval = None
        self.geyserSoundInterval.finish()
        self.geyserSound.stop()
        self.geyserSoundInterval = None
        self.geyserSound = None
        self.geyserSoundNoToonInterval.finish()
        self.geyserSoundNoToon.stop()
        self.geyserSoundNoToonInterval = None
        self.geyserSoundNoToon = None
        return

    def enterPlayground(self, requestStatus):
        self.playgroundClass = OZPlayground
        SafeZoneLoader.enterPlayground(self, requestStatus)

    def exitPlayground(self):
        taskMgr.remove('titleText')
        self.hood.hideTitleText()
        SafeZoneLoader.exitPlayground(self)
        self.playgroundClass = None
        return

    def handlePlaygroundDone(self):
        status = self.place.doneStatus
        self.doneStatus = status
        messenger.send(self.doneEvent)

    def enteringARace(self, status):
        if not status['where'] == 'golfcourse':
            return 0
        if ZoneUtil.isDynamicZone(status['zoneId']):
            return status['hoodId'] == self.hood.hoodId
        else:
            return ZoneUtil.getHoodId(status['zoneId']) == self.hood.hoodId

    def enteringAGolfCourse(self, status):
        if not status['where'] == 'golfcourse':
            return 0
        if ZoneUtil.isDynamicZone(status['zoneId']):
            return status['hoodId'] == self.hood.hoodId
        else:
            return ZoneUtil.getHoodId(status['zoneId']) == self.hood.hoodId

    def enterGolfCourse(self, requestStatus):
        if requestStatus.has_key('curseId'):
            self.golfCourseId = requestStatus['courseId']
        else:
            self.golfCourseId = 0
        self.accept('raceOver', self.handleRaceOver)
        self.accept('leavingGolf', self.handleLeftGolf)
        base.transitions.irisOut(t=0.2)

    def exitGolfCourse(self):
        del self.golfCourseId

    def handleRaceOver(self):
        print 'you done!!'

    def handleLeftGolf(self):
        req = {'loader': 'safeZoneLoader',
         'where': 'playground',
         'how': 'teleportIn',
         'zoneId': 6000,
         'hoodId': 6000,
         'shardId': None}
        self.fsm.request('quietZone', [req])
        return

    def _handleLogout(self):
        self.clearToonTracks()

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
