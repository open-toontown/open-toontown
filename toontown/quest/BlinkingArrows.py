from direct.interval.IntervalGlobal import *
from pandac.PandaModules import *

class BlinkingArrows:

    def __init__(self, parent = aspect2d, otherNode = None):
        self.arrow1 = loader.loadModel('phase_3/models/props/arrow')
        self.arrow2 = loader.loadModel('phase_3/models/props/arrow')
        self.arrowTrack = None
        self.parent = parent
        self.otherNode = otherNode
        return

    def delete(self):
        self.arrowsOff()
        self.arrow1.removeNode()
        self.arrow2.removeNode()
        del self.arrow1
        del self.arrow2

    def arrowsOn(self, x1, y1, h1, x2, y2, h2, onTime = 0.75, offTime = 0.75):
        self.stopArrowsFlashing()
        self.arrow1.setBin('gui-popup', 0)
        self.arrow2.setBin('gui-popup', 0)
        self.arrow1.reparentTo(self.parent)
        self.arrow2.reparentTo(self.parent)
        self.arrow1.setScale(0.2)
        self.arrow2.setScale(0.2)
        self.arrow1.setPos(x1, 0, y1)
        self.arrow2.setPos(x2, 0, y2)
        self.arrow1.setR(h1)
        self.arrow2.setR(h2)
        self.onTime = onTime
        self.offTime = offTime
        self.startArrowsFlashing()

    def arrowsOff(self):
        self.stopArrowsFlashing()
        self.arrow1.reparentTo(hidden)
        self.arrow2.reparentTo(hidden)

    def startArrowsFlashing(self):
        onColor = Vec4(1, 1, 1, 1)
        offColor = Vec4(1, 1, 1, 0.25)
        self.arrow1.show()
        self.arrow2.show()
        if self.otherNode:
            self.otherNode.show()
            self.arrowTrack = Sequence(Parallel(self.arrow1.colorScaleInterval(self.onTime, onColor, offColor), self.arrow2.colorScaleInterval(self.onTime, onColor, offColor), self.otherNode.colorScaleInterval(self.onTime, onColor, offColor)), Parallel(self.arrow1.colorScaleInterval(self.offTime, offColor, onColor), self.arrow2.colorScaleInterval(self.offTime, offColor, onColor), self.otherNode.colorScaleInterval(self.offTime, offColor, onColor)))
        else:
            self.arrowTrack = Sequence(Parallel(self.arrow1.colorScaleInterval(self.onTime, onColor, offColor), self.arrow2.colorScaleInterval(self.onTime, onColor, offColor)), Parallel(self.arrow1.colorScaleInterval(self.offTime, offColor, onColor), self.arrow2.colorScaleInterval(self.offTime, offColor, onColor)))
        self.arrowTrack.loop()

    def stopArrowsFlashing(self):
        if self.arrowTrack:
            self.arrowTrack.finish()
            self.arrowTrack = None
        self.arrow1.hide()
        self.arrow2.hide()
        if self.otherNode:
            self.otherNode.hide()
        return
