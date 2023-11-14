"""NameShop module: contains the NameShop class"""

from toontown.toonbase.ToontownGlobals import *
from direct.task.TaskManagerGlobal import *
from direct.gui.DirectGui import *
from panda3d.core import *
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
from . import NameGenerator
import random
from otp.distributed import PotentialAvatar
from otp.namepanel import NameCheck
from toontown.toontowngui import TeaserPanel
from direct.distributed.PyDatagram import PyDatagram
from direct.showbase import PythonUtil
from toontown.toon import NPCToons
from direct.task import Task
from toontown.makeatoon.TTPickANamePattern import TTPickANamePattern
from panda3d.core import TextEncoder

MAX_NAME_WIDTH = TTLocalizer.NSmaxNameWidth

ServerDialogTimeout = 3.0


class NameShop(StateData.StateData):
    """NameShop class: contains methods for setting the Avatar's
    name via user input"""

    notify = DirectNotifyGlobal.directNotify.newCategory("NameShop")
    # notify.setDebug(True)

    def __init__(self, makeAToon, doneEvent, avList, index, isPaid):
        """__init__(self, ClassicFSM, Event)
        Set-up the name shop interface to pick a name for the given toon
        """
        StateData.StateData.__init__(self, doneEvent)

        self.makeAToon = makeAToon
        self.isPaid = 1

        self.avList = avList
        self.index = index
        self.shopsVisited = []
        self.avId = -1
        # test
        self.avExists = 0

        # names is a list of the toon's name, wantName, approvedName, and
        # rejectedName
        # name is distributed while the other three are specialized for
        # makeatoon process
        self.names = ["", "", "", ""]
        self.toon = None

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
        self.chastise = 0    # If this is 1 or 2, mickey has chastised you!
        self.nameIndices = [-1, -1, -1, -1]
        self.nameFlags = [1, 1, 1, 0]
        self.dummyReturn = 2

        # nameAction tells makeAToon what is expected of it:
        #  0 - No payment/pending approval/accepted,
        #  1 - Indices given
        self.nameAction = 0

        self.pickANameGUIElements = []
        self.typeANameGUIElements = []

        self.textRolloverColor = Vec4(1, 1, 0, 1)
        self.textDownColor = Vec4(0.5, 0.9, 1, 1)
        self.textDisabledColor = Vec4(0.4, 0.8, 0.4, 1)

        # Add an fsm to NameShop to handle PayState, PickAName, TypeAName,
        #   NameAccepted, NameRejected, and ToonCouncil
        self.fsm = ClassicFSM.ClassicFSM('NameShop',
                                         [State.State('Init',
                                                      self.enterInit,
                                                      self.exitInit,
                                                      ['PayState']),
                                             State.State('PayState',
                                                         self.enterPayState,
                                                         self.exitPayState,
                                                         ['PickAName']),
                                             State.State('PickAName',
                                                         self.enterPickANameState,
                                                         self.exitPickANameState,
                                                         ['TypeAName', 'Done']),
                                             State.State('TypeAName',
                                                         self.enterTypeANameState,
                                                         self.exitTypeANameState,
                                                         ['PickAName', 'Approval',
                                                          'Accepted', 'Rejected']),
                                             State.State('Approval',
                                                         self.enterApprovalState,
                                                         self.exitApprovalState,
                                                         ['PickAName', 'ApprovalAccepted']),
                                             State.State('ApprovalAccepted',
                                                         self.enterApprovalAcceptedState,
                                                         self.exitApprovalAcceptedState,
                                                         ['Done']),
                                             State.State('Accepted',
                                                         self.enterAcceptedState,
                                                         self.exitAcceptedState,
                                                         ['Done']),
                                             State.State('Rejected',
                                                         self.enterRejectedState,
                                                         self.exitRejectedState,
                                                         ['TypeAName']),
                                             State.State('Done',
                                                         self.enterDone,
                                                         self.exitDone,
                                                         ['Init'])],
                                         # Initial state
                                         'Init',
                                         # Final state
                                         'Done',
                                         )

        self.parentFSM = makeAToon.fsm
        self.parentFSM.getStateNamed('NameShop').addChild(self.fsm)

        # Random name generator
        self.nameGen = NameGenerator.NameGenerator()

        self.fsm.enterInitialState()
        self.requestingSkipTutorial = False
        self.namePanel = None
        return None

    def makeLabel(self, te, index, others):
        """Used to create the frames for names in all 4 scrolled lists
        """
        alig = others[0]
        listName = others[1]

        if alig == TextNode.ARight:
            newpos = (.44, 0, 0)
        elif alig == TextNode.ALeft:
            newpos = (0, 0, 0)
        else:
            newpos = (.2, 0, 0)
        df = DirectFrame(
            state='normal',
            relief=None,
            text=te,
            text_scale=TTLocalizer.NSmakeLabel,
            text_pos=newpos,
            text_align=alig,
            textMayChange=0,
        )
        df.bind(DGG.B1PRESS, lambda x, df=df: self.nameClickedOn(listName, index))
        return df

    def nameClickedOn(self, listType, index):
        """If a name in one of the scrolled lists is clicked on,
        snap it to center
        """
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
        """enter(self, toon)
        """
        self.notify.debug('enter')
        self.newwarp = warp
        self.avExists = warp
        if self.avExists:
            for g in self.avList:
                if g.position == self.index:
                    self.avId = g.id

        if toon is None:
            return None
        else:
            self.toon = toon
            # if (self.toon.style.gender == 'm'):
            #    self.boy = 1
            #    self.girl = 0
            # else:
            #self.boy = 0
            #self.girl = 1

        self.usedNames = usedNames

        # We were able to add last names in the load function but to add
        #   titles and first names I needed to know gender
        #   Also, run again if gender has changed
        # self.oldBoy = self.boy
        self.listsLoaded = 0

        # Fill titleScrollList
        self.allTitles = [" "] + [" "] + self.nameGen.boyTitles + \
            self.nameGen.girlTitles + \
            self.nameGen.neutralTitles
        self.allTitles.sort()
        self.allTitles += [" "] + [" "]

        # Fill firstnameScrollList
        self.allFirsts = [" "] + [" "] + self.nameGen.boyFirsts + \
            self.nameGen.girlFirsts + \
            self.nameGen.neutralFirsts
        self.allFirsts.sort()
        self.allFirsts += [" "] + [" "]
        try:
            k = self.allFirsts.index("Von")
            self.allFirsts[k] = "von"
        except BaseException:
            print("NameShop: Couldn't find von")

        nameShopGui = loader.loadModel("phase_3/models/gui/tt_m_gui_mat_nameShop")
        self.namePanel = DirectFrame(
            parent=aspect2d,
            image=None,
            relief='flat',
            state='disabled',
            pos=(-0.42, 0, -0.15),
            image_pos=(0, 0, 0.025),
            frameColor=(1, 1, 1, 0.3),
        )

        panel = nameShopGui.find("**/tt_t_gui_mat_namePanel")
        self.panelFrame = DirectFrame(
            image=panel,
            scale=(.75, .7, .7),
            relief='flat',
            frameColor=(1, 1, 1, 0),
            pos=(-0.0163, 0, 0.1199)
        )
        self.panelFrame.reparentTo(self.namePanel, sort=1)

        self.pickANameGUIElements.append(self.namePanel)
        self.pickANameGUIElements.append(self.panelFrame)
        self.nameResult.reparentTo(self.namePanel, sort=2)

        # Add check boxes!
        self.circle = nameShopGui.find("**/tt_t_gui_mat_namePanelCircle")
        self.titleCheck = self.makeCheckBox(
            (-0.615, 0, 0.371), TTLocalizer.TitleCheckBox,
            (0, 0.25, 0.5, 1), self.titleToggle)
        self.firstCheck = self.makeCheckBox(
            (-0.2193, 0, 0.371), TTLocalizer.FirstCheckBox,
            (0, 0.25, 0.5, 1), self.firstToggle)
        self.lastCheck = self.makeCheckBox(
            (0.3886, 0, 0.371), TTLocalizer.LastCheckBox,
            (0, 0.25, 0.5, 1), self.lastToggle)

        # Don't attempt to remove the circle, since it's just a
        # reference to a node within the nameShopGui hierarchy.
        # self.circle.removeNode()
        del self.circle

        # Make the check buttons pretty
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

        self.titleScrollList = self.makeScrollList(
            None, (-0.6, 0, 0.202),
            (1, 0.80, .80, 1), self.allTitles,
            self.makeLabel,
            [TextNode.ACenter, 'title'])
        self.firstnameScrollList = self.makeScrollList(
            None, (-0.2, 0, 0.202),
            (0.80, 1, .80, 1), self.allFirsts,
            self.makeLabel,
            [TextNode.ACenter, 'first'])
        self.pickANameGUIElements.append(self.titleScrollList)
        self.pickANameGUIElements.append(self.firstnameScrollList)

        self.titleScrollList.reparentTo(self.namePanel, sort=-1)
        self.titleScrollList.decButton.wrtReparentTo(self.namePanel, sort=2)
        self.titleScrollList.incButton.wrtReparentTo(self.namePanel, sort=2)
        self.firstnameScrollList.reparentTo(self.namePanel, sort=-1)
        self.firstnameScrollList.decButton.wrtReparentTo(self.namePanel, sort=2)
        self.firstnameScrollList.incButton.wrtReparentTo(self.namePanel, sort=2)

        # If you're doing this you'd better make the highlights
        # again so they're on top
        self.listsLoaded = 1
        self.__randomName()

        # if we have re-entered make sure the Type/Pick button is labelled correctly
        self.typeANameButton['text'] = TTLocalizer.TypeANameButton

        if self.isLoaded == 0:
            self.load()

        self.ubershow(self.pickANameGUIElements)

        # set up the "done" button
        self.acceptOnce("next", self.__handleDone)
        self.acceptOnce("last", self.__handleBackward)
        self.acceptOnce("skipTutorial", self.__handleSkipTutorial)

        self.__listsChanged()

        self.fsm.request("PayState")
        return None

    def __overflowNameInput(self):
        self.rejectName(TTLocalizer.NameTooLong)

    def exit(self):
        """exit(self)
        Remove events and restore display
        """
        self.notify.debug('exit')
        if self.isLoaded == 0:
            return None

        self.ignore("next")
        self.ignore("last")
        self.ignore("skipTutorial")

        self.hideAll()
        return None

    def __listsChanged(self):
        """Called if a scroll list or checkbox is changed, or a name clicked
           Updates the nameResult with the current status of the four lists
           """

        newname = ""
        if self.listsLoaded:
            if self.titleActive:
                self.showList(self.titleScrollList)
                self.titleHigh.show()
                newtitle = self.titleScrollList['items'][
                    self.titleScrollList.index + 2]['text']
                self.nameIndices[0] = self.nameGen.returnUniqueID(newtitle, 0)
                newname += newtitle + " "
            else:
                self.nameIndices[0] = -1
                self.stealth(self.titleScrollList)
                self.titleHigh.hide()

            if self.firstActive:
                self.showList(self.firstnameScrollList)
                self.firstHigh.show()
                newfirst = self.firstnameScrollList['items'][
                    self.firstnameScrollList.index + 2]['text']
                if newfirst == "von":
                    nt = "Von"
                else:
                    nt = newfirst
                self.nameIndices[1] = self.nameGen.returnUniqueID(nt, 1)
                if not self.titleActive and newfirst == 'von':
                    newfirst = "Von"
                    newname += newfirst
                else:
                    newname += newfirst
                if newfirst == 'von':
                    self.nameFlags[1] = 0
                else:
                    self.nameFlags[1] = 1
                if self.lastActive:
                    newname += " "

            else:
                self.firstHigh.hide()
                self.stealth(self.firstnameScrollList)
                self.nameIndices[1] = -1

            if self.lastActive:
                self.showList(self.lastprefixScrollList)
                self.showList(self.lastsuffixScrollList)
                self.prefixHigh.show()
                self.suffixHigh.show()
                lp = self.lastprefixScrollList['items'][
                    self.lastprefixScrollList.index + 2]['text']
                ls = self.lastsuffixScrollList['items'][
                    self.lastsuffixScrollList.index + 2]['text']
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

    def makeScrollList(self, gui, ipos, mcolor, nitems,
                       nitemMakeFunction, nitemMakeExtraArgs):
        self.notify.debug("makeScrollList")
        #self.notify.debug("makeScrollList - items %s" % str(nitems))
        """Creates a scrolled list at position ipos and with color mcolor
        """
        it = nitems[:]
        ds = DirectScrolledList(
            items=it,
            itemMakeFunction=nitemMakeFunction,
            itemMakeExtraArgs=nitemMakeExtraArgs,
            parent=aspect2d,
            relief=None,
            command=self.__listsChanged,
            pos=ipos,
            scale=(.6),
            # inc and dec are DirectButtons
            incButton_image=(self.arrowUp, self.arrowDown, self.arrowHover, self.arrowUp),
            incButton_relief=None,
            incButton_scale=(1.2, 1.2, -1.2),
            incButton_pos=(0.0189, 0, -0.5335),
            incButton_image0_color=mcolor,
            incButton_image1_color=mcolor,
            incButton_image2_color=mcolor,
            # Make the disabled button fade out
            incButton_image3_color=Vec4(1, 1, 1, 0),
            decButton_image=(self.arrowUp, self.arrowDown, self.arrowHover, self.arrowUp),
            decButton_relief=None,
            decButton_scale=(1.2, 1.2, 1.2),
            decButton_pos=(0.0195, 0, 0.1779),
            decButton_image0_color=mcolor,
            decButton_image1_color=mcolor,
            decButton_image2_color=mcolor,
            # Make the disabled button fade out
            decButton_image3_color=Vec4(1, 1, 1, 0),
            # itemFrame is a DirectFrame used to hold all the items
            itemFrame_pos=(-.2, 0, 0.028),
            itemFrame_scale=1.0,
            itemFrame_relief=DGG.RAISED,
            itemFrame_frameSize=(-0.07, 0.5, -0.52, 0.12),
            itemFrame_frameColor=mcolor,
            itemFrame_borderWidth=(0.01, 0.01),
            numItemsVisible=5,
        )
        return ds

    def makeCheckBox(self, npos, ntex, ntexcolor, comm):
        return DirectCheckButton(
            parent=aspect2d,
            relief=None,
            scale=.1,
            boxBorder=0.08,
            boxImage=self.circle,
            boxImageScale=4,
            boxImageColor=VBase4(0, 0.25, 0.5, 1),
            boxRelief=None,
            pos=npos,
            text=ntex,
            text_fg=ntexcolor,
            text_scale=TTLocalizer.NSmakeCheckBox,
            text_pos=(0.2, 0),
            indicator_pos=(-0.566667, 0, -0.045),
            indicator_image_pos=(-0.26, 0, 0.075),
            command=comm,
            text_align=TextNode.ALeft,
        )

    def makeHighlight(self, npos):
        return DirectFrame(
            parent=aspect2d,
            relief='flat',
            scale=(.552, 0, .11),
            state='disabled',
            frameSize=(-0.07, 0.52, -0.5, 0.1),
            borderWidth=(0.01, 0.01),
            pos=npos,
            frameColor=(1, 0, 1, .4),
        )

    def titleToggle(self, value):
        """ Toggles titleCheck
        """
        self.titleActive = self.titleCheck['indicatorValue']
        if not (self.titleActive or self.firstActive or self.lastActive):
            self.titleActive = 1
        self.__listsChanged()
        if self.titleActive:
            self.titleScrollList.refresh()
        self.updateCheckBoxes()

    def firstToggle(self, value):
        """ Toggles firstCheck making sure lastCheck is active
        """
        self.firstActive = self.firstCheck['indicatorValue']
        if self.chastise == 2:
            messenger.send("NameShop-mickeyChange",
                           [[TTLocalizer.ApprovalForName1,
                             TTLocalizer.ApprovalForName2]])
            self.chastise = 0
        if not (self.firstActive or self.lastActive):
            self.firstActive = 1
            messenger.send("NameShop-mickeyChange",
                           [[TTLocalizer.MustHaveAFirstOrLast1,
                             TTLocalizer.MustHaveAFirstOrLast2]])
            self.chastise = 1
        self.__listsChanged()
        if self.firstActive:
            self.firstnameScrollList.refresh()
        self.updateCheckBoxes()

    def lastToggle(self, value):
        """ Toggles lastCheck making sure firstCheck is active
        """
        self.lastActive = self.lastCheck['indicatorValue']
        if self.chastise == 1:
            messenger.send("NameShop-mickeyChange",
                           [[TTLocalizer.ApprovalForName1,
                             TTLocalizer.ApprovalForName2]])
            self.chastise = 0
        if not (self.firstActive or self.lastActive):
            self.lastActive = 1
            messenger.send("NameShop-mickeyChange",
                           [[TTLocalizer.MustHaveAFirstOrLast1,
                             TTLocalizer.MustHaveAFirstOrLast2]])
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
        """load(self)
        """
        self.notify.debug('load')
        if self.isLoaded == 1:
            return None

        # set-up name selector
        nameBalloon = loader.loadModel(
            "phase_3/models/props/chatbox_input")
        guiButton = loader.loadModel("phase_3/models/gui/quit_button")
        gui = loader.loadModel("phase_3/models/gui/tt_m_gui_mat_nameShop")
        self.arrowUp = gui.find('**/tt_t_gui_mat_namePanelArrowUp')
        self.arrowDown = gui.find('**/tt_t_gui_mat_namePanelArrowDown')
        self.arrowHover = gui.find('**/tt_t_gui_mat_namePanelArrowHover')
        self.squareUp = gui.find('**/tt_t_gui_mat_namePanelSquareUp')
        self.squareDown = gui.find('**/tt_t_gui_mat_namePanelSquareDown')
        self.squareHover = gui.find('**/tt_t_gui_mat_namePanelSquareHover')

        typePanel = gui.find("**/tt_t_gui_mat_typeNamePanel")
        self.typeNamePanel = DirectFrame(
            parent=aspect2d,
            image=None,
            relief='flat',
            scale=(.75, .7, .7),
            state='disabled',
            pos=(-0.0163333, 0, 0.075),
            image_pos=(0, 0, 0.025),
            frameColor=(1, 1, 1, 0),
        )
        self.typePanelFrame = DirectFrame(
            image=typePanel,
            relief='flat',
            frameColor=(1, 1, 1, 0),
            pos=(-0.008, 0, 0.019)
        )
        self.typePanelFrame.reparentTo(self.typeNamePanel, sort=1)

        self.typeANameGUIElements.append(self.typeNamePanel)
        self.typeANameGUIElements.append(self.typePanelFrame)
        self.nameLabel = OnscreenText.OnscreenText(
            TTLocalizer.PleaseTypeName,
            parent=aspect2d,
            style=OnscreenText.ScreenPrompt,
            scale=TTLocalizer.NSnameLabel,
            pos=(-0.0163333, 0.53))
        self.nameLabel.wrtReparentTo(self.typeNamePanel, sort=2)
        self.typeANameGUIElements.append(self.nameLabel)

        self.typeNotification = OnscreenText.OnscreenText(
            TTLocalizer.AllNewNames,
            parent=aspect2d,
            style=OnscreenText.ScreenPrompt,
            scale=TTLocalizer.NStypeNotification,
            pos=(-0.0163333, 0.15))
        self.typeNotification.wrtReparentTo(self.typeNamePanel, sort=2)
        self.typeANameGUIElements.append(self.typeNotification)

        self.nameMessages = OnscreenText.OnscreenText(
            TTLocalizer.NameMessages,
            parent=aspect2d,
            style=OnscreenText.ScreenPrompt,
            scale=0.06,
            pos=(-0.0163333, -0.05))
        self.nameMessages.wrtReparentTo(self.typeNamePanel, sort=2)
        self.typeANameGUIElements.append(self.nameMessages)

        self.nameEntry = DirectEntry(
            parent=aspect2d,
            relief=None,
            scale=TTLocalizer.NSnameEntry,
            entryFont=getToonFont(),
            width=MAX_NAME_WIDTH,
            numLines=2,
            focus=0,
            cursorKeys=1,
            pos=(0.0, 0.0, 0.39),
            text_align=TextNode.ACenter,
            command=self.__typedAName,
            autoCapitalize=1,
        )
        self.nameEntry.wrtReparentTo(self.typeNamePanel, sort=2)
        self.typeANameGUIElements.append(self.nameEntry)
        self.submitButton = DirectButton(
            parent=aspect2d,
            relief=None,
            image=(self.squareUp, self.squareDown, self.squareHover, self.squareUp),
            image_scale=(1.2, 0, 1.1),
            pos=(-0.01, 0, -0.25),
            text=TTLocalizer.NameShopSubmitButton,
            text_scale=0.06,
            text_pos=(0, -0.02),
            command=self.__typedAName,
        )

        self.submitButton.wrtReparentTo(self.typeNamePanel, sort=2)
        self.typeNamePanel.setPos(-0.42, 0, -0.078)

        self.typeANameGUIElements.append(self.submitButton)

        # GUI Elements for PickAName
        self.randomButton = DirectButton(
            parent=aspect2d,
            relief=None,
            image=(self.squareUp, self.squareDown, self.squareHover, self.squareUp),
            image_scale=(1.15, 1.1, 1.1),
            scale=(1.05, 1, 1),
            pos=(0, 0, -0.25),
            text=TTLocalizer.ShuffleButton,
            text_scale=0.06,
            text_pos=(0, -0.02),
            command=self.__randomName,
        )
        self.pickANameGUIElements.append(self.randomButton)
        self.typeANameButton = DirectButton(
            parent=aspect2d,
            relief=None,
            image=(self.squareUp, self.squareDown, self.squareHover, self.squareUp),
            image_scale=(1, 1.1, 0.9),
            pos=(0.0033, 0, -.38833),
            scale=(1.2, 1, 1.2),
            text=TTLocalizer.TypeANameButton,
            text_scale=TTLocalizer.NStypeANameButton,
            text_pos=TTLocalizer.NStypeANameButtonPos,
            command=self.__typeAName,
        )
        #self.printTypeANameInfo("after constructor in DirectButton")

        if base.cr.productName in ['DE', 'BR']:
            # No type-a-name for DE (German) and BR (Brazil)
            self.typeANameButton.hide()
        self.pickANameGUIElements.append(self.typeANameButton)

        # nameResult is a label where the current name combo will be displayed
        self.nameResult = DirectLabel(
            parent=aspect2d,
            relief=None,
            scale=TTLocalizer.NSnameResult,
            pos=(0.005, 0, 0.585),
            text=" \n ",
            text_scale=0.8,
            text_align=TextNode.ACenter,
            text_wordwrap=MAX_NAME_WIDTH,
        )
        self.pickANameGUIElements.append(self.nameResult)

        self.allPrefixes = self.nameGen.lastPrefixes[:]
        self.allSuffixes = self.nameGen.lastSuffixes[:]
        self.allPrefixes.sort()
        self.allSuffixes.sort()
        self.allPrefixes = [" "] + [" "] + self.allPrefixes + [" "] + [" "]
        self.allSuffixes = [" "] + [" "] + self.allSuffixes + [" "] + [" "]

        # Create 4 scrolled lists with different colors
        self.titleScrollList = self.makeScrollList(
            gui, (-0.6, 0, 0.202),
            (1, 0.80, .80, 1), self.allTitles,
            self.makeLabel, [TextNode.ACenter, 'title'])
        self.firstnameScrollList = self.makeScrollList(
            gui, (-0.2, 0, 0.202),
            (0.80, 1, .80, 1), self.allFirsts,
            self.makeLabel, [TextNode.ACenter, 'first'])
        self.lastprefixScrollList = self.makeScrollList(
            gui, (0.2, 0, 0.202),
            (0.80, 0.80, 1, 1), self.allPrefixes,
            self.makeLabel, [TextNode.ARight, 'prefix'])
        self.lastsuffixScrollList = self.makeScrollList(
            gui, (0.55, 0, 0.202),
            (0.80, 0.80, 1, 1), self.allSuffixes,
            self.makeLabel, [TextNode.ALeft, 'suffix'])

        gui.removeNode()
        self.pickANameGUIElements.append(self.lastprefixScrollList)
        self.pickANameGUIElements.append(self.lastsuffixScrollList)
        self.pickANameGUIElements.append(self.titleScrollList)
        self.pickANameGUIElements.append(self.firstnameScrollList)

        # Make four highlights for each scroll List
        self.titleHigh = self.makeHighlight((-0.710367, 0.0, 0.122967))
        self.firstHigh = self.makeHighlight((-0.310367, 0.0, 0.122967))
        self.pickANameGUIElements.append(self.titleHigh)
        self.pickANameGUIElements.append(self.firstHigh)
        self.prefixHigh = self.makeHighlight((0.09, 0.0, 0.122967))
        self.suffixHigh = self.makeHighlight((0.44, 0.0, 0.122967))
        self.pickANameGUIElements.append(self.prefixHigh)
        self.pickANameGUIElements.append(self.suffixHigh)

        nameBalloon.removeNode()

        # GUI elements for PayState
        imageList = (guiButton.find("**/QuitBtn_UP"),
                     guiButton.find("**/QuitBtn_DN"),
                     guiButton.find("**/QuitBtn_RLVR"),
                     )
        buttonImage = [imageList, imageList]
        buttonText = [TTLocalizer.NameShopPay, TTLocalizer.NameShopPlay]

        self.payDialog = DirectDialog(dialogName="paystate",
                                      topPad=0,
                                      fadeScreen=0.2,
                                      pos=(0, .1, .1),
                                      button_relief=None,
                                      text_align=TextNode.ACenter,
                                      text=TTLocalizer.NameShopOnlyPaid,
                                      buttonTextList=buttonText,
                                      buttonImageList=buttonImage,
                                      image_color=GlobalDialogColor,
                                      buttonValueList=[1, 0],
                                      command=self.payAction)
        self.payDialog.buttonList[0].setPos(0, 0, -.27)
        self.payDialog.buttonList[1].setPos(0, 0, -.4)
        self.payDialog.buttonList[0]['image_scale'] = (1.2, 1, 1.1)
        self.payDialog.buttonList[1]['image_scale'] = (1.2, 1, 1.1)
        self.payDialog['image_scale'] = (.8, 1, .77)
        self.payDialog.buttonList[0]['text_pos'] = (0, -.02)
        self.payDialog.buttonList[1]['text_pos'] = (0, -.02)
        self.payDialog.hide()

        buttonText = [TTLocalizer.NameShopContinueSubmission, TTLocalizer.NameShopChooseAnother]

        self.approvalDialog = DirectDialog(dialogName="approvalstate",
                                           topPad=0,
                                           fadeScreen=0.2,
                                           pos=(0, .1, .1),
                                           button_relief=None,
                                           image_color=GlobalDialogColor,
                                           text_align=TextNode.ACenter,
                                           text=TTLocalizer.NameShopToonCouncil,
                                           buttonTextList=buttonText,
                                           buttonImageList=buttonImage,
                                           buttonValueList=[1, 0],
                                           command=self.approvalAction)
        self.approvalDialog.buttonList[0].setPos(0, 0, -.3)
        self.approvalDialog.buttonList[1].setPos(0, 0, -.43)
        self.approvalDialog['image_scale'] = (.8, 1, .77)
        for x in range(0, 2):
            self.approvalDialog.buttonList[x]['text_pos'] = (0, -.01)
            self.approvalDialog.buttonList[x]['text_scale'] = (.04, .05999)
            self.approvalDialog.buttonList[x].setScale(1.2, 1, 1)

        self.approvalDialog.hide()
        guiButton.removeNode()

        self.uberhide(self.typeANameGUIElements)
        self.uberhide(self.pickANameGUIElements)

        self.isLoaded = 1
        return None

    def ubershow(self, guiObjectsToShow):
        self.notify.debug("ubershow %s" % str(guiObjectsToShow))
        for x in guiObjectsToShow:
            try:
                x.show()
            except BaseException:
                print("NameShop: Tried to show already removed object")

        if base.cr.productName in ['DE', 'BR']:
            # No type-a-name for DE (German) and BR (Brazil)
            self.typeANameButton.hide()

    def hideAll(self):
        self.uberhide(self.pickANameGUIElements)
        self.uberhide(self.typeANameGUIElements)

    def uberhide(self, guiObjectsToHide):
        self.notify.debug("uberhide %s" % str(guiObjectsToHide))
        for x in guiObjectsToHide:
            try:
                x.hide()
            except BaseException:
                print("NameShop: Tried to hide already removed object")

    def uberdestroy(self, guiObjectsToDestroy):
        self.notify.debug("uberdestroy %s" % str(guiObjectsToDestroy))
        for x in guiObjectsToDestroy:
            # This is sloppy, it's causing a C++ exception at the end of
            # make-a-toon. We should bullet-proof destroy() so that it
            # doesn't do Bad Stuff when it's called more than once, or
            # check to see if the object has already been destroyed.
            try:
                x.destroy()
                del x
            except BaseException:
                print("NameShop: Tried to destroy already removed object")

    def getNameIndices(self):
        """getNameIndices(self)
        """
        return self.nameIndices

    def getNameFlags(self):
        """getNameFlags(self)
        """
        return self.nameFlags

    def getNameAction(self):
        """getNameAction(self)
        """
        return self.nameAction

    def unload(self):
        """unload(self)
        """
        self.notify.debug('unload')
        if self.isLoaded == 0:
            return None

        self.exit()
        # make sure any dialog panels are closed
        cleanupDialog("globalDialog")

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
        return None

    def _checkNpcNames(self, name):
        def match(npcName, name=name):
            # TextEncoder.upper requires encoded strings
            name = TextEncoder().encodeWtext(name)
            name = name.strip()
            return (TextEncoder.upper(npcName) == TextEncoder.upper(name.decode()))

        for npcId in list(NPCToons.NPCToonDict.keys()):
            npcName = NPCToons.NPCToonDict[npcId][1]
            if match(npcName):
                self.notify.info('name matches NPC name "%s"' % npcName)
                return TTLocalizer.NCGeneric

    def nameIsValid(self, name):
        """nameIsValid(self, string name)
        Checks the name for legitimacy according to our various
        Toontown rules.  If it violates any of those rules, returns a
        string explaining the objection; otherwise, returns None
        indicating the name is acceptable.
        """
        self.notify.debug('nameIsValid')
        if (name in self.usedNames):
            return TTLocalizer.ToonAlreadyExists % (name)

        problem = NameCheck.checkName(name, [self._checkNpcNames],
                                      font=self.nameEntry.getFont())
        if problem:
            return problem

        # name has passed local checks
        return None

    # event handlers

    def setShopsVisited(self, list):
        """setShopsVisited(self, int[])
        We must know what shops are visited so we can place the done button
        """
        self.shopsVisited = list

    def __handleDone(self):
        if self.fsm.getCurrentState().getName() == 'TypeAName':
            self.__typedAName()
        else:
            # self.__createAvatar()
            self.__isFirstTime()

    def __handleSkipTutorial(self):
        self.__createAvatar(skipTutorial=True)

    def __handleBackward(self):
        self.doneStatus = 'last'
        messenger.send(self.doneEvent)

    def __handleChastised(self):
        self.chastiseDialog.cleanup()

    def __createAvatar(self, skipTutorial=False, *args):
        """__createAvatar(self)
        Create the avatar if needed, then check name
        """
        self.notify.debug('__createAvatar')
        # If you're in typeAName then you can't click done!
        if self.fsm.getCurrentState().getName() == 'TypeAName':
            self.__typedAName()
            return

        if not self.avExists or (self.avExists and self.avId == 'deleteMe'):
            self.serverCreateAvatar(skipTutorial)
        else:
            if (self.names[0] == ""):
                # No empty names
                self.rejectName(TTLocalizer.EmptyNameError)
            else:
                rejectReason = self.nameIsValid(self.names[0])
                if rejectReason is not None:
                    self.rejectName(rejectReason)
                else:
                    self.checkNamePattern()

    def acceptName(self):
        self.notify.debug('acceptName')
        # The name was accepted by the server
        # Set our Toon name
        self.toon.setName(self.names[0])
        # Send our done event
        self.doneStatus = "done"
        self.storeSkipTutorialRequest()
        messenger.send(self.doneEvent)

    def rejectName(self, str):
        self.notify.debug('rejectName')
        self.names[0] = ""
        self.rejectDialog = TTDialog.TTGlobalDialog(
            doneEvent="rejectDone",
            message=str,
            style=TTDialog.Acknowledge)
        self.rejectDialog.show()
        self.acceptOnce("rejectDone", self.__handleReject)

    def __handleReject(self):
        self.rejectDialog.cleanup()
        self.nameEntry['focus'] = 1
        self.typeANameButton.show()
        # enable the done button again
        self.acceptOnce("next", self.__handleDone)

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
        """Scroll lists to the newly changed indices
        """
        oldindex = [self.titleIndex, self.firstIndex,
                    self.prefixIndex, self.suffixIndex]
        self.titleScrollList.scrollTo(self.titleIndex - 2)
        self.restoreIndexes(oldindex)
        self.firstnameScrollList.scrollTo(self.firstIndex - 2)
        self.restoreIndexes(oldindex)
        self.lastprefixScrollList.scrollTo(self.prefixIndex - 2)
        self.restoreIndexes(oldindex)
        self.lastsuffixScrollList.scrollTo(self.suffixIndex - 2)
        self.restoreIndexes(oldindex)

    def __randomName(self):
        self.notify.debug("Finding random name")
        # Create a random name using the new function which returns
        # more information
        uberReturn = self.nameGen.randomNameMoreinfo()
        flags = uberReturn[:3]
        names = uberReturn[3:7]
        fullName = uberReturn[-1]
        self._updateGuiWithPickAName(flags, names, fullName)

    def _updateGuiWithPickAName(self, flags, names, fullName):
        # flags are 'active' boolean for (title, first, last)
        # names are strings or '' for (title, first, lastPrefix, lastSuffix)
        # fullName is full name string
        # format the data to work with the code below
        uberReturn = flags + names + [fullName]

        self.names[0] = uberReturn[len(uberReturn) - 1]
        self.titleActive = 0
        self.firstActive = 0
        self.lastActive = 0

        # If there was a title used (the first item in return list
        # is titleFlag)
        if uberReturn[0]:
            self.titleActive = 1

        # If a first name is used (the second item in returned list
        # is firstFlag)
        if uberReturn[1]:
            self.firstActive = 1

        if uberReturn[2]:
            self.lastActive = 1

        # Now look up each name in each list, even if we're not using
        # the list (that is, even if the flag above is set false for
        # the given list).  We do this so that if the user activates a
        # new slot that was previously deactive, it will start the
        # user in the middle of the list instead of necessarily at the
        # top.

        try:
            # Find position in scrolledList of the title used
            self.titleIndex = self.allTitles.index(uberReturn[3])
            self.nameIndices[0] = self.nameGen.returnUniqueID(uberReturn[3], 0)
            self.nameFlags[0] = 1
        except BaseException:
            print("NameShop : Should have found title, uh oh!")
            print(uberReturn)

        try:
            # Find position in scrolledList of the firstname used
            self.firstIndex = self.allFirsts.index(uberReturn[4])
            self.nameIndices[1] = self.nameGen.returnUniqueID(uberReturn[4], 1)
            self.nameFlags[1] = 1
        except BaseException:
            print("NameShop : Should have found first name, uh oh!")
            print(uberReturn)

        # If there was a last name used (you get it...)
        try:
            # Find position in scrolledList of the prefix and suffix used
            self.prefixIndex = self.allPrefixes.index(uberReturn[5])
            self.suffixIndex = self.allSuffixes.index((uberReturn[6].lower()))
            self.nameIndices[2] = self.nameGen.returnUniqueID(
                uberReturn[5], 2)
            self.nameIndices[3] = self.nameGen.returnUniqueID(
                uberReturn[6].lower(), 3)
            if uberReturn[5] in self.nameGen.capPrefixes:
                self.nameFlags[3] = 1
            else:
                self.nameFlags[3] = 0
        except BaseException:
            print("NameShop : Some part of last name not found, uh oh!")
            print(uberReturn)

        self.updateCheckBoxes()
        self.updateLists()

        # Put the name in the result label
        self.nameResult['text'] = self.names[0]

    def findTempName(self):
        colorstring = TTLocalizer.NumToColor[self.toon.style.headColor]
        animaltype = TTLocalizer.AnimalToSpecies[self.toon.style.getAnimal()]
        tempname = colorstring + " " + \
            animaltype
        if not TTLocalizer.NScolorPrecede:    # fix for French grammar
            tempname = animaltype + " " + \
                colorstring
        self.names[0] = tempname
        tempname = '"' + tempname + '"'
        return tempname

    # Specific State functions
    # Init state
    def enterInit(self):
        self.notify.debug('enterInit')

    def exitInit(self):
        pass

    # PayState State
    def enterPayState(self):
        self.notify.debug('enterPayState')

        # If we are allowing free names, or this person is paid
        # let them name their toon
        if (base.cr.allowFreeNames() or self.isPaid):
            self.fsm.request("PickAName")
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
            self.doneStatus = "paynow"
            messenger.send(self.doneEvent)
            # self.fsm.request("PickAName")
        else:
            self.nameAction = 0
            self.__createAvatar()

    # PickAName state
    def enterPickANameState(self):
        self.notify.debug('enterPickANameState')
        self.ubershow(self.pickANameGUIElements)
        self.nameAction = 1
        self.__listsChanged()

    def exitPickANameState(self):
        self.uberhide(self.pickANameGUIElements)

    # TypeAName state
    def enterTypeANameState(self):
        self.notify.debug('enterTypeANameState')
        self.ubershow(self.typeANameGUIElements)
        self.typeANameButton.show()
        self.typeANameButton.wrtReparentTo(aspect2d, sort=2)
        self.nameEntry.set("")
        self.nameEntry['focus'] = 1

    def __typeAName(self):
        if base.cr.productName in ['JP', 'DE', 'BR', 'FR']:
            # for INTL users, if it not paid, it is not allowed to type their name
            if base.restrictTrialers:
                if not base.cr.isPaid():
                    # don't allow trialers to type in a name
                    dialog = TeaserPanel.TeaserPanel(pageName='typeAName')
                    return
        if self.fsm.getCurrentState().getName() == 'TypeAName':
            self.typeANameButton['text'] = TTLocalizer.TypeANameButton
            self.typeANameButton.wrtReparentTo(self.namePanel, sort=2)
            #self.printTypeANameInfo("in __typeAName, after reparent to self.namePanel")
            self.fsm.request("PickAName")
        else:
            self.typeANameButton['text'] = TTLocalizer.PickANameButton
            self.typeANameButton.wrtReparentTo(aspect2d, sort=2)
            #self.printTypeANameInfo("in __typeAName, after reparent to aspect2d")
            self.typeANameButton.show()
            self.fsm.request("TypeAName")

    def __typedAName(self, *args):
        self.notify.debug('__typedAName')

        self.nameEntry['focus'] = 0

        # strip leading/trailing whitespace
        name = self.nameEntry.get()
        # make sure we're able to recognize unicode whitespace
        name = TextEncoder().decodeText(name.encode())
        name = name.strip()
        name = TextEncoder().encodeWtext(name)

        # put the processed name back into the GUI
        self.nameEntry.enterText(name.decode())

        # do local name checks first
        problem = self.nameIsValid(self.nameEntry.get())
        if problem:
            self.rejectName(problem)
            return

        # check to see if the server would reject this name before
        # actually submitting the name for the new avatar
        self.checkNameTyped(justCheck=True)

    def exitTypeANameState(self):
        # fix type a name button shifting
        self.typeANameButton.wrtReparentTo(self.namePanel, sort=2)
        #self.printTypeANameInfo("after reparent to self.namePanel")
        self.uberhide(self.typeANameGUIElements)

    # Approval state
    def enterApprovalState(self):
        self.notify.debug('enterApprovalState')
        tempname = self.findTempName()
        self.approvalDialog['text'] = TTLocalizer.NameShopToonCouncil + tempname
        self.approvalDialog.show()

    def approvalAction(self, value):
        self.notify.debug('approvalAction')
        self.approvalDialog.hide()
        if value:
            # user approves of temp name. continue with the process, create the avatar
            self.nameAction = 2
            if not self.makeAToon.warp:
                self.__isFirstTime()
            else:
                self.serverCreateAvatar()
        else:
            self.typeANameButton['text'] = TTLocalizer.TypeANameButton
            self.fsm.request("PickAName")

    def exitApprovalState(self):
        pass

    # ApprovalAccepted state
    def enterApprovalAcceptedState(self):
        self.notify.debug('enterApprovalAcceptedState')
        # user has accepted a temporary name, and has been notified that they will have
        # to wait for their name to be approved
        self.doneStatus = "done"
        self.storeSkipTutorialRequest()
        messenger.send(self.doneEvent)

    def exitApprovalAcceptedState(self):
        pass

    # Accepted state
    def enterAcceptedState(self):
        self.notify.debug('enterAcceptedState')
        self.acceptedDialog = TTDialog.TTGlobalDialog(
            doneEvent="acceptedDone",
            message=TTLocalizer.NameShopNameAccepted,
            style=TTDialog.Acknowledge)
        self.acceptedDialog.show()
        self.acceptOnce("acceptedDone", self.__handleAccepted)

    def __handleAccepted(self):
        self.acceptedDialog.cleanup()
        # Everything is cool, send our done event
        self.doneStatus = "done"
        self.storeSkipTutorialRequest()
        messenger.send(self.doneEvent)

    def exitAcceptedState(self):
        pass

    # Rejected state
    def enterRejectedState(self):
        self.notify.debug('enterRejectedState')
        self.rejectedDialog = TTDialog.TTGlobalDialog(
            doneEvent="rejectedDone",
            message=TTLocalizer.NameShopNameRejected,
            style=TTDialog.Acknowledge)
        self.rejectedDialog.show()
        self.acceptOnce("rejectedDone", self.__handleRejected)

    def __handleRejected(self):
        self.rejectedDialog.cleanup()
        self.fsm.request("TypeAName")

    def exitRejectedState(self):
        pass

    # Done state
    def enterDone(self):
        self.notify.debug('enterDone')
        return None

    def exitDone(self):
        return None

    # Sending and Receiving wit da Server
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

        base.cr.astronLoginManager.sendSetNamePattern(self.avId, self.nameIndices[0], self.nameFlags[0],
                                                      self.nameIndices[1], self.nameFlags[1],
                                                      self.nameIndices[2], self.nameFlags[2],
                                                      self.nameIndices[3], self.nameFlags[3],
                                                      self.handleSetNamePatternAnswerMsg)

        # let the user know we are waiting to hear back
        self.waitForServer()

    def handleSetNamePatternAnswerMsg(self, newavId, returnCode):
        self.notify.debug('handleSetNamePatternAnswerMsg')

        # remove the wait msg
        self.cleanupWaitForServer()

        # Get return code
        if newavId != self.avId:
            # Big trouble in little nameshop
            self.notify.debug("doid's don't match up!")
            self.rejectName(TTLocalizer.NameError)
            pass

        if returnCode == 1:
            style = self.toon.getStyle()
            avDNA = style.makeNetString()
            self.notify.debug("pattern name accepted")
            # add the new potential avatar to the list
            newPotAv = PotentialAvatar.PotentialAvatar(newavId,
                                                       self.names,
                                                       avDNA,
                                                       self.index,
                                                       0)
            self.avList.append(newPotAv)
            # Everything is cool, send our done event
            self.doneStatus = "done"
            self.storeSkipTutorialRequest()
            messenger.send(self.doneEvent)
        else:
            # name creation was rejected by server
            self.notify.debug("name pattern rejected")
            self.rejectName(TTLocalizer.NameError)

        return None

    def _submitTypeANameAsPickAName(self):
        pnp = TTPickANamePattern(self.nameEntry.get())
        if pnp.hasNamePattern():
            # submit the name as a pick-a-name
            # manipulate the GUI elements to pick up NameShop GUI-related code
            pattern = pnp.getNamePattern()
            self.fsm.request('PickAName')
            flags = [pattern[0] != -1, pattern[1] != -1, pattern[2] != -1, ]
            names = []
            for i in range(len(pattern)):
                if pattern[i] != -1:
                    names.append(pnp.getNamePartString(i, pattern[i]))
                else:
                    names.append('')
            fullName = pnp.getNameString(pattern)
            self._updateGuiWithPickAName(flags, names, fullName)
            # now that the gui has been set to the new name, submit it
            self.__handleDone()
            return True
        return False

    def checkNameTyped(self, justCheck=False):
        self.notify.debug('checkNameTyped')

        # if it can be submitted as a pick-a-name, don't bother checking with the server
        if self._submitTypeANameAsPickAName():
            return

        if justCheck:
            # just have the server check the name, don't assign it to
            # any avatar
            avId = 0
        else:
            avId = self.avId

        base.cr.astronLoginManager.sendSetNameTyped(avId, self.nameEntry.get(), self.handleSetNameTypedAnswerMsg)

        # let the user know we are waiting to hear back
        self.waitForServer()

    def handleSetNameTypedAnswerMsg(self, newavId, returnCode):
        self.notify.debug('handleSetNameTypedAnswerMsg')

        # remove the wait msg
        self.cleanupWaitForServer()

        # avId is 0 if we just wanted to check the name
        if newavId and newavId != self.avId:
            # Big trouble in little nameshop
            self.notify.debug("doid's don't match up!")
            self.rejectName(TTLocalizer.NameError)
            pass

        if (newavId == 0):
            # we were just checking the name to see if it would be rejected
            if returnCode == 1:
                # name will need to be approved by a human
                self.notify.debug("name check pending")
                self.fsm.request("Approval")
            elif returnCode == 2:
                # it was accepted. continue with the process, create the avatar
                self.notify.debug("name check accepted")
                self.nameAction = 2
                self.serverCreateAvatar()
            elif returnCode == 0:
                # it was rejected.
                self.notify.debug("name check rejected")
                self.fsm.request('TypeAName')
                self.rejectName(TTLocalizer.NameError)
            else:
                # Something went wrong!
                self.notify.debug(
                    "typed name response did not contain any return fields")
                self.rejectName(TTLocalizer.NameError)

        else:
            if returnCode == 2:
                style = self.toon.getStyle()
                avDNA = style.makeNetString()
                self.names[0] = self.nameEntry.get()
                self.notify.debug("typed name accepted")
                # add the new potential avatar to the list
                newPotAv = PotentialAvatar.PotentialAvatar(newavId,
                                                           self.names,
                                                           avDNA,
                                                           self.index,
                                                           0)
                self.avList.append(newPotAv)
                self.fsm.request("Accepted")

            if returnCode == 1:
                style = self.toon.getStyle()
                avDNA = style.makeNetString()
                self.names[1] = self.nameEntry.get()
                self.notify.debug("typed name needs approval")
                # add the new potential avatar to the list
                newPotAv = PotentialAvatar.PotentialAvatar(newavId,
                                                           self.names,
                                                           avDNA,
                                                           self.index,
                                                           1)
                if not self.newwarp:
                    self.avList.append(newPotAv)
                self.fsm.request("ApprovalAccepted")
            elif returnCode == 0:
                self.fsm.request("Rejected")
            else:
                # Something went wrong!
                self.notify.debug(
                    "name typed accepted but didn't fill any return fields")
                self.rejectName(TTLocalizer.NameError)

        return None

    def serverCreateAvatar(self, skipTutorial=False):
        self.notify.debug('serverCreateAvatar')

        style = self.toon.getStyle()
        self.newDNA = style.makeNetString()
        if skipTutorial:
            self.requestingSkipTutorial = True
        else:
            self.requestingSkipTutorial = False

        # if the avatar doesn't exist, or exists and we want to delete it
        if not self.avExists or (self.avExists and self.avId == 'deleteMe'):
            messenger.send("nameShopCreateAvatar", [style, "", self.index])
            self.accept('nameShopCreateAvatarDone', self.handleCreateAvatarResponseMsg)
        else:
            # otherwise, just set the new name
            self.checkNameTyped()

        self.notify.debug('Ending Make A Toon: %s' % self.toon.style)
        base.cr.centralLogger.writeClientEvent('MAT - endingMakeAToon: %s' % self.toon.style)

    def handleCreateAvatarResponseMsg(self, avId):
        self.notify.debug('handleCreateAvatarResponseMsg')
        # Unnecessary echo context
        echoContext = 0
        # Get return code
        returnCode = 0
        if returnCode == 0:
            self.notify.debug("avatar with default name accepted")
            self.avId = avId
            self.avExists = 1
            # If they just want 'blue duck'
            if self.nameAction == 0:
                self.toon.setName(self.names[0])
                # add the new potential avatar to the list
                newPotAv = PotentialAvatar.PotentialAvatar(self.avId,
                                                           self.names,
                                                           self.newDNA,
                                                           self.index,
                                                           1)
                self.avList.append(newPotAv)

                # Send our done event
                self.doneStatus = "done"
                self.storeSkipTutorialRequest()
                messenger.send(self.doneEvent)
            # If they used pickAName and there are indices to send
            elif self.nameAction == 1:
                self.checkNamePattern()
            # If they used typeAName and there is a name to send
            elif self.nameAction == 2:
                self.checkNameTyped()
            else:
                # Trouble, reject anyway
                self.notify.debug("avatar invalid nameAction")
                self.rejectName(TTLocalizer.NameError)
        else:

            # create was rejected by server
            self.notify.debug("avatar rejected")
            self.rejectName(TTLocalizer.NameError)

        return None

    def waitForServer(self):
        # let the user know we are waiting to hear back from server (in case it hangs)
        self.waitForServerDialog = TTDialog.TTDialog(
            text=TTLocalizer.WaitingForNameSubmission,
            style=TTDialog.NoButtons)
        self.waitForServerDialog.show()

    def cleanupWaitForServer(self):
        if self.waitForServerDialog is not None:
            self.waitForServerDialog.cleanup()
            self.waitForServerDialog = None

    def printTypeANameInfo(self, str):
        sourceFilename, lineNumber, functionName = PythonUtil.stackEntryInfo(1)
        self.notify.debug("========================================\n"
                          "%s : %s :  %s" % (sourceFilename, lineNumber, functionName))
        self.notify.debug(str)
        # return
        curPos = self.typeANameButton.getPos()
        self.notify.debug("Pos = %.2f %.2f %.2f" % (curPos[0], curPos[1], curPos[2]))
        parent = self.typeANameButton.getParent()
        parentPos = parent.getPos()
        self.notify.debug("Parent = %s" % parent)
        self.notify.debug("ParentPos = %.2f %.2f %.2f" % (parentPos[0], parentPos[1], parentPos[2]))

    def storeSkipTutorialRequest(self):
        """Store our skip tutorial request in cr, as NameShop gets deleted.
            Also check the config variable if we want the tutorial or not."""
        base.cr.skipTutorialRequest = self.requestingSkipTutorial
      

    def __isFirstTime(self):
        """
        Determines whether this is the first time make a toon experience for the player.
        Prompt the skip tutorial if this not the first time experience.
        """
        # Go Straight to create avatar (don't pop up the skip tutorial prompt)
        # if it's the player's first MAT experience or
        # if the player has come into MAT in the warp mode, ie just to name his toon.
        if not self.makeAToon.nameList or self.makeAToon.warp:
            self.__createAvatar()
        else:
            self.promptTutorial()

    def promptTutorial(self):
        """
        This brings up a pop up window which prompts the player if they want to
        go to the tutorial or skip it.
        """
        self.promptTutorialDialog = TTDialog.TTDialog(
            ##            doneEvent = "exitMAT",
            parent=aspect2dp,
            text=TTLocalizer.PromptTutorial,
            text_scale=0.06,
            text_align=TextNode.ACenter,
            text_wordwrap=22,
            ##            topPad = -0.05,
            ##            midPad = 1.25,
            ##            sidePad = 0.0,
            command=self.__openTutorialDialog,
            fadeScreen=.5,
            style=TTDialog.TwoChoice,
            ##            style = TTDialog.Acknowledge,
            buttonTextList=[TTLocalizer.MakeAToonEnterTutorial, TTLocalizer.MakeAToonSkipTutorial],
            button_text_scale=0.06,
            buttonPadSF=5.5,
            sortOrder=DGG.NO_FADE_SORT_INDEX,
        )
        self.promptTutorialDialog.show()

    def __openTutorialDialog(self, choice=0):
        if choice == 1:
            self.notify.debug('enterTutorial')
            self.__createAvatar()
        else:
            self.notify.debug('skipTutorial')
            self.__handleSkipTutorial()
        self.promptTutorialDialog.destroy()