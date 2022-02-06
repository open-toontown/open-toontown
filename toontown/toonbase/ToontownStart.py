import builtins

class game:
    name = 'toontown'
    process = 'client'


builtins.game = game()
from panda3d.core import *
import time
import sys
try:
    launcher
except:
    if __debug__:
        loadPrcFile('etc/Configrc.prc')

    from toontown.launcher.ToontownDummyLauncher import ToontownDummyLauncher
    launcher = ToontownDummyLauncher()
    builtins.launcher = launcher

launcher.setRegistry('EXIT_PAGE', 'normal')
pollingDelay = 0.5
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
backgroundNode = tempLoader.loadSync(Filename('phase_3/models/gui/loading-background'))
from direct.gui import DirectGuiGlobals
print('ToontownStart: setting default font')
from . import ToontownGlobals
DirectGuiGlobals.setDefaultFontFunc(ToontownGlobals.getInterfaceFont)
launcher.setPandaErrorCode(7)
from . import ToonBase
ToonBase.ToonBase()
if base.win == None:
    print('Unable to open window; aborting.')
    sys.exit()
launcher.setPandaErrorCode(0)
launcher.setPandaWindowOpen()
ConfigVariableDouble('decompressor-step-time').setValue(0.01)
ConfigVariableDouble('extractor-step-time').setValue(0.01)
backgroundNodePath = aspect2d.attachNewNode(backgroundNode, 0)
backgroundNodePath.setPos(0.0, 0.0, 0.0)
backgroundNodePath.setScale(render2d, VBase3(1))
backgroundNodePath.find('**/fg').setBin('fixed', 20)
backgroundNodePath.find('**/bg').setBin('fixed', 10)
base.graphicsEngine.renderFrame()
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
from direct.gui.DirectGui import *
serverVersion = ConfigVariableString('server-version', 'no_version_set').value
print('ToontownStart: serverVersion: ', serverVersion)
version = OnscreenText(serverVersion, pos=(-1.3, -0.975), scale=0.06, fg=Vec4(0, 0, 1, 0.6), align=TextNode.ALeft)
loader.beginBulkLoad('init', TTLocalizer.LoaderLabel, 138, 0, TTLocalizer.TIP_NONE)
from .ToonBaseGlobal import *
from direct.showbase.MessengerGlobal import *
from toontown.distributed import ToontownClientRepository
cr = ToontownClientRepository.ToontownClientRepository(serverVersion, launcher)
cr.music = music
del music
base.initNametagGlobals()
base.cr = cr
loader.endBulkLoad('init')
from otp.distributed.OtpDoGlobals import *
cr.generateGlobalObject(OTP_DO_ID_FRIEND_MANAGER, 'FriendManager')
if not launcher.isDummy():
    base.startShow(cr, launcher.getGameServer())
else:
    base.startShow(cr)
backgroundNodePath.reparentTo(hidden)
backgroundNodePath.removeNode()
del backgroundNodePath
del backgroundNode
del tempLoader
version.cleanup()
del version
base.loader = base.loader
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
