from direct.gui.DirectLabel import DirectLabel
from direct.gui.DirectGui import DirectFrame, DGG
from direct.task.Task import Task
from direct.interval.MetaInterval import Sequence, Parallel
from direct.interval.FunctionInterval import Wait, Func
from pandac.PandaModules import TextNode, NodePath, Point3, CardMaker
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownIntervals
from toontown.minigame.MazeMapGui import MazeMapGui
import CogdoMazeGameGlobals as Globals
import CogdoUtil

class CogdoMazeMapGui(MazeMapGui):

    def __init__(self, mazeCollTable):
        MazeMapGui.__init__(self, mazeCollTable, bgColor=Globals.MapGuiBgColor, fgColor=Globals.MapGuiFgColor)
        self._suit2marker = {}
        self._initModel()
        self.setPos(*Globals.MapGuiPos)
        self.setScale(Globals.MapGuiScale)

    def destroy(self):
        for marker in self._suit2marker.values():
            marker.removeNode()

        del self._suit2marker
        self._entrance.removeNode()
        del self._entrance
        self._exit.removeNode()
        del self._exit
        del self._exitOpen
        del self._exitClosed
        self._suitMarkerTemplate.removeNode()
        del self._suitMarkerTemplate
        self._waterCoolerTemplate.removeNode()
        del self._waterCoolerTemplate
        MazeMapGui.destroy(self)

    def _initModel(self):
        baseName = '**/tt_t_gui_cmg_miniMap_'
        cardModel = CogdoUtil.loadMazeModel('miniMap_cards', group='gui')
        cm = CardMaker('bg')
        cm.setFrame(-1.1, 1.1, -1.1, 1.1)
        bg = self.attachNewNode(cm.generate())
        bg.setColor(*self._bgColor)
        bg.setBin('fixed', 0)
        frame = cardModel.find(baseName + 'frame')
        frame.reparentTo(self)
        frame.setScale(2.5)
        frame.setPos(0.01, 0, -0.01)
        self._entrance = cardModel.find(baseName + 'entrance')
        self._entrance.reparentTo(self)
        self._entrance.setScale(0.35)
        self._entrance.hide()
        self._exit = NodePath('exit')
        self._exit.setScale(0.35)
        self._exit.reparentTo(self)
        self._exitOpen = cardModel.find(baseName + 'exitOpen')
        self._exitOpen.reparentTo(self._exit)
        self._exitClosed = cardModel.find(baseName + 'exitClosed')
        self._exitClosed.reparentTo(self._exit)
        self._suitMarkerTemplate = cardModel.find(baseName + 'cogIcon')
        self._suitMarkerTemplate.detachNode()
        self._suitMarkerTemplate.setScale(0.225)
        self._waterCoolerTemplate = cardModel.find(baseName + 'waterDrop')
        self._waterCoolerTemplate.detachNode()
        self._waterCoolerTemplate.setScale(0.225)
        self._exit.hide()
        cardModel.removeNode()

    def addWaterCooler(self, tX, tY):
        marker = NodePath('WaterCoolerMarker-%i-%i' % (tX, tY))
        self._waterCoolerTemplate.copyTo(marker)
        marker.reparentTo(self.maskedLayer)
        x, y = self.tile2gui(tX, tY)
        marker.setPos(*self.gui2pos(x, y))

    def addSuit(self, suit):
        marker = NodePath('SuitMarker-%i' % len(self._suit2marker))
        self._suitMarkerTemplate.copyTo(marker)
        marker.reparentTo(self)
        self._suit2marker[suit] = marker

    def removeSuit(self, suit):
        self._suit2marker[suit].removeNode()
        del self._suit2marker[suit]

    def updateSuit(self, suit, tX, tY):
        x, y = self.tile2gui(tX, tY)
        self._suit2marker[suit].setPos(*self.gui2pos(x, y))

    def showExit(self):
        self._exit.show()
        self._exitClosed.hide()

    def hideExit(self):
        self._exit.hide()

    def placeExit(self, tX, tY):
        x, y = self.tile2gui(tX, tY)
        self._exit.setPos(*self.gui2pos(x, y))
        self._exit.setZ(self._exit, 0.3)

    def placeEntrance(self, tX, tY):
        x, y = self.tile2gui(tX, tY)
        self._entrance.setPos(*self.gui2pos(x, y))
        self._entrance.setZ(self._entrance, -0.35)
        self._entrance.show()


class CogdoMazeBossCodeFrame(DirectFrame):

    def __init__(self, id, code, modelToCopy):
        DirectFrame.__init__(self, relief=None, state=DGG.NORMAL, sortOrder=DGG.BACKGROUND_SORT_INDEX)
        self._id = id
        self._model = modelToCopy.copyTo(self)
        self._model.setPos(0, 0, 0)
        self._bg = self._model.find('**/bossBackground')
        self._bossIcon = self._model.find('**/bossIcon')
        self._bossIconX = self._model.find('**/bossIconX')
        self._bossIconX.reparentTo(self._bossIcon)
        self._bossIconX.hide()
        self._bg.hide()
        self._bossIcon.setBin('fixed', 2)
        self._bg.setBin('fixed', 3)
        self._label = DirectLabel(parent=self._bg, relief=None, scale=Globals.BossCodeFrameLabelScale, text=code, pos=(0, 0, -0.03), text_align=TextNode.ACenter, text_fg=Globals.BossCodeFrameLabelNormalColor, text_shadow=(0, 0, 0, 0), text_font=ToontownGlobals.getSuitFont())
        return

    def destroy(self):
        ToontownIntervals.cleanup('boss_code%i' % self._id)
        DirectFrame.destroy(self)

    def showNumber(self):
        self.setHit(False)
        self._bossIconX.show()
        ToontownIntervals.cleanup('boss_code%i' % self._id)
        ToontownIntervals.start(Sequence(Parallel(ToontownIntervals.getPresentGuiIval(self._bossIcon, '', startPos=(0, 0, -0.15))), Wait(1.0), ToontownIntervals.getPulseLargerIval(self._bg, ''), name='boss_code%i' % self._id))

    def setHit(self, hit):
        if hit:
            self._model.setColorScale(Globals.BlinkColor)
        else:
            self._model.setColorScale(1.0, 1.0, 1.0, 1.0)

    def highlightNumber(self):
        self._label['text_fg'] = Globals.BossCodeFrameLabelHighlightColor


class CogdoMazeBossGui(DirectFrame):

    def __init__(self, code):
        DirectFrame.__init__(self, relief=None, state=DGG.NORMAL, sortOrder=DGG.BACKGROUND_SORT_INDEX)
        self._code = str(code)
        self._codeLength = len(self._code)
        self._markersShown = 0
        self._markers = []
        self._initModel()
        self.setPos(*Globals.BossGuiPos)
        self.setScale(Globals.BossGuiScale)
        self.hide()
        return

    def destroy(self):
        ToontownIntervals.cleanup('bosscodedoor')
        self._model.removeNode()
        del self._model
        self._titleLabel.removeNode()
        del self._titleLabel
        for marker in self._markers:
            marker.destroy()

        del self._markers
        DirectFrame.destroy(self)

    def _initModel(self):
        codeFrameGap = Globals.BossCodeFrameGap
        codeFrameWidth = Globals.BossCodeFrameWidth
        self._model = CogdoUtil.loadMazeModel('bossCog', group='gui')
        self._model.reparentTo(self)
        self._model.find('**/frame').setBin('fixed', 1)
        titleLabelPos = self._model.find('**/title_label_loc').getPos()
        self._titleLabel = DirectLabel(parent=self, relief=None, scale=Globals.BossGuiTitleLabelScale, text=TTLocalizer.CogdoMazeGameBossGuiTitle.upper(), pos=titleLabelPos, text_align=TextNode.ACenter, text_fg=(0, 0, 0, 1), text_shadow=(0, 0, 0, 0), text_font=ToontownGlobals.getSuitFont())
        self._titleLabel.setBin('fixed', 1)
        bossCard = self._model.find('**/bossCard')
        self._openDoor = self._model.find('**/doorOpen')
        self._closedDoor = self._model.find('**/doorClosed')
        self._openDoor.stash()
        spacingX = codeFrameWidth + codeFrameGap
        startX = -0.5 * ((self._codeLength - 1) * spacingX - codeFrameGap)
        for i in range(self._codeLength):
            marker = CogdoMazeBossCodeFrame(i, self._code[i], bossCard)
            marker.reparentTo(self)
            marker.setPos(bossCard, startX + spacingX * i, 0, 0)
            self._markers.append(marker)

        bossCard.removeNode()
        return

    def showHit(self, bossIndex):
        self._markers[bossIndex].setHit(True)

    def showNumber(self, bossIndex):
        self._markers[bossIndex].setHit(False)
        self._markers[bossIndex].showNumber()
        self._markersShown += 1
        if self._markersShown == self._codeLength:
            self._openDoor.unstash()
            self._closedDoor.stash()
            ToontownIntervals.start(ToontownIntervals.getPulseLargerIval(self._openDoor, 'bosscodedoor'))


class CogdoMazeHud:

    def __init__(self):
        self._update = None
        self._initQuestArrow()
        return

    def _initQuestArrow(self):
        matchingGameGui = loader.loadModel('phase_3.5/models/gui/matching_game_gui')
        arrow = matchingGameGui.find('**/minnieArrow')
        arrow.setScale(Globals.QuestArrowScale)
        arrow.setColor(*Globals.QuestArrowColor)
        arrow.setHpr(90, -90, 0)
        self._questArrow = NodePath('Arrow')
        arrow.reparentTo(self._questArrow)
        self._questArrow.reparentTo(render)
        self.hideQuestArrow()
        matchingGameGui.removeNode()

    def destroy(self):
        self.__stopUpdateTask()
        self._questArrow.removeNode()
        self._questArrow = None
        return

    def showQuestArrow(self, parent, nodeToPoint, offset = Point3(0, 0, 0)):
        self._questArrowNodeToPoint = nodeToPoint
        self._questArrowParent = parent
        self._questArrowOffset = offset
        self._questArrow.unstash()
        self._questArrowVisible = True
        self.__startUpdateTask()

    def hideQuestArrow(self):
        self._questArrow.stash()
        self.__stopUpdateTask()
        self._questArrowVisible = False
        self._questArrowNodeToPoint = None
        return

    def __startUpdateTask(self):
        self.__stopUpdateTask()
        self._update = taskMgr.add(self._updateTask, 'CogdoMazeHud_Update', 45)

    def __stopUpdateTask(self):
        if self._update is not None:
            taskMgr.remove(self._update)
        return

    def _updateTask(self, task):
        if self._questArrowVisible:
            self._questArrow.setPos(self._questArrowParent, self._questArrowOffset)
            self._questArrow.lookAt(self._questArrowNodeToPoint)
        return Task.cont
