from pandac.PandaModules import *
from libotp import *
from direct.interval.IntervalGlobal import *
from direct.distributed.ClockDelta import *
from .KnockKnockJokes import *
from toontown.toonbase import ToontownGlobals
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM
from . import DistributedAnimatedProp
from toontown.distributed import DelayDelete
from toontown.toonbase import TTLocalizer
from toontown.hood import ZoneUtil

class DistributedKnockKnockDoor(DistributedAnimatedProp.DistributedAnimatedProp):

    def __init__(self, cr):
        DistributedAnimatedProp.DistributedAnimatedProp.__init__(self, cr)
        self.fsm.setName('DistributedKnockKnockDoor')
        self.rimshot = None
        self.knockSfx = None
        return

    def generate(self):
        DistributedAnimatedProp.DistributedAnimatedProp.generate(self)
        self.avatarTracks = []
        self.avatarId = 0

    def announceGenerate(self):
        DistributedAnimatedProp.DistributedAnimatedProp.announceGenerate(self)
        self.accept('exitKnockKnockDoorSphere_' + str(self.propId), self.exitTrigger)
        self.acceptAvatar()

    def disable(self):
        self.ignore('exitKnockKnockDoorSphere_' + str(self.propId))
        self.ignore('enterKnockKnockDoorSphere_' + str(self.propId))
        DistributedAnimatedProp.DistributedAnimatedProp.disable(self)

    def delete(self):
        DistributedAnimatedProp.DistributedAnimatedProp.delete(self)
        if self.rimshot:
            self.rimshot = None
        if self.knockSfx:
            self.knockSfx = None
        return

    def acceptAvatar(self):
        self.acceptOnce('enterKnockKnockDoorSphere_' + str(self.propId), self.enterTrigger)

    def setAvatarInteract(self, avatarId):
        DistributedAnimatedProp.DistributedAnimatedProp.setAvatarInteract(self, avatarId)

    def avatarExit(self, avatarId):
        if avatarId == self.avatarId:
            for track in self.avatarTracks:
                track.finish()
                DelayDelete.cleanupDelayDeletes(track)

            self.avatarTracks = []

    def knockKnockTrack(self, avatar, duration):
        if avatar == None:
            return
        self.rimshot = base.loader.loadSfx('phase_5/audio/sfx/AA_heal_telljoke.ogg')
        self.knockSfx = base.loader.loadSfx('phase_5/audio/sfx/GUI_knock_3.ogg')
        joke = KnockKnockJokes[self.propId % len(KnockKnockJokes)]
        place = base.cr.playGame.getPlace()
        if place:
            zone = place.getZoneId()
            branch = ZoneUtil.getBranchZone(zone)
            if branch == ToontownGlobals.SillyStreet:
                if self.propId == 44:
                    joke = KnockKnockContestJokes[ToontownGlobals.SillyStreet]
            elif branch == ToontownGlobals.LoopyLane:
                if self.propId in list(KnockKnockContestJokes[ToontownGlobals.LoopyLane].keys()):
                    joke = KnockKnockContestJokes[ToontownGlobals.LoopyLane][self.propId]
            elif branch == ToontownGlobals.PunchlinePlace:
                if self.propId == 1:
                    joke = KnockKnockContestJokes[ToontownGlobals.PunchlinePlace]
            elif branch == ToontownGlobals.PolarPlace:
                if self.propId in list(KnockKnockContestJokes[ToontownGlobals.PolarPlace].keys()):
                    joke = KnockKnockContestJokes[ToontownGlobals.PolarPlace][self.propId]
        self.nametag = None
        self.nametagNP = None
        doorNP = render.find('**/KnockKnockDoorSphere_' + str(self.propId) + ';+s')
        if doorNP.isEmpty():
            self.notify.warning('Could not find KnockKnockDoorSphere_%s' % self.propId)
            return
        self.nametag = NametagGroup()
        self.nametag.setAvatar(doorNP)
        self.nametag.setFont(ToontownGlobals.getToonFont())
        self.nametag.setName(TTLocalizer.DoorNametag)
        self.nametag.setActive(0)
        self.nametag.manage(base.marginManager)
        self.nametag.getNametag3d().setBillboardOffset(4)
        nametagNode = self.nametag.getNametag3d().upcastToPandaNode()
        self.nametagNP = render.attachNewNode(nametagNode)
        self.nametagNP.setName('knockKnockDoor_nt_' + str(self.propId))
        pos = doorNP.node().getSolid(0).getCenter()
        self.nametagNP.setPos(pos + Vec3(0, 0, avatar.getHeight() + 2))
        d = duration * 0.125
        track = Sequence(Parallel(Sequence(Wait(d * 0.5), SoundInterval(self.knockSfx)), Func(self.nametag.setChat, TTLocalizer.DoorKnockKnock, CFSpeech), Wait(d)), Func(avatar.setChatAbsolute, TTLocalizer.DoorWhosThere, CFSpeech | CFTimeout, openEnded=0), Wait(d), Func(self.nametag.setChat, joke[0], CFSpeech), Wait(d), Func(avatar.setChatAbsolute, joke[0] + TTLocalizer.DoorWhoAppendix, CFSpeech | CFTimeout, openEnded=0), Wait(d), Func(self.nametag.setChat, joke[1], CFSpeech), Parallel(SoundInterval(self.rimshot, startTime=2.0), Wait(d * 4)), Func(self.cleanupTrack))
        track.delayDelete = DelayDelete.DelayDelete(avatar, 'knockKnockTrack')
        return track

    def cleanupTrack(self):
        avatar = self.cr.doId2do.get(self.avatarId, None)
        if avatar:
            avatar.clearChat()
        if self.nametag:
            self.nametag.unmanage(base.marginManager)
            self.nametagNP.removeNode()
        self.nametag = None
        self.nametagNP = None
        return

    def enterOff(self):
        DistributedAnimatedProp.DistributedAnimatedProp.enterOff(self)

    def exitOff(self):
        DistributedAnimatedProp.DistributedAnimatedProp.exitOff(self)

    def enterAttract(self, ts):
        DistributedAnimatedProp.DistributedAnimatedProp.enterAttract(self, ts)
        self.acceptAvatar()

    def exitAttract(self):
        DistributedAnimatedProp.DistributedAnimatedProp.exitAttract(self)

    def enterPlaying(self, ts):
        DistributedAnimatedProp.DistributedAnimatedProp.enterPlaying(self, ts)
        if self.avatarId:
            avatar = self.cr.doId2do.get(self.avatarId, None)
            track = self.knockKnockTrack(avatar, 8)
            if track != None:
                track.start(ts)
                self.avatarTracks.append(track)
        return

    def exitPlaying(self):
        DistributedAnimatedProp.DistributedAnimatedProp.exitPlaying(self)
        for track in self.avatarTracks:
            track.finish()
            DelayDelete.cleanupDelayDeletes(track)

        self.avatarTracks = []
        self.avatarId = 0
