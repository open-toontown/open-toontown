from panda3d.core import *
from . import ShtikerPage
from toontown.toontowngui import TTDialog
from direct.gui.DirectGui import *
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import ToontownBattleGlobals
from toontown.hood import OutdoorLighting
from . import DisplaySettingsDialog
from direct.task import Task
from otp.speedchat import SpeedChat
from otp.speedchat import SCColorScheme
from otp.speedchat import SCStaticTextTerminal
from direct.directnotify import DirectNotifyGlobal
from enum import IntEnum
speedChatStyles = ((2000,
  (200 / 255.0, 60 / 255.0, 229 / 255.0),
  (200 / 255.0, 135 / 255.0, 255 / 255.0),
  (220 / 255.0, 195 / 255.0, 229 / 255.0)),
 (2001,
  (0 / 255.0, 0 / 255.0, 255 / 255.0),
  (140 / 255.0, 150 / 255.0, 235 / 255.0),
  (201 / 255.0, 215 / 255.0, 255 / 255.0)),
 (2002,
  (90 / 255.0, 175 / 255.0, 225 / 255.0),
  (120 / 255.0, 215 / 255.0, 255 / 255.0),
  (208 / 255.0, 230 / 255.0, 250 / 255.0)),
 (2003,
  (130 / 255.0, 235 / 255.0, 235 / 255.0),
  (120 / 255.0, 225 / 255.0, 225 / 255.0),
  (234 / 255.0, 255 / 255.0, 255 / 255.0)),
 (2004,
  (0 / 255.0, 200 / 255.0, 70 / 255.0),
  (0 / 255.0, 200 / 255.0, 80 / 255.0),
  (204 / 255.0, 255 / 255.0, 204 / 255.0)),
 (2005,
  (235 / 255.0, 230 / 255.0, 0 / 255.0),
  (255 / 255.0, 250 / 255.0, 100 / 255.0),
  (255 / 255.0, 250 / 255.0, 204 / 255.0)),
 (2006,
  (255 / 255.0, 153 / 255.0, 0 / 255.0),
  (229 / 255.0, 147 / 255.0, 0 / 255.0),
  (255 / 255.0, 234 / 255.0, 204 / 255.0)),
 (2007,
  (255 / 255.0, 0 / 255.0, 50 / 255.0),
  (229 / 255.0, 0 / 255.0, 50 / 255.0),
  (255 / 255.0, 204 / 255.0, 204 / 255.0)),
 (2008,
  (255 / 255.0, 153 / 255.0, 193 / 255.0),
  (240 / 255.0, 157 / 255.0, 192 / 255.0),
  (255 / 255.0, 215 / 255.0, 238 / 255.0)),
 (2009,
  (170 / 255.0, 120 / 255.0, 20 / 255.0),
  (165 / 255.0, 120 / 255.0, 50 / 255.0),
  (210 / 255.0, 200 / 255.0, 180 / 255.0)))
PageMode = IntEnum('PageMode', ('Options', 'Codes'), start=0)
OptionsSubTab = IntEnum('OptionsSubTab', ('Audio', 'Social', 'DisplayChat', 'Advanced', 'Gameplay', 'Lighting'), start=0)

class OptionsPage(ShtikerPage.ShtikerPage):
    notify = DirectNotifyGlobal.directNotify.newCategory('OptionsPage')

    def __init__(self):
        ShtikerPage.ShtikerPage.__init__(self)

    def load(self):
        ShtikerPage.ShtikerPage.load(self)
        self.optionsTabPage = OptionsTabPage(self)
        self.optionsTabPage.hide()
        self.codesTabPage = CodesTabPage(self)
        self.codesTabPage.hide()
        titleHeight = 0.61
        self.title = DirectLabel(parent=self, relief=None, text=TTLocalizer.OptionsPageTitle, text_scale=0.12, pos=(0, 0, titleHeight))
        normalColor = (1, 1, 1, 1)
        clickColor = (0.8, 0.8, 0, 1)
        rolloverColor = (0.15, 0.82, 1.0, 1)
        diabledColor = (1.0, 0.98, 0.15, 1)
        gui = loader.loadModel('phase_3.5/models/gui/fishingBook')
        self.optionsTab = DirectButton(parent=self, relief=None, text=TTLocalizer.OptionsPageTitle, text_scale=TTLocalizer.OPoptionsTab, text_align=TextNode.ALeft, text_pos=(0.01, 0.0, 0.0), image=gui.find('**/tabs/polySurface1'), image_pos=(0.55, 1, -0.91), image_hpr=(0, 0, -90), image_scale=(0.033, 0.033, 0.035), image_color=normalColor, image1_color=clickColor, image2_color=rolloverColor, image3_color=diabledColor, text_fg=Vec4(0.2, 0.1, 0, 1), command=self.setMode, extraArgs=[PageMode.Options], pos=(-0.36, 0, 0.77))
        self.codesTab = DirectButton(parent=self, relief=None, text=TTLocalizer.OptionsPageCodesTab, text_scale=TTLocalizer.OPoptionsTab, text_align=TextNode.ALeft, text_pos=(-0.035, 0.0, 0.0), image=gui.find('**/tabs/polySurface2'), image_pos=(0.12, 1, -0.91), image_hpr=(0, 0, -90), image_scale=(0.033, 0.033, 0.035), image_color=normalColor, image1_color=clickColor, image2_color=rolloverColor, image3_color=diabledColor, text_fg=Vec4(0.2, 0.1, 0, 1), command=self.setMode, extraArgs=[PageMode.Codes], pos=(0.11, 0, 0.77))
        return

    def enter(self):
        self.setMode(PageMode.Options, updateAnyways=1)
        ShtikerPage.ShtikerPage.enter(self)

    def exit(self):
        self.optionsTabPage.exit()
        self.codesTabPage.exit()
        ShtikerPage.ShtikerPage.exit(self)

    def unload(self):
        self.optionsTabPage.unload()
        self.codesTabPage.unload()
        del self.title
        ShtikerPage.ShtikerPage.unload(self)

    def setMode(self, mode, updateAnyways = 0):
        messenger.send('wakeup')
        if not updateAnyways:
            if self.mode == mode:
                return
            else:
                self.mode = mode
        if mode == PageMode.Options:
            self.mode = PageMode.Options
            self.title['text'] = TTLocalizer.OptionsPageTitle
            self.optionsTab['state'] = DGG.DISABLED
            self.optionsTabPage.enter()
            self.codesTab['state'] = DGG.NORMAL
            self.codesTabPage.exit()
        elif mode == PageMode.Codes:
            self.mode = PageMode.Codes
            self.title['text'] = TTLocalizer.CdrPageTitle
            self.optionsTab['state'] = DGG.NORMAL
            self.optionsTabPage.exit()
            self.codesTab['state'] = DGG.DISABLED
            self.codesTabPage.enter()
        else:
            raise Exception('OptionsPage::setMode - Invalid Mode %s' % mode)


class OptionsTabPage(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('OptionsTabPage')
    DisplaySettingsTaskName = 'save-display-settings'
    ChangeDisplaySettings = ConfigVariableBool('change-display-settings', 1).value
    ChangeDisplayAPI = ConfigVariableBool('change-display-api', 0).value

    class _Layout:
        def __init__(self):
            self.topY = 0.38
            self.helpY = self.topY - 0.065
            self.rowHeight = 0.125
            # Controls start below the help paragraph.
            self.firstRowOffset = 0.17
            self.leftX = -0.72
            self.controlX = 0.35
            self.sliderX = self.controlX + 0.2
            self.valueX = self.controlX + 0.5

        def row(self, n):
            return self.topY - self.firstRowOffset - n * self.rowHeight

        def headerPos(self):
            return (self.leftX, 0, self.topY)

        def helpPos(self):
            return (self.leftX, 0, self.helpY)

        def labelPos(self, n, zOffset=0.0):
            return (self.leftX, 0, self.row(n) + zOffset)

        def controlPos(self, n, xOffset=0.0, zOffset=0.0):
            return (self.controlX + xOffset, 0, self.row(n) + zOffset)

        def sliderPos(self, n):
            return (self.sliderX, 0.0, self.row(n))

        def valuePos(self, n):
            return (self.valueX, 0.0, self.row(n))

    def __init__(self, parent = aspect2d):
        self._parent = parent
        self.currentSizeIndex = None
        DirectFrame.__init__(self, parent=self._parent, relief=None, pos=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0))
        self.load()
        return

    def destroy(self):
        self._parent = None
        DirectFrame.destroy(self)
        return

    def load(self):
        self.displaySettings = None
        self.displaySettingsChanged = 0
        self.displaySettingsSize = (None, None)
        self.displaySettingsFullscreen = None
        self.displaySettingsEmbedded = None
        self.displaySettingsApi = None
        self.displaySettingsApiChanged = 0
        self.subTabButtons = {}
        self.subPanels = {}
        self.subTabMode = OptionsSubTab.Audio
        self._preMuteMusic = None
        self._preMuteSfx = None
        guiButton = loader.loadModel('phase_3/models/gui/quit_button')
        gui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
        tabGui = loader.loadModel('phase_3.5/models/gui/fishingBook')
        layout = self._Layout()
        button_image_scale = (0.7, 1, 1)
        button_textpos = (0, -0.02)
        options_text_scale = 0.052
        self.speed_chat_scale = 0.055
        accentFg = Vec4(0.12, 0.35, 0.62, 1)
        helpFg = Vec4(0.28, 0.22, 0.14, 0.85)
        normalColor = (1, 1, 1, 1)
        clickColor = (0.8, 0.8, 0, 1)
        rolloverColor = (0.15, 0.82, 1.0, 1)
        disabledColor = (1.0, 0.98, 0.15, 1)
        # Sub-tab art (background) alignment. The tab geometry is rotated -90,
        # so we keep it centered and *higher* to avoid overlapping content.
        subTabImagePos = (0.0, 1, -0.62)
        subTabImageScale = (0.022, 0.022, 0.024)
        subTabZ = 0.62
        tabGeomCycle = ('**/tabs/polySurface1', '**/tabs/polySurface2')
        tabSpecs = (
            (OptionsSubTab.Audio,       TTLocalizer.OptionsPageSubTabAudio,       -0.50),
            (OptionsSubTab.Social,      TTLocalizer.OptionsPageSubTabSocial,       -0.30),
            (OptionsSubTab.DisplayChat, TTLocalizer.OptionsPageSubTabDisplayChat,  -0.10),
            (OptionsSubTab.Advanced,    TTLocalizer.OptionsPageSubTabAdvanced,      0.10),
            (OptionsSubTab.Gameplay,    TTLocalizer.OptionsPageSubTabGameplay,      0.30),
            (OptionsSubTab.Lighting,    TTLocalizer.OptionsPageSubTabLighting,      0.50),
        )
        for idx, (mode, tabLabel, xpos) in enumerate(tabSpecs):
            geom = tabGeomCycle[idx % len(tabGeomCycle)]
            btn = DirectButton(
                parent=self,
                relief=None,
                text=tabLabel,
                text_scale=TTLocalizer.OPsubTab,
                text_align=TextNode.ACenter,
                text_pos=(0.0, -0.015, 0.0),
                image=tabGui.find(geom),
                image_pos=subTabImagePos,
                image_hpr=(0, 0, -90),
                image_scale=subTabImageScale,
                image_color=normalColor,
                image1_color=clickColor,
                image2_color=rolloverColor,
                image3_color=disabledColor,
                text_fg=Vec4(0.2, 0.1, 0, 1),
                command=self.setSubTab,
                extraArgs=[mode],
                pos=(xpos, 0, subTabZ),
            )
            self.subTabButtons[mode] = btn
        tabGui.removeNode()
        pAudio = DirectFrame(parent=self, relief=None, pos=(0, 0, -0.015))
        pSocial = DirectFrame(parent=self, relief=None, pos=(0, 0, -0.015))
        pDisplay = DirectFrame(parent=self, relief=None, pos=(0, 0, -0.015))
        pAdvanced = DirectFrame(parent=self, relief=None, pos=(0, 0, -0.015))
        pGameplay = DirectFrame(parent=self, relief=None, pos=(0, 0, -0.015))
        pLighting = DirectFrame(parent=self, relief=None, pos=(0, 0, -0.015))
        self.subPanels = {
            OptionsSubTab.Audio:       pAudio,
            OptionsSubTab.Social:      pSocial,
            OptionsSubTab.DisplayChat: pDisplay,
            OptionsSubTab.Advanced:    pAdvanced,
            OptionsSubTab.Gameplay:    pGameplay,
            OptionsSubTab.Lighting:    pLighting,
        }
        topY = layout.topY
        helpY = layout.helpY

        DirectLabel(
            parent=pAudio,
            relief=None,
            text=TTLocalizer.OptionsPageSectionAudioTitle,
            text_align=TextNode.ALeft,
            text_scale=TTLocalizer.OPsectionTitle,
            text_fg=accentFg,
            pos=layout.headerPos(),
        )
        DirectLabel(
            parent=pAudio,
            relief=None,
            text=TTLocalizer.OptionsPageSectionAudioHelp,
            text_align=TextNode.ALeft,
            text_scale=TTLocalizer.OPsubTabHelp,
            text_fg=helpFg,
            text_wordwrap=22,
            pos=layout.helpPos(),
        )
        self.MuteAll_Button = DirectButton(
            parent=pAudio,
            relief=None,
            image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')),
            image_scale=(0.52, 1, 0.95),
            text=TTLocalizer.OptionsPageMuteAll,
            text_scale=options_text_scale * 0.9,
            text_pos=button_textpos,
            pos=layout.controlPos(0, xOffset=-0.16),
            command=self.__doMuteAllAudio,
        )
        self.RestoreAudio_Button = DirectButton(
            parent=pAudio,
            relief=None,
            image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')),
            image_scale=(0.52, 1, 0.95),
            text=TTLocalizer.OptionsPageRestoreAudio,
            text_scale=options_text_scale * 0.9,
            text_pos=button_textpos,
            pos=layout.controlPos(0, xOffset=0.16),
            command=self.__doRestoreAudio,
        )
        self.Music_Label = DirectLabel(parent=pAudio, relief=None, text=TTLocalizer.OptionsPageMusicVolumeLabel, text_align=TextNode.ALeft, text_scale=options_text_scale, pos=layout.labelPos(1))
        self.Music_toggleSlider = DirectSlider(parent=pAudio, relief=DGG.FLAT, range=(0, 100), value=100, pageSize=5, pos=layout.sliderPos(1), scale=0.5, command=self.__setMusicVolume)
        self.Music_volumeLabel = DirectLabel(parent=pAudio, relief=None, text='100%', text_scale=options_text_scale * 0.8, pos=layout.valuePos(1))
        self.SoundFX_Label = DirectLabel(parent=pAudio, relief=None, text=TTLocalizer.OptionsPageSFXVolumeLabel, text_align=TextNode.ALeft, text_scale=options_text_scale, text_wordwrap=16, pos=layout.labelPos(2))
        self.SoundFX_toggleSlider = DirectSlider(parent=pAudio, relief=DGG.FLAT, range=(0, 100), value=100, pageSize=5, pos=layout.sliderPos(2), scale=0.5, command=self.__setSfxVolume)
        self.SoundFX_volumeLabel = DirectLabel(parent=pAudio, relief=None, text='100%', text_scale=options_text_scale * 0.8, pos=layout.valuePos(2))
        self.ToonChatSounds_Label = DirectLabel(parent=pAudio, relief=None, text='', text_align=TextNode.ALeft, text_scale=options_text_scale, text_wordwrap=15, pos=layout.labelPos(3, zOffset=0.02))
        self.ToonChatSounds_Label.setScale(0.9)
        self.ToonChatSounds_toggleButton = DirectButton(
            parent=pAudio,
            relief=None,
            image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR'), guiButton.find('**/QuitBtn_UP')),
            image3_color=Vec4(0.5, 0.5, 0.5, 0.5),
            image_scale=button_image_scale,
            text='',
            text3_fg=(0.5, 0.5, 0.5, 0.75),
            text_scale=options_text_scale,
            text_pos=button_textpos,
            pos=layout.controlPos(3),
            command=self.__doToggleToonChatSounds,
        )
        self.ToonChatSounds_toggleButton.setScale(0.8)
        DirectLabel(
            parent=pSocial,
            relief=None,
            text=TTLocalizer.OptionsPageSectionSocialTitle,
            text_align=TextNode.ALeft,
            text_scale=TTLocalizer.OPsectionTitle,
            text_fg=accentFg,
            pos=layout.headerPos(),
        )
        DirectLabel(
            parent=pSocial,
            relief=None,
            text=TTLocalizer.OptionsPageSectionSocialHelp,
            text_align=TextNode.ALeft,
            text_scale=TTLocalizer.OPsubTabHelp,
            text_fg=helpFg,
            text_wordwrap=22,
            pos=layout.helpPos(),
        )
        self.Friends_Label = DirectLabel(parent=pSocial, relief=None, text='', text_align=TextNode.ALeft, text_scale=options_text_scale, text_wordwrap=18, pos=layout.labelPos(0))
        self.Friends_toggleButton = DirectButton(parent=pSocial, relief=None, image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')), image_scale=button_image_scale, text='', text_scale=options_text_scale, text_pos=button_textpos, pos=layout.controlPos(0), command=self.__doToggleAcceptFriends)
        self.Whispers_Label = DirectLabel(parent=pSocial, relief=None, text='', text_align=TextNode.ALeft, text_scale=options_text_scale, text_wordwrap=18, pos=layout.labelPos(1))
        self.Whispers_toggleButton = DirectButton(parent=pSocial, relief=None, image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')), image_scale=button_image_scale, text='', text_scale=options_text_scale, text_pos=button_textpos, pos=layout.controlPos(1), command=self.__doToggleAcceptWhispers)
        self.TKeyOnlyChat_Label = DirectLabel(parent=pSocial, relief=None, text='', text_align=TextNode.ALeft, text_scale=options_text_scale, text_wordwrap=18, pos=layout.labelPos(2))
        self.TKeyOnlyChat_toggleButton = DirectButton(parent=pSocial, relief=None, image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')), image_scale=button_image_scale, text='', text_scale=options_text_scale, text_pos=button_textpos, pos=layout.controlPos(2), command=self.__doToggleTKeyOnlyChat)
        DirectLabel(
            parent=pDisplay,
            relief=None,
            text=TTLocalizer.OptionsPageSectionDisplayTitle,
            text_align=TextNode.ALeft,
            text_scale=TTLocalizer.OPsectionTitle,
            text_fg=accentFg,
            pos=layout.headerPos(),
        )
        DirectLabel(
            parent=pDisplay,
            relief=None,
            text=TTLocalizer.OptionsPageSectionDisplayHelp,
            text_align=TextNode.ALeft,
            text_scale=TTLocalizer.OPsubTabHelp,
            text_fg=helpFg,
            text_wordwrap=22,
            pos=layout.helpPos(),
        )
        self.Particles_Label = DirectLabel(parent=pDisplay, relief=None, text='', text_align=TextNode.ALeft, text_scale=options_text_scale, text_wordwrap=18, pos=layout.labelPos(1))
        self.Particles_toggleButton = DirectButton(parent=pDisplay, relief=None, image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')), image_scale=button_image_scale, text='', text_scale=options_text_scale, text_pos=button_textpos, pos=layout.controlPos(1), command=self.__doToggleParticles)
        self.DynamicShadows_Label = DirectLabel(parent=pDisplay, relief=None, text='', text_align=TextNode.ALeft, text_scale=options_text_scale, text_wordwrap=18, pos=layout.labelPos(2))
        self.DynamicShadows_toggleButton = DirectButton(parent=pDisplay, relief=None, image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')), image_scale=button_image_scale, text='', text_scale=options_text_scale, text_pos=button_textpos, pos=layout.controlPos(2), command=self.__doToggleDynamicShadows)
        self.DisplaySettings_Label = DirectLabel(parent=pDisplay, relief=None, text='', text_align=TextNode.ALeft, text_scale=options_text_scale, text_wordwrap=26, pos=layout.labelPos(3))
        self.DisplaySettingsButton = DirectButton(parent=pDisplay, relief=None, image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')), image3_color=Vec4(0.5, 0.5, 0.5, 0.5), image_scale=button_image_scale, text=TTLocalizer.OptionsPageChange, text3_fg=(0.5, 0.5, 0.5, 0.75), text_scale=options_text_scale, text_pos=button_textpos, pos=layout.controlPos(4), command=self.__doDisplaySettings)
        self.SpeedChatStyle_Label = DirectLabel(parent=pDisplay, relief=None, text=TTLocalizer.OptionsPageSpeedChatStyleLabel, text_align=TextNode.ALeft, text_scale=options_text_scale, text_wordwrap=12, pos=layout.labelPos(5, zOffset=0.04))
        scY = layout.row(6) + 0.02
        self.speedChatStyleLeftArrow = DirectButton(parent=pDisplay, relief=None, image=(gui.find('**/Horiz_Arrow_UP'), gui.find('**/Horiz_Arrow_DN'), gui.find('**/Horiz_Arrow_Rllvr'), gui.find('**/Horiz_Arrow_UP')), image3_color=Vec4(1, 1, 1, 0.5), scale=(-1.0, 1.0, 1.0), pos=(0.25, 0, scY), command=self.__doSpeedChatStyleLeft)
        self.speedChatStyleRightArrow = DirectButton(parent=pDisplay, relief=None, image=(gui.find('**/Horiz_Arrow_UP'), gui.find('**/Horiz_Arrow_DN'), gui.find('**/Horiz_Arrow_Rllvr'), gui.find('**/Horiz_Arrow_UP')), image3_color=Vec4(1, 1, 1, 0.5), pos=(0.65, 0, scY), command=self.__doSpeedChatStyleRight)
        self.speedChatStyleText = SpeedChat.SpeedChat(name='OptionsPageStyleText', structure=[2000], backgroundModelName='phase_3/models/gui/ChatPanel', guiModelName='phase_3.5/models/gui/speedChatGui')
        self.speedChatStyleText.setScale(self.speed_chat_scale)
        self.speedChatStyleText.setPos(0.37, 0, scY + 0.03)
        self.speedChatStyleText.reparentTo(pDisplay, DGG.FOREGROUND_SORT_INDEX)
        DirectLabel(
            parent=pGameplay,
            relief=None,
            text=TTLocalizer.OptionsPageSectionGameplayTitle,
            text_align=TextNode.ALeft,
            text_scale=TTLocalizer.OPsectionTitle,
            text_fg=accentFg,
            pos=layout.headerPos(),
        )
        DirectLabel(
            parent=pGameplay,
            relief=None,
            text=TTLocalizer.OptionsPageSectionGameplayHelp,
            text_align=TextNode.ALeft,
            text_scale=TTLocalizer.OPsubTabHelp,
            text_fg=helpFg,
            text_wordwrap=22,
            pos=layout.helpPos(),
        )
        self.SkipBattleMovies_Label = DirectLabel(parent=pGameplay, relief=None, text='', text_align=TextNode.ALeft, text_scale=options_text_scale, text_wordwrap=20, pos=layout.labelPos(0))
        self.SkipBattleMovies_toggleButton = DirectButton(parent=pGameplay, relief=None, image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')), image_scale=button_image_scale, text='', text_scale=options_text_scale, text_pos=button_textpos, pos=layout.controlPos(0), command=self.__doToggleSkipBattleMovies)
        self.WalkSpeed_Label = DirectLabel(parent=pGameplay, relief=None, text=TTLocalizer.OptionsPageWalkSpeedLabel, text_align=TextNode.ALeft, text_scale=options_text_scale, text_wordwrap=16, pos=layout.labelPos(1))
        self.WalkSpeed_Slider = DirectSlider(parent=pGameplay, relief=DGG.FLAT, range=(75, 125), value=100, pageSize=5, pos=layout.sliderPos(1), scale=0.5, command=self.__setWalkSpeedMult)
        self.WalkSpeed_valueLabel = DirectLabel(parent=pGameplay, relief=None, text='100%', text_scale=options_text_scale * 0.8, pos=layout.valuePos(1))
        self.CameraDistance_Label = DirectLabel(parent=pGameplay, relief=None, text=TTLocalizer.OptionsPageCameraDistanceLabel, text_align=TextNode.ALeft, text_scale=options_text_scale, text_wordwrap=16, pos=layout.labelPos(2))
        self.CameraDistance_Slider = DirectSlider(parent=pGameplay, relief=DGG.FLAT, range=(4, 25), value=14, pageSize=1, pos=layout.sliderPos(2), scale=0.5, command=self.__setCameraDistance)
        self.CameraDistance_valueLabel = DirectLabel(parent=pGameplay, relief=None, text='14', text_scale=options_text_scale * 0.8, pos=layout.valuePos(2))
        self.CameraYInvert_Label = DirectLabel(parent=pGameplay, relief=None, text='', text_align=TextNode.ALeft, text_scale=options_text_scale, text_wordwrap=20, pos=layout.labelPos(3))
        self.CameraYInvert_toggleButton = DirectButton(parent=pGameplay, relief=None, image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')), image_scale=button_image_scale, text='', text_scale=options_text_scale, text_pos=button_textpos, pos=layout.controlPos(3), command=self.__doToggleCameraYInvert)
        DirectLabel(
            parent=pAdvanced,
            relief=None,
            text=TTLocalizer.OptionsPageSectionAdvancedTitle,
            text_align=TextNode.ALeft,
            text_scale=TTLocalizer.OPsectionTitle,
            text_fg=accentFg,
            pos=layout.headerPos(),
        )
        DirectLabel(
            parent=pAdvanced,
            relief=None,
            text=TTLocalizer.OptionsPageSectionAdvancedHelp,
            text_align=TextNode.ALeft,
            text_scale=TTLocalizer.OPsubTabHelp,
            text_fg=helpFg,
            text_wordwrap=22,
            pos=layout.helpPos(),
        )
        self.ShowFPS_Label = DirectLabel(parent=pAdvanced, relief=None, text='', text_align=TextNode.ALeft, text_scale=options_text_scale, text_wordwrap=16, pos=layout.labelPos(0))
        self.ShowFPS_toggleButton = DirectButton(parent=pAdvanced, relief=None, image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')), image_scale=button_image_scale, text='', text_scale=options_text_scale, text_pos=button_textpos, pos=layout.controlPos(0), command=self.__doToggleShowFPS)
        self.MouseSensitivity_Label = DirectLabel(parent=pAdvanced, relief=None, text=TTLocalizer.OptionsPageMouseSensitivityLabel, text_align=TextNode.ALeft, text_scale=options_text_scale, text_wordwrap=15, pos=layout.labelPos(1))
        self.MouseSensitivity_Slider = DirectSlider(parent=pAdvanced, relief=DGG.FLAT, range=(0.5, 2.0), value=1.0, pageSize=0.1, pos=layout.sliderPos(1), scale=0.5, command=self.__setMouseSensitivity)
        self.MouseSensitivity_valueLabel = DirectLabel(parent=pAdvanced, relief=None, text='1.0x', text_scale=options_text_scale * 0.8, pos=layout.valuePos(1))
        self.CameraFOV_Label = DirectLabel(parent=pAdvanced, relief=None, text=TTLocalizer.OptionsPageCameraFovLabel, text_align=TextNode.ALeft, text_scale=options_text_scale, text_wordwrap=15, pos=layout.labelPos(2))
        self.CameraFOV_Slider = DirectSlider(parent=pAdvanced, relief=DGG.FLAT, range=(40, 90), value=ToontownGlobals.DefaultCameraFov, pageSize=1, pos=layout.sliderPos(2), scale=0.5, command=self.__setCameraFOV)
        self.CameraFOV_valueLabel = DirectLabel(parent=pAdvanced, relief=None, text='%s°' % ToontownGlobals.DefaultCameraFov, text_scale=options_text_scale * 0.8, pos=layout.valuePos(2))
        self.SmoothAnimations_Label = DirectLabel(parent=pAdvanced, relief=None, text='', text_align=TextNode.ALeft, text_scale=options_text_scale, text_wordwrap=16, pos=layout.labelPos(3))
        self.SmoothAnimations_toggleButton = DirectButton(parent=pAdvanced, relief=None, image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')), image_scale=button_image_scale, text='', text_scale=options_text_scale, text_pos=button_textpos, pos=layout.controlPos(3), command=self.__doToggleSmoothAnimations)
        self.ShowNametags_Label = DirectLabel(parent=pAdvanced, relief=None, text='', text_align=TextNode.ALeft, text_scale=options_text_scale, text_wordwrap=16, pos=layout.labelPos(4))
        self.ShowNametags_toggleButton = DirectButton(parent=pAdvanced, relief=None, image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')), image_scale=button_image_scale, text='', text_scale=options_text_scale, text_pos=button_textpos, pos=layout.controlPos(4), command=self.__doToggleShowNametags)
        self.Controls_Label = DirectLabel(parent=pAdvanced, relief=None, text=TTLocalizer.OptionsPageControlsHint, text_align=TextNode.ALeft, text_scale=options_text_scale * 0.78, text_fg=helpFg, text_wordwrap=28, pos=layout.labelPos(5, zOffset=-0.02))

        # ── Lighting panel ────────────────────────────────────────────────
        DirectLabel(
            parent=pLighting,
            relief=None,
            text=TTLocalizer.OptionsPageSectionLightingTitle,
            text_align=TextNode.ALeft,
            text_scale=TTLocalizer.OPsectionTitle,
            text_fg=accentFg,
            pos=layout.headerPos(),
        )
        DirectLabel(
            parent=pLighting,
            relief=None,
            text=TTLocalizer.OptionsPageSectionLightingHelp,
            text_align=TextNode.ALeft,
            text_scale=TTLocalizer.OPsubTabHelp,
            text_fg=helpFg,
            text_wordwrap=22,
            pos=layout.helpPos(),
        )
        self.AdvancedLighting_Label = DirectLabel(
            parent=pLighting, relief=None, text='',
            text_align=TextNode.ALeft, text_scale=options_text_scale,
            text_wordwrap=18, pos=layout.labelPos(0),
        )
        self.AdvancedLighting_toggleButton = DirectButton(
            parent=pLighting, relief=None,
            image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')),
            image_scale=button_image_scale, text='', text_scale=options_text_scale,
            text_pos=button_textpos, pos=layout.controlPos(0),
            command=self.__doToggleAdvancedLighting,
        )
        self.GodRays_Label = DirectLabel(
            parent=pLighting, relief=None, text='',
            text_align=TextNode.ALeft, text_scale=options_text_scale,
            text_wordwrap=18, pos=layout.labelPos(1),
        )
        self.GodRays_toggleButton = DirectButton(
            parent=pLighting, relief=None,
            image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')),
            image_scale=button_image_scale, text='', text_scale=options_text_scale,
            text_pos=button_textpos, pos=layout.controlPos(1),
            command=self.__doToggleGodRays,
        )
        self.LightingFog_Label = DirectLabel(
            parent=pLighting, relief=None, text='',
            text_align=TextNode.ALeft, text_scale=options_text_scale,
            text_wordwrap=18, pos=layout.labelPos(2),
        )
        self.LightingFog_toggleButton = DirectButton(
            parent=pLighting, relief=None,
            image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')),
            image_scale=button_image_scale, text='', text_scale=options_text_scale,
            text_pos=button_textpos, pos=layout.controlPos(2),
            command=self.__doToggleLightingFog,
        )
        self.LightingIntensity_Label = DirectLabel(
            parent=pLighting, relief=None,
            text=TTLocalizer.OptionsPageLightingIntensityLabel,
            text_align=TextNode.ALeft, text_scale=options_text_scale,
            text_wordwrap=16, pos=layout.labelPos(3),
        )
        self.LightingIntensity_Slider = DirectSlider(
            parent=pLighting, relief=DGG.FLAT,
            range=(0.4, 1.8), value=1.0, pageSize=0.1,
            pos=layout.sliderPos(3), scale=0.5,
            command=self.__setLightingIntensity,
        )
        self.LightingIntensity_valueLabel = DirectLabel(
            parent=pLighting, relief=None, text='1.0x',
            text_scale=options_text_scale * 0.8, pos=layout.valuePos(3),
        )
        self.ColorTemp_Label = DirectLabel(
            parent=pLighting, relief=None,
            text=TTLocalizer.OptionsPageColorTempLabel,
            text_align=TextNode.ALeft, text_scale=options_text_scale,
            text_wordwrap=16, pos=layout.labelPos(4),
        )
        self.ColorTemp_Slider = DirectSlider(
            parent=pLighting, relief=DGG.FLAT,
            range=(-1.0, 1.0), value=0.0, pageSize=0.1,
            pos=layout.sliderPos(4), scale=0.5,
            command=self.__setColorTemp,
        )
        self.ColorTemp_valueLabel = DirectLabel(
            parent=pLighting, relief=None, text='Neutral',
            text_scale=options_text_scale * 0.8, pos=layout.valuePos(4),
        )

        # Row 5 – Tonemapping
        self.Tonemap_Label = DirectLabel(
            parent=pLighting, relief=None, text='',
            text_align=TextNode.ALeft, text_scale=options_text_scale,
            text_wordwrap=18, pos=layout.labelPos(5),
        )
        self.Tonemap_toggleButton = DirectButton(
            parent=pLighting, relief=None,
            image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')),
            image_scale=button_image_scale, text='', text_scale=options_text_scale,
            text_pos=button_textpos, pos=layout.controlPos(5),
            command=self.__doToggleTonemap,
        )

        # Row 6 – Day / Night Cycle
        self.DayNight_Label = DirectLabel(
            parent=pLighting, relief=None, text='',
            text_align=TextNode.ALeft, text_scale=options_text_scale,
            text_wordwrap=18, pos=layout.labelPos(6),
        )
        self.DayNight_toggleButton = DirectButton(
            parent=pLighting, relief=None,
            image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')),
            image_scale=button_image_scale, text='', text_scale=options_text_scale,
            text_pos=button_textpos, pos=layout.controlPos(6),
            command=self.__doToggleDayNight,
        )

        # Row 7 – Procedural Sky
        self.ProceduralSky_Label = DirectLabel(
            parent=pLighting, relief=None, text='',
            text_align=TextNode.ALeft, text_scale=options_text_scale,
            text_wordwrap=18, pos=layout.labelPos(7),
        )
        self.ProceduralSky_toggleButton = DirectButton(
            parent=pLighting, relief=None,
            image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')),
            image_scale=button_image_scale, text='', text_scale=options_text_scale,
            text_pos=button_textpos, pos=layout.controlPos(7),
            command=self.__doToggleProceduralSky,
        )

        # Row 8 – Bloom
        self.Bloom_Label = DirectLabel(
            parent=pLighting, relief=None, text='',
            text_align=TextNode.ALeft, text_scale=options_text_scale,
            text_wordwrap=18, pos=layout.labelPos(8),
        )
        self.Bloom_toggleButton = DirectButton(
            parent=pLighting, relief=None,
            image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')),
            image_scale=button_image_scale, text='', text_scale=options_text_scale,
            text_pos=button_textpos, pos=layout.controlPos(8),
            command=self.__doToggleBloom,
        )

        # Row 9 – Water Reflections
        self.WaterRefl_Label = DirectLabel(
            parent=pLighting, relief=None, text='',
            text_align=TextNode.ALeft, text_scale=options_text_scale,
            text_wordwrap=18, pos=layout.labelPos(9),
        )
        self.WaterRefl_toggleButton = DirectButton(
            parent=pLighting, relief=None,
            image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')),
            image_scale=button_image_scale, text='', text_scale=options_text_scale,
            text_pos=button_textpos, pos=layout.controlPos(9),
            command=self.__doToggleWaterReflections,
        )

        # Row 10 – Shadow Quality
        self.ShadowQuality_Label = DirectLabel(
            parent=pLighting, relief=None,
            text=TTLocalizer.OptionsPageShadowQualityLabel,
            text_align=TextNode.ALeft, text_scale=options_text_scale,
            text_wordwrap=16, pos=layout.labelPos(10),
        )
        self.ShadowQuality_valueLabel = DirectLabel(
            parent=pLighting, relief=None, text='High',
            text_scale=options_text_scale * 0.8, pos=layout.valuePos(10),
        )
        self.ShadowQuality_cycleButton = DirectButton(
            parent=pLighting, relief=None,
            image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')),
            image_scale=button_image_scale, text=TTLocalizer.OptionsPageCycleButton,
            text_scale=options_text_scale, text_pos=button_textpos,
            pos=layout.controlPos(10),
            command=self.__cycleShadowQuality,
        )

        # Row 11 – Fog Density
        self.FogDensity_Label = DirectLabel(
            parent=pLighting, relief=None,
            text=TTLocalizer.OptionsPageFogDensityLabel,
            text_align=TextNode.ALeft, text_scale=options_text_scale,
            text_wordwrap=16, pos=layout.labelPos(11),
        )
        self.FogDensity_Slider = DirectSlider(
            parent=pLighting, relief=DGG.FLAT,
            range=(0.2, 2.5), value=1.0, pageSize=0.1,
            pos=layout.sliderPos(11), scale=0.5,
            command=self.__setFogDensity,
        )
        self.FogDensity_valueLabel = DirectLabel(
            parent=pLighting, relief=None, text='1.0x',
            text_scale=options_text_scale * 0.8, pos=layout.valuePos(11),
        )

        # Row 12 – Vignette
        self.Vignette_Label = DirectLabel(
            parent=pLighting, relief=None, text='',
            text_align=TextNode.ALeft, text_scale=options_text_scale,
            text_wordwrap=18, pos=layout.labelPos(12),
        )
        self.Vignette_toggleButton = DirectButton(
            parent=pLighting, relief=None,
            image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')),
            image_scale=button_image_scale, text='', text_scale=options_text_scale,
            text_pos=button_textpos, pos=layout.controlPos(12),
            command=self.__doToggleVignette,
        )

        # Row 13 – Day/Night Speed
        self.DayNightSpeed_Label = DirectLabel(
            parent=pLighting, relief=None,
            text=TTLocalizer.OptionsPageDayNightSpeedLabel,
            text_align=TextNode.ALeft, text_scale=options_text_scale,
            text_wordwrap=16, pos=layout.labelPos(13),
        )
        self.DayNightSpeed_Slider = DirectSlider(
            parent=pLighting, relief=DGG.FLAT,
            range=(0.1, 5.0), value=1.0, pageSize=0.1,
            pos=layout.sliderPos(13), scale=0.5,
            command=self.__setDayNightSpeed,
        )
        self.DayNightSpeed_valueLabel = DirectLabel(
            parent=pLighting, relief=None, text='1.0x',
            text_scale=options_text_scale * 0.8, pos=layout.valuePos(13),
        )

        self.exitButton = DirectButton(parent=self, relief=None, image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')), image_scale=1.15, text=TTLocalizer.OptionsPageExitToontown, text_scale=options_text_scale, text_pos=button_textpos, textMayChange=0, pos=(0.45, 0, -0.62), command=self.__handleExitShowWithConfirm)
        guiButton.removeNode()
        gui.removeNode()
        for panel in self.subPanels.values():
            panel.hide()
        return

    def setSubTab(self, mode, force = 0):
        messenger.send('wakeup')
        if not force and self.subTabMode == mode:
            return
        self.subTabMode = mode
        base.settings.updateSetting('options-page-subtab', int(mode))
        self.settingsChanged = 1
        for m, panel in self.subPanels.items():
            if m == mode:
                panel.show()
            else:
                panel.hide()
        for m, btn in self.subTabButtons.items():
            btn['state'] = DGG.DISABLED if m == mode else DGG.NORMAL

    def __doMuteAllAudio(self):
        messenger.send('wakeup')
        self._preMuteMusic = int(self.Music_toggleSlider['value'])
        self._preMuteSfx = int(self.SoundFX_toggleSlider['value'])
        self.Music_toggleSlider['value'] = 0
        self.SoundFX_toggleSlider['value'] = 0
        self.__setMusicVolume()
        self.__setSfxVolume()

    def __doRestoreAudio(self):
        messenger.send('wakeup')
        m = self._preMuteMusic
        s = self._preMuteSfx
        if m is None or s is None:
            self.__setMusicSlider()
            self.__setSoundFXSlider()
            return
        self.Music_toggleSlider['value'] = m
        self.SoundFX_toggleSlider['value'] = s
        self.__setMusicVolume()
        self.__setSfxVolume()

    def enter(self):
        self.show()
        taskMgr.remove(self.DisplaySettingsTaskName)
        raw = base.settings.getSetting('options-page-subtab', int(OptionsSubTab.Audio))
        try:
            tab = OptionsSubTab(int(raw))
        except (ValueError, TypeError):
            tab = OptionsSubTab.Audio
        if tab not in self.subPanels:
            tab = OptionsSubTab.Audio
        self.setSubTab(tab, force=1)
        self.settingsChanged = 0
        self.__setMusicSlider()
        self.__setSoundFXSlider()
        self.__setAcceptFriendsButton()
        self.__setAcceptWhispersButton()
        self.__setDisplaySettings()
        self.__setToonChatSoundsButton()
        self.__setTKeyOnlyChatButton()
        self.__setShowFPSButton()
        self.__setMouseSensitivitySlider()
        self.__setCameraFOVSlider()
        self.__setSmoothAnimationsButton()
        self.__setShowNametagsButton()
        self.__setParticlesButton()
        self.__setDynamicShadowsButton()
        self.__setSkipBattleMoviesButton()
        self.__setWalkSpeedSlider()
        self.__setCameraDistanceSlider()
        self.__setCameraYInvertButton()
        self.__setAdvancedLightingButton()
        self.__setGodRaysButton()
        self.__setLightingFogButton()
        self.__setLightingIntensitySlider()
        self.__setColorTempSlider()
        self.__setTonemapButton()
        self.__setDayNightButton()
        self.__setProceduralSkyButton()
        self.__setBloomButton()
        self.__setWaterReflectionsButton()
        self.__setShadowQualityLabel()
        self.__setFogDensitySlider()
        self.__setVignetteButton()
        self.__setDayNightSpeedSlider()
        self.speedChatStyleText.enter()
        self.speedChatStyleIndex = base.localAvatar.getSpeedChatStyleIndex()
        self.updateSpeedChatStyle()
        if self._parent.book.safeMode:
            self.exitButton.hide()
        else:
            self.exitButton.show()

    def exit(self):
        self.ignore('confirmDone')
        self.hide()
        if self.displaySettingsChanged:
            taskMgr.remove(self.DisplaySettingsTaskName)
            self.writeDisplaySettings()
        elif self.settingsChanged != 0:
            base.settings.writeSettings()
        self.speedChatStyleText.exit()

    def unload(self):
        self.writeDisplaySettings()
        taskMgr.remove(self.DisplaySettingsTaskName)
        if self.displaySettings != None:
            self.ignore(self.displaySettings.doneEvent)
            self.displaySettings.unload()
        self.displaySettings = None
        for btn in list(self.subTabButtons.values()):
            btn.destroy()
        self.subTabButtons.clear()
        self.speedChatStyleText.exit()
        self.speedChatStyleText.destroy()
        del self.speedChatStyleText
        for panel in list(self.subPanels.values()):
            panel.destroy()
        self.subPanels.clear()
        self.exitButton.destroy()
        del self.exitButton
        self.currentSizeIndex = None
        return

    def __setMusicVolume(self):
        messenger.send('wakeup')
        volume = int(self.Music_toggleSlider['value'])
        self.Music_volumeLabel['text'] = '%d%%' % volume
        volumeFloat = volume / 100.0
        if volumeFloat == 0:
            base.enableMusic(0)
        else:
            if not base.musicActive:
                base.enableMusic(1)
            base.musicManager.setVolume(volumeFloat)
        base.settings.updateSetting('musicVolume', volume)
        base.settings.updateSetting('music', volume > 0)
        self.settingsChanged = 1

    def __setMusicSlider(self):
        volume = base.settings.getSetting('musicVolume', 100)
        self.Music_toggleSlider['value'] = volume
        self.Music_volumeLabel['text'] = '%d%%' % volume

    def __setSfxVolume(self):
        messenger.send('wakeup')
        volume = int(self.SoundFX_toggleSlider['value'])
        self.SoundFX_volumeLabel['text'] = '%d%%' % volume
        volumeFloat = volume / 100.0
        if volumeFloat == 0:
            base.enableSoundEffects(0)
        else:
            if not base.sfxActive:
                base.enableSoundEffects(1)
            for sfxManager in base.sfxManagerList:
                sfxManager.setVolume(volumeFloat)
        base.settings.updateSetting('sfxVolume', volume)
        base.settings.updateSetting('sfx', volume > 0)
        self.settingsChanged = 1

    def __setSoundFXSlider(self):
        volume = base.settings.getSetting('sfxVolume', 100)
        self.SoundFX_toggleSlider['value'] = volume
        self.SoundFX_volumeLabel['text'] = '%d%%' % volume

    def __doToggleToonChatSounds(self):
        messenger.send('wakeup')
        if base.toonChatSounds:
            base.toonChatSounds = 0
            base.settings.updateSetting('toon-chat-sounds', False)
        else:
            base.toonChatSounds = 1
            base.settings.updateSetting('toon-chat-sounds', True)
        self.settingsChanged = 1
        self.__setToonChatSoundsButton()


    def __setToonChatSoundsButton(self):
        if base.toonChatSounds:
            self.ToonChatSounds_Label['text'] = TTLocalizer.OptionsPageToonChatSoundsOnLabel
            self.ToonChatSounds_toggleButton['text'] = TTLocalizer.OptionsPageToggleOff
        else:
            self.ToonChatSounds_Label['text'] = TTLocalizer.OptionsPageToonChatSoundsOffLabel
            self.ToonChatSounds_toggleButton['text'] = TTLocalizer.OptionsPageToggleOn
        if base.sfxActive:
            self.ToonChatSounds_Label.setColorScale(1.0, 1.0, 1.0, 1.0)
            self.ToonChatSounds_toggleButton['state'] = DGG.NORMAL
        else:
            self.ToonChatSounds_Label.setColorScale(0.5, 0.5, 0.5, 0.5)
            self.ToonChatSounds_toggleButton['state'] = DGG.DISABLED

    def __doToggleAcceptFriends(self):
        messenger.send('wakeup')
        if base.localAvatar.acceptingNewFriends:
            base.localAvatar.acceptingNewFriends = 0
            base.settings.updateSetting('accepting-new-friends', False)
        else:
            base.localAvatar.acceptingNewFriends = 1
            base.settings.updateSetting('accepting-new-friends', True)
        self.settingsChanged = 1
        self.__setAcceptFriendsButton()

    def __doToggleAcceptWhispers(self):
        messenger.send('wakeup')
        if base.localAvatar.acceptingNonFriendWhispers:
            base.localAvatar.acceptingNonFriendWhispers = 0
            base.settings.updateSetting('accepting-non-friend-whispers', False)
        else:
            base.localAvatar.acceptingNonFriendWhispers = 1
            base.settings.updateSetting('accepting-non-friend-whispers', True)
        self.settingsChanged = 1
        self.__setAcceptWhispersButton()

    def __setAcceptFriendsButton(self):
        if base.localAvatar.acceptingNewFriends:
            self.Friends_Label['text'] = TTLocalizer.OptionsPageFriendsEnabledLabel
            self.Friends_toggleButton['text'] = TTLocalizer.OptionsPageToggleOff
        else:
            self.Friends_Label['text'] = TTLocalizer.OptionsPageFriendsDisabledLabel
            self.Friends_toggleButton['text'] = TTLocalizer.OptionsPageToggleOn

    def __setAcceptWhispersButton(self):
        if base.localAvatar.acceptingNonFriendWhispers:
            self.Whispers_Label['text'] = TTLocalizer.OptionsPageWhisperEnabledLabel
            self.Whispers_toggleButton['text'] = TTLocalizer.OptionsPageToggleOff
        else:
            self.Whispers_Label['text'] = TTLocalizer.OptionsPageWhisperDisabledLabel
            self.Whispers_toggleButton['text'] = TTLocalizer.OptionsPageToggleOn
    
    def __doToggleTKeyOnlyChat(self):
        tKeyOnly = base.settings.getSetting('tKeyOnlyChat', False)
        base.settings.updateSetting('tKeyOnlyChat', not tKeyOnly)
        self.settingsChanged = 1
        self.__setTKeyOnlyChatButton()
    
    def __setTKeyOnlyChatButton(self):
        if base.settings.getSetting('tKeyOnlyChat', False):
            self.TKeyOnlyChat_Label['text'] = TTLocalizer.OptionsPageTKeyOnlyOn
            self.TKeyOnlyChat_toggleButton['text'] = TTLocalizer.OptionsPageToggleOff
        else:
            self.TKeyOnlyChat_Label['text'] = TTLocalizer.OptionsPageTKeyOnlyOff
            self.TKeyOnlyChat_toggleButton['text'] = TTLocalizer.OptionsPageToggleOn

    def __doToggleShowFPS(self):
        messenger.send('wakeup')
        showFPS = base.settings.getSetting('show-fps', False)
        base.settings.updateSetting('show-fps', not showFPS)
        base.setFrameRateMeter(not showFPS)
        self.settingsChanged = 1
        self.__setShowFPSButton()

    def __setShowFPSButton(self):
        showFPS = base.settings.getSetting('show-fps', False)
        if showFPS:
            self.ShowFPS_Label['text'] = TTLocalizer.OptionsPageShowFpsOn
            self.ShowFPS_toggleButton['text'] = TTLocalizer.OptionsPageToggleOff
            base.setFrameRateMeter(True)
        else:
            self.ShowFPS_Label['text'] = TTLocalizer.OptionsPageShowFpsOff
            self.ShowFPS_toggleButton['text'] = TTLocalizer.OptionsPageToggleOn
            base.setFrameRateMeter(False)

    def __setMouseSensitivity(self):
        messenger.send('wakeup')
        sensitivity = round(self.MouseSensitivity_Slider['value'], 1)
        self.MouseSensitivity_valueLabel['text'] = '%.1fx' % sensitivity
        base.settings.updateSetting('mouse-sensitivity', sensitivity)
        if hasattr(base, 'applyMouseSensitivity'):
            base.applyMouseSensitivity(sensitivity)
        self.settingsChanged = 1

    def __setMouseSensitivitySlider(self):
        sensitivity = base.settings.getSetting('mouse-sensitivity', 1.0)
        self.MouseSensitivity_Slider['value'] = sensitivity
        self.MouseSensitivity_valueLabel['text'] = '%.1fx' % sensitivity
        if hasattr(base, 'applyMouseSensitivity'):
            base.applyMouseSensitivity(sensitivity)

    def __setCameraFOV(self):
        messenger.send('wakeup')
        fov = round(self.CameraFOV_Slider['value'], 1)
        self.CameraFOV_valueLabel['text'] = '%.1f°' % fov
        base.settings.updateSetting('camera-fov', fov)
        if hasattr(base, 'baseFov'):
            base.baseFov = fov
        if hasattr(base, 'updateFovForAspectRatio'):
            base.updateFovForAspectRatio()
        elif hasattr(base, 'camLens'):
            base.camLens.setFov(fov)
        if hasattr(base, 'localAvatar') and base.localAvatar:
            base.localAvatar.fov = fov
        self.settingsChanged = 1

    def __setCameraFOVSlider(self):
        fov = base.settings.getSetting('camera-fov', ToontownGlobals.DefaultCameraFov)
        self.CameraFOV_Slider['value'] = fov
        self.CameraFOV_valueLabel['text'] = '%.1f°' % fov
        if hasattr(base, 'baseFov'):
            base.baseFov = fov
        if hasattr(base, 'updateFovForAspectRatio'):
            base.updateFovForAspectRatio()
        elif hasattr(base, 'camLens'):
            base.camLens.setFov(fov)
        if hasattr(base, 'localAvatar') and base.localAvatar:
            base.localAvatar.fov = fov

    def __doToggleSmoothAnimations(self):
        messenger.send('wakeup')
        smoothAnims = base.settings.getSetting('smooth-animations', True)
        base.settings.updateSetting('smooth-animations', not smoothAnims)
        if hasattr(base, 'transitions') and base.transitions and hasattr(base.transitions, 'setUseBlend'):
            base.transitions.setUseBlend(not smoothAnims)
        self.settingsChanged = 1
        self.__setSmoothAnimationsButton()

    def __doToggleParticles(self):
        messenger.send('wakeup')
        on = base.settings.getSetting('particles-enabled', True)
        newVal = not on
        base.settings.updateSetting('particles-enabled', newVal)
        if newVal:
            base.enableParticles()
        else:
            base.disableParticles()
        self.settingsChanged = 1
        self.__setParticlesButton()

    def __setParticlesButton(self):
        cfg = base.config.GetBool('want-particles', True)
        on = base.settings.getSetting('particles-enabled', True)
        if cfg:
            if on:
                base.enableParticles()
            else:
                base.disableParticles()
        if on:
            self.Particles_Label['text'] = TTLocalizer.OptionsPageParticlesOn
            self.Particles_toggleButton['text'] = TTLocalizer.OptionsPageToggleOff
        else:
            self.Particles_Label['text'] = TTLocalizer.OptionsPageParticlesOff
            self.Particles_toggleButton['text'] = TTLocalizer.OptionsPageToggleOn
        if not cfg:
            self.Particles_Label['text'] = TTLocalizer.OptionsPageParticlesOff
            self.Particles_toggleButton['state'] = DGG.DISABLED
            self.Particles_Label.setColorScale(0.55, 0.55, 0.55, 1.0)
        else:
            self.Particles_toggleButton['state'] = DGG.NORMAL
            self.Particles_Label.setColorScale(1.0, 1.0, 1.0, 1.0)

    def __doToggleDynamicShadows(self):
        messenger.send('wakeup')
        on = base.settings.getSetting('dynamic-shadows', False)
        base.settings.updateSetting('dynamic-shadows', not on)
        base.wantDynamicShadows = 0 if on else 1
        self.settingsChanged = 1
        self.__setDynamicShadowsButton()

    def __setDynamicShadowsButton(self):
        on = base.settings.getSetting('dynamic-shadows', False)
        if on:
            self.DynamicShadows_Label['text'] = TTLocalizer.OptionsPageShadowsOn
            self.DynamicShadows_toggleButton['text'] = TTLocalizer.OptionsPageToggleOff
        else:
            self.DynamicShadows_Label['text'] = TTLocalizer.OptionsPageShadowsOff
            self.DynamicShadows_toggleButton['text'] = TTLocalizer.OptionsPageToggleOn
        base.wantDynamicShadows = 1 if on else 0

    def __doToggleSkipBattleMovies(self):
        messenger.send('wakeup')
        if base.config.GetBool('skip-battle-movies', False):
            return
        on = base.settings.getSetting('skip-battle-movies', False)
        newVal = not on
        base.settings.updateSetting('skip-battle-movies', newVal)
        ToontownBattleGlobals.SkipMovie = 1 if newVal else 0
        self.settingsChanged = 1
        self.__setSkipBattleMoviesButton()

    def __setSkipBattleMoviesButton(self):
        if base.config.GetBool('skip-battle-movies', False):
            ToontownBattleGlobals.SkipMovie = 1
            self.SkipBattleMovies_Label['text'] = TTLocalizer.OptionsPageSkipBattleMoviesForced
            self.SkipBattleMovies_toggleButton['text'] = TTLocalizer.OptionsPageToggleOff
            self.SkipBattleMovies_toggleButton['state'] = DGG.DISABLED
            self.SkipBattleMovies_Label.setColorScale(0.55, 0.55, 0.55, 1.0)
            return
        self.SkipBattleMovies_toggleButton['state'] = DGG.NORMAL
        self.SkipBattleMovies_Label.setColorScale(1.0, 1.0, 1.0, 1.0)
        on = base.settings.getSetting('skip-battle-movies', False)
        ToontownBattleGlobals.SkipMovie = 1 if on else 0
        if on:
            self.SkipBattleMovies_Label['text'] = TTLocalizer.OptionsPageSkipBattleMoviesOn
            self.SkipBattleMovies_toggleButton['text'] = TTLocalizer.OptionsPageToggleOff
        else:
            self.SkipBattleMovies_Label['text'] = TTLocalizer.OptionsPageSkipBattleMoviesOff
            self.SkipBattleMovies_toggleButton['text'] = TTLocalizer.OptionsPageToggleOn

    def __setWalkSpeedMult(self):
        messenger.send('wakeup')
        pct = int(self.WalkSpeed_Slider['value'])
        pct = max(75, min(125, pct))
        self.WalkSpeed_Slider['value'] = pct
        self.WalkSpeed_valueLabel['text'] = TTLocalizer.OptionsPageWalkSpeedValue % pct
        base.settings.updateSetting('walk-speed-mult', pct)
        if hasattr(base, 'localAvatar') and base.localAvatar:
            if base.localAvatar.avatarControlsEnabled:
                base.localAvatar.setWalkSpeedNormal()
        self.settingsChanged = 1

    def __setWalkSpeedSlider(self):
        try:
            pct = int(base.settings.getSetting('walk-speed-mult', 100))
        except (TypeError, ValueError):
            pct = 100
        pct = max(75, min(125, pct))
        self.WalkSpeed_Slider['value'] = pct
        self.WalkSpeed_valueLabel['text'] = TTLocalizer.OptionsPageWalkSpeedValue % pct
        if hasattr(base, 'localAvatar') and base.localAvatar:
            if base.localAvatar.avatarControlsEnabled:
                base.localAvatar.setWalkSpeedNormal()

    def __setCameraDistance(self):
        messenger.send('wakeup')
        dist = round(self.CameraDistance_Slider['value'])
        self.CameraDistance_Slider['value'] = dist
        self.CameraDistance_valueLabel['text'] = TTLocalizer.OptionsPageCameraDistanceValue % dist
        base.settings.updateSetting('cam-distance', float(dist))
        if hasattr(base, 'localAvatar') and base.localAvatar:
            cam = getattr(base.localAvatar, 'orbitalCamera', None)
            if cam and cam.isActive():
                cam.onSettingsChanged()
        self.settingsChanged = 1

    def __setCameraDistanceSlider(self):
        try:
            dist = float(base.settings.getSetting('cam-distance', 14.0))
        except (TypeError, ValueError):
            dist = 14.0
        dist = max(4.0, min(25.0, dist))
        self.CameraDistance_Slider['value'] = dist
        self.CameraDistance_valueLabel['text'] = TTLocalizer.OptionsPageCameraDistanceValue % dist

    def __doToggleCameraYInvert(self):
        messenger.send('wakeup')
        invertY = base.settings.getSetting('cam-invert-y', False)
        base.settings.updateSetting('cam-invert-y', not invertY)
        self.settingsChanged = 1
        self.__setCameraYInvertButton()

    def __setCameraYInvertButton(self):
        invertY = base.settings.getSetting('cam-invert-y', False)
        if invertY:
            self.CameraYInvert_Label['text'] = TTLocalizer.OptionsPageCameraYInvertOn
            self.CameraYInvert_toggleButton['text'] = TTLocalizer.OptionsPageToggleOff
        else:
            self.CameraYInvert_Label['text'] = TTLocalizer.OptionsPageCameraYInvertOff
            self.CameraYInvert_toggleButton['text'] = TTLocalizer.OptionsPageToggleOn

    def __setSmoothAnimationsButton(self):
        smoothAnims = base.settings.getSetting('smooth-animations', True)
        if smoothAnims:
            self.SmoothAnimations_Label['text'] = TTLocalizer.OptionsPageSmoothAnimsOn
            self.SmoothAnimations_toggleButton['text'] = TTLocalizer.OptionsPageToggleOff
        else:
            self.SmoothAnimations_Label['text'] = TTLocalizer.OptionsPageSmoothAnimsOff
            self.SmoothAnimations_toggleButton['text'] = TTLocalizer.OptionsPageToggleOn

    def __doToggleShowNametags(self):
        messenger.send('wakeup')
        showNametags = base.settings.getSetting('show-nametags', True)
        newShow = not showNametags
        base.settings.updateSetting('show-nametags', newShow)
        if hasattr(base, 'cr') and hasattr(base.cr, 'doFindAll'):
            avatars = base.cr.doFindAll('DistributedToon')
            for avatar in avatars:
                if hasattr(avatar, 'nametag3d'):
                    if newShow:
                        avatar.nametag3d.show()
                    else:
                        avatar.nametag3d.hide()
        self.settingsChanged = 1
        self.__setShowNametagsButton()

    def __setShowNametagsButton(self):
        showNametags = base.settings.getSetting('show-nametags', True)
        if showNametags:
            self.ShowNametags_Label['text'] = TTLocalizer.OptionsPageShowNametagsOn
            self.ShowNametags_toggleButton['text'] = TTLocalizer.OptionsPageToggleOff
        else:
            self.ShowNametags_Label['text'] = TTLocalizer.OptionsPageShowNametagsOff
            self.ShowNametags_toggleButton['text'] = TTLocalizer.OptionsPageToggleOn

    def __doDisplaySettings(self):
        if self.displaySettings == None:
            self.displaySettings = DisplaySettingsDialog.DisplaySettingsDialog()
            self.displaySettings.load()
            self.accept(self.displaySettings.doneEvent, self.__doneDisplaySettings)
        self.displaySettings.enter(self.ChangeDisplaySettings, self.ChangeDisplayAPI)
        return

    def __doneDisplaySettings(self, anyChanged, apiChanged):
        if anyChanged:
            self.__setDisplaySettings()
            properties = base.win.getProperties()
            self.displaySettingsChanged = 1
            self.displaySettingsSize = (properties.getXSize(), properties.getYSize())
            self.displaySettingsFullscreen = properties.getFullscreen()
            self.displaySettingsEmbedded = self.isPropertiesEmbedded(properties)
            self.displaySettingsApi = base.pipe.getInterfaceName()
            self.displaySettingsApiChanged = apiChanged

    def isPropertiesEmbedded(self, properties):
        result = False
        if properties.getParentWindow():
            result = True
        return result

    def __setDisplaySettings(self):
        properties = base.win.getProperties()
        if properties.getFullscreen():
            screensize = '%s x %s' % (properties.getXSize(), properties.getYSize())
        else:
            screensize = TTLocalizer.OptionsPageDisplayWindowed
        isEmbedded = self.isPropertiesEmbedded(properties)
        if isEmbedded:
            screensize = TTLocalizer.OptionsPageDisplayEmbedded
        api = base.pipe.getInterfaceName()
        settings = {'screensize': screensize,
         'api': api}
        if self.ChangeDisplayAPI:
            OptionsPage.notify.debug('change display settings...')
            detail = TTLocalizer.OptionsPageDisplaySettings % settings
        else:
            OptionsPage.notify.debug('no change display settings...')
            detail = TTLocalizer.OptionsPageDisplaySettingsNoApi % settings
        self.DisplaySettings_Label['text'] = '%s\n%s' % (TTLocalizer.OptionsPageDisplaySummaryIntro, detail)

    def __doSpeedChatStyleLeft(self):
        if self.speedChatStyleIndex > 0:
            self.speedChatStyleIndex = self.speedChatStyleIndex - 1
            self.updateSpeedChatStyle()

    def __doSpeedChatStyleRight(self):
        if self.speedChatStyleIndex < len(speedChatStyles) - 1:
            self.speedChatStyleIndex = self.speedChatStyleIndex + 1
            self.updateSpeedChatStyle()

    def updateSpeedChatStyle(self):
        nameKey, arrowColor, rolloverColor, frameColor = speedChatStyles[self.speedChatStyleIndex]
        newSCColorScheme = SCColorScheme.SCColorScheme(arrowColor=arrowColor, rolloverColor=rolloverColor, frameColor=frameColor)
        self.speedChatStyleText.setColorScheme(newSCColorScheme)
        self.speedChatStyleText.clearMenu()
        colorName = SCStaticTextTerminal.SCStaticTextTerminal(nameKey)
        self.speedChatStyleText.append(colorName)
        self.speedChatStyleText.finalize()
        self.speedChatStyleText.setPos(0.445 - self.speedChatStyleText.getWidth() * self.speed_chat_scale / 2, 0, self.speedChatStyleText.getPos()[2])
        if self.speedChatStyleIndex > 0:
            self.speedChatStyleLeftArrow['state'] = DGG.NORMAL
        else:
            self.speedChatStyleLeftArrow['state'] = DGG.DISABLED
        if self.speedChatStyleIndex < len(speedChatStyles) - 1:
            self.speedChatStyleRightArrow['state'] = DGG.NORMAL
        else:
            self.speedChatStyleRightArrow['state'] = DGG.DISABLED
        base.localAvatar.b_setSpeedChatStyleIndex(self.speedChatStyleIndex)

    def writeDisplaySettings(self, task = None):
        if not self.displaySettingsChanged:
            return
        taskMgr.remove(self.DisplaySettingsTaskName)
        self.notify.info('writing new display settings %s, fullscreen %s, embedded %s, %s to SettingsFile.' % (self.displaySettingsSize,
         self.displaySettingsFullscreen,
         self.displaySettingsEmbedded,
         self.displaySettingsApi))
        base.settings.updateSetting('resolution', (self.displaySettingsSize[0], self.displaySettingsSize[1]))
        base.settings.updateSetting('windowed-mode', not self.displaySettingsFullscreen)
        #base.settings.updateSetting('embedded-mode', self.displaySettingsEmbedded)
        if self.displaySettingsApiChanged and self.displaySettingsApi:
            base.settings.updateSetting('graphics-api-interface', self.displaySettingsApi)
        base.settings.writeSettings()
        self.displaySettingsChanged = 0
        return Task.done

    def __doToggleAdvancedLighting(self):
        messenger.send('wakeup')
        on = base.settings.getSetting('want-modern-outdoor-lighting', True)
        base.settings.updateSetting('want-modern-outdoor-lighting', not on)
        self.settingsChanged = 1
        self.__setAdvancedLightingButton()
        OutdoorLighting.refreshSettings()

    def __setAdvancedLightingButton(self):
        on = base.settings.getSetting('want-modern-outdoor-lighting', True)
        if on:
            self.AdvancedLighting_Label['text'] = TTLocalizer.OptionsPageAdvancedLightingOn
            self.AdvancedLighting_toggleButton['text'] = TTLocalizer.OptionsPageToggleOff
        else:
            self.AdvancedLighting_Label['text'] = TTLocalizer.OptionsPageAdvancedLightingOff
            self.AdvancedLighting_toggleButton['text'] = TTLocalizer.OptionsPageToggleOn

    def __doToggleGodRays(self):
        messenger.send('wakeup')
        on = base.settings.getSetting('lighting-god-rays', True)
        base.settings.updateSetting('lighting-god-rays', not on)
        self.settingsChanged = 1
        self.__setGodRaysButton()
        OutdoorLighting.refreshSettings()

    def __setGodRaysButton(self):
        on = base.settings.getSetting('lighting-god-rays', True)
        adv = base.settings.getSetting('want-modern-outdoor-lighting', True)
        if on:
            self.GodRays_Label['text'] = TTLocalizer.OptionsPageGodRaysOn
            self.GodRays_toggleButton['text'] = TTLocalizer.OptionsPageToggleOff
        else:
            self.GodRays_Label['text'] = TTLocalizer.OptionsPageGodRaysOff
            self.GodRays_toggleButton['text'] = TTLocalizer.OptionsPageToggleOn
        if not adv:
            self.GodRays_Label.setColorScale(0.55, 0.55, 0.55, 1.0)
            self.GodRays_toggleButton['state'] = DGG.DISABLED
        else:
            self.GodRays_Label.setColorScale(1.0, 1.0, 1.0, 1.0)
            self.GodRays_toggleButton['state'] = DGG.NORMAL

    def __doToggleLightingFog(self):
        messenger.send('wakeup')
        on = base.settings.getSetting('lighting-fog-enabled', True)
        base.settings.updateSetting('lighting-fog-enabled', not on)
        self.settingsChanged = 1
        self.__setLightingFogButton()
        OutdoorLighting.refreshSettings()

    def __setLightingFogButton(self):
        on = base.settings.getSetting('lighting-fog-enabled', True)
        adv = base.settings.getSetting('want-modern-outdoor-lighting', True)
        if on:
            self.LightingFog_Label['text'] = TTLocalizer.OptionsPageLightingFogOn
            self.LightingFog_toggleButton['text'] = TTLocalizer.OptionsPageToggleOff
        else:
            self.LightingFog_Label['text'] = TTLocalizer.OptionsPageLightingFogOff
            self.LightingFog_toggleButton['text'] = TTLocalizer.OptionsPageToggleOn
        if not adv:
            self.LightingFog_Label.setColorScale(0.55, 0.55, 0.55, 1.0)
            self.LightingFog_toggleButton['state'] = DGG.DISABLED
        else:
            self.LightingFog_Label.setColorScale(1.0, 1.0, 1.0, 1.0)
            self.LightingFog_toggleButton['state'] = DGG.NORMAL

    def __setLightingIntensity(self):
        messenger.send('wakeup')
        val = round(self.LightingIntensity_Slider['value'], 2)
        self.LightingIntensity_valueLabel['text'] = '%.1fx' % val
        base.settings.updateSetting('lighting-intensity', val)
        self.settingsChanged = 1
        OutdoorLighting.refreshSettings()

    def __setLightingIntensitySlider(self):
        val = float(base.settings.getSetting('lighting-intensity', 1.0))
        val = max(0.4, min(1.8, val))
        self.LightingIntensity_Slider['value'] = val
        self.LightingIntensity_valueLabel['text'] = '%.1fx' % val

    def __setColorTemp(self):
        messenger.send('wakeup')
        val = round(self.ColorTemp_Slider['value'], 2)
        if val > 0.1:
            label = TTLocalizer.OptionsPageColorTempWarm
        elif val < -0.1:
            label = TTLocalizer.OptionsPageColorTempCool
        else:
            label = 'Neutral'
        self.ColorTemp_valueLabel['text'] = label
        base.settings.updateSetting('lighting-color-temp', val)
        self.settingsChanged = 1
        OutdoorLighting.refreshSettings()

    def __setColorTempSlider(self):
        val = float(base.settings.getSetting('lighting-color-temp', 0.0))
        val = max(-1.0, min(1.0, val))
        self.ColorTemp_Slider['value'] = val
        if val > 0.1:
            label = TTLocalizer.OptionsPageColorTempWarm
        elif val < -0.1:
            label = TTLocalizer.OptionsPageColorTempCool
        else:
            label = 'Neutral'
        self.ColorTemp_valueLabel['text'] = label

    # ── Tonemapping ───────────────────────────────────────────────────────────
    def __doToggleTonemap(self):
        messenger.send('wakeup')
        on = base.settings.getSetting('lighting-tonemap-enabled', True)
        base.settings.updateSetting('lighting-tonemap-enabled', not on)
        self.settingsChanged = 1
        self.__setTonemapButton()
        OutdoorLighting.refreshSettings()

    def __setTonemapButton(self):
        on  = base.settings.getSetting('lighting-tonemap-enabled', True)
        adv = base.settings.getSetting('want-modern-outdoor-lighting', True)
        if on:
            self.Tonemap_Label['text'] = TTLocalizer.OptionsPageTonemapOn
            self.Tonemap_toggleButton['text'] = TTLocalizer.OptionsPageToggleOff
        else:
            self.Tonemap_Label['text'] = TTLocalizer.OptionsPageTonemapOff
            self.Tonemap_toggleButton['text'] = TTLocalizer.OptionsPageToggleOn
        shade = 1.0 if adv else 0.55
        self.Tonemap_Label.setColorScale(shade, shade, shade, 1.0)
        self.Tonemap_toggleButton['state'] = DGG.NORMAL if adv else DGG.DISABLED

    # ── Day / Night cycle ─────────────────────────────────────────────────────
    def __doToggleDayNight(self):
        messenger.send('wakeup')
        on = base.settings.getSetting('want-day-night-cycle', False)
        base.settings.updateSetting('want-day-night-cycle', not on)
        self.settingsChanged = 1
        self.__setDayNightButton()
        OutdoorLighting.refreshSettings()

    def __setDayNightButton(self):
        on  = base.settings.getSetting('want-day-night-cycle', False)
        adv = base.settings.getSetting('want-modern-outdoor-lighting', True)
        if on:
            self.DayNight_Label['text'] = TTLocalizer.OptionsPageDayNightOn
            self.DayNight_toggleButton['text'] = TTLocalizer.OptionsPageToggleOff
        else:
            self.DayNight_Label['text'] = TTLocalizer.OptionsPageDayNightOff
            self.DayNight_toggleButton['text'] = TTLocalizer.OptionsPageToggleOn
        shade = 1.0 if adv else 0.55
        self.DayNight_Label.setColorScale(shade, shade, shade, 1.0)
        self.DayNight_toggleButton['state'] = DGG.NORMAL if adv else DGG.DISABLED

    # ── Procedural Sky ────────────────────────────────────────────────────────
    def __doToggleProceduralSky(self):
        messenger.send('wakeup')
        on = base.settings.getSetting('want-procedural-sky', True)
        base.settings.updateSetting('want-procedural-sky', not on)
        self.settingsChanged = 1
        self.__setProceduralSkyButton()
        OutdoorLighting.refreshSettings()

    def __setProceduralSkyButton(self):
        on  = base.settings.getSetting('want-procedural-sky', True)
        adv = base.settings.getSetting('want-modern-outdoor-lighting', True)
        if on:
            self.ProceduralSky_Label['text'] = TTLocalizer.OptionsPageProceduralSkyOn
            self.ProceduralSky_toggleButton['text'] = TTLocalizer.OptionsPageToggleOff
        else:
            self.ProceduralSky_Label['text'] = TTLocalizer.OptionsPageProceduralSkyOff
            self.ProceduralSky_toggleButton['text'] = TTLocalizer.OptionsPageToggleOn
        shade = 1.0 if adv else 0.55
        self.ProceduralSky_Label.setColorScale(shade, shade, shade, 1.0)
        self.ProceduralSky_toggleButton['state'] = DGG.NORMAL if adv else DGG.DISABLED

    # ── Bloom ─────────────────────────────────────────────────────────────────
    def __doToggleBloom(self):
        messenger.send('wakeup')
        on = base.settings.getSetting('lighting-bloom-enabled', True)
        base.settings.updateSetting('lighting-bloom-enabled', not on)
        self.settingsChanged = 1
        self.__setBloomButton()
        OutdoorLighting.refreshSettings()

    def __setBloomButton(self):
        on  = base.settings.getSetting('lighting-bloom-enabled', True)
        adv = base.settings.getSetting('want-modern-outdoor-lighting', True)
        if on:
            self.Bloom_Label['text'] = TTLocalizer.OptionsPageBloomOn
            self.Bloom_toggleButton['text'] = TTLocalizer.OptionsPageToggleOff
        else:
            self.Bloom_Label['text'] = TTLocalizer.OptionsPageBloomOff
            self.Bloom_toggleButton['text'] = TTLocalizer.OptionsPageToggleOn
        shade = 1.0 if adv else 0.55
        self.Bloom_Label.setColorScale(shade, shade, shade, 1.0)
        self.Bloom_toggleButton['state'] = DGG.NORMAL if adv else DGG.DISABLED

    # ── Water Reflections ─────────────────────────────────────────────────────
    def __doToggleWaterReflections(self):
        messenger.send('wakeup')
        on = base.settings.getSetting('want-water-reflections', True)
        base.settings.updateSetting('want-water-reflections', not on)
        self.settingsChanged = 1
        self.__setWaterReflectionsButton()
        OutdoorLighting.refreshSettings()

    def __setWaterReflectionsButton(self):
        on  = base.settings.getSetting('want-water-reflections', True)
        adv = base.settings.getSetting('want-modern-outdoor-lighting', True)
        if on:
            self.WaterRefl_Label['text'] = TTLocalizer.OptionsPageWaterReflOn
            self.WaterRefl_toggleButton['text'] = TTLocalizer.OptionsPageToggleOff
        else:
            self.WaterRefl_Label['text'] = TTLocalizer.OptionsPageWaterReflOff
            self.WaterRefl_toggleButton['text'] = TTLocalizer.OptionsPageToggleOn
        shade = 1.0 if adv else 0.55
        self.WaterRefl_Label.setColorScale(shade, shade, shade, 1.0)
        self.WaterRefl_toggleButton['state'] = DGG.NORMAL if adv else DGG.DISABLED

    # ── Shadow Quality ────────────────────────────────────────────────────────
    _SHADOW_QUALITY_CYCLE = ('off', 'low', 'medium', 'high')
    _SHADOW_QUALITY_LABELS = {
        'off':    TTLocalizer.OptionsPageShadowQualityOff    if hasattr(TTLocalizer, 'OptionsPageShadowQualityOff')    else 'Off',
        'low':    TTLocalizer.OptionsPageShadowQualityLow    if hasattr(TTLocalizer, 'OptionsPageShadowQualityLow')    else 'Low',
        'medium': TTLocalizer.OptionsPageShadowQualityMedium if hasattr(TTLocalizer, 'OptionsPageShadowQualityMedium') else 'Medium',
        'high':   TTLocalizer.OptionsPageShadowQualityHigh   if hasattr(TTLocalizer, 'OptionsPageShadowQualityHigh')   else 'High',
    }

    def __cycleShadowQuality(self):
        messenger.send('wakeup')
        cur = base.settings.getSetting('shadow-quality', 'high')
        cycle = self._SHADOW_QUALITY_CYCLE
        idx   = cycle.index(cur) if cur in cycle else len(cycle) - 1
        nxt   = cycle[(idx + 1) % len(cycle)]
        base.settings.updateSetting('shadow-quality', nxt)
        self.settingsChanged = 1
        self.__setShadowQualityLabel()
        OutdoorLighting.refreshSettings()

    def __setShadowQualityLabel(self):
        q = base.settings.getSetting('shadow-quality', 'high')
        self.ShadowQuality_valueLabel['text'] = self._SHADOW_QUALITY_LABELS.get(
            q, q.capitalize())

    # ── Fog Density ───────────────────────────────────────────────────────────
    def __setFogDensity(self):
        messenger.send('wakeup')
        val = round(self.FogDensity_Slider['value'], 2)
        self.FogDensity_valueLabel['text'] = '%.1fx' % val
        base.settings.updateSetting('fog-density-multiplier', val)
        self.settingsChanged = 1
        OutdoorLighting.refreshSettings()

    def __setFogDensitySlider(self):
        val = float(base.settings.getSetting('fog-density-multiplier', 1.0))
        val = max(0.2, min(2.5, val))
        self.FogDensity_Slider['value'] = val
        self.FogDensity_valueLabel['text'] = '%.1fx' % val

    # ── Vignette ──────────────────────────────────────────────────────────────
    def __doToggleVignette(self):
        messenger.send('wakeup')
        on = base.settings.getSetting('lighting-vignette-enabled', False)
        base.settings.updateSetting('lighting-vignette-enabled', not on)
        self.settingsChanged = 1
        self.__setVignetteButton()
        OutdoorLighting.refreshSettings()

    def __setVignetteButton(self):
        on  = base.settings.getSetting('lighting-vignette-enabled', False)
        adv = base.settings.getSetting('want-modern-outdoor-lighting', True)
        if on:
            self.Vignette_Label['text'] = TTLocalizer.OptionsPageVignetteOn
            self.Vignette_toggleButton['text'] = TTLocalizer.OptionsPageToggleOff
        else:
            self.Vignette_Label['text'] = TTLocalizer.OptionsPageVignetteOff
            self.Vignette_toggleButton['text'] = TTLocalizer.OptionsPageToggleOn
        shade = 1.0 if adv else 0.55
        self.Vignette_Label.setColorScale(shade, shade, shade, 1.0)
        self.Vignette_toggleButton['state'] = DGG.NORMAL if adv else DGG.DISABLED

    # ── Day/Night Speed ───────────────────────────────────────────────────────
    def __setDayNightSpeed(self):
        messenger.send('wakeup')
        val = round(self.DayNightSpeed_Slider['value'], 2)
        self.DayNightSpeed_valueLabel['text'] = '%.1fx' % val
        base.settings.updateSetting('day-night-speed', val)
        self.settingsChanged = 1
        OutdoorLighting.refreshSettings()

    def __setDayNightSpeedSlider(self):
        val = float(base.settings.getSetting('day-night-speed', 1.0))
        val = max(0.1, min(5.0, val))
        self.DayNightSpeed_Slider['value'] = val
        self.DayNightSpeed_valueLabel['text'] = '%.1fx' % val
        dn  = base.settings.getSetting('want-day-night-cycle', False)
        adv = base.settings.getSetting('want-modern-outdoor-lighting', True)
        shade = 1.0 if (adv and dn) else 0.55
        self.DayNightSpeed_Label.setColorScale(shade, shade, shade, 1.0)
        self.DayNightSpeed_Slider['state'] = (
            DGG.NORMAL if (adv and dn) else DGG.DISABLED)

    def __handleExitShowWithConfirm(self):
        self.confirm = TTDialog.TTGlobalDialog(doneEvent='confirmDone', message=TTLocalizer.OptionsPageExitConfirm, style=TTDialog.TwoChoice)
        self.confirm.show()
        self._parent.doneStatus = {'mode': 'exit',
         'exitTo': 'closeShard'}
        self.accept('confirmDone', self.__handleConfirm)

    def __handleConfirm(self):
        status = self.confirm.doneStatus
        self.ignore('confirmDone')
        self.confirm.cleanup()
        del self.confirm
        if status == 'ok':
            base.cr._userLoggingOut = True
            messenger.send(self._parent.doneEvent)


class CodesTabPage(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('CodesTabPage')

    def __init__(self, parent = aspect2d):
        self._parent = parent
        DirectFrame.__init__(self, parent=self._parent, relief=None, pos=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0))
        self.load()
        return

    def destroy(self):
        self._parent = None
        DirectFrame.destroy(self)
        return

    def load(self):
        cdrGui = loader.loadModel('phase_3.5/models/gui/tt_m_gui_sbk_codeRedemptionGui')
        instructionGui = cdrGui.find('**/tt_t_gui_sbk_cdrPresent')
        flippyGui = cdrGui.find('**/tt_t_gui_sbk_cdrFlippy')
        codeBoxGui = cdrGui.find('**/tt_t_gui_sbk_cdrCodeBox')
        self.resultPanelSuccessGui = cdrGui.find('**/tt_t_gui_sbk_cdrResultPanel_success')
        self.resultPanelFailureGui = cdrGui.find('**/tt_t_gui_sbk_cdrResultPanel_failure')
        self.resultPanelErrorGui = cdrGui.find('**/tt_t_gui_sbk_cdrResultPanel_error')
        self.successSfx = base.loader.loadSfx('phase_3.5/audio/sfx/tt_s_gui_sbk_cdrSuccess.ogg')
        self.failureSfx = base.loader.loadSfx('phase_3.5/audio/sfx/tt_s_gui_sbk_cdrFailure.ogg')
        self.instructionPanel = DirectFrame(parent=self, relief=None, image=instructionGui, image_scale=0.8, text=TTLocalizer.CdrInstructions, text_pos=TTLocalizer.OPCodesInstructionPanelTextPos, text_align=TextNode.ACenter, text_scale=TTLocalizer.OPCodesResultPanelTextScale, text_wordwrap=TTLocalizer.OPCodesInstructionPanelTextWordWrap, pos=(-0.429, 0, -0.05))
        self.codeBox = DirectFrame(parent=self, relief=None, image=codeBoxGui, pos=(0.433, 0, 0.35))
        self.flippyFrame = DirectFrame(parent=self, relief=None, image=flippyGui, pos=(0.44, 0, -0.353))
        self.codeInput = DirectEntry(parent=self.codeBox, relief=DGG.GROOVE, scale=0.08, pos=(-0.33, 0, -0.006), borderWidth=(0.05, 0.05), frameColor=((1, 1, 1, 1), (1, 1, 1, 1), (0.5, 0.5, 0.5, 0.5)), state=DGG.NORMAL, text_align=TextNode.ALeft, text_scale=TTLocalizer.OPCodesInputTextScale, width=10.5, numLines=1, focus=1, backgroundFocus=0, cursorKeys=1, text_fg=(0, 0, 0, 1), suppressMouse=1, autoCapitalize=0, command=self.__submitCode)
        submitButtonGui = loader.loadModel('phase_3/models/gui/quit_button')
        self.submitButton = DirectButton(parent=self, relief=None, image=(submitButtonGui.find('**/QuitBtn_UP'),
         submitButtonGui.find('**/QuitBtn_DN'),
         submitButtonGui.find('**/QuitBtn_RLVR'),
         submitButtonGui.find('**/QuitBtn_UP')), image3_color=Vec4(0.5, 0.5, 0.5, 0.5), image_scale=1.15, state=DGG.NORMAL, text=TTLocalizer.NameShopSubmitButton, text_scale=TTLocalizer.OPCodesSubmitTextScale, text_align=TextNode.ACenter, text_pos=TTLocalizer.OPCodesSubmitTextPos, text3_fg=(0.5, 0.5, 0.5, 0.75), textMayChange=0, pos=(0.45, 0.0, 0.0896), command=self.__submitCode)
        self.resultPanel = DirectFrame(parent=self, relief=None, image=self.resultPanelSuccessGui, text='', text_pos=TTLocalizer.OPCodesResultPanelTextPos, text_align=TextNode.ACenter, text_scale=TTLocalizer.OPCodesResultPanelTextScale, text_wordwrap=TTLocalizer.OPCodesResultPanelTextWordWrap, pos=(-0.42, 0, -0.0567))
        self.resultPanel.hide()
        closeButtonGui = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        self.closeButton = DirectButton(parent=self.resultPanel, pos=(0.296, 0, -0.466), relief=None, state=DGG.NORMAL, image=(closeButtonGui.find('**/CloseBtn_UP'), closeButtonGui.find('**/CloseBtn_DN'), closeButtonGui.find('**/CloseBtn_Rllvr')), image_scale=(1, 1, 1), command=self.__hideResultPanel)
        closeButtonGui.removeNode()
        cdrGui.removeNode()
        submitButtonGui.removeNode()
        return

    def enter(self):
        self.show()
        localAvatar.chatMgr.fsm.request('otherDialog')
        self.codeInput['focus'] = 1
        self.codeInput.enterText('')
        self.__enableCodeEntry()

    def exit(self):
        self.resultPanel.hide()
        self.hide()
        localAvatar.chatMgr.fsm.request('mainMenu')

    def unload(self):
        self.instructionPanel.destroy()
        self.instructionPanel = None
        self.codeBox.destroy()
        self.codeBox = None
        self.flippyFrame.destroy()
        self.flippyFrame = None
        self.codeInput.destroy()
        self.codeInput = None
        self.submitButton.destroy()
        self.submitButton = None
        self.resultPanel.destroy()
        self.resultPanel = None
        self.closeButton.destroy()
        self.closeButton = None
        del self.successSfx
        del self.failureSfx
        return

    def __submitCode(self, input = None):
        if input == None:
            input = self.codeInput.get()
        self.codeInput['focus'] = 1
        if input == '':
            return
        messenger.send('wakeup')
        if hasattr(base, 'codeRedemptionMgr'):
            base.codeRedemptionMgr.redeemCode(input, self.__getCodeResult)
        self.codeInput.enterText('')
        self.__disableCodeEntry()
        return

    def __getCodeResult(self, result, awardMgrResult):
        self.notify.debug('result = %s' % result)
        self.notify.debug('awardMgrResult = %s' % awardMgrResult)
        self.__enableCodeEntry()
        if result == 0:
            self.resultPanel['image'] = self.resultPanelSuccessGui
            self.resultPanel['text'] = TTLocalizer.CdrResultSuccess
        elif result == 1 or result == 3:
            self.resultPanel['image'] = self.resultPanelFailureGui
            self.resultPanel['text'] = TTLocalizer.CdrResultInvalidCode
        elif result == 2:
            self.resultPanel['image'] = self.resultPanelFailureGui
            self.resultPanel['text'] = TTLocalizer.CdrResultExpiredCode
        elif result == 4:
            self.resultPanel['image'] = self.resultPanelErrorGui
            if awardMgrResult == 0:
                self.resultPanel['text'] = TTLocalizer.CdrResultSuccess
            elif awardMgrResult == 1 or awardMgrResult == 2 or awardMgrResult == 15 or awardMgrResult == 16:
                self.resultPanel['text'] = TTLocalizer.CdrResultUnknownError
            elif awardMgrResult == 3 or awardMgrResult == 4:
                self.resultPanel['text'] = TTLocalizer.CdrResultMailboxFull
            elif awardMgrResult == 5 or awardMgrResult == 10:
                self.resultPanel['text'] = TTLocalizer.CdrResultAlreadyInMailbox
            elif awardMgrResult == 6 or awardMgrResult == 7 or awardMgrResult == 11:
                self.resultPanel['text'] = TTLocalizer.CdrResultAlreadyInQueue
            elif awardMgrResult == 8:
                self.resultPanel['text'] = TTLocalizer.CdrResultAlreadyInCloset
            elif awardMgrResult == 9:
                self.resultPanel['text'] = TTLocalizer.CdrResultAlreadyBeingWorn
            elif awardMgrResult == 12 or awardMgrResult == 13 or awardMgrResult == 14:
                self.resultPanel['text'] = TTLocalizer.CdrResultAlreadyReceived
        elif result == 5:
            self.resultPanel['text'] = TTLocalizer.CdrResultTooManyFails
            self.__disableCodeEntry()
        elif result == 6:
            self.resultPanel['text'] = TTLocalizer.CdrResultServiceUnavailable
            self.__disableCodeEntry()
        if result == 0:
            self.successSfx.play()
        else:
            self.failureSfx.play()
        self.resultPanel.show()

    def __hideResultPanel(self):
        self.resultPanel.hide()

    def __disableCodeEntry(self):
        self.codeInput['state'] = DGG.DISABLED
        self.submitButton['state'] = DGG.DISABLED

    def __enableCodeEntry(self):
        self.codeInput['state'] = DGG.NORMAL
        self.codeInput['focus'] = 1
        self.submitButton['state'] = DGG.NORMAL
