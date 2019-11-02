import calendar
from datetime import datetime
from datetime import timedelta
from pandac.PandaModules import Vec3, Vec4, Point3, TextNode, VBase4
from otp.otpbase import OTPLocalizer
from direct.gui.DirectGui import DirectFrame, DirectButton, DirectLabel, DirectScrolledList, DirectCheckButton
from direct.gui import DirectGuiGlobals
from direct.showbase import DirectObject
from direct.showbase import PythonUtil
from direct.fsm.FSM import FSM
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.toontowngui import TTDialog
from toontown.toontowngui.TeaserPanel import TeaserPanel
from toontown.toon import ToonHead
from toontown.parties import PartyGlobals
from toontown.friends.FriendsListPanel import determineFriendName
from toontown.parties.ScrolledFriendList import ScrolledFriendList
from toontown.parties.CalendarGuiMonth import CalendarGuiMonth
from toontown.parties.InviteVisual import InviteVisual
from toontown.parties.PartyInfo import PartyInfo
from toontown.parties import PartyUtils
from toontown.parties.PartyEditor import PartyEditor
from otp.otpbase import OTPGlobals
from pandac.PandaModules import *
from direct.directnotify import DirectNotifyGlobal

class PartyPlanner(DirectFrame, FSM):
    notify = DirectNotifyGlobal.directNotify.newCategory('PartyPlanner')

    def __init__(self, doneEvent = None):
        FSM.__init__(self, 'PartyPlannerFSM')
        DirectFrame.__init__(self)
        self.doneEvent = doneEvent
        self.stateArray = ['Off',
         'Welcome',
         'PartyEditor',
         'Guests',
         'Date',
         'Time',
         'Invitation',
         'Farewell']
        self.partyTime = base.cr.toontownTimeManager.getCurServerDateTime()
        self.partyNowTime = base.cr.toontownTimeManager.getCurServerDateTime()
        minutesToNextFifteen = 15 - self.partyTime.minute % 15
        self.cleanPartyTime = self.partyTime + timedelta(minutes=minutesToNextFifteen, seconds=-self.partyTime.second)
        self.partyTime = self.cleanPartyTime
        self.guests = []
        self.isPrivate = False
        self.selectedCalendarGuiDay = None
        self.gui = loader.loadModel('phase_4/models/parties/partyPlannerGUI')
        self.partyDuration = timedelta(hours=PartyGlobals.DefaultPartyDuration)
        self.timeTypeToMaxValue = {'hour': 23,
         'minute': 59}
        self.timeTypeToChangeAmount = {'hour': (1, -1),
         'minute': (15, -15),
         'ampm': (1, -1)}
        self.partyInfo = None
        self.asapMinuteRounding = base.config.GetInt('party-asap-minute-rounding', PartyGlobals.PartyPlannerAsapMinuteRounding)
        self.load()
        self.request('Welcome')
        return

    def enterWelcome(self, *args):
        self.prevButton['state'] = DirectGuiGlobals.DISABLED
        self.prevButton.hide()
        self.nextButton['state'] = DirectGuiGlobals.NORMAL
        self.welcomePage.show()
        self.partyPlannerHead.reparentTo(self.welcomePage)
        self.partyPlannerHead.startBlink()
        self.partyPlannerHead.startLookAround()
        self.nametagNP.reparentTo(self.welcomePage)
        self.chatNP.reparentTo(self.welcomePage)

    def exitWelcome(self):
        self.welcomePage.hide()
        self.prevButton.show()
        self.partyPlannerHead.stopBlink()
        self.partyPlannerHead.stopLookAround()

    def enterPartyEditor(self, *args):
        self.prevButton['state'] = DirectGuiGlobals.NORMAL
        self.nextButton['state'] = DirectGuiGlobals.DISABLED
        self.nextButton.hide()
        self.partyEditorPage.show()
        self.okWithGroundsGui.doneStatus = ''
        self.partyEditor.request('Idle')

    def exitPartyEditor(self):
        self.partyEditor.request('Hidden')
        self.partyEditorPage.hide()

    def enterGuests(self, *args):
        self.prevButton['state'] = DirectGuiGlobals.NORMAL
        self.nextButton['state'] = DirectGuiGlobals.NORMAL
        self.nextButton.show()
        self.guestPage.show()

    def exitGuests(self):
        self.guests = []
        for friendCheckBox in self.friendList['items']:
            if friendCheckBox['indicatorValue']:
                self.guests.append(friendCheckBox.getPythonTag('id'))

        self.guestPage.hide()

    def enterDate(self, *args):
        self.prevButton.show()
        self.prevButton['state'] = DirectGuiGlobals.NORMAL
        if self.selectedCalendarGuiDay is None:
            self.nextButton['state'] = DirectGuiGlobals.DISABLED
            self.nextButton.hide()
            self.makePartyNowButton.show()
        self.datePage.show()
        return

    def exitDate(self):
        self.datePage.hide()
        self.nextButton.show()
        if self.selectedCalendarGuiDay is not None:
            self.partyTime = self.cleanPartyTime
            self.alterPartyTime(year=self.selectedCalendarGuiDay.myDate.year, month=self.selectedCalendarGuiDay.myDate.month, day=self.selectedCalendarGuiDay.myDate.day)
        else:
            self.partyNowTime = self.calcAsapTime()
            self.partyTime = self.partyNowTime
        return

    def calcAsapTime(self):
        curServerTime = base.cr.toontownTimeManager.getCurServerDateTime()
        baseTime = curServerTime
        baseTime = baseTime.replace(baseTime.year, baseTime.month, baseTime.day, baseTime.hour, baseTime.minute, second=0, microsecond=0)
        minute = curServerTime.minute
        remainder = minute % self.asapMinuteRounding
        if remainder:
            baseTime += timedelta(minutes=self.asapMinuteRounding - remainder)
        else:
            baseTime += timedelta(minutes=self.asapMinuteRounding)
        return baseTime

    def enterTime(self, *args):
        self.prevButton.show()
        self.prevButton['state'] = DirectGuiGlobals.NORMAL
        self.nextButton.show()
        self.timePage.show()
        self.timePageRecapToontownTimeLabel2['text'] = '%s' % PartyUtils.formatDateTime(self.partyTime)
        self.timePageRecapLocalTimeLabel['text'] = '%s%s' % (TTLocalizer.PartyPlannerTimeLocalTime, PartyUtils.formatDateTime(self.partyTime, inLocalTime=True))

    def exitTime(self):
        self.timePage.hide()
        self.nextButton.show()

    def enterInvitation(self, *args):
        self.prevButton['state'] = DirectGuiGlobals.NORMAL
        self.nextButton.hide()
        defaultInviteTheme = PartyGlobals.InviteTheme.GenericMale
        if hasattr(base.cr, 'newsManager') and base.cr.newsManager:
            if ToontownGlobals.VICTORY_PARTY_HOLIDAY in base.cr.newsManager.getHolidayIdList():
                defaultInviteTheme = PartyGlobals.InviteTheme.VictoryParty
            elif ToontownGlobals.KARTING_TICKETS_HOLIDAY in base.cr.newsManager.getHolidayIdList() or ToontownGlobals.CIRCUIT_RACING_EVENT in base.cr.newsManager.getHolidayIdList():
                defaultInviteTheme = PartyGlobals.InviteTheme.Racing
            elif ToontownGlobals.VALENTINES_DAY in base.cr.newsManager.getHolidayIdList():
                defaultInviteTheme = PartyGlobals.InviteTheme.Valentoons
        if self.partyInfo is not None:
            del self.partyInfo
        activityList = self.partyEditor.partyEditorGrid.getActivitiesOnGrid()
        decorationList = self.partyEditor.partyEditorGrid.getDecorationsOnGrid()
        endTime = self.partyTime + self.partyDuration
        self.partyInfo = PartyInfo(0, 0, self.partyTime.year, self.partyTime.month, self.partyTime.day, self.partyTime.hour, self.partyTime.minute, endTime.year, endTime.month, endTime.day, endTime.hour, endTime.minute, self.isPrivate, defaultInviteTheme, activityList, decorationList, 0)
        if self.noFriends or len(self.getInvitees()) == 0:
            self.inviteVisual.setNoFriends(True)
            self.invitationTitleLabel['text'] = TTLocalizer.PartyPlannerConfirmTitleNoFriends
            self.inviteButton['text'] = TTLocalizer.PartyPlannerInviteButtonNoFriends
            self.selectedInviteThemeLabel.stash()
            self.nextThemeButton.stash()
            self.prevThemeButton.stash()
            self.setInviteTheme(defaultInviteTheme)
        else:
            self.inviteVisual.setNoFriends(False)
            self.invitationTitleLabel['text'] = TTLocalizer.PartyPlannerConfirmTitle
            self.inviteButton['text'] = TTLocalizer.PartyPlannerInviteButton
            self.selectedInviteThemeLabel.unstash()
            self.nextThemeButton.unstash()
            self.prevThemeButton.unstash()
            self.setInviteTheme(defaultInviteTheme)
        self.inviteVisual.updateInvitation(base.localAvatar.getName(), self.partyInfo)
        self.invitationPage.show()
        return

    def __prevTheme(self):
        self.nextThemeButton.show()
        prevTheme = self.currentInvitationTheme - 1
        while prevTheme not in self.inviteThemes:
            prevTheme -= 1
            if prevTheme == self.currentInvitationTheme:
                self.notify.warning('No previous invite theme found.')
                break
            elif prevTheme < 0:
                prevTheme = len(self.inviteVisual.inviteThemesIdToInfo) - 1

        self.setInviteTheme(prevTheme)

    def __nextTheme(self):
        self.prevThemeButton.show()
        nextTheme = self.currentInvitationTheme + 1
        while nextTheme not in self.inviteThemes:
            nextTheme += 1
            if nextTheme == self.currentInvitationTheme:
                self.notify.warning('No next invite theme found.')
                break
            elif nextTheme >= len(self.inviteVisual.inviteThemesIdToInfo):
                nextTheme = 0

        self.setInviteTheme(nextTheme)

    def setInviteTheme(self, themeNumber):
        self.currentInvitationTheme = themeNumber
        self.selectedInviteThemeLabel['text'] = '%s %s (%d/%d)' % (self.inviteVisual.inviteThemesIdToInfo[self.currentInvitationTheme][1],
         TTLocalizer.PartyPlannerInvitationTheme,
         self.inviteThemes.index(self.currentInvitationTheme) + 1,
         len(self.inviteThemes))
        self.partyInfo.inviteTheme = self.currentInvitationTheme
        self.inviteVisual.updateInvitation(base.localAvatar.getName(), self.partyInfo)

    def exitInvitation(self):
        self.invitationPage.hide()
        self.nextButton.show()

    def enterFarewell(self, goingBackAllowed):
        self.farewellPage.show()
        if goingBackAllowed:
            self.prevButton.show()
        else:
            self.prevButton.hide()
        self.nextButton.hide()
        self.partyPlannerHead.reparentTo(self.farewellPage)
        self.partyPlannerHead.startBlink()
        self.partyPlannerHead.startLookAround()
        self.nametagNP.reparentTo(self.farewellPage)
        self.chatNP.reparentTo(self.farewellPage)

    def exitFarewell(self):
        self.farewellPage.hide()
        self.nextButton.show()
        self.prevButton.show()
        self.partyPlannerHead.stopBlink()
        self.partyPlannerHead.stopLookAround()

    def load(self):
        self.frame = DirectFrame(parent=aspect2d, geom=self.gui.find('**/background'), relief=None, scale=0.85, pos=(0.05, 0.0, 0.1))
        self.titleScale = TTLocalizer.PPtitleScale
        self._createNavButtons()
        self.welcomePage = self._createWelcomePage()
        self.welcomePage.hide()
        self.datePage = self._createDatePage()
        self.datePage.hide()
        self.timePage = self._createTimePage()
        self.timePage.hide()
        self.guestPage = self._createGuestPage()
        self.guestPage.hide()
        self.partyEditorPage = self._createPartyEditorPage()
        self.partyEditorPage.hide()
        self.invitationPage = self._createInvitationPage()
        self.invitationPage.hide()
        self.farewellPage = self._createFarewellPage()
        self.farewellPage.hide()
        return

    def _createNavButtons(self):
        self.quitButton = DirectButton(parent=self.frame, relief=None, geom=(self.gui.find('**/cancelButton_up'), self.gui.find('**/cancelButton_down'), self.gui.find('**/cancelButton_rollover')), command=self.__acceptExit)
        self.nextButton = DirectButton(parent=self.frame, relief=None, geom=(self.gui.find('**/bottomNext_button/nextButton_up'), self.gui.find('**/bottomNext_button/nextButton_down'), self.gui.find('**/bottomNext_button/nextButton_rollover')), command=self.__nextItem, state=DirectGuiGlobals.DISABLED)
        self.prevButton = DirectButton(parent=self.frame, relief=None, geom=(self.gui.find('**/bottomPrevious_button/previousButton_up'), self.gui.find('**/bottomPrevious_button/previousButton_down'), self.gui.find('**/bottomPrevious_button/previousButton_rollover')), command=self.__prevItem, state=DirectGuiGlobals.DISABLED)
        self.currentItem = None
        return

    def __createNametag(self, parent):
        if self.nametagGroup == None:
            self.nametagGroup = NametagGroup()
            self.nametagGroup.setFont(OTPGlobals.getInterfaceFont())
            self.nametagGroup.setActive(0)
            self.nametagGroup.setAvatar(self.partyPlannerHead)
            self.nametagGroup.manage(base.marginManager)
            self.nametagGroup.setColorCode(self.nametagGroup.CCNonPlayer)
            self.nametagGroup.getNametag2d().setContents(0)
            self.nametagNode = NametagFloat2d()
            self.nametagNode.setContents(Nametag.CName)
            self.nametagGroup.addNametag(self.nametagNode)
            self.nametagGroup.setName(base.cr.partyManager.getPartyPlannerName())
            self.nametagNP = parent.attachNewNode(self.nametagNode.upcastToPandaNode())
            nametagPos = self.gui.find('**/step_01_partymanPeteNametag_locator').getPos()
            self.nametagNP.setPosHprScale(nametagPos[0], 0, nametagPos[2], 0, 0, 0, 0.1, 1, 0.1)
            self.chatNode = NametagFloat2d()
            self.chatNode.setContents(Nametag.CSpeech | Nametag.CThought)
            self.nametagGroup.addNametag(self.chatNode)
            self.nametagGroup.setChat(TTLocalizer.PartyPlannerInstructions, CFSpeech)
            self.chatNP = parent.attachNewNode(self.chatNode.upcastToPandaNode())
            chatPos = self.gui.find('**/step_01_partymanPeteText_locator').getPos()
            self.chatNP.setPosHprScale(chatPos[0], 0, chatPos[2], 0, 0, 0, 0.08, 1, 0.08)
        return

    def clearNametag(self):
        if self.nametagGroup != None:
            self.nametagGroup.unmanage(base.marginManager)
            self.nametagGroup.removeNametag(self.nametagNode)
            self.nametagGroup.removeNametag(self.chatNode)
            self.nametagNP.removeNode()
            self.chatNP.removeNode()
            del self.nametagNP
            del self.chatNP
            del self.nametagNode
            del self.chatNode
            self.nametagGroup.setAvatar(NodePath())
            self.nametagGroup = None
        return

    def _createWelcomePage(self):
        self.nametagGroup = None
        page = DirectFrame(self.frame)
        page.setName('PartyPlannerWelcomePage')
        self.welcomeTitleLabel = DirectLabel(parent=page, relief=None, text=TTLocalizer.PartyPlannerWelcomeTitle, pos=self.gui.find('**/title_locator').getPos(), scale=self.titleScale)
        self.partyPlannerHead = ToonHead.ToonHead()
        partyPlannerStyle = base.cr.partyManager.getPartyPlannerStyle()
        self.partyPlannerHead.setupHead(partyPlannerStyle, forGui=True)
        self.partyPlannerHead.setPos(self.gui.find('**/step_01_partymanPete_locator').getPos())
        animal = partyPlannerStyle.getAnimal()
        if animal == 'cat' or animal == 'pig':
            headScale = 0.4
        elif animal == 'dog' or animal == 'bear':
            headScale = 0.45
        elif animal == 'rabbit':
            headScale = 0.35
        else:
            headScale = 0.3
        self.partyPlannerHead.setScale(headScale)
        self.partyPlannerHead.setH(180.0)
        self.partyPlannerHead.reparentTo(page)
        self.__createNametag(page)
        return page

    def _createDatePage(self):
        page = DirectFrame(self.frame)
        page.setName('PartyPlannerDatePage')
        self.createDateTitleLabel = DirectLabel(parent=page, relief=None, text=TTLocalizer.PartyPlannerDateTitle, pos=self.gui.find('**/title_locator').getPos(), scale=self.titleScale)
        pos = self.gui.find('**/step_06_sendInvitation_locator').getPos()
        self.makePartyNowButton = DirectButton(parent=page, relief=None, geom=(self.gui.find('**/send_up'), self.gui.find('**/send_down'), self.gui.find('**/send_rollover')), text=TTLocalizer.PartyPlannerPartyNow, text_pos=(pos[0], pos[2]), text_scale=0.05, command=self.__doMakePartyNow)
        curServerDate = base.cr.toontownTimeManager.getCurServerDateTime()
        self.calendarGuiMonth = CalendarGuiMonth(page, curServerDate, scale=0.95, pos=(-0.05, 0.0, -0.33), dayClickCallback=self._dayClickCallback, onlyFutureDaysClickable=True)
        return page

    def __doMakePartyNow(self):
        self.request('Invitation')

    def _dayClickCallback(self, calendarGuiDay):
        self.selectedCalendarGuiDay = calendarGuiDay
        self.nextButton['state'] = DirectGuiGlobals.NORMAL
        self.makePartyNowButton.hide()
        self.nextButton.show()

    def alterPartyTime(self, year = None, month = None, day = None, hour = None, minute = None):
        self.partyTime = datetime(year=self.positiveTime('year', year), month=self.positiveTime('month', month), day=self.positiveTime('day', day), hour=self.positiveTime('hour', hour), minute=self.positiveTime('minute', minute), tzinfo=self.partyTime.tzinfo)

    def positiveTime(self, type, amount):
        if amount is None:
            return getattr(self.partyTime, type)
        if type == 'hour' or type == 'minute':
            if amount < 0:
                return self.timeTypeToMaxValue[type] + 1 + self.timeTypeToChangeAmount[type][1]
            elif amount > self.timeTypeToMaxValue[type]:
                return 0
        return amount

    def _createTimePage(self):
        page = DirectFrame(self.frame)
        page.setName('PartyPlannerTimePage')
        self.createTimeTitleLabel = DirectLabel(parent=page, relief=None, text=TTLocalizer.PartyPlannerTimeTitle, pos=self.gui.find('**/title_locator').getPos(), scale=self.titleScale)
        self.clockImage = DirectFrame(parent=page, relief=None, geom=self.gui.find('**/toontownTime_background'))
        self.timePageToontownLabel = DirectLabel(parent=page, relief=None, text=TTLocalizer.PartyPlannerTimeToontown, pos=self.gui.find('**/step_03_toontown_locator').getPos(), scale=0.15, text_fg=(1.0, 0.0, 0.0, 1.0), text_font=ToontownGlobals.getSignFont())
        self.timePageTimeLabel = DirectLabel(parent=page, relief=None, text=TTLocalizer.PartyPlannerTimeTime, pos=self.gui.find('**/step_03_time_locator').getPos(), scale=0.15, text_fg=(1.0, 0.0, 0.0, 1.0), text_font=ToontownGlobals.getSignFont())
        self.timePageRecapLabel = DirectLabel(parent=page, relief=None, text=TTLocalizer.PartyPlannerTimeRecap, pos=self.gui.find('**/step_03_partyDateAndTime_locator').getPos(), scale=0.09)
        self.timePageRecapToontownTimeLabel1 = DirectLabel(parent=page, relief=None, text=TTLocalizer.PartyPlannerTimeToontownTime, pos=self.gui.find('**/step_03_toontownTime_locator').getPos(), scale=0.06)
        self.timePageRecapToontownTimeLabel2 = DirectLabel(parent=page, relief=None, text='%s' % PartyUtils.formatDateTime(self.partyTime), pos=self.gui.find('**/step_03_toontownDateAndTime_loactor').getPos(), textMayChange=True, scale=0.06)
        self.timePageRecapLocalTimeLabel = DirectLabel(parent=page, relief=None, text='%s%s' % (TTLocalizer.PartyPlannerTimeLocalTime, PartyUtils.formatDateTime(self.partyTime, inLocalTime=True)), pos=self.gui.find('**/step_03_localDateAndTime_loactor').getPos(), textMayChange=True, scale=0.06, text_fg=(1.0, 0.0, 0.0, 1.0))
        self.timeInputHourLabel, self.timeInputHourUpButton, self.timeInputHourDownButton = self.getTimeWidgets(page, 'hour')
        self.timeInputMinuteLabel, self.timeInputMinuteUpButton, self.timeInputMinuteDownButton = self.getTimeWidgets(page, 'minute')
        self.timeInputAmPmLabel, self.timeInputAmPmUpButton, self.timeInputAmPmDownButton = self.getTimeWidgets(page, 'ampm')
        self.timePagecolonLabel = DirectLabel(parent=page, relief=None, text=':', pos=self.gui.find('**/step_03_colon_locator').getPos(), scale=0.15)
        return page

    def getTimeWidgets(self, page, type):
        if type == 'ampm':
            data = self.getCurrentAmPm()
        else:
            data = getattr(self.partyTime, type)
            if data == 0 and type == 'minute':
                data = '00'
            else:
                if type == 'hour':
                    data = data % 12
                    if data == 0:
                        data = 12
                data = '%d' % data
        label = DirectLabel(parent=page, relief=None, text='%s' % data, textMayChange=True, pos=self.gui.find('**/step_03_%s_locator' % type).getPos(), scale=0.12)

        def changeValue(self, amount):
            if type == 'ampm':
                self.alterPartyTime(hour=(self.partyTime.hour + 12) % 24)
                newAmount = self.getCurrentAmPm()
                label['text'] = newAmount
            else:
                if type == 'hour':
                    newAmount = getattr(self.partyTime, type) + amount
                    newAmount = newAmount % 12
                    if self.timeInputAmPmLabel['text'] == TTLocalizer.PartyTimeFormatMeridiemPM:
                        newAmount = newAmount % 12 + 12
                    self.alterPartyTime(hour=newAmount)
                elif type == 'minute':
                    newAmount = getattr(self.partyTime, type) + amount
                    self.alterPartyTime(minute=newAmount)
                else:
                    PartyPlanner.notify.error('Invalid type for changeValue in PartyPlanner: %s' % type)
                newAmount = getattr(self.partyTime, type)
                if newAmount < 10 and type == 'minute':
                    label['text'] = '0%d' % newAmount
                else:
                    if type == 'hour':
                        newAmount = newAmount % 12
                        if newAmount == 0:
                            newAmount = 12
                    label['text'] = '%d' % newAmount
            self.timePageRecapToontownTimeLabel2['text'] = '%s' % PartyUtils.formatDateTime(self.partyTime)
            self.timePageRecapLocalTimeLabel['text'] = '%s%s' % (TTLocalizer.PartyPlannerTimeLocalTime, PartyUtils.formatDateTime(self.partyTime, inLocalTime=True))

        upButton = DirectButton(parent=page, relief=None, geom=(self.gui.find('**/%sButtonUp_up' % type), self.gui.find('**/%sButtonUp_down' % type), self.gui.find('**/%sButtonUp_rollover' % type)), command=changeValue, extraArgs=[self, self.timeTypeToChangeAmount[type][0]])
        downButton = DirectButton(parent=page, relief=None, geom=(self.gui.find('**/%sButtonDown_up' % type), self.gui.find('**/%sButtonDown_down' % type), self.gui.find('**/%sButtonDown_rollover' % type)), command=changeValue, extraArgs=[self, self.timeTypeToChangeAmount[type][1]])
        return (label, upButton, downButton)

    def getCurrentAmPm(self):
        if self.partyTime.hour < 12:
            return TTLocalizer.PartyTimeFormatMeridiemAM
        else:
            return TTLocalizer.PartyTimeFormatMeridiemPM

    def _createGuestPage(self):
        page = DirectFrame(self.frame)
        page.setName('PartyPlannerGuestPage')
        self.guestTitleLabel = DirectLabel(parent=page, relief=None, text=TTLocalizer.PartyPlannerGuestTitle, pos=self.gui.find('**/title_locator').getPos(), scale=self.titleScale)
        self.guestBackgroundLabel = DirectLabel(parent=page, relief=None, image=self.gui.find('**/guestListBackground_flat'), scale=(1.2, 1.0, 1.0))
        self.friendList = ScrolledFriendList(page, self.gui, makeItemsCheckBoxes=True)
        if len(base.localAvatar.friendsList) == 0:
            self.noFriends = True
        else:
            self.noFriends = False
            for friendPair in base.localAvatar.friendsList:
                self.friendList.addFriend(determineFriendName(friendPair), friendPair[0])

            self.friendList.scrollTo(0)
        pos = self.gui.find('**/step_04_partyWillBe_locator').getPos()
        self.publicPrivateLabel = DirectLabel(parent=page, relief=None, text=TTLocalizer.PartyPlannerPublicPrivateLabel, text_align=TextNode.ACenter, text_scale=0.065, pos=pos)
        self.publicDescriptionLabel = DirectLabel(parent=page, relief=None, text=TTLocalizer.PartyPlannerPublicDescription, text_align=TextNode.ACenter, text_scale=TTLocalizer.PPpbulicDescriptionLabel, pos=(pos[0] - 0.52, pos[1], pos[2]))
        self.publicDescriptionLabel.stash()
        self.privateDescriptionLabel = DirectLabel(parent=page, relief=None, text=TTLocalizer.PartyPlannerPrivateDescription, text_align=TextNode.ACenter, text_scale=TTLocalizer.PPprivateDescriptionLabel, pos=(pos[0] + 0.55, pos[1], pos[2]))
        self.privateDescriptionLabel.stash()
        pos = self.gui.find('**/step_04_public_locator').getPos()
        self.publicButton = DirectButton(parent=page, relief=None, geom=(self.gui.find('**/publicButton_up'),
         self.gui.find('**/publicButton_down'),
         self.gui.find('**/publicButton_rollover'),
         self.gui.find('**/publicButton_inactive')), text=TTLocalizer.PartyPlannerPublic, text_pos=(pos[0], pos[2]), text_scale=TTLocalizer.PPpublicButton, command=self.__doTogglePublicPrivate)
        self.publicButton['state'] = DirectGuiGlobals.DISABLED
        self.publicButton.bind(DirectGuiGlobals.ENTER, self.__enterPublic)
        self.publicButton.bind(DirectGuiGlobals.EXIT, self.__exitPublic)
        pos = self.gui.find('**/step_04_private_locator').getPos()
        self.privateButton = DirectButton(parent=page, relief=None, geom=(self.gui.find('**/privateButton_up'),
         self.gui.find('**/privateButton_down'),
         self.gui.find('**/privateButton_rollover'),
         self.gui.find('**/privateButton_inactive')), text=TTLocalizer.PartyPlannerPrivate, text_pos=(pos[0], pos[2]), text_scale=TTLocalizer.PPprivateButton, command=self.__doTogglePublicPrivate)
        self.privateButton.bind(DirectGuiGlobals.ENTER, self.__enterPrivate)
        self.privateButton.bind(DirectGuiGlobals.EXIT, self.__exitPrivate)
        self.checkAllButton = DirectButton(parent=page, relief=None, geom=(self.gui.find('**/checkAllButton_up'), self.gui.find('**/checkAllButton_down'), self.gui.find('**/checkAllButton_rollover')), command=self.__doCheckAll)
        self.uncheckAllButton = DirectButton(parent=page, relief=None, geom=(self.gui.find('**/uncheckAllButton_up'), self.gui.find('**/uncheckAllButton_down'), self.gui.find('**/uncheckAllButton_rollover')), command=self.__doUncheckAll)
        return page

    def __doCheckAll(self):
        for friendBox in self.friendList['items']:
            friendBox['indicatorValue'] = True

    def __doUncheckAll(self):
        for friendBox in self.friendList['items']:
            friendBox['indicatorValue'] = False

    def __enterPrivate(self, mouseEvent):
        self.privateDescriptionLabel.unstash()

    def __exitPrivate(self, mouseEvent):
        self.privateDescriptionLabel.stash()

    def __enterPublic(self, mouseEvent):
        self.publicDescriptionLabel.unstash()

    def __exitPublic(self, mouseEvent):
        self.publicDescriptionLabel.stash()

    def __doTogglePublicPrivate(self):
        if self.isPrivate:
            self.isPrivate = False
            self.privateButton['state'] = DirectGuiGlobals.NORMAL
            self.publicButton['state'] = DirectGuiGlobals.DISABLED
        else:
            self.isPrivate = True
            self.privateButton['state'] = DirectGuiGlobals.DISABLED
            self.publicButton['state'] = DirectGuiGlobals.NORMAL

    def _createPartyEditorPage(self):
        page = DirectFrame(self.frame)
        page.setName('PartyPlannerEditorPage')
        self.LayoutTitleLabel = DirectLabel(parent=page, relief=None, text=TTLocalizer.PartyPlannerEditorTitle, pos=self.gui.find('**/title_locator').getPos() + Point3(0.0, 0.0, 0.075), scale=self.titleScale)
        self.costLabel = DirectLabel(parent=page, pos=(-0.74, 0.0, 0.17), relief=None, text=TTLocalizer.PartyPlannerTotalCost % 0, text_align=TextNode.ACenter, scale=TTLocalizer.PPcostLabel, textMayChange=True)
        self.partyGridBackground = DirectFrame(parent=page, relief=None, geom=self.gui.find('**/partyGrid_flat'))
        self.partyGroundsLabel = DirectLabel(parent=page, relief=None, text=TTLocalizer.PartyPlannerPartyGrounds, text_font=ToontownGlobals.getSignFont(), text_fg=VBase4(1.0, 0.0, 0.0, 1.0), text_scale=TTLocalizer.PPpartyGroundsLabel, pos=self.gui.find('**/step_05_partyGrounds_text_locator').getPos(), scale=0.1)
        self.activityBackground = DirectFrame(parent=page, relief=None, geom=self.gui.find('**/activitiesDecorations_flat1'), pos=(0.0, 0.0, 0.04))
        pos = self.gui.find('**/step_05_instructions_locator').getPos()
        self.instructionLabel = DirectLabel(parent=page, relief=None, text=' ', text_pos=(pos[0], pos[2]), text_scale=TTLocalizer.PPinstructionLabel, textMayChange=True, geom=self.gui.find('**/instructions_flat'))
        self.elementTitleLabel = DirectLabel(parent=page, relief=None, text=' ', pos=self.gui.find('**/step_05_activitiesName_text_locator').getPos() + Point3(0.0, 0.0, 0.04), text_scale=TTLocalizer.PPelementTitleLabel, textMayChange=True)
        self.elementPriceNode = TextNode('ElementPrice')
        self.elementPriceNode.setAlign(TextNode.ALeft)
        self.elementPriceNode.setTextColor(0.0, 0.0, 0.0, 1.0)
        self.elementPriceNode.setFont(ToontownGlobals.getToonFont())
        self.elementPrice = page.attachNewNode(self.elementPriceNode)
        self.elementPrice.setScale(TTLocalizer.PPelementPriceNode)
        self.elementPrice.setPos(self.gui.find('**/step_05_activityPrice_text_locator').getPos() + Point3(-0.02, 0.0, 0.04))
        self.elementDescriptionNode = TextNode('ElementDescription')
        self.elementDescriptionNode.setAlign(TextNode.ACenter)
        self.elementDescriptionNode.setWordwrap(8)
        self.elementDescriptionNode.setFont(ToontownGlobals.getToonFont())
        self.elementDescriptionNode.setTextColor(0.0, 0.0, 0.0, 1.0)
        self.elementDescription = page.attachNewNode(self.elementDescriptionNode)
        self.elementDescription.setScale(TTLocalizer.PPelementDescription)
        self.elementDescription.setPos(self.gui.find('**/step_05_activityDescription_text_locator').getPos() + Point3(0.0, 0.0, 0.04))
        self.totalMoney = base.localAvatar.getTotalMoney()
        catalogGui = loader.loadModel('phase_5.5/models/gui/catalog_gui')
        self.beanBank = DirectLabel(parent=page, relief=None, text=str(self.totalMoney), text_align=TextNode.ARight, text_scale=0.075, text_fg=(0.95, 0.95, 0, 1), text_shadow=(0, 0, 0, 1), text_pos=(0.495, -0.53), text_font=ToontownGlobals.getSignFont(), textMayChange=True, image=catalogGui.find('**/bean_bank'), image_scale=(0.65, 0.65, 0.65), scale=0.9, pos=(-0.75, 0.0, 0.6))
        catalogGui.removeNode()
        del catalogGui
        self.accept(localAvatar.uniqueName('moneyChange'), self.__moneyChange)
        self.accept(localAvatar.uniqueName('bankMoneyChange'), self.__moneyChange)
        self.partyEditor = PartyEditor(self, page)
        self.partyEditor.request('Hidden')
        pos = self.gui.find('**/step_05_add_text_locator').getPos()
        self.elementBuyButton = DirectButton(parent=page, relief=None, text=TTLocalizer.PartyPlannerBuy, text_pos=(pos[0], pos[2]), text_scale=TTLocalizer.PPelementBuyButton, geom=(self.gui.find('**/add_up'), self.gui.find('**/add_down'), self.gui.find('**/add_rollover')), geom3_color=VBase4(0.5, 0.5, 0.5, 1.0), textMayChange=True, pos=(0.0, 0.0, 0.04), command=self.partyEditor.buyCurrentElement)
        self.okWithPartyGroundsLayoutEvent = 'okWithPartyGroundsLayoutEvent'
        self.accept(self.okWithPartyGroundsLayoutEvent, self.okWithPartyGroundsLayout)
        self.okWithGroundsGui = TTDialog.TTGlobalDialog(dialogName=self.uniqueName('PartyEditorOkGui'), doneEvent=self.okWithPartyGroundsLayoutEvent, message=TTLocalizer.PartyPlannerOkWithGroundsLayout, style=TTDialog.YesNo, okButtonText=OTPLocalizer.DialogYes, cancelButtonText=OTPLocalizer.DialogNo)
        self.okWithGroundsGui.doneStatus = ''
        self.okWithGroundsGui.hide()
        return page

    def okWithPartyGroundsLayout(self):
        self.okWithGroundsGui.hide()
        if self.okWithGroundsGui.doneStatus == 'ok':
            self.__nextItem()

    def setNextButtonState(self, enabled):
        if enabled:
            self.nextButton['state'] = DirectGuiGlobals.NORMAL
            self.nextButton.show()
        else:
            self.nextButton['state'] = DirectGuiGlobals.DISABLED
            self.nextButton.hide()

    def _createInvitationPage(self):
        self.__handleHolidays()
        page = DirectFrame(self.frame)
        page.setName('PartyPlannerInvitationPage')
        self.invitationTitleLabel = DirectLabel(parent=page, relief=None, text=TTLocalizer.PartyPlannerConfirmTitle, textMayChange=True, pos=self.gui.find('**/title_locator').getPos(), scale=self.titleScale)
        self.invitationBackground = DirectFrame(parent=page, relief=None, geom=self.gui.find('**/invitationBackground'))
        self.inviteVisual = InviteVisual(page)
        self.selectedInviteThemeLabel = DirectLabel(parent=page, relief=None, pos=self.gui.find('**/step_06_theme_locator').getPos(), text='', text_scale=0.06, textMayChange=True)
        self.nextThemeButton = DirectButton(parent=page, relief=None, geom=(self.gui.find('**/topNext_button/nextButton_up'), self.gui.find('**/topNext_button/nextButton_down'), self.gui.find('**/topNext_button/nextButton_rollover')), command=self.__nextTheme)
        self.prevThemeButton = DirectButton(parent=page, relief=None, geom=(self.gui.find('**/topPrevious_button/previousButton_up'), self.gui.find('**/topPrevious_button/previousButton_down'), self.gui.find('**/topPrevious_button/previousButton_rollover')), command=self.__prevTheme)
        pos = self.gui.find('**/step_06_sendInvitation_locator').getPos()
        self.inviteButton = DirectButton(parent=page, relief=None, geom=(self.gui.find('**/send_up'), self.gui.find('**/send_down'), self.gui.find('**/send_rollover')), text=TTLocalizer.PartyPlannerInviteButton, textMayChange=True, text_scale=0.05, text_pos=(pos[0], pos[2]), command=self.__handleComplete)
        return page

    def __handleHolidays(self):
        self.inviteThemes = range(len(PartyGlobals.InviteTheme))
        if hasattr(base.cr, 'newsManager') and base.cr.newsManager:
            holidayIds = base.cr.newsManager.getHolidayIdList()
            if ToontownGlobals.VALENTINES_DAY not in holidayIds:
                self.inviteThemes.remove(PartyGlobals.InviteTheme.Valentoons)
            if ToontownGlobals.VICTORY_PARTY_HOLIDAY not in holidayIds:
                self.inviteThemes.remove(PartyGlobals.InviteTheme.VictoryParty)
            if ToontownGlobals.WINTER_DECORATIONS not in holidayIds and ToontownGlobals.WACKY_WINTER_DECORATIONS not in holidayIds:
                self.inviteThemes.remove(PartyGlobals.InviteTheme.Winter)

    def _createFarewellPage(self):
        page = DirectFrame(self.frame)
        page.setName('PartyPlannerFarewellPage')
        self.confirmTitleLabel = DirectLabel(parent=page, relief=None, text=TTLocalizer.PartyPlannerConfirmationAllOkTitle, textMayChange=True, pos=self.gui.find('**/title_locator').getPos(), scale=self.titleScale)
        pos = self.gui.find('**/step_07_close_text_locator').getPos()
        self.closePlannerButton = DirectButton(parent=page, relief=None, geom=(self.gui.find('**/close_up'), self.gui.find('**/close_down'), self.gui.find('**/close_rollover')), text=TTLocalizer.PartyPlannerClosePlanner, text_scale=0.055, text_pos=(pos[0], pos[2]), command=self.__acceptExit)
        return page

    def close(self):
        self.ignore('addPartyResponseReceived')
        self.ignore(localAvatar.uniqueName('moneyChange'))
        self.ignore(localAvatar.uniqueName('bankMoneyChange'))
        self.timeInputHourUpButton.destroy()
        self.timeInputHourDownButton.destroy()
        self.timeInputMinuteUpButton.destroy()
        self.timeInputMinuteDownButton.destroy()
        self.timeInputAmPmUpButton.destroy()
        self.timeInputAmPmDownButton.destroy()
        self.privateButton.destroy()
        self.publicButton.destroy()
        self.makePartyNowButton.destroy()
        self.checkAllButton.destroy()
        self.uncheckAllButton.destroy()
        self.elementBuyButton.destroy()
        self.nextThemeButton.destroy()
        self.prevThemeButton.destroy()
        self.inviteButton.destroy()
        self.closePlannerButton.destroy()
        self.ignore(self.okWithPartyGroundsLayoutEvent)
        if hasattr(self, 'okWithGroundsGui'):
            self.okWithGroundsGui.cleanup()
            del self.okWithGroundsGui
        if hasattr(self, 'frame') and not self.frame.isEmpty():
            messenger.send(self.doneEvent)
            self.hide()
            self.cleanup()
            self.friendList.removeAndDestroyAllItems()
            self.friendList.destroy()
            self.calendarGuiMonth.destroy()
            self.frame.destroy()
        self.partyPlannerHead.delete()
        self.partyPlannerHead.removeNode()
        self.clearNametag()
        self.partyEditor.request('Cleanup')
        self.partyEditor = None
        self.destroy()
        del self
        return

    def __handleComplete(self):
        self.inviteButton['state'] = DirectGuiGlobals.DISABLED
        self.prevButton['state'] = DirectGuiGlobals.DISABLED
        endTime = self.partyTime + self.partyDuration
        hostId = base.localAvatar.doId
        self.partyActivities = self.partyEditor.partyEditorGrid.getActivitiesOnGrid()
        decorations = self.partyEditor.partyEditorGrid.getDecorationsOnGrid()
        invitees = self.getInvitees()
        self.accept('addPartyResponseReceived', self.processAddPartyResponse)
        base.cr.partyManager.sendAddParty(hostId, self.partyTime.strftime('%Y-%m-%d %H:%M:%S'), endTime.strftime('%Y-%m-%d %H:%M:%S'), self.isPrivate, self.currentInvitationTheme, self.partyActivities, decorations, invitees)

    def getInvitees(self):
        invitees = []
        for friendBox in self.friendList['items']:
            if friendBox['indicatorValue']:
                invitees.append(friendBox.getPythonTag('id'))

        return invitees

    def processAddPartyResponse(self, hostId, errorCode):
        PartyPlanner.notify.debug('processAddPartyResponse : hostId=%d errorCode=%s' % (hostId, PartyGlobals.AddPartyErrorCode.getString(errorCode)))
        goingBackAllowed = False
        if errorCode == PartyGlobals.AddPartyErrorCode.AllOk:
            goingBackAllowed = False
            self.confirmTitleLabel['text'] = TTLocalizer.PartyPlannerConfirmationAllOkTitle
            if self.noFriends or len(self.getInvitees()) == 0:
                confirmRecapText = TTLocalizer.PartyPlannerConfirmationAllOkTextNoFriends
            else:
                confirmRecapText = TTLocalizer.PartyPlannerConfirmationAllOkText
        elif errorCode == PartyGlobals.AddPartyErrorCode.ValidationError:
            self.confirmTitleLabel['text'] = TTLocalizer.PartyPlannerConfirmationErrorTitle
            confirmRecapText = TTLocalizer.PartyPlannerConfirmationValidationErrorText
        elif errorCode == PartyGlobals.AddPartyErrorCode.DatabaseError:
            self.confirmTitleLabel['text'] = TTLocalizer.PartyPlannerConfirmationErrorTitle
            confirmRecapText = TTLocalizer.PartyPlannerConfirmationDatabaseErrorText
        elif errorCode == PartyGlobals.AddPartyErrorCode.TooManyHostedParties:
            goingBackAllowed = False
            self.confirmTitleLabel['text'] = TTLocalizer.PartyPlannerConfirmationErrorTitle
            confirmRecapText = TTLocalizer.PartyPlannerConfirmationTooManyText
        self.nametagGroup.setChat(confirmRecapText, CFSpeech)
        self.request('Farewell', goingBackAllowed)

    def __acceptExit(self):
        PartyPlanner.notify.debug('__acceptExit')
        if hasattr(self, 'frame'):
            self.hide()
            messenger.send(self.doneEvent)

    def __nextItem(self):
        messenger.send('wakeup')
        if self.state == 'PartyEditor' and self.okWithGroundsGui.doneStatus != 'ok':
            self.okWithGroundsGui.show()
            return
        if self.state == 'PartyEditor' and self.noFriends:
            self.request('Date')
            self.selectedCalendarGuiDay = None
            self.calendarGuiMonth.clearSelectedDay()
            return
        if self.state == 'Guests':
            self.selectedCalendarGuiDay = None
            self.calendarGuiMonth.clearSelectedDay()
        if self.state == 'Time':
            if self.partyTime < base.cr.toontownTimeManager.getCurServerDateTime():
                self.okChooseFutureTimeEvent = 'okChooseFutureTimeEvent'
                self.acceptOnce(self.okChooseFutureTimeEvent, self.okChooseFutureTime)
                self.chooseFutureTimeDialog = TTDialog.TTGlobalDialog(dialogName=self.uniqueName('chooseFutureTimeDialog'), doneEvent=self.okChooseFutureTimeEvent, message=TTLocalizer.PartyPlannerChooseFutureTime, style=TTDialog.Acknowledge)
                self.chooseFutureTimeDialog.show()
                return
        self.requestNext()
        return

    def okChooseFutureTime(self):
        if hasattr(self, 'chooseFutureTimeDialog'):
            self.chooseFutureTimeDialog.cleanup()
            del self.chooseFutureTimeDialog
        if hasattr(self, 'okChooseFutureTimeEvent'):
            self.ignore(self.okChooseFutureTimeEvent)

    def __prevItem(self):
        messenger.send('wakeup')
        if self.state == 'Date' and self.noFriends:
            self.request('PartyEditor')
            return
        if self.state == 'Invitation' and self.selectedCalendarGuiDay is None:
            self.request('Guests')
            return
        self.requestPrev()
        return

    def __moneyChange(self, newMoney):
        if hasattr(self, 'totalMoney'):
            self.totalMoney = base.localAvatar.getTotalMoney()
        if hasattr(self, 'beanBank'):
            self.beanBank['text'] = str(int(self.totalMoney))
