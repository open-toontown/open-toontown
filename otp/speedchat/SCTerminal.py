from SCElement import SCElement
from SCObject import SCObject
from SCMenu import SCMenu
from direct.fsm.StatePush import StateVar, FunctionCall
from direct.showbase.DirectObject import DirectObject
from otp.avatar import Emote
SCTerminalSelectedEvent = 'SCTerminalSelected'
SCTerminalLinkedEmoteEvent = 'SCTerminalLinkedEmoteEvent'
SCWhisperModeChangeEvent = 'SCWhisperModeChange'

class SCTerminal(SCElement):

    def __init__(self, linkedEmote = None):
        SCElement.__init__(self)
        self.setLinkedEmote(linkedEmote)
        scGui = loader.loadModel(SCMenu.GuiModelName)
        self.emotionIcon = scGui.find('**/emotionIcon')
        self.setDisabled(False)
        self.__numCharges = -1
        self._handleWhisperModeSV = StateVar(False)
        self._handleWhisperModeFC = None
        return

    def destroy(self):
        self._handleWhisperModeSV.set(False)
        if self._handleWhisperModeFC:
            self._handleWhisperModeFC.destroy()
        self._handleWhisperModeSV.destroy()
        SCElement.destroy(self)

    def privSetSettingsRef(self, settingsRef):
        SCElement.privSetSettingsRef(self, settingsRef)
        if self._handleWhisperModeFC is None:
            self._handleWhisperModeFC = FunctionCall(self._handleWhisperModeSVChanged, self._handleWhisperModeSV)
            self._handleWhisperModeFC.pushCurrentState()
        self._handleWhisperModeSV.set(self.settingsRef is not None and not self.isWhisperable())
        return

    def _handleWhisperModeSVChanged(self, handleWhisperMode):
        if handleWhisperMode:
            self._wmcListener = DirectObject()
            self._wmcListener.accept(self.getEventName(SCWhisperModeChangeEvent), self._handleWhisperModeChange)
        elif hasattr(self, '_wmcListener'):
            self._wmcListener.ignoreAll()
            del self._wmcListener
            self.invalidate()

    def _handleWhisperModeChange(self, whisperMode):
        self.invalidate()

    def handleSelect(self):
        messenger.send(self.getEventName(SCTerminalSelectedEvent))
        if self.hasLinkedEmote() and self.linkedEmoteEnabled():
            messenger.send(self.getEventName(SCTerminalLinkedEmoteEvent), [self.linkedEmote])

    def isWhisperable(self):
        return True

    def getLinkedEmote(self):
        return self.linkedEmote

    def setLinkedEmote(self, linkedEmote):
        self.linkedEmote = linkedEmote
        self.invalidate()

    def hasLinkedEmote(self):
        return self.linkedEmote is not None

    def linkedEmoteEnabled(self):
        if Emote.globalEmote:
            return Emote.globalEmote.isEnabled(self.linkedEmote)

    def getCharges(self):
        return self.__numCharges

    def setCharges(self, nCharges):
        self.__numCharges = nCharges
        if nCharges is 0:
            self.setDisabled(True)

    def isDisabled(self):
        return self.__disabled or self.isWhispering() and not self.isWhisperable()

    def setDisabled(self, bDisabled):
        self.__disabled = bDisabled

    def onMouseClick(self, event):
        if not self.isDisabled():
            SCElement.onMouseClick(self, event)
            self.handleSelect()

    def getMinDimensions(self):
        width, height = SCElement.getMinDimensions(self)
        if self.hasLinkedEmote():
            width += 1.3
        return (width, height)

    def finalize(self, dbArgs = {}):
        if not self.isDirty():
            return
        args = {}
        if self.hasLinkedEmote():
            self.lastEmoteIconColor = self.getEmoteIconColor()
            self.emotionIcon.setColorScale(*self.lastEmoteIconColor)
            args.update({'image': self.emotionIcon,
             'image_pos': (self.width - 0.6, 0, -self.height * 0.5)})
        if self.isDisabled():
            args.update({'rolloverColor': (0, 0, 0, 0),
             'pressedColor': (0, 0, 0, 0),
             'rolloverSound': None,
             'clickSound': None,
             'text_fg': self.getColorScheme().getTextDisabledColor() + (1,)})
        args.update(dbArgs)
        SCElement.finalize(self, dbArgs=args)
        return

    def getEmoteIconColor(self):
        if self.linkedEmoteEnabled() and not self.isWhispering():
            r, g, b = self.getColorScheme().getEmoteIconColor()
        else:
            r, g, b = self.getColorScheme().getEmoteIconDisabledColor()
        return (r,
         g,
         b,
         1)

    def updateEmoteIcon(self):
        if hasattr(self, 'button'):
            self.lastEmoteIconColor = self.getEmoteIconColor()
            for i in range(self.button['numStates']):
                self.button['image%s_image' % i].setColorScale(*self.lastEmoteIconColor)

        else:
            self.invalidate()

    def enterVisible(self):
        SCElement.enterVisible(self)
        if hasattr(self, 'lastEmoteIconColor'):
            if self.getEmoteIconColor() != self.lastEmoteIconColor:
                self.invalidate()

        def handleWhisperModeChange(whisperMode, self = self):
            if self.hasLinkedEmote():
                if self.isVisible() and not self.isWhispering():
                    self.updateEmoteIcon()

        self.accept(self.getEventName(SCWhisperModeChangeEvent), handleWhisperModeChange)

        def handleEmoteEnableStateChange(self = self):
            if self.hasLinkedEmote():
                if self.isVisible() and not self.isWhispering():
                    self.updateEmoteIcon()

        if self.hasLinkedEmote():
            if Emote.globalEmote:
                self.accept(Emote.globalEmote.EmoteEnableStateChanged, handleEmoteEnableStateChange)

    def exitVisible(self):
        SCElement.exitVisible(self)
        self.ignore(self.getEventName(SCWhisperModeChangeEvent))
        if Emote.globalEmote:
            self.ignore(Emote.globalEmote.EmoteEnableStateChanged)

    def getDisplayText(self):
        if self.getCharges() is not -1:
            return self.text + ' (%s)' % self.getCharges()
        else:
            return self.text
