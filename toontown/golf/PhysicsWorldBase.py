from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from pandac.PandaModules import *
from math import *
import math
from direct.fsm.FSM import FSM
from toontown.minigame import ArrowKeys
from direct.showbase import PythonUtil
from direct.task import Task
from direct.distributed.ClockDelta import *
import BuildGeometry
from toontown.golf import GolfGlobals
import random, time

def scalp(vec, scal):
    vec0 = vec[0] * scal
    vec1 = vec[1] * scal
    vec2 = vec[2] * scal
    vec = Vec3(vec0, vec1, vec2)


def length(vec):
    return sqrt(vec[0] ** 2 + vec[1] ** 2 + vec[2] ** 2)


class PhysicsWorldBase:
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPhysicsWorld')

    def __init__(self, canRender = 0):
        self.canRender = canRender
        self.world = OdeWorld()
        self.space = OdeSimpleSpace()
        self.contactgroup = OdeJointGroup()
        self.bodyList = []
        self.geomList = []
        self.massList = []
        self.rayList = []
        self.showContacts = 0
        self.jointMarkers = []
        self.jointMarkerCount = 64
        self.meshDataList = []
        self.geomDataList = []
        self.commonObjectInfoDict = {}
        self.maxColCount = 0
        if self.canRender:
            self.odePandaRelationList = self.bodyList
            self.root = render.attachNewNode('physics root node')
        else:
            self.root = NodePath('physics root node')
        self.placerNode = self.root.attachNewNode('Placer')
        self.subPlacerNode = self.placerNode.attachNewNode('Placer Sub Node')
        self.commonObjectDict = {}
        self.commonId = 0
        self.worldAttach = self.root.attachNewNode('physics geom attach point')
        self.timingCycleLength = 10.0
        self.timingCycleOffset = 0.0
        self.timingSimTime = 0.0
        self.FPS = 90.0
        self.refFPS = 60.0
        self.DTAStep = 1.0 / self.FPS
        self.refCon = 1.2

    def delete(self):
        self.notify.debug('Max Collision Count was %s' % self.maxColCount)
        self.stopSim()
        self.commonObjectDict = None
        if self.canRender:
            for pair in self.odePandaRelationList:
                pair[0].remove()
                pair[1].destroy()

            self.odePandaRelationList = None
        else:
            for body in self.bodyList:
                body[1].destroy()

            self.bodyList = None
        for mass in self.massList:
            mass = None

        for geom in self.geomList:
            geom.destroy()
            geom = None

        for ray in self.rayList:
            ray.destroy()
            ray = None

        self.placerNode.remove()
        self.root.remove()
        for marker in self.jointMarkers:
            marker.remove()

        self.jointMarkers = None
        for data in self.geomDataList:
            data.destroy()

        for data in self.meshDataList:
            data.destroy()

        self.floor.destroy()
        self.floor = None
        self.contactgroup.empty()
        self.world.destroy()
        self.space.destroy()
        self.world = None
        self.space = None
        return

    def setupSimulation(self):
        self.world.setAutoDisableFlag(0)
        self.world.setAutoDisableLinearThreshold(0.15)
        self.world.setAutoDisableAngularThreshold(0.15)
        self.world.setAutoDisableSteps(2)
        self.world.setGravity(0, 0, -25)
        self.world.setErp(0.8)
        self.world.setCfm(1e-05)
        self.world.initSurfaceTable(5)
        self.world.setSurfaceEntry(0, 0, 150, 0.05, 0.1, 0.9, 1e-05, 0.0, 0.4 / self.refCon)
        self.world.setSurfaceEntry(1, 1, 1500, 0.05, 0.1, 0.9, 1e-05, 0.0, 0.001 / self.refCon)
        self.world.setSurfaceEntry(2, 2, 150, 0.05, 0.1, 0.9, 1e-05, 0.0, 0.4 / self.refCon)
        self.world.setSurfaceEntry(0, 2, 150, 0.05, 0.1, 0.9, 1e-05, 0.0, 0.4 / self.refCon)
        self.world.setSurfaceEntry(0, 3, 150, 0.0, 0.1, 0.9, 1e-05, 0.0, 0.4 / self.refCon)
        self.world.setSurfaceEntry(1, 3, 150, 0.0, 99.1, 0.9, 1e-05, 0.0, 1.0 / self.refCon)
        self.world.setSurfaceEntry(2, 3, 150, 0.0, 9.1, 0.9, 1e-05, 0.0, 0.4 / self.refCon)
        self.world.setSurfaceEntry(3, 3, 150, 0.0, 9.1, 0.9, 1e-05, 0.0, 0.4 / self.refCon)
        self.world.setSurfaceEntry(4, 4, 150, 0.0, 9.1, 0.9, 1e-05, 0.0, 0.4 / self.refCon)
        self.world.setSurfaceEntry(1, 4, 150, 0.0, 99.1, 0.9, 1e-05, 0.0, 0.001 / self.refCon)
        self.world.setSurfaceEntry(pos1=0, pos2=1, mu=80, bounce=0.15, bounce_vel=0.1, soft_erp=0.9, soft_cfm=1e-05, slip=0.0, dampen=0.35 / self.refCon)
        self.world.setSurfaceEntry(pos1=2, pos2=1, mu=1500, bounce=0.9, bounce_vel=0.01, soft_erp=0.9, soft_cfm=1e-05, slip=0.0, dampen=0.001 / self.refCon)
        self.floor = OdePlaneGeom(self.space, Vec4(0.0, 0.0, 1.0, -20.0))
        self.floor.setCollideBits(BitMask32(0))
        self.floor.setCategoryBits(BitMask32(3840))
        self.space.setAutoCollideWorld(self.world)
        self.space.setAutoCollideJointGroup(self.contactgroup)
        self.world.setQuickStepNumIterations(8)
        self.DTA = 0.0
        self.frameCounter = 0
        if self.canRender:
            for count in range(self.jointMarkerCount):
                testMarker = render.attachNewNode('Joint Marker')
                ballmodel = loader.loadModel('phase_3/models/misc/sphere')
                ballmodel.reparentTo(testMarker)
                ballmodel.setScale(0.1)
                testMarker.setPos(0.0, 0.0, -100.0)
                self.jointMarkers.append(testMarker)

    def setTimingCycleLength(self, time):
        self.timingCycleLength = time

    def getTimingCycleLength(self):
        return self.timingCycleLength

    def getCycleTime(self, doprint = 0):
        cycleTime = (globalClock.getRealTime() + self.timingCycleOffset) % self.timingCycleLength
        if doprint:
            print 'Get Cycle Time %s' % cycleTime
        return cycleTime

    def setTimeIntoCycle(self, time, doprint = 0):
        trueCycleTime = globalClock.getRealTime() % self.timingCycleLength
        self.timingCycleOffset = time - trueCycleTime
        if doprint:
            self.notify.debug('Set Cycle Time %s' % self.timingCycleOffset)
            self.notify.debug('SET cycle time %s' % ((globalClock.getRealTime() + self.timingCycleOffset) % self.timingCycleLength))

    def getSimCycleTime(self):
        return
        return self.timingSimTime % self.timingCycleLength

    def startSim(self):
        taskMgr.add(self.__simulationTask, 'simulation task')

    def stopSim(self):
        taskMgr.remove('simulation task')

    def __simulationTask(self, task):
        self.DTA += globalClock.getDt()
        self.frameCounter += 1
        if self.frameCounter >= 10:
            self.frameCounter = 0
        startTime = globalClock.getRealTime()
        colCount = 0
        while self.DTA >= self.DTAStep:
            self.DTA -= self.DTAStep
            self.preStep()
            self.simulate()
            self.postStep()

        if self.canRender:
            self.placeBodies()
        if self.frameCounter == 0:
            endTime = globalClock.getRealTime() - startTime
        return task.cont

    def simulate(self):
        self.colCount = self.space.autoCollide()
        if self.maxColCount < self.colCount:
            self.maxColCount = self.colCount
            self.notify.debug('New Max Collision Count %s' % self.maxColCount)
        self.world.quickStep(self.DTAStep)
        for bodyPair in self.bodyList:
            self.world.applyDampening(self.DTAStep, bodyPair[1])

        self.contactgroup.empty()
        self.commonObjectControl()
        self.timingSimTime = self.timingSimTime + self.DTAStep

    def placeBodies(self):
        for pair in self.odePandaRelationList:
            pandaNodePathGeom = pair[0]
            odeBody = pair[1]
            if pandaNodePathGeom:
                pandaNodePathGeom.setPos(odeBody.getPosition())
                rotation = odeBody.getRotation() * (180.0 / math.pi)
                pandaNodePathGeom.setQuat(Quat(odeBody.getQuaternion()[0], odeBody.getQuaternion()[1], odeBody.getQuaternion()[2], odeBody.getQuaternion()[3]))

    def preStep(self):
        pass

    def postStep(self):
        if self.showContacts and self.canRender:
            for count in range(self.jointMarkerCount):
                pandaNodePathGeom = self.jointMarkers[count]
                if count < self.colCount:
                    pandaNodePathGeom.setPos(self.space.getContactData(count * 3 + 0), self.space.getContactData(count * 3 + 1), self.space.getContactData(count * 3 + 2))
                else:
                    pandaNodePathGeom.setPos(0.0, 0.0, -100.0)

    def commonObjectControl(self):
        time = self.getCycleTime()
        for key in self.commonObjectDict:
            if key not in self.commonObjectInfoDict:
                self.commonObjectInfoDict[key] = None
            entry = self.commonObjectDict[key]
            if entry[1] in [2, 4]:
                type = entry[1]
                body = entry[2]
                motor = entry[3]
                timeData = entry[4]
                forceData = entry[5]
                eventData = entry[6]
                model = entry[7]
                force = 0.0
                for index in range(len(timeData)):
                    if index == len(timeData) - 1 and timeData[index] < time or timeData[index] < time and timeData[index + 1] > time:
                        force = forceData[index]
                        event = eventData[index]
                        if event != self.commonObjectInfoDict[key]:
                            self.commonObjectEvent(key, model, type, force, event)
                            self.commonObjectInfoDict[key] = event

                motor.setParamVel(force)

        return

    def commonObjectEvent(self, key, model, type, force, event):
        self.notify.debug('commonObjectForceEvent %s %s %s %s %s' % (key,
         model,
         type,
         force,
         event))

    def getCommonObjectData(self):
        objectStream = [(0,
          0,
          self.getCycleTime(),
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0)]
        for key in self.commonObjectDict:
            objectPair = self.commonObjectDict[key]
            object = objectPair[2]
            pos3 = object.getPosition()
            quat4 = object.getQuaternion()
            anV3 = object.getAngularVel()
            lnV3 = object.getLinearVel()
            data = (objectPair[0],
             objectPair[1],
             pos3[0],
             pos3[1],
             pos3[2],
             quat4[0],
             quat4[1],
             quat4[2],
             quat4[3],
             anV3[0],
             anV3[1],
             anV3[2],
             lnV3[0],
             lnV3[1],
             lnV3[2])
            objectStream.append(data)

        if len(objectStream) <= 1:
            data = (0, 99, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            objectStream.append(data)
        return objectStream

    def useCommonObjectData(self, objectData, enable = 1):
        if not objectData:
            return
        if objectData[1][1] == 99:
            return
        time = objectData[0]
        self.setTimeIntoCycle(time[2])
        if time[2] > self.timingCycleLength:
            pass
        for dataIndex in range(1, len(objectData)):
            data = objectData[dataIndex]
            commonObject = self.commonObjectDict[data[0]]
            commonObject[2].setPosition(data[2], data[3], data[4])
            commonObject[2].setQuaternion(Quat(data[5], data[6], data[7], data[8]))
            commonObject[2].setAngularVel(data[9], data[10], data[11])
            commonObject[2].setLinearVel(data[12], data[13], data[14])
            if enable:
                commonObject[2].enable()
            else:
                commonObject[2].disable()

    def createCommonObject(self, type, commonId, pos, hpr, sizeX = 0, sizeY = 0, moveDistance = 0):
        if commonId == None:
            commonId = self.commonId
            self.commonId += 1
        vPos = Point3(float(pos[0]), float(pos[1]), float(pos[2]))
        vHpr = Vec3(float(hpr[0]), float(hpr[1]), float(hpr[2]))
        rHpr = Vec3(float(hpr[0]), float(hpr[1]), float(hpr[2]))
        self.placerNode.setHpr(vHpr)
        self.placerNode.setPos(vPos)
        if type == 0:
            model, box = self.createBox(self.world, self.space, 10.0, 5.0, 5.0, 5.0)
            box.setPosition(vPos)
            self.placerNode.setHpr(vHpr)
            box.setQuaternion(self.placerNode.getQuat())
            self.commonObjectDict[commonId] = (commonId, type, box)
        elif type == 1:
            model, cross = self.createCross(self.world, self.space, 1.0, 3.0, 12.0, 2.0, 2)
            motor = OdeHingeJoint(self.world)
            cross.setPosition(vPos)
            cross.setQuaternion(self.placerNode.getQuat())
            ourAxis = render.getRelativeVector(self.placerNode, Vec3(0, 0, 1))
            motor.setParamVel(1.5)
            motor.setParamFMax(500000000.0)
            boxsize = Vec3(1.0, 1.0, 1.0)
            motor.attach(0, cross)
            motor.setAnchor(vPos)
            motor.setAxis(ourAxis)
            self.cross = cross
            cross.enable()
            self.commonObjectDict[commonId] = (commonId, type, cross)
        elif type == 2:
            ourAxis = render.getRelativeVector(self.placerNode, Vec3(0, 0, 1))
            model, box = self.createBox(self.world, self.space, 10.0, 5.0, 5.0, 5.0, 2)
            box.setPosition(vPos)
            box.setQuaternion(self.placerNode.getQuat())
            motor = OdeSliderJoint(self.world)
            motor.attach(box, 0)
            motor.setAxis(ourAxis)
            motor.setParamVel(3.0)
            motor.setParamFMax(5000000.0)
            motor.setParamHiStop(10.0)
            motor.setParamLoStop(-10.0)
            timeData = (0.0, 5.0)
            forceData = (3.0, -3.0)
            eventData = (1, 2)
            self.commonObjectDict[commonId] = (commonId,
             type,
             box,
             motor,
             timeData,
             forceData,
             eventData,
             model)
        elif type == 3:
            vPos = Point3(float(pos[0]), float(pos[1]), float(pos[2]))
            vHpr = Vec3(float(hpr[0]), float(hpr[1]), float(hpr[2]))
            self.placerNode.setHpr(vHpr)
            self.placerNode.setPos(vPos)
            self.subPlacerNode.setPos(0, 0, 0)
            if self.canRender:
                myModel = loader.loadModel('phase_6/models/golf/golf_windmill_b')
            else:
                myModel = loader.loadModel('phase_6/models/golf/golf_windmill_b.bam')
            myModel.reparentTo(self.root)
            myModel.setPos(vPos)
            myModel.setHpr(vHpr)
            millFan = myModel.find('**/windmillFan0')
            millBase = myModel.find('**/arm')
            rod = myModel.find('**/rod')
            rod.wrtReparentTo(millBase)
            self.windmillFanNodePath = millFan
            self.windmillBaseNodePath = millBase
            millData = OdeTriMeshData(millBase)
            millGeom = OdeTriMeshGeom(self.space, millData)
            self.meshDataList.append(millData)
            millGeom.setPosition(self.subPlacerNode.getPos(self.root))
            millGeom.setQuaternion(self.subPlacerNode.getQuat())
            millGeom.setCollideBits(BitMask32(251658240))
            millGeom.setCategoryBits(BitMask32(8388608))
            self.space.setCollideId(millGeom, 8)
            vPos = Point3(float(pos[0]), float(pos[1]), float(pos[2]) + 5)
            vHpr = Vec3(float(hpr[0]), float(hpr[1] + 90), float(hpr[2]) - 90)
            self.placerNode.setHpr(vHpr)
            self.placerNode.setPos(vPos)
            self.subPlacerNode.setPos(-1, 0, 0.0)
            model, cross = self.createPinWheel(self.world, self.space, 10.0, 1.6, 4.0, 0.6, 5, 3.7, 1.2, 1, millFan, (0, 0, 90), (-4.6, -0.5, -0.25), 20)
            self.placerNode.setHpr(vHpr)
            self.placerNode.setPos(vPos)
            self.subPlacerNode.setPos(-1, 0, 0.0)
            motor = OdeHingeJoint(self.world)
            cross.setPosition(self.subPlacerNode.getPos(self.root))
            cross.setQuaternion(self.placerNode.getQuat())
            ourAxis = self.root.getRelativeVector(self.subPlacerNode, Vec3(0, 0, 1))
            motor.setParamVel(1.0)
            motor.setParamFMax(50000.0)
            boxsize = Vec3(1.0, 1.0, 1.0)
            motor.attach(0, cross)
            motor.setAnchor(self.subPlacerNode.getPos(self.root))
            motor.setAxis(ourAxis)
            self.cross = cross
            cross.enable()
            self.commonObjectDict[commonId] = (commonId, type, cross)
        elif type == 4:
            ourAxis = self.root.getRelativeVector(self.placerNode, Vec3(0, 1, 0))
            model, box = self.createBox(self.world, self.space, 50.0, sizeX, sizeY, 1.0, 2)
            box.setPosition(vPos)
            box.setQuaternion(self.placerNode.getQuat())
            motor = OdeSliderJoint(self.world)
            motor.attach(box, 0)
            motor.setAxis(ourAxis)
            motor.setParamVel(moveDistance / 4.0)
            motor.setParamFMax(25000.0)
            motor.setParamHiStop(moveDistance)
            motor.setParamLoStop(0)
            timeData = (0.0, 1.0, 5.0, 6.0)
            forceData = (-moveDistance / 4.0,
             moveDistance / 4.0,
             moveDistance / 4.0,
             -moveDistance / 4.0)
            eventData = (-1, 1, -2, 2)
            radius = moveDistance + sizeY * 0.5
            self.commonObjectDict[commonId] = (commonId,
             type,
             box,
             motor,
             timeData,
             forceData,
             eventData,
             model,
             radius)
        return [type,
         commonId,
         (pos[0], pos[1], pos[2]),
         (hpr[0], hpr[1], hpr[2]),
         sizeX,
         sizeY,
         moveDistance]

    def createSphere(self, world, space, density, radius, ballIndex = None):
        self.notify.debug('create sphere index %s' % ballIndex)
        body = OdeBody(world)
        M = OdeMass()
        M.setSphere(density, radius)
        body.setMass(M)
        body.setPosition(0, 0, -100)
        geom = OdeSphereGeom(space, radius)
        self.space.setSurfaceType(geom, 1)
        self.notify.debug('collide ID is %s' % self.space.setCollideId(geom, 42))
        self.massList.append(M)
        self.geomList.append(geom)
        if ballIndex == 1:
            self.notify.debug('1')
            geom.setCollideBits(BitMask32(16777215))
            geom.setCategoryBits(BitMask32(4278190080L))
        elif ballIndex == 2:
            self.notify.debug('2')
            geom.setCollideBits(BitMask32(16777215))
            geom.setCategoryBits(BitMask32(4278190080L))
        elif ballIndex == 3:
            self.notify.debug('3')
            geom.setCollideBits(BitMask32(16777215))
            geom.setCategoryBits(BitMask32(4278190080L))
        elif ballIndex == 4:
            self.notify.debug('4')
            geom.setCollideBits(BitMask32(16777215))
            geom.setCategoryBits(BitMask32(4278190080L))
        else:
            geom.setCollideBits(BitMask32(4294967295L))
            geom.setCategoryBits(BitMask32(4294967295L))
        geom.setBody(body)
        if self.notify.getDebug():
            self.notify.debug('golf ball geom id')
            geom.write()
            self.notify.debug(' -')
        self.notify.debug('Collide Bits %s' % geom.getCollideBits())
        if self.canRender:
            testball = render.attachNewNode('Ball Holder')
            ballmodel = loader.loadModel('phase_6/models/golf/golf_ball')
            ballmodel.reparentTo(testball)
            ballmodel.setColor(*GolfGlobals.PlayerColors[ballIndex - 1])
            testball.setPos(0, 0, -100)
            self.odePandaRelationList.append((testball, body))
        else:
            testball = None
            self.bodyList.append((None, body))
        return (testball, body, geom)

    def createBox(self, world, space, density, lx, ly, lz, colOnlyBall = 0):
        body = OdeBody(self.world)
        M = OdeMass()
        M.setSphere(density, 0.3 * (lx + ly + lz))
        body.setMass(M)
        boxsize = Vec3(lx, ly, lz)
        geom = OdeBoxGeom(space, boxsize)
        geom.setBody(body)
        self.space.setSurfaceType(geom, 0)
        self.space.setCollideId(geom, 7)
        self.massList.append(M)
        self.geomList.append(geom)
        if colOnlyBall:
            geom.setCollideBits(BitMask32(251658240))
            geom.setCategoryBits(BitMask32(0))
        elif colOnlyBall == 2:
            geom.setCollideBits(BitMask32(0))
            geom.setCategoryBits(BitMask32(0))
        if self.canRender:
            color = random.choice([Vec4(1.0, 0.0, 0.5, 1.0), Vec4(0.5, 0.5, 1.0, 1.0), Vec4(0.5, 1.0, 0.5, 1.0)])
            boxsize = Vec3(lx, ly, lz)
            boxNodePathGeom, t1, t2 = BuildGeometry.addBoxGeom(self.worldAttach, lx, ly, lz, color, 1)
            boxNodePathGeom.setPos(0, 0, -100)
            self.odePandaRelationList.append((boxNodePathGeom, body))
        else:
            boxNodePathGeom = None
            self.bodyList.append((None, body))
        return (boxNodePathGeom, body)

    def createCross(self, world, space, density, lx, ly, lz, colOnlyBall = 0, attachedGeo = None, aHPR = None, aPos = None):
        body = OdeBody(self.world)
        M = OdeMass()
        M.setBox(density, lx, ly, lz)
        body.setMass(M)
        body.setFiniteRotationMode(1)
        boxsize = Vec3(lx, ly, lz)
        boxsize2 = Vec3(ly, lx, lz)
        geom = OdeBoxGeom(space, boxsize)
        geom.setBody(body)
        self.space.setSurfaceType(geom, 0)
        self.space.setCollideId(geom, 13)
        geom2 = OdeBoxGeom(space, boxsize2)
        geom2.setBody(body)
        self.space.setSurfaceType(geom2, 0)
        self.space.setCollideId(geom2, 26)
        self.massList.append(M)
        self.geomList.append(geom)
        self.geomList.append(geom2)
        self.odePandaRelationList.append((boxNodePathGeom, body))
        if colOnlyBall == 1:
            geom.setCollideBits(BitMask32(251658240))
            geom.setCategoryBits(BitMask32(0))
            geom2.setCollideBits(BitMask32(251658240))
            geom2.setCategoryBits(BitMask32(0))
        elif colOnlyBall == 2:
            geom.setCollideBits(BitMask32(0))
            geom.setCategoryBits(BitMask32(0))
            geom2.setCollideBits(BitMask32(0))
            geom2.setCategoryBits(BitMask32(0))
        if self.canRender:
            boxNodePathGeom, t1, t2 = BuildGeometry.addBoxGeom(self.worldAttach, lx, ly, lz, Vec4(1.0, 1.0, 1.0, 1.0), 1)
            boxNodePathGeom.setPos(0, 0, -100)
            boxNodePathGeom2, t1, t2 = BuildGeometry.addBoxGeom(boxNodePathGeom, ly, lx, lz, Vec4(1.0, 1.0, 1.0, 1.0), 1)
            boxNodePathGeom2.setPos(0, 0, 0)
            if attachedGeo:
                attachedGeo.reparentTo(boxNodePathGeom)
                attachedGeo.setHpr(0, 0, 90)
                attachedGeo.setPos(-4.8, 0, -2.0)
            self.odePandaRelationList.append((boxNodePathGeom, body))
        else:
            boxNodePathGeom = None
            self.bodyList.append((None, body))
        return (boxNodePathGeom, body)

    def createCross2(self, world, space, density, lx, ly, lz, latSlide, colOnlyBall = 0, attachedGeo = None, aHPR = None, aPos = None):
        body = OdeBody(self.world)
        M = OdeMass()
        M.setBox(density, lx, ly, lz)
        body.setMass(M)
        body.setFiniteRotationMode(1)
        boxsize = Vec3(lx, ly * 0.5, lz)
        boxsize2 = Vec3(ly * 0.5, lx, lz)
        geom = OdeBoxGeom(space, boxsize)
        geom.setBody(body)
        geom.setOffsetPosition(-latSlide, ly * 0.25, 0)
        self.space.setSurfaceType(geom, 0)
        self.space.setCollideId(geom, 13)
        geom2 = OdeBoxGeom(space, boxsize2)
        geom2.setBody(body)
        geom2.setOffsetPosition(ly * 0.25, latSlide, 0)
        self.space.setSurfaceType(geom2, 0)
        self.space.setCollideId(geom2, 13)
        geom3 = OdeBoxGeom(space, boxsize)
        geom3.setBody(body)
        geom3.setOffsetPosition(latSlide, -ly * 0.25, 0)
        self.space.setSurfaceType(geom3, 0)
        self.space.setCollideId(geom3, 13)
        geom4 = OdeBoxGeom(space, boxsize2)
        geom4.setBody(body)
        geom4.setOffsetPosition(-ly * 0.25, -latSlide, 0)
        self.space.setSurfaceType(geom4, 0)
        self.space.setCollideId(geom4, 13)
        self.massList.append(M)
        self.geomList.append(geom)
        self.geomList.append(geom2)
        self.geomList.append(geom3)
        self.geomList.append(geom4)
        if colOnlyBall == 1:
            geom.setCollideBits(BitMask32(251658240))
            geom.setCategoryBits(BitMask32(0))
            geom2.setCollideBits(BitMask32(251658240))
            geom2.setCategoryBits(BitMask32(0))
            geom3.setCollideBits(BitMask32(251658240))
            geom3.setCategoryBits(BitMask32(0))
            geom4.setCollideBits(BitMask32(251658240))
            geom4.setCategoryBits(BitMask32(0))
        elif colOnlyBall == 2:
            geom.setCollideBits(BitMask32(0))
            geom.setCategoryBits(BitMask32(0))
            geom2.setCollideBits(BitMask32(0))
            geom2.setCategoryBits(BitMask32(0))
            geom3.setCollideBits(BitMask32(0))
            geom3.setCategoryBits(BitMask32(0))
            geom4.setCollideBits(BitMask32(0))
            geom4.setCategoryBits(BitMask32(0))
        if self.canRender:
            someNodePathGeom = render.attachNewNode('pinwheel')
            if attachedGeo:
                attachedGeo.reparentTo(someNodePathGeom)
                attachedGeo.setHpr(aHPR[0], aHPR[1], aHPR[2])
                attachedGeo.setPos(aPos[0], aPos[1], aPos[2])
            boxNodePathGeom, t1, t2 = BuildGeometry.addBoxGeom(someNodePathGeom, lx, ly * 0.5, lz, Vec4(1.0, 1.0, 1.0, 1.0), 1)
            boxNodePathGeom.setPos(-latSlide, ly * 0.25, 0)
            boxNodePathGeom2, t1, t2 = BuildGeometry.addBoxGeom(someNodePathGeom, ly * 0.5, lx, lz, Vec4(1.0, 1.0, 1.0, 1.0), 1)
            boxNodePathGeom2.setPos(ly * 0.25, latSlide, 0)
            boxNodePathGeom3, t1, t2 = BuildGeometry.addBoxGeom(someNodePathGeom, lx, ly * 0.5, lz, Vec4(1.0, 1.0, 1.0, 1.0), 1)
            boxNodePathGeom3.setPos(latSlide, -ly * 0.25, 0)
            boxNodePathGeom4, t1, t2 = BuildGeometry.addBoxGeom(someNodePathGeom, ly * 0.5, lx, lz, Vec4(1.0, 1.0, 1.0, 1.0), 1)
            boxNodePathGeom4.setPos(-ly * 0.25, -latSlide, 0)
            self.odePandaRelationList.append((someNodePathGeom, body))
        else:
            someNodePathGeom = None
            self.bodyList.append((None, body))
        return (someNodePathGeom, body)

    def createPinWheel(self, world, space, density, lx, ly, lz, numBoxes, disV, disH, colOnlyBall = 0, attachedGeo = None, aHPR = None, aPos = None, offRot = 0):
        body = OdeBody(self.world)
        M = OdeMass()
        M.setBox(density, lx, ly, lz)
        body.setMass(M)
        body.setFiniteRotationMode(1)
        boxsize = Vec3(lx, ly * 0.5, lz)
        boxsize2 = Vec3(ly * 0.5, lx, lz)
        self.massList.append(M)
        self.placerNode.setPos(0, 0, 0)
        self.placerNode.setHpr(0, 0, 0)
        self.subPlacerNode.setHpr(0, 0, 0)
        self.subPlacerNode.setPos(disH, disV, 0)
        if self.canRender:
            someNodePathGeom = render.attachNewNode('pinwheel')
        else:
            someNodePathGeom = self.root.attachNewNode('pinwheel')
        for num in range(numBoxes):
            spin = 360.0 * float(num) / float(numBoxes) + float(offRot)
            self.placerNode.setH(spin)
            geom = OdeBoxGeom(space, boxsize)
            geom.setBody(body)
            geom.setOffsetPosition(self.subPlacerNode.getPos(self.root))
            geom.setOffsetQuaternion(self.subPlacerNode.getQuat(self.root))
            self.geomList.append(geom)
            self.space.setSurfaceType(geom, 0)
            self.space.setCollideId(geom, 13)
            if colOnlyBall == 1:
                geom.setCollideBits(BitMask32(251658240))
                geom.setCategoryBits(BitMask32(0))
            elif colOnlyBall == 2:
                geom.setCollideBits(BitMask32(0))
                geom.setCategoryBits(BitMask32(0))
            if not attachedGeo:
                boxNodePathGeom, t1, t2 = BuildGeometry.addBoxGeom(someNodePathGeom, lx, ly * 0.5, lz, Vec4(1.0, 1.0, 1.0, 1.0), 1)
                boxNodePathGeom.setPos(self.subPlacerNode.getPos(self.root))
                boxNodePathGeom.setHpr(self.subPlacerNode.getHpr(self.root))

        if attachedGeo and self.canRender:
            attachedGeo.reparentTo(someNodePathGeom)
            attachedGeo.setHpr(aHPR[0], aHPR[1], aHPR[2])
            attachedGeo.setPos(aPos[0], aPos[1], aPos[2])
        if self.canRender:
            self.odePandaRelationList.append((someNodePathGeom, body))
        else:
            someNodePathGeom = None
            self.bodyList.append((None, body))
        return (someNodePathGeom, body)

    def attachMarker(self, body):
        if self.canRender:
            testMarker = render.attachNewNode('Joint Marker')
            ballmodel = loader.loadModel('models/misc/sphere')
            ballmodel.reparentTo(testMarker)
            ballmodel.setScale(0.25)
            testMarker.setPos(0.0, 0.0, -100.0)
            self.odePandaRelationList.append((testMarker, body))
