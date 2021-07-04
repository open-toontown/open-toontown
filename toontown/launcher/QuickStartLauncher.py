if __debug__:
    from panda3d.core import loadPrcFile
    loadPrcFile('etc/Configrc.prc')
else:
    import sys
    sys.path = ['']

from toontown.launcher.QuickLauncher import QuickLauncher
launcher = QuickLauncher()
launcher.notify.info('Reached end of StartQuickLauncher.py.')
