from pandac.PandaModules import NodePath
from direct.interval.MetaInterval import Sequence
from direct.interval.FunctionInterval import Func
from toontown.toonbase.ToontownTimer import ToontownTimer
from toontown.toonbase import ToontownIntervals
from .CogdoMazeGameGuis import CogdoMazeHud, CogdoMazeMapGui, CogdoMazeBossGui
from .CogdoGameMessageDisplay import CogdoGameMessageDisplay
from . import CogdoMazeGameGlobals as Globals
from .CogdoMemoGui import CogdoMemoGui

class CogdoMazeGuiManager:

    def __init__(self, maze, bossCode):
        self.maze = maze
        self.root = NodePath('CogdoMazeGui')
        self.root.reparentTo(aspect2d)
        self.mazeMapGui = CogdoMazeMapGui(self.maze.collisionTable)
        if bossCode is not None:
            self._bossGui = CogdoMazeBossGui(bossCode)
        else:
            self._bossGui = None
        self._memoGui = CogdoMemoGui(self.root)
        self._memoGui.posNextToLaffMeter()
        self._presentGuiIval = None
        self._presentTimerIval = None
        self._hud = CogdoMazeHud()
        self._timer = None
        self._initMessageDisplay()
        return

    def _initTimer(self):
        self._timer = ToontownTimer()
        self._timer.hide()
        self._timer.posInTopRightCorner()

    def _initMessageDisplay(self):
        self.messageDisplay = CogdoGameMessageDisplay('CogdoMazeMessageDisplay', self.root, pos=Globals.MessageLabelPos)

    def destroy(self):
        ToontownIntervals.cleanup('present_gui')
        ToontownIntervals.cleanup('present_timer')
        ToontownIntervals.cleanup('present_memo')
        self._hud.destroy()
        self._hud = None
        self._memoGui.destroy()
        self._memoGui = None
        if self._bossGui is not None:
            self._bossGui.destroy()
            self._bossGui = None
        self.messageDisplay.destroy()
        self.messageDisplay = None
        self.destroyMazeMap()
        self.destroyTimer()
        if self._presentGuiIval:
            self._presentGuiIval.pause()
            self._presentGuiIval = None
        if self._presentTimerIval:
            self._presentTimerIval.pause()
            self._presentTimerIval = None
        return

    def destroyMazeMap(self):
        if hasattr(self, 'mazeMapGui') and self.mazeMapGui is not None:
            self.mazeMapGui.destroy()
            del self.mazeMapGui
        return

    def destroyTimer(self):
        if self._timer is not None:
            self._timer.stop()
            self._timer.destroy()
            self._timer = None
        return

    def showPickupCounter(self):
        ToontownIntervals.start(ToontownIntervals.getPresentGuiIval(self._memoGui, 'present_memo'))

    def startGame(self, firstMessage):
        self._presentGuiIval = ToontownIntervals.start(Sequence(ToontownIntervals.getPresentGuiIval(self._bossGui, '', startPos=(0, 0, -0.15)), Func(self.mazeMapGui.show), ToontownIntervals.getPulseLargerIval(self.mazeMapGui, '', scale=self.mazeMapGui.getScale()), Func(self.setMessage, firstMessage), name='present_gui'))

    def hideMazeMap(self):
        self.mazeMapGui.hide()

    def showBossGui(self):
        if self._bossGui is not None:
            self._bossGui.show()
        return

    def hideBossGui(self):
        if self._bossGui is not None:
            self._bossGui.hide()
        return

    def revealMazeMap(self):
        self.mazeMapGui.revealAll()

    def hideLock(self, lockIndex):
        self.mazeMapGui.hideLock(lockIndex)

    def showTimer(self, duration, timerExpiredCallback = None):
        if self._timer is None:
            self._initTimer()
        self._timer.setTime(duration)
        self._timer.countdown(duration, timerExpiredCallback)
        self._presentTimerIval = ToontownIntervals.start(ToontownIntervals.getPresentGuiIval(self._timer, 'present_timer', startPos=(0, 0, 0.35)))
        return

    def hideTimer(self):
        if hasattr(self, 'timer') and self._timer is not None:
            self._timer.hide()
            self._timer.stop()
        return

    def setMessage(self, text, color = None, transition = 'fade'):
        self.messageDisplay.updateMessage(text, color, transition)

    def setMessageTemporary(self, text, time = 3.0):
        self.messageDisplay.showMessageTemporarily(text, time)

    def clearMessage(self):
        self.messageDisplay.updateMessage('')

    def setPickupCount(self, count):
        self._memoGui.setCount(count)

    def showBossCode(self, bossIndex):
        self._bossGui.showNumber(bossIndex)

    def showBossHit(self, bossIndex):
        self._bossGui.showHit(bossIndex)

    def showQuestArrow(self, toon, target, offset):
        self._hud.showQuestArrow(toon, target, offset)

    def hideQuestArrow(self):
        self._hud.hideQuestArrow()
