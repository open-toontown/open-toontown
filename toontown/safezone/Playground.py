from panda3d.core import LineSegs, NodePath, TextNode, Vec4
from panda3d.otp import NametagGlobals

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.fsm.ClassicFSM import ClassicFSM
from direct.fsm.State import State
from direct.gui.DirectLabel import DirectLabel
from direct.interval.IntervalGlobal import Func, LerpColorScaleInterval, Sequence
from direct.showbase.MessengerGlobal import messenger

from otp.distributed.TelemetryLimiter import RotationLimitToH, TLGatherAllAvs

from toontown.classicchars import CCharPaths
from toontown.hood.Place import Place
from toontown.quest import Quests
from toontown.toon.DeathForceAcknowledge import DeathForceAcknowledge
from toontown.toon.HealthForceAcknowledge import HealthForceAcknowledge
from toontown.toon.NPCForceAcknowledge import NPCForceAcknowledge
from toontown.toon.Toon import teleportDebug
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.toonbase.ToonBaseGlobal import base
from toontown.toontowngui import TTDialog
from toontown.trolley.Trolley import Trolley
from toontown.tutorial.TutorialForceAcknowledge import TutorialForceAcknowledge


class Playground(Place):
    notify = directNotify.newCategory('Playground')

    def __init__(self, loader, parentFSM, doneEvent):
        Place.__init__(self, loader, doneEvent)
        self.tfaDoneEvent = 'tfaDoneEvent'
        self.fsm = ClassicFSM('Playground', [
            State('start',
                        self.enterStart,
                        self.exitStart, [
                            'walk',
                            'deathAck',
                            'doorIn',
                            'tunnelIn']),
            State('walk',
                        self.enterWalk,
                        self.exitWalk, [
                            'drive',
                            'sit',
                            'stickerBook',
                            'TFA',
                            'DFA',
                            'trialerFA',
                            'trolley',
                            'final',
                            'doorOut',
                            'options',
                            'quest',
                            'purchase',
                            'stopped',
                            'fishing']),
            State('stickerBook',
                        self.enterStickerBook,
                        self.exitStickerBook, [
                            'walk',
                            'DFA',
                            'TFA',
                            'trolley',
                            'final',
                            'doorOut',
                            'quest',
                            'purchase',
                            'stopped',
                            'fishing',
                            'trialerFA']),
            State('sit',
                        self.enterSit,
                        self.exitSit, [
                            'walk',
                            'DFA',
                            'trialerFA']),
            State('drive',
                        self.enterDrive,
                        self.exitDrive, [
                            'walk',
                            'DFA',
                            'trialerFA']),
            State('trolley',
                        self.enterTrolley,
                        self.exitTrolley, [
                            'walk']),
            State('doorIn',
                        self.enterDoorIn,
                        self.exitDoorIn, [
                            'walk']),
            State('doorOut',
                        self.enterDoorOut,
                        self.exitDoorOut, [
                            'walk']),
            State('TFA',
                        self.enterTFA,
                        self.exitTFA, [
                            'TFAReject',
                            'DFA']),
            State('TFAReject',
                        self.enterTFAReject,
                        self.exitTFAReject, [
                            'walk']),
            State('trialerFA',
                        self.enterTrialerFA,
                        self.exitTrialerFA, [
                            'trialerFAReject',
                            'DFA']),
            State('trialerFAReject',
                        self.enterTrialerFAReject,
                        self.exitTrialerFAReject, [
                            'walk']),
            State('DFA',
                        self.enterDFA,
                        self.exitDFA, [
                            'DFAReject',
                            'NPCFA',
                            'HFA']),
            State('DFAReject',
                        self.enterDFAReject,
                        self.exitDFAReject, [
                            'walk']),
            State('NPCFA',
                        self.enterNPCFA,
                        self.exitNPCFA, [
                            'NPCFAReject',
                            'HFA']),
            State('NPCFAReject',
                        self.enterNPCFAReject,
                        self.exitNPCFAReject, [
                            'walk']),
            State('HFA',
                        self.enterHFA,
                        self.exitHFA, [
                            'HFAReject',
                            'teleportOut',
                            'tunnelOut']),
            State('HFAReject',
                        self.enterHFAReject,
                        self.exitHFAReject, [
                            'walk']),
            State('deathAck',
                        self.enterDeathAck,
                        self.exitDeathAck, [
                            'teleportIn']),
            State('teleportIn',
                        self.enterTeleportIn,
                        self.exitTeleportIn, [
                            'walk',
                            'popup']),
            State('popup',
                        self.enterPopup,
                        self.exitPopup, [
                            'walk']),
            State('teleportOut',
                        self.enterTeleportOut,
                        self.exitTeleportOut, [
                            'deathAck',
                            'teleportIn']),
            State('died',
                        self.enterDied,
                        self.exitDied, [
                            'final']),
            State('tunnelIn',
                        self.enterTunnelIn,
                        self.exitTunnelIn, [
                            'walk']),
            State('tunnelOut',
                        self.enterTunnelOut,
                        self.exitTunnelOut, [
                            'final']),
            State('quest',
                        self.enterQuest,
                        self.exitQuest, [
                            'walk']),
            State('purchase',
                        self.enterPurchase,
                        self.exitPurchase, [
                            'walk']),
            State('stopped',
                        self.enterStopped,
                        self.exitStopped, [
                            'walk']),
            State('fishing',
                        self.enterFishing,
                        self.exitFishing, [
                            'walk']),
            State('final',
                        self.enterFinal,
                        self.exitFinal, [
                            'start'])],
            'start', 'final')
        self.parentFSM = parentFSM
        self.tunnelOriginList = []
        self.trolleyDoneEvent = 'trolleyDone'
        self.hfaDoneEvent = 'hfaDoneEvent'
        self.npcfaDoneEvent = 'npcfaDoneEvent'
        self.dialog = None
        self.deathAckBox = None

    def enter(self, requestStatus):
        self.fsm.enterInitialState()
        messenger.send('enterPlayground')
        self.accept('doorDoneEvent', self.handleDoorDoneEvent)
        self.accept('DistributedDoor_doorTrigger', self.handleDoorTrigger)
        base.playMusic(self.loader.music, looping=1, volume=0.8)
        self.loader.geom.reparentTo(base.render)
        for i in self.loader.nodeList:
            self.loader.enterAnimatedProps(i)

        self._telemLimiter = TLGatherAllAvs('Playground', RotationLimitToH)

        def __lightDecorationOn__():
            geom = base.cr.playGame.hood.loader.geom
            self.loader.hood.halloweenLights = geom.findAllMatches('**/*light*')
            self.loader.hood.halloweenLights += geom.findAllMatches('**/*lamp*')
            self.loader.hood.halloweenLights += geom.findAllMatches('**/prop_snow_tree*')
            for light in self.loader.hood.halloweenLights:
                light.setColorScaleOff(0)

        newsManager = base.cr.newsManager
        if newsManager:
            holidayIds = base.cr.newsManager.getDecorationHolidayId()
            if (ToontownGlobals.HALLOWEEN_COSTUMES in holidayIds or ToontownGlobals.SPOOKY_COSTUMES in holidayIds) and self.loader.hood.spookySkyFile:
                lightsOff = Sequence(LerpColorScaleInterval(base.cr.playGame.hood.loader.geom, 0.1, Vec4(0.55, 0.55, 0.65, 1)), Func(self.loader.hood.startSpookySky), Func(__lightDecorationOn__))
                lightsOff.start()
            else:
                self.loader.hood.startSky()
                lightsOn = LerpColorScaleInterval(base.cr.playGame.hood.loader.geom, 0.1, Vec4(1, 1, 1, 1))
                lightsOn.start()
        else:
            self.loader.hood.startSky()
            lightsOn = LerpColorScaleInterval(base.cr.playGame.hood.loader.geom, 0.1, Vec4(1, 1, 1, 1))
            lightsOn.start()

        NametagGlobals.setMasterArrowsOn(1)
        self.zoneId = requestStatus['zoneId']
        self.tunnelOriginList = base.cr.hoodMgr.addLinkTunnelHooks(self, self.loader.nodeList, self.zoneId)
        how = requestStatus['how']
        if how == 'teleportIn':
            how = 'deathAck'

        self.fsm.request(how, [requestStatus])

    def exit(self):
        self.ignoreAll()
        messenger.send('exitPlayground')
        self._telemLimiter.destroy()
        del self._telemLimiter
        for node in self.tunnelOriginList:
            node.removeNode()

        del self.tunnelOriginList
        self.loader.geom.reparentTo(base.hidden)

        def __lightDecorationOff__():
            for light in self.loader.hood.halloweenLights:
                light.reparentTo(base.hidden)

        NametagGlobals.setMasterArrowsOn(0)
        for i in self.loader.nodeList:
            self.loader.exitAnimatedProps(i)

        self.loader.hood.stopSky()
        self.loader.music.stop()

    def load(self):
        Place.load(self)
        self.parentFSM.getStateNamed('playground').addChild(self.fsm)

    def unload(self):
        self.parentFSM.getStateNamed('playground').removeChild(self.fsm)
        del self.parentFSM
        del self.fsm
        if self.dialog:
            self.dialog.cleanup()
            self.dialog = None

        if self.deathAckBox:
            self.deathAckBox.cleanup()
            self.deathAckBox = None

        TTDialog.cleanupDialog('globalDialog')
        self.ignoreAll()
        Place.unload(self)

    def showTreasurePoints(self, points):
        self.hideDebugPointText()
        for i in range(len(points)):
            p = points[i]
            self.showDebugPointText(str(i), p)

    def showDropPoints(self, points):
        self.hideDebugPointText()
        for i in range(len(points)):
            p = points[i]
            self.showDebugPointText(str(i), p)

    def showPaths(self):
        pass

    def hidePaths(self):
        self.hideDebugPointText()

    def showPathPoints(self, paths, waypoints = None):
        self.hideDebugPointText()
        lines = LineSegs()
        lines.setColor(1, 0, 0, 1)
        for name, pointDef in list(paths.items()):
            self.showDebugPointText(name, pointDef[0])
            for connectTo in pointDef[1]:
                toDef = paths[connectTo]
                fromP = pointDef[0]
                toP = toDef[0]
                lines.moveTo(fromP[0], fromP[1], fromP[2] + 2.0)
                wpList = CCharPaths.getWayPoints(name, connectTo, paths, waypoints)
                for wp in wpList:
                    lines.drawTo(wp[0], wp[1], wp[2] + 2.0)
                    self.showDebugPointText('*', wp)

                lines.drawTo(toP[0], toP[1], toP[2] + 2.0)

        self.debugText.attachNewNode(lines.create())

    def hideDebugPointText(self):
        if hasattr(self, 'debugText'):
            children = self.debugText.getChildren()
            for i in range(children.getNumPaths()):
                children[i].removeNode()

    def showDebugPointText(self, text, point):
        if not hasattr(self, 'debugText'):
            self.debugText = self.loader.geom.attachNewNode('debugText')
            self.debugTextNode = TextNode('debugTextNode')
            self.debugTextNode.setTextColor(1, 0, 0, 1)
            self.debugTextNode.setAlign(TextNode.ACenter)
            self.debugTextNode.setFont(ToontownGlobals.getSignFont())

        self.debugTextNode.setText(text)
        np = self.debugText.attachNewNode(self.debugTextNode.generate())
        np.setPos(point[0], point[1], point[2])
        np.setScale(4.0)
        np.setBillboardPointEye()

    def enterTrolley(self):
        base.localAvatar.laffMeter.start()
        base.localAvatar.b_setAnimState('off', 1)
        base.localAvatar.cantLeaveGame = 1
        self.accept(self.trolleyDoneEvent, self.handleTrolleyDone)
        self.trolley = Trolley(self, self.fsm, self.trolleyDoneEvent)
        self.trolley.load()
        self.trolley.enter()

    def exitTrolley(self):
        base.localAvatar.laffMeter.stop()
        base.localAvatar.cantLeaveGame = 0
        self.ignore(self.trolleyDoneEvent)
        self.trolley.unload()
        self.trolley.exit()
        del self.trolley

    def detectedTrolleyCollision(self):
        self.fsm.request('trolley')

    def handleTrolleyDone(self, doneStatus):
        self.notify.debug('handling trolley done event')
        mode = doneStatus['mode']
        if mode == 'reject':
            self.fsm.request('walk')
        elif mode == 'exit':
            self.fsm.request('walk')
        elif mode == 'minigame':
            self.doneStatus = {'loader': 'minigame',
             'where': 'minigame',
             'hoodId': self.loader.hood.id,
             'zoneId': doneStatus['zoneId'],
             'shardId': None,
             'minigameId': doneStatus['minigameId']}
            messenger.send(self.doneEvent)
        else:
            self.notify.error('Unknown mode: ' + mode + ' in handleTrolleyDone')

    def debugStartMinigame(self, zoneId, minigameId):
        self.doneStatus = {'loader': 'minigame',
         'where': 'minigame',
         'hoodId': self.loader.hood.id,
         'zoneId': zoneId,
         'shardId': None,
         'minigameId': minigameId}
        messenger.send(self.doneEvent)

    def enterTFACallback(self, requestStatus, doneStatus):
        self.tfa.exit()
        del self.tfa
        doneStatusMode = doneStatus['mode']
        if doneStatusMode == 'complete':
            self.requestLeave(requestStatus)
        elif doneStatusMode == 'incomplete':
            self.fsm.request('TFAReject')
        else:
            self.notify.error('Unknown mode: %s' % doneStatusMode)

    def enterDFACallback(self, requestStatus, doneStatus):
        self.dfa.exit()
        del self.dfa
        ds = doneStatus['mode']
        if ds == 'complete':
            self.fsm.request('NPCFA', [requestStatus])
        elif ds == 'incomplete':
            self.fsm.request('DFAReject')
        else:
            self.notify.error('Unknown done status for DownloadForceAcknowledge: ' + repr(doneStatus))

    def enterHFA(self, requestStatus):
        self.acceptOnce(self.hfaDoneEvent, self.enterHFACallback, [requestStatus])
        self.hfa = HealthForceAcknowledge(self.hfaDoneEvent)
        self.hfa.enter(1)

    def exitHFA(self):
        self.ignore(self.hfaDoneEvent)

    def enterHFACallback(self, requestStatus, doneStatus):
        self.hfa.exit()
        del self.hfa
        if doneStatus['mode'] == 'complete':
            if requestStatus.get('partyHat', 0):
                outHow = {'teleportIn': 'tunnelOut'}
            else:
                outHow = {'teleportIn': 'teleportOut',
                 'tunnelIn': 'tunnelOut',
                 'doorIn': 'doorOut'}

            self.fsm.request(outHow[requestStatus['how']], [requestStatus])
        elif doneStatus['mode'] == 'incomplete':
            self.fsm.request('HFAReject')
        else:
            self.notify.error('Unknown done status for HealthForceAcknowledge: ' + repr(doneStatus))

    def enterHFAReject(self):
        self.fsm.request('walk')

    def exitHFAReject(self):
        pass

    def enterNPCFA(self, requestStatus):
        self.acceptOnce(self.npcfaDoneEvent, self.enterNPCFACallback, [requestStatus])
        self.npcfa = NPCForceAcknowledge(self.npcfaDoneEvent)
        self.npcfa.enter()

    def exitNPCFA(self):
        self.ignore(self.npcfaDoneEvent)

    def enterNPCFACallback(self, requestStatus, doneStatus):
        self.npcfa.exit()
        del self.npcfa
        if doneStatus['mode'] == 'complete':
            self.fsm.request('HFA', [requestStatus])
        elif doneStatus['mode'] == 'incomplete':
            self.fsm.request('NPCFAReject')
        else:
            self.notify.error('Unknown done status for NPCForceAcknowledge: ' + repr(doneStatus))

    def enterNPCFAReject(self):
        self.fsm.request('walk')

    def exitNPCFAReject(self):
        pass

    def enterWalk(self, teleportIn = 0):
        if self.deathAckBox:
            self.ignore('deathAck')
            self.deathAckBox.cleanup()
            self.deathAckBox = None

        Place.enterWalk(self, teleportIn)

    def enterDeathAck(self, requestStatus):
        self.deathAckBox = None
        self.fsm.request('teleportIn', [requestStatus])

    def exitDeathAck(self):
        if self.deathAckBox:
            self.ignore('deathAck')
            self.deathAckBox.cleanup()
            self.deathAckBox = None

    def enterTeleportIn(self, requestStatus):
        imgScale = 0.25
        if self.dialog:
            x, y, z, h, p, r = base.cr.hoodMgr.getPlaygroundCenterFromId(self.loader.hood.id)
        elif base.localAvatar.hp < 1:
            requestStatus['nextState'] = 'popup'
            x, y, z, h, p, r = base.cr.hoodMgr.getPlaygroundCenterFromId(self.loader.hood.id)
            self.accept('deathAck', self.__handleDeathAck, extraArgs=[requestStatus])
            self.deathAckBox = DeathForceAcknowledge(doneEvent='deathAck')
        elif base.localAvatar.hp > 0 and (Quests.avatarHasTrolleyQuest(base.localAvatar) or Quests.avatarHasFirstCogQuest(base.localAvatar) or Quests.avatarHasFriendQuest(base.localAvatar) or Quests.avatarHasPhoneQuest(base.localAvatar) and Quests.avatarHasCompletedPhoneQuest(base.localAvatar)) and self.loader.hood.id == ToontownGlobals.ToontownCentral:
            requestStatus['nextState'] = 'popup'
            imageModel = base.loader.loadModel('phase_4/models/gui/tfa_images')
            if base.localAvatar.quests[0][0] == Quests.TROLLEY_QUEST_ID:
                if not Quests.avatarHasCompletedTrolleyQuest(base.localAvatar):
                    x, y, z, h, p, r = base.cr.hoodMgr.getDropPoint(base.cr.hoodMgr.ToontownCentralInitialDropPoints)
                    msg = TTLocalizer.NPCForceAcknowledgeMessage3
                    imgNodePath = imageModel.find('**/trolley-dialog-image')
                    imgPos = (0, 0, 0.04)
                    imgScale = 0.5
                else:
                    x, y, z, h, p, r = base.cr.hoodMgr.getDropPoint(base.cr.hoodMgr.ToontownCentralHQDropPoints)
                    msg = TTLocalizer.NPCForceAcknowledgeMessage4
                    imgNodePath = imageModel.find('**/hq-dialog-image')
                    imgPos = (0, 0, -0.02)
                    imgScale = 0.5
            elif base.localAvatar.quests[0][0] == Quests.FIRST_COG_QUEST_ID:
                if not Quests.avatarHasCompletedFirstCogQuest(base.localAvatar):
                    x, y, z, h, p, r = base.cr.hoodMgr.getDropPoint(base.cr.hoodMgr.ToontownCentralTunnelDropPoints)
                    msg = TTLocalizer.NPCForceAcknowledgeMessage5
                    imgNodePath = imageModel.find('**/tunnelSignA')
                    imgPos = (0, 0, 0.04)
                    imgScale = 0.5
                else:
                    x, y, z, h, p, r = base.cr.hoodMgr.getDropPoint(base.cr.hoodMgr.ToontownCentralHQDropPoints)
                    msg = TTLocalizer.NPCForceAcknowledgeMessage6
                    imgNodePath = imageModel.find('**/hq-dialog-image')
                    imgPos = (0, 0, 0.05)
                    imgScale = 0.5
            elif base.localAvatar.quests[0][0] == Quests.FRIEND_QUEST_ID:
                if not Quests.avatarHasCompletedFriendQuest(base.localAvatar):
                    x, y, z, h, p, r = base.cr.hoodMgr.getDropPoint(base.cr.hoodMgr.ToontownCentralInitialDropPoints)
                    msg = TTLocalizer.NPCForceAcknowledgeMessage7
                    gui = base.loader.loadModel('phase_3.5/models/gui/friendslist_gui')
                    imgNodePath = gui.find('**/FriendsBox_Closed')
                    imgPos = (0, 0, 0.04)
                    imgScale = 1.0
                    gui.removeNode()
                else:
                    x, y, z, h, p, r = base.cr.hoodMgr.getDropPoint(base.cr.hoodMgr.ToontownCentralHQDropPoints)
                    msg = TTLocalizer.NPCForceAcknowledgeMessage8
                    imgNodePath = imageModel.find('**/hq-dialog-image')
                    imgPos = (0, 0, 0.05)
                    imgScale = 0.5
            elif base.localAvatar.quests[0][0] == Quests.PHONE_QUEST_ID:
                if Quests.avatarHasCompletedPhoneQuest(base.localAvatar):
                    x, y, z, h, p, r = base.cr.hoodMgr.getDropPoint(base.cr.hoodMgr.ToontownCentralHQDropPoints)
                    msg = TTLocalizer.NPCForceAcknowledgeMessage9
                    imgNodePath = imageModel.find('**/hq-dialog-image')
                    imgPos = (0, 0, 0.05)
                    imgScale = 0.5

            self.dialog = TTDialog.TTDialog(text=msg, command=self.__cleanupDialog, style=TTDialog.Acknowledge)
            imgLabel = DirectLabel(parent=self.dialog, relief=None, pos=imgPos, scale=TTLocalizer.PimgLabel, image=imgNodePath, image_scale=imgScale)
            imageModel.removeNode()
        else:
            requestStatus['nextState'] = 'walk'
            x, y, z, h, p, r = base.cr.hoodMgr.getPlaygroundCenterFromId(self.loader.hood.id)

        base.localAvatar.detachNode()
        base.localAvatar.setPosHpr(base.render, x, y, z, h, p, r)
        Place.enterTeleportIn(self, requestStatus)

    def __cleanupDialog(self, value):
        if self.dialog:
            self.dialog.cleanup()
            self.dialog = None

        if hasattr(self, 'fsm'):
            self.fsm.request('walk', [1])

    def __handleDeathAck(self, requestStatus):
        if self.deathAckBox:
            self.ignore('deathAck')
            self.deathAckBox.cleanup()
            self.deathAckBox = None

        self.fsm.request('walk', [1])

    def enterPopup(self, teleportIn = 0):
        if base.localAvatar.hp < 1:
            base.localAvatar.b_setAnimState('Sad', 1)
        else:
            base.localAvatar.b_setAnimState('neutral', 1.0)

        self.accept('teleportQuery', self.handleTeleportQuery)
        base.localAvatar.setTeleportAvailable(1)
        base.localAvatar.startSleepWatch(self.__handleFallingAsleepPopup)

    def exitPopup(self):
        base.localAvatar.stopSleepWatch()
        base.localAvatar.setTeleportAvailable(0)
        self.ignore('teleportQuery')

    def __handleFallingAsleepPopup(self, task):
        if hasattr(self, 'fsm'):
            self.fsm.request('walk')
            base.localAvatar.forceGotoSleep()

        return task.done

    def enterTeleportOut(self, requestStatus):
        Place.enterTeleportOut(self, requestStatus, self.__teleportOutDone)

    def __teleportOutDone(self, requestStatus):
        teleportDebug(requestStatus, 'Playground.__teleportOutDone(%s)' % (requestStatus,))
        if hasattr(self, 'activityFsm'):
            self.activityFsm.requestFinalState()

        hoodId = requestStatus['hoodId']
        zoneId = requestStatus['zoneId']
        shardId = requestStatus['shardId']
        if hoodId == self.loader.hood.hoodId and zoneId == self.loader.hood.hoodId and shardId == None:
            teleportDebug(requestStatus, 'same playground')
            self.fsm.request('deathAck', [requestStatus])
        elif hoodId == ToontownGlobals.MyEstate:
            teleportDebug(requestStatus, 'estate')
            self.getEstateZoneAndGoHome(requestStatus)
        else:
            teleportDebug(requestStatus, 'different hood/zone')
            self.doneStatus = requestStatus
            messenger.send(self.doneEvent)

    def exitTeleportOut(self):
        Place.exitTeleportOut(self)

    def createPlayground(self, dnaFile):
        base.loader.loadDNAFile(self.loader.dnaStore, self.safeZoneStorageDNAFile)
        node = base.loader.loadDNAFile(self.loader.dnaStore, dnaFile)
        if node.getNumParents() == 1:
            self.geom = NodePath(node.getParent(0))
            self.geom.reparentTo(base.hidden)
        else:
            self.geom = base.hidden.attachNewNode(node)

        self.makeDictionaries(self.loader.dnaStore)
        self.tunnelOriginList = base.cr.hoodMgr.addLinkTunnelHooks(self, self.nodeList, self.zoneId)
        self.geom.flattenMedium()
        gsg = base.win.getGsg()
        if gsg:
            self.geom.prepareScene(gsg)

    def makeDictionaries(self, dnaStore):
        self.nodeList = []
        for i in range(dnaStore.getNumDNAVisGroups()):
            groupFullName = dnaStore.getDNAVisGroupName(i)
            groupNode = self.geom.find('**/' + groupFullName)
            if groupNode.isEmpty():
                self.notify.error('Could not find visgroup')

            self.nodeList.append(groupNode)

        self.removeLandmarkBlockNodes()
        self.loader.dnaStore.resetPlaceNodes()
        self.loader.dnaStore.resetDNAGroups()
        self.loader.dnaStore.resetDNAVisGroups()
        self.loader.dnaStore.resetDNAVisGroupsAI()

    def removeLandmarkBlockNodes(self):
        npc = self.geom.findAllMatches('**/suit_building_origin')
        for i in range(npc.getNumPaths()):
            npc.getPath(i).removeNode()

    def enterTFA(self, requestStatus):
        self.acceptOnce(self.tfaDoneEvent, self.enterTFACallback, [requestStatus])
        self.tfa = TutorialForceAcknowledge(self.tfaDoneEvent)
        self.tfa.enter()

    def exitTFA(self):
        self.ignore(self.tfaDoneEvent)

    def enterTFAReject(self):
        self.fsm.request('walk')

    def exitTFAReject(self):
        pass
