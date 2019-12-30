from direct.gui.DirectGui import DGG, DirectFrame, DirectLabel
from pandac.PandaModules import TextNode
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import ToontownIntervals
from toontown.toonbase import TTLocalizer
from . import CogdoUtil
from . import CogdoGameConsts
MEMOICON_SCALE = 0.2

class CogdoMemoGui(DirectFrame):

    def __init__(self, parent):
        DirectFrame.__init__(self, parent=parent, relief=None, state=DGG.NORMAL, sortOrder=DGG.BACKGROUND_SORT_INDEX)
        self._initModel()
        self.hide()
        return

    def destroy(self):
        ToontownIntervals.cleanup('memocount_pulse')
        self._countLabel.removeNode()
        del self._countLabel
        self._memoIcon.removeNode()
        del self._memoIcon
        DirectFrame.destroy(self)

    def posNextToLaffMeter(self):
        self.setPos(-0.975, 0, -0.875)

    def _initModel(self):
        self._countLabel = DirectLabel(parent=self, relief=None, pos=(0.0625, 0, -0.025), scale=CogdoGameConsts.MemoGuiTextScale, text=str(0), text_fg=CogdoGameConsts.MemoGuiTextColor, text_shadow=(0.2, 0.2, 0.2, 1), text_align=TextNode.ALeft, text_font=ToontownGlobals.getToonFont())
        self._memoIcon = CogdoUtil.loadModel('memo_card', game='shared', group='gui')
        self._memoIcon.reparentTo(self)
        self._memoIcon.setScale(MEMOICON_SCALE)
        return

    def setCount(self, count):
        self._countLabel['text'] = str(count)
        self._countLabel.setText()
        ToontownIntervals.cleanup('memocount_pulse')
        ToontownIntervals.start(ToontownIntervals.getPulseLargerIval(self._memoIcon, 'memocount_pulse', scale=MEMOICON_SCALE))
