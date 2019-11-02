from direct.showbase.DirectObject import DirectObject
from toontown.toonbase.ToontownGlobals import *
from direct.directnotify import DirectNotifyGlobal
from direct.interval.IntervalGlobal import *
from direct.actor import Actor
import random
import DivingGameGlobals

class DivingFishSpawn(DirectObject):
    RADIUS = 0.7

    def __init__(self, spawnId, direction, position, cHandler):
        loadBase = 'phase_4/models/char/'
        self.entryNode = render.attachNewNode('entryNode')
        self.direction = direction
        self.fishArray = {}
        self.inactiveArray = []
        self.fishActive = 0
        self.position = position
        self.spawnId = spawnId
        self.id = -1

    def getUniqueNumber(self):
        self.id += 1
        return self.id

    def createFish(self, fishcode):
        loadBase = 'phase_4/models/char/'
        if fishcode is 0:
            fish = Actor.Actor('phase_4/models/char/clownFish-zero.bam', {'anim': loadBase + 'clownFish-swim.bam'})
            fish.name = 'clown'
        elif fishcode is 1:
            fish = Actor.Actor('phase_4/models/char/PBJfish-zero.bam', {'anim': 'phase_4/models/char/PBJfish-swim.bam'})
            fish.name = 'pbj'
        elif fishcode is 2:
            fish = Actor.Actor('phase_4/models/char/BearAcuda-zero.bam', {'anim': 'phase_4/models/char/BearAcuda-swim.bam'})
            fish.name = 'bear'
        elif fishcode is 3:
            fish = Actor.Actor(loadBase + 'balloonFish-zero.bam', {'anim': loadBase + 'balloonFish-swim.bam'})
            fish.name = 'balloon'
        elif fishcode is 4:
            fish = Actor.Actor(loadBase + 'nurseShark-zero.bam', {'anim': loadBase + 'nurseShark-swim.bam'})
            fish.name = 'nurse'
        elif fishcode is 5:
            fish = Actor.Actor(loadBase + 'pianoTuna-zero.bam', {'anim': loadBase + 'pianoTuna-swim.bam'})
            fish.name = 'piano'
        else:
            return
        fish.active = 1
        fish.direction = self.direction
        idCode = self.getUniqueNumber()
        fish.code = str(self.spawnId) + str(idCode)
        self.fishArray[idCode] = fish
        fish.reparentTo(render)
        fish.setScale(1)
        fish.moveLerp = Sequence()
        if fish.name == 'clown':
            fish.setH(90 * self.direction)
            fish.loop('anim')
            cSphere = CollisionSphere(0.0, 0.0, 0.0, 1.2)
        elif fish.name == 'pbj':
            fish.setH(15 * self.direction)
            fish.loop('anim')
            cSphere = CollisionSphere(0.0, 0.0, 0.0, 1)
        elif fish.name == 'balloon':
            fish.setH(0)
            fish.loop('anim', fromFrame=0, toFrame=94)
            fish.setScale(2)
            cSphere = CollisionSphere(0.0, 0.0, 0.0, 0.2)
        elif fish.name == 'bear':
            fish.setH(90 * self.direction)
            cSphere = CollisionSphere(0.0, -1.0, 3.5, 3.0)
            fish.loop('anim')
            fish.setScale(0.4, 1.7, 1.7)
        elif fish.name == 'nurse':
            fish.setH(90 * self.direction)
            cSphere = CollisionSphere(0.0, -1.0, 0.0, 1)
            fish.setScale(0.5, 1.7, 1.7)
            fish.loop('anim')
        elif fish.name == 'mackerel':
            fish.setH(90 * self.direction)
            cSphere = CollisionSphere(0.0, 0.0, 0.0, 1.5)
            fish.loop('anim', fromFrame=36, toFrame=80)
        elif fish.name == 'piano':
            fish.loop('anim')
            fish.setScale(1.4)
            cSphere = CollisionSphere(0, 0, 0, 1)
            fishSoundName = 'Piano_Tuna.mp3'
            if self.direction is -1:
                fish.setH(0)
            else:
                fish.setH(180)
        cSphere.setTangible(0)
        fish.offset = 0
        cSphereNode = CollisionNode('fc' + str(fish.code))
        cSphereNode.addSolid(cSphere)
        cSphereNode.setFromCollideMask(BitMask32.allOff())
        cSphereNode.setIntoCollideMask(DivingGameGlobals.CollideMask)
        cSphereNodePath = fish.attachNewNode(cSphereNode)
        self.accept('into-' + 'fc' + str(fish.code), self.__handleFishCollide)
        fish.moveloop = Sequence(Wait(4), LerpScaleInterval(fish, startScale=1, scale=3, duration=1), Wait(1.5), LerpScaleInterval(fish, startScale=3, scale=1, duration=0.5))
        return fish

    def destroy(self):
        self.ignoreAll()
        for fish in self.fishArray.values():
            fish.moveLerp.pause()
            fish.specialLerp.finish()
            if hasattr(fish, 'sound'):
                fish.sound.stop()
                fish.sound = None
            fish.moveLerp = None
            fish.specialLerp = None
            fish.removeNode()
            del fish

        return

    def __handleFishCollide(self, collEntry):
        messenger.send('FishHit', [collEntry])
