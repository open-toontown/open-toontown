import copy
import string
import os
import sys
import datetime
from pandac.PandaModules import loadPrcFileData, Settings, WindowProperties
from otp.otpgui import OTPDialog
from otp.otpbase import OTPGlobals
from otp.otpbase import OTPRender
from direct.directnotify import DirectNotifyGlobal
try:
    import embedded
except:
    pass

class DisplayOptions:
    notify = DirectNotifyGlobal.directNotify.newCategory('DisplayOptions')

    def __init__(self):
        self.restore_failed = False
        self.loadFromSettings()

    def loadFromSettings(self):
        Settings.readSettings()
        mode = not Settings.getWindowedMode()
        music = Settings.getMusic()
        sfx = Settings.getSfx()
        toonChatSounds = Settings.getToonChatSounds()
        musicVol = Settings.getMusicVolume()
        sfxVol = Settings.getSfxVolume()
        resList = [(640, 480),
         (800, 600),
         (1024, 768),
         (1280, 1024),
         (1600, 1200)]
        res = resList[Settings.getResolution()]
        embed = Settings.getEmbeddedMode()
        self.notify.debug('before prc settings embedded mode=%s' % str(embed))
        self.notify.debug('before prc settings full screen mode=%s' % str(mode))
        if mode == None:
            mode = 1
        if res == None:
            res = (800, 600)
        if not Settings.doSavedSettingsExist():
            self.notify.info('loadFromSettings: No settings; isDefaultEmbedded=%s' % self.isDefaultEmbedded())
            embed = self.isDefaultEmbedded()
        if embed and not self.isEmbeddedPossible():
            self.notify.warning('Embedded mode is not possible.')
            embed = False
        if not mode and not self.isWindowedPossible():
            self.notify.warning('Windowed mode is not possible.')
            mode = True
        loadPrcFileData('toonBase Settings Window Res', 'win-size %s %s' % (res[0], res[1]))
        self.notify.debug('settings resolution = %s' % str(res))
        loadPrcFileData('toonBase Settings Window FullScreen', 'fullscreen %s' % mode)
        self.notify.debug('settings full screen mode=%s' % str(mode))
        loadPrcFileData('toonBase Settings Music Active', 'audio-music-active %s' % music)
        loadPrcFileData('toonBase Settings Sound Active', 'audio-sfx-active %s' % sfx)
        loadPrcFileData('toonBase Settings Music Volume', 'audio-master-music-volume %s' % musicVol)
        loadPrcFileData('toonBase Settings Sfx Volume', 'audio-master-sfx-volume %s' % sfxVol)
        loadPrcFileData('toonBase Settings Toon Chat Sounds', 'toon-chat-sounds %s' % toonChatSounds)
        self.settingsFullScreen = mode
        self.settingsWidth = res[0]
        self.settingsHeight = res[1]
        self.settingsEmbedded = embed
        self.notify.debug('settings embedded mode=%s' % str(self.settingsEmbedded))
        self.notify.info('settingsFullScreen = %s, embedded = %s width=%d height=%d' % (self.settingsFullScreen,
         self.settingsEmbedded,
         self.settingsWidth,
         self.settingsHeight))
        return

    def restrictToEmbedded(self, restrict, change_display = True):
        if base.appRunner is None or base.appRunner.windowProperties is None:
            restrict = 0
        self.restrict_to_embedded = choice(restrict, 1, 0)
        self.notify.debug('restrict_to_embedded: %s' % self.restrict_to_embedded)
        if change_display:
            self.set(base.pipe, self.settingsWidth, self.settingsHeight, self.settingsFullScreen, self.settingsEmbedded)
        return

    def set(self, pipe, width, height, fullscreen, embedded):
        self.notify.debugStateCall(self)
        state = False
        self.notify.info('SET')
        if self.restrict_to_embedded:
            fullscreen = 0
            embedded = 1
        if embedded:
            if base.appRunner.windowProperties:
                width = base.appRunner.windowProperties.getXSize()
                height = base.appRunner.windowProperties.getYSize()
        self.current_pipe = base.pipe
        self.current_properties = WindowProperties(base.win.getProperties())
        properties = self.current_properties
        self.notify.debug('DISPLAY PREVIOUS:')
        self.notify.debug('  EMBEDDED:   %s' % bool(properties.getParentWindow()))
        self.notify.debug('  FULLSCREEN: %s' % bool(properties.getFullscreen()))
        self.notify.debug('  X SIZE:     %s' % properties.getXSize())
        self.notify.debug('  Y SIZE:     %s' % properties.getYSize())
        self.notify.debug('DISPLAY REQUESTED:')
        self.notify.debug('  EMBEDDED:   %s' % bool(embedded))
        self.notify.debug('  FULLSCREEN: %s' % bool(fullscreen))
        self.notify.debug('  X SIZE:     %s' % width)
        self.notify.debug('  Y SIZE:     %s' % height)
        if self.current_pipe == pipe and bool(self.current_properties.getParentWindow()) == bool(embedded) and self.current_properties.getFullscreen() == fullscreen and self.current_properties.getXSize() == width and self.current_properties.getYSize() == height:
            self.notify.info('DISPLAY NO CHANGE REQUIRED')
            state = True
        else:
            properties = WindowProperties()
            properties.setSize(width, height)
            properties.setFullscreen(fullscreen)
            properties.setParentWindow(0)
            if embedded:
                if base.appRunner.windowProperties:
                    properties = base.appRunner.windowProperties
            original_sort = base.win.getSort()
            if self.resetWindowProperties(pipe, properties):
                self.notify.debug('DISPLAY CHANGE SET')
                properties = base.win.getProperties()
                self.notify.debug('DISPLAY ACHIEVED:')
                self.notify.debug('  EMBEDDED:   %s' % bool(properties.getParentWindow()))
                self.notify.debug('  FULLSCREEN: %s' % bool(properties.getFullscreen()))
                self.notify.debug('  X SIZE:     %s' % properties.getXSize())
                self.notify.debug('  Y SIZE:     %s' % properties.getYSize())
                if bool(properties.getParentWindow()) == bool(embedded) and properties.getFullscreen() == fullscreen and properties.getXSize() == width and properties.getYSize() == height:
                    self.notify.info('DISPLAY CHANGE VERIFIED')
                    state = True
                else:
                    self.notify.warning('DISPLAY CHANGE FAILED, RESTORING PREVIOUS DISPLAY')
                    self.restoreWindowProperties()
            else:
                self.notify.warning('DISPLAY CHANGE FAILED')
                self.notify.warning('DISPLAY SET - BEFORE RESTORE')
                self.restoreWindowProperties()
                self.notify.warning('DISPLAY SET - AFTER RESTORE')
            base.win.setSort(original_sort)
            base.graphicsEngine.renderFrame()
            base.graphicsEngine.renderFrame()
        return state

    def resetWindowProperties(self, pipe, properties):
        if base.win:
            currentProperties = WindowProperties(base.win.getProperties())
            gsg = base.win.getGsg()
        else:
            currentProperties = WindowProperties.getDefault()
            gsg = None
        newProperties = WindowProperties(currentProperties)
        newProperties.addProperties(properties)
        if base.pipe != pipe:
            gsg = None
        if gsg == None or currentProperties.getFullscreen() != newProperties.getFullscreen() or currentProperties.getParentWindow() != newProperties.getParentWindow():
            self.notify.debug('window properties: %s' % properties)
            self.notify.debug('gsg: %s' % gsg)
            base.pipe = pipe
            if not base.openMainWindow(props=properties, gsg=gsg, keepCamera=True):
                self.notify.warning('OPEN MAIN WINDOW FAILED')
                return 0
            self.notify.info('OPEN MAIN WINDOW PASSED')
            base.graphicsEngine.openWindows()
            if base.win.isClosed():
                self.notify.warning('Window did not open, removing.')
                base.closeWindow(base.win)
                return 0
            base.disableShowbaseMouse()
            if 'libotp' in sys.modules:
                from libotp import NametagGlobals
                NametagGlobals.setCamera(base.cam)
                NametagGlobals.setMouseWatcher(base.mouseWatcherNode)
        else:
            self.notify.debug('Adjusting properties')
            base.win.requestProperties(properties)
            base.graphicsEngine.renderFrame()
        return 1

    def restoreWindowProperties(self):
        if self.resetWindowProperties(self.current_pipe, self.current_properties):
            self.restore_failed = False
        else:
            self.notify.warning("Couldn't restore original display settings!")
            if base.appRunner and base.appRunner.windowProperties:
                fullscreen = 0
                embedded = 1
                tryProps = base.appRunner.windowProperties
                if self.resetWindowProperties(self.current_pipe, tryProps):
                    self.current_properties = copy.copy(tryProps)
                    self.restore_failed = False
                    return
            if self.current_properties.getFullscreen():
                fullscreen = 0
                embedded = 0
                tryProps = self.current_properties
                tryProps.setFullscreen(0)
                if self.resetWindowProperties(self.current_pipe, tryProps):
                    self.current_properties = copy.copy(tryProps)
                    self.restore_failed = False
                    return
            self.notify.error('Failed opening regular window!')
            base.panda3dRenderError()
            self.restore_failed = True

    @staticmethod
    def isDefaultEmbedded():
        result = False
        try:
            embedOption = int(base.launcher.getValue('GAME_DEFAULT_TO_EMBEDDED', None))
            if embedOption != None:
                result = bool(int(embedOption))
        except:
            pass

        return result

    @staticmethod
    def isEmbeddedPossible():
        result = False
        try:
            showOption = base.launcher.getValue('GAME_SHOW_EMBEDDED_OPTION', None)
            if showOption != None:
                result = bool(int(showOption))
        except:
            pass

        return result

    @staticmethod
    def isWindowedPossible():
        result = True
        try:
            showOption = base.launcher.getValue('GAME_SHOW_WINDOWED_OPTION', None)
            if showOption != None:
                result = bool(int(showOption))
        except:
            pass

        return result
