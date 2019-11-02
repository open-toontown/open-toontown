from pandac.PandaModules import Vec4
from direct.gui.DirectGui import DirectFrame, DirectLabel
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import ToontownIntervals

class LaffMeter(DirectFrame):
    deathColor = Vec4(0.58039216, 0.80392157, 0.34117647, 1.0)

    def __init__(self, avdna, hp, maxHp):
        DirectFrame.__init__(self, relief=None, sortOrder=50)
        self.initialiseoptions(LaffMeter)
        self.container = DirectFrame(parent=self, relief=None)
        self.style = avdna
        self.av = None
        self.hp = hp
        self.maxHp = maxHp
        self.__obscured = 0
        if self.style.type == 't':
            self.isToon = 1
        else:
            self.isToon = 0
        self.load()
        return

    def obscure(self, obscured):
        self.__obscured = obscured
        if self.__obscured:
            self.hide()

    def isObscured(self):
        return self.__obscured

    def load(self):
        gui = loader.loadModel('phase_3/models/gui/laff_o_meter')
        if self.isToon:
            hType = self.style.getType()
            if hType == 'dog':
                headModel = gui.find('**/doghead')
            elif hType == 'cat':
                headModel = gui.find('**/cathead')
            elif hType == 'mouse':
                headModel = gui.find('**/mousehead')
            elif hType == 'horse':
                headModel = gui.find('**/horsehead')
            elif hType == 'rabbit':
                headModel = gui.find('**/bunnyhead')
            elif hType == 'duck':
                headModel = gui.find('**/duckhead')
            elif hType == 'monkey':
                headModel = gui.find('**/monkeyhead')
            elif hType == 'bear':
                headModel = gui.find('**/bearhead')
            elif hType == 'pig':
                headModel = gui.find('**/pighead')
            else:
                raise StandardError('unknown toon species: ', hType)
            self.color = self.style.getHeadColor()
            self.container['image'] = headModel
            self.container['image_color'] = self.color
            self.resetFrameSize()
            self.setScale(0.1)
            self.frown = DirectFrame(parent=self.container, relief=None, image=gui.find('**/frown'))
            self.smile = DirectFrame(parent=self.container, relief=None, image=gui.find('**/smile'))
            self.eyes = DirectFrame(parent=self.container, relief=None, image=gui.find('**/eyes'))
            self.openSmile = DirectFrame(parent=self.container, relief=None, image=gui.find('**/open_smile'))
            self.tooth1 = DirectFrame(parent=self.openSmile, relief=None, image=gui.find('**/tooth_1'))
            self.tooth2 = DirectFrame(parent=self.openSmile, relief=None, image=gui.find('**/tooth_2'))
            self.tooth3 = DirectFrame(parent=self.openSmile, relief=None, image=gui.find('**/tooth_3'))
            self.tooth4 = DirectFrame(parent=self.openSmile, relief=None, image=gui.find('**/tooth_4'))
            self.tooth5 = DirectFrame(parent=self.openSmile, relief=None, image=gui.find('**/tooth_5'))
            self.tooth6 = DirectFrame(parent=self.openSmile, relief=None, image=gui.find('**/tooth_6'))
            self.maxLabel = DirectLabel(parent=self.eyes, relief=None, pos=(0.442, 0, 0.051), text='120', text_scale=0.4, text_font=ToontownGlobals.getInterfaceFont())
            self.hpLabel = DirectLabel(parent=self.eyes, relief=None, pos=(-0.398, 0, 0.051), text='120', text_scale=0.4, text_font=ToontownGlobals.getInterfaceFont())
            self.teeth = [self.tooth6,
             self.tooth5,
             self.tooth4,
             self.tooth3,
             self.tooth2,
             self.tooth1]
            self.fractions = [0.0,
             0.166666,
             0.333333,
             0.5,
             0.666666,
             0.833333]
        gui.removeNode()
        return

    def destroy(self):
        if self.av:
            ToontownIntervals.cleanup(self.av.uniqueName('laffMeterBoing') + '-' + str(self.this))
            ToontownIntervals.cleanup(self.av.uniqueName('laffMeterBoing') + '-' + str(self.this) + '-play')
            self.ignore(self.av.uniqueName('hpChange'))
        del self.style
        del self.av
        del self.hp
        del self.maxHp
        if self.isToon:
            del self.frown
            del self.smile
            del self.openSmile
            del self.tooth1
            del self.tooth2
            del self.tooth3
            del self.tooth4
            del self.tooth5
            del self.tooth6
            del self.teeth
            del self.fractions
            del self.maxLabel
            del self.hpLabel
        DirectFrame.destroy(self)

    def adjustTeeth(self):
        if self.isToon:
            for i in range(len(self.teeth)):
                if self.hp > self.maxHp * self.fractions[i]:
                    self.teeth[i].show()
                else:
                    self.teeth[i].hide()

    def adjustText(self):
        if self.isToon:
            if self.maxLabel['text'] != str(self.maxHp) or self.hpLabel['text'] != str(self.hp):
                self.maxLabel['text'] = str(self.maxHp)
                self.hpLabel['text'] = str(self.hp)

    def animatedEffect(self, delta):
        if delta == 0 or self.av == None:
            return
        name = self.av.uniqueName('laffMeterBoing') + '-' + str(self.this)
        ToontownIntervals.cleanup(name)
        if delta > 0:
            ToontownIntervals.start(ToontownIntervals.getPulseLargerIval(self.container, name))
        else:
            ToontownIntervals.start(ToontownIntervals.getPulseSmallerIval(self.container, name))
        return

    def adjustFace(self, hp, maxHp, quietly = 0):
        if self.isToon and self.hp != None:
            self.frown.hide()
            self.smile.hide()
            self.openSmile.hide()
            self.eyes.hide()
            for tooth in self.teeth:
                tooth.hide()

            delta = hp - self.hp
            self.hp = hp
            self.maxHp = maxHp
            if self.hp < 1:
                self.frown.show()
                self.container['image_color'] = self.deathColor
            elif self.hp >= self.maxHp:
                self.smile.show()
                self.eyes.show()
                self.container['image_color'] = self.color
            else:
                self.openSmile.show()
                self.eyes.show()
                self.maxLabel.show()
                self.hpLabel.show()
                self.container['image_color'] = self.color
                self.adjustTeeth()
            self.adjustText()
            if not quietly:
                self.animatedEffect(delta)
        return

    def start(self):
        if self.av:
            self.hp = self.av.hp
            self.maxHp = self.av.maxHp
        if self.isToon:
            if not self.__obscured:
                self.show()
            self.adjustFace(self.hp, self.maxHp, 1)
            if self.av:
                self.accept(self.av.uniqueName('hpChange'), self.adjustFace)

    def stop(self):
        if self.isToon:
            self.hide()
            if self.av:
                self.ignore(self.av.uniqueName('hpChange'))

    def setAvatar(self, av):
        if self.av:
            self.ignore(self.av.uniqueName('hpChange'))
        self.av = av
