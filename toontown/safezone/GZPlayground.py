from pandac.PandaModules import *
from toontown.toonbase import ToontownGlobals
import Playground
from toontown.launcher import DownloadForceAcknowledge
from toontown.building import Elevator
from toontown.toontowngui import TTDialog
from toontown.toonbase import TTLocalizer
from toontown.racing import RaceGlobals
from direct.fsm import State
from toontown.safezone import GolfKart

class GZPlayground(Playground.Playground):

    def __init__(self, loader, parentFSM, doneEvent):
        Playground.Playground.__init__(self, loader, parentFSM, doneEvent)
        self.parentFSM = parentFSM
        self.golfKartBlockDoneEvent = 'golfKartBlockDone'
        self.fsm.addState(State.State('golfKartBlock', self.enterGolfKartBlock, self.exitGolfKartBlock, ['walk']))
        state = self.fsm.getStateNamed('walk')
        state.addTransition('golfKartBlock')
        self.golfKartDoneEvent = 'golfKartDone'

    def load(self):
        Playground.Playground.load(self)
        self.hub = loader.loadModel('phase_6/models/golf/golf_hub2')
        self.hub.reparentTo(render)
        self.dnaroot = render.find('**/goofy_speedway_DNARoot')
        self.dnaroot = base.cr.playGame.hood.loader.geom.find('**/goofy_speedway_DNARoot')
        if not self.dnaroot.isEmpty():
            self.dnaroot.removeNode()

    def unload(self):
        Playground.Playground.unload(self)
        self.hub.removeNode()

    def enter(self, requestStatus):
        Playground.Playground.enter(self, requestStatus)
        blimp = base.cr.playGame.hood.loader.geom.find('**/GS_blimp')
        if blimp.isEmpty():
            return
        blimp.setPos(-70, 250, -70)
        blimpBase = NodePath('blimpBase')
        blimpBase.setPos(0, -200, 25)
        blimpBase.setH(-40)
        blimp.reparentTo(blimpBase)
        blimpRoot = NodePath('blimpRoot')
        blimpRoot.setPos(0, -70, 40)
        blimpRoot.reparentTo(base.cr.playGame.hood.loader.geom)
        blimpBase.reparentTo(blimpRoot)
        self.rotateBlimp = blimpRoot.hprInterval(360, Vec3(360, 0, 0))
        self.rotateBlimp.loop()

    def exit(self):
        Playground.Playground.exit(self)
        if hasattr(self, 'rotateBlimp'):
            self.rotateBlimp.finish()

    def doRequestLeave(self, requestStatus):
        self.fsm.request('trialerFA', [requestStatus])

    def enterDFA(self, requestStatus):
        doneEvent = 'dfaDoneEvent'
        self.accept(doneEvent, self.enterDFACallback, [requestStatus])
        self.dfa = DownloadForceAcknowledge.DownloadForceAcknowledge(doneEvent)
        if requestStatus['hoodId'] == ToontownGlobals.MyEstate:
            self.dfa.enter(base.cr.hoodMgr.getPhaseFromHood(ToontownGlobals.MyEstate))
        else:
            self.dfa.enter(5)

    def enterTeleportIn(self, requestStatus):
        reason = requestStatus.get('reason')
        if reason == RaceGlobals.Exit_Barrier:
            requestStatus['nextState'] = 'popup'
            self.dialog = TTDialog.TTDialog(text=TTLocalizer.KartRace_RaceTimeout, command=self.__cleanupDialog, style=TTDialog.Acknowledge)
        elif reason == RaceGlobals.Exit_Slow:
            requestStatus['nextState'] = 'popup'
            self.dialog = TTDialog.TTDialog(text=TTLocalizer.KartRace_RacerTooSlow, command=self.__cleanupDialog, style=TTDialog.Acknowledge)
        elif reason == RaceGlobals.Exit_BarrierNoRefund:
            requestStatus['nextState'] = 'popup'
            self.dialog = TTDialog.TTDialog(text=TTLocalizer.KartRace_RaceTimeoutNoRefund, command=self.__cleanupDialog, style=TTDialog.Acknowledge)
        Playground.Playground.enterTeleportIn(self, requestStatus)

    def __cleanupDialog(self, value):
        if self.dialog:
            self.dialog.cleanup()
            self.dialog = None
        if hasattr(self, 'fsm'):
            self.fsm.request('walk', [1])
        return

    def enterGolfKartBlock(self, golfKart):
        base.localAvatar.laffMeter.start()
        base.localAvatar.b_setAnimState('off', 1)
        self.accept(self.golfKartDoneEvent, self.handleGolfKartDone)
        self.trolley = GolfKart.GolfKart(self, self.fsm, self.golfKartDoneEvent, golfKart.getDoId())
        self.trolley.load()
        self.trolley.enter()

    def exitGolfKartBlock(self):
        base.localAvatar.laffMeter.stop()
        self.ignore(self.trolleyDoneEvent)
        self.trolley.unload()
        self.trolley.exit()
        del self.trolley

    def detectedGolfKartCollision(self, golfKart):
        self.notify.debug('detectedGolfkartCollision()')
        self.fsm.request('golfKartBlock', [golfKart])

    def handleStartingBlockDone(self, doneStatus):
        self.notify.debug('handling StartingBlock done event')
        where = doneStatus['where']
        if where == 'reject':
            self.fsm.request('walk')
        elif where == 'exit':
            self.fsm.request('walk')
        elif where == 'racetrack':
            print 'Entering Racetrack'
            self.doneStatus = doneStatus
            messenger.send(self.doneEvent)
        else:
            self.notify.error('Unknown mode: ' + where + ' in handleStartingBlockDone')

    def handleGolfKartDone(self, doneStatus):
        self.notify.debug('handling golf kart  done event')
        mode = doneStatus['mode']
        if mode == 'reject':
            self.fsm.request('walk')
        elif mode == 'exit':
            self.fsm.request('walk')
        elif mode == 'golfcourse':
            self.doneStatus = {'loader': 'golfcourse',
             'where': 'golfcourse',
             'hoodId': self.loader.hood.id,
             'zoneId': doneStatus['zoneId'],
             'shardId': None,
             'courseId': doneStatus['courseId']}
            messenger.send(self.doneEvent)
        else:
            self.notify.error('Unknown mode: ' + mode + ' in handleGolfKartDone')
        return
