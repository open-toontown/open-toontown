from datetime import datetime
from direct.directnotify import DirectNotifyGlobal
from toontown.parties.PartyGlobals import InviteTheme
from toontown.parties.DecorBase import DecorBase
from toontown.parties.ActivityBase import ActivityBase

class PartyInfoBase:
    notify = DirectNotifyGlobal.directNotify.newCategory('PartyInfoBase')

    def __init__(self, partyId, hostId, startYear, startMonth, startDay, startHour, startMinute, endYear, endMonth, endDay, endHour, endMinute, isPrivate, inviteTheme, activityList, decors, status):
        self.partyId = partyId
        self.hostId = hostId
        self.startTime = datetime(startYear, startMonth, startDay, startHour, startMinute)
        self.endTime = datetime(endYear, endMonth, endDay, endHour, endMinute)
        self.isPrivate = isPrivate
        self.inviteTheme = inviteTheme
        self.activityList = []
        for oneItem in activityList:
            newActivity = ActivityBase(oneItem[0], oneItem[1], oneItem[2], oneItem[3])
            self.activityList.append(newActivity)

        self.decors = []
        for oneItem in decors:
            newDecor = DecorBase(oneItem[0], oneItem[1], oneItem[2], oneItem[3])
            self.decors.append(newDecor)

        self.status = status

    def getActivityIds(self):
        activities = []
        for activityBase in self.activityList:
            activities.append(activityBase.activityId)

        return activities

    def __str__(self):
        string = 'partyId=%d ' % self.partyId
        string += 'hostId=%d ' % self.hostId
        string += 'start=%s ' % self.startTime
        string += 'end=%s ' % self.endTime
        string += 'isPrivate=%s ' % self.isPrivate
        string += 'inviteTheme=%s ' % InviteTheme.getString(self.inviteTheme)
        string += 'activityList=%s ' % self.activityList
        string += 'decors=%s ' % self.decors
        string += 'status=%s' % self.status
        string += '\n'
        return string

    def __repr__(self):
        return self.__str__()


class PartyInfo(PartyInfoBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('PartyInfo')

    def __init__(self, partyId, hostId, startYear, startMonth, startDay, startHour, startMinute, endYear, endMonth, endDay, endHour, endMinute, isPrivate, inviteTheme, activityList, decors, status):
        PartyInfoBase.__init__(self, partyId, hostId, startYear, startMonth, startDay, startHour, startMinute, endYear, endMonth, endDay, endHour, endMinute, isPrivate, inviteTheme, activityList, decors, status)
        serverTzInfo = base.cr.toontownTimeManager.serverTimeZone
        self.startTime = self.startTime.replace(tzinfo=serverTzInfo)
        self.endTime = self.endTime.replace(tzinfo=serverTzInfo)


class PartyInfoAI(PartyInfoBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('PartyInfo')

    def __init__(self, partyId, hostId, startYear, startMonth, startDay, startHour, startMinute, endYear, endMonth, endDay, endHour, endMinute, isPrivate, inviteTheme, activityList, decors, status):
        PartyInfoBase.__init__(self, partyId, hostId, startYear, startMonth, startDay, startHour, startMinute, endYear, endMonth, endDay, endHour, endMinute, isPrivate, inviteTheme, activityList, decors, status)
        serverTzInfo = simbase.air.toontownTimeManager.serverTimeZone
        self.startTime = self.startTime.replace(tzinfo=serverTzInfo)
        self.endTime = self.endTime.replace(tzinfo=serverTzInfo)
