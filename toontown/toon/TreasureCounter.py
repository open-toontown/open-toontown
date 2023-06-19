# Noah Hensley

from panda3d.core import Vec4
from direct.gui.DirectGui import DirectFrame, DirectLabel
from toontown.toonbase.ToontownGlobals import *
from toontown.toonbase import ToontownIntervals

# TODO: Have this class be updated every time Toon collects a treasure
# At the moment, it's just updated when it's initialized in LocalToon and when start is called in PublicWalk
# Perhaps start could be called when the Toon collects a treasure

class TreasureCounter(DirectFrame):

    def __init__(self):
        DirectFrame.__init__(self, relief=None, sortOrder=50)
        self.initialiseoptions(TreasureCounter)
        self.container = DirectFrame(parent=self, relief=None)

        self.av = None
        self.hoodTreasuresObtained = None
        self.hoodId = None
        self.__obscured = 0

        self.treasureLabel = None

        self.load()

    def obscure(self, obscured):
        self.__obscured = obscured
        if self.__obscured:
            self.hide()

    def isObscured(self):
        return self.__obscured

    def load(self):
        self.treasureLabel = DirectLabel(parent=self.container, relief=None, pos=(1.8, 0, 2.351), text='120',
                                   text_scale=0.8, text_font=getInterfaceFont())

    def destroy(self):
        del self.av
        del self.hoodTreasuresObtained
        del self.hoodId

        DirectFrame.destroy(self)

    def start(self, hoodId = 0):
        self.hoodId = hoodId
        if self.av:
            self.hoodTreasuresObtained = self.av.hoodTreasuresObtained

        if not self.__obscured:
            self.show()

        self.treasureLabel.show()

        # TODO: Put string literals in Localizer
        # TODO: Instead of displaying this list, get hoodId and display corresponding element from list
        self.treasureLabel['text'] = 'Treasures Collected\nHere: ' + str(self.hoodTreasuresObtained)

    def stop(self):
        self.hide()

    def setAvatar(self, av):
        self.av = av
        self.hoodTreasuresObtained = self.av.hoodTreasuresObtained
