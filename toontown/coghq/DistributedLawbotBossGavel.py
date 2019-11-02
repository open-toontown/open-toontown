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

class DistributedLawbotBossGavel(DistributedObject.DistributedObject, FSM.FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedLawbotBossGavel')

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        FSM.FSM.__init__(self, 'DistributedLawbotBossGavel')
        self.boss = None
        self.index = None
        self.avId = 0
        self.modelPath = 'phase_11/models/lawbotHQ/LB_gavel'
        self.modelFindString = None
        self.nodePath = None
        self.ival = None
        self.origHpr = Point3(0, 0, 0)
        self.downTime = 0.5
        self.upTime = 5
        self.gavelSfx = None
        return

    def announceGenerate(self):
        self.notify.debug('announceGenerate: %s' % self.doId)
        DistributedObject.DistributedObject.announceGenerate(self)
        self.name = 'gavel-%s' % self.doId
        self.loadModel(self.modelPath, self.modelFindString)
        self.nodePath.wrtReparentTo(render)
        self.gavelSfx = loader.loadSfx('phase_11/audio/sfx/LB_gavel.mp3')
        tempTuple = ToontownGlobals.LawbotBossGavelPosHprs[self.index]
        self.nodePath.setPosHpr(*tempTuple)
        self.origHpr = Point3(tempTuple[3], tempTuple[4], tempTuple[5])
        self.downTime = ToontownGlobals.LawbotBossGavelTimes[self.index][0]
        self.upTime = ToontownGlobals.LawbotBossGavelTimes[self.index][1]
        self.stayDownTime = ToontownGlobals.LawbotBossGavelTimes[self.index][2]
        self.boss.gavels[self.index] = self

    def delete(self):
        DistributedObject.DistributedObject.delete(self)
        loader.unloadModel(self.modelPath)
        self.nodePath.removeNode()

    def loadModel(self, modelPath, modelFindString = None):
        if self.nodePath == None:
            self.makeNodePath()
        else:
            self.gavel.getChildren().detach()
        model = loader.loadModel(modelPath)
        if modelFindString != None:
            modTel = model.find('**/' + modelFindString)
        parts = model.findAllMatches('**/gavel*')
        gavelTop = model.find('**/top*')
        gavelHandle = model.find('**/handle*')
        model.instanceTo(self.gavel)
        self.attachColTube()
        self.scale = 3.0
        self.nodePath.setScale(self.scale)
        return

    def attachColTube(self):
        gavelTop = self.nodePath.find('**/top*')
        self.gavelTop = gavelTop
        gavelHandle = self.nodePath.find('**/handle*')
        collNode = CollisionNode(self.uniqueName('headSphere'))
        topBounds = gavelTop.getBounds()
        center = topBounds.getCenter()
        radius = topBounds.getRadius()
        tube1 = CollisionTube(0, -1, center.getZ(), 0, 1, center.getZ(), 1)
        tube1.setTangible(0)
        collNode.addSolid(tube1)
        collNode.setTag('attackCode', str(ToontownGlobals.BossCogGavelStomp))
        collNode.setName('GavelZap')
        self.collNodePath = self.nodePath.attachNewNode(collNode)
        handleBounds = gavelHandle.getBounds()
        handleCenter = handleBounds.getCenter()
        handleRadius = handleBounds.getRadius()
        tube2 = CollisionTube(0, 0, handleCenter.getZ() + handleRadius, 0, 0, handleCenter.getZ() - handleRadius, 0.25)
        tube2.setTangible(0)
        handleCollNode = CollisionNode(self.uniqueName('gavelHandle'))
        handleCollNode.addSolid(tube2)
        handleCollNode.setTag('attackCode', str(ToontownGlobals.BossCogGavelHandle))
        handleCollNode.setName('GavelHandleZap')
        self.handleCollNodePath = self.nodePath.attachNewNode(handleCollNode)

    def makeNodePath(self):
        self.nodePath = Actor.Actor()
        self.gavel = self.nodePath.attachNewNode('myGavel')

    def disable(self):
        DistributedObject.DistributedObject.disable(self)
        self.nodePath.detachNode()
        if self.ival:
            self.ival.finish()
            self.ival = None
        self.ignoreAll()
        del self.boss.gavels[self.index]
        self.cleanup()
        return

    def cleanup(self):
        self.boss = None
        return

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
        else:
            self.notify.error('Invalid state from AI: %s' % state)

    def enterOn(self):
        self.notify.debug('enterOn for gavel %d' % self.index)
        myHeadings = ToontownGlobals.LawbotBossGavelHeadings[self.index]
        seqName = 'LawbotBossGavel-%s' % self.doId
        self.ival = Sequence(name=seqName)
        downAngle = -80
        for index in range(len(myHeadings)):
            nextIndex = index + 1
            if nextIndex == len(myHeadings):
                nextIndex = 0
            goingDown = self.nodePath.hprInterval(self.downTime, Point3(myHeadings[index] + self.origHpr[0], downAngle, self.origHpr[2]), startHpr=Point3(myHeadings[index] + self.origHpr[0], 0, self.origHpr[2]))
            self.ival.append(goingDown)
            self.ival.append(SoundInterval(self.gavelSfx, node=self.gavelTop))
            self.ival.append(Wait(self.stayDownTime))
            goingUp = self.nodePath.hprInterval(self.upTime, Point3(myHeadings[nextIndex] + self.origHpr[0], 0, self.origHpr[2]), startHpr=Point3(myHeadings[index] + self.origHpr[0], downAngle, self.origHpr[2]))
            self.ival.append(goingUp)

        self.ival.loop()
        self.accept('enterGavelZap', self.__touchedGavel)
        self.accept('enterGavelHandleZap', self.__touchedGavelHandle)

    def enterOff(self):
        if self.ival:
            self.ival.finish()
        tempTuple = ToontownGlobals.LawbotBossGavelPosHprs[self.index]
        self.nodePath.setPosHpr(*tempTuple)

    def __touchedGavel(self, entry):
        self.notify.debug('__touchedGavel')
        self.notify.debug('self=%s entry=%s' % (self, entry))
        self.boss.touchedGavel(self, entry)

    def __touchedGavelHandle(self, entry):
        self.notify.debug('__touchedGavelHandle')
        self.boss.touchedGavelHandle(self, entry)
