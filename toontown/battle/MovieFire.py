from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from BattleBase import *
from BattleProps import *
from BattleSounds import *
from toontown.toon.ToonDNA import *
from toontown.suit.SuitDNA import *
from direct.directnotify import DirectNotifyGlobal
import random
import MovieCamera
import MovieUtil
from MovieUtil import calcAvgSuitPos
notify = DirectNotifyGlobal.directNotify.newCategory('MovieThrow')
hitSoundFiles = ('AA_tart_only.mp3', 'AA_slice_only.mp3', 'AA_slice_only.mp3', 'AA_slice_only.mp3', 'AA_slice_only.mp3', 'AA_wholepie_only.mp3', 'AA_wholepie_only.mp3')
tPieLeavesHand = 2.7
tPieHitsSuit = 3.0
tSuitDodges = 2.45
ratioMissToHit = 1.5
tPieShrink = 0.7
pieFlyTaskName = 'MovieThrow-pieFly'

def addHit(dict, suitId, hitCount):
    if dict.has_key(suitId):
        dict[suitId] += hitCount
    else:
        dict[suitId] = hitCount


def doFires(fires):
    if len(fires) == 0:
        return (None, None)

    suitFiresDict = {}
    for fire in fires:
        suitId = fire['target']['suit'].doId
        if suitFiresDict.has_key(suitId):
            suitFiresDict[suitId].append(fire)
        else:
            suitFiresDict[suitId] = [fire]

    suitFires = suitFiresDict.values()
    def compFunc(a, b):
        if len(a) > len(b):
            return 1
        elif len(a) < len(b):
            return -1
        return 0
    suitFires.sort(compFunc)

    totalHitDict = {}
    singleHitDict = {}
    groupHitDict = {}

    for fire in fires:
        suitId = fire['target']['suit'].doId
        if 1:
            if fire['target']['hp'] > 0:
                addHit(singleHitDict, suitId, 1)
                addHit(totalHitDict, suitId, 1)
            else:
                addHit(singleHitDict, suitId, 0)
                addHit(totalHitDict, suitId, 0)

    notify.debug('singleHitDict = %s' % singleHitDict)
    notify.debug('groupHitDict = %s' % groupHitDict)
    notify.debug('totalHitDict = %s' % totalHitDict)

    delay = 0.0
    mtrack = Parallel()
    firedTargets = []
    for sf in suitFires:
        if len(sf) > 0:
            ival = __doSuitFires(sf)
            if ival:
                mtrack.append(Sequence(Wait(delay), ival))
            delay = delay + TOON_FIRE_SUIT_DELAY

    retTrack = Sequence()
    retTrack.append(mtrack)
    camDuration = retTrack.getDuration()
    camTrack = MovieCamera.chooseFireShot(fires, suitFiresDict, camDuration)
    return (retTrack, camTrack)

def __doSuitFires(fires):
    toonTracks = Parallel()
    delay = 0.0
    hitCount = 0
    for fire in fires:
        if fire['target']['hp'] > 0:
            hitCount += 1
        else:
            break

    suitList = []
    for fire in fires:
        if fire['target']['suit'] not in suitList:
            suitList.append(fire['target']['suit'])

    for fire in fires:
        showSuitCannon = 1
        if fire['target']['suit'] not in suitList:
            showSuitCannon = 0
        else:
            suitList.remove(fire['target']['suit'])
        tracks = __throwPie(fire, delay, hitCount, showSuitCannon)
        if tracks:
            for track in tracks:
                toonTracks.append(track)

        delay = delay + TOON_THROW_DELAY

    return toonTracks


def __showProp(prop, parent, pos):
    prop.reparentTo(parent)
    prop.setPos(pos)


def __animProp(props, propName, propType):
    if 'actor' == propType:
        for prop in props:
            prop.play(propName)

    elif 'model' == propType:
        pass
    else:
        notify.error('No such propType as: %s' % propType)


def __billboardProp(prop):
    scale = prop.getScale()
    prop.setBillboardPointWorld()
    prop.setScale(scale)


def __suitMissPoint(suit, other = render):
    pnt = suit.getPos(other)
    pnt.setZ(pnt[2] + suit.getHeight() * 1.3)
    return pnt


def __propPreflight(props, suit, toon, battle):
    prop = props[0]
    toon.update(0)
    prop.wrtReparentTo(battle)
    props[1].reparentTo(hidden)
    for ci in range(prop.getNumChildren()):
        prop.getChild(ci).setHpr(0, -90, 0)

    targetPnt = MovieUtil.avatarFacePoint(suit, other=battle)
    prop.lookAt(targetPnt)


def __propPreflightGroup(props, suits, toon, battle):
    prop = props[0]
    toon.update(0)
    prop.wrtReparentTo(battle)
    props[1].reparentTo(hidden)
    for ci in range(prop.getNumChildren()):
        prop.getChild(ci).setHpr(0, -90, 0)

    avgTargetPt = Point3(0, 0, 0)
    for suit in suits:
        avgTargetPt += MovieUtil.avatarFacePoint(suit, other=battle)

    avgTargetPt /= len(suits)
    prop.lookAt(avgTargetPt)


def __piePreMiss(missDict, pie, suitPoint, other = render):
    missDict['pie'] = pie
    missDict['startScale'] = pie.getScale()
    missDict['startPos'] = pie.getPos(other)
    v = Vec3(suitPoint - missDict['startPos'])
    endPos = missDict['startPos'] + v * ratioMissToHit
    missDict['endPos'] = endPos


def __pieMissLerpCallback(t, missDict):
    pie = missDict['pie']
    newPos = missDict['startPos'] * (1.0 - t) + missDict['endPos'] * t
    if t < tPieShrink:
        tScale = 0.0001
    else:
        tScale = (t - tPieShrink) / (1.0 - tPieShrink)
    newScale = missDict['startScale'] * max(1.0 - tScale, 0.01)
    pie.setPos(newPos)
    pie.setScale(newScale)


def __piePreMissGroup(missDict, pies, suitPoint, other = render):
    missDict['pies'] = pies
    missDict['startScale'] = pies[0].getScale()
    missDict['startPos'] = pies[0].getPos(other)
    v = Vec3(suitPoint - missDict['startPos'])
    endPos = missDict['startPos'] + v * ratioMissToHit
    missDict['endPos'] = endPos
    notify.debug('startPos=%s' % missDict['startPos'])
    notify.debug('v=%s' % v)
    notify.debug('endPos=%s' % missDict['endPos'])


def __pieMissGroupLerpCallback(t, missDict):
    pies = missDict['pies']
    newPos = missDict['startPos'] * (1.0 - t) + missDict['endPos'] * t
    if t < tPieShrink:
        tScale = 0.0001
    else:
        tScale = (t - tPieShrink) / (1.0 - tPieShrink)
    newScale = missDict['startScale'] * max(1.0 - tScale, 0.01)
    for pie in pies:
        pie.setPos(newPos)
        pie.setScale(newScale)


def __getSoundTrack(level, hitSuit, node = None):
    throwSound = globalBattleSoundCache.getSound('AA_drop_trigger_box.mp3')
    throwTrack = Sequence(Wait(2.15), SoundInterval(throwSound, node=node))
    return throwTrack


def __throwPie(throw, delay, hitCount, showCannon = 1):
    toon = throw['toon']
    hpbonus = throw['hpbonus']
    target = throw['target']
    suit = target['suit']
    hp = target['hp']
    kbbonus = target['kbbonus']
    sidestep = throw['sidestep']
    died = target['died']
    revived = target['revived']
    leftSuits = target['leftSuits']
    rightSuits = target['rightSuits']
    level = throw['level']
    battle = throw['battle']
    suitPos = suit.getPos(battle)
    origHpr = toon.getHpr(battle)
    notify.debug('toon: %s throws tart at suit: %d for hp: %d died: %d' % (toon.getName(),
     suit.doId,
     hp,
     died))
    pieName = pieNames[0]
    hitSuit = hp > 0
    button = globalPropPool.getProp('button')
    buttonType = globalPropPool.getPropType('button')
    button2 = MovieUtil.copyProp(button)
    buttons = [button, button2]
    hands = toon.getLeftHands()
    toonTrack = Sequence()
    toonFace = Func(toon.headsUp, battle, suitPos)
    toonTrack.append(Wait(delay))
    toonTrack.append(toonFace)
    toonTrack.append(ActorInterval(toon, 'pushbutton'))
    toonTrack.append(ActorInterval(toon, 'wave', duration=2.0))
    toonTrack.append(ActorInterval(toon, 'duck'))
    toonTrack.append(Func(toon.loop, 'neutral'))
    toonTrack.append(Func(toon.setHpr, battle, origHpr))
    buttonTrack = Sequence()
    buttonShow = Func(MovieUtil.showProps, buttons, hands)
    buttonScaleUp = LerpScaleInterval(button, 1.0, button.getScale(), startScale=Point3(0.01, 0.01, 0.01))
    buttonScaleDown = LerpScaleInterval(button, 1.0, Point3(0.01, 0.01, 0.01), startScale=button.getScale())
    buttonHide = Func(MovieUtil.removeProps, buttons)
    buttonTrack.append(Wait(delay))
    buttonTrack.append(buttonShow)
    buttonTrack.append(buttonScaleUp)
    buttonTrack.append(Wait(2.5))
    buttonTrack.append(buttonScaleDown)
    buttonTrack.append(buttonHide)
    soundTrack = __getSoundTrack(level, hitSuit, toon)
    suitResponseTrack = Sequence()
    reactIval = Sequence()
    if showCannon:
        showDamage = Func(suit.showHpText, -hp, openEnded=0)
        updateHealthBar = Func(suit.updateHealthBar, hp)
        cannon = loader.loadModel('phase_4/models/minigames/toon_cannon')
        barrel = cannon.find('**/cannon')
        barrel.setHpr(0, 90, 0)
        cannonHolder = render.attachNewNode('CannonHolder')
        cannon.reparentTo(cannonHolder)
        cannon.setPos(0, 0, -8.6)
        cannonHolder.setPos(suit.getPos(render))
        cannonHolder.setHpr(suit.getHpr(render))
        cannonAttachPoint = barrel.attachNewNode('CannonAttach')
        kapowAttachPoint = barrel.attachNewNode('kapowAttach')
        scaleFactor = 1.6
        iScale = 1 / scaleFactor
        barrel.setScale(scaleFactor, 1, scaleFactor)
        cannonAttachPoint.setScale(iScale, 1, iScale)
        cannonAttachPoint.setPos(0, 6.7, 0)
        kapowAttachPoint.setPos(0, -0.5, 1.9)
        suit.reparentTo(cannonAttachPoint)
        suit.setPos(0, 0, 0)
        suit.setHpr(0, -90, 0)
        suitLevel = suit.getActualLevel()
        deep = 2.5 + suitLevel * 0.2
        suitScale = 0.9
        import math
        suitScale = 0.9 - math.sqrt(suitLevel) * 0.1
        sival = []
        posInit = cannonHolder.getPos()
        posFinal = Point3(posInit[0] + 0.0, posInit[1] + 0.0, posInit[2] + 7.0)
        kapow = globalPropPool.getProp('kapow')
        kapow.reparentTo(kapowAttachPoint)
        kapow.hide()
        kapow.setScale(0.25)
        kapow.setBillboardPointEye()
        smoke = loader.loadModel('phase_4/models/props/test_clouds')
        smoke.reparentTo(cannonAttachPoint)
        smoke.setScale(0.5)
        smoke.hide()
        smoke.setBillboardPointEye()
        soundBomb = base.loadSfx('phase_4/audio/sfx/MG_cannon_fire_alt.mp3')
        playSoundBomb = SoundInterval(soundBomb, node=cannonHolder)
        soundFly = base.loadSfx('phase_4/audio/sfx/firework_whistle_01.mp3')
        playSoundFly = SoundInterval(soundFly, node=cannonHolder)
        soundCannonAdjust = base.loadSfx('phase_4/audio/sfx/MG_cannon_adjust.mp3')
        playSoundCannonAdjust = SoundInterval(soundCannonAdjust, duration=0.6, node=cannonHolder)
        soundCogPanic = base.loadSfx('phase_5/audio/sfx/ENC_cogafssm.mp3')
        playSoundCogPanic = SoundInterval(soundCogPanic, node=cannonHolder)
        reactIval = Parallel(ActorInterval(suit, 'pie-small-react'), Sequence(Wait(0.0), LerpPosInterval(cannonHolder, 2.0, posFinal, startPos=posInit, blendType='easeInOut'), Parallel(LerpHprInterval(barrel, 0.6, Point3(0, 45, 0), startHpr=Point3(0, 90, 0), blendType='easeIn'), playSoundCannonAdjust), Wait(2.0), Parallel(LerpHprInterval(barrel, 0.6, Point3(0, 90, 0), startHpr=Point3(0, 45, 0), blendType='easeIn'), playSoundCannonAdjust), LerpPosInterval(cannonHolder, 1.0, posInit, startPos=posFinal, blendType='easeInOut')), Sequence(Wait(0.0), Parallel(ActorInterval(suit, 'flail'), suit.scaleInterval(1.0, suitScale), LerpPosInterval(suit, 0.25, Point3(0, -1.0, 0.0)), Sequence(Wait(0.25), Parallel(playSoundCogPanic, LerpPosInterval(suit, 1.5, Point3(0, -deep, 0.0), blendType='easeIn')))), Wait(2.5), Parallel(playSoundBomb, playSoundFly, Sequence(Func(smoke.show), Parallel(LerpScaleInterval(smoke, 0.5, 3), LerpColorScaleInterval(smoke, 0.5, Vec4(2, 2, 2, 0))), Func(smoke.hide)), Sequence(Func(kapow.show), 
ActorInterval(kapow, 'kapow'), Func(kapow.hide)), LerpPosInterval(suit, 3.0, Point3(0, 150.0, 0.0)), suit.scaleInterval(3.0, 0.01)), Func(suit.hide)))
        if hitCount == 1:
            sival = Sequence(Parallel(reactIval, MovieUtil.createSuitStunInterval(suit, 0.3, 1.3)), Wait(0.0), Func(cannonHolder.remove))
        else:
            sival = reactIval
        suitResponseTrack.append(Wait(delay + tPieHitsSuit))
        suitResponseTrack.append(showDamage)
        suitResponseTrack.append(updateHealthBar)
        suitResponseTrack.append(sival)
        bonusTrack = Sequence(Wait(delay + tPieHitsSuit))
        if kbbonus > 0:
            bonusTrack.append(Wait(0.75))
            bonusTrack.append(Func(suit.showHpText, -kbbonus, 2, openEnded=0))
        if hpbonus > 0:
            bonusTrack.append(Wait(0.75))
            bonusTrack.append(Func(suit.showHpText, -hpbonus, 1, openEnded=0))
        suitResponseTrack = Parallel(suitResponseTrack, bonusTrack)
    return [toonTrack,
     soundTrack,
     buttonTrack,
     suitResponseTrack]