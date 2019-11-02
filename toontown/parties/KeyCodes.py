from pandac.PandaModules import *
from direct.showbase.DirectObject import DirectObject
ARROW_KEYCODE_MAP = {'arrow_up': 'u',
 'arrow_down': 'd',
 'arrow_left': 'l',
 'arrow_right': 'r'}
KEYCODE_TIMEOUT_SECONDS = 1.5

class KeyCodes(DirectObject):
    notify = directNotify.newCategory('KeyCodes')
    PATTERN_MATCH_EVENT = 'KeyCodes-PATTERN_MATCH'
    PATTERN_NO_MATCH_EVENT = 'KeyCodes-PATTERN_NO_MATCH'
    KEY_DOWN_EVENT = 'KeyCodes-KEY_DOWN_EVENT'
    KEY_UP_EVENT = 'KeyCodes-KEY_UP_EVENT'
    CLEAR_CODE_EVENT = 'KeyCodes-CLEAR_CODE_EVENT'

    def __init__(self, keyMap = ARROW_KEYCODE_MAP, patterns = None, timeout = KEYCODE_TIMEOUT_SECONDS):
        self._keyMap = keyMap
        self._timeout = timeout
        self._keyCode = ''
        self._keyCodeCount = 0
        self._keyCodeTime = 0.0
        self._patterns = []
        self._patternLimit = 0
        self._enabled = False
        self._keyDown = None
        self._keysPressed = 0
        self.listenForPatterns(patterns)
        return

    def destroy(self):
        self.disable()
        self.ignoreAll()
        self._patterns = []
        del self._patterns
        del self._keyMap
        del self._timeout

    def listenForPatterns(self, patterns):
        self._patterns = patterns
        for pattern in self._patterns:
            if len(pattern) > self._patternLimit:
                self._patternLimit = len(pattern)

        if self._enabled:
            self.disable()
            self.enable()

    def isAnyKeyPressed(self):
        return self._keysPressed > 0

    def getCurrentInputLength(self):
        return self._keyCodeCount + 1

    def getLargestPatternLength(self):
        return self._patternLimit

    def getPossibleMatchesList(self):
        return [ p for p in self._patterns if p.startswith(self._keyCode) ]

    def reset(self):
        self._keyCode = ''
        self._keyCodeCount = 0
        self._keyCodeTime = 0.0

    def enable(self):
        if not self._enabled:
            self.notify.debug('Key codes enabled')
            self._enabled = True
            self.__enableControls()

    def disable(self):
        if self._enabled:
            self.notify.debug('Key codes disabled')
            self.__disableControls()
            self.reset()
            self._enabled = False
            self._keyDown = None
            self._keysPressed = 0
        return

    def __enableControls(self):
        for key in self._keyMap.keys():
            self.__acceptKeyDown(key)
            self.__acceptKeyUp(key)

    def __disableControls(self):
        self.ignoreAll()

    def __acceptKeyDown(self, key):
        self.accept(key, self.__handleKeyDown, [key])

    def __acceptKeyUp(self, key):
        self.accept(key + '-up', self.__handleKeyUp, [key])

    def __handleKeyDown(self, key):
        self._keysPressed += 1
        if self._keyDown is None and self._keysPressed == 1:
            self.__updateElapsedTime()
            messenger.send(KeyCodes.KEY_DOWN_EVENT, [self._keyMap[key], self._keyCodeCount])
            self._keyCode += self._keyMap[key]
            self._keyCodeCount += 1
            self._keyDown = key
            self.__checkForPattern()
        else:
            messenger.send(KeyCodes.KEY_DOWN_EVENT, [-1, -1])
        return

    def __handleKeyUp(self, key):
        arg = -1
        if self._keysPressed > 0:
            self._keysPressed -= 1
            if self._keyDown == key and self._keysPressed == 0:
                arg = self._keyMap[key]
        if self._keysPressed == 0:
            self._keyDown = None
        messenger.send(KeyCodes.KEY_UP_EVENT, [arg])
        return

    def __updateElapsedTime(self):
        if self._keyCodeTime != 0.0 and globalClock.getFrameTime() - self._keyCodeTime >= self._timeout:
            self.notify.debug('Key code timed out. Resetting...')
            self.reset()
            messenger.send(KeyCodes.CLEAR_CODE_EVENT)
        self._keyCodeTime = globalClock.getFrameTime()

    def __checkForPattern(self):
        if self._keyCode in self._patterns:
            messenger.send(KeyCodes.PATTERN_MATCH_EVENT, [self._keyCode])
            self.reset()
        elif self._keyCodeCount == self._patternLimit or len(self.getPossibleMatchesList()) == 0:
            messenger.send(KeyCodes.PATTERN_NO_MATCH_EVENT)
            self.reset()
