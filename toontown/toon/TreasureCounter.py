# Noah Hensley

from direct.gui.DirectGui import DirectFrame, DirectLabel
from toontown.toonbase.ToontownGlobals import *
from toontown.toonbase import TTLocalizer
from toontown.hood import ZoneUtil

class TreasureCounter(DirectFrame):

    def __init__(self):
        DirectFrame.__init__(self, relief=None, sortOrder=50)
        self.initialiseoptions(TreasureCounter)
        self.container = DirectFrame(parent=self, relief=None)

        self.av = None
        self.hoodTreasuresObtained = None
        self.zoneId = None
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
        # Original pos: 1.8, 0, 2.351
        self.treasureLabel = DirectLabel(parent=self.container, relief=None, pos=(5.85, 0, -0.0), text='120',
                                   text_scale=0.8, text_font=getInterfaceFont())

    def destroy(self):
        del self.av
        del self.hoodTreasuresObtained
        del self.zoneId

        DirectFrame.destroy(self)

    def start(self):
        self.zoneId = self.av.getZoneId()
        if ZoneUtil.isWelcomeValley(self.zoneId):  # ID for welcome valley is set to TTC
            self.zoneId = ToontownCentral

        if self.zoneId in HoodToListIndexMapper:  # This ensures the text only shows in playgrounds with treasures
            if self.av:
                self.hoodTreasuresObtained = self.av.hoodTreasuresObtained

            if not self.__obscured:
                self.show()

            self.treasureLabel.show()
            self.treasureLabel['text'] = TTLocalizer.TreasureLabelText % self.hoodTreasuresObtained[HoodToListIndexMapper[self.zoneId]]
        else:
            self.stop()

    def stop(self):
        self.hide()

    def setAvatar(self, av):
        self.av = av
        self.hoodTreasuresObtained = self.av.hoodTreasuresObtained
