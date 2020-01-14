from direct.interval.IntervalGlobal import *
from .BattleBase import *
from .BattleProps import *
from .BattleSounds import *
from . import BattleParticles
from .RewardPanel import *
from . import MovieCamera
from direct.directnotify import DirectNotifyGlobal
from . import MovieUtil
from . import MovieNPCSOS
from toontown.toonbase import ToontownBattleGlobals
notify = DirectNotifyGlobal.directNotify.newCategory('MovieSound')
soundFiles = ('AA_sound_bikehorn.ogg', 'AA_sound_whistle.ogg', 'AA_sound_bugle.ogg', 'AA_sound_aoogah.ogg', 'AA_sound_elephant.ogg', 'SZ_DD_foghorn.ogg', 'AA_sound_Opera_Singer.ogg')
appearSoundFiles = ('MG_tag_1.ogg', 'LB_receive_evidence.ogg', 'm_match_trumpet.ogg', 'TL_step_on_rake.ogg', 'toonbldg_grow.ogg', 'mailbox_full_wobble.ogg', 'mailbox_full_wobble.ogg')
hitSoundFiles = ('AA_sound_Opera_Singer_Cog_Glass.ogg',)
tSound = 2.45
tSuitReact = 2.8
DISTANCE_TO_WALK_BACK = MovieUtil.SUIT_LURE_DISTANCE * 0.75
TIME_TO_WALK_BACK = 0.5
if DISTANCE_TO_WALK_BACK == 0:
    TIME_TO_WALK_BACK = 0
INSTRUMENT_SCALE_MODIFIER = 0.5
BEFORE_STARS = 0.5
AFTER_STARS = 1.75

def doSounds(sounds):
    if len(sounds) == 0:
        return (None, None)
    npcArrivals, npcDepartures, npcs = MovieNPCSOS.doNPCTeleports(sounds)
    mtrack = Parallel()
    hitCount = 0
    prevLevel = 0
    prevSounds = [[],
     [],
     [],
     [],
     [],
     [],
     []]
    for sound in sounds:
        level = sound['level']
        prevSounds[level].append(sound)
        for target in sound['target']:
            if target['hp'] > 0:
                hitCount += 1
                break

    delay = 0.0
    for soundList in prevSounds:
        if len(soundList) > 0:
            mtrack.append(__doSoundsLevel(soundList, delay, hitCount, npcs))
            delay += TOON_SOUND_DELAY

    soundTrack = Sequence(npcArrivals, mtrack, npcDepartures)
    targets = sounds[0]['target']
    camDuration = mtrack.getDuration()
    enterDuration = npcArrivals.getDuration()
    exitDuration = npcDepartures.getDuration()
    camTrack = MovieCamera.chooseSoundShot(sounds, targets, camDuration, enterDuration, exitDuration)
    return (soundTrack, camTrack)


def __getSuitTrack(sound, lastSoundThatHit, delay, hitCount, targets, totalDamage, hpbonus, toon, npcs):
    tracks = Parallel()
    attacks = 0
    uberDelay = 0.0
    isUber = 0
    if sound['level'] >= ToontownBattleGlobals.UBER_GAG_LEVEL_INDEX:
        uberDelay = 3.0
        isUber = 1
    for target in targets:
        suit = target['suit']
        if totalDamage > 0 and sound == lastSoundThatHit:
            hp = target['hp']
            died = target['died']
            battle = sound['battle']
            kbbonus = target['kbbonus']
            suitTrack = Sequence()
            showDamage = Func(suit.showHpText, -totalDamage, openEnded=0)
            updateHealthBar = Func(suit.updateHealthBar, totalDamage)
            if isUber:
                breakEffect = BattleParticles.createParticleEffect(file='soundBreak')
                breakEffect.setDepthWrite(0)
                breakEffect.setDepthTest(0)
                breakEffect.setTwoSided(1)
                soundEffect = globalBattleSoundCache.getSound(hitSoundFiles[0])
            suitTrack.append(Wait(delay + tSuitReact))
            if isUber:
                delayTime = random.random()
                suitTrack.append(Wait(delayTime + 2.0))
                suitTrack.append(Func(setPosFromOther, breakEffect, suit, Point3(0, 0.0, suit.getHeight() - 1.0)))
                suitTrack.append(Parallel(showDamage, updateHealthBar, SoundInterval(soundEffect, node=suit), __getPartTrack(breakEffect, 0.0, 1.0, [breakEffect, suit, 0], softStop=-0.5)))
            else:
                suitTrack.append(showDamage)
                suitTrack.append(updateHealthBar)
            if hitCount == 1:
                suitTrack.append(Parallel(ActorInterval(suit, 'squirt-small-react'), MovieUtil.createSuitStunInterval(suit, 0.5, 1.8)))
            else:
                suitTrack.append(ActorInterval(suit, 'squirt-small-react'))
            if kbbonus == 0:
                suitTrack.append(__createSuitResetPosTrack(suit, battle))
                suitTrack.append(Func(battle.unlureSuit, suit))
            bonusTrack = None
            if hpbonus > 0:
                bonusTrack = Sequence(Wait(delay + tSuitReact + delay + 0.75 + uberDelay), Func(suit.showHpText, -hpbonus, 1, openEnded=0))
            suitTrack.append(Func(suit.loop, 'neutral'))
            if bonusTrack == None:
                tracks.append(suitTrack)
            else:
                tracks.append(Parallel(suitTrack, bonusTrack))
        elif totalDamage <= 0:
            tracks.append(Sequence(Wait(2.9), Func(MovieUtil.indicateMissed, suit, 1.0)))

    return tracks


def __doSoundsLevel(sounds, delay, hitCount, npcs):
    lastSoundThatHit = None
    totalDamage = 0
    for sound in sounds:
        for target in sound['target']:
            if target['hp'] > 0:
                lastSoundThatHit = sound
                totalDamage += target['hp']
                break

    mainTrack = Sequence()
    tracks = Parallel()
    deathTracks = Parallel()
    for sound in sounds:
        toon = sound['toon']
        if 'npc' in sound:
            toon = sound['npc']
        level = sound['level']
        targets = sound['target']
        hpbonus = sound['hpbonus']
        attackMTrack = soundfn_array[sound['level']](sound, delay, toon, targets, level)
        tracks.append(Sequence(Wait(delay), attackMTrack))
        tracks.append(__getSuitTrack(sound, lastSoundThatHit, delay, hitCount, targets, totalDamage, hpbonus, toon, npcs))
        for target in targets:
            battle = sound['battle']
            suit = target['suit']
            died = target['died']
            revived = target['revived']
            if revived:
                deathTracks.append(MovieUtil.createSuitReviveTrack(suit, toon, battle, npcs))
            elif died:
                deathTracks.append(MovieUtil.createSuitDeathTrack(suit, toon, battle, npcs))

    mainTrack.append(tracks)
    mainTrack.append(deathTracks)
    return mainTrack


def __createSuitResetPosTrack(suit, battle):
    resetPos, resetHpr = battle.getActorPosHpr(suit)
    moveDist = Vec3(suit.getPos(battle) - resetPos).length()
    moveDuration = 0.5
    walkTrack = Sequence(Func(suit.setHpr, battle, resetHpr), ActorInterval(suit, 'walk', startTime=1, duration=moveDuration, endTime=0.0001), Func(suit.loop, 'neutral'))
    moveTrack = LerpPosInterval(suit, moveDuration, resetPos, other=battle)
    return Parallel(walkTrack, moveTrack)


def createSuitResetPosTrack(suit, battle):
    return __createSuitResetPosTrack(suit, battle)


def __createToonInterval(sound, delay, toon, operaInstrument = None):
    isNPC = 0
    if sound.get('npc'):
        isNPC = 1
    battle = sound['battle']
    hasLuredSuits = __hasLuredSuits(sound)
    if not isNPC:
        oldPos, oldHpr = battle.getActorPosHpr(toon)
        newPos = Point3(oldPos)
        newPos.setY(newPos.getY() - DISTANCE_TO_WALK_BACK)
    retval = Sequence(Wait(delay))
    if DISTANCE_TO_WALK_BACK and hasLuredSuits and not isNPC:
        retval.append(Parallel(ActorInterval(toon, 'walk', startTime=1, duration=TIME_TO_WALK_BACK, endTime=0.0001), LerpPosInterval(toon, TIME_TO_WALK_BACK, newPos, other=battle)))
    if operaInstrument:
        sprayEffect = BattleParticles.createParticleEffect(file='soundWave')
        sprayEffect.setDepthWrite(0)
        sprayEffect.setDepthTest(0)
        sprayEffect.setTwoSided(1)
        I1 = 2.8
        retval.append(ActorInterval(toon, 'sound', playRate=1.0, startTime=0.0, endTime=I1))
        retval.append(Func(setPosFromOther, sprayEffect, operaInstrument, Point3(0, 1.6, -0.18)))
        retval.append(__getPartTrack(sprayEffect, 0.0, 6.0, [sprayEffect, toon, 0], softStop=-3.5))
        retval.append(ActorInterval(toon, 'sound', playRate=1.0, startTime=I1))
    else:
        retval.append(ActorInterval(toon, 'sound'))
    if DISTANCE_TO_WALK_BACK and hasLuredSuits and not isNPC:
        retval.append(Parallel(ActorInterval(toon, 'walk', startTime=0.0001, duration=TIME_TO_WALK_BACK, endTime=1), LerpPosInterval(toon, TIME_TO_WALK_BACK, oldPos, other=battle)))
    retval.append(Func(toon.loop, 'neutral'))
    return retval


def __hasLuredSuits(sound):
    retval = False
    targets = sound['target']
    for target in targets:
        kbbonus = target['kbbonus']
        if kbbonus == 0:
            retval = True
            break

    return retval


def __doBikehorn(sound, delay, toon, targets, level):
    tracks = Parallel()
    instrMin = Vec3(0.001, 0.001, 0.001)
    instrMax = Vec3(0.65, 0.65, 0.65)
    instrMax *= INSTRUMENT_SCALE_MODIFIER
    instrStretch = Vec3(0.6, 1.1, 0.6)
    instrStretch *= INSTRUMENT_SCALE_MODIFIER
    megaphone = globalPropPool.getProp('megaphone')
    megaphone2 = MovieUtil.copyProp(megaphone)
    megaphones = [megaphone, megaphone2]
    instrument = globalPropPool.getProp('bikehorn')
    instrument2 = MovieUtil.copyProp(instrument)
    instruments = [instrument, instrument2]

    def setInstrumentStats(instrument = instrument, instrument2 = instrument2):
        instrument.setPos(-1.1, -1.4, 0.1)
        instrument.setHpr(145, 0, 0)
        instrument.setScale(instrMin)
        instrument2.setPos(-1.1, -1.4, 0.1)
        instrument2.setHpr(145, 0, 0)
        instrument2.setScale(instrMin)

    hands = toon.getRightHands()
    megaphoneShow = Sequence(Func(MovieUtil.showProps, megaphones, hands), Func(MovieUtil.showProps, instruments, hands), Func(setInstrumentStats))
    megaphoneHide = Sequence(Func(MovieUtil.removeProps, megaphones), Func(MovieUtil.removeProps, instruments))
    instrumentAppearSfx = globalBattleSoundCache.getSound(appearSoundFiles[level])
    grow = getScaleIntervals(instruments, duration=0.2, startScale=instrMin, endScale=instrMax)
    instrumentAppear = Parallel(grow, Sequence(Wait(0.15), SoundInterval(instrumentAppearSfx, node=toon)))
    stretchInstr = getScaleBlendIntervals(instruments, duration=0.2, startScale=instrMax, endScale=instrStretch, blendType='easeOut')
    backInstr = getScaleBlendIntervals(instruments, duration=0.2, startScale=instrStretch, endScale=instrMax, blendType='easeIn')
    stretchMega = getScaleBlendIntervals(megaphones, duration=0.2, startScale=megaphone.getScale(), endScale=0.9, blendType='easeOut')
    backMega = getScaleBlendIntervals(megaphones, duration=0.2, startScale=0.9, endScale=megaphone.getScale(), blendType='easeIn')
    attackTrack = Parallel(Sequence(stretchInstr, backInstr), Sequence(stretchMega, backMega))
    hasLuredSuits = __hasLuredSuits(sound)
    delayTime = delay
    if hasLuredSuits:
        delayTime += TIME_TO_WALK_BACK
    megaphoneTrack = Sequence(Wait(delayTime), megaphoneShow, Wait(1.0), instrumentAppear, Wait(3.0), megaphoneHide)
    tracks.append(megaphoneTrack)
    toonTrack = __createToonInterval(sound, delay, toon)
    tracks.append(toonTrack)
    soundEffect = globalBattleSoundCache.getSound(soundFiles[level])
    instrumentshrink = getScaleIntervals(instruments, duration=0.1, startScale=instrMax, endScale=instrMin)
    if soundEffect:
        delayTime = delay + tSound
        if hasLuredSuits:
            delayTime += TIME_TO_WALK_BACK
        soundTrack = Sequence(Wait(delayTime), Parallel(attackTrack, SoundInterval(soundEffect, node=toon)), Wait(0.2), instrumentshrink)
        tracks.append(soundTrack)
    return tracks


def __doWhistle(sound, delay, toon, targets, level):
    tracks = Parallel()
    instrMin = Vec3(0.001, 0.001, 0.001)
    instrMax = Vec3(0.2, 0.2, 0.2)
    instrMax *= INSTRUMENT_SCALE_MODIFIER
    instrStretch = Vec3(0.25, 0.25, 0.25)
    instrStretch *= INSTRUMENT_SCALE_MODIFIER
    megaphone = globalPropPool.getProp('megaphone')
    megaphone2 = MovieUtil.copyProp(megaphone)
    megaphones = [megaphone, megaphone2]
    instrument = globalPropPool.getProp('whistle')
    instrument2 = MovieUtil.copyProp(instrument)
    instruments = [instrument, instrument2]

    def setInstrumentStats(instrument = instrument, instrument2 = instrument2):
        instrument.setPos(-1.2, -1.3, 0.1)
        instrument.setHpr(145, 0, 85)
        instrument.setScale(instrMin)
        instrument2.setPos(-1.2, -1.3, 0.1)
        instrument2.setHpr(145, 0, 85)
        instrument2.setScale(instrMin)

    hands = toon.getRightHands()
    megaphoneShow = Sequence(Func(MovieUtil.showProps, megaphones, hands), Func(MovieUtil.showProps, instruments, hands), Func(setInstrumentStats))
    megaphoneHide = Sequence(Func(MovieUtil.removeProps, megaphones), Func(MovieUtil.removeProps, instruments))
    instrumentAppearSfx = globalBattleSoundCache.getSound(appearSoundFiles[level])
    grow = getScaleIntervals(instruments, duration=0.2, startScale=instrMin, endScale=instrMax)
    instrumentAppear = Parallel(grow, Sequence(Wait(0.05), SoundInterval(instrumentAppearSfx, node=toon)))
    stretchInstr = getScaleBlendIntervals(instruments, duration=0.2, startScale=instrMax, endScale=instrStretch, blendType='easeOut')
    backInstr = getScaleBlendIntervals(instruments, duration=0.2, startScale=instrStretch, endScale=instrMax, blendType='easeIn')
    attackTrack = Sequence(stretchInstr, backInstr)
    hasLuredSuits = __hasLuredSuits(sound)
    delayTime = delay
    if hasLuredSuits:
        delayTime += TIME_TO_WALK_BACK
    megaphoneTrack = Sequence(Wait(delayTime), megaphoneShow, Wait(1.0), instrumentAppear, Wait(3.0), megaphoneHide)
    tracks.append(megaphoneTrack)
    toonTrack = __createToonInterval(sound, delay, toon)
    tracks.append(toonTrack)
    soundEffect = globalBattleSoundCache.getSound(soundFiles[level])
    instrumentshrink = getScaleIntervals(instruments, duration=0.1, startScale=instrMax, endScale=instrMin)
    if soundEffect:
        delayTime = delay + tSound
        if hasLuredSuits:
            delayTime += TIME_TO_WALK_BACK
        soundTrack = Sequence(Wait(delayTime), Parallel(attackTrack, SoundInterval(soundEffect, node=toon)), Wait(0.2), instrumentshrink)
        tracks.append(soundTrack)
    return tracks


def __doBugle(sound, delay, toon, targets, level):
    tracks = Parallel()
    instrMin = Vec3(0.001, 0.001, 0.001)
    instrMax = Vec3(0.4, 0.4, 0.4)
    instrMax *= INSTRUMENT_SCALE_MODIFIER
    instrStretch = Vec3(0.5, 0.5, 0.5)
    instrStretch *= INSTRUMENT_SCALE_MODIFIER
    megaphone = globalPropPool.getProp('megaphone')
    megaphone2 = MovieUtil.copyProp(megaphone)
    megaphones = [megaphone, megaphone2]
    instrument = globalPropPool.getProp('bugle')
    instrument2 = MovieUtil.copyProp(instrument)
    instruments = [instrument, instrument2]

    def setInstrumentStats(instrument = instrument, instrument2 = instrument2):
        instrument.setPos(-1.3, -1.4, 0.1)
        instrument.setHpr(145, 0, 85)
        instrument.setScale(instrMin)
        instrument2.setPos(-1.3, -1.4, 0.1)
        instrument2.setHpr(145, 0, 85)
        instrument2.setScale(instrMin)

    def longshake(models, num):
        inShake = getScaleBlendIntervals(models, duration=0.2, startScale=instrMax, endScale=instrStretch, blendType='easeInOut')
        outShake = getScaleBlendIntervals(models, duration=0.2, startScale=instrStretch, endScale=instrMax, blendType='easeInOut')
        i = 1
        seq = Sequence()
        while i < num:
            if i % 2 == 0:
                seq.append(inShake)
            else:
                seq.append(outShake)
            i += 1

        seq.start()

    hands = toon.getRightHands()
    megaphoneShow = Sequence(Func(MovieUtil.showProps, megaphones, hands), Func(MovieUtil.showProps, instruments, hands), Func(setInstrumentStats))
    megaphoneHide = Sequence(Func(MovieUtil.removeProps, megaphones), Func(MovieUtil.removeProps, instruments))
    instrumentAppearSfx = globalBattleSoundCache.getSound(appearSoundFiles[level])
    grow = getScaleBlendIntervals(instruments, duration=1, startScale=instrMin, endScale=instrMax, blendType='easeInOut')
    instrumentshrink = getScaleIntervals(instruments, duration=0.1, startScale=instrMax, endScale=instrMin)
    instrumentAppear = Sequence(grow, Wait(0), Func(longshake, instruments, 5))
    hasLuredSuits = __hasLuredSuits(sound)
    delayTime = delay
    if hasLuredSuits:
        delayTime += TIME_TO_WALK_BACK
    soundEffect = globalBattleSoundCache.getSound(soundFiles[level])
    megaphoneTrack = Parallel(Sequence(Wait(delay + 1.7), SoundInterval(soundEffect, node=toon)), Sequence(Wait(delayTime), megaphoneShow, Wait(1.7), instrumentAppear, Wait(1), instrumentshrink, Wait(1.5), megaphoneHide))
    tracks.append(megaphoneTrack)
    toonTrack = __createToonInterval(sound, delay, toon)
    tracks.append(toonTrack)
    if soundEffect:
        delayTime = delay + tSound
        if hasLuredSuits:
            delayTime += TIME_TO_WALK_BACK
        soundTrack = Wait(delayTime)
        tracks.append(soundTrack)
    return tracks


def __doAoogah(sound, delay, toon, targets, level):
    tracks = Parallel()
    instrMin = Vec3(0.001, 0.001, 0.001)
    instrMax = Vec3(0.5, 0.5, 0.5)
    instrMax *= INSTRUMENT_SCALE_MODIFIER
    instrStretch = Vec3(1.1, 0.9, 0.4)
    instrStretch *= INSTRUMENT_SCALE_MODIFIER
    megaphone = globalPropPool.getProp('megaphone')
    megaphone2 = MovieUtil.copyProp(megaphone)
    megaphones = [megaphone, megaphone2]
    instrument = globalPropPool.getProp('aoogah')
    instrument2 = MovieUtil.copyProp(instrument)
    instruments = [instrument, instrument2]

    def setInstrumentStats(instrument = instrument, instrument2 = instrument2):
        instrument.setPos(-1.0, -1.5, 0.2)
        instrument.setHpr(145, 0, 85)
        instrument.setScale(instrMin)
        instrument2.setPos(-1.0, -1.5, 0.2)
        instrument2.setHpr(145, 0, 85)
        instrument2.setScale(instrMin)

    hands = toon.getRightHands()
    megaphoneShow = Sequence(Func(MovieUtil.showProps, megaphones, hands), Func(MovieUtil.showProps, instruments, hands), Func(setInstrumentStats))
    megaphoneHide = Sequence(Func(MovieUtil.removeProps, megaphones), Func(MovieUtil.removeProps, instruments))
    instrumentAppearSfx = globalBattleSoundCache.getSound(appearSoundFiles[level])
    grow = getScaleIntervals(instruments, duration=0.2, startScale=instrMin, endScale=instrMax)
    instrumentAppear = Parallel(grow, Sequence(Wait(0.05), SoundInterval(instrumentAppearSfx, node=toon)))
    stretchInstr = getScaleBlendIntervals(instruments, duration=0.2, startScale=instrMax, endScale=instrStretch, blendType='easeOut')
    backInstr = getScaleBlendIntervals(instruments, duration=0.2, startScale=instrStretch, endScale=instrMax, blendType='easeInOut')
    attackTrack = Sequence(stretchInstr, Wait(1), backInstr)
    hasLuredSuits = __hasLuredSuits(sound)
    delayTime = delay
    if hasLuredSuits:
        delayTime += TIME_TO_WALK_BACK
    megaphoneTrack = Sequence(Wait(delayTime), megaphoneShow, Wait(1.0), instrumentAppear, Wait(3.0), megaphoneHide)
    tracks.append(megaphoneTrack)
    toonTrack = __createToonInterval(sound, delay, toon)
    tracks.append(toonTrack)
    soundEffect = globalBattleSoundCache.getSound(soundFiles[level])
    instrumentshrink = getScaleIntervals(instruments, duration=0.1, startScale=instrMax, endScale=instrMin)
    if soundEffect:
        delayTime = delay + tSound
        if hasLuredSuits:
            delayTime += TIME_TO_WALK_BACK
        soundTrack = Sequence(Wait(delayTime), Parallel(attackTrack, SoundInterval(soundEffect, node=toon), Sequence(Wait(1.5), instrumentshrink)))
        tracks.append(soundTrack)
    return tracks


def __doElephant(sound, delay, toon, targets, level):
    tracks = Parallel()
    instrMin = Vec3(0.001, 0.001, 0.001)
    instrMax1 = Vec3(0.3, 0.4, 0.2)
    instrMax1 *= INSTRUMENT_SCALE_MODIFIER
    instrMax2 = Vec3(0.3, 0.3, 0.3)
    instrMax2 *= INSTRUMENT_SCALE_MODIFIER
    instrStretch1 = Vec3(0.3, 0.5, 0.25)
    instrStretch1 *= INSTRUMENT_SCALE_MODIFIER
    instrStretch2 = Vec3(0.3, 0.7, 0.3)
    instrStretch2 *= INSTRUMENT_SCALE_MODIFIER
    megaphone = globalPropPool.getProp('megaphone')
    megaphone2 = MovieUtil.copyProp(megaphone)
    megaphones = [megaphone, megaphone2]
    instrument = globalPropPool.getProp('elephant')
    instrument2 = MovieUtil.copyProp(instrument)
    instruments = [instrument, instrument2]

    def setInstrumentStats(instrument = instrument, instrument2 = instrument2):
        instrument.setPos(-.6, -.9, 0.15)
        instrument.setHpr(145, 0, 85)
        instrument.setScale(instrMin)
        instrument2.setPos(-.6, -.9, 0.15)
        instrument2.setHpr(145, 0, 85)
        instrument2.setScale(instrMin)

    hands = toon.getRightHands()
    megaphoneShow = Sequence(Func(MovieUtil.showProps, megaphones, hands), Func(MovieUtil.showProps, instruments, hands), Func(setInstrumentStats))
    megaphoneHide = Sequence(Func(MovieUtil.removeProps, megaphones), Func(MovieUtil.removeProps, instruments))
    instrumentAppearSfx = globalBattleSoundCache.getSound(appearSoundFiles[level])
    grow1 = getScaleIntervals(instruments, duration=0.3, startScale=instrMin, endScale=instrMax1)
    grow2 = getScaleIntervals(instruments, duration=0.3, startScale=instrMax1, endScale=instrMax2)
    instrumentAppear = Parallel(Sequence(grow1, grow2), Sequence(Wait(0.05), SoundInterval(instrumentAppearSfx, node=toon)))
    stretchInstr1 = getScaleBlendIntervals(instruments, duration=0.1, startScale=instrMax2, endScale=instrStretch1, blendType='easeOut')
    stretchInstr2 = getScaleBlendIntervals(instruments, duration=0.1, startScale=instrStretch1, endScale=instrStretch2, blendType='easeOut')
    stretchInstr = Sequence(stretchInstr1, stretchInstr2)
    backInstr = getScaleBlendIntervals(instruments, duration=0.1, startScale=instrStretch2, endScale=instrMax2, blendType='easeOut')
    attackTrack = Sequence(stretchInstr, Wait(1), backInstr)
    hasLuredSuits = __hasLuredSuits(sound)
    delayTime = delay
    if hasLuredSuits:
        delayTime += TIME_TO_WALK_BACK
    megaphoneTrack = Sequence(Wait(delayTime), megaphoneShow, Wait(1.0), instrumentAppear, Wait(3.0), megaphoneHide)
    tracks.append(megaphoneTrack)
    toonTrack = __createToonInterval(sound, delay, toon)
    tracks.append(toonTrack)
    soundEffect = globalBattleSoundCache.getSound(soundFiles[level])
    instrumentshrink = getScaleIntervals(instruments, duration=0.1, startScale=instrMax2, endScale=instrMin)
    if soundEffect:
        delayTime = delay + tSound
        if hasLuredSuits:
            delayTime += TIME_TO_WALK_BACK
        soundTrack = Sequence(Wait(delayTime), Parallel(attackTrack, SoundInterval(soundEffect, node=toon), Sequence(Wait(1.5), instrumentshrink)))
        tracks.append(soundTrack)
    return tracks


def __doFoghorn(sound, delay, toon, targets, level):
    tracks = Parallel()
    instrMin = Vec3(0.001, 0.001, 0.001)
    instrMax1 = Vec3(0.1, 0.1, 0.1)
    instrMax1 *= INSTRUMENT_SCALE_MODIFIER
    instrMax2 = Vec3(0.3, 0.3, 0.3)
    instrMax2 *= INSTRUMENT_SCALE_MODIFIER
    instrStretch = Vec3(0.4, 0.4, 0.4)
    instrStretch *= INSTRUMENT_SCALE_MODIFIER
    megaphone = globalPropPool.getProp('megaphone')
    megaphone2 = MovieUtil.copyProp(megaphone)
    megaphones = [megaphone, megaphone2]
    instrument = globalPropPool.getProp('fog_horn')
    instrument2 = MovieUtil.copyProp(instrument)
    instruments = [instrument, instrument2]

    def setInstrumentStats(instrument = instrument, instrument2 = instrument2):
        instrument.setPos(-.8, -.9, 0.2)
        instrument.setHpr(145, 0, 0)
        instrument.setScale(instrMin)
        instrument2.setPos(-.8, -.9, 0.2)
        instrument2.setHpr(145, 0, 0)
        instrument2.setScale(instrMin)

    hands = toon.getRightHands()
    megaphoneShow = Sequence(Func(MovieUtil.showProps, megaphones, hands), Func(MovieUtil.showProps, instruments, hands), Func(setInstrumentStats))
    megaphoneHide = Sequence(Func(MovieUtil.removeProps, megaphones), Func(MovieUtil.removeProps, instruments))
    instrumentAppearSfx = globalBattleSoundCache.getSound(appearSoundFiles[level])
    grow1 = getScaleIntervals(instruments, duration=1, startScale=instrMin, endScale=instrMax1)
    grow2 = getScaleIntervals(instruments, duration=0.1, startScale=instrMax1, endScale=instrMax2)
    instrumentAppear = Parallel(Sequence(grow1, grow2), Sequence(Wait(0.05), SoundInterval(instrumentAppearSfx, node=toon)))
    stretchInstr = getScaleBlendIntervals(instruments, duration=0.3, startScale=instrMax2, endScale=instrStretch, blendType='easeOut')
    backInstr = getScaleBlendIntervals(instruments, duration=1.0, startScale=instrStretch, endScale=instrMin, blendType='easeIn')
    spinInstr1 = LerpHprInterval(instrument, duration=1.5, startHpr=Vec3(145, 0, 0), hpr=Vec3(145, 0, 90), blendType='easeInOut')
    spinInstr2 = LerpHprInterval(instrument2, duration=1.5, startHpr=Vec3(145, 0, 0), hpr=Vec3(145, 0, 90), blendType='easeInOut')
    spinInstr = Parallel(spinInstr1, spinInstr2)
    attackTrack = Parallel(Sequence(Wait(0.2), spinInstr), Sequence(stretchInstr, Wait(0.5), backInstr))
    hasLuredSuits = __hasLuredSuits(sound)
    delayTime = delay
    if hasLuredSuits:
        delayTime += TIME_TO_WALK_BACK
    megaphoneTrack = Sequence(Wait(delayTime), megaphoneShow, Wait(1.0), instrumentAppear, Wait(3.0), megaphoneHide)
    tracks.append(megaphoneTrack)
    toonTrack = __createToonInterval(sound, delay, toon)
    tracks.append(toonTrack)
    soundEffect = globalBattleSoundCache.getSound(soundFiles[level])
    if soundEffect:
        delayTime = delay + tSound
        if hasLuredSuits:
            delayTime += TIME_TO_WALK_BACK
        soundTrack = Sequence(Wait(delayTime), Parallel(attackTrack, SoundInterval(soundEffect, node=toon)))
        tracks.append(soundTrack)
    return tracks


def __doOpera(sound, delay, toon, targets, level):
    tracks = Parallel()
    delay = delay
    instrMin = Vec3(0.001, 0.001, 0.001)
    instrMax1 = Vec3(1.7, 1.7, 1.7)
    instrMax1 *= INSTRUMENT_SCALE_MODIFIER
    instrMax2 = Vec3(2.2, 2.2, 2.2)
    instrMax2 *= INSTRUMENT_SCALE_MODIFIER
    instrStretch = Vec3(0.4, 0.4, 0.4)
    instrStretch *= INSTRUMENT_SCALE_MODIFIER
    megaphone = globalPropPool.getProp('megaphone')
    megaphone2 = MovieUtil.copyProp(megaphone)
    megaphones = [megaphone, megaphone2]
    instrument = globalPropPool.getProp('singing')
    instrument2 = MovieUtil.copyProp(instrument)
    instruments = [instrument, instrument2]
    head = instrument2.find('**/opera_singer')
    head.setPos(0, 0, 0)

    def setInstrumentStats(instrument = instrument, instrument2 = instrument2):
        notify.debug('setInstrumentStats')
        newPos = Vec3(-0.8, -0.9, 0.2)
        newPos *= 1.3
        instrument.setPos(newPos[0], newPos[1], newPos[2])
        instrument.setHpr(145, 0, 90)
        instrument.setScale(instrMin)
        instrument2.setPos(newPos[0], newPos[1], newPos[2])
        instrument2.setHpr(145, 0, 90)
        instrument2.setScale(instrMin)

    hands = toon.getRightHands()
    megaphoneShow = Sequence(Func(MovieUtil.showProps, megaphones, hands), Func(MovieUtil.showProps, instruments, hands), Func(setInstrumentStats))
    megaphoneHide = Sequence(Func(MovieUtil.removeProps, megaphones), Func(MovieUtil.removeProps, instruments))
    instrumentAppearSfx = globalBattleSoundCache.getSound(appearSoundFiles[level])
    grow1 = getScaleBlendIntervals(instruments, duration=1, startScale=instrMin, endScale=instrMax1, blendType='easeOut')
    grow2 = getScaleBlendIntervals(instruments, duration=1.1, startScale=instrMax1, endScale=instrMax2, blendType='easeIn')
    shrink2 = getScaleIntervals(instruments, duration=0.1, startScale=instrMax2, endScale=instrMin)
    instrumentAppear = Parallel(Sequence(grow1, grow2, Wait(6.0), shrink2), Sequence(Wait(0.0), SoundInterval(instrumentAppearSfx, node=toon)))
    hasLuredSuits = __hasLuredSuits(sound)
    delayTime = delay
    if hasLuredSuits:
        delayTime += TIME_TO_WALK_BACK
    megaphoneTrack = Sequence(Wait(delayTime), megaphoneShow, Wait(1.0), instrumentAppear, Wait(2.0), megaphoneHide)
    tracks.append(megaphoneTrack)
    toonTrack = __createToonInterval(sound, delay, toon, operaInstrument=instrument)
    tracks.append(toonTrack)
    soundEffect = globalBattleSoundCache.getSound(soundFiles[level])
    if soundEffect:
        delayTime = delay + tSound - 0.3
        if hasLuredSuits:
            delayTime += TIME_TO_WALK_BACK
        soundTrack = Sequence(Wait(delayTime), SoundInterval(soundEffect, node=toon))
        tracks.append(Sequence(Wait(0)))
        tracks.append(soundTrack)
    return tracks


def setPosFromOther(dest, source, offset = Point3(0, 0, 0)):
    pos = render.getRelativePoint(source, offset)
    dest.setPos(pos)
    dest.reparentTo(render)


def getScaleIntervals(props, duration, startScale, endScale):
    tracks = Parallel()
    for prop in props:
        tracks.append(LerpScaleInterval(prop, duration, endScale, startScale=startScale))

    return tracks


def getScaleBlendIntervals(props, duration, startScale, endScale, blendType):
    tracks = Parallel()
    for prop in props:
        tracks.append(LerpScaleInterval(prop, duration, endScale, startScale=startScale, blendType=blendType))

    return tracks


soundfn_array = (__doBikehorn,
 __doWhistle,
 __doBugle,
 __doAoogah,
 __doElephant,
 __doFoghorn,
 __doOpera)

def __getPartTrack(particleEffect, startDelay, durationDelay, partExtraArgs, softStop = 0):
    pEffect = partExtraArgs[0]
    parent = partExtraArgs[1]
    if len(partExtraArgs) == 3:
        worldRelative = partExtraArgs[2]
    else:
        worldRelative = 1
    return Sequence(Wait(startDelay), ParticleInterval(pEffect, parent, worldRelative, duration=durationDelay, cleanup=True, softStopT=softStop))
