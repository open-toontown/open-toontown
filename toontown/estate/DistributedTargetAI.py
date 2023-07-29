from otp.ai.AIBase import *
from direct.distributed.ClockDelta import *
from direct.interval.IntervalGlobal import *

from direct.distributed import DistributedObjectAI
import random
from direct.task.Task import Task


DECREMENT_TIME = 5
MIN_WAIT_TIME = 5
MAX_WAIT_TIME = 30
MAX_SCORE = 134217728

class DistributedTargetAI(DistributedObjectAI.DistributedObjectAI):
    
    notify = directNotify.newCategory("DistributedTargetAI")

    def __init__(self, air, x, y, z):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.pos = [x, y, z]
        #self.zoneId = zoneId
        self.numConsecutiveHits = 0
        self.participants = []
        self.rewardTrack = None
        self.enabled = 0
        self.pinballHiScore = 0
        self.pinballHiScorer = ""

    def delete(self):
        DistributedObjectAI.DistributedObjectAI.delete(self)
        self.notify.debug("delete")
        taskMgr.remove(self.taskName("reduce-score"))
        taskMgr.remove(self.taskName("start-score"))
        taskMgr.remove(self.taskName("scoreTimer"))

    def start(self):
        # start the score sometime in the future
        self.reset()
        
    def reset(self):
        taskMgr.remove(self.taskName("reduce-score"))
        taskMgr.remove(self.taskName("start-score"))
        taskMgr.remove(self.taskName("scoreTimer"))

        # disable the score
        self.enabled = 0
        self.score = 0
        self.sendUpdate("setState", [0, 0, 0])

        # start again some random time later
        tWait = (random.random() * MAX_WAIT_TIME) + MIN_WAIT_TIME
        self.notify.debug("waiting %s seconds to restart target" % tWait)
        taskMgr.doMethodLater(tWait,
                              self.startScoreTask,
                              self.taskName("start-score"))

    def startScoreTask(self, task):
        assert(self.notify.debug("startScoreTask"))
        self.enabled = 1
        self.score = 1

        # keep track of people in the zone when the score starts
        # (We don't want to give the reward to people that walk in late)
        self.getParticipants()

        # start the timer for the first hit
        self.hitTime = 15
        self.sendUpdate("setState", [1, self.score, self.hitTime])
        taskMgr.doMethodLater(self.hitTime,
                              self.timerExpiredTask,
                              self.taskName("scoreTimer"))
        return Task.done
                              
    ## These functions are written for a speed-type game where
    ## the possible reward is doubled every time someone hits the
    ## target, but the time allowed to hit the target is reduced
    ## each time.  For instance, we have 10 seconds to hit the target the
    ## first time, then 8 seconds to hit it again, then 6, 4, 2, 1, .5, etc.
    ## At the same time the reward goes from 1 to 2,4,8,16, etc.
        
    def targetHit(self):
        assert(self.notify.debug("targetHit, score = %s" % self.score))
        # kill current timer
        taskMgr.remove(self.taskName("scoreTimer"))

        # increase the score, decrease the time
        if self.score > 0:
            self.score *= 2
        else:
            self.score = 2

        # cap score to something reasonable
        if self.score > MAX_SCORE:
            self.score = MAX_SCORE
            
        if self.hitTime >= 4:
            self.hitTime -= 2
        else:
            self.hitTime /= 2.0

        assert(self.notify.debug("targetHit, increase stakes: %s, time = %s" % (self.score, self.hitTime)))

        # tell client about the new score level
        self.sendUpdate("setState", [1, self.score, self.hitTime])
        
        # start another timer
        taskMgr.doMethodLater(self.hitTime,
                              self.timerExpiredTask,
                              self.taskName("scoreTimer"))

        
    def targetMiss(self):
        assert(self.notify.debug("targetMiss"))
        # do nothing if we miss
        pass

    def timerExpiredTask(self, task):
        assert(self.notify.debug("timerExpiredTask"))
        # give the reward
        if self.score > 0:
            self.doReward()
            self.sendUpdate("setReward", [self.score])
        self.reset()
        return Task.done
    
    def doReward(self):
        # self.score > 0, so give a reward to all remaining
        # participants (toons that were around when the streak started and
        # are still around).

        reward = self.score
        # first make sure the owner is still around:
        ownerAvId = simbase.air.estateMgr.zone2owner.get(self.zoneId)
        if ownerAvId:
            # get the toons currently in the zone
            visitors = simbase.air.estateMgr.refCount.get(self.zoneId)
            # now check our original participants against this list
            for avId in self.participants:
                self.notify.debug("participant: %s" % avId)
                if (visitors and (avId in visitors)) or avId == ownerAvId:
                    # they are still around, give them the reward
                    av = simbase.air.doId2do.get(avId)
                    if av:
                        self.notify.debug("giving a reward of %s" % reward)
                        av.toonUp(reward)
            
    def setResult(self, avId):
        self.notify.debug("setResult: %s" % avId)
        # if we have a valid avId, increment the consecutiveHits count
        # else, just reward the points (if consecutiveHits > 0)
        if avId:
            self.targetHit()
        else:
            self.targetMiss()

    def setBonus(self, bonus):
        if self.enabled:
            self.score += bonus
            self.sendUpdate("setState", [1, self.score, self.hitTime])
            
    def getPosition(self):
        # This is needed because setPosition is a required field.
        return self.pos

    def getParticipants(self):
        assert(self.notify.debug("getParticipants"))
        self.participants = []
        # mark all the avatars that are in the zone when the hit streak starts
        ownerAvId = simbase.air.estateMgr.zone2owner.get(self.zoneId)
        if ownerAvId:
            self.participants.append(ownerAvId)
            visitors = simbase.air.estateMgr.refCount.get(self.zoneId)
            if visitors:
                self.participants += visitors
            
        self.notify.debug("participants = %s" % self.participants)


    def getPinballHiScorer(self):
        return self.pinballHiScorer

    def getPinballHiScore(self):
        return self.pinballHiScore

    def setPinballHiScorer(self, name):
        self.pinballHiScorer = name

    def setPinballHiScore(self, score):
        self.pinballHiScore = score

    def d_setPinballHiScorer(self, name):
        self.sendUpdate('setPinballHiScorer',[name])        

    def d_setPinballHiScore(self, score):
        self.sendUpdate('setPinballHiScore',[score ])

    def b_setPinballHiScorer(self, name):
        self.setPinballHiScorer(name)
        self.d_setPinballHiScorer(name)

    def b_setPinballHiScore(self, score):
        self.setPinballHiScore(score)
        self.d_setPinballHiScore(score)


    def setCurPinballScore(self, avId,  curScore, multiplier):
        self.notify.debug('setCurPinballScore %s %s %s' % ( avId,  curScore, multiplier))
        totalScore = curScore * multiplier
        if totalScore > self.pinballHiScore:
            name = ""
            toon = self.air.doId2do.get(avId)
            if (toon):
                name = toon.getName()

            self.b_setPinballHiScorer(name)
            self.b_setPinballHiScore(totalScore)



        
        
    
    """
    # These functions were written for more of a WeakestLink style game where
    # consecutive hits on the target add up until someone finally misses.  On a miss
    # the number of consecutive hits is "paid" to participants.
    def targetHit(self):
        # This is the handler that gets called when a localToon hits
        # a DistributedTarget
        avId = self.air.getAvatarIdFromSender()
        if self.numConsecutiveHits == 0:
            self.getParticipants()
        self.numConsecutiveHits += 1
        self.sendUpdate("setLevel", [self.numConsecutiveHits])

        # if we get too high, reset:
        if self.numConsecutiveHits > 5:
            # fake a targetMiss to reset correctly
            self.targetMiss()

    def targetMiss(self):
        if self.numConsecutiveHits > 0:
            self.doReward()
        self.numConsecutiveHits = 0
        self.participants = []
        self.sendUpdate("setLevel", [0])

    def doReward(self):
        # numConsectiveHits > 0, so give a reward to all remaining
        # participants (toons that were around when the streak started and
        # are still around).

        reward = 5 * self.numConsecutiveHits
        # first make sure the owner is still around:
        ownerAvId = simbase.air.estateMgr.zone2owner.get(self.zoneId)
        if ownerAvId:
            # get the toons currently in the zone
            visitors = simbase.air.estateMgr.refCount.get(self.zoneId)
            # now check our original participants against this list
            for avId in self.participants:
                self.notify.debug("participant: %s" % avId)
                if (avId in visitors) or avId == ownerAvId:
                    # they are still around, give them the reward
                    av = simbase.air.doId2do.get(avId)
                    if av:
                        self.notify.debug("giving a reward of %s" % reward)
                        av.toonUp(reward)
            
    """


    """
    ## These functions are written for CannonGame style game in which the reward
    ## ticks down until the target is hit.  When the target is hit, the remaining
    ## reward is given to everybody in the zone (of original participants)
    def startScoreTask(self, task):
        self.enabled = 1
        self.score = MAX_SCORE
        
        # keep track of people in the zone when the score starts
        # (We don't want to give the reward to people that walk in late)
        self.getParticipants()
        
        taskMgr.remove(self.taskName("reduce-score"))
        taskMgr.doMethodLater(DECREMENT_TIME,
                              self.reduceScoreTask,
                              self.taskName("reduce-score"))
        # tell the client the score is enabled so it can
        # color it or show that it is enabled somehow
        #self.sendUpdate("setState", [1])
        self.sendUpdate("setLevel", [self.score])
        return Task.done
                              
    def reduceScoreTask(self, task):
        self.score -= 1
        self.sendUpdate("setLevel", [self.score])
        if self.score == 0:
            self.reset()
        taskMgr.doMethodLater(DECREMENT_TIME,
                              self.reduceScoreTask,
                              self.taskName("reduce-score"))
        return Task.done

    def targetHit(self):
        assert(self.notify.debug("targetHit, score = %s" % self.score))
        # someone hit us!!  pay out to all participants and reset
        if self.score > 0:
            self.doReward()
        self.reset()
        
    def targetMiss(self):
        assert(self.notify.debug("targetMiss"))
        # do nothing if we miss
        pass
    
    def doReward(self):
        # self.score > 0, so give a reward to all remaining
        # participants (toons that were around when the streak started and
        # are still around).

        reward = self.score
        # first make sure the owner is still around:
        ownerAvId = simbase.air.estateMgr.zone2owner.get(self.zoneId)
        if ownerAvId:
            # get the toons currently in the zone
            visitors = simbase.air.estateMgr.refCount.get(self.zoneId)
            # now check our original participants against this list
            for avId in self.participants:
                self.notify.debug("participant: %s" % avId)
                if (avId in visitors) or avId == ownerAvId:
                    # they are still around, give them the reward
                    av = simbase.air.doId2do.get(avId)
                    if av:
                        self.notify.debug("giving a reward of %s" % reward)
                        av.toonUp(reward)
    """
