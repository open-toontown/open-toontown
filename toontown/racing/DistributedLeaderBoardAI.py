##########################################################################
# Module: DistributedLeaderBoardAI.py
# Purpose:      -determines what to display on the client side leaderboard
#               -handles subscriptions to lists
#               -handles timer to revolve leader board
#               -handles updating lists that that leaderboardmanagaer indicates have changed
# Date: 6/24/05
# Author: sabrina (sabrina@schellgames.com)
##########################################################################

from direct.distributed import DistributedObjectAI
from direct.directnotify import DirectNotifyGlobal
from toontown.racing.RaceGlobals import  *
from toontown.toonbase.TTLocalizer import *
import pickle

class DistributedLeaderBoardAI(DistributedObjectAI.DistributedObjectAI):
    """
    The leader board class handles the display of player rankings.

    Leader Board class was created to showcase race records in Toontown Kart racing


    Inside the Toontown race code, when a race is done someone has to check race scores
    decide if any of the latest scores is a new record for any of the types of leader lists.

    If the answer is yes, the pickled race list is updated and a message is sent which notifies any
    distributed leader boards as to which leader list has been updated. The dict of leader lists
    and the titles describing them is defined in TTLocalizer file.

    The distributed leader board then flags that id as needing actual update from the pickled leader
    list file. When the distributed leader board needs to display that list it loads up the
    new list and sends an updated message with the new list via sendupdate to the local leaderboard.

    This avoids a single leader board from loading from the pickle unnecessarily often as it waits
    till the information is actually needed to update it. Could result in double access to pickle
    files if more than one leader board is listening for it... perhaps when reading in an updated
    pickle list could also sned message with new list so that other server side leader boards
    can benefit from one leader board's work? not sure which would be more taxing.

    """

    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedLeaderBoardAI')

    def __init__(self, air, pName, zoneId, pSubscribeList=[], pos=(0, 0, 0), hpr=(0, 0, 0)):
        """
        Setup the Leader Board.
        """
        self.notify.debug("__init__: initialization of leaderboard AI: name=%s, Subscriptions=%s, pos=%s, hpr=%s"%(pName, pSubscribeList, pos, hpr))
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)
        self.name = pName

        #each subscription icludes: id : track title, period title, list of (time, name)
        self.subscriptionDict = {}
        #an ordered list to cycle through
        self.subscriptionList = []
        self.changedList = [] #list to store id's of updated lists
        #subscribe to all passed ids
        #an id consits of a tuple (TrackID, PeriodID)
        for id in pSubscribeList:
                self.subscribeTo(id)

        self.posHpr = (pos[0], pos[1], pos[2], hpr[0], hpr[1], hpr[2])
        self.zoneId = zoneId

        self.curIndex = 0 #the index into the subscriptionsDict indicating which list we're on
        self.start()

    def getName(self):
        return self.name

    def getPosHpr(self):
        """
        """
        return self.posHpr

    def getDisplay(self):
        '''
        '''
        return pickle.dumps(self.subscriptionDict[self.curIndex], 1)


    def sendNewDisplay(self):
        self.notify.debug("sendNewDisplay: sending updated lb info to client")
        self.sendUpdate("setDisplay", [pickle.dumps(self.subscriptionDict[self.subscriptionList[self.curIndex]], 1)])

    def start(self):
        '''
        Starts listen for message to cycle through the boards subscribed lists.
        Could make the listened for keyword a parameter if leaderboards on a different swap cycle

        params: pSeconds - how many seconds between cycling
        '''
        self.notify.debug("start: leaderboard cycling started on leaderboard %s"%(self.name))
        self.accept("GS_LeaderBoardSwap" + str(self.zoneId), self.__switchDisplayData)

    def stop(self):
        self.notify.debug("stop: leaderboard cycling stopped on leaderboard %s"%(self.name))
        self.ignore("GS_LeaderBoardSwap" + str(self.zoneId))

    def unsubscribeTo(self, pID):
        self.notify.debug("unsubscribeTo: removing subscription %s for LB %s"%(pID, self.name))
        #if this subscription exists, remove it
        self.subscriptionDict.pop(pID)
        self.subscriptionList.remove(pID)
        #self.ignore("UpdateRaceRecord_"+str(pID))
        self.ignore("UpdateRaceRecord")

    def subscribeTo(self, pID):
        '''
        Adds this score ID to the list of ones this leader board cycles through and follows updates of

        params: pID  - the id to listen for
        '''
        self.notify.debug("subscribeTo: adding subscription %s for LB %s"%(pID, self.name))
        #first check if we're already subscribed
        if pID in self.subscriptionList:
                return


        i = str(len(self.subscriptionList))
        self.subscriptionList.append(pID)
        self.flagForUpdate(pID)

        self.subscriptionDict[pID] = [KartRace_TrackNames[pID[0]], RecordPeriodStrings[pID[1]], []]
        #                               [(3.12, "Mizzenberry"), (3.12, "Princess Precious Flutterwink"), (3.12, "Mr. Loony Snapblooper"), (3.12, "Miss Pumpkin Floo"),
        #                               (3.12, "Frizzle"), (3.12, "King Quibble"), (3.12, "Left Loopwinger"), (3.12, "Super Silly Susan "),
        #                               (3.12, "Bingo Buffworks"), (3.12, "Mickey Mouse")])
        self.flagForUpdate(pID)

        self.accept("UpdateRaceRecord", self.flagForUpdate)

    def flagForUpdate(self, pID):
        '''
        Flag this score list to be updated if its not already.
        '''
        if pID not in self.changedList:
                self.changedList.append(pID)


    def __switchDisplayData(self):
        '''
        '''
        #check that there's actually something in subscriptions list
        if not self.subscriptionDict:
                return

        #figure out next list id
        self.curIndex = (self.curIndex + 1) % len(self.subscriptionList)

        curID = self.subscriptionList[self.curIndex]
        #see if this list has been changed
        if curID in self.changedList:
                #if yes, query for updates
                self.__updateScore(curID)
                #remove from changed list
                self.changedList.remove(curID)

        #now work on displaying scores
        #sendUpdate LeaderBoard display list of scores
        self.sendNewDisplay()

    def __updateScore(self, pID):
        #update score list with ID pID by querying from server
        #print str(self.subscriptionDict)
        #print str(self.subscriptionDict[pID][2])
        newRecords =  self.air.raceMgr.getRecords(pID[0], pID[1])

        #"edited": that is, we're not using raceType and racerNum at this moment... just forget those
        editedRecords = []

        for record in newRecords:
                editedRecords.append((record[0], record[3]))

        self.subscriptionDict[pID][2] = editedRecords

        #for testing- junk filler for records
        #[(3.12, "Mizzenberry"), (3.12, "Princess Precious Flutterwink"), (3.12, "Mr. Loony Snapblooper"), (3.12, "Miss Pumpkin Floo"),
        #(3.12, "Frizzle"), (3.12, "King Quibble"), (3.12, "Left Loopwinger"), (3.12, "Super Silly Susan "),
        #(3.12, "Bingo Buffworks"), (3.12, "Mickey Mouse")]

    def delete(self):
        self.notify.debug("delete: stopping distributedleaderboardAI %s" % (self.name))
        self.ignore("UpdateRaceRecord")
        self.stop()
        DistributedObjectAI.DistributedObjectAI.delete(self)
