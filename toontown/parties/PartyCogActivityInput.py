from direct.showbase.DirectObject import DirectObject
from panda3d.core import ModifierButtons
ROTATE_LEFT_KEY = 'arrow_left'
ROTATE_RIGHT_KEY = 'arrow_right'
FORWARD_KEY = 'arrow_up'
BACKWARDS_KEY = 'arrow_down'
THROW_PIE_KEYS = ['control', 'delete', 'insert']

class PartyCogActivityInput(DirectObject):
    notify = directNotify.newCategory('PartyCogActivityInput')
    leftPressed = 0
    rightPressed = 0
    upPressed = 0
    downPressed = 0
    throwPiePressed = False
    throwPieWasReleased = False
    throwPiePressedStartTime = 0

    def __init__(self, exitActivityCallback):
        DirectObject.__init__(self)
        self.exitActivityCallback = exitActivityCallback
        self._prevModifierButtons = base.mouseWatcherNode.getModifierButtons()

    def enable(self):
        self.enableAimKeys()
        self.enableThrowPieKeys()

    def disable(self):
        self.disableAimKeys()
        self.disableThrowPieKeys()

    def enableExitActivityKeys(self):
        self.accept('escape', self.exitActivityCallback)

    def disableExitActivityKeys(self):
        self.ignore('escape')

    def enableThrowPieKeys(self):
        for key in THROW_PIE_KEYS:
            self.accept(key, self.handleThrowPieKeyPressed, [key])

        self.throwPiePressed = False
        self.readyToThrowPie = False

    def disableThrowPieKeys(self):
        for key in THROW_PIE_KEYS:
            self.ignore(key)
            self.ignore(key + '-up')

    def handleThrowPieKeyPressed(self, key):
        if self.throwPiePressed:
            return
        self.throwPiePressed = True
        self.accept(key + '-up', self.handleThrowPieKeyReleased, [key])
        self.throwPiePressedStartTime = globalClock.getFrameTime()

    def handleThrowPieKeyReleased(self, key):
        if not self.throwPiePressed:
            return
        self.ignore(key + '-up')
        self.throwPieWasReleased = True
        self.throwPiePressed = False

    def enableAimKeys(self):
        self.leftPressed = 0
        self.rightPressed = 0
        base.mouseWatcherNode.setModifierButtons(ModifierButtons())
        base.buttonThrowers[0].node().setModifierButtons(ModifierButtons())
        self.accept(ROTATE_LEFT_KEY, self.__handleLeftKeyPressed)
        self.accept(ROTATE_RIGHT_KEY, self.__handleRightKeyPressed)
        self.accept(FORWARD_KEY, self.__handleUpKeyPressed)
        self.accept(BACKWARDS_KEY, self.__handleDownKeyPressed)

    def disableAimKeys(self):
        self.ignore(ROTATE_LEFT_KEY)
        self.ignore(ROTATE_RIGHT_KEY)
        self.ignore(FORWARD_KEY)
        self.ignore(BACKWARDS_KEY)
        self.leftPressed = 0
        self.rightPressed = 0
        self.upPressed = 0
        self.downPressed = 0
        self.ignore(ROTATE_LEFT_KEY + '-up')
        self.ignore(ROTATE_RIGHT_KEY + '-up')
        self.ignore(FORWARD_KEY + '-up')
        self.ignore(BACKWARDS_KEY + '-up')
        base.mouseWatcherNode.setModifierButtons(self._prevModifierButtons)
        base.buttonThrowers[0].node().setModifierButtons(self._prevModifierButtons)

    def __handleLeftKeyPressed(self):
        self.ignore(ROTATE_LEFT_KEY)
        self.accept(ROTATE_LEFT_KEY + '-up', self.__handleLeftKeyReleased)
        self.__leftPressed()

    def __handleRightKeyPressed(self):
        self.ignore(ROTATE_RIGHT_KEY)
        self.accept(ROTATE_RIGHT_KEY + '-up', self.__handleRightKeyReleased)
        self.__rightPressed()

    def __handleLeftKeyReleased(self):
        self.ignore(ROTATE_LEFT_KEY + '-up')
        self.accept(ROTATE_LEFT_KEY, self.__handleLeftKeyPressed)
        self.__leftReleased()

    def __handleRightKeyReleased(self):
        self.ignore(ROTATE_RIGHT_KEY + '-up')
        self.accept(ROTATE_RIGHT_KEY, self.__handleRightKeyPressed)
        self.__rightReleased()

    def __handleUpKeyPressed(self):
        self.ignore(FORWARD_KEY)
        self.accept(FORWARD_KEY + '-up', self.__handleUpKeyReleased)
        self.__upPressed()

    def __handleUpKeyReleased(self):
        self.ignore(FORWARD_KEY + '-up')
        self.accept(FORWARD_KEY, self.__handleUpKeyPressed)
        self.__upReleased()

    def __handleDownKeyPressed(self):
        self.ignore(BACKWARDS_KEY)
        self.accept(BACKWARDS_KEY + '-up', self.__handleDownKeyReleased)
        self.__downPressed()

    def __handleDownKeyReleased(self):
        self.ignore(BACKWARDS_KEY + '-up')
        self.accept(BACKWARDS_KEY, self.__handleDownKeyPressed)
        self.__downReleased()

    def __leftPressed(self):
        self.leftPressed = self.__enterControlActive(self.leftPressed)

    def __rightPressed(self):
        self.rightPressed = self.__enterControlActive(self.rightPressed)

    def __upPressed(self):
        self.upPressed = self.__enterControlActive(self.upPressed)

    def __downPressed(self):
        self.downPressed = self.__enterControlActive(self.downPressed)

    def __leftReleased(self):
        self.leftPressed = self.__exitControlActive(self.leftPressed)

    def __rightReleased(self):
        self.rightPressed = self.__exitControlActive(self.rightPressed)

    def __upReleased(self):
        self.upPressed = self.__exitControlActive(self.upPressed)

    def __downReleased(self):
        self.downPressed = self.__exitControlActive(self.downPressed)

    def __enterControlActive(self, input):
        return input + 1

    def __exitControlActive(self, input):
        return max(0, input - 1)
