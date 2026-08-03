"""OptionsPage module: contains the OptionsPage class"""
import os
from enum import IntEnum, auto
from typing import Optional

from panda3d.core import TextNode, Vec4
from direct.directnotify import DirectNotifyGlobal
from direct.fsm.FSM import FSM
from direct.gui.DirectGui import *
from direct.showbase.MessengerGlobal import messenger

from otp.otpbase.OTPLocalizerEnglish import SpeedChatStaticTextToontown
from otp.speedchat.SpeedChatGlobals import speedChatStyles
from toontown.settings.Settings import Setting
from toontown.shtiker.ShtikerPage import ShtikerPage
from toontown.toonbase import TTLocalizer
from toontown.toontowngui import TTDialog
from toontown.toontowngui.ToontownScrolledFrame import ToontownScrolledFrame

from direct.distributed.ClockDelta import *

try:
    from toontown.hood import OutdoorLighting
except ImportError:
    import OutdoorLighting
from otp.avatar import ShadowCaster

class OptionTypes(IntEnum):
    BUTTON = auto()
    DROPDOWN = auto()
    SLIDER = auto()
    CONTROL = auto()
    BUTTON_SPEEDCHAT = auto()


OptionToType = {
    # Gameplay
    'camSensitivityX': OptionTypes.SLIDER,
    'camSensitivityY': OptionTypes.SLIDER,
    'movement_mode': OptionTypes.BUTTON,
    'sprint_mode': OptionTypes.BUTTON,
    'fovEffects': OptionTypes.BUTTON,
    'cam-toggle-lock': OptionTypes.BUTTON,
    'boss-alerts': OptionTypes.BUTTON,
    'speedchat-style': OptionTypes.BUTTON_SPEEDCHAT,
    'discord-rich-presence': OptionTypes.BUTTON,
    'color-blind-mode': OptionTypes.BUTTON,
    'want-legacy-models': OptionTypes.BUTTON,
    'laff-display': OptionTypes.BUTTON,
    'battle-speed': OptionTypes.DROPDOWN,

    # Privacy
    "competitive-boss-scoring": OptionTypes.BUTTON,
    "report-errors": OptionTypes.BUTTON,

    # Video
    "borderless": OptionTypes.BUTTON,
    "resolution": OptionTypes.DROPDOWN,
    "vertical-sync": OptionTypes.BUTTON,
    "anisotropic-filter": OptionTypes.DROPDOWN,
    "anti-aliasing": OptionTypes.DROPDOWN,
    "frame-rate-meter": OptionTypes.BUTTON,
    "fps-limit": OptionTypes.DROPDOWN,
    "want-modern-outdoor-lighting": OptionTypes.BUTTON,
    "dynamic-shadows": OptionTypes.BUTTON,
    "shadow-quality": OptionTypes.DROPDOWN,
    "lighting-bloom-enabled": OptionTypes.BUTTON,
    "lighting-god-rays": OptionTypes.BUTTON,
    "want-procedural-sky": OptionTypes.BUTTON,
    "want-day-night-cycle": OptionTypes.BUTTON,
    "want-water-reflections": OptionTypes.BUTTON,
    "drop-shadow-strength": OptionTypes.SLIDER,

    # Audio
    "music": OptionTypes.BUTTON,
    "sfx": OptionTypes.BUTTON,
    "music-volume": OptionTypes.SLIDER,
    "sfx-volume": OptionTypes.SLIDER,
    "toon-chat-sounds": OptionTypes.BUTTON,
    "random-music": OptionTypes.BUTTON,
    "refresh-audio": OptionTypes.BUTTON
}

# All control options are naturally going to be of the CONTROL option type,
# so let's fill the dictionary as such.
controls = list(base.settings.getControls())
OptionToType.update(dict(zip(controls, [OptionTypes.CONTROL for _ in range(len(controls))])))


class OptionsPage(ShtikerPage):
    """OptionsPage class"""

    notify = DirectNotifyGlobal.directNotify.newCategory("OptionsPage")

    # special methods
    def __init__(self):
        """__init__(self)
        OptionsPage constructor: create the options page
        """
        super().__init__()

        if __debug__:
            base.op = self

    def load(self):
        assert self.notify.debugStateCall(self)
        super().load()

        # Create the OptionsTabPage
        self.optionsTabPage = OptionsTabPage(self)
        self.optionsTabPage.hide()

        titleHeight = 0.61  # bigger number means higher the title
        self.title = DirectLabel(
            parent=self,
            relief=None,
            text=TTLocalizer.OptionsPageTitle,
            text_scale=0.12,
            pos=(0, 0, titleHeight),
        )

    def enter(self):
        assert self.notify.debugStateCall(self)

        messenger.send('wakeup')

        self.optionsTabPage.enter()

        # Make the call to the superclass enter method.
        super().enter()

    def exit(self):
        assert self.notify.debugStateCall(self)
        self.optionsTabPage.exit()

        # Make the call to the superclass exit method.
        super().exit()

    def unload(self):
        assert self.notify.debugStateCall(self)
        self.optionsTabPage.unload()

        # Cleanup the direct label.
        self.title.destroy()
        del self.title

        # Make the call to the superclass unload method.
        super().unload()


class OptionsTabPage(DirectFrame, FSM):
    tabOptions = {
        "Gameplay": [
            'camSensitivityX',
            'camSensitivityY',
            'movement_mode',
            'sprint_mode',
            'battle-speed',
            'fovEffects',
            'cam-toggle-lock',
            'boss-alerts',
            'speedchat-style',
            'discord-rich-presence',
            'color-blind-mode',
            'want-legacy-models',
            'laff-display',
        ],
        "Privacy": [
            "competitive-boss-scoring",
            "report-errors"
        ],
        "Controls": [*list(base.settings.getControls())],
        "Video": [
            "borderless", "resolution", "vertical-sync", "anisotropic-filter",
            "anti-aliasing", "frame-rate-meter", "fps-limit",
            "want-modern-outdoor-lighting", "dynamic-shadows", "shadow-quality",
            "lighting-bloom-enabled", "lighting-god-rays",
            "want-procedural-sky", "want-day-night-cycle", "want-water-reflections",
            "drop-shadow-strength",
        ],
        "Audio": [
            "music", "sfx", "music-volume", "sfx-volume", "toon-chat-sounds",
            "random-music", "refresh-audio"
        ],
    }

    def __init__(self, parent=aspect2d, **kw):
        DirectFrame.__init__(self, parent, **kw)
        FSM.__init__(self, "OptionsTabPageNEW")

        self._parent = parent

        self.tabs: dict[str, DirectButton] = {}
        self.options: dict[str, OptionsScrolledFrame] = {}

        self.load()

    def load(self) -> None:
        # Load the Fish Page to borrow its tabs
        guiFish = base.loader.loadModel("phase_3.5/models/gui/fishingBook")
        self.loadTabs(guiFish)
        # Load the "Exit Toontown" button
        guiQuit = base.loader.loadModel("phase_3/models/gui/quit_button")
        self.createExitButton(guiQuit)
        # Load (& hide) the options frames
        guiQuit2 = base.loader.loadModel("phase_3/models/gui/quit_button")
        self.createTabs(guiQuit2)

    def loadTabs(self, gui):
        # The blue and yellow colors are trying to match the
        # rollover and select colors on the options page:
        normalColor = (1, 1, 1, 1)
        clickColor = (.8, .8, 0, 1)
        rolloverColor = (0.15, 0.82, 1.0, 1)
        disabledColor = (1.0, 0.98, 0.15, 1)

        initial = -0.175 * len(self.tabOptions)
        interval = 1.95 * (1 / len(self.tabOptions))

        for i, tab in enumerate(list(self.tabOptions)):
            x = initial + i * interval
            self.tabs[tab] = DirectButton(
                parent=self, relief=None, text=TTLocalizer.OptionsPageTabs[i],
                text_scale=0.06, text_align=TextNode.ACenter,
                text_pos=(0.1, 0.0, 0.0),
                image=gui.find("**/tabs/polySurface1"),
                image_pos=(0.525, 1, -0.91), image_hpr=(0, 0, -90),
                image_scale=(0.033, 0.033, 0.035),
                image_color=normalColor, image1_color=clickColor,
                image2_color=rolloverColor, image3_color=disabledColor,
                text_fg=Vec4(0.2, 0.1, 0, 1), command=self.request,
                extraArgs=[tab], pos=(x, 0, 0.77)
            )

        gui.removeNode()

    def createExitButton(self, gui) -> None:
        self.exitButton = DirectButton(
            parent=self, relief=None,
            image=(gui.find("**/QuitBtn_UP"),
                   gui.find("**/QuitBtn_DN"),
                   gui.find("**/QuitBtn_RLVR"),
                   ),
            image_scale=1.15,
            text=TTLocalizer.OptionsPageExitToontown,
            text_scale=0.052,
            text_pos=(0, -0.02),
            textMayChange=False,
            pos=(0.45, 0, -0.6),
            command=self.__handleExitShowWithConfirm,
        )

        gui.removeNode()

    def createTabs(self, gui) -> None:
        for tab, options in self.tabOptions.items():
            frame = OptionsScrolledFrame(parent=self._parent, options=options, gui=gui)
            frame.hide()
            self.options[tab] = frame

        gui.removeNode()

    def unload(self) -> None:
        for tab in self.tabs.values():
            tab.destroy()

        self.tabs = {}

        self.destroyOptions()

        self.exitButton.destroy()
        self.exitButton = None

    def enter(self) -> None:
        self.show()

        base.localAvatar.disableOldPieKeys()
        self.request("Gameplay")

    def exit(self) -> None:
        self.hide()
        self.request("Off")

        # Write the settings to the local JSON file.
        base.settings.write()
        base.localAvatar.resetPieKeys()
        base.localAvatar.updateOverhead()

    def updateTabs(self) -> None:
        messenger.send("wakeup")

        for tab in self.tabs.values():
            tab["state"] = DGG.NORMAL

        currState = self.getCurrentOrNextState()
        if currState in self.tabs:
            self.tabs[currState]["state"] = DGG.DISABLED

    def destroyOptions(self) -> None:
        for frame in self.options.values():
            frame.destroy()

        self.options = {}

    """
    FSM states
    """

    def enterGameplay(self) -> None:
        self.updateTabs()
        self.options["Gameplay"].show()

    def exitGameplay(self) -> None:
        self.options["Gameplay"].hide()

    def enterPrivacy(self) -> None:
        self.updateTabs()
        self.options["Privacy"].show()

    def exitPrivacy(self) -> None:
        self.options["Privacy"].hide()

    def enterControls(self) -> None:
        self.updateTabs()
        self.options["Controls"].show()

    def exitControls(self) -> None:
        self.options["Controls"].hide()

    def enterVideo(self) -> None:
        self.updateTabs()
        self.options["Video"].show()

    def exitVideo(self) -> None:
        self.options["Video"].hide()

    def enterAudio(self) -> None:
        self.updateTabs()
        self.options["Audio"].show()

    def exitAudio(self) -> None:
        self.options["Audio"].hide()

    """
    Exit button
    """

    def __handleExitShowWithConfirm(self):
        # For exiting from the options panel to the avatar chooser.
        """__handleExitShowWithConfirm(self)
        """
        self.confirm = TTDialog.TTGlobalDialog(
            doneEvent="confirmDone",
            message=TTLocalizer.OptionsPageExitConfirm,
            style=TTDialog.TwoChoice)
        self.confirm.show()
        self._parent.doneStatus = {
            "mode": "exit",
            "exitTo": "closeShard"}
        self.accept("confirmDone", self.__handleConfirm)

    def __handleConfirm(self):
        """__handleConfirm(self)
        """
        status = self.confirm.doneStatus
        self.ignore("confirmDone")
        self.confirm.cleanup()
        del self.confirm
        if (status == "ok"):
            base.cr._userLoggingOut = True
            messenger.send(self._parent.doneEvent)
            # self.cr.loginFSM.request("chooseAvatar", [self.cr.avList])


class OptionsScrolledFrame(ToontownScrolledFrame):
    width = 0.8
    height = 0.53

    def __init__(self, parent=None, options: list[str] = None, gui=None, **kw) -> None:
        super().__init__(
            parent, relief=None,
            pos=(0, 0, 0),
            canvasSize=(-self.width, self.width, -self.height, self.height),
            frameSize=(-self.width, self.width, -self.height, self.height),
            **kw
        )
        self.initialiseoptions(OptionsScrolledFrame)

        self.optionNames = options or []

        self.optionElements = []
        for index, option in enumerate(self.optionNames):
            element = OptionElement(parent, parent=self.getCanvas(), name=option, index=index, gui=gui)
            self.bindToScroll(element)
            self.optionElements.append(element)

        optionAmt = len(self.optionElements)

        # Update the scrollbar if there are more than x elements.
        canvasHeight = ((optionAmt * 0.1) - self.height) if optionAmt > 10 else self.height

        self["canvasSize"] = (-self.width, self.width, -canvasHeight, self.height)
        self.setCanvasSize()

    def destroy(self) -> None:
        if hasattr(self, "optionElements"):
            for option in self.optionElements:
                option.destroy()
            del self.optionElements

        super().destroy()


class DropdownScrolledFrame(ToontownScrolledFrame):
    width = 0.3
    height = 0.3
    offset = 0.225

    def __init__(self, optionName: str, parent=None, pos=(0, 0, 0), options: list[str] = None, command=None, **kw
                 ) -> None:
        super().__init__(
            parent, relief=None,
            pos=(pos[0], pos[1], pos[2] - self.offset),
            canvasSize=(-self.width, self.width, -self.height, self.height),
            frameSize=(-self.width, self.width, -self.height, self.height),
            **kw
        )
        self.initialiseoptions(DropdownScrolledFrame)

        self.optionName = optionName
        self.optionNames = options or []

        gui = base.loader.loadModel("phase_3/models/gui/quit_button")

        self.optionElements = []
        for index, option in enumerate(self.optionNames):
            element = DirectButton(
                parent=self.getCanvas(), relief=None, pos=(0, 0, self.offset - (index * 0.1)),
                text=self.formatSetting(option),
                text_scale=0.052, image_pos=(0, 0, 0.02),
                image=(
                    gui.find("**/QuitBtn_UP"),
                    gui.find("**/QuitBtn_DN"),
                    gui.find("**/QuitBtn_RLVR"),
                ),
                image_scale=(0.7, 1, 1),
                command=command, extraArgs=[option]
            )
            self.bindToScroll(element)
            self.optionElements.append(element)

        gui.removeNode()

        optionAmt = len(self.optionElements)

        # Update the scrollbar if there are more than x elements.
        canvasHeight = ((optionAmt * 0.1) - self.height) if optionAmt > 4 else self.height

        self["canvasSize"] = (-self.width, self.width, -canvasHeight, self.height)
        self.setCanvasSize()

        base.transitions.fadeScreen(0.5)

    def formatSetting(self, setting: Setting) -> str:
        """Given the type of setting we're dealing with, handle
        how the text on the button will display.
        """
        if isinstance(setting, list):
            # When dealing with list options, strip the brackets and
            # join the parts together.
            if self.optionName == "resolution":
                string = "x"
            else:
                string = ""

            return string.join([str(e) for e in setting]).replace("[", "").replace("[", "")
        elif isinstance(setting, int):
            # We're most likely dealing with a list of integer settings,
            # so return the string from the localizer given the current setting.
            if self.optionName == "anti-aliasing":
                return TTLocalizer.OptionAntiAlias[setting]
            if self.optionName == "anisotropic-filter":
                return TTLocalizer.OptionAnisotropic[setting]
            if self.optionName == "fps-limit":
                return TTLocalizer.OptionFPSLimit[setting]
            if self.optionName == "battle-speed":
                return TTLocalizer.OptionBattleSpeed[setting]

        return str(setting)

    def destroy(self) -> None:
        if hasattr(self, "optionElements"):
            for option in self.optionElements:
                option.destroy()
            del self.optionElements

        base.transitions.noFade()

        super().destroy()


def _getPossibleScreenSizes():
    """Return the resolutions offered by the Video > Resolution dropdown.

    Uses the same standard list as DisplaySettingsDialog, plus any display modes
    supported by the current graphics pipe. Values are [width, height] lists to
    match the JSON 'resolution' setting format in Settings.py.
    """
    sizes = [
        [640, 480],    # 4:3
        [800, 600],    # 4:3
        [1024, 768],   # 4:3
        [1280, 720],   # 16:9 HD
        [1280, 800],   # 16:10
        [1280, 1024],  # 5:4
        [1366, 768],   # 16:9
        [1600, 900],   # 16:9
        [1600, 1200],  # 4:3
        [1920, 1080],  # 16:9 Full HD
        [1920, 1200],  # 16:10
        [2560, 1440],  # 16:9 QHD
        [3840, 2160],  # 16:9 4K
    ]
    try:
        displayInfo = base.pipe.getDisplayInformation()
        for i in range(displayInfo.getTotalDisplayModes()):
            size = [displayInfo.getDisplayModeWidth(i), displayInfo.getDisplayModeHeight(i)]
            if size not in sizes:
                sizes.append(size)
    except Exception:
        pass
    return sorted(sizes)


class OptionElement(DirectFrame):
    """
    Option types:
    Button: Clicking on the button will scroll through the options
    - i.e (true, false), (red, yellow, orange, blue, green), etc.
    Slider: Slide between two extremes
    - i.e (0% vol, 100% vol), (50 fov, 150 fov), etc.

    See toontown.settings.Settings.py for the default settings.
    """

    optionOptions = {}
    for option, default in base.settings.defaultSettings.items():
        if isinstance(default, bool):
            optionOptions[option] = [True, False]
        elif option == "movement_mode":
            optionOptions[option] = ["TTCC", "TTR"]
        elif option == "sprint_mode":
            optionOptions[option] = ["Hold", "Toggle"]

    optionOptions.update({
        "resolution": _getPossibleScreenSizes(),
        "anisotropic-filter": list(TTLocalizer.OptionAnisotropic),
        "anti-aliasing": list(TTLocalizer.OptionAntiAlias),
        "fps-limit": list(TTLocalizer.OptionFPSLimit),
        "battle-speed": list(TTLocalizer.OptionBattleSpeed),
        "shadow-quality": ["off", "low", "medium", "high"],
    })

    def __init__(self, page, parent, name: str, index: int, gui, **kw):
        super().__init__(parent, **kw)

        self.page = page

        # The name of the setting.
        self.optionName = name
        self.optionType = OptionToType[self.optionName]

        if self.optionType == OptionTypes.CONTROL:
            currSetting = self.formatKeybind(base.settings.getControl(name))
        elif self.optionType == OptionTypes.BUTTON_SPEEDCHAT:
            currSetting = self.formatSpeedchat(base.localAvatar.getSpeedChatStyleIndex())
        else:
            currSetting = base.settings.get(name)

        z = 0.45 - (index * 0.1)

        # Make the label which will appear on the left-hand side of
        # the page.
        self.label = DirectLabel(
            parent=self, relief=None, pos=(-0.4, 0, z),
            text=TTLocalizer.OptionNames[self.optionName],
            text_scale=0.052,
        )

        # A separate frame for dropdown options which contains a list of option buttons.
        self.dropdownFrame: Optional[DropdownScrolledFrame] = None

        # Make the button which will appear on the right-hand side of
        # the page.
        if self.optionType in (OptionTypes.BUTTON, OptionTypes.CONTROL, OptionTypes.BUTTON_SPEEDCHAT,
                               OptionTypes.DROPDOWN):
            self.optionModifier = DirectButton(
                parent=self, relief=None, pos=(0.37, 0, z),
                text=self.formatSetting(currSetting),
                text_scale=0.052, image_pos=(0, 0, 0.02),
                image=(
                    gui.find("**/QuitBtn_UP"),
                    gui.find("**/QuitBtn_DN"),
                    gui.find("**/QuitBtn_RLVR"),
                ),
                image_scale=(0.7, 1, 1),
            )
            if self.optionType == OptionTypes.DROPDOWN:
                self.optionModifier["command"] = self._openDropdown
            else:
                self.optionModifier["command"] = self._updateButtonOption

            if self.optionType == OptionTypes.CONTROL:
                self.checkForDuplicates()
                self.accept("controls_findDuplicates", self.checkForDuplicates)
            
            if self.optionName == 'refresh-audio':
                self.optionModifier["text"] = TTLocalizer.OptionRefresh  # This is a special case where there is no setting to display.
        
        # Make the slider which will appear on the right-hand side of
        # the page.
        elif self.optionType == OptionTypes.SLIDER:
            self.optionModifier = DirectSlider(
                parent=self, relief=DGG.SUNKEN, pos=(0.37, 0, z), thumb_relief=None,
                thumb_image_scale=(0.3, 0.8, 0.8),
                frameSize=(-0.25, 0.25, -0.1, 0.1),
                image_pos=(0, 0, 0.02),
                thumb_image=(
                    gui.find("**/QuitBtn_UP"),
                    gui.find("**/QuitBtn_DN"),
                    gui.find("**/QuitBtn_RLVR"),
                ),
                value=currSetting,
                command=self._updateSliderOption,
            )

            self.sliderLabel = DirectLabel(
                parent=self.optionModifier, relief=None, pos=(0.3, 0, -0.01),
                text=str(round(currSetting * 100)), text_scale=0.052,
            )
        else:
            raise Exception(f"Undefined option type: {self.optionType}")

        self.controlTask = ""

    def destroy(self) -> None:
        self.doneRegisterKey()

        self.ignore("controls_findDuplicates")

        if hasattr(self, "sliderLabel"):
            self.sliderLabel.destroy()
            del self.sliderLabel

        self.optionModifier.destroy()
        del self.optionModifier

        self.label.destroy()
        del self.label

        super().destroy()

    @staticmethod
    def formatKeybind(keybind: str) -> str:
        return " ".join(keybind.split("_")).title()

    @staticmethod
    def formatSpeedchat(index: int) -> str:
        return SpeedChatStaticTextToontown[speedChatStyles[index][0]]

    def formatSetting(self, setting: Setting) -> str:
        """Given the type of setting we're dealing with, handle
        how the text on the button will display.
        """
        if isinstance(setting, list):
            # When dealing with list options, strip the brackets and
            # join the parts together.
            if self.optionName == "resolution":
                string = "x"
            else:
                string = ""

            return string.join([str(e) for e in setting]).replace("[", "").replace("[", "")
        elif isinstance(setting, bool):
            return TTLocalizer.OptionEnabled if setting else TTLocalizer.OptionDisabled
        elif isinstance(setting, int):
            # We're most likely dealing with a list of integer settings,
            # so return the string from the localizer given the current setting.
            if self.optionName == "anti-aliasing":
                return TTLocalizer.OptionAntiAlias[setting]
            if self.optionName == "anisotropic-filter":
                return TTLocalizer.OptionAnisotropic[setting]
            if self.optionName == "fps-limit":
                return TTLocalizer.OptionFPSLimit[setting]
            if self.optionName == "battle-speed":
                return TTLocalizer.OptionBattleSpeed[setting]

        return str(setting)

    def registerKey(self, keybind: str) -> None:
        base.settings.setControl(self.optionName, keybind)
        self.doneRegisterKey()

    def doneRegisterKey(self) -> None:
        self.ignore("controls_stopListening")
        self.ignore(self.controlTask)
        messenger.send("enable-hotkeys")

        self.optionModifier.configure(
            text=self.formatKeybind(base.settings.getControl(self.optionName)),
            image_color=Vec4(1, 1, 1, 1),
        )

        messenger.send("controls_findDuplicates")

    def checkForDuplicates(self) -> None:
        """Iterate through our control schema to find if there are any
        duplicates. In the case that there is, change the button color
        to RED, to indicate that.
        """
        currentKeybind = base.settings.getControl(self.optionName)
        for control, keybind in base.settings.getControls().items():
            # This control is different, but the keybind is the same.
            # Make the button red.
            if control != self.optionName and keybind == currentKeybind:
                self.optionModifier["image_color"] = Vec4(1, 0.1, 0.1, 1)
                return

        # No duplicates were found, keep the color the same.
        self.optionModifier["image_color"] = Vec4(1, 1, 1, 1)

    def _openDropdown(self) -> None:
        self.dropdownFrame = DropdownScrolledFrame(
            self.optionName, parent=self.page, pos=self.optionModifier.getPos(),
            options=self.optionOptions[self.optionName],
            command=self._updateDropdownOption
        )
        self.dropdownFrame.setBin('gui-popup', 5000)

    def _updateDropdownOption(self, newSetting) -> None:
        print(f"[DEBUG VideoSettings] OptionsPage: _updateDropdownOption called: {self.optionName} -> {newSetting}")
        if self.dropdownFrame is not None:
            self.dropdownFrame.destroy()
            self.dropdownFrame = None

        # Update the new setting.
        base.settings.set(self.optionName, newSetting)

        if self.optionName in (
            "shadow-quality",
        ):
            # Defer to the next task frame — refreshSettings tears down and
            # recreates CommonFilters (bloom) offscreen buffers via
            # engine.removeWindow(), which deadlocks if called from a GUI
            # callback while the render thread holds the GL context mutex.
            taskMgr.remove('optionsRefreshSettings')
            taskMgr.doMethodLater(0, lambda t: (OutdoorLighting.refreshSettings(), t.done)[1],
                                  'optionsRefreshSettings')

        if self.optionName in ("resolution", "anisotropic-filter", "anti-aliasing"):
            base.updateDisplay()
        elif self.optionName == "fps-limit":
            if newSetting != 0:
                globalClock.setMode(ClockObject.MLimited)
                globalClock.setFrameRate(newSetting)
            else:
                globalClock.setMode(ClockObject.MNormal)

        # Update the button text with the new setting.
        self.optionModifier["text"] = self.formatSetting(newSetting)

    def _updateButtonOption(self) -> None:
        messenger.send("wakeup")

        if self.optionType == OptionTypes.CONTROL:
            # Tell any controls that are listening for input to stop doing that.
            messenger.send("controls_stopListening")
            # Then, listen for that same message on this control in the case
            # of another control being clicked.
            self.accept("controls_stopListening", self.doneRegisterKey)

            self.controlTask = f"{self.optionName}-updateControl"

            self.optionModifier.configure(text='...', image_color=Vec4(0.2, 0.9, 0.9, 1))
            base.buttonThrowers[0].node().setButtonDownEvent(self.controlTask)

            messenger.send("disable-hotkeys")
            self.accept(self.controlTask, self.registerKey)
            return
        
        elif self.optionName == 'refresh-audio':
            base.refreshAudio()
            self.optionModifier["text"] = TTLocalizer.OptionRefresh
            return

        elif self.optionType == OptionTypes.BUTTON_SPEEDCHAT:
            # Increment the speedchat index.
            current = base.localAvatar.getSpeedChatStyleIndex()
            new = current + 1
            if new >= len(speedChatStyles):
                new = 0

            # We handle this differently, as it gets saved on the toon itself.
            base.localAvatar.b_setSpeedChatStyleIndex(new)

            # Update the button text with the new setting.
            self.optionModifier["text"] = self.formatSpeedchat(new)
            return

        # Get the current setting.
        currSetting = base.settings.get(self.optionName)

        # Get the index of the next element of the list of options
        # for this setting.
        index = self.optionOptions[self.optionName].index(currSetting) + 1

        # If it's beyond the scope, set it to 0.
        if index >= len(self.optionOptions[self.optionName]):
            index = 0

        # Index into the options with the new index.
        newSetting = self.optionOptions[self.optionName][index]
        print(f"[DEBUG VideoSettings] OptionsPage: _updateButtonOption called: {self.optionName} -> {newSetting}")

        # Update the new setting.
        base.settings.set(self.optionName, newSetting)

        if self.optionName in (
            "want-modern-outdoor-lighting",
            "dynamic-shadows",
            "lighting-bloom-enabled",
            "lighting-god-rays",
            "want-procedural-sky",
            "want-day-night-cycle",
            "want-water-reflections",
            "lighting-fog-enabled",
            "lighting-specular-enabled",
        ):
            # Defer to the next task frame — refreshSettings tears down and
            # recreates CommonFilters (bloom) offscreen buffers via
            # engine.removeWindow(), which deadlocks if called from a GUI
            # callback while the render thread holds the GL context mutex.
            taskMgr.remove('optionsRefreshSettings')
            taskMgr.doMethodLater(0, lambda t: (OutdoorLighting.refreshSettings(), t.done)[1],
                                  'optionsRefreshSettings')

        if self.optionName == "dynamic-shadows":
            try:
                ShadowCaster.setGlobalDropShadowFlag(1 if newSetting else 0)
            except Exception:
                pass

        # Update the client with the new value.
        if self.optionName == "music":
            base.enableMusic(newSetting)
        elif self.optionName == "sfx":
            base.enableSoundEffects(newSetting)
        elif self.optionName == "toon-chat-sounds":
            base.toonChatSounds = newSetting
        elif self.optionName == 'competitive-boss-scoring':
            base.localAvatar.wantCompetitiveBossScoring = newSetting
        elif self.optionName == 'boss-alerts':
            base.localAvatar.wantAlerts = newSetting
        elif self.optionName == 'report-errors':
            os.environ['WANT_ERROR_REPORTING'] = 'true' if newSetting else 'false'
        elif self.optionName in ("borderless", "vertical-sync"):
            base.updateDisplay()
        elif self.optionName == "frame-rate-meter":
            base.setFrameRateMeter(newSetting)
        elif self.optionName == "movement_mode":
            base.localAvatar.updateMovementMode()
        elif self.optionName == "fovEffects":
            base.WANT_FOV_EFFECTS = newSetting
        elif self.optionName == 'discord-rich-presence':
            base.wantRichPresence = newSetting
            base.setRichPresence()
        elif self.optionName == "cam-toggle-lock":
            base.CAM_TOGGLE_LOCK = newSetting
        elif self.optionName == "color-blind-mode":
            base.colorBlindMode = newSetting
        elif self.optionName == "want-legacy-models":
            base.WANT_LEGACY_MODELS = newSetting
        elif self.optionName == "laff-display":
            base.laffMeterDisplay = newSetting
        elif self.optionName == "battle-speed":
            base.battleSpeed = newSetting
        elif self.optionName == "ap-sounds":
            base.apSounds = newSetting
        elif self.optionName == "random-music":
            base.randomMusic = newSetting
            base.refreshRandomMusic()

        # Update the button text with the new setting.
        self.optionModifier["text"] = self.formatSetting(newSetting)

    def _updateSliderOption(self) -> None:
        messenger.send("wakeup")

        newSetting = self.optionModifier["value"]
        print(f"[DEBUG VideoSettings] OptionsPage: _updateSliderOption called: {self.optionName} -> {newSetting}")

        # Save the new option and update the gui.
        if self.optionName == "music-volume":
            base.musicManager.setVolume(newSetting ** 2)
        elif self.optionName == "sfx-volume":
            for sfm in base.sfxManagerList:
                sfm.setVolume(newSetting ** 2)
        elif self.optionName == "drop-shadow-strength":
            try:
                ShadowCaster.setGlobalDropShadowGrayLevel(float(newSetting))
            except Exception:
                pass

        self.sliderLabel["text"] = str(round(newSetting * 100))
        base.settings.set(self.optionName, newSetting)
