from direct.interval.IntervalGlobal import *
from .BattleBase import *
from .BattleProps import *
from .BattleSounds import *
from toontown.toon.ToonDNA import *
from toontown.suit.SuitDNA import *
from direct.particles.ParticleEffect import *
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from . import MovieUtil
from . import MovieCamera
from direct.directnotify import DirectNotifyGlobal
from . import BattleParticles
from toontown.toonbase import ToontownGlobals
from . import RewardPanel
notify = DirectNotifyGlobal.directNotify.newCategory('Fanfare')

def makePanel(toon, showToonName):
    panel = DirectFrame(relief=None, geom=DGG.getDefaultDialogGeom(), geom_color=ToontownGlobals.GlobalDialogColor, geom_scale=(1.75, 1, 0.75), pos=(0, 0, 0.587))
    panel.initialiseoptions(RewardPanel)
    panel.setTransparency(1)
    panel.hide()
    if showToonName == 1:
        panel.avNameLabel = DirectLabel(parent=panel, relief=None, pos=Vec3(0, 0, 0.3), text=toon.getName(), text_scale=0.08)
    return panel


def makeMessageBox(panel, message, messagePos, messageScale, wordwrap = 100):
    panel.itemFrame = DirectFrame(parent=panel, relief=None, text=message, text_pos=messagePos, text_scale=messageScale, text_wordwrap=wordwrap)
    return


def makeImageBox(frame, image, imagePos, imageScale):
    frame.imageIcon = image.copyTo(frame)
    frame.imageIcon.setPos(imagePos)
    frame.imageIcon.setScale(imageScale)


def makeFanfare(delay, toon):
    return doFanfare(delay, toon, None)


def makeFanfareWithMessage(delay, toon, showToonName, message, messagePos, messageScale, wordwrap = 100):
    panel = makePanel(toon, showToonName)
    makeMessageBox(panel, message, messagePos, messageScale, wordwrap)
    return doFanfare(delay, toon, panel)


def makeFanfareWithImage(delay, toon, showToonName, image, imagePos, imageScale, wordwrap = 100):
    panel = makePanel(toon, showToonName)
    makeMessageBox(panel, '', Vec3(0, 0, 0), 1, wordwrap)
    makeImageBox(panel.itemFrame, image, imagePos, imageScale)
    return doFanfare(delay, toon, panel)


def makeFanfareWithMessageImage(delay, toon, showToonName, message, messagePos, messageScale, image, imagePos, imageScale, wordwrap = 100):
    panel = makePanel(toon, showToonName)
    makeMessageBox(panel, message, messagePos, messageScale, wordwrap)
    makeImageBox(panel.itemFrame, image, imagePos, imageScale)
    return doFanfare(delay, toon, panel)


def doFanfare(delay, toon, panel):
    fanfareNode = toon.attachNewNode('fanfareNode')
    partyBall = fanfareNode.attachNewNode('partyBall')
    headparts = toon.getHeadParts()
    pos = headparts[2].getPos(fanfareNode)
    partyBallLeft = globalPropPool.getProp('partyBall')
    partyBallLeft.reparentTo(partyBall)
    partyBallLeft.setScale(0.8)
    partyBallLeft.setH(90)
    partyBallLeft.setColorScale(1, 0, 0, 0)
    partyBallRight = globalPropPool.getProp('partyBall')
    partyBallRight.reparentTo(partyBall)
    partyBallRight.setScale(0.8)
    partyBallRight.setH(-90)
    partyBallRight.setColorScale(1, 1, 0, 0)
    partyBall.setZ(pos.getZ() + 3.2)
    ballShake1 = Sequence(Parallel(LerpHprInterval(partyBallLeft, duration=0.2, startHpr=Vec3(90, 0, 0), hpr=Vec3(90, 10, 0), blendType='easeInOut'), LerpHprInterval(partyBallRight, duration=0.2, startHpr=Vec3(-90, 0, 0), hpr=Vec3(-90, -10, 0), blendType='easeInOut')), Parallel(LerpHprInterval(partyBallLeft, duration=0.2, startHpr=Vec3(90, 10, 0), hpr=Vec3(90, -10, 0), blendType='easeInOut'), LerpHprInterval(partyBallRight, duration=0.2, startHpr=Vec3(-90, -10, 0), hpr=Vec3(-90, 10, 0), blendType='easeInOut')), Parallel(LerpHprInterval(partyBallLeft, duration=0.2, startHpr=Vec3(90, -10, 0), hpr=Vec3(90, 0, 0), blendType='easeInOut'), LerpHprInterval(partyBallRight, duration=0.2, startHpr=Vec3(-90, 10, 0), hpr=Vec3(-90, 0, 0), blendType='easeInOut')))
    ballShake2 = Sequence(Parallel(LerpHprInterval(partyBallLeft, duration=0.2, startHpr=Vec3(90, 0, 0), hpr=Vec3(90, -10, 0), blendType='easeInOut'), LerpHprInterval(partyBallRight, duration=0.2, startHpr=Vec3(-90, 0, 0), hpr=Vec3(-90, 10, 0), blendType='easeInOut')), Parallel(LerpHprInterval(partyBallLeft, duration=0.2, startHpr=Vec3(90, -10, 0), hpr=Vec3(90, 10, 0), blendType='easeInOut'), LerpHprInterval(partyBallRight, duration=0.2, startHpr=Vec3(-90, 10, 0), hpr=Vec3(-90, -10, 0), blendType='easeInOut')), Parallel(LerpHprInterval(partyBallLeft, duration=0.2, startHpr=Vec3(90, 10, 0), hpr=Vec3(90, 0, 0), blendType='easeInOut'), LerpHprInterval(partyBallRight, duration=0.2, startHpr=Vec3(-90, -10, 0), hpr=Vec3(-90, 0, 0), blendType='easeInOut')))
    openBall = Parallel(LerpHprInterval(partyBallLeft, duration=0.2, startHpr=Vec3(90, 0, 0), hpr=Vec3(90, 30, 0)), LerpHprInterval(partyBallRight, duration=0.2, startHpr=Vec3(-90, 0, 0), hpr=Vec3(-90, 30, 0)))
    confettiNode = fanfareNode.attachNewNode('confetti')
    confettiNode.setScale(3)
    confettiNode.setZ(pos.getZ() + 2.5)

    def longshake(models, num, duration):
        inShake = getScaleBlendIntervals(models, duration=duration, startScale=0.23, endScale=0.2, blendType='easeInOut')
        outShake = getScaleBlendIntervals(models, duration=duration, startScale=0.2, endScale=0.23, blendType='easeInOut')
        i = 1
        seq = Sequence()
        while i < num:
            if i % 2 == 0:
                seq.append(inShake)
            else:
                seq.append(outShake)
            i += 1

        return seq

    def getScaleBlendIntervals(props, duration, startScale, endScale, blendType):
        tracks = Parallel()
        for prop in props:
            tracks.append(LerpScaleInterval(prop, duration, endScale, startScale=startScale, blendType=blendType))

        return tracks

    trumpetNode = fanfareNode.attachNewNode('trumpetNode')
    trumpet1 = globalPropPool.getProp('bugle')
    trumpet2 = MovieUtil.copyProp(trumpet1)
    trumpet1.reparentTo(trumpetNode)
    trumpet1.setScale(0.2)
    trumpet1.setPos(2, 2, 1)
    trumpet1.setHpr(120, 65, 0)
    trumpet2.reparentTo(trumpetNode)
    trumpet2.setScale(0.2)
    trumpet2.setPos(-2, 2, 1)
    trumpet2.setHpr(-120, 65, 0)
    trumpetNode.setTransparency(1)
    trumpetNode.setColor(1, 1, 1, 0)
    trumpturn1 = LerpHprInterval(trumpet1, duration=4, startHpr=Vec3(80, 15, 0), hpr=Vec3(150, 40, 0))
    trumpturn2 = LerpHprInterval(trumpet2, duration=4, startHpr=Vec3(-80, 15, 0), hpr=Vec3(-150, 40, 0))
    trumpetTurn = Parallel(trumpturn1, trumpturn2)
    BattleParticles.loadParticles()
    confettiBlue = BattleParticles.createParticleEffect('Confetti')
    confettiBlue.reparentTo(confettiNode)
    blue_p0 = confettiBlue.getParticlesNamed('particles-1')
    blue_p0.renderer.getColorInterpolationManager().addConstant(0.0, 1.0, Vec4(0.0, 0.0, 1.0, 1.0), 1)
    confettiYellow = BattleParticles.createParticleEffect('Confetti')
    confettiYellow.reparentTo(confettiNode)
    yellow_p0 = confettiYellow.getParticlesNamed('particles-1')
    yellow_p0.renderer.getColorInterpolationManager().addConstant(0.0, 1.0, Vec4(1.0, 1.0, 0.0, 1.0), 1)
    confettiRed = BattleParticles.createParticleEffect('Confetti')
    confettiRed.reparentTo(confettiNode)
    red_p0 = confettiRed.getParticlesNamed('particles-1')
    red_p0.renderer.getColorInterpolationManager().addConstant(0.0, 1.0, Vec4(1.0, 0.0, 0.0, 1.0), 1)
    trumpetsAppear = LerpColorInterval(trumpetNode, 0.3, startColor=Vec4(1, 1, 0, 0), color=Vec4(1, 1, 0, 1))
    trumpetsVanish = LerpColorInterval(trumpetNode, 0.3, startColor=Vec4(1, 1, 0, 1), color=Vec4(1, 1, 0, 0))
    crabHorn = globalBattleSoundCache.getSound('King_Crab.ogg')
    drumroll = globalBattleSoundCache.getSound('SZ_MM_drumroll.ogg')
    fanfare = globalBattleSoundCache.getSound('SZ_MM_fanfare.ogg')
    crabHorn.setTime(1.5)
    partyBall.setTransparency(1)
    partyBall.setColorScale(1, 1, 1, 1)
    ballAppear = Parallel(LerpColorScaleInterval(partyBallLeft, 0.3, startColorScale=Vec4(1, 0, 0, 0), colorScale=Vec4(1, 0, 0, 1)), LerpColorScaleInterval(partyBallRight, 0.3, startColorScale=Vec4(1, 1, 0, 0), colorScale=Vec4(1, 1, 0, 1)))
    ballVanish = Parallel(LerpColorScaleInterval(partyBallLeft, 0.3, startColorScale=Vec4(1, 0, 0, 1), colorScale=Vec4(1, 0, 0, 0)), LerpColorScaleInterval(partyBallRight, 0.3, startColorScale=Vec4(1, 1, 0, 1), colorScale=Vec4(1, 1, 0, 0)))
    play = Parallel(SoundInterval(crabHorn, startTime=1.5, duration=4.0, node=toon), Sequence(Wait(0.25), longshake([trumpet1, trumpet2], 3, 0.2), Wait(0.5), longshake([trumpet1, trumpet2], 3, 0.2), Wait(0.5), longshake([trumpet1, trumpet2], 9, 0.1), longshake([trumpet1, trumpet2], 3, 0.2)))
    killParticles = Parallel(Func(blue_p0.setLitterSize, 0), Func(red_p0.setLitterSize, 0), Func(yellow_p0.setLitterSize, 0))
    p = Parallel(ParticleInterval(confettiBlue, confettiNode, worldRelative=0, duration=3, cleanup=True), ParticleInterval(confettiRed, confettiNode, worldRelative=0, duration=3, cleanup=True), ParticleInterval(confettiYellow, confettiNode, worldRelative=0, duration=3, cleanup=True))
    pOff = Parallel(Func(confettiBlue.remove), Func(confettiRed.remove), Func(confettiYellow.remove))
    partInterval = Parallel(p, Sequence(Wait(1.7), killParticles, Wait(1.3), pOff, Func(p.finish)), Sequence(Wait(3), Parallel(ballVanish)))
    seq1 = Parallel(Sequence(Wait(delay + 4.1), SoundInterval(drumroll, node=toon), Wait(0.25), SoundInterval(fanfare, node=toon)), Sequence(Wait(delay), trumpetsAppear, Wait(3), ballAppear, Wait(0.5), ballShake1, Wait(0.1), ballShake2, Wait(0.2), Wait(0.1), Parallel(openBall, partInterval), Func(fanfareNode.remove)))
    seq = Parallel(seq1, Sequence(Wait(delay), Parallel(trumpetTurn, Sequence(Wait(0.5), play)), Wait(0.5), trumpetsVanish))
    if panel != None:
        return (seq, panel)
    return (seq, None)
