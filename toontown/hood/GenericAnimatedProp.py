from . import AnimatedProp
from direct.actor import Actor
from direct.interval.IntervalGlobal import *
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from toontown.hood import ZoneUtil
from toontown.hood import HoodUtil

class GenericAnimatedProp(AnimatedProp.AnimatedProp):
    notify = DirectNotifyGlobal.directNotify.newCategory('GenericAnimatedProp')
    AnimsUsingWav = []

    def __init__(self, node):
        AnimatedProp.AnimatedProp.__init__(self, node)
        self.origAnimNameToSound = {}
        code = node.getTag('DNACode')
        if code.startswith('interactive_prop_'):
            pathStr = code[len('interactive_prop_'):].split('__')[0]
        elif code.startswith('animated_prop_generic_'):
            pathStr = code[len('animated_prop_generic_'):].split('__')[0]
        elif code.startswith('animated_prop_'):
            tempStr = code[len('animated_prop_'):]
            nextUnderscore = tempStr.find('_')
            finalStr = tempStr[nextUnderscore + 1:]
            pathStr = finalStr.split('__')[0]
        elif code.startswith('animated_building_'):
            pathStr = code[len('animated_building_'):].split('__')[0]
        phaseDelimeter = len('phase_') + pathStr[len('phase_'):].find('_')
        phaseStr = pathStr[:phaseDelimeter]
        pathTokens = pathStr[phaseDelimeter + 1:].split('_')
        self.path = phaseStr
        for path in pathTokens:
            self.path += '/'
            self.path += path

        self.notify.debug('self.path=%s' % self.path)
        self.calcHoodId(node)
        self.propType = HoodUtil.calcPropType(node)
        self.setupActor(node)
        self.code = code

    def delete(self):
        AnimatedProp.AnimatedProp.delete(self)
        self.node.cleanup()
        del self.node
        del self.trashcan

    def enter(self):
        self.node.postFlatten()
        AnimatedProp.AnimatedProp.enter(self)
        doAnimLoop = True
        try:
            if type(self).__name__ == 'instance':
                if self.__class__.__name__ == 'GenericAnimatedProp':
                    if base.cr.newsManager.isHolidayRunning(ToontownGlobals.HYDRANTS_BUFF_BATTLES):
                        doAnimLoop = True
                    else:
                        doAnimLoop = False
        except:
            pass

        if doAnimLoop:
            self.node.loop('anim')

    def exit(self):
        AnimatedProp.AnimatedProp.exit(self)
        self.node.stop()

    def getActor(self):
        return self.node

    def setupActor(self, node):
        anim = node.getTag('DNAAnim')
        self.trashcan = Actor.Actor(node, copy=0)
        self.trashcan.reparentTo(node)
        self.trashcan.loadAnims({'anim': '%s/%s' % (self.path, anim)})
        self.trashcan.pose('anim', 0)
        self.node = self.trashcan

    def calcHoodId(self, node):
        self.hoodId = ToontownGlobals.ToontownCentral
        fullString = str(node)
        splits = fullString.split('/')
        try:
            visId = int(splits[2])
            self.visId = visId
            self.hoodId = ZoneUtil.getCanonicalHoodId(visId)
            self.notify.debug('calcHoodId %d from %s' % (self.hoodId, fullString))
        except Exception as generic:
            if 'Editor' not in fullString:
                self.notify.warning("calcHoodId couldn't parse %s using 0" % fullString)
            self.hoodId = 0
            self.visId = 0

    def createSoundInterval(self, origAnimNameWithPath, maximumDuration):
        if not hasattr(base, 'localAvatar'):
            return Sequence()
        sfxVolume = 1.0
        cutoff = 45
        if not hasattr(self, 'soundPath'):
            self.soundPath = self.path.replace('/models/char', '/audio/sfx')
        origAnimName = origAnimNameWithPath.split('/')[-1]
        theSound = self.origAnimNameToSound.get(origAnimName)
        if not theSound:
            soundfile = origAnimName.replace('tt_a_ara', 'tt_s_ara')
            fullPath = self.soundPath + '/' + soundfile
            if origAnimName in self.AnimsUsingWav:
                theSound = loader.loadSfx(fullPath + '.ogg')
            else:
                theSound = loader.loadSfx(fullPath + '.ogg')
            self.origAnimNameToSound[origAnimName] = theSound
        if theSound:
            soundDur = theSound.length()
            if maximumDuration < soundDur:
                if base.config.GetBool('interactive-prop-info', False):
                    if self.visId == localAvatar.zoneId and origAnimName != 'tt_a_ara_dga_hydrant_idleIntoFight':
                        self.notify.warning('anim %s had duration of %s while sound  has duration of %s' % (origAnimName, maximumDuration, soundDur))
                soundDur = maximumDuration
            result = SoundInterval(theSound, node=self.node, listenerNode=base.localAvatar, volume=sfxVolume, cutOff=cutoff, startTime=0, duration=soundDur)
        else:
            result = Sequence()
        return result
