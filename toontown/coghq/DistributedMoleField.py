from pandac.PandaModules import *
from otp.level.BasicEntities import DistributedNodePathEntity
from direct.directnotify import DirectNotifyGlobal
from toontown.coghq import MoleHill
from toontown.coghq import MoleFieldBase
from direct.distributed.ClockDelta import globalClockDelta
from toontown.toonbase import ToontownTimer
from direct.gui.DirectGui import DGG, DirectFrame, DirectLabel
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from direct.task import Task
import random
from toontown.minigame import Trajectory
from direct.interval.IntervalGlobal import *
from toontown.battle import MovieUtil

class DistributedMoleField(DistributedNodePathEntity, MoleFieldBase.MoleFieldBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedMoleField')
    ScheduleTaskName = 'moleFieldScheduler'

    def __init__(self, cr):
        DistributedNodePathEntity.__init__(self, cr)
        self.gameStarted = False
        self.moleHills = []
        self.numMolesWhacked = 0
        self.timer = None
        self.frame2D = None
        self.isToonInRange = 0
        self.detectCount = 0
        self.cameraHold = None
        self.activeField = 1
        self.dimensionX = 0.0
        self.dimensionY = 0.0
        self.gameText = TTLocalizer.MolesInstruction
        self.winText = TTLocalizer.MolesFinished
        self.pityWinText = TTLocalizer.MolesPityWin
        self.restartedText = TTLocalizer.MolesRestarted
        self.toonHitTracks = {}
        self.hasRestarted = 0
        self.hasEntered = 0
        self.MolesWhackedTarget = 1000
        self.GameDuration = 1000
        return

    def disable(self):
        self.cleanupTimer()
        for ival in list(self.toonHitTracks.values()):
            ival.finish()

        self.toonHitTracks = {}
        DistributedNodePathEntity.disable(self)
        taskMgr.remove(self.detectName)
        self.ignoreAll()

    def delete(self):
        self.soundBomb = None
        self.soundBomb2 = None
        self.soundCog = None
        DistributedNodePathEntity.delete(self)
        self.stopScheduleTask()
        for mole in self.moleHills:
            mole.destroy()

        self.moleHills = []
        self.cleanupTimer()
        self.unloadGui()
        return

    def announceGenerate(self):
        DistributedNodePathEntity.announceGenerate(self)
        self.loadModel()
        self.loadGui()
        self.detectName = 'moleField %s' % self.doId
        taskMgr.doMethodLater(0.1, self.__detect, self.detectName)
        self.calcDimensions()
        self.notify.debug('announceGenerate doId=%d entId=%d' % (self.doId, self.entId))

    def setNumSquaresX(self, num):
        self.numSquaresX = num
        self.calcDimensions()

    def setNumSquaresY(self, num):
        self.numSquaresY = num
        self.calcDimensions()

    def setSpacingX(self, num):
        self.spacingX = num
        self.calcDimensions()

    def setSpacingY(self, num):
        self.spacingY = num
        self.calcDimensions()

    def calcDimensions(self):
        self.dimensionX = self.numSquaresX * self.spacingX
        self.dimensionY = self.numSquaresY * self.spacingY
        self.centerCenterNode()

    def loadModel(self):
        moleIndex = 0
        self.moleHills = []
        for indexY in range(self.numSquaresY):
            for indexX in range(self.numSquaresX):
                xPos = indexX * self.spacingX
                yPos = indexY * self.spacingY
                newMoleHill = MoleHill.MoleHill(xPos, yPos, 0, self, moleIndex)
                newMoleHill.reparentTo(self)
                self.moleHills.append(newMoleHill)
                moleIndex += 1

        self.numMoles = len(self.moleHills)
        self.centerNode = self.attachNewNode('center')
        self.centerCenterNode()
        self.soundBomb = base.loader.loadSfx('phase_12/audio/sfx/Mole_Surprise.ogg')
        self.soundBomb2 = base.loader.loadSfx('phase_3.5/audio/dial/AV_pig_howl.ogg')
        self.soundCog = base.loader.loadSfx('phase_12/audio/sfx/Mole_Stomp.ogg')
        self.soundUp = base.loader.loadSfx('phase_4/audio/sfx/MG_Tag_C.ogg')
        self.soundDown = base.loader.loadSfx('phase_4/audio/sfx/MG_cannon_whizz.ogg')
        upInterval = SoundInterval(self.soundUp, loop=0)
        downInterval = SoundInterval(self.soundDown, loop=0)
        self.soundIUpDown = Sequence(upInterval, downInterval)

    def centerCenterNode(self):
        self.centerNode.setPos(self.dimensionX * 0.5, self.dimensionY * 0.5, 0.0)

    def loadGui(self):
        self.frame2D = DirectFrame(scale=1.0, pos=(0.0, 0, 0.9), relief=DGG.FLAT, parent=aspect2d, frameSize=(-0.3,
         0.3,
         -0.05,
         0.05), frameColor=(0.737, 0.573, 0.345, 0.3))
        self.scoreLabel = DirectLabel(parent=self.frame2D, relief=None, pos=(0, 0, 0), scale=1.0, text='', text_font=ToontownGlobals.getSignFont(), text0_fg=(1, 1, 1, 1), text_scale=0.075, text_pos=(0, -0.02))
        self.updateGuiScore()
        self.frame2D.hide()
        return

    def unloadGui(self):
        self.frame2D.destroy()
        self.frame2D = None
        return

    def setGameStart(self, timestamp, molesWhackTarget, totalTime):
        self.GameDuration = totalTime
        self.MolesWhackedTarget = molesWhackTarget
        self.activeField = 1
        self.isToonInRange = 0
        self.scheduleMoles()
        self.notify.debug('%d setGameStart: Starting game' % self.doId)
        self.gameStartTime = globalClockDelta.networkToLocalTime(timestamp)
        self.gameStarted = True
        for hill in self.moleHills:
            hill.setGameStartTime(self.gameStartTime)

        curGameTime = self.getCurrentGameTime()
        timeLeft = self.GameDuration - curGameTime
        self.cleanupTimer()
        self.timer = ToontownTimer.ToontownTimer()
        self.timer.posBelowTopRightCorner()
        self.timer.setTime(timeLeft)
        self.timer.countdown(timeLeft, self.timerExpired)
        self.startScheduleTask()
        self.frame2D.show()
        if self.hasRestarted:
            self.level.countryClub.showInfoText(self.restartedText)
            self.sendUpdate('damageMe', [])
        else:
            self.hasRestarted = 1
        self.updateGuiScore()

    def local2GameTime(self, timestamp):
        return timestamp - self.gameStartTime

    def game2LocalTime(self, timestamp):
        return timestamp + self.gameStartTime

    def getCurrentGameTime(self):
        return self.local2GameTime(globalClock.getFrameTime())

    def startScheduleTask(self):
        taskMgr.add(self.scheduleTask, self.ScheduleTaskName)

    def stopScheduleTask(self):
        taskMgr.remove(self.ScheduleTaskName)

    def scheduleTask(self, task):
        curTime = self.getCurrentGameTime()
        while self.schedule and self.schedule[0][0] <= curTime and self.activeField:
            popupInfo = self.schedule[0]
            self.schedule = self.schedule[1:]
            startTime, moleIndex, curMoveUpTime, curStayUpTime, curMoveDownTime, moleType = popupInfo
            hill = self.moleHills[moleIndex]
            hill.doMolePop(startTime, curMoveUpTime, curStayUpTime, curMoveDownTime, moleType)

        if self.schedule:
            return task.cont
        else:
            return task.done

    def handleEnterHill(self, colEntry):
        if not self.gameStarted:
            self.notify.debug('sending clientTriggered for %d' % self.doId)
            self.sendUpdate('setClientTriggered', [])

    def handleEnterMole(self, colEntry):
        if not self.gameStarted:
            self.notify.debug('sending clientTriggered for %d' % self.doId)
            self.sendUpdate('setClientTriggered', [])
        surfaceNormal = colEntry.getSurfaceNormal(render)
        self.notify.debug('surfaceNormal=%s' % surfaceNormal)
        into = colEntry.getIntoNodePath()
        moleIndex = int(into.getName().split('-')[-1])
        self.notify.debug('hit mole %d' % moleIndex)
        moleHill = self.moleHills[moleIndex]
        moleHill.stashMoleCollision()
        popupNum = moleHill.getPopupNum()
        if moleHill.hillType == MoleFieldBase.HILL_MOLE:
            timestamp = globalClockDelta.getFrameNetworkTime()
            moleHill.setHillType(MoleFieldBase.HILL_WHACKED)
            self.sendUpdate('whackedBomb', [moleIndex, popupNum, timestamp])
            self.__showToonHitByBomb(localAvatar.doId, moleIndex, timestamp)
        elif moleHill.hillType == MoleFieldBase.HILL_BOMB:
            moleHill.setHillType(MoleFieldBase.HILL_COGWHACKED)
            self.soundCog.play()
            self.sendUpdate('whackedMole', [moleIndex, popupNum])

    def updateMole(self, moleIndex, status):
        if status == self.WHACKED:
            moleHill = self.moleHills[moleIndex]
            if not moleHill.hillType == MoleFieldBase.HILL_COGWHACKED:
                moleHill.setHillType(MoleFieldBase.HILL_COGWHACKED)
                self.soundCog.play()
            moleHill.doMoleDown()

    def updateGuiScore(self):
        molesLeft = self.MolesWhackedTarget - self.numMolesWhacked
        if self.frame2D and hasattr(self, 'scoreLabel') and molesLeft >= 0:
            newText = TTLocalizer.MolesLeft % molesLeft
            self.scoreLabel['text'] = newText

    def setScore(self, score):
        self.notify.debug('score=%d' % score)
        self.numMolesWhacked = score
        self.updateGuiScore()
        molesLeft = self.MolesWhackedTarget - self.numMolesWhacked
        if molesLeft == 0:
            self.gameWon()

    def cleanupTimer(self):
        if self.timer:
            self.timer.stop()
            self.timer.destroy()
            self.timer = None
        return

    def timerExpired(self):
        self.cleanupTimer()
        self.cleanDetect()

    def gameWon(self):
        for hill in self.moleHills:
            hill.forceMoleDown()

        self.cleanupTimer()
        self.frame2D.hide()
        self.level.countryClub.showInfoText(self.winText)
        self.cleanDetect()

    def setPityWin(self):
        for hill in self.moleHills:
            hill.forceMoleDown()

        self.cleanupTimer()
        self.frame2D.hide()
        self.level.countryClub.showInfoText(self.pityWinText)
        self.cleanDetect()

    def cleanDetect(self):
        self.activeField = 0
        self.doToonOutOfRange()

    def __detect(self, task):
        distance = self.centerNode.getDistance(localAvatar)
        greaterDim = self.dimensionX
        if self.dimensionY > self.dimensionX:
            greaterDim = self.gridScaleY
        self.detectCount += 1
        if self.detectCount > 5:
            self.detectCount = 0
        if distance < greaterDim * 0.75:
            if not self.isToonInRange:
                self.doToonInRange()
        elif self.isToonInRange:
            self.doToonOutOfRange()
        taskMgr.doMethodLater(0.1, self.__detect, self.detectName)
        return Task.done

    def doToonInRange(self):
        if not self.gameStarted:
            self.notify.debug('sending clientTriggered for %d' % self.doId)
            self.sendUpdate('setClientTriggered', [])
        self.isToonInRange = 1
        if self.activeField:
            self.setUpCamera()
            if not self.hasEntered:
                self.level.countryClub.showInfoText(self.gameText)
                self.hasEntered = 1

    def setUpCamera(self):
        camHeight = base.localAvatar.getClampedAvatarHeight()
        heightScaleFactor = camHeight * 0.3333333333
        defLookAt = Point3(0.0, 1.5, camHeight)
        cameraPoint = Point3(0.0, -22.0 * heightScaleFactor, camHeight + 12.0)
        base.localAvatar.setIdealCameraPos(cameraPoint)

    def doToonOutOfRange(self):
        self.isToonInRange = 0
        base.localAvatar.setCameraPositionByIndex(base.localAvatar.cameraIndex)
        self.cameraHold = None
        return

    def reportToonHitByBomb(self, avId, moleIndex, timestamp):
        if avId != localAvatar.doId:
            self.__showToonHitByBomb(avId, moleIndex, timestamp)
            moleHill = self.moleHills[moleIndex]
            if not moleHill.hillType == MoleFieldBase.HILL_WHACKED:
                moleHill.setHillType(MoleFieldBase.HILL_WHACKED)
                self.soundCog.play()
            moleHill.doMoleDown()

    def __showToonHitByBomb(self, avId, moleIndex, timestamp = 0):
        toon = base.cr.doId2do.get(avId)
        moleHill = self.moleHills[moleIndex]
        if toon == None:
            return
        rng = random.Random(timestamp)
        curPos = toon.getPos(render)
        oldTrack = self.toonHitTracks.get(avId)
        if oldTrack:
            if oldTrack.isPlaying():
                oldTrack.finish()
        toon.setPos(curPos)
        toon.setZ(self.getZ())
        parentNode = render.attachNewNode('mazeFlyToonParent-' + repr(avId))
        parentNode.setPos(toon.getPos(render))
        toon.reparentTo(parentNode)
        toon.setPos(0, 0, 0)
        startPos = parentNode.getPos()
        dropShadow = toon.dropShadow.copyTo(parentNode)
        dropShadow.setScale(toon.dropShadow.getScale(render))
        trajectory = Trajectory.Trajectory(0, Point3(0, 0, 0), Point3(0, 0, 50), gravMult=1.0)
        flyDur = trajectory.calcTimeOfImpactOnPlane(0.0)
        endTile = [rng.randint(0, self.numSquaresX - 1), rng.randint(0, self.numSquaresY - 1)]
        endWorldCoords = (self.getX(render) + endTile[0] * self.spacingX, self.getY(render) + endTile[1] * self.spacingY)
        endPos = Point3(endWorldCoords[0], endWorldCoords[1], startPos[2])

        def flyFunc(t, trajectory, startPos = startPos, endPos = endPos, dur = flyDur, moveNode = parentNode, flyNode = toon):
            u = t / dur
            moveNode.setX(startPos[0] + u * (endPos[0] - startPos[0]))
            moveNode.setY(startPos[1] + u * (endPos[1] - startPos[1]))
            if flyNode and not flyNode.isEmpty():
                flyNode.setPos(trajectory.getPos(t))

        def safeSetHpr(node, hpr):
            if node and not node.isEmpty():
                node.setHpr(hpr)

        flyTrack = Sequence(LerpFunctionInterval(flyFunc, fromData=0.0, toData=flyDur, duration=flyDur, extraArgs=[trajectory]), name=toon.uniqueName('hitBySuit-fly'))
        if avId != localAvatar.doId:
            cameraTrack = Sequence()
        else:
            base.localAvatar.stopUpdateSmartCamera()
            self.camParentHold = camera.getParent()
            self.camParent = base.localAvatar.attachNewNode('iCamParent')
            self.camParent.setPos(self.camParentHold.getPos())
            self.camParent.setHpr(self.camParentHold.getHpr())
            camera.reparentTo(self.camParent)
            self.camParent.reparentTo(parentNode)
            startCamPos = camera.getPos()
            destCamPos = camera.getPos()
            zenith = trajectory.getPos(flyDur / 2.0)[2]
            destCamPos.setZ(zenith * 1.3)
            destCamPos.setY(destCamPos[1] * 0.3)

            def camTask(task, zenith = zenith, flyNode = toon, startCamPos = startCamPos, camOffset = destCamPos - startCamPos):
                u = flyNode.getZ() / zenith
                camera.lookAt(toon)
                return Task.cont

            camTaskName = 'mazeToonFlyCam-' + repr(avId)
            taskMgr.add(camTask, camTaskName, priority=20)

            def cleanupCamTask(self = self, toon = toon, camTaskName = camTaskName, startCamPos = startCamPos):
                taskMgr.remove(camTaskName)
                self.camParent.reparentTo(toon)
                camera.setPos(startCamPos)
                camera.lookAt(toon)
                camera.reparentTo(self.camParentHold)
                base.localAvatar.startUpdateSmartCamera()
                self.setUpCamera()

            cameraTrack = Sequence(Wait(flyDur), Func(cleanupCamTask), name='hitBySuit-cameraLerp')
        geomNode = toon.getGeomNode()
        startHpr = geomNode.getHpr()
        destHpr = Point3(startHpr)
        hRot = rng.randrange(1, 8)
        if rng.choice([0, 1]):
            hRot = -hRot
        destHpr.setX(destHpr[0] + hRot * 360)
        spinHTrack = Sequence(LerpHprInterval(geomNode, flyDur, destHpr, startHpr=startHpr), Func(safeSetHpr, geomNode, startHpr), name=toon.uniqueName('hitBySuit-spinH'))
        parent = geomNode.getParent()
        rotNode = parent.attachNewNode('rotNode')
        geomNode.reparentTo(rotNode)
        rotNode.setZ(toon.getHeight() / 2.0)
        oldGeomNodeZ = geomNode.getZ()
        geomNode.setZ(-toon.getHeight() / 2.0)
        startHpr = rotNode.getHpr()
        destHpr = Point3(startHpr)
        pRot = rng.randrange(1, 3)
        if rng.choice([0, 1]):
            pRot = -pRot
        destHpr.setY(destHpr[1] + pRot * 360)
        spinPTrack = Sequence(LerpHprInterval(rotNode, flyDur, destHpr, startHpr=startHpr), Func(safeSetHpr, rotNode, startHpr), name=toon.uniqueName('hitBySuit-spinP'))
        soundTrack = Sequence()

        def preFunc(self = self, avId = avId, toon = toon, dropShadow = dropShadow):
            forwardSpeed = toon.forwardSpeed
            rotateSpeed = toon.rotateSpeed
            if avId == localAvatar.doId:
                toon.stopSmooth()
                base.cr.playGame.getPlace().fsm.request('stopped')
            else:
                toon.stopSmooth()
            if forwardSpeed or rotateSpeed:
                toon.setSpeed(forwardSpeed, rotateSpeed)
            toon.dropShadow.hide()

        def postFunc(self = self, avId = avId, oldGeomNodeZ = oldGeomNodeZ, dropShadow = dropShadow, parentNode = parentNode):
            if avId == localAvatar.doId:
                base.localAvatar.setPos(endPos)
                if hasattr(self, 'orthoWalk'):
                    self.orthoWalk.start()
            dropShadow.removeNode()
            del dropShadow
            if toon and toon.dropShadow:
                toon.dropShadow.show()
            geomNode = toon.getGeomNode()
            rotNode = geomNode.getParent()
            baseNode = rotNode.getParent()
            geomNode.reparentTo(baseNode)
            rotNode.removeNode()
            del rotNode
            geomNode.setZ(oldGeomNodeZ)
            toon.reparentTo(render)
            toon.setPos(endPos)
            parentNode.removeNode()
            del parentNode
            if avId == localAvatar.doId:
                toon.startSmooth()
                place = base.cr.playGame.getPlace()
                if place and hasattr(place, 'fsm'):
                    place.fsm.request('walk')
            else:
                toon.startSmooth()

        preFunc()
        hitTrack = Sequence(Func(toon.setPos, Point3(0.0, 0.0, 0.0)), Wait(0.25), Parallel(flyTrack, cameraTrack, self.soundIUpDown, spinHTrack, spinPTrack, soundTrack), Func(postFunc), name=toon.uniqueName('hitBySuit'))
        self.toonHitTracks[avId] = hitTrack
        hitTrack.start()
        posM = moleHill.getPos(render)
        posN = Point3(posM[0], posM[1], posM[2] + 4.0)
        self.soundBomb.play()
        self.soundBomb2.play()
        return
