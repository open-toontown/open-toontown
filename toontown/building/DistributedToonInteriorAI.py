from toontown.toonbase.ToontownGlobals import *
from otp.ai.AIBaseGlobal import *
from direct.distributed.ClockDelta import *
import pickle
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State
from direct.distributed import DistributedObjectAI
from direct.fsm import State
from toontown.toon import NPCToons
from toontown.toon.ToonDNA import ToonDNA

class DistributedToonInteriorAI(DistributedObjectAI.DistributedObjectAI):

    def __init__(self, *args):
        """
        Astron constructs AI-side distributed objects with only (air).
        Game code also constructs this object manually as (block, air, zoneId, building).
        Support both.
        """
        if len(args) == 1:
            air = args[0]
            block = 0
            zoneId = 0
            building = None
        else:
            block, air, zoneId, building = args[:4]
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.block = block
        self.zoneId = zoneId
        self.building = building
        self.npcs = NPCToons.createNpcsInZone(air, zoneId) if zoneId else []
        self.fsm = ClassicFSM.ClassicFSM('DistributedToonInteriorAI', [
         State.State('toon', self.enterToon, self.exitToon, [
          'beingTakenOver']),
         State.State('beingTakenOver', self.enterBeingTakenOver, self.exitBeingTakenOver, []),
         State.State('off', self.enterOff, self.exitOff, [])], 'toon', 'off')
        self.fsm.enterInitialState()

    # DC required field initializer (see etc/toon.dc: DistributedToonInterior.setZoneIdAndBlock)
    def setZoneIdAndBlock(self, zoneId, block):
        self.zoneId = zoneId
        self.block = block
        if not getattr(self, 'npcs', None):
            self.npcs = NPCToons.createNpcsInZone(self.air, zoneId) if zoneId else []

    def delete(self):
        self.ignoreAll()
        for npc in self.npcs:
            npc.requestDelete()

        del self.npcs
        del self.fsm
        del self.building
        DistributedObjectAI.DistributedObjectAI.delete(self)

    def getZoneIdAndBlock(self):
        r = [
         self.zoneId, self.block]
        return r

    def getSavedBy(self):
        savedBy = []
        for avId, name, dnaTuple in self.building.savedBy:
            dna = ToonDNA()
            dna.newToonFromProperties(*dnaTuple)
            savedBy.append([avId, name, dna.makeNetString()])
        return savedBy

    def getState(self):
        r = [
         self.fsm.getCurrentState().getName(), globalClockDelta.getRealNetworkTime()]
        return r

    def setState(self, state, timestamp=0):
        # Timestamp is supplied by the DC field signature; AI doesn't need it.
        self.sendUpdate('setState', [state, globalClockDelta.getRealNetworkTime()])
        self.fsm.request(state)

    def enterOff(self):
        pass

    def exitOff(self):
        pass

    def enterToon(self):
        pass

    def exitToon(self):
        pass

    def enterBeingTakenOver(self):
        pass

    def exitBeingTakenOver(self):
        pass
