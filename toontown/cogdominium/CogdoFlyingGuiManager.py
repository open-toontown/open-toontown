from pandac.PandaModules import NodePath
from toontown.toonbase import ToontownIntervals
from toontown.toonbase.ToontownTimer import ToontownTimer
from CogdoFlyingGameGuis import CogdoFlyingFuelGui, CogdoFlyingProgressGui
from CogdoGameMessageDisplay import CogdoGameMessageDisplay
from CogdoMemoGui import CogdoMemoGui
import CogdoFlyingGameGlobals as Globals

class CogdoFlyingGuiManager:
    ClearMessageDisplayEventName = 'ClearMessageDisplayEvent'
    EagleTargetingLocalPlayerEventName = 'EagleTargetingLocalPlayerEvent'
    EagleAttackingLocalPlayerEventName = 'EagleAttackingLocalPlayerEvent'
    FirstPressOfCtrlEventName = 'FirstPressOfCtrlEvent'
    PickedUpFirstPropellerEventName = 'PickedUpFirstPropellerEvent'
    InvulnerableEventName = 'InvulnerableEvent'
    StartRunningOutOfTimeMusicEventName = 'StartRunningOutOfTimeEvent'

    def __init__(self, level):
        self._level = level
        self.root = NodePath('CogdoFlyingGui')
        self.root.reparentTo(aspect2d)
        self.root.stash()
        self._initTimer()
        self._initHud()
        self._initMessageDisplay()
        self.sentTimeRunningOutMessage = False
        self._refuelGui = CogdoFlyingFuelGui(self.root)
        self._progressGui = CogdoFlyingProgressGui(self.root, self._level)

    def _initHud(self):
        self._memoGui = CogdoMemoGui(self.root)
        self._memoGui.posNextToLaffMeter()

    def _initTimer(self):
        self._timer = ToontownTimer()
        self._timer.reparentTo(self.root)
        self._timer.posInTopRightCorner()

    def _initMessageDisplay(self):
        audioMgr = base.cogdoGameAudioMgr
        sound = audioMgr.createSfx('popupHelpText')
        self._messageDisplay = CogdoGameMessageDisplay('CogdoFlyingMessageDisplay', self.root, sfx=sound)

    def destroyTimer(self):
        if self._timer is not None:
            self._timer.stop()
            self._timer.destroy()
            self._timer = None
        return

    def onstage(self):
        self.root.unstash()
        self._refuelGui.hide()
        self._progressGui.hide()

    def presentProgressGui(self):
        ToontownIntervals.start(ToontownIntervals.getPresentGuiIval(self._progressGui, 'present_progress_gui'))

    def presentRefuelGui(self):
        ToontownIntervals.start(ToontownIntervals.getPresentGuiIval(self._refuelGui, 'present_fuel_gui'))

    def presentTimerGui(self):
        ToontownIntervals.start(ToontownIntervals.getPresentGuiIval(self._timer, 'present_timer_gui'))

    def presentMemoGui(self):
        ToontownIntervals.start(ToontownIntervals.getPresentGuiIval(self._memoGui, 'present_memo_gui'))

    def offstage(self):
        self.root.stash()
        self._refuelGui.hide()
        self._progressGui.hide()
        self.hideTimer()

    def getTimeLeft(self):
        return Globals.Gameplay.SecondsUntilGameOver - self._timer.getElapsedTime()

    def isTimeRunningOut(self):
        return self.getTimeLeft() < Globals.Gameplay.TimeRunningOutSeconds

    def startTimer(self, duration, timerExpiredCallback = None, keepHidden = False):
        if self._timer is None:
            self._initTimer()
        self._timer.setTime(duration)
        self._timer.countdown(duration, timerExpiredCallback)
        if keepHidden:
            self.hideTimer()
        else:
            self.showTimer()
        return

    def stopTimer(self):
        if hasattr(self, '_timer') and self._timer is not None:
            self.hideTimer()
            self._timer.stop()
        return

    def showTimer(self):
        self._timer.show()

    def hideTimer(self):
        self._timer.hide()

    def forceTimerDone(self):
        if self._timer.countdownTask != None:
            self._timer.countdownTask.duration = 0
        return

    def showRefuelGui(self):
        self._refuelGui.show()

    def hideRefuelGui(self):
        self._refuelGui.hide()

    def setMessage(self, text, color = None, transition = 'fade'):
        self._messageDisplay.updateMessage(text, color, transition)

    def setTemporaryMessage(self, text, duration = 3.0, color = None):
        self._messageDisplay.showMessageTemporarily(text, duration, color)

    def setFuel(self, fuel):
        self._refuelGui.setFuel(fuel)

    def resetBlades(self):
        self._refuelGui.resetBlades()

    def setBlades(self, fuelState):
        self._refuelGui.setBlades(fuelState)

    def bladeLost(self):
        self._refuelGui.bladeLost()

    def setPropellerSpinRate(self, newRate):
        self._refuelGui.setPropellerSpinRate(newRate)

    def setMemoCount(self, score):
        self._memoGui.setCount(score)

    def addToonToProgressMeter(self, toon):
        self._progressGui.addToon(toon)

    def removeToonFromProgressMeter(self, toon):
        self._progressGui.removeToon(toon)

    def update(self):
        if self.isTimeRunningOut() and not self.sentTimeRunningOutMessage:
            messenger.send(CogdoFlyingGuiManager.StartRunningOutOfTimeMusicEventName)
            self.sentTimeRunningOutMessage = True
        self._refuelGui.update()
        self._progressGui.update()

    def destroy(self):
        ToontownIntervals.cleanup('present_fuel_gui')
        ToontownIntervals.cleanup('present_timer_gui')
        ToontownIntervals.cleanup('present_memo_gui')
        ToontownIntervals.cleanup('present_progress_gui')
        self._refuelGui.destroy()
        self._refuelGui = None
        self._memoGui.destroy()
        self._memoGui = None
        self._progressGui.destroy()
        self._progressGui = None
        self.destroyTimer()
        self._messageDisplay.destroy()
        self._messageDisplay = None
        self.root.removeNode()
        self.root = None
        return
