from direct.task import Task
from direct.fsm import StateData
from toontown.toonbase.ToontownGlobals import *
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from toontown.toonbase import ToontownTimer
from toontown.toonbase import TTLocalizer
from . import MinigameGlobals

class MinigameRulesPanel(StateData.StateData):

    def __init__(self, panelName, gameTitle, instructions, doneEvent, timeout = MinigameGlobals.rulesDuration):
        StateData.StateData.__init__(self, doneEvent)
        self.gameTitle = gameTitle
        self.instructions = instructions
        self.TIMEOUT = timeout

    def load(self):
        minigameGui = loader.loadModel('phase_4/models/gui/minigame_rules_gui')
        buttonGui = loader.loadModel('phase_3.5/models/gui/inventory_gui')
        self.frame = DirectFrame(image=minigameGui.find('**/minigame-rules-panel'), relief=None, pos=(0.1375, 0, -0.6667))
        self.gameTitleText = DirectLabel(parent=self.frame, text=self.gameTitle, scale=TTLocalizer.MRPgameTitleText, text_align=TextNode.ACenter, text_font=getSignFont(), text_fg=(1.0, 0.33, 0.33, 1.0), pos=TTLocalizer.MRgameTitleTextPos, relief=None)
        self.instructionsText = DirectLabel(parent=self.frame, text=self.instructions, scale=TTLocalizer.MRPinstructionsText, text_align=TextNode.ACenter, text_wordwrap=TTLocalizer.MRPinstructionsTextWordwrap, pos=TTLocalizer.MRPinstructionsTextPos, relief=None)
        self.playButton = DirectButton(parent=self.frame, relief=None, image=(buttonGui.find('**/InventoryButtonUp'), buttonGui.find('**/InventoryButtonDown'), buttonGui.find('**/InventoryButtonRollover')), image_color=Vec4(0, 0.9, 0.1, 1), text=TTLocalizer.MinigameRulesPanelPlay, text_fg=(1, 1, 1, 1), text_pos=(0, -0.02, 0), text_scale=TTLocalizer.MRPplayButton, pos=(1.0025, 0, -0.203), scale=1.05, command=self.playCallback)
        minigameGui.removeNode()
        buttonGui.removeNode()
        self.timer = ToontownTimer.ToontownTimer()
        self.timer.reparentTo(self.frame)
        self.timer.setScale(0.4)
        self.timer.setPos(0.997, 0, 0.064)
        self.frame.hide()
        return

    def unload(self):
        self.frame.destroy()
        del self.frame
        del self.gameTitleText
        del self.instructionsText
        self.playButton.destroy()
        del self.playButton
        del self.timer

    def enter(self):
        self.frame.show()
        self.timer.countdown(self.TIMEOUT, self.playCallback)
        self.accept('enter', self.playCallback)

    def exit(self):
        self.frame.hide()
        self.timer.stop()
        self.ignore('enter')

    def playCallback(self):
        messenger.send(self.doneEvent)
