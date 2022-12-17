from panda3d.core import loadPrcFile

# TODO: use argparse for this?
configs = ('etc/Configrc.prc',)
for prc in configs:
    loadPrcFile(prc)

import builtins

class game:
    name = "toontown"
    process = "ai"
builtins.game = game()

# NOTE: this file is not used in production. See AIServiceStart.py

import os
import sys

print("Initializing...")

from otp.ai.AIBaseGlobal import *
from . import ToontownAIRepository
from otp.otpbase import PythonUtil

# Clear the default model extension for AI developers, so they'll know
# when they screw up and omit it.
from panda3d.core import loadPrcFileData
loadPrcFileData("AIStart.py", "default-model-extension")

simbase.mdip = simbase.config.GetString("msg-director-ip", "127.0.0.1")

# Now the AI connects directly to the state server instead of the msg director
simbase.mdport = simbase.config.GetInt("msg-director-port", 6666)

simbase.esip = simbase.config.GetString("event-server-ip", "127.0.0.1")
simbase.esport = simbase.config.GetInt("event-server-port", 4343)


districtType = 0
serverId = simbase.config.GetInt("district-ssid", 20100000)

for i in range(1, 20+1):
    # always set up for i==1, then take the first district above 1 (if any)
    if i==1 or os.getenv("want_district_%s" % i):
        if i==1:
            postfix = ''
        else:
            postfix = '-%s' % i
        districtNumber = simbase.config.GetInt(
            "district-id%s"%postfix,
            200000000 + i*1000000)
        districtName = simbase.config.GetString(
            "district-name%s"%postfix,
            "%sville" % {1: 'Silly',
                         2: 'Second',
                         3: 'Third',
                         4: 'Fourth',
                         5: 'Fifth',
                         6: 'Sixth',
                         7: 'Seventh',
                         8: 'Eighth',
                         9: 'Ninth', }.get(i, str(i))
                         )
        districtMinChannel = simbase.config.GetInt(
            "district-min-channel%s"%postfix,
            200100000 + i*1000000)
        districtMaxChannel = simbase.config.GetInt(
            "district-max-channel%s"%postfix,
            200149999 + i*1000000)
        if i != 1:
            break

print("-"*30, "creating toontown district %s" % districtNumber, "-"*30)

simbase.air = ToontownAIRepository.ToontownAIRepository(
        simbase.mdip,
        simbase.mdport,
        simbase.esip,
        simbase.esport,
        None,
        districtNumber,
        districtName,
        districtType,
        serverId,
        districtMinChannel,
        districtMaxChannel)

# How we let the world know we are not running a service
simbase.aiService = 0

try:
    simbase.air.fsm.request("districtReset")        
    run()
except:
    info = PythonUtil.describeException()
    simbase.air.writeServerEvent('ai-exception', districtNumber, info)
    raise
    
