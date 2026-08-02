from panda3d.core import NodePath
from direct.distributed import DistributedObjectAI
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from toontown.coghq import DistributedCashbotBossCraneAI
from toontown.coghq import DistributedCashbotBossSafeAI


class DistributedTTCCraneSandboxAI(DistributedObjectAI.DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedTTCCraneSandboxAI')

    craneSandbox = True

    def __init__(self, air):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.scene = NodePath('scene')
        self.cranes = None
        self.safes = None
        self.heldObject = None
        self.attackCode = 0
        self.involvedToons = []

    def spawnCranesAndSafes(self):
        if self.cranes is not None:
            return
        self.cranes = []
        for index in range(len(ToontownGlobals.TTCCraneSandboxCranePosHprs)):
            crane = DistributedCashbotBossCraneAI.DistributedCashbotBossCraneAI(self.air, self, index)
            crane.generateWithRequired(self.zoneId)
            self.cranes.append(crane)

        self.safes = []
        for index in range(len(ToontownGlobals.TTCCraneSandboxSafePosHprs)):
            safe = DistributedCashbotBossSafeAI.DistributedCashbotBossSafeAI(self.air, self, index)
            safe.generateWithRequired(self.zoneId)
            self.safes.append(safe)

        for crane in self.cranes:
            crane.request('Free')

        for safe in self.safes:
            safe.request('Initial')

    def __deleteBattleObjects(self):
        if self.cranes is not None:
            for crane in self.cranes:
                try:
                    crane.request('Off')
                except Exception:
                    pass
                crane.requestDelete()

            self.cranes = None
        if self.safes is not None:
            for safe in self.safes:
                try:
                    safe.request('Off')
                except Exception:
                    pass
                safe.requestDelete()

            self.safes = None

    def delete(self):
        self.__deleteBattleObjects()
        DistributedObjectAI.DistributedObjectAI.delete(self)
