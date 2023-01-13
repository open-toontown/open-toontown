from panda3d.core import *
from direct.showbase import DirectObject

class Impulse(DirectObject.DirectObject):

    def __init__(self):
        self.mover = None
        self.nodePath = None
        return

    def destroy(self):
        pass

    def _process(self, dt):
        pass

    def _setMover(self, mover):
        self.mover = mover
        self.nodePath = self.mover.getNodePath()
        self.VecType = self.mover.VecType

    def _clearMover(self, mover):
        if self.mover == mover:
            self.mover = None
            self.nodePath = None
        return

    def isCpp(self):
        return 0
