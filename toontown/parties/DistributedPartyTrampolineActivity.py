import math
import time
import random
from direct.task import Task
from direct.directnotify import DirectNotifyGlobal
from direct.actor.Actor import Actor
from direct.fsm.FSM import FSM
from direct.gui.DirectGui import DirectButton
from direct.gui.OnscreenText import OnscreenText
from direct.interval.FunctionInterval import Func
from direct.interval.FunctionInterval import Wait
from direct.interval.LerpInterval import LerpFunc
from direct.interval.MetaInterval import Parallel
from direct.interval.MetaInterval import Sequence
from pandac.PandaModules import CardMaker
from pandac.PandaModules import NodePath
from pandac.PandaModules import TextNode
from pandac.PandaModules import Point3
from pandac.PandaModules import Vec3
from pandac.PandaModules import VBase3
from pandac.PandaModules import VBase4
from pandac.PandaModules import CollisionSphere
from pandac.PandaModules import CollisionTube
from pandac.PandaModules import CollisionNode
from pandac.PandaModules import BitMask32
from otp.otpbase import OTPGlobals
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.toontowngui import TTDialog
from toontown.parties import PartyGlobals
from toontown.parties.DistributedPartyActivity import DistributedPartyActivity
from toontown.parties.activityFSMs import TrampolineActivityFSM
from toontown.parties import PartyUtils

class DistributedPartyTrampolineActivity(DistributedPartyActivity):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPartyTrampolineActivity')

    def __init__(self, cr, doJellyBeans = True, doTricks = False, texture = None):
        DistributedPartyTrampolineActivity.notify.debug('__init__')
        DistributedPartyActivity.__init__(self, cr, PartyGlobals.ActivityIds.PartyTrampoline, PartyGlobals.ActivityTypes.GuestInitiated, wantLever=False, wantRewardGui=True)
        self.doJellyBeans = doJellyBeans
        self.doTricks = doTricks
        self.texture = texture
        self.toon = None
        self.trampHeight = 3.6
        self.trampK = 400.0
        self.normalTrampB = 2.5
        self.leavingTrampB = 8.0
        self.trampB = self.normalTrampB
        self.g = -32.0
        self.jumpBoost = 330.0
        self.beginningBoost = 500.0
        self.beginningBoostThreshold = self.trampHeight + 1.5
        self.earlyJumpThreshold = 75.0
        self.boingThreshold = 300.0
        self.turnFactor = 120.0
        self.stepDT = 0.001
        self.targetCameraPos = Point3(0.0, 40.0, 10.0)
        self.cameraSpeed = 2.0
        self.hopOffPos = Point3(16.0, 0.0, 0.0)
        self.indicatorFactor = 0.0095
        self.dropShadowCutoff = 15.0
        self.minHeightForText = 15.0
        self.heightTextOffset = -0.065
        self.beanOffset = 0.5
        self.guiBeanOffset = -0.02
        self.jumpTextShown = False
        self.toonJumped = False
        self.turnLeft = False
        self.turnRight = False
        self.leavingTrampoline = False
        self.toonVelocity = 0.0
        self.topHeight = 0.0
        self.lastPeak = 0.0
        self.beginRoundInterval = None
        self.hopOnAnim = None
        self.hopOffAnim = None
        self.flashTextInterval = None
        self.numJellyBeans = PartyGlobals.TrampolineNumJellyBeans
        self.jellyBeanBonus = PartyGlobals.TrampolineJellyBeanBonus
        self.jellyBeanStartHeight = 20.0
        self.jellyBeanStopHeight = 90.0
        self.jellyBeanColors = [VBase4(1.0, 0.5, 0.5, 1.0),
         VBase4(0.5, 1.0, 0.5, 1.0),
         VBase4(0.5, 1.0, 1.0, 1.0),
         VBase4(1.0, 1.0, 0.4, 1.0),
         VBase4(0.4, 0.4, 1.0, 1.0),
         VBase4(1.0, 0.5, 1.0, 1.0)]
        delta = (self.jellyBeanStopHeight - self.jellyBeanStartHeight) / (self.numJellyBeans - 1)
        self.jellyBeanPositions = [ self.jellyBeanStartHeight + n * delta for n in range(self.numJellyBeans) ]
        self.doSimulateStep = False
        return

    def load(self):
        DistributedPartyTrampolineActivity.notify.debug('load')
        DistributedPartyActivity.load(self)
        self.loadModels()
        self.loadCollision()
        self.loadGUI()
        self.loadSounds()
        self.loadIntervals()
        self.activityFSM = TrampolineActivityFSM(self)
        self.activityFSM.request('Idle')
        self.animFSM = TrampolineAnimFSM(self)
        self.setBestHeightInfo('', 0)

    def loadModels(self):
        self.tramp = self.root.attachNewNode(self.uniqueName('tramp'))
        self.screenPlaneElements = NodePath(self.uniqueName('screenPlane'))
        self.trampActor = Actor('phase_13/models/parties/trampoline_model', {'emptyAnim': 'phase_13/models/parties/trampoline_anim'})
        self.trampActor.reparentTo(self.tramp)
        if self.texture:
            reskinNode = self.tramp.find('**/trampoline/__Actor_modelRoot/-GeomNode')
            reskinNode.setTexture(loader.loadTexture(self.texture), 100)
        self.surface = NodePath(self.uniqueName('trampSurface'))
        self.surface.reparentTo(self.tramp)
        self.surface.setZ(self.trampHeight)
        self.trampActor.controlJoint(self.surface, 'modelRoot', 'trampoline_joint1')
        self.sign.setPos(PartyGlobals.TrampolineSignOffset)
        self.beans = [ loader.loadModelCopy('phase_4/models/props/jellybean4') for i in range(self.numJellyBeans) ]
        for bean in self.beans:
            bean.find('**/jellybean').setP(-35.0)
            bean.setScale(3.0)
            bean.setTransparency(True)
            bean.reparentTo(self.tramp)
            bean.stash()

        self.beans[-1].setScale(8.0)

    def loadCollision(self):
        collTube = CollisionTube(0.0, 0.0, 0.0, 0.0, 0.0, 6.0, 5.4)
        collTube.setTangible(True)
        self.trampolineCollision = CollisionNode(self.uniqueName('TrampolineCollision'))
        self.trampolineCollision.addSolid(collTube)
        self.trampolineCollision.setCollideMask(OTPGlobals.CameraBitmask | OTPGlobals.WallBitmask)
        self.trampolineCollisionNP = self.tramp.attachNewNode(self.trampolineCollision)
        collSphere = CollisionSphere(0.0, 0.0, 0.0, 7.0)
        collSphere.setTangible(False)
        self.trampolineTrigger = CollisionNode(self.uniqueName('TrampolineTrigger'))
        self.trampolineTrigger.addSolid(collSphere)
        self.trampolineTrigger.setIntoCollideMask(OTPGlobals.WallBitmask)
        self.trampolineTriggerNP = self.tramp.attachNewNode(self.trampolineTrigger)
        self.accept('enter%s' % self.uniqueName('TrampolineTrigger'), self.onTrampolineTrigger)

    def loadGUI(self):
        self.gui = loader.loadModel('phase_13/models/parties/trampolineGUI')
        self.gui.setX(-1.15)
        self.gui.reparentTo(self.screenPlaneElements)
        self.toonIndicator = self.gui.find('**/trampolineGUI_MovingBar')
        jumpLineLocator = self.gui.find('**/jumpLine_locator')
        guiBean = self.gui.find('**/trampolineGUI_GreenJellyBean')
        self.gui.find('**/trampolineGUI_GreenJellyBean').stash()
        self.guiBeans = [ guiBean.instanceUnderNode(jumpLineLocator, self.uniqueName('guiBean%d' % i)) for i in range(self.numJellyBeans) ]
        self.guiBeans[-1].setScale(1.5)
        heightTextNode = TextNode(self.uniqueName('TrampolineActivity.heightTextNode'))
        heightTextNode.setFont(ToontownGlobals.getSignFont())
        heightTextNode.setAlign(TextNode.ALeft)
        heightTextNode.setText('0.0')
        heightTextNode.setShadow(0.05, 0.05)
        heightTextNode.setShadowColor(0.0, 0.0, 0.0, 1.0)
        heightTextNode.setTextColor(1.0, 1.0, 1.0, 1.0)
        self.heightText = jumpLineLocator.attachNewNode(heightTextNode)
        self.heightText.setX(0.15)
        self.heightText.setScale(0.1)
        self.heightText.setAlphaScale(0.0)
        self.quitEarlyButtonModels = loader.loadModel('phase_3.5/models/gui/inventory_gui')
        quitEarlyUp = self.quitEarlyButtonModels.find('**//InventoryButtonUp')
        quitEarlyDown = self.quitEarlyButtonModels.find('**/InventoryButtonDown')
        quitEarlyRollover = self.quitEarlyButtonModels.find('**/InventoryButtonRollover')
        self.quitEarlyButton = DirectButton(parent=self.screenPlaneElements, relief=None, text=TTLocalizer.PartyTrampolineQuitEarlyButton, text_fg=(1, 1, 0.65, 1), text_pos=(0, -0.23), text_scale=0.7, image=(quitEarlyUp, quitEarlyDown, quitEarlyRollover), image_color=(1, 0, 0, 1), image_scale=(20, 1, 11), pos=(1.15, 0, 0.6), scale=0.09, command=self.leaveTrampoline)
        self.quitEarlyButton.stash()
        self.flashText = OnscreenText(text='', pos=(0.0, -0.45), scale=0.2, fg=(1.0, 1.0, 0.65, 1.0), align=TextNode.ACenter, font=ToontownGlobals.getSignFont(), mayChange=True)
        self.timer = PartyUtils.getNewToontownTimer()
        self.timer.reparentTo(self.screenPlaneElements)
        return

    def loadSounds(self):
        self.jellyBeanSound = base.loader.loadSfx('phase_4/audio/sfx/sparkly.ogg')
        self.boingSound = base.loader.loadSfx('phase_4/audio/sfx/target_trampoline_2.ogg')
        self.whistleSound = base.loader.loadSfx('phase_4/audio/sfx/AA_sound_whistle.ogg')

    def loadIntervals(self):

        def prepareHeightText():
            self.heightText.node().setText(TTLocalizer.PartyTrampolineGetHeight % int(self.toon.getZ()))
            self.heightText.setZ(self.indicatorFactor * self.toon.getZ() + self.heightTextOffset)

        self.heightTextInterval = Sequence(Func(prepareHeightText), LerpFunc(self.heightText.setAlphaScale, fromData=1.0, toData=0.0, duration=1.0))

    def unload(self):
        DistributedPartyTrampolineActivity.notify.debug('unload')
        if self.hopOnAnim and self.hopOnAnim.isPlaying():
            self.hopOnAnim.finish()
        if self.hopOffAnim and self.hopOffAnim.isPlaying():
            self.hopOffAnim.finish()
        if self.beginRoundInterval and self.beginRoundInterval.isPlaying():
            self.beginRoundInterval.finish()
        if self.flashTextInterval and self.flashTextInterval.isPlaying():
            self.flashTextInterval.finish()
        if self.heightTextInterval and self.heightTextInterval.isPlaying():
            self.heightTextInterval.finish()
        self.timer.stop()
        DistributedPartyActivity.unload(self)
        taskMgr.remove(self.uniqueName('TrampolineActivity.updateTask'))
        taskMgr.remove(self.uniqueName('TrampolineActivity.remoteUpdateTask'))
        self.ignoreAll()
        del self.heightTextInterval
        del self.beginRoundInterval
        del self.hopOnAnim
        del self.hopOffAnim
        del self.flashTextInterval
        if hasattr(self, 'beanAnims'):
            self.cleanupJellyBeans()
        self.quitEarlyButton.destroy()
        del self.quitEarlyButton
        if self.screenPlaneElements:
            self.screenPlaneElements.removeNode()
            self.screenPlaneElements = None
        del self.activityFSM
        del self.animFSM
        return

    def setBestHeightInfo(self, toonName, height):
        self.bestHeightInfo = (toonName, height)
        DistributedPartyTrampolineActivity.notify.debug('%s has the best height of %d' % (toonName, height))
        if height > 0:
            self.setSignNote(TTLocalizer.PartyTrampolineBestHeight % self.bestHeightInfo)
        else:
            self.setSignNote(TTLocalizer.PartyTrampolineNoHeightYet)

    def leaveTrampoline(self):
        if self.toon != None and self.toon.doId == base.localAvatar.doId:
            self._showFlashMessage(TTLocalizer.PartyTrampolineTimesUp)
            self.leavingTrampoline = True
            self.timer.reset()
            self.trampB = self.leavingTrampB
            self.ignore('control')
            self.quitEarlyButton.stash()
        return

    def requestAnim(self, request):
        self.animFSM.request(request)

    def b_requestAnim(self, request):
        self.requestAnim(request)
        self.sendUpdate('requestAnim', [request])

    def requestAnimEcho(self, request):
        if self.toon != None and self.toon.doId != base.localAvatar.doId:
            self.requestAnim(request)
        return

    def removeBeans(self, beansToRemove):
        for i in beansToRemove:
            height, bean, guiBean, beanAnim = self.beanDetails[i]
            guiBean.stash()
            if i in self.beansToCollect:
                self.beansToCollect.remove(i)
            else:
                self.notify.warning('removeBeans avoided a crash, %d not in self.beansToCollect' % i)
            self.poofBean(bean, beanAnim)

    def b_removeBeans(self, beansToRemove):
        self.removeBeans(beansToRemove)
        self.sendUpdate('removeBeans', [beansToRemove])

    def removeBeansEcho(self, beansToRemove):
        if self.toon != None and self.toon.doId != base.localAvatar.doId:
            self.removeBeans(beansToRemove)
        return

    def joinRequestDenied(self, reason):
        DistributedPartyActivity.joinRequestDenied(self, reason)
        self.showMessage(TTLocalizer.PartyActivityDefaultJoinDeny)
        base.cr.playGame.getPlace().fsm.request('walk')

    def exitRequestDenied(self, reason):
        DistributedPartyActivity.exitRequestDenied(self, reason)
        self.showMessage(TTLocalizer.PartyActivityDefaultExitDeny)

    def setState(self, newState, timestamp):
        DistributedPartyTrampolineActivity.notify.debug('setState( newState=%s, ... )' % newState)
        DistributedPartyActivity.setState(self, newState, timestamp)
        self.activityFSM.request(newState)

    def startIdle(self):
        DistributedPartyTrampolineActivity.notify.debug('startIdle')

    def finishIdle(self):
        DistributedPartyTrampolineActivity.notify.debug('finishIdle')

    def startRules(self):
        DistributedPartyTrampolineActivity.notify.debug('startRules')
        if self.doJellyBeans:
            self.setupJellyBeans()
        if self.toon != None and self.toon.doId == base.localAvatar.doId:
            self.acquireToon()
        return

    def startActive(self):
        DistributedPartyTrampolineActivity.notify.debug('startActive')
        if self.toon != None and self.toon.doId == base.localAvatar.doId:
            base.setCellsAvailable(base.bottomCells, True)
            self.accept('arrow_left', self.onLeft)
            self.accept('arrow_left-up', self.onLeftUp)
            self.accept('arrow_right', self.onRight)
            self.accept('arrow_right-up', self.onRightUp)
            self.beginRoundInterval = Sequence(Func(self._showFlashMessage, TTLocalizer.PartyTrampolineReady), Wait(1.2), Func(self.flashMessage, TTLocalizer.PartyTrampolineGo), Func(self.beginRound))
            self.beginRoundInterval.start()
        return

    def finishActive(self):
        DistributedPartyTrampolineActivity.notify.debug('finishActive')
        if self.doJellyBeans:
            self.cleanupJellyBeans()

    def setupJellyBeans(self):
        self.beanAnims = []
        self.beansToCollect = []
        self.beanDetails = []
        self.numBeansCollected = 0
        for i in range(self.numJellyBeans):
            bean = self.beans[i]
            guiBean = self.guiBeans[i]
            height = self.jellyBeanPositions[i]
            color = random.choice(self.jellyBeanColors)
            bean.find('**/jellybean').setColor(color)
            if self.toon.doId == base.localAvatar.doId:
                bean.setAlphaScale(1.0)
            else:
                bean.setAlphaScale(0.5)
            guiBean.setColor(color)
            bean.setZ(height + self.toon.getHeight() + self.beanOffset)
            guiBean.setZ(height * self.indicatorFactor + self.guiBeanOffset)
            bean.setH(0.0)
            bean.unstash()
            guiBean.unstash()
            beanAnim = bean.hprInterval(1.5, VBase3((i % 2 * 2 - 1) * 360.0, 0.0, 0.0))
            beanAnim.loop()
            self.beanAnims.append(beanAnim)
            self.beanDetails.append((height,
             bean,
             guiBean,
             beanAnim))

        self.beansToCollect = list(range(self.numJellyBeans))

    def cleanupJellyBeans(self):
        for bean in self.beans:
            bean.stash()

        for guiBean in self.guiBeans:
            guiBean.stash()

        if hasattr(self, 'beanAnims'):
            for beanAnim in self.beanAnims:
                beanAnim.finish()

            del self.beanAnims
            del self.beansToCollect

    def beginRound(self):
        base.playSfx(self.whistleSound)
        self.timer.setTime(PartyGlobals.TrampolineDuration)
        self.timer.countdown(PartyGlobals.TrampolineDuration)
        self.timer.show()
        self.quitEarlyButton.unstash()
        self.notify.debug('Accepting contorl')
        self.accept('control', self.onJump)
        self.notify.debug('setting simulate step to true')
        self.doSimulateStep = True

    def acquireToon(self):
        self.toon.disableSmartCameraViews()
        self.toon.stopUpdateSmartCamera()
        camera.wrtReparentTo(render)
        self.toon.dropShadow.reparentTo(hidden)
        self.toon.startPosHprBroadcast(period=0.2)
        self.toonAcceleration = 0.0
        self.toonVelocity = 0.0
        self.topHeight = 0.0
        self.trampB = self.normalTrampB
        self.leavingTrampoline = False
        self.hopOnAnim = Sequence(Func(self.toon.b_setAnimState, 'jump', 1.0), Wait(0.4), PartyUtils.arcPosInterval(0.75, self.toon, Point3(0.0, 0.0, self.trampHeight), 5.0, self.tramp), Func(self.postHopOn))
        self.hopOnAnim.start()

    def postHopOn(self):
        self.toon.setH(self.toon.getH() + 90.0)
        self.toon.dropShadow.reparentTo(self.surface)
        self.screenPlaneElements.reparentTo(aspect2d)
        self.timeLeftToSimulate = 0.0
        self.doSimulateStep = False
        taskMgr.add(self.updateTask, self.uniqueName('TrampolineActivity.updateTask'))
        base.setCellsAvailable(base.leftCells, False)
        base.setCellsAvailable(base.bottomCells, False)
        DistributedPartyActivity.startRules(self)

    def releaseToon(self):
        self._hideFlashMessage()
        self.ignore('arrow_left')
        self.ignore('arrow_left-up')
        self.ignore('arrow_right')
        self.ignore('arrow_right-up')
        taskMgr.remove(self.uniqueName('TrampolineActivity.updateTask'))
        self.hopOffAnim = Sequence(self.toon.hprInterval(0.5, VBase3(-90.0, 0.0, 0.0), other=self.tramp), Func(self.toon.b_setAnimState, 'jump', 1.0), Func(self.toon.dropShadow.reparentTo, hidden), Wait(0.4), PartyUtils.arcPosInterval(0.75, self.toon, self.hopOffPos, 5.0, self.tramp), Func(self.postHopOff))
        self.hopOffAnim.start()

    def postHopOff(self):
        self.screenPlaneElements.reparentTo(hidden)
        base.setCellsAvailable(base.leftCells, True)
        self.timer.stop()
        self.timer.hide()
        self.toon.dropShadow.reparentTo(self.toon.getShadowJoint())
        self.toon.dropShadow.setAlphaScale(1.0)
        self.toon.dropShadow.setScale(1.0)
        self.b_requestAnim('Off')
        camera.reparentTo(base.localAvatar)
        base.localAvatar.startUpdateSmartCamera()
        base.localAvatar.enableSmartCameraViews()
        base.localAvatar.setCameraPositionByIndex(base.localAvatar.cameraIndex)
        place = base.cr.playGame.getPlace()
        if self.doJellyBeans:
            self.sendUpdate('awardBeans', [self.numBeansCollected, int(self.topHeight)])
            if int(self.topHeight) > self.bestHeightInfo[1]:
                self.sendUpdate('reportHeightInformation', [int(self.topHeight)])
        self.d_toonExitDemand()

    def onTrampolineTrigger(self, collEntry):
        if self.activityFSM.state == 'Idle' and self.toon == None and base.cr.playGame.getPlace().fsm.getCurrentState().getName() == 'walk':
            base.cr.playGame.getPlace().fsm.request('activity')
            self.d_toonJoinRequest()
        else:
            self.flashMessage(TTLocalizer.PartyTrampolineActivityOccupied, duration=2.0)
        return

    def onJump(self):
        self.notify.debug('got onJump')
        if self.toon != None and self.toon.getZ() < self.trampHeight:
            self.toonJumped = True
            self.b_requestAnim('Jump')
        else:
            self.notify.debug('z is less than tramp height')
        return

    def onLeft(self):
        self.turnLeft = True

    def onLeftUp(self):
        self.turnLeft = False

    def onRight(self):
        self.turnRight = True

    def onRightUp(self):
        self.turnRight = False

    def handleToonJoined(self, toonId):
        DistributedPartyTrampolineActivity.notify.debug('handleToonJoined')
        self.toon = self.getAvatar(toonId)
        if self.toon != None and not self.toon.isEmpty():
            self.oldJumpSquatPlayRate = self.toon.getPlayRate('jump-squat')
            self.oldJumpLandPlayRate = self.toon.getPlayRate('jump-land')
            self.toon.setPlayRate(2.5, 'jump-squat')
            self.toon.setPlayRate(2.0, 'jump-land')
            self.turnLeft = False
            self.turnRight = False
            self.activityFSM.request('Rules')
            if self.toon.doId != base.localAvatar.doId:
                taskMgr.add(self.remoteUpdateTask, self.uniqueName('TrampolineActivity.remoteUpdateTask'))
        else:
            self.notify.warning('handleToonJoined could not get toon %d' % toonId)
        return

    def handleToonExited(self, toonId):
        DistributedPartyTrampolineActivity.notify.debug('handleToonExited')
        if self.toon != None:
            if self.toon.doId != base.localAvatar.doId:
                taskMgr.remove(self.uniqueName('TrampolineActivity.remoteUpdateTask'))
            self.surface.setZ(self.trampHeight)
            self.toon.setPlayRate(self.oldJumpSquatPlayRate, 'jump-squat')
            self.toon.setPlayRate(self.oldJumpLandPlayRate, 'jump-land')
            self.toon = None
        return

    def handleToonDisabled(self, toonId):
        DistributedPartyTrampolineActivity.notify.debug('handleToonDisabled')
        DistributedPartyTrampolineActivity.notify.debug('avatar ' + str(toonId) + ' disabled')
        if base.localAvatar.doId == toonId:
            self.releaseToon()

    def handleRulesDone(self):
        self.sendUpdate('toonReady')
        self.finishRules()

    def getTitle(self):
        if self.doJellyBeans:
            return TTLocalizer.PartyTrampolineJellyBeanTitle
        elif self.doTricks:
            return TTLocalizer.PartyTrampolineTricksTitle
        else:
            return DistributedPartyActivity.getTitle(self)

    def getInstructions(self):
        return TTLocalizer.PartyTrampolineActivityInstructions

    def updateTask(self, task):
        z = self.toon.getZ()
        dt = globalClock.getDt()
        if self.doSimulateStep:
            self.timeLeftToSimulate += dt
            while self.timeLeftToSimulate >= self.stepDT:
                z, a = self.simulateStep(z)
                self.timeLeftToSimulate -= self.stepDT

        self.toon.setZ(z)
        if z <= self.trampHeight:
            self.surface.setZ(z)
        else:
            self.surface.setZ(self.trampHeight)
        self.toonIndicator.setZ((z - self.trampHeight) * self.indicatorFactor)
        if self.turnLeft:
            self.toon.setH(self.toon.getH() + self.turnFactor * dt)
        if self.turnRight:
            self.toon.setH(self.toon.getH() - self.turnFactor * dt)
        currentPos = base.camera.getPos(self.toon)
        vec = self.targetCameraPos - currentPos
        newPos = currentPos + vec * (dt * self.cameraSpeed)
        base.camera.setPos(self.toon, newPos)
        base.camera.lookAt(self.toon)
        if z > self.trampHeight:
            heightFactor = 1.0 - min(1.0, (z - self.trampHeight) / self.dropShadowCutoff)
            self.toon.dropShadow.setAlphaScale(heightFactor)
            self.toon.dropShadow.setScale(max(0.1, heightFactor))
        else:
            self.toon.dropShadow.setAlphaScale(1.0)
            self.toon.dropShadow.setScale(1.0)
        if self.leavingTrampoline and z < self.trampHeight and abs(a) < 0.1:
            self.releaseToon()
        return Task.cont

    def simulateStep(self, z):
        if z >= self.trampHeight:
            a = self.g
            self.toonJumped = False
        else:
            a = self.g + self.trampK * (self.trampHeight - z) - self.trampB * self.toonVelocity
            if self.toonJumped:
                if self.lastPeak > self.earlyJumpThreshold or self.toonVelocity >= -300000.0:
                    a += self.jumpBoost
                    if self.lastPeak < self.beginningBoostThreshold:
                        a += self.beginningBoost
        lastVelocity = self.toonVelocity
        self.toonVelocity += a * self.stepDT
        if lastVelocity > 0.0 and self.toonVelocity <= 0.0:
            topOfJump = True
            bottomOfJump = False
        elif lastVelocity < 0.0 and self.toonVelocity >= 0.0:
            topOfJump = False
            bottomOfJump = True
        else:
            topOfJump = False
            bottomOfJump = False
        newZ = z + self.toonVelocity * self.stepDT
        if newZ > self.topHeight:
            self.topHeight = newZ
            if self.doJellyBeans:
                self.collectJellyBeans(newZ)
        if topOfJump:
            self.lastPeak = newZ
            if newZ >= self.minHeightForText:
                self.heightTextInterval.start()
        if topOfJump:
            if newZ > self.trampHeight + 20.0:
                self.b_requestAnim('Falling')
            elif self.animFSM.state == 'Jump':
                self.b_requestAnim('Falling')
        if newZ <= self.trampHeight and z > self.trampHeight:
            if self.animFSM.state == 'Falling':
                self.b_requestAnim('Land')
            elif self.animFSM.state != 'Neutral':
                self.b_requestAnim('Neutral')
        if bottomOfJump and a > self.boingThreshold:
            base.playSfx(self.boingSound)
        return (newZ, a)

    def collectJellyBeans(self, z):
        beansToRemove = []
        for i in self.beansToCollect:
            height = self.beanDetails[i][0]
            if height <= z:
                beansToRemove.append(i)

        if len(beansToRemove) > 0:
            base.playSfx(self.jellyBeanSound)
            self.numBeansCollected += len(beansToRemove)
            self.b_removeBeans(beansToRemove)

    def remoteUpdateTask(self, task):
        if self.toon != None and not self.toon.isEmpty():
            z = self.toon.getZ()
            if z <= self.trampHeight:
                self.surface.setZ(z)
            else:
                self.surface.setZ(self.trampHeight)
        return Task.cont

    def poofBean(self, bean, beanAnim):
        if bean == None:
            self.notify.warning('poofBean, returning immediately as bean is None')
            return
        if bean.isEmpty():
            self.notify.warning('poofBean, returning immediately as bean is empty')
            return
        currentAlpha = bean.getColorScale()[3]
        currentScale = bean.getScale()
        poofAnim = Sequence(Parallel(LerpFunc(bean.setAlphaScale, fromData=currentAlpha, toData=0.0, duration=0.25), LerpFunc(bean.setScale, fromData=currentScale, toData=currentScale * 5.0, duration=0.25)), Func(bean.stash), Func(beanAnim.finish), Func(bean.setAlphaScale, currentAlpha), Func(bean.setScale, currentScale))
        poofAnim.start()
        return

    def _showFlashMessage(self, message):
        if self.isDisabled():
            return
        if self.flashTextInterval is not None and self.flashTextInterval.isPlaying():
            self.flashTextInterval.finish()
        self.flashText.setText(message)
        self.flashText.setAlphaScale(1.0)
        self.flashText.unstash()
        return

    def _hideFlashMessage(self, duration = 0.0):
        if self.isDisabled():
            pass
        self.flashTextInterval = Sequence(Wait(duration), LerpFunc(self.flashText.setAlphaScale, fromData=1.0, toData=0.0, duration=1.0), Func(self.flashText.stash))
        self.flashTextInterval.start()

    def flashMessage(self, message, duration = 0.5):
        self._showFlashMessage(message)
        self._hideFlashMessage(duration)


class TrampolineAnimFSM(FSM):

    def __init__(self, activity):
        FSM.__init__(self, self.__class__.__name__)
        self.activity = activity

    def defaultFilter(self, request, args):
        if request == self.state:
            return None
        else:
            return FSM.defaultFilter(self, request, args)
        return None

    def enterNeutral(self):
        self.activity.toon.play('neutral')

    def exitNeutral(self):
        pass

    def enterJump(self):
        self.activity.toon.play('jump-squat')

    def exitJump(self):
        pass

    def enterFalling(self):
        self.activity.toon.loop('jump-idle')

    def exitFalling(self):
        self.activity.toon.stop('jump-idle')

    def enterLand(self):
        self.activity.toon.play('jump-land')

    def exitLand(self):
        pass
