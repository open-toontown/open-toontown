from pandac.PandaModules import *
from direct.showbase.DirectObject import DirectObject
from direct.gui.DirectGui import DirectButton
from direct.gui.OnscreenText import OnscreenText
from direct.task import Task
from toontown.toonbase import ToontownGlobals
from toontown.parties.KeyCodes import KeyCodes, KEYCODE_TIMEOUT_SECONDS
KEY_TO_INDEX = {'u': 0,
 'r': 1,
 'd': 2,
 'l': 3}

class KeyCodesGui(DirectObject):
    notify = directNotify.newCategory('KeyCodesGui')
    TIMEOUT_TASK = 'KeyCodeGui_TIMEOUT_TASK'

    def __init__(self, keyCodes, yOffset = 0.55, keyToIndex = KEY_TO_INDEX):
        self._keyCodes = keyCodes
        self._keyToIndex = keyToIndex
        self._arrowWidth = 0.18
        self._arrowSpaceInBetween = 0.05
        self._yOffset = yOffset
        self._danceMoveLabel = None
        self._arrowNodes = []
        self.timeoutTask = None
        return

    def load(self):
        matchingGameGui = loader.loadModel('phase_3.5/models/gui/matching_game_gui')
        minnieArrow = matchingGameGui.find('**/minnieArrow')
        minnieArrow.setScale(0.6)
        minnieArrow.setZ(self._yOffset + 0.2)
        maxLength = self._keyCodes.getLargestPatternLength()
        for i in range(maxLength):
            arrow = minnieArrow.copyTo(hidden)
            self._arrowNodes.append(arrow)

        matchingGameGui.removeNode()
        self._danceMoveLabel = OnscreenText(parent=aspect2d, text='', pos=(0, self._yOffset), scale=0.15, align=TextNode.ACenter, font=ToontownGlobals.getSignFont(), fg=Vec4(1, 1, 1, 1), mayChange=True)
        self._danceMoveLabel.hide()
        self.enable()

    def unload(self):
        self.disable()
        for arrow in self._arrowNodes:
            arrow.removeNode()
            arrow = None

        self._arrowNodes = []
        if self._danceMoveLabel is not None:
            self._danceMoveLabel.removeNode()
            self._danceMoveLabel = None
        return

    def enable(self):
        self.notify.debug('KeyCodeGui enabled.')
        self.accept(KeyCodes.KEY_DOWN_EVENT, self.__handleKeyDown)
        self.accept(KeyCodes.CLEAR_CODE_EVENT, self.hideAll)

    def disable(self):
        self.notify.debug('KeyCodeGui disabled.')
        self.__stopTimeout()
        self.ignoreAll()

    def hideArrows(self, startIndex = 0):
        length = len(self._arrowNodes)
        if startIndex < length:
            for i in range(startIndex, length):
                self._arrowNodes[i].reparentTo(hidden)

    def hideAll(self, startIndex = 0):
        self.hideArrows(startIndex)
        if self._danceMoveLabel:
            self._danceMoveLabel.hide()

    def showArrow(self, index, key):
        self._arrowNodes[index].setR(-(90 - 90 * self._keyToIndex[key]))
        self._arrowNodes[index].setColor(1, 1, 1, 1)
        self.__centerArrows()
        self._arrowNodes[index].reparentTo(aspect2d)
        self.hideAll(index + 1)
        self.__startTimeout()

    def showText(self, text = ''):
        self.notify.debug('"Showing text "%s"' % text)
        self._danceMoveLabel['text'] = text
        self._danceMoveLabel.show()

    def setColor(self, r, g, b):
        for arrow in self._arrowNodes:
            arrow.setColor(r, g, b)

        self._danceMoveLabel.setColorScale(r, g, b, 1)

    def __startTimeout(self):
        self.__stopTimeout()
        self.timeoutTask = taskMgr.doMethodLater(KEYCODE_TIMEOUT_SECONDS, self.__handleTimeoutTask, KeyCodesGui.TIMEOUT_TASK)

    def __stopTimeout(self):
        if self.timeoutTask is not None:
            taskMgr.remove(self.timeoutTask)
            self.timeoutTask = None
        return

    def __handleTimeoutTask(self, task):
        self.hideAll()
        return Task.done

    def __centerArrows(self):
        length = self._keyCodes.getCurrentInputLength()
        for i in range(length):
            x = -(length * self._arrowWidth * 0.5) + self._arrowWidth * (i + 0.5)
            self._arrowNodes[i].setX(x)

    def __handleKeyDown(self, key, index):
        if index >= 0:
            self.showArrow(index, key)
