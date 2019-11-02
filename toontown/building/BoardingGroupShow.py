from pandac.PandaModules import *
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from direct.task.Task import Task
from direct.interval.IntervalGlobal import *
from toontown.toonbase import TTLocalizer
from toontown.effects import DustCloud
TRACK_TYPE_TELEPORT = 1
TRACK_TYPE_RUN = 2
TRACK_TYPE_POOF = 3

class BoardingGroupShow:
    notify = DirectNotifyGlobal.directNotify.newCategory('BoardingGroupShow')
    thresholdRunDistance = 25.0

    def __init__(self, toon):
        self.toon = toon
        self.avId = self.toon.doId
        self.dustCloudIval = None
        return

    def cleanup(self):
        if localAvatar.doId == self.avId:
            self.__stopTimer()
            self.clock.removeNode()

    def startTimer(self):
        self.clockNode = TextNode('elevatorClock')
        self.clockNode.setFont(ToontownGlobals.getSignFont())
        self.clockNode.setAlign(TextNode.ACenter)
        self.clockNode.setTextColor(0.5, 0.5, 0.5, 1)
        self.clockNode.setText(str(int(self.countdownDuration)))
        self.clock = aspect2d.attachNewNode(self.clockNode)
        self.clock.setPos(0, 0, -0.6)
        self.clock.setScale(0.15, 0.15, 0.15)
        self.__countdown(self.countdownDuration, self.__boardingElevatorTimerExpired)

    def __countdown(self, duration, callback):
        self.countdownTask = Task(self.__timerTask)
        self.countdownTask.duration = duration
        self.countdownTask.callback = callback
        taskMgr.remove(self.uniqueName(self.avId))
        return taskMgr.add(self.countdownTask, self.uniqueName(self.avId))

    def __timerTask(self, task):
        countdownTime = int(task.duration - task.time)
        timeStr = self.timeWarningText + str(countdownTime)
        if self.clockNode.getText() != timeStr:
            self.clockNode.setText(timeStr)
        if task.time >= task.duration:
            if task.callback:
                task.callback()
            return Task.done
        else:
            return Task.cont

    def __boardingElevatorTimerExpired(self):
        self.notify.debug('__boardingElevatorTimerExpired')
        self.clock.removeNode()

    def __stopTimer(self):
        if self.countdownTask:
            self.countdownTask.callback = None
            taskMgr.remove(self.countdownTask)
        return

    def uniqueName(self, avId):
        uniqueName = 'boardingElevatorTimerTask-' + str(avId)
        return uniqueName

    def getBoardingTrack(self, elevatorModel, offset, offsetWrtRender, wantToonRotation):
        self.timeWarningText = TTLocalizer.BoardingTimeWarning
        self.countdownDuration = 6
        trackType = TRACK_TYPE_TELEPORT
        boardingTrack = Sequence()
        if self.toon:
            if self.avId == localAvatar.doId:
                boardingTrack.append(Func(self.startTimer))
            isInThresholdDist = self.__isInThresholdDist(elevatorModel, offset, self.thresholdRunDistance)
            isRunPathClear = self.__isRunPathClear(elevatorModel, offsetWrtRender)
            if isInThresholdDist and isRunPathClear:
                boardingTrack.append(self.__getRunTrack(elevatorModel, offset, wantToonRotation))
                trackType = TRACK_TYPE_RUN
            elif self.toon.isDisguised:
                boardingTrack.append(self.__getPoofTeleportTrack(elevatorModel, offset, wantToonRotation))
                trackType = TRACK_TYPE_POOF
            else:
                boardingTrack.append(self.__getTeleportTrack(elevatorModel, offset, wantToonRotation))
        boardingTrack.append(Func(self.cleanup))
        return (boardingTrack, trackType)

    def __getOffsetPos(self, elevatorModel, offset):
        dest = elevatorModel.getPos(self.toon.getParent())
        dest += Vec3(*offset)
        return dest

    def __getTeleportTrack(self, elevatorModel, offset, wantToonRotation):
        teleportTrack = Sequence()
        if self.toon:
            if wantToonRotation:
                teleportTrack.append(Func(self.toon.headsUp, elevatorModel, offset))
            teleportTrack.append(Func(self.toon.setAnimState, 'TeleportOut'))
            teleportTrack.append(Wait(3.5))
            teleportTrack.append(Func(self.toon.setPos, Point3(offset)))
            teleportTrack.append(Func(self.toon.setAnimState, 'TeleportIn'))
            teleportTrack.append(Wait(1))
        return teleportTrack

    def __getPoofTeleportTrack(self, elevatorModel, offset, wantToonRotation):
        teleportTrack = Sequence()
        if wantToonRotation:
            teleportTrack.append(Func(self.toon.headsUp, elevatorModel, offset))

        def getDustCloudPos():
            toonPos = self.toon.getPos(render)
            return Point3(toonPos.getX(), toonPos.getY(), toonPos.getZ() + 3)

        def cleanupDustCloudIval():
            if self.dustCloudIval:
                self.dustCloudIval.finish()
                self.dustCloudIval = None
            return

        def getDustCloudIval():
            cleanupDustCloudIval()
            dustCloud = DustCloud.DustCloud(fBillboard=0, wantSound=1)
            dustCloud.setBillboardAxis(2.0)
            dustCloud.setZ(3)
            dustCloud.setScale(0.4)
            dustCloud.createTrack()
            self.dustCloudIval = Sequence(Func(dustCloud.reparentTo, render), Func(dustCloud.setPos, getDustCloudPos()), dustCloud.track, Func(dustCloud.detachNode), Func(dustCloud.destroy), name='dustCloadIval')
            self.dustCloudIval.start()

        if self.toon:
            teleportTrack.append(Func(self.toon.setAnimState, 'neutral'))
            teleportTrack.append(Wait(0.5))
            teleportTrack.append(Func(getDustCloudIval))
            teleportTrack.append(Wait(0.25))
            teleportTrack.append(Func(self.toon.hide))
            teleportTrack.append(Wait(1.5))
            teleportTrack.append(Func(self.toon.setPos, Point3(offset)))
            teleportTrack.append(Func(getDustCloudIval))
            teleportTrack.append(Wait(0.25))
            teleportTrack.append(Func(self.toon.show))
            teleportTrack.append(Wait(0.5))
            teleportTrack.append(Func(cleanupDustCloudIval))
        return teleportTrack

    def __getRunTrack(self, elevatorModel, offset, wantToonRotation):
        runTrack = Sequence()
        if self.toon:
            if wantToonRotation:
                runTrack.append(Func(self.toon.headsUp, elevatorModel, offset))
            if self.toon.isDisguised:
                runTrack.append(Func(self.toon.suit.loop, 'walk'))
            else:
                runTrack.append(Func(self.toon.setAnimState, 'run'))
            runTrack.append(LerpPosInterval(self.toon, 1, Point3(offset)))
        return runTrack

    def __isInThresholdDist(self, elevatorModel, offset, thresholdDist):
        diff = Point3(offset) - self.toon.getPos()
        if diff.length() > thresholdDist:
            return False
        else:
            return True

    def __isRunPathClear(self, elevatorModel, offsetWrtRender):
        pathClear = True
        source = self.toon.getPos(render)
        dest = offsetWrtRender
        collSegment = CollisionSegment(source[0], source[1], source[2], dest[0], dest[1], dest[2])
        fromObject = render.attachNewNode(CollisionNode('runCollSegment'))
        fromObject.node().addSolid(collSegment)
        fromObject.node().setFromCollideMask(ToontownGlobals.WallBitmask)
        fromObject.node().setIntoCollideMask(BitMask32.allOff())
        queue = CollisionHandlerQueue()
        base.cTrav.addCollider(fromObject, queue)
        base.cTrav.traverse(render)
        queue.sortEntries()
        if queue.getNumEntries():
            for entryNum in xrange(queue.getNumEntries()):
                entry = queue.getEntry(entryNum)
                hitObject = entry.getIntoNodePath()
                if hitObject.getNetTag('pieCode') != '3':
                    pathClear = False

        base.cTrav.removeCollider(fromObject)
        fromObject.removeNode()
        return pathClear

    def getGoButtonShow(self, elevatorName):
        self.elevatorName = elevatorName
        self.timeWarningText = TTLocalizer.BoardingGoShow % self.elevatorName
        self.countdownDuration = 4
        goButtonShow = Sequence()
        if self.toon:
            if self.avId == localAvatar.doId:
                goButtonShow.append(Func(self.startTimer))
            goButtonShow.append(self.__getTeleportOutTrack())
            goButtonShow.append(Wait(3))
        goButtonShow.append(Func(self.cleanup))
        return goButtonShow

    def __getTeleportOutTrack(self):
        teleportOutTrack = Sequence()
        if self.toon and not self.toon.isDisguised:
            teleportOutTrack.append(Func(self.toon.b_setAnimState, 'TeleportOut'))
        return teleportOutTrack

    def getGoButtonPreShow(self):
        self.timeWarningText = TTLocalizer.BoardingGoPreShow
        self.countdownDuration = 4
        goButtonPreShow = Sequence()
        if self.toon:
            if self.avId == localAvatar.doId:
                goButtonPreShow.append(Func(self.startTimer))
                goButtonPreShow.append(Wait(3))
        goButtonPreShow.append(Func(self.cleanup))
        return goButtonPreShow
