import math
import random
from . import GenericAnimatedProp
from direct.actor import Actor
from direct.interval.IntervalGlobal import Sequence, ActorInterval, Wait, Func, SoundInterval, Parallel
from direct.fsm import FSM
from direct.showbase.PythonUtil import weightedChoice
from pandac.PandaModules import TextNode, Vec3
from toontown.toonbase import ToontownGlobals
from toontown.hood import ZoneUtil

def clearPythonIvals(ival):
    if hasattr(ival, 'function'):
        ival.function = None
    if hasattr(ival, 'pythonIvals'):
        for oneIval in ival.pythonIvals:
            clearPythonIvals(oneIval)

        ival.pythonIvals = []
    return


class InteractiveAnimatedProp(GenericAnimatedProp.GenericAnimatedProp, FSM.FSM):
    ZoneToIdles = {}
    ZoneToIdleIntoFightAnims = {}
    ZoneToFightAnims = {}
    ZoneToVictoryAnims = {}
    ZoneToSadAnims = {}
    IdlePauseTime = base.config.GetFloat('prop-idle-pause-time', 0.0)
    HpTextGenerator = TextNode('HpTextGenerator')
    BattleCheerText = '+'

    def __init__(self, node, holidayId = -1):
        FSM.FSM.__init__(self, 'InteractiveProp-%s' % str(node))
        self.holidayId = holidayId
        self.numIdles = 0
        self.numFightAnims = 0
        self.idleInterval = None
        self.battleCheerInterval = None
        self.sadInterval = None
        self.victoryInterval = None
        self.lastIdleAnimName = ''
        self.lastIdleTime = 0
        self.curIval = None
        self.okToStartNextAnim = False
        cellIndexStr = node.getTag('DNACellIndex')
        self.cellIndex = ord(cellIndexStr)
        self.origAnimNameToSound = {}
        self.lastPlayingAnimPhase = 0
        self.buildingsMakingMeSad = set()
        GenericAnimatedProp.GenericAnimatedProp.__init__(self, node)
        return

    def delete(self):
        self.exit()
        GenericAnimatedProp.GenericAnimatedProp.delete(self)
        self.idleInterval = None
        self.battleCheerInterval = None
        self.sadInterval = None
        self.victoryInterval = None
        return

    def getCellIndex(self):
        return self.cellIndex

    def playBattleCheerAnim(self):
        self.node.loop('battleCheer')

    def setupActor(self, node):
        if self.hoodId in self.ZoneToIdles:
            self.numIdles = len(self.ZoneToIdles[self.hoodId])
        if self.hoodId in self.ZoneToFightAnims:
            self.numFightAnims = len(self.ZoneToFightAnims[self.hoodId])
        self.idleInterval = None
        anim = node.getTag('DNAAnim')
        self.trashcan = Actor.Actor(node, copy=0)
        self.trashcan.reparentTo(node)
        animDict = {}
        animDict['anim'] = '%s/%s' % (self.path, anim)
        for i in range(self.numIdles):
            baseAnim = self.ZoneToIdles[self.hoodId][i]
            if isinstance(baseAnim, tuple):
                baseAnim = baseAnim[0]
            animStr = self.path + '/' + baseAnim
            animKey = 'idle%d' % i
            animDict[animKey] = animStr
            settleName = self.getSettleName(i)
            if settleName:
                settleStr = self.path + '/' + settleName
                settleKey = 'settle%d' % i
                animDict[settleKey] = settleStr

        for i in range(self.numFightAnims):
            animStr = self.path + '/' + self.ZoneToFightAnims[self.hoodId][i]
            animKey = 'fight%d' % i
            animDict[animKey] = animStr

        if self.hoodId in self.ZoneToIdleIntoFightAnims:
            animStr = self.path + '/' + self.ZoneToIdleIntoFightAnims[self.hoodId]
            animKey = 'idleIntoFight'
            animDict[animKey] = animStr
        if self.hoodId in self.ZoneToIdleIntoFightAnims:
            animStr = self.path + '/' + self.ZoneToVictoryAnims[self.hoodId]
            animKey = 'victory'
            animDict[animKey] = animStr
        if self.hoodId in self.ZoneToSadAnims:
            animStr = self.path + '/' + self.ZoneToSadAnims[self.hoodId]
            animKey = 'sad'
            animDict[animKey] = animStr
        self.trashcan.loadAnims(animDict)
        self.trashcan.pose('anim', 0)
        self.node = self.trashcan
        self.idleInterval = self.createIdleInterval()
        self.battleCheerInterval = self.createBattleCheerInterval()
        self.victoryInterval = self.createVictoryInterval()
        self.sadInterval = self.createSadInterval()
        return

    def createIdleInterval(self):
        result = Sequence()
        if self.numIdles >= 3:
            numberOfAnimsAbove2 = self.numIdles - 2
            for rareIdle in range(2, self.numIdles):
                for i in range(2):
                    result.append(ActorInterval(self.node, 'idle0'))
                    result.append(Wait(self.IdlePauseTime))
                    result.append(ActorInterval(self.node, 'idle1'))
                    result.append(Wait(self.IdlePauseTime))

                result.append(ActorInterval(self.node, 'idle%d' % rareIdle))
                result.append(Wait(self.IdlePauseTime))

        else:
            for i in range(self.numIdles):
                result.append(ActorInterval(self.node, 'idle%d' % i))

        self.notify.debug('idle interval=%s' % result)
        return result

    def createBattleCheerText(self):
        self.HpTextGenerator.setFont(ToontownGlobals.getSignFont())
        self.HpTextGenerator.setText(self.BattleCheerText)
        self.HpTextGenerator.clearShadow()
        self.HpTextGenerator.setAlign(TextNode.ACenter)
        r = 0
        g = 0
        b = 1
        a = 1
        self.HpTextGenerator.setTextColor(r, g, b, a)
        self.hpTextNode = self.HpTextGenerator.generate()
        self.hpText = self.node.attachNewNode(self.hpTextNode)
        self.hpText.setScale(1)
        self.hpText.setBillboardPointEye()
        self.hpText.setBin('fixed', 100)
        self.hpText.setPos(0, 0, 4)
        self.hpText.hide()

    def createBattleCheerInterval(self):
        result = Sequence()
        for i in range(self.numFightAnims):
            animKey = 'fight%d' % i
            animAndSoundIval = self.createAnimAndSoundIval(animKey)
            origAnimName = self.node.getAnimFilename(animKey).split('/')[-1]
            if self.hasOverrideIval(origAnimName):
                result.append(self.getOverrideIval(origAnimName))
            elif self.hasSpecialIval(origAnimName):
                result.append(Parallel(animAndSoundIval, self.getSpecialIval(origAnimName)))
            else:
                result.append(animAndSoundIval)

        self.createBattleCheerText()
        battleCheerTextIval = Sequence(Func(self.hpText.show), self.hpText.posInterval(duration=4.0, pos=Vec3(0, 0, 7), startPos=(0, 0, 3)), Func(self.hpText.hide))
        ivalWithText = Parallel(battleCheerTextIval, result)
        return ivalWithText

    def createSadInterval(self):
        result = Sequence()
        if self.hoodId in self.ZoneToSadAnims:
            result = self.createAnimAndSoundIval('sad')
        return result

    def hasSpecialIval(self, origAnimName):
        return False

    def getSpecialIval(self, origAnimName):
        return Sequence()

    def hasOverrideIval(self, origAnimName):
        return False

    def getOverrideIval(self, origAnimName):
        return Sequence()

    def createVictoryInterval(self):
        result = Sequence()
        if self.hoodId in self.ZoneToVictoryAnims:
            animAndSoundIval = self.createAnimAndSoundIval('victory')
            result.append(animAndSoundIval)
        return result

    def enter(self):
        GenericAnimatedProp.GenericAnimatedProp.enter(self)
        if base.config.GetBool('props-buff-battles', True):
            self.notify.debug('props buff battles is true')
            if base.cr.newsManager.isHolidayRunning(self.holidayId):
                self.notify.debug('holiday is running, doing idle interval')
                self.node.stop()
                self.node.pose('idle0', 0)
                if base.config.GetBool('interactive-prop-random-idles', 1):
                    self.requestIdleOrSad()
                else:
                    self.idleInterval.loop()
            else:
                self.notify.debug('holiday is NOT running, doing nothing')
                self.node.stop()
                self.node.pose('idle0', 0)
        else:
            self.notify.debug('props do not buff battles')
            self.node.stop()
            self.node.pose('idle0', 0)

    def exit(self):
        self.okToStartNextAnim = False
        self.notify.debug('%s %d okToStartNextAnim=%s' % (self, self.visId, self.okToStartNextAnim))
        GenericAnimatedProp.GenericAnimatedProp.exit(self)
        self.request('Off')

    def requestIdleOrSad(self):
        if not hasattr(self, 'node') or not self.node:
            self.notify.warning("requestIdleOrSad  returning hasattr(self,'node')=%s" % hasattr(self, 'node'))
            return
        if self.buildingsMakingMeSad:
            self.request('Sad')
        else:
            self.request('DoIdleAnim')

    def enterDoIdleAnim(self):
        self.notify.debug('enterDoIdleAnim numIdels=%d' % self.numIdles)
        self.okToStartNextAnim = True
        self.notify.debug('%s %d okToStartNextAnim=%s' % (self, self.visId, self.okToStartNextAnim))
        self.startNextIdleAnim()

    def exitDoIdleAnim(self):
        self.notify.debug('exitDoIdlesAnim numIdles=%d' % self.numIdles)
        self.okToStartNextAnim = False
        self.notify.debug('%s %d okToStartNextAnim=%s' % (self, self.visId, self.okToStartNextAnim))
        self.calcLastIdleFrame()
        self.clearCurIval()

    def calcLastIdleFrame(self):
        if self.curIval and self.curIval.ivals:
            firstIval = self.curIval.ivals[0]
            if isinstance(firstIval, ActorInterval):
                self.lastIdleFrame = firstIval.getCurrentFrame()
                self.lastIdleAnimName = firstIval.animName
            elif isinstance(firstIval, Parallel):
                for testIval in firstIval.ivals:
                    if isinstance(firstIval, ActorInterval):
                        self.lastIdleTime = testIval.getT()
                        self.lastIdleAnimName = testIval.animName
                        break

    def chooseIdleAnimToRun(self):
        result = self.numIdles - 1
        if base.config.GetBool('randomize-interactive-idles', True):
            pairs = []
            for i in range(self.numIdles):
                reversedChance = self.numIdles - i - 1
                pairs.append((math.pow(2, reversedChance), i))

            sum = math.pow(2, self.numIdles) - 1
            result = weightedChoice(pairs, sum=sum)
            self.notify.debug('chooseAnimToRun numIdles=%s pairs=%s result=%s' % (self.numIdles, pairs, result))
        else:
            result = self.lastPlayingAnimPhase + 1
            if result >= len(self.ZoneToIdles[self.hoodId]):
                result = 0
        return result

    def startNextIdleAnim(self):
        self.notify.debug('startNextAnim self.okToStartNextAnim=%s' % self.okToStartNextAnim)
        if not hasattr(self, 'node') or not self.node:
            self.notify.warning("startNextIdleAnim returning hasattr(self,'node')=%s" % hasattr(self, 'node'))
            return
        self.curIval = None
        if self.okToStartNextAnim:
            self.notify.debug('got pass okToStartNextAnim')
            whichAnim = self.chooseIdleAnimToRun()
            if self.visId == localAvatar.zoneId:
                self.notify.debug('whichAnim=%s' % whichAnim)
                if __dev__:
                    self.notify.info('whichAnim=%s %s' % (whichAnim, self.getOrigIdleAnimName(whichAnim)))
            self.lastPlayingAnimPhase = whichAnim
            self.curIval = self.createIdleAnimSequence(whichAnim)
            self.notify.debug('starting curIval of length %s' % self.curIval.getDuration())
            self.curIval.start()
        else:
            self.curIval = Wait(10)
            self.notify.debug('false self.okToStartNextAnim=%s' % self.okToStartNextAnim)
        return

    def createIdleAnimAndSoundInterval(self, whichIdleAnim, startingTime = 0):
        animIval = self.node.actorInterval('idle%d' % whichIdleAnim, startTime=startingTime)
        animIvalDuration = animIval.getDuration()
        origAnimName = self.ZoneToIdles[self.hoodId][whichIdleAnim]
        if isinstance(origAnimName, tuple):
            origAnimName = origAnimName[0]
        soundIval = self.createSoundInterval(origAnimName, animIvalDuration)
        soundIvalDuration = soundIval.getDuration()
        if self.hasSpecialIval(origAnimName):
            specialIval = self.getSpecialIval(origAnimName)
            idleAnimAndSound = Parallel(animIval, soundIval, specialIval)
        else:
            idleAnimAndSound = Parallel(animIval, soundIval)
        return idleAnimAndSound

    def createIdleAnimSequence(self, whichIdleAnim):
        dummyResult = Sequence(Wait(self.IdlePauseTime))
        if not hasattr(self, 'node') or not self.node:
            self.notify.warning("createIdleAnimSequence returning dummyResult hasattr(self,'node')=%s" % hasattr(self, 'node'))
            return dummyResult
        idleAnimAndSound = self.createIdleAnimAndSoundInterval(whichIdleAnim)
        result = Sequence(idleAnimAndSound, Wait(self.IdlePauseTime), Func(self.startNextIdleAnim))
        if isinstance(self.ZoneToIdles[self.hoodId][whichIdleAnim], tuple) and len(self.ZoneToIdles[self.hoodId][whichIdleAnim]) > 2:
            info = self.ZoneToIdles[self.hoodId][whichIdleAnim]
            origAnimName = info[0]
            minLoop = info[1]
            maxLoop = info[2]
            settleAnim = info[3]
            minPauseTime = info[4]
            maxPauseTime = info[5]
            numberOfLoops = random.randrange(minLoop, maxLoop + 1)
            pauseTime = random.randrange(minPauseTime, maxPauseTime + 1)
            result = Sequence()
            for i in range(numberOfLoops):
                result.append(idleAnimAndSound)

            if self.getSettleName(whichIdleAnim):
                result.append(self.node.actorInterval('settle%d' % whichIdleAnim))
            result.append(Wait(pauseTime))
            result.append(Func(self.startNextIdleAnim))
        return result

    def gotoFaceoff(self):
        self.notify.debugStateCall(self)
        if base.cr.newsManager.isHolidayRunning(self.holidayId):
            self.request('Faceoff')
        else:
            self.notify.debug('not going to faceoff because holiday %d is not running' % self.holidayId)

    def gotoBattleCheer(self):
        self.notify.debugStateCall(self)
        if base.cr.newsManager.isHolidayRunning(self.holidayId):
            self.request('BattleCheer')
        else:
            self.notify.debug('not going to battleCheer because holiday %d is not running' % self.holidayId)

    def gotoIdle(self):
        self.notify.debugStateCall(self)
        if base.cr.newsManager.isHolidayRunning(self.holidayId):
            self.request('DoIdleAnim')
        else:
            self.notify.debug('not going to idle because holiday %d is not running' % self.holidayId)

    def gotoVictory(self):
        self.notify.debugStateCall(self)
        if base.cr.newsManager.isHolidayRunning(self.holidayId):
            self.request('Victory')
        else:
            self.notify.debug('not going to victory because holiday %d is not running' % self.holidayId)

    def gotoSad(self, buildingDoId):
        self.notify.debugStateCall(self)
        self.buildingsMakingMeSad.add(buildingDoId)
        if base.cr.newsManager.isHolidayRunning(self.holidayId):
            self.request('Sad')
        else:
            self.notify.debug('not going to sad because holiday %d is not running' % self.holidayId)

    def buildingLiberated(self, buildingDoId):
        self.buildingsMakingMeSad.discard(buildingDoId)
        if not self.buildingsMakingMeSad:
            self.gotoIdle()

    def enterFaceoff(self):
        self.notify.debugStateCall(self)
        self.curIval = self.createFaceoffInterval()
        self.curIval.start()

    def exitFaceoff(self):
        self.notify.debugStateCall(self)
        self.curIval.pause()
        self.curIval = None
        return

    def calcWhichIdleAnim(self, animName):
        result = 0
        info = self.ZoneToIdles[self.hoodId]
        for index, curInfo in enumerate(info):
            if isinstance(curInfo, tuple):
                if curInfo[0] == animName:
                    result = index
                    break
            elif isinstance(curInfo, str):
                if curInfo == animName:
                    result = index
                    breal

        return result

    def createFaceoffInterval(self):
        result = Sequence()
        if self.lastIdleAnimName:
            whichIdleAnim = self.calcWhichIdleAnim(self.lastIdleAnimName)
            animAndSound = self.createIdleAnimAndSoundInterval(whichIdleAnim, self.lastIdleTime)
            result.append(animAndSound)
        idleIntoFightIval = self.createAnimAndSoundIval('idleIntoFight')
        result.append(idleIntoFightIval)
        result.append(Func(self.gotoBattleCheer))
        return result

    def enterBattleCheer(self):
        self.notify.debugStateCall(self)
        self.curIval = self.battleCheerInterval
        if self.curIval:
            self.curIval.loop()

    def exitBattleCheer(self):
        self.notify.debugStateCall(self)
        if self.curIval:
            self.curIval.finish()
            self.curIval = None
        return

    def enterVictory(self):
        self.notify.debugStateCall(self)
        self.curIval = self.victoryInterval
        if self.curIval:
            self.curIval.loop()

    def exitVictory(self):
        self.notify.debugStateCall(self)
        if self.curIval:
            self.curIval.finish()
            self.curIval = None
        return

    def enterSad(self):
        self.notify.debugStateCall(self)
        self.curIval = self.sadInterval
        if self.curIval:
            self.curIval.loop()

    def exitSad(self):
        self.notify.debugStateCall(self)
        if self.curIval:
            self.curIval.finish()
            self.curIval = None
        return

    def getSettleName(self, whichIdleAnim):
        result = None
        if isinstance(self.ZoneToIdles[self.hoodId][whichIdleAnim], tuple) and len(self.ZoneToIdles[self.hoodId][whichIdleAnim]) > 3:
            result = self.ZoneToIdles[self.hoodId][whichIdleAnim][3]
        return result

    def getOrigIdleAnimName(self, whichIdleAnim):
        result = None
        if isinstance(self.ZoneToIdles[self.hoodId][whichIdleAnim], tuple):
            result = self.ZoneToIdles[self.hoodId][whichIdleAnim][0]
        else:
            result = self.ZoneToIdles[self.hoodId][whichIdleAnim]
        return result

    def createAnimAndSoundIval(self, animKey):
        animIval = self.node.actorInterval(animKey)
        animIvalDuration = animIval.getDuration()
        origAnimName = self.node.getAnimFilename(animKey)
        soundIval = self.createSoundInterval(origAnimName, animIvalDuration)
        soundIvalDuration = soundIval.getDuration()
        printFunc = Func(self.printAnimIfClose, animKey)
        if self.hasSpecialIval(origAnimName):
            specialIval = self.getSpecialIval(origAnimName)
            idleAnimAndSound = Parallel(animIval, soundIval, specialIval)
            if base.config.GetBool('interactive-prop-info', False):
                idleAnimAndSound.append(printFunc)
        else:
            idleAnimAndSound = Parallel(animIval, soundIval)
            if base.config.GetBool('interactive-prop-info', False):
                idleAnimAndSound.append(printFunc)
        return idleAnimAndSound

    def printAnimIfClose(self, animKey):
        if base.config.GetBool('interactive-prop-info', False):
            try:
                animName = self.node.getAnimFilename(animKey)
                baseAnimName = animName.split('/')[-1]
                if localAvatar.zoneId == self.visId:
                    self.notify.info('playing %s' % baseAnimName)
            except Exception as e:
                self.notify.warning('Unknown error in printAnimIfClose, giving up:\n%s' % str(e))

    def clearCurIval(self):
        if self.curIval:
            self.curIval.finish()
        clearPythonIvals(self.curIval)
        self.curIval = None
        return
