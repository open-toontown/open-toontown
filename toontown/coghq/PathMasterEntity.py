from toontown.toonbase.ToontownGlobals import *
from direct.interval.IntervalGlobal import *
from direct.directnotify import DirectNotifyGlobal
from toontown.suit import GoonPathData
from otp.level import PathEntity

class PathMasterEntity(PathEntity.PathEntity):
    notify = DirectNotifyGlobal.directNotify.newCategory('PathMasterEntity')

    def __init__(self, level, entId):
        self.pathScale = 1.0
        PathEntity.PathEntity.__init__(self, level, entId)
        self.setPathIndex(self.pathIndex)
        self.initPath()

    def initPath(self):
        self.pathTargetList = [None,
         None,
         None,
         None,
         None,
         None,
         None,
         None]
        if not hasattr(self, 'pathTarget0'):
            self.pathTarget0 = None
        else:
            self.pathTargetList[0] = self.pathTarget0
        if not hasattr(self, 'pathTarget1'):
            self.pathTarget1 = None
        else:
            self.pathTargetList[1] = self.pathTarget1
        if not hasattr(self, 'pathTarget2'):
            self.pathTarget2 = None
        else:
            self.pathTargetList[2] = self.pathTarget2
        if not hasattr(self, 'pathTarget3'):
            self.pathTarget3 = None
        else:
            self.pathTargetList[3] = self.pathTarget3
        if not hasattr(self, 'pathTarget4'):
            self.pathTarget4 = None
        else:
            self.pathTargetList[4] = self.pathTarget4
        if not hasattr(self, 'pathTarget5'):
            self.pathTarget5 = None
        else:
            self.pathTargetList[5] = self.pathTarget5
        if not hasattr(self, 'pathTarget6'):
            self.pathTarget6 = None
        else:
            self.pathTargetList[6] = self.pathTarget6
        if not hasattr(self, 'pathTarget7'):
            self.pathTarget7 = None
        else:
            self.pathTargetList[7] = self.pathTarget7
        return

    def destroy(self):
        PathEntity.PathEntity.destroy(self)

    def setPathTarget0(self, targetId):
        self.pathTarget0 = targetId
        self.pathTargetList[0] = targetId
        if __dev__:
            messenger.send(self.getChangeEvent())

    def setPathTarget1(self, targetId):
        self.pathTarget1 = targetId
        self.pathTargetList[1] = targetId
        if __dev__:
            messenger.send(self.getChangeEvent())

    def setPathTarget2(self, targetId):
        self.pathTarget2 = targetId
        self.pathTargetList[2] = targetId
        if __dev__:
            messenger.send(self.getChangeEvent())

    def setPathTarget3(self, targetId):
        self.pathTarget3 = targetId
        self.pathTargetList[3] = targetId
        if __dev__:
            messenger.send(self.getChangeEvent())

    def setPathTarget4(self, targetId):
        self.pathTarget4 = targetId
        self.pathTargetList[4] = targetId
        if __dev__:
            messenger.send(self.getChangeEvent())

    def setPathTarget5(self, targetId):
        self.pathTarget5 = targetId
        self.pathTargetList[5] = targetId
        if __dev__:
            messenger.send(self.getChangeEvent())

    def setPathTarget6(self, targetId):
        self.pathTarget6 = targetId
        self.pathTargetList[6] = targetId
        if __dev__:
            messenger.send(self.getChangeEvent())

    def setPathTarget7(self, targetId):
        self.pathTarget7 = targetId
        self.pathTargetList[7] = targetId
        if __dev__:
            messenger.send(self.getChangeEvent())

    def getReducedPath(self):
        returnPath = []
        for entityId in self.pathTargetList:
            if self.level and entityId != 0:
                thing = self.level.entities.get(entityId, None)
                returnPath.append(thing.getPos(self))

        return returnPath

    def setPathIndex(self, pathIndex):
        self.pathIndex = pathIndex
        pathTableId = GoonPathData.taskZoneId2pathId[self.level.getTaskZoneId()]
        if self.pathIndex in GoonPathData.Paths[pathTableId]:
            self.path = GoonPathData.Paths[pathTableId][self.pathIndex]
            if __dev__:
                messenger.send(self.getChangeEvent())
        else:
            PathEntity.notify.warning('invalid pathIndex: %s' % pathIndex)
            self.path = None
        return

    def makePathTrack(self, node, velocity, name, turnTime = 1, lookAroundNode = None):
        track = Sequence(name=name)
        self.path = self.getReducedPath()
        if self.path is None or len(self.path) < 1:
            track.append(WaitInterval(1.0))
            return track
        path = self.path + [self.path[0]]
        for pointIndex in range(len(path) - 1):
            startPoint = Point3(path[pointIndex]) * self.pathScale
            endPoint = Point3(path[pointIndex + 1]) * self.pathScale
            v = startPoint - endPoint
            node.setPos(startPoint[0], startPoint[1], startPoint[2])
            node.headsUp(endPoint[0], endPoint[1], endPoint[2])
            theta = node.getH() % 360
            track.append(LerpHprInterval(node, turnTime, Vec3(theta, 0, 0)))
            distance = Vec3(v).length()
            duration = distance / velocity
            track.append(LerpPosInterval(node, duration=duration, pos=endPoint, startPos=startPoint))

        return track

    def makePathTrackBak(self, node, velocity, name, turnTime = 1, lookAroundNode = None):
        track = Sequence(name=name)
        if self.path is None:
            track.append(WaitInterval(1.0))
            return track
        path = self.path + [self.path[0]]
        for pointIndex in range(len(path) - 1):
            startPoint = Point3(path[pointIndex]) * self.pathScale
            endPoint = Point3(path[pointIndex + 1]) * self.pathScale
            v = startPoint - endPoint
            node.setPos(startPoint[0], startPoint[1], startPoint[2])
            node.headsUp(endPoint[0], endPoint[1], endPoint[2])
            theta = node.getH() % 360
            track.append(LerpHprInterval(node, turnTime, Vec3(theta, 0, 0)))
            distance = Vec3(v).length()
            duration = distance / velocity
            track.append(LerpPosInterval(node, duration=duration, pos=endPoint, startPos=startPoint))

        return track

    if __dev__:

        def getChangeEvent(self):
            return self.getUniqueName('pathChanged')

        def setPathScale(self, pathScale):
            self.pathScale = pathScale
            self.setPathIndex(self.pathIndex)
