from pandac.PandaModules import *
from toontown.toonbase import ToontownGlobals
import Playground
from toontown.launcher import DownloadForceAcknowledge
from toontown.building import Elevator
from toontown.toontowngui import TTDialog
from toontown.toonbase import TTLocalizer
from toontown.racing import RaceGlobals
from direct.fsm import State

class GSPlayground(Playground.Playground):

    def __init__(self, loader, parentFSM, doneEvent):
        Playground.Playground.__init__(self, loader, parentFSM, doneEvent)
        self.parentFSM = parentFSM
        self.startingBlockDoneEvent = 'startingBlockDone'
        self.fsm.addState(State.State('startingBlock', self.enterStartingBlock, self.exitStartingBlock, ['walk']))
        state = self.fsm.getStateNamed('walk')
        state.addTransition('startingBlock')

    def load(self):
        Playground.Playground.load(self)

    def unload(self):
        Playground.Playground.unload(self)

    def enter(self, requestStatus):
        Playground.Playground.enter(self, requestStatus)
        blimp = base.cr.playGame.hood.loader.geom.find('**/GS_blimp')
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

    def enterStartingBlock(self, distStartingBlock):
        import pdb
        pdb.set_trace()
        self.accept(self.startingBlockDoneEvent, self.handleStartingBlockDone)
        self.startingBlock = Elevator.Elevator(self.fsm.getStateNamed('startingBlock'), self.startingBlockDoneEvent, distStartingBlock)
        distStartingBlock.elevatorFSM = self.startingBlock
        self.startingBlock.load()
        self.startingBlock.enter()

    def exitStartingBlock(self):
        self.ignore(self.startingBlockDoneEvent)
        self.startingBlock.unload()
        self.startingBlock.exit()
        del self.startingBlock

    def detectedStartingBlockCollision(self, distStartingBlock):
        import pdb
        pdb.set_trace()
        self.fsm.request('startingBlock', [distStartingBlock])

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

    def showPaths(self):
        from toontown.classicchars import CCharPaths
        from toontown.toonbase import TTLocalizer
        self.showPathPoints(CCharPaths.getPaths(TTLocalizer.Goofy, 1))
