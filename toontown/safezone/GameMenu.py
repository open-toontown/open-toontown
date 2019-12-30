from pandac.PandaModules import *
from direct.distributed.ClockDelta import *
from direct.task.Task import Task
from direct.interval.IntervalGlobal import *
from .TrolleyConstants import *
from direct.gui.DirectGui import *
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals

class GameMenu(DirectFrame):

    def __init__(self, picnicFunction, menuType):
        self.picnicFunction = picnicFunction
        DirectFrame.__init__(
            self,
            pos=(0.0, 0.0, 0.85),
            image_color=ToontownGlobals.GlobalDialogColor,
            image_scale=(1.8, 0.9, 0.13),
            text='',
            text_scale=0.05)
        self['image'] = DGG.getDefaultDialogGeom()
        if menuType == 1:
            self.title = DirectLabel(
                self,
                relief=None,
                text=TTLocalizer.PicnicTableMenuTutorial,
                text_pos=(0.0, -0.038),
                text_fg=(1, 0, 0, 1),
                text_scale=0.09,
                text_font=ToontownGlobals.getSignFont(),
                text_shadow=(1, 1, 1, 1))
        elif menuType == 2:
            self.title = DirectLabel(
                self,
                relief=None,
                text=TTLocalizer.PicnicTableMenuSelect,
                text_pos=(0.0, -0.04),
                text_fg=(1, 0, 0, 1),
                text_scale=0.09,
                text_font=ToontownGlobals.getSignFont())
        self.selectionButtons = loader.loadModel('phase_6/models/golf/picnic_game_menu.bam')
        btn1 = self.selectionButtons.find('**/Btn1')
        btn2 = self.selectionButtons.find('**/Btn2')
        btn3 = self.selectionButtons.find('**/Btn3')
        self.ChineseCheckers = DirectButton(
            self,
            image=(btn1.find('**/checkersBtnUp'), btn1.find('**/checkersBtnDn'), btn1.find('**/checkersBtnHi'), btn1.find('**/checkersBtnUp')),
            scale=0.36,
            relief=0,
            pos=(0, 0, -0.7),
            command=self.checkersSelected)
        self.Checkers = DirectButton(
            self,
            image=(btn2.find('**/regular_checkersBtnUp'), btn2.find('**/regular_checkersBtnDn'), btn2.find('**/regular_checkersBtnHi'), btn2.find('**/regular_checkersBtnUp')),
            scale=0.36,
            relief=0,
            pos=(0.8, 0, -0.7),
            command=self.regCheckersSelected)
        self.FindFour = DirectButton(
            self,
            image=(btn3.find('**/findfourBtnUp'), btn3.find('**/findfourBtnDn'), btn3.find('**/findfourBtnHi'), btn3.find('**/findfourBtnUp')),
            scale=0.36,
            relief=0,
            pos=(-0.8, 0, -0.7),
            command=self.findFourSelected)
        if not base.config.GetBool('want-chinese', 0):
            self.ChineseCheckers['command'] = self.doNothing
            self.ChineseCheckers.setColor(0.7, 0.7, 0.7, 0.7)
        if not base.config.GetBool('want-checkers', 0):
            self.Checkers['command'] = self.doNothing
            self.Checkers.setColor(0.7, 0.7, 0.7, 0.7)
        if not base.config.GetBool('want-findfour', 0):
            self.FindFour['command'] = self.doNothing
            self.FindFour.setColor(0.7, 0.7, 0.7, 0.7)
        self.chineseText = OnscreenText(
            text='Chinese Checkers',
            pos=(0, 0.56, -0.8),
            scale=0.15,
            fg=Vec4(1, 1, 1, 1),
            align=TextNode.ACenter,
            font=ToontownGlobals.getMinnieFont(),
            wordwrap=7,
            shadow=(0, 0, 0, 0.8),
            shadowOffset=(-0.1, -0.1),
            mayChange=True)
        self.chineseText.setR(-8)
        self.checkersText = OnscreenText(
            text='Checkers',
            pos=(0.81, -.1, -0.8),
            scale=0.15,
            fg=Vec4(1, 1, 1, 1),
            align=TextNode.ACenter,
            font=ToontownGlobals.getMinnieFont(),
            wordwrap=7,
            shadow=(0, 0, 0, 0.8),
            shadowOffset=(0.1, -0.1),
            mayChange=True)
        self.findFourText = OnscreenText(
            text='Find Four',
            pos=(-0.81, -.08, -0.8),
            scale=0.15,
            fg=Vec4(1, 1, 1, 1),
            align=TextNode.ACenter,
            font=ToontownGlobals.getMinnieFont(),
            wordwrap=8,
            shadow=(0, 0, 0, 0.8),
            shadowOffset=(-0.1, -0.1),
            mayChange=True)
        self.findFourText.setR(-8)
        self.checkersText.setR(8)
        return

    def delete(self):
        self.removeButtons()

    def removeButtons(self):
        self.ChineseCheckers.destroy()
        self.Checkers.destroy()
        self.FindFour.destroy()
        self.chineseText.destroy()
        self.checkersText.destroy()
        self.findFourText.destroy()
        DirectFrame.destroy(self)

    def checkersSelected(self):
        self.picnicFunction(1)
        self.picnicFunction = None
        return

    def regCheckersSelected(self):
        self.picnicFunction(2)
        self.picnicFunction = None
        return

    def findFourSelected(self):
        self.picnicFunction(3)
        self.picnicFunction = None
        return

    def doNothing(self):
        pass
