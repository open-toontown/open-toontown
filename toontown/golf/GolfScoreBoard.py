from pandac.PandaModules import *
from toontown.toonbase.ToonBaseGlobal import *
from direct.directnotify import DirectNotifyGlobal
from direct.interval.IntervalGlobal import *
from direct.task import Task
from math import *
from direct.distributed.ClockDelta import *
from toontown.golf import GolfGlobals
from pandac.PandaModules import LineSegs
AUTO_HIDE_TIMEOUT = 3

class GolfScoreBoard:
    notify = directNotify.newCategory('GolfScoreBoard')

    def __init__(self, golfCourse):
        self.golfCourse = golfCourse
        self.numPlayas = len(golfCourse.avIdList)
        self.avIdList = golfCourse.avIdList
        self.playaTags = []
        self.scoreTags = []
        self.totalTags = []
        self.scoreLabels = []
        self.holeLabels = []
        self.parLabels = []
        self.numExited = 0
        self.setup()

    def setup(self):
        self.scoreboard = DirectFrame(parent=aspect2d, relief=None, geom=DGG.getDefaultDialogGeom(), geom_color=ToontownGlobals.GlobalDialogColor, geom_scale=(1.9, 1, 1.05), pos=(0, 0, 0.375))
        self.lines = LineSegs()
        self.lines.setColor(0, 0, 0, 1)
        self.lines.setThickness(2)
        guiModel = loader.loadModel('phase_6/models/golf/golf_gui')
        highlight = loader.loadModel('phase_6/models/golf/headPanel')
        self.maximizeB = DirectButton(parent=aspect2d, pos=(1.2, 0, -0.85), relief=None, state=DGG.NORMAL, image=(guiModel.find('**/score_card_icon'), guiModel.find('**/score_card_icon_rollover'), guiModel.find('**/score_card_icon_rollover')), image_scale=(0.2, 1, 0.2), command=self.showBoard)
        self.vertOffset = 0.13
        self.playaTop = 0.12
        horzOffset = 0.12
        holeTop = 0.3
        self.vCenter = 0.025
        totScore = 0
        totPar = 0
        self.lineVStart = -0.465
        self.lineHStart = 0.17
        self.lineHorOffset = 0.13
        self.lineVertOffset = 0.125
        self.lineVCenter = 0.025
        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        self.minimizeB = DirectButton(parent=self.scoreboard, pos=(0, 0, self.lineHStart - 0.59), relief=None, state=DGG.NORMAL, image=(buttons.find('**/CloseBtn_UP'), buttons.find('**/CloseBtn_DN'), buttons.find('**/CloseBtn_Rllvr')), image_scale=(1, 1, 1), command=self.hideBoard, extraArgs=[None])
        self.exitCourseB = DirectButton(parent=self.scoreboard, pos=(0, 0, self.lineHStart - 0.59), relief=None, state=DGG.NORMAL, image=(buttons.find('**/CloseBtn_UP'), buttons.find('**/CloseBtn_DN'), buttons.find('**/CloseBtn_Rllvr')), image_scale=(1, 1, 1), text=TTLocalizer.GolfExitCourse, text_scale=0.04, text_pos=TTLocalizer.GSBexitCourseBPos, command=self.exitCourse)
        self.exitCourseB.hide()
        self.highlightCur = DirectLabel(parent=self.scoreboard, relief=None, pos=(-0.003, 0, 0.038), image=highlight, image_scale=(1.82, 1, 0.135))
        self.titleBar = DirectLabel(parent=self.scoreboard, relief=None, pos=(-0.003, 0, 0.166), color=(0.7, 0.7, 0.7, 0.3), image=highlight, image_scale=(1.82, 1, 0.195))
        self.titleBar.show()
        self.highlightCur.show()
        buttons.removeNode()
        guiModel.removeNode()
        title = GolfGlobals.getCourseName(self.golfCourse.courseId) + ' - ' + GolfGlobals.getHoleName(self.golfCourse.holeIds[self.golfCourse.curHoleIndex])
        self.titleLabel = DirectLabel(parent=self.scoreboard, relief=None, pos=(0, 0, holeTop + 0.1), text_align=TextNode.ACenter, text=title, text_scale=TTLocalizer.GSBtitleLabel, text_font=ToontownGlobals.getSignFont(), text_fg=(0, 0.5, 0.125, 1))
        self.playaLabel = DirectLabel(parent=self.scoreboard, relief=None, pos=(self.lineVStart - 0.23, 0, holeTop), text_align=TextNode.ACenter, text=TTLocalizer.GolfHole, text_font=ToontownGlobals.getMinnieFont(), text_scale=0.05)
        for holeLIndex in range(self.golfCourse.numHoles):
            holeLabel = DirectLabel(parent=self.scoreboard, relief=None, pos=(self.lineVStart + 0.055 + horzOffset * holeLIndex, 0, holeTop), text_align=TextNode.ACenter, text='%s' % (holeLIndex + 1), text_scale=0.05)
            self.holeLabels.append(holeLabel)

        self.totalLabel = DirectLabel(parent=self.scoreboard, relief=None, pos=(self.lineVStart + 0.1 + horzOffset * 9.5, 0, holeTop), text_align=TextNode.ACenter, text=TTLocalizer.GolfTotal, text_font=ToontownGlobals.getMinnieFont(), text_scale=0.05)
        self.parTitleLabel = DirectLabel(parent=self.scoreboard, relief=None, pos=(self.lineVStart - 0.23, 0, holeTop - 0.1), text_align=TextNode.ACenter, text=TTLocalizer.GolfPar, text_font=ToontownGlobals.getMinnieFont(), text_scale=0.05)
        for parHoleIndex in range(self.golfCourse.numHoles):
            parLabel = DirectLabel(parent=self.scoreboard, relief=None, pos=(self.lineVStart + 0.055 + horzOffset * parHoleIndex, 0, holeTop - 0.1), text_align=TextNode.ACenter, text='%s' % GolfGlobals.HoleInfo[self.golfCourse.holeIds[parHoleIndex]]['par'], text_scale=0.05, text_wordwrap=10)
            totPar = totPar + GolfGlobals.HoleInfo[self.golfCourse.holeIds[parHoleIndex]]['par']
            self.parLabels.append(parLabel)

        parLabel = DirectLabel(parent=self.scoreboard, relief=None, pos=(self.lineVStart + 0.1 + horzOffset * 9.5, 0, holeTop - 0.1), text_align=TextNode.ACenter, text='%s' % totPar, text_scale=0.05, text_wordwrap=10)
        self.parLabels.append(parLabel)
        vert = 0.0
        self.numPlayas = len(self.golfCourse.avIdList)
        for playaIndex in range(self.numPlayas):
            name = TTLocalizer.GolfUnknownPlayer
            av = base.cr.doId2do.get(self.golfCourse.avIdList[playaIndex])
            if av:
                name = av.getName()
            playaLabel = DirectLabel(parent=self.scoreboard, relief=None, text_align=TextNode.ACenter, text=name, text_scale=0.05, text_wordwrap=9)
            self.playaTags.append(playaLabel)
            textN = playaLabel.component(playaLabel.components()[0])
            if type(textN) == OnscreenText:
                try:
                    if textN.textNode.getWordwrappedWtext() != name:
                        vert = self.playaTop - self.vertOffset * playaIndex
                    else:
                        vert = self.playaTop - self.vertOffset * playaIndex - self.vCenter
                except:
                    vert = self.playaTop - self.vertOffset * playaIndex

            self.playaTags[playaIndex].setPos(self.lineVStart - 0.23, 0, vert)
            self.notify.debug('self.text height = %f' % self.playaTags[playaIndex].getHeight())
            holeIndex = 0
            for holeIndex in range(self.golfCourse.numHoles):
                holeLabel = DirectLabel(parent=self.scoreboard, relief=None, pos=(self.lineVStart + 0.055 + horzOffset * holeIndex, 0, self.playaTop - self.vertOffset * playaIndex - self.vCenter), text_align=TextNode.ACenter, text='-', text_scale=0.05, text_wordwrap=10)
                self.scoreTags.append(holeLabel)

            holeLabel = DirectLabel(parent=self.scoreboard, relief=None, pos=(self.lineVStart + 0.1 + horzOffset * 9.5, 0, self.playaTop - self.vertOffset * playaIndex - self.vCenter), text_align=TextNode.ACenter, text='-', text_scale=0.05, text_wordwrap=10)
            self.totalTags.append(holeLabel)

        self.lines.moveTo(self.lineVStart - 0.45, 0, self.lineHStart + 0.19)
        self.lines.drawTo(self.lineVStart + 11 * self.lineVertOffset, 0, self.lineHStart + 0.19)
        self.lines.moveTo(self.lineVStart - 0.45, 0, self.lineHStart + 0.09)
        self.lines.drawTo(self.lineVStart + 11 * self.lineVertOffset, 0, self.lineHStart + 0.09)
        self.lines.moveTo(self.lineVStart - 0.45, 0, self.lineHStart)
        self.lines.drawTo(self.lineVStart + 11 * self.lineVertOffset, 0, self.lineHStart)
        self.lines.moveTo(self.lineVStart - 0.45, 0, self.lineHStart + 0.19)
        self.lines.drawTo(self.lineVStart - 0.45, 0, self.lineHStart - 4 * 0.13)
        self.lines.moveTo(self.lineVStart, 0, self.lineHStart + 0.19)
        self.lines.drawTo(self.lineVStart, 0, self.lineHStart - 4 * 0.13)
        for x in range(4):
            self.lines.moveTo(self.lineVStart - 0.45, 0, self.lineHStart - (x + 1) * self.lineHorOffset)
            self.lines.drawTo(self.lineVStart + 11 * self.lineVertOffset + 0.005, 0, self.lineHStart - (x + 1) * self.lineHorOffset)

        for y in range(10):
            self.lines.moveTo(self.lineVStart + y * self.lineVertOffset, 0, self.lineHStart + 0.19)
            self.lines.drawTo(self.lineVStart + y * self.lineVertOffset, 0, self.lineHStart - 4 * 0.13)

        self.lines.moveTo(self.lineVStart + 11 * self.lineVertOffset, 0, self.lineHStart + 0.19)
        self.lines.drawTo(self.lineVStart + 11 * self.lineVertOffset, 0, self.lineHStart - 4 * 0.13)
        self.scoreboard.attachNewNode(self.lines.create())
        self.hide()
        return

    def getScoreLabel(self, avIdorIndex, holeNum):
        index = None
        if avIdorIndex < 100:
            index = avIdorIndex
        else:
            for playaIndex in range(self.numPlayas):
                if self.golfCourse.avIdList[playaIndex] == avIdorIndex:
                    index = playaIndex

        return self.scoreTags[index * self.golfCourse.numHoles + holeNum]

    def update(self):
        self.showBoard()
        taskMgr.doMethodLater(AUTO_HIDE_TIMEOUT, self.hideBoard, 'hide score board')

    def hideBoard(self, task):
        self.hide()

    def hide(self):
        self.scoreboard.hide()
        self.maximizeB.show()

    def showBoardFinal(self, task = None):
        self.exitCourseB.show()
        self.minimizeB.hide()
        self.showBoard()

    def showBoard(self, task = None):
        scoreDict = self.golfCourse.scores
        x = 0
        currentGolfer = self.golfCourse.getCurGolfer()
        for playaIndex in range(self.numPlayas):
            if self.golfCourse.isGameDone():
                self.playaTags[playaIndex].setColor(0, 0, 0, 1)
            elif currentGolfer == self.golfCourse.avIdList[playaIndex]:
                self.highlightCur.setColor(*GolfGlobals.PlayerColors[playaIndex])
                self.highlightCur.setAlphaScale(0.4)
                self.highlightCur.setPos(-0.003, 0, 0.038 - playaIndex * (self.lineVertOffset + 0.005))
                self.highlightCur.show()
            else:
                self.playaTags[playaIndex].setColor(0, 0, 0, 1)

        for avId in self.avIdList:
            holeIndex = 0
            totScore = 0
            playerExited = False
            for y in range(len(self.golfCourse.exitedAvIdList)):
                if self.golfCourse.exitedAvIdList[y] == avId:
                    self.playaTags[x].setColor(0.7, 0.7, 0.7, 1)
                    holeIndex = 0
                    for holeIndex in range(self.golfCourse.numHoles):
                        self.getScoreLabel(self.avIdList[x], holeIndex).setColor(0.7, 0.7, 0.7, 1)

                    self.totalTags[x].setColor(0.7, 0.7, 0.7, 1)
                    playerExited = True

            if playerExited == False:
                for holeIndex in range(self.golfCourse.numHoles):
                    if holeIndex <= self.golfCourse.curHoleIndex:
                        self.getScoreLabel(avId, holeIndex)['text'] = '%s' % scoreDict[avId][holeIndex]
                        totScore = totScore + scoreDict[avId][holeIndex]
                        if self.golfCourse.isGameDone() == False:
                            if holeIndex == self.golfCourse.curHoleIndex:
                                self.getScoreLabel(avId, holeIndex).setColor(1, 0, 0, 1)
                                self.holeLabels[holeIndex].setColor(1, 0, 0, 1)
                                self.parLabels[holeIndex].setColor(1, 0, 0, 1)
                                title = GolfGlobals.getCourseName(self.golfCourse.courseId) + ' - ' + GolfGlobals.getHoleName(self.golfCourse.holeIds[self.golfCourse.curHoleIndex])
                                self.titleLabel['text'] = title
                            else:
                                self.getScoreLabel(avId, holeIndex).setColor(0, 0, 0, 1)
                                self.holeLabels[holeIndex].setColor(0, 0, 0, 1)
                                self.parLabels[holeIndex].setColor(0, 0, 0, 1)

                self.totalTags[x]['text'] = '%s' % totScore
            if self.golfCourse.isGameDone():
                self.getScoreLabel(avId, self.golfCourse.numHoles - 1).setColor(0, 0, 0, 1)
                self.totalTags[x].setColor(1, 0, 0, 1)
            x = x + 1

        y = 0
        if self.golfCourse.isGameDone():
            self.parLabels[self.golfCourse.numHoles - 1].setColor(0, 0, 0, 1)
            self.holeLabels[self.golfCourse.numHoles - 1].setColor(0, 0, 0, 1)
            self.parLabels[self.golfCourse.numHoles].setColor(1, 0, 0, 1)
            self.totalLabel.setColor(1, 0, 0, 1)
        self.scoreboard.show()
        self.maximizeB.hide()

    def exitCourse(self):
        course = self.golfCourse
        self.delete()
        course.exitEarly()

    def delete(self):
        if self.maximizeB:
            self.maximizeB.destroy()
        self.maximizeB = None
        if self.scoreboard:
            self.scoreboard.destroy()
        self.scoreboard = None
        self.golfCourse = None
        taskMgr.remove('hide score board')
        return
