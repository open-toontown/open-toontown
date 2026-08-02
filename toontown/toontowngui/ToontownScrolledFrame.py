from direct.gui.DirectGui import DirectFrame, DGG, DirectScrollBar
from panda3d.core import NodePath, PGScrollFrame


class ToontownScrolledFrame(DirectFrame):

    def __init__(self, parent=None, **kw):
        # Merge keyword options with default options
        self.defineoptions(kw, (
            ('scrollDistance', 0.2, None),
            ('scrollCondition', True, None),
            ('pgFunc', PGScrollFrame, None),
            ('frameSize', (-0.5, 0.5, -0.5, 0.5), None),
            ('canvasSize', (-1, 1, -1, 1), self.setCanvasSize),
            ('manageScrollBars', 1, self.setManageScrollBars),
            ('autoHideScrollBars', 1, self.setAutoHideScrollBars),
            ('scrollBarWidth', 0.08, self.setScrollBarWidth),
            ('borderWidth', (0.01, 0.01), self.setBorderWidth),
        ))
        super().__init__(parent, **kw)

        w = self['scrollBarWidth']

        self.verticalScroll = self.createcomponent(
            "verticalScroll", (), None,
            DirectScrollBar, (self,),
            borderWidth=self['borderWidth'],
            frameSize=(-w / 2.0, w / 2.0, -1, 1),
            orientation=DGG.VERTICAL
        )

        self.guiItem.setVerticalSlider(self.verticalScroll.guiItem)

        self.canvas = NodePath(self.guiItem.getCanvasNode())

        # Call option initialization functions
        self.initialiseoptions(ToontownScrolledFrame)

        # Bind the scroll wheel.
        self['state'] = DGG.NORMAL
        self.bindToScroll(self)
        self.bindToScroll(self.verticalScroll)
        self.bindToScroll(self.verticalScroll.thumb)
        self.bindToScroll(self.verticalScroll.incButton)
        self.bindToScroll(self.verticalScroll.decButton)

    def scroll(self, direction):
        if bool(self['scrollCondition']) or (callable(self['scrollCondition']) and bool(self['scrollCondition']())):
            scrollPercent = self['scrollDistance'] / abs(self['canvasSize'][2] - self['canvasSize'][3])
            self['verticalScroll_value'] = self['verticalScroll_value'] + scrollPercent * direction

    def bindToScroll(self, gui):
        gui.bind(DGG.WHEELUP, lambda _: self.scroll(-1))
        gui.bind(DGG.WHEELDOWN, lambda _: self.scroll(1))

    def setScrollBarWidth(self):
        if self.fInit:
            return

        w = self['scrollBarWidth']
        self.verticalScroll["frameSize"] = (
            -w / 2.0, w / 2.0, self.verticalScroll["frameSize"][2], self.verticalScroll["frameSize"][3])

    def setCanvasSize(self):
        f = self['canvasSize']
        self.guiItem.setVirtualFrame(f[0], f[1], f[2], f[3])

    def getCanvas(self):
        return self.canvas

    def setManageScrollBars(self):
        self.guiItem.setManagePieces(self['manageScrollBars'])

    def setAutoHideScrollBars(self):
        self.guiItem.setAutoHide(self['autoHideScrollBars'])

    def commandFunc(self):
        if self['command']:
            self['command'](*self['extraArgs'])

    def destroy(self):
        # Destroy children of the canvas
        for child in self.canvas.getChildren():
            childGui = self.guiDict.get(child.getName())
            if childGui:
                childGui.destroy()
            else:
                parts = child.getName().split('-')
                simpleChildGui = self.guiDict.get(parts[-1])
                if simpleChildGui:
                    simpleChildGui.destroy()

        if self.verticalScroll:
            self.verticalScroll.destroy()

        self.verticalScroll = None

        super().destroy()
