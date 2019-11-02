from pandac.PandaModules import Vec3, Vec4, Point3, TextNode, VBase4
from direct.gui.DirectGui import DGG, DirectFrame, DirectButton, DirectLabel, DirectScrolledList, DirectCheckButton
from direct.gui import DirectGuiGlobals
from direct.showbase import DirectObject
from direct.showbase import PythonUtil
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.toontowngui import TTDialog
from toontown.parties import PartyGlobals
from toontown.parties import PartyUtils

class PublicPartyGui(DirectFrame):
    notify = directNotify.newCategory('PublicPartyGui')

    def __init__(self, doneEvent):
        DirectFrame.__init__(self)
        self.doneEvent = doneEvent
        self.gui = loader.loadModel('phase_4/models/parties/publicPartyGUI')
        self.setPos(0.1, 0.0, 0.1)
        self.doneStatus = None
        self.activityIconsModel = loader.loadModel('phase_4/models/parties/eventSignIcons')
        self.normalFrameColor = Vec4(130 / 255.0, 174 / 255.0, 249 / 255.0, 1.0)
        self.selectedFrameColor = Vec4(1.0, 1.0, 0.0, 1.0)
        self.load()
        self.gui.removeNode()
        self.accept('stoppedAsleep', self._close)
        return

    def load(self):
        for backgroundName in ['background', 'parties_background', 'activities_background']:
            background = DirectFrame(parent=self, geom=self.gui.find('**/%s' % backgroundName), relief=None)

        self.titleLabel = DirectLabel(parent=self, relief=None, text=TTLocalizer.PartyGateTitle, pos=self.gui.find('**/title_locator').getPos(), scale=0.1)
        self.partyList, self.partyListLabel = self.createPartyListAndLabel('parties', 14)
        self.activityList, self.activityListLabel = self.createListAndLabel('activities', 1)
        pos = self.gui.find('**/startText_locator').getPos()
        self.partyStartButton = DirectButton(parent=self, relief=None, text=TTLocalizer.PartyGateGoToParty, text_align=TextNode.ACenter, text_scale=TTLocalizer.PPGpartyStartButton, text_pos=(pos[0], pos[2]), geom=(self.gui.find('**/startButton_up'),
         self.gui.find('**/startButton_down'),
         self.gui.find('**/startButton_rollover'),
         self.gui.find('**/startButton_inactive')), command=self._startParty)
        self.closeButton = DirectButton(parent=self, relief=None, geom=(self.gui.find('**/cancelButton_up'), self.gui.find('**/cancelButton_down'), self.gui.find('**/cancelButton_rollover')), command=self._close)
        instructionPos = (0, -0.9)
        if not self.gui.find('**/helpText_locator').isEmpty():
            tempPos = self.gui.find('**/helpText_locator').getPos()
            instructionPos = (tempPos.getX(), tempPos.getZ())
        self.instructionsLabel = DirectLabel(parent=self, relief=None, text=TTLocalizer.PartyGateInstructions, text_align=TextNode.ACenter, text_scale=TTLocalizer.PPGinstructionsLabel, text_pos=instructionPos)
        return

    def createListAndLabel(self, typeString, numItems):
        list = DirectScrolledList(parent=self, relief=None, incButton_image=(self.gui.find('**/%sButtonDown_up' % typeString),
         self.gui.find('**/%sButtonDown_down' % typeString),
         self.gui.find('**/%sButtonDown_rollover' % typeString),
         self.gui.find('**/%sButtonDown_inactive' % typeString)), incButton_relief=None, decButton_image=(self.gui.find('**/%sButtonUp_up' % typeString),
         self.gui.find('**/%sButtonUp_down' % typeString),
         self.gui.find('**/%sButtonUp_rollover' % typeString),
         self.gui.find('**/%sButtonUp_inactive' % typeString)), decButton_relief=None, itemFrame_pos=self.gui.find('**/%s_locator' % typeString).getPos(), itemFrame_relief=None, numItemsVisible=numItems, forceHeight=0.055)
        strings = {'activities': TTLocalizer.EventsPageHostingTabActivityListTitle,
         'parties': TTLocalizer.PartyGatePartiesListTitle}
        label = DirectLabel(parent=self, relief=None, text=strings[typeString], text_scale=0.06, pos=self.gui.find('**/%sText_locator' % typeString).getPos())
        return (list, label)

    def refresh(self, partyInfoTupleList):
        PublicPartyGui.notify.debug('refresh : partyInfoTupleList = %s' % partyInfoTupleList)
        self.selectedItem = None
        self.partyList.removeAndDestroyAllItems()
        self.activityList.removeAndDestroyAllItems()
        self.partyStartButton['state'] = DirectGuiGlobals.DISABLED
        sortedList = partyInfoTupleList[:]

        def cmp(left, right):
            if left[2] < right[2]:
                return -1
            elif left[2] == right[2]:
                if len(left[4]) < len(right[4]):
                    return -1
                elif len(left[4]) == len(right[4]):
                    return 0
                else:
                    return 1
            else:
                return 1

        sortedList.sort(cmp, reverse=True)
        indexToCut = -1
        for index, partyTuple in enumerate(sortedList):
            numberOfGuests = partyTuple[2]
            if numberOfGuests < PartyGlobals.MaxToonsAtAParty:
                indexToCut = index
                break

        if indexToCut > 0:
            sortedList = sortedList[indexToCut:] + sortedList[:indexToCut]
        for index, partyTuple in enumerate(sortedList):
            shardId = partyTuple[0]
            zoneId = partyTuple[1]
            numberOfGuests = partyTuple[2]
            hostName = partyTuple[3]
            activityIds = partyTuple[4]
            minLeft = partyTuple[5]
            item = DirectButton(relief=DGG.RIDGE, borderWidth=(0.01, 0.01), frameSize=(-0.01,
             0.45,
             -0.015,
             0.04), frameColor=self.normalFrameColor, text=hostName, text_align=TextNode.ALeft, text_bg=Vec4(0.0, 0.0, 0.0, 0.0), text_scale=0.045, command=self.partyClicked)
            otherInfoWidth = 0.08
            numActivities = len(activityIds)
            PartyUtils.truncateTextOfLabelBasedOnWidth(item, hostName, PartyGlobals.EventsPageGuestNameMaxWidth)
            num = DirectLabel(relief=DGG.RIDGE, borderWidth=(0.01, 0.01), frameSize=(0.0,
             otherInfoWidth,
             -0.015,
             0.04), frameColor=self.normalFrameColor, text='%d' % numberOfGuests, text_align=TextNode.ALeft, text_scale=0.045, text_pos=(0.01, 0, 0), pos=(0.45, 0.0, 0.0))
            num.reparentTo(item)
            item.numLabel = num
            actLabelPos = num.getPos()
            actLabelPos.setX(actLabelPos.getX() + otherInfoWidth)
            actLabel = DirectLabel(relief=DGG.RIDGE, borderWidth=(0.01, 0.01), frameSize=(0.0,
             otherInfoWidth,
             -0.015,
             0.04), frameColor=self.normalFrameColor, text='%d' % numActivities, text_align=TextNode.ALeft, text_scale=0.045, text_pos=(0.01, 0, 0), pos=actLabelPos)
            actLabel.reparentTo(item)
            item.actLabel = actLabel
            minLabelPos = actLabel.getPos()
            minLabelPos.setX(minLabelPos.getX() + otherInfoWidth)
            minLabel = DirectLabel(relief=DGG.RIDGE, borderWidth=(0.01, 0.01), frameSize=(0.0,
             otherInfoWidth,
             -0.015,
             0.04), frameColor=self.normalFrameColor, text='%d' % minLeft, text_align=TextNode.ALeft, text_scale=0.045, text_pos=(0.01, 0, 0), pos=minLabelPos)
            minLabel.reparentTo(item)
            item.minLabel = minLabel
            item['extraArgs'] = [item]
            item.setPythonTag('shardId', shardId)
            item.setPythonTag('zoneId', zoneId)
            item.setPythonTag('activityIds', activityIds)
            self.partyList.addItem(item)

        return

    def partyClicked(self, item):
        self.partyStartButton['state'] = DirectGuiGlobals.NORMAL
        if self.selectedItem is not None:
            self.selectedItem['state'] = DirectGuiGlobals.NORMAL
            self.selectedItem['frameColor'] = self.normalFrameColor
            numLabel = self.selectedItem.numLabel
            if not numLabel.isEmpty():
                numLabel['frameColor'] = self.normalFrameColor
            actLabel = self.selectedItem.actLabel
            if not actLabel.isEmpty():
                actLabel['frameColor'] = self.normalFrameColor
            minLabel = self.selectedItem.minLabel
            if not minLabel.isEmpty():
                minLabel['frameColor'] = self.normalFrameColor
        self.selectedItem = item
        self.selectedItem['state'] = DirectGuiGlobals.DISABLED
        self.selectedItem['frameColor'] = self.selectedFrameColor
        numLabel = self.selectedItem.numLabel
        if not numLabel.isEmpty():
            numLabel['frameColor'] = self.selectedFrameColor
        actLabel = self.selectedItem.actLabel
        if not actLabel.isEmpty():
            actLabel['frameColor'] = self.selectedFrameColor
        minLabel = self.selectedItem.minLabel
        if not minLabel.isEmpty():
            minLabel['frameColor'] = self.selectedFrameColor
        self.fillActivityList(item.getPythonTag('activityIds'))
        return

    def fillActivityList(self, activityIds):
        self.activityList.removeAndDestroyAllItems()
        sortedList = activityIds[:]
        sortedList.sort()
        lastActivityId = -1
        for activityId in sortedList:
            if activityId == lastActivityId:
                continue
            lastActivityId = activityId
            number = sortedList.count(activityId)
            text = TTLocalizer.PartyActivityNameDict[activityId]['generic']
            if number > 1:
                text += ' X %d' % number
            item = DirectLabel(relief=None, text=text, text_align=TextNode.ACenter, text_scale=0.05, text_pos=(0.0, -0.15), geom_scale=0.3, geom_pos=Vec3(0.0, 0.0, 0.07), geom=PartyUtils.getPartyActivityIcon(self.activityIconsModel, PartyGlobals.ActivityIds.getString(activityId)))
            self.activityList.addItem(item)

        return

    def _startParty(self):
        if self.selectedItem is None:
            self.partyStartButton['state'] = DirectGuiGlobals.DISABLED
            return
        self.doneStatus = (self.selectedItem.getPythonTag('shardId'), self.selectedItem.getPythonTag('zoneId'))
        messenger.send(self.doneEvent)
        return

    def _close(self):
        self.doneStatus = None
        messenger.send(self.doneEvent)
        return

    def destroy(self):
        self.activityIconsModel.removeNode()
        del self.activityIconsModel
        self.partyList.removeAndDestroyAllItems()
        try:
            for item in self.partyList['items']:
                item.actLabel = None
                item.numLabel = None
                item.minLabel = None

        except:
            pass

        self.activityList.removeAndDestroyAllItems()
        del self.partyList
        del self.activityList
        self.ignoreAll()
        DirectFrame.destroy(self)
        return

    def createPartyListAndLabel(self, typeString, numItems):
        list = DirectScrolledList(parent=self, relief=None, incButton_image=(self.gui.find('**/%sButtonDown_up' % typeString),
         self.gui.find('**/%sButtonDown_down' % typeString),
         self.gui.find('**/%sButtonDown_rollover' % typeString),
         self.gui.find('**/%sButtonDown_inactive' % typeString)), incButton_relief=None, decButton_image=(self.gui.find('**/%sButtonUp_up' % typeString),
         self.gui.find('**/%sButtonUp_down' % typeString),
         self.gui.find('**/%sButtonUp_rollover' % typeString),
         self.gui.find('**/%sButtonUp_inactive' % typeString)), decButton_relief=None, itemFrame_pos=self.gui.find('**/%s_locator' % typeString).getPos(), itemFrame_relief=None, numItemsVisible=numItems, forceHeight=0.055)
        strings = {'activities': TTLocalizer.EventsPageHostingTabActivityListTitle,
         'parties': TTLocalizer.PartyGatePartiesListTitle}
        hostPos = self.gui.find('**/%sText_locator' % typeString).getPos()
        label = DirectLabel(parent=self, text_align=TextNode.ALeft, relief=None, text=strings[typeString], text_scale=0.06, pos=hostPos)
        curPos = label.getPos()
        curPos.setX(curPos.getX() + 0.5)
        if not self.gui.find('**/partiesText_locator1').isEmpty():
            curPos = self.gui.find('**/partiesText_locator1').getPos()
        hpr = Point3(0, 0, -40)
        toonsLabel = DirectLabel(parent=self, text_align=TextNode.ALeft, relief=None, text=TTLocalizer.PartyGatesPartiesListToons, text_scale=TTLocalizer.PPGtoonsLabel, pos=curPos, hpr=hpr)
        curPos.setX(curPos.getX() + 0.1)
        if not self.gui.find('**/partiesText_locator2').isEmpty():
            curPos = self.gui.find('**/partiesText_locator2').getPos()
        activitiesLabel = DirectLabel(parent=self, text_align=TextNode.ALeft, relief=None, text=TTLocalizer.PartyGatesPartiesListActivities, text_scale=TTLocalizer.PPGactivitiesLabel, pos=curPos, hpr=hpr)
        curPos.setX(curPos.getX() + 0.1)
        if not self.gui.find('**/partiesText_locator3').isEmpty():
            curPos = self.gui.find('**/partiesText_locator3').getPos()
        minLeftLabel = DirectLabel(parent=self, text_align=TextNode.ALeft, relief=None, text=TTLocalizer.PartyGatesPartiesListMinLeft, text_scale=TTLocalizer.PPGminLeftLabel, pos=curPos, hpr=hpr)
        return (list, label)

    def stash(self):
        base.setCellsAvailable(base.bottomCells, 1)
        DirectFrame.stash(self)

    def unstash(self):
        base.setCellsAvailable(base.bottomCells, 0)
        DirectFrame.unstash(self)
