from pandac.PandaModules import *
from direct.showbase import GarbageReport, ContainerReport, MessengerLeakDetector
from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from direct.showbase.InputStateGlobal import inputState
from otp.otpbase.ObjectCount import ObjectCount
from direct.task import Task
from direct.task.TaskProfiler import TaskProfiler
from otp.avatar import Avatar
import string
from direct.showbase import PythonUtil
from direct.showbase.PythonUtil import Functor, DelayedCall, ScratchPad
from otp.otpbase import OTPGlobals
from direct.distributed.ClockDelta import *
from direct.showutil.TexViewer import TexViewer

class MagicWordManager(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('MagicWordManager')
    neverDisable = 1
    GameAvatarClass = None

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        self.shownFontNode = None
        self.csShown = 0
        self.guiPopupShown = 0
        self.texViewer = None
        return

    def generate(self):
        DistributedObject.DistributedObject.generate(self)
        self.accept('magicWord', self.b_setMagicWord)
        self.autoMagicWordEvent = localAvatar.getArrivedOnDistrictEvent()
        if localAvatar.isGeneratedOnDistrict():
            self.doLoginMagicWords()
        else:
            self.accept(self.autoMagicWordEvent, self.doLoginMagicWords)

    def doLoginMagicWords(self):
        pass

    def disable(self):
        self.ignore(self.autoMagicWordEvent)
        del self.autoMagicWordEvent
        self.ignore('magicWord')
        self.hidefont()
        DistributedObject.DistributedObject.disable(self)

    def setMagicWord(self, word, avId, zoneId):
        try:
            self.doMagicWord(word, avId, zoneId)
        except:
            response = PythonUtil.describeException(backTrace=1)
            self.notify.warning('Ignoring error in magic word:\n%s' % response)
            self.setMagicWordResponse(response)

    def wordIs(self, word, w):
        return word == w or word[:len(w) + 1] == '%s ' % w

    def getWordIs(self, word):
        return Functor(self.wordIs, word)

    def doMagicWord(self, word, avId, zoneId):
        wordIs = self.getWordIs(word)
        print(word)
        if wordIs('~oobe'):
            base.oobe()
        elif wordIs('~oobeCull'):
            base.oobeCull()
        elif wordIs('~tex'):
            self.doTex(word)
        elif wordIs('~texmem'):
            base.toggleTexMem()
        elif wordIs('~verts'):
            base.toggleShowVertices()
        elif wordIs('~wire'):
            base.toggleWireframe()
        elif wordIs('~stereo'):
            base.toggleStereo()
        elif wordIs('~showfont'):
            self.showfont(word[9:])
        elif wordIs('~hidefont'):
            self.hidefont()
        elif wordIs('~guiPopup'):
            self.toggleGuiPopup()
        elif wordIs('~showCS') or wordIs('~showcs'):
            bitmask = self.getCSBitmask(word[7:])
            render.showCS(bitmask)
            self.csShown = 1
        elif wordIs('~hideCS') or wordIs('~hidecs'):
            bitmask = self.getCSBitmask(word[7:])
            render.hideCS(bitmask)
            self.csShown = 0
        elif wordIs('~cs'):
            bitmask = self.getCSBitmask(word[3:])
            if self.csShown:
                render.hideCS(bitmask)
                self.csShown = 0
            else:
                render.showCS(bitmask)
                self.csShown = 1
        elif wordIs('~showShadowCollisions'):
            self.showShadowCollisions()
        elif wordIs('~hideShadowCollisions'):
            self.hideShadowCollisions()
        elif wordIs('~showCollisions'):
            self.showCollisions()
        elif wordIs('~hideCollisions'):
            self.hideCollisions()
        elif wordIs('~showCameraCollisions'):
            self.showCameraCollisions()
        elif wordIs('~hideCameraCollisions'):
            self.hideCameraCollisions()
        elif wordIs('~collidespam'):
            n = Notify.ptr().getCategory(':collide')
            if hasattr(self, '_collideSpamSeverity'):
                n.setSeverity(self._collideSpamSeverity)
                del self._collideSpamSeverity
            else:
                self._collideSpamSeverity = n.getSeverity()
                n.setSeverity(NSSpam)
        elif wordIs('~notify'):
            args = word.split()
            n = Notify.ptr().getCategory(args[1])
            n.setSeverity({'error': NSError,
             'warning': NSWarning,
             'info': NSInfo,
             'debug': NSDebug,
             'spam': NSSpam}[args[2]])
        elif wordIs('~stress'):
            factor = word[7:]
            if factor:
                factor = float(factor)
                LOD.setStressFactor(factor)
                response = 'Set LOD stress factor to %s' % factor
            else:
                factor = LOD.getStressFactor()
                response = 'LOD stress factor is %s' % factor
            self.setMagicWordResponse(response)
        elif wordIs('~for'):
            self.forAnother(word, avId, zoneId)
        elif wordIs('~badname'):
            word = '~for %s ~badname' % word[9:]
            print('word is %s' % word)
            self.forAnother(word, avId, zoneId)
        elif wordIs('~avId'):
            self.setMagicWordResponse(str(localAvatar.doId))
        elif wordIs('~doId'):
            name = string.strip(word[6:])
            objs = self.identifyDistributedObjects(name)
            if len(objs) == 0:
                response = '%s is unknown.' % name
            else:
                response = ''
                for name, obj in objs:
                    response += '\n%s %d' % (name, obj.doId)

                response = response[1:]
            self.setMagicWordResponse(response)
        elif wordIs('~exec'):
            from otp.chat import ChatManager
            ChatManager.ChatManager.execChat = 1
        elif wordIs('~run'):
            self.toggleRun()
        elif wordIs('~runFaster'):
            if config.GetBool('want-running', 1):
                args = word.split()
                if len(args) > 1:
                    base.debugRunningMultiplier = float(args[1])
                else:
                    base.debugRunningMultiplier = 10
                inputState.set('debugRunning', True)
        elif wordIs('~who'):
            avIds = []
            for av in Avatar.Avatar.ActiveAvatars:
                if hasattr(av, 'getFriendsList'):
                    avIds.append(av.doId)

            self.d_setWho(avIds)
        elif wordIs('~sync'):
            tm = self.cr.timeManager
            if tm == None:
                response = 'No TimeManager.'
                self.setMagicWordResponse(response)
            else:
                tm.extraSkew = 0.0
                skew = string.strip(word[5:])
                if skew != '':
                    tm.extraSkew = float(skew)
                globalClockDelta.clear()
                tm.handleHotkey()
        elif wordIs('~period'):
            timeout = string.strip(word[7:])
            if timeout != '':
                seconds = int(timeout)
                self.cr.stopPeriodTimer()
                self.cr.resetPeriodTimer(seconds)
                self.cr.startPeriodTimer()
            if self.cr.periodTimerExpired:
                response = 'Period timer has expired.'
            elif self.cr.periodTimerStarted:
                elapsed = globalClock.getFrameTime() - self.cr.periodTimerStarted
                secondsRemaining = self.cr.periodTimerSecondsRemaining - elapsed
                response = 'Period timer expires in %s seconds.' % int(secondsRemaining)
            else:
                response = 'Period timer not set.'
            self.setMagicWordResponse(response)
        elif wordIs('~DIRECT'):
            args = word.split()
            fEnableLight = 0
            if len(args) > 1:
                if direct and args[1] == 'CAM':
                    direct.enable()
                    taskMgr.removeTasksMatching('updateSmartCamera*')
                    camera.wrtReparentTo(render)
                    direct.cameraControl.enableMouseFly()
                    self.setMagicWordResponse('Enabled DIRECT camera')
                    return
                elif args[1] == 'LIGHT':
                    fEnableLight = 1
            base.startTk()
            from direct.directtools import DirectSession
            if fEnableLight:
                direct.enableLight()
            else:
                direct.enable()
            self.setMagicWordResponse('Enabled DIRECT')
        elif wordIs('~TT'):
            if not direct:
                return
            args = word.split()
            if len(args) > 1:
                if args[1] == 'CAM':
                    direct.cameraControl.disableMouseFly()
                    camera.wrtReparentTo(base.localAvatar)
                    base.localAvatar.startUpdateSmartCamera()
                    self.setMagicWordResponse('Disabled DIRECT camera')
                    return
            direct.disable()
            camera.wrtReparentTo(base.localAvatar)
            base.localAvatar.startUpdateSmartCamera()
            self.setMagicWordResponse('Disabled DIRECT')
        elif wordIs('~net'):
            if self.cr.networkPlugPulled():
                self.cr.restoreNetworkPlug()
                self.cr.startHeartbeat()
                response = 'Network restored.'
            else:
                self.cr.pullNetworkPlug()
                self.cr.stopHeartbeat()
                response = 'Network disconnected.'
            self.setMagicWordResponse(response)
        elif wordIs('~disconnect'):
            base.cr.distributedDistrict.sendUpdate('broadcastMessage')
        elif wordIs('~model'):
            args = word.split()
            path = args[1]
            model = loader.loadModel(path)
            model.reparentTo(localAvatar)
            model.wrtReparentTo(render)
            self.setMagicWordResponse('loaded %s' % path)
        elif wordIs('~axis'):
            axis = loader.loadModel('models/misc/xyzAxis.bam')
            axis.reparentTo(render)
            axis.setPos(base.localAvatar, 0, 0, 0)
            axis.setHpr(render, 0, 0, 0)
            axis10 = loader.loadModel('models/misc/xyzAxis.bam')
            axis10.reparentTo(render)
            axis10.setPos(base.localAvatar, 0, 0, 0)
            axis10.setScale(10)
            axis10.setHpr(render, 0, 0, 0)
            axis10.setColorScale(1, 1, 1, 0.4)
            axis10.setTransparency(1)
        elif wordIs('~clearAxes') or wordIs('~clearAxis'):
            render.findAllMatches('**/xyzAxis.egg').detach()
        elif wordIs('~myAxis'):
            if hasattr(self, 'myAxis'):
                self.myAxis.detachNode()
                del self.myAxis
            else:
                self.myAxis = loader.loadModel('models/misc/xyzAxis.bam')
                self.myAxis.reparentTo(localAvatar)
        elif wordIs('~osd'):
            onScreenDebug.enabled = not onScreenDebug.enabled
        elif wordIs('~osdScale'):
            args = word.split()
            defScale = 0.05
            if len(args) > 1:
                scale = float(args[1])
            else:
                scale = 1.0
            onScreenDebug.onScreenText.setScale(defScale * scale)
        elif wordIs('~osdTaskMgr'):
            if taskMgr.osdEnabled():
                taskMgr.stopOsd()
            else:
                if not onScreenDebug.enabled:
                    onScreenDebug.enabled = True
                taskMgr.startOsd()
        elif wordIs('~fps'):
            self.doFps(word, avId, zoneId)
        elif wordIs('~sleep'):
            args = word.split()
            if len(args) > 1:
                s = float(args[1])
                base.setSleep(s)
                response = 'sleeping %s' % s
            else:
                base.setSleep(0.0)
                response = 'not sleeping'
            self.setMagicWordResponse(response)
        elif wordIs('~objects'):
            args = word.split()
            from direct.showbase import ObjectReport
            report = ObjectReport.ObjectReport('client ~objects')
            if 'all' in args:
                self.notify.info('printing full object set...')
                report.getObjectPool().printObjsByType(printReferrers='ref' in args)
            if hasattr(self, 'baselineObjReport'):
                self.notify.info('calculating diff from baseline ObjectReport...')
                self.lastDiff = self.baselineObjReport.diff(report)
                self.lastDiff.printOut(full='diff' in args or 'dif' in args)
            if 'baseline' in args or not hasattr(self, 'baselineObjReport'):
                self.notify.info('recording baseline ObjectReport...')
                if hasattr(self, 'baselineObjReport'):
                    self.baselineObjReport.destroy()
                self.baselineObjReport = report
            self.setMagicWordResponse('objects logged')
        elif wordIs('~objectcount'):

            def handleObjectCountDone(objectCount):
                self.setMagicWordResponse('object count logged')

            oc = ObjectCount('~objectcount', doneCallback=handleObjectCountDone)
        elif wordIs('~objecthg'):
            import gc
            objs = gc.get_objects()
            type2count = {}
            for obj in objs:
                tn = safeTypeName(obj)
                type2count.setdefault(tn, 0)
                type2count[tn] += 1

            count2type = invertDictLossless(type2count)
            counts = list(count2type.keys())
            counts.sort()
            counts.reverse()
            for count in counts:
                print('%s: %s' % (count, count2type[count]))

            self.setMagicWordResponse('~aiobjecthg complete')
        elif wordIs('~containers'):
            args = word.split()
            limit = 30
            if 'full' in args:
                limit = None
            ContainerReport.ContainerReport('~containers', log=True, limit=limit, threaded=True)
        elif wordIs('~garbage'):
            args = word.split()
            full = 'full' in args
            safeMode = 'safe' in args
            delOnly = 'delonly' in args
            GarbageReport.GarbageLogger('~garbage', fullReport=full, threaded=True, safeMode=safeMode, delOnly=delOnly, doneCallback=self.garbageReportDone)
        elif wordIs('~guicreates'):
            base.printGuiCreates = True
            self.setMagicWordResponse('printing gui creation stacks')
        elif wordIs('~creategarbage'):
            GarbageReport._createGarbage()
        elif wordIs('~leakTask'):

            def leakTask(task):
                return task.cont

            taskMgr.add(leakTask, uniqueName('leakedTask'))
            leakTask = None
        elif wordIs('~leakmessage'):
            MessengerLeakDetector._leakMessengerObject()
            self.down_setMagicWordResponse(senderId, 'messenger leak object created')
        elif wordIs('~pstats'):
            args = word.split()
            hostname = None
            port = None
            if len(args) > 1:
                hostname = args[1]
            if len(args) > 2:
                port = int(args[2])
            base.wantStats = 1
            Task.TaskManager.pStatsTasks = 1
            result = base.createStats(hostname, port)
            connectionName = '%s' % hostname
            if port is not None:
                connectionName += ':%s' % port
            if result:
                response = 'connected client pstats to %s' % connectionName
            else:
                response = 'could not connect pstats to %s' % connectionName
            self.setMagicWordResponse(response)
        elif wordIs('~profile'):
            args = word.split()
            if len(args) > 1:
                num = int(args[1])
            else:
                num = 5
            session = taskMgr.getProfileSession('~profile')
            session.setLogAfterProfile(True)
            taskMgr.profileFrames(num, session)
            self.setMagicWordResponse('profiling %s client frames...' % num)
        elif wordIs('~frameprofile'):
            args = word.split()
            wasOn = bool(taskMgr.getProfileFrames())
            if len(args) > 1:
                setting = bool(int(args[1]))
            else:
                setting = not wasOn
            taskMgr.setProfileFrames(setting)
            self.setMagicWordResponse('frame profiling %s%s' % (choice(setting, 'ON', 'OFF'), choice(wasOn == setting, ' already', '')))
        elif wordIs('~taskprofile'):
            args = word.split()
            wasOn = bool(taskMgr.getProfileTasks())
            if len(args) > 1:
                setting = bool(int(args[1]))
            else:
                setting = not wasOn
            taskMgr.setProfileTasks(setting)
            self.setMagicWordResponse('task profiling %s%s' % (choice(setting, 'ON', 'OFF'), choice(wasOn == setting, ' already', '')))
        elif wordIs('~taskspikethreshold'):
            args = word.split()
            if len(args) > 1:
                threshold = float(args[1])
                response = 'task spike threshold set to %ss' % threshold
            else:
                threshold = TaskProfiler.GetDefaultSpikeThreshold()
                response = 'task spike threshold reset to %ss' % threshold
            TaskProfiler.SetSpikeThreshold(threshold)
            self.setMagicWordResponse(response)
        elif wordIs('~logtaskprofiles'):
            args = word.split()
            if len(args) > 1:
                name = args[1]
            else:
                name = None
            taskMgr.logTaskProfiles(name)
            response = 'logged task profiles%s' % choice(name, ' for %s' % name, '')
            self.setMagicWordResponse(response)
        elif wordIs('~taskprofileflush'):
            args = word.split()
            if len(args) > 1:
                name = args[1]
            else:
                name = None
            taskMgr.flushTaskProfiles(name)
            response = 'flushed AI task profiles%s' % choice(name, ' for %s' % name, '')
            self.setMagicWordResponse(response)
        elif wordIs('~dobjectcount'):
            base.cr.printObjectCount()
            self.setMagicWordResponse('logging client distributed object count...')
        elif wordIs('~taskmgr'):
            print(taskMgr)
            self.setMagicWordResponse('logging client taskMgr...')
        elif wordIs('~jobmgr'):
            print(jobMgr)
            self.setMagicWordResponse('logging client jobMgr...')
        elif wordIs('~jobtime'):
            args = word.split()
            if len(args) > 1:
                time = float(args[1])
            else:
                time = None
            response = ''
            if time is None:
                time = jobMgr.getDefaultTimeslice()
                response = 'reset client jobMgr timeslice to %s ms' % time
            else:
                response = 'set client jobMgr timeslice to %s ms' % time
                time = time / 1000.0
            jobMgr.setTimeslice(time)
            self.setMagicWordResponse(response)
        elif wordIs('~detectleaks'):
            started = self.cr.startLeakDetector()
            self.setMagicWordResponse(choice(started, 'leak detector started', 'leak detector already started'))
        elif wordIs('~taskthreshold'):
            args = word.split()
            if len(args) > 1.0:
                threshold = float(args[1])
            else:
                threshold = None
            response = ''
            if threshold is None:
                threshold = taskMgr.DefTaskDurationWarningThreshold
                response = 'reset task duration warning threshold to %s' % threshold
            else:
                response = 'set task duration warning threshold to %s' % threshold
            taskMgr.setTaskDurationWarningThreshold(threshold)
            self.setMagicWordResponse(response)
        elif wordIs('~messenger'):
            print(messenger)
            self.setMagicWordResponse('logging client messenger...')
        elif wordIs('~clientcrash'):
            DelayedCall(Functor(self.notify.error, '~clientcrash: simulating a client crash'))
        elif wordIs('~badDelete'):
            doId = 0
            while doId in base.cr.doId2do:
                doId += 1

            DelayedCall(Functor(base.cr.deleteObjectLocation, ScratchPad(doId=doId), 1, 1))
            self.setMagicWordResponse('doing bad delete')
        elif wordIs('~idTags'):
            messenger.send('nameTagShowAvId', [])
            base.idTags = 1
        elif wordIs('~nameTags'):
            messenger.send('nameTagShowName', [])
            base.idTags = 0
        elif wordIs('~hideNames'):
            if NametagGlobals.getMasterNametagsVisible():
                NametagGlobals.setMasterNametagsVisible(0)
            else:
                NametagGlobals.setMasterNametagsVisible(1)
        elif wordIs('~hideGui'):
            if aspect2d.isHidden():
                aspect2d.show()
            else:
                aspect2d.hide()
        elif wordIs('~flush'):
            base.cr.doDataCache.flush()
            base.cr.cache.flush()
            self.setMagicWordResponse('client object and data caches flushed')
        elif wordIs('~prof'):
            import time
            name = 'default'
            p = Point3()
            ts = time.time()
            for i in range(1000000):
                p.set(1, 2, 3)

            tf = time.time()
            dt = tf - ts
            response = 'prof(%s): %s secs' % (name, dt)
            print(response)
            self.setMagicWordResponse(response)
        elif wordIs('~gptc'):
            args = word.split()
            if len(args) > 1.0 and hasattr(self.cr, 'leakDetector'):
                gptcJob = self.cr.leakDetector.getPathsToContainers('~gptc', args[1], Functor(self._handleGPTCfinished, args[1]))
            else:
                self.setMagicWordResponse('error')
        elif wordIs('~gptcn'):
            args = word.split()
            if len(args) > 1.0 and hasattr(self.cr, 'leakDetector'):
                gptcnJob = self.cr.leakDetector.getPathsToContainersNamed('~gptcn', args[1], Functor(self._handleGPTCNfinished, args[1]))
            else:
                self.setMagicWordResponse('error')
        else:
            return 0
        return 1

    def toggleRun(self):
        if config.GetBool('want-running', 1):
            inputState.set('debugRunning', inputState.isSet('debugRunning') != True)

    def d_setMagicWord(self, magicWord, avId, zoneId):
        self.sendUpdate('setMagicWord', [magicWord,
         avId,
         zoneId,
         base.cr.userSignature])

    def b_setMagicWord(self, magicWord, avId=None, zoneId=None):
        if self.cr.wantMagicWords:
            if avId == None:
                avId = base.localAvatar.doId

            if zoneId == None:
                try:
                    zoneId = self.cr.playGame.getPlace().getZoneId()
                except:
                    pass

                if zoneId == None:
                    zoneId = 0

            self.d_setMagicWord(magicWord, avId, zoneId)
            if magicWord.count("~crash"):
                args = magicWord.split()
                errorCode = 12
                if len(args) > 1:
                    errorCode = int(args[1])
                self.notify.info("Simulating client crash: exit error = %s" % errorCode)
                base.exitShow(errorCode)

            if magicWord.count("~exception"):
                self.notify.error("~exception: simulating a client exception...")
                s = ""
                while 1:
                    s += "INVALIDNAME"
                    eval(s)

            self.setMagicWord(magicWord, avId, zoneId)

    def setMagicWordResponse(self, response):
        self.notify.info(response)
        base.localAvatar.setChatAbsolute(response, CFSpeech | CFTimeout)
        base.talkAssistant.receiveDeveloperMessage(response)

    def d_setWho(self, avIds):
        self.sendUpdate('setWho', [avIds])

    def _handleGPTCfinished(self, ct, gptcJob):
        self.setMagicWordResponse('gptc(%s) finished' % ct)

    def _handleGPTCNfinished(self, cn, gptcnJob):
        self.setMagicWordResponse('gptcn(%s) finished' % cn)

    def forAnother(self, word, avId, zoneId):
        b = 5
        while word[b:b + 2] != ' ~':
            b += 1
            if b >= len(word):
                self.setMagicWordResponse('No next magic word!')
                return

        nextWord = word[b + 1:]
        name = string.strip(word[5:b])
        id = self.identifyAvatar(name)
        if id == None:
            self.setMagicWordResponse("Don't know who %s is." % name)
            return
        self.d_setMagicWord(nextWord, id, zoneId)
        return

    def identifyAvatar(self, name):
        self.notify.error('Pure virtual - please override me.')

    def identifyDistributedObjects(self, name):
        result = []
        lowerName = string.lower(name)
        for obj in list(self.cr.doId2do.values()):
            className = obj.__class__.__name__
            try:
                name = obj.getName()
            except:
                name = className

            if string.lower(name) == lowerName or string.lower(className) == lowerName or string.lower(className) == 'distributed' + lowerName:
                result.append((name, obj))

        return result

    def doTex(self, word):
        args = word.split()
        if len(args) <= 1:
            if self.texViewer:
                self.texViewer.cleanup()
                self.texViewer = None
                return
            base.toggleTexture()
            return
        if self.texViewer:
            self.texViewer.cleanup()
            self.texViewer = None
        tex = TexturePool.findTexture(args[1])
        if not tex:
            tex = TexturePool.findTexture('*%s*' % args[1])
        if not tex:
            self.setMagicWordResponse('Unknown texture: %s' % args[1])
            return
        self.texViewer = TexViewer(tex)
        return

    def getCSBitmask(self, str):
        words = string.lower(str).split()
        if len(words) == 0:
            return None
        invalid = ''
        bitmask = BitMask32.allOff()
        for w in words:
            if w == 'wall':
                bitmask |= OTPGlobals.WallBitmask
            elif w == 'floor':
                bitmask |= OTPGlobals.FloorBitmask
            elif w == 'cam':
                bitmask |= OTPGlobals.CameraBitmask
            elif w == 'catch':
                bitmask |= OTPGlobals.CatchBitmask
            elif w == 'ghost':
                bitmask |= OTPGlobals.GhostBitmask
            elif w == 'pet':
                bitmask |= OTPGlobals.PetBitmask
            elif w == 'furniture':
                bitmask |= OTPGlobals.FurnitureSideBitmask | OTPGlobals.FurnitureTopBitmask | OTPGlobals.FurnitureDragBitmask
            elif w == 'furnitureside':
                bitmask |= OTPGlobals.FurnitureSideBitmask
            elif w == 'furnituretop':
                bitmask |= OTPGlobals.FurnitureTopBitmask
            elif w == 'furnituredrag':
                bitmask |= OTPGlobals.FurnitureDragBitmask
            elif w == 'pie':
                bitmask |= OTPGlobals.PieBitmask
            else:
                try:
                    bitmask |= BitMask32.bit(int(w))
                    print(bitmask)
                except ValueError:
                    invalid += ' ' + w

        if invalid:
            self.setMagicWordResponse('Unknown CS keyword(s): %s' % invalid)
        return bitmask

    def getFontByName(self, fontname):
        if fontname == 'default':
            return TextNode.getDefaultFont()
        elif fontname == 'interface':
            return OTPGlobals.getInterfaceFont()
        elif fontname == 'sign':
            return OTPGlobals.getSignFont()
        else:
            return None
        return None

    def showfont(self, fontname):
        fontname = string.strip(string.lower(fontname))
        font = self.getFontByName(fontname)
        if font == None:
            self.setMagicWordResponse('Unknown font: %s' % fontname)
            return
        if not isinstance(font, DynamicTextFont):
            self.setMagicWordResponse('Font %s is not dynamic.' % fontname)
            return
        self.hidefont()
        self.shownFontNode = aspect2d.attachNewNode('shownFont')
        tn = TextNode('square')
        tn.setCardActual(0.0, 1.0, -1.0, 0.0)
        tn.setFrameActual(0.0, 1.0, -1.0, 0.0)
        tn.setCardColor(1, 1, 1, 0.5)
        tn.setFrameColor(1, 1, 1, 1)
        tn.setFont(font)
        tn.setText(' ')
        numXPages = 2
        numYPages = 2
        pageScale = 0.8
        pageMargin = 0.1
        numPages = font.getNumPages()
        x = 0
        y = 0
        for pi in range(numPages):
            page = font.getPage(pi)
            tn.setCardTexture(page)
            np = self.shownFontNode.attachNewNode(tn.generate())
            np.setScale(pageScale)
            (np.setPos(float(x) / numXPages * 2 - 1 + pageMargin, 0, 1 - float(y) / numYPages * 2 - pageMargin),)
            x += 1
            if x >= numXPages:
                y += 1
                x = 0

        return

    def hidefont(self):
        if self.shownFontNode != None:
            self.shownFontNode.removeNode()
            self.shownFontNode = None
        return

    def showShadowCollisions(self):
        try:
            base.shadowTrav.showCollisions(render)
        except:
            self.setMagicWordResponse('CollisionVisualizer is not compiled in.')

    def hideShadowCollisions(self):
        base.shadowTrav.hideCollisions()

    def showCollisions(self):
        try:
            base.cTrav.showCollisions(render)
        except:
            self.setMagicWordResponse('CollisionVisualizer is not compiled in.')

    def hideCollisions(self):
        base.cTrav.hideCollisions()

    def showCameraCollisions(self):
        try:
            localAvatar.ccTrav.showCollisions(render)
        except:
            self.setMagicWordResponse('CollisionVisualizer is not compiled in.')

    def hideCameraCollisions(self):
        localAvatar.ccTrav.hideCollisions()

    def doFps(self, word, avId, zoneId):
        args = word.split()
        response = None
        if len(args) == 1 or args[1] == 'normal':
            if globalClock.getMode() != ClockObject.MNormal:
                globalClock.setMode(ClockObject.MNormal)
                response = 'Normal frame rate set.'
            else:
                base.setFrameRateMeter(not base.frameRateMeter)
        elif args[1] == 'forced':
            fps = float(args[2])
            globalClock.setMode(ClockObject.MForced)
            globalClock.setDt(1.0 / fps)
            response = 'Frame rate forced to %s fps.' % fps
            base.setFrameRateMeter(1)
        elif args[1] == 'degrade':
            factor = float(args[2])
            globalClock.setMode(ClockObject.MDegrade)
            globalClock.setDegradeFactor(factor)
            response = 'Frame rate degraded by factor of %s.' % factor
            base.setFrameRateMeter(1)
        elif args[1][-1] == '%':
            percent = float(args[1][:-1])
            if percent == 100:
                globalClock.setMode(ClockObject.MNormal)
                response = 'Normal frame rate set.'
            else:
                globalClock.setMode(ClockObject.MDegrade)
                globalClock.setDegradeFactor(100.0 / percent)
                response = 'Frame rate degraded to %s percent.' % percent
            base.setFrameRateMeter(1)
        else:
            try:
                fps = float(args[1])
            except:
                fps = None

            if fps != None:
                globalClock.setMode(ClockObject.MForced)
                globalClock.setDt(1.0 / fps)
                response = 'Frame rate forced to %s fps.' % fps
                base.setFrameRateMeter(1)
            else:
                response = 'Unknown fps command: ~s' % args[1]
        if base.frameRateMeter:
            globalClock.setAverageFrameRateInterval(ConfigVariableDouble('average-frame-rate-interval').getValue())
        if response != None:
            self.setMagicWordResponse(response)
        return

    def identifyAvatar(self, name):
        for av in Avatar.Avatar.ActiveAvatars:
            if isinstance(av, self.GameAvatarClass) and av.getName() == name:
                return av.doId

        lowerName = string.lower(name)
        for av in Avatar.Avatar.ActiveAvatars:
            if isinstance(av, self.GameAvatarClass) and string.strip(string.lower(av.getName())) == lowerName:
                return av.doId

        try:
            avId = int(name)
            return avId
        except:
            pass

        return None

    def toggleGuiPopup(self):
        if self.guiPopupShown:
            base.mouseWatcherNode.hideRegions()
            self.guiPopupShown = 0
        else:
            base.mouseWatcherNode.showRegions(render2d, 'gui-popup', 0)
            self.guiPopupShown = 1

    def garbageReportDone(self, garbageReport):
        self.setMagicWordResponse('%s garbage cycles' % garbageReport.getNumCycles())


def magicWord(mw):
    messenger.send('magicWord', [mw])


import builtins
builtins.magicWord = magicWord
