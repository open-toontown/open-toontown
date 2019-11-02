from direct.gui.DirectGui import DirectFrame, DirectButton, DirectLabel
from direct.gui.DirectGui import DirectScrolledList, DirectCheckButton
from direct.gui.DirectCheckBox import DirectCheckBox
from direct.gui import DirectGuiGlobals
from toontown.toonbase import ToontownGlobals
from pandac.PandaModules import Vec3, Vec4, PlaneNode, Plane, Point3, TextNode, VBase4, NodePath

class ScrolledFriendList(DirectScrolledList):

    def __init__(self, parent, gui, clickCallback = None, makeItemsCheckBoxes = False):
        self.makeItemsCheckBoxes = makeItemsCheckBoxes
        self.clickCallback = clickCallback
        self.parent = parent
        self.gui = gui
        self.scrollSpeed = 1
        DirectScrolledList.__init__(self, parent=parent, relief=None, incButton_image=(self.gui.find('**/inviteButtonDown_up'), self.gui.find('**/inviteButtonDown_down'), self.gui.find('**/inviteButtonDown_rollover')), incButton_relief=None, incButton_pos=(0.0, 0.0, -0.03), incButton_image3_color=Vec4(0.6, 0.6, 0.6, 0.6), decButton_image=(self.gui.find('**/inviteButtonUp_up'), self.gui.find('**/inviteButtonUp_down'), self.gui.find('**/inviteButtonUp_rollover')), decButton_relief=None, decButton_pos=(0.0, 0.0, 0.02), decButton_image3_color=Vec4(0.6, 0.6, 0.6, 0.6), itemFrame_relief=None, forceHeight=0.084, numItemsVisible=8, items=[], incButtonCallback=self.scrollButtonPressed, decButtonCallback=self.scrollButtonPressed, itemFrame_pos=(0.0, 0.0, -0.01))
        self.incButtonCallback = None
        self.decButtonCallback = None
        self.setForceHeight()
        return

    def scrollButtonPressed(self):
        pass

    def addFriend(self, name, id):
        if self.makeItemsCheckBoxes:
            checkedImage = self.gui.find('**/inviteButtonChecked')
            uncheckedImage = self.gui.find('**/inviteButtonUnchecked')
            widget = DirectCheckButton(relief=None, scale=0.1, boxBorder=0.08, boxImage=(uncheckedImage, checkedImage, None), boxImageScale=10.0, boxRelief=None, text=name, text_align=TextNode.ALeft, text_scale=0.7, text_pos=(-3.7, -0.25), command=self.clickCallback, indicator_pos=(-4.8, 0.0, 0.0))
            widget['extraArgs'] = [widget]
        else:
            widget = DirectLabel(relief=None, text=name, text_align=TextNode.ALeft, text_pos=(-0.6, 0.0, 0.0), scale=0.055)
        widget.setPythonTag('id', id)
        self.addItem(widget)
        return
