from direct.gui.DirectGui import DirectWaitBar, DGG
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject
from direct.interval.LerpInterval import LerpScaleInterval
from direct.interval.MetaInterval import Sequence
from direct.interval.FunctionInterval import Wait, Func
from pandac.PandaModules import Point3, VBase4
from pandac.PandaModules import TextNode
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import ToontownIntervals
from toontown.toonbase import TTLocalizer
from . import PartyGlobals

class PartyCogTrackerGui:

    def __init__(self):
        self.cogTracker = loader.loadModel('phase_13/models/parties/cogTrackerGUI')
        self.cogTracker.reparentTo(aspect2d)
        self.cogTracker.setScale(1.25)
        self.cogTracker.setX(1.0)
        self.cogTracker.setZ(-0.75)
        self.frame = self.cogTracker.find('**/tracker')
        self.cogs = []
        self.cogLayers = []
        self.blinkIntervals = []
        i = 0
        self.cogTracker.find('**/shadow').setBin('fixed', 0)
        self.cogTracker.find('**/plane').setBin('fixed', 1)
        for i in range(3):
            layers = [self.cogTracker.find('**/cog%d_blue' % i), self.cogTracker.find('**/cog%d_orange' % i), self.cogTracker.find('**/cog%d_white' % i)]
            self.cogs.append(self.cogTracker.find('**/cog%d' % i))
            self.cogLayers.append(layers)
            self.cogTracker.find('**/cog%d' % i).setBin('fixed', 2)
            big = Point3(1.5, 1.5, 1.5)
            seq = Sequence(LerpScaleInterval(self.cogs[i], duration=0.1, scale=big, startScale=Point3(1.0, 1.0, 1.0), blendType='easeOut'), LerpScaleInterval(self.cogs[i], duration=0.25, scale=Point3(1.0, 1.0, 1.0), startScale=big, blendType='easeOut'), Wait(0.4))
            self.blinkIntervals.append(seq)

        self.top = self.cogTracker.find('**/cog0_top').getZ()
        self.bottom = self.cogTracker.find('**/cog0_bottom').getZ()
        self.whiteTextureNp = self.cogTracker.find('**/cog0_white')
        self.whiteTexture = self.whiteTextureNp.findTexture('*')
        for cog in self.cogs:
            cog.setTexture(self.whiteTexture)

    def updateCog(self, cogNumber, cog, team):
        theCog = self.cogs[cogNumber]
        t = (cog.currentT + 1.0) / 2.0
        Z = self.bottom + (self.top - self.bottom) * t
        theCog.setZ(Z)
        for layer in self.cogLayers[cogNumber]:
            layer.stash()

        if cog.currentT < 0.0:
            self.cogLayers[cogNumber][0].unstash()
            if team == 1 and cog.currentT < -0.5 and not self.blinkIntervals[cogNumber].isPlaying():
                self.blinkIntervals[cogNumber].start()
        elif cog.currentT > 0.0:
            self.cogLayers[cogNumber][1].unstash()
            if team == 0 and cog.currentT > 0.5 and not self.blinkIntervals[cogNumber].isPlaying():
                self.blinkIntervals[cogNumber].start()
        else:
            self.cogLayers[cogNumber][2].unstash()

    def destory(self):
        if self.blinkIntervals is not None:
            for interval in self.blinkIntervals:
                if interval is not None:
                    interval.clearToInitial()
                    interval = None

        if self.cogTracker is not None:
            self.cogTracker.removeNode()
            self.cogTracker = None
        return


class PartyCogActivityGui(DirectObject):
    notify = directNotify.newCategory('PartyCogActivityGui')

    def __init__(self):
        DirectObject.__init__(self)
        self._piePowerMeter = None
        self._victoryBalanceBar = None
        self._scoreLabel = None
        self._cogTracker = None
        self._piePowerTitle = None
        self._victoryBalanceTitle = None
        self._scoreTitle = None
        self._spamWarning = None
        self._spamWarningIvalName = 'PartyCogActivityGui-SpamWarning'
        return

    def load(self):
        self._initPiePowerMeter()
        self._initScore()
        self._initCogTracker()
        self._initSpamWarning()
        self._initControlGui()
        self._initVictoryBalanceBar()

    def unload(self):
        if self._cogTracker is not None:
            self._cogTracker.destory()
            self._cogTracker = None
        if self._piePowerMeter is not None:
            self._piePowerMeter.destroy()
            self._piePowerMeter = None
        if self._piePowerTitle is not None:
            self._piePowerTitle.destroy()
            self._piePowerTitle = None
        if self._scoreLabel is not None:
            self._scoreLabel.destroy()
            self._scoreLabel = None
        if self._scoreTitle is not None:
            self._scoreTitle.destroy()
            self._scoreTitle = None
        taskMgr.remove(self._spamWarningIvalName)
        if self._spamWarning:
            self._spamWarning.destroy()
            self._spamWarning = None
        if hasattr(self, '_attackKeys'):
            self._attackKeys.detachNode()
            del self._attackKeys
        if hasattr(self, '_moveKeys'):
            self._moveKeys.detachNode()
            del self._moveKeys
        if self._victoryBalanceBar:
            self._victoryBalanceBar.detachNode()
            self._victoryBalanceBar = None
        if self._victoryBalanceBarOrange:
            self._victoryBalanceBarOrange.detachNode()
            self._victoryBalanceBarOrange = None
        if self._victoryBalanceBarPie:
            self._victoryBalanceBarPie.detachNode()
            self._victoryBalanceBarPie = None
        if self._victoryBalanceBarArrow:
            self._victoryBalanceBarArrow.detachNode()
            self._victoryBalanceBarArrow = None
        return

    def _initVictoryBalanceBar(self):
        h = PartyGlobals.CogActivityPowerMeterHeight / 2.0
        w = PartyGlobals.CogActivityPowerMeterWidth / 2.0
        victoryBalanceBar = loader.loadModel('phase_13/models/parties/tt_m_gui_pty_pieToss_balanceBar')
        self._victoryBalanceBar = victoryBalanceBar.find('**/*tt_t_gui_pty_pieToss_balanceBarBG')
        self._victoryBalanceBar.reparentTo(aspect2d)
        self._victoryBalanceBar.setBin('fixed', 0)
        self._victoryBalanceBar.setPos(PartyGlobals.CogActivityVictoryBarPos)
        self._victoryBalanceBar.setScale(1)
        self._victoryBalanceBarOrange = victoryBalanceBar.find('**/*tt_t_gui_pty_pieToss_balanceBarOrange')
        self._victoryBalanceBarOrange.reparentTo(self._victoryBalanceBar)
        self._victoryBalanceBarOrange.setBin('fixed', 1)
        self._victoryBalanceBarOrange.setPos(PartyGlobals.CogActivityVictoryBarOrangePos)
        self._victoryBalanceBarOrange.setScale(PartyGlobals.CogActivityBarStartScale, 1.0, 1.0)
        self._victoryBalanceBarPie = victoryBalanceBar.find('**/*tt_t_gui_pty_pieToss_balanceBarPie')
        self._victoryBalanceBarPie.reparentTo(self._victoryBalanceBar)
        self._victoryBalanceBarPie.setBin('fixed', 2)
        self._victoryBalanceBarPie.setX(PartyGlobals.CogActivityVictoryBarPiePos[0])
        self._victoryBalanceBarPie.setY(PartyGlobals.CogActivityVictoryBarPiePos[1])
        self._victoryBalanceBarPie.setZ(PartyGlobals.CogActivityVictoryBarPiePos[2])
        self._victoryBalanceBarPie.setScale(PartyGlobals.CogActivityBarPieScale)
        self._victoryBalanceBarArrow = victoryBalanceBar.find('**/*tt_t_gui_pty_pieToss_balanceArrow')
        self._victoryBalanceBarArrow.reparentTo(self._victoryBalanceBarPie)
        self._victoryBalanceBarArrow.setBin('fixed', 2)
        self._victoryBalanceBarArrow.setPos(PartyGlobals.CogActivityVictoryBarArrow)
        self._victoryBalanceBarArrow.setScale(1 / PartyGlobals.CogActivityBarPieScale)

    def _initControlGui(self):
        self._attackIvalName = 'PartyCogActivityGui-attackKeys'
        self._moveIvalName = 'PartyCogActivityGui-moveKeys'
        pieTossControls = loader.loadModel('phase_13/models/parties/tt_m_gui_pty_pieToss_controls')
        self._attackKeys = pieTossControls.find('**/*control*')
        self._moveKeys = pieTossControls.find('**/*arrow*')
        self._moveKeys.reparentTo(aspect2d)
        self._moveKeys.setPos(1.0, 0.0, -0.435)
        self._moveKeys.setScale(0.15)
        self._attackKeys.reparentTo(aspect2d)
        self._attackKeys.setPos(0.85, 0.0, -0.45)
        self._attackKeys.setScale(0.15)
        self._moveKeys.hide()
        self._attackKeys.hide()

    def _initPiePowerMeter(self):
        h = PartyGlobals.CogActivityPowerMeterHeight / 2.0
        w = PartyGlobals.CogActivityPowerMeterWidth / 2.0
        self._piePowerMeter = DirectWaitBar(frameSize=(-h,
         h,
         -w,
         w), relief=DGG.GROOVE, frameColor=(0.9, 0.9, 0.9, 1.0), borderWidth=(0.01, 0.01), barColor=PartyGlobals.CogActivityColors[0], pos=PartyGlobals.CogActivityPowerMeterPos, hpr=(0.0, 0.0, -90.0))
        self._piePowerMeter.setBin('fixed', 0)
        self._piePowerTitle = OnscreenText(text=TTLocalizer.PartyCogGuiPowerLabel, pos=PartyGlobals.CogActivityPowerMeterTextPos, scale=0.05, fg=(1.0, 1.0, 1.0, 1.0), align=TextNode.ACenter)
        self._piePowerTitle.setBin('fixed', 0)
        self._piePowerMeter.hide()
        self._piePowerTitle.hide()

    def _initScore(self):
        self._scoreLabel = OnscreenText(text='0', pos=PartyGlobals.CogActivityScorePos, scale=PartyGlobals.TugOfWarTextWordScale, fg=(1.0, 1.0, 0.0, 1.0), align=TextNode.ARight, font=ToontownGlobals.getSignFont(), mayChange=True)
        self._scoreTitle = OnscreenText(text=TTLocalizer.PartyCogGuiScoreLabel, pos=PartyGlobals.CogActivityScoreTitle, scale=0.05, fg=(1.0, 1.0, 1.0, 1.0), align=TextNode.ARight)
        self._scoreLabel.hide()
        self._scoreTitle.hide()

    def _initCogTracker(self):
        self._cogTracker = PartyCogTrackerGui()

    def _initSpamWarning(self):
        self._spamWarning = OnscreenText(text=TTLocalizer.PartyCogGuiSpamWarning, scale=0.15, fg=(1.0, 1.0, 0, 1.0), shadow=(0, 0, 0, 0.62), mayChange=False, pos=(0, 0.33))
        self._spamWarning.hide()

    def showScore(self):
        self._scoreLabel.show()
        self._scoreTitle.show()

    def hideScore(self):
        self._scoreLabel.hide()
        self._scoreTitle.hide()

    def setScore(self, score = 0):
        self._scoreLabel['text'] = str(score)

    def resetPiePowerMeter(self):
        self._piePowerMeter['value'] = 0

    def showPiePowerMeter(self):
        self._piePowerMeter.show()
        self._piePowerTitle.show()

    def hidePiePowerMeter(self):
        self._piePowerMeter.hide()
        self._piePowerTitle.hide()

    def updatePiePowerMeter(self, value):
        self._piePowerMeter['value'] = value

    def getPiePowerMeterValue(self):
        return self._piePowerMeter['value']

    def hideSpamWarning(self):
        taskMgr.remove(self._spamWarningIvalName)
        if self._spamWarning:
            self._spamWarning.hide()

    def showSpamWarning(self):
        if self._spamWarning.isHidden():
            self._spamWarning.show()
            taskMgr.remove(self._spamWarningIvalName)
            Sequence(ToontownIntervals.getPulseLargerIval(self._spamWarning, ''), Wait(PartyGlobals.CogActivitySpamWarningShowTime), Func(self.hideSpamWarning), name=self._spamWarningIvalName, autoFinish=1).start()

    def hide(self):
        self.hidePiePowerMeter()
        self.hideScore()
        self.hideSpamWarning()
        self.hideControls()

    def disableToontownHUD(self):
        base.localAvatar.hideName()
        base.localAvatar.laffMeter.hide()
        base.setCellsAvailable(base.bottomCells + [base.rightCells[1]], False)

    def enableToontownHUD(self):
        base.localAvatar.showName()
        base.localAvatar.laffMeter.show()
        base.setCellsAvailable(base.bottomCells + [base.rightCells[1]], True)

    def setTeam(self, team):
        self.team = team
        if team == 0:
            self._cogTracker.frame.setR(180)
        self._piePowerMeter['barColor'] = PartyGlobals.CogActivityColors[team]

    def startTrackingCogs(self, cogs):
        self.cogs = cogs
        taskMgr.add(self.trackCogs, 'trackCogs')

    def trackCogs(self, task):
        if self.cogs is None:
            return
        self._updateVictoryBar()
        for i, cog in enumerate(self.cogs):
            self._cogTracker.updateCog(i, cog, self.team)

        return task.cont

    def _updateVictoryBar(self):
        if not (hasattr(self, '_victoryBalanceBar') and self._victoryBalanceBar):
            return
        netDistance = 0
        for cog in self.cogs:
            netDistance = netDistance + cog.targetDistance

        teamDistance = netDistance / 6.0
        self._victoryBalanceBarOrange.setScale(PartyGlobals.CogActivityBarStartScale + teamDistance * 10 * PartyGlobals.CogActivityBarUnitScale, 1.0, 1.0)
        self._victoryBalanceBarPie.setX(PartyGlobals.CogActivityVictoryBarPiePos[0] + teamDistance * 10 * PartyGlobals.CogActivityBarPieUnitMove)
        self._victoryBalanceBarPie.setY(PartyGlobals.CogActivityVictoryBarPiePos[1])
        self._victoryBalanceBarPie.setZ(PartyGlobals.CogActivityVictoryBarPiePos[2])
        if teamDistance > 0.0:
            self._victoryBalanceBarArrow.setColor(PartyGlobals.CogActivityColors[1])
        elif teamDistance < 0.0:
            self._victoryBalanceBarArrow.setColor(PartyGlobals.CogActivityColors[0])
        else:
            self._victoryBalanceBarArrow.setColor(VBase4(1.0, 1.0, 1.0, 1.0))

    def stopTrackingCogs(self):
        taskMgr.remove('trackCogs')

    def showAttackControls(self):
        if self._attackKeys.isHidden():
            self._attackKeys.show()
            taskMgr.remove(self._attackIvalName)
            Sequence(ToontownIntervals.getPulseLargerIval(self._attackKeys, '', scale=0.15), Wait(PartyGlobals.CogActivityControlsShowTime), Func(self.hideAttackControls), name=self._attackIvalName, autoFinish=1).start()

    def showMoveControls(self):
        if self._moveKeys.isHidden() and not self._attackKeys.isHidden():
            self._moveKeys.show()
            taskMgr.remove(self._moveIvalName)
            Sequence(ToontownIntervals.getPulseLargerIval(self._moveKeys, '', scale=0.15), Wait(PartyGlobals.CogActivityControlsShowTime), Func(self.hideMoveControls), name=self._moveIvalName, autoFinish=1).start()

    def hideAttackControls(self):
        taskMgr.remove(self._attackIvalName)
        if hasattr(self, '_attackKeys') and self._attackKeys:
            self._attackKeys.hide()

    def hideMoveControls(self):
        taskMgr.remove(self._moveIvalName)
        if hasattr(self, '_moveKeys') and self._moveKeys:
            self._moveKeys.hide()

    def hideControls(self):
        self.hideMoveControls()
        self.hideAttackControls()
