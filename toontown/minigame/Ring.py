from pandac.PandaModules import *
from toontown.toonbase.ToonBaseGlobal import *
from pandac.PandaModules import NodePath
import RingTrack

class Ring(NodePath):

    def __init__(self, moveTrack, tOffset, posScale = 1.0):
        NodePath.__init__(self)
        self.assign(hidden.attachNewNode(base.localAvatar.uniqueName('ring')))
        self.setMoveTrack(moveTrack)
        self.setTOffset(tOffset)
        self.setPosScale(posScale)
        self.setT(0.0)

    def setMoveTrack(self, moveTrack):
        self.__moveTrack = moveTrack

    def setTOffset(self, tOffset):
        self.__tOffset = float(tOffset)

    def setPosScale(self, posScale):
        self.__posScale = posScale

    def setT(self, t):
        pos = self.__moveTrack.eval((t + self.__tOffset) % 1.0)
        self.setPos(pos[0] * self.__posScale, 0, pos[1] * self.__posScale)
