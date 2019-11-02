from direct.interval.IntervalGlobal import *
from BattleBase import *
from BattleProps import *
from direct.directnotify import DirectNotifyGlobal
import random
from direct.particles import ParticleEffect
import BattleParticles
import BattleProps
from toontown.toonbase import TTLocalizer
notify = DirectNotifyGlobal.directNotify.newCategory('MovieUtil')
SUIT_LOSE_DURATION = 6.0
SUIT_LURE_DISTANCE = 2.6
SUIT_LURE_DOLLAR_DISTANCE = 5.1
SUIT_EXTRA_REACH_DISTANCE = 0.9
SUIT_EXTRA_RAKE_DISTANCE = 1.1
SUIT_TRAP_DISTANCE = 2.6
SUIT_TRAP_RAKE_DISTANCE = 4.5
SUIT_TRAP_MARBLES_DISTANCE = 3.7
SUIT_TRAP_TNT_DISTANCE = 5.1
PNT3_NEARZERO = Point3(0.01, 0.01, 0.01)
PNT3_ZERO = Point3(0.0, 0.0, 0.0)
PNT3_ONE = Point3(1.0, 1.0, 1.0)
largeSuits = ['f',
 'cc',
 'gh',
 'tw',
 'bf',
 'sc',
 'ds',
 'hh',
 'cr',
 'tbc',
 'bs',
 'sd',
 'le',
 'bw',
 'nc',
 'mb',
 'ls',
 'rb',
 'ms',
 'tf',
 'm',
 'mh']
shotDirection = 'left'

def avatarDodge(leftAvatars, rightAvatars, leftData, rightData):
    if len(leftAvatars) > len(rightAvatars):
        PoLR = rightAvatars
        PoMR = leftAvatars
    else:
        PoLR = leftAvatars
        PoMR = rightAvatars
    upper = 1 + 4 * abs(len(leftAvatars) - len(rightAvatars))
    if random.randint(0, upper) > 0:
        avDodgeList = PoLR
    else:
        avDodgeList = PoMR
    if avDodgeList is leftAvatars:
        data = leftData
    else:
        data = rightData
    return (avDodgeList, data)


def avatarHide(avatar):
    notify.debug('avatarHide(%d)' % avatar.doId)
    if hasattr(avatar, 'battleTrapProp'):
        notify.debug('avatar.battleTrapProp = %s' % avatar.battleTrapProp)
    avatar.detachNode()


def copyProp(prop):
    from direct.actor import Actor
    if isinstance(prop, Actor.Actor):
        return Actor.Actor(other=prop)
    else:
        return prop.copyTo(hidden)


def showProp(prop, hand, pos = None, hpr = None, scale = None):
    prop.reparentTo(hand)
    if pos:
        if callable(pos):
            pos = pos()
        prop.setPos(pos)
    if hpr:
        if callable(hpr):
            hpr = hpr()
        prop.setHpr(hpr)
    if scale:
        if callable(scale):
            scale = scale()
        prop.setScale(scale)


def showProps(props, hands, pos = None, hpr = None, scale = None):
    index = 0
    for prop in props:
        prop.reparentTo(hands[index])
        if pos:
            prop.setPos(pos)
        if hpr:
            prop.setHpr(hpr)
        if scale:
            prop.setScale(scale)
        index += 1


def hideProps(props):
    for prop in props:
        prop.detachNode()


def removeProp(prop):
    from direct.actor import Actor
    if prop.isEmpty() == 1 or prop == None:
        return
    prop.detachNode()
    if isinstance(prop, Actor.Actor):
        prop.cleanup()
    else:
        prop.removeNode()
    return


def removeProps(props):
    for prop in props:
        removeProp(prop)


def getActorIntervals(props, anim):
    tracks = Parallel()
    for prop in props:
        tracks.append(ActorInterval(prop, anim))

    return tracks


def getScaleIntervals(props, duration, startScale, endScale):
    tracks = Parallel()
    for prop in props:
        tracks.append(LerpScaleInterval(prop, duration, endScale, startScale=startScale))

    return tracks


def avatarFacePoint(av, other = render):
    pnt = av.getPos(other)
    pnt.setZ(pnt[2] + av.getHeight())
    return pnt


def insertDeathSuit(suit, deathSuit, battle = None, pos = None, hpr = None):
    holdParent = suit.getParent()
    if suit.getVirtual():
        virtualize(deathSuit)
    avatarHide(suit)
    if deathSuit != None and not deathSuit.isEmpty():
        if holdParent and 0:
            deathSuit.reparentTo(holdParent)
        else:
            deathSuit.reparentTo(render)
        if battle != None and pos != None:
            deathSuit.setPos(battle, pos)
        if battle != None and hpr != None:
            deathSuit.setHpr(battle, hpr)
    return


def removeDeathSuit(suit, deathSuit):
    notify.debug('removeDeathSuit()')
    if not deathSuit.isEmpty():
        deathSuit.detachNode()
        suit.cleanupLoseActor()


def insertReviveSuit(suit, deathSuit, battle = None, pos = None, hpr = None):
    holdParent = suit.getParent()
    if suit.getVirtual():
        virtualize(deathSuit)
    suit.hide()
    if deathSuit != None and not deathSuit.isEmpty():
        if holdParent and 0:
            deathSuit.reparentTo(holdParent)
        else:
            deathSuit.reparentTo(render)
        if battle != None and pos != None:
            deathSuit.setPos(battle, pos)
        if battle != None and hpr != None:
            deathSuit.setHpr(battle, hpr)
    return


def removeReviveSuit(suit, deathSuit):
    notify.debug('removeDeathSuit()')
    suit.setSkelecog(1)
    suit.show()
    if not deathSuit.isEmpty():
        deathSuit.detachNode()
        suit.cleanupLoseActor()
    suit.healthBar.show()
    suit.reseatHealthBarForSkele()


def virtualize(deathsuit):
    actorNode = deathsuit.find('**/__Actor_modelRoot')
    actorCollection = actorNode.findAllMatches('*')
    parts = ()
    for thingIndex in range(0, actorCollection.getNumPaths()):
        thing = actorCollection[thingIndex]
        if thing.getName() not in ('joint_attachMeter', 'joint_nameTag', 'def_nameTag'):
            thing.setColorScale(1.0, 0.0, 0.0, 1.0)
            thing.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd))
            thing.setDepthWrite(False)
            thing.setBin('fixed', 1)


def createTrainTrackAppearTrack(dyingSuit, toon, battle, npcs):
    retval = Sequence()
    return retval
    possibleSuits = []
    for suitAttack in battle.movie.suitAttackDicts:
        suit = suitAttack['suit']
        if not suit == dyingSuit:
            if hasattr(suit, 'battleTrapProp') and suit.battleTrapProp and suit.battleTrapProp.getName() == 'traintrack':
                possibleSuits.append(suitAttack['suit'])

    closestXDistance = 10000
    closestSuit = None
    for suit in possibleSuits:
        suitPoint, suitHpr = battle.getActorPosHpr(suit)
        xDistance = abs(suitPoint.getX())
        if xDistance < closestXDistance:
            closestSuit = suit
            closestXDistance = xDistance

    if closestSuit and closestSuit.battleTrapProp.isHidden():
        closestSuit.battleTrapProp.setColorScale(1, 1, 1, 0)
        closestSuit.battleTrapProp.show()
        newRelativePos = dyingSuit.battleTrapProp.getPos(closestSuit)
        newHpr = dyingSuit.battleTrapProp.getHpr(closestSuit)
        closestSuit.battleTrapProp.setPos(newRelativePos)
        closestSuit.battleTrapProp.setHpr(newHpr)
        retval.append(LerpColorScaleInterval(closestSuit.battleTrapProp, 3.0, Vec4(1, 1, 1, 1)))
    else:
        notify.debug('could not find closest suit, returning empty sequence')
    return retval


def createSuitReviveTrack(suit, toon, battle, npcs = []):
    suitTrack = Sequence()
    suitPos, suitHpr = battle.getActorPosHpr(suit)
    if hasattr(suit, 'battleTrapProp') and suit.battleTrapProp and suit.battleTrapProp.getName() == 'traintrack' and not suit.battleTrapProp.isHidden():
        suitTrack.append(createTrainTrackAppearTrack(suit, toon, battle, npcs))
    deathSuit = suit.getLoseActor()
    suitTrack.append(Func(notify.debug, 'before insertDeathSuit'))
    suitTrack.append(Func(insertReviveSuit, suit, deathSuit, battle, suitPos, suitHpr))
    suitTrack.append(Func(notify.debug, 'before actorInterval lose'))
    suitTrack.append(ActorInterval(deathSuit, 'lose', duration=SUIT_LOSE_DURATION))
    suitTrack.append(Func(notify.debug, 'before removeDeathSuit'))
    suitTrack.append(Func(removeReviveSuit, suit, deathSuit, name='remove-death-suit'))
    suitTrack.append(Func(notify.debug, 'after removeDeathSuit'))
    suitTrack.append(Func(suit.loop, 'neutral'))
    spinningSound = base.loadSfx('phase_3.5/audio/sfx/Cog_Death.mp3')
    deathSound = base.loadSfx('phase_3.5/audio/sfx/ENC_cogfall_apart.mp3')
    deathSoundTrack = Sequence(Wait(0.8), SoundInterval(spinningSound, duration=1.2, startTime=1.5, volume=0.2, node=suit), SoundInterval(spinningSound, duration=3.0, startTime=0.6, volume=0.8, node=suit), SoundInterval(deathSound, volume=0.32, node=suit))
    BattleParticles.loadParticles()
    smallGears = BattleParticles.createParticleEffect(file='gearExplosionSmall')
    singleGear = BattleParticles.createParticleEffect('GearExplosion', numParticles=1)
    smallGearExplosion = BattleParticles.createParticleEffect('GearExplosion', numParticles=10)
    bigGearExplosion = BattleParticles.createParticleEffect('BigGearExplosion', numParticles=30)
    gearPoint = Point3(suitPos.getX(), suitPos.getY(), suitPos.getZ() + suit.height - 0.2)
    smallGears.setPos(gearPoint)
    singleGear.setPos(gearPoint)
    smallGears.setDepthWrite(False)
    singleGear.setDepthWrite(False)
    smallGearExplosion.setPos(gearPoint)
    bigGearExplosion.setPos(gearPoint)
    smallGearExplosion.setDepthWrite(False)
    bigGearExplosion.setDepthWrite(False)
    explosionTrack = Sequence()
    explosionTrack.append(Wait(5.4))
    explosionTrack.append(createKapowExplosionTrack(battle, explosionPoint=gearPoint))
    gears1Track = Sequence(Wait(2.1), ParticleInterval(smallGears, battle, worldRelative=0, duration=4.3, cleanup=True), name='gears1Track')
    gears2MTrack = Track((0.0, explosionTrack), (0.7, ParticleInterval(singleGear, battle, worldRelative=0, duration=5.7, cleanup=True)), (5.2, ParticleInterval(smallGearExplosion, battle, worldRelative=0, duration=1.2, cleanup=True)), (5.4, ParticleInterval(bigGearExplosion, battle, worldRelative=0, duration=1.0, cleanup=True)), name='gears2MTrack')
    toonMTrack = Parallel(name='toonMTrack')
    for mtoon in battle.toons:
        toonMTrack.append(Sequence(Wait(1.0), ActorInterval(mtoon, 'duck'), ActorInterval(mtoon, 'duck', startTime=1.8), Func(mtoon.loop, 'neutral')))

    for mtoon in npcs:
        toonMTrack.append(Sequence(Wait(1.0), ActorInterval(mtoon, 'duck'), ActorInterval(mtoon, 'duck', startTime=1.8), Func(mtoon.loop, 'neutral')))

    return Parallel(suitTrack, deathSoundTrack, gears1Track, gears2MTrack, toonMTrack)


def createSuitDeathTrack(suit, toon, battle, npcs = []):
    suitTrack = Sequence()
    suitPos, suitHpr = battle.getActorPosHpr(suit)
    if hasattr(suit, 'battleTrapProp') and suit.battleTrapProp and suit.battleTrapProp.getName() == 'traintrack' and not suit.battleTrapProp.isHidden():
        suitTrack.append(createTrainTrackAppearTrack(suit, toon, battle, npcs))
    deathSuit = suit.getLoseActor()
    suitTrack.append(Func(notify.debug, 'before insertDeathSuit'))
    suitTrack.append(Func(insertDeathSuit, suit, deathSuit, battle, suitPos, suitHpr))
    suitTrack.append(Func(notify.debug, 'before actorInterval lose'))
    suitTrack.append(ActorInterval(deathSuit, 'lose', duration=SUIT_LOSE_DURATION))
    suitTrack.append(Func(notify.debug, 'before removeDeathSuit'))
    suitTrack.append(Func(removeDeathSuit, suit, deathSuit, name='remove-death-suit'))
    suitTrack.append(Func(notify.debug, 'after removeDeathSuit'))
    spinningSound = base.loadSfx('phase_3.5/audio/sfx/Cog_Death.mp3')
    deathSound = base.loadSfx('phase_3.5/audio/sfx/ENC_cogfall_apart.mp3')
    deathSoundTrack = Sequence(Wait(0.8), SoundInterval(spinningSound, duration=1.2, startTime=1.5, volume=0.2, node=deathSuit), SoundInterval(spinningSound, duration=3.0, startTime=0.6, volume=0.8, node=deathSuit), SoundInterval(deathSound, volume=0.32, node=deathSuit))
    BattleParticles.loadParticles()
    smallGears = BattleParticles.createParticleEffect(file='gearExplosionSmall')
    singleGear = BattleParticles.createParticleEffect('GearExplosion', numParticles=1)
    smallGearExplosion = BattleParticles.createParticleEffect('GearExplosion', numParticles=10)
    bigGearExplosion = BattleParticles.createParticleEffect('BigGearExplosion', numParticles=30)
    gearPoint = Point3(suitPos.getX(), suitPos.getY(), suitPos.getZ() + suit.height - 0.2)
    smallGears.setPos(gearPoint)
    singleGear.setPos(gearPoint)
    smallGears.setDepthWrite(False)
    singleGear.setDepthWrite(False)
    smallGearExplosion.setPos(gearPoint)
    bigGearExplosion.setPos(gearPoint)
    smallGearExplosion.setDepthWrite(False)
    bigGearExplosion.setDepthWrite(False)
    explosionTrack = Sequence()
    explosionTrack.append(Wait(5.4))
    explosionTrack.append(createKapowExplosionTrack(battle, explosionPoint=gearPoint))
    gears1Track = Sequence(Wait(2.1), ParticleInterval(smallGears, battle, worldRelative=0, duration=4.3, cleanup=True), name='gears1Track')
    gears2MTrack = Track((0.0, explosionTrack), (0.7, ParticleInterval(singleGear, battle, worldRelative=0, duration=5.7, cleanup=True)), (5.2, ParticleInterval(smallGearExplosion, battle, worldRelative=0, duration=1.2, cleanup=True)), (5.4, ParticleInterval(bigGearExplosion, battle, worldRelative=0, duration=1.0, cleanup=True)), name='gears2MTrack')
    toonMTrack = Parallel(name='toonMTrack')
    for mtoon in battle.toons:
        toonMTrack.append(Sequence(Wait(1.0), ActorInterval(mtoon, 'duck'), ActorInterval(mtoon, 'duck', startTime=1.8), Func(mtoon.loop, 'neutral')))

    for mtoon in npcs:
        toonMTrack.append(Sequence(Wait(1.0), ActorInterval(mtoon, 'duck'), ActorInterval(mtoon, 'duck', startTime=1.8), Func(mtoon.loop, 'neutral')))

    return Parallel(suitTrack, deathSoundTrack, gears1Track, gears2MTrack, toonMTrack)


def createSuitDodgeMultitrack(tDodge, suit, leftSuits, rightSuits):
    suitTracks = Parallel()
    suitDodgeList, sidestepAnim = avatarDodge(leftSuits, rightSuits, 'sidestep-left', 'sidestep-right')
    for s in suitDodgeList:
        suitTracks.append(Sequence(ActorInterval(s, sidestepAnim), Func(s.loop, 'neutral')))

    suitTracks.append(Sequence(ActorInterval(suit, sidestepAnim), Func(suit.loop, 'neutral')))
    suitTracks.append(Func(indicateMissed, suit))
    return Sequence(Wait(tDodge), suitTracks)


def createToonDodgeMultitrack(tDodge, toon, leftToons, rightToons):
    toonTracks = Parallel()
    if len(leftToons) > len(rightToons):
        PoLR = rightToons
        PoMR = leftToons
    else:
        PoLR = leftToons
        PoMR = rightToons
    upper = 1 + 4 * abs(len(leftToons) - len(rightToons))
    if random.randint(0, upper) > 0:
        toonDodgeList = PoLR
    else:
        toonDodgeList = PoMR
    if toonDodgeList is leftToons:
        sidestepAnim = 'sidestep-left'
        for t in toonDodgeList:
            toonTracks.append(Sequence(ActorInterval(t, sidestepAnim), Func(t.loop, 'neutral')))

    else:
        sidestepAnim = 'sidestep-right'
    toonTracks.append(Sequence(ActorInterval(toon, sidestepAnim), Func(toon.loop, 'neutral')))
    toonTracks.append(Func(indicateMissed, toon))
    return Sequence(Wait(tDodge), toonTracks)


def createSuitTeaseMultiTrack(suit, delay = 0.01):
    suitTrack = Sequence(Wait(delay), ActorInterval(suit, 'victory', startTime=0.5, endTime=1.9), Func(suit.loop, 'neutral'))
    missedTrack = Sequence(Wait(delay + 0.2), Func(indicateMissed, suit, 0.9))
    return Parallel(suitTrack, missedTrack)


SPRAY_LEN = 1.5

def getSprayTrack(battle, color, origin, target, dScaleUp, dHold, dScaleDown, horizScale = 1.0, vertScale = 1.0, parent = render):
    track = Sequence()
    sprayProp = globalPropPool.getProp('spray')
    sprayScale = hidden.attachNewNode('spray-parent')
    sprayRot = hidden.attachNewNode('spray-rotate')
    spray = sprayRot
    spray.setColor(color)
    if color[3] < 1.0:
        spray.setTransparency(1)

    def showSpray(sprayScale, sprayRot, sprayProp, origin, target, parent):
        if callable(origin):
            origin = origin()
        if callable(target):
            target = target()
        sprayRot.reparentTo(parent)
        sprayRot.clearMat()
        sprayScale.reparentTo(sprayRot)
        sprayScale.clearMat()
        sprayProp.reparentTo(sprayScale)
        sprayProp.clearMat()
        sprayRot.setPos(origin)
        sprayRot.lookAt(Point3(target))

    track.append(Func(battle.movie.needRestoreRenderProp, sprayProp))
    track.append(Func(showSpray, sprayScale, sprayRot, sprayProp, origin, target, parent))

    def calcTargetScale(target = target, origin = origin, horizScale = horizScale, vertScale = vertScale):
        if callable(target):
            target = target()
        if callable(origin):
            origin = origin()
        distance = Vec3(target - origin).length()
        yScale = distance / SPRAY_LEN
        targetScale = Point3(yScale * horizScale, yScale, yScale * vertScale)
        return targetScale

    track.append(LerpScaleInterval(sprayScale, dScaleUp, calcTargetScale, startScale=PNT3_NEARZERO))
    track.append(Wait(dHold))

    def prepareToShrinkSpray(spray, sprayProp, origin, target):
        if callable(target):
            target = target()
        if callable(origin):
            origin = origin()
        sprayProp.setPos(Point3(0.0, -SPRAY_LEN, 0.0))
        spray.setPos(target)

    track.append(Func(prepareToShrinkSpray, spray, sprayProp, origin, target))
    track.append(LerpScaleInterval(sprayScale, dScaleDown, PNT3_NEARZERO))

    def hideSpray(spray, sprayScale, sprayRot, sprayProp, propPool):
        sprayProp.detachNode()
        removeProp(sprayProp)
        sprayRot.removeNode()
        sprayScale.removeNode()

    track.append(Func(hideSpray, spray, sprayScale, sprayRot, sprayProp, globalPropPool))
    track.append(Func(battle.movie.clearRenderProp, sprayProp))
    return track


T_HOLE_LEAVES_HAND = 1.708
T_TELEPORT_ANIM = 3.3
T_HOLE_CLOSES = 0.3

def getToonTeleportOutInterval(toon):
    holeActors = toon.getHoleActors()
    holes = [holeActors[0], holeActors[1]]
    hole = holes[0]
    hole2 = holes[1]
    hands = toon.getRightHands()
    delay = T_HOLE_LEAVES_HAND
    dur = T_TELEPORT_ANIM
    holeTrack = Sequence()
    holeTrack.append(Func(showProps, holes, hands))
    (holeTrack.append(Wait(0.5)),)
    holeTrack.append(Func(base.playSfx, toon.getSoundTeleport()))
    holeTrack.append(Wait(delay - 0.5))
    holeTrack.append(Func(hole.reparentTo, toon))
    holeTrack.append(Func(hole2.reparentTo, hidden))
    holeAnimTrack = Sequence()
    holeAnimTrack.append(ActorInterval(hole, 'hole', duration=dur))
    holeAnimTrack.append(Func(hideProps, holes))
    runTrack = Sequence(ActorInterval(toon, 'teleport', duration=dur), Wait(T_HOLE_CLOSES), Func(toon.detachNode))
    return Parallel(runTrack, holeAnimTrack, holeTrack)


def getToonTeleportInInterval(toon):
    hole = toon.getHoleActors()[0]
    holeAnimTrack = Sequence()
    holeAnimTrack.append(Func(toon.detachNode))
    holeAnimTrack.append(Func(hole.reparentTo, toon))
    pos = Point3(0, -2.4, 0)
    holeAnimTrack.append(Func(hole.setPos, toon, pos))
    holeAnimTrack.append(ActorInterval(hole, 'hole', startTime=T_TELEPORT_ANIM, endTime=T_HOLE_LEAVES_HAND))
    holeAnimTrack.append(ActorInterval(hole, 'hole', startTime=T_HOLE_LEAVES_HAND, endTime=T_TELEPORT_ANIM))
    holeAnimTrack.append(Func(hole.reparentTo, hidden))
    delay = T_TELEPORT_ANIM - T_HOLE_LEAVES_HAND
    jumpTrack = Sequence(Wait(delay), Func(toon.reparentTo, render), ActorInterval(toon, 'jump'))
    return Parallel(holeAnimTrack, jumpTrack)


def getSuitRakeOffset(suit):
    suitName = suit.getStyleName()
    if suitName == 'gh':
        return 1.4
    elif suitName == 'f':
        return 1.0
    elif suitName == 'cc':
        return 0.7
    elif suitName == 'tw':
        return 1.3
    elif suitName == 'bf':
        return 1.0
    elif suitName == 'sc':
        return 0.8
    elif suitName == 'ym':
        return 0.1
    elif suitName == 'mm':
        return 0.05
    elif suitName == 'tm':
        return 0.07
    elif suitName == 'nd':
        return 0.07
    elif suitName == 'pp':
        return 0.04
    elif suitName == 'bc':
        return 0.36
    elif suitName == 'b':
        return 0.41
    elif suitName == 'dt':
        return 0.31
    elif suitName == 'ac':
        return 0.39
    elif suitName == 'ds':
        return 0.41
    elif suitName == 'hh':
        return 0.8
    elif suitName == 'cr':
        return 2.1
    elif suitName == 'tbc':
        return 1.4
    elif suitName == 'bs':
        return 0.4
    elif suitName == 'sd':
        return 1.02
    elif suitName == 'le':
        return 1.3
    elif suitName == 'bw':
        return 1.4
    elif suitName == 'nc':
        return 0.6
    elif suitName == 'mb':
        return 1.85
    elif suitName == 'ls':
        return 1.4
    elif suitName == 'rb':
        return 1.6
    elif suitName == 'ms':
        return 0.7
    elif suitName == 'tf':
        return 0.75
    elif suitName == 'm':
        return 0.9
    elif suitName == 'mh':
        return 1.3
    else:
        notify.warning('getSuitRakeOffset(suit) - Unknown suit name: %s' % suitName)
        return 0


def startSparksIval(tntProp):
    tip = tntProp.find('**/joint_attachEmitter')
    sparks = BattleParticles.createParticleEffect(file='tnt')
    return Func(sparks.start, tip)


def indicateMissed(actor, duration = 1.1, scale = 0.7):
    actor.showHpString(TTLocalizer.AttackMissed, duration=duration, scale=scale)


def createKapowExplosionTrack(parent, explosionPoint = None, scale = 1.0):
    explosionTrack = Sequence()
    explosion = loader.loadModel('phase_3.5/models/props/explosion.bam')
    explosion.setBillboardPointEye()
    explosion.setDepthWrite(False)
    if not explosionPoint:
        explosionPoint = Point3(0, 3.6, 2.1)
    explosionTrack.append(Func(explosion.reparentTo, parent))
    explosionTrack.append(Func(explosion.setPos, explosionPoint))
    explosionTrack.append(Func(explosion.setScale, 0.4 * scale))
    explosionTrack.append(Wait(0.6))
    explosionTrack.append(Func(removeProp, explosion))
    return explosionTrack


def createSuitStunInterval(suit, before, after):
    p1 = Point3(0)
    p2 = Point3(0)
    stars = globalPropPool.getProp('stun')
    stars.setColor(1, 1, 1, 1)
    stars.adjustAllPriorities(100)
    head = suit.getHeadParts()[0]
    head.calcTightBounds(p1, p2)
    return Sequence(Wait(before), Func(stars.reparentTo, head), Func(stars.setZ, max(0.0, p2[2] - 1.0)), Func(stars.loop, 'stun'), Wait(after), Func(stars.removeNode))


def calcAvgSuitPos(throw):
    battle = throw['battle']
    avgSuitPos = Point3(0, 0, 0)
    numTargets = len(throw['target'])
    for i in range(numTargets):
        suit = throw['target'][i]['suit']
        avgSuitPos += suit.getPos(battle)

    avgSuitPos /= numTargets
    return avgSuitPos
