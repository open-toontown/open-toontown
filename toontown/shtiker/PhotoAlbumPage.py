from pandac.PandaModules import *
from . import ShtikerPage
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from toontown.toonbase import TTLocalizer
import os
from toontown.toonbase import ToontownGlobals

class PhotoAlbumPage(ShtikerPage.ShtikerPage):

    def __init__(self):
        ShtikerPage.ShtikerPage.__init__(self)
        self.textRolloverColor = Vec4(1, 1, 0, 1)
        self.textDownColor = Vec4(0.5, 0.9, 1, 1)
        self.textDisabledColor = Vec4(0.4, 0.8, 0.4, 1)
        self.photos = {}
        self.selectedFileName = None
        self.photoIndex = 0
        return

    def load(self):
        self.title = DirectLabel(parent=self, relief=None, text='Photo Album', text_scale=0.1, pos=(0, 0, 0.6))
        self.pictureImage = loader.loadModel('phase_3.5/models/gui/photo_frame')
        self.pictureImage.setScale(0.2)
        self.pictureImage.setPos(0.44, 0, 0.25)
        self.pictureImage.reparentTo(self)
        self.pictureFg = self.pictureImage.find('**/fg')
        self.pictureFg.setColor(1, 1, 1, 0.1)
        guiButton = loader.loadModel('phase_3/models/gui/quit_button')
        self.pictureCaption = DirectLabel(parent=self, relief=None, text='Caption', text_scale=0.05, text_wordwrap=10, text_align=TextNode.ACenter, pos=(0.45, 0, -0.22))
        self.renameButton = DirectButton(parent=self, relief=None, image=(guiButton.find('**/QuitBtn_UP'), guiButton.find('**/QuitBtn_DN'), guiButton.find('**/QuitBtn_RLVR')), image_scale=(1, 1, 1), pos=(0.45, 0, -0.35), text='Caption', text_scale=0.06, text_pos=(0, -0.02), command=self.renameImage, state=DGG.DISABLED)
        trashcanGui = loader.loadModel('phase_3/models/gui/trashcan_gui')
        self.deleteButton = DirectButton(parent=self, image=(trashcanGui.find('**/TrashCan_CLSD'), trashcanGui.find('**/TrashCan_OPEN'), trashcanGui.find('**/TrashCan_RLVR')), text=('', 'Delete', 'Delete'), text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1), text_scale=0.1, text_pos=(0, -0.1), text_font=ToontownGlobals.getInterfaceFont(), textMayChange=0, relief=None, pos=(0.73, 0, -0.33), scale=0.4, state=DGG.DISABLED, command=self.deleteImage)
        guiButton.removeNode()
        trashcanGui.removeNode()
        gui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
        self.scrollList = DirectScrolledList(parent=self, relief=None, forceHeight=0.07, pos=(-0.5, 0, 0), incButton_image=(gui.find('**/FndsLst_ScrollUp'),
         gui.find('**/FndsLst_ScrollDN'),
         gui.find('**/FndsLst_ScrollUp_Rllvr'),
         gui.find('**/FndsLst_ScrollUp')), incButton_relief=None, incButton_scale=(1.3, 1.3, -1.3), incButton_pos=(0, 0, -0.51), incButton_image3_color=Vec4(1, 1, 1, 0.2), decButton_image=(gui.find('**/FndsLst_ScrollUp'),
         gui.find('**/FndsLst_ScrollDN'),
         gui.find('**/FndsLst_ScrollUp_Rllvr'),
         gui.find('**/FndsLst_ScrollUp')), decButton_relief=None, decButton_scale=(1.3, 1.3, 1.3), decButton_pos=(0, 0, 0.51), decButton_image3_color=Vec4(1, 1, 1, 0.2), itemFrame_pos=(-0.237, 0, 0.41), itemFrame_scale=1.0, itemFrame_relief=DGG.SUNKEN, itemFrame_frameSize=(-0.05,
         0.66,
         -0.88,
         0.06), itemFrame_frameColor=(0.85, 0.95, 1, 1), itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=13, items=[])
        self.renamePanel = DirectFrame(parent=self, relief=None, pos=(0.45, 0, -0.45), image=DGG.getDefaultDialogGeom(), image_color=ToontownGlobals.GlobalDialogColor, image_scale=(1.0, 1.0, 0.6), text='Caption Photo', text_scale=0.06, text_pos=(0.0, 0.13), sortOrder=NO_FADE_SORT_INDEX)
        self.renameEntry = DirectEntry(parent=self.renamePanel, relief=DGG.SUNKEN, scale=0.06, pos=(-0.3, 0, 0), borderWidth=(0.1, 0.1), numLines=1, cursorKeys=0, frameColor=(0.8, 0.8, 0.5, 1), frameSize=(-0.2,
         10,
         -0.4,
         1.1), command=self.renameDialog)
        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        self.bCancel = DirectButton(parent=self.renamePanel, image=(buttons.find('**/CloseBtn_UP'), buttons.find('**/CloseBtn_DN'), buttons.find('**/CloseBtn_Rllvr')), relief=None, text='Cancel', text_scale=0.05, text_pos=(0.0, -0.1), pos=(0.0, 0.0, -0.1), command=self.renameCancel)
        self.renamePanel.hide()
        self.deletePanel = DirectFrame(parent=self, relief=None, pos=(0, 0, 0), image=DGG.getDefaultDialogGeom(), image_color=ToontownGlobals.GlobalDialogColor, image_scale=(1.0, 1.0, 0.6), text='Delete Photo?', text_scale=0.06, text_pos=(0.0, 0.13), sortOrder=NO_FADE_SORT_INDEX)
        self.dOk = DirectButton(parent=self.deletePanel, image=(buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr')), relief=None, text='Ok', text_scale=0.05, text_pos=(0.0, -0.1), pos=(-0.1, 0.0, -0.1), command=self.deleteConfirm)
        self.dCancel = DirectButton(parent=self.deletePanel, image=(buttons.find('**/CloseBtn_UP'), buttons.find('**/CloseBtn_DN'), buttons.find('**/CloseBtn_Rllvr')), relief=None, text='Cancel', text_scale=0.05, text_pos=(0.0, -0.1), pos=(0.1, 0.0, -0.1), command=self.deleteCancel)
        self.deletePanel.hide()
        self.leftArrow = DirectButton(parent=self, relief=None, image=(gui.find('**/Horiz_Arrow_UP'),
         gui.find('**/Horiz_Arrow_DN'),
         gui.find('**/Horiz_Arrow_Rllvr'),
         gui.find('**/Horiz_Arrow_UP')), image3_color=Vec4(1, 1, 1, 0.5), scale=(-1.0, 1.0, 1.0), pos=(0.15, 0, -0.21), command=self.prevPhoto)
        self.rightArrow = DirectButton(parent=self, relief=None, image=(gui.find('**/Horiz_Arrow_UP'),
         gui.find('**/Horiz_Arrow_DN'),
         gui.find('**/Horiz_Arrow_Rllvr'),
         gui.find('**/Horiz_Arrow_UP')), image3_color=Vec4(1, 1, 1, 0.5), pos=(0.75, 0, -0.21), command=self.nextPhoto)
        gui.removeNode()
        buttons.removeNode()
        return

    def unload(self):
        del self.title
        del self.scrollList
        self.pictureImage.removeNode()
        self.pictureFg.removeNode()
        del self.pictureCaption
        del self.deleteButton
        del self.renameButton
        del self.renamePanel
        del self.renameEntry
        del self.bCancel
        del self.deletePanel
        del self.dOk
        del self.dCancel
        del self.leftArrow
        del self.rightArrow
        ShtikerPage.ShtikerPage.unload(self)

    def renameDialog(self, str):
        separator = '_'
        validChars = string.letters + string.digits + ' -'
        str = [s for s in str if s in validChars]
        if not str:
            self.renameCleanup()
            return 0
        oldName = self.selectedFileName
        numUnders = oldName.count(separator)
        if numUnders == 0:
            newName = oldName[0:11] + separator + str + separator + oldName[10:]
        elif numUnders == 2:
            sp = oldName.split(separator)
            newName = sp[0] + separator + str + separator + sp[2]
        else:
            self.renameCleanup()
            return 0
        os.rename(oldName, newName)
        self.renameCleanup()
        self.updateScrollList()
        self.chosePhoto(newName)
        return 1

    def renameCancel(self):
        self.renameCleanup()

    def renameCleanup(self):
        self.renamePanel.hide()
        chatEntry = base.localAvatar.chatMgr.chatInputNormal.chatEntry
        chatEntry['backgroundFocus'] = self.oldFocus

    def renameImage(self):
        self.deleteCleanup()
        self.renameEntry.set(self.getPhotoName(self.selectedFileName))
        self.renamePanel.show()
        chatEntry = base.localAvatar.chatMgr.chatInputNormal.chatEntry
        chatEntry['backgroundFocus'] = 0
        self.renameEntry['focus'] = 1
        print(self.selectedFileName)

    def deleteConfirm(self):
        os.remove(self.selectedFileName)
        self.selectedFileName = None
        self.deleteCleanup()
        self.updateScrollList()
        return

    def deleteCancel(self):
        self.deleteCleanup()

    def deleteCleanup(self):
        self.deletePanel.hide()

    def deleteImage(self):
        self.renameCleanup()
        self.deletePanel['text'] = 'Delete Photo?\n%s' % self.getPhotoName(self.selectedFileName)
        self.deletePanel.show()

    def makePhotoButton(self, fileName):
        return DirectButton(relief=None, text=self.getPhotoName(fileName), text_scale=0.06, text_align=TextNode.ALeft, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, command=self.chosePhoto, extraArgs=[fileName])

    def getPhotoName(self, fileName):
        separator = '_'
        numUnders = fileName.count(separator)
        if numUnders == 0:
            return 'noname'
        elif numUnders == 2:
            return fileName.split(separator)[1]
        else:
            return 'unknown'

    def chosePhoto(self, fileName):
        if fileName:
            self.selectedFileName = fileName
            photoTexture = loader.loadTexture(fileName)
            photoName = self.getPhotoName(fileName)
            self.pictureFg.setTexture(photoTexture, 1)
            self.pictureFg.setColor(1, 1, 1, 1)
            self.pictureCaption['text'] = photoName
            self.renameButton['state'] = DGG.NORMAL
            self.deleteButton['state'] = DGG.NORMAL
            self.renameEntry.set(photoName)
        else:
            self.selectedFileName = None
            self.pictureFg.clearTexture()
            self.pictureFg.setColor(1, 1, 1, 0.1)
            self.pictureCaption['text'] = ''
            self.renameButton['state'] = DGG.DISABLED
            self.deleteButton['state'] = DGG.DISABLED
            self.renameEntry.set('')
        return

    def getPhotos(self):
        files = os.listdir('.')
        photos = []
        for fileName in files:
            if fileName[0:10] == 'screenshot' and fileName[-4:] == '.jpg':
                photos.append(fileName)

        return photos

    def newScreenshot(self, filename):
        self.updateScrollList()

    def updateScrollList(self):
        newPhotos = self.getPhotos()
        for photo in list(self.photos.keys()):
            if photo not in newPhotos:
                photoButton = self.photos[photo]
                self.scrollList.removeItem(photoButton)
                photoButton.destroy()
                del self.photos[photo]

        for photo in newPhotos:
            if photo not in self.photos:
                photoButton = self.makePhotoButton(photo)
                self.scrollList.addItem(photoButton)
                self.photos[photo] = photoButton

        if list(self.photos.keys()):
            self.chosePhoto(list(self.photos.keys())[0])
        else:
            self.chosePhoto(None)
        return

    def enter(self):
        self.accept('screenshot', self.newScreenshot)
        self.updateScrollList()
        chatEntry = base.localAvatar.chatMgr.chatInputNormal.chatEntry
        self.oldFocus = chatEntry['backgroundFocus']
        ShtikerPage.ShtikerPage.enter(self)

    def exit(self):
        self.ignore('screenshot')
        self.renameCleanup()
        self.deleteCleanup()
        ShtikerPage.ShtikerPage.exit(self)

    def updateArrows(self):
        pass

    def prevPhoto(self):
        pass

    def nextPhoto(self):
        pass
