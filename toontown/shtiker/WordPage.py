from enum import IntEnum
from direct.gui import DirectGuiGlobals
from panda3d.core import *
from direct.directnotify import DirectNotifyGlobal
from direct.interval.IntervalGlobal import *
from direct.distributed import DistributedObject
from direct.gui.DirectGui import *
from otp.otpbase import PythonUtil
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.toon import Toon
from toontown.toon import ToonDNA
from toontown.spellbook.MagicWordIndex import *
from . import ShtikerPage
from ..util.ui import make_dsl_scrollable

PageMode = IntEnum('PageMode', ('Words', 'IDs', 'Acc1', 'Acc2'))

class WordPage(ShtikerPage.ShtikerPage):
    notify = DirectNotifyGlobal.directNotify.newCategory('WordPage')

    def __init__(self):
        ShtikerPage.ShtikerPage.__init__(self)

    def load(self):
        ShtikerPage.ShtikerPage.load(self)
        self.wordsTabPage = WordsTabPage(self)
        self.wordsTabPage.hide()
        self.clothingTabPage = ClothingTabPage(self)
        self.clothingTabPage.hide()
        self.acc1Page = AccTabPage1(self)
        self.acc1Page.hide()
        self.acc2Page = AccTabPage2(self)
        self.acc2Page.hide()
        titleHeight = 0.61
        self.title = DirectLabel(parent=self, relief=None, text=TTLocalizer.SpellbookPageTitle, text_scale=0.12, pos=(0, 0, titleHeight))
        normalColor = (1, 1, 1, 1)
        clickColor = (0.8, 0.8, 0, 1)
        rolloverColor = (0.15, 0.82, 1.0, 1)
        diabledColor = (1.0, 0.98, 0.15, 1)
        gui = loader.loadModel('phase_3.5/models/gui/fishingBook')
        self.wordsTab = DirectButton(parent=self, relief=None, text=TTLocalizer.WordPageTabTitle, text_scale=0.063,
                                     text_align=TextNode.ALeft, text_pos=(0.0, 0.0, 0.0),
                                     image=gui.find('**/tabs/polySurface1'), image_pos=(0.55, 1, -0.91),
                                     image_hpr=(0, 0, -90), image_scale=(0.033, 0.033, 0.035), image_color=normalColor,
                                     image1_color=clickColor, image2_color=rolloverColor, image3_color=diabledColor,
                                     text_fg=Vec4(0.2, 0.1, 0, 1), command=self.setMode, extraArgs=[PageMode.Words],
                                     pos=(-0.83, 0, 0.77))
        self.idsTab = DirectButton(parent=self, relief=None, text=TTLocalizer.ClothingPageTitle, text_scale=0.065,
                                   text_align=TextNode.ALeft, text_pos=(0.0, 0.0, 0.0),
                                   image=gui.find('**/tabs/polySurface2'), image_pos=(0.12, 1, -0.91),
                                   image_hpr=(0, 0, -90), image_scale=(0.033, 0.033, 0.035), image_color=normalColor,
                                   image1_color=clickColor, image2_color=rolloverColor, image3_color=diabledColor,
                                   text_fg=Vec4(0.2, 0.1, 0, 1), command=self.setMode, extraArgs=[PageMode.IDs],
                                   pos=(-0.36, 0, 0.77))
        self.acc1Tab = DirectButton(parent=self, relief=None, text=TTLocalizer.AccessoriesPageHeadTab, text_scale=0.045,
                                   text_align=TextNode.ACenter, text_pos=(0.125, 0.035, 0.0),
                                   image=gui.find('**/tabs/polySurface2'), image_pos=(0.12, 1, -0.91),
                                   image_hpr=(0, 0, -90), image_scale=(0.033, 0.033, 0.035), image_color=normalColor,
                                   image1_color=clickColor, image2_color=rolloverColor, image3_color=diabledColor,
                                   text_fg=Vec4(0.2, 0.1, 0, 1), command=self.setMode, extraArgs=[PageMode.Acc1],
                                   pos=(0.11, 0, 0.77))
        self.acc2Tab = DirectButton(parent=self, relief=None, text=TTLocalizer.AccessoriesPageBodyTab, text_scale=0.045,
                                    text_align=TextNode.ACenter, text_pos=(0.125, 0.035, 0.0),
                                    image=gui.find('**/tabs/polySurface2'), image_pos=(0.12, 1, -0.91),
                                    image_hpr=(0, 0, -90), image_scale=(0.033, 0.033, 0.035), image_color=normalColor,
                                    image1_color=clickColor, image2_color=rolloverColor, image3_color=diabledColor,
                                    text_fg=Vec4(0.2, 0.1, 0, 1), command=self.setMode, extraArgs=[PageMode.Acc2],
                                    pos=(0.58, 0, 0.77))
        return

    def enter(self):
        self.setMode(PageMode.Words, updateAnyways=1)
        ShtikerPage.ShtikerPage.enter(self)

    def exit(self):
        self.clothingTabPage.exit()
        self.wordsTabPage.exit()
        self.acc1Page.exit()
        self.acc2Page.exit()
        ShtikerPage.ShtikerPage.exit(self)

    def unload(self):
        self.wordsTabPage.unload()
        self.clothingTabPage.unload()
        self.acc1Page.unload()
        self.acc2Page.unload()
        del self.title
        ShtikerPage.ShtikerPage.unload(self)

    def setMode(self, mode, updateAnyways = 0):
        messenger.send('wakeup')
        if not updateAnyways:
            if self.mode == mode:
                return
            else:
                self.mode = mode
        if mode == PageMode.Words:
            self.mode = PageMode.Words
            self.title['text'] = TTLocalizer.WordPageTabTitle
            self.wordsTab['state'] = DGG.DISABLED
            self.wordsTabPage.enter()
            self.idsTab['state'] = DGG.NORMAL
            self.clothingTabPage.exit()
            self.acc1Tab['state'] = DGG.NORMAL
            self.acc1Page.exit()
            self.acc2Tab['state'] = DGG.NORMAL
            self.acc2Page.exit()
        elif mode == PageMode.IDs:
            self.mode = PageMode.IDs
            self.title['text'] = TTLocalizer.ClothingPageTitle
            self.wordsTab['state'] = DGG.NORMAL
            self.wordsTabPage.exit()
            self.idsTab['state'] = DGG.DISABLED
            self.clothingTabPage.enter()
            self.acc1Tab['state'] = DGG.NORMAL
            self.acc1Page.exit()
            self.acc2Tab['state'] = DGG.NORMAL
            self.acc2Page.exit()
        elif mode == PageMode.Acc1:
            self.mode = PageMode.Acc1
            self.title['text'] = TTLocalizer.AccessoriesPageHead
            self.wordsTab['state'] = DGG.NORMAL
            self.wordsTabPage.exit()
            self.idsTab['state'] = DGG.NORMAL
            self.clothingTabPage.exit()
            self.acc1Tab['state'] = DGG.DISABLED
            self.acc1Page.enter()
            self.acc2Tab['state'] = DGG.NORMAL
            self.acc2Page.exit()
        elif mode == PageMode.Acc2:
            self.mode = PageMode.Acc2
            self.title['text'] = TTLocalizer.AccessoriesPageBody
            self.wordsTab['state'] = DGG.NORMAL
            self.wordsTabPage.exit()
            self.idsTab['state'] = DGG.NORMAL
            self.clothingTabPage.exit()
            self.acc1Tab['state'] = DGG.NORMAL
            self.acc1Page.exit()
            self.acc2Tab['state'] = DGG.DISABLED
            self.acc2Page.enter()
        else:
            raise Exception('WordPage::setMode - Invalid Mode %s' % mode)


class WordsTabPage(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('WordsTabPage')

    def __init__(self, parent = aspect2d):
        self._parent = parent
        self.currentSizeIndex = None
        DirectFrame.__init__(self, parent=self._parent, relief=None, pos=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0))
        self.load()

    def load(self):
        self.priorityMagicWords = []
        self.magicWords = []
        self.hiddenMagicWords = []
        self.shownMagicWords = []
        self.setupWords()

        gui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
        coolbutton = loader.loadModel('phase_3/models/gui/pick_a_toon_gui')
        guiButton = loader.loadModel('phase_3/models/gui/quit_button')
        cdrGui = loader.loadModel('phase_3.5/models/gui/tt_m_gui_sbk_codeRedemptionGui')
        guiClose = loader.loadModel('phase_3.5/models/gui/avatar_panel_gui')
        self.helpLabel = DirectLabel(parent=self, relief=None, text=TTLocalizer.WordPageHelp, text_scale=0.06,
                                     text_wordwrap=12, text_align=TextNode.ALeft, textMayChange=1,
                                     pos=(0.058, 0, 0.403))
        self.searchLabel = DirectLabel(parent=self, relief=None, text=TTLocalizer.WordPageSearch, text_scale=0.06,
                                       text_wordwrap=12, text_align=TextNode.ACenter, textMayChange=1,
                                       pos=(0.439, 0, -0.2))
        self.searchBarFrame = DirectFrame(parent=self, relief=None, image=cdrGui.find('**/tt_t_gui_sbk_cdrCodeBox'),
                                          pos=(0.439, 0.0, -0.3225), scale=0.7)
        self.searchBarEntry = DirectEntry(parent=self, relief=None, text_scale=0.06, width=7.75, textMayChange=1,
                                          pos=(0.209, 0, -0.3325), text_align=TextNode.ALeft, backgroundFocus=0,
                                          focusInCommand=self.toggleEntryFocus)
        self.searchBarEntry.bind(DGG.TYPE, self.updateWordSearch)
        self.searchBarEntry.bind(DGG.ERASE, self.updateWordSearch)
        self.activatorLabel = DirectLabel(parent=self, relief=None,
                                          text=TTLocalizer.WordPageActivator + TTLocalizer.WordPageNA,
                                          text_scale=0.06, text_wordwrap=12, text_align=TextNode.ALeft, textMayChange=1,
                                          pos=(0.058, 0, 0.15))
        self.totalLabel = DirectLabel(parent=self, relief=None,
                                      text=TTLocalizer.WordPageTotal + str(len(self.shownMagicWords)), text_scale=0.06,
                                      text_wordwrap=12, text_align=TextNode.ALeft, textMayChange=1,
                                      pos=(0.058, 0, 0.05))
        self.currentLabel = DirectLabel(parent=self, relief=None,
                                        text=TTLocalizer.WordPageCurrent + TTLocalizer.WordPageNA, text_scale=0.06,
                                        text_wordwrap=12, text_align=TextNode.ALeft, textMayChange=1,
                                        pos=(0.058, 0, -0.05))
        self.copyToChatButton = DirectButton(parent=self, relief=None, image=(guiButton.find('**/QuitBtn_UP'),
                                                                              guiButton.find('**/QuitBtn_DN'),
                                                                              guiButton.find('**/QuitBtn_RLVR')),
                                             image_scale=(0.7, 1, 1), text=TTLocalizer.WordPageCopyToChat,
                                             text_scale=0.04, text_pos=(0, -0.01), pos=(0.629, 0.0, -0.5325),
                                             command=self.copyToChat)
        self.infoButton = DirectButton(parent=self, relief=None, image=(guiButton.find('**/QuitBtn_UP'),
                                                                        guiButton.find('**/QuitBtn_DN'),
                                                                        guiButton.find('**/QuitBtn_RLVR')),
                                       image_scale=(0.7, 1, 1), text=TTLocalizer.WordPageMoreInfo,
                                       text_scale=0.04, text_pos=(0, -0.01), pos=(0.249, 0.0, -0.5325),
                                       command=self.showInfoPanel)
        self.scrollList = DirectScrolledList(parent=self, forceHeight=0.07, pos=(-0.5, 0, 0),
                                             incButton_image=(gui.find('**/FndsLst_ScrollUp'),
                                                              gui.find('**/FndsLst_ScrollDN'),
                                                              gui.find('**/FndsLst_ScrollUp_Rllvr'),
                                                              gui.find('**/FndsLst_ScrollUp')),
                                             incButton_relief=None, incButton_scale=(1.3, 1.3, -1.3),
                                             incButton_pos=(0.08, 0, -0.60), incButton_image3_color=Vec4(1, 1, 1, 0.2),
                                             decButton_image=(gui.find('**/FndsLst_ScrollUp'),
                                                              gui.find('**/FndsLst_ScrollDN'),
                                                              gui.find('**/FndsLst_ScrollUp_Rllvr'),
                                                              gui.find('**/FndsLst_ScrollUp')),
                                             decButton_relief=None,  decButton_scale=(1.3, 1.3, 1.3),
                                             decButton_pos=(0.08, 0, 0.52), decButton_image3_color=Vec4(1, 1, 1, 0.2),
                                             itemFrame_pos=(-0.237, 0, 0.41), itemFrame_scale=1.0,
                                             itemFrame_relief=DGG.SUNKEN,
                                             itemFrame_frameSize=(-0.05, 0.66, -0.98, 0.07),
                                             itemFrame_frameColor=(0.85, 0.95, 1, 1),
                                             itemFrame_borderWidth=(0.01, 0.01),
                                             numItemsVisible=14, items=self.shownMagicWords)
        make_dsl_scrollable(self.scrollList)
        self.slider = DirectSlider(parent=self, range=(len(self.shownMagicWords), 0),
                                   scale=(0.7, 0.7, 0.515), pos=(-0.1, 0, -0.045),
                                   pageSize=1, orientation=DGG.VERTICAL, command=self.scrollListTo,
                                   thumb_geom=(coolbutton.find('**/QuitBtn_UP'),
                                                coolbutton.find('**/QuitBtn_DN'),
                                                coolbutton.find('**/QuitBtn_RLVR'),
                                                coolbutton.find('**/QuitBtn_UP')),
                                   thumb_relief=None, thumb_geom_hpr=(0, 0, -90), thumb_geom_scale=(0.5, 1, 0.5))
        self.magicWordInfo = DirectFrame(parent=self, relief=None, pos=(0.0, 0.0, -0.05), scale=0.9,
                                         geom=DGG.getDefaultDialogGeom(), geom_scale=(1.4, 1, 1),
                                         geom_color=ToontownGlobals.GlobalDialogColor)
        self.magicWordTitle = DirectLabel(parent=self.magicWordInfo, relief=None, text=TTLocalizer.WordPageNA,
                                          text_scale=0.12,  textMayChange=1, pos=(0, 0, 0.3500))
        self.magicWordInfoLabel = DirectLabel(parent=self.magicWordInfo, relief=None, text=TTLocalizer.WordPageNA,
                                         text_scale=0.06, text_wordwrap=20, text_align=TextNode.ALeft, textMayChange=1,
                                         pos=(-0.6, 0, 0.2))
        self.magicWordQuitButton = DirectButton(parent=self.magicWordInfo,
                                                image=(guiClose.find('**/CloseBtn_UP'),
                                                       guiClose.find('**/CloseBtn_DN'),
                                                       guiClose.find('**/CloseBtn_Rllvr'),
                                                       guiClose.find('**/CloseBtn_UP')),
                                                relief=None, scale=1.5, pos=(0.6, 0, -0.4),
                                                command=self.hideInfoPanel)
        self.magicWordInfo.hide()
        gui.removeNode()
        coolbutton.removeNode()
        guiButton.removeNode()
        cdrGui.removeNode()
        guiClose.removeNode()

    def unload(self):
        for word in self.magicWords + self.hiddenMagicWords + self.shownMagicWords + self.priorityMagicWords:
            word.destroy()
            del word

        gui = [self.helpLabel, self.searchLabel, self.searchBarFrame, self.searchBarEntry, self.activatorLabel,
               self.totalLabel, self.currentLabel, self.copyToChatButton, self.infoButton, self.scrollList,
               self.slider, self.magicWordTitle, self.magicWordInfoLabel, self.magicWordQuitButton, self.magicWordInfo]

        for dgui in gui:
            dgui.destroy()
            del dgui

    def exit(self):
        for word in self.magicWords:
            if word['state'] != DGG.NORMAL:
                word['state'] = DGG.NORMAL

        self.activatorLabel['text'] = TTLocalizer.WordPageActivator + base.cr.magicWordManager.chatPrefix + ' (' + str(MagicWordConfig.PREFIX_ALLOWED.index(base.cr.magicWordManager.chatPrefix)) + ')'
        self.currentLabel['text'] = TTLocalizer.WordPageCurrent + TTLocalizer.WordPageNA
        self.ignore('mouse1')
        self.toggleEntryFocus(True)
        self.searchBarEntry.set('')
        self.updateWordSearch()
        self.hideInfoPanel()
        self.hide()

    def enter(self):
        for word in self.magicWords:
            if word['state'] != DGG.NORMAL:
                word['state'] = DGG.NORMAL

        self.activatorLabel['text'] = TTLocalizer.WordPageActivator + base.cr.magicWordManager.chatPrefix + ' (' + str(MagicWordConfig.PREFIX_ALLOWED.index(base.cr.magicWordManager.chatPrefix)) + ')'
        self.currentLabel['text'] = TTLocalizer.WordPageCurrent + TTLocalizer.WordPageNA
        self.accept('mouse1', self.toggleEntryFocus, extraArgs=[True])
        self.searchBarEntry.set('')
        self.updateWordSearch()
        self.hideInfoPanel()
        self.show()

    def scrollListTo(self):
        self.scrollList.scrollTo(int(self.slider['value']))

    def toggleEntryFocus(self, lose=False):
        if lose:
            self.searchBarEntry['focus'] = 0
            base.localAvatar.chatMgr.fsm.request('mainMenu')
            messenger.send("enable-hotkeys")
        else:
            base.localAvatar.chatMgr.fsm.request('otherDialog')
            messenger.send("disable-hotkeys")

    def setupWords(self, returnWords=False):
        words = []
        priorityWords = []
        nonCheatWords = []

        for wordName in magicWordIndex:
            word = magicWordIndex[wordName]
            if word['classname'] not in words:
                if not word['hidden']:
                    if word['priority']:
                        priorityWords.append(word['classname'])
                    if word['access'] == "NO_ACCESS":
                        nonCheatWords.append(word['classname'])
                    words.append(word['classname'])

        for word in priorityWords:
            if word in words:
                words.remove(word)
            if word in nonCheatWords:
                nonCheatWords.remove(word)

        for word in nonCheatWords:
            if word in words:
                words.remove(word)

        sortedWords = sorted(priorityWords) + sorted(nonCheatWords) + sorted(words)

        numWords = len(sortedWords)
        if returnWords:
            return numWords

        currentWordIndex = 0
        while currentWordIndex < numWords:
            newWordButton = DirectButton(parent=self, relief=None, text=sortedWords[currentWordIndex],
                                         text_align=TextNode.ALeft, text_scale=0.05, text1_bg=Vec4(0.5, 0.9, 1, 1),
                                         text2_bg=Vec4(1, 1, 0, 1), text3_fg=Vec4(0.4, 0.8, 0.4, 1), textMayChange=0,
                                         command=self.showWordInfo, extraArgs=[currentWordIndex])
            self.magicWords.append(newWordButton)
            self.shownMagicWords.append(newWordButton)
            currentWordIndex += 1

    def showWordInfo(self, wordNum):
        for word in self.magicWords:
            if word['state'] != DGG.NORMAL:
                word['state'] = DGG.NORMAL

        wordName = self.magicWords[wordNum]
        wordName['state'] = DGG.DISABLED
        self.currentLabel['text'] = TTLocalizer.WordPageCurrent + wordName['text']

    def updateWordSearch(self, extraArgs=None):
        self.hiddenMagicWords = []
        searchTerm = self.searchBarEntry.get().lower()
        for word in self.magicWords + self.hiddenMagicWords:
            wordLabel = word['text'].lower()
            if searchTerm not in wordLabel and word in self.magicWords:
                self.hiddenMagicWords.append(word)
                if word['state'] != DGG.NORMAL:
                    self.currentLabel['text'] = TTLocalizer.WordPageCurrent + TTLocalizer.WordPageNA
                    word['state'] = DGG.NORMAL
                word.hide()
            elif searchTerm in wordLabel and word in self.hiddenMagicWords:
                self.hiddenMagicWords.remove(word)
                word.show()

        self.shownMagicWords = []
        for word in self.magicWords:
            if word not in self.hiddenMagicWords:
                self.shownMagicWords.append(word)

        magicWordCount = len(self.shownMagicWords)
        if magicWordCount == 0:
            magicWordCount = 1

        self.totalLabel['text'] = TTLocalizer.WordPageTotal + str(len(self.shownMagicWords))
        self.scrollList['items'] = self.shownMagicWords
        self.slider['range'] = (magicWordCount, 0)

    def copyToChat(self):
        wordName = None
        for word in self.magicWords:
            if word['state'] != DGG.NORMAL:
                wordName = word['text']
                break

        if not wordName:
            return

        phrase = base.cr.magicWordManager.chatPrefix + wordName + ' '
        localAvatar.book.closeBook()
        localAvatar.chatMgr.fsm.request('mainMenu')
        localAvatar.chatMgr.chatInputNormal.typeCallback(None)
        localAvatar.chatMgr.chatInputNormal.chatEntry.enterText(phrase)

    def showInfoPanel(self):
        wordName = None
        for word in self.magicWords:
            if word['state'] != DGG.NORMAL:
                wordName = word['text']
                break

        if not wordName:
            return

        wordInfo = magicWordIndex[wordName.lower()]
        wordText = TTLocalizer.WordPageDescription + wordInfo['desc']
        prefix = base.cr.magicWordManager.chatPrefix
        if not wordInfo['example']:
            exampleText = TTLocalizer.WordPageExample + prefix + wordName.lower()
        else:
            exampleText = TTLocalizer.WordPageExample + prefix + wordName.lower() + ' ' + wordInfo['example']
        aliasText = TTLocalizer.WordPageAliases
        for alias in wordInfo['aliases']:
            aliasText += alias
            if wordInfo['aliases'].index(alias) != len(wordInfo['aliases']) - 1:
                aliasText += ', '
        accessLevelText = TTLocalizer.WordPageAccessLevel + wordInfo['access'] + ' (' + str(OTPGlobals.AccessLevelName2Int.get(wordInfo['access'])) + ')'

        lineBreak = '\n\n'
        infoText = wordText + lineBreak + exampleText + lineBreak + aliasText + lineBreak + accessLevelText

        self.magicWordTitle['text'] = wordName
        self.magicWordInfoLabel['text'] = infoText

        self.magicWordInfo.show()

    def hideInfoPanel(self):
        self.magicWordTitle['text'] = TTLocalizer.WordPageNA
        self.magicWordInfoLabel['text'] = TTLocalizer.WordPageNA

        self.magicWordInfo.hide()


class ClothingTabPage(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('ClothingTabPage')

    # TODO Clean Up if possible

    def __init__(self, parent = aspect2d):
        self.textRolloverColor = Vec4(1, 1, 0, 1)
        self.textDownColor = Vec4(0.5, 0.9, 1, 1)
        self.textDisabledColor = Vec4(0.4, 0.8, 0.4, 1)
        self._parent = parent
        self.currentSizeIndex = None
        DirectFrame.__init__(self, parent=self._parent, relief=None, pos=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0))
        self.load()

    def load(self):
        self.model = None
        self.turnSeq = Sequence()
        self.freakSeq = None
        self.word1Desc = DirectLabel(parent=hidden, relief=None, text='', text_align=TextNode.ALeft, text_scale=0.06, text_wordwrap=12, pos=(0.058, 0, 0))
        self.shirtList = []
        self.shirtIDs = []
        self.sleeveList = []
        self.sleeveIDs = []
        self.boyPantList = []
        self.boyPantIDs = []
        self.girlPantList = []
        self.girlPantIDs = []
        self.girlPantTypes = []
        self.colorList = []
        self.colorIDs = []
        av = base.cr.doId2do.get(base.localAvatar.doId)
        self.shirt = av.style.topTex
        self.shirtColor = av.style.topTexColor
        self.sleeve = av.style.sleeveTex
        self.sleeveColor = av.style.sleeveTexColor
        self.pant = av.style.botTex
        self.pantColor = av.style.botTexColor
        genderList = ['m', 'f']
        self.gender = genderList.index(av.style.gender)
        self.color = 0
        self.torsoSize = av.style.torso[0]
        self.torsoType = 's'
        if len(av.style.torso) > 1:
            self.torsoType = av.style.torso[1]
        self.l = locals()
        self.makeList()
        self.shirtWords = list(self.shirtList)
        self.sleeveWords = list(self.sleeveList)
        self.boyPantWords = list(self.boyPantList)
        self.girlPantWords = list(self.girlPantList)
        self.colorWords = list(self.colorIDs)
        self.rainbowEffect = Sequence()

        self.makeScrollLists()
        self.createModel()
        self.makeButtons()


    def scrollListTo(self, scrollList, slider):
        if slider == 'shirt':
            slider = self.shirtslider
        elif slider == 'sleeve':
            slider = self.sleeveslider
        elif slider == 'boypants':
            slider = self.pantslider1
        elif slider == 'girlpants':
            slider = self.pantslider2
        elif slider == 'color':
            slider = self.colorslider
        scrollList.scrollTo(int(slider['value']))

    def makeList(self):
        for x in range(len(ToonDNA.Shirts)):
            self.l['self.shirts' + str(x)] = DirectButton(parent=self, relief=None, text=str(x) + " - " + ToonDNA.Shirts[x].split('/', 1)[-1].split('/', 1)[-1].replace(".jpg", ""), text_align=TextNode.ALeft, text_scale=0.05, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, textMayChange=1, command=self.showWordInfo, extraArgs=[x, self.word1Desc, 'shirt'])
            #--disposing of long labels--

            if ToonDNA.Shirts[x].split('/', 1)[-1].split('/', 1)[-1].startswith('apparel/') or ToonDNA.Shirts[x].split('/', 1)[-1].split('/', 1)[-1].startswith('tiers/'):
                self.l['self.shirts' + str(x)]["text"] = str(x) + " - " + ToonDNA.Shirts[x].split('/', 1)[-1].split('/', 1)[-1].split('/', 1)[-1].replace(".jpg", "")
            elif ToonDNA.Shirts[x].split('/', 1)[-1].split('/', 1)[-1].startswith('tt_t_chr_'):
                self.l['self.shirts' + str(x)]["text"] = str(x) + " - " + ToonDNA.Shirts[x].split('/', 1)[-1].split('/', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].replace(".jpg", "")

            self.shirtList.append(self.l['self.shirts' + str(x)])
            self.shirtIDs.append( x )
        for x in range(len(ToonDNA.Sleeves)):
            self.l['self.sleeves' + str(x)] = DirectButton(parent=self, relief=None, text=str(x) + " - " + ToonDNA.Sleeves[x].split('/', 1)[-1].split('/', 1)[-1].replace(".jpg", ""), text_align=TextNode.ALeft, text_scale=0.05, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, textMayChange=1, command=self.showWordInfo, extraArgs=[x, self.word1Desc, 'sleeve'])

            if ToonDNA.Sleeves[x].split('/', 1)[-1].split('/', 1)[-1].startswith('apparel/') or ToonDNA.Sleeves[x].split('/', 1)[-1].split('/', 1)[-1].startswith('tiers/'):
                self.l['self.sleeves' + str(x)]["text"] = str(x) + " - " + ToonDNA.Sleeves[x].split('/', 1)[-1].split('/', 1)[-1].split('/', 1)[-1].replace(".jpg", "")
            elif ToonDNA.Sleeves[x].split('/', 1)[-1].split('/', 1)[-1].startswith('tt_t_chr_'):
                self.l['self.sleeves' + str(x)]["text"] = str(x) + " - " + ToonDNA.Sleeves[x].split('/', 1)[-1].split('/', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].replace(".jpg", "")

            self.sleeveList.append(self.l['self.sleeves' + str(x)])
            self.sleeveIDs.append( x )
        for x in range(len(ToonDNA.BoyShorts)):
            self.l['self.boypants' + str(x)] = DirectButton(parent=self, relief=None, text=str(x) + " - " + ToonDNA.BoyShorts[x].split('/', 1)[-1].split('/', 1)[-1].replace(".jpg", ""), text_align=TextNode.ALeft, text_scale=0.05, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, textMayChange=1, command=self.showWordInfo, extraArgs=[x, self.word1Desc, 'pants'])

            if ToonDNA.BoyShorts[x].split('/', 1)[-1].split('/', 1)[-1].startswith('apparel/') or ToonDNA.BoyShorts[x].split('/', 1)[-1].split('/', 1)[-1].startswith('tiers/'):
                self.l['self.boypants' + str(x)]["text"] = str(x) + " - " + ToonDNA.BoyShorts[x].split('/', 1)[-1].split('/', 1)[-1].split('/', 1)[-1].replace(".jpg", "")
            elif ToonDNA.BoyShorts[x].split('/', 1)[-1].split('/', 1)[-1].startswith('tt_t_chr_'):
                self.l['self.boypants' + str(x)]["text"] = str(x) + " - " + ToonDNA.BoyShorts[x].split('/', 1)[-1].split('/', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].replace(".jpg", "")

            self.boyPantList.append(self.l['self.boypants' + str(x)])
            self.boyPantIDs.append( x )
        for x in range(len(ToonDNA.GirlBottoms)):
            pantsTypes = ['s', 'd']
            self.l['self.girlpants' + str(x)] = DirectButton(parent=self, relief=None, text=str(x) + " - " + ToonDNA.GirlBottoms[x][0].split('/', 1)[-1].split('/', 1)[-1].replace(".jpg", ""), text_align=TextNode.ALeft, text_scale=0.05, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, textMayChange=1, command=self.showWordInfo, extraArgs=[x, self.word1Desc, 'pants'])

            if ToonDNA.GirlBottoms[x][0].split('/', 1)[-1].split('/', 1)[-1].startswith('apparel/') or ToonDNA.GirlBottoms[x][0].split('/', 1)[-1].split('/', 1)[-1].startswith('tiers/'):
                self.l['self.girlpants' + str(x)]["text"] = str(x) + " - " + ToonDNA.GirlBottoms[x][0].split('/', 1)[-1].split('/', 1)[-1].split('/', 1)[-1].replace(".jpg", "")
            elif ToonDNA.GirlBottoms[x][0].split('/', 1)[-1].split('/', 1)[-1].startswith('tt_t_chr_'):
                self.l['self.girlpants' + str(x)]["text"] = str(x) + " - " + ToonDNA.GirlBottoms[x][0].split('/', 1)[-1].split('/', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].replace(".jpg", "")

            #--end of eye-bleeding code--
            self.girlPantList.append(self.l['self.girlpants' + str(x)])
            self.girlPantIDs.append( x )
            self.girlPantTypes.append(pantsTypes[ToonDNA.GirlBottoms[x][1]])
        for x in range(len(ToonDNA.allColorsList)):
            self.l['self.colors' + str(x)] = DirectButton(parent=self, relief=None, text=str(x), text_align=TextNode.ALeft, text_scale=0.05, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, textMayChange=0, command=self.showWordInfo, extraArgs=[x, self.word1Desc, 'color'])
            self.colorList.append(self.l['self.colors' + str(x)])
            self.colorIDs.append(x)

        self.shirtLabel = DirectLabel(parent=self, relief=None,
                                     text="Shirt ID: " + str(self.shirt) + ' / ' + str(self.shirtColor),
                                     text_align=TextNode.ALeft, text_scale=0.06, text_wordwrap=12, pos=(-0.75, 0, 0.5))
        self.sleeveLabel = DirectLabel(parent=self, relief=None,
                                     text="Sleeve ID: " + str(self.sleeve) + ' / ' + str(self.sleeveColor),
                                     text_align=TextNode.ALeft, text_scale=0.06, text_wordwrap=12, pos=(-0.2, 0, 0.5))
        self.pantLabel = DirectLabel(parent=self, relief=None,
                                     text="Pants ID: " + str(self.pant) + ' / ' + str(self.pantColor),
                                     text_align=TextNode.ALeft, text_scale=0.06, text_wordwrap=12, pos=(0.35, 0, 0.5))
        self.colorSelectedLabel = DirectLabel(parent=self, relief=None,
                                              text="Color Selected: " + str(self.color),
                                              text_align=TextNode.ALeft, text_scale=0.06, text_wordwrap=12, pos=(0.35, 0, -0.65))
        pickAToonGui = loader.loadModel('phase_3.5/models/gui/matching_game_gui')

        self.colorTest = DirectButton(parent=self, relief=None, image=pickAToonGui.find('**/minnieCircle'),
                                      image_scale=0.375, image2_scale=0.4375, pos=(0.3, 0, -0.635), text_scale=0.04,
                                      text_align=TextNode.ACenter, text_pos=(-0.00625, 0.00625), text="Color\nAll", text_fg=Vec4(0, 0, 0, 0),
                                      text1_fg=Vec4(0, 0, 0, 0), text2_fg=Vec4(0, 0, 0, 1), text3_fg=Vec4(0, 0, 0, 0), command=self.showWordInfo,
                                      extraArgs=[8008135, 'huh', 'all', True])

        pickAToonGui.removeNode()
        self.colorTest.setColor(ToonDNA.allColorsList[self.color])
        self.colorTest['text2_fg'] = Vec4(0, 0, 0, 1) + Vec4(ToonDNA.allColorsList[self.color][0], ToonDNA.allColorsList[self.color][1],
                                                             ToonDNA.allColorsList[self.color][2], 1)/3
        self.nakedLabel = DirectLabel(relief=None,
                                      text="Naked Toons\nDon't Wear Clothing!", text_font=ToontownGlobals.getSignFont(), pos=(0, 0, 0),
                                      text_fg=(1, 0, 0, 1), text_align=TextNode.ACenter, text_scale=0.2)
        self.freakSeq = Sequence(Func(self.nakedLabel.show), SoundInterval(loader.loadSfx('phase_9/audio/sfx/CHQ_GOON_tractor_beam_alarmed.ogg')), Func(self.nakedLabel.hide), Func(self.enableClothButton, 1))
        self.nakedLabel.hide()

    def unload(self):
        for x in range(len(ToonDNA.Shirts)):
            del self.l['self.shirts' + str(x)]
        for x in range(len(ToonDNA.Sleeves)):
            del self.l['self.sleeves' + str(x)]
        for x in range(len(ToonDNA.BoyShorts)):
            del self.l['self.boypants' + str(x)]
        for x in range(len(ToonDNA.GirlBottoms)):
            del self.l['self.girlpants' + str(x)]
        for x in range(len(ToonDNA.allColorsList)):
            del self.l['self.colors' + str(x)]
        del self.shirtLabel
        del self.sleeveLabel
        del self.pantLabel
        del self.colorSelectedLabel
        del self.colorTest
        if self.freakSeq.isPlaying():
            self.freakSeq.finish()
        del self.nakedLabel

        self.shirtScrollList.destroy()
        del self.shirtScrollList
        self.sleeveScrollList.destroy()
        del self.sleeveScrollList
        self.pantScrollList1.destroy()
        del self.pantScrollList1
        self.pantScrollList2.destroy()
        del self.pantScrollList2
        self.colorScrollList.destroy()
        del self.colorScrollList

        self.shirtslider.destroy()
        del self.shirtslider
        self.sleeveslider.destroy()
        del self.sleeveslider
        self.pantslider1.destroy()
        del self.pantslider1
        self.pantslider2.destroy()
        del self.pantslider2
        self.colorslider.destroy()
        del self.colorslider

        self.toggleGender.destroy()
        del self.toggleGender
        self.toggleBody.destroy()
        del self.toggleBody
        self.toggleNude.destroy()
        del self.toggleNude
        self.colorShirt.destroy()
        del self.colorShirt
        self.colorSleeve.destroy()
        del self.colorSleeve
        self.colorPant.destroy()
        del self.colorPant
        self.setClothes.destroy()
        del self.setClothes

        if self.turnSeq.isPlaying():
            self.turnSeq.finish()
        del self.turnSeq
        if self.rainbowEffect.isPlaying():
            self.rainbowEffect.finish()
        del self.rainbowEffect
        self.model.removeNode()
        del self.model

    def exit(self):
        self.ignore('confirmDone')
        self.hide()

    def enter(self):
        self.ignore('confirmDone')
        self.show()

    def createModel(self):
        if self.turnSeq.isPlaying():
            self.turnSeq.finish()
        if self.rainbowEffect.isPlaying():
            self.rainbowEffect.finish()
            self.rainbowEffect = Sequence()
        magicParallel = Parallel()
        if self.model:
            self.model.removeNode()
            del self.model
        toon = Toon.Toon()
        dna = ToonDNA.ToonDNA()
        if self.gender == 1:
            gender = 'f'
        else:
            gender = 'm'
        dna.newToon(('cls', self.torsoSize + self.torsoType, 'm', gender))
        if self.torsoType != '':
            dna.topTex = self.shirt
            dna.topTexColor = self.shirtColor
            dna.botTex = self.pant
            dna.botTexColor = self.pantColor
            dna.sleeveTex = self.sleeve
            dna.sleeveTexColor = self.sleeveColor
        dna.armColor = 27
        toon.setDNA(dna)
        self.model = NodePath('clothing')
        if self.torsoType != '':
            pieceNames = ('**/1000/**/torso-top', '**/1000/**/sleeves', '**/1000/**/torso-bot',)
            for name in pieceNames:
                for piece in toon.findAllMatches(name):
                    piece.wrtReparentTo(self.model)
        else:
            for piece in toon.findAllMatches('**/1000/**/torso'):
                piece.wrtReparentTo(self.model)
                magicParallel.append(Sequence(
                    LerpColorInterval(piece, duration=1, color=VBase4(0.996094, 0.898438, 0.320312, 1.0)),
                    LerpColorInterval(piece, duration=1, color=VBase4(0.304688, 0.96875, 0.402344, 1.0)),
                    LerpColorInterval(piece, duration=1, color=VBase4(0.191406, 0.5625, 0.773438, 1.0)),
                    LerpColorInterval(piece, duration=0.5, color=VBase4(0.546875, 0.28125, 0.75, 1.0)),
                    LerpColorInterval(piece, duration=0.5, color=VBase4(0.933594, 0.265625, 0.28125, 1.0))
                ))
            self.rainbowEffect.append(magicParallel)
            self.rainbowEffect.loop()

        toon.delete()
        self.model.setH(180)
        self.model.reparentTo(self)
        self.model.setScale(0.125)
        self.model.setPos(0.2, 0, -0.425)
        self.model.setBin('unsorted', 0, 1)
        self.model.setDepthTest(True)
        self.model.setDepthWrite(True)
        self.turnSeq = LerpHprInterval(self.model, duration=5, hpr=(540, 0, 0), startHpr=(180, 0, 0))
        self.turnSeq.loop()

    def makeButtons(self):
        if self.torsoSize == 'l':
            b = "Long"
        elif self.torsoSize == 'm':
            b = "Med"
        else:
            b = "Short"
        if self.gender == 0:
            a = "Male"
        else:
            a = "Female"
        gui = loader.loadModel('phase_3/models/gui/pick_a_toon_gui')
        self.toggleGender = DirectButton(parent=self,
            image=(gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'), gui.find('**/QuitBtn_RLVR'), gui.find('**/QuitBtn_RLVR')), relief=None,
            text='Toggle Gender (%s)' % a, text_scale=0.04, text_pos=(0, -0.0125), scale=0.8, pos=(0.2, 0, -0.4), command=self.changeBody, extraArgs=['gender'])
        self.toggleBody = DirectButton(parent=self,
            image=(gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'), gui.find('**/QuitBtn_RLVR')), relief=None,
            text='Toggle Body (%s)' % b, text_scale=0.04, text_pos=(0, -0.0125), scale=0.8, pos=(0.2, 0, -0.5), command=self.changeBody, extraArgs=['body'])
        self.toggleNude = DirectButton(parent=self,
                                       image=(gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'),
                                              gui.find('**/QuitBtn_RLVR')), relief=None,
                                       text='Streak', text_scale=0.065, text_pos=(0, -0.0125), scale=0.8,
                                       pos=(0.6, 0, -0.525), command=self.changeBody, extraArgs=['nude'])
        self.colorShirt = DirectButton(parent=self,
                                       image=(gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'),
                                              gui.find('**/QuitBtn_RLVR'), gui.find('**/QuitBtn_RLVR')), relief=None,
                                       text='Color Shirt', text_scale=0.065, text_pos=(0, -0.0125), scale=0.6,
                                       pos=(-0.7, 0, -0.55), command=self.showWordInfo, extraArgs=[self.color, 'huh', 'shirt', True])
        self.colorSleeve = DirectButton(parent=self,
                                       image=(gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'),
                                              gui.find('**/QuitBtn_RLVR'), gui.find('**/QuitBtn_RLVR')), relief=None,
                                       text='Color Sleeve', text_scale=0.065, text_pos=(0, -0.0125), scale=0.6,
                                       pos=(-0.45, 0, -0.55), command=self.showWordInfo,
                                       extraArgs=[self.color, 'huh', 'sleeve', True])
        self.colorPant = DirectButton(parent=self,
                                        image=(gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'),
                                               gui.find('**/QuitBtn_RLVR'), gui.find('**/QuitBtn_RLVR')), relief=None,
                                        text='Color Pants', text_scale=0.065, text_pos=(0, -0.0125), scale=0.6,
                                        pos=(-0.2, 0, -0.55), command=self.showWordInfo,
                                        extraArgs=[8008135, 'huh', 'pants', True])
        self.setClothes = DirectButton(parent=self,
                                      image=(gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'),
                                             gui.find('**/QuitBtn_RLVR'), gui.find('**/QuitBtn_DN')), relief=None,
                                      text='Set As Outfit', text_scale=0.05, text_pos=(0, -0.0125), scale=0.8,
                                      pos=(0, 0, -0.65), command=self.setAsClothing)
        av = base.cr.doId2do.get(base.localAvatar.doId)
        self.toggleNude.hide()
        if len(av.style.torso) == 1:
            self.changeBody("nude")

    def setAsClothing(self):
        av = base.cr.doId2do.get(base.localAvatar.doId)
        genderList = ['m', 'f']
        if av.style.gender != genderList[self.gender] and self.torsoType != '':
            self.changeBody('gender')
        newDNA = ToonDNA.ToonDNA()
        newDNA.makeFromNetString(av.style.makeNetString())
        newDNA.torso = av.style.torso[0] + self.torsoType
        newDNA.topTex = self.shirt
        newDNA.topTexColor = self.shirtColor
        newDNA.botTex = self.pant
        newDNA.botTexColor = self.pantColor
        newDNA.sleeveTex = self.sleeve
        newDNA.sleeveTexColor = self.sleeveColor
        av.sendUpdate('setMagicDNA', [newDNA.makeNetString()])

    def nakedDetect(self):
        self.enableClothButton(0)
        self.freakSeq.start()

    def enableClothButton(self, active):
        if active == 0:
            self.setClothes['state'] = DGG.DISABLED
        else:
            self.setClothes['state'] = DGG.NORMAL

    def changeBody(self, type):
        if type == 'gender':
            if self.gender == 0:
                self.gender = 1
                try:
                    self.torsoType = self.girlPantTypes[self.pant]
                except:
                    self.torso = self.girlPantIDs[-1]
                    self.torsoType = self.girlPantTypes[-1]
                self.pantScrollList1.hide()
                self.pantslider1.hide()
                self.pantScrollList2.show()
                self.pantslider2.show()
                self.toggleGender['text'] = 'Toggle Gender (Female)'
            else:
                self.gender = 0
                self.torsoType = 's'
                self.pantScrollList2.hide()
                self.pantslider2.hide()
                self.pantScrollList1.show()
                self.pantslider1.show()
                self.toggleGender['text'] = 'Toggle Gender (Male)'
        elif type == 'body':
            if self.torsoSize == 'm':
                self.torsoSize = 'l'
                self.toggleBody['text'] = 'Toggle Body (Long)'
            elif self.torsoSize == 'l':
                self.torsoSize = 's'
                self.toggleBody['text'] = 'Toggle Body (Short)'
            else:
                self.torsoSize = 'm'
                self.toggleBody['text'] = 'Toggle Body (Med)'
        elif type == 'nude':
            if self.torsoType == '':
                self.torsoType = 's'
                if self.gender == 1:
                    try:
                        self.torsoType = self.girlPantTypes[self.pant]
                    except:
                        self.torso = self.girlPantIDs[-1]
                        self.torsoType = self.girlPantTypes[-1]
                self.toggleGender['state'] = DGG.NORMAL
                self.colorShirt['state'] = DGG.NORMAL
                self.colorSleeve['state'] = DGG.NORMAL
                self.colorPant['state'] = DGG.NORMAL
                self.colorTest['state'] = DGG.NORMAL
                self.toggleNude['text'] = "Streak"
            else:
                self.torsoType = ''
                self.toggleGender['state'] = DGG.DISABLED
                self.colorShirt['state'] = DGG.DISABLED
                self.colorSleeve['state'] = DGG.DISABLED
                self.colorPant['state'] = DGG.DISABLED
                self.colorTest['state'] = DGG.DISABLED
                self.toggleNude['text'] = "Clothe"
            self.toggleAllWords()
        self.createModel()

    def toggleAllWords(self):
        i = 0
        j = 0
        currentEnabled = (self.shirt, self.sleeve, self.pant, self.pant, self.color)
        for list in (self.shirtList, self.sleeveList, self.boyPantList, self.girlPantList, self.colorList):
            for word in list:
                if self.torsoType == '':
                    word['state'] = DGG.DISABLED
                else:
                    if currentEnabled[i] == j:
                        word['state'] = DGG.DISABLED
                    else:
                        word['state'] = DGG.NORMAL
                j += 1
            i += 1
            j = 0

    def showWordInfo(self, wordNum, desc, clothType, isColorChange=False):
        if isColorChange:
            wordNum = self.color
        if clothType == 'sleeve':
            clothList = self.sleeveList
        elif clothType == 'pants' and self.gender == 0:
            clothList = self.boyPantList
        elif clothType == 'pants' and self.gender == 1:
            clothList = self.girlPantList
        elif clothType == 'color':
            clothList = self.colorList
        elif clothType == 'all':
            pass
        else:
            clothList = self.shirtList
        if not isColorChange:
            for word in clothList:
                if word['state'] != DGG.NORMAL:
                    word['state'] = DGG.NORMAL

            wordName = clothList[wordNum]
            wordName['state'] = DGG.DISABLED

        if clothType == 'all':
            if isColorChange:
                self.sleeveColor = wordNum
                self.model.find('**/sleeves').setColor(ToonDNA.allColorsList[wordNum], 1)
                self.pantColor = wordNum
                self.model.find('**/torso-bot').setColor(ToonDNA.allColorsList[wordNum], 1)
                self.shirtColor = wordNum
                self.model.find('**/torso-top').setColor(ToonDNA.allColorsList[wordNum], 1)
                self.shirtLabel['text'] = "Shirt ID: " + str(self.shirt) + ' / ' + str(self.shirtColor)
                self.sleeveLabel['text'] = "Sleeve ID: " + str(self.sleeve) + ' / ' + str(self.sleeveColor)
                self.pantLabel['text'] = "Pants ID: " + str(self.pant) + ' / ' + str(self.pantColor)

        if clothType == 'sleeve':
            if isColorChange:
                self.sleeveColor = wordNum
                self.model.find('**/sleeves').setColor(ToonDNA.allColorsList[wordNum], 1)
            else:
                self.sleeve = wordNum
                try:
                    self.model.find('**/sleeves').setTexture(loader.loadTexture(ToonDNA.Sleeves[wordNum]), 1)
                except IOError:
                    wordNum = 0
                    self.sleeve = wordNum
                    self.model.find('**/sleeves').setTexture(loader.loadTexture(ToonDNA.Sleeves[wordNum]), 1)
        elif clothType == 'pants':
            if isColorChange:
                self.pantColor = wordNum
            else:
                self.pant = wordNum
            if self.gender == 1 and self.girlPantTypes[wordNum] != self.torsoType:
                self.torsoType = self.girlPantTypes[wordNum]
                self.createModel()
            elif self.gender == 0 and self.torsoType != 's':
                self.torsoType = 's'
                self.createModel()
            else:
                if isColorChange:
                    self.model.find('**/torso-bot').setColor(ToonDNA.allColorsList[wordNum], 1)
                else:
                    try:
                        if self.gender == 1:
                            self.model.find('**/torso-bot').setTexture(loader.loadTexture(ToonDNA.GirlBottoms[wordNum][0]), 1)
                        else:
                            self.model.find('**/torso-bot').setTexture(loader.loadTexture(ToonDNA.BoyShorts[wordNum]), 1)
                    except IOError:
                        wordNum = 0
                        self.pant = wordNum
                        if self.gender == 1:
                            self.model.find('**/torso-bot').setTexture(loader.loadTexture(ToonDNA.GirlBottoms[wordNum][0]), 1)
                        else:
                            self.model.find('**/torso-bot').setTexture(loader.loadTexture(ToonDNA.BoyShorts[wordNum]), 1)
        elif clothType == 'color':
            self.color = wordNum
        else:
            if isColorChange:
                self.shirtColor = wordNum
                self.model.find('**/torso-top').setColor(ToonDNA.allColorsList[wordNum], 1)
            else:
                self.shirt = wordNum
                try:
                    self.model.find('**/torso-top').setTexture(loader.loadTexture(ToonDNA.Shirts[wordNum]), 1)
                except IOError:
                    wordNum = 0
                    self.shirt = wordNum
                    self.model.find('**/torso-top').setTexture(loader.loadTexture(ToonDNA.Shirts[wordNum]), 1)

        if clothType == 'shirt':
            self.shirtLabel['text'] = "Shirt ID: " + str(self.shirt) + ' / ' + str(self.shirtColor)
        elif clothType == 'sleeve':
            self.sleeveLabel['text'] = "Sleeve ID: " + str(self.sleeve) + ' / ' + str(self.sleeveColor)
        elif clothType == 'pants':
            self.pantLabel['text'] = "Pants ID: " + str(self.pant) + ' / ' + str(self.pantColor)
        elif clothType == 'color':
            self.colorSelectedLabel['text'] = "Color Selected: " + str(self.color)
            self.colorTest.setColor(ToonDNA.allColorsList[self.color])
            self.colorTest['text2_fg'] = Vec4(0, 0, 0, 1) + Vec4(ToonDNA.allColorsList[self.color][0],
                                                                 ToonDNA.allColorsList[self.color][1],
                                                                 ToonDNA.allColorsList[self.color][2], 1)/3

    def makeScrollLists(self):
        gui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
        coolbutton = loader.loadModel('phase_3/models/gui/pick_a_toon_gui')
        self.shirtScrollList = DirectScrolledList(parent=self, relief=None, forceHeight=0.07, pos=(-0.5, 0, 0),
                                                  itemFrame_pos=(-0.237, 0, 0.41), itemFrame_scale=1.0,
                                                  itemFrame_relief=DGG.SUNKEN, itemFrame_frameSize=(-0.05,
                                                                                                    0.66,
                                                                                                    -0.4,
                                                                                                    0.07),
                                                  itemFrame_frameColor=(0.85, 0.95, 1, 1),
                                                  itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=6,
                                                  items=list(self.shirtList))
        make_dsl_scrollable(self.shirtScrollList)
        self.shirtScrollList.incButton.reparentTo(hidden)
        self.shirtScrollList.decButton.reparentTo(hidden)
        self.shirtslider = DirectSlider(parent=self, range=(len(self.shirtIDs), 0),
                                   scale=(0.7, 0.7, 0.225), pos=(-0.1, 0, 0.245),
                                   pageSize=1, orientation=DGG.VERTICAL, command=self.scrollListTo, extraArgs=[self.shirtScrollList, 'shirt'],
                                   thumb_geom=(coolbutton.find('**/QuitBtn_UP'),
                                               coolbutton.find('**/QuitBtn_DN'),
                                               coolbutton.find('**/QuitBtn_RLVR'),
                                               coolbutton.find('**/QuitBtn_UP')),
                                   thumb_relief=None, thumb_geom_hpr=(0, 0, -90), thumb_geom_scale=(0.35, 1, 0.5))
        self.sleeveScrollList = DirectScrolledList(parent=self, relief=None, forceHeight=0.07, pos=(0.35, 0, 0),
                                                  itemFrame_pos=(-0.237, 0, 0.41), itemFrame_scale=1.0,
                                                  itemFrame_relief=DGG.SUNKEN, itemFrame_frameSize=(-0.05,
                                                                                                    0.66,
                                                                                                    -0.4,
                                                                                                    0.07),
                                                  itemFrame_frameColor=(0.85, 0.95, 1, 1),
                                                  itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=6,
                                                  items=list(self.sleeveList))
        make_dsl_scrollable(self.sleeveScrollList)
        self.sleeveScrollList.incButton.reparentTo(hidden)
        self.sleeveScrollList.decButton.reparentTo(hidden)
        self.sleeveslider = DirectSlider(parent=self, range=(len(self.sleeveIDs), 0),
                                        scale=(0.7, 0.7, 0.225), pos=(0.75, 0, 0.245),
                                        pageSize=1, orientation=DGG.VERTICAL, command=self.scrollListTo,  extraArgs=[self.sleeveScrollList, 'sleeve'],
                                        thumb_geom=(coolbutton.find('**/QuitBtn_UP'),
                                                    coolbutton.find('**/QuitBtn_DN'),
                                                    coolbutton.find('**/QuitBtn_RLVR'),
                                                    coolbutton.find('**/QuitBtn_UP')),
                                        thumb_relief=None, thumb_geom_hpr=(0, 0, -90), thumb_geom_scale=(0.35, 1, 0.5))
        self.pantScrollList1 = DirectScrolledList(parent=self, relief=None, forceHeight=0.07, pos=(-0.5, 0, 0),
                                                 itemFrame_pos=(-0.237, 0, -0.08), itemFrame_scale=1.0,
                                                 itemFrame_relief=DGG.SUNKEN, itemFrame_frameSize=(-0.05,
                                                                                                   0.66,
                                                                                                   -0.4,
                                                                                                   0.07),
                                                 itemFrame_frameColor=(0.85, 0.95, 1, 1),
                                                 itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=6,
                                                 items=list(self.boyPantList))
        make_dsl_scrollable(self.pantScrollList1)
        self.pantScrollList1.incButton.reparentTo(hidden)
        self.pantScrollList1.decButton.reparentTo(hidden)
        self.pantslider1 = DirectSlider(parent=self, range=(len(self.boyPantIDs), 0),
                                       scale=(0.7, 0.7, 0.225), pos=(-0.1, 0, -0.245),
                                       pageSize=1, orientation=DGG.VERTICAL, command=self.scrollListTo,
                                       extraArgs=[self.pantScrollList1, 'boypants'],
                                       thumb_geom=(coolbutton.find('**/QuitBtn_UP'),
                                                   coolbutton.find('**/QuitBtn_DN'),
                                                   coolbutton.find('**/QuitBtn_RLVR'),
                                                   coolbutton.find('**/QuitBtn_UP')),
                                       thumb_relief=None, thumb_geom_hpr=(0, 0, -90), thumb_geom_scale=(0.5, 1, 0.5))
        if self.gender == 1:
            self.pantScrollList1.hide()
            self.pantslider1.hide()
        self.pantScrollList2 = DirectScrolledList(parent=self, relief=None, forceHeight=0.07, pos=(-0.5, 0, 0),
                                                  itemFrame_pos=(-0.237, 0, -0.08), itemFrame_scale=1.0,
                                                  itemFrame_relief=DGG.SUNKEN, itemFrame_frameSize=(-0.05,
                                                                                                    0.66,
                                                                                                    -0.4,
                                                                                                    0.07),
                                                  itemFrame_frameColor=(0.85, 0.95, 1, 1),
                                                  itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=6,
                                                  items=list(self.girlPantList))
        make_dsl_scrollable(self.pantScrollList2)
        self.pantScrollList2.incButton.reparentTo(hidden)
        self.pantScrollList2.decButton.reparentTo(hidden)
        self.pantslider2 = DirectSlider(parent=self, range=(len(self.girlPantIDs), 0),
                                        scale=(0.7, 0.7, 0.225), pos=(-0.1, 0, -0.245),
                                        pageSize=1, orientation=DGG.VERTICAL, command=self.scrollListTo,
                                        extraArgs=[self.pantScrollList2, 'girlpants'],
                                        thumb_geom=(coolbutton.find('**/QuitBtn_UP'),
                                                    coolbutton.find('**/QuitBtn_DN'),
                                                    coolbutton.find('**/QuitBtn_RLVR'),
                                                    coolbutton.find('**/QuitBtn_UP')),
                                        thumb_relief=None, thumb_geom_hpr=(0, 0, -90), thumb_geom_scale=(0.5, 1, 0.5))
        if self.gender == 0:
            self.pantScrollList2.hide()
            self.pantslider2.hide()
        self.colorScrollList = DirectScrolledList(parent=self, relief=None, forceHeight=0.07, pos=(0.68, 0, 0),
                                                  itemFrame_pos=(-0.237, 0, -0.08), itemFrame_scale=1.0,
                                                  itemFrame_relief=DGG.SUNKEN, itemFrame_frameSize=(-0.05,
                                                                                                    0.33,
                                                                                                    -0.4,
                                                                                                    0.07),
                                                  itemFrame_frameColor=(0.85, 0.95, 1, 1),
                                                  itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=6,
                                                  items=list(self.colorList))
        make_dsl_scrollable(self.colorScrollList)
        self.colorScrollList.incButton.reparentTo(hidden)
        self.colorScrollList.decButton.reparentTo(hidden)
        self.colorslider = DirectSlider(parent=self, range=(len(self.colorIDs), 0),
                                        scale=(0.7, 0.7, 0.225), pos=(0.75, 0, -0.245),
                                        pageSize=1, orientation=DGG.VERTICAL, command=self.scrollListTo,
                                        extraArgs=[self.colorScrollList, 'color'],
                                        thumb_geom=(coolbutton.find('**/QuitBtn_UP'),
                                                    coolbutton.find('**/QuitBtn_DN'),
                                                    coolbutton.find('**/QuitBtn_RLVR'),
                                                    coolbutton.find('**/QuitBtn_UP')),
                                        thumb_relief=None, thumb_geom_hpr=(0, 0, -90), thumb_geom_scale=(0.75, 1, 0.5))
        gui.removeNode()
        coolbutton.removeNode()


class AccTabPage1(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('AccTabPage1')

    # TODO Clean Up if possible

    def __init__(self, parent = aspect2d):
        self.textRolloverColor = Vec4(1, 1, 0, 1)
        self.textDownColor = Vec4(0.5, 0.9, 1, 1)
        self.textDisabledColor = Vec4(0.4, 0.8, 0.4, 1)
        self._parent = parent
        self.currentSizeIndex = None
        DirectFrame.__init__(self, parent=self._parent, relief=None, pos=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0))
        self.load()

    def load(self):
        self.model = None
        self.turnSeq = Sequence()
        self.word1Desc = DirectLabel(parent=hidden, relief=None, text='', text_align=TextNode.ALeft, text_scale=0.06, text_wordwrap=12, pos=(0.058, 0, 0))
        self.hatList = []
        self.hatIDs = []
        self.hatTexList = []
        self.hatTexIDs = []
        self.glassesList = []
        self.glassesIDs = []
        self.glassesTexList = []
        self.glassesTexIDs = []
        self.hat = 0
        self.hatTex = 0
        self.glasses = 0
        self.glassesTex = 0
        av = base.cr.doId2do.get(base.localAvatar.doId)
        self.headType = ToonDNA.toonHeadTypes.index(av.style.head)
        self.headName = ToonDNA.toonHeadTypes[self.headType]
        self.gender = av.style.gender
        self.l = locals()
        self.makeList()
        self.hatWords = list(self.hatList)
        self.hatTexWords = list(self.hatTexList)
        self.glassesWords = list(self.glassesList)
        self.glassesTexWords = list(self.glassesTexList)

        self.makeScrollLists()
        self.createModel()
        self.makeButtons()


    def scrollListTo(self, scrollList, slider):
        if slider == 'hat':
            slider = self.hatslider
        elif slider == 'hatTex':
            slider = self.hattexslider
        elif slider == 'glasses':
            slider = self.glassesslider
        elif slider == 'glassesTex':
            slider = self.glassestexslider
        scrollList.scrollTo(int(slider['value']))

    def makeSplit(self, string):
        abble = string.split('/', 1)[-1].split('/', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_',1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_', 1)[-1]
        return abble

    def makeList(self):
        for x in range(len(ToonDNA.HatModels)):
            text = str(x) + " - "
            if ToonDNA.HatModels[x] == None:
                text += "No Hat"
            else:
                text += self.makeSplit(ToonDNA.HatModels[x])

            self.l['self.hats' + str(x)] = DirectButton(parent=self, relief=None, text=text, text_align=TextNode.ALeft, text_scale=0.05, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, textMayChange=1, command=self.showWordInfo, extraArgs=[x, self.word1Desc, 'hat'])

            self.l['self.hats' + str(x)]["text"] = text

            self.hatList.append(self.l['self.hats' + str(x)])
            self.hatIDs.append(x)
        for x in range(len(ToonDNA.HatTextures)):
            text = str(x) + " - "
            if ToonDNA.HatTextures[x] == None:
                text += "Normal Texture"
            else:
                text += self.makeSplit(ToonDNA.HatTextures[x].replace(".jpg", ""))

            self.l['self.hatTexs' + str(x)] = DirectButton(parent=self, relief=None, text=text, text_align=TextNode.ALeft, text_scale=0.05, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, textMayChange=1, command=self.showWordInfo, extraArgs=[x, self.word1Desc, 'hatTex'])

            self.l['self.hatTexs' + str(x)]["text"] = text

            self.hatTexList.append(self.l['self.hatTexs' + str(x)])
            self.hatTexIDs.append(x)
        for x in range(len(ToonDNA.GlassesModels)):
            text = str(x) + " - "
            if ToonDNA.GlassesModels[x] == None:
                text += "No Glasses"
            else:
                text += self.makeSplit(ToonDNA.GlassesModels[x])

            self.l['self.glass' + str(x)] = DirectButton(parent=self, relief=None, text=text, text_align=TextNode.ALeft, text_scale=0.05, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, textMayChange=1, command=self.showWordInfo, extraArgs=[x, self.word1Desc, 'glasses'])

            self.l['self.glass' + str(x)]["text"] = text

            self.glassesList.append(self.l['self.glass' + str(x)])
            self.glassesIDs.append(x)
        for x in range(len(ToonDNA.GlassesTextures)):
            text = str(x) + " - "
            if ToonDNA.GlassesTextures[x] == None:
                text += "Normal Texture"
            else:
                text += self.makeSplit(ToonDNA.GlassesTextures[x].replace(".jpg", ""))

            self.l['self.glassTexs' + str(x)] = DirectButton(parent=self, relief=None, text=text, text_align=TextNode.ALeft, text_scale=0.05, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, textMayChange=1, command=self.showWordInfo, extraArgs=[x, self.word1Desc, 'glassesTex'])


            self.l['self.glassTexs' + str(x)]["text"] = text

            self.glassesTexList.append(self.l['self.glassTexs' + str(x)])
            self.glassesTexIDs.append(x)

        self.hatLabel = DirectLabel(parent=self, relief=None,
                                     text="Hat ID: (" + str(self.hat) + ', ' + str(self.hatTex) + ", 0)",
                                     text_align=TextNode.ALeft, text_scale=0.06, text_wordwrap=12, pos=(-0.65, 0, 0.5))
        self.glassesLabel = DirectLabel(parent=self, relief=None,
                                     text="Glasses ID: (" + str(self.glasses) + ', ' + str(self.glassesTex) + ", 0)",
                                     text_align=TextNode.ALeft, text_scale=0.06, text_wordwrap=12, pos=(0.15, 0, 0.5))



    def unload(self):
        for x in range(len(ToonDNA.HatModels)):
            del self.l['self.hats' + str(x)]
        for x in range(len(ToonDNA.HatTextures)):
            del self.l['self.hatTexs' + str(x)]
        for x in range(len(ToonDNA.GlassesModels)):
            del self.l['self.glass' + str(x)]
        for x in range(len(ToonDNA.GlassesTextures)):
            del self.l['self.glassTexs' + str(x)]
        del self.hatLabel
        del self.glassesLabel

        self.hatScrollList.destroy()
        del self.hatScrollList
        self.glassesScrollList.destroy()
        del self.glassesScrollList
        self.hatTexScrollList.destroy()
        del self.hatTexScrollList
        self.glassesTexScrollList.destroy()
        del self.glassesTexScrollList

        self.hatslider.destroy()
        del self.hatslider
        self.glassesslider.destroy()
        del self.glassesslider
        self.hattexslider.destroy()
        del self.hattexslider
        self.glassestexslider.destroy()
        del self.glassestexslider

        self.toggleGender.destroy()
        del self.toggleGender
        self.toggleBody.destroy()
        del self.toggleBody
        self.setClothes.destroy()
        del self.setClothes

        if self.turnSeq.isPlaying():
            self.turnSeq.finish()
        del self.turnSeq
        self.model.removeNode()
        del self.model

    def exit(self):
        self.ignore('confirmDone')
        self.hide()

    def enter(self):
        self.ignore('confirmDone')
        self.show()

    def createModel(self):
        if self.turnSeq.isPlaying():
            self.turnSeq.finish()
        if self.model:
            self.model.removeNode()
            del self.model

        frameGUI = loader.loadModel('phase_3.5/models/gui/fishingBook')
        toonFrame = DirectFrame(parent=self, relief=None, image=frameGUI.find('**/fram3'), pos=(0.7, 0, -0.45),
                                scale=0.0225)

        toon = Toon.Toon()
        dna = ToonDNA.ToonDNA()
        dna.newToon((self.headName, 'ms', 'm', self.gender))
        dna.headColor = 27
        dna.armColor = 27
        dna.legColor = 27
        toon.setDNA(dna)
        toon.setHat(self.hat, self.hatTex, 0)
        toon.setGlasses(self.glasses, self.glassesTex, 0)
        self.model = NodePath('clothing')
        toon.getPart('head', '1000').reparentTo(self.model)
        toon.getGeomNode().hide()
        self.model.setH(180)
        self.model.reparentTo(self)
        self.model.setScale(0.125)
        self.model.setPos(0.4, 0, -0.525)
        self.model.setBin('unsorted', 0, 1)
        self.model.setDepthTest(True)
        self.model.setDepthWrite(True)
        self.turnSeq = LerpHprInterval(self.model, duration=5, hpr=(540, 0, 0), startHpr=(180, 0, 0))
        self.turnSeq.loop()

    def makeButtons(self):
        if self.gender == 'm':
            a = "Male"
        else:
            a = "Female"
        gui = loader.loadModel('phase_3/models/gui/pick_a_toon_gui')
        self.toggleGender = DirectButton(parent=self, image=(gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'),
                                                             gui.find('**/QuitBtn_RLVR')), relief=None,
                                         text='Toggle Gender (%s)' % a, text_scale=0.04, text_pos=(0, -0.0125),
                                         scale=0.8, pos=(-0.45, 0, -0.4), command=self.changeBody, extraArgs=['gender'])
        self.toggleBody = DirectButton(parent=self, image=(gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'),
                                                           gui.find('**/QuitBtn_RLVR')), relief=None,
                                       text='Toggle Head (%s)' % self.headName, text_scale=0.04, text_pos=(0, -0.0125),
                                       scale=0.8, pos=(-0.45, 0, -0.5), command=self.changeBody, extraArgs=['species'])
        self.setClothes = DirectButton(parent=self, image=(gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'),
                                                           gui.find('**/QuitBtn_RLVR')), relief=None,
                                       text='Set Accessories', text_scale=0.05, text_pos=(0, -0.0125), scale=0.8,
                                       pos=(-0.45, 0, -0.6), command=self.setAsClothing)

    def setAsClothing(self):
        av = base.cr.doId2do.get(base.localAvatar.doId)
        av.sendUpdate('setMagicHeadAccessories', [self.hat, self.hatTex, self.glasses, self.glassesTex])

    def changeBody(self, type):
        if type == 'gender':
            if self.gender == 'm':
                self.gender = 'f'
                self.toggleGender['text'] = 'Toggle Gender (Female)'
            else:
                self.gender = 'm'
                self.toggleGender['text'] = 'Toggle Gender (Male)'
        elif type == 'species':
            self.headType = self.headType + 1
            if self.headType > 33:
                self.headType = 0
            self.headName = ToonDNA.toonHeadTypes[self.headType]
            self.toggleBody['text'] = 'Toggle Head (%s)' % self.headName
        self.createModel()

    def showWordInfo(self, wordNum, desc, clothType):
        listNum = wordNum
        if clothType == 'hat':
            clothList = self.hatList
        elif clothType == 'hatTex':
            clothList = self.hatTexList
        elif clothType == 'glasses':
            clothList = self.glassesList
        elif clothType == 'glassesTex':
            clothList = self.glassesTexList

        for word in clothList:
            if word['state'] != DGG.NORMAL:
                word['state'] = DGG.NORMAL

        wordName = clothList[listNum]
        wordName['state'] = DGG.DISABLED

        if clothType == 'hat':
            self.hat = wordNum
        elif clothType == 'hatTex':
            self.hatTex = wordNum
        elif clothType == 'glasses':
            self.glasses = wordNum
        elif clothType == 'glassesTex':
            self.glassesTex = wordNum

        self.hatLabel['text'] = "Hat ID: (" + str(self.hat) + ', ' + str(self.hatTex) + ", 0)"
        self.glassesLabel['text'] = "Glasses ID: (" + str(self.glasses) + ', ' + str(self.glassesTex) + ", 0)"
        self.createModel()

    def makeScrollLists(self):
        gui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
        coolbutton = loader.loadModel('phase_3/models/gui/pick_a_toon_gui')
        self.hatScrollList = DirectScrolledList(parent=self, relief=None, forceHeight=0.07, pos=(-0.5, 0, 0),
                                                  itemFrame_pos=(-0.237, 0, 0.41), itemFrame_scale=1.0,
                                                  itemFrame_relief=DGG.SUNKEN, itemFrame_frameSize=(-0.05,
                                                                                                    0.66,
                                                                                                    -0.4,
                                                                                                    0.07),
                                                  itemFrame_frameColor=(0.85, 0.95, 1, 1),
                                                  itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=6,
                                                  items=list(self.hatList))
        make_dsl_scrollable(self.hatScrollList)
        self.hatScrollList.incButton.reparentTo(hidden)
        self.hatScrollList.decButton.reparentTo(hidden)
        self.hatslider = DirectSlider(parent=self, range=(len(self.hatIDs), 0),
                                   scale=(0.7, 0.7, 0.225), pos=(-0.1, 0, 0.245),
                                   pageSize=1, orientation=DGG.VERTICAL, command=self.scrollListTo, extraArgs=[self.hatScrollList, 'hat'],
                                   thumb_geom=(coolbutton.find('**/QuitBtn_UP'),
                                               coolbutton.find('**/QuitBtn_DN'),
                                               coolbutton.find('**/QuitBtn_RLVR'),
                                               coolbutton.find('**/QuitBtn_UP')),
                                   thumb_relief=None, thumb_geom_hpr=(0, 0, -90), thumb_geom_scale=(-0.5, 1, 0.5))
        self.hatTexScrollList = DirectScrolledList(parent=self, relief=None, forceHeight=0.07, pos=(-0.5, 0, 0),
                                                  itemFrame_pos=(-0.237, 0, -0.08), itemFrame_scale=1.0,
                                                  itemFrame_relief=DGG.SUNKEN, itemFrame_frameSize=(-0.05,
                                                                                                    0.66,
                                                                                                    -0.25,
                                                                                                    0.07),
                                                  itemFrame_frameColor=(0.85, 0.95, 1, 1),
                                                  itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=4,
                                                  items=list(self.hatTexList))
        make_dsl_scrollable(self.hatTexScrollList)
        self.hatTexScrollList.incButton.reparentTo(hidden)
        self.hatTexScrollList.decButton.reparentTo(hidden)
        self.hattexslider = DirectSlider(parent=self, range=(len(self.hatTexIDs), 0),
                                        scale=(0.7, 0.7, 0.15), pos=(-0.1, 0, -0.1685),
                                        pageSize=1, orientation=DGG.VERTICAL, command=self.scrollListTo,  extraArgs=[self.hatTexScrollList, 'hatTex'],
                                        thumb_geom=(coolbutton.find('**/QuitBtn_UP'),
                                                    coolbutton.find('**/QuitBtn_DN'),
                                                    coolbutton.find('**/QuitBtn_RLVR'),
                                                    coolbutton.find('**/QuitBtn_UP')),
                                        thumb_relief=None, thumb_geom_hpr=(0, 0, -90), thumb_geom_scale=(0.5, 1, 0.5))
        self.glassesScrollList = DirectScrolledList(parent=self, relief=None, forceHeight=0.07, pos=(0.35, 0, 0),
                                                 itemFrame_pos=(-0.237, 0, 0.41), itemFrame_scale=1.0,
                                                 itemFrame_relief=DGG.SUNKEN, itemFrame_frameSize=(-0.05,
                                                                                                   0.66,
                                                                                                   -0.4,
                                                                                                   0.07),
                                                 itemFrame_frameColor=(0.85, 0.95, 1, 1),
                                                 itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=6,
                                                 items=list(self.glassesList))
        make_dsl_scrollable(self.glassesScrollList)
        self.glassesScrollList.incButton.reparentTo(hidden)
        self.glassesScrollList.decButton.reparentTo(hidden)
        self.glassesslider = DirectSlider(parent=self, range=(len(self.glassesIDs), 0),
                                       scale=(0.7, 0.7, 0.225), pos=(0.75, 0, 0.245),
                                       pageSize=1, orientation=DGG.VERTICAL, command=self.scrollListTo,
                                       extraArgs=[self.glassesScrollList, 'glasses'],
                                       thumb_geom=(coolbutton.find('**/QuitBtn_UP'),
                                                   coolbutton.find('**/QuitBtn_DN'),
                                                   coolbutton.find('**/QuitBtn_RLVR'),
                                                   coolbutton.find('**/QuitBtn_UP')),
                                       thumb_relief=None, thumb_geom_hpr=(0, 0, -90), thumb_geom_scale=(0.5, 1, 0.5))
        self.glassesTexScrollList = DirectScrolledList(parent=self, relief=None, forceHeight=0.07, pos=(0.35, 0, 0),
                                                  itemFrame_pos=(-0.237, 0, -0.08), itemFrame_scale=1.0,
                                                  itemFrame_relief=DGG.SUNKEN, itemFrame_frameSize=(-0.05,
                                                                                                    0.66,
                                                                                                    -0.25,
                                                                                                    0.07),
                                                  itemFrame_frameColor=(0.85, 0.95, 1, 1),
                                                  itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=4,
                                                  items=list(self.glassesTexList))
        make_dsl_scrollable(self.glassesTexScrollList)
        self.glassesTexScrollList.incButton.reparentTo(hidden)
        self.glassesTexScrollList.decButton.reparentTo(hidden)
        self.glassestexslider = DirectSlider(parent=self, range=(len(self.glassesTexIDs), 0),
                                        scale=(0.7, 0.7, 0.15), pos=(0.75, 0, -0.1685),
                                        pageSize=1, orientation=DGG.VERTICAL, command=self.scrollListTo,
                                        extraArgs=[self.glassesTexScrollList, 'glassesTex'],
                                        thumb_geom=(coolbutton.find('**/QuitBtn_UP'),
                                                    coolbutton.find('**/QuitBtn_DN'),
                                                    coolbutton.find('**/QuitBtn_RLVR'),
                                                    coolbutton.find('**/QuitBtn_UP')),
                                        thumb_relief=None, thumb_geom_hpr=(0, 0, -90), thumb_geom_scale=(0.5, 1, 0.5))
        gui.removeNode()
        coolbutton.removeNode()


class AccTabPage2(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('AccTabPage2')

    # TODO Clean Up if possible

    def __init__(self, parent = aspect2d):
        self.textRolloverColor = Vec4(1, 1, 0, 1)
        self.textDownColor = Vec4(0.5, 0.9, 1, 1)
        self.textDisabledColor = Vec4(0.4, 0.8, 0.4, 1)
        self._parent = parent
        self.currentSizeIndex = None
        DirectFrame.__init__(self, parent=self._parent, relief=None, pos=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0))
        self.load()

    def load(self):
        self.model = None
        self.turnSeq = Sequence()
        self.word1Desc = DirectLabel(parent=hidden, relief=None, text='', text_align=TextNode.ALeft, text_scale=0.06, text_wordwrap=12, pos=(0.058, 0, 0))
        self.backpackList = []
        self.backpackIDs = []
        self.backpackTexList = []
        self.backpackTexIDs = []
        self.shoesList = []
        self.shoesIDs = []
        self.shoesTexList = []
        self.shoesTexIDs = []
        self.backpack = 0
        self.backpackTex = 0
        self.shoes = 0
        self.shoesTex = 0
        self.headType = 0
        av = base.cr.doId2do.get(base.localAvatar.doId)
        self.torsoType = av.style.torso[0]
        self.nudity = False
        if len(av.style.torso) == 1:
            self.nudity = True
            self.gender = 'f'
        else:
            if av.style.torso[1] == 'd':
                self.gender = 'f'
            else:
                self.gender = 'm'
        self.l = locals()
        self.makeList()
        self.backpackWords = list(self.backpackList)
        self.backpackTexWords = list(self.backpackTexList)
        self.shoesWords = list(self.shoesList)
        self.shoesTexWords = list(self.shoesTexList)

        self.makeScrollLists()
        self.createModel()
        self.makeButtons()


    def scrollListTo(self, scrollList, slider):
        if slider == 'backpack':
            slider = self.backpackslider
        elif slider == 'backpackTex':
            slider = self.backpacktexslider
        elif slider == 'shoes':
            slider = self.shoesslider
        elif slider == 'shoesTex':
            slider = self.shoestexslider
        scrollList.scrollTo(int(slider['value']))

    def makeSplit(self, string):
        abble = string.split('/', 1)[-1].split('/', 1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_',1)[-1].split('_', 1)[-1].split('_', 1)[-1].split('_', 1)[-1]
        return abble

    def makeList(self):
        for x in range(len(ToonDNA.BackpackModels)):
            text = str(x) + " - "
            if ToonDNA.BackpackModels[x] == None:
                text += "No Backpack"
            else:
                text += self.makeSplit(ToonDNA.BackpackModels[x])

            self.l['self.backpacks' + str(x)] = DirectButton(parent=self, relief=None, text=text, text_align=TextNode.ALeft, text_scale=0.05, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, textMayChange=1, command=self.showWordInfo, extraArgs=[x, self.word1Desc, 'backpack'])

            self.l['self.backpacks' + str(x)]["text"] = text

            self.backpackList.append(self.l['self.backpacks' + str(x)])
            self.backpackIDs.append(x)
        for x in range(len(ToonDNA.BackpackTextures)):
            text = str(x) + " - "
            if ToonDNA.BackpackTextures[x] == None:
                text += "Normal Texture"
            else:
                text += self.makeSplit(ToonDNA.BackpackTextures[x].replace(".jpg", ""))

            self.l['self.backpackTexs' + str(x)] = DirectButton(parent=self, relief=None, text=text, text_align=TextNode.ALeft, text_scale=0.05, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, textMayChange=1, command=self.showWordInfo, extraArgs=[x, self.word1Desc, 'backpackTex'])

            self.l['self.backpackTexs' + str(x)]["text"] = text

            self.backpackTexList.append(self.l['self.backpackTexs' + str(x)])
            self.backpackTexIDs.append(x)
        for x in range(len(ToonDNA.ShoesModels)):
            text = str(x) + " - "
            if ToonDNA.ShoesModels[x] == None:
                text += "FuckerA"
            else:
                text += ToonDNA.ShoesModels[x]

            self.l['self.shoe' + str(x)] = DirectButton(parent=self, relief=None, text=text, text_align=TextNode.ALeft, text_scale=0.05, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, textMayChange=1, command=self.showWordInfo, extraArgs=[x, self.word1Desc, 'shoes'])

            self.l['self.shoe' + str(x)]["text"] = text

            self.shoesList.append(self.l['self.shoe' + str(x)])
            self.shoesIDs.append(x)
        for x in range(len(ToonDNA.ShoesTextures)):
            text = str(x) + " - "
            if ToonDNA.ShoesTextures[x] == None:
                text += "FuckerB"
            else:
                text += self.makeSplit(ToonDNA.ShoesTextures[x].replace(".jpg", ""))

            self.l['self.shoeTexs' + str(x)] = DirectButton(parent=self, relief=None, text=text, text_align=TextNode.ALeft, text_scale=0.05, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, textMayChange=1, command=self.showWordInfo, extraArgs=[x, self.word1Desc, 'shoesTex'])


            self.l['self.shoeTexs' + str(x)]["text"] = text

            self.shoesTexList.append(self.l['self.shoeTexs' + str(x)])
            self.shoesTexIDs.append(x)

        self.backpackLabel = DirectLabel(parent=self, relief=None,
                                     text="Backpack ID: (" + str(self.backpack) + ', ' + str(self.backpackTex) + ", 0)",
                                     text_align=TextNode.ALeft, text_scale=0.06, text_wordwrap=12, pos=(-0.75, 0, 0.5))
        self.shoesLabel = DirectLabel(parent=self, relief=None,
                                     text="Shoes ID: (" + str(self.shoes) + ', ' + str(self.shoesTex) + ", 0)",
                                     text_align=TextNode.ALeft, text_scale=0.06, text_wordwrap=12, pos=(0.15, 0, 0.5))



    def unload(self):
        for x in range(len(ToonDNA.BackpackModels)):
            del self.l['self.backpacks' + str(x)]
        for x in range(len(ToonDNA.BackpackTextures)):
            del self.l['self.backpackTexs' + str(x)]
        for x in range(len(ToonDNA.ShoesModels)):
            del self.l['self.shoe' + str(x)]
        for x in range(len(ToonDNA.ShoesTextures)):
            del self.l['self.shoeTexs' + str(x)]
        del self.backpackLabel
        del self.shoesLabel

        self.backpackScrollList.destroy()
        del self.backpackScrollList
        self.shoesScrollList.destroy()
        del self.shoesScrollList
        self.backpackTexScrollList.destroy()
        del self.backpackTexScrollList
        self.shoesTexScrollList.destroy()
        del self.shoesTexScrollList

        self.backpackslider.destroy()
        del self.backpackslider
        self.shoesslider.destroy()
        del self.shoesslider
        self.backpacktexslider.destroy()
        del self.backpacktexslider
        self.shoestexslider.destroy()
        del self.shoestexslider

        self.toggleGender.destroy()
        del self.toggleGender
        self.toggleBody.destroy()
        del self.toggleBody
        self.setClothes.destroy()
        del self.setClothes

        if self.turnSeq.isPlaying():
            self.turnSeq.finish()
        del self.turnSeq
        self.model.removeNode()
        del self.model

    def exit(self):
        self.ignore('confirmDone')
        self.hide()

    def enter(self):
        self.ignore('confirmDone')
        self.show()

    def createModel(self):
        if self.turnSeq.isPlaying():
            self.turnSeq.finish()
        if self.model:
            self.model.removeNode()
            del self.model
        toon = Toon.Toon()
        dna = ToonDNA.ToonDNA()
        if self.headType > 33:
            self.headType = 0
        bodyEnd = 's'
        if self.nudity:
            bodyEnd = ''
        elif self.gender == 'f':
            bodyEnd = 'd'
        dna.newToon(('cls', self.torsoType + bodyEnd, self.torsoType, self.gender))
        dna.sleeveTexColor = 27
        dna.topTexColor = 27
        dna.botTexColor = 27
        dna.headColor = 27
        dna.armColor = 27
        dna.legColor = 27
        toon.setDNA(dna)
        toon.setBackpack(self.backpack, self.backpackTex, 0)
        toon.setShoes(self.shoes, self.shoesTex, 0)
        self.model = NodePath('clothing')
        toon.getPart('head', '1000').removeNode()
        toon.find('**/1000/**/neck').removeNode()
        toon.reparentTo(self.model)
        toon.loop('neutral')
        self.model.setH(180)
        self.model.reparentTo(self)
        self.model.setScale(0.1)
        self.model.setPos(0, 0, -0.525)
        self.model.setBin('unsorted', 0, 1)
        self.model.setDepthTest(True)
        self.model.setDepthWrite(True)
        self.turnSeq = LerpHprInterval(self.model, duration=5, hpr=(540, 0, 0), startHpr=(180, 0, 0))
        self.turnSeq.loop()

    def makeButtons(self):
        if self.torsoType == 'l':
            b = "Long"
        elif self.torsoType == 'm':
            b = "Med"
        else:
            b = "Short"
        if self.nudity:
            a = "None"
        elif self.gender == 'f':
            a = "Skirt"
        else:
            a = "Shorts"
        gui = loader.loadModel('phase_3/models/gui/pick_a_toon_gui')
        self.toggleGender = DirectButton(parent=self,
            image=(gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'), gui.find('**/QuitBtn_RLVR')), relief=None,
            text='Toggle Clothes (%s)' % a, text_scale=0.04, text_pos=(0, -0.0125), scale=0.8, pos=(-0.4, 0, -0.5), command=self.changeBody, extraArgs=['gender'])
        self.toggleBody = DirectButton(parent=self,
            image=(gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'), gui.find('**/QuitBtn_RLVR')), relief=None,
            text='Toggle Body (%s)' % b, text_scale=0.04, text_pos=(0, -0.0125), scale=0.8, pos=(0.4, 0, -0.5), command=self.changeBody, extraArgs=['body'])
        self.setClothes = DirectButton(parent=self,
                                      image=(gui.find('**/QuitBtn_UP'), gui.find('**/QuitBtn_DN'),
                                             gui.find('**/QuitBtn_RLVR')), relief=None,
                                      text='Set Accessories', text_scale=0.05, text_pos=(0, -0.0125), scale=0.8,
                                      pos=(0, 0, -0.65), command=self.setAsClothing)

    def setAsClothing(self):
        av = base.cr.doId2do.get(base.localAvatar.doId)
        av.sendUpdate('setMagicBodyAccessories', [self.backpack, self.backpackTex, self.shoes, self.shoesTex])

    def changeBody(self, type):
        if type == 'gender':
            if self.nudity:
                self.nudity = False
                self.gender = 'm'
                self.toggleGender['text'] = 'Toggle Clothes (Shorts)'
            elif self.gender == 'f':
                self.nudity = True
                self.toggleGender['text'] = 'Toggle Clothes (None)'
            else:
                self.gender = 'f'
                self.toggleGender['text'] = 'Toggle Clothes (Skirt)'
        elif type == 'body':
            if self.torsoType == 'm':
                self.torsoType = 'l'
                self.toggleBody['text'] = 'Toggle Body (Long)'
            elif self.torsoType == 'l':
                self.torsoType = 's'
                self.toggleBody['text'] = 'Toggle Body (Short)'
            else:
                self.torsoType = 'm'
                self.toggleBody['text'] = 'Toggle Body (Med)'
        self.createModel()

    def showWordInfo(self, wordNum, desc, clothType):
        if clothType == 'backpack':
            clothList = self.backpackList
        elif clothType == 'backpackTex':
            clothList = self.backpackTexList
        elif clothType == 'shoes':
            clothList = self.shoesList
        elif clothType == 'shoesTex':
            clothList = self.shoesTexList

        for word in clothList:
            if word['state'] != DGG.NORMAL:
                word['state'] = DGG.NORMAL

        wordName = clothList[wordNum]
        wordName['state'] = DGG.DISABLED

        if clothType == 'backpack':
            self.backpack = wordNum
        elif clothType == 'backpackTex':
            self.backpackTex = wordNum
        elif clothType == 'shoes':
            self.shoes = wordNum
        elif clothType == 'shoesTex':
            self.shoesTex = wordNum

        self.backpackLabel['text'] = "Backpack ID: (" + str(self.backpack) + ', ' + str(self.backpackTex) + ", 0)"
        self.shoesLabel['text'] = "shoes ID: (" + str(self.shoes) + ', ' + str(self.shoesTex) + ", 0)"
        self.createModel()

    def makeScrollLists(self):
        gui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
        coolbutton = loader.loadModel('phase_3/models/gui/pick_a_toon_gui')
        self.backpackScrollList = DirectScrolledList(parent=self, relief=None, forceHeight=0.07, pos=(-0.5, 0, 0),
                                                  itemFrame_pos=(-0.237, 0, 0.41), itemFrame_scale=1.0,
                                                  itemFrame_relief=DGG.SUNKEN, itemFrame_frameSize=(-0.05,
                                                                                                    0.66,
                                                                                                    -0.4,
                                                                                                    0.07),
                                                  itemFrame_frameColor=(0.85, 0.95, 1, 1),
                                                  itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=6,
                                                  items=list(self.backpackList))
        make_dsl_scrollable(self.backpackScrollList)
        self.backpackScrollList.incButton.reparentTo(hidden)
        self.backpackScrollList.decButton.reparentTo(hidden)
        self.backpackslider = DirectSlider(parent=self, range=(len(self.backpackIDs), 0),
                                   scale=(0.7, 0.7, 0.225), pos=(-0.1, 0, 0.245),
                                   pageSize=1, orientation=DGG.VERTICAL, command=self.scrollListTo, extraArgs=[self.backpackScrollList, 'backpack'],
                                   thumb_geom=(coolbutton.find('**/QuitBtn_UP'),
                                               coolbutton.find('**/QuitBtn_DN'),
                                               coolbutton.find('**/QuitBtn_RLVR'),
                                               coolbutton.find('**/QuitBtn_UP')),
                                   thumb_relief=None, thumb_geom_hpr=(0, 0, -90), thumb_geom_scale=(-0.5, 1, 0.5))
        self.backpackTexScrollList = DirectScrolledList(parent=self, relief=None, forceHeight=0.07, pos=(-0.5, 0, 0),
                                                  itemFrame_pos=(-0.237, 0, -0.08), itemFrame_scale=1.0,
                                                  itemFrame_relief=DGG.SUNKEN, itemFrame_frameSize=(-0.05,
                                                                                                    0.66,
                                                                                                    -0.25,
                                                                                                    0.07),
                                                  itemFrame_frameColor=(0.85, 0.95, 1, 1),
                                                  itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=4,
                                                  items=list(self.backpackTexList))
        make_dsl_scrollable(self.backpackTexScrollList)
        self.backpackTexScrollList.incButton.reparentTo(hidden)
        self.backpackTexScrollList.decButton.reparentTo(hidden)
        self.backpacktexslider = DirectSlider(parent=self, range=(len(self.backpackTexIDs), 0),
                                        scale=(0.7, 0.7, 0.15), pos=(-0.1, 0, -0.1685),
                                        pageSize=1, orientation=DGG.VERTICAL, command=self.scrollListTo,  extraArgs=[self.backpackTexScrollList, 'backpackTex'],
                                        thumb_geom=(coolbutton.find('**/QuitBtn_UP'),
                                                    coolbutton.find('**/QuitBtn_DN'),
                                                    coolbutton.find('**/QuitBtn_RLVR'),
                                                    coolbutton.find('**/QuitBtn_UP')),
                                        thumb_relief=None, thumb_geom_hpr=(0, 0, -90), thumb_geom_scale=(0.5, 1, 0.5))
        self.shoesScrollList = DirectScrolledList(parent=self, relief=None, forceHeight=0.07, pos=(0.35, 0, 0),
                                                 itemFrame_pos=(-0.237, 0, 0.41), itemFrame_scale=1.0,
                                                 itemFrame_relief=DGG.SUNKEN, itemFrame_frameSize=(-0.05,
                                                                                                   0.66,
                                                                                                   -0.4,
                                                                                                   0.07),
                                                 itemFrame_frameColor=(0.85, 0.95, 1, 1),
                                                 itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=6,
                                                 items=list(self.shoesList))
        make_dsl_scrollable(self.shoesScrollList)
        self.shoesScrollList.incButton.reparentTo(hidden)
        self.shoesScrollList.decButton.reparentTo(hidden)
        self.shoesslider = DirectSlider(parent=self, range=(len(self.shoesIDs), 0),
                                       scale=(0.7, 0.7, 0.225), pos=(0.75, 0, 0.245),
                                       pageSize=1, orientation=DGG.VERTICAL, command=self.scrollListTo,
                                       extraArgs=[self.shoesScrollList, 'shoes'],
                                       thumb_geom=(coolbutton.find('**/QuitBtn_UP'),
                                                   coolbutton.find('**/QuitBtn_DN'),
                                                   coolbutton.find('**/QuitBtn_RLVR'),
                                                   coolbutton.find('**/QuitBtn_UP')),
                                       thumb_relief=None, thumb_geom_hpr=(0, 0, -90), thumb_geom_scale=(0.5, 1, 0.5))
        self.shoesTexScrollList = DirectScrolledList(parent=self, relief=None, forceHeight=0.07, pos=(0.35, 0, 0),
                                                  itemFrame_pos=(-0.237, 0, -0.08), itemFrame_scale=1.0,
                                                  itemFrame_relief=DGG.SUNKEN, itemFrame_frameSize=(-0.05,
                                                                                                    0.66,
                                                                                                    -0.25,
                                                                                                    0.07),
                                                  itemFrame_frameColor=(0.85, 0.95, 1, 1),
                                                  itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=4,
                                                  items=list(self.shoesTexList))
        make_dsl_scrollable(self.shoesTexScrollList)
        self.shoesTexScrollList.incButton.reparentTo(hidden)
        self.shoesTexScrollList.decButton.reparentTo(hidden)
        self.shoestexslider = DirectSlider(parent=self, range=(len(self.shoesTexIDs), 0),
                                        scale=(0.7, 0.7, 0.15), pos=(0.75, 0, -0.1685),
                                        pageSize=1, orientation=DGG.VERTICAL, command=self.scrollListTo,
                                        extraArgs=[self.shoesTexScrollList, 'shoesTex'],
                                        thumb_geom=(coolbutton.find('**/QuitBtn_UP'),
                                                    coolbutton.find('**/QuitBtn_DN'),
                                                    coolbutton.find('**/QuitBtn_RLVR'),
                                                    coolbutton.find('**/QuitBtn_UP')),
                                        thumb_relief=None, thumb_geom_hpr=(0, 0, -90), thumb_geom_scale=(0.5, 1, 0.5))
        gui.removeNode()
        coolbutton.removeNode()
