from panda3d.core import *

from . import NametagGlobals


class MarginPopup(PandaNode):
    def __init__(self):
        PandaNode.__init__(self, 'MarginPopup')

        self.m_managed = False
        self.m_visible = False
        self.m_np = None
        self.m_cell_width = 1.0
        self.m_seq = NametagGlobals._margin_prop_seq

    def getCellWidth(self):
        return self.m_cell_width

    def setManaged(self, value):
        self.m_managed = value
        if value:
            self.m_np = NodePath.anyPath(self)

        else:
            self.m_np = None

    def isManaged(self):
        return self.m_managed

    def setVisible(self, value):
        self.m_visible = value

    def isVisible(self):
        return self.m_visible

    def getScore(self):
        return 0.0

    def getObjectCode(self):
        return 0

    def considerVisible(self):
        if self.m_seq != NametagGlobals._margin_prop_seq:
            self.m_seq = NametagGlobals._margin_prop_seq
            self.updateContents()

    def updateContents(self):
        pass

    def frameCallback(self):
        pass
