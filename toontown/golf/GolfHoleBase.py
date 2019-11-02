from direct.distributed import DistributedObjectAI
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from pandac.PandaModules import *
import DistributedPhysicsWorldAI
from direct.fsm.FSM import FSM
from toontown.ai.ToonBarrier import *
from toontown.golf import GolfGlobals
import random
import math

class GolfHoleBase:

    def __init__(self, canRender = 0):
        self.canRender = canRender
        self.recording = []
        self.aVRecording = []
        self.holePositions = []
        self.grayCount = 0
        self.skyContact = None
        self.lastSkyContactPoint = None
        self.doingRecording = 0
        self.backAmount = 270
        self.ballRocket = 0
        self.inCount = 0
        self.frame = 0
        self.onSlick = 0
        self.didHoleBreak = 0
        return

    def loadLevel(self):
        tm = self.holeInfo['terrainModel']
        self.terrainModel = loader.loadModel(tm)
        td = self.holeInfo['physicsData']
        if self.canRender:
            self.terrainModel.reparentTo(render)
        if self.canRender:
            self.terrainModel.find('**/softSurface').setBin('ground', 0)
        terrainData = self.terrainModel.find('**/softSurface')
        grassData = terrainData.findAllMatches('**/grass*')
        self.terrainData = []
        for index in range(grassData.getNumPaths()):
            someTerrainData = grassData[index]
            terrainDataOde = OdeTriMeshData(someTerrainData)
            self.meshDataList.append(terrainDataOde)
            terrainGeomOde = OdeTriMeshGeom(self.space, terrainDataOde)
            self.geomDataList.append(terrainGeomOde)
            terrainGeomOde.setCollideBits(BitMask32(4026531840L))
            terrainGeomOde.setCategoryBits(BitMask32(240))
            self.space.setSurfaceType(terrainGeomOde, GolfGlobals.GRASS_SURFACE)
            self.space.setCollideId(terrainGeomOde, 2)

        slickData = terrainData.findAllMatches('**/slick*')
        self.terrainData = []
        for index in range(slickData.getNumPaths()):
            someTerrainData = slickData[index]
            terrainDataOde = OdeTriMeshData(someTerrainData)
            self.meshDataList.append(terrainDataOde)
            terrainGeomOde = OdeTriMeshGeom(self.space, terrainDataOde)
            self.geomDataList.append(terrainGeomOde)
            terrainGeomOde.setCollideBits(BitMask32(4026531840L))
            terrainGeomOde.setCategoryBits(BitMask32(240))
            self.space.setSurfaceType(terrainGeomOde, GolfGlobals.SLICK_SURFACE)
            self.space.setCollideId(terrainGeomOde, GolfGlobals.SLICK_COLLIDE_ID)

        cupData = terrainData.find('**/hole*')
        cupData = OdeTriMeshData(cupData)
        self.meshDataList.append(cupData)
        cupGeom = OdeTriMeshGeom(self.space, cupData)
        self.geomDataList.append(cupGeom)
        cupGeom.setCollideBits(BitMask32(4026531840L))
        cupGeom.setCategoryBits(BitMask32(240))
        self.space.setSurfaceType(cupGeom, GolfGlobals.HOLE_SURFACE)
        self.space.setCollideId(cupGeom, GolfGlobals.HOLE_CUP_COLLIDE_ID)
        if self.canRender:
            self.golfBarrier = self.terrainModel.find('**/collision1')
            if not self.golfBarrier.isEmpty():
                golfBarrierCollection = self.terrainModel.findAllMatches('**/collision?')
                for i in xrange(golfBarrierCollection.getNumPaths()):
                    oneBarrier = golfBarrierCollection.getPath(i)
                    if oneBarrier != self.golfBarrier:
                        oneBarrier.wrtReparentTo(self.golfBarrier)

                self.golfBarrier.hide()
            else:
                self.notify.warning('Could not find collision1 node ---------')
        self.hardSurfaceNodePath = self.terrainModel.find('**/hardSurface')
        if self.canRender:
            self.terrainModel.find('**/hardSurface').setBin('ground', 0)
        self.loadBlockers()
        hardData = OdeTriMeshData(self.hardSurfaceNodePath)
        self.meshDataList.append(hardData)
        hardGeom = OdeTriMeshGeom(self.space, hardData)
        self.geomDataList.append(hardGeom)
        hardGeom.setCollideBits(BitMask32(4026531840L))
        hardGeom.setCategoryBits(BitMask32(240))
        self.space.setCollideId(hardGeom, 3)
        hardSurface = self.space.getSurfaceType(hardGeom)
        self.notify.debug('hardSurface = %s' % hardSurface)
        if self.notify.getDebug():
            self.notify.debug('self.hardGeom')
            hardGeom.write()
            self.notify.debug(' -')
        self.holeBottomNodePath = self.terrainModel.find('**/holebottom0')
        if self.holeBottomNodePath.isEmpty():
            self.holeBottomPos = Vec3(*self.holeInfo['holePos'][0])
        else:
            self.holeBottomPos = self.holeBottomNodePath.getPos()
        self.holePositions.append(self.holeBottomPos)

    def isBallInHole(self, ball):
        retval = False
        for holePos in self.holePositions:
            displacement = ball.getPosition() - holePos
            length = displacement.length()
            self.notify.debug('hole %s length=%s' % (holePos, length))
            if length <= GolfGlobals.DistanceToBeInHole * 0.5:
                retval = True
                break

        return retval

    def createRays(self):
        self.notify.debug('createRays')
        body = OdeBody(self.world)
        self.ballRay = OdeRayGeom(self.space, 50.0)
        self.ballRay.setBody(body)
        self.ballRay.setOffsetRotation(Mat3(1, 0, 0, 0, -1, 0, 0, 0, -1))
        self.ballRay.setOffsetPosition(0, 0, 0.0)
        self.ballRay.setCollideBits(BitMask32(16773375))
        self.ballRay.setCategoryBits(BitMask32(4278190080L))
        self.ballRayBody = body
        self.space.setCollideId(self.ballRay, GolfGlobals.OOB_RAY_COLLIDE_ID)
        self.rayList.append(self.ballRay)
        self.rayList.append(self.ballRayBody)
        self.skyRay = OdeRayGeom(self.space, 100.0)
        self.skyRay.setCollideBits(BitMask32(240))
        self.skyRay.setCategoryBits(BitMask32(0))
        self.skyRay.setRotation(Mat3(1, 0, 0, 0, -1, 0, 0, 0, -1))
        self.space.setCollideId(self.skyRay, GolfGlobals.SKY_RAY_COLLIDE_ID)
        self.rayList.append(self.skyRay)

    def delete(self):
        self.ballRay = None
        self.skyRay = None
        self.recording = None
        self.avRecording = None
        self.llv = None
        return

    def initRecord(self):
        del self.recording
        self.recording = []
        del self.aVRecording
        self.aVRecording = []
        self.skipFrame = 0.0
        self.frame = 0
        self.tXYMax = 1.0
        self.tZMax = 1.0
        self.tXYMin = 0.1
        self.tZMin = 0.1
        self.skyContact = 1
        self.doingRecording = 1
        self.ballRocket = 0
        self.inCount = 0
        self.ballInHoleFrame = 0
        self.ballTouchedHoleFrame = 0
        self.ballFirstTouchedHoleFrame = 0
        self.ballLastTouchedGrass = 0
        self.hasReset = 0
        self.resetAt = 100000
        self.greenIn = 0
        for key in self.commonObjectDict:
            self.commonObjectDict[key][2].enable()

    def checkCommonObjectsNeedPass(self):
        for index in self.commonObjectDict:
            if self.commonObjectDict[index][1] in [4]:
                return 1

        return 0

    def checkInRadius(self, ball):
        smallestDist = None
        for index in self.commonObjectDict:
            if self.commonObjectDict[index][1] in [4]:
                radius = self.commonObjectDict[index][8]
                mover = self.commonObjectDict[index][2]
                diffX = ball.getPosition()[0] - mover.getPosition()[0]
                diffY = ball.getPosition()[1] - mover.getPosition()[1]
                diffZ = ball.getPosition()[2] - mover.getPosition()[2]
                dist = math.sqrt(diffX * diffX + diffY * diffY + diffZ * diffZ)
                if dist < radius:
                    if not smallestDist or smallestDist[1] > dist:
                        smallestDist = [radius, dist]
                        self.notify.debug('Ball Pos %s\nMover Pos %s' % (ball.getPosition(), mover.getPosition()))

        return smallestDist

    def trackRecordBodyFlight(self, ball, cycleTime, power, startPos, dirX, dirY):
        self.notify.debug('trackRecordBodyFlight')
        self.ballInHoleFrame = 0
        self.ballTouchedHoleFrame = 0
        self.ballFirstTouchedHoleFrame = 0
        self.ballLastTouchedGrass = 0
        startTime = globalClock.getRealTime()
        self.notify.debug('start position %s' % startPos)
        self.swingTime = cycleTime
        frameCount = 0
        lift = 0
        startTime = GolfGlobals.BALL_CONTACT_FRAME / 24
        startFrame = startTime * self.FPS
        for frame in range(startFrame):
            self.simulate()
            self.setTimeIntoCycle(self.swingTime + float(frameCount) * self.DTAStep)
            frameCount += 1

        forceMove = 1500
        if power > 50:
            lift = 0
        self.didHoleBreak = 0
        ball.setPosition(startPos)
        ball.setLinearVel(0.0, 0.0, 0.0)
        ball.setAngularVel(0.0, 0.0, 0.0)
        ball.enable()
        self.preStep()
        self.simulate()
        self.postStep()
        ball.enable()
        ball.addForce(Vec3(dirX * forceMove * power / 100.0, dirY * forceMove * power / 100.0, lift))
        self.initRecord()
        self.llv = None
        self.lastSkyContactPoint = None
        ran = 0
        self.record(ball)
        self.comObjNeedPass = self.checkCommonObjectsNeedPass()
        self.notify.debug('self.comObjNeedPass %s' % self.comObjNeedPass)
        firstDisabled = -1
        reEnabled = 0
        lastFrameEnabled = 0
        checkFrames = self.FPS * (self.timingCycleLength + 1.0)
        hasPrinted = 0
        while ball.isEnabled() and len(self.recording) < 2100 or self.comObjNeedPass or len(self.recording) < 10:
            ran = 1
            if len(self.recording) > 2100 and not hasPrinted:
                self.notify.debug('recording too long %s' % len(self.recording))
                hasPrinted = 1
                ball.disable()
            self.preStep()
            self.simulate()
            self.setTimeIntoCycle(self.swingTime + float(frameCount) * self.DTAStep)
            frameCount += 1
            self.postStep()
            self.record(ball)
            if self.comObjNeedPass:
                if firstDisabled == -1 and not ball.isEnabled():
                    firstDisabled = self.frame
                    self.notify.debug('firstDisabled %s' % firstDisabled)
                    check = self.checkInRadius(ball)
                    if check == None:
                        self.comObjNeedPass = 0
                        self.notify.debug('out radius')
                    else:
                        self.notify.debug('in radius %s dist %s' % (check[0], check[1]))
                elif ball.isEnabled() and firstDisabled != -1 and not reEnabled:
                    reEnabled = self.frame
                    self.notify.debug('reEnabled %s' % reEnabled)
                if reEnabled:
                    if self.frame > reEnabled + checkFrames:
                        self.comObjNeedPass = 0
                        self.notify.debug('renable limit passed')
                elif self.frame > 2100 + checkFrames:
                    self.comObjNeedPass = 0
                    print 'recording limit passed comObj'
            if ball.isEnabled():
                lastFrameEnabled = self.frame

        self.notify.debug('lastFrameEnabled %s' % lastFrameEnabled)
        if lastFrameEnabled < 3:
            lastFrameEnabled = 3
        self.record(ball)
        self.notify.debug('Frames %s' % self.frame)
        midTime = globalClock.getRealTime()
        self.recording = self.recording[:lastFrameEnabled]
        self.aVRecording = self.aVRecording[:lastFrameEnabled]
        self.frame = lastFrameEnabled
        self.processRecording()
        self.processAVRecording()
        self.notify.debug('Recording End time %s cycle %s len %s avLen %s' % (self.timingSimTime,
         self.getCycleTime(),
         len(self.recording),
         len(self.aVRecording)))
        length = len(self.recording) - 1
        x = self.recording[length][1]
        y = self.recording[length][2]
        z = self.recording[length][3]
        endTime = globalClock.getRealTime()
        diffTime = endTime - startTime
        self.doingRecording = 0
        fpsTime = self.frame / diffTime
        self.notify.debug('Time Start %s Mid %s End %s Diff %s Fps %s frames %s' % (startTime,
         midTime,
         endTime,
         diffTime,
         fpsTime,
         self.frame))
        return Vec3(x, y, z)

    def record(self, ball):
        self.recording.append((self.frame,
         ball.getPosition()[0],
         ball.getPosition()[1],
         ball.getPosition()[2]))
        self.aVRecording.append((self.frame,
         ball.getAngularVel()[0],
         ball.getAngularVel()[1],
         ball.getAngularVel()[2]))
        if self.frame > 50 and not self.frame % 13:
            curFrame = self.recording[self.frame]
            pastFrame5 = self.recording[self.frame - 11]
            pastFrame10 = self.recording[self.frame - 34]
            currPosA = Vec3(curFrame[1], curFrame[2], curFrame[3])
            past5PosA = Vec3(pastFrame5[1], pastFrame5[2], pastFrame5[3])
            past10PosA = Vec3(pastFrame10[1], pastFrame10[2], pastFrame10[3])
            displacement1 = currPosA - past5PosA
            displacement2 = currPosA - past10PosA
            if displacement1.lengthSquared() < 0.002 and displacement2.lengthSquared() < 0.002 and not self.grayCount and not self.onSlick:
                ball.disable()
        self.frame += 1

    def preStep(self):
        if hasattr(self, 'ballRay'):
            bp = self.curGolfBall().getPosition()
            self.ballRayBody.setPosition(bp[0], bp[1], bp[2])
            self.skyRay.setPosition(bp[0], bp[1], 50.0)

    def getOrderedContacts(self, count):
        c0 = self.space.getContactId(count, 0)
        c1 = self.space.getContactId(count, 1)
        if c0 > c1:
            chold = c1
            c1 = c0
            c0 = chold
        return (c0, c1)

    def postStep(self):
        if self.canRender:
            self.translucentLastFrame = self.translucentCurFrame[:]
            self.translucentCurFrame = []
        self.onSlick = 0
        rayCount = 0
        skyRayHitPos = None
        ballRayHitPos = None
        bp = self.curGolfBall().getPosition()
        for count in range(self.colCount):
            c0, c1 = self.getOrderedContacts(count)
            x = self.space.getContactData(count * 3 + 0)
            y = self.space.getContactData(count * 3 + 1)
            z = self.space.getContactData(count * 3 + 2)
            if c0 == GolfGlobals.OOB_RAY_COLLIDE_ID or c1 == GolfGlobals.OOB_RAY_COLLIDE_ID:
                rayCount += 1
                if self.canRender:
                    if self.currentGolfer:
                        self.ballShadowDict[self.currentGolfer].setPos(x, y, z + 0.1)
                if c1 == GolfGlobals.GRASS_COLLIDE_ID or c1 == GolfGlobals.HARD_COLLIDE_ID:
                    if self.curGolfBall().getPosition()[2] < z + 0.2:
                        ballRayHitPos = Vec3(x, y, z)
            if c0 == GolfGlobals.OOB_RAY_COLLIDE_ID and c1 == GolfGlobals.SLICK_COLLIDE_ID:
                self.onSlick = 1
            elif c0 == GolfGlobals.OOB_RAY_COLLIDE_ID and c1 == GolfGlobals.HARD_COLLIDE_ID:
                self.onSlick = 1
            if c0 == GolfGlobals.GRASS_COLLIDE_ID and c1 == GolfGlobals.SKY_RAY_COLLIDE_ID:
                self.lastSkyContactPoint = (x, y, z)
                if self.curGolfBall().getPosition()[2] < z + 0.2 and rayCount == 0:
                    if self.skyContact in [1, 2]:
                        skyRayHitPos = Vec3(x, y, z)
                        self.skyContact += 1
            if self.doingRecording:
                if c0 == GolfGlobals.OOB_RAY_COLLIDE_ID or c1 == GolfGlobals.OOB_RAY_COLLIDE_ID:
                    rayCount += 1
                    if c1 == GolfGlobals.GRASS_COLLIDE_ID:
                        self.greenIn = self.frame
                        self.llv = self.curGolfBall().getLinearVel()
                elif GolfGlobals.BALL_COLLIDE_ID in [c0, c1] and GolfGlobals.HOLE_CUP_COLLIDE_ID in [c0, c1]:
                    zCon = self.space.getContactData(count * 3 + 2)
                    self.ballTouchedHoleFrame = self.frame
                    ballUndersideZ = self.curGolfBall().getPosition()[2] - 0.05
                    if zCon < ballUndersideZ:
                        if not self.ballInHoleFrame:
                            self.ballInHoleFrame = self.frame
                    if self.ballFirstTouchedHoleFrame < self.ballLastTouchedGrass:
                        self.ballFirstTouchedHoleFrame = self.frame
                    if self.isBallInHole(self.curGolfBall()) and self.didHoleBreak == 0:
                        self.comObjNeedPass = 0
                        ballLV = self.curGolfBall().getLinearVel()
                        ballAV = self.curGolfBall().getAngularVel()
                        self.curGolfBall().setLinearVel(0.5 * ballLV[0], 0.5 * ballLV[1], 0.5 * ballLV[2])
                        self.curGolfBall().setAngularVel(0.5 * ballAV[0], 0.5 * ballAV[1], 0.5 * ballAV[2])
                        self.notify.debug('BALL IN THE HOLE!!! FOO!')
                        self.didHoleBreak = 1
                        return
                elif GolfGlobals.BALL_COLLIDE_ID in [c0, c1] and GolfGlobals.GRASS_COLLIDE_ID in [c0, c1]:
                    if self.ballInHoleFrame:
                        self.ballInHoleFrame = 0
                        self.notify.debug('setting ballInHoleFrame=0')
                    self.ballLastTouchedGrass = self.frame
            elif self.canRender:
                if c0 == GolfGlobals.TOON_RAY_COLLIDE_ID or c1 == GolfGlobals.TOON_RAY_COLLIDE_ID:
                    x = self.space.getContactData(count * 3 + 0)
                    y = self.space.getContactData(count * 3 + 1)
                    z = self.space.getContactData(count * 3 + 2)
                    self.toonRayCollisionCallback(x, y, z)
                if GolfGlobals.CAMERA_RAY_COLLIDE_ID in [c0, c1] and GolfGlobals.WINDMILL_BASE_COLLIDE_ID in [c0, c1]:
                    self.translucentCurFrame.append(self.windmillFanNodePath)
                    self.translucentCurFrame.append(self.windmillBaseNodePath)
                if GolfGlobals.BALL_COLLIDE_ID in [c0, c1] and GolfGlobals.GRASS_COLLIDE_ID not in [c0, c1]:
                    self.handleBallHitNonGrass(c0, c1)

        if not self.curGolfBall().isEnabled():
            return
        if rayCount == 0:
            self.notify.debug('out of bounds detected!')
            self.grayCount += 1
            self.outCommon = self.getCommonObjectData()
            self.inCount = 0
            if skyRayHitPos:
                self.curGolfBall().setPosition(skyRayHitPos[0], skyRayHitPos[1], skyRayHitPos[2] + 0.27)
                self.notify.debug('SKY RAY ADJUST?')
        else:
            if self.grayCount > 1:
                self.notify.debug('Back in bounds')
            self.grayCount = 0
            self.inCount += 1
            if ballRayHitPos:
                self.curGolfBall().setPosition(ballRayHitPos[0], ballRayHitPos[1], ballRayHitPos[2] + 0.245)
                ballRayHitPos = None
                if self.doingRecording:
                    self.notify.debug('BALL RAY ADJUST!')
                    self.notify.debug('%s' % self.curGolfBall().getLinearVel())
        if self.ballRocket > 0 and self.inCount > 1:
            self.ballRocket -= 1
            rocketVel = self.curGolfBall().getLinearVel()
            self.curGolfBall().setLinearVel(2.0 * rocketVel[0], 2.0 * rocketVel[1], 2.0 * rocketVel[2])
            self.notify.debug('ROCKET!!!!')
        if self.grayCount > self.backAmount and self.doingRecording:
            if self.greenIn > 2:
                self.greenIn -= 2
            if self.greenIn > self.resetAt:
                self.greenIn = self.resetAt - 10
            if self.greenIn < 0 or self.hasReset > 3:
                self.greenIn = 0
            self.hasReset += 1
            self.notify.debug('BALL RESET frame %s greenIn %s resetAt %s' % (self.frame, self.greenIn, self.resetAt))
            self.useCommonObjectData(self.outCommon)
            self.curGolfBall().setPosition(self.recording[self.greenIn][1], self.recording[self.greenIn][2], self.recording[self.greenIn][3] + 0.27)
            self.curGolfBall().setAngularVel(0, 0, 0)
            if self.hasReset < 3 and self.llv:
                self.ballRocket += 1
                self.notify.debug(' BRAKE!!!!')
                self.curGolfBall().setLinearVel(0.5 * self.llv[0], 0.5 * self.llv[1], 0.5 * self.llv[2])
            else:
                self.notify.debug('back disable %s' % self.frame)
                if self.lastSkyContactPoint:
                    self.curGolfBall().setPosition(self.lastSkyContactPoint[0], self.lastSkyContactPoint[1], self.lastSkyContactPoint[2] + 0.27)
                self.curGolfBall().setLinearVel(0, 0, 0)
                self.curGolfBall().disable()
            self.recording = self.recording[:self.greenIn]
            self.aVRecording = self.aVRecording[:self.greenIn]
            self.frame = self.greenIn
            self.resetAt = self.greenIn
            self.grayCount = 0
            if self.ballFirstTouchedHoleFrame > self.frame:
                self.notify.debug('reseting first touched hole, self.frame=%d self.ballFirstTouchedHoleFrame=%d' % (self.frame, self.ballFirstTouchedHoleFrame))
                self.ballFirstTouchedHoleFrame = 0
            if self.ballLastTouchedGrass > self.frame:
                self.ballLastTouchedGrass = 0
        return

    def processRecording(self, errorMult = 1.0):
        self.notify.debug('processRecording')
        lastFrame = self.recording[len(self.recording) - 1][0]
        countRemovals = 0
        for frame in self.recording:
            if frame[0] == 0 or frame[0] == lastFrame:
                pass
            else:
                index = self.recording.index(frame)
                prevFrame = self.recording[index - 1]
                nextFrame = self.recording[index + 1]
                if self.predict(frame, prevFrame, nextFrame, errorMult):
                    self.recording.remove(frame)
                    countRemovals += 1

        if countRemovals > 5:
            self.processRecording()
        elif len(self.recording) > 120:
            self.processRecording(errorMult * 1.25)
        else:
            for frame in self.recording:
                pass

    def processAVRecording(self, errorMult = 1.0, trials = 0):
        self.notify.debug('processAVRecording')
        lastFrame = self.recording[len(self.recording) - 1][0]
        countRemovals = 0
        countTrials = trials
        for frame in self.aVRecording:
            if frame[0] == 0 or frame[0] == lastFrame:
                pass
            else:
                index = self.aVRecording.index(frame)
                prevFrame = self.aVRecording[index - 1]
                nextFrame = self.aVRecording[index + 1]
                if self.predictAV(frame, prevFrame, nextFrame, errorMult):
                    self.aVRecording.remove(frame)
                    countRemovals += 1
                else:
                    countTrials += 1

        if countRemovals > 5:
            self.processAVRecording(errorMult, countTrials)
        elif len(self.aVRecording) > 80:
            self.processAVRecording(errorMult * 1.25, countTrials)
        else:
            for frame in self.aVRecording:
                pass

    def predict(self, frame, sourceFrame, destFrame, errorMult = 1.0):
        tXY = 0.05 * errorMult
        tZ = 0.05 * errorMult
        projLength = destFrame[0] - sourceFrame[0]
        projPen = destFrame[0] - frame[0]
        propSource = float(projPen) / float(projLength)
        propDest = 1.0 - propSource
        projX = sourceFrame[1] * propSource + destFrame[1] * propDest
        projY = sourceFrame[2] * propSource + destFrame[2] * propDest
        projZ = sourceFrame[3] * propSource + destFrame[3] * propDest
        varX = abs(projX - frame[1])
        varY = abs(projY - frame[2])
        varZ = abs(projZ - frame[3])
        if varX > tXY or varY > tXY or varZ > tZ:
            return 0
        else:
            return 1

    def predictAV(self, frame, sourceFrame, destFrame, errorMult = 1.0):
        tXYZ = 1.5 * errorMult
        projLength = destFrame[0] - sourceFrame[0]
        projPen = destFrame[0] - frame[0]
        propSource = float(projPen) / float(projLength)
        propDest = 1.0 - propSource
        projX = sourceFrame[1] * propSource + destFrame[1] * propDest
        projY = sourceFrame[2] * propSource + destFrame[2] * propDest
        projZ = sourceFrame[3] * propSource + destFrame[3] * propDest
        varX = abs(projX - frame[1])
        varY = abs(projY - frame[2])
        varZ = abs(projZ - frame[3])
        if varX > tXYZ or varY > tXYZ or varZ > tXYZ:
            return 0
        else:
            return 1

    def handleBallHitNonGrass(self, c0, c1):
        pass
