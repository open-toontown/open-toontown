from pandac import PandaModules as PM
from direct.directnotify.DirectNotifyGlobal import directNotify
from toontown.cogdominium.DistCogdoLevelGameAI import DistCogdoLevelGameAI
from toontown.cogdominium.DistCogdoCraneAI import DistCogdoCraneAI
from toontown.cogdominium import CogdoCraneGameConsts as GameConsts
from toontown.cogdominium.CogdoCraneGameBase import CogdoCraneGameBase
from toontown.cogdominium import CogdoGameConsts
from toontown.cogdominium.DistCogdoCraneMoneyBagAI import DistCogdoCraneMoneyBagAI
from toontown.cogdominium.DistCogdoCraneCogAI import DistCogdoCraneCogAI
from toontown.suit.SuitDNA import SuitDNA
import random

class DistCogdoCraneGameAI(CogdoCraneGameBase, DistCogdoLevelGameAI, PM.NodePath):
    notify = directNotify.newCategory('DistCogdoCraneGameAI')

    def __init__(self, air, interior):
        PM.NodePath.__init__(self, uniqueName('CraneGameAI'))
        DistCogdoLevelGameAI.__init__(self, air, interior)
        self._cranes = [
            None] * CogdoGameConsts.MaxPlayers
        self._moneyBags = [
            None] * 8

    def delete(self):
        DistCogdoLevelGameAI.delete(self)
        self.removeNode()

    def enterLoaded(self):
        DistCogdoLevelGameAI.enterLoaded(self)
        self.scene = PM.NodePath('scene')
        cn = PM.CollisionNode('walls')
        cs = PM.CollisionSphere(0, 0, 0, 13)
        cn.addSolid(cs)
        cs = PM.CollisionInvSphere(0, 0, 0, 42)
        cn.addSolid(cs)
        self.attachNewNode(cn)
        for i in range(CogdoGameConsts.MaxPlayers):
            crane = DistCogdoCraneAI(self.air, self, i)
            crane.generateWithRequired(self.zoneId)
            self._cranes[i] = crane

        for i in range(len(self._moneyBags)):
            mBag = DistCogdoCraneMoneyBagAI(self.air, self, i)
            mBag.generateWithRequired(self.zoneId)
            self._moneyBags[i] = mBag

    def exitLoaded(self):
        for i in range(len(self._moneyBags)):
            if self._moneyBags[i]:
                self._moneyBags[i].requestDelete()
                self._moneyBags[i] = None

        for i in range(CogdoGameConsts.MaxPlayers):
            if self._cranes[i]:
                self._cranes[i].requestDelete()
                self._cranes[i] = None

        DistCogdoLevelGameAI.exitLoaded(self)

    def enterGame(self):
        DistCogdoLevelGameAI.enterGame(self)
        for i in range(self.getNumPlayers()):
            self._cranes[i].request('Controlled', self.getToonIds()[i])

        for i in range(len(self._moneyBags)):
            if self._moneyBags[i]:
                self._moneyBags[i].request('Initial')

        self._cog = DistCogdoCraneCogAI(self.air, self, self.getDroneCogDNA(), random.randrange(4), globalClock.getFrameTime())
        self._cog.generateWithRequired(self.zoneId)
        self._scheduleGameDone()

    def _scheduleGameDone(self):
        timeLeft = GameConsts.Settings.GameDuration.get() - (globalClock.getRealTime() - self.getStartTime())
        if timeLeft > 0:
            self._gameDoneEvent = taskMgr.doMethodLater(timeLeft, self._gameDoneDL, self.uniqueName('boardroomGameDone'))
        else:
            self._gameDoneDL()

    def exitGame(self):
        self._cog.requestDelete()
        self._cog = None
        taskMgr.remove(self._gameDoneEvent)
        self._gameDoneEvent = None

    def _gameDoneDL(self, task = None):
        self._handleGameFinished()
        return task.done

    def enterFinish(self):
        DistCogdoLevelGameAI.enterFinish(self)
        self._finishDoneEvent = taskMgr.doMethodLater(10.0, self._finishDoneDL, self.uniqueName('boardroomFinishDone'))

    def exitFinish(self):
        taskMgr.remove(self._finishDoneEvent)
        self._finishDoneEvent = None

    def _finishDoneDL(self, task):
        self.announceGameDone()
        return task.done

    if __dev__:

        def _handleGameDurationChanged(self, gameDuration):
            if hasattr(self, '_gameDoneEvent') and self._gameDoneEvent != None:
                taskMgr.remove(self._gameDoneEvent)
                self._scheduleGameDone()
