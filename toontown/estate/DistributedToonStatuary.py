from toontown.estate import DistributedStatuary
from toontown.estate import DistributedLawnDecor
from direct.directnotify import DirectNotifyGlobal
from direct.showbase.ShowBase import *
from pandac.PandaModules import *
from toontown.toon import Toon
from toontown.toon import ToonDNA
from . import GardenGlobals
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals
from pandac.PandaModules import NodePath
from pandac.PandaModules import Point3

def dnaCodeFromToonDNA(dna):

    def findItemNumInList(wantItem, wantList):
        i = 0
        for item in wantList:
            if item == wantItem:
                break
            i += 1

        return i

    if dna.gender == 'f':
        genderTypeNum = 0
    else:
        genderTypeNum = 1
    legTypeNum = findItemNumInList(dna.legs, ToonDNA.toonLegTypes) << 1
    torsoTypeNum = findItemNumInList(dna.torso, ToonDNA.toonTorsoTypes) << 3
    headTypeNum = findItemNumInList(dna.head, ToonDNA.toonHeadTypes) << 7
    return headTypeNum | torsoTypeNum | legTypeNum | genderTypeNum


class DistributedToonStatuary(DistributedStatuary.DistributedStatuary):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedToonStatuary')

    def __init__(self, cr):
        self.notify.debug('constructing DistributedToonStatuary')
        DistributedStatuary.DistributedStatuary.__init__(self, cr)
        self.toon = None
        return

    def loadModel(self):
        DistributedStatuary.DistributedStatuary.loadModel(self)
        self.model.setScale(self.worldScale * 1.5, self.worldScale * 1.5, self.worldScale)
        self.getToonPropertiesFromOptional()
        dna = ToonDNA.ToonDNA()
        dna.newToonFromProperties(self.headType, self.torsoType, self.legType, self.gender, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        self.setupStoneToon(dna)
        self.poseToonFromTypeIndex(self.typeIndex)
        self.toon.reparentTo(self.model)

    def delete(self):
        self.deleteToon()
        DistributedStatuary.DistributedStatuary.delete(self)

    def setupStoneToon(self, dna):
        self.toon = Toon.Toon()
        self.toon.setPos(0, 0, 0)
        self.toon.setDNA(dna)
        self.toon.initializeBodyCollisions('toonStatue')
        self.toon.stopBlink()
        self.toon.stopLookAround()
        self.gender = self.toon.style.gender
        self.speciesType = self.toon.style.getAnimal()
        self.headType = self.toon.style.head
        self.removeTextures()
        self.setStoneTexture()
        self.toon.dropShadow.hide()
        self.toon.setZ(70)
        self.toon.setScale(20 / 1.5, 20 / 1.5, 20)

    def deleteToon(self):
        self.notify.debug('entering deleteToon')
        self.toon.delete()
        self.toon = None
        return

    def copyLocalAvatarToon(self):
        self.toon = Toon.Toon()
        self.toon.reparentTo(render)
        self.toon.setDNA(base.localAvatar.style)
        self.toon.setPos(base.localAvatar, 0, 0, 0)
        self.toon.pose('victory', 30)
        self.toon.setH(180)
        self.speciesType = self.toon.style.getAnimal()
        self.gender = self.toon.style.gender

    def setupCollision(self):
        DistributedStatuary.DistributedStatuary.setupCollision(self)
        self.colSphereNode.setScale(self.colSphereNode.getScale() * 1.5)

    def setupShadow(self):
        pass

    def removeTextures(self):
        for node in self.toon.findAllMatches('**/*'):
            node.setState(RenderState.makeEmpty())

        desatShirtTex = loader.loadTexture('phase_3/maps/desat_shirt_1.jpg')
        desatSleeveTex = loader.loadTexture('phase_3/maps/desat_sleeve_1.jpg')
        desatShortsTex = loader.loadTexture('phase_3/maps/desat_shorts_1.jpg')
        desatSkirtTex = loader.loadTexture('phase_3/maps/desat_skirt_1.jpg')
        if self.toon.hasLOD():
            for lodName in self.toon.getLODNames():
                torso = self.toon.getPart('torso', lodName)
                torsoTop = torso.find('**/torso-top')
                if torsoTop:
                    torsoTop.setTexture(desatShirtTex, 1)
                sleeves = torso.find('**/sleeves')
                if sleeves:
                    sleeves.setTexture(desatSleeveTex, 1)
                bottoms = torso.findAllMatches('**/torso-bot*')
                for bottomNum in range(0, bottoms.getNumPaths()):
                    bottom = bottoms.getPath(bottomNum)
                    if bottom:
                        if self.toon.style.torso[1] == 's':
                            bottom.setTexture(desatShortsTex, 1)
                        else:
                            bottom.setTexture(desatSkirtTex, 1)

    def setStoneTexture(self):
        gray = VBase4(1.6, 1.6, 1.6, 1)
        self.toon.setColor(gray, 10)
        stoneTex = loader.loadTexture('phase_5.5/maps/smoothwall_1.jpg')
        ts = TextureStage('ts')
        ts.setPriority(1)
        self.toon.setTexture(ts, stoneTex)
        tsDetail = TextureStage('tsDetail')
        tsDetail.setPriority(2)
        tsDetail.setSort(10)
        tsDetail.setCombineRgb(tsDetail.CMInterpolate, tsDetail.CSTexture, tsDetail.COSrcColor, tsDetail.CSPrevious, tsDetail.COSrcColor, tsDetail.CSConstant, tsDetail.COSrcColor)
        tsDetail.setColor(VBase4(0.5, 0.5, 0.5, 1))
        if self.toon.hasLOD():
            for lodName in self.toon.getLODNames():
                head = self.toon.getPart('head', lodName)
                eyes = head.find('**/eye*')
                if not eyes.isEmpty():
                    eyes.setColor(Vec4(1.4, 1.4, 1.4, 0.3), 10)
                ears = head.find('**/ears*')
                animal = self.toon.style.getAnimal()
                if animal != 'dog':
                    muzzle = head.find('**/muzzle*neutral')
                else:
                    muzzle = head.find('**/muzzle*')
                if ears != ears.notFound():
                    if self.speciesType == 'cat':
                        ears.setTexture(tsDetail, stoneTex)
                    elif self.speciesType == 'horse':
                        pass
                    elif self.speciesType == 'rabbit':
                        ears.setTexture(tsDetail, stoneTex)
                    elif self.speciesType == 'monkey':
                        ears.setTexture(tsDetail, stoneTex)
                        ears.setColor(VBase4(0.6, 0.9, 1, 1), 10)
                if muzzle != muzzle.notFound():
                    muzzle.setTexture(tsDetail, stoneTex)
                if self.speciesType == 'dog':
                    nose = head.find('**/nose')
                    if nose != nose.notFound():
                        nose.setTexture(tsDetail, stoneTex)

        tsLashes = TextureStage('tsLashes')
        tsLashes.setPriority(2)
        tsLashes.setMode(tsLashes.MDecal)
        if self.gender == 'f':
            if self.toon.hasLOD():
                head = self.toon.getPart('head', '1000')
            else:
                head = self.toon.getPart('head', 'lodRoot')
            if self.headType[1] == 'l':
                openString = 'open-long'
                closedString = 'closed-long'
            else:
                openString = 'open-short'
                closedString = 'closed-short'
            lashesOpen = head.find('**/' + openString)
            lashesClosed = head.find('**/' + closedString)
            if lashesOpen != lashesOpen.notFound():
                lashesOpen.setTexture(tsLashes, stoneTex)
                lashesOpen.setColor(VBase4(1, 1, 1, 0.4), 10)
            if lashesClosed != lashesClosed.notFound():
                lashesClosed.setTexture(tsLashes, stoneTex)
                lashesClosed.setColor(VBase4(1, 1, 1, 0.4), 10)

    def setOptional(self, optional):
        self.optional = optional

    def getToonPropertiesFromOptional(self):
        genderTypeNum = self.optional & 1
        legTypeNum = (self.optional & 6) >> 1
        torsoTypeNum = (self.optional & 120) >> 3
        headTypeNum = (self.optional & 65408) >> 7
        if genderTypeNum == 0:
            self.gender = 'f'
        else:
            self.gender = 'm'
        if legTypeNum <= len(ToonDNA.toonLegTypes):
            self.legType = ToonDNA.toonLegTypes[legTypeNum]
        if torsoTypeNum <= len(ToonDNA.toonTorsoTypes):
            self.torsoType = ToonDNA.toonTorsoTypes[torsoTypeNum]
        if headTypeNum <= len(ToonDNA.toonHeadTypes):
            self.headType = ToonDNA.toonHeadTypes[headTypeNum]

    def poseToonFromTypeIndex(self, typeIndex):
        if typeIndex == 205:
            self.toon.pose('wave', 18)
        elif typeIndex == 206:
            self.toon.pose('victory', 116)
        elif typeIndex == 207:
            self.toon.pose('bored', 96)
        elif typeIndex == 208:
            self.toon.pose('think', 59)

    def poseToonFromSpecialsIndex(self, specialsIndex):
        if specialsIndex == 105:
            self.toon.pose('wave', 18)
        elif specialsIndex == 106:
            self.toon.pose('victory', 116)
        elif specialsIndex == 107:
            self.toon.pose('bored', 96)
        elif specialsIndex == 108:
            self.toon.pose('think', 59)
