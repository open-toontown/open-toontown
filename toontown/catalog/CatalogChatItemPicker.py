from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.showbase import DirectObject
import CatalogItem
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from otp.otpbase import OTPLocalizer
from toontown.toontowngui import TTDialog
NUM_ITEMS_SHOWN = 15

class CatalogChatItemPicker(DirectObject.DirectObject):

    def __init__(self, callback, newMsg):
        self.confirmDelete = None
        self.doneCallback = callback
        self.panel = DirectFrame(relief=None, geom=DGG.getDefaultDialogGeom(), geom_color=ToontownGlobals.GlobalDialogColor, geom_scale=(1.4, 1, 1.6), text=TTLocalizer.MessagePickerTitle % OTPLocalizer.CustomSCStrings[newMsg], text_pos=(0, 0.68), text_scale=0.05, text_wordwrap=24, pos=(0, 0, 0))
        msgStrings = []
        for msg in base.localAvatar.customMessages:
            msgStrings.append(OTPLocalizer.CustomSCStrings[msg])

        gui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
        self.picker = DirectScrolledList(parent=self.panel, relief=None, pos=(0, 0, 0), incButton_image=(gui.find('**/FndsLst_ScrollUp'),
         gui.find('**/FndsLst_ScrollDN'),
         gui.find('**/FndsLst_ScrollUp_Rllvr'),
         gui.find('**/FndsLst_ScrollUp')), incButton_relief=None, incButton_scale=(1.3, 1.3, -1.3), incButton_pos=(0, 0, -0.5), incButton_image3_color=Vec4(1, 1, 1, 0.2), decButton_image=(gui.find('**/FndsLst_ScrollUp'),
         gui.find('**/FndsLst_ScrollDN'),
         gui.find('**/FndsLst_ScrollUp_Rllvr'),
         gui.find('**/FndsLst_ScrollUp')), decButton_relief=None, decButton_scale=(1.3, 1.3, 1.3), decButton_pos=(0, 0, 0.5), decButton_image3_color=Vec4(1, 1, 1, 0.2), itemFrame_pos=(0, 0, 0.39), itemFrame_scale=1.0, itemFrame_relief=DGG.SUNKEN, itemFrame_frameSize=(-0.55,
         0.55,
         -0.85,
         0.06), itemFrame_frameColor=(0.85, 0.95, 1, 1), itemFrame_borderWidth=(0.01, 0.01), itemMakeFunction=self.makeMessageButton, itemMakeExtraArgs=[base.localAvatar.customMessages], numItemsVisible=NUM_ITEMS_SHOWN, items=msgStrings)
        clipper = PlaneNode('clipper')
        clipper.setPlane(Plane(Vec3(-1, 0, 0), Point3(0.55, 0, 0)))
        clipNP = self.picker.attachNewNode(clipper)
        self.picker.setClipPlane(clipNP)
        gui.removeNode()
        buttonModels = loader.loadModel('phase_3.5/models/gui/inventory_gui')
        upButton = buttonModels.find('**/InventoryButtonUp')
        downButton = buttonModels.find('**/InventoryButtonDown')
        rolloverButton = buttonModels.find('**/InventoryButtonRollover')
        exitButton = DirectButton(parent=self.panel, relief=None, pos=(0, 0, -0.7), text=TTLocalizer.MessagePickerCancel, text_scale=TTLocalizer.CCIPexitButton, text_pos=(-0.005, -0.01), text_fg=Vec4(1, 1, 1, 1), textMayChange=0, image=(upButton, downButton, rolloverButton), image_scale=1.1, image_color=(0, 0.6, 1, 1), command=self.__handleCancel)
        buttonModels.removeNode()
        return

    def hide(self):
        base.transitions.noTransitions()
        self.panel.hide()

    def show(self):
        base.transitions.fadeScreen(0.5)
        self.panel.setBin('gui-popup', 0)
        self.panel.show()

    def destroy(self):
        base.transitions.noTransitions()
        self.panel.destroy()
        del self.panel
        del self.picker
        del self.doneCallback
        if self.confirmDelete:
            self.confirmDelete.cleanup()
            del self.confirmDelete
            self.confirmDelete = None
        return

    def makeMessageButton(self, name, number, *extraArgs):
        msg = extraArgs[0][0][number]
        return DirectButton(relief=None, text=OTPLocalizer.CustomSCStrings[msg], text_pos=(-0.5, 0, 0), text_scale=0.05, text_align=TextNode.ALeft, text1_bg=Vec4(1, 1, 0, 1), text2_bg=Vec4(0.5, 0.9, 1, 1), text3_fg=Vec4(0.4, 0.8, 0.4, 1), command=self.__handleDelete, extraArgs=[msg])

    def __handleDelete(self, msg):
        self.confirmDelete = TTDialog.TTGlobalDialog(doneEvent='confirmDelete', message=TTLocalizer.MessageConfirmDelete % OTPLocalizer.CustomSCStrings[msg], style=TTDialog.TwoChoice)
        self.confirmDelete.msg = msg
        self.hide()
        self.confirmDelete.show()
        self.accept('confirmDelete', self.__handleDeleteConfirm)

    def __handleCancel(self):
        self.doneCallback('cancel')

    def __handleDeleteConfirm(self):
        status = self.confirmDelete.doneStatus
        msg = self.confirmDelete.msg
        self.ignore('confirmDelete')
        self.confirmDelete.cleanup()
        del self.confirmDelete
        self.confirmDelete = None
        if status == 'ok':
            self.doneCallback('pick', base.localAvatar.customMessages.index(msg))
        else:
            self.show()
        return
