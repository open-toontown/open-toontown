from panda3d.core import Vec4
from direct.gui.DirectGuiGlobals import PGButton

class ColorProfile:
    def __init__(self, clickable=Vec4(0, 0, 0, 1), hover=Vec4(0, 0, 0, 1), pressed=Vec4(0, 0, 0, 1), disabled=Vec4(0, 0, 0, 1)):
        self.clickable = Vec4(clickable)
        self.hover = Vec4(hover)
        self.pressed = Vec4(pressed)
        self.disabled = Vec4(disabled)

    def copy(self):
        return ColorProfile(self.clickable, self.hover, self.pressed, self.disabled)

    def getColorFromState(self, state):
        if state == PGButton.SReady:
            return Vec4(self.clickable)
        elif state == PGButton.SDepressed:
            return Vec4(self.pressed)
        elif state == PGButton.SRollover:
            return Vec4(self.hover)
        elif state == PGButton.SInactive:
            return Vec4(self.disabled)
        return Vec4(self.clickable)

GRAY = ColorProfile(Vec4(0.5, 0.5, 0.5, 1), Vec4(0.6, 0.6, 0.6, 1), Vec4(0.4, 0.4, 0.4, 1), Vec4(0.3, 0.3, 0.3, 1))