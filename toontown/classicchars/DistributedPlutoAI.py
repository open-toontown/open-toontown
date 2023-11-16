from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State
from direct.task import Task

from otp.ai.AIBaseGlobal import *

from toontown.classicchars import CCharChatter, CharStateDatasAI, DistributedCCharBaseAI
from toontown.toonbase import ToontownGlobals, TTLocalizer


class DistributedPlutoAI(DistributedCCharBaseAI.DistributedCCharBaseAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedPlutoAI')

    def __init__(self, air):
        DistributedCCharBaseAI.DistributedCCharBaseAI.__init__(self, air, TTLocalizer.Pluto)
        self.fsm = ClassicFSM.ClassicFSM('DistributedPlutoAI', [
         State.State('Off', self.enterOff, self.exitOff, [
          'Lonely', 'TransitionToCostume', 'Walk']),
         State.State('Lonely', self.enterLonely, self.exitLonely, [
          'Chatty', 'Walk', 'TransitionToCostume']),
         State.State('Chatty', self.enterChatty, self.exitChatty, [
          'Lonely', 'Walk', 'TransitionToCostume']),
         State.State('Walk', self.enterWalk, self.exitWalk, [
          'Lonely', 'Chatty', 'TransitionToCostume']),
         State.State('TransitionToCostume', self.enterTransitionToCostume, self.exitTransitionToCostume, [
          'Off'])], 'Off', 'Off')
        self.fsm.enterInitialState()
        self.handleHolidays()

    def delete(self):
        self.fsm.requestFinalState()
        DistributedCCharBaseAI.DistributedCCharBaseAI.delete(self)
        self.lonelyDoneEvent = None
        self.lonely = None
        self.chattyDoneEvent = None
        self.chatty = None
        self.walkDoneEvent = None
        self.walk = None
        return

    def generate(self):
        DistributedCCharBaseAI.DistributedCCharBaseAI.generate(self)
        self.lonelyDoneEvent = self.taskName('pluto-lonely-done')
        self.lonely = CharStateDatasAI.CharLonelyStateAI(self.lonelyDoneEvent, self)
        self.chattyDoneEvent = self.taskName('pluto-chatty-done')
        self.chatty = CharStateDatasAI.CharChattyStateAI(self.chattyDoneEvent, self)
        self.walkDoneEvent = self.taskName('pluto-walk-done')
        if self.diffPath == None:
            self.walk = CharStateDatasAI.CharWalkStateAI(self.walkDoneEvent, self)
        else:
            self.walk = CharStateDatasAI.CharWalkStateAI(self.walkDoneEvent, self, self.diffPath)
        return

    def walkSpeed(self):
        return ToontownGlobals.PlutoSpeed

    def start(self):
        self.fsm.request('Lonely')

    def __decideNextState(self, doneStatus):
        if self.transitionToCostume == 1:
            curWalkNode = self.walk.getDestNode()
            if simbase.air.holidayManager:
                if ToontownGlobals.HALLOWEEN_COSTUMES in simbase.air.holidayManager.currentHolidays and simbase.air.holidayManager.currentHolidays[ToontownGlobals.HALLOWEEN_COSTUMES]:
                    simbase.air.holidayManager.currentHolidays[ToontownGlobals.HALLOWEEN_COSTUMES].triggerSwitch(curWalkNode, self)
                    self.fsm.request('TransitionToCostume')
                    return
                elif ToontownGlobals.APRIL_FOOLS_COSTUMES in simbase.air.holidayManager.currentHolidays and simbase.air.holidayManager.currentHolidays[ToontownGlobals.APRIL_FOOLS_COSTUMES]:
                    simbase.air.holidayManager.currentHolidays[ToontownGlobals.APRIL_FOOLS_COSTUMES].triggerSwitch(curWalkNode, self)
                    self.fsm.request('TransitionToCostume')
                    return
                else:
                    self.notify.warning('transitionToCostume == 1 but no costume holiday')
            else:
                self.notify.warning('transitionToCostume == 1 but no holiday Manager')
        if doneStatus['state'] == 'lonely' and doneStatus['status'] == 'done':
            self.fsm.request('Walk')
        elif doneStatus['state'] == 'chatty' and doneStatus['status'] == 'done':
            self.fsm.request('Walk')
        elif doneStatus['state'] == 'walk' and doneStatus['status'] == 'done':
            if len(self.nearbyAvatars) > 0:
                self.fsm.request('Chatty')
            else:
                self.fsm.request('Lonely')

    def enterOff(self):
        pass

    def exitOff(self):
        DistributedCCharBaseAI.DistributedCCharBaseAI.exitOff(self)

    def enterLonely(self):
        self.lonely.enter()
        self.acceptOnce(self.lonelyDoneEvent, self.__decideNextState)

    def exitLonely(self):
        self.ignore(self.lonelyDoneEvent)
        self.lonely.exit()

    def __goForAWalk(self, task):
        self.notify.debug('going for a walk')
        self.fsm.request('Walk')
        return Task.done

    def enterChatty(self):
        chatter = CCharChatter.getChatter(self.getName(), self.getCCChatter())
        if not chatter:
            self.chatterExists = False
            self.fsm.request('Lonely')
        else:
            self.chatterExists = True
            self.chatty.enter()
            self.acceptOnce(self.chattyDoneEvent, self.__decideNextState)

    def exitChatty(self):
        if self.chatterExists:
            self.ignore(self.chattyDoneEvent)
            self.chatty.exit()

    def enterWalk(self):
        self.notify.debug('going for a walk')
        self.walk.enter()
        self.acceptOnce(self.walkDoneEvent, self.__decideNextState)

    def exitWalk(self):
        self.ignore(self.walkDoneEvent)
        self.walk.exit()

    def avatarEnterNextState(self):
        if len(self.nearbyAvatars) == 1:
            if self.fsm.getCurrentState().getName() != 'Walk':
                self.fsm.request('Chatty')
            else:
                self.notify.debug('avatarEnterNextState: in walk state')
        else:
            self.notify.debug('avatarEnterNextState: num avatars: ' + str(len(self.nearbyAvatars)))

    def avatarExitNextState(self):
        if len(self.nearbyAvatars) == 0:
            if self.fsm.getCurrentState().getName() != 'Walk':
                self.fsm.request('Lonely')

    def handleHolidays(self):
        DistributedCCharBaseAI.DistributedCCharBaseAI.handleHolidays(self)
        if hasattr(simbase.air, 'holidayManager'):
            if ToontownGlobals.APRIL_FOOLS_COSTUMES in simbase.air.holidayManager.currentHolidays:
                if simbase.air.holidayManager.currentHolidays[ToontownGlobals.APRIL_FOOLS_COSTUMES] != None and simbase.air.holidayManager.currentHolidays[ToontownGlobals.APRIL_FOOLS_COSTUMES].getRunningState():
                    self.diffPath = TTLocalizer.Minnie
        return

    def enterTransitionToCostume(self):
        pass

    def exitTransitionToCostume(self):
        pass
