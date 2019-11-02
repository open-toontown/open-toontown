from pandac.PandaModules import *
from direct.showbase.DirectObject import DirectObject
from direct.gui.DirectGui import DirectFrame, DirectButton, DirectLabel
from direct.gui.DirectGui import DirectScrolledListItem, DirectScrolledList
from direct.gui import DirectGuiGlobals
from toontown.toonbase import TTLocalizer
from toontown.parties import PartyUtils

class JukeboxGui(DirectObject):
    notify = directNotify.newCategory('JukeboxGui')
    CLOSE_EVENT = 'JukeboxGui_CLOSE_EVENT'
    SONG_SELECT_EVENT = 'JukeboxGui_SONG_SELECT_EVENT'
    QUEUE_SELECT_EVENT = 'JukeboxGui_QUEUE_SELECT_EVENT'
    ADD_SONG_CLICK_EVENT = 'JukeboxGui_ADD_SONG_CLICK_EVENT'
    MOVE_TO_TOP_CLICK_EVENT = 'JukeboxGUI_MOVE_TO_TOP_EVENT'

    def __init__(self, phaseToMusicData):
        self._loaded = False
        self._timerGui = None
        self._windowFrame = None
        self.phaseToMusicData = phaseToMusicData
        return

    def load(self):
        if self.isLoaded():
            return
        guiNode = loader.loadModel('phase_13/models/parties/jukeboxGUI')
        self._timerGui = PartyUtils.getNewToontownTimer()
        self._windowFrame = DirectFrame(image=guiNode.find('**/background'), relief=None, pos=(0, 0, 0), scale=0.7)
        self._songFrame = DirectFrame(image=guiNode.find('**/songTitle_background'), parent=self._windowFrame, relief=None)
        self._currentlyPlayingLabel = self.__createLabel(guiNode, 'currentlyPlaying', parent=self._windowFrame, text=TTLocalizer.JukeboxCurrentlyPlayingNothing, scale=TTLocalizer.JGcurrentlyPlayingLabel)
        self._songNameLabel = self.__createLabel(guiNode, 'songName', parent=self._windowFrame, text=TTLocalizer.JukeboxCurrentSongNothing, scale=TTLocalizer.JGsongNameLabel)
        self._queueList, self._queueLabel = self.__createLabeledScrolledList(guiNode, 'queue', label=TTLocalizer.JukeboxQueueLabel, parent=self._windowFrame)
        self._songsList, self._songsLabel = self.__createLabeledScrolledList(guiNode, 'songs', label=TTLocalizer.JukeboxSongsLabel, parent=self._windowFrame)
        pos = guiNode.find('**/addButton_text_locator').getPos()
        self._addSongButton = self.__createButton(guiNode, 'addSongButton', parent=self._windowFrame, command=self.__handleAddSongButtonClick, image3_color=Vec4(0.6, 0.6, 0.6, 0.6), text=TTLocalizer.JukeboxAddSong, text_align=TextNode.ACenter, text_pos=(pos[0], pos[2]), text_scale=TTLocalizer.JGaddSongButton)
        self._closeButton = self.__createButton(guiNode, 'can_cancelButton', parent=self._windowFrame, command=self.__handleCloseButtonClick)
        pos = guiNode.find('**/close_text_locator').getPos()
        self._closeButton = self.__createButton(guiNode, 'close', parent=self._windowFrame, command=self.__handleCloseButtonClick, text=TTLocalizer.JukeboxClose, text_align=TextNode.ACenter, text_pos=(pos[0], pos[2]), text_scale=0.08)
        self._moveToTopButton = self.__createButton(guiNode, 'moveToTop', command=self.__handleMoveToTopButtonClick)
        guiNode.removeNode()
        self._loaded = True
        return

    def __createButton(self, guiNode, imagePrefix, parent = hidden, **kwargs):
        return DirectButton(parent=parent, relief=None, image=(guiNode.find('**/%s_up' % imagePrefix), guiNode.find('**/%s_down' % imagePrefix), guiNode.find('**/%s_rollover' % imagePrefix)), **kwargs)

    def __createLabel(self, guiNode, locatorPrefix, parent = hidden, **kwargs):
        return DirectLabel(parent=parent, relief=None, pos=guiNode.find('**/%s_text_locator' % locatorPrefix).getPos(), **kwargs)

    def __createLabeledScrolledList(self, guiNode, namePrefix, label, parent = hidden, **kwargs):
        return (DirectScrolledList(parent=parent, relief=None, incButton_image=(guiNode.find('**/%sButtonDown_up' % namePrefix), guiNode.find('**/%sButtonDown_down' % namePrefix), guiNode.find('**/%sButtonDown_rollover' % namePrefix)), incButton_relief=None, incButton_image3_color=Vec4(0.6, 0.6, 0.6, 0.6), decButton_image=(guiNode.find('**/%sButtonUp_up' % namePrefix), guiNode.find('**/%sButtonUp_down' % namePrefix), guiNode.find('**/%sButtonUp_rollover' % namePrefix)), decButton_relief=None, decButton_image3_color=Vec4(0.6, 0.6, 0.6, 0.6), image=guiNode.find('**/%s_background' % namePrefix), itemFrame_relief=None, itemFrame_pos=guiNode.find('**/%sList_locator' % namePrefix).getPos(), itemFrame_scale=0.07, numItemsVisible=TTLocalizer.JGnumItemsVisible, items=[], **kwargs), self.__createLabel(guiNode, namePrefix, parent=parent, text=label, text_fg=(0.5, 1.0, 1.0, 1.0), text_shadow=(0.0, 0.0, 0.0, 1.0), scale=0.12))

    def enable(self, timer = 0):
        if not self.isLoaded():
            self.load()
            phase = 13
            tunes = self.phaseToMusicData[13]
            for filename, info in tunes.items():
                self.addToSongList(info[0], phase, filename, info[1])

            for phase, tunes in self.phaseToMusicData.items():
                if phase == 13:
                    continue
                for filename, info in tunes.items():
                    self.addToSongList(info[0], phase, filename, info[1])

        self._windowFrame.show()
        if timer > 0:
            self._timerGui.setTime(timer)
            self._timerGui.countdown(timer)
            self._timerGui.show()

    def disable(self):
        self._windowFrame.hide()
        self._timerGui.hide()

    def unload(self):
        self.ignoreAll()
        if not self.isLoaded():
            return
        if self._windowFrame is not None:
            self._windowFrame.destroy()
            self._windowFrame = None
            self._moveToTopButton.destroy()
            del self._moveToTopButton
        if self._timerGui is not None:
            self._timerGui.destroy()
            self._timerGui = None
        self._loaded = False
        return

    def isLoaded(self):
        return self._loaded

    def addToSongList(self, text, phase, filename, length):
        listItem = DirectScrolledListItem(relief=None, parent=self._songsList, text=text, text_align=TextNode.ALeft, text_pos=(0.0, 0.0, 0.0), text_scale=TTLocalizer.JGlistItem, text_fg=(0.0, 0.0, 0.0, 1.0), text1_fg=(1.0, 1.0, 1.0, 1.0), text1_bg=(0.0, 0.0, 1.0, 1.0), text2_fg=(0.0, 0.0, 1.0, 1.0), text3_bg=(0.0, 0.8, 0.0, 1.0), command=self.__handleSongListItemSelect, extraArgs=[])
        listItem.setPythonTag('value', (phase, filename, length))
        self._songsList.addItem(listItem)
        return listItem

    def __handleCloseButtonClick(self):
        self.disable()
        messenger.send(JukeboxGui.CLOSE_EVENT)

    def __handleMoveToTopButtonClick(self):
        messenger.send(JukeboxGui.MOVE_TO_TOP_CLICK_EVENT)

    def __handleSongListItemSelect(self):
        pass

    def __handleAddSongButtonClick(self):
        if hasattr(self._songsList, 'currentSelected'):
            song = self._songsList.currentSelected
            messenger.send(JukeboxGui.ADD_SONG_CLICK_EVENT, [song['text'], song.getPythonTag('value')])

    def disableAddSongButton(self):
        self._addSongButton['state'] = DirectGuiGlobals.DISABLED

    def enableAddSongButton(self):
        self._addSongButton['state'] = DirectGuiGlobals.NORMAL

    def addSongToQueue(self, text, highlight = False, moveToTopButton = False):
        listItem = DirectLabel(relief=None, parent=self._queueList, text=text, text_align=TextNode.ALeft, text_pos=(0.0, 0.0, 0.0), text_scale=TTLocalizer.JGlistItem)
        self._queueList.addItem(listItem)
        if highlight:
            listItem['text_fg'] = (0.0, 0.5, 0.0, 1.0)
            self._addSongButton['text'] = TTLocalizer.JukeboxReplaceSong
            listItem.setPythonTag('highlighted', True)
        if moveToTopButton and len(self._queueList['items']) > 1:
            self._moveToTopButton.reparentTo(listItem)
            self._moveToTopButton.setScale(self._windowFrame, 1.0)
            self._moveToTopButton.setPos(10.0, 0.0, 0.25)
            self._queueList.scrollTo(len(self._queueList['items']) - 1)
        return listItem

    def popSongFromQueue(self):
        if len(self._queueList['items']) > 0:
            item = self._queueList['items'][0]
            self._queueList.removeItem(item)
            if self._moveToTopButton.getParent() == item:
                self._moveToTopButton.reparentTo(hidden)
            if self._moveToTopButton.getParent() == item:
                self._moveToTopButton.reparentTo(hidden)
            if item.getPythonTag('highlighted') == True:
                self._addSongButton['text'] = TTLocalizer.JukeboxAddSong
            item.removeNode()
            return item
        return None

    def setSongCurrentlyPlaying(self, phase, filename):
        songs = self.phaseToMusicData.get(phase / 1)
        if songs:
            songName = songs.get(filename)
            if songName:
                self._songNameLabel['text'] = songName
                self._currentlyPlayingLabel['text'] = TTLocalizer.JukeboxCurrentlyPlaying

    def clearSongCurrentlyPlaying(self):
        self._currentlyPlayingLabel['text'] = TTLocalizer.JukeboxCurrentlyPlayingNothing
        self._songNameLabel['text'] = TTLocalizer.JukeboxCurrentSongNothing

    def pushQueuedItemToTop(self, item):
        self._queueList['items'].remove(item)
        self._queueList['items'].insert(0, item)
        if self._moveToTopButton.getParent() == item:
            self._moveToTopButton.reparentTo(hidden)
        self._queueList.refresh()
