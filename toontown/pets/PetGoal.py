from direct.task import Task
from direct.fsm import FSM, ClassicFSM, State
from direct.showbase.PythonUtil import randFloat, Functor
from direct.directnotify import DirectNotifyGlobal
from toontown.pets import PetConstants
from toontown.toon import DistributedToonAI

class PetGoal(FSM.FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('PetGoal')
    SerialNum = 0

    def __init__(self):
        FSM.FSM.__init__(self, self.__class__.__name__)
        self.goalMgr = None
        self.pet = None
        self.brain = None
        self.removeOnDone = 0
        self.serialNum = PetGoal.SerialNum
        PetGoal.SerialNum += 1
        self.fsm = ClassicFSM.ClassicFSM('PetGoalFSM', [State.State('off', self.enterOff, self.exitOff, ['background']), State.State('background', self.enterBackground, self.exitBackground, ['foreground']), State.State('foreground', self.enterForeground, self.exitForeground, ['background'])], 'off', 'off')
        self.fsm.enterInitialState()
        return

    def destroy(self):
        if hasattr(self, 'fsm'):
            self.fsm.requestFinalState()
            del self.fsm
        self.cleanup()

    def _removeSelf(self):
        self.goalMgr.removeGoal(self)

    def getDoneEvent(self):
        return 'PetGoalDone-%s' % self.serialNum

    def announceDone(self):
        if self.removeOnDone:
            self._removeSelf()
        messenger.send(self.getDoneEvent())
        if self.removeOnDone:
            self.destroy()

    def setGoalMgr(self, goalMgr):
        self.goalMgr = goalMgr
        self.pet = goalMgr.pet
        self.brain = self.pet.brain
        self.fsm.request('background')

    def clearGoalMgr(self):
        self.goalMgr = None
        self.pet = None
        self.brain = None
        self.fsm.requestFinalState()
        return

    def getPriority(self):
        return PetConstants.PriorityDefault

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def enterBackground(self):
        pass

    def exitBackground(self):
        pass

    def enterForeground(self):
        pass

    def exitForeground(self):
        pass

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.getPriority())


class InteractWithAvatar(PetGoal):
    SerialNum = 0

    def __init__(self, avatar):
        PetGoal.__init__(self)
        self.avatar = avatar
        self.serialNum = InteractWithAvatar.SerialNum
        InteractWithAvatar.SerialNum += 1
        self.transitionDoLaterName = '%s-doLater-%s' % (InteractWithAvatar.__name__, self.serialNum)

    def destroy(self):
        PetGoal.destroy(self)
        if hasattr(self, 'avatar'):
            del self.avatar

    def enterForeground(self):
        self.request('Chase')

    def exitForeground(self):
        self.request('Off')

    def enterChase(self):
        PetGoal.notify.debug('enterChase')
        if self.brain.lookingAt(self.avatar.doId):

            def goToInteract(task = None, self = self):
                self.request('Interact')
                return Task.done

            taskMgr.doMethodLater(0.0001, goToInteract, self.transitionDoLaterName)
        else:
            self.accept(self.brain.getObserveEventAttendingAvStart(self.avatar.doId), Functor(self.request, 'Interact'))
            self.brain._chase(self.avatar)
        return

    def exitChase(self):
        self.ignore(self.brain.getObserveEventAttendingAvStart(self.avatar.doId))
        taskMgr.remove(self.transitionDoLaterName)

    def enterInteract(self):
        PetGoal.notify.debug('enterInteract')
        if self._chaseAvInInteractMode():
            self.accept(self.brain.getObserveEventAttendingAvStop(self.avatar.doId), Functor(self.request, 'Chase'))
        self.startInteract()

    def exitInteract(self):
        self.stopInteract()
        self.ignore(self.brain.getObserveEventAttendingAvStop(self.avatar.doId))

    def startInteract(self):
        pass

    def stopInteract(self):
        pass

    def _chaseAvInInteractMode(self):
        return True

    def __str__(self):
        return '%s-%s: %s' % (self.__class__.__name__, self.avatar.doId, self.getPriority())


class Wander(PetGoal):

    def enterForeground(self):
        self.brain._wander()


class ChaseAvatar(PetGoal):

    def __init__(self, avatar):
        PetGoal.__init__(self)
        self.avatar = avatar
        self.isToon = isinstance(self.avatar, DistributedToonAI.DistributedToonAI)

    def destroy(self):
        PetGoal.destroy(self)
        if hasattr(self, 'avatar'):
            del self.avatar

    def setGoalMgr(self, goalMgr):
        PetGoal.setGoalMgr(self, goalMgr)
        self.basePriority = PetConstants.PriorityChaseAv

    def getPriority(self):
        priority = self.basePriority
        if self.isToon and self.pet.mood.getDominantMood() == 'hunger':
            priority *= PetConstants.HungerChaseToonScale
        lastInteractTime = self.brain.lastInteractTime.get(self.avatar.doId)
        if lastInteractTime is not None:
            elapsed = globalClock.getFrameTime() - lastInteractTime
            if elapsed < PetConstants.GettingAttentionGoalScaleDur:
                priority *= PetConstants.GettingAttentionGoalScale
        return priority

    def enterForeground(self):
        self.brain._chase(self.avatar)

    def __str__(self):
        return '%s-%s: %s' % (self.__class__.__name__, self.avatar.doId, self.getPriority())


class ChaseAvatarLeash(PetGoal):

    def __init__(self, avId):
        PetGoal.__init__(self)
        self.avId = avId

    def getPriority(self):
        return PetConstants.PriorityDebugLeash

    def enterForeground(self):
        av = simbase.air.doId2do.get(self.avId)
        if av:
            self.brain._chase(av)
        else:
            self._removeSelf()

    def __str__(self):
        return '%s-%s: %s' % (self.__class__.__name__, self.avatar.doId, self.getPriority())


class FleeFromAvatar(PetGoal):

    def __init__(self, avatar):
        PetGoal.__init__(self)
        self.avatar = avatar

    def destroy(self):
        PetGoal.destroy(self)
        if hasattr(self, 'avatar'):
            del self.avatar

    def getPriority(self):
        priority = PetConstants.PriorityFleeFromAvatar
        if self.avatar.doId == self.goalMgr.pet.ownerId:
            priority *= PetConstants.FleeFromOwnerScale
        return priority

    def enterForeground(self):
        self.brain._chase(self.avatar)

    def __str__(self):
        return '%s-%s: %s' % (self.__class__.__name__, self.avatar.doId, self.getPriority())


class DoTrick(InteractWithAvatar):

    def __init__(self, avatar, trickId):
        InteractWithAvatar.__init__(self, avatar)
        self.trickId = trickId
        self.removeOnDone = 1

    def getPriority(self):
        return PetConstants.PriorityDoTrick

    def setGoalMgr(self, goalMgr):
        goalMgr._setHasTrickGoal(True)
        InteractWithAvatar.setGoalMgr(self, goalMgr)

    def clearGoalMgr(self):
        self.goalMgr._setHasTrickGoal(False)
        InteractWithAvatar.clearGoalMgr(self)

    def _chaseAvInInteractMode(self):
        return False

    def startInteract(self):
        self.brain._doTrick(self.trickId, self.avatar)
        self.trickDoneEvent = self.pet.actionFSM.getTrickDoneEvent()
        self.accept(self.trickDoneEvent, self.announceDone)

    def stopInteract(self):
        self.ignore(self.trickDoneEvent)
        del self.trickDoneEvent

    def __str__(self):
        return '%s-%s-%s: %s' % (self.__class__.__name__,
         self.avatar.doId,
         self.trickId,
         self.getPriority())
