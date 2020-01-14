from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from direct.showbase import PythonUtil
from toontown.battle.BattleProps import globalPropPool
from direct.directnotify import DirectNotifyGlobal
SFX = PythonUtil.Enum('poof, magic')
SFXPATHS = {SFX.poof: 'phase_4/audio/sfx/firework_distance_02.ogg',
 SFX.magic: 'phase_4/audio/sfx/SZ_DD_treasure.ogg'}

class DustCloud(NodePath):
    dustCloudCount = 0
    sounds = {}
    notify = DirectNotifyGlobal.directNotify.newCategory('DustCloud')

    def __init__(self, parent = hidden, fBillboard = 1, wantSound = 0):
        NodePath.__init__(self)
        self.assign(globalPropPool.getProp('suit_explosion_dust'))
        if fBillboard:
            self.setBillboardAxis()
        self.reparentTo(parent)
        self.seqNode = self.find('**/+SequenceNode').node()
        self.seqNode.setFrameRate(0)
        self.wantSound = wantSound
        if self.wantSound and not DustCloud.sounds:
            DustCloud.sounds[SFX.poof] = loader.loadSfx(SFXPATHS[SFX.poof])
        self.track = None
        self.trackId = DustCloud.dustCloudCount
        DustCloud.dustCloudCount += 1
        self.setBin('fixed', 100, 1)
        self.hide()
        return

    def createTrack(self, rate = 24):

        def getSoundFuncIfAble(soundId):
            sound = DustCloud.sounds.get(soundId)
            if self.wantSound and sound:
                return sound.play
            else:

                def dummy():
                    pass

                return dummy

        tflipDuration = self.seqNode.getNumChildren() / float(rate)
        self.track = Sequence(Func(self.show), Func(self.messaging), Func(self.seqNode.play, 0, self.seqNode.getNumFrames() - 1), Func(self.seqNode.setFrameRate, rate), Func(getSoundFuncIfAble(SFX.poof)), Wait(tflipDuration), Func(self._resetTrack), name='dustCloud-track-%d' % self.trackId)

    def _resetTrack(self):
        self.seqNode.setFrameRate(0)
        self.hide()

    def messaging(self):
        self.notify.debug('CREATING TRACK ID: %s' % self.trackId)

    def isPlaying(self):
        if self.track == None:
            return False
        if self.track.isPlaying():
            return True
        else:
            return False
        return

    def play(self, rate = 24):
        self.stop()
        self.createTrack(rate)
        self.track.start()

    def loop(self, rate = 24):
        self.stop()
        self.createTrack(rate)
        self.track.loop()

    def stop(self):
        if self.track:
            self.track.finish()
            self.track.clearToInitial()

    def destroy(self):
        self.notify.debug('DESTROYING TRACK ID: %s' % self.trackId)
        if self.track:
            self._resetTrack()
            self.track.clearToInitial()
        del self.track
        del self.seqNode
        self.removeNode()
