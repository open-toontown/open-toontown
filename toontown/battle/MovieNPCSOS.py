from libotp import *
from direct.interval.IntervalGlobal import *
from .BattleProps import *
from .BattleSounds import *
from direct.directnotify import DirectNotifyGlobal
from . import MovieCamera
import random
from . import MovieUtil
from . import BattleParticles
from . import HealJokes
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownBattleGlobals
from toontown.toon import NPCToons
notify = DirectNotifyGlobal.directNotify.newCategory('MovieNPCSOS')
soundFiles = ('AA_heal_tickle.ogg', 'AA_heal_telljoke.ogg', 'AA_heal_smooch.ogg', 'AA_heal_happydance.ogg', 'AA_heal_pixiedust.ogg', 'AA_heal_juggle.ogg')
offset = Point3(0, 4.0, 0)

def __cogsMiss(attack, level, hp):
    return __doCogsMiss(attack, level, hp)


def __toonsHit(attack, level, hp):
    return __doToonsHit(attack, level, hp)


def __restockGags(attack, level, hp):
    return __doRestockGags(attack, level, hp)


NPCSOSfn_dict = {ToontownBattleGlobals.NPC_COGS_MISS: __cogsMiss,
 ToontownBattleGlobals.NPC_TOONS_HIT: __toonsHit,
 ToontownBattleGlobals.NPC_RESTOCK_GAGS: __restockGags}

def doNPCSOSs(NPCSOSs):
    if len(NPCSOSs) == 0:
        return (None, None)
    track = Sequence()
    textTrack = Sequence()
    for n in NPCSOSs:
        ival, textIval = __doNPCSOS(n)
        if ival:
            track.append(ival)
            textTrack.append(textIval)

    camDuration = track.getDuration()
    if camDuration > 0.0:
        camTrack = MovieCamera.chooseHealShot(NPCSOSs, camDuration)
    else:
        camTrack = Sequence()
    return (track, Parallel(camTrack, textTrack))


def __doNPCSOS(sos):
    npcId = sos['npcId']
    track, level, hp = NPCToons.getNPCTrackLevelHp(npcId)
    if track != None:
        return NPCSOSfn_dict[track](sos, level, hp)
    else:
        return __cogsMiss(sos, 0, 0)
    return


def __healToon(toon, hp, ineffective = 0):
    notify.debug('healToon() - toon: %d hp: %d ineffective: %d' % (toon.doId, hp, ineffective))
    if ineffective == 1:
        laughter = random.choice(TTLocalizer.MovieHealLaughterMisses)
    else:
        maxDam = ToontownBattleGlobals.AvPropDamage[0][1][0][1]
        if hp >= maxDam - 1:
            laughter = random.choice(TTLocalizer.MovieHealLaughterHits2)
        else:
            laughter = random.choice(TTLocalizer.MovieHealLaughterHits1)
    toon.setChatAbsolute(laughter, CFSpeech | CFTimeout)


def __getSoundTrack(level, delay, duration = None, node = None):
    soundEffect = globalBattleSoundCache.getSound(soundFiles[level])
    soundIntervals = Sequence()
    if soundEffect:
        if duration:
            playSound = SoundInterval(soundEffect, duration=duration, node=node)
        else:
            playSound = SoundInterval(soundEffect, node=node)
        soundIntervals.append(Wait(delay))
        soundIntervals.append(playSound)
    return soundIntervals


def teleportIn(attack, npc, pos = Point3(0, 0, 0), hpr = Vec3(180.0, 0.0, 0.0)):
    a = Func(npc.reparentTo, attack['battle'])
    b = Func(npc.setPos, pos)
    c = Func(npc.setHpr, hpr)
    d = Func(npc.pose, 'teleport', npc.getNumFrames('teleport') - 1)
    e = npc.getTeleportInTrack()
    ee = Func(npc.addActive)
    f = Func(npc.setChatAbsolute, TTLocalizer.MovieNPCSOSGreeting % attack['toon'].getName(), CFSpeech | CFTimeout)
    g = ActorInterval(npc, 'wave')
    h = Func(npc.loop, 'neutral')
    i = Func(npc.clearChat)
    return Sequence(a, b, c, d, e, ee, f, g, h, i)


def teleportOut(attack, npc):
    if npc.style.getGender() == 'm':
        a = ActorInterval(npc, 'bow')
    else:
        a = ActorInterval(npc, 'curtsy')
    b = Func(npc.setChatAbsolute, TTLocalizer.MovieNPCSOSGoodbye, CFSpeech | CFTimeout)
    c = npc.getTeleportOutTrack()
    d = Func(npc.removeActive)
    e = Func(npc.detachNode)
    f = Func(npc.delete)
    return Sequence(a, b, c, d, e, f)


def __getPartTrack(particleEffect, startDelay, durationDelay, partExtraArgs):
    pEffect = partExtraArgs[0]
    parent = partExtraArgs[1]
    if len(partExtraArgs) == 3:
        worldRelative = partExtraArgs[2]
    else:
        worldRelative = 1
    return Sequence(Wait(startDelay), ParticleInterval(pEffect, parent, worldRelative, duration=durationDelay, cleanup=True))


def __doSprinkle(attack, recipients, hp = 0):
    toon = NPCToons.createLocalNPC(attack['npcId'])
    if toon == None:
        return
    targets = attack[recipients]
    level = 4
    battle = attack['battle']
    track = Sequence(teleportIn(attack, toon))

    def face90(target, toon, battle):
        vec = Point3(target.getPos(battle) - toon.getPos(battle))
        vec.setZ(0)
        temp = vec[0]
        vec.setX(-vec[1])
        vec.setY(temp)
        targetPoint = Point3(toon.getPos(battle) + vec)
        toon.headsUp(battle, targetPoint)

    delay = 2.5
    effectTrack = Sequence()
    for target in targets:
        sprayEffect = BattleParticles.createParticleEffect(file='pixieSpray')
        dropEffect = BattleParticles.createParticleEffect(file='pixieDrop')
        explodeEffect = BattleParticles.createParticleEffect(file='pixieExplode')
        poofEffect = BattleParticles.createParticleEffect(file='pixiePoof')
        wallEffect = BattleParticles.createParticleEffect(file='pixieWall')
        mtrack = Parallel(__getPartTrack(sprayEffect, 1.5, 0.5, [sprayEffect, toon, 0]), __getPartTrack(dropEffect, 1.9, 2.0, [dropEffect, target, 0]), __getPartTrack(explodeEffect, 2.7, 1.0, [explodeEffect, toon, 0]), __getPartTrack(poofEffect, 3.4, 1.0, [poofEffect, target, 0]), __getPartTrack(wallEffect, 4.05, 1.2, [wallEffect, toon, 0]), __getSoundTrack(level, 2, duration=3.1, node=toon), Sequence(Func(face90, target, toon, battle), ActorInterval(toon, 'sprinkle-dust')), Sequence(Wait(delay), Func(__healToon, target, hp)))
        effectTrack.append(mtrack)

    track.append(effectTrack)
    track.append(Func(toon.setHpr, Vec3(180.0, 0.0, 0.0)))
    track.append(teleportOut(attack, toon))
    return track


def __doSmooch(attack, hp = 0):
    toon = NPCToons.createLocalNPC(attack['npcId'])
    if toon == None:
        return
    targets = attack['toons']
    level = 2
    battle = attack['battle']
    track = Sequence(teleportIn(attack, toon))
    lipstick = globalPropPool.getProp('lipstick')
    lipstick2 = MovieUtil.copyProp(lipstick)
    lipsticks = [lipstick, lipstick2]
    rightHands = toon.getRightHands()
    dScale = 0.5
    lipstickTrack = Sequence(Func(MovieUtil.showProps, lipsticks, rightHands, Point3(-0.27, -0.24, -0.95), Point3(-118, -10.6, -25.9)), MovieUtil.getScaleIntervals(lipsticks, dScale, MovieUtil.PNT3_NEARZERO, MovieUtil.PNT3_ONE), Wait(toon.getDuration('smooch') - 2.0 * dScale), MovieUtil.getScaleIntervals(lipsticks, dScale, MovieUtil.PNT3_ONE, MovieUtil.PNT3_NEARZERO))
    lips = globalPropPool.getProp('lips')
    dScale = 0.5
    tLips = 2.5
    tThrow = 115.0 / toon.getFrameRate('smooch')
    dThrow = 0.5

    def getLipPos(toon = toon):
        toon.pose('smooch', 57)
        toon.update(0)
        hand = toon.getRightHands()[0]
        return hand.getPos(render)

    effectTrack = Sequence()
    for target in targets:
        lipcopy = MovieUtil.copyProp(lips)
        lipsTrack = Sequence(Wait(tLips), Func(MovieUtil.showProp, lipcopy, render, getLipPos), Func(lipcopy.setBillboardPointWorld), LerpScaleInterval(lipcopy, dScale, Point3(3, 3, 3), startScale=MovieUtil.PNT3_NEARZERO), Wait(tThrow - tLips - dScale), LerpPosInterval(lipcopy, dThrow, Point3(target.getPos() + Point3(0, 0, target.getHeight()))), Func(MovieUtil.removeProp, lipcopy))
        delay = tThrow + dThrow
        mtrack = Parallel(lipstickTrack, lipsTrack, __getSoundTrack(level, 2, node=toon), Sequence(ActorInterval(toon, 'smooch')), Sequence(Wait(delay), ActorInterval(target, 'conked')), Sequence(Wait(delay), Func(__healToon, target, hp)))
        effectTrack.append(mtrack)

    effectTrack.append(Func(MovieUtil.removeProps, lipsticks))
    track.append(effectTrack)
    track.append(teleportOut(attack, toon))
    track.append(Func(target.clearChat))
    return track


def __doToonsHit(attack, level, hp):
    track = __doSprinkle(attack, 'toons', hp)
    pbpText = attack['playByPlayText']
    pbpTrack = pbpText.getShowInterval(TTLocalizer.MovieNPCSOSToonsHit, track.getDuration())
    return (track, pbpTrack)


def __doCogsMiss(attack, level, hp):
    track = __doSprinkle(attack, 'suits', hp)
    pbpText = attack['playByPlayText']
    pbpTrack = pbpText.getShowInterval(TTLocalizer.MovieNPCSOSCogsMiss, track.getDuration())
    return (track, pbpTrack)


def __doRestockGags(attack, level, hp):
    track = __doSmooch(attack, hp)
    pbpText = attack['playByPlayText']
    if level == ToontownBattleGlobals.HEAL_TRACK:
        text = TTLocalizer.MovieNPCSOSHeal
    elif level == ToontownBattleGlobals.TRAP_TRACK:
        text = TTLocalizer.MovieNPCSOSTrap
    elif level == ToontownBattleGlobals.LURE_TRACK:
        text = TTLocalizer.MovieNPCSOSLure
    elif level == ToontownBattleGlobals.SOUND_TRACK:
        text = TTLocalizer.MovieNPCSOSSound
    elif level == ToontownBattleGlobals.THROW_TRACK:
        text = TTLocalizer.MovieNPCSOSThrow
    elif level == ToontownBattleGlobals.SQUIRT_TRACK:
        text = TTLocalizer.MovieNPCSOSSquirt
    elif level == ToontownBattleGlobals.DROP_TRACK:
        text = TTLocalizer.MovieNPCSOSDrop
    elif level == -1:
        text = TTLocalizer.MovieNPCSOSAll
    pbpTrack = pbpText.getShowInterval(TTLocalizer.MovieNPCSOSRestockGags % text, track.getDuration())
    return (track, pbpTrack)


def doNPCTeleports(attacks):
    npcs = []
    npcDatas = []
    arrivals = Sequence()
    departures = Parallel()
    for attack in attacks:
        if 'npcId' in attack:
            npcId = attack['npcId']
            npc = NPCToons.createLocalNPC(npcId)
            if npc != None:
                npcs.append(npc)
                attack['npc'] = npc
                toon = attack['toon']
                battle = attack['battle']
                pos = toon.getPos(battle) + offset
                hpr = toon.getHpr(battle)
                npcDatas.append((npc, battle, hpr))
                arrival = teleportIn(attack, npc, pos=pos)
                arrivals.append(arrival)
                departure = teleportOut(attack, npc)
                departures.append(departure)

    turns = Parallel()
    unturns = Parallel()
    hpr = Vec3(180.0, 0, 0)
    for npc in npcDatas:
        turns.append(Func(npc[0].setHpr, npc[1], npc[2]))
        unturns.append(Func(npc[0].setHpr, npc[1], hpr))

    arrivals.append(turns)
    unturns.append(departures)
    return (arrivals, unturns, npcs)
