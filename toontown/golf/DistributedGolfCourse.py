from direct.interval.IntervalGlobal import Sequence, Func, Wait, LerpColorScaleInterval, Parallel
from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from direct.task.Task import Task
from direct.showbase import PythonUtil
from toontown.distributed import DelayDelete
from toontown.distributed.DelayDeletable import DelayDeletable
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from pandac.PandaModules import *
from direct.gui.DirectGui import *
from direct.distributed.ClockDelta import *
from direct.fsm.FSM import FSM
from toontown.golf import GolfGlobals
from toontown.golf import GolfScoreBoard
from toontown.golf import GolfRewardDialog
from toontown.toon import ToonHeadFrame

class DistributedGolfCourse(DistributedObject.DistributedObject, FSM, DelayDeletable):
    notify = directNotify.newCategory('DistributedGolfCourse')
    defaultTransitions = {'Off': ['Join'],
     'Join': ['WaitStartHole', 'Cleanup'],
     'WaitStartHole': ['PlayHole', 'Cleanup', 'WaitReward'],
     'PlayHole': ['WaitFinishCourse',
                  'WaitStartHole',
                  'WaitReward',
                  'Cleanup'],
     'WaitReward': ['WaitFinishCourse', 'Cleanup'],
     'WaitFinishCourse': ['Cleanup'],
     'Cleanup': ['Off']}
    id = 0

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, base.cr)
        FSM.__init__(self, 'Golf_%s_FSM' % self.id)
        self.waitingStartLabel = DirectLabel(text=TTLocalizer.MinigameWaitingForOtherPlayers, text_fg=VBase4(1, 1, 1, 1), relief=None, pos=(-0.6, 0, -0.75), scale=0.075)
        self.waitingStartLabel.hide()
        self.avIdList = []
        self.remoteAvIdList = []
        self.exitedAvIdList = []
        self.toonPanels = []
        self.exitedPanels = []
        self.exitedToonsWithPanels = []
        self.localAvId = base.localAvatar.doId
        self.hasLocalToon = 0
        self.modelCount = 500
        self.cleanupActions = []
        self.courseId = None
        self.scores = {}
        self.curHoleIndex = 0
        self.golfRewardDialog = None
        self.rewardIval = None
        self.scoreBoard = None
        self.exit = False
        self.drivingToons = []
        return

    def generate(self):
        self.notify.debug('GOLF COURSE: generate, %s' % self.getTitle())
        DistributedObject.DistributedObject.generate(self)

    def announceGenerate(self):
        DistributedObject.DistributedObject.announceGenerate(self)
        if not self.hasLocalToon:
            return
        self.notify.debug('BASE: handleAnnounceGenerate: send setAvatarJoined')
        self.__delayDelete = DelayDelete.DelayDelete(self, 'GolfCourse.self')
        self.request('Join')
        self.normalExit = 1
        count = self.modelCount
        loader.beginBulkLoad('minigame', TTLocalizer.HeadingToMinigameTitle % self.getTitle(), count, 1, TTLocalizer.TIP_GOLF)
        self.load()
        globalClock.syncFrameTime()
        self.onstage()
        self.accept('clientCleanup', self._handleClientCleanup)

    def _handleClientCleanup(self):
        self._destroyDelayDelete()

    def _destroyDelayDelete(self):
        if self.__delayDelete:
            self.__delayDelete.destroy()
            self.__delayDelete = None
        return

    def delete(self):
        print 'GOLF COURSE DELETE'
        self.ignore('clientCleanup')
        if self.scoreBoard:
            self.scoreBoard.delete()
        DistributedObject.DistributedObject.delete(self)
        if self.golfRewardDialog:
            self.golfRewardDialog.delete()
        self.cleanUpReward()
        if self.toonPanels:
            for x in range(len(self.toonPanels)):
                self.toonPanels[x].destroy()

            self.toonPanels = None
        self.scores = None
        self.music.stop()
        self.music = None
        for avId in self.avIdList:
            av = base.cr.doId2do.get(avId)
            if av:
                av.show()

        return

    def load(self):
        self.music = base.loadMusic('phase_6/audio/bgm/GZ_PlayGolf.mid')

    def setCourseReady(self, numHoles, holeIds, coursePar):
        self.notify.debug('GOLF COURSE: received setCourseReady')
        if self.state == 'Cleanup':
            return
        self.numHoles = numHoles
        self.holeIds = holeIds
        self.coursePar = coursePar
        for avId in self.avIdList:
            blankScoreList = [0] * self.numHoles
            self.scores[avId] = blankScoreList

        self.request('WaitStartHole')
        for avId in self.avIdList:
            av = base.cr.doId2do.get(avId)
            if av:
                av.show()
                av.reparentTo(render)
                av.setPos(0, 0, -100)
            else:
                self.notify.warning('avId =%d does not exist')

        self.scoreBoard = GolfScoreBoard.GolfScoreBoard(self)
        toonPanelsStart = 0.3
        whichToon = 0
        color = 0
        tpDiff = -0.45
        headPanel = loader.loadModel('phase_6/models/golf/headPanel')
        if self.numPlayers > 0:
            for avId in self.avIdList:
                if not self.localAvId == avId:
                    av = base.cr.doId2do.get(avId)
                    if av:
                        tPanels = ToonHeadFrame.ToonHeadFrame(av, GolfGlobals.PlayerColors[color], headPanel)
                        tPanels.setPos(-1.17, 0, toonPanelsStart + whichToon * tpDiff)
                        tPanels.setScale(0.3, 1, 0.7)
                        tPanels.head.setPos(0, 10, 0.18)
                        tPanels.head.setScale(0.47, 0.2, 0.2)
                        tPanels.tag1.setPos(0.3, 10, 0.18)
                        tPanels.tag1.setScale(0.1283, 0.055, 0.055)
                        tPanels.tag2.setPos(0, 10, 0.43)
                        tPanels.tag2.setScale(0.117, 0.05, 0.05)
                        self.toonPanels.append(tPanels)
                        whichToon = whichToon + 1
                        color += 1
                else:
                    color += 1

        else:
            self.toonPanels = None
        for avId in self.exitedAvIdList:
            if avId not in self.exitedToonsWithPanels:
                self.exitMessageForToon(avId)

        return

    def setPlayHole(self):
        self.notify.debug('GOLF COURSE: received setPlayHole')
        if self.state not in ['PlayHole', 'Cleanup']:
            self.request('PlayHole')

    def getTitle(self):
        return GolfGlobals.getCourseName(self.courseId)

    def getInstructions(self):
        return 'You should not be seeing this'

    def setGolferIds(self, avIds):
        self.avIdList = avIds
        self.numPlayers = len(self.avIdList)
        self.hasLocalToon = self.localAvId in self.avIdList
        if not self.hasLocalToon:
            self.notify.warning('localToon (%s) not in list of golfers: %s' % (self.localAvId, self.avIdList))
            return
        self.notify.info('GOLF COURSE: setParticipants: %s' % self.avIdList)
        self.remoteAvIdList = []
        for avId in self.avIdList:
            if avId != self.localAvId:
                self.remoteAvIdList.append(avId)

    def setCourseAbort(self, avId):
        if avId == self.localAvId or avId == 0:
            if not self.hasLocalToon:
                return
            self.notify.warning('GOLF COURSE: setGameAbort: Aborting game')
            self.normalExit = 0
            if not self.state == 'Cleanup':
                self.request('Cleanup')
            else:
                self.notify.warning('GOLF COURSE: Attempting to clean up twice')

    def onstage(self):
        self.notify.debug('GOLF COURSE: onstage')
        base.playMusic(self.music, looping=1, volume=0.9)

    def avExited(self, avId):
        self.exitedAvIdList.append(avId)
        hole = base.cr.doId2do.get(self.curHoleDoId)
        if hole:
            hole.avExited(avId)
        if self.localAvId == avId:
            self.notify.debug('forcing setCourseAbort')
            if self.state == 'Join':
                loader.endBulkLoad('minigame')
            self.setCourseAbort(0)
        self.exitMessageForToon(avId)

    def exitMessageForToon(self, avId):
        if self.toonPanels and self.localAvId != avId:
            y = 0
            for x in range(len(self.avIdList)):
                if avId == self.avIdList[x] and y < len(self.toonPanels):
                    toonPanel = self.toonPanels[y]
                    toonPanel.headModel.hide()
                    exitedToon = DirectLabel(parent=self.toonPanels[y], relief=None, pos=(0, 0, 0.4), color=(1, 1, 1, 1), text_align=TextNode.ACenter, text=TTLocalizer.GolferExited % toonPanel.av.getName(), text_scale=0.07, text_wordwrap=6)
                    exitedToon.setScale(2, 1, 1)
                    self.exitedPanels.append(exitedToon)
                    self.exitedToonsWithPanels.append(avId)
                    toonPanel.removeAvKeep()
                elif not self.avIdList[x] == self.localAvId:
                    y += 1

        return

    def enterJoin(self):
        self.sendUpdate('setAvatarJoined', [])

    def handleFallingAsleepGolf(self, task):
        base.localAvatar.stopSleepWatch()
        base.localAvatar.forceGotoSleep()
        self.sendUpdate('setAvatarExited', [])

    def exitJoin(self):
        pass

    def enterWaitStartHole(self):
        self.sendUpdate('setAvatarReadyCourse', [])

    def exitWaitStartHole(self):
        pass

    def enterPlayHole(self):
        loader.endBulkLoad('minigame')

    def exitPlayHole(self):
        pass

    def enterCleanup(self):
        print 'GOLF COURSE CLEANUP'
        base.localAvatar.stopSleepWatch()
        for action in self.cleanupActions:
            action()

        self.cleanupActions = []
        if not self.scoreBoard == None:
            self.scoreBoard.delete()
        if self.toonPanels:
            for x in range(len(self.toonPanels)):
                self.toonPanels[x].destroy()

        self.toonPanels = None
        for avId in self.avIdList:
            av = base.cr.doId2do.get(avId)
            if av:
                av.show()
                av.resetLOD()

        self.ignoreAll()
        if self.hasLocalToon:
            messenger.send('leavingGolf')
            self._destroyDelayDelete()
        return

    def exitCleanup(self):
        pass

    def setCourseId(self, courseId):
        self.courseId = courseId

    def calcHolesToUse(self):
        retval = []
        while len(retval) < self.numHoles:
            for holeId in self.courseInfo['holeIds']:
                retval.append(holeId)
                if len(retval) >= self.numHoles:
                    break

        return retval

    def calcCoursePar(self):
        retval = 0
        for holeId in self.holeIds:
            holeInfo = GolfGlobals.HoleInfo[holeId]
            retval += holeInfo['par']

        return retval

    def setScores(self, scoreList):
        scoreList.reverse()
        for avId in self.avIdList:
            avScores = []
            for holeIndex in range(self.numHoles):
                avScores.append(scoreList.pop())

            self.scores[avId] = avScores

        self.notify.debug('self.scores=%s' % self.scores)

    def setCurHoleIndex(self, holeIndex):
        self.curHoleIndex = holeIndex

    def setCurHoleDoId(self, holeDoId):
        self.curHoleDoId = holeDoId

    def getCurGolfer(self):
        if self.curHoleDoId != 0:
            av = base.cr.doId2do.get(self.curHoleDoId)
            if av:
                return av.currentGolfer
        else:
            return None
        return None

    def getStrokesForCurHole(self, avId):
        retval = 0
        if avId in self.scores:
            retval = self.scores[avId][self.curHoleIndex]
        return retval

    def isGameDone(self):
        retval = False
        self.notify.debug('Self state is: %s' % self.state)
        if self.getCurrentOrNextState() == 'WaitReward' or self.getCurrentOrNextState() == 'WaitFinishCourse':
            retval = True
        return retval

    def setReward(self, trophiesList, rankingsList, holeBestList, courseBestList, cupList, tieBreakWinner, aim0, aim1, aim2, aim3):
        self.trophiesList = trophiesList
        self.rankingsList = rankingsList
        self.holeBestList = holeBestList
        self.courseBestList = courseBestList
        self.cupList = cupList
        self.tieBreakWinner = tieBreakWinner
        self.aimTimesList = [aim0,
         aim1,
         aim2,
         aim3]
        if self.state not in ['Cleanup']:
            self.demand('WaitReward')

    def enterWaitReward(self):
        self.scoreBoard.showBoardFinal()
        if self.curHoleDoId != 0:
            av = base.cr.doId2do.get(self.curHoleDoId)
        av.cleanupPowerBar()

        def doneWithRewardMovie():
            if self.exit == False:
                self.notify.debug('doneWithRewardMovie')
                self.sendUpdate('setDoneReward', [])
                self._destroyDelayDelete()
                self.exit = True

        self.golfRewardDialog = GolfRewardDialog.GolfRewardDialog(self.avIdList, self.trophiesList, self.rankingsList, self.holeBestList, self.courseBestList, self.cupList, self.localAvId, self.tieBreakWinner, self.aimTimesList)
        self.rewardIval = Sequence(Parallel(Wait(5), self.golfRewardDialog.getMovie()), Func(doneWithRewardMovie))
        self.rewardIval.start()

    def exitEarly(self):
        if self.exit == False:
            self.notify.debug('doneWithRewardMovie')
            self.sendUpdate('setDoneReward', [])
            self._destroyDelayDelete()
            self.exit = True

    def exitReward(self):
        self.cleanUpReward()

    def cleanUpReward(self):
        if self.rewardIval:
            self.rewardIval.pause()
            self.rewardIval = None
        return

    def updateScoreBoard(self):
        if self.scoreBoard:
            self.scoreBoard.update()

    def changeDrivePermission(self, avId, canDrive):
        if canDrive:
            if avId not in self.drivingToons:
                self.drivingToons.append(avId)
        elif avId in self.drivingToons:
            self.drivingToons.remove(avId)

    def canDrive(self, avId):
        retval = avId in self.drivingToons
        return retval
