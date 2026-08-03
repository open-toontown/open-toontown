if __debug__:
    import os
    from panda3d.core import loadPrcFile, loadPrcFileData, Filename
    loadPrcFile('etc/Configrc.prc')
    # Optional local overrides (shard-debug, notify levels, etc.); not loaded automatically before.
    _devPrc = os.path.join('etc', 'Configrc_dev.prc')
    if os.path.isfile(_devPrc):
        loadPrcFile(_devPrc)

    # Test-harness injection: the MCP test server writes a generated PRC file
    # (auto-login, auto-avatar-choice, MCP bridge, window size, etc.) and points
    # TTBTN_EXTRA_PRC at it. Loaded last so it wins over the default config.
    _extraPrc = os.environ.get('TTBTN_EXTRA_PRC', '')
    if _extraPrc:
        # loadPrcFile needs a Unix-style path even on Windows.
        _extraPrcFilename = Filename.fromOsSpecific(_extraPrc)
        if os.path.isfile(_extraPrc):
            print('QuickStartLauncher: loading extra PRC %s' % _extraPrc)
            loadPrcFile(_extraPrcFilename)
        else:
            print('QuickStartLauncher: TTBTN_EXTRA_PRC set but file missing: %s' % _extraPrc)

    # Freeze-capture mode: set env var TTBTN_FREEZE_CAPTURE=1 before launch.
    # This turns on shard flow breadcrumbs + watchdog stack dumps without
    # requiring any local PRC override files to be present/loaded.
    if os.environ.get('TTBTN_FREEZE_CAPTURE') == '1':
        loadPrcFileData('', '\n'.join([
            'shard-debug 1',
            'eventmanager-debug-flood 1',
            'eventmanager-drain-on-flood 1',
            # force-setzone-done is a last-resort escape hatch; leave it off
            # for normal testing now that interests are completing.
            'default-directnotify-level info',
            'notify-level-OTPClientRepository info',
        ]))
else:
    import sys
    sys.path = ['']

from toontown.launcher.QuickLauncher import QuickLauncher
launcher = QuickLauncher()
launcher.notify.info('Reached end of StartQuickLauncher.py.')
