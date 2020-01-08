from pandac.PandaModules import *
from libotp import *
from direct.interval.IntervalGlobal import *
from toontown.battle.BattleBase import *
from toontown.battle import DistributedBattle
from direct.directnotify import DirectNotifyGlobal
from toontown.toon import TTEmote
from otp.avatar import Emote
from toontown.battle import SuitBattleGlobals
import random
from toontown.suit import SuitDNA
from direct.fsm import State
from direct.fsm import ClassicFSM
from toontown.toonbase import ToontownGlobals

class DistributedLevelBattle(DistributedBattle.DistributedBattle):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedLevelBattle')

    def __init__(self, cr):
        DistributedBattle.DistributedBattle.__init__(self, cr)
        self.levelRequest = None
        self.levelBattle = 1
        return

    def setLevelDoId(self, levelDoId):
        self.levelDoId = levelDoId

    def setBattleCellId(self, battleCellId):
        self.battleCellId = battleCellId

        def doPlacement(levelList, self = self):
            self.levelRequest = None
            self.level = levelList[0]
            spec = self.level.getBattleCellSpec(self.battleCellId)
            self.level.requestReparent(self, spec['parentEntId'])
            self.setPos(spec['pos'])
            print('spec = %s' % spec)
            print('h = %s' % spec.get('h'))
            self.wrtReparentTo(render)
            return

        level = base.cr.doId2do.get(self.levelDoId)
        if level is None:
            self.notify.warning('level %s not in doId2do yet, battle %s will be mispositioned.' % self.levelDoId, self.doId)
            self.levelRequest = self.cr.relatedObjectMgr.requestObjects([self.levelDoId], doPlacement)
        else:
            doPlacement([level])
        return

    def setPosition(self, *args):
        pass

    def setInitialSuitPos(self, x, y, z):
        self.initialSuitPos = Point3(x, y, z)

    def disable(self):
        if self.hasLocalToon():
            self.unlockLevelViz()
        if self.levelRequest is not None:
            self.cr.relatedObjectMgr.abortRequest(self.levelRequest)
            self.levelRequest = None
        DistributedBattle.DistributedBattle.disable(self)
        return

    def delete(self):
        self.ignoreAll()
        DistributedBattle.DistributedBattle.delete(self)

    def handleBattleBlockerCollision(self):
        messenger.send(self.getCollisionName(), [None])
        return

    def lockLevelViz(self):
        level = base.cr.doId2do.get(self.levelDoId)
        if level:
            level.lockVisibility(zoneId=self.zoneId)
        else:
            self.notify.warning("lockLevelViz: couldn't find level %s" % self.levelDoId)

    def unlockLevelViz(self):
        level = base.cr.doId2do.get(self.levelDoId)
        if level:
            level.unlockVisibility()
        else:
            self.notify.warning("unlockLevelViz: couldn't find level %s" % self.levelDoId)

    def onWaitingForJoin(self):
        self.lockLevelViz()

    def __faceOff(self, ts, name, callback):
        if len(self.suits) == 0:
            self.notify.warning('__faceOff(): no suits.')
            return
        if len(self.toons) == 0:
            self.notify.warning('__faceOff(): no toons.')
            return
        toon = self.toons[0]
        point = self.toonPoints[0][0]
        toonPos = point[0]
        toonHpr = VBase3(point[1], 0.0, 0.0)
        p = toon.getPos(self)
        toon.setPos(self, p[0], p[1], 0.0)
        toon.setShadowHeight(0)
        if len(self.suits) == 1:
            leaderIndex = 0
        elif self.bossBattle == 1:
            for suit in self.suits:
                if suit.boss:
                    leaderIndex = self.suits.index(suit)
                    break

        else:
            maxTypeNum = -1
            for suit in self.suits:
                suitTypeNum = SuitDNA.getSuitType(suit.dna.name)
                if maxTypeNum < suitTypeNum:
                    maxTypeNum = suitTypeNum
                    leaderIndex = self.suits.index(suit)

        delay = FACEOFF_TAUNT_T
        suitTrack = Parallel()
        suitLeader = None
        for suit in self.suits:
            suit.setState('Battle')
            suitIsLeader = 0
            oneSuitTrack = Sequence()
            oneSuitTrack.append(Func(suit.loop, 'neutral'))
            oneSuitTrack.append(Func(suit.headsUp, toonPos))
            if self.suits.index(suit) == leaderIndex:
                suitLeader = suit
                suitIsLeader = 1
                if self.bossBattle == 1 and self.levelDoId in base.cr.doId2do:
                    level = base.cr.doId2do[self.levelDoId]
                    if suit.boss:
                        taunt = level.getBossTaunt()
                    else:
                        taunt = level.getBossBattleTaunt()
                else:
                    taunt = SuitBattleGlobals.getFaceoffTaunt(suit.getStyleName(), suit.doId)
                oneSuitTrack.append(Func(suit.setChatAbsolute, taunt, CFSpeech | CFTimeout))
            destPos, destHpr = self.getActorPosHpr(suit, self.suits)
            oneSuitTrack.append(Wait(delay))
            if suitIsLeader == 1:
                oneSuitTrack.append(Func(suit.clearChat))
            oneSuitTrack.append(self.createAdjustInterval(suit, destPos, destHpr))
            suitTrack.append(oneSuitTrack)

        suitHeight = suitLeader.getHeight()
        suitOffsetPnt = Point3(0, 0, suitHeight)
        toonTrack = Parallel()
        for toon in self.toons:
            oneToonTrack = Sequence()
            destPos, destHpr = self.getActorPosHpr(toon, self.toons)
            oneToonTrack.append(Wait(delay))
            oneToonTrack.append(self.createAdjustInterval(toon, destPos, destHpr, toon=1, run=1))
            toonTrack.append(oneToonTrack)

        if self.hasLocalToon():
            MidTauntCamHeight = suitHeight * 0.66
            MidTauntCamHeightLim = suitHeight - 1.8
            if MidTauntCamHeight < MidTauntCamHeightLim:
                MidTauntCamHeight = MidTauntCamHeightLim
            TauntCamY = 18
            TauntCamX = 0
            TauntCamHeight = random.choice((MidTauntCamHeight, 1, 11))
            camTrack = Sequence()
            camTrack.append(Func(camera.reparentTo, suitLeader))
            camTrack.append(Func(base.camLens.setFov, self.camFOFov))
            camTrack.append(Func(camera.setPos, TauntCamX, TauntCamY, TauntCamHeight))
            camTrack.append(Func(camera.lookAt, suitLeader, suitOffsetPnt))
            camTrack.append(Wait(delay))
            camTrack.append(Func(base.camLens.setFov, self.camFov))
            camTrack.append(Func(camera.wrtReparentTo, self))
            camTrack.append(Func(camera.setPos, self.camFOPos))
            camTrack.append(Func(camera.lookAt, suit))
        mtrack = Parallel(suitTrack, toonTrack)
        if self.hasLocalToon():
            NametagGlobals.setMasterArrowsOn(0)
            mtrack = Parallel(mtrack, camTrack)
        done = Func(callback)
        track = Sequence(mtrack, done, name=name)
        track.start(ts)
        self.storeInterval(track, name)
        return

    def enterFaceOff(self, ts):
        if len(self.toons) > 0 and base.localAvatar == self.toons[0]:
            Emote.globalEmote.disableAll(self.toons[0], 'dbattlebldg, enterFaceOff')
        self.delayDeleteMembers()
        self.__faceOff(ts, self.faceOffName, self.__handleFaceOffDone)

    def __handleFaceOffDone(self):
        self.notify.debug('FaceOff done')
        self.d_faceOffDone(base.localAvatar.doId)

    def exitFaceOff(self):
        self.notify.debug('exitFaceOff()')
        if len(self.toons) > 0 and base.localAvatar == self.toons[0]:
            Emote.globalEmote.releaseAll(self.toons[0], 'dbattlebldg exitFaceOff')
        self.clearInterval(self.faceOffName)
        self._removeMembersKeep()

    def __playReward(self, ts, callback):
        toonTracks = Parallel()
        for toon in self.toons:
            toonTracks.append(Sequence(Func(toon.loop, 'victory'), Wait(FLOOR_REWARD_TIMEOUT), Func(toon.loop, 'neutral')))

        name = self.uniqueName('floorReward')
        track = Sequence(toonTracks, Func(callback), name=name)
        camera.setPos(0, 0, 1)
        camera.setHpr(180, 10, 0)
        self.storeInterval(track, name)
        track.start(ts)

    def enterReward(self, ts):
        self.notify.info('enterReward()')
        self.disableCollision()
        self.delayDeleteMembers()
        self.__playReward(ts, self.__handleFloorRewardDone)

    def __handleFloorRewardDone(self):
        pass

    def exitReward(self):
        self.notify.info('exitReward()')
        self.clearInterval(self.uniqueName('floorReward'))
        self._removeMembersKeep()
        NametagGlobals.setMasterArrowsOn(1)
        for toon in self.toons:
            toon.startSmooth()
