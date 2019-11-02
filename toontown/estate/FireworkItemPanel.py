from direct.gui.DirectGui import *
from pandac.PandaModules import *
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.effects import FireworkGlobals
from toontown.effects import Fireworks
import FireworksGui

class FireworkItemPanel(DirectFrame):

    def __init__(self, itemName, itemNum, *extraArgs):
        self.gui = extraArgs[0][0]
        self.type = extraArgs[0][1][itemNum]
        self.shootEvent = extraArgs[0][2]
        self.name = FireworkGlobals.Names[self.type]
        DirectFrame.__init__(self, image=DGG.getDefaultDialogGeom(), image_color=(0.75, 0.75, 0.75, 1), image_scale=(0.25, 0, 0.25), relief=None)
        self.initialiseoptions(FireworkItemPanel)
        self.load()
        return

    def load(self):
        self.picture = DirectButton(parent=self, image=(DGG.getDefaultDialogGeom(), DGG.getDefaultDialogGeom(), DGG.getDefaultDialogGeom()), relief=None, command=self.__launchFirework, extraArgs=[self.type], image_color=(0.8, 0.9, 1, 1))
        self.picture.setScale(0.2)
        self.picture.setPos(0, 0, 0)
        self.picture.initialiseoptions(self.picture)
        panelWidth = 7
        nameFont = ToontownGlobals.getInterfaceFont()
        self.quantityLabel = DirectLabel(parent=self.picture, relief=None, pos=(0, 0, 0.0), scale=0.45, text=self.name, text_scale=0.6, text_fg=(0, 0, 0, 1), text_pos=(0, -.14, 0), text_font=nameFont, text_wordwrap=panelWidth)
        return

    def unload(self):
        del self.picture
        self.quantityLabel.destroy()
        del self.quantityLabel
        DirectFrame.destroy(self)

    def destroy(self):
        self.unload()

    def __launchFirework(self, index):
        messenger.send(self.shootEvent, [index])

    def __dimSky(self):
        self.oldSkyScale = base.cr.playGame.hood.loader.sky.getColorScale()
        base.cr.playGame.hood.loader.sky.setColorScale(0.3, 0.3, 0.3, 1)

    def __resetSky(self):
        base.cr.playGame.hood.loader.sky.setColorScale(self.oldSkyScale)
