from pandac.PandaModules import *
from direct.actor import Actor
from otp.avatar import Avatar
from toontown.toonbase import ToontownGlobals
from pandac.PandaModules import *
from toontown.toonbase import TTLocalizer
from . import GoonGlobals
from . import SuitDNA
import math
AnimDict = {'pg': (('walk', '-walk'), ('collapse', '-collapse'), ('recovery', '-recovery')),
 'sg': (('walk', '-walk'), ('collapse', '-collapse'), ('recovery', '-recovery'))}
ModelDict = {'pg': 'phase_9/models/char/Cog_Goonie',
 'sg': 'phase_9/models/char/Cog_Goonie'}

class Goon(Avatar.Avatar):

    def __init__(self, dnaName = None):
        try:
            self.Goon_initialized
        except:
            self.Goon_initialized = 1
            Avatar.Avatar.__init__(self)
            self.ignore('nametagAmbientLightChanged')
            self.hFov = 70
            self.attackRadius = 15
            self.strength = 15
            self.velocity = 4
            self.scale = 1.0
            if dnaName is not None:
                self.initGoon(dnaName)

        return

    def initGoon(self, dnaName):
        dna = SuitDNA.SuitDNA()
        dna.newGoon(dnaName)
        self.setDNA(dna)
        self.type = dnaName
        self.createHead()
        self.find('**/actorGeom').setH(180)

    def initializeBodyCollisions(self, collIdStr):
        Avatar.Avatar.initializeBodyCollisions(self, collIdStr)
        if not self.ghostMode:
            self.collNode.setCollideMask(self.collNode.getIntoCollideMask() | ToontownGlobals.PieBitmask)

    def delete(self):
        try:
            self.Goon_deleted
        except:
            self.Goon_deleted = 1
            filePrefix = ModelDict[self.style.name]
            loader.unloadModel(filePrefix + '-zero')
            animList = AnimDict[self.style.name]
            for anim in animList:
                loader.unloadModel(filePrefix + anim[1])

            Avatar.Avatar.delete(self)

        return None

    def setDNAString(self, dnaString):
        self.dna = SuitDNA.SuitDNA()
        self.dna.makeFromNetString(dnaString)
        self.setDNA(self.dna)

    def setDNA(self, dna):
        if self.style:
            pass
        else:
            self.style = dna
            self.generateGoon()
            self.initializeDropShadow()
            self.initializeNametag3d()

    def generateGoon(self):
        dna = self.style
        filePrefix = ModelDict[dna.name]
        self.loadModel(filePrefix + '-zero')
        animDict = {}
        animList = AnimDict[dna.name]
        for anim in animList:
            animDict[anim[0]] = filePrefix + anim[1]

        self.loadAnims(animDict)

    def getShadowJoint(self):
        return self.getGeomNode()

    def getNametagJoints(self):
        return []

    def createHead(self):
        self.headHeight = 3.0
        head = self.find('**/joint35')
        if head.isEmpty():
            head = self.find('**/joint40')
        self.hat = self.find('**/joint8')
        parentNode = head.getParent()
        self.head = parentNode.attachNewNode('headRotate')
        head.reparentTo(self.head)
        self.hat.reparentTo(self.head)
        if self.type == 'pg':
            self.hat.find('**/security_hat').hide()
        elif self.type == 'sg':
            self.hat.find('**/hard_hat').hide()
        else:
            self.hat.find('**/security_hat').hide()
            self.hat.find('**/hard_hat').hide()
        self.eye = self.find('**/eye')
        self.eye.setColorScale(1, 1, 1, 1)
        self.eye.setColor(1, 1, 0, 1)
        self.radar = None
        return

    def scaleRadar(self):
        if self.radar:
            self.radar.removeNode()
        self.radar = self.eye.attachNewNode('radar')
        model = loader.loadModel('phase_9/models/cogHQ/alphaCone2')
        beam = self.radar.attachNewNode('beam')
        transformNode = model.find('**/transform')
        transformNode.getChildren().reparentTo(beam)
        self.radar.setPos(0, -.5, 0.4)
        self.radar.setTransparency(1)
        self.radar.setDepthWrite(0)
        self.halfFov = self.hFov / 2.0
        fovRad = self.halfFov * math.pi / 180.0
        self.cosHalfFov = math.cos(fovRad)
        kw = math.tan(fovRad) * self.attackRadius / 10.5
        kl = math.sqrt(self.attackRadius * self.attackRadius + 9.0) / 25.0
        beam.setScale(kw / self.scale, kl / self.scale, kw / self.scale)
        beam.setHpr(0, self.halfFov, 0)
        p = self.radar.getRelativePoint(beam, Point3(0, -6, -1.8))
        self.radar.setSz(-3.5 / p[2])
        self.radar.flattenMedium()
        self.radar.setColor(1, 1, 1, 0.2)

    def colorHat(self):
        if self.type == 'pg':
            colorList = GoonGlobals.PG_COLORS
        elif self.type == 'sg':
            colorList = GoonGlobals.SG_COLORS
        else:
            return
        if self.strength >= 20:
            self.hat.setColorScale(colorList[0])
        elif self.strength >= 15:
            self.hat.setColorScale(colorList[1])
        else:
            self.hat.clearColorScale()
