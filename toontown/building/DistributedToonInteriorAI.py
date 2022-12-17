from toontown.toonbase.ToontownGlobals import *
""" DistributedToonInteriorAI module: contains the DistributedToonInteriorAI
    class, the server side representation of a 'landmark door'."""


from otp.ai.AIBaseGlobal import *
from direct.distributed.ClockDelta import *

import pickle
from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State
from direct.distributed import DistributedObjectAI
from direct.fsm import State
from toontown.toon import NPCToons

class DistributedToonInteriorAI(DistributedObjectAI.DistributedObjectAI):
    """
    DistributedToonInteriorAI class:  
    """

    if __debug__:
        notify = DirectNotifyGlobal.directNotify.newCategory('DistributedToonInteriorAI')

    def __init__(self, block, air, zoneId, building):
        """blockNumber: the landmark building number (from the name)"""
        #self.air=air
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.block=block
        self.zoneId=zoneId
        self.building=building
        assert(self.debugPrint(
                "DistributedToonInteriorAI(air=%s, zoneId=%s, building=%s)"
                %(air, zoneId, building)))

        # Make any npcs that may be in this interior zone
        # If there are none specified, this will just be an empty list
        self.npcs = NPCToons.createNpcsInZone(air, zoneId)

        # TODO
        #for i in range(len(self.npcs)):
        #    npc = self.npcs[i]
        #    npc.d_setIndex(i)
        
        self.fsm = ClassicFSM.ClassicFSM('DistributedToonInteriorAI',
                               [State.State('toon',
                                            self.enterToon,
                                            self.exitToon,
                                            ['beingTakenOver']),
                                State.State('beingTakenOver',
                                            self.enterBeingTakenOver,
                                            self.exitBeingTakenOver,
                                            []),
                                State.State('off',
                                            self.enterOff,
                                            self.exitOff,
                                            []),
                                ],
                               # Initial State
                               'toon',
                               # Final State
                               'off',
                               )
        self.fsm.enterInitialState()

    def delete(self):
        assert(self.debugPrint("delete()"))
        self.ignoreAll()
        for npc in self.npcs:
            npc.requestDelete()
        del self.npcs
        del self.fsm
        del self.building
        DistributedObjectAI.DistributedObjectAI.delete(self)
        
    def getZoneIdAndBlock(self):
        r=[self.zoneId, self.block]
        assert(self.debugPrint("getZoneIdAndBlock() returning: "+str(r)))
        return r
    
    def getToonData(self):
        assert(self.notify.debug("getToonData()"))
        return pickle.dumps(self.building.savedBy, 1)
    
    def getState(self):
        r=[self.fsm.getCurrentState().getName(),
           globalClockDelta.getRealNetworkTime()]
        assert(self.debugPrint("getState()  returning: "+str(r)))
        return r
    
    def setState(self, state):
        assert(self.debugPrint("setState("+str(state)+")"))
        self.sendUpdate('setState', [state, globalClockDelta.getRealNetworkTime()])
        self.fsm.request(state)
    
    def enterOff(self):
        assert(self.debugPrint("enterOff()"))
    
    def exitOff(self):
        assert(self.debugPrint("exitOff()"))
    
    def enterToon(self):
        assert(self.debugPrint("enterToon()"))
    
    def exitToon(self):
        assert(self.debugPrint("exitToon()"))
    
    def enterBeingTakenOver(self):
        """Kick everybody out of the building"""
        assert(self.debugPrint("enterBeingTakenOver()"))
    
    def exitBeingTakenOver(self):
        assert(self.debugPrint("exitBeingTakenOver()"))
    
    if __debug__:
        def debugPrint(self, message):
            """for debugging"""
            return self.notify.debug(
                    str(self.__dict__.get('zoneId', '?'))+' '+message)

