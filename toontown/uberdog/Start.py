"""
Start the Toontown UberDog (Uber Distributed Object Globals server).
"""

from panda3d.core import loadPrcFile

# TODO: use argparse for this?
configs = ('etc/Configrc.prc',)
for prc in configs:
    loadPrcFile(prc)

import builtins
from direct.task.Task import Task

class game:
    name = "uberDog"
    process = "server"
builtins.game = game()

import time
import os
import sys

if os.getenv('TTMODELS'):
    from pandac.PandaModules import getModelPath, Filename
    # In the publish environment, TTMODELS won't be on the model
    # path by default, so we always add it there.  In the dev
    # environment, it'll be on the model path already, but it
    # doesn't hurt to add it again.
    getModelPath().appendDirectory(Filename.expandFrom("$TTMODELS/built"))

from direct.showbase.PythonUtil import *
from otp.uberdog.UberDogGlobal import *
from toontown.coderedemption import TTCodeRedemptionConsts
from toontown.uberdog.ToontownUberDog import ToontownUberDog
from toontown.uberdog import PartiesUdConfig

print("Initializing the Toontown UberDog (Uber Distributed Object Globals server)...")

uber.mdip = uber.config.GetString("msg-director-ip", "127.0.0.1")
uber.mdport = uber.config.GetInt("msg-director-port", 6666)

uber.esip = uber.config.GetString("event-server-ip", "127.0.0.1")
uber.esport = uber.config.GetInt("event-server-port", 4343)

stateServerId = uber.config.GetInt("state-server-id", 20100000)

uber.objectNames = set(os.getenv("uberdog_objects", "").split())

minChannel = uber.config.GetInt("uberdog-min-channel", 200400000)
maxChannel = uber.config.GetInt("uberdog-max-channel", 200449999)

uber.sbNSHost = uber.config.GetString("sb-host","")
uber.sbNSPort = uber.config.GetInt("sb-port",6053)
uber.sbListenPort = 6060
uber.clHost = "127.0.0.1"
uber.clPort = 9090
uber.allowUnfilteredChat = uber.config.GetInt("allow-unfiltered-chat",0)
uber.bwDictPath = ""

uber.RATManagerHTTPListenPort = uber.config.GetInt("rat-port",8080)
uber.awardManagerHTTPListenPort = uber.config.GetInt("award-port",8888)
uber.inGameNewsMgrHTTPListenPort = uber.config.GetInt("in-game-news-port",8889)
uber.mysqlhost = uber.config.GetString("mysql-host", PartiesUdConfig.ttDbHost)


uber.codeRedemptionMgrHTTPListenPort = uber.config.GetInt('code-redemption-port', 8998)
uber.crDbName = uber.config.GetString("tt-code-db-name", TTCodeRedemptionConsts.DefaultDbName)

uber.cpuInfoMgrHTTPListenPort = uber.config.GetInt("security_ban_mgr_port",8892)

uber.air = ToontownUberDog(
        uber.mdip, uber.mdport,
        uber.esip, uber.esport,
        None,
        stateServerId,
        minChannel,
        maxChannel)

# How we let the world know we are not running a service
uber.aiService = 0

uber.wantEmbeddedOtpServer = uber.config.GetInt(
    "toontown-uberdog-want-embedded-otp-server", 0)
if uber.wantEmbeddedOtpServer:
    otpServerPath = uber.config.GetString(
        "toontown-uberdog-otp-server-path", "c:/toonsrv")
    sys.path.append(otpServerPath)

    import otp_server_py
    if not otp_server_py.serverInit(otpServerPath):
       sys.exit(1)

    def ServerYield(task):
        otp_server_py.serverLoop()
        return Task.cont

    uber.taskMgr.add(ServerYield, 'serverYield')
    __builtins__["otpServer"] = otp_server_py


try:
    run()
except:
    info = describeException()
    #uber.air.writeServerEvent('uberdog-exception', districtNumber, info)
    raise

