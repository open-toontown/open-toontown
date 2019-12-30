from pandac.PandaModules import *
from direct.distributed import ParentMgr
from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.task import Task
from direct.showbase import LeakDetectors
from otp.otpbase import OTPGlobals
import random

class AIZoneData:
    notify = directNotify.newCategory('AIZoneData')

    def __init__(self, air, parentId, zoneId):
        self._air = air
        self._parentId = parentId
        self._zoneId = zoneId
        self._data = self._air.getZoneDataStore().getDataForZone(self._parentId, self._zoneId)

    def destroy(self):
        del self._data
        self._air.getZoneDataStore().releaseDataForZone(self._parentId, self._zoneId)
        del self._zoneId
        del self._parentId
        del self._air

    def __getattr__(self, attr):
        return getattr(self._data, attr)


class AIZoneDataObj:
    notify = directNotify.newCategory('AIZoneDataObj')
    DefaultCTravName = 'default'

    def __init__(self, parentId, zoneId):
        self._parentId = parentId
        self._zoneId = zoneId
        self._refCount = 0
        self._collTravs = {}
        self._collTravsStarted = set()

    def __str__(self):
        output = str(self._collTravs)
        output += '\n'
        totalColliders = 0
        totalTraversers = 0
        for currCollTrav in list(self._collTravs.values()):
            totalTraversers += 1
            totalColliders += currCollTrav.getNumColliders()

        output += 'Num traversers: %s  Num total colliders: %s' % (totalTraversers, totalColliders)
        return output

    def _incRefCount(self):
        self._refCount += 1

    def _decRefCount(self):
        self._refCount -= 1

    def _getRefCount(self):
        return self._refCount

    def destroy(self):
        for name in list(self._collTravsStarted):
            self.stopCollTrav(cTravName=name)

        del self._collTravsStarted
        del self._collTravs
        if hasattr(self, '_nonCollidableParent'):
            self._nonCollidableParent.removeNode()
            del self._nonCollidableParent
        if hasattr(self, '_render'):
            if hasattr(self, '_renderLeakDetector'):
                self._renderLeakDetector.destroy()
                del self._renderLeakDetector
            self._render.removeNode()
            del self._render
        if hasattr(self, '_parentMgr'):
            self._parentMgr.destroy()
            del self._parentMgr
        del self._zoneId
        del self._parentId

    def getLocation(self):
        return (self._parentId, self._zoneId)

    def getRender(self):
        if not hasattr(self, '_render'):
            self._render = NodePath('render-%s-%s' % (self._parentId, self._zoneId))
            if config.GetBool('leak-scene-graph', 0):
                self._renderLeakDetector = LeakDetectors.SceneGraphLeakDetector(self._render)
        return self._render

    def getNonCollidableParent(self):
        if not hasattr(self, '_nonCollidableParent'):
            render = self.getRender()
            self._nonCollidableParent = render.attachNewNode('nonCollidables')
        if __dev__:
            pass
        return self._nonCollidableParent

    def getParentMgr(self):
        if not hasattr(self, '_parentMgr'):
            self._parentMgr = ParentMgr.ParentMgr()
            self._parentMgr.registerParent(OTPGlobals.SPHidden, hidden)
            self._parentMgr.registerParent(OTPGlobals.SPRender, self.getRender())
        return self._parentMgr

    def hasCollTrav(self, name = None):
        if name is None:
            name = AIZoneDataObj.DefaultCTravName
        return name in self._collTravs

    def getCollTrav(self, name = None):
        if name is None:
            name = AIZoneDataObj.DefaultCTravName
        if name not in self._collTravs:
            self._collTravs[name] = CollisionTraverser('cTrav-%s-%s-%s' % (name, self._parentId, self._zoneId))
        return self._collTravs[name]

    def removeCollTrav(self, name):
        if name in self._collTravs:
            del self._collTravs[name]

    def _getCTravTaskName(self, name = None):
        if name is None:
            name = AIZoneDataObj.DefaultCTravName
        return 'collTrav-%s-%s-%s' % (name, self._parentId, self._zoneId)

    def _doCollisions(self, task = None, topNode = None, cTravName = None):
        render = self.getRender()
        curTime = globalClock.getFrameTime()
        render.setTag('lastTraverseTime', str(curTime))
        if topNode is not None:
            if not render.isAncestorOf(topNode):
                self.notify.warning('invalid topNode for collision traversal in %s: %s' % (self.getLocation(), topNode))
        else:
            topNode = render
        if cTravName is None:
            cTravName = AIZoneDataObj.DefaultCTravName
        collTrav = self._collTravs[cTravName]
        messenger.send('preColl-' + collTrav.getName())
        collTrav.traverse(topNode)
        messenger.send('postColl-' + collTrav.getName())
        return Task.cont

    def doCollTrav(self, topNode = None, cTravName = None):
        self.getCollTrav(cTravName)
        self._doCollisions(topNode=topNode, cTravName=cTravName)

    def startCollTrav(self, respectPrevTransform = 1, cTravName = None):
        if cTravName is None:
            cTravName = AIZoneDataObj.DefaultCTravName
        if cTravName not in self._collTravsStarted:
            self.getCollTrav(name=cTravName)
            taskMgr.add(self._doCollisions, self._getCTravTaskName(name=cTravName), priority=OTPGlobals.AICollisionPriority, extraArgs=[self._zoneId])
            self._collTravsStarted.add(cTravName)
        self.setRespectPrevTransform(respectPrevTransform, cTravName=cTravName)
        return

    def stopCollTrav(self, cTravName = None):
        if cTravName is None:
            cTravName = AIZoneDataObj.DefaultCTravName
        self.notify.debug('stopCollTrav(%s, %s, %s)' % (cTravName, self._parentId, self._zoneId))
        if cTravName in self._collTravsStarted:
            self.notify.info('removing %s collision traversal for (%s, %s)' % (cTravName, self._parentId, self._zoneId))
            taskMgr.remove(self._getCTravTaskName(name=cTravName))
            self._collTravsStarted.remove(cTravName)
        return

    def setRespectPrevTransform(self, flag, cTravName = None):
        if cTravName is None:
            cTravName = AIZoneDataObj.DefaultCTravName
        self._collTravs[cTravName].setRespectPrevTransform(flag)
        return

    def getRespectPrevTransform(self, cTravName = None):
        if cTravName is None:
            cTravName = AIZoneDataObj.DefaultCTravName
        return self._collTravs[cTravName].getRespectPrevTransform()


class AIZoneDataStore:
    notify = directNotify.newCategory('AIZoneDataStore')

    def __init__(self):
        self._zone2data = {}

    def destroy(self):
        for zone, data in list(self._zone2data.items()):
            data.destroy()

        del self._zone2data

    def hasDataForZone(self, parentId, zoneId):
        key = (parentId, zoneId)
        return key in self._zone2data

    def getDataForZone(self, parentId, zoneId):
        key = (parentId, zoneId)
        if key not in self._zone2data:
            self._zone2data[key] = AIZoneDataObj(parentId, zoneId)
            self.printStats()
        data = self._zone2data[key]
        data._incRefCount()
        return data

    def releaseDataForZone(self, parentId, zoneId):
        key = (parentId, zoneId)
        data = self._zone2data[key]
        data._decRefCount()
        refCount = data._getRefCount()
        if refCount == 0:
            del self._zone2data[key]
            data.destroy()
            self.printStats()

    def printStats(self):
        self.notify.debug('%s zones have zone data allocated' % len(self._zone2data))
