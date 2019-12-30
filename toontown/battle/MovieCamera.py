from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from .BattleBase import *
from .BattleProps import *
from toontown.toonbase.ToontownBattleGlobals import *
from .SuitBattleGlobals import *
from direct.directnotify import DirectNotifyGlobal
import random
from . import MovieUtil
notify = DirectNotifyGlobal.directNotify.newCategory('MovieCamera')

def chooseHealShot(heals, attackDuration):
    isUber = 0
    for heal in heals:
        if heal['level'] == 6 and not heal.get('petId'):
            isUber = 1

    if isUber:
        print('is uber')
        openShot = chooseHealOpenShot(heals, attackDuration, isUber)
        openDuration = openShot.getDuration()
        openName = openShot.getName()
        closeShot = chooseHealCloseShot(heals, openDuration, openName, attackDuration * 3, isUber)
        track = Sequence(closeShot)
    else:
        openShot = chooseHealOpenShot(heals, attackDuration, isUber)
        openDuration = openShot.getDuration()
        openName = openShot.getName()
        closeShot = chooseHealCloseShot(heals, openDuration, openName, attackDuration, isUber)
        track = Sequence(openShot, closeShot)
    return track


def chooseHealOpenShot(heals, attackDuration, isUber = 0):
    numHeals = len(heals)
    av = None
    duration = 2.8
    if isUber:
        duration = 5.0
    shotChoices = [toonGroupShot]
    track = random.choice(shotChoices)(*[av, duration])
    return track


def chooseHealMidShot(heals, attackDuration, isUber = 0):
    numHeals = len(heals)
    av = None
    duration = 2.1
    if isUber:
        duration = 2.1
    shotChoices = [toonGroupHighShot]
    track = random.choice(shotChoices)(*[av, duration])
    return track


def chooseHealCloseShot(heals, openDuration, openName, attackDuration, isUber = 0):
    av = None
    duration = attackDuration - openDuration
    shotChoices = [toonGroupShot]
    if isUber:
        shotChoices = [allGroupLowShot]
    track = random.choice(shotChoices)(*[av, duration])
    return track


def chooseTrapShot(traps, attackDuration, enterDuration = 0, exitDuration = 0):
    enterShot = chooseNPCEnterShot(traps, enterDuration)
    openShot = chooseTrapOpenShot(traps, attackDuration)
    openDuration = openShot.getDuration()
    openName = openShot.getName()
    closeShot = chooseTrapCloseShot(traps, openDuration, openName, attackDuration)
    exitShot = chooseNPCExitShot(traps, exitDuration)
    track = Sequence(enterShot, openShot, closeShot, exitShot)
    return track


def chooseTrapOpenShot(traps, attackDuration):
    numTraps = len(traps)
    av = None
    duration = 3.0
    shotChoices = [allGroupLowShot]
    track = random.choice(shotChoices)(*[av, duration])
    return track


def chooseTrapCloseShot(traps, openDuration, openName, attackDuration):
    av = None
    duration = attackDuration - openDuration
    shotChoices = [allGroupLowShot]
    track = random.choice(shotChoices)(*[av, duration])
    return track


def chooseLureShot(lures, attackDuration, enterDuration = 0.0, exitDuration = 0.0):
    enterShot = chooseNPCEnterShot(lures, enterDuration)
    openShot = chooseLureOpenShot(lures, attackDuration)
    openDuration = openShot.getDuration()
    openName = openShot.getName()
    closeShot = chooseLureCloseShot(lures, openDuration, openName, attackDuration)
    exitShot = chooseNPCExitShot(lures, exitDuration)
    track = Sequence(enterShot, openShot, closeShot, exitShot)
    return track


def chooseLureOpenShot(lures, attackDuration):
    numLures = len(lures)
    av = None
    duration = 3.0
    shotChoices = [allGroupLowShot]
    track = random.choice(shotChoices)(*[av, duration])
    return track


def chooseLureCloseShot(lures, openDuration, openName, attackDuration):
    av = None
    duration = attackDuration - openDuration
    hasTrainTrackTrap = False
    battle = lures[0]['battle']
    for suit in battle.suits:
        if hasattr(suit, 'battleTrap') and suit.battleTrap == UBER_GAG_LEVEL_INDEX:
            hasTrainTrackTrap = True

    if hasTrainTrackTrap:
        shotChoices = [avatarBehindHighRightShot]
        av = lures[0]['toon']
    else:
        shotChoices = [allGroupLowShot]
    track = random.choice(shotChoices)(*[av, duration])
    return track


def chooseSoundShot(sounds, targets, attackDuration, enterDuration = 0.0, exitDuration = 0.0):
    enterShot = chooseNPCEnterShot(sounds, enterDuration)
    openShot = chooseSoundOpenShot(sounds, targets, attackDuration)
    openDuration = openShot.getDuration()
    openName = openShot.getName()
    closeShot = chooseSoundCloseShot(sounds, targets, openDuration, openName, attackDuration)
    exitShot = chooseNPCExitShot(sounds, exitDuration)
    track = Sequence(enterShot, openShot, closeShot, exitShot)
    return track


def chooseSoundOpenShot(sounds, targets, attackDuration):
    duration = 3.1
    isUber = 0
    for sound in sounds:
        if sound['level'] == 6:
            isUber = 1
            duration = 5.0

    numSounds = len(sounds)
    av = None
    if numSounds == 1:
        av = sounds[0]['toon']
        if isUber:
            shotChoices = [avatarCloseUpThreeQuarterRightShotWide, allGroupLowShot, suitGroupThreeQuarterLeftBehindShot]
        else:
            shotChoices = [avatarCloseUpThreeQuarterRightShot, allGroupLowShot, suitGroupThreeQuarterLeftBehindShot]
    elif numSounds >= 2 and numSounds <= 4:
        shotChoices = [allGroupLowShot, suitGroupThreeQuarterLeftBehindShot]
    else:
        notify.error('Bad number of sounds: %s' % numSounds)
    track = random.choice(shotChoices)(*[av, duration])
    return track


def chooseSoundCloseShot(sounds, targets, openDuration, openName, attackDuration):
    numSuits = len(targets)
    av = None
    duration = attackDuration - openDuration
    if numSuits == 1:
        av = targets[0]['suit']
        shotChoices = [avatarCloseUpThrowShot,
         avatarCloseUpThreeQuarterLeftShot,
         allGroupLowShot,
         suitGroupThreeQuarterLeftBehindShot]
    elif numSuits >= 2 and numSuits <= 4:
        shotChoices = [allGroupLowShot, suitGroupThreeQuarterLeftBehindShot]
    else:
        notify.error('Bad number of suits: %s' % numSuits)
    track = random.choice(shotChoices)(*[av, duration])
    return track


def chooseThrowShot(throws, suitThrowsDict, attackDuration):
    openShot = chooseThrowOpenShot(throws, suitThrowsDict, attackDuration)
    openDuration = openShot.getDuration()
    openName = openShot.getName()
    closeShot = chooseThrowCloseShot(throws, suitThrowsDict, openDuration, openName, attackDuration)
    track = Sequence(openShot, closeShot)
    return track


def chooseThrowOpenShot(throws, suitThrowsDict, attackDuration):
    numThrows = len(throws)
    av = None
    duration = 3.0
    if numThrows == 1:
        av = throws[0]['toon']
        shotChoices = [avatarCloseUpThrowShot,
         avatarCloseUpThreeQuarterRightShot,
         avatarBehindShot,
         allGroupLowShot,
         suitGroupThreeQuarterLeftBehindShot]
    elif numThrows >= 2 and numThrows <= 4:
        shotChoices = [allGroupLowShot, suitGroupThreeQuarterLeftBehindShot]
    else:
        notify.error('Bad number of throws: %s' % numThrows)
    track = random.choice(shotChoices)(*[av, duration])
    return track


def chooseThrowCloseShot(throws, suitThrowsDict, openDuration, openName, attackDuration):
    numSuits = len(suitThrowsDict)
    av = None
    duration = attackDuration - openDuration
    if numSuits == 1:
        av = base.cr.doId2do[list(suitThrowsDict.keys())[0]]
        shotChoices = [avatarCloseUpThrowShot,
         avatarCloseUpThreeQuarterLeftShot,
         allGroupLowShot,
         suitGroupThreeQuarterLeftBehindShot]
    elif numSuits >= 2 and numSuits <= 4 or numSuits == 0:
        shotChoices = [allGroupLowShot, suitGroupThreeQuarterLeftBehindShot]
    else:
        notify.error('Bad number of suits: %s' % numSuits)
    track = random.choice(shotChoices)(*[av, duration])
    return track


def chooseSquirtShot(squirts, suitSquirtsDict, attackDuration):
    openShot = chooseSquirtOpenShot(squirts, suitSquirtsDict, attackDuration)
    openDuration = openShot.getDuration()
    openName = openShot.getName()
    closeShot = chooseSquirtCloseShot(squirts, suitSquirtsDict, openDuration, openName, attackDuration)
    track = Sequence(openShot, closeShot)
    return track


def chooseSquirtOpenShot(squirts, suitSquirtsDict, attackDuration):
    numSquirts = len(squirts)
    av = None
    duration = 3.0
    if numSquirts == 1:
        av = squirts[0]['toon']
        shotChoices = [avatarCloseUpThrowShot,
         avatarCloseUpThreeQuarterRightShot,
         avatarBehindShot,
         allGroupLowShot,
         suitGroupThreeQuarterLeftBehindShot]
    elif numSquirts >= 2 and numSquirts <= 4:
        shotChoices = [allGroupLowShot, suitGroupThreeQuarterLeftBehindShot]
    else:
        notify.error('Bad number of squirts: %s' % numSquirts)
    track = random.choice(shotChoices)(*[av, duration])
    return track


def chooseSquirtCloseShot(squirts, suitSquirtsDict, openDuration, openName, attackDuration):
    numSuits = len(suitSquirtsDict)
    av = None
    duration = attackDuration - openDuration
    if numSuits == 1:
        av = base.cr.doId2do[list(suitSquirtsDict.keys())[0]]
        shotChoices = [avatarCloseUpThrowShot,
         avatarCloseUpThreeQuarterLeftShot,
         allGroupLowShot,
         suitGroupThreeQuarterLeftBehindShot]
    elif numSuits >= 2 and numSuits <= 4:
        shotChoices = [allGroupLowShot, suitGroupThreeQuarterLeftBehindShot]
    else:
        notify.error('Bad number of suits: %s' % numSuits)
    track = random.choice(shotChoices)(*[av, duration])
    return track


def chooseDropShot(drops, suitDropsDict, attackDuration, enterDuration = 0.0, exitDuration = 0.0):
    enterShot = chooseNPCEnterShot(drops, enterDuration)
    openShot = chooseDropOpenShot(drops, suitDropsDict, attackDuration)
    openDuration = openShot.getDuration()
    openName = openShot.getName()
    closeShot = chooseDropCloseShot(drops, suitDropsDict, openDuration, openName, attackDuration)
    exitShot = chooseNPCExitShot(drops, exitDuration)
    track = Sequence(enterShot, openShot, closeShot, exitShot)
    return track


def chooseDropOpenShot(drops, suitDropsDict, attackDuration):
    numDrops = len(drops)
    av = None
    duration = 3.0
    if numDrops == 1:
        av = drops[0]['toon']
        shotChoices = [avatarCloseUpThrowShot,
         avatarCloseUpThreeQuarterRightShot,
         avatarBehindShot,
         allGroupLowShot,
         suitGroupThreeQuarterLeftBehindShot]
    elif numDrops >= 2 and numDrops <= 4 or numDrops == 0:
        shotChoices = [allGroupLowShot, suitGroupThreeQuarterLeftBehindShot]
    else:
        notify.error('Bad number of drops: %s' % numDrops)
    track = random.choice(shotChoices)(*[av, duration])
    return track


def chooseDropCloseShot(drops, suitDropsDict, openDuration, openName, attackDuration):
    numSuits = len(suitDropsDict)
    av = None
    duration = attackDuration - openDuration
    if numSuits == 1:
        av = base.cr.doId2do[list(suitDropsDict.keys())[0]]
        shotChoices = [avatarCloseUpThrowShot,
         avatarCloseUpThreeQuarterLeftShot,
         allGroupLowShot,
         suitGroupThreeQuarterLeftBehindShot]
    elif numSuits >= 2 and numSuits <= 4 or numSuits == 0:
        shotChoices = [allGroupLowShot, suitGroupThreeQuarterLeftBehindShot]
    else:
        notify.error('Bad number of suits: %s' % numSuits)
    choice = random.choice(shotChoices)
    track = choice(av, duration)
    return track


def chooseNPCEnterShot(enters, entersDuration):
    av = None
    duration = entersDuration
    shotChoices = [toonGroupShot]
    track = random.choice(shotChoices)(*[av, duration])
    return track


def chooseNPCExitShot(exits, exitsDuration):
    av = None
    duration = exitsDuration
    shotChoices = [toonGroupShot]
    track = random.choice(shotChoices)(*[av, duration])
    return track


def chooseSuitShot(attack, attackDuration):
    groupStatus = attack['group']
    target = attack['target']
    if groupStatus == ATK_TGT_SINGLE:
        toon = target['toon']
    suit = attack['suit']
    name = attack['id']
    battle = attack['battle']
    camTrack = Sequence()

    def defaultCamera(attack = attack, attackDuration = attackDuration, openShotDuration = 3.5, target = target):
        if attack['group'] == ATK_TGT_GROUP:
            return randomGroupAttackCam(attack['suit'], target, attack['battle'], attackDuration, openShotDuration)
        else:
            return randomAttackCam(attack['suit'], target['toon'], attack['battle'], attackDuration, openShotDuration, 'suit')

    if name == AUDIT:
        camTrack.append(defaultCamera())
    elif name == BITE:
        camTrack.append(defaultCamera(openShotDuration=2.8))
    elif name == BOUNCE_CHECK:
        camTrack.append(defaultCamera())
    elif name == BRAIN_STORM:
        camTrack.append(defaultCamera(openShotDuration=2.4))
    elif name == BUZZ_WORD:
        camTrack.append(defaultCamera(openShotDuration=4.7))
    elif name == CALCULATE:
        camTrack.append(defaultCamera())
    elif name == CANNED:
        camTrack.append(defaultCamera(openShotDuration=2.9))
    elif name == CHOMP:
        camTrack.append(defaultCamera(openShotDuration=2.8))
    elif name == CLIPON_TIE:
        camTrack.append(defaultCamera(openShotDuration=3.3))
    elif name == CRUNCH:
        camTrack.append(defaultCamera(openShotDuration=3.4))
    elif name == DEMOTION:
        camTrack.append(defaultCamera(openShotDuration=1.7))
    elif name == DOUBLE_TALK:
        camTrack.append(defaultCamera(openShotDuration=3.9))
    elif name == EVICTION_NOTICE:
        camTrack.append(defaultCamera(openShotDuration=3.2))
    elif name == EVIL_EYE:
        camTrack.append(defaultCamera(openShotDuration=2.7))
    elif name == FILIBUSTER:
        camTrack.append(defaultCamera(openShotDuration=2.7))
    elif name == FILL_WITH_LEAD:
        camTrack.append(defaultCamera(openShotDuration=3.2))
    elif name == FINGER_WAG:
        camTrack.append(defaultCamera(openShotDuration=2.3))
    elif name == FIRED:
        camTrack.append(defaultCamera(openShotDuration=1.7))
    elif name == FOUNTAIN_PEN:
        camTrack.append(defaultCamera(openShotDuration=2.6))
    elif name == FREEZE_ASSETS:
        camTrack.append(defaultCamera(openShotDuration=2.5))
    elif name == HALF_WINDSOR:
        camTrack.append(defaultCamera(openShotDuration=2.8))
    elif name == HEAD_SHRINK:
        camTrack.append(defaultCamera(openShotDuration=1.3))
    elif name == GLOWER_POWER:
        camTrack.append(defaultCamera(openShotDuration=1.4))
    elif name == GUILT_TRIP:
        camTrack.append(defaultCamera(openShotDuration=0.9))
    elif name == HANG_UP:
        camTrack.append(defaultCamera(openShotDuration=5.1))
    elif name == HOT_AIR:
        camTrack.append(defaultCamera(openShotDuration=2.5))
    elif name == JARGON:
        camTrack.append(defaultCamera())
    elif name == LEGALESE:
        camTrack.append(defaultCamera(openShotDuration=1.5))
    elif name == LIQUIDATE:
        camTrack.append(defaultCamera(openShotDuration=2.5))
    elif name == MARKET_CRASH:
        camTrack.append(defaultCamera(openShotDuration=2.9))
    elif name == MUMBO_JUMBO:
        camTrack.append(defaultCamera(openShotDuration=2.8))
    elif name == PARADIGM_SHIFT:
        camTrack.append(defaultCamera(openShotDuration=1.6))
    elif name == PECKING_ORDER:
        camTrack.append(defaultCamera(openShotDuration=2.8))
    elif name == PLAY_HARDBALL:
        camTrack.append(defaultCamera(openShotDuration=2.3))
    elif name == PICK_POCKET:
        camTrack.append(allGroupLowShot(suit, 2.7))
    elif name == PINK_SLIP:
        camTrack.append(defaultCamera(openShotDuration=2.8))
    elif name == POUND_KEY:
        camTrack.append(defaultCamera(openShotDuration=2.8))
    elif name == POWER_TIE:
        camTrack.append(defaultCamera(openShotDuration=2.4))
    elif name == POWER_TRIP:
        camTrack.append(defaultCamera(openShotDuration=1.1))
    elif name == QUAKE:
        shakeIntensity = 5.15
        quake = 1
        camTrack.append(suitCameraShakeShot(suit, attackDuration, shakeIntensity, quake))
    elif name == RAZZLE_DAZZLE:
        camTrack.append(defaultCamera(openShotDuration=2.2))
    elif name == RED_TAPE:
        camTrack.append(defaultCamera(openShotDuration=3.5))
    elif name == RE_ORG:
        camTrack.append(defaultCamera(openShotDuration=1.1))
    elif name == RESTRAINING_ORDER:
        camTrack.append(defaultCamera(openShotDuration=2.8))
    elif name == ROLODEX:
        camTrack.append(defaultCamera())
    elif name == RUBBER_STAMP:
        camTrack.append(defaultCamera(openShotDuration=3.2))
    elif name == RUB_OUT:
        camTrack.append(defaultCamera(openShotDuration=2.2))
    elif name == SACKED:
        camTrack.append(defaultCamera(openShotDuration=2.9))
    elif name == SCHMOOZE:
        camTrack.append(defaultCamera(openShotDuration=2.8))
    elif name == SHAKE:
        shakeIntensity = 1.75
        camTrack.append(suitCameraShakeShot(suit, attackDuration, shakeIntensity))
    elif name == SHRED:
        camTrack.append(defaultCamera(openShotDuration=4.1))
    elif name == SPIN:
        camTrack.append(defaultCamera(openShotDuration=1.7))
    elif name == SYNERGY:
        camTrack.append(defaultCamera(openShotDuration=1.7))
    elif name == TABULATE:
        camTrack.append(defaultCamera())
    elif name == TEE_OFF:
        camTrack.append(defaultCamera(openShotDuration=4.5))
    elif name == TREMOR:
        shakeIntensity = 0.25
        camTrack.append(suitCameraShakeShot(suit, attackDuration, shakeIntensity))
    elif name == WATERCOOLER:
        camTrack.append(defaultCamera())
    elif name == WITHDRAWAL:
        camTrack.append(defaultCamera(openShotDuration=1.2))
    elif name == WRITE_OFF:
        camTrack.append(defaultCamera())
    else:
        notify.warning('unknown attack id in chooseSuitShot: %d using default cam' % name)
        camTrack.append(defaultCamera())
    pbpText = attack['playByPlayText']
    displayName = TTLocalizer.SuitAttackNames[attack['name']]
    pbpTrack = pbpText.getShowInterval(displayName, 3.5)
    return Parallel(camTrack, pbpTrack)


def chooseSuitCloseShot(attack, openDuration, openName, attackDuration):
    av = None
    duration = attackDuration - openDuration
    if duration < 0:
        duration = 1e-06
    groupStatus = attack['group']
    diedTrack = None
    if groupStatus == ATK_TGT_SINGLE:
        av = attack['target']['toon']
        shotChoices = [avatarCloseUpThreeQuarterRightShot, suitGroupThreeQuarterLeftBehindShot]
        died = attack['target']['died']
        if died != 0:
            pbpText = attack['playByPlayText']
            diedText = av.getName() + ' was defeated!'
            diedTextList = [diedText]
            diedTrack = pbpText.getToonsDiedInterval(diedTextList, duration)
    elif groupStatus == ATK_TGT_GROUP:
        av = None
        shotChoices = [allGroupLowShot, suitGroupThreeQuarterLeftBehindShot]
        deadToons = []
        targetDicts = attack['target']
        for targetDict in targetDicts:
            died = targetDict['died']
            if died != 0:
                deadToons.append(targetDict['toon'])

        if len(deadToons) > 0:
            pbpText = attack['playByPlayText']
            diedTextList = []
            for toon in deadToons:
                pbpText = attack['playByPlayText']
                diedTextList.append(toon.getName() + ' was defeated!')

            diedTrack = pbpText.getToonsDiedInterval(diedTextList, duration)
    else:
        notify.error('Bad groupStatus: %s' % groupStatus)
    track = random.choice(shotChoices)(*[av, duration])
    if diedTrack == None:
        return track
    else:
        mtrack = Parallel(track, diedTrack)
        return mtrack
    return


def makeShot(x, y, z, h, p, r, duration, other = None, name = 'makeShot'):
    if other:
        return heldRelativeShot(other, x, y, z, h, p, r, duration, name)
    else:
        return heldShot(x, y, z, h, p, r, duration, name)


def focusShot(x, y, z, duration, target, other = None, splitFocusPoint = None, name = 'focusShot'):
    track = Sequence()
    if other:
        track.append(Func(camera.setPos, other, Point3(x, y, z)))
    else:
        track.append(Func(camera.setPos, Point3(x, y, z)))
    if splitFocusPoint:
        track.append(Func(focusCameraBetweenPoints, target, splitFocusPoint))
    else:
        track.append(Func(camera.lookAt, target))
    track.append(Wait(duration))
    return track


def moveShot(x, y, z, h, p, r, duration, other = None, name = 'moveShot'):
    return motionShot(x, y, z, h, p, r, duration, other, name)


def focusMoveShot(x, y, z, duration, target, other = None, name = 'focusMoveShot'):
    camera.setPos(Point3(x, y, z))
    camera.lookAt(target)
    hpr = camera.getHpr()
    return motionShot(x, y, z, hpr[0], hpr[1], hpr[2], duration, other, name)


def chooseSOSShot(av, duration):
    shotChoices = [avatarCloseUpThreeQuarterRightShot,
     avatarBehindShot,
     avatarBehindHighShot,
     suitGroupThreeQuarterLeftBehindShot]
    track = random.choice(shotChoices)(*[av, duration])
    return track


def chooseRewardShot(av, duration, allowGroupShot = 1):

    def chooseRewardShotNow(av):
        if av.playingAnim == 'victory' or not allowGroupShot:
            shotChoices = [(0,
              8,
              av.getHeight() * 0.66,
              179,
              15,
              0), (5.2,
              5.45,
              av.getHeight() * 0.66,
              131.5,
              3.6,
              0)]
            shot = random.choice(shotChoices)
            camera.setPosHpr(av, *shot)
        else:
            camera.setPosHpr(10, 0, 10, 115, -30, 0)

    return Sequence(Func(chooseRewardShotNow, av), Wait(duration))


def heldShot(x, y, z, h, p, r, duration, name = 'heldShot'):
    track = Sequence(name=name)
    track.append(Func(camera.setPosHpr, x, y, z, h, p, r))
    track.append(Wait(duration))
    return track


def heldRelativeShot(other, x, y, z, h, p, r, duration, name = 'heldRelativeShot'):
    track = Sequence(name=name)
    track.append(Func(camera.setPosHpr, other, x, y, z, h, p, r))
    track.append(Wait(duration))
    return track


def motionShot(x, y, z, h, p, r, duration, other = None, name = 'motionShot'):
    if other:
        posTrack = LerpPosInterval(camera, duration, pos=Point3(x, y, z), other=other)
        hprTrack = LerpHprInterval(camera, duration, hpr=Point3(h, p, r), other=other)
    else:
        posTrack = LerpPosInterval(camera, duration, pos=Point3(x, y, z))
        hprTrack = LerpHprInterval(camera, duration, hpr=Point3(h, p, r))
    return Parallel(posTrack, hprTrack)


def allGroupShot(avatar, duration):
    return heldShot(10, 0, 10, 89, -30, 0, duration, 'allGroupShot')


def allGroupLowShot(avatar, duration):
    return heldShot(15, 0, 3, 89, 0, 0, duration, 'allGroupLowShot')


def allGroupLowDiagonalShot(avatar, duration):
    return heldShot(7, 5, 6, 119, -30, 0, duration, 'allGroupLowShot')


def toonGroupShot(avatar, duration):
    return heldShot(10, 0, 10, 115, -30, 0, duration, 'toonGroupShot')


def toonGroupHighShot(avatar, duration):
    return heldShot(5, 0, 1, 115, 45, 0, duration, 'toonGroupHighShot')


def suitGroupShot(avatar, duration):
    return heldShot(10, 0, 10, 65, -30, 0, duration, 'suitGroupShot')


def suitGroupLowLeftShot(avatar, duration):
    return heldShot(8.4, -3.85, 2.75, 36.3, 3.25, 0, duration, 'suitGroupLowLeftShot')


def suitGroupThreeQuarterLeftBehindShot(avatar, duration):
    if random.random() > 0.5:
        x = 12.37
        h = 134.61
    else:
        x = -12.37
        h = -134.61
    return heldShot(x, 11.5, 8.16, h, -22.7, 0, duration, 'suitGroupThreeQuarterLeftBehindShot')


def suitWakeUpShot(avatar, duration):
    return heldShot(10, -5, 10, 65, -30, 0, duration, 'suitWakeUpShot')


def suitCameraShakeShot(avatar, duration, shakeIntensity, quake = 0):
    track = Sequence(name='suitShakeCameraShot')
    if quake == 1:
        shakeDelay = 1.1
        numShakes = 4
    else:
        shakeDelay = 0.3
        numShakes = 5
    postShakeDelay = 0.5
    shakeTime = (duration - shakeDelay - postShakeDelay) / numShakes
    shakeDuration = shakeTime * (1.0 / numShakes)
    shakeWaitInterval = shakeTime * ((numShakes - 1.0) / numShakes)

    def shakeCameraTrack(intensity, shakeWaitInterval = shakeWaitInterval, quake = quake, shakeDuration = shakeDuration, numShakes = numShakes):
        vertShakeTrack = Sequence(Wait(shakeWaitInterval), Func(camera.setZ, camera.getZ() + intensity / 2), Wait(shakeDuration / 2), Func(camera.setZ, camera.getZ() - intensity), Wait(shakeDuration / 2), Func(camera.setZ, camera.getZ() + intensity / 2))
        horizShakeTrack = Sequence(Wait(shakeWaitInterval - shakeDuration / 2), Func(camera.setY, camera.getY() + intensity / 4), Wait(shakeDuration / 2), Func(camera.setY, camera.getY() - intensity / 2), Wait(shakeDuration / 2), Func(camera.setY, camera.getY() + intensity / 4), Wait(shakeDuration / 2), Func(camera.lookAt, Point3(0, 0, 0)))
        shakeTrack = Sequence()
        for i in range(0, numShakes):
            if quake == 0:
                shakeTrack.append(vertShakeTrack)
            else:
                shakeTrack.append(Parallel(vertShakeTrack, horizShakeTrack))

        return shakeTrack

    x = 10 + random.random() * 3
    if random.random() > 0.5:
        x = -x
    z = 7 + random.random() * 3
    track.append(Func(camera.setPos, x, -5, z))
    track.append(Func(camera.lookAt, Point3(0, 0, 0)))
    track.append(Wait(shakeDelay))
    track.append(shakeCameraTrack(shakeIntensity))
    track.append(Wait(postShakeDelay))
    return track


def avatarCloseUpShot(avatar, duration):
    return heldRelativeShot(avatar, 0, 8, avatar.getHeight() * 0.66, 179, 15, 0, duration, 'avatarCloseUpShot')


def avatarCloseUpThrowShot(avatar, duration):
    return heldRelativeShot(avatar, 3, 8, avatar.getHeight() * 0.66, 159, 3.6, 0, duration, 'avatarCloseUpThrowShot')


def avatarCloseUpThreeQuarterRightShot(avatar, duration):
    return heldRelativeShot(avatar, 5.2, 5.45, avatar.getHeight() * 0.66, 131.5, 3.6, 0, duration, 'avatarCloseUpThreeQuarterRightShot')


def avatarCloseUpThreeQuarterRightShotWide(avatar, duration):
    return heldRelativeShot(avatar, 7.2, 8.45, avatar.getHeight() * 0.66, 131.5, 3.6, 0, duration, 'avatarCloseUpThreeQuarterRightShot')


def avatarCloseUpThreeQuarterLeftShot(avatar, duration):
    return heldRelativeShot(avatar, -5.2, 5.45, avatar.getHeight() * 0.66, -131.5, 3.6, 0, duration, 'avatarCloseUpThreeQuarterLeftShot')


def avatarCloseUpThreeQuarterRightFollowShot(avatar, duration):
    track = Sequence(name='avatarCloseUpThreeQuarterRightFollowShot')
    track.append(heldRelativeShot(avatar, 5.2, 5.45, avatar.getHeight() * 0.66, 131.5, 3.6, 0, duration * 0.65))
    track.append(LerpHprInterval(nodePath=camera, other=avatar, duration=duration * 0.2, hpr=Point3(110, 3.6, 0), blendType='easeInOut'))
    track.append(Wait(duration * 0.25))
    return track


def avatarCloseUpZoomShot(avatar, duration):
    track = Sequence('avatarCloseUpZoomShot')
    track.append(LerpPosHprInterval(nodePath=camera, other=avatar, duration=duration / 2, startPos=Point3(0, 10, avatar.getHeight()), startHpr=Point3(179, -10, 0), pos=Point3(0, 6, avatar.getHeight()), hpr=Point3(179, -10, 0), blendType='easeInOut'))
    track.append(Wait(duration / 2))
    return track


def avatarBehindShot(avatar, duration):
    return heldRelativeShot(avatar, 5, -7, avatar.getHeight(), 40, -12, 0, duration, 'avatarBehindShot')


def avatarBehindHighShot(avatar, duration):
    return heldRelativeShot(avatar, -4, -7, 5 + avatar.getHeight(), -30, -35, 0, duration, 'avatarBehindHighShot')


def avatarBehindHighRightShot(avatar, duration):
    return heldRelativeShot(avatar, 4, -7, 5 + avatar.getHeight(), 30, -35, 0, duration, 'avatarBehindHighShot')


def avatarBehindThreeQuarterRightShot(avatar, duration):
    return heldRelativeShot(avatar, 7.67, -8.52, avatar.getHeight() * 0.66, 25, 7.5, 0, duration, 'avatarBehindThreeQuarterRightShot')


def avatarSideFollowAttack(suit, toon, duration, battle):
    windupDuration = duration * (0.1 + random.random() * 0.1)
    projectDuration = duration * 0.75
    impactDuration = duration - windupDuration - projectDuration
    suitHeight = suit.getHeight()
    toonHeight = toon.getHeight()
    suitCentralPoint = suit.getPos(battle)
    suitCentralPoint.setZ(suitCentralPoint.getZ() + suitHeight * 0.75)
    toonCentralPoint = toon.getPos(battle)
    toonCentralPoint.setZ(toonCentralPoint.getZ() + toonHeight * 0.75)
    initialX = random.randint(12, 14)
    finalX = random.randint(7, 8)
    initialY = finalY = random.randint(-3, 0)
    initialZ = suitHeight * 0.5 + random.random() * suitHeight
    finalZ = toonHeight * 0.5 + random.random() * toonHeight
    if random.random() > 0.5:
        initialX = -initialX
        finalX = -finalX
    return Sequence(focusShot(initialX, initialY, initialZ, windupDuration, suitCentralPoint), focusMoveShot(finalX, finalY, finalZ, projectDuration, toonCentralPoint), Wait(impactDuration))


def focusCameraBetweenPoints(point1, point2):
    if point1[0] > point2[0]:
        x = point2[0] + (point1[0] - point2[0]) * 0.5
    else:
        x = point1[0] + (point2[0] - point1[0]) * 0.5
    if point1[1] > point2[1]:
        y = point2[1] + (point1[1] - point2[1]) * 0.5
    else:
        y = point1[1] + (point2[1] - point1[1]) * 0.5
    if point1[2] > point2[2]:
        z = point2[2] + (point1[2] - point2[2]) * 0.5
    else:
        z = point1[2] + (point2[2] - point1[2]) * 0.5
    camera.lookAt(Point3(x, y, z))


def randomCamera(suit, toon, battle, attackDuration, openShotDuration):
    return randomAttackCam(suit, toon, battle, attackDuration, openShotDuration, 'suit')


def randomAttackCam(suit, toon, battle, attackDuration, openShotDuration, attackerString = 'suit'):
    if openShotDuration > attackDuration:
        openShotDuration = attackDuration
    closeShotDuration = attackDuration - openShotDuration
    if attackerString == 'suit':
        attacker = suit
        defender = toon
        defenderString = 'toon'
    else:
        attacker = toon
        defender = suit
        defenderString = 'suit'
    randomDouble = random.random()
    if randomDouble > 0.6:
        openShot = randomActorShot(attacker, battle, openShotDuration, attackerString)
    elif randomDouble > 0.2:
        openShot = randomOverShoulderShot(suit, toon, battle, openShotDuration, focus=attackerString)
    else:
        openShot = randomSplitShot(attacker, defender, battle, openShotDuration)
    randomDouble = random.random()
    if randomDouble > 0.6:
        closeShot = randomActorShot(defender, battle, closeShotDuration, defenderString)
    elif randomDouble > 0.2:
        closeShot = randomOverShoulderShot(suit, toon, battle, closeShotDuration, focus=defenderString)
    else:
        closeShot = randomSplitShot(attacker, defender, battle, closeShotDuration)
    return Sequence(openShot, closeShot)


def randomGroupAttackCam(suit, targets, battle, attackDuration, openShotDuration):
    if openShotDuration > attackDuration:
        openShotDuration = attackDuration
    closeShotDuration = attackDuration - openShotDuration
    openShot = randomActorShot(suit, battle, openShotDuration, 'suit', groupShot=0)
    closeShot = randomToonGroupShot(targets, suit, closeShotDuration, battle)
    return Sequence(openShot, closeShot)


def randomActorShot(actor, battle, duration, actorType, groupShot = 0):
    height = actor.getHeight()
    centralPoint = actor.getPos(battle)
    centralPoint.setZ(centralPoint.getZ() + height * 0.75)
    if actorType == 'suit':
        x = 4 + random.random() * 8
        y = -2 - random.random() * 4
        z = height * 0.5 + random.random() * height * 1.5
        if groupShot == 1:
            y = -4
            z = height * 0.5
    else:
        x = 2 + random.random() * 8
        y = -2 + random.random() * 3
        z = height + random.random() * height * 1.5
        if groupShot == 1:
            y = y + 3
            z = height * 0.5
    if MovieUtil.shotDirection == 'left':
        x = -x
    return focusShot(x, y, z, duration, centralPoint)


def randomSplitShot(suit, toon, battle, duration):
    suitHeight = suit.getHeight()
    toonHeight = toon.getHeight()
    suitCentralPoint = suit.getPos(battle)
    suitCentralPoint.setZ(suitCentralPoint.getZ() + suitHeight * 0.75)
    toonCentralPoint = toon.getPos(battle)
    toonCentralPoint.setZ(toonCentralPoint.getZ() + toonHeight * 0.75)
    x = 9 + random.random() * 2
    y = -2 - random.random() * 2
    z = suitHeight * 0.5 + random.random() * suitHeight
    if MovieUtil.shotDirection == 'left':
        x = -x
    return focusShot(x, y, z, duration, toonCentralPoint, splitFocusPoint=suitCentralPoint)


def randomOverShoulderShot(suit, toon, battle, duration, focus):
    suitHeight = suit.getHeight()
    toonHeight = toon.getHeight()
    suitCentralPoint = suit.getPos(battle)
    suitCentralPoint.setZ(suitCentralPoint.getZ() + suitHeight * 0.75)
    toonCentralPoint = toon.getPos(battle)
    toonCentralPoint.setZ(toonCentralPoint.getZ() + toonHeight * 0.75)
    x = 2 + random.random() * 10
    if focus == 'toon':
        y = 8 + random.random() * 6
        z = suitHeight * 1.2 + random.random() * suitHeight
    else:
        y = -10 - random.random() * 6
        z = toonHeight * 1.5
    if MovieUtil.shotDirection == 'left':
        x = -x
    return focusShot(x, y, z, duration, toonCentralPoint, splitFocusPoint=suitCentralPoint)


def randomCameraSelection(suit, attack, attackDuration, openShotDuration):
    shotChoices = [avatarCloseUpThrowShot,
     avatarCloseUpThreeQuarterLeftShot,
     allGroupLowShot,
     suitGroupLowLeftShot,
     avatarBehindHighShot]
    if openShotDuration > attackDuration:
        openShotDuration = attackDuration
    closeShotDuration = attackDuration - openShotDuration
    openShot = random.choice(shotChoices)(*[suit, openShotDuration])
    closeShot = chooseSuitCloseShot(attack, closeShotDuration, openShot.getName(), attackDuration)
    return Sequence(openShot, closeShot)


def randomToonGroupShot(toons, suit, duration, battle):
    sum = 0
    for t in toons:
        toon = t['toon']
        height = toon.getHeight()
        sum = sum + height

    avgHeight = sum / len(toons) * 0.75
    suitPos = suit.getPos(battle)
    x = 1 + random.random() * 6
    if suitPos.getX() > 0:
        x = -x
    if random.random() > 0.5:
        y = 4 + random.random() * 1
        z = avgHeight + random.random() * 6
    else:
        y = 11 + random.random() * 2
        z = 13 + random.random() * 2
    focalPoint = Point3(0, -4, avgHeight)
    return focusShot(x, y, z, duration, focalPoint)


def chooseFireShot(throws, suitThrowsDict, attackDuration):
    openShot = chooseFireOpenShot(throws, suitThrowsDict, attackDuration)
    openDuration = openShot.getDuration()
    openName = openShot.getName()
    closeShot = chooseFireCloseShot(throws, suitThrowsDict, openDuration, openName, attackDuration)
    track = Sequence(openShot, closeShot)
    return track


def chooseFireOpenShot(throws, suitThrowsDict, attackDuration):
    numThrows = len(throws)
    av = None
    duration = 3.0
    if numThrows == 1:
        av = throws[0]['toon']
        shotChoices = [avatarCloseUpThrowShot,
         avatarCloseUpThreeQuarterRightShot,
         avatarBehindShot,
         allGroupLowShot,
         suitGroupThreeQuarterLeftBehindShot]
    elif numThrows >= 2 and numThrows <= 4:
        shotChoices = [allGroupLowShot, suitGroupThreeQuarterLeftBehindShot]
    else:
        notify.error('Bad number of throws: %s' % numThrows)
    shotChoice = random.choice(shotChoices)
    track = shotChoice(*[av, duration])
    print('chooseFireOpenShot %s' % shotChoice)
    return track


def chooseFireCloseShot(throws, suitThrowsDict, openDuration, openName, attackDuration):
    numSuits = len(suitThrowsDict)
    av = None
    duration = attackDuration - openDuration
    if numSuits == 1:
        av = base.cr.doId2do[list(suitThrowsDict.keys())[0]]
        shotChoices = [avatarCloseUpFireShot,
         avatarCloseUpThreeQuarterLeftFireShot,
         allGroupLowShot,
         suitGroupThreeQuarterLeftBehindShot]
    elif numSuits >= 2 and numSuits <= 4 or numSuits == 0:
        shotChoices = [allGroupLowShot, suitGroupThreeQuarterLeftBehindShot]
    else:
        notify.error('Bad number of suits: %s' % numSuits)
    shotChoice = random.choice(shotChoices)
    track = shotChoice(*[av, duration])
    print('chooseFireOpenShot %s' % shotChoice)
    return track


def avatarCloseUpFireShot(avatar, duration):
    return heldRelativeShot(avatar, 7, 17, avatar.getHeight() * 0.66, 159, 3.6, 0, duration, 'avatarCloseUpFireShot')


def avatarCloseUpThreeQuarterLeftFireShot(avatar, duration):
    return heldRelativeShot(avatar, -8.2, 8.45, avatar.getHeight() * 0.66, -131.5, 3.6, 0, duration, 'avatarCloseUpThreeQuarterLeftShot')
