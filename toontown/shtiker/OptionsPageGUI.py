from direct.gui.DirectGui import DirectButton, DirectLabel
from panda3d.core import TextNode, Vec4

Preloaded = {}

def loadModels():
    if Preloaded:
        return
    gui = loader.loadModel('phase_3.5/models/gui/fishingBook.bam')
    Preloaded['tab1'] = gui.find('**/tabs/polySurface1')
    Preloaded['tab2'] = gui.find('**/tabs/polySurface2')
    gui.removeNode()
    del gui

    guiButton = loader.loadModel('phase_3/models/gui/quit_button')
    Preloaded['button1'] = guiButton.find('**/QuitBtn_UP')
    Preloaded['button2'] = guiButton.find('**/QuitBtn_DN')
    Preloaded['button3'] = guiButton.find('**/QuitBtn_RLVR')
    guiButton.removeNode()
    del guiButton

normalColor = (1, 1, 1, 1)
clickColor = (0.8, 0.8, 0, 1)
rolloverColor = (0.15, 0.82, 1.0, 1)
diabledColor = (1.0, 0.98, 0.15, 1)


class OptionTab(DirectButton):
    def __init__(self, tabType=2, parent=None, **kw):
        loadModels()

        if parent is None:
            parent = aspect2d

        if tabType == 1:
            image = Preloaded['tab1']
        elif tabType == 2:
            image = Preloaded['tab2']
        else:
            image = None

        optiondefs = (
            ('relief', None, None),
            ('text_align', TextNode.ALeft, None),
            ('text_fg', Vec4(0.2, 0.1, 0, 1), None),
            ('image', image, None),
            ('image_color', normalColor, None),
            ('image1_color', clickColor, None),
            ('image2_color', rolloverColor, None),
            ('image3_color', diabledColor, None),
            ('image_scale', (0.033, 0.033, 0.035), None),
            ('image_hpr', (0, 0, -90), None)
        )

        self.defineoptions(kw, optiondefs)
        DirectButton.__init__(self, parent)
        self.initialiseoptions(OptionTab)

buttonbase_xcoord = 0.35
buttonbase_ycoord = 0.45

class OptionButton(DirectButton):
    def __init__(self, parent=None, wantLabel=False, z=buttonbase_ycoord, labelZ=None,
                 labelOrientation='left', labelPos=None, labelText='', image_scale=(0.7, 1, 1), text='', **kw):
        loadModels()

        if parent is None:
            parent = aspect2d

        pos = (buttonbase_xcoord, 0, z) if not kw.get('pos') else kw['pos']
        optiondefs = (
            ('relief', None, None),
            ('image', (Preloaded['button1'], Preloaded['button2'], Preloaded['button3']), None),
            ('image_scale', image_scale, None),
            ('text', text, None),
            ('text_scale', 0.052, None),
            ('text_pos', (0, -0.02), None),
            ('pos', pos, None),
        )

        self.defineoptions(kw, optiondefs)
        DirectButton.__init__(self, parent)
        self.initialiseoptions(OptionButton)
        if wantLabel:
            self.label=OptionLabel(parent=self, z=labelZ, pos=labelPos, orientation=labelOrientation,
                                   text=labelText)

titleHeight = 0.61
textStartHeight = 0.45
leftMargin = -0.72

class OptionLabel(DirectLabel):
    def __init__(self,  parent=None, z=textStartHeight, text_wordwrap=16, text='',
                 orientation='left', **kw):
        loadModels()

        if parent is None:
            parent = aspect2d

        if orientation == 'left':
            pos = (leftMargin, 0, z)
            text_align = TextNode.ALeft
        else:
            pos = kw['pos']
            text_align = TextNode.ACenter

        optiondefs = (
            ('relief', None, None),
            ('pos', pos, None),
            ('text_align', text_align, None),
            ('text_scale', 0.052, None),
            ('text_wordwrap', text_wordwrap, None),
            ('text', text, None)
        )

        self.defineoptions(kw, optiondefs)
        DirectLabel.__init__(self, parent)
        self.initialiseoptions(OptionLabel)
