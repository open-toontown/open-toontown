from pandac.PandaModules import *
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from toontown.toonbase import ToontownBattleGlobals
from . import BattleBase
from direct.directnotify import DirectNotifyGlobal
import random
import string
from toontown.quest import Quests
import copy
from toontown.suit import SuitDNA
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.toon import NPCToons
import math
from toontown.coghq import CogDisguiseGlobals
from toontown.shtiker import DisguisePage
from . import Fanfare
from otp.otpbase import OTPGlobals

class RewardPanel(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('RewardPanel')
    SkipBattleMovieEvent = 'skip-battle-movie-event'

    def __init__(self, name):
        gscale = (TTLocalizer.RPdirectFrame[0], TTLocalizer.RPdirectFrame[1], TTLocalizer.RPdirectFrame[2] * 1.1)
        DirectFrame.__init__(self, relief=None, geom=DGG.getDefaultDialogGeom(), geom_color=ToontownGlobals.GlobalDialogColor, geom_pos=Point3(0, 0, -.05), geom_scale=gscale, pos=(0, 0, 0.587))
        self.initialiseoptions(RewardPanel)
        self.avNameLabel = DirectLabel(parent=self, relief=None, pos=(0, 0, 0.3), text=name, text_scale=0.08)
        self.gagExpFrame = DirectFrame(parent=self, relief=None, pos=(-0.32, 0, 0.24))
        self.itemFrame = DirectFrame(parent=self, relief=None, text=TTLocalizer.RewardPanelItems, text_pos=(0, 0.2), text_scale=0.08)
        self.cogPartFrame = DirectFrame(parent=self, relief=None, text=TTLocalizer.RewardPanelCogPart, text_pos=(0, 0.2), text_scale=0.08)
        self.missedItemFrame = DirectFrame(parent=self, relief=None, text=TTLocalizer.RewardPanelMissedItems, text_pos=(0, 0.2), text_scale=0.08)
        self.itemLabel = DirectLabel(parent=self.itemFrame, text='', text_scale=0.06)
        self.cogPartLabel = DirectLabel(parent=self.cogPartFrame, text='', text_scale=0.06)
        self.missedItemLabel = DirectLabel(parent=self.missedItemFrame, text='', text_scale=0.06)
        self.questFrame = DirectFrame(parent=self, relief=None, text=TTLocalizer.RewardPanelToonTasks, text_pos=(0, 0.2), text_scale=0.06)
        self.questLabelList = []
        for i in range(ToontownGlobals.MaxQuestCarryLimit):
            label = DirectLabel(parent=self.questFrame, relief=None, pos=(-0.85, 0, -0.1 * i), text=TTLocalizer.RewardPanelQuestLabel % i, text_scale=0.05, text_align=TextNode.ALeft)
            label.hide()
            self.questLabelList.append(label)

        self.newGagFrame = DirectFrame(parent=self, relief=None, pos=(0, 0, 0.24), text='', text_wordwrap=14.4, text_pos=(0, -0.46), text_scale=0.06)
        self.endTrackFrame = DirectFrame(parent=self, relief=None, pos=(0, 0, 0.24), text='', text_wordwrap=14.4, text_pos=(0, -0.46), text_scale=0.06)
        self.congratsLeft = DirectLabel(parent=self.newGagFrame, pos=(-0.2, 0, -0.1), text='', text_pos=(0, 0), text_scale=0.06)
        self.congratsLeft.setHpr(0, 0, -30)
        self.congratsRight = DirectLabel(parent=self.newGagFrame, pos=(0.2, 0, -0.1), text='', text_pos=(0, 0), text_scale=0.06)
        self.congratsRight.setHpr(0, 0, 30)
        self.promotionFrame = DirectFrame(parent=self, relief=None, pos=(0, 0, 0.24), text='', text_wordwrap=14.4, text_pos=(0, -0.46), text_scale=0.06)
        self.trackLabels = []
        self.trackIncLabels = []
        self.trackBars = []
        self.trackBarsOffset = 0
        self.meritLabels = []
        self.meritIncLabels = []
        self.meritBars = []
        for i in range(len(SuitDNA.suitDepts)):
            deptName = TextEncoder.upper(SuitDNA.suitDeptFullnames[SuitDNA.suitDepts[i]])
            self.meritLabels.append(DirectLabel(parent=self.gagExpFrame, relief=None, text=deptName, text_scale=0.05, text_align=TextNode.ARight, pos=(TTLocalizer.RPmeritLabelPosX, 0, -0.09 * i - 0.125), text_pos=(0, -0.02)))
            self.meritIncLabels.append(DirectLabel(parent=self.gagExpFrame, relief=None, text='', text_scale=0.05, text_align=TextNode.ALeft, pos=(0.7, 0, -0.09 * i - 0.125), text_pos=(0, -0.02)))
            self.meritBars.append(DirectWaitBar(parent=self.gagExpFrame, relief=DGG.SUNKEN, frameSize=(-1,
             1,
             -0.15,
             0.15), borderWidth=(0.02, 0.02), scale=0.25, frameColor=(DisguisePage.DeptColors[i][0] * 0.7,
             DisguisePage.DeptColors[i][1] * 0.7,
             DisguisePage.DeptColors[i][2] * 0.7,
             1), barColor=(DisguisePage.DeptColors[i][0],
             DisguisePage.DeptColors[i][1],
             DisguisePage.DeptColors[i][2],
             1), text='0/0 ' + TTLocalizer.RewardPanelMeritBarLabels[i], text_scale=TTLocalizer.RPmeritBarLabels, text_fg=(0, 0, 0, 1), text_align=TextNode.ALeft, text_pos=(-0.96, -0.05), pos=(TTLocalizer.RPmeritBarsPosX, 0, -0.09 * i - 0.125)))

        for i in range(len(ToontownBattleGlobals.Tracks)):
            trackName = TextEncoder.upper(ToontownBattleGlobals.Tracks[i])
            self.trackLabels.append(DirectLabel(parent=self.gagExpFrame, relief=None, text=trackName, text_scale=TTLocalizer.RPtrackLabels, text_align=TextNode.ARight, pos=(0.13, 0, -0.09 * i), text_pos=(0, -0.02)))
            self.trackIncLabels.append(DirectLabel(parent=self.gagExpFrame, relief=None, text='', text_scale=0.05, text_align=TextNode.ALeft, pos=(0.65, 0, -0.09 * i), text_pos=(0, -0.02)))
            self.trackBars.append(DirectWaitBar(parent=self.gagExpFrame, relief=DGG.SUNKEN, frameSize=(-1,
             1,
             -0.15,
             0.15), borderWidth=(0.02, 0.02), scale=0.25, frameColor=(ToontownBattleGlobals.TrackColors[i][0] * 0.7,
             ToontownBattleGlobals.TrackColors[i][1] * 0.7,
             ToontownBattleGlobals.TrackColors[i][2] * 0.7,
             1), barColor=(ToontownBattleGlobals.TrackColors[i][0],
             ToontownBattleGlobals.TrackColors[i][1],
             ToontownBattleGlobals.TrackColors[i][2],
             1), text='0/0', text_scale=0.18, text_fg=(0, 0, 0, 1), text_align=TextNode.ACenter, text_pos=(0, -0.05), pos=(0.4, 0, -0.09 * i)))

        self._battleGui = loader.loadModel('phase_3.5/models/gui/battle_gui')
        self.skipButton = DirectButton(parent=self, relief=None, image=(self._battleGui.find('**/tt_t_gui_gen_skipSectionUp'),
         self._battleGui.find('**/tt_t_gui_gen_skipSectionDown'),
         self._battleGui.find('**/tt_t_gui_gen_skipSectionRollOver'),
         self._battleGui.find('**/tt_t_gui_gen_skipSectionDisabled')), pos=(0.815, 0, -0.395), scale=(0.39, 1.0, 0.39), text=('',
         TTLocalizer.RewardPanelSkip,
         TTLocalizer.RewardPanelSkip,
         ''), text_scale=TTLocalizer.RPskipScale, text_fg=Vec4(1, 1, 1, 1), text_shadow=Vec4(0, 0, 0, 1), text_pos=TTLocalizer.RPskipPos, textMayChange=0, command=self._handleSkip)
        return

    def getNextExpValue(self, curSkill, trackIndex):
        retVal = ToontownBattleGlobals.UberSkill
        for amount in ToontownBattleGlobals.Levels[trackIndex]:
            if curSkill < amount:
                retVal = amount
                return retVal

        return retVal

    def getNextExpValueUber(self, curSkill, trackIndex):
        return ToontownBattleGlobals.UberSkill

    def getNextMeritValue(self, curMerits, toon, dept):
        totalMerits = CogDisguiseGlobals.getTotalMerits(toon, dept)
        retVal = totalMerits
        if curMerits > totalMerits:
            retVal = amount
        return retVal

    def initItemFrame(self, toon):
        self.endTrackFrame.hide()
        self.gagExpFrame.hide()
        self.newGagFrame.hide()
        self.promotionFrame.hide()
        self.questFrame.hide()
        self.itemFrame.show()
        self.cogPartFrame.hide()
        self.missedItemFrame.hide()

    def initMissedItemFrame(self, toon):
        self.endTrackFrame.hide()
        self.gagExpFrame.hide()
        self.newGagFrame.hide()
        self.promotionFrame.hide()
        self.questFrame.hide()
        self.itemFrame.hide()
        self.cogPartFrame.hide()
        self.missedItemFrame.show()

    def initCogPartFrame(self, toon):
        self.endTrackFrame.hide()
        self.gagExpFrame.hide()
        self.newGagFrame.hide()
        self.promotionFrame.hide()
        self.questFrame.hide()
        self.itemFrame.hide()
        self.cogPartFrame.show()
        self.cogPartLabel['text'] = ''
        self.missedItemFrame.hide()

    def initQuestFrame(self, toon, avQuests):
        self.endTrackFrame.hide()
        self.gagExpFrame.hide()
        self.newGagFrame.hide()
        self.promotionFrame.hide()
        self.questFrame.show()
        self.itemFrame.hide()
        self.cogPartFrame.hide()
        self.missedItemFrame.hide()
        for i in range(ToontownGlobals.MaxQuestCarryLimit):
            questLabel = self.questLabelList[i]
            questLabel['text_fg'] = (0, 0, 0, 1)
            questLabel.hide()

        for i in range(len(avQuests)):
            questDesc = avQuests[i]
            questId, npcId, toNpcId, rewardId, toonProgress = questDesc
            quest = Quests.getQuest(questId)
            if quest:
                questString = quest.getString()
                progressString = quest.getProgressString(toon, questDesc)
                rewardString = quest.getRewardString(progressString)
                rewardString = Quests.fillInQuestNames(rewardString, toNpcId=toNpcId)
                completed = quest.getCompletionStatus(toon, questDesc) == Quests.COMPLETE
                questLabel = self.questLabelList[i]
                questLabel.show()
                if base.localAvatar.tutorialAck:
                    questLabel['text'] = rewardString
                    if completed:
                        questLabel['text_fg'] = (0, 0.3, 0, 1)
                else:
                    questLabel['text'] = questString + ' :'

    def initGagFrame(self, toon, expList, meritList, noSkip = False):
        self.avNameLabel['text'] = toon.getName()
        self.endTrackFrame.hide()
        self.gagExpFrame.show()
        self.newGagFrame.hide()
        self.promotionFrame.hide()
        self.questFrame.hide()
        self.itemFrame.hide()
        self.cogPartFrame.hide()
        self.missedItemFrame.hide()
        trackBarOffset = 0
        self.skipButton['state'] = choice(noSkip, DGG.DISABLED, DGG.NORMAL)
        for i in range(len(SuitDNA.suitDepts)):
            meritBar = self.meritBars[i]
            meritLabel = self.meritLabels[i]
            totalMerits = CogDisguiseGlobals.getTotalMerits(toon, i)
            merits = meritList[i]
            self.meritIncLabels[i].hide()
            if CogDisguiseGlobals.isSuitComplete(toon.cogParts, i):
                if not self.trackBarsOffset:
                    trackBarOffset = 0.47
                    self.trackBarsOffset = 1
                meritBar.show()
                meritLabel.show()
                meritLabel.show()
                if totalMerits:
                    meritBar['range'] = totalMerits
                    meritBar['value'] = merits
                    if merits == totalMerits:
                        meritBar['text'] = TTLocalizer.RewardPanelMeritAlert
                    else:
                        meritBar['text'] = '%s/%s %s' % (merits, totalMerits, TTLocalizer.RewardPanelMeritBarLabels[i])
                else:
                    meritBar['range'] = 1
                    meritBar['value'] = 1
                    meritBar['text'] = TTLocalizer.RewardPanelMeritsMaxed
                self.resetMeritBarColor(i)
            else:
                meritBar.hide()
                meritLabel.hide()

        for i in range(len(expList)):
            curExp = expList[i]
            trackBar = self.trackBars[i]
            trackLabel = self.trackLabels[i]
            trackIncLabel = self.trackIncLabels[i]
            trackBar.setX(trackBar.getX() - trackBarOffset)
            trackLabel.setX(trackLabel.getX() - trackBarOffset)
            trackIncLabel.setX(trackIncLabel.getX() - trackBarOffset)
            trackIncLabel.hide()
            if toon.hasTrackAccess(i):
                trackBar.show()
                if curExp >= ToontownBattleGlobals.UnpaidMaxSkills[i] and toon.getGameAccess() != OTPGlobals.AccessFull:
                    nextExp = self.getNextExpValue(curExp, i)
                    trackBar['range'] = nextExp
                    trackBar['value'] = ToontownBattleGlobals.UnpaidMaxSkills[i]
                    trackBar['text'] = TTLocalizer.InventoryGuestExp
                elif curExp >= ToontownBattleGlobals.regMaxSkill:
                    nextExp = self.getNextExpValueUber(curExp, i)
                    trackBar['range'] = nextExp
                    uberCurrExp = curExp - ToontownBattleGlobals.regMaxSkill
                    trackBar['value'] = uberCurrExp
                    trackBar['text'] = TTLocalizer.InventoryUberTrackExp % {'nextExp': ToontownBattleGlobals.MaxSkill - curExp}
                else:
                    nextExp = self.getNextExpValue(curExp, i)
                    trackBar['range'] = nextExp
                    trackBar['value'] = curExp
                    trackBar['text'] = '%s/%s' % (curExp, nextExp)
                self.resetBarColor(i)
            else:
                trackBar.hide()

    def incrementExp(self, track, newValue, toon):
        trackBar = self.trackBars[track]
        oldValue = trackBar['value']
        newValue = min(ToontownBattleGlobals.MaxSkill, newValue)
        nextExp = self.getNextExpValue(newValue, track)
        if newValue >= ToontownBattleGlobals.UnpaidMaxSkills[track] and toon.getGameAccess() != OTPGlobals.AccessFull:
            newValue = oldValue
            trackBar['text'] = TTLocalizer.GuestLostExp
        elif newValue >= ToontownBattleGlobals.regMaxSkill:
            newValue = newValue - ToontownBattleGlobals.regMaxSkill
            nextExp = self.getNextExpValueUber(newValue, track)
            trackBar['text'] = TTLocalizer.InventoryUberTrackExp % {'nextExp': ToontownBattleGlobals.UberSkill - newValue}
        else:
            trackBar['text'] = '%s/%s' % (newValue, nextExp)
        trackBar['range'] = nextExp
        trackBar['value'] = newValue
        trackBar['barColor'] = (ToontownBattleGlobals.TrackColors[track][0],
         ToontownBattleGlobals.TrackColors[track][1],
         ToontownBattleGlobals.TrackColors[track][2],
         1)

    def resetBarColor(self, track):
        self.trackBars[track]['barColor'] = (ToontownBattleGlobals.TrackColors[track][0] * 0.8,
         ToontownBattleGlobals.TrackColors[track][1] * 0.8,
         ToontownBattleGlobals.TrackColors[track][2] * 0.8,
         1)

    def incrementMerits(self, toon, dept, newValue, totalMerits):
        meritBar = self.meritBars[dept]
        oldValue = meritBar['value']
        if totalMerits:
            newValue = min(totalMerits, newValue)
            meritBar['range'] = totalMerits
            meritBar['value'] = newValue
            if newValue == totalMerits:
                meritBar['text'] = TTLocalizer.RewardPanelMeritAlert
                meritBar['barColor'] = (DisguisePage.DeptColors[dept][0],
                 DisguisePage.DeptColors[dept][1],
                 DisguisePage.DeptColors[dept][2],
                 1)
            else:
                meritBar['text'] = '%s/%s %s' % (newValue, totalMerits, TTLocalizer.RewardPanelMeritBarLabels[dept])

    def resetMeritBarColor(self, dept):
        self.meritBars[dept]['barColor'] = (DisguisePage.DeptColors[dept][0] * 0.8,
         DisguisePage.DeptColors[dept][1] * 0.8,
         DisguisePage.DeptColors[dept][2] * 0.8,
         1)

    def getRandomCongratsPair(self, toon):
        congratsStrings = TTLocalizer.RewardPanelCongratsStrings
        numStrings = len(congratsStrings)
        indexList = list(range(numStrings))
        index1 = random.choice(indexList)
        indexList.remove(index1)
        index2 = random.choice(indexList)
        string1 = congratsStrings[index1]
        string2 = congratsStrings[index2]
        return (string1, string2)

    def uberGagInterval(self, toon, track, level):
        self.endTrackFrame.hide()
        self.gagExpFrame.hide()
        self.newGagFrame.show()
        self.promotionFrame.hide()
        self.questFrame.hide()
        self.itemFrame.hide()
        self.missedItemFrame.hide()
        self.newGagFrame['text'] = TTLocalizer.RewardPanelUberGag % {'gagName': ToontownBattleGlobals.Tracks[track].capitalize(),
         'exp': str(ToontownBattleGlobals.UberSkill),
         'avName': toon.getName()}
        self.congratsLeft['text'] = ''
        self.congratsRight['text'] = ''
        gagOriginal = base.localAvatar.inventory.buttonLookup(track, level)
        self.newGagIcon = gagOriginal.copyTo(self.newGagFrame)
        self.newGagIcon.setPos(0, 0, -0.25)
        self.newGagIcon.setScale(1.5)

    def newGag(self, toon, track, level):
        self.endTrackFrame.hide()
        self.gagExpFrame.hide()
        self.newGagFrame.show()
        self.promotionFrame.hide()
        self.questFrame.hide()
        self.itemFrame.hide()
        self.missedItemFrame.hide()
        self.newGagFrame['text'] = TTLocalizer.RewardPanelNewGag % {'gagName': ToontownBattleGlobals.Tracks[track].capitalize(),
         'avName': toon.getName()}
        self.congratsLeft['text'] = ''
        self.congratsRight['text'] = ''
        gagOriginal = base.localAvatar.inventory.buttonLookup(track, level)
        self.newGagIcon = gagOriginal.copyTo(self.newGagFrame)
        self.newGagIcon.setPos(0, 0, -0.25)
        self.newGagIcon.setScale(1.5)

    def cleanupNewGag(self):
        self.endTrackFrame.hide()
        if self.newGagIcon:
            self.newGagIcon.removeNode()
            self.newGagIcon = None
        self.gagExpFrame.show()
        self.newGagFrame.hide()
        self.promotionFrame.hide()
        self.questFrame.hide()
        self.itemFrame.hide()
        self.missedItemFrame.hide()
        return

    def getNewGagIntervalList(self, toon, track, level):
        leftCongratsAnticipate = 1.0
        rightCongratsAnticipate = 1.0
        finalDelay = 1.5
        leftString, rightString = self.getRandomCongratsPair(toon)
        intervalList = [Func(self.newGag, toon, track, level),
         Wait(leftCongratsAnticipate),
         Func(self.congratsLeft.setProp, 'text', leftString),
         Wait(rightCongratsAnticipate),
         Func(self.congratsRight.setProp, 'text', rightString),
         Wait(finalDelay),
         Func(self.cleanupNewGag)]
        return intervalList

    def getUberGagIntervalList(self, toon, track, level):
        leftCongratsAnticipate = 1.0
        rightCongratsAnticipate = 1.0
        finalDelay = 1.5
        leftString, rightString = self.getRandomCongratsPair(toon)
        intervalList = [Func(self.uberGagInterval, toon, track, level),
         Wait(leftCongratsAnticipate),
         Func(self.congratsLeft.setProp, 'text', leftString),
         Wait(rightCongratsAnticipate),
         Func(self.congratsRight.setProp, 'text', rightString),
         Wait(finalDelay),
         Func(self.cleanupNewGag)]
        return intervalList

    def vanishFrames(self):
        self.hide()
        self.endTrackFrame.hide()
        self.gagExpFrame.hide()
        self.newGagFrame.hide()
        self.promotionFrame.hide()
        self.questFrame.hide()
        self.itemFrame.hide()
        self.missedItemFrame.hide()
        self.cogPartFrame.hide()
        self.missedItemFrame.hide()

    def endTrack(self, toon, toonList, track):
        for t in toonList:
            if t == base.localAvatar:
                self.show()

        self.endTrackFrame.show()
        self.endTrackFrame['text'] = TTLocalizer.RewardPanelEndTrack % {'gagName': ToontownBattleGlobals.Tracks[track].capitalize(),
         'avName': toon.getName()}
        gagLast = base.localAvatar.inventory.buttonLookup(track, ToontownBattleGlobals.UBER_GAG_LEVEL_INDEX)
        self.gagIcon = gagLast.copyTo(self.endTrackFrame)
        self.gagIcon.setPos(0, 0, -0.25)
        self.gagIcon.setScale(1.5)

    def cleanIcon(self):
        self.gagIcon.removeNode()
        self.gagIcon = None
        return

    def cleanupEndTrack(self):
        self.endTrackFrame.hide()
        self.gagExpFrame.show()
        self.newGagFrame.hide()
        self.promotionFrame.hide()
        self.questFrame.hide()
        self.itemFrame.hide()
        self.missedItemFrame.hide()

    def getEndTrackIntervalList(self, toon, toonList, track):
        intervalList = [Func(self.endTrack, toon, toonList, track), Wait(2.0), Func(self.cleanIcon)]
        return intervalList

    def showTrackIncLabel(self, track, earnedSkill, guestWaste = 0):
        if guestWaste:
            self.trackIncLabels[track]['text'] = ''
        elif earnedSkill > 0:
            self.trackIncLabels[track]['text'] = '+ ' + str(earnedSkill)
        elif earnedSkill < 0:
            self.trackIncLabels[track]['text'] = ' ' + str(earnedSkill)
        self.trackIncLabels[track].show()

    def showMeritIncLabel(self, dept, earnedMerits):
        self.meritIncLabels[dept]['text'] = '+ ' + str(earnedMerits)
        self.meritIncLabels[dept].show()

    def getTrackIntervalList(self, toon, track, origSkill, earnedSkill, hasUber, guestWaste = 0):
        if hasUber < 0:
            print((toon.doId, 'Reward Panel received an invalid hasUber from an uberList'))
        tickDelay = 1.0 / 60
        intervalList = []
        if origSkill + earnedSkill >= ToontownBattleGlobals.UnpaidMaxSkills[track] and toon.getGameAccess() != OTPGlobals.AccessFull:
            lostExp = origSkill + earnedSkill - ToontownBattleGlobals.UnpaidMaxSkills[track]
            intervalList.append(Func(self.showTrackIncLabel, track, lostExp, 1))
        else:
            intervalList.append(Func(self.showTrackIncLabel, track, earnedSkill))
        barTime = 0.5
        numTicks = int(math.ceil(barTime / tickDelay))
        for i in range(numTicks):
            t = (i + 1) / float(numTicks)
            newValue = int(origSkill + t * earnedSkill + 0.5)
            intervalList.append(Func(self.incrementExp, track, newValue, toon))
            intervalList.append(Wait(tickDelay))

        intervalList.append(Func(self.resetBarColor, track))
        intervalList.append(Wait(0.1))
        nextExpValue = self.getNextExpValue(origSkill, track)
        finalGagFlag = 0
        while origSkill + earnedSkill >= nextExpValue and origSkill < nextExpValue and not finalGagFlag:
            if newValue >= ToontownBattleGlobals.UnpaidMaxSkills[track] and toon.getGameAccess() != OTPGlobals.AccessFull:
                pass
            elif nextExpValue != ToontownBattleGlobals.MaxSkill:
                intervalList += self.getNewGagIntervalList(toon, track, ToontownBattleGlobals.Levels[track].index(nextExpValue))
            newNextExpValue = self.getNextExpValue(nextExpValue, track)
            if newNextExpValue == nextExpValue:
                finalGagFlag = 1
            else:
                nextExpValue = newNextExpValue

        uberIndex = ToontownBattleGlobals.LAST_REGULAR_GAG_LEVEL + 1
        currentSkill = origSkill + earnedSkill
        uberSkill = ToontownBattleGlobals.UberSkill + ToontownBattleGlobals.Levels[track][ToontownBattleGlobals.LAST_REGULAR_GAG_LEVEL + 1]
        if currentSkill >= uberSkill and not hasUber > 0:
            intervalList += self.getUberGagIntervalList(toon, track, ToontownBattleGlobals.LAST_REGULAR_GAG_LEVEL + 1)
            intervalList.append(Wait(0.1))
            skillDiff = currentSkill - ToontownBattleGlobals.Levels[track][ToontownBattleGlobals.LAST_REGULAR_GAG_LEVEL + 1]
            barTime = math.log(skillDiff + 1)
            numTicks = int(math.ceil(barTime / tickDelay))
            displayedSkillDiff = skillDiff
            if displayedSkillDiff > ToontownBattleGlobals.UberSkill:
                displayedSkillDiff = ToontownBattleGlobals.UberSkill
            intervalList.append(Func(self.showTrackIncLabel, track, -displayedSkillDiff))
            for i in range(numTicks):
                t = (i + 1) / float(numTicks)
                newValue = int(currentSkill - t * skillDiff + 0.5)
                intervalList.append(Func(self.incrementExp, track, newValue, toon))
                intervalList.append(Wait(tickDelay * 0.5))

            intervalList.append(Wait(0.1))
        return intervalList

    def getMeritIntervalList(self, toon, dept, origMerits, earnedMerits):
        tickDelay = 1.0 / 60
        intervalList = []
        totalMerits = CogDisguiseGlobals.getTotalMerits(toon, dept)
        neededMerits = 0
        if totalMerits and origMerits != totalMerits:
            neededMerits = totalMerits - origMerits
            intervalList.append(Func(self.showMeritIncLabel, dept, min(neededMerits, earnedMerits)))
        barTime = 0.5
        numTicks = int(math.ceil(barTime / tickDelay))
        for i in range(numTicks):
            t = (i + 1) / float(numTicks)
            newValue = int(origMerits + t * earnedMerits + 0.5)
            intervalList.append(Func(self.incrementMerits, toon, dept, newValue, totalMerits))
            intervalList.append(Wait(tickDelay))

        intervalList.append(Func(self.resetMeritBarColor, dept))
        intervalList.append(Wait(0.1))
        if toon.cogLevels[dept] < ToontownGlobals.MaxCogSuitLevel:
            if neededMerits and toon.readyForPromotion(dept):
                intervalList.append(Wait(0.4))
                intervalList += self.getPromotionIntervalList(toon, dept)
        return intervalList

    def promotion(self, toon, dept):
        self.endTrackFrame.hide()
        self.gagExpFrame.hide()
        self.newGagFrame.hide()
        self.promotionFrame.show()
        self.questFrame.hide()
        self.itemFrame.hide()
        self.missedItemFrame.hide()
        name = SuitDNA.suitDepts[dept]
        self.promotionFrame['text'] = TTLocalizer.RewardPanelPromotion % SuitDNA.suitDeptFullnames[name]
        icons = loader.loadModel('phase_3/models/gui/cog_icons')
        if dept == 0:
            self.deptIcon = icons.find('**/CorpIcon').copyTo(self.promotionFrame)
        elif dept == 1:
            self.deptIcon = icons.find('**/LegalIcon').copyTo(self.promotionFrame)
        elif dept == 2:
            self.deptIcon = icons.find('**/MoneyIcon').copyTo(self.promotionFrame)
        elif dept == 3:
            self.deptIcon = icons.find('**/SalesIcon').copyTo(self.promotionFrame)
        icons.removeNode()
        self.deptIcon.setPos(0, 0, -0.225)
        self.deptIcon.setScale(0.33)

    def cleanupPromotion(self):
        if not hasattr(self, 'deptIcon'):
            return
        self.deptIcon.removeNode()
        self.deptIcon = None
        self.endTrackFrame.hide()
        self.gagExpFrame.show()
        self.newGagFrame.hide()
        self.promotionFrame.hide()
        self.questFrame.hide()
        self.itemFrame.hide()
        self.missedItemFrame.hide()
        return

    def getPromotionIntervalList(self, toon, dept):
        finalDelay = 2.0
        intervalList = [Func(self.promotion, toon, dept), Wait(finalDelay), Func(self.cleanupPromotion)]
        return intervalList

    def getQuestIntervalList(self, toon, deathList, toonList, origQuestsList, itemList, helpfulToonsList = []):
        avId = toon.getDoId()
        tickDelay = 0.2
        intervalList = []
        toonShortList = []
        for t in toonList:
            if t is not None:
                toonShortList.append(t)

        cogList = []
        for i in range(0, len(deathList), 4):
            cogIndex = deathList[i]
            cogLevel = deathList[i + 1]
            activeToonBits = deathList[i + 2]
            flags = deathList[i + 3]
            activeToonIds = []
            for j in range(8):
                if activeToonBits & 1 << j:
                    if toonList[j] is not None:
                        activeToonIds.append(toonList[j].getDoId())

            isSkelecog = flags & ToontownBattleGlobals.DLF_SKELECOG
            isForeman = flags & ToontownBattleGlobals.DLF_FOREMAN
            isVP = flags & ToontownBattleGlobals.DLF_VP
            isCFO = flags & ToontownBattleGlobals.DLF_CFO
            isSupervisor = flags & ToontownBattleGlobals.DLF_SUPERVISOR
            isVirtual = flags & ToontownBattleGlobals.DLF_VIRTUAL
            hasRevives = flags & ToontownBattleGlobals.DLF_REVIVES
            if isVP or isCFO:
                cogType = None
                cogTrack = SuitDNA.suitDepts[cogIndex]
            else:
                cogType = SuitDNA.suitHeadTypes[cogIndex]
                cogTrack = SuitDNA.getSuitDept(cogType)
            cogList.append({'type': cogType,
             'level': cogLevel,
             'track': cogTrack,
             'isSkelecog': isSkelecog,
             'isForeman': isForeman,
             'isVP': isVP,
             'isCFO': isCFO,
             'isSupervisor': isSupervisor,
             'isVirtual': isVirtual,
             'hasRevives': hasRevives,
             'activeToons': activeToonIds})

        try:
            zoneId = base.cr.playGame.getPlace().getTaskZoneId()
        except:
            zoneId = 0

        avQuests = []
        for i in range(0, len(origQuestsList), 5):
            avQuests.append(origQuestsList[i:i + 5])

        for i in range(len(avQuests)):
            questDesc = avQuests[i]
            questId, npcId, toNpcId, rewardId, toonProgress = questDesc
            quest = Quests.getQuest(questId)
            if quest and i < len(self.questLabelList):
                questString = quest.getString()
                progressString = quest.getProgressString(toon, questDesc)
                questLabel = self.questLabelList[i]
                earned = 0
                orig = questDesc[4] & pow(2, 16) - 1
                num = 0
                if quest.getType() == Quests.RecoverItemQuest:
                    questItem = quest.getItem()
                    if questItem in itemList:
                        earned = itemList.count(questItem)
                else:
                    for cogDict in cogList:
                        if cogDict['isVP']:
                            num = quest.doesVPCount(avId, cogDict, zoneId, toonShortList)
                        elif cogDict['isCFO']:
                            num = quest.doesCFOCount(avId, cogDict, zoneId, toonShortList)
                        else:
                            num = quest.doesCogCount(avId, cogDict, zoneId, toonShortList)
                        if num:
                            if base.config.GetBool('battle-passing-no-credit', True):
                                if avId in helpfulToonsList:
                                    earned += num
                                else:
                                    self.notify.debug('avId=%d not getting %d kill cog quest credit' % (avId, num))
                            else:
                                earned += num

                if base.localAvatar.tutorialAck:
                    if earned > 0:
                        earned = min(earned, quest.getNumQuestItems() - questDesc[4])
                if earned > 0 or base.localAvatar.tutorialAck == 0 and num == 1:
                    barTime = 0.5
                    numTicks = int(math.ceil(barTime / tickDelay))
                    for i in range(numTicks):
                        t = (i + 1) / float(numTicks)
                        newValue = int(orig + t * earned + 0.5)
                        questDesc[4] = newValue
                        progressString = quest.getProgressString(toon, questDesc)
                        str = '%s : %s' % (questString, progressString)
                        if quest.getCompletionStatus(toon, questDesc) == Quests.COMPLETE:
                            intervalList.append(Func(questLabel.setProp, 'text_fg', (0, 0.3, 0, 1)))
                        intervalList.append(Func(questLabel.setProp, 'text', str))
                        intervalList.append(Wait(tickDelay))

        return intervalList

    def getItemIntervalList(self, toon, itemList):
        intervalList = []
        for itemId in itemList:
            itemName = Quests.getItemName(itemId)
            intervalList.append(Func(self.itemLabel.setProp, 'text', itemName))
            intervalList.append(Wait(1))

        return intervalList

    def getCogPartIntervalList(self, toon, cogPartList):
        itemName = CogDisguiseGlobals.getPartName(cogPartList)
        intervalList = []
        intervalList.append(Func(self.cogPartLabel.setProp, 'text', itemName))
        intervalList.append(Wait(1))
        return intervalList

    def getMissedItemIntervalList(self, toon, missedItemList):
        intervalList = []
        for itemId in missedItemList:
            itemName = Quests.getItemName(itemId)
            intervalList.append(Func(self.missedItemLabel.setProp, 'text', itemName))
            intervalList.append(Wait(1))

        return intervalList

    def getExpTrack(self, toon, origExp, earnedExp, deathList, origQuestsList, itemList, missedItemList, origMeritList, meritList, partList, toonList, uberEntry, helpfulToonsList, noSkip = False):
        track = Sequence(Func(self.initGagFrame, toon, origExp, origMeritList, noSkip=noSkip), Wait(1.0))
        endTracks = [0,
         0,
         0,
         0,
         0,
         0,
         0]
        trackEnded = 0
        for trackIndex in range(len(earnedExp)):
            if earnedExp[trackIndex] > 0 or origExp[trackIndex] >= ToontownBattleGlobals.MaxSkill:
                track += self.getTrackIntervalList(toon, trackIndex, origExp[trackIndex], earnedExp[trackIndex], ToontownBattleGlobals.getUberFlagSafe(uberEntry, trackIndex))
                maxExp = ToontownBattleGlobals.MaxSkill - ToontownBattleGlobals.UberSkill
                if origExp[trackIndex] < maxExp and earnedExp[trackIndex] + origExp[trackIndex] >= maxExp:
                    endTracks[trackIndex] = 1
                    trackEnded = 1

        for dept in range(len(SuitDNA.suitDepts)):
            if meritList[dept]:
                track += self.getMeritIntervalList(toon, dept, origMeritList[dept], meritList[dept])

        track.append(Wait(0.75))
        itemInterval = self.getItemIntervalList(toon, itemList)
        if itemInterval:
            track.append(Func(self.initItemFrame, toon))
            track.append(Wait(0.25))
            track += itemInterval
            track.append(Wait(0.5))
        missedItemInterval = self.getMissedItemIntervalList(toon, missedItemList)
        if missedItemInterval:
            track.append(Func(self.initMissedItemFrame, toon))
            track.append(Wait(0.25))
            track += missedItemInterval
            track.append(Wait(0.5))
        self.notify.debug('partList = %s' % partList)
        newPart = 0
        for part in partList:
            if part != 0:
                newPart = 1
                break

        if newPart:
            partList = self.getCogPartIntervalList(toon, partList)
            if partList:
                track.append(Func(self.initCogPartFrame, toon))
                track.append(Wait(0.25))
                track += partList
                track.append(Wait(0.5))
        questList = self.getQuestIntervalList(toon, deathList, toonList, origQuestsList, itemList, helpfulToonsList)
        if questList:
            avQuests = []
            for i in range(0, len(origQuestsList), 5):
                avQuests.append(origQuestsList[i:i + 5])

            track.append(Func(self.initQuestFrame, toon, copy.deepcopy(avQuests)))
            track.append(Wait(0.25))
            track += questList
            track.append(Wait(0.5))
        track.append(Wait(0.25))
        if trackEnded:
            track.append(Func(self.vanishFrames))
            track.append(Fanfare.makeFanfare(0, toon)[0])
            for i in range(len(endTracks)):
                if endTracks[i] == 1:
                    track += self.getEndTrackIntervalList(toon, toonList, i)

            track.append(Func(self.cleanupEndTrack))
        return track

    def testMovie(self, otherToons = []):
        track = Sequence()
        track.append(Func(self.show))
        expTrack = self.getExpTrack(base.localAvatar, [1999,
         0,
         20,
         30,
         10,
         0,
         60], [2,
         0,
         2,
         6,
         1,
         0,
         8], [3,
         1,
         3,
         0,
         2,
         2,
         1,
         1,
         30,
         2,
         1,
         0], [], [], [], [0,
         0,
         0,
         0], [0,
         0,
         0,
         0], [], [base.localAvatar] + otherToons)
        track.append(expTrack)
        if len(track) > 0:
            track.append(Func(self.hide))
            track.append(Func(base.localAvatar.loop, 'neutral'))
            track.append(Func(base.localAvatar.startUpdateSmartCamera))
            track.start()
            base.localAvatar.loop('victory')
            base.localAvatar.stopUpdateSmartCamera()
            camera.setPosHpr(0, 8, base.localAvatar.getHeight() * 0.66, 179, 15, 0)
        else:
            self.notify.debug('no experience, no movie.')
        return None

    def _handleSkip(self):
        messenger.send(self.SkipBattleMovieEvent)
