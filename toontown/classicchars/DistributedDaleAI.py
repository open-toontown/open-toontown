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

class DistributedDaleAI(DistributedCCharBaseAI.DistributedCCharBaseAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedDaleAI')

    def __init__(self, air, chipId):
        DistributedCCharBaseAI.DistributedCCharBaseAI.__init__(self, air, TTLocalizer.Dale)
        self.chipId = chipId
        self.chip = air.doId2do.get(chipId)
        self.fsm = ClassicFSM.ClassicFSM('DistributedDaleAI', [
         State.State('Off', self.enterOff, self.exitOff, [
          'Lonely']),
         State.State('Lonely', self.enterLonely, self.exitLonely, [
          'Chatty', 'FollowChip', 'Walk']),
         State.State('Chatty', self.enterChatty, self.exitChatty, [
          'Lonely', 'FollowChip', 'Walk']),
         State.State('Walk', self.enterWalk, self.exitWalk, [
          'Lonely', 'Chatty']),
         State.State('FollowChip', self.enterFollowChip, self.exitFollowChip, [
          'Lonely', 'Chatty', 'FollowChip'])], 'Off', 'Off')
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
        self.lonely = CharStateDatasAI.CharLonelyStateAI(None, self)
        self.chatty = CharStateDatasAI.CharChattyStateAI(None, self)
        self.followChip = CharStateDatasAI.CharFollowChipStateAI(None, self, self.chip)
        return

    def walkSpeed(self):
        return ToontownGlobals.DaleSpeed

    def start(self):
        self.fsm.request('Lonely')

    def __decideNextState(self, doneStatus):
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

    def exitLonely(self):
        self.lonely.exit()

    def __goForAWalk(self, task):
        self.notify.debug('going for a walk')
        self.fsm.request('Walk')
        return Task.done

    def enterChatty(self):
        self.chatty.enter()

    def exitChatty(self):
        self.chatty.exit()

    def enterWalk(self):
        self.notify.debug('going for a walk')
        self.walk.enter()
        self.acceptOnce(self.walkDoneEvent, self.__decideNextState)

    def exitWalk(self):
        self.ignore(self.walkDoneEvent)
        self.walk.exit()

    def enterFollowChip(self):
        self.notify.debug('enterFollowChip')
        walkState = self.chip.walk
        destNode = walkState.getDestNode()
        self.followChip.enter(destNode)

    def exitFollowChip(self):
        self.notify.debug('exitFollowChip')
        self.followChip.exit()

    def avatarEnterNextState(self):
        if len(self.nearbyAvatars) == 1:
            if False:
                self.fsm.request('Chatty')
            else:
                self.notify.debug('avatarEnterNextState: in walk state')
        else:
            self.notify.debug('avatarEnterNextState: num avatars: ' + str(len(self.nearbyAvatars)))

    def avatarExitNextState(self):
        if len(self.nearbyAvatars) == 0:
            if self.fsm.getCurrentState().getName() != 'Walk':
                pass

    def chipEnteringState(self, newState):
        if newState == 'Walk':
            self.doFollowChip()

    def chipLeavingState(self, oldState):
        pass

    def doFollowChip(self):
        walkState = self.chip.walk
        destNode = walkState.getDestNode()
        self.fsm.request('FollowChip')

    def doChatty(self):
        pass

    def getChipId(self):
        return self.chipId

    def enterTransitionToCostume(self):
        pass

    def exitTransitionToCostume(self):
        pass
