import builtins

class game:
    name = 'toontown'
    process = 'client'


builtins.game = game()
from panda3d.core import (
    ConfigVariableBool,
    ConfigVariableDouble,
    ConfigVariableString,
    Filename,
    HTTPClient,
    Loader,
    loadPrcFile,
    TextNode,
    Thread,
    VBase3,
    Vec4
)

import time
import sys

# Always load config so PRC toggles work regardless of launcher path / -O.
try:
    loadPrcFile('etc/Configrc.prc')
except Exception:
    pass
try:
    launcher
except:
    from toontown.launcher.ToontownDummyLauncher import ToontownDummyLauncher
    launcher = ToontownDummyLauncher()
    builtins.launcher = launcher

launcher.setRegistry('EXIT_PAGE', 'normal')
pollingDelay = 0.01
print('ToontownStart: Polling for game2 to finish...')
while not launcher.getGame2Done():
    time.sleep(pollingDelay)

print('ToontownStart: Game2 is finished.')
print('ToontownStart: Starting the game.')
if launcher.isDummy():
    http = HTTPClient()
else:
    http = launcher.http

tempLoader = Loader()
from direct.gui import DirectGuiGlobals
print('ToontownStart: setting default font')
from . import ToontownGlobals
DirectGuiGlobals.setDefaultFontFunc(ToontownGlobals.getInterfaceFont)
launcher.setPandaErrorCode(7)
from .ToonBaseGlobal import base
if base.win == None:
    print('Unable to open window; aborting.')
    sys.exit()

launcher.setPandaErrorCode(0)
launcher.setPandaWindowOpen()
ConfigVariableDouble('decompressor-step-time').setValue(0.001)
ConfigVariableDouble('extractor-step-time').setValue(0.001)
ConfigVariableBool('preload-textures').setValue(1)
ConfigVariableBool('preload-simple-textures').setValue(1)
ConfigVariableBool('compressed-textures').setValue(1)
# Additional performance optimizations
ConfigVariableBool('garbage-collect-states').setValue(0)
ConfigVariableBool('support-threads').setValue(1)
# Texture and Model pools are managed automatically by Panda3D


# Modern launcher/loading overlay (best-effort).
try:
    from toontown.toontowngui.ModernLoadingScreen import ModernLoadingScreen
    base.modernLoading = ModernLoadingScreen()
    _ml = getattr(base, 'modernLoading', None)
    if _ml and _ml.enabled():
        base.modernLoading.set_title('Toontown', 'Starting up…')
        base.modernLoading.set_status('Initializing engine…')
        base.modernLoading.set_progress(3)
except Exception:
    try:
        import traceback
        print('ToontownStart: ModernLoadingScreen failed:')
        print(traceback.format_exc())
    except Exception:
        pass
    base.modernLoading = None

# Legacy loading background when modern UI is unavailable (init failure or PRC disabled).
# Important: ModernLoadingScreen() is truthy even when want-modern-launcher-ui is off (root is None);
# skipping legacy in that case leaves a blank (grey) window until login draws.
backgroundNodePath = None
_modern = getattr(base, 'modernLoading', None)
if not (_modern and _modern.enabled()):
    backgroundNode = tempLoader.loadSync(Filename('phase_3/models/gui/loading-background'))
    backgroundNodePath = aspect2d.attachNewNode(backgroundNode, 0)
    backgroundNodePath.setPos(0.0, 0.0, 0.0)
    # Widescreen: stretch the 4:3 loading background to cover widescreen displays.
    backgroundGuiXScale = 1.0
    try:
        backgroundGuiXScale = base.getWidescreenGUIXScale()
    except Exception:
        pass
    backgroundNodePath.setScale(render2d, VBase3(backgroundGuiXScale, 1.0, 1.0))
    backgroundNodePath.find('**/fg').setBin('fixed', 20)
    backgroundNodePath.find('**/bg').setBin('fixed', 10)

base.graphicsEngine.renderFrame()

# Optional: auto-start local servers (Astron/UberDOG/AI) before connecting.
try:
    from panda3d.core import ConfigVariableBool
    wantAutoServers = ConfigVariableBool('auto-start-local-servers', False).value
except Exception:
    wantAutoServers = False

try:
    print('ToontownStart: auto-start-local-servers = %s' % wantAutoServers)
    print('ToontownStart: local-servers-forward-logs = %s' % ConfigVariableBool('local-servers-forward-logs', True).value)
    print('ToontownStart: local-servers-always-spawn-python = %s' % ConfigVariableBool('local-servers-always-spawn-python', True).value)
except Exception:
    pass

if wantAutoServers:
    try:
        from toontown.launcher.LocalServerManager import LocalServerManager
        mgr = LocalServerManager()
        # Keep a reference for shutdown cleanup.
        try:
            base.localServerManager = mgr
        except Exception:
            pass

        def _status_cb(msg: str):
            try:
                try:
                    print('ToontownStart: LocalServers: %s' % msg)
                except Exception:
                    pass
                if getattr(base, 'modernLoading', None):
                    base.modernLoading.set_status(msg)
                    base.modernLoading.set_progress(18)
                    base.graphicsEngine.renderFrame()
            except Exception:
                pass

        if getattr(base, 'modernLoading', None):
            base.modernLoading.set_status('Booting local servers…')
            base.modernLoading.set_progress(12)
            base.graphicsEngine.renderFrame()

        ok = mgr.start_if_needed(status_cb=_status_cb)
        if not ok:
            # Give the user a readable status before connection attempts.
            if getattr(base, 'modernLoading', None):
                base.modernLoading.set_status('Server not ready yet… retrying shortly')
                base.modernLoading.set_progress(18)
                base.graphicsEngine.renderFrame()
            time.sleep(1.0)

        if getattr(base, 'modernLoading', None):
            base.modernLoading.set_status('Connecting…')
            base.modernLoading.set_progress(26)
            base.graphicsEngine.renderFrame()
    except Exception:
        try:
            import traceback
            print('ToontownStart: ERROR starting local servers:')
            print(traceback.format_exc())
        except Exception:
            pass
DirectGuiGlobals.setDefaultRolloverSound(base.loader.loadSfx('phase_3/audio/sfx/GUI_rollover.ogg'))
DirectGuiGlobals.setDefaultClickSound(base.loader.loadSfx('phase_3/audio/sfx/GUI_create_toon_fwd.ogg'))
DirectGuiGlobals.setDefaultDialogGeom(loader.loadModel('phase_3/models/gui/dialog_box_gui'))
from . import TTLocalizer
from otp.otpbase import OTPGlobals
OTPGlobals.setDefaultProductPrefix(TTLocalizer.ProductPrefix)
if base.musicManagerIsValid:
    music = base.musicManager.getSound('phase_3/audio/bgm/tt_theme.ogg')
    if music:
        music.setLoop(1)
        music.setVolume(0.9)
        music.play()

    print('ToontownStart: Loading default gui sounds')
    DirectGuiGlobals.setDefaultRolloverSound(base.loader.loadSfx('phase_3/audio/sfx/GUI_rollover.ogg'))
    DirectGuiGlobals.setDefaultClickSound(base.loader.loadSfx('phase_3/audio/sfx/GUI_create_toon_fwd.ogg'))
else:
    music = None

from direct.gui.DirectGui import OnscreenText
serverVersion = ConfigVariableString('server-version', 'no_version_set').value
print('ToontownStart: serverVersion: ', serverVersion)

# Pin the version text to the left edge of the screen (works in any aspect ratio)
versionX = -1.3
try:
    versionX = base.a2dLeft + 0.033  # same distance from the left edge as -1.3 at 4:3
except Exception:
    pass
version = OnscreenText(serverVersion, pos=(versionX, -0.975), scale=0.06, fg=Vec4(0, 0, 1, 0.6), align=TextNode.ALeft)
try:
    if getattr(base, 'modernLoading', None):
        base.modernLoading.set_status('Loading client repository…')
        base.modernLoading.set_progress(38)
        base.graphicsEngine.renderFrame()
except Exception:
    pass
# Progress range: six `loader.loadModel` calls in initNametagGlobals (ToonBase).
loader.beginBulkLoad('init', TTLocalizer.LoaderLabel, 6, 0, TTLocalizer.TIP_NONE)

from toontown.distributed.ToontownClientRepository import ToontownClientRepository
cr = ToontownClientRepository(serverVersion, launcher)
cr.music = music
del music
base.initNametagGlobals()
base.cr = cr
loader.endBulkLoad('init')
from otp.distributed.OtpDoGlobals import OTP_DO_ID_FRIEND_MANAGER
cr.generateGlobalObject(OTP_DO_ID_FRIEND_MANAGER, 'FriendManager')
if not launcher.isDummy():
    base.startShow(cr, launcher.getGameServer())
else:
    base.startShow(cr)

if backgroundNodePath is not None:
    backgroundNodePath.reparentTo(hidden)
    backgroundNodePath.removeNode()
    del backgroundNodePath
try:
    del backgroundNode
except Exception:
    pass
del tempLoader
version.cleanup()
del version
builtins.loader = base.loader
autoRun = ConfigVariableBool('toontown-auto-run', 1)
if autoRun and launcher.isDummy() and (not Thread.isTrueThreads() or __name__ == '__main__'):
    try:
        base.run()
    except SystemExit:
        raise
    except:
        from otp.otpbase import PythonUtil
        print(PythonUtil.describeException())
        raise
