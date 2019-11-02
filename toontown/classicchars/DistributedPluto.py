from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
import DistributedCCharBase
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from toontown.toonbase import ToontownGlobals
import CharStateDatas
from direct.fsm import StateData
from direct.task import Task
from toontown.toonbase import TTLocalizer
from toontown.hood import MMHood

class DistributedPluto(DistributedCCharBase.DistributedCCharBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPluto')

    def __init__(self, cr):
        try:
            self.DistributedPluto_initialized
        except:
            self.DistributedPluto_initialized = 1
            DistributedCCharBase.DistributedCCharBase.__init__(self, cr, TTLocalizer.Pluto, 'p')
            self.fsm = ClassicFSM.ClassicFSM('DistributedPluto', [State.State('Off', self.enterOff, self.exitOff, ['Neutral']), State.State('Neutral', self.enterNeutral, self.exitNeutral, ['Walk']), State.State('Walk', self.enterWalk, self.exitWalk, ['Neutral'])], 'Off', 'Off')
            self.fsm.enterInitialState()
            self.handleHolidays()

    def disable(self):
        self.fsm.requestFinalState()
        DistributedCCharBase.DistributedCCharBase.disable(self)
        taskMgr.remove('enterNeutralTask')
        taskMgr.remove('enterWalkTask')
        del self.neutralDoneEvent
        del self.neutral
        del self.walkDoneEvent
        del self.walk
        del self.neutralStartTrack
        del self.walkStartTrack
        self.fsm.requestFinalState()

    def delete(self):
        try:
            self.DistributedPluto_deleted
        except:
            self.DistributedPluto_deleted = 1
            del self.fsm
            DistributedCCharBase.DistributedCCharBase.delete(self)

    def generate(self):
        DistributedCCharBase.DistributedCCharBase.generate(self, self.diffPath)
        self.neutralDoneEvent = self.taskName('pluto-neutral-done')
        self.neutral = CharStateDatas.CharNeutralState(self.neutralDoneEvent, self)
        self.walkDoneEvent = self.taskName('pluto-walk-done')
        if self.diffPath == None:
            self.walk = CharStateDatas.CharWalkState(self.walkDoneEvent, self)
        else:
            self.walk = CharStateDatas.CharWalkState(self.walkDoneEvent, self, self.diffPath)
        self.walkStartTrack = Sequence(self.actorInterval('stand'), Func(self.stand))
        self.neutralStartTrack = Sequence(self.actorInterval('sit'), Func(self.sit))
        self.fsm.request('Neutral')
        return

    def stand(self):
        self.dropShadow.setScale(0.9, 1.35, 0.9)
        if hasattr(self, 'collNodePath'):
            self.collNodePath.setScale(1.0, 1.5, 1.0)

    def sit(self):
        self.dropShadow.setScale(0.9)
        if hasattr(self, 'collNodePath'):
            self.collNodePath.setScale(1.0)

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def enterNeutral(self):
        self.notify.debug('Neutral ' + self.getName() + '...')
        self.neutral.enter(self.neutralStartTrack)
        self.acceptOnce(self.neutralDoneEvent, self.__decideNextState)

    def exitNeutral(self):
        self.ignore(self.neutralDoneEvent)
        self.neutral.exit()

    def enterWalk(self):
        self.notify.debug('Walking ' + self.getName() + '...')
        self.walk.enter(self.walkStartTrack)
        self.acceptOnce(self.walkDoneEvent, self.__decideNextState)

    def exitWalk(self):
        self.ignore(self.walkDoneEvent)
        self.walk.exit()

    def __decideNextState(self, doneStatus):
        self.fsm.request('Neutral')

    def setWalk(self, srcNode, destNode, timestamp):
        if destNode and not destNode == srcNode:
            self.walk.setWalk(srcNode, destNode, timestamp)
            self.fsm.request('Walk')

    def walkSpeed(self):
        return ToontownGlobals.PlutoSpeed

    def handleHolidays(self):
        DistributedCCharBase.DistributedCCharBase.handleHolidays(self)
        if hasattr(base.cr, 'newsManager') and base.cr.newsManager:
            holidayIds = base.cr.newsManager.getHolidayIdList()
            if ToontownGlobals.APRIL_FOOLS_COSTUMES in holidayIds and isinstance(self.cr.playGame.hood, MMHood.MMHood):
                self.diffPath = TTLocalizer.Minnie

    def getCCLocation(self):
        if self.diffPath == None:
            return 1
        else:
            return 0
        return
