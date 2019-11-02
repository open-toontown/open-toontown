from pandac.PandaModules import *
from toontown.toonbase.ToontownGlobals import *
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.showbase import DirectObject
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import TTLocalizer
from toontown.pets import PetTricks
from otp.otpbase import OTPLocalizer
from direct.showbase.PythonUtil import lerp
FUDGE_FACTOR = 0.01

class PetDetailPanel(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('PetDetailPanel')

    def __init__(self, pet, closeCallback, parent = aspect2d, **kw):
        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        gui = loader.loadModel('phase_3.5/models/gui/avatar_panel_gui')
        detailPanel = gui.find('**/PetBattlePannel2')
        optiondefs = (('pos', (-4.52, 0.0, 3.05), None),
         ('scale', 3.58, None),
         ('relief', None, None),
         ('image', detailPanel, None),
         ('image_color', GlobalDialogColor, None),
         ('text', TTLocalizer.PetDetailPanelTitle, None),
         ('text_wordwrap', 10.4, None),
         ('text_scale', 0.132, None),
         ('text_pos', (-0.2, 0.6125), None))
        self.defineoptions(kw, optiondefs)
        DirectFrame.__init__(self, parent)
        self.dataText = DirectLabel(self, text='', text_scale=0.09, text_align=TextNode.ALeft, text_wordwrap=15, relief=None, pos=(-0.7, 0.0, 0.55))
        self.bCancel = DirectButton(self, image=(buttons.find('**/CloseBtn_UP'), buttons.find('**/CloseBtn_DN'), buttons.find('**/CloseBtn_Rllvr')), relief=None, text=TTLocalizer.AvatarDetailPanelCancel, text_scale=0.05, text_pos=(0.12, -0.01), pos=(-0.88, 0.0, -0.68), scale=2.0, command=closeCallback)
        self.initialiseoptions(PetDetailPanel)
        self.labels = {}
        self.bars = {}
        self.update(pet)
        buttons.removeNode()
        gui.removeNode()
        return

    def cleanup(self):
        del self.labels
        del self.bars
        self.destroy()

    def update(self, pet):
        if not pet:
            return
        for trickId in PetTricks.TrickId2scIds.keys():
            trickText = TTLocalizer.PetTrickStrings[trickId]
            if trickId < len(pet.trickAptitudes):
                aptitude = pet.trickAptitudes[trickId]
                bar = self.bars.get(trickId)
                label = self.bars.get(trickId)
                if aptitude != 0:
                    healRange = PetTricks.TrickHeals[trickId]
                    hp = lerp(healRange[0], healRange[1], aptitude)
                    if hp == healRange[1]:
                        hp = healRange[1]
                        length = 1
                        barColor = (0.7, 0.8, 0.5, 1)
                    else:
                        hp, length = divmod(hp, 1)
                        barColor = (0.9, 1, 0.7, 1)
                    if not label:
                        self.labels[trickId] = DirectLabel(parent=self, relief=None, pos=(0, 0, 0.43 - trickId * 0.155), scale=0.7, text=trickText, text_scale=TTLocalizer.PDPtrickText, text_fg=(0.05, 0.14, 0.4, 1), text_align=TextNode.ALeft, text_pos=(-1.4, -0.05))
                    else:
                        label['text'] = trickText
                    if not bar:
                        self.bars[trickId] = DirectWaitBar(parent=self, pos=(0, 0, 0.43 - trickId * 0.155), relief=DGG.SUNKEN, frameSize=(-0.5,
                         0.9,
                         -0.1,
                         0.1), borderWidth=(0.025, 0.025), scale=0.7, frameColor=(0.4, 0.6, 0.4, 1), barColor=barColor, range=1.0 + FUDGE_FACTOR, value=length + FUDGE_FACTOR, text=str(int(hp)) + ' ' + TTLocalizer.Laff, text_scale=TTLocalizer.PDPlaff, text_fg=(0.05, 0.14, 0.4, 1), text_align=TextNode.ALeft, text_pos=TTLocalizer.PDPlaffPos)
                    else:
                        bar['value'] = length + FUDGE_FACTOR
                        bar['text'] = (str(int(hp)) + ' ' + TTLocalizer.Laff,)

        return
