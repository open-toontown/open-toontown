import random
from pandac.PandaModules import *
from direct.interval.FunctionInterval import Wait, Func
from direct.interval.MetaInterval import Sequence, Parallel
from direct.showbase.PythonUtil import lerp, Enum
from direct.fsm import FSM
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals
from toontown.minigame.OrthoDrive import OrthoDrive
from toontown.minigame.OrthoWalk import OrthoWalk
from toontown.parties.activityFSMs import DanceActivityFSM
from toontown.parties.PartyGlobals import ActivityIds, ActivityTypes
from toontown.parties.PartyGlobals import DancePatternToAnims, DanceAnimToName
from toontown.parties.DistributedPartyActivity import DistributedPartyActivity
from toontown.parties.PartyDanceActivityToonFSM import PartyDanceActivityToonFSM
from toontown.parties.PartyDanceActivityToonFSM import ToonDancingStates
from toontown.parties.KeyCodes import KeyCodes
from toontown.parties.KeyCodesGui import KeyCodesGui
from toontown.parties import PartyGlobals
DANCE_FLOOR_COLLISION = 'danceFloor_collision'
DanceViews = Enum(('Normal', 'Dancing', 'Isometric'))

class DistributedPartyDanceActivityBase(DistributedPartyActivity):
    notify = directNotify.newCategory('DistributedPartyDanceActivity')

    def __init__(self, cr, actId, dancePatternToAnims, model = 'phase_13/models/parties/danceFloor'):
        DistributedPartyActivity.__init__(self, cr, actId, ActivityTypes.Continuous)
        self.model = model
        self.danceFloor = None
        self.localToonDancing = False
        self.keyCodes = None
        self.gui = None
        self.currentCameraMode = None
        self.orthoWalk = None
        self.cameraParallel = None
        self.localToonDanceSequence = None
        self.localPatternsMatched = []
        self.dancePatternToAnims = dancePatternToAnims
        self.dancingToonFSMs = {}
        return

    def generateInit(self):
        self.notify.debug('generateInit')
        DistributedPartyActivity.generateInit(self)
        self.keyCodes = KeyCodes(patterns=self.dancePatternToAnims.keys())
        self.gui = KeyCodesGui(self.keyCodes)
        self.__initOrthoWalk()
        self.activityFSM = DanceActivityFSM(self)

    def announceGenerate(self):
        DistributedPartyActivity.announceGenerate(self)
        self.activityFSM.request('Active')

    def load(self):
        DistributedPartyActivity.load(self)
        self.danceFloor = loader.loadModel(self.model)
        self.danceFloor.reparentTo(self.getParentNodePath())
        self.danceFloor.setPos(self.x, self.y, 0.0)
        self.danceFloor.setH(self.h)
        self.danceFloor.wrtReparentTo(render)
        self.sign.setPos(22, -22, 0)
        floor = self.danceFloor.find('**/danceFloor_mesh')
        self.danceFloorSequence = Sequence(Wait(0.3), Func(floor.setH, floor, 36))
        discoBall = self.danceFloor.find('**/discoBall_mesh')
        self.discoBallSequence = Parallel(discoBall.hprInterval(6.0, Vec3(360, 0, 0)), Sequence(discoBall.posInterval(3, Point3(0, 0, 1), blendType='easeInOut'), discoBall.posInterval(3, Point3(0, 0, 0), blendType='easeInOut')))

    def unload(self):
        DistributedPartyActivity.unload(self)
        self.activityFSM.request('Disabled')
        if self.localToonDanceSequence is not None:
            self.localToonDanceSequence.finish()
        if self.localToonDancing:
            self.__localStopDancing()
        self.ignoreAll()
        if self.discoBallSequence is not None:
            self.discoBallSequence.finish()
        if self.danceFloorSequence is not None:
            self.danceFloorSequence.finish()
        del self.danceFloorSequence
        del self.discoBallSequence
        del self.localToonDanceSequence
        if self.danceFloor is not None:
            self.danceFloor.removeNode()
            self.danceFloor = None
        self.__destroyOrthoWalk()
        for toonId in self.dancingToonFSMs.keys():
            self.dancingToonFSMs[toonId].destroy()
            del self.dancingToonFSMs[toonId]

        del self.dancingToonFSMs
        del self.cameraParallel
        del self.currentCameraMode
        if self.keyCodes is not None:
            self.keyCodes.destroy()
            del self.keyCodes
        del self.activityFSM
        del self.gui
        del self.localPatternsMatched
        return

    def handleToonDisabled(self, toonId):
        self.notify.debug('handleToonDisabled avatar ' + str(toonId) + ' disabled')
        if self.dancingToonFSMs.has_key(toonId):
            self.dancingToonFSMs[toonId].request('cleanup')
            self.dancingToonFSMs[toonId].destroy()
            del self.dancingToonFSMs[toonId]

    def getTitle(self):
        self.notify.warning('define title for this dance activity')
        return TTLocalizer.PartyDanceActivityTitle

    def getInstructions(self):
        self.notify.warning('define instructions for this dance activity')
        return TTLocalizer.PartyDanceActivityInstructions

    def startActive(self):
        self.accept('enter' + DANCE_FLOOR_COLLISION, self.__handleEnterDanceFloor)
        self.accept('exit' + DANCE_FLOOR_COLLISION, self.__handleExitDanceFloor)
        self.danceFloorSequence.loop()
        self.discoBallSequence.loop()

    def finishActive(self):
        pass

    def startDisabled(self):
        self.ignore('enter' + DANCE_FLOOR_COLLISION)
        self.ignore('exit' + DANCE_FLOOR_COLLISION)
        self.discoBallSequence.pause()
        self.danceFloorSequence.pause()

    def finishDisabled(self):
        pass

    def __initOrthoWalk(self):
        self.notify.debug('Initialize Ortho Walk')
        orthoDrive = OrthoDrive(9.778)
        self.orthoWalk = OrthoWalk(orthoDrive, broadcast=True)

    def __destroyOrthoWalk(self):
        self.notify.debug('Destroy Ortho Walk')
        self.orthoWalk.stop()
        self.orthoWalk.destroy()
        del self.orthoWalk

    def __disableLocalControl(self):
        self.orthoWalk.stop()
        self.keyCodes.disable()
        self.keyCodesGui.disable()

    def __enableLocalControl(self):
        self.orthWalk.start()
        self.keyCodes.enable()
        self.keyCodesGui.enable()
        self.keyCodesGui.hideAll()

    def __handleEnterDanceFloor(self, collEntry):
        if not self.isLocalToonInActivity() and not self.localToonDancing:
            self.notify.debug('Toon enters dance floor collision area.')
            place = base.cr.playGame.getPlace()
            if place and hasattr(place, 'fsm'):
                place.fsm.request('activity')
            self.d_toonJoinRequest()
            place = base.cr.playGame.getPlace()
            if place and hasattr(place, 'fsm'):
                place.fsm.request('activity')

    def joinRequestDenied(self, reason):
        DistributedPartyActivity.joinRequestDenied(self, reason)
        self.showMessage(TTLocalizer.PartyActivityDefaultJoinDeny)
        place = base.cr.playGame.getPlace()
        if place and hasattr(place, 'fsm'):
            place.fsm.request('walk')

    def setToonsPlaying(self, toonIds, toonHeadings):
        self.notify.debug('setToonsPlaying')
        self.notify.debug('\ttoonIds: %s' % toonIds)
        self.notify.debug('\ttoonHeadings: %s' % toonHeadings)
        exitedToons, joinedToons = self.getToonsPlayingChanges(self.toonIds, toonIds)
        self.notify.debug('\texitedToons: %s' % exitedToons)
        self.notify.debug('\tjoinedToons: %s' % joinedToons)
        self.setToonIds(toonIds)
        self._processExitedToons(exitedToons)
        for toonId in joinedToons:
            if toonId != base.localAvatar.doId or toonId == base.localAvatar.doId and self.isLocalToonRequestStatus(PartyGlobals.ActivityRequestStatus.Joining):
                self._enableHandleToonDisabled(toonId)
                self.handleToonJoined(toonId, toonHeadings[toonIds.index(toonId)])
                if toonId == base.localAvatar.doId:
                    self._localToonRequestStatus = None

        return

    def handleToonJoined(self, toonId, h):
        self.notify.debug('handleToonJoined( toonId=%d, h=%.2f )' % (toonId, h))
        if base.cr.doId2do.has_key(toonId):
            toonFSM = PartyDanceActivityToonFSM(toonId, self, h)
            toonFSM.request('Init')
            self.dancingToonFSMs[toonId] = toonFSM
            if toonId == base.localAvatar.doId:
                self.__localStartDancing(h)

    def __localStartDancing(self, h):
        if not self.localToonDancing:
            place = base.cr.playGame.getPlace()
            if place and hasattr(place, 'fsm'):
                self.localToonDancing = True
                place.fsm.request('activity')
                self.__updateLocalToonState(ToonDancingStates.Run)
                self.__setViewMode(DanceViews.Dancing)
                self.gui.load()
                self.startRules()
                self.__localEnableControls()
            else:
                self.notify.warning('__localStartDancing, failed in playGame.getPlace()')

    def handleRulesDone(self):
        self.finishRules()

    def __localEnableControls(self):
        if not self.dancingToonFSMs.has_key(base.localAvatar.doId):
            self.notify.debug('no dancing FSM for local avatar, not enabling controls')
            return
        self.accept(KeyCodes.PATTERN_MATCH_EVENT, self.__doDanceMove)
        self.accept(KeyCodes.PATTERN_NO_MATCH_EVENT, self.__noDanceMoveMatch)
        self.acceptOnce(KeyCodes.KEY_DOWN_EVENT, self._handleKeyDown)
        self.accept(KeyCodes.KEY_UP_EVENT, self._handleKeyUp)
        self.keyCodes.enable()
        self.orthoWalk.start()
        self.gui.enable()
        self.gui.hideAll()

    def __localDisableControls(self):
        self.orthoWalk.stop()
        self.keyCodes.disable()
        self.gui.disable()
        self.ignore(KeyCodes.PATTERN_MATCH_EVENT)
        self.ignore(KeyCodes.PATTERN_NO_MATCH_EVENT)
        self.ignore(KeyCodes.KEY_DOWN_EVENT)
        self.ignore(KeyCodes.KEY_UP_EVENT)

    def __handleExitDanceFloor(self, collEntry):
        if self.localToonDanceSequence is not None:
            self.notify.debug('finishing %s' % self.localToonDanceSequence)
            self.localToonDanceSequence.finish()
            self.localToonDanceSequence = None
        self.finishRules()
        self.notify.debug('Toon exits dance floor collision area.')
        self.d_toonExitRequest()
        return

    def exitRequestDenied(self, reason):
        DistributedPartyActivity.exitRequestDenied(self, reason)
        if reason != PartyGlobals.DenialReasons.SilentFail:
            self.showMessage(TTLocalizer.PartyActivityDefaultExitDeny)

    def handleToonExited(self, toonId):
        self.notify.debug('exitDanceFloor %s' % toonId)
        if toonId == base.localAvatar.doId:
            self.__localStopDancing()

    def __localStopDancing(self):
        if self.localToonDancing:
            self.__localDisableControls()
            self.gui.unload()
            self.__setViewMode(DanceViews.Normal)
            self.__updateLocalToonState(ToonDancingStates.Cleanup)
            if base.cr.playGame.getPlace():
                if hasattr(base.cr.playGame.getPlace(), 'fsm'):
                    base.cr.playGame.getPlace().fsm.request('walk')
            self.localToonDancing = False

    def __doDanceMove(self, pattern):
        self.notify.debug('Dance move! %s' % pattern)
        anim = self.dancePatternToAnims.get(pattern)
        if anim:
            self.__updateLocalToonState(ToonDancingStates.DanceMove, anim)
            self.gui.setColor(0, 1, 0)
            self.gui.showText(DanceAnimToName.get(anim, anim))
            self.finishRules()
            if pattern not in self.localPatternsMatched:
                camNode = NodePath(self.uniqueName('danceCamNode'))
                camNode.reparentTo(base.localAvatar)
                camNode.lookAt(camera)
                camNode.setHpr(camNode.getH(), 0, 0)
                node2 = NodePath('tempCamNode')
                node2.reparentTo(camNode)
                node2.setPos(Point3(0, 15, 10))
                node2.lookAt(camNode)
                h = node2.getH() * (camera.getH(camNode) / abs(camera.getH(camNode)))
                node2.removeNode
                del node2
                hpr = camera.getHpr()
                pos = camera.getPos()
                camParent = camera.getParent()
                camera.wrtReparentTo(camNode)
                self.localToonDanceSequence = Sequence(Func(self.__localDisableControls), Parallel(camera.posInterval(0.5, Point3(0, 15, 10), blendType='easeIn'), camera.hprInterval(0.5, Point3(h, -20, 0), blendType='easeIn')), camNode.hprInterval(4.0, Point3(camNode.getH() - 360, 0, 0)), Func(camera.wrtReparentTo, camParent), Func(camNode.removeNode), Parallel(camera.posInterval(0.5, pos, blendType='easeOut'), camera.hprInterval(0.5, hpr, blendType='easeOut')), Func(self.__localEnableControls))
            else:
                self.localToonDanceSequence = Sequence(Func(self.__localDisableControls), Wait(2.0), Func(self.__localEnableControls))
            self.localToonDanceSequence.start()
            self.localPatternsMatched.append(pattern)

    def __noDanceMoveMatch(self):
        self.gui.setColor(1, 0, 0)
        self.gui.showText('No Match!')
        self.__updateLocalToonState(ToonDancingStates.DanceMove)
        self.localToonDanceSequence = Sequence(Func(self.__localDisableControls), Wait(1.0), Func(self.__localEnableControls))
        self.localToonDanceSequence.start()

    def _handleKeyDown(self, key, index):
        self.__updateLocalToonState(ToonDancingStates.Run)

    def _handleKeyUp(self, key):
        if not self.keyCodes.isAnyKeyPressed():
            self.__updateLocalToonState(ToonDancingStates.DanceMove)
            self.acceptOnce(KeyCodes.KEY_DOWN_EVENT, self._handleKeyDown)

    def __updateLocalToonState(self, state, anim = ''):
        self._requestToonState(base.localAvatar.doId, state, anim)
        self.d_updateDancingToon(state, anim)

    def d_updateDancingToon(self, state, anim):
        self.sendUpdate('updateDancingToon', [state, anim])

    def setDancingToonState(self, toonId, state, anim):
        if toonId != base.localAvatar.doId and self.dancingToonFSMs.has_key(toonId):
            self._requestToonState(toonId, state, anim)

    def _requestToonState(self, toonId, state, anim):
        if self.dancingToonFSMs.has_key(toonId):
            state = ToonDancingStates.getString(state)
            curState = self.dancingToonFSMs[toonId].getCurrentOrNextState()
            try:
                self.dancingToonFSMs[toonId].request(state, anim)
            except FSM.RequestDenied:
                self.notify.warning('could not go from state=%s to state %s' % (curState, state))

            if state == ToonDancingStates.getString(ToonDancingStates.Cleanup):
                self.notify.debug('deleting this fsm %s' % self.dancingToonFSMs[toonId])
                del self.dancingToonFSMs[toonId]
                if self.localToonDanceSequence:
                    self.notify.debug('forcing a finish of localToonDanceSequence')
                    self.localToonDanceSequence.finish()
                    self.localToonDanceSequence = None
        return

    def __setViewMode(self, mode):
        toon = base.localAvatar
        if mode == DanceViews.Normal:
            if self.cameraParallel is not None:
                self.cameraParallel.pause()
                self.cameraParallel = None
            camera.reparentTo(toon)
            base.localAvatar.startUpdateSmartCamera()
        elif mode == DanceViews.Dancing:
            base.localAvatar.stopUpdateSmartCamera()
            camera.wrtReparentTo(self.danceFloor)
            node = NodePath('temp')
            node.reparentTo(toon.getParent())
            node.setPos(Point3(0, -40, 20))
            node2 = NodePath('temp2')
            node2.reparentTo(self.danceFloor)
            node.reparentTo(node2)
            node2.setH(render, toon.getParent().getH())
            pos = node.getPos(self.danceFloor)
            node2.removeNode()
            node.removeNode()
            self.cameraParallel = Parallel(camera.posInterval(0.5, pos, blendType='easeIn'), camera.hprInterval(0.5, Point3(0, -27, 0), other=toon.getParent(), blendType='easeIn'))
            self.cameraParallel.start()
        self.currentCameraMode = mode
        return
