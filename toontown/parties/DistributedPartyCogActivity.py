from direct.distributed.ClockDelta import globalClockDelta
from pandac.PandaModules import Point3
from toontown.toonbase import TTLocalizer
from . import PartyGlobals
from .DistributedPartyTeamActivity import DistributedPartyTeamActivity
from .PartyCogActivity import PartyCogActivity

class DistributedPartyCogActivity(DistributedPartyTeamActivity):
    notify = directNotify.newCategory('DistributedPartyCogActivity')
    players = {}
    localPlayer = None
    view = None

    def __init__(self, cr, arenaModel = 'phase_13/models/parties/cogPieArena_model', texture = None):
        DistributedPartyTeamActivity.__init__(self, cr, PartyGlobals.ActivityIds.PartyCog, startDelay=PartyGlobals.CogActivityStartDelay, balanceTeams=PartyGlobals.CogActivityBalanceTeams)
        self.arenaModel = arenaModel
        self.texture = texture

    def load(self):
        DistributedPartyTeamActivity.load(self)
        self.view = PartyCogActivity(self, self.arenaModel, self.texture)
        self.view.load()

    def announceGenerate(self):
        DistributedPartyTeamActivity.announceGenerate(self)
        for i in range(len(self.toonIds)):
            for toonId in self.toonIds[i]:
                toon = base.cr.doId2do.get(toonId, None)
                if toon:
                    self.view.handleToonJoined(toon, i, lateEntry=True)

        return

    def unload(self):
        if hasattr(self, 'view') and self.view is not None:
            self.view.unload()
            del self.view
        DistributedPartyTeamActivity.unload(self)
        return

    def enable(self):
        DistributedPartyTeamActivity.enable(self)

    def disable(self):
        DistributedPartyTeamActivity.disable(self)

    def getTitle(self):
        return TTLocalizer.PartyCogTitle

    def getInstructions(self):
        return TTLocalizer.PartyCogInstructions

    def pieThrow(self, toonId, timestamp, h, x, y, z, power):
        if toonId not in self.toonIds:
            return
        if toonId != base.localAvatar.doId:
            self.view.pieThrow(toonId, timestamp, h, Point3(x, y, z), power)

    def b_pieThrow(self, toon, power):
        timestamp = globalClockDelta.localToNetworkTime(globalClock.getFrameTime(), bits=32)
        pos = toon.getPos()
        h = toon.getH()
        toonId = toon.doId
        self.view.pieThrow(toonId, timestamp, h, pos, power)
        self.d_broadcastPieThrow(toonId, timestamp, h, pos[0], pos[1], pos[2], power)

    def d_broadcastPieThrow(self, toonId, timestamp, h, x, y, z, power):
        self.sendUpdate('pieThrow', [toonId,
         timestamp,
         h,
         x,
         y,
         z,
         power])

    def pieHitsToon(self, toonId, timestamp, x, y, z):
        if toonId not in self.toonIds:
            return
        self.view.pieHitsToon(toonId, timestamp, Point3(x, y, z))

    def d_broadcastPieHitsToon(self, toonId, timestamp, pos):
        self.sendUpdate('pieHitsToon', [toonId,
         timestamp,
         pos[0],
         pos[1],
         pos[2]])

    def b_pieHitsToon(self, toonId, timestamp, pos):
        self.view.pieHitsToon(toonId, timestamp, pos)
        self.d_broadcastPieHitsToon(toonId, timestamp, pos)

    def pieHitsCog(self, toonId, timestamp, hitCogNum, x, y, z, direction, part):
        if toonId not in self.toonIds:
            return
        if toonId != base.localAvatar.doId:
            self.view.pieHitsCog(timestamp, hitCogNum, Point3(x, y, z), direction, part)

    def b_pieHitsCog(self, timestamp, hitCogNum, pos, direction, part):
        self.view.pieHitsCog(timestamp, hitCogNum, pos, direction, part)
        self.d_broadcastSendPieHitsCog(timestamp, hitCogNum, pos, direction, part)

    def d_broadcastSendPieHitsCog(self, timestamp, hitCogNum, pos, direction, part):
        self.sendUpdate('pieHitsCog', [base.localAvatar.doId,
         timestamp,
         hitCogNum,
         pos[0],
         pos[1],
         pos[2],
         direction,
         part])

    def setCogDistances(self, distances):
        self.view.setCogDistances(distances)

    def setHighScore(self, toonName, score):
        self.setSignNote(TTLocalizer.PartyCogSignNote % (toonName, score))

    def handleToonJoined(self, toonId):
        DistributedPartyTeamActivity.handleToonJoined(self, toonId)
        toon = base.cr.doId2do.get(toonId, None)
        team = self.getTeam(toonId)
        if toon is not None and self.view is not None:
            self.view.handleToonJoined(toon, team)
        return

    def handleToonExited(self, toonId):
        toon = base.cr.doId2do.get(toonId, None)
        if toon is None:
            return
        if self.view is not None:
            self.view.handleToonExited(toon)
        DistributedPartyTeamActivity.handleToonExited(self, toonId)
        return

    def handleToonShifted(self, toonId):
        toon = base.cr.doId2do.get(toonId, None)
        if toon is None:
            return
        if self.view is not None:
            self.view.handleToonShifted(toon)
        return

    def handleToonSwitchedTeams(self, toonId):
        DistributedPartyTeamActivity.handleToonSwitchedTeams(self, toonId)
        toon = base.cr.doId2do.get(toonId, None)
        if toon is None:
            return
        if self.view is not None:
            self.view.handleToonSwitchedTeams(toon)
        return

    def handleToonDisabled(self, toonId):
        if self.view is not None:
            self.view.handleToonDisabled(toonId)
        return

    def startWaitForEnough(self):
        DistributedPartyTeamActivity.startWaitForEnough(self)
        self.view.openArenaDoors()
        self.view.hideCogs()

    def startRules(self):
        DistributedPartyTeamActivity.startRules(self)
        self.view.closeArenaDoors()
        self.view.showCogs()

    def startActive(self):
        DistributedPartyTeamActivity.startActive(self)
        self.view.startActivity(self.getCurrentActivityTime())
        self.view.closeArenaDoors()
        if not self.isLocalToonPlaying:
            self.view.showArenaDoorTimers(self._duration + PartyGlobals.CogActivityConclusionDuration + 1.0 - self.getCurrentActivityTime())

    def finishActive(self):
        DistributedPartyTeamActivity.finishActive(self)
        self.view.stopActivity()

    def startConclusion(self, data):
        DistributedPartyTeamActivity.startConclusion(self, data)
        if self.isLocalToonPlaying:
            score = (int(data / 10000), data % 10000)
            winner = 2
            if score[PartyGlobals.TeamActivityTeams.LeftTeam] > score[PartyGlobals.TeamActivityTeams.RightTeam]:
                winner = PartyGlobals.TeamActivityTeams.LeftTeam
            elif score[PartyGlobals.TeamActivityTeams.LeftTeam] < score[PartyGlobals.TeamActivityTeams.RightTeam]:
                winner = PartyGlobals.TeamActivityTeams.RightTeam
            if winner < 2:
                if self.getTeam(base.localAvatar.doId) == winner:
                    resultsText = TTLocalizer.PartyTeamActivityLocalAvatarTeamWins
                else:
                    resultsText = TTLocalizer.PartyTeamActivityWins % TTLocalizer.PartyCogTeams[winner]
            else:
                resultsText = TTLocalizer.PartyTeamActivityGameTie
            self.view.showResults(resultsText, winner, score)

    def finishConclusion(self):
        self.view.hideResults()
        DistributedPartyTeamActivity.finishConclusion(self)
        self.view.hideArenaDoorTimers()
