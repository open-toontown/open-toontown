from pandac.PandaModules import *
from direct.directnotify import DirectNotifyGlobal
from direct.interval.IntervalGlobal import *
from direct.fsm.ClassicFSM import *
from direct.fsm.State import *
from direct.distributed.ClockDelta import globalClockDelta
from otp.avatar import Avatar
from direct.actor import Actor
from direct.task import Task
from toontown.pets import PetDNA
from PetDNA import HeadParts, EarParts, NoseParts, TailParts, BodyTypes, BodyTextures, AllPetColors, getColors, ColorScales, PetEyeColors, EarTextures, TailTextures, getFootTexture, getEarTexture, GiraffeTail, LeopardTail, PetGenders
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals
from direct.showbase import PythonUtil
import random
import types
Component2IconDict = {'boredom': 'Bored',
 'restlessness': None,
 'playfulness': 'Play',
 'loneliness': 'Lonely',
 'sadness': 'Sad',
 'fatigue': 'Sleepy',
 'hunger': 'Hungry',
 'confusion': 'Confused',
 'excitement': 'Surprised',
 'anger': 'Angry',
 'surprise': 'Surprised',
 'affection': 'Love'}

class Pet(Avatar.Avatar):
    notify = DirectNotifyGlobal.directNotify.newCategory('Pet')
    SerialNum = 0
    Interactions = PythonUtil.Enum('SCRATCH, BEG, EAT, NEUTRAL')
    InteractAnims = {Interactions.SCRATCH: ('toPet', 'pet', 'fromPet'),
     Interactions.BEG: ('toBeg', 'beg', 'fromBeg'),
     Interactions.EAT: ('eat', 'swallow', 'neutral'),
     Interactions.NEUTRAL: 'neutral'}

    def __init__(self, forGui = 0):
        Avatar.Avatar.__init__(self)
        self.serialNum = Pet.SerialNum
        Pet.SerialNum += 1
        self.lockedDown = 0
        self.setPickable(1)
        self.setPlayerType(NametagGroup.CCNonPlayer)
        self.animFSM = ClassicFSM('petAnimFSM', [State('off', self.enterOff, self.exitOff),
         State('neutral', self.enterNeutral, self.exitNeutral),
         State('neutralHappy', self.enterNeutralHappy, self.exitNeutralHappy),
         State('neutralSad', self.enterNeutralSad, self.exitNeutralSad),
         State('run', self.enterRun, self.exitRun),
         State('swim', self.enterSwim, self.exitSwim),
         State('teleportIn', self.enterTeleportIn, self.exitTeleportOut),
         State('teleportOut', self.enterTeleportOut, self.exitTeleportOut),
         State('walk', self.enterWalk, self.exitWalk),
         State('walkHappy', self.enterWalkHappy, self.exitWalkHappy),
         State('walkSad', self.enterWalkSad, self.exitWalkSad)], 'off', 'off')
        self.animFSM.enterInitialState()
        self.forGui = forGui
        self.moodModel = None
        self.__blinkName = 'petblink-' + str(self.this)
        self.track = None
        self.soundBackflip = None
        self.soundRollover = None
        self.soundPlaydead = None
        self.soundTeleportIn = None
        self.soundTeleportOut = None
        self.teleportHole = None
        return

    def isPet(self):
        return True

    def stopAnimations(self):
        if self.track:
            self.track.pause()
        self.stopBlink()
        self.animFSM.request('off')

    def delete(self):
        self.stopAnimations()
        self.track = None
        self.soundBackflip = None
        self.soundRollover = None
        self.soundPlaydead = None
        self.soundTeleportIn = None
        self.soundTeleportOut = None
        if self.teleportHole:
            self.teleportHole.cleanup()
            self.teleportHole = None
        self.eyesOpenTexture = None
        self.eyesClosedTexture = None
        self.animFSM = None
        self.eyes = None
        self.rightPupil = None
        self.rightHighlight = None
        self.rightBrow = None
        self.leftPupil = None
        self.leftHighlight = None
        self.leftBrow = None
        self.color = None
        Avatar.Avatar.delete(self)
        return

    def getDNA(self):
        return self.style

    def setDNA(self, dna):
        if self.style:
            pass
        else:
            self.style = dna
            self.generatePet()
            self.generateMoods()
            self.initializeDropShadow()
            self.initializeNametag3d()
            self.dropShadow.setScale(0.75)

    def generatePet(self):
        self.loadModel('phase_4/models/char/TT_pets-mod')
        self.loadAnims({'toBeg': 'phase_5/models/char/TT_pets-intoBeg',
         'beg': 'phase_5/models/char/TT_pets-beg',
         'fromBeg': 'phase_5/models/char/TT_pets-begOut',
         'backflip': 'phase_5/models/char/TT_pets-backflip',
         'dance': 'phase_5/models/char/TT_pets-heal',
         'toDig': 'phase_5/models/char/TT_pets-intoDig',
         'dig': 'phase_5/models/char/TT_pets-dig',
         'fromDig': 'phase_5/models/char/TT_pets-digToNeutral',
         'disappear': 'phase_5/models/char/TT_pets-disappear',
         'eat': 'phase_5.5/models/char/TT_pets-eat',
         'jump': 'phase_5/models/char/TT_pets-jump',
         'neutral': 'phase_4/models/char/TT_pets-neutral',
         'neutralHappy': 'phase_4/models/char/TT_pets-neutralHappy',
         'neutralSad': 'phase_4/models/char/TT_pets-neutral_sad',
         'toPet': 'phase_5.5/models/char/TT_pets-petin',
         'pet': 'phase_5.5/models/char/TT_pets-petloop',
         'fromPet': 'phase_5.5/models/char/TT_pets-petend',
         'playDead': 'phase_5/models/char/TT_pets-playdead',
         'fromPlayDead': 'phase_5/models/char/TT_pets-deadend',
         'reappear': 'phase_5/models/char/TT_pets-reappear',
         'run': 'phase_5.5/models/char/TT_pets-run',
         'rollover': 'phase_5/models/char/TT_pets-rollover',
         'walkSad': 'phase_5.5/models/char/TT_pets-sadwalk',
         'speak': 'phase_5/models/char/TT_pets-speak',
         'swallow': 'phase_5.5/models/char/TT_pets-swallow',
         'swim': 'phase_5.5/models/char/TT_pets-swim',
         'toBall': 'phase_5.5/models/char/TT_pets-toBall',
         'walk': 'phase_5.5/models/char/TT_pets-walk',
         'walkHappy': 'phase_5.5/models/char/TT_pets-walkHappy'})
        self.setHeight(2)
        color = None
        colorIndex = self.style[5]
        color = AllPetColors[colorIndex]
        self.color = color
        bodyType = self.style[4]
        body = self.find('**/body')
        tex = loader.loadTexture(BodyTextures[BodyTypes[bodyType]])
        tex.setMinfilter(Texture.FTLinear)
        tex.setMagfilter(Texture.FTLinear)
        body.setTexture(tex, 1)
        body.setColor(color)
        leftFoot = self.find('**/leftFoot')
        rightFoot = self.find('**/rightFoot')
        texName = getFootTexture(bodyType)
        tex = loader.loadTexture(texName)
        tex.setMinfilter(Texture.FTLinear)
        tex.setMagfilter(Texture.FTLinear)
        leftFoot.setTexture(tex, 1)
        rightFoot.setTexture(tex, 1)
        leftFoot.setColor(color)
        rightFoot.setColor(color)
        for part in HeadParts + EarParts + NoseParts + TailParts:
            self.find('**/' + part).stash()

        colorScale = ColorScales[self.style[6]]
        partColor = self.amplifyColor(color, colorScale)
        headIndex = self.style[0]
        if headIndex != -1:
            head = self.find('**/@@' + HeadParts[headIndex])
            head.setColor(partColor)
            head.unstash()
        earsIndex = self.style[1]
        if earsIndex != -1:
            ears = self.find('**/@@' + EarParts[earsIndex])
            ears.setColor(partColor)
            texName = getEarTexture(bodyType, EarParts[earsIndex])
            if texName:
                tex = loader.loadTexture(texName)
                tex.setMinfilter(Texture.FTLinear)
                tex.setMagfilter(Texture.FTLinear)
                ears.setTexture(tex, 1)
            ears.unstash()
        noseIndex = self.style[2]
        if noseIndex != -1:
            nose = self.find('**/@@' + NoseParts[noseIndex])
            nose.setColor(partColor)
            nose.unstash()
        tailIndex = self.style[3]
        if tailIndex != -1:
            tail = self.find('**/@@' + TailParts[tailIndex])
            tail.setColor(partColor)
            texName = TailTextures[TailParts[tailIndex]]
            if texName:
                if BodyTypes[bodyType] == 'giraffe':
                    texName = GiraffeTail
                elif BodyTypes[bodyType] == 'leopard':
                    texName = LeopardTail
                tex = loader.loadTexture(texName)
                tex.setMinfilter(Texture.FTLinear)
                tex.setMagfilter(Texture.FTLinear)
                tail.setTexture(tex, 1)
            tail.unstash()
        if not self.forGui:
            self.drawInFront('eyeWhites', 'body', 1)
            self.drawInFront('rightPupil', 'eyeWhites', 2)
            self.drawInFront('leftPupil', 'eyeWhites', 2)
            self.drawInFront('rightHighlight', 'rightPupil', 3)
            self.drawInFront('leftHighlight', 'leftPupil', 3)
        else:
            self.drawInFront('eyeWhites', 'body', -2)
            self.drawInFront('rightPupil', 'eyeWhites', -2)
            self.drawInFront('leftPupil', 'eyeWhites', -2)
            self.find('**/rightPupil').adjustAllPriorities(1)
            self.find('**/leftPupil').adjustAllPriorities(1)
        eyes = self.style[7]
        eyeColor = PetEyeColors[eyes]
        self.eyes = self.find('**/eyeWhites')
        self.rightPupil = self.find('**/rightPupil')
        self.leftPupil = self.find('**/leftPupil')
        self.rightHighlight = self.find('**/rightHighlight')
        self.leftHighlight = self.find('**/leftHighlight')
        self.rightBrow = self.find('**/rightBrow')
        self.leftBrow = self.find('**/leftBrow')
        self.eyes.setColor(1, 1, 1, 1)
        self.rightPupil.setColor(eyeColor, 2)
        self.leftPupil.setColor(eyeColor, 2)
        self.rightHighlight.setColor(1, 1, 1, 1)
        self.leftHighlight.setColor(1, 1, 1, 1)
        self.rightBrow.setColor(0, 0, 0, 1)
        self.leftBrow.setColor(0, 0, 0, 1)
        self.eyes.setTwoSided(1, 1)
        self.rightPupil.setTwoSided(1, 1)
        self.leftPupil.setTwoSided(1, 1)
        self.rightHighlight.setTwoSided(1, 1)
        self.leftHighlight.setTwoSided(1, 1)
        self.rightBrow.setTwoSided(1, 1)
        self.leftBrow.setTwoSided(1, 1)
        if self.forGui:
            self.rightHighlight.hide()
            self.leftHighlight.hide()
        if self.style[8]:
            self.eyesOpenTexture = loader.loadTexture('phase_4/maps/BeanEyeBoys2.jpg', 'phase_4/maps/BeanEyeBoys2_a.rgb')
            self.eyesClosedTexture = loader.loadTexture('phase_4/maps/BeanEyeBoysBlink.jpg', 'phase_4/maps/BeanEyeBoysBlink_a.rgb')
        else:
            self.eyesOpenTexture = loader.loadTexture('phase_4/maps/BeanEyeGirlsNew.jpg', 'phase_4/maps/BeanEyeGirlsNew_a.rgb')
            self.eyesClosedTexture = loader.loadTexture('phase_4/maps/BeanEyeGirlsBlinkNew.jpg', 'phase_4/maps/BeanEyeGirlsBlinkNew_a.rgb')
        self.eyesOpenTexture.setMinfilter(Texture.FTLinear)
        self.eyesOpenTexture.setMagfilter(Texture.FTLinear)
        self.eyesClosedTexture.setMinfilter(Texture.FTLinear)
        self.eyesClosedTexture.setMagfilter(Texture.FTLinear)
        self.eyesOpen()
        return None

    def initializeBodyCollisions(self, collIdStr):
        Avatar.Avatar.initializeBodyCollisions(self, collIdStr)
        if not self.ghostMode:
            self.collNode.setCollideMask(self.collNode.getIntoCollideMask() | ToontownGlobals.PieBitmask)

    def amplifyColor(self, color, scale):
        color = color * scale
        for i in (0, 1, 2):
            if color[i] > 1.0:
                color.setCell(i, 1.0)

        return color

    def generateMoods(self):
        moodIcons = loader.loadModel('phase_4/models/char/petEmotes')
        self.moodIcons = self.attachNewNode('moodIcons')
        self.moodIcons.setScale(2.0)
        self.moodIcons.setZ(3.65)
        moods = moodIcons.findAllMatches('**/+GeomNode')
        for moodNum in range(0, moods.getNumPaths()):
            mood = moods.getPath(moodNum)
            mood.reparentTo(self.moodIcons)
            mood.setBillboardPointEye()
            mood.hide()

    def clearMood(self):
        if self.moodModel:
            self.moodModel.hide()
        self.moodModel = None
        return

    def showMood(self, mood):
        if hasattr(base.cr, 'newsManager') and base.cr.newsManager:
            holidayIds = base.cr.newsManager.getHolidayIdList()
            if (ToontownGlobals.APRIL_FOOLS_COSTUMES in holidayIds or ToontownGlobals.SILLYMETER_EXT_HOLIDAY in holidayIds) and not mood == 'confusion':
                self.speakMood(mood)
                return
            else:
                self.clearChat()
        else:
            self.clearChat()
        mood = Component2IconDict[mood]
        if mood is None:
            moodModel = None
        else:
            moodModel = self.moodIcons.find('**/*' + mood + '*')
            if moodModel.isEmpty():
                self.notify.warning('No such mood!: %s' % mood)
                return
        if self.moodModel == moodModel:
            return
        if self.moodModel:
            self.moodModel.hide()
        self.moodModel = moodModel
        if self.moodModel:
            self.moodModel.show()
        return

    def speakMood(self, mood):
        if self.moodModel:
            self.moodModel.hide()
        if base.config.GetBool('want-speech-bubble', 1):
            self.nametag.setChat(random.choice(TTLocalizer.SpokenMoods[mood]), CFSpeech)
        else:
            self.nametag.setChat(random.choice(TTLocalizer.SpokenMoods[mood]), CFThought)

    def getGenderString(self):
        if self.style:
            if self.style[8]:
                return TTLocalizer.GenderShopBoyButtonText
            else:
                return TTLocalizer.GenderShopGirlButtonText

    def getShadowJoint(self):
        if hasattr(self, 'shadowJoint'):
            return self.shadowJoint
        shadowJoint = self.find('**/attachShadow')
        if shadowJoint.isEmpty():
            self.shadowJoint = self
        else:
            self.shadowJoint = shadowJoint
        return self.shadowJoint

    def getNametagJoints(self):
        joints = []
        bundle = self.getPartBundle('modelRoot')
        joint = bundle.findChild('attachNametag')
        if joint:
            joints.append(joint)
        return joints

    def fitAndCenterHead(self, maxDim, forGui = 0):
        p1 = Point3()
        p2 = Point3()
        self.calcTightBounds(p1, p2)
        if forGui:
            h = 180
            t = p1[0]
            p1.setX(-p2[0])
            p2.setX(-t)
            self.getGeomNode().setDepthWrite(1)
            self.getGeomNode().setDepthTest(1)
        else:
            h = 0
        d = p2 - p1
        biggest = max(d[0], d[2])
        s = (maxDim + 0.0) / biggest
        mid = (p1 + d / 2.0) * s
        self.setPosHprScale(-mid[0], -mid[1] + 1, -mid[2], h, 0, 0, s, s, s)

    def makeRandomPet(self):
        dna = PetDNA.getRandomPetDNA()
        self.setDNA(dna)

    def enterOff(self):
        self.stop()

    def exitOff(self):
        pass

    def enterBall(self):
        self.setPlayRate(1, 'toBall')
        self.play('toBall')

    def exitBall(self):
        self.setPlayRate(-1, 'toBall')
        self.play('toBall')

    def enterBackflip(self):
        self.play('backflip')

    def exitBackflip(self):
        self.stop('backflip')

    def enterBeg(self):
        delay = self.getDuration('toBeg')
        self.track = Sequence(Func(self.play, 'toBeg'), Wait(delay), Func(self.loop, 'beg'))
        self.track.start()

    def exitBeg(self):
        self.track.pause()
        self.play('fromBeg')

    def enterEat(self):
        self.loop('eat')

    def exitEat(self):
        self.stop('swallow')

    def enterDance(self):
        self.loop('dance')

    def exitDance(self):
        self.stop('dance')

    def enterNeutral(self):
        anim = 'neutral'
        self.pose(anim, random.choice(range(0, self.getNumFrames(anim))))
        self.loop(anim, restart=0)

    def exitNeutral(self):
        self.stop('neutral')

    def enterNeutralHappy(self):
        anim = 'neutralHappy'
        self.pose(anim, random.choice(range(0, self.getNumFrames(anim))))
        self.loop(anim, restart=0)

    def exitNeutralHappy(self):
        self.stop('neutralHappy')

    def enterNeutralSad(self):
        anim = 'neutralSad'
        self.pose(anim, random.choice(range(0, self.getNumFrames(anim))))
        self.loop(anim, restart=0)

    def exitNeutralSad(self):
        self.stop('neutralSad')

    def enterRun(self):
        self.loop('run')

    def exitRun(self):
        self.stop('run')

    def enterSwim(self):
        self.loop('swim')

    def exitSwim(self):
        self.stop('swim')

    def getTeleportInTrack(self):
        if not self.teleportHole:
            self.teleportHole = Actor.Actor('phase_3.5/models/props/portal-mod', {'hole': 'phase_3.5/models/props/portal-chan'})
        track = Sequence(Wait(1.0), Parallel(self.getTeleportInSoundInterval(), Sequence(Func(self.showHole), ActorInterval(self.teleportHole, 'hole', startFrame=81, endFrame=71), ActorInterval(self, 'reappear'), ActorInterval(self.teleportHole, 'hole', startFrame=71, endFrame=81), Func(self.cleanupHole), Func(self.loop, 'neutral')), Sequence(Func(self.dropShadow.hide), Wait(1.0), Func(self.dropShadow.show))))
        return track

    def enterTeleportIn(self, timestamp):
        self.track = self.getTeleportInTrack()
        self.track.start(globalClockDelta.localElapsedTime(timestamp))

    def exitTeleportIn(self):
        self.track.pause()

    def getTeleportOutTrack(self):
        if not self.teleportHole:
            self.teleportHole = Actor.Actor('phase_3.5/models/props/portal-mod', {'hole': 'phase_3.5/models/props/portal-chan'})
        track = Sequence(Wait(1.0), Parallel(self.getTeleportOutSoundInterval(), Sequence(ActorInterval(self, 'toDig'), Parallel(ActorInterval(self, 'dig'), Func(self.showHole), ActorInterval(self.teleportHole, 'hole', startFrame=81, endFrame=71)), ActorInterval(self, 'disappear'), ActorInterval(self.teleportHole, 'hole', startFrame=71, endFrame=81), Func(self.cleanupHole)), Sequence(Wait(1.0), Func(self.dropShadow.hide))))
        return track

    def enterTeleportOut(self, timestamp):
        self.track = self.getTeleportOutTrack()
        self.track.start(globalClockDelta.localElapsedTime(timestamp))

    def exitTeleportOut(self):
        self.track.pause()

    def showHole(self):
        if self.teleportHole:
            self.teleportHole.setBin('shadow', 0)
            self.teleportHole.setDepthTest(0)
            self.teleportHole.setDepthWrite(0)
            self.teleportHole.reparentTo(self)
            self.teleportHole.setScale(0.75)
            self.teleportHole.setPos(0, -1, 0)

    def cleanupHole(self):
        if self.teleportHole:
            self.teleportHole.reparentTo(hidden)
            self.teleportHole.clearBin()
            self.teleportHole.clearDepthTest()
            self.teleportHole.clearDepthWrite()

    def getTeleportInSoundInterval(self):
        if not self.soundTeleportIn:
            self.soundTeleportIn = loader.loadSfx('phase_5/audio/sfx/teleport_reappear.mp3')
        return SoundInterval(self.soundTeleportIn)

    def getTeleportOutSoundInterval(self):
        if not self.soundTeleportOut:
            self.soundTeleportOut = loader.loadSfx('phase_5/audio/sfx/teleport_disappear.mp3')
        return SoundInterval(self.soundTeleportOut)

    def enterWalk(self):
        self.loop('walk')

    def exitWalk(self):
        self.stop('walk')

    def enterWalkHappy(self):
        self.loop('walkHappy')

    def exitWalkHappy(self):
        self.stop('walkHappy')

    def enterWalkSad(self):
        self.loop('walkSad')

    def exitWalkSad(self):
        self.stop('walkSad')

    def trackAnimToSpeed(self, forwardVel, rotVel, inWater = 0):
        action = 'neutral'
        if self.isInWater():
            action = 'swim'
        elif forwardVel > 0.1 or abs(rotVel) > 0.1:
            action = 'walk'
        self.setAnimWithMood(action)

    def setAnimWithMood(self, action):
        how = ''
        if self.isExcited():
            how = 'Happy'
        elif self.isSad():
            how = 'Sad'
        if action == 'swim':
            anim = action
        else:
            anim = '%s%s' % (action, how)
        if anim != self.animFSM.getCurrentState().getName():
            self.animFSM.request(anim)

    def isInWater(self):
        return 0

    def isExcited(self):
        return 0

    def isSad(self):
        return 0

    def startTrackAnimToSpeed(self):
        self.lastPos = self.getPos(render)
        self.lastH = self.getH(render)
        taskMgr.add(self._trackAnimTask, self.getTrackAnimTaskName())

    def stopTrackAnimToSpeed(self):
        taskMgr.remove(self.getTrackAnimTaskName())
        del self.lastPos
        del self.lastH

    def getTrackAnimTaskName(self):
        return 'trackPetAnim-%s' % self.serialNum

    def _trackAnimTask(self, task):
        curPos = self.getPos(render)
        curH = self.getH(render)
        self.trackAnimToSpeed(curPos - self.lastPos, curH - self.lastH)
        self.lastPos = curPos
        self.lastH = curH
        return Task.cont

    def __blinkOpen(self, task):
        self.eyesOpen()
        r = random.random()
        if r < 0.1:
            t = 0.2
        else:
            t = r * 4.0 + 1
        taskMgr.doMethodLater(t, self.__blinkClosed, self.__blinkName)
        return Task.done

    def __blinkClosed(self, task):
        self.eyesClose()
        taskMgr.doMethodLater(0.125, self.__blinkOpen, self.__blinkName)
        return Task.done

    def startBlink(self):
        taskMgr.remove(self.__blinkName)
        self.eyesOpen()
        t = random.random() * 4.0 + 1
        taskMgr.doMethodLater(t, self.__blinkClosed, self.__blinkName)

    def stopBlink(self):
        taskMgr.remove(self.__blinkName)
        self.eyesOpen()

    def eyesOpen(self):
        self.eyes.setColor(1, 1, 1, 1)
        self.eyes.setTexture(self.eyesOpenTexture, 1)
        self.rightPupil.show()
        self.leftPupil.show()
        if not self.forGui:
            self.rightHighlight.show()
            self.leftHighlight.show()

    def eyesClose(self):
        self.eyes.setColor(self.color)
        self.eyes.setTexture(self.eyesClosedTexture, 1)
        self.rightPupil.hide()
        self.leftPupil.hide()
        if not self.forGui:
            self.rightHighlight.hide()
            self.leftHighlight.hide()

    def lockPet(self):
        if not self.lockedDown:
            self.prevAnimState = self.animFSM.getCurrentState().getName()
            self.animFSM.request('neutral')
        self.lockedDown += 1

    def isLockedDown(self):
        return self.lockedDown != 0

    def unlockPet(self):
        self.lockedDown -= 1
        if not self.lockedDown:
            self.animFSM.request(self.prevAnimState)
            self.prevAnimState = None
        return

    def getInteractIval(self, interactId):
        anims = self.InteractAnims[interactId]
        if type(anims) == types.StringType:
            animIval = ActorInterval(self, anims)
        else:
            animIval = Sequence()
            for anim in anims:
                animIval.append(ActorInterval(self, anim))

        return animIval


def gridPets():
    pets = []
    offsetX = 0
    offsetY = 0
    startPos = base.localAvatar.getPos()
    for body in range(0, len(BodyTypes)):
        colors = getColors(body)
        for color in colors:
            p = Pet()
            p.setDNA([random.choice(range(-1, len(HeadParts))),
             random.choice(range(-1, len(EarParts))),
             random.choice(range(-1, len(NoseParts))),
             random.choice(range(-1, len(TailParts))),
             body,
             color,
             random.choice(range(-1, len(ColorScales))),
             random.choice(range(0, len(PetEyeColors))),
             random.choice(range(0, len(PetGenders)))])
            p.setPos(startPos[0] + offsetX, startPos[1] + offsetY, startPos[2])
            p.animFSM.request('neutral')
            p.reparentTo(render)
            pets.append(p)
            offsetX += 3

        offsetY += 3
        offsetX = 0

    return pets
