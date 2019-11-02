from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from direct.distributed.ClockDelta import *
from direct.fsm import FSM
from direct.distributed import DistributedObject
from direct.showutil import Rope
from direct.showbase import PythonUtil
from direct.task import Task
from toontown.toonbase import ToontownGlobals
from otp.otpbase import OTPGlobals
from direct.actor import Actor
from toontown.suit import Suit
from toontown.suit import SuitDNA
import random
from toontown.battle import BattleProps
from toontown.toon import NPCToons

class DistributedLawbotChair(DistributedObject.DistributedObject, FSM.FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedLawbotChair')
    chairCushionSurface = Point3(0, -0.75, 2.25)
    landingPt = Point3(0, -1.5, 0)
    courtroomCeiling = 30

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        FSM.FSM.__init__(self, 'DistributedLawbotBossChair')
        self.boss = None
        self.index = None
        self.avId = 0
        self.modelPath = 'phase_11/models/lawbotHQ/JuryBoxChair'
        self.modelFindString = None
        self.nodePath = None
        self.ival = None
        self.origHpr = Point3(0, 0, 0)
        self.downTime = 0.5
        self.upTime = 5
        self.cogJuror = None
        self.propInSound = None
        self.propOutSound = None
        self.propTrack = None
        self.cogJurorTrack = None
        self.cogJurorSound = None
        self.toonJurorIndex = -1
        self.toonJuror = None
        return

    def announceGenerate(self):
        self.notify.debug('announceGenerate: %s' % self.doId)
        DistributedObject.DistributedObject.announceGenerate(self)
        self.name = 'Chair-%s' % self.doId
        self.loadModel(self.modelPath, self.modelFindString)
        self.randomGenerator = random.Random()
        self.randomGenerator.seed(self.doId)
        self.loadSounds()
        self.loadCogJuror()
        self.cogJuror.stash()
        origPos = self.computePos()
        self.nodePath.setPos(origPos)
        self.nodePath.setHpr(-90, 0, 0)
        chairParent = self.boss.getChairParent()
        self.nodePath.wrtReparentTo(chairParent)
        self.boss.chairs[self.index] = self

    def delete(self):
        DistributedObject.DistributedObject.delete(self)
        loader.unloadModel(self.modelPath)
        self.unloadSounds()
        self.nodePath.removeNode()

    def loadModel(self, modelPath, modelFindString = None):
        if self.nodePath == None:
            self.makeNodePath()
        else:
            self.chair.getChildren().detach()
        model = loader.loadModel(modelPath)
        if modelFindString != None:
            model = model.find('**/' + modelFindString)
        model.instanceTo(self.chair)
        trigger_chair = self.chair.find('**/trigger_chair')
        if not trigger_chair.isEmpty():
            trigger_chair.stash()
        collision_chair = self.chair.find('**/collision_chair')
        if not collision_chair.isEmpty():
            collision_chair.stash()
        shadow = self.chair.find('**/shadow')
        if not shadow.isEmpty():
            pass
        self.scale = 0.5
        self.chair.setScale(self.scale)
        self.attachColSphere()
        return

    def loadSounds(self):
        if self.propInSound == None:
            self.propInSound = base.loadSfx('phase_5/audio/sfx/ENC_propeller_in.mp3')
        if self.propOutSound == None:
            self.propOutSound = base.loadSfx('phase_5/audio/sfx/ENC_propeller_out.mp3')
        if self.cogJurorSound == None:
            self.cogJurorSound = base.loadSfx('phase_11/audio/sfx/LB_cog_jury.mp3')
        return

    def unloadSounds(self):
        if self.propInSound:
            del self.propInSound
            self.propInSound = None
        if self.propOutSound:
            del self.propOutSound
            self.propOutSound = None
        if self.cogJurorSound:
            del self.cogJurorSound
            self.cogJurorSound = None
        return

    def loadCogJuror(self):
        self.cleanupCogJuror()
        self.cogJuror = Suit.Suit()
        level = self.randomGenerator.randrange(len(SuitDNA.suitsPerLevel))
        self.cogJuror.dna = SuitDNA.SuitDNA()
        self.cogJuror.dna.newSuitRandom(level=level, dept='l')
        self.cogJuror.setDNA(self.cogJuror.dna)
        self.cogJuror.pose('landing', 0)
        self.cogJuror.reparentTo(self.nodePath)
        self.cogJuror.prop = None
        if self.cogJuror.prop == None:
            self.cogJuror.prop = BattleProps.globalPropPool.getProp('propeller')
        head = self.cogJuror.find('**/joint_head')
        self.cogJuror.prop.reparentTo(head)
        self.propTrack = Sequence(ActorInterval(self.cogJuror.prop, 'propeller', startFrame=8, endFrame=25))
        return

    def attachColSphere(self):
        chairTop = self.nodePath.find('**/top*')
        chairHandle = self.nodePath.find('**/handle*')
        collNode = CollisionNode(self.uniqueName('headSphere'))
        topBounds = self.chair.getBounds()
        center = topBounds.getCenter()
        radius = topBounds.getRadius()
        radius *= 0.65
        adjustedZ = center[2]
        adjustedZ += 0.6
        sphere1 = CollisionSphere(center[0], center[1], adjustedZ, radius)
        sphere1.setTangible(1)
        collNode.addSolid(sphere1)
        collNode.setName('Chair-%s' % self.index)
        self.collNodePath = self.nodePath.attachNewNode(collNode)

    def makeNodePath(self):
        self.nodePath = Actor.Actor()
        self.chair = self.nodePath.attachNewNode('myChair')

    def disable(self):
        DistributedObject.DistributedObject.disable(self)
        self.nodePath.detachNode()
        if self.ival:
            self.ival.finish()
            self.ival = None
        self.ignoreAll()
        del self.boss.chairs[self.index]
        self.cleanup()
        if self.propTrack:
            self.propTrack.finish()
            self.propTrack = None
        if self.cogJurorTrack:
            self.cogJurorTrack.finish()
            self.cogJurorTrack = None
        self.cleanupCogJuror()
        self.cleanupToonJuror()
        return

    def stopCogsFlying(self):
        if self.ival:
            self.ival.finish()
            self.ival = None
        if self.propTrack:
            self.propTrack.finish()
            self.propTrack = None
        if self.cogJurorTrack:
            self.cogJurorTrack.finish()
            self.cogJurorTrack = None
        return

    def cleanupCogJuror(self):
        if self.cogJuror:
            self.cogJuror.detachNode()
            self.cogJuror.delete()
            del self.cogJuror
            self.cogJuror = None
        return

    def cleanupToonJuror(self):
        if self.toonJuror:
            self.toonJuror.detachNode()
            self.toonJuror.delete()
            del self.toonJuror
            self.toonJuror = None
        return

    def cleanup(self):
        self.boss = None
        return

    def startCogJuror(self, duration, y):
        if self.cogJurorTrack:
            self.cogJurorTrack.finish()
        self.loadCogJuror()
        self.cogJuror.stash()
        x = 0
        curPos = self.nodePath.getPos(render)
        z = self.courtroomCeiling - curPos[2]
        self.notify.debug('curPos =%s\nz=%f' % (curPos, z))
        cogTrack = Sequence(Func(self.cogJuror.setPos, x, y, z), Func(self.cogJuror.unstash), Func(self.propTrack.loop), self.cogJuror.posInterval(duration, self.landingPt, Point3(x, y, z)), Func(self.propTrack.finish), Func(self.stashCogJuror))
        audioTrack = SoundInterval(self.propInSound, duration=duration, node=self.cogJuror, loop=1)
        self.cogJurorTrack = Parallel(audioTrack, cogTrack)
        self.cogJurorTrack.start()

    def stashCogJuror(self):
        if self.cogJuror and not self.cogJuror.isEmpty():
            self.cogJuror.stash()

    def putCogJurorOnSeat(self):
        self.stopCogsFlying()
        if self.cogJuror and not self.cogJuror.isEmpty():
            base.playSfx(self.cogJurorSound, node=self.chair)
            self.cogJuror.unstash()
            self.cogJuror.prop.stash()
            self.cogJuror.pose('landing', 47)
            self.cogJuror.setH(180)
            self.cogJuror.setPos(0, -1.25, 0.95)
            if self.toonJuror:
                self.toonJuror.hide()
        else:
            self.notify.warning('putCogJurorOnSeat invalid cogJuror')

    def putToonJurorOnSeat(self):
        if self.toonJuror and not self.toonJuror.isEmpty():
            self.toonJuror.show()
            self.toonJuror.reparentTo(self.nodePath)
            self.toonJuror.setH(180)
            self.toonJuror.setPos(0, -2.5, 0.95)
            self.toonJuror.animFSM.request('Sit')
        else:
            self.notify.warning('putToonJurorOnSeat invalid toonJuror')

    def showCogJurorFlying(self):
        self.notify.debug('showCogJurorFlying')
        self.startCogJuror(ToontownGlobals.LawbotBossCogJurorFlightTime, -ToontownGlobals.LawbotBossCogJurorDistance)

    def setBossCogId(self, bossCogId):
        self.bossCogId = bossCogId
        self.boss = base.cr.doId2do[bossCogId]

    def setIndex(self, index):
        self.index = index

    def setState(self, state):
        avId = 0
        if state == 'C':
            self.demand('Controlled', avId)
        elif state == 'F':
            self.demand('Free')
        elif state == 'N':
            self.demand('On')
        elif state == 'T':
            self.demand('ToonJuror')
        elif state == 'S':
            self.demand('SuitJuror')
        elif state == 'E':
            self.demand('EmptyJuror')
        elif state == 'E':
            self.demand('StopCogs')
        else:
            self.notify.error('Invalid state from AI: %s' % state)

    def __touchedChair(self, entry):
        self.notify.debug('__touchedChair')
        self.notify.debug('self=%s entry=%s' % (self, entry))
        self.boss.touchedChair(self, entry)

    def __touchedChairHandle(self, entry):
        self.notify.debug('__touchedChairHandle')
        self.boss.touchedChairHandle(self, entry)

    def enterToonJuror(self):
        self.chair.setColorScale(0.2, 0.2, 1.0, 1.0)
        self.boss.countToonJurors()
        if not self.cogJurorTrack:
            self.cogJuror.stash()
        self.putToonJurorOnSeat()

    def enterSuitJuror(self):
        self.chair.setColorScale(0.5, 0.5, 0.5, 1.0)
        self.boss.countToonJurors()
        if self.toonJuror:
            self.toonJuror.hide()
        self.putCogJurorOnSeat()

    def enterEmptyJuror(self):
        self.chair.setColorScale(1.0, 1.0, 1.0, 1.0)

    def enterStopCogs(self):
        self.stopCogs()

    def exitStopCogs(self):
        pass

    def enterOn(self):
        self.notify.debug('enterOn for chair %d' % self.index)
        myHeadings = ToontownGlobals.LawbotBossChairHeadings[self.index]
        seqName = 'LawbotBossChair-%s' % self.doId
        self.ival = Sequence(name=seqName)
        downAngle = -80
        for index in range(len(myHeadings)):
            nextIndex = index + 1
            if nextIndex == len(myHeadings):
                nextIndex = 0
            goingDown = self.nodePath.hprInterval(self.downTime, Point3(myHeadings[index] + self.origHpr[0], downAngle, self.origHpr[2]), startHpr=Point3(myHeadings[index] + self.origHpr[0], 0, self.origHpr[2]))
            self.ival.append(goingDown)
            self.ival.append(Wait(self.stayDownTime))
            goingUp = self.nodePath.hprInterval(self.upTime, Point3(myHeadings[nextIndex] + self.origHpr[0], 0, self.origHpr[2]), startHpr=Point3(myHeadings[index] + self.origHpr[0], downAngle, self.origHpr[2]))
            self.ival.append(goingUp)

        self.ival.loop()
        self.accept('enterChairZap', self.__touchedChair)
        self.accept('enterChairHandleZap', self.__touchedChairHandle)

    def computePos(self):
        rowIndex = self.index % 6
        if self.index < 6:
            startPt = Point3(*ToontownGlobals.LawbotBossChairRow1PosA)
            endPt = Point3(*ToontownGlobals.LawbotBossChairRow1PosB)
        else:
            startPt = Point3(*ToontownGlobals.LawbotBossChairRow2PosA)
            endPt = Point3(*ToontownGlobals.LawbotBossChairRow2PosB)
        totalDisplacement = endPt - startPt
        stepDisplacement = totalDisplacement / (6 - 1)
        newPos = stepDisplacement * rowIndex
        self.notify.debug('curDisplacement = %s' % newPos)
        newPos += startPt
        self.notify.debug('newPos before offset  = %s' % newPos)
        newPos -= Point3(*ToontownGlobals.LawbotBossJuryBoxRelativeEndPos)
        self.notify.debug('newPos  = %s' % newPos)
        return newPos

    def loadToonJuror(self):
        self.cleanupToonJuror()
        self.toonJuror = NPCToons.createLocalNPC(ToontownGlobals.LawbotBossBaseJurorNpcId + self.toonJurorIndex)
        self.toonJuror.hide()

    def setToonJurorIndex(self, newVal):
        if not self.toonJurorIndex == newVal:
            self.toonJurorIndex = newVal
            self.loadToonJuror()
