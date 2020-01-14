from direct.distributed.ClockDelta import *
from direct.interval.IntervalGlobal import *
from toontown.building.ElevatorConstants import *
from toontown.building.ElevatorUtils import *
from toontown.building import DistributedElevatorExt
from toontown.building import DistributedElevator
from toontown.toonbase import ToontownGlobals
from direct.fsm import ClassicFSM
from direct.fsm import State
from direct.gui import DirectGui
from toontown.hood import ZoneUtil
from toontown.toonbase import TTLocalizer
from toontown.toontowngui import TTDialog
from direct.distributed import DistributedObject
from direct.distributed import DistributedSmoothNode
from direct.actor import Actor
from direct.fsm.FSM import FSM
from direct.showbase import PythonUtil
from toontown.toonbase.ToontownTimer import ToontownTimer
from toontown.racing.Kart import Kart
from toontown.racing.KartShopGlobals import KartGlobals
from toontown.racing import RaceGlobals
from toontown.toontowngui.TTDialog import TTGlobalDialog
from toontown.toontowngui.TeaserPanel import TeaserPanel
if (__debug__):
    import pdb

class DistributedStartingBlock(DistributedObject.DistributedObject, FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedStartingBlock')
    sphereRadius = 1.5
    id = 0
    cameraPos = Point3(0, -23, 10)
    cameraHpr = Point3(0, -10, 0)
    SFX_BaseDir = 'phase_6/audio/sfx/'
    SFX_KartAppear = SFX_BaseDir + 'KART_Appear.ogg'
    defaultTransitions = {'Off': ['EnterMovie'],
     'EnterMovie': ['Off', 'Waiting', 'ExitMovie'],
     'Waiting': ['ExitMovie', 'Off'],
     'ExitMovie': ['Off', 'ExitMovie']}

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        FSM.__init__(self, 'staringBlock_%s_FSM' % DistributedStartingBlock.id)
        self.avId = 0
        self.av = None
        self.lastAvId = 0
        self.avatar = None
        self.kartPad = None
        self.collNode = None
        self.movieNode = None
        self.movieTrack = None
        self.collSphere = None
        self.collNodePath = None
        self.localToonKarting = 0
        self.kartNode = None
        self.kart = None
        self.holeActor = None
        self.exitRequested = False
        if (__debug__):
            self.testLOD = False
        self.id = DistributedStartingBlock.id
        DistributedStartingBlock.id += 1
        return

    def disable(self):
        FSM.cleanup(self)
        self.ignore(self.uniqueName('enterStartingBlockSphere'))
        self.ignore('stoppedAsleep')
        self.setOccupied(0)
        self.avId = 0
        self.nodePath.detachNode()
        self.kartPad = None
        if self.holeActor:
            self.holeActor.cleanup()
            self.holeActor = None
        DistributedObject.DistributedObject.disable(self)
        return

    def delete(self):
        if hasattr(self, 'dialog'):
            if not self.dialog.removed():
                self.dialog.ignoreAll()
                if not self.dialog.isEmpty():
                    self.dialog.cleanup()
                del self.dialog
        self.finishMovie()
        if hasattr(self, 'cancelButton'):
            self.cancelButton.destroy()
            del self.cancelButton
        del self.kartPad
        if self.nodePath:
            self.nodePath.removeNode()
            del self.nodePath
        DistributedObject.DistributedObject.delete(self)

    def generateInit(self):
        self.notify.debugStateCall(self)
        DistributedObject.DistributedObject.generateInit(self)
        self.nodePath = NodePath(self.uniqueName('StartingBlock'))
        self.collSphere = CollisionSphere(0, 0, 0, self.sphereRadius)
        self.collSphere.setTangible(0)
        self.collNode = CollisionNode(self.uniqueName('StartingBlockSphere'))
        self.collNode.setCollideMask(ToontownGlobals.WallBitmask)
        self.collNode.addSolid(self.collSphere)
        self.collNodePath = self.nodePath.attachNewNode(self.collNode)

    def announceGenerate(self):
        self.notify.debugStateCall(self)
        DistributedObject.DistributedObject.announceGenerate(self)
        self.nodePath.reparentTo(render)
        self.accept(self.uniqueName('enterStartingBlockSphere'), self.__handleEnterSphere)
        if (__debug__):
            if self.testLOD:
                self.__generateKartAppearTrack()

    def setPadDoId(self, padDoId):
        self.notify.debugStateCall(self)
        self.kartPad = base.cr.doId2do.get(padDoId)
        self.kartPad.addStartingBlock(self)

    def setPosHpr(self, x, y, z, h, p, r):
        self.notify.debugStateCall(self)
        self.nodePath.setPosHpr(x, y, z, h + 180, 0, 0)

    def setPadLocationId(self, padLocationId):
        self.notify.debugStateCall(self)
        self.movieNode = self.nodePath.attachNewNode(self.uniqueName('MovieNode'))
        self.exitMovieNode = self.movieNode
        if padLocationId % 2:
            self.movieNode.setPosHpr(3.0, 0, 0, 90.0, 0, 0)
        else:
            self.movieNode.setPosHpr(-3.0, 0, 0, -90.0, 0, 0)

    def setActive(self, isTangible):
        self.collSphere.setTangible(isTangible)

    def __handleEnterSphere(self, collEntry):
        if base.localAvatar.doId == self.lastAvId and globalClock.getFrameCount() <= self.lastFrame + 1:
            self.notify.debug('Ignoring duplicate entry for avatar.')
            return
        if base.localAvatar.hp > 0:

            def handleEnterRequest(self = self):
                self.ignore('stoppedAsleep')
                if hasattr(self.dialog, 'doneStatus') and self.dialog.doneStatus == 'ok':
                    self.d_requestEnter(base.cr.isPaid())
                elif self.cr and not self.isDisabled():
                    self.cr.playGame.getPlace().setState('walk')
                else:
                    self.notify.warning('Warning! Object has already been disabled.')
                self.dialog.ignoreAll()
                self.dialog.cleanup()
                del self.dialog

            self.cr.playGame.getPlace().fsm.request('stopped')
            self.accept('stoppedAsleep', handleEnterRequest)
            doneEvent = 'enterRequest|dialog'
            if self.kartPad.isPractice():
                msg = TTLocalizer.StartingBlock_EnterPractice
            else:
                raceName = TTLocalizer.KartRace_RaceNames[self.kartPad.trackType]
                numTickets = RaceGlobals.getEntryFee(self.kartPad.trackId, self.kartPad.trackType)
                msg = TTLocalizer.StartingBlock_EnterNonPractice % (raceName, numTickets)
            self.dialog = TTGlobalDialog(msg, doneEvent, 4)
            self.dialog.accept(doneEvent, handleEnterRequest)

    def d_movieFinished(self):
        self.notify.debugStateCall(self)
        self.sendUpdate('movieFinished', [])

    def d_requestEnter(self, paid):
        self.notify.debugStateCall(self)
        self.sendUpdate('requestEnter', [paid])

    def d_requestExit(self):
        self.notify.debugStateCall(self)
        self.exitRequested = True
        self.hideGui()
        self.sendUpdate('requestExit', [])

    def rejectEnter(self, errCode):
        self.notify.debugStateCall(self)

        def handleTicketError(self = self):
            self.ignore('stoppedAsleep')
            self.dialog.ignoreAll()
            self.dialog.cleanup()
            del self.dialog
            self.cr.playGame.getPlace().setState('walk')

        doneEvent = 'errorCode|dialog'
        if errCode == KartGlobals.ERROR_CODE.eTickets:
            msg = TTLocalizer.StartingBlock_NotEnoughTickets
            self.dialog = TTGlobalDialog(msg, doneEvent, 2)
            self.dialog.accept(doneEvent, handleTicketError)
            self.accept('stoppedAsleep', handleTicketError)
        elif errCode == KartGlobals.ERROR_CODE.eBoardOver:
            msg = TTLocalizer.StartingBlock_NoBoard
            self.dialog = TTGlobalDialog(msg, doneEvent, 2)
            self.dialog.accept(doneEvent, handleTicketError)
            self.accept('stoppedAsleep', handleTicketError)
        elif errCode == KartGlobals.ERROR_CODE.eNoKart:
            msg = TTLocalizer.StartingBlock_NoKart
            self.dialog = TTGlobalDialog(msg, doneEvent, 2)
            self.dialog.accept(doneEvent, handleTicketError)
            self.accept('stoppedAsleep', handleTicketError)
        elif errCode == KartGlobals.ERROR_CODE.eOccupied:
            msg = TTLocalizer.StartingBlock_Occupied
            self.dialog = TTGlobalDialog(msg, doneEvent, 2)
            self.dialog.accept(doneEvent, handleTicketError)
            self.accept('stoppedAsleep', handleTicketError)
        elif errCode == KartGlobals.ERROR_CODE.eTrackClosed:
            msg = TTLocalizer.StartingBlock_TrackClosed
            self.dialog = TTGlobalDialog(msg, doneEvent, 2)
            self.dialog.accept(doneEvent, handleTicketError)
            self.accept('stoppedAsleep', handleTicketError)
        elif errCode == KartGlobals.ERROR_CODE.eUnpaid:
            self.dialog = TeaserPanel(pageName='karting', doneFunc=handleTicketError)
        else:
            self.cr.playGame.getPlace().setState('walk')

    def finishMovie(self):
        if self.movieTrack:
            self.movieTrack.finish()
            self.movieTrack = None
        return

    def setOccupied(self, avId):
        self.notify.debug('%d setOccupied: %d' % (self.doId, avId))
        if self.av != None:
            self.finishMovie()
            if not self.av.isEmpty() and not self.av.isDisabled():
                self.av.loop('neutral')
                self.av.setParent(ToontownGlobals.SPRender)
                self.av.startSmooth()
            self.finishMovie()
            if self.kart:
                self.kart.delete()
                self.kart = None
            if self.kartNode:
                self.kartNode.removeNode()
                self.kartNode = None
            self.placedAvatar = 0
            self.ignore(self.av.uniqueName('disable'))
            self.av = None
        wasLocalToon = self.localToonKarting
        self.lastAvId = self.avId
        self.lastFrame = globalClock.getFrameCount()
        self.avId = avId
        self.localToonKarting = 0
        if self.avId == 0:
            self.collSphere.setTangible(0)
            self.request('Off')
        else:
            self.collSphere.setTangible(1)
            av = self.cr.doId2do.get(self.avId)
            self.placedAvatar = 0
            if self.avId == base.localAvatar.doId:
                self.localToonKarting = 1
            if av != None:
                self.av = av
                self.av.stopSmooth()
                self.placedAvatar = 0
                self.acceptOnce(self.av.uniqueName('disable'), self.__avatarGone)
                self.kartNode = render.attachNewNode(self.av.uniqueName('KartNode'))
                self.kartNode.setPosHpr(self.nodePath.getPos(render), self.nodePath.getHpr(render))
                self.kart = Kart()
                self.kart.baseScale = 1.6
                self.kart.setDNA(self.av.getKartDNA())
                self.kart.generateKart()
                self.kart.resetGeomPos()
                self.av.wrtReparentTo(self.nodePath)
                self.av.setAnimState('neutral', 1.0)
                if not self.localToonKarting:
                    av.stopSmooth()
                    self.__placeAvatar()
                self.avParent = av.getParent()
            else:
                self.notify.warning('Unknown avatar %d in kart block %d ' % (self.avId, self.doId))
                self.avId = 0
        if wasLocalToon and not self.localToonKarting:
            place = base.cr.playGame.getPlace()
            if place:
                if self.exitRequested:
                    place.setState('walk')
                else:

                    def handleDialogOK(self = self):
                        self.ignore('stoppedAsleep')
                        place.setState('walk')
                        self.dialog.ignoreAll()
                        self.dialog.cleanup()
                        del self.dialog

                    doneEvent = 'kickedOutDialog'
                    msg = TTLocalizer.StartingBlock_KickSoloRacer
                    self.dialog = TTGlobalDialog(msg, doneEvent, style=1)
                    self.dialog.accept(doneEvent, handleDialogOK)
                    self.accept('stoppedAsleep', handleDialogOK)
        return

    def __avatarGone(self):
        self.notify.debugStateCall(self)
        self.setOccupied(0)

    def __placeAvatar(self):
        self.notify.debugStateCall(self)
        if not self.placedAvatar:
            self.placedAvatar = 1
            self.av.setPosHpr(0, 0, 0, 0, 0, 0)

    def setMovie(self, mode):
        self.notify.debugStateCall(self)
        if self.avId == 0:
            return
        self.finishMovie()
        if mode == 0:
            pass
        elif mode == KartGlobals.ENTER_MOVIE:
            self.request('EnterMovie')
        elif mode == KartGlobals.EXIT_MOVIE:
            self.request('ExitMovie')

    def makeGui(self):
        self.notify.debugStateCall(self)
        if hasattr(self, 'cancelButton'):
            return
        fishGui = loader.loadModel('phase_4/models/gui/fishingGui')
        self.cancelButton = DirectGui.DirectButton(relief=None, scale=0.67, pos=(1.16, 0, -0.9), text=('', TTLocalizer.FishingExit, TTLocalizer.FishingExit), text_align=TextNode.ACenter, text_fg=Vec4(1, 1, 1, 1), text_shadow=Vec4(0, 0, 0, 1), text_pos=(0.0, -0.12), textMayChange=0, text_scale=0.1, image=(fishGui.find('**/exit_buttonUp'), fishGui.find('**/exit_buttonDown'), fishGui.find('**/exit_buttonRollover')), text_font=ToontownGlobals.getInterfaceFont(), command=self.d_requestExit)
        self.cancelButton.hide()
        return

    def showGui(self):
        self.notify.debugStateCall(self)
        if hasattr(self.kartPad, 'state'):
            if not self.kartPad.state == 'WaitCountdown':
                return
        self.cancelButton.show()

    def hideGui(self):
        self.notify.debugStateCall(self)
        if not hasattr(self, 'cancelButton'):
            return
        self.cancelButton.hide()

    def generateToonMoveTrack(self):
        hpr = self.movieNode.getHpr(render)
        heading = PythonUtil.fitDestAngle2Src(self.av.getH(render), hpr[0])
        hpr.setX(heading)
        self.av.setAnimState('run', 1.0)
        toonTrack = Sequence(Wait(0.5), Parallel(LerpPosInterval(self.av, 1.0, Point3(self.movieNode.getX(self.avParent), self.movieNode.getY(self.avParent), 0)), LerpHprInterval(self.av, 1.0, hpr=hpr, other=render)), Func(self.av.loop, 'neutral'))
        return toonTrack

    def generateKartAppearTrack(self):
        if not self.av:
            if not self.kartNode:
                self.kartNode = render.attachNewNode(str(self) + 'kartNode')
                self.kartNode.setPosHpr(self.nodePath.getPos(render), self.nodePath.getHpr(render))
            self.kart.setScale(0.85)
            self.kart.reparentTo(self.kartNode)
            return Parallel()
        self.kart.setScale(0.1)
        kartTrack = Parallel(
            Sequence(
                ActorInterval(self.av, 'feedPet'),
                Func(self.av.loop, 'neutral')),
            Sequence(
                Func(self.kart.setActiveShadow, False),
                Func(self.kart.reparentTo, self.av.rightHand),
                Wait(2.1),
                Func(self.kart.wrtReparentTo, render),
                Func(self.kart.setShear, 0, 0, 0),
                Parallel(
                    LerpHprInterval(self.kart,  hpr=self.kartNode.getHpr(render), duration=1.2),
                    ProjectileInterval(self.kart, endPos=self.kartNode.getPos(render), duration=1.2, gravityMult=0.45)),
                Wait(0.2),
                Func(self.kart.setActiveShadow, True),
                Sequence(
                    LerpScaleInterval(self.kart, scale=Point3(1.1, 1.1, 0.1), duration=0.2),
                    LerpScaleInterval(self.kart, scale=Point3(0.9, 0.9, 0.1), duration=0.1),
                    LerpScaleInterval(self.kart, scale=Point3(1.0, 1.0, 0.1), duration=0.1),
                    LerpScaleInterval(self.kart, scale=Point3(1.0, 1.0, 1.1), duration=0.2),
                    LerpScaleInterval(self.kart, scale=Point3(1.0, 1.0, 0.9), duration=0.1),
                    LerpScaleInterval(self.kart, scale=Point3(1.0, 1.0, 1.0), duration=0.1),
                    Func(self.kart.wrtReparentTo, self.kartNode))))
        return kartTrack

    def generateToonJumpTrack(self):
        base.sb = self

        def getToonJumpTrack(av, kart):

            def getJumpDest(av = av, node = kart.toonNode[0]):
                dest = node.getPos(av.getParent())
                return dest

            def getJumpHpr(av = av, node = kart.toonNode[0]):
                hpr = node.getHpr(av.getParent())
                return hpr

            toonJumpTrack = Parallel(
                ActorInterval(av, 'jump'),
                Sequence(Wait(0.43),
                         Parallel(
                             LerpHprInterval(av, hpr=getJumpHpr, duration=0.9),
                             ProjectileInterval(av, endPos=getJumpDest, duration=0.9))))
            return toonJumpTrack

        def getToonSitTrack(av):
            toonSitTrack = Sequence(ActorInterval(av, 'sit-start'), Func(av.loop, 'sit'))
            return toonSitTrack

        toonJumpTrack = getToonJumpTrack(self.av, self.kart)
        toonSitTrack = getToonSitTrack(self.av)
        jumpTrack = Sequence(
            Parallel(
                toonJumpTrack,
                Sequence(
                    Wait(1),
                    toonSitTrack)),
                Func(self.av.setPosHpr, 0, 0.45, -.25, 0, 0, 0),
                Func(self.av.reparentTo, self.kart.toonSeat))
        return jumpTrack

    def generateToonReverseJumpTrack(self):

        def getToonJumpTrack(av, destNode):

            def getJumpDest(av = av, node = destNode):
                dest = node.getPos(av.getParent())
                return dest

            def getJumpHpr(av = av, node = destNode):
                hpr = node.getHpr(av.getParent())
                return hpr

            toonJumpTrack = Parallel(ActorInterval(av, 'jump'), Sequence(Wait(0.1), Parallel(LerpHprInterval(av, hpr=getJumpHpr, duration=0.9), ProjectileInterval(av, endPos=getJumpDest, duration=0.9))))
            return toonJumpTrack

        toonJumpTrack = getToonJumpTrack(self.av, self.exitMovieNode)
        jumpTrack = Sequence(toonJumpTrack, Func(self.av.loop, 'neutral'), Func(self.av.reparentTo, render), Func(self.av.setPosHpr, self.exitMovieNode, 0, 0, 0, 0, 0, 0))
        return jumpTrack

    def generateCameraMoveTrack(self):
        self.cPos = camera.getPos(self.av)
        self.cHpr = camera.getHpr(self.av)
        camera.wrtReparentTo(self.nodePath)
        cameraTrack = LerpPosHprInterval(camera, 1.5, self.cameraPos, self.cameraHpr)
        return cameraTrack

    def generateCameraReturnMoveTrack(self):
        cameraTrack = Sequence(Func(camera.wrtReparentTo, self.av), LerpPosHprInterval(camera, 1.5, self.cPos, self.cHpr))
        return cameraTrack

    def generateKartDisappearTrack(self):

        def getHoleTrack(hole, holeParent):
            holeTrack = Sequence(
                Wait(0.2),
                Func(hole.setBin, 'shadow', 0),
                Func(hole.setDepthTest, 0),
                Func(hole.setDepthWrite, 0),
                Func(hole.reparentTo, holeParent),
                Func(hole.setPos, holeParent, Point3(0, 0.0, -.6)),
                ActorInterval(hole, 'hole', startTime=3.4, endTime=3.1),
                Wait(0.4),
                ActorInterval(hole, 'hole', startTime=3.1, endTime=3.4))
            return holeTrack

        def getKartShrinkTrack(kart):
            pos = kart.getPos()
            pos.addZ(-1.0)
            kartTrack = Sequence(LerpScaleInterval(kart, scale=Point3(1.0, 1.0, 0.9), duration=0.1), LerpScaleInterval(kart, scale=Point3(1.0, 1.0, 1.1), duration=0.1), LerpScaleInterval(kart, scale=Point3(1.0, 1.0, 0.1), duration=0.2), LerpScaleInterval(kart, scale=Point3(0.9, 0.9, 0.1), duration=0.1), LerpScaleInterval(kart, scale=Point3(1.1, 1.1, 0.1), duration=0.1), LerpScaleInterval(kart, scale=Point3(0.1, 0.1, 0.1), duration=0.2), Wait(0.2), LerpPosInterval(kart, pos=pos, duration=0.2), Func(kart.hide))
            return kartTrack

        if not self.holeActor:
            self.holeActor = Actor.Actor('phase_3.5/models/props/portal-mod', {'hole': 'phase_3.5/models/props/portal-chan'})
        holeTrack = getHoleTrack(self.holeActor, self.kartNode)
        shrinkTrack = getKartShrinkTrack(self.kart)
        kartTrack = Parallel(shrinkTrack, holeTrack)
        return kartTrack

    def enterOff(self):
        self.notify.debug('%d enterOff: Entering the Off State.' % self.doId)
        self.hideGui()

    def exitOff(self):
        self.notify.debug('%d exitOff: Exiting the Off State.' % self.doId)

    def enterEnterMovie(self):
        self.notify.debug('%d enterEnterMovie: Entering the Enter Movie State.' % self.doId)
        if base.config.GetBool('want-qa-regression', 0):
            raceName = TTLocalizer.KartRace_RaceNames[self.kartPad.trackType]
            self.notify.info('QA-REGRESSION: KARTING: %s' % raceName)
        toonTrack = self.generateToonMoveTrack()
        kartTrack = self.generateKartAppearTrack()
        jumpTrack = self.generateToonJumpTrack()
        name = self.av.uniqueName('EnterRaceTrack')
        if self.av is not None and self.localToonKarting:
            kartAppearSfx = base.loader.loadSfx(self.SFX_KartAppear)
            cameraTrack = self.generateCameraMoveTrack()
            engineStartTrack = self.kart.generateEngineStartTrack()
            self.finishMovie()
            self.movieTrack = Sequence(Parallel(cameraTrack, toonTrack), Parallel(SoundInterval(kartAppearSfx), Sequence(kartTrack, jumpTrack, engineStartTrack, Func(self.makeGui), Func(self.showGui), Func(self.request, 'Waiting'), Func(self.d_movieFinished))), name=name, autoFinish=1)
            self.exitRequested = False
        else:
            self.finishMovie()
            self.movieTrack = Sequence(toonTrack, kartTrack, jumpTrack, name=name, autoFinish=1)
        self.movieTrack.start()
        return

    def exitEnterMovie(self):
        self.notify.debug('%d exitEnterMovie: Exiting the Enter Movie State.' % self.doId)

    def enterWaiting(self):
        self.notify.debug('%d enterWaiting: Entering the Waiting State.' % self.doId)

    def exitWaiting(self):
        self.notify.debug('%d exitWaiting: Exiting the Waiting State.' % self.doId)

    def enterExitMovie(self):
        self.notify.debug('%d enterExitMovie: Entering the Exit Movie State.' % self.doId)
        self.hideGui()
        jumpTrack = self.generateToonReverseJumpTrack()
        kartTrack = self.generateKartDisappearTrack()
        self.finishMovie()
        self.movieTrack = Sequence(Func(self.kart.kartLoopSfx.stop), jumpTrack, kartTrack, name=self.av.uniqueName('ExitRaceTrack'), autoFinish=1)
        if self.av is not None and self.localToonKarting:
            cameraTrack = self.generateCameraReturnMoveTrack()
            self.movieTrack.append(cameraTrack)
            self.movieTrack.append(Func(self.d_movieFinished))
        self.movieTrack.start()
        return

    def exitExitMovie(self):
        self.notify.debug('%d exitExitMovie: Exiting the Exit Movie State.' % self.doId)

    def doExitToRaceTrack(self):
        self.hideGui()
        self.finishMovie()
        oldBlockPos = self.kartNode.getPos(render)
        self.kartNode.setPos(self.kartNode, 0, 40, 0)
        newBlockPos = self.kartNode.getPos(render)
        oldBlockScale = self.kartNode.getScale()
        self.kart.LODnode.setSwitch(0, 60, 0)
        self.kartNode.setPos(render, oldBlockPos)
        blockLerpIval = LerpPosInterval(self.kartNode, pos=newBlockPos, duration=2.0)
        scaleLerpIval = LerpScaleInterval(self.kartNode, scale=oldBlockScale * 0.2, duration=2.0)
        engineStopTrack = self.kart.generateEngineStopTrack(2)
        self.finishMovie()
        self.movieTrack = Parallel()
        if self.av == base.localAvatar:
            self.movieTrack.insert(0, Func(base.transitions.irisOut, 1.5, 0))
            (self.movieTrack.append(engineStopTrack),)
            taskMgr.doMethodLater(1.6, self.bulkLoad, 'loadIt', extraArgs=[])
        self.movieTrack.append(Sequence(Parallel(blockLerpIval, scaleLerpIval), Func(self.kartNode.hide), Func(self.kartNode.setPos, render, oldBlockPos), Func(self.kartNode.setScale, oldBlockScale)))
        self.movieTrack.start()

    def bulkLoad(self):
        base.loader.beginBulkLoad('atRace', TTLocalizer.StartingBlock_Loading, 60, 1, TTLocalizer.TIP_KARTING)


class DistributedViewingBlock(DistributedStartingBlock):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedViewingBlock')
    sphereRadius = 6

    def __init__(self, cr):
        DistributedStartingBlock.__init__(self, cr)
        self.timer = None
        return

    def delete(self):
        if self.timer is not None:
            self.timer.destroy()
            del self.timer
        DistributedStartingBlock.delete(self)
        return

    def generateInit(self):
        self.notify.debugStateCall(self)
        DistributedObject.DistributedObject.generateInit(self)
        self.nodePath = NodePath(self.uniqueName('StartingBlock'))
        self.collSphere = CollisionSphere(-1, 6.75, -1, self.sphereRadius)
        self.collSphere.setTangible(0)
        self.collNode = CollisionNode(self.uniqueName('StartingBlockSphere'))
        self.collNode.setCollideMask(ToontownGlobals.WallBitmask)
        self.collNode.addSolid(self.collSphere)
        self.collNodePath = self.nodePath.attachNewNode(self.collNode)

    def announceGenerate(self):
        self.notify.debugStateCall(self)
        DistributedObject.DistributedObject.announceGenerate(self)
        self.nodePath.reparentTo(render)
        self.accept(self.uniqueName('enterStartingBlockSphere'), self.__handleEnterSphere)
        if (__debug__):
            if self.testLOD:
                self.__generateKartAppearTrack()

    def setPadLocationId(self, padLocationId):
        self.notify.debugStateCall(self)
        self.movieNode = self.nodePath.attachNewNode(self.uniqueName('MovieNode'))
        self.exitMovieNode = self.nodePath.attachNewNode(self.uniqueName('ExitMovieNode'))
        if padLocationId % 2:
            self.movieNode.setPosHpr(0, 6.5, 0, 0, 0, 0)
        else:
            self.movieNode.setPosHpr(0, -6.5, 0, 0, 0, 0)
        self.exitMovieNode.setPosHpr(3, 6.5, 0, 270, 0, 0)
        self.collNodePath.reparentTo(self.movieNode)

    def __handleEnterSphere(self, collEntry):
        if base.localAvatar.doId == self.lastAvId and globalClock.getFrameCount() <= self.lastFrame + 1:
            self.notify.debug('Ignoring duplicate entry for avatar.')
            return
        if base.localAvatar.hp > 0:

            def handleEnterRequest(self = self):
                self.ignore('stoppedAsleep')
                if hasattr(self.dialog, 'doneStatus') and self.dialog.doneStatus == 'ok':
                    self.d_requestEnter(base.cr.isPaid())
                else:
                    self.cr.playGame.getPlace().setState('walk')
                self.dialog.ignoreAll()
                self.dialog.cleanup()
                del self.dialog

            self.cr.playGame.getPlace().fsm.request('stopped')
            self.accept('stoppedAsleep', handleEnterRequest)
            doneEvent = 'enterRequest|dialog'
            msg = TTLocalizer.StartingBlock_EnterShowPad
            self.dialog = TTGlobalDialog(msg, doneEvent, 4)
            self.dialog.accept(doneEvent, handleEnterRequest)

    def generateCameraMoveTrack(self):
        self.cPos = camera.getPos(self.av)
        self.cHpr = camera.getHpr(self.av)
        cameraPos = Point3(23, -10, 7)
        cameraHpr = Point3(65, -10, 0)
        camera.wrtReparentTo(self.nodePath)
        cameraTrack = LerpPosHprInterval(camera, 1.5, cameraPos, cameraHpr)
        return cameraTrack

    def makeGui(self):
        self.notify.debugStateCall(self)
        if self.timer is not None:
            return
        self.timer = ToontownTimer()
        self.timer.setScale(0.3)
        self.timer.setPos(1.16, 0, -.73)
        self.timer.hide()
        DistributedStartingBlock.makeGui(self)
        return

    def showGui(self):
        self.notify.debugStateCall(self)
        self.timer.show()
        DistributedStartingBlock.showGui(self)

    def hideGui(self):
        self.notify.debugStateCall(self)
        if not hasattr(self, 'timer') or self.timer is None:
            return
        self.timer.reset()
        self.timer.hide()
        DistributedStartingBlock.hideGui(self)
        return

    def countdown(self):
        countdownTime = KartGlobals.COUNTDOWN_TIME - globalClockDelta.localElapsedTime(self.kartPad.getTimestamp(self.avId))
        self.timer.countdown(countdownTime)

    def enterEnterMovie(self):
        self.notify.debug('%d enterEnterMovie: Entering the Enter Movie State.' % self.doId)
        if base.config.GetBool('want-qa-regression', 0):
            raceName = TTLocalizer.KartRace_RaceNames[self.kartPad.trackType]
            self.notify.info('QA-REGRESSION: KARTING: %s' % raceName)
        pos = self.nodePath.getPos(render)
        hpr = self.nodePath.getHpr(render)
        pos.addZ(1.7)
        hpr.addX(270)
        self.kartNode.setPosHpr(pos, hpr)
        toonTrack = self.generateToonMoveTrack()
        kartTrack = self.generateKartAppearTrack()
        jumpTrack = self.generateToonJumpTrack()
        name = self.av.uniqueName('EnterRaceTrack')
        if self.av is not None and self.localToonKarting:
            cameraTrack = self.generateCameraMoveTrack()
            self.finishMovie()
            self.movieTrack = Sequence(Parallel(cameraTrack, Sequence()), kartTrack, jumpTrack, Func(self.makeGui), Func(self.showGui), Func(self.countdown), Func(self.request, 'Waiting'), Func(self.d_movieFinished), name=name, autoFinish=1)
        else:
            self.finishMovie()
            self.movieTrack = Sequence(toonTrack, kartTrack, jumpTrack, name=name, autoFinish=1)
        self.movieTrack.start()
        self.exitRequested = True
        return
