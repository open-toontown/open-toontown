from pandac.PandaModules import *
from direct.fsm import StateData
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from toontown.toonbase import TTLocalizer

class TownBattleWaitPanel(StateData.StateData):

    def __init__(self, doneEvent):
        StateData.StateData.__init__(self, doneEvent)

    def load(self):
        gui = loader.loadModel('phase_3.5/models/gui/battle_gui')
        self.frame = DirectFrame(relief=None, image=gui.find('**/Waiting4Others'), text_align=TextNode.ALeft, pos=(0, 0, 0), scale=0.65)
        self.frame.hide()
        self.backButton = DirectButton(parent=self.frame, relief=None, image=(gui.find('**/PckMn_BackBtn'), gui.find('**/PckMn_BackBtn_Dn'), gui.find('**/PckMn_BackBtn_Rlvr')), pos=(-0.647, 0, -0.011), scale=1.05, text=TTLocalizer.TownBattleWaitBack, text_scale=0.05, text_pos=(0.01, -0.012), text_fg=Vec4(0, 0, 0.8, 1), command=self.__handleBack)
        gui.removeNode()
        return

    def unload(self):
        self.frame.destroy()
        del self.frame
        del self.backButton

    def enter(self, numParticipants):
        if numParticipants > 1:
            self.frame['text'] = TTLocalizer.TownBattleWaitTitle
            self.frame['text_pos'] = (0, 0.01, 0)
            self.frame['text_scale'] = 0.1
        else:
            self.frame['text'] = TTLocalizer.TownSoloBattleWaitTitle
            self.frame['text_pos'] = (0, -0.05, 0)
            self.frame['text_scale'] = 0.13
        self.frame.show()

    def exit(self):
        self.frame.hide()

    def __handleBack(self):
        doneStatus = {'mode': 'Back'}
        messenger.send(self.doneEvent, [doneStatus])
