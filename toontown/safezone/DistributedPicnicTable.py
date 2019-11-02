from pandac.PandaModules import *
from direct.distributed.ClockDelta import *
from direct.task.Task import Task
from direct.interval.IntervalGlobal import *
from TrolleyConstants import *
from direct.gui.DirectGui import *
from toontown.toonbase import TTLocalizer
from direct.distributed import DistributedNode
from direct.distributed.ClockDelta import globalClockDelta
from ChineseCheckersBoard import ChineseCheckersBoard
from GameTutorials import *
from GameMenu import GameMenu
from direct.fsm import ClassicFSM, State
from direct.fsm import StateData
from toontown.distributed import DelayDelete
from toontown.toonbase.ToontownTimer import ToontownTimer
from toontown.toonbase import ToontownGlobals
from direct.showbase import PythonUtil
from otp.otpbase import OTPGlobals

class DistributedPicnicTable(DistributedNode.DistributedNode):

    def __init__(self, cr):
        self.cr = cr
        NodePath.__init__(self, 'DistributedPicnicTable')
        DistributedNode.DistributedNode.__init__(self, cr)
        self.reparentTo(render)
        self.picnicTable = loader.loadModel('phase_6/models/golf/game_table.bam')
        self.picnicTable.reparentTo(self)
        self.picnicTableSphereNodes = []
        self.numSeats = 6
        self.seats = []
        self.jumpOffsets = []
        self.inGame = False
        self.requestSeat = None
        self.gameState = None
        self.cameraBoardTrack = Func(self.doNothing)
        self.seatBumpForObserve = 0
        self.winTrack = Sequence()
        self.outTrack = Sequence()
        self.joinButton = None
        self.observeButton = None
        self.tutorialButton = None
        self.exitButton = None
        self.isPlaying = False
        self.gameMenu = None
        self.game = None
        self.gameZone = None
        self.tutorial = None
        self.timerFunc = None
        self.gameDoId = None
        self.gameWantTimer = False
        self.tableState = [None,
         None,
         None,
         None,
         None,
         None]
        self.haveAnimated = []
        self.winSound = base.loadSfx('phase_6/audio/sfx/KART_Applause_1.mp3')
        self.happyDance = base.loadSfx('phase_5/audio/sfx/AA_heal_happydance.mp3')
        self.accept('stoppedAsleep', self.handleSleep)
        base.localAvatar.startSleepWatch(self.handleSleep)
        self.__toonTracks = {}
        self.fsm = ClassicFSM.ClassicFSM('PicnicTable', [State.State('off', self.enterOff, self.exitOff, ['chooseMode', 'observing']),
         State.State('chooseMode', self.enterChooseMode, self.exitChooseMode, ['sitting', 'off', 'observing']),
         State.State('sitting', self.enterSitting, self.exitSitting, ['off']),
         State.State('observing', self.enterObserving, self.exitObserving, ['off'])], 'off', 'off')
        self.fsm.enterInitialState()
        for i in range(self.numSeats):
            self.seats.append(self.picnicTable.find('**/*seat%d' % (i + 1)))
            self.jumpOffsets.append(self.picnicTable.find('**/*jumpOut%d' % (i + 1)))

        self.tableCloth = self.picnicTable.find('**/basket_locator')
        self.tableclothSphereNode = self.tableCloth.attachNewNode(CollisionNode('tablecloth_sphere'))
        self.tableclothSphereNode.node().addSolid(CollisionSphere(0, 0, -2, 5.5))
        self.clockNode = ToontownTimer()
        self.clockNode.setPos(1.16, 0, -0.83)
        self.clockNode.setScale(0.3)
        self.clockNode.hide()
        return

    def announceGenerate(self):
        DistributedNode.DistributedNode.announceGenerate(self)
        for i in range(self.numSeats):
            self.picnicTableSphereNodes.append(self.seats[i].attachNewNode(CollisionNode('picnicTable_sphere_%d_%d' % (self.getDoId(), i))))
            self.picnicTableSphereNodes[i].node().addSolid(CollisionSphere(0, 0, 0, 2))

        self.tableState = [None,
         None,
         None,
         None,
         None,
         None]
        self.requestTableState()
        self.buttonModels = loader.loadModel('phase_3.5/models/gui/inventory_gui')
        self.upButton = self.buttonModels.find('**//InventoryButtonUp')
        self.downButton = self.buttonModels.find('**/InventoryButtonDown')
        self.rolloverButton = self.buttonModels.find('**/InventoryButtonRollover')
        angle = self.getH()
        angle -= 90
        radAngle = deg2Rad(angle)
        unitVec = Vec3(math.cos(radAngle), math.sin(radAngle), 0)
        unitVec *= 30.0
        self.endPos = self.getPos() + unitVec
        dist = Vec3(self.endPos - self.getPos()).length()
        wheelAngle = dist / (0.5 * 1.4 * math.pi) * 360
        self.__enableCollisions()
        return

    def handleSleep(self, task = None):
        if self.fsm.getCurrentState().getName() == 'chooseMode':
            self.cancelButtonPushed()
        elif self.fsm.getCurrentState().getName() == 'sitting':
            self.sendUpdate('requestExit', [])
        if self.gameMenu != None:
            self.gameMenu.removeButtons()
            self.gameMenu.picnicFunction = None
            self.gameMenu = None
        if task != None:
            task.done
        return

    def disable(self):
        DistributedNode.DistributedNode.disable(self)
        self.ignore('stoppedAsleep')
        self.clearToonTracks()
        self.__disableCollisions()
        self.disableChoiceButtons()
        self.picnicTable.removeNode()
        self.cameraBoardTrack = None
        return

    def delete(self):
        self.__disableCollisions()
        self.ignore('stoppedAsleep')
        DistributedNode.DistributedNode.delete(self)
        self.disableChoiceButtons()
        self.cameraBoardTrack = None
        del self.winTrack
        del self.outTrack
        self.fsm = None
        self.gameZone = None
        self.clearToonTracks()
        self.cameraBoardTrack = None
        return

    def setName(self, name):
        self.name = name

    def setGameDoId(self, doId):
        self.gameDoId = doId
        self.game = self.cr.doId2do[doId]
        self.game.setHpr(self.getHpr())
        self.gameWantTimer = self.game.wantTimer
        if self.gameState == 1:
            self.game.fsm.request('playing')

    def setTimerFunc(self, function):
        self.timerFunc = function

    def setTimer(self, timerEnd):
        self.clockNode.stop()
        time = globalClockDelta.networkToLocalTime(timerEnd)
        self.timeLeft = int(time - globalClock.getRealTime())
        if self.gameWantTimer and self.game != None:
            self.showTimer()
        return

    def showTimer(self):
        self.clockNode.stop()
        self.clockNode.countdown(self.timeLeft, self.timerFunc)
        self.clockNode.show()

    def requestTableState(self):
        self.sendUpdate('requestTableState', [])

    def setTableState(self, tableStateList, isplaying):
        y = 0
        print 'SET TABLE STATE'
        if isplaying == 0:
            self.isPlaying = False
        else:
            self.isPlaying = True
        for x in tableStateList:
            if x != 0:
                if x not in self.tableState and self.cr.doId2do.has_key(x) and x not in self.haveAnimated:
                    seatIndex = tableStateList.index(x)
                    toon = self.cr.doId2do[x]
                    toon.stopSmooth()
                    toon.setAnimState('Sit', 1.0)
                    dest = self.seats[seatIndex].getPos(self.tableCloth)
                    hpr = self.seats[seatIndex].getHpr(render)
                    toon.setHpr(hpr)
                    if seatIndex > 2:
                        toon.setH(self.getH() + 180)
                    toon.wrtReparentTo(self)
                    toon.setPos(dest)
                    toon.setZ(toon.getZ() + 1.35)
                    if seatIndex > 2:
                        toon.setY(toon.getY() - 1.0)
                    else:
                        toon.setY(toon.getY() + 1.0)
            if x != 0:
                self.tableState[y] = x
            else:
                self.tableState[y] = None
            y = y + 1

        numPlayers = 0
        for x in self.tableState:
            if x != None:
                numPlayers += 1

        print ' GETTING 2', self.gameMenu, numPlayers
        if self.gameMenu:
            if numPlayers > 2:
                print ' GETTING HERE!!'
                self.gameMenu.FindFour.setColor(0.7, 0.7, 0.7, 0.7)
                self.gameMenu.FindFour['command'] = self.doNothing
                self.gameMenu.findFourText['fg'] = (0.7, 0.7, 0.7, 0.7)
                self.gameMenu.Checkers.setColor(0.7, 0.7, 0.7, 0.7)
                self.gameMenu.Checkers['command'] = self.doNothing
                self.gameMenu.checkersText['fg'] = (0.7, 0.7, 0.7, 0.7)
        return

    def setIsPlaying(self, isPlaying):
        if isPlaying == 0:
            self.isPlaying = False
        elif isPlaying == 1:
            self.isPlaying = True

    def announceWinner(self, winString, avId):
        if avId == base.localAvatar.getDoId():
            sound = Sequence(Wait(2.0), Parallel(SoundInterval(self.winSound), SoundInterval(self.happyDance)))
            sound.start()
            base.cr.playGame.getPlace().setState('walk')
            if winString == 'Chinese Checkers':
                whisper = WhisperPopup(TTLocalizer.ChineseCheckersYouWon, OTPGlobals.getInterfaceFont(), WhisperPopup.WTNormal)
            elif winString == 'Checkers':
                whisper = WhisperPopup(TTLocalizer.RegularCheckersYouWon, OTPGlobals.getInterfaceFont(), WhisperPopup.WTNormal)
            elif winString == 'Find Four':
                whisper = WhisperPopup('You won a game of Find Four!', OTPGlobals.getInterfaceFont(), WhisperPopup.WTNormal)
        elif self.cr.doId2do.has_key(avId):
            stateString = self.fsm.getCurrentState().getName()
            if stateString == 'sitting' or stateString == 'observing':
                base.cr.playGame.getPlace().setState('walk')
            av = self.cr.doId2do[avId]
            if winString == 'Chinese Checkers':
                whisper = WhisperPopup(av.getName() + TTLocalizer.ChineseCheckersGameOf + TTLocalizer.ChineseCheckers, OTPGlobals.getInterfaceFont(), WhisperPopup.WTNormal)
            elif winString == 'Checkers':
                whisper = WhisperPopup(av.getName() + TTLocalizer.RegularCheckersGameOf + TTLocalizer.RegularCheckers, OTPGlobals.getInterfaceFont(), WhisperPopup.WTNormal)
            elif winString == 'Find Four':
                whisper = WhisperPopup(av.getName() + ' has won a game of' + ' Find Four!', OTPGlobals.getInterfaceFont(), WhisperPopup.WTNormal)
        if self.cr.doId2do.has_key(avId):
            toon = self.cr.doId2do[avId]
            self.winTrack = Sequence(autoFinish=1)
            if self.outTrack.isPlaying():
                self.winTrack.append(Wait(2.0))
            if avId == base.localAvatar.getDoId():
                self.winTrack.append(Func(self.stopToWalk))
            self.winTrack.append(ActorInterval(toon, 'happy-dance'))
            if avId == base.localAvatar.getDoId():
                self.winTrack.append(Func(self.allowToWalk))
            self.winTrack.start()
        whisper.manage(base.marginManager)

    def handleEnterPicnicTableSphere(self, i, collEntry):
        self.notify.debug('Entering Picnic Table Sphere.... %s' % self.getDoId())
        self.requestSeat = i
        self.seatBumpForObserve = i
        self.fsm.request('chooseMode')

    def enableChoiceButtons(self):
        if self.tableState[self.seatBumpForObserve] == None and self.isPlaying == False:
            self.joinButton = DirectButton(
                relief=None,
                text=TTLocalizer.PicnicTableJoinButton,
                text_fg=(1, 1, 0.65, 1),
                text_pos=(0, -.23),
                text_scale=0.8,
                image=(self.upButton, self.downButton, self.rolloverButton),
                image_color=(1, 0, 0, 1),
                image_scale=(20, 1, 11),
                pos=(0, 0, 0.8),
                scale=0.15,
                command=lambda self = self: self.joinButtonPushed())
        if self.isPlaying == True:
            self.observeButton = DirectButton(
                relief=None,
                text=TTLocalizer.PicnicTableObserveButton,
                text_fg=(1, 1, 0.65, 1),
                text_pos=(0, -.23),
                text_scale=0.8,
                image=(self.upButton, self.downButton, self.rolloverButton),
                image_color=(1, 0, 0, 1),
                image_scale=(20, 1, 11),
                pos=(0, 0, 0.6),
                scale=0.15,
                command=lambda self = self: self.observeButtonPushed())
        self.exitButton = DirectButton(
            relief=None,
            text=TTLocalizer.PicnicTableCancelButton,
            text_fg=(1, 1, 0.65, 1),
            text_pos=(0, -.23),
            text_scale=0.8,
            image=(self.upButton, self.downButton, self.rolloverButton),
            image_color=(1, 0, 0, 1),
            image_scale=(20, 1, 11),
            pos=(1, 0, 0.6),
            scale=0.15,
            command=lambda self = self: self.cancelButtonPushed())
        self.tutorialButton = DirectButton(
            relief=None,
            text=TTLocalizer.PicnicTableTutorial,
            text_fg=(1, 1, 0.65, 1),
            text_pos=(-.05, -.13),
            text_scale=0.55,
            image=(self.upButton, self.downButton, self.rolloverButton),
            image_color=(1, 0, 0, 1),
            image_scale=(20, 1, 11),
            pos=(-1, 0, 0.6),
            scale=0.15,
            command=lambda self = self: self.tutorialButtonPushed())
        base.cr.playGame.getPlace().setState('stopped')
        return

    def tutorialButtonPushed(self):
        self.disableChoiceButtons()
        self.gameMenu = GameMenu(self.tutorialFunction, 1)
        self.tutorialButton.destroy()
        self.tutorialButton = None
        return

    def tutorialFunction(self, tutVal):
        if tutVal == 1:
            self.tutorial = ChineseTutorial(self.tutorialDone)
        elif tutVal == 2:
            self.tutorial = CheckersTutorial(self.tutorialDone)
        self.gameMenu.picnicFunction = None
        self.gameMenu = None
        return

    def tutorialDone(self):
        self.requestSeat = None
        self.fsm.request('off')
        self.tutorial = None
        return

    def joinButtonPushed(self):
        toon = base.localAvatar
        self.sendUpdate('requestJoin', [self.requestSeat,
         toon.getX(),
         toon.getY(),
         toon.getZ(),
         toon.getH(),
         toon.getP(),
         toon.getR()])
        self.requestSeat = None
        self.fsm.request('sitting')
        return

    def rejectJoin(self):
        self.fsm.request('off')
        self.allowToWalk()

    def cancelButtonPushed(self):
        base.cr.playGame.getPlace().setState('walk')
        self.requestSeat = None
        self.fsm.request('off')
        return

    def disableChoiceButtons(self):
        if self.joinButton:
            self.joinButton.destroy()
        if self.observeButton:
            self.observeButton.destroy()
        if self.exitButton:
            self.exitButton.destroy()
        if self.tutorialButton:
            self.tutorialButton.destroy()

    def pickFunction(self, gameNum):
        if gameNum == 1:
            self.sendUpdate('requestPickedGame', [gameNum])
        elif gameNum == 2:
            self.sendUpdate('requestPickedGame', [gameNum])
        elif gameNum == 3:
            self.sendUpdate('requestPickedGame', [gameNum])

    def allowPick(self):
        self.gameMenu = GameMenu(self.pickFunction, 2)

    def setZone(self, zoneId):
        if self.fsm.getCurrentState().getName() == 'sitting' or self.fsm.getCurrentState().getName() == 'observing':
            if self.tutorial == None:
                self.gameZone = base.cr.addInterest(base.localAvatar.defaultShard, zoneId, 'gameBoard')
                if self.gameMenu != None:
                    self.gameMenu.removeButtons()
                    self.gameMenu.picnicFunction = None
                    self.gameMenu = None
        return

    def fillSlot(self, avId, index, x, y, z, h, p, r, timestamp, parentDoId):
        self.notify.debug('fill Slot: %d for %d' % (index, avId))
        if avId not in self.haveAnimated:
            self.haveAnimated.append(avId)
        if avId == base.localAvatar.getDoId():
            if self.inGame == True:
                return
            else:
                self.inGame = True
                self.seatPos = index
        if self.cr.doId2do.has_key(avId):
            toon = self.cr.doId2do[avId]
            toon.stopSmooth()
            toon.wrtReparentTo(self.tableCloth)
            sitStartDuration = toon.getDuration('sit-start')
            jumpTrack = self.generateToonJumpTrack(toon, index)
            track = Sequence(autoFinish=1)
            if avId == base.localAvatar.getDoId():
                if not base.cr.playGame.getPlace() == None:
                    self.moveCamera(index)
                    track.append(Func(self.__disableCollisions))
            track.append(jumpTrack)
            track.append(Func(toon.setAnimState, 'Sit', 1.0))
            track.append(Func(self.clearToonTrack, avId))
            self.storeToonTrack(avId, track)
            track.start()
        return

    def emptySlot(self, avId, index, timestamp):
        self.notify.debug('### seat %s now empty' % index)
        if index == 255 and self.game != None:
            self.stopObserveButtonPushed()
            return
        if avId in self.haveAnimated:
            self.haveAnimated.remove(avId)
        if self.cr.doId2do.has_key(avId):
            if avId == base.localAvatar.getDoId():
                if self.gameZone:
                    base.cr.removeInterest(self.gameZone)
                if self.inGame == True:
                    self.inGame = False
                else:
                    return
            toon = self.cr.doId2do[avId]
            toon.stopSmooth()
            sitStartDuration = toon.getDuration('sit-start')
            jumpOutTrack = self.generateToonReverseJumpTrack(toon, index)
            self.outTrack = Sequence(jumpOutTrack)
            if base.localAvatar.getDoId() == avId:
                self.outTrack.append(Func(self.__enableCollisions))
                self.outTrack.append(Func(self.allowToWalk))
                self.fsm.request('off')
            val = self.jumpOffsets[index].getPos(render)
            self.outTrack.append(Func(toon.setPos, val))
            self.outTrack.append(Func(toon.startSmooth))
            self.outTrack.start()
        return

    def stopToWalk(self):
        base.cr.playGame.getPlace().setState('stopped')

    def allowToWalk(self):
        base.cr.playGame.getPlace().setState('walk')

    def moveCamera(self, seatIndex):
        self.oldCameraPos = camera.getPos()
        self.oldCameraHpr = camera.getHpr()
        camera.wrtReparentTo(self.picnicTable)
        heading = PythonUtil.fitDestAngle2Src(camera.getH(), 90)
        if seatIndex < 3:
            self.cameraBoardTrack = LerpPosHprInterval(camera, 2.0, Point3(0, 0, 17), Point3(0, -90, 0))
        elif camera.getH() < 0:
            self.cameraBoardTrack = LerpPosHprInterval(camera, 2.0, Point3(0, 0, 17), Point3(-180, -90, 0))
        else:
            self.cameraBoardTrack = LerpPosHprInterval(camera, 2.0, Point3(0, 0, 17), Point3(180, -90, 0))
        self.cameraBoardTrack.start()

    def moveCameraBack(self):
        self.cameraBoardTrack = LerpPosHprInterval(camera, 2.5, self.oldCameraPos, self.oldCameraHpr)
        self.cameraBoardTrack.start()

    def __enableCollisions(self):
        for i in range(self.numSeats):
            self.accept('enterpicnicTable_sphere_%d_%d' % (self.getDoId(), i), self.handleEnterPicnicTableSphere, [i])
            self.picnicTableSphereNodes[i].setCollideMask(ToontownGlobals.WallBitmask)

        self.tableclothSphereNode.setCollideMask(ToontownGlobals.WallBitmask)

    def __disableCollisions(self):
        for i in range(self.numSeats):
            self.ignore('enterpicnicTable_sphere_%d_%d' % (self.getDoId(), i))
            self.ignore('enterPicnicTableOK_%d_%d' % (self.getDoId(), i))

        for i in range(self.numSeats):
            self.picnicTableSphereNodes[i].setCollideMask(BitMask32(0))

        self.tableclothSphereNode.setCollideMask(BitMask32(0))

    def enterOff(self):
        base.setCellsAvailable(base.leftCells + base.bottomCells, 0)

    def exitOff(self):
        base.setCellsAvailable(base.bottomCells, 0)

    def enterChooseMode(self):
        self.winTrack = Sequence(autoFinish=1)
        self.enableChoiceButtons()

    def exitChooseMode(self):
        self.disableChoiceButtons()

    def enterObserving(self):
        self.enableStopObserveButton()
        self.moveCamera(self.seatBumpForObserve)
        self.sendUpdate('requestGameZone')

    def exitObserving(self):
        if self.cameraBoardTrack.isPlaying():
            self.cameraBoardTrack.pause()
        self.allowToWalk()
        self.stopObserveButton.destroy()

    def enterSitting(self):
        pass

    def exitSitting(self):
        self.gameMenu = None
        return

    def setGameZone(self, zoneId, gamestate):
        self.gameZone = base.cr.addInterest(base.localAvatar.defaultShard, zoneId, 'gameBoard')
        self.gameState = gamestate

    def observeButtonPushed(self):
        self.requestSeat = None
        self.fsm.request('observing')
        return

    def enableStopObserveButton(self):
        self.stopObserveButton = DirectButton(
            relief=None,
            text='Stop Observing',
            text_fg=(1, 1, 0.65, 1),
            text_pos=(0, -.23),
            text_scale=0.45,
            image=(self.upButton, self.downButton, self.rolloverButton),
            image_color=(1, 0, 0, 1),
            image_scale=(20, 1, 11),
            pos=(0.92, 0, 0.4),
            scale=0.15,
            command=lambda self = self: self.stopObserveButtonPushed())
        return

    def stopObserveButtonPushed(self):
        self.sendUpdate('leaveObserve', [])
        self.gameState = None
        if self.game:
            self.game.fsm.request('gameOver')
            base.cr.removeInterest(self.gameZone)
        self.fsm.request('off')
        return

    def generateToonReverseJumpTrack(self, av, seatIndex):
        self.notify.debug('av.getH() = %s' % av.getH())

        def getToonJumpTrack(av, destNode):

            def getJumpDest(av = av, node = destNode):
                dest = node.getPos(self.tableCloth)
                dest += self.jumpOffsets[seatIndex].getPos(self.tableCloth)
                return dest

            def getJumpHpr(av = av, node = destNode):
                hpr = node.getHpr(av.getParent())
                hpr.setX(hpr.getX() + 180)
                angle = PythonUtil.fitDestAngle2Src(av.getH(), hpr.getX())
                hpr.setX(angle)
                return hpr

            toonJumpTrack = Parallel(ActorInterval(av, 'jump'), Sequence(Wait(0.1), Parallel(ProjectileInterval(av, endPos=getJumpDest, duration=0.9))))
            return toonJumpTrack

        toonJumpTrack = getToonJumpTrack(av, self.tableCloth)
        jumpTrack = Sequence(toonJumpTrack, Func(av.loop, 'neutral'), Func(av.wrtReparentTo, render))
        return jumpTrack

    def generateToonJumpTrack(self, av, seatIndex):
        av.pose('sit', 47)
        hipOffset = av.getHipsParts()[2].getPos(av)

        def getToonJumpTrack(av, seatIndex):

            def getJumpDest(av = av, node = self.tableCloth):
                dest = Vec3(self.tableCloth.getPos(av.getParent()))
                seatNode = self.picnicTable.find('**/seat' + str(seatIndex + 1))
                dest += seatNode.getPos(self.tableCloth)
                dna = av.getStyle()
                dest -= hipOffset
                if seatIndex > 2:
                    dest.setY(dest.getY() - 2.0)
                if seatIndex == 1:
                    dest.setY(dest.getY() - 0.5)
                dest.setZ(dest.getZ() + 0.2)
                return dest

            def getJumpHpr(av = av, node = self.tableCloth):
                hpr = self.seats[seatIndex].getHpr(av.getParent())
                if seatIndex < 3:
                    hpr.setX(hpr.getX())
                elif av.getH() < 0:
                    hpr.setX(hpr.getX() - 180)
                else:
                    hpr.setX(hpr.getX() + 180)
                return hpr

            toonJumpTrack = Parallel(ActorInterval(av, 'jump'), Sequence(Wait(0.43), Parallel(LerpHprInterval(av, hpr=getJumpHpr, duration=1), ProjectileInterval(av, endPos=getJumpDest, duration=1))))
            return toonJumpTrack

        def getToonSitTrack(av):
            toonSitTrack = Sequence(ActorInterval(av, 'sit-start'), Func(av.loop, 'sit'))
            return toonSitTrack

        toonJumpTrack = getToonJumpTrack(av, seatIndex)
        toonSitTrack = getToonSitTrack(av)
        jumpTrack = Sequence(Parallel(toonJumpTrack, Sequence(Wait(1), toonSitTrack)), Func(av.wrtReparentTo, self.tableCloth))
        return jumpTrack

    def storeToonTrack(self, avId, track):
        self.clearToonTrack(avId)
        self.__toonTracks[avId] = track

    def clearToonTrack(self, avId):
        oldTrack = self.__toonTracks.get(avId)
        if oldTrack:
            oldTrack.pause()
            cleanupDelayDeletes(oldTrack)

    def clearToonTracks(self):
        keyList = []
        for key in self.__toonTracks:
            keyList.append(key)

        for key in keyList:
            if self.__toonTracks.has_key(key):
                self.clearToonTrack(key)

    def doNothing(self):
        pass
