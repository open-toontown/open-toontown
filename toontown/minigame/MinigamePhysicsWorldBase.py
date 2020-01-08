from pandac.PandaModules import Quat
from pandac.PandaModules import OdeWorld, OdeSimpleSpace, OdeJointGroup, OdeUtil
from direct.directnotify import DirectNotifyGlobal
from direct.distributed.ClockDelta import globalClockDelta

class MinigamePhysicsWorldBase:
    notify = DirectNotifyGlobal.directNotify.newCategory('MinigamePhysicsWorldBase')

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
        self.FPS = 60.0
        self.DTAStep = 1.0 / self.FPS
        self.DTA = 0
        self.useQuickStep = False
        self.deterministic = True
        self.numStepsInSimulateTask = 0
        self.collisionEventName = 'ode-collision-%s' % id(self)
        self.space.setCollisionEvent(self.collisionEventName)
        self.accept(self.collisionEventName, self.__handleCollision)

    def delete(self):
        self.notify.debug('Max Collision Count was %s' % self.maxColCount)
        self.stopSim()
        self.commonObjectDict = None
        if self.canRender:
            for pair in self.odePandaRelationList:
                pair[0].removeNode()
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

        self.placerNode.removeNode()
        self.root.removeNode()
        for marker in self.jointMarkers:
            marker.removeNode()

        self.jointMarkers = None
        for data in self.geomDataList:
            data.destroy()

        for data in self.meshDataList:
            data.destroy()

        self.contactgroup.empty()
        self.world.destroy()
        self.space.destroy()
        self.world = None
        self.space = None
        self.ignore(self.collisionEventName)
        return

    def setupSimulation(self):
        if self.canRender:
            for count in range(self.jointMarkerCount):
                testMarker = render.attachNewNode('Joint Marker')
                ballmodel = loader.loadModel('phase_3/models/misc/sphere')
                ballmodel.reparentTo(testMarker)
                ballmodel.setScale(0.1)
                testMarker.setPos(0.0, 0.0, -100.0)
                self.jointMarkers.append(testMarker)

    def startSim(self):
        taskMgr.add(self.__simulationTask, 'simulation task')

    def stopSim(self):
        taskMgr.remove('simulation task')

    def __simulationTask(self, task):
        self.DTA += globalClock.getDt()
        numSteps = int(self.DTA / self.DTAStep)
        if numSteps > 10:
            self.notify.warning('phyics steps = %d' % numSteps)
        startTime = globalClock.getRealTime()
        while self.DTA >= self.DTAStep:
            if self.deterministic:
                OdeUtil.randSetSeed(0)
            self.DTA -= self.DTAStep
            self.preStep()
            self.simulate()
            self.postStep()

        if self.canRender:
            self.placeBodies()
        return task.cont

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

    def __handleCollision(self, entry):
        self.colEntries.append(entry)

    def simulate(self):
        self.colEntries = []
        self.space.autoCollide()
        eventMgr.doEvents()
        self.colCount = len(self.colEntries)
        if self.maxColCount < self.colCount:
            self.maxColCount = self.colCount
            self.notify.debug('New Max Collision Count %s' % self.maxColCount)
        if self.useQuickStep:
            self.world.quickStep(self.DTAStep)
        else:
            self.world.step(self.DTAStep)
        for bodyPair in self.bodyList:
            self.world.applyDampening(self.DTAStep, bodyPair[1])

        self.contactgroup.empty()
        self.timingSimTime = self.timingSimTime + self.DTAStep

    def placeBodies(self):
        for pair in self.odePandaRelationList:
            pandaNodePathGeom = pair[0]
            odeBody = pair[1]
            if pandaNodePathGeom:
                pandaNodePathGeom.setPos(odeBody.getPosition())
                pandaNodePathGeom.setQuat(Quat(odeBody.getQuaternion()[0], odeBody.getQuaternion()[1], odeBody.getQuaternion()[2], odeBody.getQuaternion()[3]))

    def getOrderedContacts(self, entry):
        c0 = self.space.getCollideId(entry.getGeom1())
        c1 = self.space.getCollideId(entry.getGeom2())
        if c0 > c1:
            return c1, c0
        else:
            return c0, c1
