from pandac.PandaModules import *
from direct.distributed.ClockDelta import *
from direct.interval.IntervalGlobal import *
from direct.directtools.DirectGeometry import *
from ElevatorConstants import *
from ElevatorUtils import *
from SuitBuildingGlobals import *
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from toontown.toonbase import ToontownGlobals
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State
from direct.distributed import DistributedObject
import random
from toontown.suit import SuitDNA
from toontown.toonbase import TTLocalizer
from toontown.distributed import DelayDelete
from toontown.toon import TTEmote
from otp.avatar import Emote
from toontown.hood import ZoneUtil
FO_DICT = {'s': 'tt_m_ara_cbe_fieldOfficeMoverShaker',
 'l': 'tt_m_ara_cbe_fieldOfficeMoverShaker',
 'm': 'tt_m_ara_cbe_fieldOfficeMoverShaker',
 'c': 'tt_m_ara_cbe_fieldOfficeMoverShaker'}

class DistributedBuilding(DistributedObject.DistributedObject):
    SUIT_INIT_HEIGHT = 125
    TAKEOVER_SFX_PREFIX = 'phase_5/audio/sfx/'

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        self.interactiveProp = None
        self.suitDoorOrigin = None
        self.elevatorModel = None
        self.fsm = ClassicFSM.ClassicFSM('DistributedBuilding', [State.State('off', self.enterOff, self.exitOff, ['waitForVictors',
          'waitForVictorsFromCogdo',
          'becomingToon',
          'becomingToonFromCogdo',
          'toon',
          'clearOutToonInterior',
          'becomingSuit',
          'suit',
          'clearOutToonInteriorForCogdo',
          'becomingCogdo',
          'becomingCogdoFromCogdo',
          'cogdo']),
         State.State('waitForVictors', self.enterWaitForVictors, self.exitWaitForVictors, ['becomingToon']),
         State.State('waitForVictorsFromCogdo', self.enterWaitForVictorsFromCogdo, self.exitWaitForVictorsFromCogdo, ['becomingToonFromCogdo', 'becomingCogdoFromCogdo']),
         State.State('becomingToon', self.enterBecomingToon, self.exitBecomingToon, ['toon']),
         State.State('becomingToonFromCogdo', self.enterBecomingToonFromCogdo, self.exitBecomingToonFromCogdo, ['toon']),
         State.State('toon', self.enterToon, self.exitToon, ['clearOutToonInterior', 'clearOutToonInteriorForCogdo']),
         State.State('clearOutToonInterior', self.enterClearOutToonInterior, self.exitClearOutToonInterior, ['becomingSuit']),
         State.State('becomingSuit', self.enterBecomingSuit, self.exitBecomingSuit, ['suit']),
         State.State('suit', self.enterSuit, self.exitSuit, ['waitForVictors', 'becomingToon']),
         State.State('clearOutToonInteriorForCogdo', self.enterClearOutToonInteriorForCogdo, self.exitClearOutToonInteriorForCogdo, ['becomingCogdo']),
         State.State('becomingCogdo', self.enterBecomingCogdo, self.exitBecomingCogdo, ['cogdo']),
         State.State('becomingCogdoFromCogdo', self.enterBecomingCogdoFromCogdo, self.exitBecomingCogdoFromCogdo, ['cogdo']),
         State.State('cogdo', self.enterCogdo, self.exitCogdo, ['waitForVictorsFromCogdo', 'becomingToonFromCogdo'])], 'off', 'off')
        self.fsm.enterInitialState()
        self.bossLevel = 0
        self.transitionTrack = None
        self.elevatorNodePath = None
        self.victorList = [0,
         0,
         0,
         0]
        self.waitingMessage = None
        self.cogDropSound = None
        self.cogLandSound = None
        self.cogSettleSound = None
        self.cogWeakenSound = None
        self.toonGrowSound = None
        self.toonSettleSound = None
        return

    def generate(self):
        DistributedObject.DistributedObject.generate(self)
        self.mode = 'toon'
        self.townTopLevel = self.cr.playGame.hood.loader.geom

    def disable(self):
        self.fsm.request('off')
        del self.townTopLevel
        self.stopTransition()
        DistributedObject.DistributedObject.disable(self)

    def delete(self):
        if self.elevatorNodePath:
            self.elevatorNodePath.removeNode()
            del self.elevatorNodePath
            del self.elevatorModel
            if hasattr(self, 'cab'):
                del self.cab
            del self.leftDoor
            del self.rightDoor
        del self.suitDoorOrigin
        self.cleanupSuitBuilding()
        self.unloadSfx()
        del self.fsm
        DistributedObject.DistributedObject.delete(self)

    def setBlock(self, block, interiorZoneId):
        self.block = block
        self.interiorZoneId = interiorZoneId

    def setSuitData(self, suitTrack, difficulty, numFloors):
        self.track = suitTrack
        self.difficulty = difficulty
        self.numFloors = numFloors

    def setState(self, state, timestamp):
        self.fsm.request(state, [globalClockDelta.localElapsedTime(timestamp)])

    def getSuitElevatorNodePath(self):
        if self.mode != 'suit':
            self.setToSuit()
        return self.elevatorNodePath

    def getCogdoElevatorNodePath(self):
        if self.mode != 'cogdo':
            self.setToCogdo()
        return self.elevatorNodePath

    def getSuitDoorOrigin(self):
        if self.mode != 'suit':
            self.setToSuit()
        return self.suitDoorOrigin

    def getCogdoDoorOrigin(self):
        if self.mode != 'cogdo':
            self.setToCogdo()
        return self.suitDoorOrigin

    def getBossLevel(self):
        return self.bossLevel

    def setBossLevel(self, bossLevel):
        self.bossLevel = bossLevel

    def setVictorList(self, victorList):
        self.victorList = victorList

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def enterWaitForVictors(self, ts):
        if self.mode != 'suit':
            self.setToSuit()
        victorCount = self.victorList.count(base.localAvatar.doId)
        if victorCount == 1:
            self.acceptOnce('insideVictorElevator', self.handleInsideVictorElevator)
            camera.reparentTo(render)
            camera.setPosHpr(self.elevatorNodePath, 0, -32.5, 9.4, 0, 348, 0)
            base.camLens.setFov(52.0)
            anyOthers = 0
            for v in self.victorList:
                if v != 0 and v != base.localAvatar.doId:
                    anyOthers = 1

            if anyOthers:
                self.waitingMessage = DirectLabel(text=TTLocalizer.BuildingWaitingForVictors, text_fg=VBase4(1, 1, 1, 1), text_align=TextNode.ACenter, relief=None, pos=(0, 0, 0.35), scale=0.1)
        elif victorCount == 0:
            pass
        else:
            self.error('localToon is on the victorList %d times' % victorCount)
        closeDoors(self.leftDoor, self.rightDoor)
        for light in self.floorIndicator:
            if light != None:
                light.setColor(LIGHT_OFF_COLOR)

        return

    def handleInsideVictorElevator(self):
        self.notify.info('inside victor elevator')
        self.sendUpdate('setVictorReady', [])

    def exitWaitForVictors(self):
        self.ignore('insideVictorElevator')
        if self.waitingMessage != None:
            self.waitingMessage.destroy()
            self.waitingMessage = None
        return

    def enterWaitForVictorsFromCogdo(self, ts):
        if self.mode != 'cogdo':
            self.setToCogdo()
        victorCount = self.victorList.count(base.localAvatar.doId)
        if victorCount == 1:
            self.acceptOnce('insideVictorElevator', self.handleInsideVictorElevatorFromCogdo)
            camera.reparentTo(render)
            camera.setPosHpr(self.elevatorNodePath, 0, -32.5, 9.4, 0, 348, 0)
            base.camLens.setFov(52.0)
            anyOthers = 0
            for v in self.victorList:
                if v != 0 and v != base.localAvatar.doId:
                    anyOthers = 1

            if anyOthers:
                self.waitingMessage = DirectLabel(text=TTLocalizer.BuildingWaitingForVictors, text_fg=VBase4(1, 1, 1, 1), text_align=TextNode.ACenter, relief=None, pos=(0, 0, 0.35), scale=0.1)
        elif victorCount == 0:
            pass
        else:
            self.error('localToon is on the victorList %d times' % victorCount)
        closeDoors(self.leftDoor, self.rightDoor)
        for light in self.floorIndicator:
            if light != None:
                light.setColor(LIGHT_OFF_COLOR)

        return

    def handleInsideVictorElevatorFromCogdo(self):
        self.sendUpdate('setVictorReady', [])

    def exitWaitForVictorsFromCogdo(self):
        self.ignore('insideVictorElevator')
        if self.waitingMessage != None:
            self.waitingMessage.destroy()
            self.waitingMessage = None
        return

    def enterBecomingToon(self, ts):
        self.animToToon(ts)

    def exitBecomingToon(self):
        pass

    def enterBecomingToonFromCogdo(self, ts):
        self.animToToonFromCogdo(ts)

    def exitBecomingToonFromCogdo(self):
        pass

    def enterToon(self, ts):
        if self.getInteractiveProp():
            self.getInteractiveProp().buildingLiberated(self.doId)
        self.setToToon()

    def exitToon(self):
        pass

    def enterClearOutToonInterior(self, ts):
        pass

    def exitClearOutToonInterior(self):
        pass

    def enterBecomingSuit(self, ts):
        self.animToSuit(ts)

    def exitBecomingSuit(self):
        pass

    def enterSuit(self, ts):
        self.makePropSad()
        self.setToSuit()

    def exitSuit(self):
        pass

    def enterClearOutToonInteriorForCogdo(self, ts):
        pass

    def exitClearOutToonInteriorForCogdo(self):
        pass

    def enterBecomingCogdo(self, ts):
        self.animToCogdo(ts)

    def exitBecomingCogdo(self):
        pass

    def enterBecomingCogdoFromCogdo(self, ts):
        self.animToCogdoFromCogdo(ts)

    def exitBecomingCogdoFromCogdo(self):
        pass

    def enterCogdo(self, ts):
        self.setToCogdo()

    def exitCogdo(self):
        pass

    def getNodePaths(self):
        nodePath = []
        npc = self.townTopLevel.findAllMatches('**/?b' + str(self.block) + ':*_DNARoot;+s')
        for i in range(npc.getNumPaths()):
            nodePath.append(npc.getPath(i))

        return nodePath

    def loadElevator(self, newNP, cogdo = False):
        self.floorIndicator = [None,
         None,
         None,
         None,
         None]
        self.elevatorNodePath = hidden.attachNewNode('elevatorNodePath')
        if cogdo:
            self.elevatorModel = loader.loadModel('phase_5/models/cogdominium/tt_m_ara_csa_elevatorB')
        else:
            self.elevatorModel = loader.loadModel('phase_4/models/modules/elevator')
            npc = self.elevatorModel.findAllMatches('**/floor_light_?;+s')
            for i in range(npc.getNumPaths()):
                np = npc.getPath(i)
                floor = int(np.getName()[-1:]) - 1
                self.floorIndicator[floor] = np
                if floor < self.numFloors:
                    np.setColor(LIGHT_OFF_COLOR)
                else:
                    np.hide()

        self.elevatorModel.reparentTo(self.elevatorNodePath)
        if self.mode == 'suit':
            self.cab = self.elevatorModel.find('**/elevator')
            cogIcons = loader.loadModel('phase_3/models/gui/cog_icons')
            dept = chr(self.track)
            if dept == 'c':
                corpIcon = cogIcons.find('**/CorpIcon').copyTo(self.cab)
            elif dept == 's':
                corpIcon = cogIcons.find('**/SalesIcon').copyTo(self.cab)
            elif dept == 'l':
                corpIcon = cogIcons.find('**/LegalIcon').copyTo(self.cab)
            elif dept == 'm':
                corpIcon = cogIcons.find('**/MoneyIcon').copyTo(self.cab)
            corpIcon.setPos(0, 6.79, 6.8)
            corpIcon.setScale(3)
            from toontown.suit import Suit
            corpIcon.setColor(Suit.Suit.medallionColors[dept])
            cogIcons.removeNode()
        self.leftDoor = self.elevatorModel.find('**/left-door')
        if self.leftDoor.isEmpty():
            self.leftDoor = self.elevatorModel.find('**/left_door')
        self.rightDoor = self.elevatorModel.find('**/right-door')
        if self.rightDoor.isEmpty():
            self.rightDoor = self.elevatorModel.find('**/right_door')
        self.suitDoorOrigin = newNP.find('**/*_door_origin')
        self.elevatorNodePath.reparentTo(self.suitDoorOrigin)
        self.normalizeElevator()
        return

    def loadAnimToSuitSfx(self):
        if base.config.GetBool('want-qa-regression', 0):
            self.notify.info('QA-REGRESSION: COGBUILDING: Cog Take Over')
        if self.cogDropSound == None:
            self.cogDropSound = base.loadSfx(self.TAKEOVER_SFX_PREFIX + 'cogbldg_drop.mp3')
            self.cogLandSound = base.loadSfx(self.TAKEOVER_SFX_PREFIX + 'cogbldg_land.mp3')
            self.cogSettleSound = base.loadSfx(self.TAKEOVER_SFX_PREFIX + 'cogbldg_settle.mp3')
            self.openSfx = base.loadSfx('phase_5/audio/sfx/elevator_door_open.mp3')
        return

    def loadAnimToToonSfx(self):
        if base.config.GetBool('want-qa-regression', 0):
            self.notify.info('QA-REGRESSION: COGBUILDING: Toon Take Over')
        if self.cogWeakenSound == None:
            self.cogWeakenSound = base.loadSfx(self.TAKEOVER_SFX_PREFIX + 'cogbldg_weaken.mp3')
            self.toonGrowSound = base.loadSfx(self.TAKEOVER_SFX_PREFIX + 'toonbldg_grow.mp3')
            self.toonSettleSound = base.loadSfx(self.TAKEOVER_SFX_PREFIX + 'toonbldg_settle.mp3')
            self.openSfx = base.loadSfx('phase_5/audio/sfx/elevator_door_open.mp3')
        return

    def unloadSfx(self):
        if self.cogDropSound != None:
            self.cogDropSound = None
            self.cogLandSound = None
            self.cogSettleSound = None
            self.openSfx = None
        if self.cogWeakenSound != None:
            self.cogWeakenSound = None
            self.toonGrowSound = None
            self.toonSettleSound = None
            self.openSfx = None
        return

    def _deleteTransitionTrack(self):
        if self.transitionTrack:
            DelayDelete.cleanupDelayDeletes(self.transitionTrack)
            self.transitionTrack = None
        return

    def animToSuit(self, timeStamp):
        self.stopTransition()
        if self.mode != 'toon':
            self.setToToon()
        self.loadAnimToSuitSfx()
        sideBldgNodes = self.getNodePaths()
        nodePath = hidden.find(self.getSbSearchString())
        newNP = self.setupSuitBuilding(nodePath)
        closeDoors(self.leftDoor, self.rightDoor)
        newNP.stash()
        sideBldgNodes.append(newNP)
        soundPlayed = 0
        tracks = Parallel(name=self.taskName('toSuitTrack'))
        for i in sideBldgNodes:
            name = i.getName()
            timeForDrop = TO_SUIT_BLDG_TIME * 0.85
            if name[0] == 's':
                showTrack = Sequence(name=self.taskName('ToSuitFlatsTrack') + '-' + str(sideBldgNodes.index(i)))
                initPos = Point3(0, 0, self.SUIT_INIT_HEIGHT) + i.getPos()
                showTrack.append(Func(i.setPos, initPos))
                showTrack.append(Func(i.unstash))
                if i == sideBldgNodes[len(sideBldgNodes) - 1]:
                    showTrack.append(Func(self.normalizeElevator))
                if not soundPlayed:
                    showTrack.append(Func(base.playSfx, self.cogDropSound, 0, 1, None, 0.0))
                showTrack.append(LerpPosInterval(i, timeForDrop, i.getPos(), name=self.taskName('ToSuitAnim') + '-' + str(sideBldgNodes.index(i))))
                if not soundPlayed:
                    showTrack.append(Func(base.playSfx, self.cogLandSound, 0, 1, None, 0.0))
                showTrack.append(self.createBounceTrack(i, 2, 0.65, TO_SUIT_BLDG_TIME - timeForDrop, slowInitBounce=1.0))
                if not soundPlayed:
                    showTrack.append(Func(base.playSfx, self.cogSettleSound, 0, 1, None, 0.0))
                tracks.append(showTrack)
                if not soundPlayed:
                    soundPlayed = 1
            elif name[0] == 't':
                hideTrack = Sequence(name=self.taskName('ToSuitToonFlatsTrack'))
                timeTillSquish = (self.SUIT_INIT_HEIGHT - 20.0) / self.SUIT_INIT_HEIGHT
                timeTillSquish *= timeForDrop
                hideTrack.append(LerpFunctionInterval(self.adjustColorScale, fromData=1, toData=0.25, duration=timeTillSquish, extraArgs=[i]))
                hideTrack.append(LerpScaleInterval(i, timeForDrop - timeTillSquish, Vec3(1, 1, 0.01)))
                hideTrack.append(Func(i.stash))
                hideTrack.append(Func(i.setScale, Vec3(1)))
                hideTrack.append(Func(i.clearColorScale))
                tracks.append(hideTrack)

        self.stopTransition()
        self._deleteTransitionTrack()
        self.transitionTrack = tracks
        self.transitionTrack.start(timeStamp)
        return

    def setupSuitBuilding(self, nodePath):
        dnaStore = self.cr.playGame.dnaStore
        level = int(self.difficulty / 2) + 1
        suitNP = dnaStore.findNode('suit_landmark_' + chr(self.track) + str(level))
        zoneId = dnaStore.getZoneFromBlockNumber(self.block)
        zoneId = ZoneUtil.getTrueZoneId(zoneId, self.interiorZoneId)
        newParentNP = base.cr.playGame.hood.loader.zoneDict[zoneId]
        suitBuildingNP = suitNP.copyTo(newParentNP)
        buildingTitle = dnaStore.getTitleFromBlockNumber(self.block)
        if not buildingTitle:
            buildingTitle = TTLocalizer.CogsInc
        else:
            buildingTitle += TTLocalizer.CogsIncExt
        buildingTitle += '\n%s' % SuitDNA.getDeptFullname(chr(self.track))
        textNode = TextNode('sign')
        textNode.setTextColor(1.0, 1.0, 1.0, 1.0)
        textNode.setFont(ToontownGlobals.getSuitFont())
        textNode.setAlign(TextNode.ACenter)
        textNode.setWordwrap(17.0)
        textNode.setText(buildingTitle)
        textHeight = textNode.getHeight()
        zScale = (textHeight + 2) / 3.0
        signOrigin = suitBuildingNP.find('**/sign_origin;+s')
        backgroundNP = loader.loadModel('phase_5/models/modules/suit_sign')
        backgroundNP.reparentTo(signOrigin)
        backgroundNP.setPosHprScale(0.0, 0.0, textHeight * 0.8 / zScale, 0.0, 0.0, 0.0, 8.0, 8.0, 8.0 * zScale)
        backgroundNP.node().setEffect(DecalEffect.make())
        signTextNodePath = backgroundNP.attachNewNode(textNode.generate())
        signTextNodePath.setPosHprScale(0.0, 0.0, -0.21 + textHeight * 0.1 / zScale, 0.0, 0.0, 0.0, 0.1, 0.1, 0.1 / zScale)
        signTextNodePath.setColor(1.0, 1.0, 1.0, 1.0)
        frontNP = suitBuildingNP.find('**/*_front/+GeomNode;+s')
        backgroundNP.wrtReparentTo(frontNP)
        frontNP.node().setEffect(DecalEffect.make())
        suitBuildingNP.setName('sb' + str(self.block) + ':_landmark__DNARoot')
        suitBuildingNP.setPosHprScale(nodePath, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0)
        suitBuildingNP.flattenMedium()
        self.loadElevator(suitBuildingNP)
        return suitBuildingNP

    def cleanupSuitBuilding(self):
        if hasattr(self, 'floorIndicator'):
            del self.floorIndicator

    def adjustColorScale(self, scale, node):
        node.setColorScale(scale, scale, scale, 1)

    def animToCogdo(self, timeStamp):
        self.stopTransition()
        if self.mode != 'toon':
            self.setToToon()
        self.loadAnimToSuitSfx()
        sideBldgNodes = self.getNodePaths()
        nodePath = hidden.find(self.getSbSearchString())
        newNP = self.setupCogdo(nodePath)
        closeDoors(self.leftDoor, self.rightDoor)
        newNP.stash()
        sideBldgNodes.append(newNP)
        for np in sideBldgNodes:
            if not np.isEmpty():
                np.setColorScale(0.6, 0.6, 0.6, 1.0)

        soundPlayed = 0
        tracks = Parallel(name=self.taskName('toCogdoTrack'))
        for i in sideBldgNodes:
            name = i.getName()
            timeForDrop = TO_SUIT_BLDG_TIME * 0.85
            if name[0] == 'c':
                showTrack = Sequence(name=self.taskName('ToCogdoFlatsTrack') + '-' + str(sideBldgNodes.index(i)))
                initPos = Point3(0, 0, self.SUIT_INIT_HEIGHT) + i.getPos()
                showTrack.append(Func(i.setPos, initPos))
                showTrack.append(Func(i.unstash))
                if i == sideBldgNodes[len(sideBldgNodes) - 1]:
                    showTrack.append(Func(self.normalizeElevator))
                if not soundPlayed:
                    showTrack.append(Func(base.playSfx, self.cogDropSound, 0, 1, None, 0.0))
                showTrack.append(LerpPosInterval(i, timeForDrop, i.getPos(), name=self.taskName('ToCogdoAnim') + '-' + str(sideBldgNodes.index(i))))
                if not soundPlayed:
                    showTrack.append(Func(base.playSfx, self.cogLandSound, 0, 1, None, 0.0))
                showTrack.append(self.createBounceTrack(i, 2, 0.65, TO_SUIT_BLDG_TIME - timeForDrop, slowInitBounce=1.0))
                if not soundPlayed:
                    showTrack.append(Func(base.playSfx, self.cogSettleSound, 0, 1, None, 0.0))
                tracks.append(showTrack)
                if not soundPlayed:
                    soundPlayed = 1
            elif name[0] == 't':
                hideTrack = Sequence(name=self.taskName('ToCogdoToonFlatsTrack'))
                timeTillSquish = (self.SUIT_INIT_HEIGHT - 20.0) / self.SUIT_INIT_HEIGHT
                timeTillSquish *= timeForDrop
                hideTrack.append(LerpFunctionInterval(self.adjustColorScale, fromData=1, toData=0.25, duration=timeTillSquish, extraArgs=[i]))
                hideTrack.append(LerpScaleInterval(i, timeForDrop - timeTillSquish, Vec3(1, 1, 0.01)))
                hideTrack.append(Func(i.stash))
                hideTrack.append(Func(i.setScale, Vec3(1)))
                hideTrack.append(Func(i.clearColorScale))
                tracks.append(hideTrack)

        self.stopTransition()
        self._deleteTransitionTrack()
        self.transitionTrack = tracks
        self.transitionTrack.start(timeStamp)
        return

    def setupCogdo(self, nodePath):
        dnaStore = self.cr.playGame.dnaStore
        level = int(self.difficulty / 2) + 1
        suitNP = dnaStore.findNode(FO_DICT[chr(self.track)])
        zoneId = dnaStore.getZoneFromBlockNumber(self.block)
        zoneId = ZoneUtil.getTrueZoneId(zoneId, self.interiorZoneId)
        newParentNP = base.cr.playGame.hood.loader.zoneDict[zoneId]
        suitBuildingNP = suitNP.copyTo(newParentNP)
        buildingTitle = dnaStore.getTitleFromBlockNumber(self.block)
        if not buildingTitle:
            buildingTitle = TTLocalizer.Cogdominiums
        else:
            buildingTitle += TTLocalizer.CogdominiumsExt
        textNode = TextNode('sign')
        textNode.setTextColor(1.0, 1.0, 1.0, 1.0)
        textNode.setFont(ToontownGlobals.getSuitFont())
        textNode.setAlign(TextNode.ACenter)
        textNode.setWordwrap(12.0)
        textNode.setText(buildingTitle)
        textHeight = textNode.getHeight()
        zScale = (textHeight + 2) / 3.0
        signOrigin = suitBuildingNP.find('**/sign_origin;+s')
        backgroundNP = loader.loadModel('phase_5/models/cogdominium/field_office_sign')
        backgroundNP.reparentTo(signOrigin)
        backgroundNP.setPosHprScale(0.0, 0.0, -1.2 + textHeight * 0.8 / zScale, 0.0, 0.0, 0.0, 20.0, 8.0, 8.0 * zScale)
        backgroundNP.node().setEffect(DecalEffect.make())
        signTextNodePath = backgroundNP.attachNewNode(textNode.generate())
        signTextNodePath.setPosHprScale(0.0, 0.0, -0.13 + textHeight * 0.1 / zScale, 0.0, 0.0, 0.0, 0.1 * 8.0 / 20.0, 0.1, 0.1 / zScale)
        signTextNodePath.setColor(1.0, 1.0, 1.0, 1.0)
        frontNP = suitBuildingNP.find('**/*_front/+GeomNode;+s')
        backgroundNP.wrtReparentTo(frontNP)
        frontNP.node().setEffect(DecalEffect.make())
        suitBuildingNP.setName('cb' + str(self.block) + ':_landmark__DNARoot')
        suitBuildingNP.setPosHprScale(nodePath, 15.463, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0)
        suitBuildingNP.flattenMedium()
        suitBuildingNP.setColorScale(0.6, 0.6, 0.6, 1.0)
        self.loadElevator(suitBuildingNP, cogdo=True)
        return suitBuildingNP

    def animToToon(self, timeStamp):
        self.stopTransition()
        if self.mode != 'suit':
            self.setToSuit()
        self.loadAnimToToonSfx()
        suitSoundPlayed = 0
        toonSoundPlayed = 0
        bldgNodes = self.getNodePaths()
        tracks = Parallel()
        for i in bldgNodes:
            name = i.getName()
            if name[0] == 's':
                hideTrack = Sequence(name=self.taskName('ToToonSuitFlatsTrack'))
                landmark = name.find('_landmark_') != -1
                if not suitSoundPlayed:
                    hideTrack.append(Func(base.playSfx, self.cogWeakenSound, 0, 1, None, 0.0))
                hideTrack.append(self.createBounceTrack(i, 3, 1.2, TO_TOON_BLDG_TIME * 0.05, slowInitBounce=0.0))
                hideTrack.append(self.createBounceTrack(i, 5, 0.8, TO_TOON_BLDG_TIME * 0.1, slowInitBounce=0.0))
                hideTrack.append(self.createBounceTrack(i, 7, 1.2, TO_TOON_BLDG_TIME * 0.17, slowInitBounce=0.0))
                hideTrack.append(self.createBounceTrack(i, 9, 1.2, TO_TOON_BLDG_TIME * 0.18, slowInitBounce=0.0))
                realScale = i.getScale()
                hideTrack.append(LerpScaleInterval(i, TO_TOON_BLDG_TIME * 0.1, Vec3(realScale[0], realScale[1], 0.01)))
                if landmark:
                    hideTrack.append(Func(i.removeNode))
                else:
                    hideTrack.append(Func(i.stash))
                    hideTrack.append(Func(i.setScale, Vec3(1)))
                if not suitSoundPlayed:
                    suitSoundPlayed = 1
                tracks.append(hideTrack)
            elif name[0] == 't':
                hideTrack = Sequence(name=self.taskName('ToToonFlatsTrack'))
                hideTrack.append(Wait(TO_TOON_BLDG_TIME * 0.5))
                if not toonSoundPlayed:
                    hideTrack.append(Func(base.playSfx, self.toonGrowSound, 0, 1, None, 0.0))
                hideTrack.append(Func(i.unstash))
                hideTrack.append(Func(i.setScale, Vec3(1, 1, 0.01)))
                if not toonSoundPlayed:
                    hideTrack.append(Func(base.playSfx, self.toonSettleSound, 0, 1, None, 0.0))
                hideTrack.append(self.createBounceTrack(i, 11, 1.2, TO_TOON_BLDG_TIME * 0.5, slowInitBounce=4.0))
                tracks.append(hideTrack)
                if not toonSoundPlayed:
                    toonSoundPlayed = 1

        self.stopTransition()
        bldgMTrack = tracks
        localToonIsVictor = self.localToonIsVictor()
        if localToonIsVictor:
            camTrack = self.walkOutCameraTrack()
        victoryRunTrack, delayDeletes = self.getVictoryRunTrack()
        trackName = self.taskName('toToonTrack')
        self._deleteTransitionTrack()
        if localToonIsVictor:
            freedomTrack1 = Func(self.cr.playGame.getPlace().setState, 'walk')
            freedomTrack2 = Func(base.localAvatar.d_setParent, ToontownGlobals.SPRender)
            self.transitionTrack = Parallel(camTrack, Sequence(victoryRunTrack, bldgMTrack, freedomTrack1, freedomTrack2), name=trackName)
        else:
            self.transitionTrack = Sequence(victoryRunTrack, bldgMTrack, name=trackName)
        self.transitionTrack.delayDeletes = delayDeletes
        if localToonIsVictor:
            self.transitionTrack.start(0)
        else:
            self.transitionTrack.start(timeStamp)
        return

    def animToToonFromCogdo(self, timeStamp):
        self.stopTransition()
        if self.mode != 'cogdo':
            self.setToCogdo()
        self.loadAnimToToonSfx()
        suitSoundPlayed = 0
        toonSoundPlayed = 0
        bldgNodes = self.getNodePaths()
        tracks = Parallel()
        for i in bldgNodes:
            i.clearColorScale()
            name = i.getName()
            if name[0] == 'c':
                hideTrack = Sequence(name=self.taskName('ToToonCogdoFlatsTrack'))
                landmark = name.find('_landmark_') != -1
                if not suitSoundPlayed:
                    hideTrack.append(Func(base.playSfx, self.cogWeakenSound, 0, 1, None, 0.0))
                hideTrack.append(self.createBounceTrack(i, 3, 1.2, TO_TOON_BLDG_TIME * 0.05, slowInitBounce=0.0))
                hideTrack.append(self.createBounceTrack(i, 5, 0.8, TO_TOON_BLDG_TIME * 0.1, slowInitBounce=0.0))
                hideTrack.append(self.createBounceTrack(i, 7, 1.2, TO_TOON_BLDG_TIME * 0.17, slowInitBounce=0.0))
                hideTrack.append(self.createBounceTrack(i, 9, 1.2, TO_TOON_BLDG_TIME * 0.18, slowInitBounce=0.0))
                realScale = i.getScale()
                hideTrack.append(LerpScaleInterval(i, TO_TOON_BLDG_TIME * 0.1, Vec3(realScale[0], realScale[1], 0.01)))
                if landmark:
                    hideTrack.append(Func(i.removeNode))
                else:
                    hideTrack.append(Func(i.stash))
                    hideTrack.append(Func(i.setScale, Vec3(1)))
                if not suitSoundPlayed:
                    suitSoundPlayed = 1
                tracks.append(hideTrack)
            elif name[0] == 't':
                hideTrack = Sequence(name=self.taskName('ToToonFromCogdoFlatsTrack'))
                hideTrack.append(Wait(TO_TOON_BLDG_TIME * 0.5))
                if not toonSoundPlayed:
                    hideTrack.append(Func(base.playSfx, self.toonGrowSound, 0, 1, None, 0.0))
                hideTrack.append(Func(i.unstash))
                hideTrack.append(Func(i.setScale, Vec3(1, 1, 0.01)))
                if not toonSoundPlayed:
                    hideTrack.append(Func(base.playSfx, self.toonSettleSound, 0, 1, None, 0.0))
                hideTrack.append(self.createBounceTrack(i, 11, 1.2, TO_TOON_BLDG_TIME * 0.5, slowInitBounce=4.0))
                tracks.append(hideTrack)
                if not toonSoundPlayed:
                    toonSoundPlayed = 1

        self.stopTransition()
        bldgMTrack = tracks
        localToonIsVictor = self.localToonIsVictor()
        if localToonIsVictor:
            camTrack = self.walkOutCameraTrack()
        victoryRunTrack, delayDeletes = self.getVictoryRunTrack()
        trackName = self.taskName('toToonFromCogdoTrack')
        self._deleteTransitionTrack()
        if localToonIsVictor:
            freedomTrack1 = Func(self.cr.playGame.getPlace().setState, 'walk')
            freedomTrack2 = Func(base.localAvatar.d_setParent, ToontownGlobals.SPRender)
            self.transitionTrack = Parallel(camTrack, Sequence(victoryRunTrack, bldgMTrack, freedomTrack1, freedomTrack2), name=trackName)
        else:
            self.transitionTrack = Sequence(victoryRunTrack, bldgMTrack, name=trackName)
        self.transitionTrack.delayDeletes = delayDeletes
        if localToonIsVictor:
            self.transitionTrack.start(0)
        else:
            self.transitionTrack.start(timeStamp)
        return

    def walkOutCameraTrack(self):
        track = Sequence(Func(camera.reparentTo, render), Func(camera.setPosHpr, self.elevatorNodePath, 0, -32.5, 9.4, 0, 348, 0), Func(base.camLens.setFov, 52.0), Wait(VICTORY_RUN_TIME), Func(camera.setPosHpr, self.elevatorNodePath, 0, -32.5, 17, 0, 347, 0), Func(base.camLens.setFov, 75.0), Wait(TO_TOON_BLDG_TIME), Func(base.camLens.setFov, 52.0))
        return track

    def plantVictorsOutsideBldg(self):
        retVal = 0
        for victor in self.victorList:
            if victor != 0 and self.cr.doId2do.has_key(victor):
                toon = self.cr.doId2do[victor]
                toon.setPosHpr(self.elevatorModel, 0, -10, 0, 0, 0, 0)
                toon.startSmooth()
                if victor == base.localAvatar.getDoId():
                    retVal = 1
                    self.cr.playGame.getPlace().setState('walk')

        return retVal

    def getVictoryRunTrack(self):
        origPosTrack = Sequence()
        delayDeletes = []
        i = 0
        for victor in self.victorList:
            if victor != 0 and self.cr.doId2do.has_key(victor):
                toon = self.cr.doId2do[victor]
                delayDeletes.append(DelayDelete.DelayDelete(toon, 'getVictoryRunTrack'))
                toon.stopSmooth()
                toon.setParent(ToontownGlobals.SPHidden)
                origPosTrack.append(Func(toon.setPosHpr, self.elevatorNodePath, apply(Point3, ElevatorPoints[i]), Point3(180, 0, 0)))
                origPosTrack.append(Func(toon.setParent, ToontownGlobals.SPRender))
            i += 1

        openDoors = getOpenInterval(self, self.leftDoor, self.rightDoor, self.openSfx, None)
        toonDoorPosHpr = self.cr.playGame.dnaStore.getDoorPosHprFromBlockNumber(self.block)
        useFarExitPoints = toonDoorPosHpr.getPos().getZ() > 1.0
        runOutAll = Parallel()
        i = 0
        for victor in self.victorList:
            if victor != 0 and self.cr.doId2do.has_key(victor):
                toon = self.cr.doId2do[victor]
                p0 = Point3(0, 0, 0)
                p1 = Point3(ElevatorPoints[i][0], ElevatorPoints[i][1] - 5.0, ElevatorPoints[i][2])
                if useFarExitPoints:
                    p2 = Point3(ElevatorOutPointsFar[i][0], ElevatorOutPointsFar[i][1], ElevatorOutPointsFar[i][2])
                else:
                    p2 = Point3(ElevatorOutPoints[i][0], ElevatorOutPoints[i][1], ElevatorOutPoints[i][2])
                runOutSingle = Sequence(Func(Emote.globalEmote.disableBody, toon, 'getVictory'), Func(toon.animFSM.request, 'run'), LerpPosInterval(toon, TOON_VICTORY_EXIT_TIME * 0.25, p1, other=self.elevatorNodePath), Func(toon.headsUp, self.elevatorNodePath, p2), LerpPosInterval(toon, TOON_VICTORY_EXIT_TIME * 0.5, p2, other=self.elevatorNodePath), LerpHprInterval(toon, TOON_VICTORY_EXIT_TIME * 0.25, Point3(0, 0, 0), other=self.elevatorNodePath), Func(toon.animFSM.request, 'neutral'), Func(toon.startSmooth), Func(Emote.globalEmote.releaseBody, toon, 'getVictory'))
                runOutAll.append(runOutSingle)
            i += 1

        victoryRunTrack = Sequence(origPosTrack, openDoors, runOutAll)
        return (victoryRunTrack, delayDeletes)

    def animToCogdoFromCogdo(self, timeStamp):
        self.stopTransition()
        if self.mode != 'cogdo':
            self.setToCogdo()
        self.loadAnimToToonSfx()
        localToonIsVictor = self.localToonIsVictor()
        if localToonIsVictor:
            camTrack = self.walkOutCameraTrack()
        victoryRunTrack, delayDeletes = self.getVictoryRunTrack()
        trackName = self.taskName('toToonFromCogdoTrack')
        self._deleteTransitionTrack()
        if localToonIsVictor:
            freedomTrack1 = Func(self.cr.playGame.getPlace().setState, 'walk')
            freedomTrack2 = Func(base.localAvatar.d_setParent, ToontownGlobals.SPRender)
            self.transitionTrack = Parallel(camTrack, Sequence(victoryRunTrack, freedomTrack1, freedomTrack2), name=trackName)
        else:
            self.transitionTrack = Sequence(victoryRunTrack, name=trackName)
        self.transitionTrack.delayDeletes = delayDeletes
        if localToonIsVictor:
            self.transitionTrack.start(0)
        else:
            self.transitionTrack.start(timeStamp)

    def localToonIsVictor(self):
        retVal = 0
        for victor in self.victorList:
            if victor == base.localAvatar.getDoId():
                retVal = 1

        return retVal

    def createBounceTrack(self, nodeObj, numBounces, startScale, totalTime, slowInitBounce = 0.0):
        if not nodeObj or numBounces < 1 or startScale == 0.0 or totalTime == 0:
            self.notify.warning('createBounceTrack called with invalid parameter')
            return
        result = Sequence()
        numBounces += 1
        if slowInitBounce:
            bounceTime = totalTime / (numBounces + slowInitBounce - 1.0)
        else:
            bounceTime = totalTime / float(numBounces)
        if slowInitBounce:
            currTime = bounceTime * float(slowInitBounce)
        else:
            currTime = bounceTime
        realScale = nodeObj.getScale()
        currScaleDiff = startScale - realScale[2]
        for currBounceScale in range(numBounces):
            if currBounceScale == numBounces - 1:
                currScale = realScale[2]
            elif currBounceScale % 2:
                currScale = realScale[2] - currScaleDiff
            else:
                currScale = realScale[2] + currScaleDiff
            result.append(LerpScaleInterval(nodeObj, currTime, Vec3(realScale[0], realScale[1], currScale), blendType='easeInOut'))
            currScaleDiff *= 0.5
            currTime = bounceTime

        return result

    def stopTransition(self):
        if self.transitionTrack:
            self.transitionTrack.finish()
            self._deleteTransitionTrack()

    def setToSuit(self):
        self.stopTransition()
        if self.mode == 'suit':
            return
        self.mode = 'suit'
        nodes = self.getNodePaths()
        for i in nodes:
            name = i.getName()
            if name[0] == 's':
                if name.find('_landmark_') != -1:
                    i.removeNode()
                else:
                    i.unstash()
            elif name[0] == 't':
                if name.find('_landmark_') != -1:
                    i.stash()
                else:
                    i.stash()
            elif name[0] == 'c':
                if name.find('_landmark_') != -1:
                    i.removeNode()
                else:
                    i.stash()

        npc = hidden.findAllMatches(self.getSbSearchString())
        for i in range(npc.getNumPaths()):
            nodePath = npc.getPath(i)
            self.adjustSbNodepathScale(nodePath)
            self.notify.debug('net transform = %s' % str(nodePath.getNetTransform()))
            self.setupSuitBuilding(nodePath)

    def setToCogdo(self):
        self.stopTransition()
        if self.mode == 'cogdo':
            return
        self.mode = 'cogdo'
        nodes = self.getNodePaths()
        for i in nodes:
            name = i.getName()
            if name[0] == 'c':
                if name.find('_landmark_') != -1:
                    i.removeNode()
                else:
                    i.unstash()
            elif name[0] == 't':
                if name.find('_landmark_') != -1:
                    i.stash()
                else:
                    i.stash()
            elif name[0] == 's':
                if name.find('_landmark_') != -1:
                    i.removeNode()
                else:
                    i.stash()

        for np in nodes:
            if not np.isEmpty():
                np.setColorScale(0.6, 0.6, 0.6, 1.0)

        npc = hidden.findAllMatches(self.getSbSearchString())
        for i in range(npc.getNumPaths()):
            nodePath = npc.getPath(i)
            self.adjustSbNodepathScale(nodePath)
            self.notify.debug('net transform = %s' % str(nodePath.getNetTransform()))
            self.setupCogdo(nodePath)

    def setToToon(self):
        self.stopTransition()
        if self.mode == 'toon':
            return
        self.mode = 'toon'
        self.suitDoorOrigin = None
        nodes = self.getNodePaths()
        for i in nodes:
            i.clearColorScale()
            name = i.getName()
            if name[0] == 's':
                if name.find('_landmark_') != -1:
                    i.removeNode()
                else:
                    i.stash()
            elif name[0] == 't':
                if name.find('_landmark_') != -1:
                    i.unstash()
                else:
                    i.unstash()
            elif name[0] == 'c':
                if name.find('_landmark_') != -1:
                    i.removeNode()
                else:
                    i.stash()

        return

    def normalizeElevator(self):
        self.elevatorNodePath.setScale(render, Vec3(1, 1, 1))
        self.elevatorNodePath.setPosHpr(0, 0, 0, 0, 0, 0)

    def getSbSearchString(self):
        result = 'landmarkBlocks/sb' + str(self.block) + ':*_landmark_*_DNARoot'
        return result

    def adjustSbNodepathScale(self, nodePath):
        pass

    def getVisZoneId(self):
        exteriorZoneId = base.cr.playGame.hood.dnaStore.getZoneFromBlockNumber(self.block)
        visZoneId = ZoneUtil.getTrueZoneId(exteriorZoneId, self.zoneId)
        return visZoneId

    def getInteractiveProp(self):
        result = None
        if self.interactiveProp:
            result = self.interactiveProp
        else:
            visZoneId = self.getVisZoneId()
            if base.cr.playGame.hood:
                loader = base.cr.playGame.hood.loader
                if hasattr(loader, 'getInteractiveProp'):
                    self.interactiveProp = loader.getInteractiveProp(visZoneId)
                    result = self.interactiveProp
                    self.notify.debug('self.interactiveProp = %s' % self.interactiveProp)
                else:
                    self.notify.warning('no loader.getInteractiveProp self.interactiveProp is None')
            else:
                self.notify.warning('no hood self.interactiveProp is None')
        return result

    def makePropSad(self):
        self.notify.debug('makePropSad')
        if self.getInteractiveProp():
            if self.getInteractiveProp().state == 'Sad':
                pass
            self.getInteractiveProp().gotoSad(self.doId)
