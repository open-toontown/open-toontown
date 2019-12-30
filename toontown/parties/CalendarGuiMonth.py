import calendar
from datetime import timedelta, datetime
from pandac.PandaModules import Vec4, TextNode
from direct.gui.DirectGui import DirectFrame, DirectLabel, DirectButton, DirectScrolledList, DGG
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals
from toontown.parties.CalendarGuiDay import CalendarGuiDay

class CalendarGuiMonth(DirectFrame):
    notify = directNotify.newCategory('CalendarGuiMonth')

    def __init__(self, parent, startingDateTime, scale = 1.0, pos = (0, 0, -0.1), dayClickCallback = None, onlyFutureDaysClickable = False, onlyFutureMonthsClickable = False):
        self.startDate = startingDateTime
        self.curDate = startingDateTime
        self.dayClickCallback = dayClickCallback
        self.onlyFutureDaysClickable = onlyFutureDaysClickable
        self.onlyFutureMonthsClickable = onlyFutureMonthsClickable
        if self.onlyFutureDaysClickable:
            self.onlyFutureMonthsClickable = True
        DirectFrame.__init__(self, parent=parent, scale=scale, pos=pos)
        self.showMarkers = base.config.GetBool('show-calendar-markers', 0)
        self.load()
        self.createGuiObjects()
        self.lastSelectedDate = None
        self.accept('clickedOnDay', self.clickedOnDay)
        return

    def createDummyLocators(self):
        self.monthLocator = self.attachNewNode('monthLocator')
        self.monthLocator.setZ(0.6)
        self.weekDayLocators = []
        for i in range(7):
            self.weekDayLocators.append(self.attachNewNode('weekDayLocator-%d' % i))
            self.weekDayLocators[i].setZ(0.5)
            self.weekDayLocators[i].setX(i * 0.24 + -0.75)

        dayTopLeftX = -0.8
        dayTopLeftZ = 0.4
        self.dayLocators = []
        for row in range(6):
            oneWeek = []
            for col in range(7):
                newDayLoc = self.attachNewNode('dayLocator-row-%d-col-%d' % (row, col))
                newDayLoc.setX(col * 0.24 + dayTopLeftX)
                newDayLoc.setZ(row * -0.18 + dayTopLeftZ)
                oneWeek.append(newDayLoc)

            self.dayLocators.append(oneWeek)

        self.monthLeftLocator = self.attachNewNode('monthLeft')
        self.monthLeftLocator.setPos(-0.3, 0, 0.65)
        self.monthRightLocator = self.attachNewNode('monthRight')
        self.monthRightLocator.setPos(0.3, 0, 0.65)

    def attachMarker(self, parent, scale = 0.01, color = (1, 0, 0)):
        if self.showMarkers:
            marker = loader.loadModel('phase_3/models/misc/sphere')
            marker.reparentTo(parent)
            marker.setScale(scale)
            marker.setColor(*color)

    def load(self):
        monthAsset = loader.loadModel('phase_4/models/parties/tt_m_gui_sbk_calendar')
        monthAsset.reparentTo(self)
        self.monthLocator = self.find('**/locator_month/locator_month')
        self.attachMarker(self.monthLocator)
        self.weekDayLocators = []
        for weekday in ('sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'):
            weekDayLoc = self.find('**/loc_%s' % weekday)
            self.weekDayLocators.append(weekDayLoc)
            self.attachMarker(weekDayLoc)

        self.dayLocators = []
        for row in range(6):
            oneWeek = []
            for col in range(7):
                newDayLoc = self.find('**/loc_box_%s_%s' % (row, col))
                oneWeek.append(newDayLoc)

            self.dayLocators.append(oneWeek)

        self.monthLeftLocator = self.find('**/locator_month_arrowL')
        self.monthRightLocator = self.find('**/locator_month_arrowR')
        self.filterLocator = self.find('**/locator_filter')
        self.filterLocatorArrowUp = self.find('**/locator_filter_arrowTop')
        self.filterLocatorArrowDown = self.find('**/locator_filter_arrowBottom')
        self.yearLocator = self.attachNewNode('yearLocator')
        self.yearLocator.setPos(self.monthLocator, 0, 0, -0.03)

    def createGuiObjects(self):
        self.monthLabel = DirectLabel(parent=self.monthLocator, relief=None, text=TTLocalizer.Months[self.startDate.month], text_scale=0.075, text_font=ToontownGlobals.getMinnieFont(), text_fg=(40 / 255.0,
         140 / 255.0,
         246 / 255.0,
         1.0))
        self.yearLabel = DirectLabel(parent=self.yearLocator, relief=None, text=str(self.startDate.year), text_scale=0.03, text_font=ToontownGlobals.getMinnieFont(), text_fg=(140 / 255.0,
         140 / 255.0,
         246 / 255.0,
         1.0))
        self.weekdayLabels = []
        for posIndex in range(7):
            adjustedNameIndex = (posIndex - 1) % 7
            self.weekdayLabels.append(DirectLabel(parent=self.weekDayLocators[posIndex], relief=None, text=TTLocalizer.DayNamesAbbrev[adjustedNameIndex], text_font=ToontownGlobals.getInterfaceFont(), text_fg=(255 / 255.0,
             146 / 255.0,
             113 / 255.0,
             1.0), text_scale=0.05))

        self.createGuiDays()
        arrowUp = self.find('**/month_arrowR_up')
        arrowDown = self.find('**/month_arrowR_down')
        arrowHover = self.find('**/month_arrowR_hover')
        self.monthLeftArrow = DirectButton(parent=self.monthLeftLocator, relief=None, image=(arrowUp,
         arrowDown,
         arrowHover,
         arrowUp), image3_color=Vec4(1, 1, 1, 0.5), scale=(-1.0, 1.0, 1.0), command=self.__doMonthLeft)
        if self.onlyFutureMonthsClickable:
            self.monthLeftArrow.hide()
        self.monthRightArrow = DirectButton(parent=self.monthRightLocator, relief=None, image=(arrowUp,
         arrowDown,
         arrowHover,
         arrowUp), image3_color=Vec4(1, 1, 1, 0.5), command=self.__doMonthRight)

        def makeLabel(itemName, itemNum, *extraArgs):
            return DirectLabel(text=itemName, frameColor=(0, 0, 0, 0), text_scale=0.04)

        gui = loader.loadModel('phase_4/models/parties/tt_m_gui_sbk_calendar_box')
        arrowUp = gui.find('**/downScroll_up')
        arrowDown = gui.find('**/downScroll_down')
        arrowHover = gui.find('**/downScroll_hover')
        filterLocatorUpPos = self.filterLocatorArrowUp.getPos(self.filterLocator)
        filterLocatorDownPos = self.filterLocatorArrowDown.getPos(self.filterLocator)
        self.filterList = DirectScrolledList(parent=self.filterLocator, relief=None, pos=(0, 0, 0), image=None, text_scale=0.025, incButton_image=(arrowUp,
         arrowDown,
         arrowHover,
         arrowUp), incButton_relief=None, incButton_pos=filterLocatorDownPos, incButton_image3_color=Vec4(1, 1, 1, 0.2), incButtonCallback=self.filterChanged, decButton_image=(arrowUp,
         arrowDown,
         arrowHover,
         arrowUp), decButton_relief=None, decButton_pos=filterLocatorUpPos, decButton_scale=(1, 1, -1), decButton_image3_color=Vec4(1, 1, 1, 0.2), decButtonCallback=self.filterChanged, numItemsVisible=1, itemMakeFunction=makeLabel, items=[TTLocalizer.CalendarShowAll, TTLocalizer.CalendarShowOnlyHolidays, TTLocalizer.CalendarShowOnlyParties], itemFrame_frameSize=(-.2, 0.2, -.02, 0.05), itemFrame_frameColor=(0, 0, 0, 0))
        gui.removeNode()
        return

    def getTopLeftDate(self):
        firstOfTheMonth = self.curDate.replace(day=1)
        daysAwayFromSunday = (firstOfTheMonth.weekday() - 6) % 7
        topLeftDate = firstOfTheMonth + timedelta(days=-daysAwayFromSunday)
        return topLeftDate

    def createGuiDays(self):
        topLeftDate = self.getTopLeftDate()
        curDate = topLeftDate
        self.guiDays = []
        for row in self.dayLocators:
            for oneLocator in row:
                self.guiDays.append(CalendarGuiDay(oneLocator, curDate, self.curDate, self.dayClickCallback, self.onlyFutureDaysClickable))
                curDate += timedelta(days=1)

    def changeDateForGuiDays(self):
        topLeftDate = self.getTopLeftDate()
        guiDayDate = topLeftDate
        for guiDay in self.guiDays:
            guiDay.changeDate(self.curDate, guiDayDate)
            guiDayDate += timedelta(days=1)

    def changeMonth(self, monthChange):
        if monthChange != 0:
            newMonth = self.curDate.month + monthChange
            newYear = self.curDate.year
            while newMonth > 12:
                newYear += 1
                newMonth -= 12

            while newMonth < 1:
                if newYear - 1 > 1899:
                    newMonth += 12
                    newYear -= 1
                else:
                    newMonth += 1

            self.curDate = datetime(newYear, newMonth, 1, self.curDate.time().hour, self.curDate.time().minute, self.curDate.time().second, self.curDate.time().microsecond, self.curDate.tzinfo)
        self.monthLabel['text'] = (TTLocalizer.Months[self.curDate.month],)
        self.yearLabel['text'] = (str(self.curDate.year),)
        startTime = globalClock.getRealTime()
        self.changeDateForGuiDays()
        endTime = globalClock.getRealTime()
        self.notify.debug('changeDate took %f seconds' % (endTime - startTime))
        self.updateSelectedDate()
        if monthChange != 0:
            if self.onlyFutureMonthsClickable and newMonth == self.startDate.month and newYear == self.startDate.year:
                self.monthLeftArrow.hide()

    def __doMonthLeft(self):
        self.changeMonth(-1)

    def __doMonthRight(self):
        self.monthLeftArrow.show()
        self.changeMonth(1)

    def destroy(self):
        self.ignoreAll()
        self.dayClickCallback = None
        self.monthLeftArrow.destroy()
        self.monthRightArrow.destroy()
        for day in self.guiDays:
            if day is not None:
                day.destroy()
            day = None

        self.filterList.destroy()
        DirectFrame.destroy(self)
        return

    def clickedOnDay(self, dayDate):
        self.lastSelectedDate = dayDate
        self.updateSelectedDate()

    def updateSelectedDate(self):
        if self.lastSelectedDate:
            for oneGuiDay in self.guiDays:
                if oneGuiDay.myDate.date() == self.lastSelectedDate:
                    oneGuiDay.updateSelected(True)
                else:
                    oneGuiDay.updateSelected(False)

    def clearSelectedDay(self):
        for oneGuiDay in self.guiDays:
            oneGuiDay.updateSelected(False)

    def filterChanged(self):
        newFilter = self.filterList.getSelectedIndex()
        for guiDay in self.guiDays:
            guiDay.changeFilter(newFilter)
