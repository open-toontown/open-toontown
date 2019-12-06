from panda3d.core import *
from direct.directnotify import DirectNotifyGlobal
from direct.task.Task import Task
from direct.distributed.ClockDelta import *
from direct.fsm.FSM import FSM
from direct.interval.IntervalGlobal import *
from toontown.racing.DistributedKartPad import DistributedKartPad
from toontown.racing import RaceGlobals
from toontown.toonbase.ToontownTimer import ToontownTimer
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals
from toontown.racing.KartShopGlobals import KartGlobals

class DistributedRacePad(DistributedKartPad, FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedRacePad')
    defaultTransitions = {'Off': ['WaitEmpty'],
     'WaitEmpty': ['WaitCountdown', 'Off'],
     'WaitCountdown': ['WaitEmpty',
                       'WaitBoarding',
                       'Off',
                       'AllAboard'],
     'WaitBoarding': ['AllAboard', 'WaitEmpty', 'Off'],
     'AllAboard': ['Off', 'WaitEmpty', 'WaitCountdown']}
    id = 0

    def __init__(self, cr):
        self.cr = cr
        DistributedKartPad.__init__(self, cr)
        FSM.__init__(self, 'RacePad_%s_FSM' % self.id)
        self.id = DistributedRacePad.id
        DistributedRacePad.id += 1
        self.trackId = None
        self.trackType = None
        self.timeStamp = None
        self.clockNodepath = None
        self.timerTask = None
        self.tunnelSign = None
        self.trackNameNode = None
        self.tunnelSignInterval = None
        return

    def disable(self):
        self.notify.debug('Disable')
        self.ignore('enterPlayground')
        self.request('Off')
        if self.tunnelSignInterval:
            self.tunnelSignInterval = None
        DistributedKartPad.disable(self)
        return

    def enableStartingBlocks(self):
        self.notify.debug('Enabling starting blocks')
        for block in self.startingBlocks:
            block.setActive(0)

    def disableStartingBlocks(self):
        for block in self.startingBlocks:
            self.notify.debug('Disabling kart block: %s' % block.getDoId())
            block.setActive(1)

    def isPractice(self):
        return self.trackType == RaceGlobals.Practice

    def setState(self, state, timestamp):
        self.request(state, [timestamp])

    def setRaceZone(self, zoneId):
        for block in self.startingBlocks:
            if block.avId == base.localAvatar.getDoId():
                hoodId = self.cr.playGame.hood.hoodId
                self.cr.playGame.getPlace().doneStatus = {'loader': 'racetrack',
                 'where': 'racetrack',
                 'zoneId': zoneId,
                 'trackId': self.trackId,
                 'hoodId': hoodId}
                messenger.send(base.cr.playGame.getPlace().doneEvent)

    def setTrackInfo(self, trackInfo):
        if self.isDisabled():
            return
        self.trackId, self.trackType = trackInfo
        self.notify.debugStateCall(self)
        self.setTunnelSignText()
        self.ignore('enterPlayground')
        self.acceptOnce('enterPlayground', self.setTunnelSignText)

    def enterOff(self):
        self.notify.debug('enterOff: Entering Off State for RacePad %s' % self.id)
        if self.tunnelSignInterval:
            self.tunnelSignInterval.finish()
        self.cleanupTunnelText()

    def exitOff(self):
        self.notify.debug('exitOff: Exiting Off state for RacePad %s' % self.id)

    def enterWaitEmpty(self, args):
        self.notify.debug('enterWaitEmpty: Entering WaitEmpty State for RacePad %s' % self.id)
        if self.tunnelSignInterval:
            self.tunnelSignInterval.finish()

    def exitWaitEmpty(self):
        self.notify.debug('exitWaitEmpty: Exiting WaitEmpty State for RacePad %s' % self.id)

    def enterWaitCountdown(self, args):
        self.notify.debug('enterWaitCountdown: Entering WaitCountdown State for RacePad %s' % self.id)
        self.timeStamp = args[0]
        self.startCountdown()

    def exitWaitCountdown(self):
        self.notify.debug('exitWaitCountdown: Exiting WaitCountdown State for RacePad %s' % self.id)
        self.stopCountdown()

    def enterWaitBoarding(self, args):
        self.notify.debug('enterWaitBoarding: Entering WaitBoarding State for RacePad %s' % self.id)
        self.timeStamp = args[0]
        for block in self.startingBlocks:
            block.hideGui()

    def exitWaitBoarding(self):
        self.notify.debug('exitWaitBoarding: Exiting WaitBording State for RacePad %s' % self.id)

    def enterAllAboard(self, args):
        self.notify.debug('enterAllAboard: Entering AllAboard State for RacePad %s' % self.id)
        for block in self.startingBlocks:
            block.request('Off')
            if block.av and block.kartNode:
                self.notify.debug('enterAllAboard: Avatar %s is in the race.' % block.av.doId)
                block.doExitToRaceTrack()

    def exitAllAboard(self):
        self.notify.debug('enterAllAboard: Exiting AllAboard State for RacePad %s' % self.id)

    def getTimestamp(self, avId = None):
        error = 'DistributedRacePad::getTimeStamp - timestamp not yet set!'
        return self.timeStamp

    def stopCountdown(self):
        if self.timerTask:
            taskMgr.remove(self.timerTask)
            self.clockNodepath.removeNode()
            self.clockNodepath = None
            self.clockNode = None
            self.timerTask = None
        return

    def updateTimerTask(self, task):
        countdownTime = int(task.duration - task.time)
        timeStr = str(countdownTime)
        if self.clockNode.getText() != timeStr:
            self.clockNode.setText(timeStr)
        if task.time >= task.duration:
            return Task.done
        else:
            return Task.cont

    def startCountdown(self):
        if not self.timerTask and self.startingBlocks:
            self.makeClockGui()
            duration = KartGlobals.COUNTDOWN_TIME - globalClockDelta.localElapsedTime(self.getTimestamp())
            countdownTask = Task(self.updateTimerTask)
            countdownTask.duration = duration
            self.timerTask = taskMgr.add(countdownTask, self.uniqueName('racePadTimerTask'))

    def addStartingBlock(self, block):
        DistributedKartPad.addStartingBlock(self, block)
        if self.state == 'WaitCountdown':
            self.startCountdown()

    def makeClockGui(self):
        self.notify.debugStateCall(self)
        if self.clockNodepath is not None:
            return
        self.clockNode, self.clockNodepath = self.getSignTextNodes('racePadClock')
        self.clockNodepath.setPos(0, 0.125, -3.0)
        self.clockNodepath.setScale(2.5)
        self.clockNodepath.flattenLight()
        return

    def getTunnelSign(self):
        cPadId = RaceGlobals.RaceInfo2RacePadId(self.trackId, self.trackType)
        genreId = RaceGlobals.getTrackGenre(self.trackId)
        tunnelName = RaceGlobals.getTunnelSignName(genreId, cPadId)
        self.tunnelSign = self.cr.playGame.hood.loader.geom.find('**/' + tunnelName)

    def getSignTextNodes(self, nodeName, font = ToontownGlobals.getSignFont()):
        signTextNode = TextNode(nodeName)
        signTextNode.setFont(font)
        signTextNode.setAlign(TextNode.ACenter)
        signTextNode.setTextColor(0.5, 0.5, 0.5, 1)
        signTextNodepath = self.tunnelSign.attachNewNode(signTextNode)
        signTextNodepath.setPos(0, 0.25, 0)
        signTextNodepath.setH(165.0)
        signTextNodepath.setDepthWrite(0)
        return (signTextNode, signTextNodepath)

    def setTunnelSignText(self):
        self.notify.debugStateCall(self)
        self.getTunnelSign()
        if not self.tunnelSign or self.tunnelSign.isEmpty():
            return
        if not self.trackNameNode:
            self.makeTextNodes()
        if self.tunnelSignInterval:
            self.tunnelSignInterval.finish()
        self.tunnelSignInterval = Sequence(Func(self.hideTunnelSignText), Wait(0.2), Func(self.showTunnelSignText), Wait(0.2), Func(self.hideTunnelSignText), Wait(0.2), Func(self.showTunnelSignText), Wait(0.2), Func(self.hideTunnelSignText), Wait(0.2), Func(self.updateTunnelSignText), Func(self.showTunnelSignText))
        self.tunnelSignInterval.start()

    def hideTunnelSignText(self):
        if self.tunnelSign:
            textNodePaths = self.tunnelSign.findAllMatches('**/+TextNode')
            numTextNodePaths = textNodePaths.getNumPaths()
            for i in range(numTextNodePaths):
                textNodePath = textNodePaths.getPath(i)
                textNodePath.hide()

    def showTunnelSignText(self):
        if self.tunnelSign:
            textNodePaths = self.tunnelSign.findAllMatches('**/+TextNode')
            numTextNodePaths = textNodePaths.getNumPaths()
            for i in range(numTextNodePaths):
                textNodePath = textNodePaths.getPath(i)
                textNodePath.show()

    def updateTunnelSignText(self):
        self.notify.debugStateCall(self)
        trackNameString = TTLocalizer.KartRace_TrackNames[self.trackId]
        if not self.trackNameNode:
            self.notify.warning('invalid trackNameNode, just returning')
            return
        self.trackNameNode.setText(trackNameString)
        trackTypeString = TTLocalizer.KartRace_RaceNames[self.trackType]
        self.trackTypeNode.setText(trackTypeString)
        deposit = 0
        if self.trackType:
            deposit = RaceGlobals.getEntryFee(self.trackId, self.trackType)
        depositString = TTLocalizer.KartRace_DepositPhrase + str(deposit)
        self.depositNode.setText(depositString)
        time = RaceGlobals.TrackDict[self.trackId][1]
        secs, hundredths = divmod(time, 1)
        min, sec = divmod(secs, 60)
        timeText = '%02d:%02d:%02d' % (min, sec, hundredths * 100)
        qualifyString = TTLocalizer.KartRace_QualifyPhrase + timeText
        self.qualifyNode.setText(qualifyString)

    def makeTextNodes(self):
        self.notify.debugStateCall(self)
        self.trackNameNode, trackNameNodePath = self.getSignTextNodes('trackNameNode')
        trackNameNodePath.setZ(0.7)
        trackNameNodePath.setScale(0.875)
        trackNameNodePath.flattenLight()
        self.trackTypeNode, trackTypeNodePath = self.getSignTextNodes('trackTypeNode')
        trackTypeNodePath.setZ(-0.35)
        trackTypeNodePath.setScale(0.875)
        trackTypeNodePath.flattenLight()
        self.depositNode, depositNodePath = self.getSignTextNodes('depositNode', ToontownGlobals.getToonFont())
        self.depositNode.setTextColor(0, 0, 0, 1)
        depositNodePath.setPos(4.0, -1.0, -2.0)
        depositNodePath.setScale(0.75)
        depositNodePath.flattenLight()
        self.qualifyNode, qualifyNodePath = self.getSignTextNodes('qualifyNode', ToontownGlobals.getToonFont())
        self.qualifyNode.setTextColor(0, 0, 0, 1)
        qualifyNodePath.setPos(-4.0, 1.2, -2.0)
        qualifyNodePath.setScale(0.75)
        qualifyNodePath.flattenLight()

    def cleanupTunnelText(self):
        self.notify.debugStateCall(self)
        if self.tunnelSign:
            textNodePaths = self.tunnelSign.findAllMatches('**/+TextNode')
            numTextNodePaths = textNodePaths.getNumPaths()
            for i in range(numTextNodePaths):
                textNodePath = textNodePaths.getPath(i)
                textNodePath.removeNode()
                textNodePath = None

        self.tunnelSign = None
        self.trackNameNode = None
        return
