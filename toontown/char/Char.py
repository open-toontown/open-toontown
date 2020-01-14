from otp.avatar import Avatar
from pandac.PandaModules import *
from libotp import *
from direct.task import Task
import random
from pandac.PandaModules import *
from direct.directnotify import DirectNotifyGlobal
AnimDict = {'mk': (('walk', 'walk', 3),
        ('run', 'run', 3),
        ('neutral', 'wait', 3),
        ('left-point-start', 'left-start', 3.5),
        ('left-point', 'left', 3.5),
        ('right-point-start', 'right-start', 3.5),
        ('right-point', 'right', 3.5)),
 'vmk': (('walk', 'sneak', 3),
         ('run', 'run', 3),
         ('neutral', 'idle', 3),
         ('sneak', 'sneak', 3),
         ('into_sneak', 'into_sneak', 3),
         ('chat', 'run', 3),
         ('into_idle', 'into_idle', 3)),
 'wmn': (('walk', 'walkHalloween3', 3), ('neutral', 'neutral2', 3)),
 'mn': (('walk', 'walk', 3),
        ('run', 'run', 3),
        ('neutral', 'wait', 3),
        ('left-point-start', 'start-Lpoint', 3.5),
        ('left-point', 'Lpoint', 3.5),
        ('right-point-start', 'start-Rpoint', 3.5),
        ('right-point', 'Rpoint', 3.5),
        ('up', 'up', 4),
        ('down', 'down', 4),
        ('left', 'left', 4),
        ('right', 'right', 4)),
 'g': (('walk', 'Walk', 6), ('run', 'Run', 6), ('neutral', 'Wait', 6)),
 'sg': (('walk', 'walkStrut2', 6), ('neutral', 'neutral', 6)),
 'd': (('walk', 'walk', 6),
       ('trans', 'transition', 6),
       ('neutral', 'neutral', 6),
       ('trans-back', 'transBack', 6)),
 'fd': (('walk', 'walk', 6), ('neutral', 'idle', 6)),
 'dw': (('wheel', 'wheel', 6), ('neutral', 'wheel', 6)),
 'p': (('walk', 'walk', 6),
       ('sit', 'sit', 6),
       ('neutral', 'neutral', 6),
       ('stand', 'stand', 6)),
 'wp': (('walk', 'walk', 6),
        ('sit', 'sitStart', 6),
        ('neutral', 'sitLoop', 6),
        ('stand', 'sitStop', 6)),
 'cl': (),
 'dd': (('walk', 'walk', 4), ('neutral', 'idle', 4)),
 'shdd': (('walk', 'walk', 4), ('neutral', 'idle', 4)),
 'ch': (('walk', 'walk', 6), ('neutral', 'idle', 6)),
 'pch': (('walk', 'walk', 6), ('neutral', 'idle', 6)),
 'da': (('walk', 'walk', 6), ('neutral', 'idle', 6)),
 'jda': (('walk', 'walk', 6), ('neutral', 'idle', 6))}
ModelDict = {'mk': 'phase_3/models/char/mickey-',
 'vmk': 'phase_3.5/models/char/tt_a_chr_csc_mickey_vampire_',
 'mn': 'phase_3/models/char/minnie-',
 'wmn': 'phase_3.5/models/char/tt_a_chr_csc_witchMinnie_',
 'g': 'phase_6/models/char/TT_G',
 'sg': 'phase_6/models/char/tt_a_chr_csc_goofyCostume_',
 'd': 'phase_6/models/char/DL_donald-',
 'fd': 'phase_6/models/char/tt_a_chr_csc_donaldCostume_',
 'dw': 'phase_6/models/char/donald-wheel-',
 'p': 'phase_6/models/char/pluto-',
 'wp': 'phase_6/models/char/tt_a_chr_csc_plutoCostume_',
 'cl': 'phase_5.5/models/estate/Clara_pose2-',
 'dd': 'phase_4/models/char/daisyduck_',
 'shdd': 'phase_4/models/char/tt_a_chr_csc_daisyCostume_',
 'ch': 'phase_6/models/char/chip_',
 'pch': 'phase_6/models/char/tt_a_chr_csc_chipCostume_',
 'da': 'phase_6/models/char/dale_',
 'jda': 'phase_6/models/char/tt_a_chr_csc_daleCostume_'}
LODModelDict = {'mk': [1200, 800, 400],
 'vmk': [1200, 800, 400],
 'wmn': [1200, 800, 400],
 'mn': [1200, 800, 400],
 'g': [1500, 1000, 500],
 'sg': [1200, 800, 400],
 'd': [1000, 500, 250],
 'fd': ['default'],
 'dw': [1000],
 'p': [1000, 500, 300],
 'wp': [1200, 800, 400],
 'cl': [],
 'dd': [1600, 800, 400],
 'shdd': ['default'],
 'ch': [1000, 500, 250],
 'pch': ['default'],
 'da': [1000, 500, 250],
 'jda': ['default']}

class Char(Avatar.Avatar):
    notify = DirectNotifyGlobal.directNotify.newCategory('Char')

    def __init__(self):
        try:
            self.Char_initialized
        except:
            self.Char_initialized = 1
            Avatar.Avatar.__init__(self)
            self.setPickable(0)
            self.setPlayerType(NametagGroup.CCNonPlayer)
            self.dialogueArray = []
            self.chatterArray = [[], [], []]

    def delete(self):
        try:
            self.Char_deleted
        except:
            self.Char_deleted = 1
            self.unloadDialogue()
            Avatar.Avatar.delete(self)

    def updateCharDNA(self, newDNA):
        if newDNA.name != self.style.name:
            self.swapCharModel(newDNA)

    def setDNAString(self, dnaString):
        newDNA = CharDNA.CharDNA()
        newDNA.makeFromNetString(dnaString)
        self.setDNA(newDNA)

    def setDNA(self, dna):
        if self.style:
            self.updateCharDNA(dna)
        else:
            self.style = dna
            self.generateChar()
            self.initializeDropShadow()
            self.initializeNametag3d()
            self.nametag3d.setBin('fixed', 0)
            if self._name == 'chip' or self._name == 'dale' or self._name == 'police_chip' or self._name == 'jailbird_dale':
                self.find('**/drop-shadow').setScale(0.33)

    def setLODs(self):
        self.setLODNode()
        levelOneIn = base.config.GetInt('lod1-in', 50)
        levelOneOut = base.config.GetInt('lod1-out', 1)
        levelTwoIn = base.config.GetInt('lod2-in', 100)
        levelTwoOut = base.config.GetInt('lod2-out', 50)
        levelThreeIn = base.config.GetInt('lod3-in', 280)
        levelThreeOut = base.config.GetInt('lod3-out', 100)
        self.addLOD(LODModelDict[self.style.name][0], levelOneIn, levelOneOut)
        self.addLOD(LODModelDict[self.style.name][1], levelTwoIn, levelTwoOut)
        self.addLOD(LODModelDict[self.style.name][2], levelThreeIn, levelThreeOut)

    def generateChar(self):
        dna = self.style
        self._name = dna.getCharName()
        self.geoEyes = 0
        if len(LODModelDict[dna.name]) > 1:
            self.setLODs()
        filePrefix = ModelDict[dna.name]
        if self._name == 'mickey':
            height = 3.0
        elif self._name == 'vampire_mickey':
            height = 3.0
        elif self._name == 'minnie':
            height = 3.0
        elif self._name == 'witch_minnie':
            height = 3.0
        elif self._name == 'goofy':
            height = 4.8
        elif self._name == 'super_goofy':
            height = 4.8
        elif self._name == 'donald' or self._name == 'donald-wheel' or self._name == 'franken_donald':
            height = 4.5
        elif self._name == 'daisy' or self._name == 'sockHop_daisy':
            height = 4.5
        elif self._name == 'pluto':
            height = 3.0
        elif self._name == 'western_pluto':
            height = 4.5
        elif self._name == 'clarabelle':
            height = 3.0
        elif self._name == 'chip':
            height = 2.0
        elif self._name == 'dale':
            height = 2.0
        elif self._name == 'police_chip':
            height = 2.0
        elif self._name == 'jailbird_dale':
            height = 2.0
        self.lodStrings = []
        for lod in LODModelDict[self.style.name]:
            self.lodStrings.append(str(lod))

        if self.lodStrings:
            for lodStr in self.lodStrings:
                if len(self.lodStrings) > 1:
                    lodName = lodStr
                else:
                    lodName = 'lodRoot'
                if self._name == 'goofy':
                    self.loadModel(filePrefix + '-' + lodStr, lodName=lodName)
                else:
                    self.loadModel(filePrefix + lodStr, lodName=lodName)

        else:
            self.loadModel(filePrefix)
        animDict = {}
        animList = AnimDict[self.style.name]
        for anim in animList:
            animFilePrefix = filePrefix[:6] + str(anim[2]) + filePrefix[7:]
            animDict[anim[0]] = animFilePrefix + anim[1]

        for lodStr in self.lodStrings:
            if len(self.lodStrings) > 1:
                lodName = lodStr
            else:
                lodName = 'lodRoot'
            self.loadAnims(animDict, lodName=lodName)

        self.setHeight(height)
        self.loadDialogue(dna.name)
        self.ears = []
        if self._name == 'mickey' or self._name == 'vampire_mickey' or self._name == 'minnie':
            for bundle in list(self.getPartBundleDict().values()):
                bundle = bundle['modelRoot'].getBundle()
                earNull = bundle.findChild('sphere3')
                if not earNull:
                    earNull = bundle.findChild('*sphere3')
                earNull.clearNetTransforms()

            for bundle in list(self.getPartBundleDict().values()):
                charNodepath = bundle['modelRoot'].partBundleNP
                bundle = bundle['modelRoot'].getBundle()
                earNull = bundle.findChild('sphere3')
                if not earNull:
                    earNull = bundle.findChild('*sphere3')
                ears = charNodepath.find('**/sphere3')
                if ears.isEmpty():
                    ears = charNodepath.find('**/*sphere3')
                ears.clearEffect(CharacterJointEffect.getClassType())
                earRoot = charNodepath.attachNewNode('earRoot')
                earPitch = earRoot.attachNewNode('earPitch')
                earPitch.setP(40.0)
                ears.reparentTo(earPitch)
                earNull.addNetTransform(earRoot.node())
                ears.clearMat()
                ears.node().setPreserveTransform(ModelNode.PTNone)
                ears.setP(-40.0)
                ears.flattenMedium()
                self.ears.append(ears)
                ears.setBillboardAxis()

        self.eyes = None
        self.lpupil = None
        self.rpupil = None
        self.eyesOpen = None
        self.eyesClosed = None
        if self._name == 'mickey' or self._name == 'minnie':
            self.eyesOpen = loader.loadTexture('phase_3/maps/eyes1.jpg', 'phase_3/maps/eyes1_a.rgb')
            self.eyesClosed = loader.loadTexture('phase_3/maps/mickey_eyes_closed.jpg', 'phase_3/maps/mickey_eyes_closed_a.rgb')
            self.eyes = self.find('**/1200/**/eyes')
            self.eyes.setBin('transparent', 0)
            self.lpupil = self.find('**/1200/**/joint_pupilL')
            self.rpupil = self.find('**/1200/**/joint_pupilR')
            for lodName in self.getLODNames():
                self.drawInFront('joint_pupil?', 'eyes*', -3, lodName=lodName)

        elif (self._name == 'witch_minnie' or
              self._name == 'vampire_mickey' or
              self._name == 'super_goofy' or
              self._name == 'western_pluto' or
              self._name == 'police_chip' or
              self._name == 'jailbird_dale' or
              self._name == 'franken_donald' or
              self._name == 'sockHop_daisy'):
            self.geoEyes = 1
            self.eyeOpenList = []
            self.eyeCloseList = []
            if self.find('**/1200/**/eyesOpen').isEmpty():
                self.eyeCloseList.append(self.find('**/eyesClosed'))
                self.eyeOpenList.append(self.find('**/eyesOpen'))
            else:
                self.eyeCloseList.append(self.find('**/1200/**/eyesClosed'))
                self.eyeOpenList.append(self.find('**/1200/**/eyesOpen'))
            for part in self.eyeOpenList:
                part.show()

            for part in self.eyeCloseList:
                part.hide()

        elif self._name == 'pluto':
            self.eyesOpen = loader.loadTexture('phase_6/maps/plutoEyesOpen.jpg', 'phase_6/maps/plutoEyesOpen_a.rgb')
            self.eyesClosed = loader.loadTexture('phase_6/maps/plutoEyesClosed.jpg', 'phase_6/maps/plutoEyesClosed_a.rgb')
            self.eyes = self.find('**/1000/**/eyes')
            self.lpupil = self.find('**/1000/**/joint_pupilL')
            self.rpupil = self.find('**/1000/**/joint_pupilR')
            for lodName in self.getLODNames():
                self.drawInFront('joint_pupil?', 'eyes*', -3, lodName=lodName)

        elif self._name == 'daisy':
            self.geoEyes = 1
            self.eyeOpenList = []
            self.eyeCloseList = []
            self.eyeCloseList.append(self.find('**/1600/**/eyesclose'))
            self.eyeCloseList.append(self.find('**/800/**/eyesclose'))
            self.eyeOpenList.append(self.find('**/1600/**/eyesclose'))
            self.eyeOpenList.append(self.find('**/800/**/eyesclose'))
            self.eyeOpenList.append(self.find('**/1600/**/eyespupil'))
            self.eyeOpenList.append(self.find('**/800/**/eyespupil'))
            self.eyeOpenList.append(self.find('**/1600/**/eyesopen'))
            self.eyeOpenList.append(self.find('**/800/**/eyesopen'))
            for part in self.eyeOpenList:
                part.show()

            for part in self.eyeCloseList:
                part.hide()

        elif self._name == 'donald-wheel':
            self.eyes = self.find('**/eyes')
            self.lpupil = self.find('**/joint_pupilL')
            self.rpupil = self.find('**/joint_pupilR')
            self.drawInFront('joint_pupil?', 'eyes*', -3)
        elif self._name == 'chip' or self._name == 'dale':
            self.eyesOpen = loader.loadTexture('phase_6/maps/dale_eye1.jpg', 'phase_6/maps/dale_eye1_a.rgb')
            self.eyesClosed = loader.loadTexture('phase_6/maps/chip_dale_eye1_blink.jpg', 'phase_6/maps/chip_dale_eye1_blink_a.rgb')
            self.eyes = self.find('**/eyes')
            self.lpupil = self.find('**/pupil_left')
            self.rpupil = self.find('**/pupil_right')
            self.find('**/blink').hide()
        if self.lpupil != None:
            self.lpupil.adjustAllPriorities(1)
            self.rpupil.adjustAllPriorities(1)
        if self.eyesOpen:
            self.eyesOpen.setMinfilter(Texture.FTLinear)
            self.eyesOpen.setMagfilter(Texture.FTLinear)
        if self.eyesClosed:
            self.eyesClosed.setMinfilter(Texture.FTLinear)
            self.eyesClosed.setMagfilter(Texture.FTLinear)
        if self._name == 'mickey':
            pupilParent = self.rpupil.getParent()
            pupilOffsetNode = pupilParent.attachNewNode('pupilOffsetNode')
            pupilOffsetNode.setPos(0, 0.025, 0)
            self.rpupil.reparentTo(pupilOffsetNode)
        self.__blinkName = 'blink-' + self._name
        return

    def swapCharModel(self, charStyle):
        for lodStr in self.lodStrings:
            if len(self.lodStrings) > 1:
                lodName = lodStr
            else:
                lodName = 'lodRoot'
            self.removePart('modelRoot', lodName=lodName)

        self.setStyle(charStyle)
        self.generateChar()

    def getDialogue(self, type, length):
        sfxIndex = None
        if type == 'statementA' or type == 'statementB':
            if length == 1:
                sfxIndex = 0
            elif length == 2:
                sfxIndex = 1
            elif length >= 3:
                sfxIndex = 2
        elif type == 'question':
            sfxIndex = 3
        elif type == 'exclamation':
            sfxIndex = 4
        elif type == 'special':
            sfxIndex = 5
        else:
            self.notify.error('unrecognized dialogue type: ', type)
        if sfxIndex != None and sfxIndex < len(self.dialogueArray) and self.dialogueArray[sfxIndex] != None:
            return self.dialogueArray[sfxIndex]
        else:
            return
        return

    def playDialogue(self, type, length, delay = None):
        dialogue = self.getDialogue(type, length)
        base.playSfx(dialogue)

    def getChatterDialogue(self, category, msg):
        try:
            return self.chatterArray[category][msg]
        except IndexError:
            return None

        return None

    def getShadowJoint(self):
        return self.getGeomNode()

    def getNametagJoints(self):
        return []

    def loadChatterDialogue(self, name, audioIndexArray, loadPath, language):
        chatterTypes = ['greetings', 'comments', 'goodbyes']
        for categoryIndex in range(len(audioIndexArray)):
            chatterType = chatterTypes[categoryIndex]
            for fileIndex in audioIndexArray[categoryIndex]:
                if fileIndex:
                    self.chatterArray[categoryIndex].append(base.loader.loadSfx('%s/CC_%s_chatter_%s%02d.ogg' % (loadPath,
                     name,
                     chatterType,
                     fileIndex)))
                else:
                    self.chatterArray[categoryIndex].append(None)

        return

    def loadDialogue(self, char):
        if self.dialogueArray:
            self.notify.warning('loadDialogue() called twice.')
        self.unloadDialogue()
        language = base.config.GetString('language', 'english')
        if char == 'mk':
            dialogueFile = base.loader.loadSfx('phase_3/audio/dial/mickey.ogg')
            for i in range(0, 6):
                self.dialogueArray.append(dialogueFile)

            if language == 'japanese':
                chatterIndexArray = ([1, 2], [1,
                  2,
                  3,
                  4], [1,
                  2,
                  3,
                  4,
                  5])
                self.loadChatterDialogue('mickey', chatterIndexArray, 'phase_3/audio/dial', language)
        elif char == 'vmk':
            dialogueFile = base.loader.loadSfx('phase_3/audio/dial/mickey.ogg')
            for i in range(0, 6):
                self.dialogueArray.append(dialogueFile)

            if language == 'japanese':
                chatterIndexArray = ([1, 2], [1,
                  2,
                  3,
                  4], [1,
                  2,
                  3,
                  4,
                  5])
                self.loadChatterDialogue('mickey', chatterIndexArray, 'phase_3/audio/dial', language)
        elif char == 'mn' or char == 'wmn':
            dialogueFile = base.loader.loadSfx('phase_3/audio/dial/minnie.ogg')
            for i in range(0, 6):
                self.dialogueArray.append(dialogueFile)

            if language == 'japanese':
                chatterIndexArray = ([1, 2], [1,
                  2,
                  3,
                  4,
                  5,
                  6,
                  7,
                  8,
                  9,
                  10,
                  11,
                  12,
                  13,
                  14,
                  15,
                  16,
                  17], [1, 2, 3])
                self.loadChatterDialogue('minnie', chatterIndexArray, 'phase_3/audio/dial', language)
        elif char == 'dd' or char == 'shdd':
            dialogueFile = base.loader.loadSfx('phase_4/audio/dial/daisy.ogg')
            for i in range(0, 6):
                self.dialogueArray.append(dialogueFile)

            if language == 'japanese':
                chatterIndexArray = ([1, 2, 3], [1,
                  2,
                  3,
                  4,
                  5,
                  6,
                  7,
                  8,
                  9,
                  10,
                  11,
                  12], [1,
                  2,
                  3,
                  4])
                self.loadChatterDialogue('daisy', chatterIndexArray, 'phase_8/audio/dial', language)
        elif char == 'g' or char == 'sg':
            dialogueFile = base.loader.loadSfx('phase_6/audio/dial/goofy.ogg')
            for i in range(0, 6):
                self.dialogueArray.append(dialogueFile)

            if language == 'japanese':
                chatterIndexArray = ([1, 2, 3], [1,
                  2,
                  3,
                  4,
                  5,
                  6,
                  7,
                  8,
                  9,
                  10,
                  11,
                  12], [1,
                  2,
                  3,
                  4])
                self.loadChatterDialogue('goofy', chatterIndexArray, 'phase_6/audio/dial', language)
        elif char == 'd' or char == 'dw' or char == 'fd':
            dialogueFile = base.loader.loadSfx('phase_6/audio/dial/donald.ogg')
            for i in range(0, 6):
                self.dialogueArray.append(dialogueFile)

            if char == 'd':
                if language == 'japanese':
                    chatterIndexArray = ([1, 2], [1,
                      2,
                      3,
                      4,
                      5,
                      6,
                      7,
                      8,
                      9,
                      10,
                      11], [1,
                      2,
                      3,
                      4])
                    self.loadChatterDialogue('donald', chatterIndexArray, 'phase_6/audio/dial', language)
        elif char == 'p' or char == 'wp':
            dialogueFile = base.loader.loadSfx('phase_3.5/audio/dial/AV_dog_med.ogg')
            for i in range(0, 6):
                self.dialogueArray.append(dialogueFile)

        elif char == 'cl':
            dialogueFile = base.loader.loadSfx('phase_3.5/audio/dial/AV_dog_med.ogg')
            for i in range(0, 6):
                self.dialogueArray.append(dialogueFile)

        elif char == 'ch':
            dialogueFile = base.loader.loadSfx('phase_6/audio/dial/chip.ogg')
            for i in range(0, 6):
                self.dialogueArray.append(dialogueFile)

        elif char == 'da':
            dialogueFile = base.loader.loadSfx('phase_6/audio/dial/dale.ogg')
            for i in range(0, 6):
                self.dialogueArray.append(dialogueFile)

        elif char == 'pch':
            dialogueFile = base.loader.loadSfx('phase_6/audio/dial/chip.ogg')
            for i in range(0, 6):
                self.dialogueArray.append(dialogueFile)

        elif char == 'jda':
            dialogueFile = base.loader.loadSfx('phase_6/audio/dial/dale.ogg')
            for i in range(0, 6):
                self.dialogueArray.append(dialogueFile)

        else:
            self.notify.error('unknown character %s' % char)

    def unloadDialogue(self):
        self.dialogueArray = []
        self.chatterArray = [[], [], []]

    def __blinkOpenEyes(self, task):
        self.openEyes()
        r = random.random()
        if r < 0.1:
            t = 0.2
        else:
            t = r * 4.0 + 1.0
        taskMgr.doMethodLater(t, self.__blinkCloseEyes, self.__blinkName)
        return Task.done

    def __blinkCloseEyes(self, task):
        self.closeEyes()
        taskMgr.doMethodLater(0.125, self.__blinkOpenEyes, self.__blinkName)
        return Task.done

    def openEyes(self):
        if self.geoEyes:
            for part in self.eyeOpenList:
                part.show()

            for part in self.eyeCloseList:
                part.hide()

        else:
            if self.eyes:
                self.eyes.setTexture(self.eyesOpen, 1)
            self.lpupil.show()
            self.rpupil.show()

    def closeEyes(self):
        if self.geoEyes:
            for part in self.eyeOpenList:
                part.hide()

            for part in self.eyeCloseList:
                part.show()

        else:
            if self.eyes:
                self.eyes.setTexture(self.eyesClosed, 1)
            self.lpupil.hide()
            self.rpupil.hide()

    def startBlink(self):
        if self.eyesOpen or self.geoEyes:
            taskMgr.remove(self.__blinkName)
            taskMgr.doMethodLater(random.random() * 4 + 1, self.__blinkCloseEyes, self.__blinkName)

    def stopBlink(self):
        if self.eyesOpen or self.geoEyes:
            taskMgr.remove(self.__blinkName)
            self.openEyes()

    def startEarTask(self):
        pass

    def stopEarTask(self):
        pass

    def uniqueName(self, idString):
        return idString + '-' + str(self.this)
