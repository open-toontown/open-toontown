import math
from direct.gui.DirectGui import DirectFrame
from pandac.PandaModules import Point3

class StretchingArrow(DirectFrame):
    notify = directNotify.newCategory('StretchingArrow')
    arrowMoving = 0
    arrowBegin = 1
    arrowComplete = 2
    body = None
    head = None

    def __init__(self, parent, useColor = 'blue', autoload = True):
        DirectFrame.__init__(self, parent)
        self.useColor = useColor
        self.endOffset = 1.5
        self.startOffset = 0.0
        self.shrinkRange = 7.0
        self.ratioDrawn = 0.0
        if autoload:
            self.load()
        self.stash()

    def load(self):
        model = loader.loadModel('phase_13/models/parties/stretchingArrow')
        model.setP(-90)
        self.body = model.find('**/arrowBody_' + self.useColor)
        self.body.wrtReparentTo(self)
        self.head = model.find('**/arrowHead_' + self.useColor)
        self.head.wrtReparentTo(self)
        model.removeNode()

    def unload(self):
        if self.body is not None:
            self.body.removeNode()
            self.body = None
        if self.head is not None:
            self.body.removeNode()
            self.body = None
        return

    def reset(self):
        self.ratioDrawn = 0.0

    def draw(self, fromPoint, toPoint, rotation = 0, animate = True):
        arrowlength = 2.72
        if self.body is None or self.head is None:
            return
        actualDifference = fromPoint - toPoint
        actualLength = actualDifference.length()
        oldRatio = self.ratioDrawn
        drawSpeed = 1.6
        drawSpeedMin = 0.6
        downTime = 1.0
        fadeOutTime = 0.5
        drawRate = max(drawSpeedMin, drawSpeed * actualLength / arrowlength)
        self.ratioDrawn += globalClock.getDt() / drawRate
        result = StretchingArrow.arrowMoving
        if self.ratioDrawn >= 1.0:
            result = StretchingArrow.arrowComplete
            self.ratioDrawn = -downTime
        if cmp(oldRatio, 0) != cmp(self.ratioDrawn, 0) and result != StretchingArrow.arrowComplete:
            result = StretchingArrow.arrowBegin
        if not animate:
            self.ratioDrawn = 1.0
        normal = Point3(actualDifference.getX(), actualDifference.getY(), actualDifference.getZ())
        normal.normalize()
        rotation = math.degrees(math.atan2(actualDifference.getY(), actualDifference.getX()))
        endPoint = toPoint + normal * self.endOffset
        startPoint = fromPoint - normal * self.startOffset
        newlength = (endPoint - startPoint).length() / arrowlength
        newScale = min(actualLength / self.shrinkRange, 1.0)
        self.head.setScale(newScale)
        ratio = max(0.0, self.ratioDrawn)
        if ratio == 0.0:
            ratio = 1.0
        newlength *= ratio
        if actualLength < self.endOffset:
            self.stash()
        else:
            self.unstash()
        self.body.setPos(startPoint)
        self.body.setH(rotation)
        self.head.setH(rotation - 90)
        self.body.setScale(newlength - 0.013 * newScale, newScale, newScale)
        vec = startPoint - endPoint
        vec *= ratio
        self.head.setPos(startPoint - vec)
        self.head.setZ(render, self.body.getZ(render) + 0.001)
        if self.ratioDrawn < 0.0:
            self.setAlphaScale(abs(self.ratioDrawn) - (downTime - fadeOutTime))
        else:
            self.setAlphaScale(1.0)
        return
