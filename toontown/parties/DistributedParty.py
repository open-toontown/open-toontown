import random
import time
import datetime
from panda3d.core import Vec4, TextNode, CardMaker, NodePath
from direct.distributed import DistributedObject
from direct.gui.DirectGui import DirectLabel
from direct.gui import OnscreenText
from direct.interval.IntervalGlobal import *
from toontown.toonbase import ToontownGlobals
from toontown.parties.PartyInfo import PartyInfo
from toontown.toonbase import TTLocalizer
from toontown.toon import Toon
from toontown.parties import PartyGlobals
from toontown.parties.Decoration import Decoration
from . import PartyUtils

class DistributedParty(DistributedObject.DistributedObject):
    notify = directNotify.newCategory('DistributedParty')
    generatedEvent = 'distributedPartyGenerated'

    def __init__(self, cr):
        DistributedObject.DistributedObject.__init__(self, cr)
        self.partyDoneEvent = 'partyDone'
        self.load()
        self.avIdsAtParty = []
        base.distributedParty = self
        self.titleText = ''
        self.isPartyEnding = False

    def setPartyState(self, partyState):
        self.isPartyEnding = partyState
        messenger.send('partyStateChanged', [partyState])

    def getPartyState(self):
        return self.isPartyEnding

    def setPartyClockInfo(self, x, y, h):
        x = PartyUtils.convertDistanceFromPartyGrid(x, 0)
        y = PartyUtils.convertDistanceFromPartyGrid(y, 1)
        h = PartyUtils.convertDegreesFromPartyGrid(h)
        self.partyClockInfo = (x, y, h)
        self.loadPartyCountdownTimer()

    def setInviteeIds(self, inviteeIds):
        self.inviteeIds = inviteeIds

    def setPartyInfoTuple(self, partyInfoTuple):
        self.partyInfo = PartyInfo(*partyInfoTuple)
        self.loadDecorations()
        allActIds = [ x.activityId for x in self.partyInfo.activityList ]
        base.partyHasJukebox = PartyGlobals.ActivityIds.PartyJukebox in allActIds or PartyGlobals.ActivityIds.PartyJukebox40 in allActIds
        self.grid = [[False,
          False,
          False,
          False,
          False,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          False,
          False,
          False],
         [False,
          False,
          False,
          False,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          False,
          False,
          False],
         [False,
          False,
          False,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          False,
          False],
         [False,
          False,
          False,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          False,
          False],
         [False,
          False,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          False],
         [False,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True],
         [True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True],
         [True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True],
         [True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True],
         [True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True],
         [False,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True],
         [False,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          False,
          False,
          False,
          False],
         [False,
          False,
          False,
          False,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          False,
          False,
          False,
          False,
          False],
         [False,
          False,
          False,
          False,
          False,
          True,
          True,
          True,
          True,
          True,
          True,
          True,
          False,
          False,
          False,
          False,
          False,
          False],
         [False,
          False,
          False,
          False,
          False,
          False,
          True,
          True,
          True,
          True,
          True,
          False,
          False,
          False,
          False,
          False,
          False,
          False]]

        def fillGrid(x, y, size):
            for i in range(-size[1] // 2 + 1, size[1] // 2 + 1):
                for j in range(-size[0] // 2 + 1, size[0] // 2 + 1):
                    self.grid[i + y][j + x] = False

        for activityBase in self.partyInfo.activityList:
            fillGrid(activityBase.x, activityBase.y, PartyGlobals.ActivityInformationDict[activityBase.activityId]['gridsize'])

        for decorBase in self.partyInfo.decors:
            fillGrid(decorBase.x, decorBase.y, PartyGlobals.DecorationInformationDict[decorBase.decorId]['gridsize'])

        self.loadGrass()

    def setPartyStartedTime(self, startedTime):
        stime = time.strptime(startedTime, '%Y-%m-%d %H:%M:%S')
        self.partyStartedTime = datetime.datetime(year=stime.tm_year, month=stime.tm_mon, day=stime.tm_mday, hour=stime.tm_hour, minute=stime.tm_min, second=stime.tm_sec, tzinfo=base.cr.toontownTimeManager.getCurServerDateTime().tzinfo)

    def disable(self):
        self.notify.debug('disable')
        DistributedObject.DistributedObject.disable(self)
        base.localAvatar.chatMgr.chatInputSpeedChat.removeInsidePartiesMenu()

    def delete(self):
        self.notify.debug('delete')
        self.unload()
        if hasattr(base, 'distributedParty'):
            del base.distributedParty
        DistributedObject.DistributedObject.delete(self)

    def load(self):
        Toon.loadMinigameAnims()
        self.defaultSignModel = loader.loadModel('phase_13/models/parties/eventSign')
        self.activityIconsModel = loader.loadModel('phase_4/models/parties/eventSignIcons')
        model = loader.loadModel('phase_4/models/parties/partyStickerbook')
        self.partyHat = model.find('**/Stickerbook_PartyIcon')
        self.partyHat.setPos(0.0, 0.1, 2.5)
        self.partyHat.setHpr(0.0, 0.0, -50.0)
        self.partyHat.setScale(4.0)
        self.partyHat.setBillboardAxis()
        self.partyHat.reparentTo(hidden)
        model.removeNode()
        self.defaultLeverModel = loader.loadModel('phase_13/models/parties/partyLeverBase')
        self.defaultStickModel = loader.loadModel('phase_13/models/parties/partyLeverStick')

    def loadGrass(self):
        self.grassRoot = NodePath('GrassRoot')
        self.grassRoot.reparentTo(base.cr.playGame.hood.loader.geom)
        grass = loader.loadModel('phase_13/models/parties/grass')
        clearPositions = self.getClearSquarePositions()
        numTufts = min(len(clearPositions) * 3, PartyGlobals.TuftsOfGrass)
        for i in range(numTufts):
            g = grass.copyTo(self.grassRoot)
            pos = random.choice(clearPositions)
            g.setPos(pos[0] + random.randint(-8, 8), pos[1] + random.randint(-8, 8), 0.0)

    def loadDecorations(self):
        self.decorationsList = []
        for decorBase in self.partyInfo.decors:
            self.decorationsList.append(Decoration(PartyGlobals.DecorationIds.getString(decorBase.decorId), PartyUtils.convertDistanceFromPartyGrid(decorBase.x, 0), PartyUtils.convertDistanceFromPartyGrid(decorBase.y, 1), PartyUtils.convertDegreesFromPartyGrid(decorBase.h)))

    def unload(self):
        if hasattr(self, 'decorationsList') and self.decorationsList:
            for decor in self.decorationsList:
                decor.unload()

            del self.decorationsList
        self.stopPartyClock()
        self.grassRoot.removeNode()
        del self.grassRoot
        if hasattr(self, 'testGrid'):
            self.testGrid.removeNode()
            del self.testGrid
        self.ignoreAll()
        Toon.unloadMinigameAnims()
        self.partyHat.removeNode()
        del self.partyHat
        if hasattr(base, 'partyHasJukebox'):
            del base.partyHasJukebox

    def announceGenerate(self):
        DistributedObject.DistributedObject.announceGenerate(self)
        self.sendUpdate('avIdEnteredParty', [base.localAvatar.doId])
        globalClock.syncFrameTime()
        self.startPartyClock()
        base.localAvatar.chatMgr.chatInputSpeedChat.addInsidePartiesMenu()
        self.spawnTitleText()
        messenger.send(self.generatedEvent)
        if config.GetBool('show-debug-party-grid', 0):
            self.testGrid = NodePath('test_grid')
            self.testGrid.reparentTo(base.cr.playGame.hood.loader.geom)
            for i in range(len(self.grid)):
                for j in range(len(self.grid[i])):
                    cm = CardMaker('gridsquare')
                    np = NodePath(cm.generate())
                    np.setScale(12)
                    np.setP(-90.0)
                    np.setPos(PartyUtils.convertDistanceFromPartyGrid(j, 0) - 6.0, PartyUtils.convertDistanceFromPartyGrid(i, 1) - 6.0, 0.1)
                    np.reparentTo(self.testGrid)
                    if self.grid[i][j]:
                        np.setColorScale(0.0, 1.0, 0.0, 1.0)
                    else:
                        np.setColorScale(1.0, 0.0, 0.0, 1.0)

    def getClearSquarePos(self):
        clearPositions = self.getClearSquarePositions()
        if len(clearPositions) == 0:
            raise Exception('Party %s has no empty grid squares.' % self.doId)
        return random.choice(clearPositions)

    def getClearSquarePositions(self):
        clearPositions = []
        for y in range(len(self.grid)):
            for x in range(len(self.grid[0])):
                if self.grid[y][x]:
                    pos = (PartyUtils.convertDistanceFromPartyGrid(x, 0), PartyUtils.convertDistanceFromPartyGrid(y, 1), 0.1)
                    clearPositions.append(pos)

        return clearPositions

    def startPartyClock(self):
        self.partyClockModel.reparentTo(base.cr.playGame.hood.loader.geom)
        curServerTime = base.cr.toontownTimeManager.getCurServerDateTime()
        timePartyWillEnd = self.partyStartedTime + datetime.timedelta(hours=PartyGlobals.DefaultPartyDuration)
        timeLeftInParty = timePartyWillEnd - curServerTime
        if curServerTime < timePartyWillEnd:
            self.secondsLeftInParty = timeLeftInParty.seconds
        else:
            self.secondsLeftInParty = 0
        taskMgr.doMethodLater(0.5, self.partyClockTask, 'UpdatePartyClock')
        self.partyClockSignFront = self.partyClockModel.find('**/signFrontText_locator')
        self.partyClockSignBack = self.partyClockModel.find('**/signBackText_locator')
        self.attachHostNameToSign(self.partyClockSignFront)
        self.attachHostNameToSign(self.partyClockSignBack)

    def attachHostNameToSign(self, locator):
        if self.hostName == '':
            return
        nameText = TextNode('nameText')
        nameText.setCardAsMargin(0.1, 0.1, 0.1, 0.1)
        nameText.setCardDecal(True)
        nameText.setCardColor(1.0, 1.0, 1.0, 0.0)
        r = 232.0 / 255.0
        g = 169.0 / 255.0
        b = 23.0 / 255.0
        nameText.setTextColor(r, g, b, 1)
        nameText.setAlign(nameText.ACenter)
        nameText.setFont(ToontownGlobals.getBuildingNametagFont())
        nameText.setShadowColor(0, 0, 0, 1)
        nameText.setBin('fixed')
        if TTLocalizer.BuildingNametagShadow:
            nameText.setShadow(*TTLocalizer.BuildingNametagShadow)
        nameWordWrap = 11.0
        nameText.setWordwrap(nameWordWrap)
        scaleMult = 0.48
        houseName = self.hostName
        nameText.setText(houseName)
        textWidth = nameText.getWidth()
        xScale = 1.0 * scaleMult
        if textWidth > nameWordWrap:
            xScale = nameWordWrap / textWidth * scaleMult
        sign_origin = locator
        namePlate = sign_origin.attachNewNode(nameText)
        namePlate.setDepthWrite(0)
        namePlate.setPos(0, 0, 0)
        namePlate.setScale(xScale)

    def stopPartyClock(self):
        self.partyClockModel.removeNode()
        taskMgr.remove('UpdatePartyClock')

    def partyClockTask(self, task):
        self.secondsLeftInParty -= 0.5
        if self.secondsLeftInParty < 0:
            self.frontTimer['minute']['text'] = '--'
            self.backTimer['minute']['text'] = '--'
            self.frontTimer['second']['text'] = '--'
            self.backTimer['second']['text'] = '--'
            return
        if self.frontTimer['colon'].isStashed():
            self.frontTimer['colon'].unstash()
            self.backTimer['colon'].unstash()
        else:
            self.frontTimer['colon'].stash()
            self.backTimer['colon'].stash()
        minutesLeft = int(int(self.secondsLeftInParty / 60) % 60)
        if minutesLeft < 10:
            minutesLeft = '0%d' % minutesLeft
        else:
            minutesLeft = '%d' % minutesLeft
        secondsLeft = int(self.secondsLeftInParty % 60)
        if secondsLeft < 10:
            secondsLeft = '0%d' % secondsLeft
        else:
            secondsLeft = '%d' % secondsLeft
        self.frontTimer['minute']['text'] = minutesLeft
        self.backTimer['minute']['text'] = minutesLeft
        self.frontTimer['second']['text'] = secondsLeft
        self.backTimer['second']['text'] = secondsLeft
        taskMgr.doMethodLater(0.5, self.partyClockTask, 'UpdatePartyClock')
        if self.secondsLeftInParty != int(self.secondsLeftInParty):
            self.partyClockModel.find('**/middleRotateFront_grp').setR(-6.0 * (self.secondsLeftInParty % 60))
            self.partyClockModel.find('**/middleRotateBack_grp').setR(6.0 * (self.secondsLeftInParty % 60))

    def getAvIdsAtParty(self):
        return self.avIdsAtParty

    def setAvIdsAtParty(self, avIdsAtParty):
        self.avIdsAtParty = avIdsAtParty

    def loadPartyCountdownTimer(self):
        self.partyClockModel = loader.loadModel('phase_13/models/parties/partyClock')
        self.partyClockModel.setPos(self.partyClockInfo[0], self.partyClockInfo[1], 0.0)
        self.partyClockModel.setH(self.partyClockInfo[2])
        self.partyClockModel.reparentTo(base.cr.playGame.hood.loader.geom)
        self.partyClockModel.find('**/frontText_locator').setY(-1.1)
        self.partyClockModel.find('**/backText_locator').setY(0.633)
        self.frontTimer = self.getTimer(self.partyClockModel.find('**/frontText_locator'))
        base.frontTimerLoc = self.partyClockModel.find('**/frontText_locator')
        base.backTimerLoc = self.partyClockModel.find('**/backText_locator')
        self.backTimer = self.getTimer(self.partyClockModel.find('**/backText_locator'))
        self.partyClockModel.stash()

    def getTimer(self, parent):
        timeFont = ToontownGlobals.getMinnieFont()
        timer = {}
        timer['minute'] = DirectLabel(parent=parent, pos=TTLocalizer.DPtimerMinutePos, relief=None, text='59', text_align=TextNode.ACenter, text_font=timeFont, text_fg=(0.7, 0.3, 0.3, 1.0), scale=TTLocalizer.DPtimerMinute)
        timer['colon'] = DirectLabel(parent=parent, pos=TTLocalizer.DPtimerColonPos, relief=None, text=':', text_align=TextNode.ACenter, text_font=timeFont, text_fg=(0.7, 0.3, 0.3, 1.0), scale=TTLocalizer.DPtimerColon)
        timer['second'] = DirectLabel(parent=parent, relief=None, pos=TTLocalizer.DPtimerSecondPos, text='14', text_align=TextNode.ACenter, text_font=timeFont, text_fg=(0.7, 0.3, 0.3, 1.0), scale=TTLocalizer.DPtimerSecond)
        timer['textLabel'] = DirectLabel(parent=parent, relief=None, pos=(0.0, 0.0, 1.15), text=TTLocalizer.PartyCountdownClockText, text_font=timeFont, text_fg=(0.7, 0.3, 0.3, 1.0), scale=TTLocalizer.DPtimerTextLabel)
        return timer

    def setHostName(self, hostName):
        self.hostName = hostName
        if hasattr(self, 'partyClockSignFront'):
            self.attachHostNameToSign(self.partyClockSignFront)
        if hasattr(self, 'partyClockSignBack'):
            self.attachHostNameToSign(self.partyClockSignBack)

    def spawnTitleText(self):
        if not self.hostName:
            return
        partyText = TTLocalizer.PartyTitleText % TTLocalizer.GetPossesive(self.hostName)
        self.doSpawnTitleText(partyText)

    def doSpawnTitleText(self, text):
        self.titleColor = (1.0, 0.5, 0.4, 1.0)
        self.titleText = OnscreenText.OnscreenText(text, fg=self.titleColor, font=ToontownGlobals.getSignFont(), pos=(0, -0.5), scale=0.16, drawOrder=0, mayChange=1, wordwrap=16)
        self.titleText.setText(text)
        self.titleText.show()
        self.titleText.setColor(Vec4(*self.titleColor))
        self.titleText.clearColorScale()
        self.titleText.setFg(self.titleColor)
        seq = Sequence(Wait(0.1), Wait(6.0), self.titleText.colorScaleInterval(0.5, Vec4(1.0, 1.0, 1.0, 0.0)), Func(self.hideTitleText))
        seq.start()

    def hideTitleText(self):
        if self.titleText:
            self.titleText.hide()
