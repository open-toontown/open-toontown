from datetime import datetime
import calendar
from direct.gui.DirectGui import DirectFrame, DirectLabel
from toontown.toonbase import TTLocalizer
from direct.showbase import PythonUtil
from direct.fsm.FSM import FSM
from toontown.parties import PartyGlobals
from toontown.parties import PartyUtils
from toontown.toonbase.ToontownGlobals import VALENTINES_DAY

class InviteVisual(DirectFrame):
    notify = directNotify.newCategory('InviteVisual')

    def __init__(self, parent):
        DirectFrame.__init__(self, parent=parent)
        self.gui = loader.loadModel('phase_5.5/models/parties/partyInviteGUI')
        self.inviteThemesIdToInfo = {PartyGlobals.InviteTheme.Birthday: (self.gui.find('**/birthdayPage'), TTLocalizer.PartyPlannerBirthdayTheme, (0.0,
                                              0.0,
                                              0.0,
                                              1.0)),
         PartyGlobals.InviteTheme.GenericMale: (self.gui.find('**/genericMalePage'), TTLocalizer.PartyPlannerGenericMaleTheme, (0.7,
                                                 0.7,
                                                 0.0,
                                                 1.0)),
         PartyGlobals.InviteTheme.GenericFemale: (self.gui.find('**/genericFemalePage'), TTLocalizer.PartyPlannerGenericFemaleTheme, (0.0,
                                                   1.0,
                                                   0.5,
                                                   1.0)),
         PartyGlobals.InviteTheme.Racing: (self.gui.find('**/racingPage'), TTLocalizer.PartyPlannerRacingTheme, (0.0,
                                            0.0,
                                            0.0,
                                            1.0)),
         PartyGlobals.InviteTheme.Valentoons: (self.gui.find('**/valentinePage1'), TTLocalizer.PartyPlannerValentoonsTheme, (0.0,
                                                0.0,
                                                0.0,
                                                1.0)),
         PartyGlobals.InviteTheme.VictoryParty: (self.gui.find('**/victoryPartyPage'), TTLocalizer.PartyPlannerVictoryPartyTheme, (0.0,
                                                  0.0,
                                                  0.0,
                                                  1.0)),
         PartyGlobals.InviteTheme.Winter: (self.gui.find('**/winterPartyPage1'), TTLocalizer.PartyPlannerWinterPartyTheme, (1.0,
                                            1.0,
                                            1.0,
                                            1.0))}
        self.inviteThemeBackground = DirectFrame(parent=self, image=self.inviteThemesIdToInfo[0][0], relief=None)
        self.whosePartyLabel = DirectLabel(parent=self, relief=None, pos=self.gui.find('**/who_locator').getPos(), text='.', text_scale=0.067, textMayChange=True)
        self.activityTextLabel = DirectLabel(parent=self, relief=None, text='.\n.\n.\n.', pos=self.gui.find('**/what_locator').getPos(), text_scale=TTLocalizer.IVactivityTextLabel, textMayChange=True)
        self.whenTextLabel = DirectLabel(parent=self, relief=None, text='.\n.\n.', pos=self.gui.find('**/when_locator').getPos(), text_scale=TTLocalizer.IVwhenTextLabel, textMayChange=True)
        self.noFriends = False
        return None

    def setNoFriends(self, noFriends):
        self.noFriends = noFriends
        self.inviteThemeBackground.show()

    def updateInvitation(self, hostsName, partyInfo):
        self.partyInfo = partyInfo
        hostsName = TTLocalizer.GetPossesive(hostsName)
        self.whosePartyLabel['text'] = TTLocalizer.PartyPlannerInvitationWhoseSentence % hostsName
        if self.partyInfo.isPrivate:
            publicPrivateText = TTLocalizer.PartyPlannerPrivate.lower()
        else:
            publicPrivateText = TTLocalizer.PartyPlannerPublic.lower()
        activities = self.getActivitiesFormattedCorrectly()
        if self.noFriends:
            self.activityTextLabel['text'] = TTLocalizer.PartyPlannerInvitationThemeWhatSentenceNoFriends % (publicPrivateText, activities)
        else:
            self.activityTextLabel['text'] = TTLocalizer.PartyPlannerInvitationThemeWhatSentence % (publicPrivateText, activities)
        if self.noFriends:
            self.whenTextLabel['text'] = TTLocalizer.PartyPlannerInvitationWhenSentenceNoFriends % (PartyUtils.formatDate(self.partyInfo.startTime.year, self.partyInfo.startTime.month, self.partyInfo.startTime.day), PartyUtils.formatTime(self.partyInfo.startTime.hour, self.partyInfo.startTime.minute))
        else:
            self.whenTextLabel['text'] = TTLocalizer.PartyPlannerInvitationWhenSentence % (PartyUtils.formatDate(self.partyInfo.startTime.year, self.partyInfo.startTime.month, self.partyInfo.startTime.day), PartyUtils.formatTime(self.partyInfo.startTime.hour, self.partyInfo.startTime.minute))
        self.changeTheme(partyInfo.inviteTheme)

    def getActivitiesFormattedCorrectly(self):
        activitiesString = ''
        activityList = []
        for activity in self.partyInfo.activityList:
            text = TTLocalizer.PartyActivityNameDict[activity.activityId]['invite']
            if text not in activityList:
                activityList.append(text)

        if len(activityList) == 1:
            return '\n' + TTLocalizer.PartyPlannerInvitationThemeWhatActivitiesBeginning + activityList[0]
        conjunction = TTLocalizer.PartyActivityConjunction
        for activity in activityList:
            activitiesString = '%s, %s' % (activitiesString, activity)

        activitiesString = activitiesString[2:]
        activitiesString = activitiesString[:activitiesString.rfind(',')] + conjunction + activitiesString[activitiesString.rfind(',') + 1:]
        activitiesString = TTLocalizer.PartyPlannerInvitationThemeWhatActivitiesBeginning + activitiesString
        return self.insertCarriageReturn(activitiesString)

    def insertCarriageReturn(self, stringLeft, stringDone = ''):
        desiredNumberOfCharactersInLine = 42
        if len(stringLeft) < desiredNumberOfCharactersInLine:
            return stringDone + '\n' + stringLeft
        for i in range(desiredNumberOfCharactersInLine - 6, len(stringLeft)):
            if stringLeft[i] == ' ':
                return self.insertCarriageReturn(stringLeft[i:], stringDone + '\n' + stringLeft[:i])

        return stringDone + '\n' + stringLeft

    def changeTheme(self, newTheme):
        self.inviteThemeBackground['image'] = self.inviteThemesIdToInfo[newTheme][0]
        self.whosePartyLabel['text_fg'] = self.inviteThemesIdToInfo[newTheme][2]
        self.activityTextLabel['text_fg'] = self.inviteThemesIdToInfo[newTheme][2]
        self.whenTextLabel['text_fg'] = self.inviteThemesIdToInfo[newTheme][2]

    def close(self):
        self.destroy()
        del self
