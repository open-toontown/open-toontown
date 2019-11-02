from direct.interval.MetaInterval import Sequence, Parallel, Track
from direct.interval.FunctionInterval import Func, Wait
from direct.interval.SoundInterval import SoundInterval
from direct.interval.ActorInterval import ActorInterval
from direct.interval.ProjectileInterval import ProjectileInterval
from direct.distributed.ClockDelta import globalClockDelta
from direct.showbase.PythonUtil import bound, lerp
from direct.showbase.DirectObject import DirectObject
from pandac.PandaModules import NodePath, Point3, TextNode
from pandac.PandaModules import CollisionSphere, CollisionNode, CollisionHandlerEvent
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.toonbase.ToontownTimer import ToontownTimer
import PartyGlobals
import PartyCogUtils
from PartyCog import PartyCogManager
from PartyCogActivityPlayer import PartyCogActivityPlayer
from PartyCogActivityPlayer import PartyCogActivityLocalPlayer
from StretchingArrow import StretchingArrow

class PartyCogActivity(DirectObject):
    notify = directNotify.newCategory('PartyCogActivity')
    cog = None
    arena = None
    player = None
    players = {}

    def __init__(self, activity, arenaModel = None, texture = None):
        self.activity = activity
        self.root = self.activity.root
        self.toonPieTracks = {}
        self.toonPieEventNames = {}
        self.toonIdsToAnimIntervals = {}
        self.pieIvals = []
        self.resultsIval = None
        self.arenaModel = arenaModel
        self.texture = texture
        return

    def load(self):
        self.arena = loader.loadModel(self.arenaModel)
        self.arena.reparentTo(self.root)
        ground = self.arena.find('**/ground')
        ground.setBin('ground', 1)
        entranceArrows = self.arena.findAllMatches('**/arrowFlat*')
        for arrow in entranceArrows:
            arrow.setBin('ground', 5)

        self.leftEntranceLocator = self.arena.find('**/leftEntrance_locator')
        self.rightEntranceLocator = self.arena.find('**/rightEntrance_locator')
        self.leftExitLocator = self.arena.find('**/leftExit_locator')
        self.rightExitLocator = self.arena.find('**/rightExit_locator')
        self.teamCamPosLocators = (self.arena.find('**/team0CamPos_locator'), self.arena.find('**/team1CamPos_locator'))
        self.teamCamAimLocators = (self.arena.find('**/team0CamAim_locator'), self.arena.find('**/team1CamAim_locator'))
        leftTeamLocator = NodePath('TeamLocator-%d' % PartyGlobals.TeamActivityTeams.LeftTeam)
        leftTeamLocator.reparentTo(self.root)
        leftTeamLocator.setH(90)
        rightTeamLocator = NodePath('TeamLocator-%d' % PartyGlobals.TeamActivityTeams.RightTeam)
        rightTeamLocator.reparentTo(self.root)
        rightTeamLocator.setH(-90)
        self.teamLocators = (leftTeamLocator, rightTeamLocator)
        self._lengthBetweenEntrances = self.leftEntranceLocator.getY() - self.rightExitLocator.getY()
        self._skyCollisionsCollection = self.arena.findAllMatches('**/cogPieArena_sky*_collision')
        if len(self._skyCollisionsCollection) > 0:
            self._skyCollisionParent = self._skyCollisionsCollection[0].getParent()
        else:
            self._skyCollisionParent = self.arena
        self._wallCollisionsCollection = self.arena.findAllMatches('**/cogPieArena_wall*_collision')
        self._arenaFlagGroups = (self.arena.find('**/flagsL_grp'), self.arena.find('**/flagsR_grp'))
        self._initArenaDoors()
        self.cogManager = PartyCogManager()
        self.arrows = []
        self.distanceLabels = []
        self.teamColors = list(PartyGlobals.CogActivityColors) + [PartyGlobals.TeamActivityStatusColor]
        for i in range(3):
            start = self.arena.find('**/cog%d_start_locator' % (i + 1))
            end = self.arena.find('**/cog%d_end_locator' % (i + 1))
            cog = self.cogManager.generateCog(self.arena)
            cog.setEndPoints(start.getPos(), end.getPos())
            arrow1 = StretchingArrow(self.arena, useColor='orange')
            arrow2 = StretchingArrow(self.arena, useColor='blue')
            arrow1.setZ(0.1)
            arrow2.setZ(0.1)
            self.arrows.append([arrow1, arrow2])
            distanceLabel = self.createDistanceLabel(0, self.teamColors[1])
            distanceLabel[0].stash()
            distanceLabel2 = self.createDistanceLabel(0, self.teamColors[0])
            distanceLabel2[0].stash()
            self.distanceLabels.append([distanceLabel, distanceLabel2])

        self.winText = []
        text1 = self.createText(0, Point3(-0.5, 0.0, -0.5), self.teamColors[1])
        text2 = self.createText(1, Point3(0.5, 0.0, -0.5), self.teamColors[0])
        self.winText.append(text1)
        self.winText.append(text2)
        self.winStatus = self.createText(2, Point3(0.0, 0.0, -0.8), self.teamColors[0])
        signLocator = self.arena.find('**/eventSign_locator')
        self.activity.sign.setPos(signLocator.getPos(self.root))
        if self.texture:
            textureAlpha = self.texture[:-4] + '_a.rgb'
            reskinTexture = loader.loadTexture(self.texture, textureAlpha)
            self.arena.find('**/center_grp').setTexture(reskinTexture, 100)
            self.arena.find('**/leftSide_grp').setTexture(reskinTexture, 100)
            self.arena.find('**/rightSide_grp').setTexture(reskinTexture, 100)
        self.enable()

    def _initArenaDoors(self):
        self._arenaDoors = (self.arena.find('**/doorL'), self.arena.find('**/doorR'))
        arenaDoorLocators = (self.arena.find('**/doorL_locator'), self.arena.find('**/doorR_locator'))
        for i in range(len(arenaDoorLocators)):
            arenaDoorLocators[i].wrtReparentTo(self._arenaDoors[i])

        self._arenaDoorTimers = (self.createDoorTimer(PartyGlobals.TeamActivityTeams.LeftTeam), self.createDoorTimer(PartyGlobals.TeamActivityTeams.RightTeam))
        self._arenaDoorIvals = [None, None]
        self._doorStartPos = []
        for i in range(len(self._arenaDoors)):
            door = self._arenaDoors[i]
            timer = self._arenaDoorTimers[i]
            timer.reparentTo(arenaDoorLocators[i])
            timer.hide()
            self._doorStartPos.append(door.getPos())
            door.setPos(door, 0, 0, -7.0)

        return

    def _destroyArenaDoors(self):
        for ival in self._arenaDoorIvals:
            ival.finish()

        self._arenaDoorIvals = None
        self._arenaDoors = None
        for timer in self._arenaDoorTimers:
            timer.stop()
            timer.removeNode()

        self._arenaDoorTimers = None
        return

    def createDoorTimer(self, team):
        timer = ToontownTimer(useImage=False, highlightNearEnd=False)
        timer['text_font'] = ToontownGlobals.getMinnieFont()
        timer.setFontColor(PartyGlobals.CogActivityColors[team])
        timer.setScale(7.0)
        timer.setPos(0.2, -0.03, 0.0)
        return timer

    def createText(self, number, position, color):
        text = TextNode('winText%d' % number)
        text.setAlign(TextNode.ACenter)
        text.setTextColor(color)
        text.setFont(ToontownGlobals.getSignFont())
        text.setText('')
        noteText = aspect2d.attachNewNode(text)
        noteText.setScale(0.2)
        noteText.setPos(position)
        noteText.stash()
        return (text, noteText)

    def createDistanceLabel(self, number, color):
        text = TextNode('distanceText-%d' % number)
        text.setAlign(TextNode.ACenter)
        text.setTextColor(color)
        text.setFont(ToontownGlobals.getSignFont())
        text.setText('10 ft')
        node = self.root.attachNewNode(text)
        node.setBillboardPointEye()
        node.setScale(2.5)
        node.setZ(5.0)
        return (node, text)

    def unload(self):
        self.disable()
        self._cleanupResultsIval()
        if self.winText is not None:
            for pair in self.winText:
                pair[1].reparentTo(hidden)
                pair[1].removeNode()

            self.winText = None
        if self.winStatus is not None:
            self.winStatus[1].reparentTo(hidden)
            self.winStatus[1].removeNode()
            self.winStatus = None
        if self.cogManager is not None:
            self.cogManager.unload()
            self.cogManager = None
        if self.arrows is not None:
            for pair in self.arrows:
                for arrow in pair:
                    arrow.destroy()
                    arrow = None

                pair = None

            self.arrows = None
        if self.distanceLabels is not None:
            for pair in self.distanceLabels:
                for node, text in pair:
                    node.removeNode()

                pair = None

        self.distanceLabels = None
        if len(self.players):
            for player in self.players.values():
                player.disable()
                player.destroy()

        self.players.clear()
        self.player = None
        if self.arena is not None:
            self.leftEntranceLocator = None
            self.rightEntranceLocator = None
            self.leftExitLocator = None
            self.rightExitLocator = None
            self._skyCollisions = None
            self._skyCollisionParent = None
            self._arenaFlagGroups = None
            self._destroyArenaDoors()
            self.arena.removeNode()
            self.arena = None
        for ival in self.toonPieTracks.values():
            if ival is not None and ival.isPlaying():
                try:
                    ival.finish()
                except Exception, theException:
                    self.notify.warning('Ival could not finish:\n %s \nException %s ' % (str(ival), str(theException)))

        self.toonPieTracks = {}
        for ival in self.pieIvals:
            if ival is not None and ival.isPlaying():
                try:
                    ival.finish()
                except Exception, theException:
                    self.notify.warning('Ival could not finish:\n %s \nException %s ' % (str(ival), str(theException)))

        self.pieIvals = []
        self.toonIdsToAnimIntervals = {}
        for eventName in self.toonPieEventNames.values():
            self.ignore(eventName)

        self.toonPieEventNames = {}
        return

    def enable(self):
        self.enableEnterGateCollision()

    def disable(self):
        self.disableEnterGateCollision()
        self.ignoreAll()

    def hideTeamFlags(self, team):
        self._arenaFlagGroups[team].stash()

    def showTeamFlags(self, team):
        self._arenaFlagGroups[team].unstash()

    def _playArenaDoorIval(self, team, opening = True):
        ival = self._arenaDoorIvals[team]
        if ival is not None and ival.isPlaying():
            ival.pause()
        if not opening:
            pos = self._doorStartPos[team]
        else:
            pos = (self._doorStartPos[team] + Point3(0, 0, -7.0),)
        ival = self._arenaDoors[team].posInterval(0.75, pos, blendType='easeIn')
        self._arenaDoorIvals[team] = ival
        ival.start()
        return

    def openArenaDoorForTeam(self, team):
        self._playArenaDoorIval(team, opening=True)

    def closeArenaDoorForTeam(self, team):
        self._playArenaDoorIval(team, opening=False)

    def openArenaDoors(self):
        self.enableEnterGateCollision()
        for i in range(len(self._arenaDoors)):
            self.openArenaDoorForTeam(i)

    def closeArenaDoors(self):
        self.disableEnterGateCollision()
        for i in range(len(self._arenaDoors)):
            self.closeArenaDoorForTeam(i)

    def showArenaDoorTimers(self, duration):
        for timer in self._arenaDoorTimers:
            timer.setTime(duration)
            timer.countdown(duration)
            timer.show()

    def hideArenaDoorTimers(self):
        for timer in self._arenaDoorTimers:
            timer.hide()

    def enableEnterGateCollision(self):
        self.acceptOnce('entercogPieArena_entranceLeft_collision', self.handleEnterLeftEntranceTrigger)
        self.acceptOnce('entercogPieArena_entranceRight_collision', self.handleEnterRightEntranceTrigger)

    def disableEnterGateCollision(self):
        self.ignore('entercogPieArena_entranceLeft_collision')
        self.ignore('entercogPieArena_entranceRight_collision')

    def enableWallCollisions(self):
        self._wallCollisionsCollection.unstash()

    def disableWallCollisions(self):
        self._wallCollisionsCollection.stash()

    def enableSkyCollisions(self):
        self._skyCollisionsCollection.unstash()

    def disableSkyCollisions(self):
        self._skyCollisionsCollection.stash()

    def handleEnterLeftEntranceTrigger(self, collEntry):
        self.activity.d_toonJoinRequest(PartyGlobals.TeamActivityTeams.LeftTeam)

    def handleEnterRightEntranceTrigger(self, collEntry):
        self.activity.d_toonJoinRequest(PartyGlobals.TeamActivityTeams.RightTeam)

    def checkOrthoDriveCollision(self, oldPos, newPos):
        x = bound(newPos[0], -16.8, 16.8)
        y = bound(newPos[1], -17.25, -24.1)
        newPos.setX(x)
        newPos.setY(y)
        return newPos

    def getPlayerStartPos(self, team, spot):
        if team == PartyGlobals.TeamActivityTeams.LeftTeam:
            node = self.leftExitLocator
        else:
            node = self.rightExitLocator
        d = self._lengthBetweenEntrances / (self.activity.getMaxPlayersPerTeam() + 1)
        yOffset = node.getY(self.root) + d * (spot + 1)
        pos = node.getPos(self.root)
        pos.setY(yOffset)
        return pos

    def handleToonJoined(self, toon, team, lateEntry = False):
        pos = self.getPlayerStartPos(team, self.activity.getIndex(toon.doId, team))
        if toon == base.localAvatar:
            player = PartyCogActivityLocalPlayer(self.activity, pos, team, self.handleToonExited)
            player.entersActivity()
            self.player = player
            self.disableSkyCollisions()
            self.playPlayerEnterIval()
        else:
            player = PartyCogActivityPlayer(self.activity, toon, pos, team)
            player.entersActivity()
            if lateEntry:
                player.updateToonPosition()
        self.players[toon.doId] = player

    def handleToonSwitchedTeams(self, toon):
        toonId = toon.doId
        player = self.players.get(toonId)
        if player is None:
            self.notify.warning('handleToonSwitchedTeams: toonId %s not found' % toonId)
            return
        team = self.activity.getTeam(toonId)
        spot = self.activity.getIndex(toonId, team)
        pos = self.getPlayerStartPos(team, spot)
        self.finishToonIval(toonId)
        player.setTeam(team)
        player.setToonStartPosition(pos)
        player.updateToonPosition()
        return

    def handleToonShifted(self, toon):
        toonId = toon.doId
        if self.players.has_key(toonId):
            player = self.players[toonId]
            spot = self.activity.getIndex(toonId, player.team)
            pos = self.getPlayerStartPos(player.team, spot)
            player.setToonStartPosition(pos)
            if self.player is not None and toon == self.player.toon:
                self.playToonIval(base.localAvatar.doId, self.player.getRunToStartPositionIval())
        return

    def handleToonDisabled(self, toonId):
        self.finishToonIval(toonId)
        self.finishPieIvals(toonId)
        player = self.players.get(toonId)
        if player is not None:
            player.disable()
            if player == self.player:
                self.player = None
            del self.players[toonId]
        return

    def finishPieIvals(self, toonId):
        for ival in self.pieIvals:
            if ival.isPlaying():
                if ival.getName().find(str(toonId)) != -1:
                    ival.finish()

    def playPlayerEnterIval(self):

        def conditionallyShowSwitchButton(self = self, enable = True):
            if enable and self.activity.activityFSM.state in ['WaitForEnough', 'WaitToStart']:
                self.activity.teamActivityGui.enableSwitchButton()
            else:
                self.activity.teamActivityGui.disableSwitchButton()

        ival = Sequence(Func(self.disableWallCollisions), Func(conditionallyShowSwitchButton, self, False), self.player.getRunToStartPositionIval(), Func(conditionallyShowSwitchButton, self, True), Func(self.enableWallCollisions))
        self.playToonIval(base.localAvatar.doId, ival)

    def finishToonIval(self, toonId):
        if self.toonIdsToAnimIntervals.get(toonId) is not None and self.toonIdsToAnimIntervals[toonId].isPlaying():
            self.toonIdsToAnimIntervals[toonId].finish()
        return

    def playToonIval(self, toonId, ival):
        self.finishToonIval(toonId)
        self.toonIdsToAnimIntervals[toonId] = ival
        ival.start()

    def startActivity(self, timestamp):
        self.pieHandler = CollisionHandlerEvent()
        self.pieHandler.setInPattern('pieHit-%fn')
        if self.player is not None:
            self.player.resetScore()
            self.hideTeamFlags(self.player.team)
        for player in self.players.values():
            self.finishToonIval(player.toon.doId)
            player.enable()

        for cog in self.cogManager.cogs:
            cog.request('Active', timestamp)

        for ival in self.pieIvals:
            if ival.isPlaying():
                ival.finish()

        self.pieIvals = []
        return

    def stopActivity(self):
        for player in self.players.values():
            player.disable()

        for eventName in self.toonPieEventNames.values():
            self.ignore(eventName)

        self.toonPieEventNames.clear()
        for cog in self.cogManager.cogs:
            cog.request('Static')

    def handleToonExited(self, toon):
        self.finishToonIval(toon.doId)
        player = self.players[toon.doId]
        player.disable()
        player.exitsActivity()
        player.destroy()
        if player == self.player:
            self.showTeamFlags(self.activity.getTeam(toon.doId))
            self.player = None
            self.enableEnterGateCollision()
            self.enableSkyCollisions()
        del self.players[toon.doId]
        return

    def pieThrow(self, avId, timestamp, heading, pos, power):
        toon = self.activity.getAvatar(avId)
        if toon is None:
            return
        tossTrack, pieTrack, flyPie = self.getTossPieInterval(toon, pos[0], pos[1], pos[2], heading, 0, 0, power)
        if avId == base.localAvatar.doId:
            flyPie.setTag('throwerId', str(avId))
            collSphere = CollisionSphere(0, 0, 0, 0.5)
            collSphere.setTangible(0)
            name = 'PieSphere-%d' % avId
            collSphereName = self.activity.uniqueName(name)
            collNode = CollisionNode(collSphereName)
            collNode.setFromCollideMask(ToontownGlobals.PieBitmask)
            collNode.addSolid(collSphere)
            collNP = flyPie.attachNewNode(collNode)
            base.cTrav.addCollider(collNP, self.pieHandler)
            self.toonPieEventNames[collNP] = 'pieHit-' + collSphereName
            self.accept(self.toonPieEventNames[collNP], self.handlePieCollision)
        else:
            player = self.players.get(avId)
            if player is not None:
                player.faceForward()

        def matchRunningAnim(toon = toon):
            toon.playingAnim = None
            toon.setSpeed(toon.forwardSpeed, toon.rotateSpeed)
            return

        newTossTrack = Sequence(tossTrack, Func(matchRunningAnim))
        pieTrack = Parallel(newTossTrack, pieTrack, name='PartyCogActivity.pieTrack-%d-%s' % (avId, timestamp))
        elapsedTime = globalClockDelta.localElapsedTime(timestamp)
        if elapsedTime < 16.0 / 24.0:
            elapsedTime = 16.0 / 24.0
        pieTrack.start(elapsedTime)
        self.pieIvals.append(pieTrack)
        self.toonPieTracks[avId] = pieTrack
        return

    def getTossPieInterval(self, toon, x, y, z, h, p, r, power, beginFlyIval = Sequence()):
        from toontown.toonbase import ToontownBattleGlobals
        from toontown.battle import BattleProps
        pie = toon.getPieModel()
        pie.setScale(0.5)
        flyPie = pie.copyTo(NodePath('a'))
        pieName = ToontownBattleGlobals.pieNames[toon.pieType]
        pieType = BattleProps.globalPropPool.getPropType(pieName)
        animPie = Sequence()
        if pieType == 'actor':
            animPie = ActorInterval(pie, pieName, startFrame=48)
        sound = loader.loadSfx('phase_3.5/audio/sfx/AA_pie_throw_only.mp3')
        t = power / 100.0
        dist = lerp(PartyGlobals.CogActivityPieMinDist, PartyGlobals.CogActivityPieMaxDist, t)
        time = lerp(1.0, 1.5, t)
        proj = ProjectileInterval(None, startPos=Point3(0, 0, 0), endPos=Point3(0, dist, 0), duration=time)
        relVel = proj.startVel

        def getVelocity(toon = toon, relVel = relVel):
            return render.getRelativeVector(toon, relVel) * 0.6

        def __safeSetAnimState(toon = toon, state = 'Happy'):
            if toon and hasattr(toon, 'animFSM'):
                toon.setAnimState('Happy')
            else:
                self.notify.warning('The toon is being destroyed. No attribute animState.')

        toss = Track((0, Sequence(Func(toon.setPosHpr, x, y, z, h, p, r), Func(pie.reparentTo, toon.rightHand), Func(pie.setPosHpr, 0, 0, 0, 0, 0, 0), animPie, Parallel(ActorInterval(toon, 'throw', startFrame=48, playRate=1.5, partName='torso'), animPie), Func(__safeSetAnimState, toon, 'Happy'))), (16.0 / 24.0, Func(pie.detachNode)))
        fly = Track((14.0 / 24.0, SoundInterval(sound, node=toon, cutOff=PartyGlobals.PARTY_COG_CUTOFF)), (16.0 / 24.0, Sequence(Func(flyPie.reparentTo, render), Func(flyPie.setPosHpr, toon, 0.52, 0.97, 2.24, 0, -45, 0), beginFlyIval, ProjectileInterval(flyPie, startVel=getVelocity, duration=6), Func(flyPie.detachNode))))
        return (toss, fly, flyPie)

    def handlePieCollision(self, colEntry):
        if not self.activity.isState('Active') or self.player is None:
            return
        handled = False
        into = colEntry.getIntoNodePath()
        intoName = into.getName()
        timestamp = globalClockDelta.localToNetworkTime(globalClock.getFrameTime(), bits=32)
        if 'PartyCog' in intoName:
            if self.toonPieTracks.get(base.localAvatar.doId) is not None:
                self.toonPieTracks[base.localAvatar.doId].finish()
                self.toonPieTracks[base.localAvatar.doId] = None
            parts = intoName.split('-')
            cogID = int(parts[1])
            point = colEntry.getSurfacePoint(self.cogManager.cogs[cogID].root)
            cog = self.cogManager.cogs[cogID]
            hitHead = point.getZ() > cog.getHeadLocation() and not parts[2].startswith('Arm')
            if self.activity.getTeam(base.localAvatar.doId) == PartyGlobals.TeamActivityTeams.LeftTeam:
                direction = -1.0
            else:
                direction = 1.0
            self.activity.b_pieHitsCog(timestamp, cogID, point, direction, hitHead)
            if hitHead:
                hitPoints = self.player.hitHead()
            else:
                hitPoints = self.player.hitBody()
            self.player.updateScore()
            if hitPoints > 0:
                cog.showHitScore(hitPoints)
            handled = True
        elif 'distAvatarCollNode' in intoName:
            parts = intoName.split('-')
            hitToonId = int(parts[1])
            toon = base.cr.doId2do.get(hitToonId)
            if toon is not None and self.activity.getTeam(hitToonId) != self.player.team:
                point = colEntry.getSurfacePoint(toon)
                self.activity.b_pieHitsToon(hitToonId, timestamp, point)
                handled = True
        if handled:
            eventName = self.toonPieEventNames.get(colEntry.getFromNodePath())
            if eventName is not None:
                self.ignore(eventName)
                del self.toonPieEventNames[colEntry.getFromNodePath()]

    def pieHitsCog(self, timestamp, cogNum, pos, direction, part):
        cog = self.cogManager.cogs[cogNum]
        cog.respondToPieHit(timestamp, pos, part, direction)

    def pieHitsToon(self, toonId, timestamp, pos):
        player = self.players.get(toonId)
        if player is not None:
            player.respondToPieHit(timestamp, pos)
        return

    def setCogDistances(self, distances):
        self.cogManager.updateDistances(distances)

    def showCogs(self):
        for cog in self.cogManager.cogs:
            cog.request('Static')

    def hideCogs(self):
        for cog in self.cogManager.cogs:
            cog.request('Down')

    def showResults(self, resultsText, winner, totals):
        if self.player is None:
            return
        base.localAvatar.showName()
        self.resultsIval = Sequence(Wait(0.1), Func(self.activity.setStatus, TTLocalizer.PartyCogTimeUp), Func(self.activity.showStatus), Wait(2.0), Func(self.activity.hideStatus), Wait(0.5), Func(self.player.lookAtArena), Func(self.showTeamFlags, self.activity.getTeam(base.localAvatar.doId)), Wait(1.0), Func(self.showArrow, 0), Wait(1.3), Func(self.showArrow, 1), Wait(1.3), Func(self.showArrow, 2), Wait(1.3), Func(self.showTotals, totals), Wait(1.0), Func(self.showWinner, resultsText, winner), Func(self._cleanupResultsIval), name='PartyCog-conclusionSequence')
        self.accept('DistributedPartyActivity-showJellybeanReward', self._cleanupResultsIval)
        self.resultsIval.start()
        return

    def _cleanupResultsIval(self):
        if self.resultsIval:
            if self.resultsIval.isPlaying():
                self.resultsIval.pause()
            self.resultsIval = None
        self.ignore('DistributedPartyActivity-showJellybeanReward')
        return

    def showTotals(self, totals):
        newtotals = (totals[1] - totals[0] + PartyGlobals.CogActivityArenaLength / 2.0 * 3, totals[0] - totals[1] + PartyGlobals.CogActivityArenaLength / 2.0 * 3)
        self.winText[0][0].setText(TTLocalizer.PartyCogDistance % newtotals[0])
        self.winText[1][0].setText(TTLocalizer.PartyCogDistance % newtotals[1])
        for textPair in self.winText:
            textPair[1].unstash()

    def hideTotals(self):
        for textPair in self.winText:
            textPair[0].setText('')
            textPair[1].stash()

    def showWinner(self, text, winner):
        self.winStatus[0].setText(text)
        self.winStatus[0].setTextColor(self.teamColors[winner])
        self.winStatus[1].unstash()

    def hideWinner(self):
        self.winStatus[0].setText('')
        self.winStatus[1].stash()

    def showArrow(self, arrowNum):
        arrows = self.arrows[arrowNum]
        cog = self.cogManager.cogs[arrowNum]
        points = [self.arena.find('**/cog%d_start_locator' % (arrowNum + 1)), self.arena.find('**/cog%d_end_locator' % (arrowNum + 1))]
        Y = cog.root.getY()
        for point in points:
            point.setY(Y)

        for i in range(len(arrows)):
            arrow = arrows[i]
            arrow.draw(points[i].getPos(), cog.root.getPos(), animate=False)
            arrow.unstash()

        i = -1
        length = PartyGlobals.CogActivityArenaLength
        for node, text in self.distanceLabels[arrowNum]:
            current = bound(i, 0, 1)
            node.setPos(cog.root.getPos(self.root) + Point3(i * 4, 2, 4))
            dist = PartyCogUtils.getCogDistanceUnitsFromCenter(cog.currentT)
            dist = abs(dist - i * length / 2)
            if dist > length - dist:
                node.setScale(2.8)
            else:
                node.setScale(2.2)
            text.setText(TTLocalizer.PartyCogDistance % dist)
            if dist > 0:
                node.unstash()
            else:
                arrows[current].stash()
            i += 2

    def hideArrows(self):
        for pair in self.arrows:
            for arrow in pair:
                arrow.stash()

        for pair in self.distanceLabels:
            for node, text in pair:
                node.stash()

    def hideResults(self):
        self.hideArrows()
        self.hideTotals()
        self.hideWinner()
