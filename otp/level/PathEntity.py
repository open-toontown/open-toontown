from toontown.toonbase.ToontownGlobals import *
from direct.interval.IntervalGlobal import *
from direct.directnotify import DirectNotifyGlobal
from . import BasicEntities
from toontown.suit import GoonPathData

class PathEntity(BasicEntities.NodePathEntity):
    notify = DirectNotifyGlobal.directNotify.newCategory('PathEntity')

    def __init__(self, level, entId):
        self.pathScale = 1.0
        BasicEntities.NodePathEntity.__init__(self, level, entId)
        self.setPathIndex(self.pathIndex)

    def destroy(self):
        BasicEntities.NodePathEntity.destroy(self)

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
