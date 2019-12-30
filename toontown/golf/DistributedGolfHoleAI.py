from direct.distributed import DistributedObjectAI
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from pandac.PandaModules import *
from . import DistributedPhysicsWorldAI
from direct.fsm.FSM import FSM
from toontown.ai.ToonBarrier import *
from toontown.golf import GolfGlobals
import random
from toontown.golf import GolfHoleBase

class DistributedGolfHoleAI(DistributedPhysicsWorldAI.DistributedPhysicsWorldAI, FSM, GolfHoleBase.GolfHoleBase):
    defaultTransitions = {'Off': ['Cleanup', 'WaitTee'], 'WaitTee': ['WaitSwing', 'Cleanup', 'WaitTee', 'WaitPlayback'], 'WaitSwing': ['WaitPlayback', 'Cleanup', 'WaitSwing', 'WaitTee'], 'WaitPlayback': ['WaitSwing', 'Cleanup', 'WaitTee', 'WaitPlayback'], 'Cleanup': ['Off']}
    id = 0
    notify = directNotify.newCategory('DistributedGolfHoleAI')

    def __init__(self, zoneId, golfCourse, holeId):
        FSM.__init__(self, 'Golf_%s_FSM' % self.id)
        DistributedPhysicsWorldAI.DistributedPhysicsWorldAI.__init__(self, simbase.air)
        GolfHoleBase.GolfHoleBase.__init__(self)
        self.zoneId = zoneId
        self.golfCourse = golfCourse
        self.holeId = holeId
        self.avIdList = golfCourse.avIdList[:]
        self.watched = [0, 0, 0, 0]
        self.barrierPlayback = None
        self.trustedPlayerId = None
        self.activeGolferIndex = None
        self.activeGolferId = None
        self.holeInfo = GolfGlobals.HoleInfo[self.holeId]
        self.teeChosen = {}
        for avId in self.avIdList:
            self.teeChosen[avId] = -1

        self.ballPos = {}
        for avId in self.avIdList:
            self.ballPos[avId] = Vec3(0, 0, 0)

        self.playStarted = False
        return

    def curGolfBall(self):
        return self.ball

    def generate(self):
        DistributedPhysicsWorldAI.DistributedPhysicsWorldAI.generate(self)
        self.ball = self.createBall()
        self.createRays()
        if len(self.teePositions) > 1:
            startPos = self.teePositions[1]
        else:
            startPos = self.teePositions[0]
        startPos += Vec3(0, 0, GolfGlobals.GOLF_BALL_RADIUS)
        self.ball.setPosition(startPos)

    def delete(self):
        self.notify.debug('__delete__')
        DistributedPhysicsWorldAI.DistributedPhysicsWorldAI.delete(self)
        self.notify.debug('calling self.terrainModel.removeNode')
        self.terrainModel.removeNode()
        self.notify.debug('self.barrierPlayback is %s' % self.barrierPlayback)
        if self.barrierPlayback:
            self.notify.debug('calling self.barrierPlayback.cleanup')
            self.barrierPlayback.cleanup()
            self.notify.debug('calling self.barrierPlayback = None')
            self.barrierPlayback = None
        self.activeGolferId = None
        return

    def setZoneId(self, zoneId):
        self.zoneId = zoneId

    def setAvatarReadyHole(self):
        self.notify.debugStateCall(self)
        avId = self.air.getAvatarIdFromSender()
        self.golfCourse.avatarReadyHole(avId)

    def startPlay(self):
        self.notify.debug('startPlay')
        self.playStarted = True
        self.numGolfers = len(self.golfCourse.getGolferIds())
        self.selectNextGolfer()

    def selectNextGolfer(self):
        self.notify.debug('selectNextGolfer, old golferIndex=%s old golferId=%s' % (self.activeGolferIndex, self.activeGolferId))
        if self.golfCourse.isCurHoleDone():
            return
        if self.activeGolferIndex == None:
            self.activeGolferIndex = 0
            self.activeGolferId = self.golfCourse.getGolferIds()[self.activeGolferIndex]
        else:
            self.activeGolferIndex += 1
            if self.activeGolferIndex >= len(self.golfCourse.getGolferIds()):
                self.activeGolferIndex = 0
            self.activeGolferId = self.golfCourse.getGolferIds()[self.activeGolferIndex]
        safety = 0
        while safety < 50 and not self.golfCourse.checkGolferPlaying(self.golfCourse.getGolferIds()[self.activeGolferIndex]):
            self.activeGolferIndex += 1
            self.notify.debug('Index %s' % self.activeGolferIndex)
            if self.activeGolferIndex >= len(self.golfCourse.getGolferIds()):
                self.activeGolferIndex = 0
            self.activeGolferId = self.golfCourse.getGolferIds()[self.activeGolferIndex]
            safety += 1

        if safety != 50:
            golferId = self.golfCourse.getGolferIds()[self.activeGolferIndex]
            if self.teeChosen[golferId] == -1:
                self.sendUpdate('golferChooseTee', [golferId])
                self.request('WaitTee')
            else:
                self.sendUpdate('golfersTurn', [golferId])
                self.request('WaitSwing')
        else:
            self.notify.debug('safety')
        self.notify.debug('selectNextGolfer, new golferIndex=%s new golferId=%s' % (self.activeGolferIndex, self.activeGolferId))
        return

    def clearWatched(self):
        self.watched = [
         1, 1, 1, 1]
        for index in range(len(self.golfCourse.getGolferIds())):
            self.watched[index] = 0

    def setWatched(self, avId):
        for index in range(len(self.golfCourse.getGolferIds())):
            if self.golfCourse.getGolferIds()[index] == avId:
                self.watched[index] = 1

    def checkWatched(self):
        if 0 not in self.watched:
            return True
        else:
            return False

    def turnDone(self):
        self.notify.debug('Turn Done')
        avId = self.air.getAvatarIdFromSender()
        if self.barrierPlayback:
            self.barrierPlayback.clear(avId)

    def ballInHole(self, golferId=None):
        self.notify.debug('ballInHole')
        if golferId:
            avId = golferId
        else:
            avId = self.air.getAvatarIdFromSender()
        self.golfCourse.setBallIn(avId)
        if self.golfCourse.isCurHoleDone():
            self.notify.debug('ballInHole doing nothing')
        else:
            self.notify.debug('ballInHole calling self.selectNextGolfer')
            self.selectNextGolfer()

    def getHoleId(self):
        return self.holeId

    def finishHole(self):
        self.notify.debug('finishHole')
        self.golfCourse.holeOver()

    def getGolferIds(self):
        return self.avIdList

    def loadLevel(self):
        GolfHoleBase.GolfHoleBase.loadLevel(self)
        optionalObjects = self.terrainModel.findAllMatches('**/optional*')
        requiredObjects = self.terrainModel.findAllMatches('**/required*')
        self.parseLocators(optionalObjects, 1)
        self.parseLocators(requiredObjects, 0)
        self.teeNodePath = self.terrainModel.find('**/tee0')
        if self.teeNodePath.isEmpty():
            teePos = Vec3(0, 0, 10)
        else:
            teePos = self.teeNodePath.getPos()
            teePos.setZ(teePos.getZ() + GolfGlobals.GOLF_BALL_RADIUS)
            self.notify.debug('teeNodePath heading = %s' % self.teeNodePath.getH())
        self.teePositions = [
         teePos]
        teeIndex = 1
        teeNode = self.terrainModel.find('**/tee%d' % teeIndex)
        while not teeNode.isEmpty():
            teePos = teeNode.getPos()
            teePos.setZ(teePos.getZ() + GolfGlobals.GOLF_BALL_RADIUS)
            self.teePositions.append(teePos)
            self.notify.debug('teeNodeP heading = %s' % teeNode.getH())
            teeIndex += 1
            teeNode = self.terrainModel.find('**/tee%d' % teeIndex)

    def createLocatorDict(self):
        self.locDict = {}
        locatorNum = 1
        curNodePath = self.hardSurfaceNodePath.find('**/locator%d' % locatorNum)
        while not curNodePath.isEmpty():
            self.locDict[locatorNum] = curNodePath
            locatorNum += 1
            curNodePath = self.hardSurfaceNodePath.find('**/locator%d' % locatorNum)

    def loadBlockers(self):
        loadAll = simbase.config.GetBool('golf-all-blockers', 0)
        self.createLocatorDict()
        self.blockerNums = self.holeInfo['blockers']
        for locatorNum in self.locDict:
            if locatorNum in self.blockerNums or loadAll:
                locator = self.locDict[locatorNum]
                locatorParent = locator.getParent()
                locator.getChildren().wrtReparentTo(locatorParent)
            else:
                self.locDict[locatorNum].removeNode()

        self.hardSurfaceNodePath.flattenStrong()

    def createBall(self):
        golfBallGeom = self.createSphere(self.world, self.space, GolfGlobals.GOLF_BALL_DENSITY, GolfGlobals.GOLF_BALL_RADIUS, 1)[1]
        return golfBallGeom

    def preStep(self):
        GolfHoleBase.GolfHoleBase.preStep(self)

    def postStep(self):
        GolfHoleBase.GolfHoleBase.postStep(self)

    def postSwing(self, cycleTime, power, x, y, z, dirX, dirY):
        avId = self.air.getAvatarIdFromSender()
        self.storeAction = [
         avId, cycleTime, power, x, y, z, dirX, dirY]
        if self.commonHoldData:
            self.doAction()

    def postSwingState(self, cycleTime, power, x, y, z, dirX, dirY, curAimTime, commonObjectData):
        self.notify.debug('postSwingState')
        if not self.golfCourse.getStillPlayingAvIds():
            return
        avId = self.air.getAvatarIdFromSender()
        self.storeAction = [avId, cycleTime, power, x, y, z, dirX, dirY]
        self.commonHoldData = commonObjectData
        self.trustedPlayerId = self.choosePlayerToSimulate()
        self.sendUpdateToAvatarId(self.trustedPlayerId, 'assignRecordSwing', [avId, cycleTime, power, x, y, z, dirX, dirY, commonObjectData])
        self.golfCourse.addAimTime(avId, curAimTime)

    def choosePlayerToSimulate(self):
        stillPlaying = self.golfCourse.getStillPlayingAvIds()
        playerId = 0
        if simbase.air.config.GetBool('golf-trust-driver-first', 0):
            if stillPlaying:
                playerId = stillPlaying[0]
        else:
            playerId = random.choice(stillPlaying)
        return playerId

    def ballMovie2AI(self, cycleTime, avId, movie, spinMovie, ballInFrame, ballTouchedHoleFrame, ballFirstTouchedHoleFrame, commonObjectData):
        sentFromId = self.air.getAvatarIdFromSender()
        if sentFromId == self.trustedPlayerId:
            lastFrameNum = len(movie) - 2
            if lastFrameNum < 0:
                lastFrameNum = 0
            lastFrame = movie[lastFrameNum]
            lastPos = Vec3(lastFrame[1], lastFrame[2], lastFrame[3])
            self.ballPos[avId] = lastPos
            self.golfCourse.incrementScore(avId)
            for id in self.golfCourse.getStillPlayingAvIds():
                if not id == sentFromId:
                    self.sendUpdateToAvatarId(id, 'ballMovie2Client', [cycleTime, avId, movie, spinMovie, ballInFrame, ballTouchedHoleFrame, ballFirstTouchedHoleFrame, commonObjectData])

            if self.state == 'WaitPlayback' or self.state == 'WaitTee':
                self.notify.warning('ballMovie2AI requesting from %s to WaitPlayback' % self.state)
            self.request('WaitPlayback')
        else:
            if self.trustedPlayerId == None:
                return
            else:
                self.doAction()
        self.trustedPlayerId = None
        return

    def performReadyAction(self):
        avId = self.storeAction[0]
        if self.state == 'WaitPlayback':
            self.notify.debugStateCall(self)
            self.notify.debug('ignoring the postSwing for avId=%d since we are in WaitPlayback' % avId)
            return
        if avId == self.activeGolferId:
            self.golfCourse.incrementScore(self.activeGolferId)
        else:
            self.notify.warning('activGolferId %d not equal to sender avId %d' % (self.activeGolferId, avId))
        if avId not in self.golfCourse.drivingToons:
            position = self.ballPos[avId]
        else:
            position = Vec3(self.storeAction[3], self.storeAction[4], self.storeAction[5])
        self.useCommonObjectData(self.commonHoldData)
        newPos = self.trackRecordBodyFlight(self.ball, self.storeAction[1], self.storeAction[2], position, self.storeAction[6], self.storeAction[7])
        if self.state == 'WaitPlayback' or self.state == 'WaitTee':
            self.notify.warning('performReadyAction requesting from %s to WaitPlayback' % self.state)
        self.request('WaitPlayback')
        self.sendUpdate('ballMovie2Client', [self.storeAction[1], avId, self.recording, self.aVRecording, self.ballInHoleFrame, self.ballTouchedHoleFrame, self.ballFirstTouchedHoleFrame, self.commonHoldData])
        self.ballPos[avId] = newPos
        self.trustedPlayerId = None
        return

    def postResult(self, cycleTime, avId, recording, aVRecording, ballInHoleFrame, ballTouchedHoleFrame, ballFirstTouchedHoleFrame):
        pass

    def enterWaitSwing(self):
        pass

    def exitWaitSwing(self):
        pass

    def enterWaitTee(self):
        pass

    def exitWaitTee(self):
        pass

    def enterWaitPlayback(self):
        self.notify.debug('enterWaitPlayback')
        stillPlayingList = self.golfCourse.getStillPlayingAvIds()
        self.barrierPlayback = ToonBarrier('waitClientsPlayback', self.uniqueName('waitClientsPlayback'), stillPlayingList, 120, self.handleWaitPlaybackDone, self.handlePlaybackTimeout)

    def hasCurGolferReachedMaxSwing(self):
        strokes = self.golfCourse.getCurHoleScore(self.activeGolferId)
        maxSwing = self.holeInfo['maxSwing']
        retval = strokes >= maxSwing
        if retval:
            av = simbase.air.doId2do.get(self.activeGolferId)
            if av:
                if av.getUnlimitedSwing():
                    retval = False
        return retval

    def handleWaitPlaybackDone(self):
        if self.isCurBallInHole(self.activeGolferId) or self.hasCurGolferReachedMaxSwing():
            if self.activeGolferId:
                self.ballInHole(self.activeGolferId)
        else:
            self.selectNextGolfer()

    def isCurBallInHole(self, golferId):
        retval = False
        senderId = self.air.getAvatarIdFromSender()
        if golferId not in self.ballPos:
            self.notify.warning('golferId=%s not in self.ballPos=%s' % (golferId, self.ballPos))
            simbase.air.writeServerEvent('suspicious', senderId, 'isCurBallInHole golferId=%s not in self.ballPos=%s' % (golferId, self.ballPos))
            return False
        for holePos in self.holePositions:
            displacement = self.ballPos[golferId] - holePos
            length = displacement.length()
            self.notify.debug('hole %s length=%s' % (holePos, length))
            if length <= GolfGlobals.DistanceToBeInHole:
                retval = True
                break

        return retval

    def exitWaitPlayback(self):
        self.notify.debug('exitWaitPlayback')
        if hasattr(self, 'barrierPlayback') and self.barrierPlayback:
            self.barrierPlayback.cleanup()
            self.barrierPlayback = None
        return

    def enterCleanup(self):
        pass

    def exitCleanup(self):
        pass

    def handlePlaybackTimeout(self, task=None):
        self.notify.debug('handlePlaybackTimeout')
        self.handleWaitPlaybackDone()

    def getGolfCourseDoId(self):
        return self.golfCourse.doId

    def avatarDropped(self, avId):
        self.notify.warning('avId %d dropped, self.state=%s' % (avId, self.state))
        if self.barrierPlayback:
            self.barrierPlayback.clear(avId)
        else:
            if avId == self.trustedPlayerId:
                self.doAction()
            if avId == self.activeGolferId and not self.golfCourse.haveAllGolfersExited():
                self.selectNextGolfer()

    def setAvatarTee(self, chosenTee):
        golferId = self.air.getAvatarIdFromSender()
        self.teeChosen[golferId] = chosenTee
        self.ballPos[golferId] = self.teePositions[chosenTee]
        self.sendUpdate('setAvatarFinalTee', [golferId, chosenTee])
        self.sendUpdate('golfersTurn', [golferId])
        self.request('WaitSwing')

    def setBox(self, pos0, pos1, pos2, quat0, quat1, quat2, quat3, anV0, anV1, anV2, lnV0, lnV1, lnV2):
        self.sendUpdate('sendBox', [
         pos0, pos1, pos2, quat0, quat1, quat2, quat3, anV0, anV1, anV2, lnV0, lnV1, lnV2])

    def parseLocators(self, objectCollection, optional = 0):
        if optional and objectCollection.getNumPaths():
            if 'optionalMovers' in self.holeInfo:
                for optionalMoverId in self.holeInfo['optionalMovers']:
                    searchStr = 'optional_mover_' + str(optionalMoverId)
                    for objIndex in range(objectCollection.getNumPaths()):
                        object = objectCollection.getPath(objIndex)
                        if searchStr in object.getName():
                            self.fillLocator(objectCollection, objIndex)
                            break

        else:
            for index in range(objectCollection.getNumPaths()):
                self.fillLocator(objectCollection, index)

    def fillLocator(self, objectCollection, index):
        path = objectCollection[index]
        pathName = path.getName()
        pathArray = pathName.split('_')
        sizeX = None
        sizeY = None
        move = None
        type = None
        for subString in pathArray:
            if subString[:1] == 'X':
                dataString = subString[1:]
                dataString = dataString.replace('p', '.')
                sizeX = float(dataString)
            elif subString[:1] == 'Y':
                dataString = subString[1:]
                dataString = dataString.replace('p', '.')
                sizeY = float(dataString)
            elif subString[:1] == 'd':
                dataString = subString[1:]
                dataString = dataString.replace('p', '.')
                move = float(dataString)
            elif subString == 'mover':
                type = 4
            elif subString == 'windmillLocator':
                type = 3

        if type == 4 and move and sizeX and sizeY:
            self.createCommonObject(4, path.getPos(), path.getHpr(), sizeX, sizeY, move)
        elif type == 3:
            self.createCommonObject(3, path.getPos(), path.getHpr())
        return
