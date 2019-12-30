from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from . import MovingPlatform
from otp.level import BasicEntities

class ConveyorBelt(BasicEntities.NodePathEntity):
    UseClipPlanes = 1

    def __init__(self, level, entId):
        BasicEntities.NodePathEntity.__init__(self, level, entId)
        self.initBelt()

    def destroy(self):
        self.destroyBelt()
        BasicEntities.NodePathEntity.destroy(self)

    def initBelt(self):
        treadModel = loader.loadModel(self.treadModelPath)
        treadModel.setSx(self.widthScale)
        treadModel.flattenLight()
        self.numTreads = int(self.length / self.treadLength) + 3
        self.beltNode = self.attachNewNode('belt')
        self.treads = []
        for i in range(self.numTreads):
            mp = MovingPlatform.MovingPlatform()
            mp.parentingNode = render.attachNewNode('parentTarget')
            mp.setupCopyModel('conv%s-%s' % (self.getParentToken(), i), treadModel, self.floorName, parentingNode=mp.parentingNode)
            mp.parentingNode.reparentTo(mp)
            mp.reparentTo(self.beltNode)
            self.treads.append(mp)

        self.start()

    def destroyBelt(self):
        self.stop()
        for tread in self.treads:
            tread.destroy()
            tread.parentingNode.removeNode()
            del tread.parentingNode

        del self.treads
        self.beltNode.removeNode()
        del self.beltNode

    def start(self):
        startTime = self.level.startTime
        treadsIval = Parallel(name='treads')
        treadPeriod = self.treadLength / abs(self.speed)
        startY = -self.treadLength
        for i in range(self.numTreads):
            periodsToEnd = self.numTreads - i
            periodsFromStart = self.numTreads - periodsToEnd
            ival = Sequence()
            if periodsToEnd != 0:
                ival.append(LerpPosInterval(self.treads[i], duration=treadPeriod * periodsToEnd, pos=Point3(0, startY + self.numTreads * self.treadLength, 0), startPos=Point3(0, startY + i * self.treadLength, 0), fluid=1))

            def dumpContents(tread = self.treads[i]):
                tread.releaseLocalToon()

            ival.append(Sequence(Func(dumpContents), Func(self.treads[i].setPos, Point3(0, startY + self.numTreads * self.treadLength, 0))))
            if periodsFromStart != 0:
                ival.append(LerpPosInterval(self.treads[i], duration=treadPeriod * periodsFromStart, pos=Point3(0, startY + i * self.treadLength, 0), startPos=Point3(0, startY, 0), fluid=1))
            treadsIval.append(ival)

        self.beltIval = Sequence(treadsIval, name='ConveyorBelt-%s' % self.entId)
        playRate = 1.0
        startT = 0.0
        endT = self.beltIval.getDuration()
        if self.speed < 0.0:
            playRate = -1.0
            temp = startT
            startT = endT
            endT = temp
        self.beltIval.loop(playRate=playRate)
        self.beltIval.setT(globalClock.getFrameTime() - startTime)
        if ConveyorBelt.UseClipPlanes:
            headClip = PlaneNode('headClip')
            tailClip = PlaneNode('tailClip')
            self.headClipPath = self.beltNode.attachNewNode(headClip)
            self.headClipPath.setP(-90)
            self.tailClipPath = self.beltNode.attachNewNode(tailClip)
            self.tailClipPath.setY(self.length)
            self.tailClipPath.setP(90)
            self.beltNode.setClipPlane(self.headClipPath)
            self.beltNode.setClipPlane(self.tailClipPath)
            for tread in self.treads:
                tread.parentingNode.setClipPlaneOff(self.headClipPath)
                tread.parentingNode.setClipPlaneOff(self.tailClipPath)

    def stop(self):
        if hasattr(self, 'beltIval'):
            self.beltIval.pause()
            del self.beltIval
        if ConveyorBelt.UseClipPlanes:
            self.headClipPath.removeNode()
            del self.headClipPath
            self.tailClipPath.removeNode()
            del self.tailClipPath
            self.clearClipPlane()
            for tread in self.treads:
                tread.parentingNode.clearClipPlane()

    if __dev__:

        def attribChanged(self, attrib, value):
            self.destroyBelt()
            self.initBelt()
