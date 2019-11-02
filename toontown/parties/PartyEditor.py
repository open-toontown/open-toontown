import time
from sets import Set
from pandac.PandaModules import Vec3, Vec4, Point3, TextNode, VBase4
from direct.gui.DirectGui import DirectFrame, DirectButton, DirectLabel, DirectScrolledList, DirectCheckButton
from direct.gui import DirectGuiGlobals
from direct.showbase.DirectObject import DirectObject
from direct.showbase import PythonUtil
from direct.fsm.FSM import FSM
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.parties import PartyGlobals
from toontown.parties.PartyInfo import PartyInfo
from toontown.parties import PartyUtils
from toontown.parties.PartyEditorGrid import PartyEditorGrid
from toontown.parties.PartyEditorListElement import PartyEditorListElement

class PartyEditor(DirectObject, FSM):
    notify = directNotify.newCategory('PartyEditor')

    def __init__(self, partyPlanner, parent):
        FSM.__init__(self, self.__class__.__name__)
        self.partyPlanner = partyPlanner
        self.parent = parent
        self.partyEditorGrid = PartyEditorGrid(self)
        self.currentElement = None
        self.defaultTransitions = {'Hidden': ['Idle', 'Cleanup'],
         'Idle': ['DraggingElement', 'Hidden', 'Cleanup'],
         'DraggingElement': ['Idle',
                             'DraggingElement',
                             'Hidden',
                             'Cleanup'],
         'Cleanup': []}
        self.initElementList()
        self.initPartyClock()
        self.initTrashCan()
        return

    def initElementList(self):
        self.activityIconsModel = loader.loadModel('phase_4/models/parties/eventSignIcons')
        self.decorationModels = loader.loadModel('phase_4/models/parties/partyDecorations')
        pos = self.partyPlanner.gui.find('**/step_05_activitiesIcon_locator').getPos()
        self.elementList = DirectScrolledList(parent=self.parent, relief=None, decButton_image=(self.partyPlanner.gui.find('**/activitiesButtonUp_up'),
         self.partyPlanner.gui.find('**/activitiesButtonUp_down'),
         self.partyPlanner.gui.find('**/activitiesButtonUp_rollover'),
         self.partyPlanner.gui.find('**/activitiesButtonUp_inactive')), decButton_relief=None, decButton_pos=(-0.05, 0.0, -0.38), incButton_image=(self.partyPlanner.gui.find('**/activitiesButtonDown_up'),
         self.partyPlanner.gui.find('**/activitiesButtonDown_down'),
         self.partyPlanner.gui.find('**/activitiesButtonDown_rollover'),
         self.partyPlanner.gui.find('**/activitiesButtonDown_inactive')), incButton_relief=None, incButton_pos=(-0.05, 0.0, -0.94), itemFrame_pos=(pos[0], pos[1], pos[2] + 0.04), itemFrame_relief=None, numItemsVisible=1, items=[])
        holidayIds = base.cr.newsManager.getHolidayIdList()
        isWinter = ToontownGlobals.WINTER_DECORATIONS in holidayIds or ToontownGlobals.WACKY_WINTER_DECORATIONS in holidayIds
        isVictory = ToontownGlobals.VICTORY_PARTY_HOLIDAY in holidayIds
        isValentine = ToontownGlobals.VALENTINES_DAY in holidayIds
        for activityId in PartyGlobals.PartyEditorActivityOrder:
            if not isVictory and activityId in PartyGlobals.VictoryPartyActivityIds or not isWinter and activityId in PartyGlobals.WinterPartyActivityIds or not isValentine and activityId in PartyGlobals.ValentinePartyActivityIds:
                pass
            elif isVictory and activityId in PartyGlobals.VictoryPartyReplacementActivityIds or isWinter and activityId in PartyGlobals.WinterPartyReplacementActivityIds or isValentine and activityId in PartyGlobals.ValentinePartyReplacementActivityIds:
                pass
            else:
                pele = PartyEditorListElement(self, activityId)
                self.elementList.addItem(pele)
                if activityId == PartyGlobals.ActivityIds.PartyClock:
                    self.partyClockElement = pele

        for decorationId in PartyGlobals.DecorationIds:
            if not isVictory and decorationId in PartyGlobals.VictoryPartyDecorationIds or not isWinter and decorationId in PartyGlobals.WinterPartyDecorationIds or not isValentine and decorationId in PartyGlobals.ValentinePartyDecorationIds:
                pass
            elif isVictory and decorationId in PartyGlobals.VictoryPartyReplacementDecorationIds or isValentine and decorationId in PartyGlobals.ValentinePartyReplacementDecorationIds:
                pass
            else:
                pele = PartyEditorListElement(self, decorationId, isDecoration=True)
                self.elementList.addItem(pele)

        self.elementList.refresh()
        self.elementList['command'] = self.scrollItemChanged
        return

    def initPartyClock(self):
        self.partyClockElement.buyButtonClicked((8, 7))

    def initTrashCan(self):
        trashcanGui = loader.loadModel('phase_3/models/gui/trashcan_gui')
        self.trashCanButton = DirectButton(parent=self.parent, relief=None, pos=Point3(*PartyGlobals.TrashCanPosition), scale=PartyGlobals.TrashCanScale, geom=(trashcanGui.find('**/TrashCan_CLSD'),
         trashcanGui.find('**/TrashCan_OPEN'),
         trashcanGui.find('**/TrashCan_RLVR'),
         trashcanGui.find('**/TrashCan_RLVR')), command=self.trashCanClicked)
        self.trashCanButton.bind(DirectGuiGlobals.ENTER, self.mouseEnterTrash)
        self.trashCanButton.bind(DirectGuiGlobals.EXIT, self.mouseExitTrash)
        self.mouseOverTrash = False
        self.oldInstructionText = ''
        self.trashCanLastClickedTime = 0
        return

    def scrollItemChanged(self):
        if not self.elementList['items']:
            return
        self.currentElement = self.elementList['items'][self.elementList.getSelectedIndex()]
        self.elementList['items'][self.elementList.getSelectedIndex()].elementSelectedFromList()
        if self.elementList['items'][self.elementList.getSelectedIndex()].isDecoration:
            self.partyPlanner.instructionLabel['text'] = TTLocalizer.PartyPlannerEditorInstructionsClickedElementDecoration
        else:
            self.partyPlanner.instructionLabel['text'] = TTLocalizer.PartyPlannerEditorInstructionsClickedElementActivity

    def listElementClicked(self):
        self.request('DraggingElement')

    def listElementReleased(self):
        self.request('Idle', True)

    def trashCanClicked(self):
        currentTime = time.time()
        if currentTime - self.trashCanLastClickedTime < 0.2:
            self.clearPartyGrounds()
        self.trashCanLastClickedTime = time.time()

    def clearPartyGrounds(self):
        for item in self.elementList['items']:
            item.clearPartyGrounds()

        self.initPartyClock()
        if self.currentElement:
            self.currentElement.checkSoldOutAndPaidStatusAndAffordability()

    def buyCurrentElement(self):
        if self.currentElement:
            purchaseSuccessful = self.currentElement.buyButtonClicked()
            if purchaseSuccessful:
                self.handleMutuallyExclusiveActivities()
            else:
                self.partyPlanner.instructionLabel['text'] = TTLocalizer.PartyPlannerEditorInstructionsNoRoom

    def mouseEnterTrash(self, mouseEvent):
        self.mouseOverTrash = True
        self.oldInstructionText = self.partyPlanner.instructionLabel['text']
        self.partyPlanner.instructionLabel['text'] = TTLocalizer.PartyPlannerEditorInstructionsTrash

    def mouseExitTrash(self, mouseEvent):
        self.mouseOverTrash = False
        self.partyPlanner.instructionLabel['text'] = self.oldInstructionText

    def enterHidden(self):
        PartyEditor.notify.debug('Enter Hidden')

    def exitHidden(self):
        PartyEditor.notify.debug('Exit Hidden')

    def enterIdle(self, fromDragging = False):
        PartyEditor.notify.debug('Enter Idle')
        if not fromDragging:
            self.elementList.scrollTo(0)
            self.elementList['items'][0].elementSelectedFromList()
            self.currentElement = self.elementList['items'][self.elementList.getSelectedIndex()]
            self.currentElement.checkSoldOutAndPaidStatusAndAffordability()
        self.partyPlanner.instructionLabel['text'] = TTLocalizer.PartyPlannerEditorInstructionsIdle
        self.updateCostsAndBank()
        self.handleMutuallyExclusiveActivities()

    def handleMutuallyExclusiveActivities(self):
        mutSet = self.getMutuallyExclusiveActivities()
        if not mutSet:
            return
        currentActivities = self.partyEditorGrid.getActivitiesElementsOnGrid()
        lastActivity = self.partyEditorGrid.lastActivityIdPlaced
        for act in currentActivities:
            if act.id in mutSet and not lastActivity == act.id:
                act.removeFromGrid()
                removedName = TTLocalizer.PartyActivityNameDict[act.id]['editor']
                addedName = TTLocalizer.PartyActivityNameDict[lastActivity]['editor']
                instr = TTLocalizer.PartyPlannerEditorInstructionsRemoved % {'removed': removedName,
                 'added': addedName}
                self.partyPlanner.instructionLabel['text'] = instr
                self.updateCostsAndBank()

    def getMutuallyExclusiveActivities(self):
        currentActivities = self.partyEditorGrid.getActivitiesOnGrid()
        actSet = Set([])
        for act in currentActivities:
            actSet.add(act[0])

        result = None
        for mutuallyExclusiveTuples in PartyGlobals.MutuallyExclusiveActivities:
            mutSet = Set(mutuallyExclusiveTuples)
            inter = mutSet.intersection(actSet)
            if len(inter) > 1:
                result = inter
                break

        return result

    def updateCostsAndBank(self):
        currentActivities = self.partyEditorGrid.getActivitiesOnGrid()
        currentDecorations = self.partyEditorGrid.getDecorationsOnGrid()
        newCost = 0
        for elementTuple in currentActivities:
            newCost += PartyGlobals.ActivityInformationDict[elementTuple[0]]['cost']

        for elementTuple in currentDecorations:
            newCost += PartyGlobals.DecorationInformationDict[elementTuple[0]]['cost']

        self.partyPlanner.costLabel['text'] = TTLocalizer.PartyPlannerTotalCost % newCost
        if len(currentActivities) > 0 or len(currentDecorations) > 0:
            self.partyPlanner.setNextButtonState(enabled=True)
        else:
            self.partyPlanner.setNextButtonState(enabled=False)
        self.partyPlanner.totalCost = newCost
        self.partyPlanner.beanBank['text'] = str(int(self.partyPlanner.totalMoney - self.partyPlanner.totalCost))

    def exitIdle(self):
        PartyEditor.notify.debug('Exit Idle')

    def enterDraggingElement(self):
        PartyEditor.notify.debug('Enter DraggingElement')
        if self.currentElement.isDecoration:
            self.partyPlanner.instructionLabel['text'] = TTLocalizer.PartyPlannerEditorInstructionsDraggingDecoration
        else:
            self.partyPlanner.instructionLabel['text'] = TTLocalizer.PartyPlannerEditorInstructionsDraggingActivity

    def exitDraggingElement(self):
        PartyEditor.notify.debug('Exit DraggingElement')

    def enterCleanup(self):
        PartyEditor.notify.debug('Enter Cleanup')
        self.partyEditorGrid.destroy()
        self.elementList.removeAndDestroyAllItems()
        self.elementList.destroy()
        self.trashCanButton.unbind(DirectGuiGlobals.ENTER)
        self.trashCanButton.unbind(DirectGuiGlobals.EXIT)
        self.trashCanButton.destroy()

    def exitCleanup(self):
        PartyEditor.notify.debug('Exit Cleanup')
