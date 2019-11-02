from direct.fsm import FSM
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.directnotify import DirectNotifyGlobal
from direct.interval.IntervalGlobal import *
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.fishing import FishPhoto
from toontown.fishing import BingoGlobals

class BingoCardCell(DirectButton, FSM.FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('BingoCardCell')

    def __init__(self, cellId, fish, model, color, parent, **kw):
        self.model = model
        self.color = color
        buttonToUse = self.model.find('**/mickeyButton')
        optiondefs = (('relief', None, None),
         ('state', DGG.DISABLED, None),
         ('image', buttonToUse, None),
         ('image_color', self.color, None),
         ('image_hpr', (0, 90, 0), None),
         ('image_pos', (0, 0, 0), None),
         ('pressEffect', False, None))
        self.defineoptions(kw, optiondefs)
        DirectButton.__init__(self, parent)
        FSM.FSM.__init__(self, 'BingoCardCell')
        self.initialiseoptions(BingoCardCell)
        self.parent = parent
        self.fish = fish
        self.cellId = cellId
        self.request('Off')
        return

    def destroy(self):
        DirectButton.destroy(self)

    def setImageTo(self, button):
        button.setHpr(0, 90, 0)
        button.setPos(0, 0, 0)
        button.setScale(BingoGlobals.CellImageScale)
        button.setColor(self.color[0], self.color[1], self.color[2], self.color[3])
        self['image'] = button
        self.setImage()

    def getButtonName(self):
        genus = self.getFishGenus()
        return BingoGlobals.FishButtonDict[genus][0]

    def generateLogo(self):
        buttonName = self.getButtonName()
        buttonToUse = self.model.find('**/' + buttonName)
        self.setImageTo(buttonToUse)

    def generateMarkedLogo(self):
        self.setImageTo(self.model.find('**/mickeyButton'))

    def setFish(self, fish):
        if self.fish:
            del self.fish
        self.fish = fish

    def getFish(self):
        return self.fish

    def getFishGenus(self):
        if self.fish == 'Free':
            return -1
        return self.fish.getGenus()

    def getFishSpecies(self):
        return self.fish.getSpecies()

    def enable(self, callback = None):
        self.request('On', callback)

    def disable(self):
        self.request('Off')
        if not self.fish == 'Free':
            self.generateMarkedLogo()

    def enterOff(self):
        self['state'] = DGG.DISABLED
        self['command'] = None
        return

    def filterOff(self, request, args):
        if request == 'On':
            return (request, args)
        elif request == 'Off':
            return request
        else:
            self.notify.debug('filterOff: Invalid State Transition from Off to %s' % request)

    def enterOn(self, args):
        self['state'] = DGG.NORMAL
        if args[0]:
            self['command'] = Func(args[0], self.cellId).start

    def filterOn(self, request, args):
        if request == 'Off':
            return request
        else:
            self.notify.debug('filterOn: Invalid State Transition from Off to %s' % request)
