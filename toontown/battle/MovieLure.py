from direct.interval.IntervalGlobal import *
from BattleBase import *
from BattleProps import *
from toontown.suit.SuitBase import *
from toontown.toon.ToonDNA import *
from BattleSounds import *
import MovieCamera
from direct.directnotify import DirectNotifyGlobal
import MovieUtil
from toontown.toonbase import ToontownBattleGlobals
import BattleParticles
import BattleProps
import MovieNPCSOS
notify = DirectNotifyGlobal.directNotify.newCategory('MovieLures')

def safeWrtReparentTo(nodePath, parent):
    if nodePath and not nodePath.isEmpty():
        nodePath.wrtReparentTo(parent)


def doLures(lures):
    if len(lures) == 0:
        return (None, None)
    npcArrivals, npcDepartures, npcs = MovieNPCSOS.doNPCTeleports(lures)
    mtrack = Parallel()
    for l in lures:
        ival = __doLureLevel(l, npcs)
        if ival:
            mtrack.append(ival)

    lureTrack = Sequence(npcArrivals, mtrack, npcDepartures)
    camDuration = mtrack.getDuration()
    enterDuration = npcArrivals.getDuration()
    exitDuration = npcDepartures.getDuration()
    camTrack = MovieCamera.chooseLureShot(lures, camDuration, enterDuration, exitDuration)
    return (lureTrack, camTrack)


def __doLureLevel(lure, npcs):
    level = lure['level']
    if level == 0:
        return __lureOneDollar(lure)
    elif level == 1:
        return __lureSmallMagnet(lure, npcs)
    elif level == 2:
        return __lureFiveDollar(lure)
    elif level == 3:
        return __lureLargeMagnet(lure, npcs)
    elif level == 4:
        return __lureTenDollar(lure)
    elif level == 5:
        return __lureHypnotize(lure, npcs)
    elif level == 6:
        return __lureSlideshow(lure, npcs)
    return None


def getSoundTrack(fileName, delay = 0.01, duration = None, node = None):
    soundEffect = globalBattleSoundCache.getSound(fileName)
    if duration:
        return Sequence(Wait(delay), SoundInterval(soundEffect, duration=duration, node=node))
    else:
        return Sequence(Wait(delay), SoundInterval(soundEffect, node=node))


def __createFishingPoleMultiTrack(lure, dollar, dollarName):
    toon = lure['toon']
    target = lure['target']
    battle = lure['battle']
    sidestep = lure['sidestep']
    hp = target['hp']
    kbbonus = target['kbbonus']
    suit = target['suit']
    targetPos = suit.getPos(battle)
    died = target['died']
    revived = target['revived']
    reachAnimDuration = 3.5
    trapProp = suit.battleTrapProp
    pole = globalPropPool.getProp('fishing-pole')
    pole2 = MovieUtil.copyProp(pole)
    poles = [pole, pole2]
    hands = toon.getRightHands()

    def positionDollar(dollar, suit):
        dollar.reparentTo(suit)
        dollar.setPos(0, MovieUtil.SUIT_LURE_DOLLAR_DISTANCE, 0)

    dollarTrack = Sequence(Func(positionDollar, dollar, suit), Func(dollar.wrtReparentTo, battle), ActorInterval(dollar, dollarName, duration=3), getSplicedLerpAnimsTrack(dollar, dollarName, 0.7, 2.0, startTime=3), LerpPosInterval(dollar, 0.2, Point3(0, -10, 7)), Func(MovieUtil.removeProp, dollar))
    poleTrack = Sequence(Func(MovieUtil.showProps, poles, hands), ActorInterval(pole, 'fishing-pole'), Func(MovieUtil.removeProps, poles))
    toonTrack = Sequence(Func(toon.headsUp, battle, targetPos), ActorInterval(toon, 'battlecast'), Func(toon.loop, 'neutral'))
    tracks = Parallel(dollarTrack, poleTrack, toonTrack)
    if sidestep == 0:
        if kbbonus == 1 or hp > 0:
            suitTrack = Sequence()
            opos, ohpr = battle.getActorPosHpr(suit)
            reachDist = MovieUtil.SUIT_LURE_DISTANCE
            reachPos = Point3(opos[0], opos[1] - reachDist, opos[2])
            suitTrack.append(Func(suit.loop, 'neutral'))
            suitTrack.append(Wait(3.5))
            suitName = suit.getStyleName()
            retardPos, retardHpr = battle.getActorPosHpr(suit)
            retardPos.setY(retardPos.getY() + MovieUtil.SUIT_EXTRA_REACH_DISTANCE)
            if suitName in MovieUtil.largeSuits:
                moveTrack = lerpSuit(suit, 0.0, reachAnimDuration / 2.5, retardPos, battle, trapProp)
                reachTrack = ActorInterval(suit, 'reach', duration=reachAnimDuration)
                suitTrack.append(Parallel(moveTrack, reachTrack))
            else:
                suitTrack.append(ActorInterval(suit, 'reach', duration=reachAnimDuration))
            if trapProp:
                suitTrack.append(Func(trapProp.wrtReparentTo, battle))
            suitTrack.append(Func(suit.setPos, battle, reachPos))
            if trapProp:
                suitTrack.append(Func(trapProp.wrtReparentTo, suit))
                suit.battleTrapProp = trapProp
            suitTrack.append(Func(suit.loop, 'neutral'))
            suitTrack.append(Func(battle.lureSuit, suit))
            if hp > 0:
                suitTrack.append(__createSuitDamageTrack(battle, suit, hp, lure, trapProp))
            if revived != 0:
                suitTrack.append(MovieUtil.createSuitReviveTrack(suit, toon, battle))
            if died != 0:
                suitTrack.append(MovieUtil.createSuitDeathTrack(suit, toon, battle))
            tracks.append(suitTrack)
    else:
        tracks.append(Sequence(Wait(3.7), Func(MovieUtil.indicateMissed, suit)))
    tracks.append(getSoundTrack('TL_fishing_pole.mp3', delay=0.5, node=toon))
    return tracks


def __createMagnetMultiTrack(lure, magnet, pos, hpr, scale, isSmallMagnet = 1, npcs = []):
    toon = lure['toon']
    if lure.has_key('npc'):
        toon = lure['npc']
    battle = lure['battle']
    sidestep = lure['sidestep']
    targets = lure['target']
    tracks = Parallel()
    tracks.append(Sequence(ActorInterval(toon, 'hold-magnet'), Func(toon.loop, 'neutral')))
    hands = toon.getLeftHands()
    magnet2 = MovieUtil.copyProp(magnet)
    magnets = [magnet, magnet2]
    magnetTrack = Sequence(Wait(0.7), Func(MovieUtil.showProps, magnets, hands, pos, hpr, scale), Wait(6.3), Func(MovieUtil.removeProps, magnets))
    tracks.append(magnetTrack)
    for target in targets:
        suit = target['suit']
        trapProp = suit.battleTrapProp
        if sidestep == 0:
            hp = target['hp']
            kbbonus = target['kbbonus']
            died = target['died']
            revived = target['revived']
            if kbbonus == 1 or hp > 0:
                suitDelay = 2.6
                suitMoveDuration = 0.8
                suitTrack = Sequence()
                opos, ohpr = battle.getActorPosHpr(suit)
                reachDist = MovieUtil.SUIT_LURE_DISTANCE
                reachPos = Point3(opos[0], opos[1] - reachDist, opos[2])
                numShakes = 3
                shakeTotalDuration = 0.8
                shakeDuration = shakeTotalDuration / float(numShakes)
                suitTrack.append(Func(suit.loop, 'neutral'))
                suitTrack.append(Wait(suitDelay))
                suitTrack.append(ActorInterval(suit, 'landing', startTime=2.37, endTime=1.82))
                for i in range(0, numShakes):
                    suitTrack.append(ActorInterval(suit, 'landing', startTime=1.82, endTime=1.16, duration=shakeDuration))

                suitTrack.append(ActorInterval(suit, 'landing', startTime=1.16, endTime=0.7))
                suitTrack.append(ActorInterval(suit, 'landing', startTime=0.7, duration=1.3))
                suitTrack.append(Func(suit.loop, 'neutral'))
                suitTrack.append(Func(battle.lureSuit, suit))
                if hp > 0:
                    suitTrack.append(__createSuitDamageTrack(battle, suit, hp, lure, trapProp))
                if revived != 0:
                    suitTrack.append(MovieUtil.createSuitReviveTrack(suit, toon, battle, npcs))
                elif died != 0:
                    suitTrack.append(MovieUtil.createSuitDeathTrack(suit, toon, battle, npcs))
                tracks.append(suitTrack)
                tracks.append(lerpSuit(suit, suitDelay + 0.55 + shakeTotalDuration, suitMoveDuration, reachPos, battle, trapProp))
        else:
            tracks.append(Sequence(Wait(3.7), Func(MovieUtil.indicateMissed, suit)))

    if isSmallMagnet == 1:
        tracks.append(getSoundTrack('TL_small_magnet.mp3', delay=0.7, node=toon))
    else:
        tracks.append(getSoundTrack('TL_large_magnet.mp3', delay=0.7, node=toon))
    return tracks


def __createHypnoGogglesMultiTrack(lure, npcs = []):
    toon = lure['toon']
    if lure.has_key('npc'):
        toon = lure['npc']
    targets = lure['target']
    battle = lure['battle']
    sidestep = lure['sidestep']
    goggles = globalPropPool.getProp('hypno-goggles')
    goggles2 = MovieUtil.copyProp(goggles)
    bothGoggles = [goggles, goggles2]
    pos = Point3(-1.03, 1.04, -0.3)
    hpr = Point3(-96.55, 36.14, -170.59)
    scale = Point3(1.5, 1.5, 1.5)
    hands = toon.getLeftHands()
    gogglesTrack = Sequence(Wait(0.6), Func(MovieUtil.showProps, bothGoggles, hands, pos, hpr, scale), ActorInterval(goggles, 'hypno-goggles', duration=2.2), Func(MovieUtil.removeProps, bothGoggles))
    toonTrack = Sequence(ActorInterval(toon, 'hypnotize'), Func(toon.loop, 'neutral'))
    tracks = Parallel(gogglesTrack, toonTrack)
    for target in targets:
        suit = target['suit']
        trapProp = suit.battleTrapProp
        if sidestep == 0:
            hp = target['hp']
            kbbonus = target['kbbonus']
            died = target['died']
            revived = target['revived']
            if kbbonus == 1 or hp > 0:
                suitTrack = Sequence()
                suitDelay = 1.6
                suitAnimDuration = 1.5
                opos, ohpr = battle.getActorPosHpr(suit)
                reachDist = MovieUtil.SUIT_LURE_DISTANCE
                reachPos = Point3(opos[0], opos[1] - reachDist, opos[2])
                suitTrack.append(Func(suit.loop, 'neutral'))
                suitTrack.append(Wait(suitDelay))
                suitTrack.append(ActorInterval(suit, 'hypnotized', duration=3.1))
                suitTrack.append(Func(suit.setPos, battle, reachPos))
                suitTrack.append(Func(suit.loop, 'neutral'))
                suitTrack.append(Func(battle.lureSuit, suit))
                if hp > 0:
                    suitTrack.append(__createSuitDamageTrack(battle, suit, hp, lure, trapProp))
                if revived != 0:
                    suitTrack.append(MovieUtil.createSuitReviveTrack(suit, toon, battle, npcs))
                elif died != 0:
                    suitTrack.append(MovieUtil.createSuitDeathTrack(suit, toon, battle, npcs))
                tracks.append(suitTrack)
                tracks.append(lerpSuit(suit, suitDelay + 1.7, 0.7, reachPos, battle, trapProp))
        else:
            tracks.append(Sequence(Wait(2.3), Func(MovieUtil.indicateMissed, suit, 1.1)))

    tracks.append(getSoundTrack('TL_hypnotize.mp3', delay=0.5, node=toon))
    return tracks


def __lureOneDollar(lure):
    dollarProp = '1dollar'
    dollar = globalPropPool.getProp(dollarProp)
    return __createFishingPoleMultiTrack(lure, dollar, dollarProp)


def __lureSmallMagnet(lure, npcs = []):
    magnet = globalPropPool.getProp('small-magnet')
    pos = Point3(-0.27, 0.19, 0.29)
    hpr = Point3(-90.0, 84.17, -180.0)
    scale = Point3(0.85, 0.85, 0.85)
    return __createMagnetMultiTrack(lure, magnet, pos, hpr, scale, isSmallMagnet=1, npcs=npcs)


def __lureFiveDollar(lure):
    dollarProp = '5dollar'
    dollar = globalPropPool.getProp(dollarProp)
    return __createFishingPoleMultiTrack(lure, dollar, dollarProp)


def __lureLargeMagnet(lure, npcs = []):
    magnet = globalPropPool.getProp('big-magnet')
    pos = Point3(-0.27, 0.08, 0.29)
    hpr = Point3(-90.0, 84.17, -180)
    scale = Point3(1.32, 1.32, 1.32)
    return __createMagnetMultiTrack(lure, magnet, pos, hpr, scale, isSmallMagnet=0, npcs=npcs)


def __lureTenDollar(lure):
    dollarProp = '10dollar'
    dollar = globalPropPool.getProp(dollarProp)
    return __createFishingPoleMultiTrack(lure, dollar, dollarProp)


def __lureHypnotize(lure, npcs = []):
    return __createHypnoGogglesMultiTrack(lure, npcs)


def __lureSlideshow(lure, npcs):
    return __createSlideshowMultiTrack(lure, npcs)


def __createSuitDamageTrack(battle, suit, hp, lure, trapProp):
    if trapProp == None or trapProp.isEmpty():
        return Func(suit.loop, 'neutral')
    trapProp.wrtReparentTo(battle)
    trapTrack = ToontownBattleGlobals.TRAP_TRACK
    trapLevel = suit.battleTrap
    trapTrackNames = ToontownBattleGlobals.AvProps[trapTrack]
    trapName = trapTrackNames[trapLevel]
    result = Sequence()

    def reparentTrap(trapProp = trapProp, battle = battle):
        if trapProp and not trapProp.isEmpty():
            trapProp.wrtReparentTo(battle)

    result.append(Func(reparentTrap))
    parent = battle
    if suit.battleTrapIsFresh == 1:
        if trapName == 'quicksand' or trapName == 'trapdoor':
            trapProp.hide()
            trapProp.reparentTo(suit)
            trapProp.setPos(Point3(0, MovieUtil.SUIT_TRAP_DISTANCE, 0))
            trapProp.setHpr(Point3(0, 0, 0))
            trapProp.wrtReparentTo(battle)
        elif trapName == 'rake':
            trapProp.hide()
            trapProp.reparentTo(suit)
            trapProp.setPos(0, MovieUtil.SUIT_TRAP_RAKE_DISTANCE, 0)
            trapProp.setHpr(Point3(0, 270, 0))
            trapProp.setScale(Point3(0.7, 0.7, 0.7))
            rakeOffset = MovieUtil.getSuitRakeOffset(suit)
            trapProp.setY(trapProp.getY() + rakeOffset)
        else:
            parent = render
    if trapName == 'banana':
        slidePos = trapProp.getPos(parent)
        slidePos.setY(slidePos.getY() - 5.1)
        moveTrack = Sequence(Wait(0.1), LerpPosInterval(trapProp, 0.1, slidePos, other=battle))
        animTrack = Sequence(ActorInterval(trapProp, 'banana', startTime=3.1), Wait(1.1), LerpScaleInterval(trapProp, 1, Point3(0.01, 0.01, 0.01)))
        suitTrack = ActorInterval(suit, 'slip-backward')
        damageTrack = Sequence(Wait(0.5), Func(suit.showHpText, -hp, openEnded=0), Func(suit.updateHealthBar, hp))
        soundTrack = Sequence(SoundInterval(globalBattleSoundCache.getSound('AA_pie_throw_only.mp3'), duration=0.55, node=suit), SoundInterval(globalBattleSoundCache.getSound('Toon_bodyfall_synergy.mp3'), node=suit))
        result.append(Parallel(moveTrack, animTrack, suitTrack, damageTrack, soundTrack))
    elif trapName == 'rake' or trapName == 'rake-react':
        hpr = trapProp.getHpr(parent)
        upHpr = Vec3(hpr[0], 179.9999, hpr[2])
        bounce1Hpr = Vec3(hpr[0], 120, hpr[2])
        bounce2Hpr = Vec3(hpr[0], 100, hpr[2])
        rakeTrack = Sequence(Wait(0.5), LerpHprInterval(trapProp, 0.1, upHpr, startHpr=hpr), Wait(0.7), LerpHprInterval(trapProp, 0.4, hpr, startHpr=upHpr), LerpHprInterval(trapProp, 0.15, bounce1Hpr, startHpr=hpr), LerpHprInterval(trapProp, 0.05, hpr, startHpr=bounce1Hpr), LerpHprInterval(trapProp, 0.15, bounce2Hpr, startHpr=hpr), LerpHprInterval(trapProp, 0.05, hpr, startHpr=bounce2Hpr), Wait(0.2), LerpScaleInterval(trapProp, 0.2, Point3(0.01, 0.01, 0.01)))
        rakeAnimDuration = 3.125
        suitTrack = ActorInterval(suit, 'rake-react', duration=rakeAnimDuration)
        damageTrack = Sequence(Wait(0.5), Func(suit.showHpText, -hp, openEnded=0), Func(suit.updateHealthBar, hp))
        soundTrack = getSoundTrack('TL_step_on_rake.mp3', delay=0.6, node=suit)
        result.append(Parallel(rakeTrack, suitTrack, damageTrack, soundTrack))
    elif trapName == 'marbles':
        slidePos = trapProp.getPos(parent)
        slidePos.setY(slidePos.getY() - 6.5)
        moveTrack = Sequence(Wait(0.1), LerpPosInterval(trapProp, 0.8, slidePos, other=battle), Wait(1.1), LerpScaleInterval(trapProp, 1, Point3(0.01, 0.01, 0.01)))
        animTrack = ActorInterval(trapProp, 'marbles', startTime=3.1)
        suitTrack = ActorInterval(suit, 'slip-backward')
        damageTrack = Sequence(Wait(0.5), Func(suit.showHpText, -hp, openEnded=0), Func(suit.updateHealthBar, hp))
        soundTrack = Sequence(SoundInterval(globalBattleSoundCache.getSound('AA_pie_throw_only.mp3'), duration=0.55, node=suit), SoundInterval(globalBattleSoundCache.getSound('Toon_bodyfall_synergy.mp3'), node=suit))
        result.append(Parallel(moveTrack, animTrack, suitTrack, damageTrack, soundTrack))
    elif trapName == 'quicksand':
        sinkPos1 = trapProp.getPos(battle)
        sinkPos2 = trapProp.getPos(battle)
        dropPos = trapProp.getPos(battle)
        landPos = trapProp.getPos(battle)
        sinkPos1.setZ(sinkPos1.getZ() - 3.1)
        sinkPos2.setZ(sinkPos2.getZ() - 9.1)
        dropPos.setZ(dropPos.getZ() + 15)
        if base.config.GetBool('want-new-cogs', 0):
            nameTag = suit.find('**/def_nameTag')
        else:
            nameTag = suit.find('**/joint_nameTag')
        trapTrack = Sequence(Wait(2.4), LerpScaleInterval(trapProp, 0.8, Point3(0.01, 0.01, 0.01)))
        moveTrack = Sequence(Wait(0.9), LerpPosInterval(suit, 0.9, sinkPos1, other=battle), LerpPosInterval(suit, 0.4, sinkPos2, other=battle), Func(suit.setPos, battle, dropPos), Func(suit.wrtReparentTo, hidden), Wait(1.1), Func(suit.wrtReparentTo, battle), LerpPosInterval(suit, 0.3, landPos, other=battle))
        animTrack = Sequence(ActorInterval(suit, 'flail'), ActorInterval(suit, 'flail', startTime=1.1), Wait(0.7), ActorInterval(suit, 'slip-forward', duration=2.1))
        damageTrack = Sequence(Wait(3.5), Func(suit.showHpText, -hp, openEnded=0), Func(suit.updateHealthBar, hp))
        soundTrack = Sequence(Wait(0.7), SoundInterval(globalBattleSoundCache.getSound('TL_quicksand.mp3'), node=suit), Wait(0.1), SoundInterval(globalBattleSoundCache.getSound('Toon_bodyfall_synergy.mp3'), node=suit))
        result.append(Parallel(trapTrack, moveTrack, animTrack, damageTrack, soundTrack))
    elif trapName == 'trapdoor':
        sinkPos = trapProp.getPos(battle)
        dropPos = trapProp.getPos(battle)
        landPos = trapProp.getPos(battle)
        sinkPos.setZ(sinkPos.getZ() - 9.1)
        dropPos.setZ(dropPos.getZ() + 15)
        trapTrack = Sequence(Wait(2.4), LerpScaleInterval(trapProp, 0.8, Point3(0.01, 0.01, 0.01)))
        moveTrack = Sequence(Wait(2.2), LerpPosInterval(suit, 0.4, sinkPos, other=battle), Func(suit.setPos, battle, dropPos), Func(suit.wrtReparentTo, hidden), Wait(1.6), Func(suit.wrtReparentTo, battle), LerpPosInterval(suit, 0.3, landPos, other=battle))
        animTrack = Sequence(getSplicedLerpAnimsTrack(suit, 'flail', 0.7, 0.25), Func(trapProp.setColor, Vec4(0, 0, 0, 1)), ActorInterval(suit, 'flail', startTime=0.7, endTime=0), ActorInterval(suit, 'neutral', duration=0.5), ActorInterval(suit, 'flail', startTime=1.1), Wait(1.1), ActorInterval(suit, 'slip-forward', duration=2.1))
        damageTrack = Sequence(Wait(3.5), Func(suit.showHpText, -hp, openEnded=0), Func(suit.updateHealthBar, hp))
        soundTrack = Sequence(Wait(0.8), SoundInterval(globalBattleSoundCache.getSound('TL_trap_door.mp3'), node=suit), Wait(0.8), SoundInterval(globalBattleSoundCache.getSound('Toon_bodyfall_synergy.mp3'), node=suit))
        result.append(Parallel(trapTrack, moveTrack, animTrack, damageTrack, soundTrack))
    elif trapName == 'tnt':
        tntTrack = ActorInterval(trapProp, 'tnt')
        explosionTrack = Sequence(Wait(2.3), createTNTExplosionTrack(battle, trapProp=trapProp, relativeTo=parent))
        suitTrack = Sequence(ActorInterval(suit, 'flail', duration=0.7), ActorInterval(suit, 'flail', startTime=0.7, endTime=0.0), ActorInterval(suit, 'neutral', duration=0.4), ActorInterval(suit, 'flail', startTime=0.6, endTime=0.7), Wait(0.4), ActorInterval(suit, 'slip-forward', startTime=2.48, duration=0.1), Func(battle.movie.needRestoreColor), Func(suit.setColorScale, Vec4(0.2, 0.2, 0.2, 1)), Func(trapProp.reparentTo, hidden), ActorInterval(suit, 'slip-forward', startTime=2.58), Func(suit.clearColorScale), Func(trapProp.sparksEffect.cleanup), Func(battle.movie.clearRestoreColor))
        damageTrack = Sequence(Wait(2.3), Func(suit.showHpText, -hp, openEnded=0), Func(suit.updateHealthBar, hp))
        explosionSound = base.loadSfx('phase_3.5/audio/sfx/ENC_cogfall_apart.mp3')
        soundTrack = Sequence(SoundInterval(globalBattleSoundCache.getSound('TL_dynamite.mp3'), duration=2.0, node=suit), SoundInterval(explosionSound, duration=0.6, node=suit))
        result.append(Parallel(tntTrack, suitTrack, damageTrack, explosionTrack, soundTrack))
    elif trapName == 'traintrack':
        trainInterval = createIncomingTrainInterval(battle, suit, hp, lure, trapProp)
        result.append(trainInterval)
    else:
        notify.warning('unknown trapName: %s detected on suit: %s' % (trapName, suit))
    suit.battleTrapProp = trapProp
    result.append(Func(battle.removeTrap, suit, True))
    result.append(Func(battle.unlureSuit, suit))
    result.append(__createSuitResetPosTrack(suit, battle))
    result.append(Func(suit.loop, 'neutral'))
    if trapName == 'traintrack':
        result.append(Func(MovieUtil.removeProp, trapProp))
    return result


def __createSuitResetPosTrack(suit, battle):
    resetPos, resetHpr = battle.getActorPosHpr(suit)
    moveDist = Vec3(suit.getPos(battle) - resetPos).length()
    moveDuration = 0.5
    walkTrack = Sequence(Func(suit.setHpr, battle, resetHpr), ActorInterval(suit, 'walk', startTime=1, duration=moveDuration, endTime=0.0001), Func(suit.loop, 'neutral'))
    moveTrack = LerpPosInterval(suit, moveDuration, resetPos, other=battle)
    return Parallel(walkTrack, moveTrack)


def getSplicedLerpAnimsTrack(object, animName, origDuration, newDuration, startTime = 0, fps = 30):
    track = Sequence()
    addition = 0
    numIvals = origDuration * fps
    timeInterval = newDuration / numIvals
    animInterval = origDuration / numIvals
    for i in range(0, numIvals):
        track.append(Wait(timeInterval))
        track.append(ActorInterval(object, animName, startTime=startTime + addition, duration=animInterval))
        addition += animInterval

    return track


def lerpSuit(suit, delay, duration, reachPos, battle, trapProp):
    track = Sequence()
    if trapProp:
        track.append(Func(safeWrtReparentTo, trapProp, battle))
    track.append(Wait(delay))
    track.append(LerpPosInterval(suit, duration, reachPos, other=battle))
    if trapProp:
        if trapProp.getName() == 'traintrack':
            notify.debug('UBERLURE MovieLure.lerpSuit deliberately not parenting trainTrack to suit')
        else:
            track.append(Func(safeWrtReparentTo, trapProp, suit))
        suit.battleTrapProp = trapProp
    return track


def createTNTExplosionTrack(parent, explosionPoint = None, trapProp = None, relativeTo = render):
    explosionTrack = Sequence()
    explosion = BattleProps.globalPropPool.getProp('kapow')
    explosion.setBillboardPointEye()
    if not explosionPoint:
        if trapProp:
            explosionPoint = trapProp.getPos(relativeTo)
            explosionPoint.setZ(explosionPoint.getZ() + 2.3)
        else:
            explosionPoint = Point3(0, 3.6, 2.1)
    explosionTrack.append(Func(explosion.reparentTo, parent))
    explosionTrack.append(Func(explosion.setPos, explosionPoint))
    explosionTrack.append(Func(explosion.setScale, 0.11))
    explosionTrack.append(ActorInterval(explosion, 'kapow'))
    explosionTrack.append(Func(MovieUtil.removeProp, explosion))
    return explosionTrack


TRAIN_STARTING_X = -7.131
TRAIN_TUNNEL_END_X = 7.1
TRAIN_TRAVEL_DISTANCE = 45
TRAIN_SPEED = 35.0
TRAIN_DURATION = TRAIN_TRAVEL_DISTANCE / TRAIN_SPEED
TRAIN_MATERIALIZE_TIME = 3
TOTAL_TRAIN_TIME = TRAIN_DURATION + TRAIN_MATERIALIZE_TIME

def createSuitReactionToTrain(battle, suit, hp, lure, trapProp):
    toon = lure['toon']
    retval = Sequence()
    suitPos, suitHpr = battle.getActorPosHpr(suit)
    distance = suitPos.getX() - TRAIN_STARTING_X
    timeToGetHit = distance / TRAIN_SPEED
    suitTrack = Sequence()
    showDamage = Func(suit.showHpText, -hp, openEnded=0)
    updateHealthBar = Func(suit.updateHealthBar, hp)
    anim = 'flatten'
    suitReact = ActorInterval(suit, anim)
    cogGettingHit = getSoundTrack('TL_train_cog.mp3', node=toon)
    suitTrack.append(Func(suit.loop, 'neutral'))
    suitTrack.append(Wait(timeToGetHit + TRAIN_MATERIALIZE_TIME))
    suitTrack.append(updateHealthBar)
    suitTrack.append(Parallel(suitReact, cogGettingHit))
    suitTrack.append(showDamage)
    curDuration = suitTrack.getDuration()
    timeTillEnd = TOTAL_TRAIN_TIME - curDuration
    if timeTillEnd > 0:
        suitTrack.append(Wait(timeTillEnd))
    retval.append(suitTrack)
    return retval


def createIncomingTrainInterval(battle, suit, hp, lure, trapProp):
    toon = lure['toon']
    retval = Parallel()
    suitTrack = createSuitReactionToTrain(battle, suit, hp, lure, trapProp)
    retval.append(suitTrack)
    if not trapProp.find('**/train_gag').isEmpty():
        return retval
    clipper = PlaneNode('clipper')
    clipper.setPlane(Plane(Vec3(1, 0, 0), Point3(TRAIN_STARTING_X, 0, 0)))
    clipNP = trapProp.attachNewNode(clipper)
    trapProp.setClipPlane(clipNP)
    clipper2 = PlaneNode('clipper2')
    clipper2.setPlane(Plane(Vec3(-1, 0, 0), Point3(TRAIN_TUNNEL_END_X, 0, 0)))
    clipNP2 = trapProp.attachNewNode(clipper2)
    trapProp.setClipPlane(clipNP2)
    train = globalPropPool.getProp('train')
    train.hide()
    train.reparentTo(trapProp)
    tempScale = trapProp.getScale()
    trainScale = Vec3(1.0 / tempScale[0], 1.0 / tempScale[1], 1.0 / tempScale[2])
    trainIval = Sequence()
    trainIval.append(Func(train.setScale, trainScale))
    trainIval.append(Func(train.setH, 90))
    trainIval.append(Func(train.setX, TRAIN_STARTING_X))
    trainIval.append(Func(train.setTransparency, 1))
    trainIval.append(Func(train.setColorScale, Point4(1, 1, 1, 0)))
    trainIval.append(Func(train.show))
    tunnel2 = trapProp.find('**/tunnel3')
    tunnel3 = trapProp.find('**/tunnel2')
    tunnels = [tunnel2, tunnel3]
    for tunnel in tunnels:
        trainIval.append(Func(tunnel.setTransparency, 1))
        trainIval.append(Func(tunnel.setColorScale, Point4(1, 1, 1, 0)))
        trainIval.append(Func(tunnel.setScale, Point3(1.0, 0.01, 0.01)))
        trainIval.append(Func(tunnel.show))

    materializeIval = Parallel()
    materializeIval.append(LerpColorScaleInterval(train, TRAIN_MATERIALIZE_TIME, Point4(1, 1, 1, 1)))
    for tunnel in tunnels:
        materializeIval.append(LerpColorScaleInterval(tunnel, TRAIN_MATERIALIZE_TIME, Point4(1, 1, 1, 1)))

    for tunnel in tunnels:
        tunnelScaleIval = Sequence()
        tunnelScaleIval.append(LerpScaleInterval(tunnel, TRAIN_MATERIALIZE_TIME - 1.0, Point3(1.0, 2.0, 2.5)))
        tunnelScaleIval.append(LerpScaleInterval(tunnel, 0.5, Point3(1.0, 3.0, 1.5)))
        tunnelScaleIval.append(LerpScaleInterval(tunnel, 0.5, Point3(1.0, 2.5, 2.0)))
        materializeIval.append(tunnelScaleIval)

    trainIval.append(materializeIval)
    endingX = TRAIN_STARTING_X + TRAIN_TRAVEL_DISTANCE
    trainIval.append(LerpPosInterval(train, TRAIN_DURATION, Point3(endingX, 0, 0), other=battle))
    trainIval.append(LerpColorScaleInterval(train, TRAIN_MATERIALIZE_TIME, Point4(1, 1, 1, 0)))
    retval.append(trainIval)
    trainSoundTrack = getSoundTrack('TL_train.mp3', node=toon)
    retval.append(trainSoundTrack)
    return retval


def __createSlideshowMultiTrack(lure, npcs = []):
    toon = lure['toon']
    battle = lure['battle']
    sidestep = lure['sidestep']
    origHpr = toon.getHpr(battle)
    slideshowDelay = 2.5
    hands = toon.getLeftHands()
    endPos = toon.getPos(battle)
    endPos.setY(endPos.getY() + 4)
    button = globalPropPool.getProp('button')
    button2 = MovieUtil.copyProp(button)
    buttons = [button, button2]
    toonTrack = Sequence()
    toonTrack.append(Func(MovieUtil.showProps, buttons, hands))
    toonTrack.append(Func(toon.headsUp, battle, endPos))
    toonTrack.append(ActorInterval(toon, 'pushbutton'))
    toonTrack.append(Func(MovieUtil.removeProps, buttons))
    toonTrack.append(Func(toon.loop, 'neutral'))
    toonTrack.append(Func(toon.setHpr, battle, origHpr))
    slideShowProp = globalPropPool.getProp('slideshow')
    propTrack = Sequence()
    propTrack.append(Wait(slideshowDelay))
    propTrack.append(Func(slideShowProp.show))
    propTrack.append(Func(slideShowProp.setScale, Point3(0.1, 0.1, 0.1)))
    propTrack.append(Func(slideShowProp.reparentTo, battle))
    propTrack.append(Func(slideShowProp.setPos, endPos))
    propTrack.append(LerpScaleInterval(slideShowProp, 1.2, Point3(1.0, 1.0, 1.0)))
    shrinkDuration = 0.4
    totalDuration = 7.1
    propTrackDurationAtThisPoint = propTrack.getDuration()
    waitTime = totalDuration - propTrackDurationAtThisPoint - shrinkDuration
    if waitTime > 0:
        propTrack.append(Wait(waitTime))
    propTrack.append(LerpScaleInterval(nodePath=slideShowProp, scale=Point3(1.0, 1.0, 0.1), duration=shrinkDuration))
    propTrack.append(Func(MovieUtil.removeProp, slideShowProp))
    tracks = Parallel(propTrack, toonTrack)
    targets = lure['target']
    for target in targets:
        suit = target['suit']
        trapProp = suit.battleTrapProp
        if sidestep == 0:
            hp = target['hp']
            kbbonus = target['kbbonus']
            died = target['died']
            revived = target['revived']
            if kbbonus == 1 or hp > 0:
                suitTrack = Sequence()
                suitDelay = 3.8
                suitAnimDuration = 1.5
                opos, ohpr = battle.getActorPosHpr(suit)
                reachDist = MovieUtil.SUIT_LURE_DISTANCE
                reachPos = Point3(opos[0], opos[1] - reachDist, opos[2])
                suitTrack.append(Func(suit.loop, 'neutral'))
                suitTrack.append(Wait(suitDelay))
                suitTrack.append(ActorInterval(suit, 'hypnotized', duration=3.1))
                suitTrack.append(Func(suit.setPos, battle, reachPos))
                suitTrack.append(Func(suit.loop, 'neutral'))
                suitTrack.append(Func(battle.lureSuit, suit))
                if hp > 0:
                    suitTrack.append(__createSuitDamageTrack(battle, suit, hp, lure, trapProp))
                if revived != 0:
                    suitTrack.append(MovieUtil.createSuitReviveTrack(suit, toon, battle, npcs))
                elif died != 0:
                    suitTrack.append(MovieUtil.createSuitDeathTrack(suit, toon, battle, npcs))
                tracks.append(suitTrack)
                tracks.append(lerpSuit(suit, suitDelay + 1.7, 0.7, reachPos, battle, trapProp))
        else:
            tracks.append(Sequence(Wait(2.3), Func(MovieUtil.indicateMissed, suit, 1.1)))

    tracks.append(getSoundTrack('TL_presentation.mp3', delay=2.3, node=toon))
    tracks.append(getSoundTrack('AA_drop_trigger_box.mp3', delay=slideshowDelay, node=toon))
    return tracks
