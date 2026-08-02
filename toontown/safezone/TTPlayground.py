from panda3d.core import *
from toontown.toonbase import ToontownGlobals
from . import Playground
import random
from toontown.launcher import DownloadForceAcknowledge
from direct.task.Task import Task
from direct.fsm import State
from toontown.hood import ZoneUtil

class TTPlayground(Playground.Playground):

    def __init__(self, loader, parentFSM, doneEvent):
        Playground.Playground.__init__(self, loader, parentFSM, doneEvent)
        self.fsm.addState(State.State('crane', self.enterCraneTTC, self.exitCraneTTC, ['finalBattle']))
        self.fsm.addState(State.State('finalBattle', self.enterFinalBattleTTC, self.exitFinalBattleTTC, ['walk',
         'crane']))
        for name in ('walk', 'stickerBook', 'fishing', 'trolley', 'quest', 'purchase', 'stopped', 'DFA', 'HFA', 'TFA', 'teleportIn', 'popup', 'doorIn', 'doorOut', 'deathAck', 'NPCFA', 'NPCFAReject', 'trialerFA'):
            try:
                self.fsm.getStateNamed(name).addTransition('crane')
                self.fsm.getStateNamed(name).addTransition('finalBattle')
            except KeyError:
                pass

    def load(self):
        Playground.Playground.load(self)

    def unload(self):
        Playground.Playground.unload(self)

    def enter(self, requestStatus):
        Playground.Playground.enter(self, requestStatus)
        taskMgr.doMethodLater(1, self.__birds, 'TT-birds')

    def exit(self):
        Playground.Playground.exit(self)
        taskMgr.remove('TT-birds')

    def __birds(self, task):
        if not self.loader.birdSound:
            return Task.done
        base.playSfx(random.choice(self.loader.birdSound))
        t = random.random() * 20.0 + 1
        taskMgr.doMethodLater(t, self.__birds, 'TT-birds')
        return Task.done

    def doRequestLeave(self, requestStatus):
        self.fsm.request('trialerFA', [requestStatus])

    def enterDFA(self, requestStatus):
        doneEvent = 'dfaDoneEvent'
        self.accept(doneEvent, self.enterDFACallback, [requestStatus])
        self.dfa = DownloadForceAcknowledge.DownloadForceAcknowledge(doneEvent)
        hood = ZoneUtil.getCanonicalZoneId(requestStatus['hoodId'])
        if hood == ToontownGlobals.MyEstate:
            self.dfa.enter(base.cr.hoodMgr.getPhaseFromHood(ToontownGlobals.MyEstate))
        elif hood == ToontownGlobals.GoofySpeedway:
            self.dfa.enter(base.cr.hoodMgr.getPhaseFromHood(ToontownGlobals.GoofySpeedway))
        elif hood == ToontownGlobals.PartyHood:
            self.dfa.enter(base.cr.hoodMgr.getPhaseFromHood(ToontownGlobals.PartyHood))
        else:
            self.dfa.enter(5)

    def enterCraneTTC(self):
        base.localAvatar.setTeleportAvailable(0)
        base.localAvatar.laffMeter.start()
        base.localAvatar.collisionsOn()

    def exitCraneTTC(self):
        base.localAvatar.collisionsOff()
        base.localAvatar.laffMeter.stop()

    def enterFinalBattleTTC(self, *args):
        taskMgr.doMethodLater(0.0, self.__requestWalkAfterCrane, 'TTPlayground-finalBattle')

    def __requestWalkAfterCrane(self, task):
        self.fsm.request('walk', [0])
        return Task.done

    def exitFinalBattleTTC(self):
        taskMgr.remove('TTPlayground-finalBattle')

    def showPaths(self):
        from toontown.classicchars import CCharPaths
        from toontown.toonbase import TTLocalizer
        self.showPathPoints(CCharPaths.getPaths(TTLocalizer.Mickey))
