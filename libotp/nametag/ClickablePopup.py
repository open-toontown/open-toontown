from direct.showbase.DirectObject import DirectObject
from panda3d.core import *

from . import NametagGlobals


class PopupMouseWatcherRegion(MouseWatcherRegion):
    """
    This is an ultra hacky class!
    The correct implementation of PopupMouseWatcherRegion cannot be done in Python.
    This also assumes that m_mouse_watcher is NametagGlobals::_mouse_watcher.
    """

    class _Param:
        def __init__(self, outside=False):
            self.outside = outside

        def isOutside(self):
            return self.outside

        def getButton(self):
            return MouseButton.one()

    MOUSE_WATCHER_SETUP = False

    def __init__(self, obj, name, frame):
        MouseWatcherRegion.__init__(self, '%s-%s' % (name, id(self)), frame)

        self.obj = obj
        self.__inside = False
        self.__active = False

        if not self.MOUSE_WATCHER_SETUP:
            NametagGlobals._mouse_watcher.setEnterPattern('mouse-enter-%r')
            NametagGlobals._mouse_watcher.setLeavePattern('mouse-leave-%r')
            NametagGlobals._mouse_watcher.setButtonDownPattern('button-down-%r')
            NametagGlobals._mouse_watcher.setButtonUpPattern('button-up-%r')
            self.MOUSE_WATCHER_SETUP = True

        self.slaveObject = DirectObject()
        self.activate()

    def activate(self):
        if not self.__active:
            self.__active = True

            self.slaveObject.accept(self.__getEvent(NametagGlobals._mouse_watcher.getEnterPattern()), self.__mouseEnter)
            self.slaveObject.accept(self.__getEvent(NametagGlobals._mouse_watcher.getLeavePattern()), self.__mouseLeave)
            self.slaveObject.accept(self.__getEvent(NametagGlobals._mouse_watcher.getButtonDownPattern()),
                                    self.__buttonDown)
            self.slaveObject.accept(self.__getEvent(NametagGlobals._mouse_watcher.getButtonUpPattern()), self.__buttonUp)

    def deactivate(self):
        if self.__active:
            self.__active = False

            self.slaveObject.ignoreAll()

    def __mouseEnter(self, region, extra):
        self.__inside = True
        self.obj.enterRegion(None)

    def __mouseLeave(self, region, extra):
        self.__inside = False
        self.obj.exitRegion(None)

    def __buttonDown(self, region, button):
        if button == 'mouse1':
            self.obj.press(PopupMouseWatcherRegion._Param())

    def __buttonUp(self, region, button):
        if button == 'mouse1':
            self.obj.release(PopupMouseWatcherRegion._Param(not self.__inside))

    def __getEvent(self, pattern):
        return pattern.replace('%r', self.getName())


class ClickablePopup:
    def __init__(self):
        self.m_state = PGButton.SReady

    def setState(self, state):
        if state != self.m_state:
            self.m_state = state
            self.updateContents()

    def enterRegion(self, arg):
        if NametagGlobals._rollover_sound:
            NametagGlobals._rollover_sound.play()

        self.setState(PGButton.SRollover)

    def exitRegion(self, arg):
        self.setState(PGButton.SReady)

    def press(self, arg):
        if arg.getButton() == MouseButton.one():
            if NametagGlobals._click_sound:
                NametagGlobals._click_sound.play()
                self.setState(PGButton.SDepressed)

    def release(self, arg):
        if arg.getButton() == MouseButton.one():
            if arg.isOutside():
                self.setState(PGButton.SReady)

            else:
                self.setState(PGButton.SRollover)
                self.click()

    def _createRegion(self, frame):
        name = '%s-%s' % (self.__class__.__name__, self.getName())
        return PopupMouseWatcherRegion(self, name, frame)
