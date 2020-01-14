from pandac.PandaModules import *
from toontown.toonbase.ToonBaseGlobal import *
from direct.interval.IntervalGlobal import *
from direct.task import Task
from direct.directnotify import DirectNotifyGlobal
from math import *
from direct.distributed.ClockDelta import *
from toontown.golf import GolfGlobals
from toontown.shtiker.GolfPage import GolfTrophy

class GolfRewardDialog:
    notify = directNotify.newCategory('GolfRewardDialog')

    def __init__(self, avIdList, trophyList, rankingsList, holeBestList, courseBestList, cupList, localAvId, tieBreakWinner, aimTimesList, endMovieCallback = None):
        self.avIdList = avIdList
        self.trophyList = trophyList
        self.rankingsList = rankingsList
        self.holeBestList = holeBestList
        self.courseBestList = courseBestList
        self.cupList = cupList
        self.tieBreakWinner = tieBreakWinner
        self.movie = None
        self.myPlace = 0
        self.victory = None
        self.endMovieCallback = endMovieCallback
        self.aimTimesList = aimTimesList
        self.setup(localAvId)
        return

    def calcTrophyTextListForOnePlayer(self, avId):
        retval = []
        av = base.cr.doId2do.get(avId)
        if av and avId in self.avIdList:
            playerIndex = self.avIdList.index(avId)
            name = av.getName()
            for trophyIndex in range(len(self.trophyList[playerIndex])):
                wonTrophy = self.trophyList[playerIndex][trophyIndex]
                if wonTrophy:
                    trophyName = TTLocalizer.GolfTrophyDescriptions[trophyIndex]
                    text = TTLocalizer.GolfAvReceivesTrophy % {'name': name,
                     'award': trophyName}
                    retval.append(text)

        return retval

    def calcCupTextListForAllPlayers(self, localAvId):
        retval = []
        for cupPlayerIndex in range(len(self.avIdList)):
            if self.avIdList[cupPlayerIndex] != localAvId:
                av = base.cr.doId2do.get(self.avIdList[cupPlayerIndex])
                name = ''
                if av:
                    name = av.getName()
                cupIndex = 0
                for cupIndex in range(len(self.cupList[cupPlayerIndex])):
                    if self.cupList[cupPlayerIndex][cupIndex]:
                        cupName = TTLocalizer.GolfCupDescriptions[cupIndex]
                        text = TTLocalizer.GolfAvReceivesCup % {'name': name,
                         'cup': cupName}
                        retval.append(text)

        for cupPlayerIndex in range(len(self.avIdList)):
            if self.avIdList[cupPlayerIndex] == localAvId:
                av = base.cr.doId2do.get(self.avIdList[cupPlayerIndex])
                name = av.getName()
                cupIndex = 0
                for cupIndex in range(len(self.cupList[cupPlayerIndex])):
                    if self.cupList[cupPlayerIndex][cupIndex]:
                        cupName = TTLocalizer.GolfCupDescriptions[cupIndex]
                        text = TTLocalizer.GolfAvReceivesCup % {'name': name,
                         'cup': cupName}
                        retval.append(text)

        return retval

    def calcRankings(self, localAvId):
        retval = []
        self.notify.debug('aimTimesList=%s' % self.aimTimesList)
        for rank in range(len(self.rankingsList) + 1):
            for avIndex in range(len(self.avIdList)):
                if self.rankingsList[avIndex] == rank:
                    name = ' '
                    av = base.cr.doId2do.get(self.avIdList[avIndex])
                    if av:
                        name = av.getName()
                    text = '%d. ' % rank + ' ' + name
                    if GolfGlobals.TIME_TIE_BREAKER:
                        time = self.aimTimesList[avIndex]
                        minutes = int(time / 60)
                        time -= minutes * 60
                        seconds = int(time)
                        padding = (seconds < 10 and ['0'] or [''])[0]
                        time -= seconds
                        fraction = str(time)[2:4]
                        fraction = fraction + '0' * (2 - len(fraction))
                        timeStr = "%d'%s%d''%s" % (minutes,
                            padding,
                            seconds,
                            fraction)
                        text += ' - ' + timeStr
                    retval.append(text)
                    if self.avIdList[avIndex] == localAvId:
                        self.myPlace = rank

        return retval

    def calcHoleBestTextListForAllPlayers(self, localAvId):
        retval = []
        if GolfGlobals.CalcOtherHoleBest:
            for hbPlayerIndex in range(len(self.avIdList)):
                if self.avIdList[hbPlayerIndex] != localAvId:
                    av = base.cr.doId2do.get(self.avIdList[hbPlayerIndex])
                    name = av.getName()
                    for hbIndex in range(len(self.holeBestList[hbPlayerIndex])):
                        if self.holeBestList[hbPlayerIndex][hbIndex]:
                            hbName = TTLocalizer.GolfHoleNames[hbIndex]
                            text = TTLocalizer.GolfAvReceivesHoleBest % {'name': name,
                             'hole': hbName}
                            retval.append(text)

        for hbPlayerIndex in range(len(self.avIdList)):
            if self.avIdList[hbPlayerIndex] == localAvId:
                av = base.cr.doId2do.get(self.avIdList[hbPlayerIndex])
                name = av.getName()
                for hbIndex in range(len(self.holeBestList[hbPlayerIndex])):
                    if self.holeBestList[hbPlayerIndex][hbIndex]:
                        hbName = TTLocalizer.GolfHoleNames[hbIndex]
                        text = TTLocalizer.GolfAvReceivesHoleBest % {'name': name,
                         'hole': hbName}
                        retval.append(text)

        return retval

    def calcCourseBestTextListForAllPlayers(self, localAvId):
        retval = []
        if GolfGlobals.CalcOtherCourseBest:
            for cbPlayerIndex in range(len(self.avIdList)):
                if self.avIdList[cbPlayerIndex] != localAvId:
                    av = base.cr.doId2do.get(self.avIdList[cbPlayerIndex])
                    name = av.getName()
                    for cbIndex in range(len(self.holeBestList[cbPlayerIndex])):
                        if self.holeBestList[cbPlayerIndex][cbIndex]:
                            cbName = TTLocalizer.GolfCourseNames[cbIndex]
                            text = TTLocalizer.GolfAvReceivesCourseBest % {'name': name,
                             'course': cbName}
                            retval.append(text)

        for cbPlayerIndex in range(len(self.avIdList)):
            if self.avIdList[cbPlayerIndex] == localAvId:
                av = base.cr.doId2do.get(self.avIdList[cbPlayerIndex])
                name = av.getName()
                for cbIndex in range(len(self.courseBestList[cbPlayerIndex])):
                    if self.courseBestList[cbPlayerIndex][cbIndex]:
                        cbName = TTLocalizer.GolfCourseNames[cbIndex]
                        text = TTLocalizer.GolfAvReceivesCourseBest % {'name': name,
                         'course': cbName}
                        retval.append(text)

        return retval

    def createRewardMovie(self, localAvId):
        retval = Sequence(name='Reward sequence', autoPause=1)
        self.trophy = None

        def setTrophyLabelText(text, playerIndex, trophyIndex):
            self.rankLabel.hide()
            self.rewardLabel.hide()
            self.trophy = GolfTrophy(level=self.trophyList[playerIndex][trophyIndex], parent=self.trophyLabel, pos=(1.3, 0, -0.25))
            self.trophy.setScale(0.65, 1, 0.65)
            self.trophy.show()
            self.trophyLabel['text'] = text

        def setRewardLabelText(text):
            self.rewardLabel.show()
            self.rankLabel.hide()
            self.trophyLabel.hide()
            if self.trophy:
                self.trophy.hide()
            self.rewardLabel['text'] = text

        def setRankLabelText(text):
            self.rankLabel.show()
            self.rewardLabel.hide()
            self.trophyLabel.hide()
            if self.trophy:
                self.trophy.hide()
            self.rankLabel['text'] = text
            if len(self.avIdList) > 1:
                self.victory = base.loader.loadSfx('phase_6/audio/sfx/KART_Applause_%d.ogg' % self.myPlace)
                self.victory.play()

        for avId in self.avIdList:
            if avId != localAvId:
                rewardTextList = self.calcTrophyTextListForOnePlayer(avId)
                trophyIndex = 0
                for rewardText in rewardTextList:
                    playerIndex = self.avIdList.index(avId)
                    var = (rewardText, playerIndex, trophyIndex)
                    oneTrophyIval = Parallel(Func(setTrophyLabelText, rewardText, playerIndex, trophyIndex), LerpColorScaleInterval(self.trophyLabel, 4, Vec4(1, 1, 1, 0), startColorScale=Vec4(1, 1, 1, 1), blendType='easeIn'))
                    trophyIndex = trophyIndex + 1
                    retval.append(oneTrophyIval)

        rewardTextList = self.calcTrophyTextListForOnePlayer(localAvId)
        trophyIndex = 0
        playerIndex = self.avIdList.index(localAvId)
        for rewardText in rewardTextList:
            if len(rewardTextList) > 0:
                var = (rewardText, playerIndex, trophyIndex)
                oneRewardIval = Parallel(Func(setTrophyLabelText, rewardText, playerIndex, trophyIndex), LerpColorScaleInterval(self.trophyLabel, 4, Vec4(1, 1, 1, 0), startColorScale=Vec4(1, 1, 1, 1), blendType='easeIn'))
                retval.append(oneRewardIval)

        rewardCupList = self.calcCupTextListForAllPlayers(localAvId)
        if len(rewardCupList) > 0:
            for rewardText in rewardCupList:
                oneCupIval = Parallel(Func(setRewardLabelText, rewardText), LerpColorScaleInterval(self.rewardLabel, 4, Vec4(1, 1, 1, 0), startColorScale=Vec4(1, 1, 1, 1), blendType='noBlend'))
                retval.append(oneCupIval)

        if self.tieBreakWinner:
            name = ''
            av = base.cr.doId2do.get(self.tieBreakWinner)
            if av:
                name = av.getName()
                if GolfGlobals.TIME_TIE_BREAKER:
                    rewardText = TTLocalizer.GolfTimeTieBreakWinner % {'name': name}
                else:
                    rewardText = TTLocalizer.GolfTieBreakWinner % {'name': name}
                randomWinnerIval = Parallel(Func(setRewardLabelText, rewardText), LerpColorScaleInterval(self.rewardLabel, 7, Vec4(1, 1, 1, 0), startColorScale=Vec4(1, 1, 1, 1), blendType='noBlend'))
                retval.append(randomWinnerIval)
        rankings = self.calcRankings(localAvId)
        rankText = TTLocalizer.GolfRanking + '\n'
        for rank in range(len(rankings)):
            rankText = rankText + rankings[rank] + '\n'

        oneRankIval = Parallel(Func(setRankLabelText, rankText), LerpColorScaleInterval(self.rankLabel, 8, Vec4(1, 1, 1, 1), startColorScale=Vec4(1, 1, 1, 1), blendType='easeIn'))
        retval.append(oneRankIval)
        rewardHoleList = self.calcHoleBestTextListForAllPlayers(localAvId)
        if len(rewardHoleList) > 0:
            for rewardText in rewardHoleList:
                oneHoleIval = Parallel(Func(setRewardLabelText, rewardText), LerpColorScaleInterval(self.rewardLabel, 8, Vec4(1, 1, 1, 0), startColorScale=Vec4(1, 1, 1, 1), blendType='easeIn'))
                retval.append(oneHoleIval)

        rewardCourseList = self.calcCourseBestTextListForAllPlayers(localAvId)
        if len(rewardCourseList) > 0:
            for rewardText in rewardCourseList:
                oneCourseIval = Parallel(Func(setRewardLabelText, rewardText), LerpColorScaleInterval(self.rewardLabel, 4, Vec4(1, 1, 1, 0), startColorScale=Vec4(1, 1, 1, 1), blendType='easeIn'))
                retval.append(oneCourseIval)

        if self.endMovieCallback:
            retval.append(Func(self.endMovieCallback))
        return retval

    def setup(self, localAvId):
        self.rewardBoard = DirectFrame(parent=aspect2d, relief=None, geom=DGG.getDefaultDialogGeom(), geom_color=ToontownGlobals.GlobalDialogColor, geom_scale=(1.75, 1, 0.6), pos=(0, 0, -0.6))
        self.rewardLabel = DirectLabel(parent=self.rewardBoard, relief=None, pos=(-0, 0, 0), text_align=TextNode.ACenter, text='', text_scale=0.05, text_wordwrap=30)
        self.rankLabel = DirectLabel(parent=self.rewardBoard, relief=None, pos=(-0, 0, 0.17), text_align=TextNode.ACenter, text='', text_scale=0.06)
        self.trophyLabel = DirectLabel(parent=self.rewardBoard, relief=None, pos=(-0.7, 0, 0.05), text_align=TextNode.ALeft, text='', text_scale=0.06, text_wordwrap=20)
        self.movie = self.createRewardMovie(localAvId)
        return

    def delete(self):
        self.movie.pause()
        self.notify.debug('Movie is paused')
        self.rewardBoard.destroy()
        self.notify.debug('Reward board is destroyed')
        self.movie = None
        self.notify.debug('Movie is deleted')
        return

    def getMovie(self):
        return self.movie
