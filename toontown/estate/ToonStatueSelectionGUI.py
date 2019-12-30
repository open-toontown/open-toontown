from toontown.estate import PlantingGUI
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from direct.task import Task
from toontown.estate import GardenGlobals
from toontown.estate import DistributedToonStatuary
from direct.interval.IntervalGlobal import *
from direct.gui.DirectScrolledList import *
from toontown.toon import Toon
from toontown.toon import DistributedToon
from direct.distributed import DistributedObject

class ToonStatueSelectionGUI(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToonStatueSelectionGUI')

    def __init__(self, doneEvent, specialBoxActive = False):
        base.tssGUI = self
        instructions = TTLocalizer.GardeningChooseToonStatue
        instructionsPos = (0, 0.4)
        DirectFrame.__init__(self, relief=None, state='normal', geom=DGG.getDefaultDialogGeom(), geom_color=ToontownGlobals.GlobalDialogColor, geom_scale=(1.5, 1.0, 1.0), frameSize=(-1, 1, -1, 1), pos=(0, 0, 0), text=instructions, text_wordwrap=18, text_scale=0.08, text_pos=instructionsPos)
        self.initialiseoptions(ToonStatueSelectionGUI)
        self.doneEvent = doneEvent
        buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
        okImageList = (buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr'))
        cancelImageList = (buttons.find('**/CloseBtn_UP'), buttons.find('**/CloseBtn_DN'), buttons.find('**/CloseBtn_Rllvr'))
        self.cancelButton = DirectButton(parent=self, relief=None, image=cancelImageList, pos=(-0.3, 0, -0.35), text=TTLocalizer.PlantingGuiCancel, text_scale=0.06, text_pos=(0, -0.1), command=self.__cancel)
        self.okButton = DirectButton(parent=self, relief=None, image=okImageList, pos=(0.3, 0, -0.35), text=TTLocalizer.PlantingGuiOk, text_scale=0.06, text_pos=(0, -0.1), command=self.__accept)
        buttons.removeNode()
        self.ffList = []
        self.friends = {}
        self.doId2Dna = {}
        self.textRolloverColor = Vec4(1, 1, 0, 1)
        self.textDownColor = Vec4(0.5, 0.9, 1, 1)
        self.textDisabledColor = Vec4(0.4, 0.8, 0.4, 1)
        self.createFriendsList()
        return

    def destroy(self):
        self.doneEvent = None
        self.previewToon.delete()
        self.previewToon = None
        for ff in self.ffList:
            self.friends[ff].destroy()

        self.ffList = []
        self.friends = {}
        self.doId2Dna = {}
        self.scrollList.destroy()
        DirectFrame.destroy(self)
        return

    def __cancel(self):
        messenger.send(self.doneEvent, [0, '', -1])
        messenger.send('wakeup')

    def __accept(self):
        messenger.send(self.doneEvent, [1, '', DistributedToonStatuary.dnaCodeFromToonDNA(self.dnaSelected)])
        messenger.send('wakeup')

    def createFriendsList(self):
        self.__makeFFlist()
        if len(self.ffList) > 0:
            gui = loader.loadModel('phase_3.5/models/gui/friendslist_gui')
            self.scrollList = DirectScrolledList(parent=self, relief=None, incButton_image=(gui.find('**/FndsLst_ScrollUp'),
             gui.find('**/FndsLst_ScrollDN'),
             gui.find('**/FndsLst_ScrollUp_Rllvr'),
             gui.find('**/FndsLst_ScrollUp')), incButton_relief=None, incButton_pos=(0.0, 0.0, -0.316), incButton_image1_color=Vec4(1.0, 0.9, 0.4, 1.0), incButton_image3_color=Vec4(1.0, 1.0, 0.6, 0.5), incButton_scale=(1.0, 1.0, -1.0), decButton_image=(gui.find('**/FndsLst_ScrollUp'),
             gui.find('**/FndsLst_ScrollDN'),
             gui.find('**/FndsLst_ScrollUp_Rllvr'),
             gui.find('**/FndsLst_ScrollUp')), decButton_relief=None, decButton_pos=(0.0, 0.0, 0.117), decButton_image1_color=Vec4(1.0, 1.0, 0.6, 1.0), decButton_image3_color=Vec4(1.0, 1.0, 0.6, 0.6), itemFrame_pos=(-0.17, 0.0, 0.06), itemFrame_relief=DGG.SUNKEN, itemFrame_frameSize=(-0.01,
             0.35,
             -0.35,
             0.04), itemFrame_frameColor=(0.85, 0.95, 1, 1), itemFrame_borderWidth=(0.01, 0.01), numItemsVisible=8, itemFrame_scale=1.0, items=[])
            gui.removeNode()
            self.scrollList.setPos(0.35, 0, 0.125)
            self.scrollList.setScale(1.25)
            clipper = PlaneNode('clipper')
            clipper.setPlane(Plane(Vec3(-1, 0, 0), Point3(0.17, 0, 0)))
            clipNP = self.scrollList.attachNewNode(clipper)
            self.scrollList.setClipPlane(clipNP)
            self.__makeScrollList()
        return

    def checkFamily(self, doId):
        test = 0
        for familyMember in base.cr.avList:
            if familyMember.id == doId:
                test = 1

        return test

    def __makeFFlist(self):
        playerAvatar = (base.localAvatar.doId, base.localAvatar.name, NametagGroup.CCNonPlayer)
        self.ffList.append(playerAvatar)
        self.dnaSelected = base.localAvatar.style
        self.createPreviewToon(self.dnaSelected)
        for familyMember in base.cr.avList:
            if familyMember.id != base.localAvatar.doId:
                newFF = (familyMember.id, familyMember.name, NametagGroup.CCNonPlayer)
                self.ffList.append(newFF)

        for friendPair in base.localAvatar.friendsList:
            friendId, flags = friendPair
            handle = base.cr.identifyFriend(friendId)
            if handle and not self.checkFamily(friendId):
                if hasattr(handle, 'getName'):
                    colorCode = NametagGroup.CCSpeedChat
                    if flags & ToontownGlobals.FriendChat:
                        colorCode = NametagGroup.CCFreeChat
                    newFF = (friendPair[0], handle.getName(), colorCode)
                    self.ffList.append(newFF)
                else:
                    self.notify.warning('Bad Handle for getName in makeFFlist')

    def __makeScrollList(self):
        for ff in self.ffList:
            ffbutton = self.makeFamilyButton(ff[0], ff[1], ff[2])
            if ffbutton:
                self.scrollList.addItem(ffbutton, refresh=0)
                self.friends[ff] = ffbutton

        self.scrollList.refresh()

    def makeFamilyButton(self, familyId, familyName, colorCode):
        fg = NametagGlobals.getNameFg(colorCode, PGButton.SInactive)
        return DirectButton(relief=None, text=familyName, text_scale=0.04, text_align=TextNode.ALeft, text_fg=fg, text1_bg=self.textDownColor, text2_bg=self.textRolloverColor, text3_fg=self.textDisabledColor, textMayChange=0, command=self.__chooseFriend, extraArgs=[familyId, familyName])

    def __chooseFriend(self, friendId, friendName):
        messenger.send('wakeup')
        if self.checkFamily(friendId):
            if friendId == base.localAvatar.doId:
                self.createPreviewToon(base.localAvatar.style)
            elif friendId in self.doId2Dna:
                self.createPreviewToon(self.doId2Dna[friendId])
            else:
                familyAvatar = DistributedToon.DistributedToon(base.cr)
                familyAvatar.doId = friendId
                familyAvatar.forceAllowDelayDelete()
                base.cr.getAvatarDetails(familyAvatar, self.__handleFamilyAvatar, 'DistributedToon')
        else:
            friend = base.cr.identifyFriend(friendId)
            if friend:
                self.createPreviewToon(friend.style)

    def __handleFamilyAvatar(self, gotData, avatar, dclass):
        self.doId2Dna[avatar.doId] = avatar.style
        self.createPreviewToon(avatar.style)
        avatar.delete()

    def createPreviewToon(self, dna):
        if hasattr(self, 'previewToon'):
            self.previewToon.delete()
        self.dnaSelected = dna
        self.previewToon = Toon.Toon()
        self.previewToon.setDNA(dna)
        self.previewToon.loop('neutral')
        self.previewToon.setH(180)
        self.previewToon.setPos(-0.3, 0, -0.3)
        self.previewToon.setScale(0.13)
        self.previewToon.reparentTo(self)
        self.previewToon.startBlink()
        self.previewToon.startLookAround()
        self.previewToon.getGeomNode().setDepthWrite(1)
        self.previewToon.getGeomNode().setDepthTest(1)
