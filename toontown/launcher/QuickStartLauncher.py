from panda3d.core import *
if __debug__:
    loadPrcFile('etc/Configrc.prc')
else:
    import sys
    sys.path = ['']
from toontown.launcher.QuickLauncher import QuickLauncher
launcher = QuickLauncher()
launcher.notify.info('Reached end of StartQuickLauncher.py.')
