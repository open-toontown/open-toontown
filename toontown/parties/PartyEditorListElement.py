from pandac.PandaModules import Vec3
from direct.gui.DirectGui import DirectButton, DirectLabel
from direct.gui import DirectGuiGlobals
from toontown.toonbase import TTLocalizer
from toontown.parties import PartyGlobals
from toontown.parties.PartyEditorGridElement import PartyEditorGridElement
from toontown.parties.PartyUtils import getPartyActivityIcon

class PartyEditorListElement(DirectButton):
    notify = directNotify.newCategory('PartyEditorListElement')

    def __init__(self, partyEditor, id, isDecoration = False, **kw):
        self.partyEditor = partyEditor
        self.id = id
        self.isDecoration = isDecoration
        self.unreleased = self.calcUnreleased(id)
        self.comingSoonTextScale = 1.0
        if self.isDecoration:
            self._name = TTLocalizer.PartyDecorationNameDict[self.id]['editor']
            colorList = ((1.0, 0.0, 1.0, 1.0),
             (0.0, 0.0, 1.0, 1.0),
             (0.0, 1.0, 1.0, 1.0),
             (0.5, 0.5, 0.5, 1.0))
            assetName = PartyGlobals.DecorationIds.getString(self.id)
            if assetName == 'Hydra':
                assetName = 'StageSummer'
            geom = self.partyEditor.decorationModels.find('**/partyDecoration_%s' % assetName)
            if geom.isEmpty() or self.unreleased:
                helpGui = loader.loadModel('phase_3.5/models/gui/tt_m_gui_brd_help')
                helpImageList = (helpGui.find('**/tt_t_gui_brd_helpUp'),
                 helpGui.find('**/tt_t_gui_brd_helpDown'),
                 helpGui.find('**/tt_t_gui_brd_helpHover'),
                 helpGui.find('**/tt_t_gui_brd_helpDown'))
                geom = helpImageList[2]
                geom3_color = (0.5, 0.5, 0.5, 1.0)
                scale = Vec3(2.5, 2.5, 2.5)
                geom_pos = (0.0, 0.0, 0.0)
                self.comingSoonTextScale = 0.035
            else:
                geom_pos = (0.0, 0.0, -3.0)
                geom3_color = (0.5, 0.5, 0.5, 1.0)
                scale = Vec3(0.06, 0.0001, 0.06)
                if self.id in [PartyGlobals.DecorationIds.CogStatueVictory, PartyGlobals.DecorationIds.TubeCogVictory, PartyGlobals.DecorationIds.CogIceCreamVictory]:
                    geom_pos = (0.0, 0.0, -3.9)
                    scale = Vec3(0.05, 0.0001, 0.05)
        else:
            self._name = TTLocalizer.PartyActivityNameDict[self.id]['editor']
            colorList = ((0.0, 0.0, 0.0, 1.0),
             (0.0, 1.0, 0.0, 1.0),
             (1.0, 1.0, 0.0, 1.0),
             (0.5, 0.5, 0.5, 1.0))
            iconString = PartyGlobals.ActivityIds.getString(self.id)
            if self.id == PartyGlobals.ActivityIds.PartyJukebox40:
                iconString = PartyGlobals.ActivityIds.getString(PartyGlobals.ActivityIds.PartyJukebox)
            elif self.id == PartyGlobals.ActivityIds.PartyDance20:
                iconString = PartyGlobals.ActivityIds.getString(PartyGlobals.ActivityIds.PartyDance)
            geom = getPartyActivityIcon(self.partyEditor.activityIconsModel, iconString)
            scale = 0.35
            geom3_color = (0.5, 0.5, 0.5, 1.0)
            geom_pos = (0.0, 0.0, 0.0)
            self.comingSoonTextScale = 0.25
        optiondefs = (('geom', geom, None),
         ('geom3_color', geom3_color, None),
         ('geom_pos', geom_pos, None),
         ('relief', None, None))
        self.defineoptions(kw, optiondefs)
        DirectButton.__init__(self, self.partyEditor.elementList)
        self.initialiseoptions(PartyEditorListElement)
        self.setName('%sListElement' % self._name)
        self.setScale(scale)
        self.bind(DirectGuiGlobals.B1PRESS, self.clicked)
        self.bind(DirectGuiGlobals.B1RELEASE, self.released)
        self.partyEditorGridElements = []
        if self.isDecoration:
            for i in range(PartyGlobals.DecorationInformationDict[self.id]['limitPerParty']):
                self.partyEditorGridElements.append(PartyEditorGridElement(self.partyEditor, self.id, self.isDecoration, self.checkSoldOutAndPaidStatusAndAffordability))

        else:
            for i in range(PartyGlobals.ActivityInformationDict[self.id]['limitPerParty']):
                self.partyEditorGridElements.append(PartyEditorGridElement(self.partyEditor, self.id, self.isDecoration, self.checkSoldOutAndPaidStatusAndAffordability))

        self.activeGridElementIndex = -1
        self.adjustForUnreleased()
        return

    def calcUnreleased(self, id):
        if base.cr.partyManager.allowUnreleasedClient():
            self.unreleased = False
        elif self.isDecoration:
            self.unreleased = id in PartyGlobals.UnreleasedDecorationIds
        else:
            self.unreleased = id in PartyGlobals.UnreleasedActivityIds
        return self.unreleased

    def adjustForUnreleased(self):
        if self.unreleased:
            textScale = self.comingSoonTextScale
            comingSoon = DirectLabel(parent=self, text=TTLocalizer.PartyPlannerComingSoon, text_scale=textScale, text_fg=(1.0, 0, 0, 1.0), text_shadow=(0, 0, 0, 1), relief=None)
            self['state'] = DirectGuiGlobals.DISABLED
        return

    def clearPartyGrounds(self):
        for gridElement in self.partyEditorGridElements:
            gridElement.removeFromGrid()

    def elementSelectedFromList(self):
        PartyEditorListElement.notify.debug('Element %s clicked' % self._name)
        if self.isDecoration:
            self.partyEditor.partyPlanner.elementDescriptionNode.setText(TTLocalizer.PartyDecorationNameDict[self.id]['description'])
            self.partyEditor.partyPlanner.elementPriceNode.setText('%d %s' % (PartyGlobals.DecorationInformationDict[self.id]['cost'], TTLocalizer.PartyPlannerBeans))
            self.partyEditor.partyPlanner.elementTitleLabel['text'] = self._name
        else:
            self.partyEditor.partyPlanner.elementDescriptionNode.setText(TTLocalizer.PartyActivityNameDict[self.id]['description'])
            self.partyEditor.partyPlanner.elementPriceNode.setText('%d %s' % (PartyGlobals.ActivityInformationDict[self.id]['cost'], TTLocalizer.PartyPlannerBeans))
            self.partyEditor.partyPlanner.elementTitleLabel['text'] = self._name
        self.checkSoldOutAndPaidStatusAndAffordability()

    def checkSoldOutAndPaidStatusAndAffordability(self):
        if self.partyEditor.currentElement != self:
            if self.partyEditor.currentElement is not None:
                self.partyEditor.currentElement.checkSoldOutAndPaidStatusAndAffordability()
            return
        if self.isDecoration:
            infoDict = PartyGlobals.DecorationInformationDict
        else:
            infoDict = PartyGlobals.ActivityInformationDict
        if not base.cr.isPaid() and infoDict[self.id]['paidOnly']:
            self.setOffLimits()
            return
        if infoDict[self.id]['cost'] > self.partyEditor.partyPlanner.totalMoney - self.partyEditor.partyPlanner.totalCost:
            self.setTooExpensive(True)
            tooExpensive = True
        else:
            self.setTooExpensive(False)
            tooExpensive = False
        for i in range(len(self.partyEditorGridElements)):
            if not self.partyEditorGridElements[i].overValidSquare:
                if not tooExpensive:
                    self.setSoldOut(False)
                return

        self.setSoldOut(True)
        return

    def setOffLimits(self):
        self['state'] = DirectGuiGlobals.DISABLED
        self.partyEditor.partyPlanner.elementBuyButton['text'] = TTLocalizer.PartyPlannerPaidOnly
        self.partyEditor.partyPlanner.elementBuyButton['state'] = DirectGuiGlobals.DISABLED
        self.partyEditor.partyPlanner.elementBuyButton['text_scale'] = 0.04

    def setTooExpensive(self, value):
        self.partyEditor.partyPlanner.elementBuyButton['text'] = TTLocalizer.PartyPlannerBuy
        if value:
            self['state'] = DirectGuiGlobals.DISABLED
            self.partyEditor.partyPlanner.elementBuyButton['state'] = DirectGuiGlobals.DISABLED
        else:
            self['state'] = DirectGuiGlobals.NORMAL
            self.partyEditor.partyPlanner.elementBuyButton['state'] = DirectGuiGlobals.NORMAL

    def setSoldOut(self, value):
        if value:
            self['state'] = DirectGuiGlobals.DISABLED
            self.partyEditor.partyPlanner.elementBuyButton['text'] = TTLocalizer.PartyPlannerSoldOut
            self.partyEditor.partyPlanner.elementBuyButton['state'] = DirectGuiGlobals.DISABLED
        else:
            self['state'] = DirectGuiGlobals.NORMAL
            self.partyEditor.partyPlanner.elementBuyButton['text'] = TTLocalizer.PartyPlannerBuy
            self.partyEditor.partyPlanner.elementBuyButton['state'] = DirectGuiGlobals.NORMAL
        if self.unreleased:
            self['state'] = DirectGuiGlobals.DISABLED
            self.partyEditor.partyPlanner.elementBuyButton['text'] = TTLocalizer.PartyPlannerCantBuy
            self.partyEditor.partyPlanner.elementBuyButton['state'] = DirectGuiGlobals.DISABLED

    def clicked(self, mouseEvent):
        PartyEditorListElement.notify.debug("Element %s's icon was clicked" % self._name)
        self.partyEditor.listElementClicked()
        for i in range(len(self.partyEditorGridElements)):
            if not self.partyEditorGridElements[i].overValidSquare:
                self.partyEditorGridElements[i].attach(mouseEvent)
                self.activeGridElementIndex = i
                return

    def buyButtonClicked(self, desiredXY = None):
        for i in range(len(self.partyEditorGridElements)):
            if not self.partyEditorGridElements[i].overValidSquare:
                if self.partyEditorGridElements[i].placeInPartyGrounds(desiredXY):
                    self.activeGridElementIndex = i
                    return True
                else:
                    self.checkSoldOutAndPaidStatusAndAffordability()
                    return False

    def released(self, mouseEvent):
        PartyEditorListElement.notify.debug("Element %s's icon was released" % self._name)
        self.partyEditor.listElementReleased()
        if self.activeGridElementIndex != -1:
            self.partyEditorGridElements[self.activeGridElementIndex].detach(mouseEvent)

    def destroy(self):
        self.unbind(DirectGuiGlobals.B1PRESS)
        self.unbind(DirectGuiGlobals.B1RELEASE)
        for partyEditorGridElement in self.partyEditorGridElements:
            partyEditorGridElement.destroy()

        del self.partyEditorGridElements
        self.partyEditor = None
        DirectButton.destroy(self)
        return
