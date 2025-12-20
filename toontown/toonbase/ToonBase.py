from otp.otpbase import OTPBase
from otp.otpbase import OTPLauncherGlobals
from otp.otpbase import OTPGlobals
from otp.settings.Settings import Settings
from direct.showbase.PythonUtil import *
from . import ToontownGlobals
from direct.directnotify import DirectNotifyGlobal
from . import ToontownLoader
from direct.gui import DirectGuiGlobals
from direct.gui.DirectGui import *
from panda3d.core import *
from panda3d.otp import *
import sys
import os
import math
from toontown.toonbase import ToontownAccess
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownBattleGlobals
from toontown.launcher import ToontownDownloadWatcher
from toontown.toonbase.AssetCache import assetCache

class ToonBase(OTPBase.OTPBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToonBase')

    def __init__(self):
        self.settings = Settings()
        # Remap orbital camera to right-click instead of middle-click  
        loadPrcFileData('toonBase Camera Controls', 'drive-button2 alt-mouse3')
        # Make orbital camera more responsive (less smooth, more precise)
        loadPrcFileData('toonBase Camera Responsive', 'drive-rotational-speed 100')
        loadPrcFileData('toonBase Camera Direct', 'drive-mouse-scale 0.015')
        # Fix camera locking bug - disable acceleration and smoothing
        loadPrcFileData('toonBase Camera No Lock', 'drive-rotate-accel 0')
        loadPrcFileData('toonBase Camera No Smooth', 'drive-angular-smooth 0')
        loadPrcFileData('toonBase Camera Instant', 'drive-heading-dampening 0')
        # Enable tank-like controls (A/D rotate, W/S move forward/backward)
        loadPrcFileData('toonBase Tank Controls', 'drive-mode tank')
        if not ConfigVariableInt('ignore-user-options', 0).value:
            self.settings.readSettings()
            mode = not self.settings.getSetting('windowed-mode', True)
            music = self.settings.getSetting('music', True)
            sfx = self.settings.getSetting('sfx', True)
            toonChatSounds = self.settings.getSetting('toon-chat-sounds', True)
            res = self.settings.getSetting('resolution', (800, 600))
            if mode == None:
                mode = 1
            if res == None:
                res = (800, 600)
            loadPrcFileData('toonBase Settings Window Res', 'win-size %s %s' % (res[0], res[1]))
            loadPrcFileData('toonBase Settings Window FullScreen', 'fullscreen %s' % mode)
            loadPrcFileData('toonBase Settings Music Active', 'audio-music-active %s' % music)
            loadPrcFileData('toonBase Settings Sound Active', 'audio-sfx-active %s' % sfx)
            loadPrcFileData('toonBase Settings Toon Chat Sounds', 'toon-chat-sounds %s' % toonChatSounds)
        OTPBase.OTPBase.__init__(self)
        if not self.isMainWindowOpen():
            try:
                launcher.setPandaErrorCode(7)
            except:
                pass

            sys.exit(1)
        self.disableShowbaseMouse()
        base.debugRunningMultiplier /= OTPGlobals.ToonSpeedFactor
        self.toonChatSounds = ConfigVariableBool('toon-chat-sounds', 1).value
        
        # Setup WASD controls alongside arrow keys
        self.setupWASDControls()
        self.placeBeforeObjects = ConfigVariableBool('place-before-objects', 0).value
        self.endlessQuietZone = False
        self.wantDynamicShadows = 0
        self.exitErrorCode = 0
        camera.setPosHpr(0, 0, 0, 0, 0, 0)
        # Set up widescreen support with dynamic FOV based on aspect ratio
        self.baseFov = ToontownGlobals.DefaultCameraFov
        self.updateFovForAspectRatio()
        self.camLens.setNearFar(ToontownGlobals.DefaultCameraNear, ToontownGlobals.DefaultCameraFar)
        # Apply saved volume settings
        musicVolume = self.settings.getSetting('musicVolume', 100) / 100.0
        sfxVolume = self.settings.getSetting('sfxVolume', 100) / 100.0
        self.musicManager.setVolume(musicVolume)
        for sfxManager in self.sfxManagerList:
            sfxManager.setVolume(sfxVolume)
        self.setBackgroundColor(ToontownGlobals.DefaultBackgroundColor)
        tpm = TextPropertiesManager.getGlobalPtr()
        candidateActive = TextProperties()
        candidateActive.setTextColor(0, 0, 1, 1)
        tpm.setProperties('candidate_active', candidateActive)
        candidateInactive = TextProperties()
        candidateInactive.setTextColor(0.3, 0.3, 0.7, 1)
        tpm.setProperties('candidate_inactive', candidateInactive)
        self.transitions.IrisModelName = 'phase_3/models/misc/iris'
        self.transitions.FadeModelName = 'phase_3/models/misc/fade'
        self.exitFunc = self.userExit
        if 'launcher' in __builtins__ and launcher:
            launcher.setPandaErrorCode(11)
        globalClock.setMaxDt(0.2)
        if ConfigVariableBool('want-particles', 1).value == 1:
            self.notify.debug('Enabling particles')
            self.enableParticles()
        self.accept(ToontownGlobals.ScreenshotHotkey, self.takeScreenShot)
        self.accept('panda3d-render-error', self.panda3dRenderError)
        oldLoader = self.loader
        self.loader = ToontownLoader.ToontownLoader(self)
        __builtins__['loader'] = self.loader
        oldLoader.destroy()
        # Initialize asset cache for faster loading
        assetCache.initialize(self.loader)
        self.accept('PandaPaused', self.disableAllAudio)
        self.accept('PandaRestarted', self.enableAllAudio)
        self.friendMode = ConfigVariableBool('switchboard-friends', 0).value
        self.wantPets = ConfigVariableBool('want-pets', 1).value
        self.wantBingo = ConfigVariableBool('want-fish-bingo', 1).value
        self.wantKarts = ConfigVariableBool('want-karts', 1).value
        self.wantNewSpecies = ConfigVariableBool('want-new-species', 0).value
        self.inactivityTimeout = ConfigVariableDouble('inactivity-timeout', ToontownGlobals.KeyboardTimeout).value
        if self.inactivityTimeout:
            self.notify.debug('Enabling Panda timeout: %s' % self.inactivityTimeout)
            self.mouseWatcherNode.setInactivityTimeout(self.inactivityTimeout)
        self.randomMinigameAbort = ConfigVariableBool('random-minigame-abort', 0).value
        self.randomMinigameDisconnect = ConfigVariableBool('random-minigame-disconnect', 0).value
        self.randomMinigameNetworkPlugPull = ConfigVariableBool('random-minigame-netplugpull', 0).value
        self.autoPlayAgain = ConfigVariableBool('auto-play-again', 0).value
        self.skipMinigameReward = ConfigVariableBool('skip-minigame-reward', 0).value
        self.wantMinigameDifficulty = ConfigVariableBool('want-minigame-difficulty', 0).value
        self.minigameDifficulty = ConfigVariableDouble('minigame-difficulty', -1.0).value
        if self.minigameDifficulty == -1.0:
            del self.minigameDifficulty
        self.minigameSafezoneId = ConfigVariableInt('minigame-safezone-id', -1).value
        if self.minigameSafezoneId == -1:
            del self.minigameSafezoneId
        cogdoGameSafezoneId = ConfigVariableInt('cogdo-game-safezone-id', -1).value
        cogdoGameDifficulty = ConfigVariableDouble('cogdo-game-difficulty', -1).value
        if cogdoGameDifficulty != -1:
            self.cogdoGameDifficulty = cogdoGameDifficulty
        if cogdoGameSafezoneId != -1:
            self.cogdoGameSafezoneId = cogdoGameSafezoneId
        ToontownBattleGlobals.SkipMovie = ConfigVariableBool('skip-battle-movies', 0).value
        self.creditCardUpFront = ConfigVariableInt('credit-card-up-front', -1).value
        if self.creditCardUpFront == -1:
            del self.creditCardUpFront
        else:
            self.creditCardUpFront = self.creditCardUpFront != 0
        self.housingEnabled = ConfigVariableBool('want-housing', 1).value
        self.cannonsEnabled = ConfigVariableBool('estate-cannons', 0).value
        self.fireworksEnabled = ConfigVariableBool('estate-fireworks', 0).value
        self.dayNightEnabled = ConfigVariableBool('estate-day-night', 0).value
        self.cloudPlatformsEnabled = ConfigVariableBool('estate-clouds', 0).value
        self.greySpacing = ConfigVariableBool('allow-greyspacing', 0).value
        self.goonsEnabled = ConfigVariableBool('estate-goon', 0).value
        self.restrictTrialers = ConfigVariableBool('restrict-trialers', 1).value
        self.roamingTrialers = ConfigVariableBool('roaming-trialers', 1).value
        self.slowQuietZone = ConfigVariableBool('slow-quiet-zone', 0).value
        self.slowQuietZoneDelay = ConfigVariableDouble('slow-quiet-zone-delay', 5).value
        self.killInterestResponse = ConfigVariableBool('kill-interest-response', 0).value
        tpMgr = TextPropertiesManager.getGlobalPtr()
        WLDisplay = TextProperties()
        WLDisplay.setSlant(0.3)
        WLEnter = TextProperties()
        WLEnter.setTextColor(1.0, 0.0, 0.0, 1)
        tpMgr.setProperties('WLDisplay', WLDisplay)
        tpMgr.setProperties('WLEnter', WLEnter)
        del tpMgr
        CullBinManager.getGlobalPtr().addBin('gui-popup', CullBinManager.BTUnsorted, 60)
        CullBinManager.getGlobalPtr().addBin('shadow', CullBinManager.BTFixed, 15)
        CullBinManager.getGlobalPtr().addBin('ground', CullBinManager.BTFixed, 14)
        self.lastScreenShotTime = globalClock.getRealTime()
        self.accept('InputState-forward', self.__walking)
        self.canScreenShot = 1
        self.glitchCount = 0
        self.walking = 0
        self.oldX = max(1, base.win.getXSize())
        self.oldY = max(1, base.win.getYSize())
        self.aspectRatio = float(self.oldX) / self.oldY
        return
    
    def updateFovForAspectRatio(self):
        """Update FOV dynamically based on aspect ratio for proper widescreen support."""
        aspectRatio = base.camLens.getAspectRatio()
        
        # Base FOV is for 4:3 aspect ratio (1.333...)
        # For widescreen, we increase horizontal FOV to prevent stretching
        baseAspectRatio = 4.0 / 3.0
        
        if aspectRatio > baseAspectRatio:
            # Widescreen - increase FOV proportionally
            # Calculate the horizontal FOV adjustment
            fovMultiplier = aspectRatio / baseAspectRatio
            newFov = self.baseFov * fovMultiplier
            # Cap maximum FOV to prevent fish-eye effect
            newFov = min(newFov, 90.0)
        else:
            # Standard or narrower aspect ratio
            newFov = self.baseFov
        
        self.camLens.setFov(newFov)
    
    def getWidescreenGUIXScale(self):
        """Get the X scaling factor for GUI elements in widescreen.
        
        DEPRECATED: Use getWidescreenXOffset() for proper positioning instead.
        Returns a multiplier to adjust horizontal GUI positions from 4:3 to current aspect.
        """
        currentAspect = base.camLens.getAspectRatio()
        baseAspect = 4.0 / 3.0  # 1.333...
        return currentAspect / baseAspect
    
    def getWidescreenXOffset(self, baseX, alignment='left'):
        """Calculate proper X position for GUI elements in widescreen.
        
        Args:
            baseX: The original X position designed for 4:3 (1.333 aspect)
            alignment: 'left', 'right', or 'center' - which edge the element aligns to
        
        Returns:
            Adjusted X position that maintains distance from screen edge
        """
        # Base aspect2d boundaries for 4:3 reference
        base4x3Left = -4.0 / 3.0  # -1.333...
        base4x3Right = 4.0 / 3.0   # 1.333...
        
        # Current aspect2d boundaries (automatically adjusted by Panda3D)
        currentLeft = base.a2dLeft
        currentRight = base.a2dRight
        
        if alignment == 'left':
            # Calculate offset from left edge in 4:3
            offsetFrom4x3Left = baseX - base4x3Left
            # Apply same offset from current left edge
            return currentLeft + offsetFrom4x3Left
        elif alignment == 'right':
            # Calculate offset from right edge in 4:3
            offsetFrom4x3Right = baseX - base4x3Right
            # Apply same offset from current right edge
            return currentRight + offsetFrom4x3Right
        else:  # center
            # For centered elements, no adjustment needed (aspect2d handles it)
            return baseX

    def windowEvent(self, win):
        OTPBase.OTPBase.windowEvent(self, win)
        
        # Update FOV when window is resized for widescreen support
        self.updateFovForAspectRatio()
        
        if not ConfigVariableInt('keep-aspect-ratio', 0).value:
            return
        x = max(1, win.getXSize())
        y = max(1, win.getYSize())
        maxX = base.pipe.getDisplayWidth()
        maxY = base.pipe.getDisplayHeight()
        cwp = win.getProperties()
        originX = 0
        originY = 0
        if cwp.hasOrigin():
            originX = cwp.getXOrigin()
            originY = cwp.getYOrigin()
            if originX > maxX:
                originX = originX - maxX
            if originY > maxY:
                oringY = originY - maxY
        maxX -= originX
        maxY -= originY
        if math.fabs(x - self.oldX) > math.fabs(y - self.oldY):
            newY = x / self.aspectRatio
            newX = x
            if newY > maxY:
                newY = maxY
                newX = self.aspectRatio * maxY
        else:
            newX = self.aspectRatio * y
            newY = y
            if newX > maxX:
                newX = maxX
                newY = maxX / self.aspectRatio
        wp = WindowProperties()
        wp.setSize(newX, newY)
        base.win.requestProperties(wp)
        base.cam.node().getLens().setFilmSize(newX, newY)
        self.oldX = newX
        self.oldY = newY

    def disableShowbaseMouse(self):
        self.useDrive()
        self.disableMouse()
        if self.mouseInterface:
            self.mouseInterface.detachNode()
        if base.mouse2cam:
            self.mouse2cam.detachNode()

    def __walking(self, pressed):
        self.walking = pressed
    
    def setupWASDControls(self):
        """Add WASD key bindings as alternative to arrow keys"""
        from direct.showbase.InputStateGlobal import inputState
        
        # Map WASD to same states as arrow keys
        inputState.watchWithModifiers('forward', 'w')
        inputState.watchWithModifiers('reverse', 's')
        inputState.watchWithModifiers('turnLeft', 'a')
        inputState.watchWithModifiers('turnRight', 'd')
        inputState.watchWithModifiers('jump', 'space')
        
        # Keep arrow keys working too
        inputState.watchWithModifiers('forward', 'arrow_up')
        inputState.watchWithModifiers('reverse', 'arrow_down')
        inputState.watchWithModifiers('turnLeft', 'arrow_left')
        inputState.watchWithModifiers('turnRight', 'arrow_right')
        inputState.watchWithModifiers('jump', 'control')
        
        self.notify.info('WASD controls enabled alongside arrow keys')

    def takeScreenShot(self):
        if not os.path.exists('screenshots/'):
            os.mkdir('screenshots/')

        namePrefix = 'screenshot'
        namePrefix = 'screenshots/' + launcher.logPrefix + namePrefix
        timedif = globalClock.getRealTime() - self.lastScreenShotTime
        if self.glitchCount > 10 and self.walking:
            return
        if timedif < 1.0 and self.walking:
            self.glitchCount += 1
            return
        if not hasattr(self, 'localAvatar'):
            self.screenshot(namePrefix=namePrefix)
            self.lastScreenShotTime = globalClock.getRealTime()
            return
        coordOnScreen = ConfigVariableBool('screenshot-coords', 0).value
        self.localAvatar.stopThisFrame = 1
        ctext = self.localAvatar.getAvPosStr()
        self.screenshotStr = ''
        messenger.send('takingScreenshot')
        if coordOnScreen:
            coordTextLabel = DirectLabel(pos=(-0.81, 0.001, -0.87), text=ctext, text_scale=0.05, text_fg=VBase4(1.0, 1.0, 1.0, 1.0), text_bg=(0, 0, 0, 0), text_shadow=(0, 0, 0, 1), relief=None)
            coordTextLabel.setBin('gui-popup', 0)
            strTextLabel = None
            if len(self.screenshotStr):
                strTextLabel = DirectLabel(pos=(0.0, 0.001, 0.9), text=self.screenshotStr, text_scale=0.05, text_fg=VBase4(1.0, 1.0, 1.0, 1.0), text_bg=(0, 0, 0, 0), text_shadow=(0, 0, 0, 1), relief=None)
                strTextLabel.setBin('gui-popup', 0)
        self.graphicsEngine.renderFrame()
        self.screenshot(namePrefix=namePrefix, imageComment=ctext + ' ' + self.screenshotStr)
        self.lastScreenShotTime = globalClock.getRealTime()
        if coordOnScreen:
            if strTextLabel is not None:
                strTextLabel.destroy()
            coordTextLabel.destroy()
        return

    def addScreenshotString(self, str):
        if len(self.screenshotStr):
            self.screenshotStr += '\n'
        self.screenshotStr += str

    def initNametagGlobals(self):
        arrow = loader.loadModel('phase_3/models/props/arrow')
        card = loader.loadModel('phase_3/models/props/panel')
        speech3d = ChatBalloon(loader.loadModel('phase_3/models/props/chatbox').node())
        thought3d = ChatBalloon(loader.loadModel('phase_3/models/props/chatbox_thought_cutout').node())
        speech2d = ChatBalloon(loader.loadModel('phase_3/models/props/chatbox_noarrow').node())
        chatButtonGui = loader.loadModel('phase_3/models/gui/chat_button_gui')
        NametagGlobals.setCamera(self.cam)
        NametagGlobals.setArrowModel(arrow)
        NametagGlobals.setNametagCard(card, VBase4(-0.5, 0.5, -0.5, 0.5))
        if self.mouseWatcherNode:
            NametagGlobals.setMouseWatcher(self.mouseWatcherNode)
        NametagGlobals.setSpeechBalloon3d(speech3d)
        NametagGlobals.setThoughtBalloon3d(thought3d)
        NametagGlobals.setSpeechBalloon2d(speech2d)
        NametagGlobals.setThoughtBalloon2d(thought3d)
        NametagGlobals.setPageButton(PGButton.SReady, chatButtonGui.find('**/Horiz_Arrow_UP'))
        NametagGlobals.setPageButton(PGButton.SDepressed, chatButtonGui.find('**/Horiz_Arrow_DN'))
        NametagGlobals.setPageButton(PGButton.SRollover, chatButtonGui.find('**/Horiz_Arrow_Rllvr'))
        NametagGlobals.setQuitButton(PGButton.SReady, chatButtonGui.find('**/CloseBtn_UP'))
        NametagGlobals.setQuitButton(PGButton.SDepressed, chatButtonGui.find('**/CloseBtn_DN'))
        NametagGlobals.setQuitButton(PGButton.SRollover, chatButtonGui.find('**/CloseBtn_Rllvr'))
        rolloverSound = DirectGuiGlobals.getDefaultRolloverSound()
        if rolloverSound:
            NametagGlobals.setRolloverSound(rolloverSound)
        clickSound = DirectGuiGlobals.getDefaultClickSound()
        if clickSound:
            NametagGlobals.setClickSound(clickSound)
        NametagGlobals.setToon(self.cam)
        self.marginManager = MarginManager()
        self.margins = self.aspect2d.attachNewNode(self.marginManager, DirectGuiGlobals.MIDGROUND_SORT_INDEX + 1)
        mm = self.marginManager
        self.leftCells = [mm.addGridCell(0, 1, base.a2dLeft, base.a2dRight, base.a2dBottom, base.a2dTop), mm.addGridCell(0, 2, base.a2dLeft, base.a2dRight, base.a2dBottom, base.a2dTop), mm.addGridCell(0, 3, base.a2dLeft, base.a2dRight, base.a2dBottom, base.a2dTop)]
        self.bottomCells = [mm.addGridCell(0.5, 0, base.a2dLeft, base.a2dRight, base.a2dBottom, base.a2dTop),
         mm.addGridCell(1.5, 0, base.a2dLeft, base.a2dRight, base.a2dBottom, base.a2dTop),
         mm.addGridCell(2.5, 0, base.a2dLeft, base.a2dRight, base.a2dBottom, base.a2dTop),
         mm.addGridCell(3.5, 0, base.a2dLeft, base.a2dRight, base.a2dBottom, base.a2dTop),
         mm.addGridCell(4.5, 0, base.a2dLeft, base.a2dRight, base.a2dBottom, base.a2dTop)]
        self.rightCells = [mm.addGridCell(5, 2, base.a2dLeft, base.a2dRight, base.a2dBottom, base.a2dTop), mm.addGridCell(5, 1, base.a2dLeft, base.a2dRight, base.a2dBottom, base.a2dTop)]

    def setCellsAvailable(self, cell_list, available):
        for cell in cell_list:
            self.marginManager.setCellAvailable(cell, available)

    def cleanupDownloadWatcher(self):
        self.downloadWatcher.cleanup()
        self.downloadWatcher = None
        return

    def startShow(self, cr, launcherServer = None):
        self.cr = cr
        base.graphicsEngine.renderFrame()
        self.downloadWatcher = ToontownDownloadWatcher.ToontownDownloadWatcher(TTLocalizer.LauncherPhaseNames)
        if launcher.isDownloadComplete():
            self.cleanupDownloadWatcher()
        else:
            self.acceptOnce('launcherAllPhasesComplete', self.cleanupDownloadWatcher)
        gameServer = ConfigVariableString('game-server', '').value
        if gameServer:
            self.notify.info('Using game-server from Configrc: %s ' % gameServer)
        elif launcherServer:
            gameServer = launcherServer
            self.notify.info('Using gameServer from launcher: %s ' % gameServer)
        else:
            gameServer = '127.0.0.1'
        serverPort = ConfigVariableInt('server-port', 7198).value
        serverList = []
        for name in gameServer.split(';'):
            url = URLSpec(name, 1)
            if ConfigVariableBool('server-want-ssl', False).value:
                url.setScheme('s')
            if not url.hasPort():
                url.setPort(serverPort)
            serverList.append(url)

        if len(serverList) == 1:
            failover = ConfigVariableString('server-failover', '').value
            serverURL = serverList[0]
            for arg in failover.split():
                try:
                    port = int(arg)
                    url = URLSpec(serverURL)
                    url.setPort(port)
                except:
                    url = URLSpec(arg, 1)

                if url != serverURL:
                    serverList.append(url)

        cr.loginFSM.request('connect', [serverList])
        self.ttAccess = ToontownAccess.ToontownAccess()

    def removeGlitchMessage(self):
        self.ignore('InputState-forward')
        print('ignoring InputState-forward')

    def exitShow(self, errorCode = None):
        self.notify.info('Exiting Toontown: errorCode = %s' % errorCode)
        if errorCode:
            launcher.setPandaErrorCode(errorCode)
        else:
            launcher.setPandaErrorCode(0)
        sys.exit()

    def setExitErrorCode(self, code):
        self.exitErrorCode = code
        if os.name == 'nt':
            exitCode2exitPage = {OTPLauncherGlobals.ExitEnableChat: 'chat',
             OTPLauncherGlobals.ExitSetParentPassword: 'setparentpassword',
             OTPLauncherGlobals.ExitPurchase: 'purchase'}
            if code in exitCode2exitPage:
                launcher.setRegistry('EXIT_PAGE', exitCode2exitPage[code])

    def getExitErrorCode(self):
        return self.exitErrorCode

    def userExit(self):
        try:
            self.localAvatar.d_setAnimState('TeleportOut', 1)
        except:
            pass

        if self.cr.timeManager:
            self.cr.timeManager.setDisconnectReason(ToontownGlobals.DisconnectCloseWindow)
        base.cr._userLoggingOut = False
        try:
            localAvatar
        except:
            pass
        else:
            messenger.send('clientLogout')
            self.cr.dumpAllSubShardObjects()

        self.cr.loginFSM.request('shutdown')
        self.notify.warning('Could not request shutdown; exiting anyway.')
        self.exitShow()

    def panda3dRenderError(self):
        launcher.setPandaErrorCode(14)
        if self.cr.timeManager:
            self.cr.timeManager.setDisconnectReason(ToontownGlobals.DisconnectGraphicsError)
        self.cr.sendDisconnect()
        sys.exit()

    def getShardPopLimits(self):
        if self.cr.productName == 'JP':
            return (ConfigVariableInt('shard-low-pop', ToontownGlobals.LOW_POP_JP).value, ConfigVariableInt('shard-mid-pop', ToontownGlobals.MID_POP_JP).value, ConfigVariableInt('shard-high-pop', ToontownGlobals.HIGH_POP_JP).value)
        elif self.cr.productName in ['BR', 'FR']:
            return (ConfigVariableInt('shard-low-pop', ToontownGlobals.LOW_POP_INTL).value, ConfigVariableInt('shard-mid-pop', ToontownGlobals.MID_POP_INTL).value, ConfigVariableInt('shard-high-pop', ToontownGlobals.HIGH_POP_INTL).value)
        else:
            return (ConfigVariableInt('shard-low-pop', ToontownGlobals.LOW_POP).value, ConfigVariableInt('shard-mid-pop', ToontownGlobals.MID_POP).value, ConfigVariableInt('shard-high-pop', ToontownGlobals.HIGH_POP).value)

    def playMusic(self, music, looping = 0, interrupt = 1, volume = None, time = 0.0):
        OTPBase.OTPBase.playMusic(self, music, looping, interrupt, volume, time)
