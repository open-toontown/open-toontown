from otp.ai.AIBase import *
from direct.distributed.ClockDelta import *
from .BattleBase import *
from .BattleCalculatorAI import *
from toontown.toonbase.ToontownBattleGlobals import *
from .SuitBattleGlobals import *
from direct.showbase.PythonUtil import addListsByValue
from . import DistributedBattleBaseAI
from direct.task import Task
from direct.directnotify import DirectNotifyGlobal
import random
from direct.fsm import State
from direct.fsm import ClassicFSM, State
from otp.otpbase import PythonUtil

class DistributedBattleBldgAI(DistributedBattleBaseAI.DistributedBattleBaseAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedBattleBldgAI')

    def __init__(self, air, zoneId, roundCallback=None, finishCallback=None, maxSuits=4, bossBattle=0):
        DistributedBattleBaseAI.DistributedBattleBaseAI.__init__(self, air, zoneId, finishCallback, maxSuits, bossBattle)
        self.streetBattle = 0
        self.roundCallback = roundCallback
        self.fsm.addState(State.State('BuildingReward', self.enterBuildingReward, self.exitBuildingReward, [
         'Resume']))
        playMovieState = self.fsm.getStateNamed('PlayMovie')
        playMovieState.addTransition('BuildingReward')
        self.elevatorPos = Point3(0, -30, 0)
        self.resumeNeedUpdate = 0

    def setInitialMembers(self, toonIds, suits):
        for suit in suits:
            self.addSuit(suit)

        for toonId in toonIds:
            self.addToon(toonId)

        self.fsm.request('FaceOff')

    def delete(self):
        del self.roundCallback
        DistributedBattleBaseAI.DistributedBattleBaseAI.delete(self)

    def faceOffDone(self):
        toonId = self.air.getAvatarIdFromSender()
        if self.ignoreResponses == 1:
            self.notify.debug('faceOffDone() - ignoring toon: %d' % toonId)
            return
        else:
            if self.fsm.getCurrentState().getName() != 'FaceOff':
                self.notify.warning('faceOffDone() - in state: %s' % self.fsm.getCurrentState().getName())
                return
            else:
                if self.toons.count(toonId) == 0:
                    self.notify.warning('faceOffDone() - toon: %d not in toon list' % toonId)
                    return
        self.responses[toonId] += 1
        self.notify.debug('toon: %d done facing off' % toonId)
        if not self.ignoreFaceOffDone:
            if self.allToonsResponded():
                self.handleFaceOffDone()
            else:
                self.timer.stop()
                self.timer.startCallback(TIMEOUT_PER_USER, self.__serverFaceOffDone)

    def enterFaceOff(self):
        self.notify.debug('enterFaceOff()')
        self.joinableFsm.request('Joinable')
        self.runableFsm.request('Unrunable')
        self.timer.startCallback(self.calcToonMoveTime(self.pos, self.elevatorPos) + FACEOFF_TAUNT_T + SERVER_BUFFER_TIME, self.__serverFaceOffDone)
        return None

    def __serverFaceOffDone(self):
        self.notify.debug('faceoff timed out on server')
        self.ignoreFaceOffDone = 1
        self.handleFaceOffDone()

    def exitFaceOff(self):
        self.timer.stop()
        self.resetResponses()
        return None

    def handleFaceOffDone(self):
        for suit in self.suits:
            self.activeSuits.append(suit)

        for toon in self.toons:
            self.activeToons.append(toon)
            self.sendEarnedExperience(toon)

        self.d_setMembers()
        self.b_setState('WaitForInput')

    def localMovieDone(self, needUpdate, deadToons, deadSuits, lastActiveSuitDied):
        self.timer.stop()
        self.resumeNeedUpdate = needUpdate
        self.resumeDeadToons = deadToons
        self.resumeDeadSuits = deadSuits
        self.resumeLastActiveSuitDied = lastActiveSuitDied
        if len(self.toons) == 0:
            self.d_setMembers()
            self.b_setState('Resume')
        else:
            totalHp = 0
            for suit in self.suits:
                if suit.currHP > 0:
                    totalHp += suit.currHP

            self.roundCallback(self.activeToons, totalHp, deadSuits)

    def __goToResumeState(self, task):
        self.b_setState('Resume')

    def resume(self, currentFloor=0, topFloor=0):
        if len(self.suits) == 0:
            self.d_setMembers()
            self.suitsKilledPerFloor.append(self.suitsKilledThisBattle)
            if topFloor == 0:
                self.b_setState('Reward')
            else:
                for floorNum, cogsThisFloor in PythonUtil.enumerate(self.suitsKilledPerFloor):
                    for toonId in self.activeToons:
                        toon = self.getToon(toonId)
                        if toon:
                            recovered, notRecovered = self.air.questManager.recoverItems(toon, cogsThisFloor, self.zoneId)
                            self.toonItems[toonId][0].extend(recovered)
                            self.toonItems[toonId][1].extend(notRecovered)
                            meritArray = self.air.promotionMgr.recoverMerits(toon, cogsThisFloor, self.zoneId, getCreditMultiplier(floorNum))
                            if toonId in self.helpfulToons:
                                self.toonMerits[toonId] = addListsByValue(self.toonMerits[toonId], meritArray)
                            else:
                                self.notify.debug('toon %d not helpful, skipping merits' % toonId)

                self.d_setBattleExperience()
                self.b_setState('BuildingReward')
        else:
            if self.resumeNeedUpdate == 1:
                self.d_setMembers()
                if len(self.resumeDeadSuits) > 0 and self.resumeLastActiveSuitDied == 0 or len(self.resumeDeadToons) > 0:
                    self.needAdjust = 1
            self.setState('WaitForJoin')
        self.resumeNeedUpdate = 0
        self.resumeDeadToons = []
        self.resumeDeadSuits = []
        self.resumeLastActiveSuitDied = 0

    def enterReservesJoining(self, ts=0):
        return None

    def exitReservesJoining(self, ts=0):
        return None

    def enterReward(self):
        self.timer.startCallback(FLOOR_REWARD_TIMEOUT, self.serverRewardDone)
        return None

    def exitReward(self):
        self.timer.stop()
        return None

    def enterBuildingReward(self):
        self.resetResponses()
        self.assignRewards()
        self.timer.startCallback(BUILDING_REWARD_TIMEOUT, self.serverRewardDone)
        return None

    def exitBuildingReward(self):
        return None

    def enterResume(self):
        DistributedBattleBaseAI.DistributedBattleBaseAI.enterResume(self)
        self.finishCallback(self.zoneId, self.activeToons)

    def exitResume(self):
        DistributedBattleBaseAI.DistributedBattleBaseAI.exitResume(self)
        taskName = self.taskName('finish')
        taskMgr.remove(taskName)
