from pandac.PandaModules import *
from toontown.toonbase.ToonBaseGlobal import *
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.gui.DirectScrolledList import *
from direct.distributed.ClockDelta import *
from toontown.toontowngui import TTDialog
import math
from toontown.toonbase import ToontownGlobals
from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM
from direct.fsm import State
from toontown.toon import Toon
from direct.showbase import RandomNumGen
from toontown.toonbase import TTLocalizer
import random
import random
import cPickle
from direct.showbase import PythonUtil
import GameSprite
from math import pi
from toontown.estate import GardenGlobals
SHOVEL = 0
WATERINGCAN = 1
GAMEWIN = 2

class GardenProgressMeter(DirectObject.DirectObject):

    def __init__(self, typePromotion = 'game', level = 0):
        if typePromotion == 'shovel':
            self.typePromotion = SHOVEL
        elif typePromotion == 'wateringCan':
            self.typePromotion = WATERINGCAN
        elif typePromotion == 'game':
            self.typePromotion == GAMEWIN
        else:
            print 'No type of %s' % typePromotion
        self.level = level
        self.acceptErrorDialog = None
        self.doneEvent = 'game Done'
        self.sprites = []
        self.load()
        thing = self.model.find('**/item_board')
        self.block = self.model1.find('**/minnieCircle')
        return

    def load(self):
        model = loader.loadModel('phase_5.5/models/gui/package_delivery_panel')
        model1 = loader.loadModel('phase_3.5/models/gui/matching_game_gui')
        self.model = model
        self.model1 = model1
        background = model.find('**/bg')
        itemBoard = model.find('**/item_board')
        congratsMessage = 'Super Congratulations!!'
        if self.typePromotion == SHOVEL:
            congratsMessage = TTLocalizer.GardenShovelLevelUp + ' \n' + GardenGlobals.ShovelAttributes[self.level]['name']
        elif self.typePromotion == WATERINGCAN:
            congratsMessage = TTLocalizer.GardenWateringCanLevelUp + ' \n' + GardenGlobals.WateringCanAttributes[self.level]['name']
        elif self.typePromotion == GAMEWIN:
            congratsMessage = TTLocalizer.GardenMiniGameWon
        self.frame = DirectFrame(scale=1.1, relief=None, image=DGG.getDefaultDialogGeom(), image_scale=(1.75, 1, 0.75), image_color=ToontownGlobals.GlobalDialogColor, frameSize=(-0.5,
         0.5,
         -0.45,
         -0.05))
        self.congratsText = DirectLabel(scale=1.1, relief=None, text_pos=(0, 0.2), text_wordwrap=16, text=congratsMessage, text_font=ToontownGlobals.getSignFont(), pos=(0.0, 0.0, 0.0), text_scale=0.1, text0_fg=(1, 1, 1, 1), parent=self.frame)
        gui2 = loader.loadModel('phase_3/models/gui/quit_button')
        self.quitButton = DirectButton(parent=self.frame, relief=None, image=(gui2.find('**/QuitBtn_UP'), gui2.find('**/QuitBtn_DN'), gui2.find('**/QuitBtn_RLVR')), pos=(0.5, 1.0, -0.32), scale=0.9, text='Exit', text_font=ToontownGlobals.getSignFont(), text0_fg=(1, 1, 1, 1), text1_fg=(1, 1, 1, 1), text2_fg=(1, 1, 1, 1), text_scale=0.045, text_pos=(0, -0.01), command=self.__handleExit)
        return

    def unload(self):
        self.frame.destroy()
        del self.frame
        if self.acceptErrorDialog:
            self.acceptErrorDialog.cleanup()
            self.acceptErrorDialog = None
        taskMgr.remove('gameTask')
        self.ignoreAll()
        return

    def show(self):
        self.frame.show()

    def hide(self):
        self.frame.hide()

    def __handleExit(self):
        self.__acceptExit()

    def __acceptExit(self, buttonValue = None):
        if hasattr(self, 'frame'):
            self.hide()
            self.unload()
            messenger.send(self.doneEvent)
