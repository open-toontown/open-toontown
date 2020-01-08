from direct.distributed.ClockDelta import *
from pandac.PandaModules import *
from direct.showbase.PythonUtil import Functor, sameElements, list2dict, uniqueElements
from direct.interval.IntervalGlobal import *
from toontown.distributed.ToontownMsgTypes import *
from toontown.toonbase import ToontownGlobals
from otp.otpbase import OTPGlobals
from direct.distributed import DistributedObject
from . import Level
from . import LevelConstants
from direct.directnotify import DirectNotifyGlobal
from . import EntityCreator
from direct.gui import OnscreenText
from direct.task import Task
from . import LevelUtil
import random

class DistributedLevel(DistributedObject.DistributedObject, Level.Level):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedLevel')
    WantVisibility = config.GetBool('level-visibility', 1)
    ColorZonesAllDOs = 0
    FloorCollPrefix = 'zoneFloor'
    OuchTaskName = 'ouchTask'
    VisChangeTaskName = 'visChange'
    EmulateEntrancePoint = True

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        Level.Level.__init__(self)
        self.lastToonZone = None
        self.lastCamZone = 0
        self.titleColor = (1, 1, 1, 1)
        self.titleText = OnscreenText.OnscreenText('', fg=self.titleColor, shadow=(0, 0, 0, 1), font=ToontownGlobals.getSuitFont(), pos=(0, -0.5), scale=0.16, drawOrder=0, mayChange=1)
        self.smallTitleText = OnscreenText.OnscreenText('', fg=self.titleColor, font=ToontownGlobals.getSuitFont(), pos=(0.65, 0.9), scale=0.08, drawOrder=0, mayChange=1, bg=(0.5, 0.5, 0.5, 0.5), align=TextNode.ARight)
        self.titleTextSeq = None
        self.zonesEnteredList = []
        self.fColorZones = 0
        self.scenarioIndex = 0
        return

    def generate(self):
        DistributedLevel.notify.debug('generate')
        DistributedObject.DistributedObject.generate(self)
        self.parent2pendingChildren = {}
        self.curSpec = None
        if base.cr.timeManager is not None:
            base.cr.timeManager.synchronize('DistributedLevel.generate')
        else:
            self.notify.warning('generate(): no TimeManager!')
        return

    def setLevelZoneId(self, zoneId):
        self.levelZone = zoneId

    def setPlayerIds(self, avIdList):
        self.avIdList = avIdList

    def setEntranceId(self, entranceId):
        self.entranceId = entranceId

    def getEntranceId(self):
        return self.entranceId

    def setZoneIds(self, zoneIds):
        DistributedLevel.notify.debug('setZoneIds: %s' % zoneIds)
        self.zoneIds = zoneIds

    def setStartTimestamp(self, timestamp):
        DistributedLevel.notify.debug('setStartTimestamp: %s' % timestamp)
        self.startTime = globalClockDelta.networkToLocalTime(timestamp, bits=32)
        self.privGotAllRequired()

    def privGotAllRequired(self):
        self.levelAnnounceGenerate()

    def levelAnnounceGenerate(self):
        pass

    def initializeLevel(self, levelSpec):
        if __dev__:
            self.candidateSpec = levelSpec
            self.sendUpdate('requestCurrentLevelSpec', [levelSpec.stringHash(), levelSpec.entTypeReg.getHashStr()])
        else:
            self.privGotSpec(levelSpec)

    if __dev__:

        def reportModelSpecSyncError(self, msg):
            DistributedLevel.notify.error('%s\n\nyour spec does not match the level model\nuse SpecUtil.updateSpec, then restart your AI and client' % msg)

        def setSpecDeny(self, reason):
            DistributedLevel.notify.error(reason)

        def setSpecSenderDoId(self, doId):
            DistributedLevel.notify.debug('setSpecSenderDoId: %s' % doId)
            blobSender = base.cr.doId2do[doId]

            def setSpecBlob(specBlob, blobSender = blobSender, self = self):
                blobSender.sendAck()
                from .LevelSpec import LevelSpec
                spec = eval(specBlob)
                if spec is None:
                    spec = self.candidateSpec
                del self.candidateSpec
                self.privGotSpec(spec)
                return

            if blobSender.isComplete():
                setSpecBlob(blobSender.getBlob())
            else:
                evtName = self.uniqueName('specDone')
                blobSender.setDoneEvent(evtName)
                self.acceptOnce(evtName, setSpecBlob)

    def privGotSpec(self, levelSpec):
        Level.Level.initializeLevel(self, self.doId, levelSpec, self.scenarioIndex)
        modelZoneNums = self.zoneNums
        specZoneNums = list(self.zoneNum2zoneId.keys())
        if not sameElements(modelZoneNums, specZoneNums):
            self.reportModelSpecSyncError('model zone nums (%s) do not match spec zone nums (%s)' % (modelZoneNums, specZoneNums))
        self.initVisibility()
        self.placeLocalToon()

    def announceLeaving(self):
        DistributedLevel.notify.debug('announceLeaving')
        self.doneBarrier()

    def placeLocalToon(self, moveLocalAvatar = True):
        initialZoneEnt = None
        if self.entranceId in self.entranceId2entity:
            epEnt = self.entranceId2entity[self.entranceId]
            if moveLocalAvatar:
                epEnt.placeToon(base.localAvatar, self.avIdList.index(base.localAvatar.doId), len(self.avIdList))
            initialZoneEnt = self.getEntity(epEnt.getZoneEntId())
        elif self.EmulateEntrancePoint:
            self.notify.debug('unknown entranceId %s' % self.entranceId)
            if moveLocalAvatar:
                base.localAvatar.reparentTo(render)
                base.localAvatar.setPosHpr(0, 0, 0, 0, 0, 0)
            self.notify.debug('showing all zones')
            self.setColorZones(1)
            zoneEntIds = list(self.entType2ids['zone'])
            zoneEntIds.remove(LevelConstants.UberZoneEntId)
            if len(zoneEntIds):
                zoneEntId = random.choice(zoneEntIds)
                initialZoneEnt = self.getEntity(zoneEntId)
                if moveLocalAvatar:
                    base.localAvatar.setPos(render, initialZoneEnt.getZoneNode().getPos(render))
            else:
                initialZoneEnt = self.getEntity(LevelConstants.UberZoneEntId)
                if moveLocalAvatar:
                    base.localAvatar.setPos(render, 0, 0, 0)
        if initialZoneEnt is not None:
            self.enterZone(initialZoneEnt.entId)
        return

    def createEntityCreator(self):
        return EntityCreator.EntityCreator(level=self)

    def onEntityTypePostCreate(self, entType):
        Level.Level.onEntityTypePostCreate(self, entType)
        if entType == 'levelMgr':
            self.__handleLevelMgrCreated()

    def __handleLevelMgrCreated(self):
        levelMgr = self.getEntity(LevelConstants.LevelMgrEntId)
        self.geom = levelMgr.geom
        self.zoneNum2node = LevelUtil.getZoneNum2Node(self.geom)
        self.zoneNums = list(self.zoneNum2node.keys())
        self.zoneNums.sort()
        self.zoneNumDict = list2dict(self.zoneNums)
        DistributedLevel.notify.debug('zones from model: %s' % self.zoneNums)
        self.fixupLevelModel()

    def fixupLevelModel(self):
        for zoneNum, zoneNode in list(self.zoneNum2node.items()):
            if zoneNum == LevelConstants.UberZoneEntId:
                continue
            allColls = zoneNode.findAllMatches('**/+CollisionNode')
            floorColls = []
            for coll in allColls:
                bitmask = coll.node().getIntoCollideMask()
                if not (bitmask & ToontownGlobals.FloorBitmask).isZero():
                    floorColls.append(coll)

            if len(floorColls) > 0:
                floorCollName = '%s%s' % (DistributedLevel.FloorCollPrefix, zoneNum)
                others = zoneNode.findAllMatches('**/%s' % floorCollName)
                for other in others:
                    other.setName('%s_renamed' % floorCollName)

                for floorColl in floorColls:
                    floorColl.setName(floorCollName)

                def handleZoneEnter(collisionEntry, self = self, zoneNum = zoneNum):
                    self.toonEnterZone(zoneNum)
                    floorNode = collisionEntry.getIntoNode()
                    if floorNode.hasTag('ouch'):
                        ouchLevel = int(self.getFloorOuchLevel())
                        self.startOuch(ouchLevel)

                self.accept('enter%s' % floorCollName, handleZoneEnter)

                def handleZoneExit(collisionEntry, self = self, zoneNum = zoneNum):
                    floorNode = collisionEntry.getIntoNode()
                    if floorNode.hasTag('ouch'):
                        self.stopOuch()

                self.accept('exit%s' % floorCollName, handleZoneExit)

    def getFloorOuchLevel(self):
        return 1

    def announceGenerate(self):
        DistributedLevel.notify.debug('announceGenerate')
        DistributedObject.DistributedObject.announceGenerate(self)

    def disable(self):
        DistributedLevel.notify.debug('disable')
        if hasattr(self, 'geom'):
            del self.geom
        self.shutdownVisibility()
        self.destroyLevel()
        self.ignoreAll()
        if self.titleTextSeq:
            self.titleTextSeq.finish()
            self.titleTextSeq = None
        if self.smallTitleText:
            self.smallTitleText.cleanup()
            self.smallTitleText = None
        if self.titleText:
            self.titleText.cleanup()
            self.titleText = None
        self.zonesEnteredList = []
        DistributedObject.DistributedObject.disable(self)
        return

    def delete(self):
        DistributedLevel.notify.debug('delete')
        DistributedObject.DistributedObject.delete(self)
        self.stopOuch()

    def requestReparent(self, entity, parentId, wrt = False):
        parent = self.getEntity(parentId)
        if parent is not None:
            if wrt:
                entity.wrtReparentTo(parent.getNodePath())
            else:
                entity.reparentTo(parent.getNodePath())
        else:
            DistributedLevel.notify.debug('entity %s requesting reparent to %s, not yet created' % (entity, parentId))
            entity.reparentTo(hidden)
            if parentId not in self.parent2pendingChildren:
                self.parent2pendingChildren[parentId] = []

                def doReparent(parentId = parentId, self = self, wrt = wrt):
                    parent = self.getEntity(parentId)
                    for child in self.parent2pendingChildren[parentId]:
                        DistributedLevel.notify.debug('performing pending reparent of %s to %s' % (child, parent))
                        if wrt:
                            child.wrtReparentTo(parent.getNodePath())
                        else:
                            child.reparentTo(parent.getNodePath())

                    del self.parent2pendingChildren[parentId]
                    self.ignore(self.getEntityCreateEvent(parentId))

                self.accept(self.getEntityCreateEvent(parentId), doReparent)
            self.parent2pendingChildren[parentId].append(entity)
        return

    def getZoneNode(self, zoneEntId):
        return self.zoneNum2node.get(zoneEntId)

    def warpToZone(self, zoneNum):
        zoneNode = self.getZoneNode(zoneNum)
        if zoneNode is None:
            return
        base.localAvatar.setPos(zoneNode, 0, 0, 0)
        base.localAvatar.setHpr(zoneNode, 0, 0, 0)
        self.enterZone(zoneNum)
        return

    def showZone(self, zoneNum):
        zone = self.getZoneNode(zoneNum)
        zone.unstash()
        zone.clearColor()

    def setColorZones(self, fColorZones):
        self.fColorZones = fColorZones
        self.resetVisibility()

    def getColorZones(self):
        return self.fColorZones

    def hideZone(self, zoneNum):
        zone = self.getZoneNode(zoneNum)
        if self.fColorZones:
            zone.unstash()
            zone.setColor(1, 0, 0)
        else:
            zone.stash()

    def setTransparency(self, alpha, zone = None):
        self.geom.setTransparency(1)
        if zone is None:
            node = self.geom
        else:
            node = self.getZoneNode(zoneNum)
        node.setAlphaScale(alpha)
        return

    def initVisibility(self):
        self.curVisibleZoneNums = list2dict(self.zoneNums)
        del self.curVisibleZoneNums[LevelConstants.UberZoneEntId]
        self.curZoneNum = None
        self.visChangedThisFrame = 0
        self.fForceSetZoneThisFrame = 0

        def handleCameraRayFloorCollision(collEntry, self = self):
            name = collEntry.getIntoNode().getName()
            self.notify.debug('camera floor ray collided with: %s' % name)
            prefixLen = len(DistributedLevel.FloorCollPrefix)
            if name[:prefixLen] == DistributedLevel.FloorCollPrefix:
                try:
                    zoneNum = int(name[prefixLen:])
                except:
                    DistributedLevel.notify.warning('Invalid zone floor collision node: %s' % name)
                else:
                    self.camEnterZone(zoneNum)

        self.accept('on-floor', handleCameraRayFloorCollision)
        if not DistributedLevel.WantVisibility:
            zoneNums = list(self.zoneNums)
            zoneNums.remove(LevelConstants.UberZoneEntId)
            self.forceSetZoneThisFrame()
            self.setVisibility(zoneNums)
        taskMgr.add(self.visChangeTask, self.uniqueName(DistributedLevel.VisChangeTaskName), priority=49)
        return

    def shutdownVisibility(self):
        taskMgr.remove(self.uniqueName(DistributedLevel.VisChangeTaskName))

    def toonEnterZone(self, zoneNum, ouchLevel = None):
        DistributedLevel.notify.debug('toonEnterZone%s' % zoneNum)
        if zoneNum != self.lastToonZone:
            self.lastToonZone = zoneNum
            self.notify.debug('toon is standing in zone %s' % zoneNum)
            messenger.send('factoryZoneChanged', [zoneNum])

    def camEnterZone(self, zoneNum):
        DistributedLevel.notify.debug('camEnterZone%s' % zoneNum)
        self.enterZone(zoneNum)
        if zoneNum != self.lastCamZone:
            self.lastCamZone = zoneNum
            self.smallTitleText.hide()
            self.spawnTitleText()

    def lockVisibility(self, zoneNum = None, zoneId = None):
        if zoneId is not None:
            zoneNum = self.getZoneNumFromId(zoneId)
        self.notify.debug('lockVisibility to zoneNum %s' % zoneNum)
        self.lockVizZone = zoneNum
        self.enterZone(self.lockVizZone)
        return

    def unlockVisibility(self):
        self.notify.debug('unlockVisibility')
        if not hasattr(self, 'lockVizZone'):
            self.notify.warning('visibility already unlocked')
        else:
            del self.lockVizZone
            self.updateVisibility()

    def enterZone(self, zoneNum):
        DistributedLevel.notify.debug('entering zone %s' % zoneNum)
        if not DistributedLevel.WantVisibility:
            return
        if zoneNum == self.curZoneNum:
            return
        if zoneNum not in self.zoneNumDict:
            DistributedLevel.notify.error('no ZoneEntity for this zone (%s)!!' % zoneNum)
        self.updateVisibility(zoneNum)

    def updateVisibility(self, zoneNum = None):
        if zoneNum is None:
            zoneNum = self.curZoneNum
            if zoneNum is None:
                return
        if hasattr(self, 'lockVizZone'):
            zoneNum = self.lockVizZone
        zoneEnt = self.getEntity(zoneNum)
        visibleZoneNums = list2dict([zoneNum])
        visibleZoneNums.update(list2dict(zoneEnt.getVisibleZoneNums()))
        if not __debug__:
            if self.lastToonZone not in visibleZoneNums:
                if self.lastToonZone is not None:
                    self.notify.warning('adding zoneNum %s to visibility list because toon is standing in that zone!' % self.lastToonZone)
                    visibleZoneNums.update(list2dict([self.lastToonZone]))
        zoneEntIds = list(self.entType2ids['zone'])
        zoneEntIds.remove(LevelConstants.UberZoneEntId)
        if len(zoneEntIds):
            pass
        vizZonesChanged = 1
        addedZoneNums = []
        removedZoneNums = []
        allVZ = dict(visibleZoneNums)
        allVZ.update(self.curVisibleZoneNums)
        for vz, dummy in list(allVZ.items()):
            new = vz in visibleZoneNums
            old = vz in self.curVisibleZoneNums
            if new and old:
                continue
            if new:
                addedZoneNums.append(vz)
            else:
                removedZoneNums.append(vz)

        if not addedZoneNums and not removedZoneNums:
            DistributedLevel.notify.debug('visible zone list has not changed')
            vizZonesChanged = 0
        else:
            DistributedLevel.notify.debug('showing zones %s' % addedZoneNums)
            for az in addedZoneNums:
                self.showZone(az)

            DistributedLevel.notify.debug('hiding zones %s' % removedZoneNums)
            for rz in removedZoneNums:
                self.hideZone(rz)

        if vizZonesChanged or self.fForceSetZoneThisFrame:
            self.setVisibility(list(visibleZoneNums.keys()))
            self.fForceSetZoneThisFrame = 0
        self.curZoneNum = zoneNum
        self.curVisibleZoneNums = visibleZoneNums
        return

    def setVisibility(self, vizList):
        if self.fColorZones and DistributedLevel.ColorZonesAllDOs:
            vizList = list(self.zoneNums)
            vizList.remove(LevelConstants.UberZoneEntId)
        uberZone = self.getZoneId(LevelConstants.UberZoneEntId)
        visibleZoneIds = [OTPGlobals.UberZone, self.levelZone, uberZone]
        for vz in vizList:
            if vz is not LevelConstants.UberZoneEntId:
                visibleZoneIds.append(self.getZoneId(vz))

        DistributedLevel.notify.debug('new viz list: %s' % visibleZoneIds)
        base.cr.sendSetZoneMsg(self.levelZone, visibleZoneIds)

    def resetVisibility(self):
        self.curVisibleZoneNums = list2dict(self.zoneNums)
        del self.curVisibleZoneNums[LevelConstants.UberZoneEntId]
        for vz, dummy in list(self.curVisibleZoneNums.items()):
            self.showZone(vz)

        self.updateVisibility()

    def handleVisChange(self):
        Level.Level.handleVisChange(self)
        self.visChangedThisFrame = 1

    def forceSetZoneThisFrame(self):
        self.fForceSetZoneThisFrame = 1

    def visChangeTask(self, task):
        if self.visChangedThisFrame or self.fForceSetZoneThisFrame:
            self.updateVisibility()
            self.visChangedThisFrame = 0
        return Task.cont

    if __dev__:

        def setAttribChange(self, entId, attribName, valueStr, username):
            value = eval(valueStr)
            self.levelSpec.setAttribChange(entId, attribName, value, username)

    def spawnTitleText(self):

        def getDescription(zoneNum, self = self):
            ent = self.entities.get(zoneNum)
            if ent and hasattr(ent, 'description'):
                return ent.description
            return None

        description = getDescription(self.lastCamZone)
        if description and description != '':
            if self.titleTextSeq:
                self.titleTextSeq.finish()
                self.titleTextSeq = None
            self.smallTitleText.setText(description)
            self.titleText.setText(description)
            self.titleText.setColor(Vec4(*self.titleColor))
            self.titleText.setFg(self.titleColor)
            titleSeq = None
            if self.lastCamZone not in self.zonesEnteredList:
                self.zonesEnteredList.append(self.lastCamZone)
                titleSeq = Sequence(Func(self.hideSmallTitleText), Func(self.showTitleText), Wait(0.1), Wait(6.0), self.titleText.colorInterval(0.5, Vec4(self.titleColor[0], self.titleColor[1], self.titleColor[2], self.titleColor[3]), startColor=Vec4(self.titleColor[0], self.titleColor[1], self.titleColor[2], 0.0)))
            smallTitleSeq = Sequence(Func(self.hideTitleText), Func(self.showSmallTitle))
            if titleSeq:
                self.titleTextSeq = Sequence(titleSeq, smallTitleSeq, name=self.uniqueName('titleText'))
            else:
                self.titleTextSeq = Sequence(smallTitleSeq, name=self.uniqueName('titleText'))
            self.titleTextSeq.start()
        return

    def showInfoText(self, text = 'hello world'):
        description = text
        if description and description != '':
            if self.titleTextSeq:
                self.titleTextSeq.finish()
                self.titleTextSeq = None
            self.smallTitleText.setText(description)
            self.titleText.setText(description)
            self.titleText.setColor(Vec4(*self.titleColor))
            self.titleText.setFg(self.titleColor)
            titleSeq = None
            titleSeq = Sequence(Func(self.hideSmallTitleText), Func(self.showTitleText), Wait(0.1), Wait(3.0), self.titleText.colorInterval(0.5, Vec4(self.titleColor[0], self.titleColor[1], self.titleColor[2], self.titleColor[3]), startColor=Vec4(self.titleColor[0], self.titleColor[1], self.titleColor[2], 0.0)))
            if titleSeq:
                self.titleTextSeq = Sequence(titleSeq, name=self.uniqueName('titleText'))
            self.titleTextSeq.start()
        return

    def showTitleText(self):
        self.titleText.show()

    def hideTitleText(self):
        if self.titleText:
            self.titleText.hide()

    def showSmallTitle(self):
        if self.titleText:
            self.titleText.hide()
        self.smallTitleText.show()

    def hideSmallTitleText(self):
        if self.smallTitleText:
            self.smallTitleText.hide()

    def startOuch(self, ouchLevel, period = 2):
        self.notify.debug('startOuch %s' % ouchLevel)
        if not hasattr(self, 'doingOuch'):

            def doOuch(task, self = self, ouchLevel = ouchLevel, period = period):
                self.b_setOuch(ouchLevel)
                self.lastOuchTime = globalClock.getFrameTime()
                taskMgr.doMethodLater(period, doOuch, DistributedLevel.OuchTaskName)

            delay = 0
            if hasattr(self, 'lastOuchTime'):
                curFrameTime = globalClock.getFrameTime()
                timeSinceLastOuch = curFrameTime - self.lastOuchTime
                if timeSinceLastOuch < period:
                    delay = period - timeSinceLastOuch
            if delay > 0:
                taskMgr.doMethodLater(period, doOuch, DistributedLevel.OuchTaskName)
            else:
                doOuch(None)
            self.doingOuch = 1
        return

    def stopOuch(self):
        if hasattr(self, 'doingOuch'):
            taskMgr.remove(DistributedLevel.OuchTaskName)
            del self.doingOuch

    def b_setOuch(self, penalty, anim = None):
        self.notify.debug('b_setOuch %s' % penalty)
        av = base.localAvatar
        if not av.isStunned:
            self.d_setOuch(penalty)
            self.setOuch(penalty, anim)

    def d_setOuch(self, penalty):
        self.sendUpdate('setOuch', [penalty])

    def setOuch(self, penalty, anim = None):
        if anim == 'Squish':
            if base.cr.playGame.getPlace():
                base.cr.playGame.getPlace().fsm.request('squished')
        elif anim == 'Fall':
            if base.cr.playGame.getPlace():
                base.cr.playGame.getPlace().fsm.request('fallDown')
        av = base.localAvatar
        av.stunToon()
        av.playDialogueForString('!')

    def complexVis(self):
        return 1
