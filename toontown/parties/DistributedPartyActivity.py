from pandac.PandaModules import CollisionSphere, CollisionNode, CollisionTube
from pandac.PandaModules import TextNode, NodePath, Vec3, Point3
from direct.distributed.ClockDelta import globalClockDelta
from direct.distributed import DistributedObject
from direct.showbase import RandomNumGen
from direct.showbase import PythonUtil
from direct.interval.IntervalGlobal import Sequence, Parallel, ActorInterval
from direct.interval.FunctionInterval import Wait
from otp.avatar import Emote
from otp.otpbase import OTPGlobals
from toontown.toonbase import TTLocalizer
from toontown.parties import PartyGlobals
from toontown.minigame.MinigameRulesPanel import MinigameRulesPanel
from toontown.toontowngui import TTDialog
from toontown.parties.JellybeanRewardGui import JellybeanRewardGui
from toontown.parties.PartyUtils import getPartyActivityIcon, getCenterPosFromGridSize

class DistributedPartyActivity(DistributedObject.DistributedObject):

    def __init__(self, cr, activityId, activityType, wantLever = False, wantRewardGui = False):
        DistributedObject.DistributedObject.__init__(self, cr)
        self.activityId = activityId
        self.activityName = PartyGlobals.ActivityIds.getString(self.activityId)
        self.activityType = activityType
        self.wantLever = wantLever
        self.wantRewardGui = wantRewardGui
        self.messageGui = None
        self.rewardGui = None
        self.toonIds = []
        self._toonId2ror = {}
        childName = '%s' % self
        childName = childName[childName.rfind('.DistributedParty') + len('.DistributedParty'):childName.rfind('Activity instance')]
        if not hasattr(base, 'partyActivityDict'):
            base.partyActivityDict = {}
        base.partyActivityDict[childName] = self
        self.root = NodePath('root')
        self.rulesDoneEvent = 'rulesDone'
        self.modelCount = 500
        self.cleanupActions = []
        self.usesSmoothing = 0
        self.usesLookAround = 0
        self.difficultyOverride = None
        self.trolleyZoneOverride = None
        self._localToonRequestStatus = None
        return

    def localToonExiting(self):
        self._localToonRequestStatus = PartyGlobals.ActivityRequestStatus.Exiting

    def localToonJoining(self):
        self._localToonRequestStatus = PartyGlobals.ActivityRequestStatus.Joining

    def d_toonJoinRequest(self):
        if self._localToonRequestStatus is None:
            self.localToonJoining()
            self.sendUpdate('toonJoinRequest')
        return

    def d_toonExitRequest(self):
        if self._localToonRequestStatus is None:
            self.localToonExiting()
            self.sendUpdate('toonExitRequest')
        return

    def d_toonExitDemand(self):
        self.localToonExiting()
        self.sendUpdate('toonExitDemand')

    def joinRequestDenied(self, reason):
        self._localToonRequestStatus = None
        return

    def exitRequestDenied(self, reason):
        self._localToonRequestStatus = None
        return

    def handleToonJoined(self, toonId):
        self.notify.error('BASE: handleToonJoined should be overridden %s' % self.activityName)

    def handleToonExited(self, toonId):
        self.notify.error('BASE: handleToonExited should be overridden %s' % self.activityName)

    def handleToonDisabled(self, toonId):
        self.notify.error('BASE: handleToonDisabled should be overridden %s' % self.activityName)

    def setToonsPlaying(self, toonIds):
        exitedToons, joinedToons = self.getToonsPlayingChanges(self.toonIds, toonIds)
        self.setToonIds(toonIds)
        self._processExitedToons(exitedToons)
        self._processJoinedToons(joinedToons)

    def _processExitedToons(self, exitedToons):
        for toonId in exitedToons:
            if toonId != base.localAvatar.doId or toonId == base.localAvatar.doId and self.isLocalToonRequestStatus(PartyGlobals.ActivityRequestStatus.Exiting):
                toon = self.getAvatar(toonId)
                if toon is not None:
                    self.ignore(toon.uniqueName('disable'))
                self.handleToonExited(toonId)
                if toonId == base.localAvatar.doId:
                    self._localToonRequestStatus = None
                if toonId in self._toonId2ror:
                    self.cr.relatedObjectMgr.abortRequest(self._toonId2ror[toonId])
                    del self._toonId2ror[toonId]

        return

    def _processJoinedToons(self, joinedToons):
        for toonId in joinedToons:
            if toonId != base.localAvatar.doId or toonId == base.localAvatar.doId and self.isLocalToonRequestStatus(PartyGlobals.ActivityRequestStatus.Joining):
                if toonId not in self._toonId2ror:
                    request = self.cr.relatedObjectMgr.requestObjects([toonId], allCallback=self._handlePlayerPresent)
                    if toonId in self._toonId2ror:
                        del self._toonId2ror[toonId]
                    else:
                        self._toonId2ror[toonId] = request

    def _handlePlayerPresent(self, toons):
        toon = toons[0]
        toonId = toon.doId
        if toonId in self._toonId2ror:
            del self._toonId2ror[toonId]
        else:
            self._toonId2ror[toonId] = None
        self._enableHandleToonDisabled(toonId)
        self.handleToonJoined(toonId)
        if toonId == base.localAvatar.doId:
            self._localToonRequestStatus = None
        return

    def _enableHandleToonDisabled(self, toonId):
        toon = self.getAvatar(toonId)
        if toon is not None:
            self.acceptOnce(toon.uniqueName('disable'), self.handleToonDisabled, [toonId])
        else:
            self.notify.warning('BASE: unable to get handle to toon with toonId:%d. Hook for handleToonDisabled not set.' % toonId)
        return

    def isLocalToonRequestStatus(self, requestStatus):
        return self._localToonRequestStatus == requestStatus

    def setToonIds(self, toonIds):
        self.toonIds = toonIds

    def getToonsPlayingChanges(self, oldToonIds, newToonIds):
        oldToons = set(oldToonIds)
        newToons = set(newToonIds)
        exitedToons = oldToons.difference(newToons)
        joinedToons = newToons.difference(oldToons)
        return (list(exitedToons), list(joinedToons))

    def setUsesSmoothing(self):
        self.usesSmoothing = True

    def setUsesLookAround(self):
        self.usesLookAround = True

    def getInstructions(self):
        return TTLocalizer.DefaultPartyActivityInstructions

    def getParentNodePath(self):
        if hasattr(base.cr.playGame, 'hood') and base.cr.playGame.hood and hasattr(base.cr.playGame.hood, 'loader') and base.cr.playGame.hood.loader and hasattr(base.cr.playGame.hood.loader, 'geom') and base.cr.playGame.hood.loader.geom:
            return base.cr.playGame.hood.loader.geom
        else:
            self.notify.warning('Hood or loader not created, defaulting to render')
            return render

    def __createRandomNumGen(self):
        self.notify.debug('BASE: self.doId=0x%08X' % self.doId)
        self.randomNumGen = RandomNumGen.RandomNumGen(self.doId)

        def destroy(self = self):
            self.notify.debug('BASE: destroying random num gen')
            del self.randomNumGen

        self.cleanupActions.append(destroy)

    def generate(self):
        DistributedObject.DistributedObject.generate(self)
        self.notify.debug('BASE: generate, %s' % self.getTitle())
        self.__createRandomNumGen()

    def announceGenerate(self):
        DistributedObject.DistributedObject.announceGenerate(self)
        self.notify.debug('BASE: announceGenerate %s' % self.activityName)
        self.root.setName(self.activityName + 'Root')
        centeredX, centeredY = getCenterPosFromGridSize(self.x, self.y, PartyGlobals.ActivityInformationDict[self.activityId]['gridsize'])
        self.root.setPos(centeredX, centeredY, 0.0)
        self.root.setH(self.h)
        self.normalExit = True
        if self.wantLever:
            self.leverTriggerEvent = self.uniqueName('leverTriggerEvent')
        self.load()

        def cleanup(self = self):
            self.notify.debug('BASE: cleanup: normalExit=%s' % self.normalExit)
            base.cr.renderFrame()
            if self.normalExit:
                self.sendUpdate('toonExitRequest')

        self.cleanupActions.append(cleanup)

    def disable(self):
        self.notify.debug('BASE: disable')
        DistributedObject.DistributedObject.disable(self)
        rorToonIds = self._toonId2ror.keys()
        for toonId in rorToonIds:
            self.cr.relatedObjectMgr.abortRequest(self._toonId2ror[toonId])
            del self._toonId2ror[toonId]

        self.ignore(self.messageDoneEvent)
        if self.messageGui is not None and not self.messageGui.isEmpty():
            self.messageGui.cleanup()
            self.messageGui = None
        return

    def delete(self):
        self.notify.debug('BASE: delete')
        self.unload()
        self.ignoreAll()
        DistributedObject.DistributedObject.delete(self)

    def load(self):
        self.notify.debug('BASE: load')
        self.loadSign()
        if self.wantLever:
            self.loadLever()
        if self.wantRewardGui:
            self.showRewardDoneEvent = self.uniqueName('showRewardDoneEvent')
            self.rewardGui = JellybeanRewardGui(self.showRewardDoneEvent)
        self.messageDoneEvent = self.uniqueName('messageDoneEvent')
        self.root.reparentTo(self.getParentNodePath())
        self._enableCollisions()

    def loadSign(self):
        actNameForSign = self.activityName
        if self.activityId == PartyGlobals.ActivityIds.PartyJukebox40:
            actNameForSign = PartyGlobals.ActivityIds.getString(PartyGlobals.ActivityIds.PartyJukebox)
        elif self.activityId == PartyGlobals.ActivityIds.PartyDance20:
            actNameForSign = PartyGlobals.ActivityIds.getString(PartyGlobals.ActivityIds.PartyDance)
        self.sign = self.root.attachNewNode('%sSign' % self.activityName)
        self.signModel = self.party.defaultSignModel.copyTo(self.sign)
        self.signFlat = self.signModel.find('**/sign_flat')
        self.signFlatWithNote = self.signModel.find('**/sign_withNote')
        self.signTextLocator = self.signModel.find('**/signText_locator')
        textureNodePath = getPartyActivityIcon(self.party.activityIconsModel, actNameForSign)
        textureNodePath.setPos(0.0, -0.02, 2.2)
        textureNodePath.setScale(2.35)
        textureNodePath.copyTo(self.signFlat)
        textureNodePath.copyTo(self.signFlatWithNote)
        text = TextNode('noteText')
        text.setTextColor(0.2, 0.1, 0.7, 1.0)
        text.setAlign(TextNode.ACenter)
        text.setFont(OTPGlobals.getInterfaceFont())
        text.setWordwrap(10.0)
        text.setText('')
        self.noteText = self.signFlatWithNote.attachNewNode(text)
        self.noteText.setPosHpr(self.signTextLocator, 0.0, 0.0, 0.2, 0.0, 0.0, 0.0)
        self.noteText.setScale(0.2)
        self.signFlatWithNote.stash()
        self.signTextLocator.stash()

    def loadLever(self):
        self.lever = self.root.attachNewNode('%sLever' % self.activityName)
        self.leverModel = self.party.defaultLeverModel.copyTo(self.lever)
        self.controlColumn = NodePath('cc')
        column = self.leverModel.find('**/column')
        column.getChildren().reparentTo(self.controlColumn)
        self.controlColumn.reparentTo(column)
        self.stickHinge = self.controlColumn.attachNewNode('stickHinge')
        self.stick = self.party.defaultStickModel.copyTo(self.stickHinge)
        self.stickHinge.setHpr(0.0, 90.0, 0.0)
        self.stick.setHpr(0, -90.0, 0)
        self.stick.flattenLight()
        self.bottom = self.leverModel.find('**/bottom')
        self.bottom.wrtReparentTo(self.controlColumn)
        self.bottomPos = self.bottom.getPos()
        cs = CollisionSphere(0.0, 1.35, 2.0, 1.0)
        cs.setTangible(False)
        cn = CollisionNode(self.leverTriggerEvent)
        cn.addSolid(cs)
        cn.setIntoCollideMask(OTPGlobals.WallBitmask)
        self.leverTrigger = self.root.attachNewNode(cn)
        self.leverTrigger.reparentTo(self.lever)
        self.leverTrigger.stash()
        cs = CollisionTube(0.0, 2.7, 0.0, 0.0, 2.7, 3.0, 1.2)
        cn = CollisionNode('levertube')
        cn.addSolid(cs)
        cn.setIntoCollideMask(OTPGlobals.WallBitmask)
        self.leverTube = self.leverModel.attachNewNode(cn)
        host = base.cr.doId2do.get(self.party.partyInfo.hostId)
        if host is None:
            self.notify.debug('%s loadLever : Host has left the game before lever could be created.' % self.activityName)
            return
        scale = host.getGeomNode().getChild(0).getSz(render)
        self.leverModel.setScale(scale)
        self.controlColumn.setPos(0, 0, 0)
        host.setPosHpr(self.lever, 0, 0, 0, 0, 0, 0)
        host.pose('leverNeutral', 0)
        host.update()
        pos = host.rightHand.getPos(self.controlColumn)
        self.controlColumn.setPos(pos[0], pos[1], pos[2] - 1)
        self.bottom.setZ(host, 0.0)
        self.bottom.setPos(self.bottomPos[0], self.bottomPos[1], self.bottom.getZ())
        lookAtPoint = Point3(0.3, 0, 0.1)
        lookAtUp = Vec3(0, -1, 0)
        self.stickHinge.lookAt(host.rightHand, lookAtPoint, lookAtUp)
        host.play('walk')
        host.update()
        return

    def unloadLever(self):
        self.lever.removeNode()
        self.leverModel.removeNode()
        self.controlColumn.removeNode()
        self.stickHinge.removeNode()
        self.stick.removeNode()
        self.bottom.removeNode()
        self.leverTrigger.removeNode()
        self.leverTube.removeNode()
        del self.bottomPos
        del self.lever
        del self.leverModel
        del self.controlColumn
        del self.stickHinge
        del self.stick
        del self.bottom
        del self.leverTrigger
        del self.leverTube

    def _enableCollisions(self):
        if self.wantLever:
            self.leverTrigger.unstash()
            self.accept('enter%s' % self.leverTriggerEvent, self._leverPulled)

    def _disableCollisions(self):
        if self.wantLever:
            self.leverTrigger.stash()
            self.ignore('enter%s' % self.leverTriggerEvent)

    def _leverPulled(self, collEntry):
        self.notify.debug('_leverPulled : Someone pulled the lever!!! ')
        if self.activityType == PartyGlobals.ActivityTypes.HostInitiated and base.localAvatar.doId != self.party.partyInfo.hostId:
            return False
        return True

    def getToonPullingLeverInterval(self, toon):
        walkTime = 0.2
        reach = ActorInterval(toon, 'leverReach', playRate=2.0)
        pull = ActorInterval(toon, 'leverPull', startFrame=6)
        origPos = toon.getPos(render)
        origHpr = toon.getHpr(render)
        newPos = self.lever.getPos(render)
        newHpr = self.lever.getHpr(render)
        origHpr.setX(PythonUtil.fitSrcAngle2Dest(origHpr[0], newHpr[0]))
        toon.setPosHpr(origPos, origHpr)
        reachAndPull = Sequence(ActorInterval(toon, 'walk', loop=True, duration=walkTime - reach.getDuration()), reach, pull)
        leverSeq = Sequence(Wait(walkTime + reach.getDuration() - 0.1), self.stick.hprInterval(0.55, Point3(0.0, 25.0, 0.0), Point3(0.0, 0.0, 0.0)), Wait(0.3), self.stick.hprInterval(0.4, Point3(0.0, 0.0, 0.0), Point3(0.0, 25.0, 0.0)))
        returnSeq = Sequence(Parallel(toon.posInterval(walkTime, newPos, origPos), toon.hprInterval(walkTime, newHpr, origHpr), leverSeq, reachAndPull))
        return returnSeq

    def showMessage(self, message, endState = 'walk'):
        base.cr.playGame.getPlace().fsm.request('activity')
        self.acceptOnce(self.messageDoneEvent, self.__handleMessageDone)
        self.messageGui = TTDialog.TTGlobalDialog(doneEvent=self.messageDoneEvent, message=message, style=TTDialog.Acknowledge)
        self.messageGui.endState = endState

    def __handleMessageDone(self):
        self.ignore(self.messageDoneEvent)
        if hasattr(base.cr.playGame.getPlace(), 'fsm'):
            if self.messageGui and hasattr(self.messageGui, 'endState'):
                self.notify.info('__handleMessageDone (endState=%s)' % self.messageGui.endState)
                base.cr.playGame.getPlace().fsm.request(self.messageGui.endState)
            else:
                self.notify.warning("messageGui has no endState, defaulting to 'walk'")
                base.cr.playGame.getPlace().fsm.request('walk')
        if self.messageGui is not None and not self.messageGui.isEmpty():
            self.messageGui.cleanup()
            self.messageGui = None
        return

    def showJellybeanReward(self, earnedAmount, jarAmount, message):
        if not self.isLocalToonInActivity() or base.localAvatar.doId in self.getToonIdsAsList():
            messenger.send('DistributedPartyActivity-showJellybeanReward')
            base.cr.playGame.getPlace().fsm.request('activity')
            self.acceptOnce(self.showRewardDoneEvent, self.__handleJellybeanRewardDone)
            self.rewardGui.showReward(earnedAmount, jarAmount, message)

    def __handleJellybeanRewardDone(self):
        self.ignore(self.showRewardDoneEvent)
        self.handleRewardDone()

    def handleRewardDone(self):
        if base.cr.playGame.getPlace() and hasattr(base.cr.playGame.getPlace(), 'fsm'):
            base.cr.playGame.getPlace().fsm.request('walk')

    def setSignNote(self, note):
        self.noteText.node().setText(note)
        if len(note.strip()) > 0:
            self.signFlat.stash()
            self.signFlatWithNote.unstash()
            self.signTextLocator.unstash()
        else:
            self.signFlat.unstash()
            self.signFlatWithNote.stash()
            self.signTextLocator.stash()

    def unload(self):
        self.notify.debug('BASE: unload')
        self.finishRules()
        self._disableCollisions()
        self.signModel.removeNode()
        del self.signModel
        self.sign.removeNode()
        del self.sign
        self.ignoreAll()
        if self.wantLever:
            self.unloadLever()
        self.root.removeNode()
        del self.root
        del self.activityId
        del self.activityName
        del self.activityType
        del self.wantLever
        del self.messageGui
        if self.rewardGui is not None:
            self.rewardGui.destroy()
        del self.rewardGui
        if hasattr(self, 'toonIds'):
            del self.toonIds
        del self.rulesDoneEvent
        del self.modelCount
        del self.cleanupActions
        del self.usesSmoothing
        del self.usesLookAround
        del self.difficultyOverride
        del self.trolleyZoneOverride
        if hasattr(base, 'partyActivityDict'):
            del base.partyActivityDict
        return

    def setPartyDoId(self, partyDoId):
        self.party = base.cr.doId2do[partyDoId]

    def setX(self, x):
        self.x = x

    def setY(self, y):
        self.y = y

    def setH(self, h):
        self.h = h

    def setState(self, newState, timestamp):
        if newState == 'Active':
            self.activityStartTime = globalClockDelta.networkToLocalTime(timestamp)

    def turnOffSmoothingOnGuests(self):
        for toonId in self.toonIds:
            avatar = self.getAvatar(toonId)
            if avatar:
                if not self.usesSmoothing:
                    avatar.stopSmooth()
                if not self.usesLookAround:
                    avatar.stopLookAround()

    def getAvatar(self, toonId):
        if self.cr.doId2do.has_key(toonId):
            return self.cr.doId2do[toonId]
        else:
            self.notify.warning('BASE: getAvatar: No avatar in doId2do with id: ' + str(toonId))
            return None
        return None

    def getAvatarName(self, toonId):
        avatar = self.getAvatar(toonId)
        if avatar:
            return avatar.getName()
        else:
            return 'Unknown'

    def isLocalToonInActivity(self):
        result = False
        place = base.cr.playGame.getPlace()
        if place and place.__class__.__name__ == 'Party' and hasattr(place, 'fsm') and place.fsm:
            result = place.fsm.getCurrentState().getName() == 'activity'
        return result

    def getToonIdsAsList(self):
        return self.toonIds

    def startRules(self, timeout = PartyGlobals.DefaultRulesTimeout):
        self.notify.debug('BASE: startRules')
        self.accept(self.rulesDoneEvent, self.handleRulesDone)
        self.rulesPanel = MinigameRulesPanel('PartyRulesPanel', self.getTitle(), self.getInstructions(), self.rulesDoneEvent, timeout)
        base.setCellsAvailable(base.bottomCells + [base.leftCells[0], base.rightCells[1]], False)
        self.rulesPanel.load()
        self.rulesPanel.enter()

    def finishRules(self):
        self.notify.debug('BASE: finishRules')
        self.ignore(self.rulesDoneEvent)
        if hasattr(self, 'rulesPanel'):
            self.rulesPanel.exit()
            self.rulesPanel.unload()
            del self.rulesPanel
            base.setCellsAvailable(base.bottomCells + [base.leftCells[0], base.rightCells[1]], True)

    def handleRulesDone(self):
        self.notify.error('BASE: handleRulesDone should be overridden')

    def getTitle(self):
        return TTLocalizer.PartyActivityNameDict[self.activityId]['generic']

    def local2ActivityTime(self, timestamp):
        return timestamp - self.activityStartTime

    def activity2LocalTime(self, timestamp):
        return timestamp + self.activityStartTime

    def getCurrentActivityTime(self):
        return self.local2ActivityTime(globalClock.getFrameTime())

    def disableEmotes(self):
        Emote.globalEmote.disableAll(base.localAvatar)

    def enableEmotes(self):
        Emote.globalEmote.releaseAll(base.localAvatar)
