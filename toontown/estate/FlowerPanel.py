from toontown.toonbase import ToontownGlobals
from direct.directnotify import DirectNotifyGlobal
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from toontown.toonbase import TTLocalizer
from direct.interval.IntervalGlobal import *
from . import GardenGlobals
from . import FlowerPhoto

class FlowerPanel(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('FlowerPanel')

    def __init__(self, flower = None, parent = aspect2d, doneEvent = None, **kw):
        optiondefs = (('relief', None, None),
         ('state', DGG.DISABLED, None),
         ('image', DGG.getDefaultDialogGeom(), None),
         ('image_color', ToontownGlobals.GlobalDialogColor, None),
         ('image_scale', (0.65, 1, 0.85), None),
         ('text', '', None),
         ('text_scale', 0.06, None),
         ('text_fg', (0, 0, 0, 1), None),
         ('text_pos', (0, 0.35, 0), None),
         ('text_font', ToontownGlobals.getInterfaceFont(), None),
         ('text_wordwrap', 13.5, None))
        self.defineoptions(kw, optiondefs)
        DirectFrame.__init__(self, parent)
        self.initialiseoptions(FlowerPanel)
        self.doneEvent = doneEvent
        self.flower = flower
        self._parent = parent
        self.photo = None
        return

    def destroy(self):
        if self.photo:
            self.photo.destroy()
            self.photo = None
        self.flower = None
        DirectFrame.destroy(self)
        self._parent = None
        return

    def load(self):
        self.weight = DirectLabel(parent=self, pos=(0, 0, -0.28), relief=None, state=DGG.NORMAL, text='', text_scale=0.05, text_fg=(0, 0, 0, 1), text_pos=(0, 0.0, 0), text_font=ToontownGlobals.getInterfaceFont(), text_wordwrap=10.5)
        self.value = DirectLabel(parent=self, pos=TTLocalizer.FPvaluePos, relief=None, state=DGG.NORMAL, text='', text_scale=TTLocalizer.FPvalue, text_fg=(0, 0, 0, 1), text_pos=(0, 0, 0), text_font=ToontownGlobals.getInterfaceFont(), text_wordwrap=10.5)
        self.mystery = DirectLabel(parent=self, pos=(-0.025, 0, -0.055), relief=None, state=DGG.NORMAL, text='?', text_scale=0.25, text_fg=(0, 0, 0, 1), text_pos=(0, 0, 0), text_font=ToontownGlobals.getInterfaceFont(), text_wordwrap=10.5)
        self.extraLabel = DirectLabel(parent=self, relief=None, state=DGG.NORMAL, text='', text_fg=(0.2, 0.8, 0.4, 1), text_font=ToontownGlobals.getSignFont(), text_scale=0.08, pos=(0, 0, 0.26))
        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        self.cancel = DirectButton(parent=self, pos=(0.275, 0, -0.375), relief=None, state=DGG.NORMAL, image=(buttons.find('**/CloseBtn_UP'), buttons.find('**/CloseBtn_DN'), buttons.find('**/CloseBtn_Rllvr')), image_scale=(0.6, 1, 0.6), command=self.handleCancel)
        buttons.removeNode()
        self.photo = FlowerPhoto.FlowerPhoto(parent=self)
        self.update(self.flower)
        return

    def update(self, flower):
        self.flower = flower
        if self.flower == None:
            return
        self['text'] = self.flower.getFullName()
        value = self.flower.getValue()
        if value == 1:
            self.value['text'] = TTLocalizer.GardenPageValueS % value
        else:
            self.value['text'] = TTLocalizer.GardenPageValueP % value
        self.photo.update(flower.getSpecies(), flower.getVariety())
        return

    def setSwimBounds(self, *bounds):
        self.swimBounds = bounds

    def setSwimColor(self, *colors):
        self.swimColor = colors

    def handleCancel(self):
        self.hide()
        if self.doneEvent:
            messenger.send(self.doneEvent)

    def show(self, code = GardenGlobals.FlowerItem):
        messenger.send('wakeup')
        self.photo.setSwimBounds(*self.swimBounds)
        self.photo.setSwimColor(*self.swimColor)
        if code == GardenGlobals.FlowerItem:
            self.extraLabel.hide()
        elif code == GardenGlobals.FlowerItemNewEntry:
            self.extraLabel.show()
            self.extraLabel['text'] = TTLocalizer.FloweringNewEntry
            self.extraLabel['text_scale'] = 0.08
            self.extraLabel.setPos(0, 0, 0.26)
        self.photo.show()
        DirectFrame.show(self)

    def hide(self):
        self.photo.hide()
        DirectFrame.hide(self)
