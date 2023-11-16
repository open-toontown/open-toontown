from panda3d.core import CompassEffect, ModelPool, NodePath, TexturePool, TransparencyAttrib, Vec4

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.fsm.StateData import StateData
from direct.gui.OnscreenText import OnscreenText
from direct.interval.IntervalGlobal import Func, Sequence, Wait
from direct.showbase.MessengerGlobal import messenger
from direct.showbase.PythonUtil import uniqueName
from direct.task.TaskManagerGlobal import taskMgr

from toontown.hood import ZoneUtil
from toontown.hood.QuietZoneState import QuietZoneState
from toontown.toon.Toon import teleportDebug
from toontown.toonbase import ToontownGlobals, TTLocalizer
from toontown.toonbase.ToonBaseGlobal import base


class Hood(StateData):
    notify = directNotify.newCategory('Hood')

    def __init__(self, parentFSM, doneEvent, dnaStore, hoodId):
        StateData.__init__(self, doneEvent)
        self.loader = 'not initialized'
        self.parentFSM = parentFSM
        self.dnaStore = dnaStore
        self.loaderDoneEvent = 'loaderDone'
        self.id = None
        self.hoodId = hoodId
        self.titleText = None
        self.titleTextSeq = None
        self.titleColor = (1, 1, 1, 1)
        self.holidayStorageDNADict = {}
        self.spookySkyFile = None
        self.halloweenLights = []

    def enter(self, requestStatus):
        zoneId = requestStatus['zoneId']
        hoodText = self.getHoodText(zoneId)
        self.titleText = OnscreenText(hoodText, fg=self.titleColor, font=ToontownGlobals.getSignFont(), pos=(0, -0.5), scale=TTLocalizer.HtitleText, drawOrder=0, mayChange=1)
        self.fsm.request(requestStatus['loader'], [requestStatus])

    def getHoodText(self, zoneId):
        hoodText = base.cr.hoodMgr.getFullnameFromId(self.id)
        if self.id != ToontownGlobals.Tutorial:
            streetName = ToontownGlobals.StreetNames.get(ZoneUtil.getCanonicalBranchZone(zoneId))
            if streetName:
                hoodText = hoodText + '\n' + streetName[-1]

        return hoodText

    def spawnTitleText(self, zoneId):
        hoodText = self.getHoodText(zoneId)
        self.doSpawnTitleText(hoodText)

    def doSpawnTitleText(self, text):
        self.titleText.setText(text)
        self.titleText.show()
        self.titleText.setColor(Vec4(*self.titleColor))
        self.titleText.clearColorScale()
        self.titleText.setFg(self.titleColor)
        self.titleTextSeq = Sequence(Wait(0.1), Wait(6.0), self.titleText.colorScaleInterval(0.5, Vec4(1.0, 1.0, 1.0, 0.0)), Func(self.hideTitleText))
        self.titleTextSeq.start()

    def hideTitleText(self):
        if self.titleText:
            self.titleText.hide()

    def exit(self):
        if self.titleTextSeq:
            self.titleTextSeq.finish()
            self.titleTextSeq = None

        if self.titleText:
            self.titleText.cleanup()
            self.titleText = None

        base.localAvatar.stopChat()

    def load(self):
        if self.storageDNAFile:
            base.loader.loadDNAFile(self.dnaStore, self.storageDNAFile)

        newsManager = base.cr.newsManager
        if newsManager:
            holidayIds = base.cr.newsManager.getDecorationHolidayId()
            for holiday in holidayIds:
                for storageFile in self.holidayStorageDNADict.get(holiday, []):
                    base.loader.loadDNAFile(self.dnaStore, storageFile)

            if ToontownGlobals.HALLOWEEN_COSTUMES not in holidayIds and ToontownGlobals.SPOOKY_COSTUMES not in holidayIds or not self.spookySkyFile:
                self.sky = base.loader.loadModel(self.skyFile)
                self.sky.setTag('sky', 'Regular')
                self.sky.setScale(1.0)
                self.sky.setFogOff()
            else:
                self.sky = base.loader.loadModel(self.spookySkyFile)
                self.sky.setTag('sky', 'Halloween')

        if not newsManager:
            self.sky = base.loader.loadModel(self.skyFile)
            self.sky.setTag('sky', 'Regular')
            self.sky.setScale(1.0)
            self.sky.setFogOff()

    def unload(self):
        if hasattr(self, 'loader'):
            self.notify.info('Aggressively cleaning up loader: %s' % self.loader)
            self.loader.exit()
            self.loader.unload()
            del self.loader

        del self.fsm
        del self.parentFSM
        self.dnaStore.resetHood()
        del self.dnaStore
        self.sky.removeNode()
        del self.sky
        self.ignoreAll()
        ModelPool.garbageCollect()
        TexturePool.garbageCollect()

    def enterStart(self):
        pass

    def exitStart(self):
        pass

    def isSameHood(self, status):
        return status['hoodId'] == self.hoodId and status['shardId'] == None

    def enterFinal(self):
        pass

    def exitFinal(self):
        pass

    def enterQuietZone(self, requestStatus):
        teleportDebug(requestStatus, 'Hood.enterQuietZone: status=%s' % requestStatus)
        self._quietZoneDoneEvent = uniqueName('quietZoneDone')
        self.acceptOnce(self._quietZoneDoneEvent, self.handleQuietZoneDone)
        self.quietZoneStateData = QuietZoneState(self._quietZoneDoneEvent)
        self._enterWaitForSetZoneResponseMsg = self.quietZoneStateData.getEnterWaitForSetZoneResponseMsg()
        self.acceptOnce(self._enterWaitForSetZoneResponseMsg, self.handleWaitForSetZoneResponse)
        self._quietZoneLeftEvent = self.quietZoneStateData.getQuietZoneLeftEvent()
        if base.placeBeforeObjects:
            self.acceptOnce(self._quietZoneLeftEvent, self.handleLeftQuietZone)

        self.quietZoneStateData.load()
        self.quietZoneStateData.enter(requestStatus)

    def exitQuietZone(self):
        self.ignore(self._quietZoneDoneEvent)
        self.ignore(self._quietZoneLeftEvent)
        self.ignore(self._enterWaitForSetZoneResponseMsg)
        del self._quietZoneDoneEvent
        self.quietZoneStateData.exit()
        self.quietZoneStateData.unload()
        self.quietZoneStateData = None

    def loadLoader(self, requestStatus):
        pass

    def handleWaitForSetZoneResponse(self, requestStatus):
        loaderName = requestStatus['loader']
        if loaderName == 'safeZoneLoader':
            if not base.loader.inBulkBlock:
                base.loader.beginBulkLoad('hood', TTLocalizer.HeadingToPlayground, ToontownGlobals.safeZoneCountMap[self.id], 1, TTLocalizer.TIP_GENERAL)

            self.loadLoader(requestStatus)
            base.loader.endBulkLoad('hood')
        elif loaderName == 'townLoader':
            if not base.loader.inBulkBlock:
                zoneId = requestStatus['zoneId']
                toPhrase = ToontownGlobals.StreetNames[ZoneUtil.getCanonicalBranchZone(zoneId)][0]
                streetName = ToontownGlobals.StreetNames[ZoneUtil.getCanonicalBranchZone(zoneId)][-1]
                base.loader.beginBulkLoad('hood', TTLocalizer.HeadingToStreet % {'to': toPhrase,
                 'street': streetName}, ToontownGlobals.townCountMap[self.id], 1, TTLocalizer.TIP_STREET)

            self.loadLoader(requestStatus)
            base.loader.endBulkLoad('hood')
        elif loaderName == 'minigame':
            pass
        elif loaderName == 'cogHQLoader':
            print('should be loading HQ')

    def handleLeftQuietZone(self):
        status = self.quietZoneStateData.getRequestStatus()
        teleportDebug(status, 'handleLeftQuietZone, status=%s' % status)
        teleportDebug(status, 'requesting %s' % status['loader'])
        self.fsm.request(status['loader'], [status])

    def handleQuietZoneDone(self):
        if not base.placeBeforeObjects:
            status = self.quietZoneStateData.getRequestStatus()
            self.fsm.request(status['loader'], [status])

    def enterSafeZoneLoader(self, requestStatus):
        self.accept(self.loaderDoneEvent, self.handleSafeZoneLoaderDone)
        self.loader.enter(requestStatus)
        self.spawnTitleText(requestStatus['zoneId'])

    def exitSafeZoneLoader(self):
        if self.titleTextSeq:
            self.titleTextSeq.finish()
            self.titleTextSeq = None

        self.hideTitleText()
        self.ignore(self.loaderDoneEvent)
        self.loader.exit()
        self.loader.unload()
        del self.loader

    def handleSafeZoneLoaderDone(self):
        doneStatus = self.loader.getDoneStatus()
        teleportDebug(doneStatus, 'handleSafeZoneLoaderDone, doneStatus=%s' % doneStatus)
        if self.isSameHood(doneStatus) and doneStatus['where'] != 'party' or doneStatus['loader'] == 'minigame':
            teleportDebug(doneStatus, 'same hood')
            self.fsm.request('quietZone', [doneStatus])
        else:
            teleportDebug(doneStatus, 'different hood')
            self.doneStatus = doneStatus
            messenger.send(self.doneEvent)

    def startSky(self):
        self.sky.reparentTo(base.camera)
        self.sky.setZ(0.0)
        self.sky.setHpr(0.0, 0.0, 0.0)
        ce = CompassEffect.make(NodePath(), CompassEffect.PRot | CompassEffect.PZ)
        self.sky.node().setEffect(ce)

    def stopSky(self):
        taskMgr.remove('skyTrack')
        self.sky.reparentTo(base.hidden)

    def startSpookySky(self):
        if not self.spookySkyFile:
            return

        if hasattr(self, 'sky') and self.sky:
            self.stopSky()

        self.sky = base.loader.loadModel(self.spookySkyFile)
        self.sky.setTag('sky', 'Halloween')
        self.sky.setColor(0.5, 0.5, 0.5, 1)
        self.sky.reparentTo(base.camera)
        self.sky.setTransparency(TransparencyAttrib.MDual, 1)
        fadeIn = self.sky.colorScaleInterval(1.5, Vec4(1, 1, 1, 1), startColorScale=Vec4(1, 1, 1, 0.25), blendType='easeInOut')
        fadeIn.start()
        self.sky.setZ(0.0)
        self.sky.setHpr(0.0, 0.0, 0.0)
        ce = CompassEffect.make(NodePath(), CompassEffect.PRot | CompassEffect.PZ)
        self.sky.node().setEffect(ce)

    def endSpookySky(self):
        if hasattr(self, 'sky') and self.sky:
            self.sky.reparentTo(base.hidden)

        if hasattr(self, 'sky'):
            self.sky = base.loader.loadModel(self.skyFile)
            self.sky.setTag('sky', 'Regular')
            self.sky.setScale(1.0)
            self.startSky()
