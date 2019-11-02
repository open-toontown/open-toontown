from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from direct.distributed.ClockDelta import *
from direct.fsm import StateData
from direct.directnotify import DirectNotifyGlobal
from direct.showbase.PythonUtil import *
from direct.task import Task
import CCharPaths
from toontown.toonbase import ToontownGlobals

class CharNeutralState(StateData.StateData):
    notify = DirectNotifyGlobal.directNotify.newCategory('CharNeutralState')

    def __init__(self, doneEvent, character):
        StateData.StateData.__init__(self, doneEvent)
        self.__doneEvent = doneEvent
        self.character = character

    def enter(self, startTrack = None, playRate = None):
        StateData.StateData.enter(self)
        self.notify.debug('Neutral ' + self.character.getName() + '...')
        self.__neutralTrack = Sequence(name=self.character.getName() + '-neutral')
        if startTrack:
            self.__neutralTrack.append(startTrack)
        if playRate:
            self.__neutralTrack.append(Func(self.character.setPlayRate, playRate, 'neutral'))
        self.__neutralTrack.append(Func(self.character.loop, 'neutral'))
        self.__neutralTrack.start()

    def exit(self):
        StateData.StateData.exit(self)
        self.__neutralTrack.finish()

    def __doneHandler(self):
        doneStatus = {}
        doneStatus['state'] = 'walk'
        doneStatus['status'] = 'done'
        messenger.send(self.__doneEvent, [doneStatus])
        return Task.done


class CharWalkState(StateData.StateData):
    notify = DirectNotifyGlobal.directNotify.newCategory('CharWalkState')

    def __init__(self, doneEvent, character, diffPath = None):
        StateData.StateData.__init__(self, doneEvent)
        self.doneEvent = doneEvent
        self.character = character
        if diffPath == None:
            self.paths = CCharPaths.getPaths(character.getName(), character.getCCLocation())
        else:
            self.paths = CCharPaths.getPaths(diffPath, character.getCCLocation())
        self.speed = character.walkSpeed()
        self.offsetX = 0
        self.offsetY = 0
        self.oldOffsetX = 0
        self.olfOffsetY = 0
        self.walkTrack = None
        return

    def enter(self, startTrack = None, playRate = None):
        StateData.StateData.enter(self)
        self.notify.debug('Walking ' + self.character.getName() + '... from ' + str(self.walkInfo[0]) + ' to ' + str(self.walkInfo[1]))
        posPoints = CCharPaths.getPointsFromTo(self.walkInfo[0], self.walkInfo[1], self.paths)
        lastPos = posPoints[-1]
        newLastPos = Point3(lastPos[0] + self.offsetX, lastPos[1] + self.offsetY, lastPos[2])
        posPoints[-1] = newLastPos
        firstPos = posPoints[0]
        newFirstPos = Point3(firstPos[0] + self.oldOffsetX, firstPos[1] + self.oldOffsetY, firstPos[2])
        posPoints[0] = newFirstPos
        self.walkTrack = Sequence(name=self.character.getName() + '-walk')
        if startTrack:
            self.walkTrack.append(startTrack)
        self.character.setPos(posPoints[0])
        raycast = CCharPaths.getRaycastFlag(self.walkInfo[0], self.walkInfo[1], self.paths)
        moveTrack = self.makePathTrack(self.character, posPoints, self.speed, raycast)
        if playRate:
            self.walkTrack.append(Func(self.character.setPlayRate, playRate, 'walk'))
        self.walkTrack.append(Func(self.character.loop, 'walk'))
        self.walkTrack.append(moveTrack)
        doneEventName = self.character.getName() + 'WalkDone'
        self.walkTrack.append(Func(messenger.send, doneEventName))
        ts = globalClockDelta.localElapsedTime(self.walkInfo[2])
        self.accept(doneEventName, self.doneHandler)
        self.notify.debug('walkTrack.start(%s)' % ts)
        self.walkTrack.start(ts)

    def makePathTrack(self, nodePath, posPoints, velocity, raycast = 0):
        track = Sequence()
        if raycast:
            track.append(Func(nodePath.enableRaycast, 1))
        startHpr = nodePath.getHpr()
        for pointIndex in range(len(posPoints) - 1):
            startPoint = posPoints[pointIndex]
            endPoint = posPoints[pointIndex + 1]
            track.append(Func(nodePath.setPos, startPoint))
            distance = Vec3(endPoint - startPoint).length()
            duration = distance / velocity
            curHpr = nodePath.getHpr()
            nodePath.headsUp(endPoint[0], endPoint[1], endPoint[2])
            destHpr = nodePath.getHpr()
            reducedCurH = reduceAngle(curHpr[0])
            reducedCurHpr = Vec3(reducedCurH, curHpr[1], curHpr[2])
            reducedDestH = reduceAngle(destHpr[0])
            shortestAngle = closestDestAngle(reducedCurH, reducedDestH)
            shortestHpr = Vec3(shortestAngle, destHpr[1], destHpr[2])
            turnTime = abs(shortestAngle) / 270.0
            nodePath.setHpr(shortestHpr)
            if duration - turnTime > 0.01:
                track.append(Parallel(Func(nodePath.loop, 'walk'), LerpHprInterval(nodePath, turnTime, shortestHpr, startHpr=reducedCurHpr, name='lerp' + nodePath.getName() + 'Hpr'), LerpPosInterval(nodePath, duration=duration - turnTime, pos=Point3(endPoint), startPos=Point3(startPoint), fluid=1)))

        nodePath.setHpr(startHpr)
        if raycast:
            track.append(Func(nodePath.enableRaycast, 0))
        return track

    def doneHandler(self):
        doneStatus = {}
        doneStatus['state'] = 'walk'
        doneStatus['status'] = 'done'
        messenger.send(self.doneEvent, [doneStatus])
        return Task.done

    def exit(self):
        StateData.StateData.exit(self)
        self.ignore(self.character.getName() + 'WalkDone')
        if self.walkTrack:
            self.walkTrack.finish()
        self.walkTrack = None
        return

    def setWalk(self, srcNode, destNode, timestamp, offsetX = 0, offsetY = 0):
        self.oldOffsetX = self.offsetX
        self.oldOffsetY = self.offsetY
        self.walkInfo = (srcNode, destNode, timestamp)
        self.offsetX = offsetX
        self.offsetY = offsetY


class CharFollowChipState(CharWalkState):
    notify = DirectNotifyGlobal.directNotify.newCategory('CharFollowChipState')
    completeRevolutionDistance = 13

    def __init__(self, doneEvent, character, chipId):
        CharWalkState.__init__(self, doneEvent, character)
        self.offsetDict = {'a': (ToontownGlobals.DaleOrbitDistance, 0)}
        self.chipId = chipId

    def setWalk(self, srcNode, destNode, timestamp, offsetX = 0, offsetY = 0):
        self.offsetDict[destNode] = (offsetX, offsetY)
        self.srcNode = srcNode
        self.destNode = destNode
        self.orbitDistance = ToontownGlobals.DaleOrbitDistance
        if (srcNode, destNode) in CCharPaths.DaleOrbitDistanceOverride:
            self.orbitDistance = CCharPaths.DaleOrbitDistanceOverride[srcNode, destNode]
        elif (destNode, srcNode) in CCharPaths.DaleOrbitDistanceOverride:
            self.orbitDistance = CCharPaths.DaleOrbitDistanceOverride[destNode, srcNode]
        CharWalkState.setWalk(self, srcNode, destNode, timestamp, offsetX, offsetY)

    def makePathTrack(self, nodePath, posPoints, velocity, raycast = 0):
        retval = Sequence()
        if raycast:
            retval.append(Func(nodePath.enableRaycast, 1))
        chip = base.cr.doId2do.get(self.chipId)
        self.chipPaths = CCharPaths.getPaths(chip.getName(), chip.getCCLocation())
        self.posPoints = posPoints
        chipDuration = chip.walk.walkTrack.getDuration()
        self.notify.debug('chipDuration = %f' % chipDuration)
        chipDistance = CCharPaths.getWalkDistance(self.srcNode, self.destNode, ToontownGlobals.ChipSpeed, self.chipPaths)
        self.revolutions = chipDistance / self.completeRevolutionDistance
        srcOffset = (0, 0)
        if self.srcNode in self.offsetDict:
            srcOffset = self.offsetDict[self.srcNode]
        srcTheta = math.atan2(srcOffset[1], srcOffset[0])
        if srcTheta < 0:
            srcTheta += 2 * math.pi
        if srcTheta > 0:
            srcRev = (2 * math.pi - srcTheta) / (2 * math.pi)
        else:
            srcRev = 0
        self.srcTheta = srcTheta
        destOffset = (0, 0)
        if self.destNode in self.offsetDict:
            destOffset = self.offsetDict[self.destNode]
        destTheta = math.atan2(destOffset[1], destOffset[0])
        if destTheta < 0:
            destTheta += 2 * math.pi
        self.destTheta = destTheta
        self.revolutions += srcRev
        endingTheta = srcTheta + self.revolutions % 1.0 * 2 * math.pi
        diffTheta = destTheta - endingTheta
        destRev = diffTheta / (2 * math.pi)
        self.revolutions += destRev
        while self.revolutions < 1:
            self.revolutions += 1

        def positionDale(t):
            self.orbitChip(t)

        retval.append(LerpFunctionInterval(positionDale, chipDuration))
        if raycast:
            retval.append(Func(nodePath.enableRaycast, 0))
        return retval

    def orbitChip(self, t):
        srcOffset = (0, 0)
        if self.srcNode in self.offsetDict:
            srcOffset = self.offsetDict[self.srcNode]
        chipSrcPos = Point3(self.posPoints[0][0] - srcOffset[0], self.posPoints[0][1] - srcOffset[1], self.posPoints[0][2])
        destOffset = (0, 0)
        if self.destNode in self.offsetDict:
            destOffset = self.offsetDict[self.destNode]
        chipDestPos = Point3(self.posPoints[-1][0] - destOffset[0], self.posPoints[-1][1] - destOffset[1], self.posPoints[-1][2])
        displacement = chipDestPos - chipSrcPos
        displacement *= t
        chipPos = chipSrcPos + displacement
        diffTheta = t * self.revolutions * 2 * math.pi
        curTheta = self.srcTheta + diffTheta
        newOffsetX = math.cos(curTheta) * self.orbitDistance
        newOffsetY = math.sin(curTheta) * self.orbitDistance
        dalePos = Point3(chipPos[0] + newOffsetX, chipPos[1] + newOffsetY, chipPos[2])
        self.character.setPos(dalePos)
        newHeading = rad2Deg(curTheta)
        newHeading %= 360
        self.character.setH(newHeading)
