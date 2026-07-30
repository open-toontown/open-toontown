from panda3d.core import *
import builtins

import argparse

parser = argparse.ArgumentParser(description='Open Toontown - AI Server')
parser.add_argument('--base-channel', help='The base channel that the server will use.')
parser.add_argument('--max-channels', help='The number of channels that the server will be able to use.')
parser.add_argument('--stateserver', help='The control channel of this AI\'s designated State Server.')
parser.add_argument('--district-name', help='The name of the district on this AI server.')
parser.add_argument('--messagedirector-ip',
                    help='The IP address of the Message Director that this AI will connect to.')
parser.add_argument('--eventlogger-ip', help='The IP address of the Astron Event Logger that this AI will log to.')
parser.add_argument('config', nargs='*', default=['etc/Configrc.prc'],
                    help='PRC file(s) that will be loaded on this AI instance.')
args = parser.parse_args()

for prc in args.config:
    loadPrcFile(prc)

localConfig = ''
if args.base_channel:
    localConfig += 'air-base-channel %s\n' % args.base_channel
if args.max_channels:
    localConfig += 'air-channel-allocation %s\n' % args.max_channels
if args.stateserver:
    localConfig += 'air-stateserver %s\n' % args.stateserver
if args.district_name:
    localConfig += 'district-name %s\n' % args.district_name
if args.messagedirector_ip:
    localConfig += 'air-connect %s\n' % args.messagedirector_ip
if args.eventlogger_ip:
    localConfig += 'eventlog-host %s\n' % args.eventlogger_ip

loadPrcFileData('AI Args Config', localConfig)

class game:
    name = 'toontown'
    process = 'server'

builtins.game = game

from otp.ai.AIBaseGlobal import *
from toontown.ai.ToontownAIRepository import ToontownAIRepository
from toontown.toonbase import TTLocalizer

simbase.air = ToontownAIRepository(ConfigVariableInt('air-base-channel', 401000000).value, ConfigVariableInt('air-stateserver', 4002).value, ConfigVariableString('district-name', TTLocalizer.AIStartDefaultDistrict).value)

host = ConfigVariableString('air-connect', '127.0.0.1:7199').value
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
