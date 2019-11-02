from direct.directnotify import DirectNotifyGlobal
import RingAction

class RingTrack:
    notify = DirectNotifyGlobal.directNotify.newCategory('RingTrack')

    def __init__(self, actions, actionDurations = None, reverseFlag = 0):
        if actionDurations == None:
            actionDurations = [1.0 / float(len(actions))] * len(actions)
        sum = 0.0
        for duration in actionDurations:
            sum += duration

        if sum != 1.0:
            self.notify.warning('action lengths do not sum to 1.; sum=' + str(sum))
        self.actions = actions
        self.actionDurations = actionDurations
        self.reverseFlag = reverseFlag
        return

    def eval(self, t):
        t = float(t)
        if self.reverseFlag:
            t = 1.0 - t
        actionStart = 0.0
        for action, duration in zip(self.actions, self.actionDurations):
            actionEnd = actionStart + duration
            if t < actionEnd:
                actionT = (t - actionStart) / duration
                return action.eval(actionT)
            else:
                actionStart = actionEnd

        if t == actionStart:
            self.notify.debug('time value is at end of ring track: ' + str(t) + ' == ' + str(actionStart))
        else:
            self.notify.debug('time value is beyond end of ring track: ' + str(t) + ' > ' + str(actionStart))
        lastAction = self.actions[len(self.actions) - 1]
        return lastAction.eval(1.0)
