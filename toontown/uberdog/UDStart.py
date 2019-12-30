import builtins


class game:
    name = 'uberDog'
    process = 'server'


builtins.game = game

from panda3d.core import *

loadPrcFile('etc/Configrc.prc')

from otp.ai.AIBaseGlobal import *
from toontown.uberdog.ToontownUDRepository import ToontownUDRepository

udConfig = ''
udConfig += 'air-base-channel %s\n' % 1000000
udConfig += 'air-channel-allocation %s\n' % 999999
udConfig += 'air-stateserver %s\n' % 4002
udConfig += 'air-connect %s\n' % '127.0.0.1:7199'
udConfig += 'eventlog-host %s\n' % '127.0.0.1:7197'
loadPrcFileData('UberDOG Config', udConfig)

simbase.air = ToontownUDRepository(config.GetInt('air-base-channel', 1000000), config.GetInt('air-stateserver', 4002))

host = config.GetString('air-connect', '127.0.0.1:7199')
port = 7199
if ':' in host:
    host, port = host.split(':', 1)
    port = int(port)

simbase.air.connect(host, port)

try:
    run()
except SystemExit:
    raise
except Exception:
    from otp.otpbase import PythonUtil
    print(PythonUtil.describeException())
    raise
