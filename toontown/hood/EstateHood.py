from pandac.PandaModules import *
from toontown.toonbase.ToonBaseGlobal import *
from toontown.toonbase.ToontownGlobals import *
from toontown.distributed.ToontownMsgTypes import *
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from toontown.minigame import Purchase
from otp.avatar import DistributedAvatar
from . import SkyUtil
from direct.task.Task import Task
from . import Hood
from toontown.estate import EstateLoader
from toontown.estate import HouseGlobals
from . import ZoneUtil

class EstateHood(Hood.Hood):
    notify = DirectNotifyGlobal.directNotify.newCategory('EstateHood')

    def __init__(self, parentFSM, doneEvent, dnaStore, hoodId):
        Hood.Hood.__init__(self, parentFSM, doneEvent, dnaStore, hoodId)
        self.fsm = ClassicFSM.ClassicFSM('Hood', [State.State('start', self.enterStart, self.exitStart, ['safeZoneLoader']),
         State.State('safeZoneLoader', self.enterSafeZoneLoader, self.exitSafeZoneLoader, ['quietZone']),
         State.State('quietZone', self.enterQuietZone, self.exitQuietZone, ['safeZoneLoader']),
         State.State('final', self.enterFinal, self.exitFinal, [])], 'start', 'final')
        self.fsm.enterInitialState()
        self.id = MyEstate
        self.safeZoneLoaderClass = EstateLoader.EstateLoader
        self.storageDNAFile = 'phase_5.5/dna/storage_estate.dna'
        self.holidayStorageDNADict = {WINTER_DECORATIONS: ['phase_5.5/dna/winter_storage_estate.dna'],
         WACKY_WINTER_DECORATIONS: ['phase_5.5/dna/winter_storage_estate.dna'],
         HALLOWEEN_PROPS: ['phase_5.5/dna/halloween_props_storage_estate.dna'],
         SPOOKY_PROPS: ['phase_5.5/dna/halloween_props_storage_estate.dna']}
        self.skyFile = 'phase_3.5/models/props/TT_sky'
        self.spookySkyFile = 'phase_3.5/models/props/BR_sky'
        self.popupInfo = None
        return

    def load(self):
        Hood.Hood.load(self)

    def unload(self):
        del self.safeZoneLoaderClass
        if self.popupInfo:
            self.popupInfo.destroy()
            self.popupInfo = None
        Hood.Hood.unload(self)
        return

    def enter(self, requestStatus):
        hoodId = requestStatus['hoodId']
        zoneId = requestStatus['zoneId']
        self.accept('kickToPlayground', self.kickToPlayground)
        self.fsm.request(requestStatus['loader'], [requestStatus])

    def exit(self):
        if self.loader:
            self.loader.exit()
            self.loader.unload()
            del self.loader
        Hood.Hood.exit(self)

    def loadLoader(self, requestStatus):
        loaderName = requestStatus['loader']
        if loaderName == 'safeZoneLoader':
            self.loader = self.safeZoneLoaderClass(self, self.fsm.getStateNamed('safeZoneLoader'), self.loaderDoneEvent)
            self.loader.load()

    def spawnTitleText(self, zoneId):
        pass

    def hideTitleTextTask(self, task):
        return Task.done

    def kickToPlayground(self, retCode):
        if retCode == 0:
            msg = TTLocalizer.EstateOwnerLeftMessage % HouseGlobals.BOOT_GRACE_PERIOD
            self.__popupKickoutMessage(msg)
        elif retCode == 1:
            zoneId = base.localAvatar.lastHood
            self.doneStatus = {'loader': ZoneUtil.getBranchLoaderName(zoneId),
             'where': ZoneUtil.getToonWhereName(zoneId),
             'how': 'teleportIn',
             'hoodId': zoneId,
             'zoneId': zoneId,
             'shardId': None,
             'avId': -1}
            messenger.send(self.doneEvent)
        elif retCode == 2:
            zoneId = base.localAvatar.lastHood
            self.doneStatus = {'loader': ZoneUtil.getBranchLoaderName(zoneId),
             'where': ZoneUtil.getToonWhereName(zoneId),
             'how': 'teleportIn',
             'hoodId': zoneId,
             'zoneId': zoneId,
             'shardId': None,
             'avId': -1}
            messenger.send(self.doneEvent)
        else:
            self.notify.error('unknown reason for exiting estate')
        return

    def __popupKickoutMessage(self, msg):
        if self.popupInfo != None:
            self.popupInfo.destroy()
            self.popupInfo = None
        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        okButtonImage = (buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr'))
        self.popupInfo = DirectFrame(parent=hidden, relief=None, state='normal', text=msg, frameSize=(-1, 1, -1, 1), text_wordwrap=10, geom=DGG.getDefaultDialogGeom(), geom_color=GlobalDialogColor, geom_scale=(0.88, 1, 0.75), geom_pos=(0, 0, -.08), text_scale=TTLocalizer.EHpopupInfo, text_pos=(0, 0.1))
        DirectButton(self.popupInfo, image=okButtonImage, relief=None, text=TTLocalizer.EstatePopupOK, text_scale=0.05, text_pos=(0.0, -0.1), textMayChange=0, pos=(0.0, 0.0, -0.3), command=self.__handleKickoutOk)
        buttons.removeNode()
        self.popupInfo.reparentTo(aspect2d)
        return

    def __handleKickoutOk(self):
        self.popupInfo.reparentTo(hidden)

    def skyTrack(self, task):
        return SkyUtil.cloudSkyTrack(task)

    def startSky(self):
        if not self.sky.getTag('sky') == 'Regular':
            self.endSpookySky()
        SkyUtil.startCloudSky(self)
        if base.cloudPlatformsEnabled:
            self.loader.startCloudPlatforms()

    def stopSky(self):
        Hood.Hood.stopSky(self)
        self.loader.stopCloudPlatforms()

    def startSpookySky(self):
        if hasattr(self, 'loader') and self.loader and hasattr(self.loader, 'cloudTrack') and self.loader.cloudTrack:
            self.stopSky()
        self.sky = loader.loadModel(self.spookySkyFile)
        self.sky.setTag('sky', 'Halloween')
        self.sky.setScale(1.0)
        self.sky.setDepthTest(0)
        self.sky.setDepthWrite(0)
        self.sky.setColor(0.5, 0.5, 0.5, 1)
        self.sky.setBin('background', 100)
        self.sky.setFogOff()
        self.sky.reparentTo(camera)
        self.sky.setTransparency(TransparencyAttrib.MDual, 1)
        fadeIn = self.sky.colorScaleInterval(1.5, Vec4(1, 1, 1, 1), startColorScale=Vec4(1, 1, 1, 0.25), blendType='easeInOut')
        fadeIn.start()
        self.sky.setZ(0.0)
        self.sky.setHpr(0.0, 0.0, 0.0)
        ce = CompassEffect.make(NodePath(), CompassEffect.PRot | CompassEffect.PZ)
        self.sky.node().setEffect(ce)
