import math
from pandac.PandaModules import CollisionSphere, CollisionNode, Point3, CollisionTube, Vec3, rad2Deg
from direct.showbase.DirectObject import DirectObject
from direct.distributed.ClockDelta import globalClockDelta
from direct.interval.IntervalGlobal import Parallel, SoundInterval, Sequence, Func, LerpScaleInterval
from toontown.suit import Suit
from toontown.suit import SuitDNA
from toontown.toonbase import ToontownGlobals
from toontown.minigame import CogThiefGameGlobals
from toontown.battle.BattleProps import globalPropPool
from toontown.battle.BattleSounds import globalBattleSoundCache
CTGG = CogThiefGameGlobals

class CogThief(DirectObject):
    notify = directNotify.newCategory('CogThief')
    DefaultSpeedWalkAnim = 4.0
    CollisionRadius = 1.25
    MaxFriendsVisible = 4
    Infinity = 100000.0
    SeparationDistance = 6.0
    MinUrgency = 0.5
    MaxUrgency = 0.75

    def __init__(self, cogIndex, suitType, game, cogSpeed):
        self.cogIndex = cogIndex
        self.suitType = suitType
        self.game = game
        self.cogSpeed = cogSpeed
        suit = Suit.Suit()
        d = SuitDNA.SuitDNA()
        d.newSuit(suitType)
        suit.setDNA(d)
        suit.pose('walk', 0)
        self.suit = suit
        self.goal = CTGG.NoGoal
        self.goalId = CTGG.InvalidGoalId
        self.lastLocalTimeStampFromAI = 0
        self.lastPosFromAI = Point3(0, 0, 0)
        self.lastThinkTime = 0
        self.doneAdjust = False
        self.barrel = CTGG.NoBarrelCarried
        self.signalledAtReturnPos = False
        self.defaultPlayRate = 1.0
        self.netTimeSentToStartByHit = 0
        self.velocity = Vec3(0, 0, 0)
        self.oldVelocity = Vec3(0, 0, 0)
        self.acceleration = Vec3(0, 0, 0)
        self.bodyLength = self.CollisionRadius * 2
        self.cruiseDistance = 2 * self.bodyLength
        self.maxVelocity = self.cogSpeed
        self.maxAcceleration = 5.0
        self.perceptionRange = 6
        self.notify.debug('cogSpeed=%s' % self.cogSpeed)
        self.kaboomSound = loader.loadSfx('phase_4/audio/sfx/MG_cannon_fire_alt.mp3')
        self.kaboom = loader.loadModel('phase_4/models/minigames/ice_game_kaboom')
        self.kaboom.setScale(2.0)
        self.kaboom.setBillboardPointEye()
        self.kaboom.hide()
        self.kaboomTrack = None
        splatName = 'splat-creampie'
        self.splat = globalPropPool.getProp(splatName)
        self.splat.setBillboardPointEye()
        self.splatType = globalPropPool.getPropType(splatName)
        self.pieHitSound = globalBattleSoundCache.getSound('AA_wholepie_only.mp3')
        return

    def destroy(self):
        self.ignoreAll()
        self.suit.delete()
        self.game = None
        return

    def uniqueName(self, baseStr):
        return baseStr + '-' + str(self.game.doId)

    def handleEnterSphere(self, collEntry):
        intoNp = collEntry.getIntoNodePath()
        self.notify.debug('handleEnterSphere suit %d hit %s' % (self.cogIndex, intoNp))
        if self.game:
            self.game.handleEnterSphere(collEntry)

    def gameStart(self, gameStartTime):
        self.gameStartTime = gameStartTime
        self.initCollisions()
        self.startWalkAnim()

    def gameEnd(self):
        self.moveIval.pause()
        del self.moveIval
        self.shutdownCollisions()
        self.suit.loop('neutral')

    def initCollisions(self):
        self.collSphere = CollisionSphere(0, 0, 0, 1.25)
        self.collSphere.setTangible(1)
        name = 'CogThiefSphere-%d' % self.cogIndex
        self.collSphereName = self.uniqueName(name)
        self.collNode = CollisionNode(self.collSphereName)
        self.collNode.setIntoCollideMask(CTGG.BarrelBitmask | ToontownGlobals.WallBitmask)
        self.collNode.addSolid(self.collSphere)
        self.collNodePath = self.suit.attachNewNode(self.collNode)
        self.accept('enter' + self.collSphereName, self.handleEnterSphere)
        self.pieCollSphere = CollisionTube(0, 0, 0, 0, 0, 4, self.CollisionRadius)
        self.pieCollSphere.setTangible(1)
        name = 'CogThiefPieSphere-%d' % self.cogIndex
        self.pieCollSphereName = self.uniqueName(name)
        self.pieCollNode = CollisionNode(self.pieCollSphereName)
        self.pieCollNode.setIntoCollideMask(ToontownGlobals.PieBitmask)
        self.pieCollNode.addSolid(self.pieCollSphere)
        self.pieCollNodePath = self.suit.attachNewNode(self.pieCollNode)

    def shutdownCollisions(self):
        self.ignore(self.uniqueName('enter' + self.collSphereName))
        del self.collSphere
        self.collNodePath.removeNode()
        del self.collNodePath
        del self.collNode

    def updateGoal(self, timestamp, inResponseClientStamp, goalType, goalId, pos):
        self.notify.debug('self.netTimeSentToStartByHit =%s' % self.netTimeSentToStartByHit)
        if not self.game:
            self.notify.debug('updateGoal self.game is None, just returning')
            return
        if not self.suit:
            self.notify.debug('updateGoal self.suit is None, just returning')
            return
        if self.goal == CTGG.NoGoal:
            self.startWalkAnim()
        if goalType == CTGG.NoGoal:
            self.notify.debug('updateGoal setting position to %s' % pos)
            self.suit.setPos(pos)
        self.lastThinkTime = 0
        self.velocity = Vec3(0, 0, 0)
        self.oldVelocity = Vec3(0, 0, 0)
        self.acceleration = Vec3(0, 0, 0)
        if goalType == CTGG.RunAwayGoal:
            pass
        if inResponseClientStamp < self.netTimeSentToStartByHit and self.goal == CTGG.NoGoal and goalType == CTGG.RunAwayGoal:
            self.notify.warning('ignoring newGoal %s as cog %d was recently hit responsetime=%s hitTime=%s' % (CTGG.GoalStr[goalType],
             self.cogIndex,
             inResponseClientStamp,
             self.netTimeSentToStartByHit))
        else:
            self.lastLocalTimeStampFromAI = globalClockDelta.networkToLocalTime(timestamp, bits=32)
            self.goal = goalType
            self.goalId = goalId
            self.lastPosFromAI = pos
            self.doneAdjust = False
        self.signalledAtReturnPos = False

    def startWalkAnim(self):
        if self.suit:
            self.suit.loop('walk')
            speed = self.cogSpeed
            self.defaultPlayRate = float(self.cogSpeed / self.DefaultSpeedWalkAnim)
            self.suit.setPlayRate(self.defaultPlayRate, 'walk')

    def think(self):
        if self.goal == CTGG.ToonGoal:
            self.thinkAboutCatchingToon()
        elif self.goal == CTGG.BarrelGoal:
            self.thinkAboutGettingBarrel()
        elif self.goal == CTGG.RunAwayGoal:
            self.thinkAboutRunAway()

    def thinkAboutCatchingToon(self):
        if not self.game:
            return
        av = self.game.getAvatar(self.goalId)
        if av:
            if not self.lastThinkTime:
                self.lastThinkTime = globalClock.getFrameTime()
            diffTime = globalClock.getFrameTime() - self.lastThinkTime
            avPos = av.getPos()
            myPos = self.suit.getPos()
            if not self.doneAdjust:
                myPos = self.lastPosFromAI
                self.notify.debug('thinkAboutCatchingToon not doneAdjust setting pos %s' % myPos)
                self.doneAdjust = True
            self.suit.setPos(myPos)
            if self.game.isToonPlayingHitTrack(self.goalId):
                self.suit.headsUp(av)
                self.velocity = Vec3(0, 0, 0)
                self.oldVelocity = Vec3(0, 0, 0)
                self.acceleration = Vec3(0, 0, 0)
            else:
                self.commonMove()
            newPos = self.suit.getPos()
            self.adjustPlayRate(newPos, myPos, diffTime)
        self.lastThinkTime = globalClock.getFrameTime()

    def convertNetworkStampToGameTime(self, timestamp):
        localStamp = globalClockDelta.networkToLocalTime(timestamp, bits=32)
        gameTime = self.game.local2GameTime(localStamp)
        return gameTime

    def respondToToonHit(self, timestamp):
        localStamp = globalClockDelta.networkToLocalTime(timestamp, bits=32)
        if self.netTimeSentToStartByHit < timestamp:
            self.clearGoal()
            self.showKaboom()
            startPos = CTGG.CogStartingPositions[self.cogIndex]
            oldPos = self.suit.getPos()
            self.suit.setPos(startPos)
            if self.netTimeSentToStartByHit < timestamp:
                self.netTimeSentToStartByHit = timestamp
        else:
            self.notify.debug('localStamp = %s, lastLocalTimeStampFromAI=%s, ignoring respondToToonHit' % (localStamp, self.lastLocalTimeStampFromAI))
        self.notify.debug('respondToToonHit self.netTimeSentToStartByHit = %s' % self.netTimeSentToStartByHit)

    def clearGoal(self):
        self.goal = CTGG.NoGoal
        self.goalId = CTGG.InvalidGoalId

    def thinkAboutGettingBarrel(self):
        if not self.game:
            return
        if not hasattr(self.game, 'barrels'):
            return
        if self.goalId not in xrange(len(self.game.barrels)):
            return
        if not self.lastThinkTime:
            self.lastThinkTime = globalClock.getFrameTime()
        diffTime = globalClock.getFrameTime() - self.lastThinkTime
        barrel = self.game.barrels[self.goalId]
        barrelPos = barrel.getPos()
        myPos = self.suit.getPos()
        if not self.doneAdjust:
            myPos = self.lastPosFromAI
            self.notify.debug('thinkAboutGettingBarrel not doneAdjust setting position to %s' % myPos)
            self.suit.setPos(myPos)
            self.doneAdjust = True
        displacement = barrelPos - myPos
        distanceToToon = displacement.length()
        self.suit.headsUp(barrel)
        lengthTravelled = diffTime * self.cogSpeed
        if lengthTravelled > distanceToToon:
            lengthTravelled = distanceToToon
        displacement.normalize()
        dirVector = displacement
        dirVector *= lengthTravelled
        newPos = myPos + dirVector
        newPos.setZ(0)
        self.suit.setPos(newPos)
        self.adjustPlayRate(newPos, myPos, diffTime)
        self.lastThinkTime = globalClock.getFrameTime()

    def stopWalking(self, timestamp):
        localStamp = globalClockDelta.networkToLocalTime(timestamp, bits=32)
        if localStamp > self.lastLocalTimeStampFromAI:
            self.suit.loop('neutral')
            self.clearGoal()

    def thinkAboutRunAway(self):
        if not self.game:
            return
        if not self.lastThinkTime:
            self.lastThinkTime = globalClock.getFrameTime()
        diffTime = globalClock.getFrameTime() - self.lastThinkTime
        returnPos = CTGG.CogReturnPositions[self.goalId]
        myPos = self.suit.getPos()
        if not self.doneAdjust:
            myPos = self.lastPosFromAI
            self.suit.setPos(myPos)
            self.doneAdjust = True
        displacement = returnPos - myPos
        distanceToToon = displacement.length()
        tempNp = render.attachNewNode('tempRet')
        tempNp.setPos(returnPos)
        self.suit.headsUp(tempNp)
        tempNp.removeNode()
        lengthTravelled = diffTime * self.cogSpeed
        if lengthTravelled > distanceToToon:
            lengthTravelled = distanceToToon
        displacement.normalize()
        dirVector = displacement
        dirVector *= lengthTravelled
        newPos = myPos + dirVector
        newPos.setZ(0)
        self.suit.setPos(newPos)
        self.adjustPlayRate(newPos, myPos, diffTime)
        if (self.suit.getPos() - returnPos).length() < 0.0001:
            if not self.signalledAtReturnPos and self.barrel >= 0:
                self.game.sendCogAtReturnPos(self.cogIndex, self.barrel)
                self.signalledAtReturnPos = True
        self.lastThinkTime = globalClock.getFrameTime()

    def makeCogCarryBarrel(self, timestamp, inResponseClientStamp, barrelModel, barrelIndex, cogPos):
        if not self.game:
            return
        localTimeStamp = globalClockDelta.networkToLocalTime(timestamp, bits=32)
        self.lastLocalTimeStampFromAI = localTimeStamp
        inResponseGameTime = self.convertNetworkStampToGameTime(inResponseClientStamp)
        self.notify.debug('inResponseGameTime =%s timeSentToStart=%s' % (inResponseGameTime, self.netTimeSentToStartByHit))
        if inResponseClientStamp < self.netTimeSentToStartByHit and self.goal == CTGG.NoGoal:
            self.notify.warning('ignoring makeCogCarrybarrel')
        else:
            barrelModel.setPos(0, -1.0, 1.5)
            barrelModel.reparentTo(self.suit)
            self.suit.setPos(cogPos)
            self.barrel = barrelIndex

    def makeCogDropBarrel(self, timestamp, inResponseClientStamp, barrelModel, barrelIndex, barrelPos):
        localTimeStamp = globalClockDelta.networkToLocalTime(timestamp, bits=32)
        self.lastLocalTimeStampFromAI = localTimeStamp
        barrelModel.reparentTo(render)
        barrelModel.setPos(barrelPos)
        self.barrel = CTGG.NoBarrelCarried

    def respondToPieHit(self, timestamp):
        localStamp = globalClockDelta.networkToLocalTime(timestamp, bits=32)
        if self.netTimeSentToStartByHit < timestamp:
            self.clearGoal()
            self.showSplat()
            startPos = CTGG.CogStartingPositions[self.cogIndex]
            oldPos = self.suit.getPos()
            self.suit.setPos(startPos)
            if self.netTimeSentToStartByHit < timestamp:
                self.netTimeSentToStartByHit = timestamp
        else:
            self.notify.debug('localStamp = %s, lastLocalTimeStampFromAI=%s, ignoring respondToPieHit' % (localStamp, self.lastLocalTimeStampFromAI))
            self.notify.debug('respondToPieHit self.netTimeSentToStartByHit = %s' % self.netTimeSentToStartByHit)

    def cleanup(self):
        self.clearGoal()
        self.ignoreAll()
        self.suit.delete()
        if self.kaboomTrack and self.kaboomTrack.isPlaying():
            self.kaboomTrack.finish()
        self.suit = None
        self.game = None
        return

    def adjustPlayRate(self, newPos, oldPos, diffTime):
        lengthTravelled = (newPos - oldPos).length()
        if diffTime:
            speed = lengthTravelled / diffTime
        else:
            speed = self.cogSpeed
        rateMult = speed / self.cogSpeed
        newRate = rateMult * self.defaultPlayRate
        self.suit.setPlayRate(newRate, 'walk')

    def commonMove(self):
        if not self.lastThinkTime:
            self.lastThinkTime = globalClock.getFrameTime()
        dt = globalClock.getFrameTime() - self.lastThinkTime
        self.oldpos = self.suit.getPos()
        pos = self.suit.getPos()
        pos += self.velocity * dt
        self.suit.setPos(pos)
        self.seeFriends()
        acc = Vec3(0, 0, 0)
        self.accumulate(acc, self.getTargetVector())
        if self.numFlockmatesSeen > 0:
            keepDistanceVector = self.keepDistance()
            oldAcc = Vec3(acc)
            self.accumulate(acc, keepDistanceVector)
            if self.cogIndex == 0:
                pass
        if acc.length() > self.maxAcceleration:
            acc.normalize()
            acc *= self.maxAcceleration
        self.oldVelocity = self.velocity
        self.velocity += acc
        if self.velocity.length() > self.maxVelocity:
            self.velocity.normalize()
            self.velocity *= self.maxVelocity
        forwardVec = Vec3(1, 0, 0)
        heading = rad2Deg(math.atan2(self.velocity[1], self.velocity[0]))
        heading -= 90
        self.suit.setH(heading)

    def getTargetVector(self):
        targetPos = Point3(0, 0, 0)
        if self.goal == CTGG.ToonGoal:
            av = self.game.getAvatar(self.goalId)
            if av:
                targetPos = av.getPos()
        elif self.goal == CTGG.BarrelGoal:
            barrel = self.game.barrels[self.goalId]
            targetPos = barrel.getPos()
        elif self.goal == CTGG.RunAwayGoal:
            targetPos = CTGG.CogReturnPositions[self.goalId]
        targetPos.setZ(0)
        myPos = self.suit.getPos()
        diff = targetPos - myPos
        if diff.length() > 1.0:
            diff.normalize()
            diff *= 1.0
        return diff

    def accumulate(self, accumulator, valueToAdd):
        accumulator += valueToAdd
        return accumulator.length()

    def seeFriends(self):
        self.clearVisibleList()
        for cogIndex in self.game.cogInfo.keys():
            if cogIndex == self.cogIndex:
                continue
            if self.sameGoal(cogIndex):
                dist = self.canISee(cogIndex)
                if dist != self.Infinity:
                    self.addToVisibleList(cogIndex)
                    if dist < self.distToNearestFlockmate:
                        self.nearestFlockmate = cogIndex
                        self.distToNearestFlockmate = dist

        return self.numFlockmatesSeen

    def clearVisibleList(self):
        self.visibleFriendsList = []
        self.numFlockmatesSeen = 0
        self.nearestFlockmate = None
        self.distToNearestFlockmate = self.Infinity
        return

    def addToVisibleList(self, cogIndex):
        if self.numFlockmatesSeen < self.MaxFriendsVisible:
            self.visibleFriendsList.append(cogIndex)
            self.numFlockmatesSeen += 1
            if self.cogIndex == 0:
                pass

    def canISee(self, cogIndex):
        if self.cogIndex == cogIndex:
            return self.Infinity
        cogThief = self.game.getCogThief(cogIndex)
        distance = self.suit.getDistance(cogThief.suit)
        if distance < self.perceptionRange:
            return distance
        return self.Infinity

    def sameGoal(self, cogIndex):
        cogThief = self.game.getCogThief(cogIndex)
        result = cogThief.goalId == self.goalId and cogThief.goal == self.goal
        return result

    def keepDistance(self):
        ratio = self.distToNearestFlockmate / self.SeparationDistance
        nearestThief = self.game.getCogThief(self.nearestFlockmate)
        change = nearestThief.suit.getPos() - self.suit.getPos()
        if ratio < self.MinUrgency:
            ratio = self.MinUrgency
        if ratio > self.MaxUrgency:
            ratio = self.MaxUrgency
        if self.distToNearestFlockmate < self.SeparationDistance:
            change.normalize()
            change *= -(1 - ratio)
        elif self.distToNearestFlockmate > self.SeparationDistance:
            change.normalize()
            change *= ratio
        else:
            change = Vec3(0, 0, 0)
        return change

    def showKaboom(self):
        if self.kaboomTrack and self.kaboomTrack.isPlaying():
            self.kaboomTrack.finish()
        self.kaboom.reparentTo(render)
        self.kaboom.setPos(self.suit.getPos())
        self.kaboom.setZ(3)
        self.kaboomTrack = Parallel(SoundInterval(self.kaboomSound, volume=0.5), Sequence(Func(self.kaboom.showThrough), LerpScaleInterval(self.kaboom, duration=0.5, scale=Point3(10, 10, 10), startScale=Point3(1, 1, 1), blendType='easeOut'), Func(self.kaboom.hide)))
        self.kaboomTrack.start()

    def showSplat(self):
        if self.kaboomTrack and self.kaboomTrack.isPlaying():
            self.kaboomTrack.finish()
        self.splat.reparentTo(render)
        self.splat.setPos(self.suit.getPos())
        self.splat.setZ(3)
        self.kaboomTrack = Parallel(SoundInterval(self.pieHitSound, volume=1.0), Sequence(Func(self.splat.showThrough), LerpScaleInterval(self.splat, duration=0.5, scale=1.75, startScale=Point3(0.1, 0.1, 0.1), blendType='easeOut'), Func(self.splat.hide)))
        self.kaboomTrack.start()
