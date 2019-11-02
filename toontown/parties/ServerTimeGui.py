from pandac.PandaModules import TextNode
from direct.gui.DirectGui import DirectFrame, DirectLabel
from direct.interval.IntervalGlobal import Func, Sequence, Wait
from toontown.toonbase import ToontownGlobals

class ServerTimeGui(DirectFrame):

    def __init__(self, parent, pos = (0, 0, 0), hourCallback = None):
        DirectFrame.__init__(self, parent=parent, pos=pos)
        self.createGuiObjects()
        self.hourCallback = hourCallback
        self.lastHour = -1
        self.lastMinute = -1

    def createGuiObjects(self):
        textScale = 0.075
        timeFont = ToontownGlobals.getMinnieFont()
        self.hourLabel = DirectLabel(parent=self, pos=(-0.015, 0, 0), relief=None, text='', text_scale=textScale, text_align=TextNode.ARight, text_font=timeFont)
        self.colonLabel = DirectLabel(parent=self, relief=None, text=':', text_scale=textScale, text_align=TextNode.ACenter, text_font=timeFont)
        self.minutesLabel = DirectLabel(relief=None, parent=self, pos=(0.015, 0, 0), text='', text_scale=textScale, text_align=TextNode.ALeft, text_font=timeFont)
        self.amLabel = DirectLabel(relief=None, parent=self, pos=(0.14, 0, 0), text='', text_scale=textScale, text_align=TextNode.ALeft, text_font=timeFont)
        self.ival = Sequence(Func(self.colonLabel.show), Wait(0.75), Func(self.colonLabel.hide), Wait(0.25), Func(self.updateTime))
        self.ival.loop()
        return

    def destroy(self):
        self.ival.finish()
        self.ival = None
        DirectFrame.destroy(self)
        return

    def updateTime(self):
        curServerDate = base.cr.toontownTimeManager.getCurServerDateTime()
        if self.hourCallback is not None:
            if curServerDate.hour != self.lastHour and self.lastHour != -1:
                self.lastHour = curServerDate.hour
                self.hourCallback(curServerDate.hour)
        if not curServerDate.minute == self.lastMinute:
            self.hourLabel['text'] = curServerDate.strftime('%I')
            self.lastHour = curServerDate.hour
            if self.hourLabel['text'][0] == '0':
                self.hourLabel['text'] = self.hourLabel['text'][1:]
            self.minutesLabel['text'] = curServerDate.strftime('%M')
            self.amLabel['text'] = curServerDate.strftime('%p')
        return
