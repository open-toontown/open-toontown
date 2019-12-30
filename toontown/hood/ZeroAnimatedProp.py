import types
import math
from direct.interval.IntervalGlobal import Sequence, Wait, ActorInterval, Func, SoundInterval, Parallel
from direct.task import Task
from direct.fsm import FSM
from direct.showbase.PythonUtil import weightedChoice
from toontown.hood import GenericAnimatedProp
from toontown.hood import AnimatedProp
from toontown.toonbase import ToontownGlobals
from direct.directnotify import DirectNotifyGlobal

class ZeroAnimatedProp(GenericAnimatedProp.GenericAnimatedProp, FSM.FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('ZeroAnimatedProp')

    def __init__(self, node, propString, phaseInfo, holidayId):
        self.propString = propString
        self.phaseInfo = phaseInfo
        self.holidayId = holidayId
        GenericAnimatedProp.GenericAnimatedProp.__init__(self, node)
        FSM.FSM.__init__(self, '%sZeroAnimPropFsm' % self.propString)
        self.node.unloadAnims('anim')
        self.loadPhaseAnims()
        self.phaseIvals = []
        self.curIval = None
        self.curPhase = -1
        self.okToStartNextAnim = False
        return

    def delete(self):
        self.exit()
        GenericAnimatedProp.GenericAnimatedProp.delete(self)

    def loadPhaseAnims(self):
        animDict = {}
        for key, info in self.phaseInfo.items():
            if type(info[0]) == tuple:
                for index, anims in enumerate(info[0]):
                    fullPath = self.path + '/' + anims
                    animName = 'phase%d_%d' % (key, index)
                    animDict[animName] = fullPath

            else:
                animName = 'phase%d' % key
                fullPath = self.path + '/' + info[0]
                animDict[animName] = fullPath

        self.node.loadAnims(animDict)

    def createPhaseIntervals(self):
        if self.phaseIvals:
            self.notify.debug('not creating phase ivals again')
            return
        self.phaseIvals = []
        for key, info in self.phaseInfo.items():
            self.notify.debug('key=%s' % key)
            if type(info[0]) == tuple:
                ival = Sequence()
                for index, anims in enumerate(info[0]):
                    animName = 'phase%d_%d' % (key, index)
                    animIval = self.node.actorInterval(animName)
                    animIvalDuration = animIval.getDuration()
                    soundIval = self.createSoundInterval(anims, animIvalDuration)
                    soundIvalDuration = soundIval.getDuration()
                    animAndSound = Parallel(soundIval, animIval)
                    ival.append(animAndSound)

                self.phaseIvals.append(ival)
            else:
                animName = 'phase%d' % key
                animIval = self.node.actorInterval('phase%d' % key)
                animIvalDuration = animIval.getDuration()
                soundIval = self.createSoundInterval(info[0], animIvalDuration)
                soundIvalDuration = soundIval.getDuration()
                ival = Parallel(animIval, soundIval)
                self.phaseIvals.append(ival)

    def enter(self):
        self.node.postFlatten()
        self.createPhaseIntervals()
        AnimatedProp.AnimatedProp.enter(self)
        defaultAnim = self.node.getAnimControl('anim')
        numFrames = defaultAnim.getNumFrames()
        self.node.pose('phase0', 0)
        self.accept('%sZeroPhase' % self.propString, self.handleNewPhase)
        self.accept('%sZeroIsRunning' % self.propString, self.handleNewIsRunning)
        self.startIfNeeded()

    def startIfNeeded(self):
        try:
            self.curPhase = self.getPhaseToRun()
            if self.curPhase >= 0:
                self.request('DoAnim')
        except:
            pass

    def chooseAnimToRun(self):
        result = self.curPhase
        if base.config.GetBool('anim-props-randomized', True):
            pairs = []
            for i in range(self.curPhase + 1):
                pairs.append((math.pow(2, i), i))

            sum = math.pow(2, self.curPhase + 1) - 1
            result = weightedChoice(pairs, sum=sum)
            self.notify.debug('chooseAnimToRun curPhase=%s pairs=%s result=%s' % (self.curPhase, pairs, result))
        return result

    def createAnimSequence(self, animPhase):
        result = Sequence(self.phaseIvals[animPhase], Wait(self.phaseInfo[self.curPhase][1]), Func(self.startNextAnim))
        return result

    def startNextAnim(self):
        self.notify.debug('startNextAnim self.okToStartNextAnim=%s' % self.okToStartNextAnim)
        self.curIval = None
        if self.okToStartNextAnim:
            self.notify.debug('got pass okToStartNextAnim')
            whichAnim = self.chooseAnimToRun()
            self.notify.debug('whichAnim=%s' % whichAnim)
            self.lastPlayingAnimPhase = whichAnim
            self.curIval = self.createAnimSequence(whichAnim)
            self.notify.debug('starting curIval of length %s' % self.curIval.getDuration())
            self.curIval.start()
        else:
            self.notify.debug('false self.okToStartNextAnim=%s' % self.okToStartNextAnim)
        return

    def enterDoAnim(self):
        self.notify.debug('enterDoAnim curPhase=%d' % self.curPhase)
        self.okToStartNextAnim = True
        self.startNextAnim()

    def exitDoAnim(self):
        self.notify.debug('exitDoAnim curPhase=%d' % self.curPhase)
        self.okToStartNextAnim = False
        self.curIval.finish()
        self.curIval = None
        return

    def getPhaseToRun(self):
        result = -1
        enoughInfoToRun = False
        if base.cr.newsManager.isHolidayRunning(self.holidayId):
            zeroMgrString = '%sZeroMgr' % self.propString
            if hasattr(base.cr, zeroMgrString):
                zeroMgr = eval('base.cr.%s' % zeroMgrString)
                if not zeroMgr.isDisabled():
                    enoughInfoToRun = True
                else:
                    self.notify.debug('isDisabled = %s' % zeroMgr.isDisabled())
            else:
                self.notify.debug('base.cr does not have %s' % zeroMgrString)
        else:
            self.notify.debug('holiday is not running')
        self.notify.debug('enoughInfoToRun = %s' % enoughInfoToRun)
        if enoughInfoToRun and zeroMgr.getIsRunning():
            curPhase = zeroMgr.getCurPhase()
            if curPhase >= len(self.phaseIvals):
                curPhase = len(self.phaseIvals) - 1
                self.notify.warning('zero mgr says to go to phase %d, but we only have %d ivals.  forcing curPhase to %d' % (curPhase, len(self.phaseIvals), curPhase))
            result = curPhase
        return result

    def exit(self):
        self.okToStartNextAnim = False
        self.ignore('%sZeroPhase' % self.propString)
        self.ignore('%sZeroIsRunning' % self.propString)
        GenericAnimatedProp.GenericAnimatedProp.exit(self)
        self.request('Off')

    def handleNewPhase(self, newPhase):
        self.startIfNeeded()

    def handleNewIsRunning(self, isRunning):
        if isRunning:
            self.startIfNeeded()
        else:
            self.request('Off')
