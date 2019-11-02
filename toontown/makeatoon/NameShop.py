from pandac.PandaModules import *
from toontown.toonbase.ToontownGlobals import *
from direct.task.TaskManagerGlobal import *
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from toontown.distributed.ToontownMsgTypes import *
from direct.directnotify import DirectNotifyGlobal
from direct.gui import OnscreenText
from otp.avatar import Avatar
from otp.chat import ChatManager
from direct.fsm import StateData
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from toontown.toontowngui import TTDialog
import re
import string
from toontown.toonbase import TTLocalizer
import NameGenerator
import random
from otp.distributed import PotentialAvatar
from otp.namepanel import NameCheck
from toontown.toontowngui import TeaserPanel
from direct.distributed.PyDatagram import PyDatagram
from direct.showbase import PythonUtil
from toontown.toon import NPCToons
from direct.task import Task
from toontown.makeatoon.TTPickANamePattern import TTPickANamePattern
from pandac.PandaModules import TextEncoder
MAX_NAME_WIDTH = TTLocalizer.NSmaxNameWidth
ServerDialogTimeout = 3.0

class NameShop(StateData.StateData):
    notify = DirectNotifyGlobal.directNotify.newCategory('NameShop')

    def __init__(self, makeAToon, doneEvent, avList, index, isPaid):
        StateData.StateData.__init__(self, doneEvent)
        self.makeAToon = makeAToon
        self.isPaid = isPaid
        self.avList = avList
        self.index = index
        self.shopsVisited = []
        self.avId = -1
        self.avExists = 0
        self.names = ['',
         '',
         '',
         '']
        self.toon = None
        self.boy = 0
        self.girl = 0
        self.allTitles = []
        self.allFirsts = []
        self.allPrefixes = []
        self.allSuffixes = []
        self.titleIndex = 0
        self.firstIndex = 0
        self.prefixIndex = 0
        self.suffixIndex = 0
        self.titleActive = 0
        self.firstActive = 0
        self.lastActive = 0
        self.quickFind = 0
        self.listsLoaded = 0
        self.addedGenderSpecific = 0
        self.chastise = 0
        self.nameIndices = [-1,
         -1,
         -1,
         -1]
        self.nameFlags = [1,
         1,
         1,
         0]
        self.dummyReturn = 2
        self.nameAction = 0
        self.pickANameGUIElements = []
        self.typeANameGUIElements = []
        self.textRolloverColor = Vec4(1, 1, 0, 1)
        self.textDownColor = Vec4(0.5, 0.9, 1, 1)
        self.textDisabledColor = Vec4(0.4, 0.8, 0.4, 1)
        self.fsm = ClassicFSM.ClassicFSM('NameShop', [State.State('Init', self.enterInit, self.exitInit, ['PayState']),
         State.State('PayState', self.enterPayState, self.exitPayState, ['PickAName']),
         State.State('PickAName', self.enterPickANameState, self.exitPickANameState, ['TypeAName', 'Done']),
         State.State('TypeAName', self.enterTypeANameState, self.exitTypeANameState, ['PickAName',
          'Approval',
          'Accepted',
          'Rejected']),
         State.State('Approval', self.enterApprovalState, self.exitApprovalState, ['PickAName', 'ApprovalAccepted']),
         State.State('ApprovalAccepted', self.enterApprovalAcceptedState, self.exitApprovalAcceptedState, ['Done']),
         State.State('Accepted', self.enterAcceptedState, self.exitAcceptedState, ['Done']),
         State.State('Rejected', self.enterRejectedState, self.exitRejectedState, ['TypeAName']),
         State.State('Done', self.enterDone, self.exitDone, ['Init'])], 'Init', 'Done')
        self.parentFSM = makeAToon.fsm
        self.parentFSM.getStateNamed('NameShop').addChild(self.fsm)
        self.nameGen = NameGenerator.NameGenerator()
        self.fsm.enterInitialState()
        self.requestingSkipTutorial = False
        return

    def makeLabel(self, te, index, others):
        alig = others[0]
        listName = others[1]
        if alig == TextNode.ARight:
            newpos = (0.44, 0, 0)
        elif alig == TextNode.ALeft:
            newpos = (0, 0, 0)
        else:
            newpos = (0.2, 0, 0)
        df = DirectFrame(state='normal', relief=None, text=te, text_scale=TTLocalizer.NSmakeLabel, text_pos=newpos, text_align=alig, textMayChange=0)
        df.bind(DGG.B1PRESS, lambda x, df = df: self.nameClickedOn(listName, index))
        return df

    def nameClickedOn(self, listType, index):
        if listType == 'title':
            self.titleIndex = index
        elif listType == 'first':
            self.firstIndex = index
        elif listType == 'prefix':
            self.prefixIndex = index
        else:
            self.suffixIndex = index
        self.updateLists()
        self.__listsChanged()

    def enter(self, toon, usedNames, warp):
        self.notify.debug('enter')
        self.newwarp = warp
        self.avExists = warp
        if self.avExists:
            for g in self.avList:
                if g.position == self.index:
                    self.avId = g.id

        if toon == None:
            return
        else:
            self.toon = toon
            if self.toon.style.gender == 'm':
                self.boy = 1
                self.girl = 0
            else:
                self.boy = 0
                self.girl = 1
        self.usedNames = usedNames
        if not self.addedGenderSpecific or self.oldBoy != self.boy:
            self.oldBoy = self.boy
            self.listsLoaded = 0
            self.allTitles = [' '] + [' '] + self.nameGen.boyTitles * self.boy + self.nameGen.girlTitles * self.girl + self.nameGen.neutralTitles
            self.allTitles.sort()
            self.allTitles += [' '] + [' ']
            self.allFirsts = [' '] + [' '] + self.nameGen.boyFirsts * self.boy + self.nameGen.girlFirsts * self.girl + self.nameGen.neutralFirsts
            self.allFirsts.sort()
            self.allFirsts += [' '] + [' ']
            try:
                k = self.allFirsts.index('Von')
                self.allFirsts[k] = 'von'
            except:
                print "NameShop: Couldn't find von"

            if not self.addedGenderSpecific:
                nameShopGui = loader.loadModel('phase_3/models/gui/tt_m_gui_mat_nameShop')
                self.namePanel = DirectFrame(parent=aspect2d, image=None, relief='flat', state='disabled', pos=(-0.42, 0, -0.15), image_pos=(0, 0, 0.025), frameColor=(1, 1, 1, 0.3))
                panel = nameShopGui.find('**/tt_t_gui_mat_namePanel')
                self.panelFrame = DirectFrame(image=panel, scale=(0.75, 0.7, 0.7), relief='flat', frameColor=(1, 1, 1, 0), pos=(-0.0163, 0, 0.1199))
                self.panelFrame.reparentTo(self.namePanel, sort=1)
                self.pickANameGUIElements.append(self.namePanel)
                self.pickANameGUIElements.append(self.panelFrame)
                self.nameResult.reparentTo(self.namePanel, sort=2)
                self.circle = nameShopGui.find('**/tt_t_gui_mat_namePanelCircle')
                self.titleCheck = self.makeCheckBox((-0.615, 0, 0.371), TTLocalizer.TitleCheckBox, (0, 0.25, 0.5, 1), self.titleToggle)
                self.firstCheck = self.makeCheckBox((-0.2193, 0, 0.371), TTLocalizer.FirstCheckBox, (0, 0.25, 0.5, 1), self.firstToggle)
                self.lastCheck = self.makeCheckBox((0.3886, 0, 0.371), TTLocalizer.LastCheckBox, (0, 0.25, 0.5, 1), self.lastToggle)
                del self.circle
                self.pickANameGUIElements.append(self.titleCheck)
                self.pickANameGUIElements.append(self.firstCheck)
                self.pickANameGUIElements.append(self.lastCheck)
                self.titleCheck.reparentTo(self.namePanel, sort=2)
                self.firstCheck.reparentTo(self.namePanel, sort=2)
                self.lastCheck.reparentTo(self.namePanel, sort=2)
                nameShopGui.removeNode()
                self.lastprefixScrollList.reparentTo(self.namePanel)
                self.lastprefixScrollList.decButton.wrtReparentTo(self.namePanel, sort=2)
                self.lastprefixScrollList.incButton.wrtReparentTo(self.namePanel, sort=2)
                self.lastsuffixScrollList.reparentTo(self.namePanel)
                self.lastsuffixScrollList.decButton.wrtReparentTo(self.namePanel, sort=2)
                self.lastsuffixScrollList.incButton.wrtReparentTo(self.namePanel, sort=2)
                self.titleHigh.reparentTo(self.namePanel)
                self.prefixHigh.reparentTo(self.namePanel)
                self.firstHigh.reparentTo(self.namePanel)
                self.suffixHigh.reparentTo(self.namePanel)
                self.randomButton.reparentTo(self.namePanel, sort=2)
                self.typeANameButton.reparentTo(self.namePanel, sort=2)
            self.pickANameGUIElements.remove(self.titleScrollList)
            self.pickANameGUIElements.remove(self.firstnameScrollList)
            self.titleScrollList.destroy()
            self.firstnameScrollList.destroy()
            self.titleScrollList = self.makeScrollList(None, (-0.6, 0, 0.202), (1, 0.8, 0.8, 1), self.allTitles, self.makeLabel, [TextNode.ACenter, 'title'])
            self.firstnameScrollList = self.makeScrollList(None, (-0.2, 0, 0.202), (0.8, 1, 0.8, 1), self.allFirsts, self.makeLabel, [TextNode.ACenter, 'first'])
            self.pickANameGUIElements.append(self.titleScrollList)
            self.pickANameGUIElements.append(self.firstnameScrollList)
            self.titleScrollList.reparentTo(self.namePanel, sort=-1)
            self.titleScrollList.decButton.wrtReparentTo(self.namePanel, sort=2)
            self.titleScrollList.incButton.wrtReparentTo(self.namePanel, sort=2)
            self.firstnameScrollList.reparentTo(self.namePanel, sort=-1)
            self.firstnameScrollList.decButton.wrtReparentTo(self.namePanel, sort=2)
            self.firstnameScrollList.incButton.wrtReparentTo(self.namePanel, sort=2)
            self.listsLoaded = 1
            self.addedGenderSpecific = 1
            self.__randomName()
        self.typeANameButton['text'] = TTLocalizer.TypeANameButton
        if self.isLoaded == 0:
            self.load()
        self.ubershow(self.pickANameGUIElements)
        self.acceptOnce('next', self.__handleDone)
        self.acceptOnce('last', self.__handleBackward)
        self.acceptOnce('skipTutorial', self.__handleSkipTutorial)
        self.__listsChanged()
        self.fsm.request('PayState')
        return

    def __overflowNameInput(self):
        self.rejectName(TTLocalizer.NameTooLong)

    def exit(self):
        self.notify.debug('exit')
        if self.isLoaded == 0:
            return None
        self.ignore('next')
        self.ignore('last')
        self.ignore('skipTutorial')
        self.hideAll()
        return None

    def __listsChanged(self):
        newname = ''
        if self.listsLoaded:
            if self.titleActive:
                self.showList(self.titleScrollList)
                self.titleHigh.show()
                newtitle = self.titleScrollList['items'][self.titleScrollList.index + 2]['text']
                self.nameIndices[0] = self.nameGen.returnUniqueID(newtitle, 0)
                newname += newtitle + ' '
            else:
                self.nameIndices[0] = -1
                self.stealth(self.titleScrollList)
                self.titleHigh.hide()
            if self.firstActive:
                self.showList(self.firstnameScrollList)
                self.firstHigh.show()
                newfirst = self.firstnameScrollList['items'][self.firstnameScrollList.index + 2]['text']
                if newfirst == 'von':
                    nt = 'Von'
                else:
                    nt = newfirst
                self.nameIndices[1] = self.nameGen.returnUniqueID(nt, 1)
                if not self.titleActive and newfirst == 'von':
                    newfirst = 'Von'
                    newname += newfirst
                else:
                    newname += newfirst
                if newfirst == 'von':
                    self.nameFlags[1] = 0
                else:
                    self.nameFlags[1] = 1
                if self.lastActive:
                    newname += ' '
            else:
                self.firstHigh.hide()
                self.stealth(self.firstnameScrollList)
                self.nameIndices[1] = -1
            if self.lastActive:
                self.showList(self.lastprefixScrollList)
                self.showList(self.lastsuffixScrollList)
                self.prefixHigh.show()
                self.suffixHigh.show()
                lp = self.lastprefixScrollList['items'][self.lastprefixScrollList.index + 2]['text']
                ls = self.lastsuffixScrollList['items'][self.lastsuffixScrollList.index + 2]['text']
                self.nameIndices[2] = self.nameGen.returnUniqueID(lp, 2)
                self.nameIndices[3] = self.nameGen.returnUniqueID(ls, 3)
                newname += lp
                if lp in self.nameGen.capPrefixes:
                    ls = ls.capitalize()
                    self.nameFlags[3] = 1
                else:
                    self.nameFlags[3] = 0
                newname += ls
            else:
                self.stealth(self.lastprefixScrollList)
                self.stealth(self.lastsuffixScrollList)
                self.prefixHigh.hide()
                self.suffixHigh.hide()
                self.nameIndices[2] = -1
                self.nameIndices[3] = -1
            self.titleIndex = self.titleScrollList.index + 2
            self.firstIndex = self.firstnameScrollList.index + 2
            self.prefixIndex = self.lastprefixScrollList.index + 2
            self.suffixIndex = self.lastsuffixScrollList.index + 2
            self.nameResult['text'] = newname
            self.names[0] = newname

    def makeScrollList(self, gui, ipos, mcolor, nitems, nitemMakeFunction, nitemMakeExtraArgs):
        self.notify.debug('makeScrollList')
        it = nitems[:]
        ds = DirectScrolledList(items=it, itemMakeFunction=nitemMakeFunction, itemMakeExtraArgs=nitemMakeExtraArgs, parent=aspect2d, relief=None, command=self.__listsChanged, pos=ipos, scale=0.6, incButton_image=(self.arrowUp,
         self.arrowDown,
         self.arrowHover,
         self.arrowUp), incButton_relief=None, incButton_scale=(1.2, 1.2, -1.2), incButton_pos=(0.0189, 0, -0.5335), incButton_image0_color=mcolor, incButton_image1_color=mcolor, incButton_image2_color=mcolor, incButton_image3_color=Vec4(1, 1, 1, 0), decButton_image=(self.arrowUp,
         self.arrowDown,
         self.arrowHover,
         self.arrowUp), decButton_relief=None, decButton_scale=(1.2, 1.2, 1.2), decButton_pos=(0.0195, 0, 0.1779), decButton_image0_color=mcolor, decButton_image1_color=mcolor, decButton_image2_color=mcolor, decButton_image3_color=Vec4(1, 1, 1, 0), itemFrame_pos=(-.2, 0, 0.028), itemFrame_scale=1.0, itemFrame_relief=DGG.RAISED, itemFrame_frameSize=(-0.07,
         0.5,
         -0.52,
         0.12), itemFrame_frameColor=mcolor, itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=5, forceHeight=TTLocalizer.NSdirectScrolleList)
        return ds

    def makeCheckBox(self, npos, ntex, ntexcolor, comm):
        return DirectCheckButton(parent=aspect2d, relief=None, scale=0.1, boxBorder=0.08, boxImage=self.circle, boxImageScale=4, boxImageColor=VBase4(0, 0.25, 0.5, 1), boxRelief=None, pos=npos, text=ntex, text_fg=ntexcolor, text_scale=TTLocalizer.NSmakeCheckBox, text_pos=(0.2, 0), indicator_pos=(-0.566667, 0, -0.045), indicator_image_pos=(-0.26, 0, 0.075), command=comm, text_align=TextNode.ALeft)

    def makeHighlight(self, npos):
        return DirectFrame(parent=aspect2d, relief='flat', scale=(0.552, 0, 0.11), state='disabled', frameSize=(-0.07,
         0.52,
         -0.5,
         0.1), borderWidth=(0.01, 0.01), pos=npos, frameColor=(1, 0, 1, 0.4))

    def titleToggle(self, value):
        self.titleActive = self.titleCheck['indicatorValue']
        if not (self.titleActive or self.firstActive or self.lastActive):
            self.titleActive = 1
        self.__listsChanged()
        if self.titleActive:
            self.titleScrollList.refresh()
        self.updateCheckBoxes()

    def firstToggle(self, value):
        self.firstActive = self.firstCheck['indicatorValue']
        if self.chastise == 2:
            messenger.send('NameShop-mickeyChange', [[TTLocalizer.ApprovalForName1, TTLocalizer.ApprovalForName2]])
            self.chastise = 0
        if not self.firstActive and not self.lastActive:
            self.firstActive = 1
            messenger.send('NameShop-mickeyChange', [[TTLocalizer.MustHaveAFirstOrLast1, TTLocalizer.MustHaveAFirstOrLast2]])
            self.chastise = 1
        self.__listsChanged()
        if self.firstActive:
            self.firstnameScrollList.refresh()
        self.updateCheckBoxes()

    def lastToggle(self, value):
        self.lastActive = self.lastCheck['indicatorValue']
        if self.chastise == 1:
            messenger.send('NameShop-mickeyChange', [[TTLocalizer.ApprovalForName1, TTLocalizer.ApprovalForName2]])
            self.chastise = 0
        if not self.firstActive and not self.lastActive:
            self.lastActive = 1
            messenger.send('NameShop-mickeyChange', [[TTLocalizer.MustHaveAFirstOrLast1, TTLocalizer.MustHaveAFirstOrLast2]])
            self.chastise = 2
        self.__listsChanged()
        if self.lastActive:
            self.lastprefixScrollList.refresh()
            self.lastsuffixScrollList.refresh()
        self.updateCheckBoxes()

    def updateCheckBoxes(self):
        self.titleCheck['indicatorValue'] = self.titleActive
        self.titleCheck.setIndicatorValue()
        self.firstCheck['indicatorValue'] = self.firstActive
        self.firstCheck.setIndicatorValue()
        self.lastCheck['indicatorValue'] = self.lastActive
        self.lastCheck.setIndicatorValue()

    def load(self):
        self.notify.debug('load')
        if self.isLoaded == 1:
            return None
        nameBalloon = loader.loadModel('phase_3/models/props/chatbox_input')
        guiButton = loader.loadModel('phase_3/models/gui/quit_button')
        gui = loader.loadModel('phase_3/models/gui/tt_m_gui_mat_nameShop')
        self.arrowUp = gui.find('**/tt_t_gui_mat_namePanelArrowUp')
        self.arrowDown = gui.find('**/tt_t_gui_mat_namePanelArrowDown')
        self.arrowHover = gui.find('**/tt_t_gui_mat_namePanelArrowHover')
        self.squareUp = gui.find('**/tt_t_gui_mat_namePanelSquareUp')
        self.squareDown = gui.find('**/tt_t_gui_mat_namePanelSquareDown')
        self.squareHover = gui.find('**/tt_t_gui_mat_namePanelSquareHover')
        typePanel = gui.find('**/tt_t_gui_mat_typeNamePanel')
        self.typeNamePanel = DirectFrame(parent=aspect2d, image=None, relief='flat', scale=(0.75, 0.7, 0.7), state='disabled', pos=(-0.0163333, 0, 0.075), image_pos=(0, 0, 0.025), frameColor=(1, 1, 1, 0))
        self.typePanelFrame = DirectFrame(image=typePanel, relief='flat', frameColor=(1, 1, 1, 0), pos=(-0.008, 0, 0.019))
        self.typePanelFrame.reparentTo(self.typeNamePanel, sort=1)
        self.typeANameGUIElements.append(self.typeNamePanel)
        self.typeANameGUIElements.append(self.typePanelFrame)
        self.nameLabel = OnscreenText.OnscreenText(TTLocalizer.PleaseTypeName, parent=aspect2d, style=OnscreenText.ScreenPrompt, scale=TTLocalizer.NSnameLabel, pos=(-0.0163333, 0.53))
        self.nameLabel.wrtReparentTo(self.typeNamePanel, sort=2)
        self.typeANameGUIElements.append(self.nameLabel)
        self.typeNotification = OnscreenText.OnscreenText(TTLocalizer.AllNewNames, parent=aspect2d, style=OnscreenText.ScreenPrompt, scale=TTLocalizer.NStypeNotification, pos=(-0.0163333, 0.15))
        self.typeNotification.wrtReparentTo(self.typeNamePanel, sort=2)
        self.typeANameGUIElements.append(self.typeNotification)
        self.nameMessages = OnscreenText.OnscreenText(TTLocalizer.NameMessages, parent=aspect2d, style=OnscreenText.ScreenPrompt, scale=0.06, pos=(-0.0163333, -0.05))
        self.nameMessages.wrtReparentTo(self.typeNamePanel, sort=2)
        self.typeANameGUIElements.append(self.nameMessages)
        self.nameEntry = DirectEntry(parent=aspect2d, relief=None, scale=TTLocalizer.NSnameEntry, entryFont=getToonFont(), width=MAX_NAME_WIDTH, numLines=2, focus=0, cursorKeys=1, pos=(0.0, 0.0, 0.39), text_align=TextNode.ACenter, command=self.__typedAName, autoCapitalize=1)
        self.nameEntry.wrtReparentTo(self.typeNamePanel, sort=2)
        self.typeANameGUIElements.append(self.nameEntry)
        self.submitButton = DirectButton(parent=aspect2d, relief=None, image=(self.squareUp,
         self.squareDown,
         self.squareHover,
         self.squareUp), image_scale=(1.2, 0, 1.1), pos=(-0.01, 0, -0.25), text=TTLocalizer.NameShopSubmitButton, text_scale=0.06, text_pos=(0, -0.02), command=self.__typedAName)
        self.submitButton.wrtReparentTo(self.typeNamePanel, sort=2)
        self.typeNamePanel.setPos(-0.42, 0, -0.078)
        self.typeANameGUIElements.append(self.submitButton)
        self.randomButton = DirectButton(parent=aspect2d, relief=None, image=(self.squareUp,
         self.squareDown,
         self.squareHover,
         self.squareUp), image_scale=(1.15, 1.1, 1.1), scale=(1.05, 1, 1), pos=(0, 0, -0.25), text=TTLocalizer.ShuffleButton, text_scale=0.06, text_pos=(0, -0.02), command=self.__randomName)
        self.pickANameGUIElements.append(self.randomButton)
        self.typeANameButton = DirectButton(parent=aspect2d, relief=None, image=(self.squareUp,
         self.squareDown,
         self.squareHover,
         self.squareUp), image_scale=(1, 1.1, 0.9), pos=(0.0033, 0, -.38833), scale=(1.2, 1, 1.2), text=TTLocalizer.TypeANameButton, text_scale=TTLocalizer.NStypeANameButton, text_pos=TTLocalizer.NStypeANameButtonPos, command=self.__typeAName)
        if base.cr.productName in ['DE', 'BR']:
            self.typeANameButton.hide()
        self.pickANameGUIElements.append(self.typeANameButton)
        self.nameResult = DirectLabel(parent=aspect2d, relief=None, scale=TTLocalizer.NSnameResult, pos=(0.005, 0, 0.585), text=' \n ', text_scale=0.8, text_align=TextNode.ACenter, text_wordwrap=MAX_NAME_WIDTH)
        self.pickANameGUIElements.append(self.nameResult)
        self.allPrefixes = self.nameGen.lastPrefixes[:]
        self.allSuffixes = self.nameGen.lastSuffixes[:]
        self.allPrefixes.sort()
        self.allSuffixes.sort()
        self.allPrefixes = [' '] + [' '] + self.allPrefixes + [' '] + [' ']
        self.allSuffixes = [' '] + [' '] + self.allSuffixes + [' '] + [' ']
        self.titleScrollList = self.makeScrollList(gui, (-0.6, 0, 0.202), (1, 0.8, 0.8, 1), self.allTitles, self.makeLabel, [TextNode.ACenter, 'title'])
        self.firstnameScrollList = self.makeScrollList(gui, (-0.2, 0, 0.202), (0.8, 1, 0.8, 1), self.allFirsts, self.makeLabel, [TextNode.ACenter, 'first'])
        self.lastprefixScrollList = self.makeScrollList(gui, (0.2, 0, 0.202), (0.8, 0.8, 1, 1), self.allPrefixes, self.makeLabel, [TextNode.ARight, 'prefix'])
        self.lastsuffixScrollList = self.makeScrollList(gui, (0.55, 0, 0.202), (0.8, 0.8, 1, 1), self.allSuffixes, self.makeLabel, [TextNode.ALeft, 'suffix'])
        gui.removeNode()
        self.pickANameGUIElements.append(self.lastprefixScrollList)
        self.pickANameGUIElements.append(self.lastsuffixScrollList)
        self.pickANameGUIElements.append(self.titleScrollList)
        self.pickANameGUIElements.append(self.firstnameScrollList)
        self.titleHigh = self.makeHighlight((-0.710367, 0.0, 0.122967))
        self.firstHigh = self.makeHighlight((-0.310367, 0.0, 0.122967))
        self.pickANameGUIElements.append(self.titleHigh)
        self.pickANameGUIElements.append(self.firstHigh)
        self.prefixHigh = self.makeHighlight((0.09, 0.0, 0.122967))
        self.suffixHigh = self.makeHighlight((0.44, 0.0, 0.122967))
        self.pickANameGUIElements.append(self.prefixHigh)
        self.pickANameGUIElements.append(self.suffixHigh)
        nameBalloon.removeNode()
        imageList = (guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR'))
        buttonImage = [imageList, imageList]
        buttonText = [TTLocalizer.NameShopPay, TTLocalizer.NameShopPlay]
        self.payDialog = DirectDialog(dialogName='paystate', topPad=0, fadeScreen=0.2, pos=(0, 0.1, 0.1), button_relief=None, text_align=TextNode.ACenter, text=TTLocalizer.NameShopOnlyPaid, buttonTextList=buttonText, buttonImageList=buttonImage, image_color=GlobalDialogColor, buttonValueList=[1, 0], command=self.payAction)
        self.payDialog.buttonList[0].setPos(0, 0, -.27)
        self.payDialog.buttonList[1].setPos(0, 0, -.4)
        self.payDialog.buttonList[0]['image_scale'] = (1.2, 1, 1.1)
        self.payDialog.buttonList[1]['image_scale'] = (1.2, 1, 1.1)
        self.payDialog['image_scale'] = (0.8, 1, 0.77)
        self.payDialog.buttonList[0]['text_pos'] = (0, -.02)
        self.payDialog.buttonList[1]['text_pos'] = (0, -.02)
        self.payDialog.hide()
        buttonText = [TTLocalizer.NameShopContinueSubmission, TTLocalizer.NameShopChooseAnother]
        self.approvalDialog = DirectDialog(dialogName='approvalstate', topPad=0, fadeScreen=0.2, pos=(0, 0.1, 0.1), button_relief=None, image_color=GlobalDialogColor, text_align=TextNode.ACenter, text=TTLocalizer.NameShopToonCouncil, buttonTextList=buttonText, buttonImageList=buttonImage, buttonValueList=[1, 0], command=self.approvalAction)
        self.approvalDialog.buttonList[0].setPos(0, 0, -.3)
        self.approvalDialog.buttonList[1].setPos(0, 0, -.43)
        self.approvalDialog['image_scale'] = (0.8, 1, 0.77)
        for x in range(0, 2):
            self.approvalDialog.buttonList[x]['text_pos'] = (0, -.01)
            self.approvalDialog.buttonList[x]['text_scale'] = (0.04, 0.05999)
            self.approvalDialog.buttonList[x].setScale(1.2, 1, 1)

        self.approvalDialog.hide()
        guiButton.removeNode()
        self.uberhide(self.typeANameGUIElements)
        self.uberhide(self.pickANameGUIElements)
        self.isLoaded = 1

    def ubershow(self, guiObjectsToShow):
        self.notify.debug('ubershow %s' % str(guiObjectsToShow))
        for x in guiObjectsToShow:
            try:
                x.show()
            except:
                print 'NameShop: Tried to show already removed object'

        if base.cr.productName in ['DE', 'BR']:
            self.typeANameButton.hide()

    def hideAll(self):
        self.uberhide(self.pickANameGUIElements)
        self.uberhide(self.typeANameGUIElements)

    def uberhide(self, guiObjectsToHide):
        self.notify.debug('uberhide %s' % str(guiObjectsToHide))
        for x in guiObjectsToHide:
            try:
                x.hide()
            except:
                print 'NameShop: Tried to hide already removed object'

    def uberdestroy(self, guiObjectsToDestroy):
        self.notify.debug('uberdestroy %s' % str(guiObjectsToDestroy))
        for x in guiObjectsToDestroy:
            try:
                x.destroy()
                del x
            except:
                print 'NameShop: Tried to destroy already removed object'

    def getNameIndices(self):
        return self.nameIndices

    def getNameFlags(self):
        return self.nameFlags

    def getNameAction(self):
        return self.nameAction

    def unload(self):
        self.notify.debug('unload')
        if self.isLoaded == 0:
            return None
        self.exit()
        cleanupDialog('globalDialog')
        self.uberdestroy(self.pickANameGUIElements)
        self.uberdestroy(self.typeANameGUIElements)
        del self.toon
        self.payDialog.cleanup()
        self.approvalDialog.cleanup()
        del self.payDialog
        del self.approvalDialog
        self.parentFSM.getStateNamed('NameShop').removeChild(self.fsm)
        del self.parentFSM
        del self.fsm
        self.ignoreAll()
        self.isLoaded = 0
        self.makeAToon = None

    def _checkNpcNames(self, name):

        def match(npcName, name = name):
            name = TextEncoder().encodeWtext(name)
            name = string.strip(name)
            return TextEncoder.upper(npcName) == TextEncoder.upper(name)

        for npcId in NPCToons.NPCToonDict.keys():
            npcName = NPCToons.NPCToonDict[npcId][1]
            if match(npcName):
                self.notify.info('name matches NPC name "%s"' % npcName)
                return TTLocalizer.NCGeneric

    def nameIsValid(self, name):
        self.notify.debug('nameIsValid')
        if name in self.usedNames:
            return TTLocalizer.ToonAlreadyExists % name
        problem = NameCheck.checkName(name, [self._checkNpcNames], font=self.nameEntry.getFont())
        if problem:
            return problem
        return None

    def setShopsVisited(self, list):
        self.shopsVisited = list

    def __handleDone(self):
        if self.fsm.getCurrentState().getName() == 'TypeAName':
            self.__typedAName()
        else:
            self.__isFirstTime()

    def __handleSkipTutorial(self):
        self.__createAvatar(skipTutorial=True)

    def __handleBackward(self):
        self.doneStatus = 'last'
        messenger.send(self.doneEvent)

    def __handleChastised(self):
        self.chastiseDialog.cleanup()

    def __createAvatar(self, skipTutorial = False, *args):
        self.notify.debug('__createAvatar')
        if self.fsm.getCurrentState().getName() == 'TypeAName':
            self.__typedAName()
            return
        if not self.avExists or self.avExists and self.avId == 'deleteMe':
            self.serverCreateAvatar(skipTutorial)
        elif self.names[0] == '':
            self.rejectName(TTLocalizer.EmptyNameError)
        else:
            rejectReason = self.nameIsValid(self.names[0])
            if rejectReason != None:
                self.rejectName(rejectReason)
            else:
                self.checkNamePattern()
        return

    def acceptName(self):
        self.notify.debug('acceptName')
        self.toon.setName(self.names[0])
        self.doneStatus = 'done'
        self.storeSkipTutorialRequest()
        messenger.send(self.doneEvent)

    def rejectName(self, str):
        self.notify.debug('rejectName')
        self.names[0] = ''
        self.rejectDialog = TTDialog.TTGlobalDialog(doneEvent='rejectDone', message=str, style=TTDialog.Acknowledge)
        self.rejectDialog.show()
        self.acceptOnce('rejectDone', self.__handleReject)

    def __handleReject(self):
        self.rejectDialog.cleanup()
        self.nameEntry['focus'] = 1
        self.typeANameButton.show()
        self.acceptOnce('next', self.__handleDone)

    def restoreIndexes(self, oi):
        self.titleIndex = oi[0]
        self.firstIndex = oi[1]
        self.prefixIndex = oi[2]
        self.suffixIndex = oi[3]

    def stealth(self, listToDo):
        listToDo.decButton['state'] = 'disabled'
        listToDo.incButton['state'] = 'disabled'
        for item in listToDo['items']:
            if item.__class__.__name__ != 'str':
                item.hide()

    def showList(self, listToDo):
        listToDo.show()
        listToDo.decButton['state'] = 'normal'
        listToDo.incButton['state'] = 'normal'

    def updateLists(self):
        oldindex = [self.titleIndex,
         self.firstIndex,
         self.prefixIndex,
         self.suffixIndex]
        self.titleScrollList.scrollTo(self.titleIndex - 2)
        self.restoreIndexes(oldindex)
        self.firstnameScrollList.scrollTo(self.firstIndex - 2)
        self.restoreIndexes(oldindex)
        self.lastprefixScrollList.scrollTo(self.prefixIndex - 2)
        self.restoreIndexes(oldindex)
        self.lastsuffixScrollList.scrollTo(self.suffixIndex - 2)
        self.restoreIndexes(oldindex)

    def __randomName(self):
        self.notify.debug('Finding random name')
        uberReturn = self.nameGen.randomNameMoreinfo(self.boy, self.girl)
        flags = uberReturn[:3]
        names = uberReturn[3:7]
        fullName = uberReturn[-1]
        self._updateGuiWithPickAName(flags, names, fullName)

    def _updateGuiWithPickAName(self, flags, names, fullName):
        uberReturn = flags + names + [fullName]
        self.names[0] = uberReturn[len(uberReturn) - 1]
        self.titleActive = 0
        self.firstActive = 0
        self.lastActive = 0
        if uberReturn[0]:
            self.titleActive = 1
        if uberReturn[1]:
            self.firstActive = 1
        if uberReturn[2]:
            self.lastActive = 1
        try:
            self.titleIndex = self.allTitles.index(uberReturn[3])
            self.nameIndices[0] = self.nameGen.returnUniqueID(uberReturn[3], 0)
            self.nameFlags[0] = 1
        except:
            print 'NameShop : Should have found title, uh oh!'
            print uberReturn

        try:
            self.firstIndex = self.allFirsts.index(uberReturn[4])
            self.nameIndices[1] = self.nameGen.returnUniqueID(uberReturn[4], 1)
            self.nameFlags[1] = 1
        except:
            print 'NameShop : Should have found first name, uh oh!'
            print uberReturn

        try:
            self.prefixIndex = self.allPrefixes.index(uberReturn[5])
            self.suffixIndex = self.allSuffixes.index(uberReturn[6].lower())
            self.nameIndices[2] = self.nameGen.returnUniqueID(uberReturn[5], 2)
            self.nameIndices[3] = self.nameGen.returnUniqueID(uberReturn[6].lower(), 3)
            if uberReturn[5] in self.nameGen.capPrefixes:
                self.nameFlags[3] = 1
            else:
                self.nameFlags[3] = 0
        except:
            print 'NameShop : Some part of last name not found, uh oh!'
            print uberReturn

        self.updateCheckBoxes()
        self.updateLists()
        self.nameResult['text'] = self.names[0]

    def findTempName(self):
        colorstring = TTLocalizer.NumToColor[self.toon.style.headColor]
        animaltype = TTLocalizer.AnimalToSpecies[self.toon.style.getAnimal()]
        tempname = colorstring + ' ' + animaltype
        if not TTLocalizer.NScolorPrecede:
            tempname = animaltype + ' ' + colorstring
        self.names[0] = tempname
        tempname = '"' + tempname + '"'
        return tempname

    def enterInit(self):
        self.notify.debug('enterInit')

    def exitInit(self):
        pass

    def enterPayState(self):
        self.notify.debug('enterPayState')
        if base.cr.allowFreeNames() or self.isPaid:
            self.fsm.request('PickAName')
        else:
            tempname = self.findTempName()
            self.payDialog['text'] = TTLocalizer.NameShopOnlyPaid + tempname
            self.payDialog.show()

    def exitPayState(self):
        pass

    def payAction(self, value):
        self.notify.debug('payAction')
        self.payDialog.hide()
        if value:
            self.doneStatus = 'paynow'
            messenger.send(self.doneEvent)
        else:
            self.nameAction = 0
            self.__createAvatar()

    def enterPickANameState(self):
        self.notify.debug('enterPickANameState')
        self.ubershow(self.pickANameGUIElements)
        self.nameAction = 1
        self.__listsChanged()

    def exitPickANameState(self):
        self.uberhide(self.pickANameGUIElements)

    def enterTypeANameState(self):
        self.notify.debug('enterTypeANameState')
        self.ubershow(self.typeANameGUIElements)
        self.typeANameButton.show()
        self.typeANameButton.wrtReparentTo(aspect2d, sort=2)
        self.nameEntry.set('')
        self.nameEntry['focus'] = 1

    def __typeAName(self):
        if base.cr.productName in ['JP',
         'DE',
         'BR',
         'FR']:
            if base.restrictTrialers:
                if not base.cr.isPaid():
                    dialog = TeaserPanel.TeaserPanel(pageName='typeAName')
                    return
        if self.fsm.getCurrentState().getName() == 'TypeAName':
            self.typeANameButton['text'] = TTLocalizer.TypeANameButton
            self.typeANameButton.wrtReparentTo(self.namePanel, sort=2)
            self.fsm.request('PickAName')
        else:
            self.typeANameButton['text'] = TTLocalizer.PickANameButton
            self.typeANameButton.wrtReparentTo(aspect2d, sort=2)
            self.typeANameButton.show()
            self.fsm.request('TypeAName')

    def __typedAName(self, *args):
        self.notify.debug('__typedAName')
        self.nameEntry['focus'] = 0
        name = self.nameEntry.get()
        name = TextEncoder().decodeText(name)
        name = name.strip()
        name = TextEncoder().encodeWtext(name)
        self.nameEntry.enterText(name)
        problem = self.nameIsValid(self.nameEntry.get())
        if problem:
            self.rejectName(problem)
            return
        self.checkNameTyped(justCheck=True)

    def exitTypeANameState(self):
        self.typeANameButton.wrtReparentTo(self.namePanel, sort=2)
        self.uberhide(self.typeANameGUIElements)

    def enterApprovalState(self):
        self.notify.debug('enterApprovalState')
        tempname = self.findTempName()
        self.approvalDialog['text'] = TTLocalizer.NameShopToonCouncil + tempname
        self.approvalDialog.show()

    def approvalAction(self, value):
        self.notify.debug('approvalAction')
        self.approvalDialog.hide()
        if value:
            self.nameAction = 2
            if not self.makeAToon.warp:
                self.__isFirstTime()
            else:
                self.serverCreateAvatar()
        else:
            self.typeANameButton['text'] = TTLocalizer.TypeANameButton
            self.fsm.request('PickAName')

    def exitApprovalState(self):
        pass

    def enterApprovalAcceptedState(self):
        self.notify.debug('enterApprovalAcceptedState')
        self.doneStatus = 'done'
        self.storeSkipTutorialRequest()
        messenger.send(self.doneEvent)

    def exitApprovalAcceptedState(self):
        pass

    def enterAcceptedState(self):
        self.notify.debug('enterAcceptedState')
        self.acceptedDialog = TTDialog.TTGlobalDialog(doneEvent='acceptedDone', message=TTLocalizer.NameShopNameAccepted, style=TTDialog.Acknowledge)
        self.acceptedDialog.show()
        self.acceptOnce('acceptedDone', self.__handleAccepted)

    def __handleAccepted(self):
        self.acceptedDialog.cleanup()
        self.doneStatus = 'done'
        self.storeSkipTutorialRequest()
        messenger.send(self.doneEvent)

    def exitAcceptedState(self):
        pass

    def enterRejectedState(self):
        self.notify.debug('enterRejectedState')
        self.rejectedDialog = TTDialog.TTGlobalDialog(doneEvent='rejectedDone', message=TTLocalizer.NameShopNameRejected, style=TTDialog.Acknowledge)
        self.rejectedDialog.show()
        self.acceptOnce('rejectedDone', self.__handleRejected)

    def __handleRejected(self):
        self.rejectedDialog.cleanup()
        self.fsm.request('TypeAName')

    def exitRejectedState(self):
        pass

    def enterDone(self):
        self.notify.debug('enterDone')
        return None

    def exitDone(self):
        return None

    def nameShopHandler(self, msgType, di):
        self.notify.debug('nameShopHandler')
        if msgType == CLIENT_CREATE_AVATAR_RESP:
            self.handleCreateAvatarResponseMsg(di)
        elif msgType == CLIENT_SET_NAME_PATTERN_ANSWER:
            self.handleSetNamePatternAnswerMsg(di)
        elif msgType == CLIENT_SET_WISHNAME_RESP:
            self.handleSetNameTypedAnswerMsg(di)
        return None

    def checkNamePattern(self):
        self.notify.debug('checkNamePattern')
        datagram = PyDatagram()
        datagram.addUint16(CLIENT_SET_NAME_PATTERN)
        datagram.addUint32(self.avId)
        datagram.addInt16(self.nameIndices[0])
        datagram.addInt16(self.nameFlags[0])
        datagram.addInt16(self.nameIndices[1])
        datagram.addInt16(self.nameFlags[1])
        datagram.addInt16(self.nameIndices[2])
        datagram.addInt16(self.nameFlags[2])
        datagram.addInt16(self.nameIndices[3])
        datagram.addInt16(self.nameFlags[3])
        messenger.send('nameShopPost', [datagram])
        self.waitForServer()

    def handleSetNamePatternAnswerMsg(self, di):
        self.notify.debug('handleSetNamePatternAnswerMsg')
        self.cleanupWaitForServer()
        newavId = di.getUint32()
        if newavId != self.avId:
            self.notify.debug("doid's don't match up!")
            self.rejectName(TTLocalizer.NameError)
        returnCode = di.getUint8()
        if returnCode == 0:
            style = self.toon.getStyle()
            avDNA = style.makeNetString()
            self.notify.debug('pattern name accepted')
            newPotAv = PotentialAvatar.PotentialAvatar(newavId, self.names, avDNA, self.index, 0)
            self.avList.append(newPotAv)
            self.doneStatus = 'done'
            self.storeSkipTutorialRequest()
            messenger.send(self.doneEvent)
        else:
            self.notify.debug('name pattern rejected')
            self.rejectName(TTLocalizer.NameError)
        return None

    def _submitTypeANameAsPickAName(self):
        pnp = TTPickANamePattern(self.nameEntry.get(), self.toon.style.gender)
        if pnp.hasNamePattern():
            pattern = pnp.getNamePattern()
            self.fsm.request('PickAName')
            flags = [pattern[0] != -1, pattern[1] != -1, pattern[2] != -1]
            names = []
            for i in xrange(len(pattern)):
                if pattern[i] != -1:
                    names.append(pnp.getNamePartString(self.toon.style.gender, i, pattern[i]))
                else:
                    names.append('')

            fullName = pnp.getNameString(pattern, self.toon.style.gender)
            self._updateGuiWithPickAName(flags, names, fullName)
            self.__handleDone()
            return True
        return False

    def checkNameTyped(self, justCheck = False):
        self.notify.debug('checkNameTyped')
        if self._submitTypeANameAsPickAName():
            return
        datagram = PyDatagram()
        datagram.addUint16(CLIENT_SET_WISHNAME)
        if justCheck:
            avId = 0
        else:
            avId = self.avId
        datagram.addUint32(avId)
        datagram.addString(self.nameEntry.get())
        messenger.send('nameShopPost', [datagram])
        self.waitForServer()

    def handleSetNameTypedAnswerMsg(self, di):
        self.notify.debug('handleSetNameTypedAnswerMsg')
        self.cleanupWaitForServer()
        newavId = di.getUint32()
        if newavId and newavId != self.avId:
            self.notify.debug("doid's don't match up!")
            self.rejectName(TTLocalizer.NameError)
        returnCode = di.getUint16()
        if newavId == 0:
            if returnCode == 0:
                pendingname = di.getString()
                approvedname = di.getString()
                rejectedname = di.getString()
                if pendingname != '':
                    self.notify.debug('name check pending')
                    self.fsm.request('Approval')
                elif approvedname != '':
                    self.notify.debug('name check accepted')
                    self.nameAction = 2
                    self.serverCreateAvatar()
                elif rejectedname != '':
                    self.notify.debug('name check rejected')
                    self.fsm.request('TypeAName')
                    self.rejectName(TTLocalizer.NameError)
                else:
                    self.notify.debug('typed name response did not contain any return fields')
                    self.rejectName(TTLocalizer.NameError)
        elif returnCode == 0:
            wishname = di.getString()
            approvedname = di.getString()
            rejectedname = di.getString()
            if approvedname != '':
                style = self.toon.getStyle()
                avDNA = style.makeNetString()
                self.names[0] = self.nameEntry.get()
                self.notify.debug('typed name accepted')
                newPotAv = PotentialAvatar.PotentialAvatar(newavId, self.names, avDNA, self.index, 0)
                self.avList.append(newPotAv)
                self.fsm.request('Accepted')
            elif wishname != '':
                style = self.toon.getStyle()
                avDNA = style.makeNetString()
                self.names[1] = self.nameEntry.get()
                self.notify.debug('typed name needs approval')
                newPotAv = PotentialAvatar.PotentialAvatar(newavId, self.names, avDNA, self.index, 1)
                if not self.newwarp:
                    self.avList.append(newPotAv)
                self.fsm.request('ApprovalAccepted')
            elif rejectedname != '':
                self.fsm.request('Rejected')
            else:
                self.notify.debug("name typed accepted but didn't fill any return fields")
                self.rejectName(TTLocalizer.NameError)
        else:
            self.notify.debug('name typed rejected')
            self.rejectName(TTLocalizer.NameError)
        return None

    def serverCreateAvatar(self, skipTutorial = False):
        self.notify.debug('serverCreateAvatar')
        style = self.toon.getStyle()
        self.newDNA = style.makeNetString()
        if skipTutorial:
            self.requestingSkipTutorial = True
        else:
            self.requestingSkipTutorial = False
        if not self.avExists or self.avExists and self.avId == 'deleteMe':
            messenger.send('nameShopCreateAvatar', [style, '', self.index])
        else:
            self.checkNameTyped()
        self.notify.debug('Ending Make A Toon: %s' % self.toon.style)
        base.cr.centralLogger.writeClientEvent('MAT - endingMakeAToon: %s' % self.toon.style)

    def handleCreateAvatarResponseMsg(self, di):
        self.notify.debug('handleCreateAvatarResponseMsg')
        echoContext = di.getUint16()
        returnCode = di.getUint8()
        if returnCode == 0:
            self.notify.debug('avatar with default name accepted')
            self.avId = di.getUint32()
            self.avExists = 1
            self.logAvatarCreation()
            if self.nameAction == 0:
                self.toon.setName(self.names[0])
                newPotAv = PotentialAvatar.PotentialAvatar(self.avId, self.names, self.newDNA, self.index, 1)
                self.avList.append(newPotAv)
                self.doneStatus = 'done'
                self.storeSkipTutorialRequest()
                messenger.send(self.doneEvent)
            elif self.nameAction == 1:
                self.checkNamePattern()
            elif self.nameAction == 2:
                self.checkNameTyped()
            else:
                self.notify.debug('avatar invalid nameAction')
                self.rejectName(TTLocalizer.NameError)
        else:
            self.notify.debug('avatar rejected')
            self.rejectName(TTLocalizer.NameError)
        return None

    def waitForServer(self):
        self.waitForServerDialog = TTDialog.TTDialog(text=TTLocalizer.WaitingForNameSubmission, style=TTDialog.NoButtons)
        self.waitForServerDialog.show()

    def cleanupWaitForServer(self):
        if self.waitForServerDialog != None:
            self.waitForServerDialog.cleanup()
            self.waitForServerDialog = None
        return

    def printTypeANameInfo(self, str):
        sourceFilename, lineNumber, functionName = PythonUtil.stackEntryInfo(1)
        self.notify.debug('========================================\n%s : %s :  %s' % (sourceFilename, lineNumber, functionName))
        self.notify.debug(str)
        curPos = self.typeANameButton.getPos()
        self.notify.debug('Pos = %.2f %.2f %.2f' % (curPos[0], curPos[1], curPos[2]))
        parent = self.typeANameButton.getParent()
        parentPos = parent.getPos()
        self.notify.debug('Parent = %s' % parent)
        self.notify.debug('ParentPos = %.2f %.2f %.2f' % (parentPos[0], parentPos[1], parentPos[2]))

    def storeSkipTutorialRequest(self):
        base.cr.skipTutorialRequest = self.requestingSkipTutorial

    def __isFirstTime(self):
        if not self.makeAToon.nameList or self.makeAToon.warp:
            self.__createAvatar()
        else:
            self.promptTutorial()

    def promptTutorial(self):
        self.promptTutorialDialog = TTDialog.TTDialog(parent=aspect2dp, text=TTLocalizer.PromptTutorial, text_scale=0.06, text_align=TextNode.ACenter, text_wordwrap=22, command=self.__openTutorialDialog, fadeScreen=0.5, style=TTDialog.TwoChoice, buttonTextList=[TTLocalizer.MakeAToonEnterTutorial, TTLocalizer.MakeAToonSkipTutorial], button_text_scale=0.06, buttonPadSF=5.5, sortOrder=NO_FADE_SORT_INDEX)
        self.promptTutorialDialog.show()

    def __openTutorialDialog(self, choice = 0):
        if choice == 1:
            self.notify.debug('enterTutorial')
            if base.config.GetBool('want-qa-regression', 0):
                self.notify.info('QA-REGRESSION: ENTERTUTORIAL: Enter Tutorial')
            self.__createAvatar()
        else:
            self.notify.debug('skipTutorial')
            if base.config.GetBool('want-qa-regression', 0):
                self.notify.info('QA-REGRESSION: SKIPTUTORIAL: Skip Tutorial')
            self.__handleSkipTutorial()
        self.promptTutorialDialog.destroy()

    def logAvatarCreation(self):
        dislId = 0
        try:
            dislId = launcher.getValue('GAME_DISL_ID')
        except:
            pass

        if not dislId:
            self.notify.warning('No dislId, using 0')
            dislId = 0
        gameSource = '0'
        try:
            gameSource = launcher.getValue('GAME_SOURCE')
        except:
            pass

        if not gameSource:
            gameSource = '0'
        else:
            self.notify.info('got GAME_SOURCE=%s' % gameSource)
        if self.avId > 0:
            base.cr.centralLogger.writeClientEvent('createAvatar %s-%s-%s' % (self.avId, dislId, gameSource))
            self.notify.debug('createAvatar %s-%s-%s' % (self.avId, dislId, gameSource))
        else:
            self.notify.warning('logAvatarCreation got self.avId =%s' % self.avId)
