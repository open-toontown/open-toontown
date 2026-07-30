from otp.ai.AIBaseGlobal import *
from . import DistributedCCharBaseAI
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM
from direct.fsm import State
from direct.task import Task
import random
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from . import CharStateDatasAI

class DistributedChipAI(DistributedCCharBaseAI.DistributedCCharBaseAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedChipAI')

    def __init__(self, air):
        DistributedCCharBaseAI.DistributedCCharBaseAI.__init__(self, air, TTLocalizer.Chip)
        self.fsm = ClassicFSM.ClassicFSM('DistributedChipAI', [
         State.State('Off', self.enterOff, self.exitOff, [
          'Lonely', 'TransitionToCostume']),
         State.State('Lonely', self.enterLonely, self.exitLonely, [
          'Chatty', 'Walk', 'TransitionToCostume']),
         State.State('Chatty', self.enterChatty, self.exitChatty, [
          'Lonely', 'Walk', 'TransitionToCostume']),
         State.State('Walk', self.enterWalk, self.exitWalk, [
          'Lonely', 'Chatty', 'TransitionToCostume']),
         State.State('TransitionToCostume', self.enterTransitionToCostume, self.exitTransitionToCostume, [
          'Off'])], 'Off', 'Off')
        self.fsm.enterInitialState()
        self.dale = None
        self.handleHolidays()
        return

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
        name = self.getName()
        self.lonelyDoneEvent = self.taskName(name + '-lonely-done')
        self.lonely = CharStateDatasAI.CharLonelyStateAI(self.lonelyDoneEvent, self)
        self.chattyDoneEvent = self.taskName(name + '-chatty-done')
        self.chatty = CharStateDatasAI.ChipChattyStateAI(self.chattyDoneEvent, self)
        self.walkDoneEvent = self.taskName(name + '-walk-done')
        self.walk = CharStateDatasAI.CharWalkStateAI(self.walkDoneEvent, self)

    def walkSpeed(self):
        return ToontownGlobals.ChipSpeed

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
        if self.dale:
            self.dale.chipEnteringState(self.fsm.getCurrentState().getName())

    def exitLonely(self):
        self.ignore(self.lonelyDoneEvent)
        self.lonely.exit()
        if self.dale:
            self.dale.chipLeavingState(self.fsm.getCurrentState().getName())

    def __goForAWalk(self, task):
        self.notify.debug('going for a walk')
        self.fsm.request('Walk')
        return Task.done

    def enterChatty(self):
        self.chatty.enter()
        self.acceptOnce(self.chattyDoneEvent, self.__decideNextState)
        if self.dale:
            self.dale.chipEnteringState(self.fsm.getCurrentState().getName())
        taskMgr.doMethodLater(CharStateDatasAI.CHATTY_DURATION + 10, self.forceLeaveChatty, self.taskName('forceLeaveChatty'))

    def forceLeaveChatty(self, task):
        self.notify.warning('Had to force change of state from Chatty state')
        doneStatus = {}
        doneStatus['state'] = 'chatty'
        doneStatus['status'] = 'done'
        self.__decideNextState(doneStatus)
        return Task.done

    def cleanUpChattyTasks(self):
        taskMgr.removeTasksMatching(self.taskName('forceLeaveChatty'))

    def exitChatty(self):
        self.ignore(self.chattyDoneEvent)
        self.chatty.exit()
        if self.dale:
            self.dale.chipLeavingState(self.fsm.getCurrentState().getName())
        self.cleanUpChattyTasks()

    def enterWalk(self):
        self.notify.debug('going for a walk')
        self.walk.enter()
        self.acceptOnce(self.walkDoneEvent, self.__decideNextState)
        if self.dale:
            self.dale.chipEnteringState(self.fsm.getCurrentState().getName())

    def exitWalk(self):
        self.ignore(self.walkDoneEvent)
        self.walk.exit()
        if self.dale:
            self.dale.chipLeavingState(self.fsm.getCurrentState().getName())

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

    def setDaleId(self, daleId):
        self.daleId = daleId
        self.dale = self.air.doId2do.get(daleId)
        self.chatty.setDaleId(self.daleId)

    def enterTransitionToCostume(self):
        pass

    def exitTransitionToCostume(self):
        pass
