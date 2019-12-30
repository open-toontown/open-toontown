from direct.showbase.ShowBase import ShowBase
from pandac.PandaModules import Camera, TPLow, VBase4, ColorWriteAttrib, Filename, getModelPath, NodePath
from . import OTPRender
import time
import math
import re

class OTPBase(ShowBase):

    def __init__(self, windowType = None):
        self.wantEnviroDR = False
        ShowBase.__init__(self, windowType=windowType)
        if config.GetBool('want-phase-checker', 0):
            from direct.showbase import Loader
            Loader.phaseChecker = self.loaderPhaseChecker
            self.errorAccumulatorBuffer = ''
            taskMgr.add(self.delayedErrorCheck, 'delayedErrorCheck', priority=10000)
        self.idTags = config.GetBool('want-id-tags', 0)
        if not self.idTags:
            del self.idTags
        self.wantNametags = self.config.GetBool('want-nametags', 1)
        self.slowCloseShard = self.config.GetBool('slow-close-shard', 0)
        self.slowCloseShardDelay = self.config.GetFloat('slow-close-shard-delay', 10.0)
        self.fillShardsToIdealPop = self.config.GetBool('fill-shards-to-ideal-pop', 1)
        self.logPrivateInfo = self.config.GetBool('log-private-info', __dev__)
        self.wantDynamicShadows = 1
        self.stereoEnabled = False
        self.enviroDR = None
        self.enviroCam = None
        self.pixelZoomSetup = False
        self.gameOptionsCode = ''
        self.locationCode = ''
        self.locationCodeChanged = time.time()
        if base.cam:
            if self.wantEnviroDR:
                base.cam.node().setCameraMask(OTPRender.MainCameraBitmask)
            else:
                base.cam.node().setCameraMask(OTPRender.MainCameraBitmask | OTPRender.EnviroCameraBitmask)
        taskMgr.setupTaskChain('net')
        return

    def setTaskChainNetThreaded(self):
        if base.config.GetBool('want-threaded-network', 0):
            taskMgr.setupTaskChain('net', numThreads=1, frameBudget=0.001, threadPriority=TPLow)

    def setTaskChainNetNonthreaded(self):
        taskMgr.setupTaskChain('net', numThreads=0, frameBudget=-1)

    def toggleStereo(self):
        self.stereoEnabled = not self.stereoEnabled
        if self.stereoEnabled:
            if not base.win.isStereo():
                base.win.setRedBlueStereo(True, ColorWriteAttrib.CRed, ColorWriteAttrib.CGreen | ColorWriteAttrib.CBlue)
        if self.wantEnviroDR:
            self.setupEnviroCamera()
            return
        mainDR = base.camNode.getDisplayRegion(0)
        if self.stereoEnabled:
            if not mainDR.isStereo():
                base.win.removeDisplayRegion(mainDR)
                mainDR = base.win.makeStereoDisplayRegion()
                mainDR.getRightEye().setClearDepthActive(True)
                mainDR.setCamera(base.cam)
        elif mainDR.isStereo():
            base.win.removeDisplayRegion(mainDR)
            mainDR = base.win.makeMonoDisplayRegion()
            mainDR.setCamera(base.cam)

    def setupEnviroCamera(self):
        clearColor = VBase4(0, 0, 0, 1)
        if self.enviroDR:
            clearColor = self.enviroDR.getClearColor()
            self.win.removeDisplayRegion(self.enviroDR)
        if not self.enviroCam:
            self.enviroCam = self.cam.attachNewNode(Camera('enviroCam'))
        mainDR = self.camNode.getDisplayRegion(0)
        if self.stereoEnabled:
            self.enviroDR = self.win.makeStereoDisplayRegion()
            if not mainDR.isStereo():
                self.win.removeDisplayRegion(mainDR)
                mainDR = self.win.makeStereoDisplayRegion()
                mainDR.setCamera(self.cam)
            ml = mainDR.getLeftEye()
            mr = mainDR.getRightEye()
            el = self.enviroDR.getLeftEye()
            er = self.enviroDR.getRightEye()
            el.setSort(-8)
            ml.setSort(-6)
            er.setSort(-4)
            er.setClearDepthActive(True)
            mr.setSort(-2)
            mr.setClearDepthActive(False)
        else:
            self.enviroDR = self.win.makeMonoDisplayRegion()
            if mainDR.isStereo():
                self.win.removeDisplayRegion(mainDR)
                mainDR = self.win.makeMonoDisplayRegion()
                mainDR.setCamera(self.cam)
            self.enviroDR.setSort(-10)
        self.enviroDR.setClearColor(clearColor)
        self.win.setClearColor(clearColor)
        self.enviroDR.setCamera(self.enviroCam)
        self.enviroCamNode = self.enviroCam.node()
        self.enviroCamNode.setLens(self.cam.node().getLens())
        self.enviroCamNode.setCameraMask(OTPRender.EnviroCameraBitmask)
        render.hide(OTPRender.EnviroCameraBitmask)
        self.camList.append(self.enviroCam)
        self.backgroundDrawable = self.enviroDR
        self.enviroDR.setTextureReloadPriority(-10)
        if self.pixelZoomSetup:
            self.setupAutoPixelZoom()

    def setupAutoPixelZoom(self):
        self.win.setPixelZoom(1)
        self.enviroDR.setPixelZoom(1)
        if not self.stereoEnabled:
            self.enviroDR.setClearColorActive(True)
            self.enviroDR.setClearDepthActive(True)
            self.win.setClearColorActive(False)
            self.win.setClearDepthActive(False)
            self.backgroundDrawable = self.enviroDR
        else:
            self.enviroDR.setClearColorActive(False)
            self.enviroDR.setClearDepthActive(False)
            self.enviroDR.getRightEye().setClearDepthActive(True)
            self.win.setClearColorActive(True)
            self.win.setClearDepthActive(True)
            self.backgroundDrawable = self.win
        self.pixelZoomSetup = True
        self.targetPixelZoom = 1.0
        self.pixelZoomTask = None
        self.pixelZoomCamHistory = 2.0
        self.pixelZoomCamMovedList = []
        self.pixelZoomStarted = None
        flag = self.config.GetBool('enable-pixel-zoom', True)
        self.enablePixelZoom(flag)
        return

    def enablePixelZoom(self, flag):
        if not self.backgroundDrawable.supportsPixelZoom():
            flag = False
        self.pixelZoomEnabled = flag
        taskMgr.remove('chasePixelZoom')
        if flag:
            taskMgr.add(self.__chasePixelZoom, 'chasePixelZoom', priority=-52)
        else:
            self.backgroundDrawable.setPixelZoom(1)

    def __chasePixelZoom(self, task):
        now = globalClock.getFrameTime()
        pos = base.cam.getNetTransform().getPos()
        prevPos = base.cam.getNetPrevTransform().getPos()
        d2 = (pos - prevPos).lengthSquared()
        if d2:
            d = math.sqrt(d2)
            self.pixelZoomCamMovedList.append((now, d))
        while self.pixelZoomCamMovedList and self.pixelZoomCamMovedList[0][0] < now - self.pixelZoomCamHistory:
            del self.pixelZoomCamMovedList[0]

        dist = sum([pair[1] for pair in self.pixelZoomCamMovedList])
        speed = dist / self.pixelZoomCamHistory
        if speed < 5:
            self.backgroundDrawable.setPixelZoom(4)
            self.pixelZoomStart = None
        elif speed > 10:
            if self.pixelZoomStart == None:
                self.pixelZoomStart = now
            elapsed = now - self.pixelZoomStart
            if elapsed > 10:
                self.backgroundDrawable.setPixelZoom(16)
            elif elapsed > 5:
                self.backgroundDrawable.setPixelZoom(8)
        return task.cont

    def getShardPopLimits(self):
        return (300, 600, 1200)

    def setLocationCode(self, locationCode):
        if locationCode != self.locationCode:
            self.locationCode = locationCode
            self.locationCodeChanged = time.time()

    def delayedErrorCheck(self, task):
        if self.errorAccumulatorBuffer:
            buffer = self.errorAccumulatorBuffer
            self.errorAccumulatorBuffer = ''
            self.notify.error('\nAccumulated Phase Errors!:\n %s' % buffer)
        return task.cont

    def loaderPhaseChecker(self, path, loaderOptions):
        if 'audio/' in path:
            return 1
        file = Filename(path)
        if not file.getExtension():
            file.setExtension('bam')
        mp = getModelPath()
        path = mp.findFile(file).cStr()
        if not path:
            return
        match = re.match('.*phase_([^/]+)/', path)
        if not match:
            if 'dmodels' in path:
                return
            else:
                self.errorAccumulatorBuffer += 'file not in phase (%s, %s)\n' % (file, path)
                return
        basePhase = float(match.groups()[0])
        if not launcher.getPhaseComplete(basePhase):
            self.errorAccumulatorBuffer += 'phase is not loaded for this model %s\n' % path
        model = loader.loader.loadSync(Filename(path), loaderOptions)
        if model:
            model = NodePath(model)
            for tex in model.findAllTextures():
                texPath = tex.getFullpath().cStr()
                match = re.match('.*phase_([^/]+)/', texPath)
                if match:
                    texPhase = float(match.groups()[0])
                    if texPhase > basePhase:
                        self.errorAccumulatorBuffer += 'texture phase is higher than the models (%s, %s)\n' % (path, texPath)

    def getRepository(self):
        return self.cr

    def openMainWindow(self, *args, **kw):
        result = ShowBase.openMainWindow(self, *args, **kw)
        if result:
            self.wantEnviroDR = not self.win.getGsg().isHardware() or config.GetBool('want-background-region', 1)
            self.backgroundDrawable = self.win
        return result
