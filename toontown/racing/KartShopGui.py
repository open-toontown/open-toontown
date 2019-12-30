if __name__ == '__main__':
    from direct.directbase import DirectStart
from pandac.PandaModules import *
from direct.directnotify import DirectNotifyGlobal
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.showbase import DirectObject, PythonUtil
from toontown.toonbase import ToontownGlobals, TTLocalizer
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownTimer
from .KartShopGlobals import *
from toontown.racing.Kart import Kart
from toontown.shtiker.KartPage import KartViewer
from .KartDNA import *
from toontown.toontowngui.TeaserPanel import TeaserPanel
if (__debug__):
    import pdb
MENUS = PythonUtil.Enum('MainMenu, BuyKart, BuyAccessory, ReturnKart, ConfirmBuyAccessory, ConfirmBuyKart, BoughtKart, BoughtAccessory, TeaserPanel')
MM_OPTIONS = PythonUtil.Enum('Cancel, BuyAccessory, BuyKart', -1)
BK_OPTIONS = PythonUtil.Enum('Cancel, BuyKart', -1)
BA_OPTIONS = PythonUtil.Enum('Cancel, BuyAccessory', -1)
RK_OPTIONS = PythonUtil.Enum('Cancel, ReturnKart', -1)
CBK_OPTIONS = PythonUtil.Enum('Cancel, BuyKart', -1)
CBA_OPTIONS = PythonUtil.Enum('Cancel, BuyAccessory', -1)
BTK_OPTIONS = PythonUtil.Enum('Ok', -1)
BTA_OPTIONS = PythonUtil.Enum('Ok', -1)
KS_TEXT_SIZE_BIG = TTLocalizer.KSGtextSizeBig
KS_TEXT_SIZE_SMALL = TTLocalizer.KSGtextSizeSmall

class KartShopGuiMgr(DirectObject.DirectObject, object):
    notify = DirectNotifyGlobal.directNotify.newCategory('KartShopGuiMgr')

    class MainMenuDlg(DirectFrame):
        notify = DirectNotifyGlobal.directNotify.newCategory('KartShopGuiMgr.MainMenuDlg')

        def __init__(self, doneEvent):
            model = loader.loadModel('phase_6/models/gui/Kart_MainMenuPanel')
            self.modelScale = 0.75
            DirectFrame.__init__(self, relief=None, state='normal', geom=model, text_scale=0.1, geom_scale=self.modelScale, pos=(0, 0, -.01), frameSize=(-1, 1, -1, 1))
            self.initialiseoptions(KartShopGuiMgr.MainMenuDlg)
            self.cancelButton = DirectButton(
                parent=self,
                relief=None,
                geom=model.find('**/CancelIcon'),
                image=(model.find('**/CancelButtonUp'), model.find('**/CancelButtonDown'), model.find('**/CancelButtonRollover')),
                scale=self.modelScale,
                pressEffect=False,
                command=lambda : messenger.send(doneEvent, [MM_OPTIONS.Cancel]))
            self.buyKartButton = DirectButton(
                parent=self,
                relief=None,
                image=(model.find('**/BuyKartButtonUp'), model.find('**/BuyKartButtonDown'), model.find('**/BuyKartButtonRollover'), model.find('**/BuyKartButtonDisabled')),
                scale=self.modelScale,
                geom=model.find('**/BuyKartIcon'),
                text=TTLocalizer.KartShop_BuyKart,
                text_scale=KS_TEXT_SIZE_BIG,
                text_pos=(-0.2, 0.34),
                pressEffect=False,
                command=lambda : messenger.send(doneEvent, [MM_OPTIONS.BuyKart]))
            self.buyAccessoryButton = DirectButton(
                parent=self,
                relief=None,
                image=(model.find('**/BuyAccessoryButtonUp'), model.find('**/BuyAccessoryButtonDown'), model.find('**/BuyAccessoryButtonRollover'), model.find('**/BuyAccessoryButtonDisabled')),
                geom=model.find('**/BuyAccessoryIcon'),
                image3_color=Vec4(0.6, 0.6, 0.6, 1),
                scale=self.modelScale,
                text=TTLocalizer.KartShop_BuyAccessories,
                text_scale=KS_TEXT_SIZE_BIG,
                text_pos=(-0.1, 0.036),
                pressEffect=False,
                command=lambda : messenger.send(doneEvent, [MM_OPTIONS.BuyAccessory]))
            self.updateButtons()
            return

        def updateButtons(self):
            if not base.localAvatar.hasKart():
                self.buyAccessoryButton['state'] = DGG.DISABLED
            else:
                self.buyAccessoryButton['state'] = DGG.NORMAL

        def show(self):
            self.updateButtons()
            DirectFrame.DirectFrame.show(self)

    class BuyKartDlg(DirectFrame):
        notify = DirectNotifyGlobal.directNotify.newCategory('KartShopGuiMgr.BuyKartDlg')

        def __init__(self, doneEvent):
            self.modelScale = 1
            model = loader.loadModel('phase_6/models/gui/BuyKartPanel')
            self.unownedKartList = list(KartDict.keys())
            if base.localAvatar.hasKart():
                k = base.localAvatar.getKartBodyType()
                if k in self.unownedKartList:
                    self.unownedKartList.remove(k)
            self.numKarts = len(self.unownedKartList)
            self.curKart = 0
            DirectFrame.__init__(
                self,
                relief=None,
                state='normal',
                geom=model,
                geom_scale=self.modelScale,
                frameSize=(-1, 1, -1, 1),
                pos=(0, 0, -0.01),
                text_wordwrap=26,
                text_scale=KS_TEXT_SIZE_BIG,
                text_pos=(0, 0))
            self.initialiseoptions(KartShopGuiMgr.BuyKartDlg)
            self.ticketDisplay = DirectLabel(
                parent=self,
                relief=None,
                text=str(base.localAvatar.getTickets()),
                text_scale=KS_TEXT_SIZE_SMALL,
                text_fg=(0.95, 0.95, 0.0, 1.0),
                text_shadow=(0, 0, 0, 1),
                text_pos=(0.44, -0.55),
                text_font=ToontownGlobals.getSignFont())
            self.buyKartButton = DirectButton(
                parent=self,
                relief=None,
                image=(model.find('**/BuyKartButtonUp'), model.find('**/BuyKartButtonDown'), model.find('**/BuyKartButtonRollover'), model.find('**/BuyKartButtonDisabled')),
                scale=self.modelScale,
                text=TTLocalizer.KartShop_BuyKart,
                text_scale=KS_TEXT_SIZE_BIG,
                text_pos=(0, -.534),
                pressEffect=False,
                command=lambda : messenger.send(doneEvent, [self.unownedKartList[self.curKart]]))
            self.cancelButton = DirectButton(
                parent=self,
                relief=None,
                image=(model.find('**/CancelButtonUp'), model.find('**/CancelButtonDown'), model.find('**/CancelButtonRollover')),
                geom=model.find('**/CancelIcon'),
                scale=self.modelScale,
                pressEffect=False,
                command=lambda : messenger.send(doneEvent, [BK_OPTIONS.Cancel]))
            self.arrowLeftButton = DirectButton(
                parent=self,
                relief=None,
                image=(model.find('**/ArrowLeftButtonUp'), model.find('**/ArrowLeftButtonDown'), model.find('**/ArrowLeftButtonRollover'), model.find('**/ArrowLeftButtonInactive')),
                scale=self.modelScale,
                pressEffect=False,
                command=self.__handleKartChange,
                extraArgs=[-1])
            self.arrowRightButton = DirectButton(
                parent=self,
                relief=None,
                image=(model.find('**/ArrowRightButtonUp'), model.find('**/ArrowRightButtonDown'), model.find('**/ArrowRightButtonRollover'), model.find('**/ArrowRightButtonInactive')),
                scale=self.modelScale,
                pressEffect=False,
                command=self.__handleKartChange,
                extraArgs=[1])
            self.kartView = KartViewer([self.curKart, -1, -1, -1, -1, -1, -1, -1, -1], parent=self)
            self.kartView.setPos(model.find('**/KartViewerFrame').getPos())
            self.kartView.load(model, 'KartViewerFrame', ['rotate_right_up',
             'rotate_right_down',
             'rotate_right_roll',
             'rotate_right_down',
             (0.255, -.054)], ['rotate_left_up',
             'rotate_left_down',
             'rotate_left_roll',
             'rotate_left_down',
             (-.24, -.054)], (0, -.055))
            self.kartView.setBounds(-0.38, 0.38, 0.0035, 0.53)
            self.kartView.setBgColor(1.0, 1.0, 0.8, 1.0)
            self.showKart()
            self.initialize = True
            model.removeNode()
            return

        def showKart(self):
            self.buyKartButton.configure(text=TTLocalizer.KartShop_BuyKart)
            self.buyKartButton.configure(text_scale=KS_TEXT_SIZE_BIG)
            if self.numKarts > 0:
                info = getKartTypeInfo(self.unownedKartList[self.curKart])
                description = info[KartInfo.name]
                cost = TTLocalizer.KartShop_Cost % info[KartInfo.cost]
                self.kartDescription = DirectButton(
                    parent=self,
                    relief=None,
                    scale=self.modelScale,
                    text=description,
                    text_pos=(0, -.29),
                    text_scale=KS_TEXT_SIZE_SMALL,
                    pressEffect=False,
                    textMayChange=True)
                self.kartCost = DirectButton(
                    parent=self,
                    relief=None,
                    scale=self.modelScale,
                    text=cost,
                    text_pos=(0, -.365),
                    text_scale=KS_TEXT_SIZE_SMALL,
                    pressEffect=False,
                    textMayChange=True)
                self.buyKartButton['state'] = DGG.NORMAL
                self.arrowRightButton['state'] = DGG.DISABLED
                self.arrowLeftButton['state'] = DGG.DISABLED
                if self.numKarts > self.curKart + 1:
                    self.arrowRightButton['state'] = DGG.NORMAL
                if self.curKart > 0:
                    self.arrowLeftButton['state'] = DGG.NORMAL
                if info[KartInfo.cost] > base.localAvatar.getTickets():
                    self.buyKartButton['state'] = DGG.DISABLED
                    self.buyKartButton.configure(text_scale=KS_TEXT_SIZE_SMALL * 0.75)
                    self.buyKartButton.configure(text=TTLocalizer.KartShop_NotEnoughTickets)
                    self.kartCost.configure(text_fg=(0.95, 0, 0.0, 1.0))
                self.kartView.refresh([self.unownedKartList[self.curKart], -1, -1, -1, -1, -1, -1, -1, -1])
                self.kartView.show()
            return

        def __handleKartChange(self, nDir):
            self.curKart = (self.curKart + nDir) % self.numKarts
            self.kartDescription.destroy()
            self.kartCost.destroy()
            self.showKart()

        def destroy(self):
            if self.initialize:
                self.kartView.destroy()
                DirectFrame.destroy(self)

    class ReturnKartDlg(DirectFrame):
        notify = DirectNotifyGlobal.directNotify.newCategory('KartShopGuiMgr.ReturnKartDlg')

        def __init__(self, doneEvent):
            self.modelScale = 1
            model = loader.loadModel('phase_6/models/gui/ReturnKartPanel')
            DirectFrame.__init__(
                self,
                relief=None,
                state='normal',
                geom=model,
                geom_scale=self.modelScale,
                frameSize=(-1, 1, -1, 1),
                pos=(0, 0, -0.01),
                text=TTLocalizer.KartShop_ConfirmReturnKart,
                text_wordwrap=11,
                text_scale=KS_TEXT_SIZE_SMALL * 0.9,
                text_pos=(0, -0.26))
            self.initialiseoptions(KartShopGuiMgr.ReturnKartDlg)
            self.cancelButton = DirectButton(
                parent=self,
                relief=None,
                image=(model.find('**/CancelButtonUp'), model.find('**/CancelButtonDown'), model.find('**/CancelButtonRollover')),
                geom=model.find('**/CancelIcon'),
                scale=self.modelScale,
                pressEffect=False,
                command=lambda : messenger.send(doneEvent, [RK_OPTIONS.Cancel]))
            self.okButton = DirectButton(
                parent=self,
                relief=None,
                image=(model.find('**/CheckButtonUp'), model.find('**/CheckButtonDown'), model.find('**/CheckButtonRollover')),
                geom=model.find('**/CheckIcon'),
                scale=self.modelScale,
                pressEffect=False,
                command=lambda : messenger.send(doneEvent, [RK_OPTIONS.ReturnKart]))
            oldDNA = list(base.localAvatar.getKartDNA())
            for d in range(len(oldDNA)):
                if d == KartDNA.bodyType:
                    continue
                else:
                    oldDNA[d] = InvalidEntry

            self.kartView = KartViewer(oldDNA, parent=self)
            self.kartView.setPos(model.find('**/KartViewerFrame').getPos())
            self.kartView.load(model, 'KartViewerFrame', [], [], None)
            self.kartView.setBounds(-0.38, 0.38, -.04, 0.49)
            self.kartView.setBgColor(1.0, 1.0, 0.8, 1.0)
            self.kartView.show()
            model.removeNode()
            self.initialize = True
            return

        def destroy(self):
            if self.initialize:
                self.kartView.destroy()
            DirectFrame.destroy(self)

    class BoughtKartDlg(DirectFrame):
        notify = DirectNotifyGlobal.directNotify.newCategory('KartShopGuiMgr.BoughtKartDlg')

        def __init__(self, doneEvent, kartID):
            self.modelScale = 1
            model = loader.loadModel('phase_6/models/gui/BoughtKartPanel')
            kartInfo = getKartTypeInfo(kartID)
            name = kartInfo[KartInfo.name]
            DirectFrame.__init__(
                self,
                relief=None,
                state='normal',
                geom=model,
                geom_scale=self.modelScale,
                frameSize=(-1, 1, -1, 1),
                pos=(0, 0, -0.01),
                text=TTLocalizer.KartShop_ConfirmBoughtTitle,
                text_wordwrap=26,
                text_scale=KS_TEXT_SIZE_SMALL,
                text_pos=(0, -0.26))
            self.initialiseoptions(KartShopGuiMgr.BoughtKartDlg)
            self.ticketDisplay = DirectLabel(
                parent=self,
                relief=None,
                text=str(base.localAvatar.getTickets()),
                text_scale=KS_TEXT_SIZE_SMALL,
                text_fg=(0.95, 0.95, 0.0, 1.0),
                text_shadow=(0, 0, 0, 1),
                text_pos=(0.43, -0.5),
                text_font=ToontownGlobals.getSignFont())
            self.okButton = DirectButton(
                parent=self,
                relief=None,
                image=(model.find('**/CheckButtonUp'), model.find('**/CheckButtonDown'), model.find('**/CheckButtonRollover')),
                geom=model.find('**/CheckIcon'),
                scale=self.modelScale,
                pressEffect=False,
                command=lambda : messenger.send(doneEvent, [BTK_OPTIONS.Ok]))
            self.kartView = KartViewer([kartID, -1, -1, -1, -1, -1, -1, -1, -1], parent=self)
            self.kartView.setPos(model.find('**/KartViewerFrame').getPos())
            self.kartView.load(model, 'KartViewerFrame', [], [])
            self.kartView.setBounds(-0.38, 0.38, -.0425, 0.49)
            self.kartView.setBgColor(1.0, 1.0, 0.8, 1.0)
            self.kartView.show()
            model.removeNode()
            self.initialize = True
            return

        def destroy(self):
            if self.initialize:
                self.kartView.destroy()
            DirectFrame.destroy(self)

    class ConfirmBuyKartDlg(DirectFrame):
        notify = DirectNotifyGlobal.directNotify.newCategory('KartShopGuiMgr.ConfirmBuyKartDlg')

        def __init__(self, doneEvent, kartNum):
            self.kartNum = kartNum
            self.modelScale = 1
            model = loader.loadModel('phase_6/models/gui/ConfirmBuyKartPanel')
            kartInfo = getKartTypeInfo(kartNum)
            name = kartInfo[KartInfo.name]
            cost = kartInfo[KartInfo.cost]
            DirectFrame.__init__(
                self,
                relief=None,
                state='normal',
                geom=model,
                geom_scale=self.modelScale,
                frameSize=(-1, 1, -1, 1),
                pos=(0, 0, -0.01),
                text=TTLocalizer.KartShop_ConfirmBuy % (name, cost),
                text_wordwrap=11,
                text_scale=KS_TEXT_SIZE_SMALL,
                text_pos=(0, -0.26))
            self.initialiseoptions(KartShopGuiMgr.ConfirmBuyKartDlg)
            self.ticketDisplay = DirectLabel(
                parent=self,
                relief=None,
                text=str(base.localAvatar.getTickets()),
                text_scale=KS_TEXT_SIZE_SMALL,
                text_fg=(0.95, 0.95, 0.0, 1.0),
                text_shadow=(0, 0, 0, 1),
                text_pos=(0.43, -0.5),
                text_font=ToontownGlobals.getSignFont())
            self.cancelButton = DirectButton(
                parent=self,
                relief=None,
                image=(model.find('**/CancelButtonUp'), model.find('**/CancelButtonDown'), model.find('**/CancelButtonRollover')),
                geom=model.find('**/CancelIcon'),
                scale=self.modelScale,
                pressEffect=False,
                command=lambda : messenger.send(doneEvent, [CBK_OPTIONS.Cancel]))
            self.okButton = DirectButton(
                parent=self,
                relief=None,
                image=(model.find('**/CheckButtonUp'), model.find('**/CheckButtonDown'), model.find('**/CheckButtonRollover')),
                geom=model.find('**/CheckIcon'),
                scale=self.modelScale,
                pressEffect=False,
                command=lambda : messenger.send(doneEvent, [CBK_OPTIONS.BuyKart]))
            self.kartView = KartViewer([self.kartNum, -1, -1, -1, -1, -1, -1, -1, -1], parent=self)
            self.kartView.setPos(model.find('**/KartViewerFrame').getPos())
            self.kartView.load(model, 'KartViewerFrame', [], [], None)
            self.kartView.setBounds(-0.38, 0.38, -.0425, 0.49)
            self.kartView.setBgColor(1.0, 1.0, 0.8, 1.0)
            self.initialize = True
            self.kartView.show()
            model.removeNode()
            return

        def destroy(self):
            if self.initialize:
                self.kartView.destroy()
                DirectFrame.destroy(self)

    class BuyAccessoryDlg(DirectFrame):
        notify = DirectNotifyGlobal.directNotify.newCategory('KartShopGuiMgr.buyAccessoryDlg')

        def __init__(self, doneEvent):
            self.modelScale = 1
            model = loader.loadModel('phase_6/models/gui/BuyAccessoryPanel')
            self.doneEvent = doneEvent
            DirectFrame.__init__(self, relief=None, state='normal', geom=model, geom_scale=self.modelScale, frameSize=(-1, 1, -1, 1), pos=(0, 0, -0.01), text_wordwrap=26, text_scale=0.1, text_fg=Vec4(0.36, 0.94, 0.93, 1.0), text_pos=(0, 0))
            self.initialiseoptions(KartShopGuiMgr.BuyAccessoryDlg)
            self.ticketDisplay = DirectLabel(
                parent=self,
                relief=None,
                text=str(base.localAvatar.getTickets()),
                text_scale=KS_TEXT_SIZE_SMALL,
                text_fg=(0.95, 0.95, 0.0, 1.0),
                text_shadow=(0, 0, 0, 1),
                text_pos=(0.42, -0.6),
                text_font=ToontownGlobals.getSignFont())
            self.arrowLeftButton = DirectButton(
                parent=self,
                relief=None,
                image=(model.find('**/ArrowLeftButtonUp'), model.find('**/ArrowLeftButtonDown'), model.find('**/ArrowLeftButtonRollover'), model.find('**/ArrowLeftButtonInactive')),
                scale=self.modelScale,
                text_pos=(0, 0),
                text_scale=0.1,
                pressEffect=False,
                command=self.__handleAccessoryChange,
                extraArgs=[-1])
            self.arrowRightButton = DirectButton(
                parent=self,
                relief=None,
                image=(model.find('**/ArrowRightButtonUp'), model.find('**/ArrowRightButtonDown'), model.find('**/ArrowRightButtonRollover'), model.find('**/ArrowRightButtonInactive')),
                scale=self.modelScale,
                text_pos=(0, 0),
                text_scale=0.1,
                pressEffect=False,
                command=self.__handleAccessoryChange,
                extraArgs=[1])
            self.cancelButton = DirectButton(
                parent=self,
                relief=None,
                image=(model.find('**/CancelButtonUp'), model.find('**/CancelButtonDown'), model.find('**/CancelButtonRollover')),
                geom=model.find('**/CancelIcon'),
                scale=self.modelScale,
                command=lambda : messenger.send(doneEvent, [BA_OPTIONS.Cancel]),
                pressEffect=False)
            self.decalAccButton = DirectButton(
                parent=self,
                relief=None,
                image=(model.find('**/DecalButtonUp'), model.find('**/DecalButtonDown'), model.find('**/DecalButtonRollover'), model.find('**/DecalButtonDown')),
                scale=self.modelScale,
                pressEffect=False,
                command=self.__handleAccessoryTypeChange,
                extraArgs=[KartDNA.decalType])
            self.spoilerAccButton = DirectButton(
                parent=self,
                relief=None,
                image=(model.find('**/SpoilerButtonUp'), model.find('**/SpoilerButtonDown'), model.find('**/SpoilerButtonRollover'), model.find('**/SpoilerButtonDown')),
                scale=self.modelScale,
                pressEffect=False,
                command=self.__handleAccessoryTypeChange,
                extraArgs=[KartDNA.spType])
            self.eBlockAccButton = DirectButton(
                parent=self,
                relief=None,
                image=(model.find('**/EBlockButtonUp'), model.find('**/EBlockButtonDown'), model.find('**/EBlockButtonRollover'), model.find('**/EBlockButtonDown')),
                scale=self.modelScale,
                pressEffect=False,
                command=self.__handleAccessoryTypeChange,
                extraArgs=[KartDNA.ebType])
            self.rearAccButton = DirectButton(
                parent=self,
                relief=None,
                image=(model.find('**/RearButtonUp'), model.find('**/RearButtonDown'), model.find('**/RearButtonRollover'), model.find('**/RearButtonDown')),
                scale=self.modelScale,
                pressEffect=False,
                command=self.__handleAccessoryTypeChange,
                extraArgs=[KartDNA.bwwType])
            self.frontAccButton = DirectButton(
                parent=self,
                relief=None,
                image=(model.find('**/FrontButtonUp'), model.find('**/FrontButtonDown'), model.find('**/FrontButtonRollover'), model.find('**/FrontButtonDown')),
                scale=self.modelScale,
                text_pos=(0, 0),
                text_scale=0.1,
                pressEffect=False,
                command=self.__handleAccessoryTypeChange,
                extraArgs=[KartDNA.fwwType])
            self.rimAccButton = DirectButton(
                parent=self,
                relief=None,
                image=(model.find('**/RimButtonUp'), model.find('**/RimButtonDown'), model.find('**/RimButtonRollover'), model.find('**/RimButtonDown')),
                scale=self.modelScale,
                pressEffect=False,
                command=self.__handleAccessoryTypeChange,
                extraArgs=[KartDNA.rimsType])
            self.paintAccButton = DirectButton(
                parent=self,
                relief=None,
                image=(model.find('**/PaintButtonUp'), model.find('**/PaintButtonDown'), model.find('**/PaintButtonRollover'), model.find('**/PaintButtonDown')),
                scale=self.modelScale,
                pressEffect=False,
                command=self.__handleAccessoryTypeChange,
                extraArgs=[KartDNA.bodyColor])
            self.accButtonsDict = {
                KartDNA.ebType: self.eBlockAccButton,
                KartDNA.spType: self.spoilerAccButton,
                KartDNA.fwwType: self.frontAccButton,
                KartDNA.bwwType: self.rearAccButton,
                KartDNA.rimsType: self.rimAccButton,
                KartDNA.decalType: self.decalAccButton,
                KartDNA.bodyColor: self.paintAccButton}
            self.buyAccessoryButton = DirectButton(
                parent=self,
                relief=None,
                image=(model.find('**/BuyAccessoryButtonUp'), model.find('**/BuyAccessoryButtonDown'), model.find('**/BuyAccessoryButtonRollover'), model.find('**/BuyAccessoryButtonDisabled')),
                scale=self.modelScale,
                text=TTLocalizer.KartShop_BuyAccessory,
                text_pos=(0, -.57),
                text_scale=KS_TEXT_SIZE_SMALL,
                pressEffect=False,
                command=self.__handleBuyAccessory)
            if not base.cr.isPaid():

                def showTeaserPanel():
                    TeaserPanel(pageName='kartingAccessories')

                self.buyAccessoryButton['command'] = showTeaserPanel
            self.ownedAccList = base.localAvatar.getKartAccessoriesOwned()
            while -1 in self.ownedAccList:
                self.ownedAccList.remove(-1)

            self.unownedAccDict = getAccessoryDictFromOwned(self.ownedAccList)
            self.curAccType = KartDNA.ebType
            self.curAccIndex = {}
            for type in self.unownedAccDict:
                self.curAccIndex[type] = 0

            self.kartView = KartViewer(list(base.localAvatar.getKartDNA()), parent=self)
            self.kartView.setPos(model.find('**/KartViewerFrame').getPos())
            self.kartView.load(model, 'KartViewerFrame', ['rotate_right_up',
             'rotate_right_down',
             'rotate_right_roll',
             'rotate_right_down',
             (0.255, 0)], ['rotate_left_up',
             'rotate_left_down',
             'rotate_left_roll',
             'rotate_left_down',
             (-.24, 0)], (0, 0))
            self.kartView.setBounds(-0.38, 0.38, 0.044, 0.58)
            self.kartView.setBgColor(1.0, 1.0, 0.87, 1.0)
            self.initialize = True
            self.showAccessory()
            model.removeNode()
            return

        def __handleBuyAccessory(self):
            accessoryID = self.unownedAccDict[self.curAccType][self.curAccIndex[self.curAccType]]
            self.ownedAccList.append(accessoryID)
            self.unownedAccDict = getAccessoryDictFromOwned(self.ownedAccList)
            self.__handleAccessoryChange(0)
            messenger.send(self.doneEvent, [accessoryID])

        def __handleAccessoryChange(self, nDir):
            if len(self.unownedAccDict[self.curAccType]) < 1:
                self.curAccIndex[self.curAccType] = -1
            else:
                self.curAccIndex[self.curAccType] = (self.curAccIndex[self.curAccType] + nDir) % len(self.unownedAccDict[self.curAccType])
            if hasattr(self, 'accDescription'):
                self.accDescription.destroy()
                self.accCost.destroy()
            self.showAccessory()

        def __handleAccessoryTypeChange(self, type):
            self.curAccType = type
            try:
                self.accDescription.destroy()
                self.accCost.destroy()
            except:
                pass

            for b in self.accButtonsDict:
                self.accButtonsDict[b]['state'] = DGG.NORMAL

            self.accButtonsDict[self.curAccType]['state'] = DGG.DISABLED
            self.showAccessory()

        def showAccessory(self):
            self.arrowRightButton['state'] = DGG.DISABLED
            self.arrowLeftButton['state'] = DGG.DISABLED
            self.buyAccessoryButton['state'] = DGG.DISABLED
            self.accDescription = DirectButton(
                parent=self,
                relief=None,
                scale=self.modelScale,
                text='',
                text_pos=(0, -.33),
                text_scale=KS_TEXT_SIZE_SMALL,
                pressEffect=False,
                text_wordwrap=TTLocalizer.KSGaccDescriptionWordwrap,
                textMayChange=True)
            self.buyAccessoryButton.configure(text_fg=(0, 0, 0.0, 1.0))
            self.buyAccessoryButton.configure(text=TTLocalizer.KartShop_BuyAccessory)
            self.buyAccessoryButton.configure(text_scale=KS_TEXT_SIZE_SMALL)
            self.buyAccessoryButton['state'] = DGG.NORMAL
            if len(self.unownedAccDict[self.curAccType]) < 1:
                self.kartView.setDNA(None)
                self.kartView.hide()
                self.accDescription.configure(text=TTLocalizer.KartShop_NoAvailableAcc)
                self.buyAccessoryButton['state'] = DGG.DISABLED
            else:
                if self.curAccIndex[self.curAccType] + 1 < len(self.unownedAccDict[self.curAccType]):
                    self.arrowRightButton['state'] = DGG.NORMAL
                if self.curAccIndex[self.curAccType] > 0:
                    self.arrowLeftButton['state'] = DGG.NORMAL
                curDNA = None
                curDNA = list(base.localAvatar.getKartDNA())
                for d in range(len(curDNA)):
                    if d == KartDNA.bodyType or d == KartDNA.accColor or d == KartDNA.bodyColor:
                        continue
                    else:
                        curDNA[d] = -1

                curAcc = self.unownedAccDict[self.curAccType][self.curAccIndex[self.curAccType]]
                curDNA[self.curAccType] = curAcc
                self.kartView.refresh(curDNA)
                self.accDescription.configure(text=AccessoryDict[curAcc][KartInfo.name])
                cost = TTLocalizer.KartShop_Cost % AccessoryDict[curAcc][KartInfo.cost]
                self.accCost = DirectButton(
                    parent=self,
                    relief=None,
                    scale=self.modelScale,
                    text=cost,
                    text_pos=(0, -.4),
                    text_scale=KS_TEXT_SIZE_SMALL,
                    text_fg=(0, 0, 0.0, 1.0),
                    pressEffect=False,
                    textMayChange=True)
                if AccessoryDict[curAcc][KartInfo.cost] > base.localAvatar.getTickets():
                    self.buyAccessoryButton['state'] = DGG.DISABLED
                    self.buyAccessoryButton.configure(text_scale=KS_TEXT_SIZE_SMALL * 0.75)
                    self.buyAccessoryButton.configure(text=TTLocalizer.KartShop_NotEnoughTickets)
                    self.accCost.configure(text_fg=(0.95, 0, 0.0, 1.0))
            if len(base.localAvatar.getKartAccessoriesOwned()) >= KartShopGlobals.MAX_KART_ACC:
                self.buyAccessoryButton['state'] = DGG.DISABLED
                self.buyAccessoryButton.configure(text_fg=(0.95, 0, 0.0, 1.0))
                self.buyAccessoryButton.configure(text_scale=KS_TEXT_SIZE_SMALL * 0.8)
                self.buyAccessoryButton.configure(text=TTLocalizer.KartShop_FullTrunk)
            self.kartView.show()
            return

        def destroy(self):
            if self.initialize:
                try:
                    self.accDescription.destroy()
                except:
                    pass

                try:
                    self.kartView.destroy()
                except:
                    pass

                DirectFrame.destroy(self)

    class BoughtAccessoryDlg(DirectFrame):
        notify = DirectNotifyGlobal.directNotify.newCategory('KartShopGuiMgr.BoughtAccessoryDlg')

        def __init__(self, doneEvent, accID):
            self.modelScale = 1
            model = loader.loadModel('phase_6/models/gui/BoughtAccessoryPanel')
            accInfo = getAccessoryInfo(accID)
            name = accInfo[AccInfo.name]
            DirectFrame.__init__(self, relief=None, state='normal', geom=model, geom_scale=self.modelScale, frameSize=(-1, 1, -1, 1), pos=(0, 0, -0.01), text=TTLocalizer.KartShop_ConfirmBoughtTitle, text_wordwrap=26, text_scale=KS_TEXT_SIZE_SMALL, text_pos=(0, -0.28))
            self.initialiseoptions(KartShopGuiMgr.BoughtAccessoryDlg)
            self.ticketDisplay = DirectLabel(parent=self, relief=None, text=str(base.localAvatar.getTickets()), text_scale=KS_TEXT_SIZE_SMALL, text_fg=(0.95, 0.95, 0.0, 1.0), text_shadow=(0, 0, 0, 1), text_pos=(0.43, -0.5), text_font=ToontownGlobals.getSignFont())
            self.okButton = DirectButton(parent=self, relief=None, image=(model.find('**/CheckButtonUp'), model.find('**/CheckButtonDown'), model.find('**/CheckButtonRollover')), geom=model.find('**/CheckIcon'), scale=self.modelScale, pressEffect=False, command=lambda : messenger.send(doneEvent, [BTA_OPTIONS.Ok]))
            self.kartView = DirectFrame(parent=self, relief=None, geom=model.find('**/KartViewerFrame'), scale=1.0)
            bounds = self.kartView.getBounds()
            radius = (bounds[3] - bounds[2]) / 2
            xCenter = self.kartView.getCenter()[0]
            cm = CardMaker('accViewer')
            cm.setFrame(xCenter - radius, xCenter + radius, bounds[2], bounds[3])
            self.kartView['geom'] = NodePath(cm.generate())
            self.kartView.component('geom0').setColorScale(1.0, 1.0, 0.8, 1.0)
            self.kartView.component('geom0').setTransparency(True)
            accType = getAccessoryType(accID)
            texNodePath = None
            tex = None
            if accType in [KartDNA.ebType,
             KartDNA.spType,
             KartDNA.fwwType,
             KartDNA.bwwType]:
                texNodePath = getTexCardNode(accID)
                tex = loader.loadTexture('phase_6/maps/%s.jpg' % texNodePath, 'phase_6/maps/%s_a.rgb' % texNodePath)
            elif accType == KartDNA.rimsType:
                if accID == InvalidEntry:
                    texNodePath = getTexCardNode(getDefaultRim())
                else:
                    texNodePath = getTexCardNode(accID)
                tex = loader.loadTexture('phase_6/maps/%s.jpg' % texNodePath, 'phase_6/maps/%s_a.rgb' % texNodePath)
            elif accType in [KartDNA.bodyColor, KartDNA.accColor]:
                tex = loader.loadTexture('phase_6/maps/Kartmenu_paintbucket.jpg', 'phase_6/maps/Kartmenu_paintbucket_a.rgb')
                if accID == InvalidEntry:
                    self.kartView.component('geom0').setColorScale(getDefaultColor())
                else:
                    self.kartView.component('geom0').setColorScale(getAccessory(accID))
            elif accType == KartDNA.decalType:
                kartDecal = getDecalId(base.localAvatar.getKartBodyType())
                texNodePath = getTexCardNode(accID)
                tex = loader.loadTexture('phase_6/maps/%s.jpg' % texNodePath % kartDecal, 'phase_6/maps/%s_a.rgb' % texNodePath % kartDecal)
            else:
                tex = loader.loadTexture('phase_6/maps/NoAccessoryIcon3.jpg', 'phase_6/maps/NoAccessoryIcon3_a.rgb')
            tex.setMinfilter(Texture.FTLinearMipmapLinear)
            self.kartView.component('geom0').setTexture(tex, 1)
            self.initialize = True
            return

        def destroy(self):
            if self.initialize:
                DirectFrame.destroy(self)

    class ConfirmBuyAccessoryDlg(DirectFrame):
        notify = DirectNotifyGlobal.directNotify.newCategory('KartShopGuiMgr.ConfirmBuyAccessoryDlg')

        def __init__(self, doneEvent, accID):
            self.accID = accID
            self.modelScale = 1
            model = loader.loadModel('phase_6/models/gui/ConfirmBuyAccessory')
            accInfo = getAccessoryInfo(accID)
            cost = accInfo[AccInfo.cost]
            name = accInfo[AccInfo.name]
            DirectFrame.__init__(self, relief=None, state='normal', geom=model, geom_scale=self.modelScale, frameSize=(-1, 1, -1, 1), pos=(0, 0, -0.01), text=TTLocalizer.KartShop_ConfirmBuy % (name, cost), text_wordwrap=14, text_scale=KS_TEXT_SIZE_SMALL, text_pos=(0, -0.25))
            self.initialiseoptions(KartShopGuiMgr.ConfirmBuyAccessoryDlg)
            self.ticketDisplay = DirectLabel(parent=self, relief=None, text=str(base.localAvatar.getTickets()), text_scale=KS_TEXT_SIZE_SMALL, text_fg=(0.95, 0.95, 0.0, 1.0), text_shadow=(0, 0, 0, 1), text_pos=(0.43, -0.5), text_font=ToontownGlobals.getSignFont())
            self.cancelButton = DirectButton(parent=self, relief=None, image=(model.find('**/CancelButtonUp'), model.find('**/CancelButtonDown'), model.find('**/CancelButtonRollover')), geom=model.find('**/CancelIcon'), scale=self.modelScale, pressEffect=False, command=lambda : messenger.send(doneEvent, [CBA_OPTIONS.Cancel]))
            self.okButton = DirectButton(parent=self, relief=None, image=(model.find('**/CheckButtonUp'), model.find('**/CheckButtonDown'), model.find('**/CheckButtonRollover')), geom=model.find('**/CheckIcon'), scale=self.modelScale, pressEffect=False, command=lambda : messenger.send(doneEvent, [CBA_OPTIONS.BuyAccessory]))
            self.kartView = DirectFrame(parent=self, relief=None, geom=model.find('**/KartViewerFrame'), scale=1.0)
            bounds = self.kartView.getBounds()
            radius = (bounds[3] - bounds[2]) / 3
            xCenter, yCenter = self.kartView.getCenter()
            cm = CardMaker('accViewer')
            cm.setFrame(xCenter - radius, xCenter + radius, yCenter - radius, yCenter + radius)
            self.kartView['geom'] = NodePath(cm.generate())
            self.kartView.component('geom0').setColorScale(1.0, 1.0, 0.8, 1.0)
            self.kartView.component('geom0').setTransparency(True)
            accType = getAccessoryType(accID)
            texNodePath = None
            tex = None
            if accType in [KartDNA.ebType,
             KartDNA.spType,
             KartDNA.fwwType,
             KartDNA.bwwType]:
                texNodePath = getTexCardNode(accID)
                tex = loader.loadTexture('phase_6/maps/%s.jpg' % texNodePath, 'phase_6/maps/%s_a.rgb' % texNodePath)
            elif accType == KartDNA.rimsType:
                if accID == InvalidEntry:
                    texNodePath = getTexCardNode(getDefaultRim())
                else:
                    texNodePath = getTexCardNode(accID)
                tex = loader.loadTexture('phase_6/maps/%s.jpg' % texNodePath, 'phase_6/maps/%s_a.rgb' % texNodePath)
            elif accType in [KartDNA.bodyColor, KartDNA.accColor]:
                tex = loader.loadTexture('phase_6/maps/Kartmenu_paintbucket.jpg', 'phase_6/maps/Kartmenu_paintbucket_a.rgb')
                if accID == InvalidEntry:
                    self.kartView.component('geom0').setColorScale(getDefaultColor())
                else:
                    self.kartView.component('geom0').setColorScale(getAccessory(accID))
            elif accType == KartDNA.decalType:
                kartDecal = getDecalId(base.localAvatar.getKartBodyType())
                texNodePath = getTexCardNode(accID)
                tex = loader.loadTexture('phase_6/maps/%s.jpg' % texNodePath % kartDecal, 'phase_6/maps/%s_a.rgb' % texNodePath % kartDecal)
            else:
                tex = loader.loadTexture('phase_6/maps/NoAccessoryIcon3.jpg', 'phase_6/maps/NoAccessoryIcon3_a.rgb')
            tex.setMinfilter(Texture.FTLinearMipmapLinear)
            self.kartView.component('geom0').setTexture(tex, 1)
            self.initialize = True
            return

        def destroy(self):
            if self.initialize:
                DirectFrame.destroy(self)

    def __init__(self, eventDict):
        self.dialog = None
        self.dialogStack = []
        self.eventDict = eventDict
        self.dialogEventDict = {MENUS.MainMenu: ('MainMenuGuiDone', self.__handleMainMenuDlg, self.MainMenuDlg),
         MENUS.BuyKart: ('BuyKartGuiDone', self.__handleBuyKartDlg, self.BuyKartDlg),
         MENUS.BuyAccessory: ('BuyAccessoryGuiDone', self.__handleBuyAccessoryDlg, self.BuyAccessoryDlg),
         MENUS.ReturnKart: ('ReturnKartGuiDone', self.__handleReturnKartDlg, self.ReturnKartDlg),
         MENUS.ConfirmBuyKart: ('ConfirmBuyKartGuiDone', self.__handleConfirmBuyKartDlg, self.ConfirmBuyKartDlg),
         MENUS.ConfirmBuyAccessory: ('ConfirmBuyAccessoryGuiDone', self.__handleConfirmBuyAccessoryDlg, self.ConfirmBuyAccessoryDlg),
         MENUS.BoughtKart: ('BoughtKartGuiDone', self.__handleBoughtKartDlg, self.BoughtKartDlg),
         MENUS.BoughtAccessory: ('BoughtAccessoryGuiDone', self.__handleBoughtAccessoryDlg, self.BoughtAccessoryDlg),
         MENUS.TeaserPanel: ('UnpaidPurchaseAttempt', self.__handleTeaserPanelDlg, TeaserPanel)}
        self.kartID = -1
        self.accID = -1
        self.timer = ToontownTimer.ToontownTimer()
        self.timer.reparentTo(aspect2d)
        self.timer.posInTopRightCorner()
        self.timer.accept('RESET_KARTSHOP_TIMER', self.__resetTimer)
        self.timer.countdown(KartShopGlobals.KARTCLERK_TIMER, self.__timerExpired)
        self.__doDialog(MENUS.MainMenu)
        return

    def __resetTimer(self):
        if hasattr(self, 'timer') and self.timer:
            self.timer.stop()
            self.timer.countdown(KartShopGlobals.KARTCLERK_TIMER, self.__timerExpired)

    def __isActive(self, dlgName):
        for d in self.dialogStack:
            if d == dlgName:
                return True

        return False

    def __timerExpired(self):
        messenger.send(self.eventDict['guiDone'], [True])

    def destroy(self):
        self.__destroyDialog()
        self.ignoreAll()
        self.timer.destroy()
        del self.timer
        for event in list(self.dialogEventDict.values()):
            self.ignore(event)

        self.dialogEventDict = None
        return

    def __destroyDialog(self):
        if hasattr(self, 'timer'):
            self.ignoreAll()
        if self.dialog != None:
            self.dialog.destroy()
            self.dialog = None
        return

    def __removeDialog(self, dlgName = None):
        if self.dialog != None:
            if dlgName != None:
                for d in self.dialogStack:
                    if d == dlgName:
                        self.dialogStack.remove(d)

        return

    def __popDialog(self):
        if self.dialog != None:
            if dlgName != None:
                for d in self.dialogStack:
                    if d == dlgName:
                        self.dialogStack.remove(d)

            else:
                d = self.dialogStack.pop()
                event = self.dialogEventDict.get(d)
                eventType = event[0]
                self.ignore(eventType)
                if self.dialogStack:
                    self.__doDialog(self.dialogStack[-1])
        return

    def __doLastMenu(self):
        self.__doDialog(self.lastMenu)

    def __doDialog(self, dialogType):
        self.__destroyDialog()
        messenger.send('wakeup')
        event = self.dialogEventDict.get(dialogType)
        eventType = event[0]
        eventHandler = event[1]
        eventDlg = event[2]
        self.acceptOnce(eventType, eventHandler)
        if dialogType == MENUS.ConfirmBuyKart:
            self.dialog = eventDlg(eventType, self.kartID)
        elif dialogType == MENUS.BoughtKart:
            self.dialog = eventDlg(eventType, self.kartID)
        elif dialogType == MENUS.ConfirmBuyAccessory:
            self.dialog = eventDlg(eventType, self.accID)
        elif dialogType == MENUS.BoughtAccessory:
            self.dialog = eventDlg(eventType, self.accID)
        elif dialogType == MENUS.TeaserPanel:
            self.dialog = eventDlg(pageName='karting', doneFunc=self.__doLastMenu)
        else:
            self.dialog = eventDlg(eventType)
        if not dialogType == MENUS.TeaserPanel:
            self.lastMenu = dialogType

    def __handleMainMenuDlg(self, exitType, args = []):
        self.notify.debug('__handleMainMenuDlg: Handling MainMenu Dialog Selection.')
        if exitType == MM_OPTIONS.Cancel:
            messenger.send(self.eventDict['guiDone'])
        elif exitType == MM_OPTIONS.BuyKart:
            self.__doDialog(MENUS.BuyKart)
        elif exitType == MM_OPTIONS.BuyAccessory:
            self.__doDialog(MENUS.BuyAccessory)

    def __handleBoughtKartDlg(self, exitType):
        self.notify.debug('__handleBoughtKartDlg: Telling the player their purchase was successful')
        if not hasattr(base.localAvatar, 'kartPage'):
            base.localAvatar.addKartPage()
        self.kartID = -1
        self.__doDialog(MENUS.MainMenu)

    def __handleBoughtAccessoryDlg(self, exitType):
        self.notify.debug('__handleBoughtAccessoryDlg: Telling the player their purchase was successful')
        self.accID = -1
        self.__doDialog(MENUS.BuyAccessory)

    def __handleTeaserPanelDlg(self):
        self.__doDialog(MENUS.TeaserPanel)

    def __handleBuyKartDlg(self, exitType, args = []):
        self.notify.debug('__handleBuyKartDlg: Handling BuyKart Dialog Selection.')
        if exitType == BK_OPTIONS.Cancel:
            self.__doDialog(MENUS.MainMenu)
        else:
            self.kartID = exitType
            if base.localAvatar.hasKart():
                self.__doDialog(MENUS.ReturnKart)
            else:
                self.__doDialog(MENUS.ConfirmBuyKart)

    def __handleBuyAccessoryDlg(self, exitType, args = []):
        self.notify.debug('__handleBuyKartDlg: Handling BuyKart Dialog Selection.')
        if exitType == BA_OPTIONS.Cancel:
            self.__doDialog(MENUS.MainMenu)
        else:
            self.accID = exitType
            self.__doDialog(MENUS.ConfirmBuyAccessory)

    def __handleReturnKartDlg(self, exitType, args = []):
        self.notify.debug('__handleReturnKartDlg: Handling ReturnKart Dialog Selection.')
        if exitType == RK_OPTIONS.Cancel:
            self.__doDialog(MENUS.BuyKart)
        elif exitType == RK_OPTIONS.ReturnKart:
            self.__doDialog(MENUS.ConfirmBuyKart)

    def __handleConfirmBuyAccessoryDlg(self, exitType, args = []):
        self.notify.debug('__handleConfirmBuyAccessoryDlg: Handling ConfirmBuyAccessory Dialog Selection.')
        if exitType == CBA_OPTIONS.Cancel:
            self.__doDialog(MENUS.BuyAccessory)
            self.accID = -1
        elif exitType == CBA_OPTIONS.BuyAccessory:
            if self.accID != -1:
                messenger.send(self.eventDict['buyAccessory'], [self.accID])
            oldTickets = base.localAvatar.getTickets()
            accInfo = getAccessoryInfo(self.accID)
            cost = accInfo[AccInfo.cost]
            base.localAvatar.setTickets(oldTickets - cost)
            accList = base.localAvatar.getKartAccessoriesOwned()
            accList.append(self.accID)
            base.localAvatar.setKartAccessoriesOwned(accList)
            self.accID = -1
            self.__doDialog(MENUS.BuyAccessory)

    def __handleConfirmBuyKartDlg(self, exitType, args = []):
        self.notify.debug('__handleConfirmBuyKartDlg: Handling ConfirmBuyKart Dialog Selection.')
        if exitType == CBK_OPTIONS.Cancel:
            self.__doDialog(MENUS.BuyKart)
            self.kartID = -1
        elif exitType == CBK_OPTIONS.BuyKart:
            if self.kartID != -1:
                messenger.send(self.eventDict['buyKart'], [self.kartID])
            self.__doDialog(MENUS.BoughtKart)
        if __name__ == '__main__':

            class Main(DirectObject.DirectObject):

                def __init__(self):
                    self.acceptOnce('1', self.__popupKartShopGui)
                    self.accept(KartShopGlobals.EVENTDICT['buyAccessory'], self.__handleBuyAccessory)
                    self.accept(KartShopGlobals.EVENTDICT['buyKart'], self.__handleBuyKart)

                def __popupKartShopGui(self):
                    if not hasattr(self, 'kartShopGui') or self.kartShopGui == None:
                        self.acceptOnce(KartShopGlobals.EVENTDICT['guiDone'], self.__handleGuiDone)
                        self.kartShopGui = KartShopGuiMgr(KartShopGlobals.EVENTDICT)
                    return

                def __handleGuiDone(self, args = []):
                    if hasattr(self, 'kartShopGui') and self.kartShopGui != None:
                        self.ignoreAll()
                        self.kartShopGui.destroy()
                        del self.kartShopGui
                        self.acceptOnce('1', self.__popupKartShopGui)
                    return

                def __handleBuyAccessory(self, accID = -1):
                    requestAddOwnedAccessory(self, accID)

                def __handleBuyKart(self, kartID = -1):
                    pass

            m = Main()
            run()
