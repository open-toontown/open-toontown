from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from otp.otpbase import OTPTimer
from toontown.toonbase import TTLocalizer
from toontown.racing import KartShopGlobals
from toontown.toonbase.ToonBaseGlobal import *
from pandac.PandaModules import *
from toontown.toonbase.ToontownGlobals import *
import random
import pickle

class DistributedLeaderBoard(DistributedObject.DistributedObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('DisributedLeaderBoard')

    def __init__(self, cr):
        self.notify.debug('__init__: initialization of local leaderboard')
        DistributedObject.DistributedObject.__init__(self, cr)
        self.corner = 0
        self.length = 0
        self.width = 0
        self.updateCount = 0
        self.board = None
        self.surface = None
        return

    def generateInit(self):
        DistributedObject.DistributedObject.generateInit(self)
        self.board = NodePath(self.uniqueName('LeaderBoard'))

    def generate(self):
        DistributedObject.DistributedObject.generate(self)
        self.buildListParts()

    def announceGenerate(self):
        DistributedObject.DistributedObject.announceGenerate(self)
        self.board.reparentTo(render)
        self.accept('decorator-holiday-%d-ending' % ToontownGlobals.CRASHED_LEADERBOARD, self.showLists)
        self.accept('decorator-holiday-%d-starting' % ToontownGlobals.CRASHED_LEADERBOARD, self.hideLists)
        newsManager = base.cr.newsManager
        if newsManager:
            if ToontownGlobals.CRASHED_LEADERBOARD in newsManager.holidayIdList:
                self.hideLists()

    def showLists(self):
        self.board.show()

    def hideLists(self):
        self.board.hide()

    def setPosHpr(self, x, y, z, h, p, r):
        self.surface.setPosHpr(x, y, z, h, p, r)

    def setDisplay(self, pData):
        self.notify.debug('setDisplay: changing leaderboard text on local side')
        trackName, recordTitle, scores = pickle.loads(pData)
        self.display(trackName, recordTitle, scores)

    def buildListParts(self):
        self.surface = self.board.attachNewNode('surface')
        z = 7.7
        dz = 0.4
        x = -3.7
        row, trackName = self.buildTrackRow()
        self.trackNameNode = trackName
        row.reparentTo(self.surface)
        row.setPos(0, 1.6, z)
        z = 7.3
        row, self.titleTextNode = self.buildTitleRow()
        row.reparentTo(self.surface)
        row.setPos(0, 1.6, z)
        zListTop = 6.9
        z = zListTop
        self.nameTextNodes = []
        self.timeTextNodes = []
        for i in range(10):
            row, nameText, timeText, placeText = self.buildLeaderRow()
            self.nameTextNodes.append(nameText)
            placeText.setText(str(len(self.nameTextNodes)) + '.')
            self.timeTextNodes.append(timeText)
            row.reparentTo(self.surface)
            if len(self.nameTextNodes) == 6:
                z = zListTop
                x = 0.35
            row.setX(x)
            row.setZ(z)
            row.setY(1.6)
            z -= dz

        self.surface.flattenLight()

    def display(self, pTrackTitle = 'Track Title', pPeriodTitle = 'Period Title', pLeaderList = []):
        self.titleTextNode.setText(pPeriodTitle)
        self.trackNameNode.setText(pTrackTitle)
        self.updateCount += 1
        for i in range(10):
            if i > len(pLeaderList):
                self.nameTextNodes[i].setText('-')
                self.timeTextNodes[i].setText('-')
            else:
                name = pLeaderList[i][1]
                time = pLeaderList[i][0]
                secs, hundredths = divmod(time, 1)
                min, sec = divmod(secs, 60)
                self.nameTextNodes[i].setText(name[:22])
                self.timeTextNodes[i].setText('%02d:%02d:%02d' % (min, sec, hundredths * 100))

    def buildTitleRow(self):
        row = hidden.attachNewNode('TitleRow')
        nameText = TextNode('titleRow')
        nameText.setFont(ToontownGlobals.getSignFont())
        nameText.setAlign(TextNode.ACenter)
        nameText.setTextColor(0.3, 0.75, 0.6, 1)
        nameText.setText('Score Title')
        namePath = row.attachNewNode(nameText)
        namePath.setScale(TTLocalizer.DLBbuildTitleRow)
        namePath.setDepthWrite(0)
        return (row, nameText)

    def buildTrackRow(self):
        row = hidden.attachNewNode('trackRow')
        nameText = TextNode('trackRow')
        nameText.setFont(ToontownGlobals.getSignFont())
        nameText.setAlign(TextNode.ACenter)
        nameText.setTextColor(0.5, 0.75, 0.7, 1)
        nameText.setText('Track Title')
        namePath = row.attachNewNode(nameText)
        namePath.setScale(0.55)
        namePath.setDepthWrite(0)
        return (row, nameText)

    def buildLeaderRow(self):
        row = hidden.attachNewNode('leaderRow')
        nameText = TextNode('nameText')
        nameText.setFont(ToontownGlobals.getToonFont())
        nameText.setAlign(TextNode.ALeft)
        nameText.setTextColor(0.125, 0, 0.5, 1)
        nameText.setText('-')
        namePath = row.attachNewNode(nameText)
        namePath.setPos(1.1, 0, 0)
        namePath.setScale(0.23)
        namePath.setDepthWrite(0)
        timeText = TextNode('timeText')
        timeText.setFont(ToontownGlobals.getToonFont())
        timeText.setAlign(TextNode.ARight)
        timeText.setTextColor(0, 0, 0, 1)
        timeText.setText('-')
        timePath = row.attachNewNode(timeText)
        timePath.setPos(1.0, 0, 0)
        timePath.setScale(0.23)
        timePath.setDepthWrite(0)
        placeText = TextNode('placeText')
        placeText.setFont(ToontownGlobals.getSignFont())
        placeText.setAlign(TextNode.ARight)
        placeText.setTextColor(1, 1, 0.1, 1)
        placeText.setText('-')
        placePath = row.attachNewNode(placeText)
        placePath.setPos(-0.1, 0, -0.05)
        placePath.setScale(0.3)
        placePath.setDepthWrite(0)
        return (row,
         nameText,
         timeText,
         placeText)

    def delete(self):
        self.notify.debug('delete: deleting local leaderboard')
        self.ignoreAll()
        self.board.removeNode()
        DistributedObject.DistributedObject.delete(self)
