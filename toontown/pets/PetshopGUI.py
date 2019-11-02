from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.directnotify import DirectNotifyGlobal
from direct.showbase.DirectObject import DirectObject
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownTimer
from direct.task import Task
from otp.namepanel import NameTumbler
from otp.otpbase import OTPGlobals
from otp.otpbase import OTPLocalizer
from toontown.fishing import FishSellGUI
from toontown.pets import Pet, PetConstants
from toontown.pets import PetDNA
from toontown.pets import PetUtil
from toontown.pets import PetDetail
from toontown.pets import PetTraits
from toontown.pets import PetNameGenerator
from toontown.hood import ZoneUtil
import string
import random
Dialog_MainMenu = 0
Dialog_AdoptPet = 1
Dialog_ChoosePet = 2
Dialog_ReturnPet = 3
Dialog_SellFish = 4
Dialog_NamePicker = 5
Dialog_GoHome = 6
disabledImageColor = Vec4(0.6, 0.6, 0.6, 1)
text0Color = Vec4(0.65, 0, 0.87, 1)
text1Color = Vec4(0.65, 0, 0.87, 1)
text2Color = Vec4(1, 1, 0.5, 1)
text3Color = Vec4(0.4, 0.4, 0.4, 1)

class PetshopGUI(DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('PetshopGui')

    class GoHomeDlg(DirectFrame):
        notify = DirectNotifyGlobal.directNotify.newCategory('GoHomeDlg')

        def __init__(self, doneEvent):
            DirectFrame.__init__(self, pos=(0.0, 0.0, 0.0), image_color=ToontownGlobals.GlobalDialogColor, image_scale=(1.0, 1.0, 0.6), text='', text_wordwrap=13.5, text_scale=0.06, text_pos=(0.0, 0.13))
            self['image'] = DGG.getDefaultDialogGeom()
            self['text'] = TTLocalizer.PetshopGoHomeText
            buttons = loader.loadModel('phase_3/models/gui/dialog_box_buttons_gui')
            gui = loader.loadModel('phase_3.5/models/gui/avatar_panel_gui')
            self.bYes = DirectButton(self, image=(buttons.find('**/ChtBx_OKBtn_UP'), buttons.find('**/ChtBx_OKBtn_DN'), buttons.find('**/ChtBx_OKBtn_Rllvr')), relief=None, text=TTLocalizer.TutorialYes, text_scale=0.05, text_pos=(0.0, -0.1), pos=(-0.15, 0.0, -0.1), command=lambda : messenger.send(doneEvent, [1]))
            self.bNo = DirectButton(self, image=(buttons.find('**/CloseBtn_UP'), buttons.find('**/CloseBtn_DN'), buttons.find('**/CloseBtn_Rllvr')), relief=None, text=TTLocalizer.TutorialNo, text_scale=0.05, text_pos=(0.0, -0.1), pos=(0.15, 0.0, -0.1), command=lambda : messenger.send(doneEvent, [0]))
            buttons.removeNode()
            gui.removeNode()
            return

    class NamePicker(DirectFrame):
        notify = DirectNotifyGlobal.directNotify.newCategory('PetshopGUI.NamePicker')

        def __init__(self, doneEvent, petSeed, gender):
            zoneId = ZoneUtil.getCanonicalSafeZoneId(base.localAvatar.getZoneId())
            name, dna, traitSeed = PetUtil.getPetInfoFromSeed(petSeed, zoneId)
            self.gui = loader.loadModel('phase_4/models/gui/PetNamePanel')
            self.guiScale = 0.09
            DirectFrame.__init__(self, relief=None, geom=self.gui, geom_scale=self.guiScale, state='normal', frameSize=(-1, 1, -1, 1))
            self.initialiseoptions(PetshopGUI.NamePicker)
            self.petView = self.attachNewNode('petView')
            self.petView.setPos(-0.21, 0, -0.04)
            self.petModel = Pet.Pet(forGui=1)
            self.petModel.setDNA(dna)
            self.petModel.fitAndCenterHead(0.435, forGui=1)
            self.petModel.reparentTo(self.petView)
            self.petModel.setH(225)
            self.petModel.enterNeutralHappy()
            self.ng = PetNameGenerator.PetNameGenerator()
            if gender == 1:
                self.allNames = self.ng.boyFirsts
            else:
                self.allNames = self.ng.girlFirsts
            self.allNames += self.ng.neutralFirsts
            self.allNames.sort()
            self.checkNames()
            self.letters = []
            for name in self.allNames:
                if name[0:TTLocalizer.PGUIcharLength] not in self.letters:
                    self.letters.append(name[0:TTLocalizer.PGUIcharLength])

            self.curLetter = self.letters[0]
            self.curNames = []
            self.curName = ''
            self.alphabetList = self.makeScrollList(self.gui, (-0.012, 0, -0.075), (1, 0.8, 0.8, 1), self.letters, self.makeLabel, [TextNode.ACenter, 'alphabet'], 6)
            self.nameList = None
            self.rebuildNameList()
            self.randomButton = DirectButton(parent=self, relief=None, image=(self.gui.find('**/RandomUpButton'), self.gui.find('**/RandomDownButton'), self.gui.find('**/RandomRolloverButton')), scale=self.guiScale, text=TTLocalizer.RandomButton, text_pos=(-0.8, -5.7), text_scale=0.8, text_fg=text2Color, pressEffect=False, command=self.randomName)
            self.nameResult = DirectLabel(parent=self, relief=None, scale=self.guiScale, text='', text_align=TextNode.ACenter, text_pos=(-1.85, 2.6), text_fg=text0Color, text_scale=0.6, text_wordwrap=8)
            self.submitButton = DirectButton(parent=self, relief=None, image=(self.gui.find('**/SubmitUpButton'), self.gui.find('**/SubmitDownButton'), self.gui.find('**/SubmitRolloverButton')), scale=self.guiScale, text=TTLocalizer.PetshopAdopt, text_pos=(3.3, -5.7), text_scale=TTLocalizer.PGUIsubmitButton, text_fg=text0Color, pressEffect=False, command=lambda : messenger.send(doneEvent, [self.ng.returnUniqueID(self.curName)]))
            model = loader.loadModel('phase_4/models/gui/PetShopInterface')
            modelScale = 0.1
            cancelImageList = (model.find('**/CancelButtonUp'), model.find('**/CancelButtonDown'), model.find('**/CancelButtonRollover'))
            cancelIcon = model.find('**/CancelIcon')
            self.cancelButton = DirectButton(parent=self, relief=None, pos=(-0.04, 0, -0.47), image=cancelImageList, geom=cancelIcon, scale=modelScale, pressEffect=False, command=lambda : messenger.send(doneEvent, [-1]))
            self.randomName()
            return

        def checkNames(self):
            if __dev__:
                for name in self.allNames:
                    if not name.replace(' ', '').isalpha():
                        self.notify.warning('Bad name:%s' % name)

        def destroy(self):
            self.petModel.delete()
            DirectFrame.destroy(self)

        def rebuildNameList(self):
            self.curNames = []
            for name in self.allNames:
                if name[0:TTLocalizer.PGUIcharLength] == self.curLetter:
                    self.curNames += [name]

            if self.nameList:
                self.nameList.destroy()
            self.nameList = self.makeScrollList(self.gui, (0.277, 0, -0.075), (1, 0.8, 0.8, 1), self.curNames, self.makeLabel, [TextNode.ACenter, 'name'], 5)

        def updateNameText(self):
            self.nameResult['text'] = self.curName

        def nameClickedOn(self, listType, index):
            if listType == 'alphabet':
                self.curLetter = self.letters[index]
                self.rebuildNameList()
            elif listType == 'name':
                self.curName = self.curNames[index]
                self.updateNameText()

        def makeLabel(self, te, index, others):
            alig = others[0]
            listName = others[1]
            if alig == TextNode.ARight:
                newpos = (0.44, 0, 0)
            elif alig == TextNode.ALeft:
                newpos = (0, 0, 0)
            else:
                newpos = (0.2, 0, 0)
            df = DirectButton(parent=self, state='normal', relief=None, text=te, text_scale=0.1, text_pos=(0.2, 0, 0), text_align=alig, textMayChange=0, command=lambda : self.nameClickedOn(listName, index))
            return df

        def makeScrollList(self, gui, ipos, mcolor, nitems, nitemMakeFunction, nitemMakeExtraArgs, nVisibleItems):
            decScale = self.guiScale / 0.44
            incScale = (decScale, decScale, -decScale)
            it = nitems[:]
            listType = nitemMakeExtraArgs[1]
            if listType == 'alphabet':
                arrowList = (gui.find('**/ArrowSmUpButton'),
                 gui.find('**/ArrowSmUpRollover'),
                 gui.find('**/ArrowSmUpRollover'),
                 gui.find('**/ArrowSmUpButton'))
                fHeight = 0.09
            elif listType == 'name':
                arrowList = (gui.find('**/ArrowUpBigButton'),
                 gui.find('**/ArrowUpBigRollover'),
                 gui.find('**/ArrowUpBigRollover'),
                 gui.find('**/ArrowUpBigButton'))
                fHeight = 0.119
            ds = DirectScrolledList(parent=self, items=it, itemMakeFunction=nitemMakeFunction, itemMakeExtraArgs=nitemMakeExtraArgs, relief=None, command=None, pos=ipos, scale=0.44, incButton_image=arrowList, incButton_image_pos=(1.015, 0, 3.32), incButton_relief=None, incButton_scale=incScale, incButton_image3_color=Vec4(0.4, 0.4, 0.4, 1), decButton_image=arrowList, decButton_image_pos=(1.015, 0, 1.11), decButton_relief=None, decButton_scale=decScale, decButton_image3_color=Vec4(0.4, 0.4, 0.4, 1), numItemsVisible=nVisibleItems, forceHeight=fHeight)
            return ds

        def randomName(self):
            numNames = len(self.allNames)
            self.curName = self.allNames[random.randrange(numNames)]
            self.curLetter = self.curName[0:TTLocalizer.PGUIcharLength]
            self.rebuildNameList()
            self.updateNameText()
            self.alphabetList.scrollTo(self.letters.index(self.curLetter))
            self.nameList.scrollTo(self.curNames.index(self.curName))

    class MainMenuDlg(DirectFrame):
        notify = DirectNotifyGlobal.directNotify.newCategory('PetshopGUI.MainMenuDlg')

        def __init__(self, doneEvent):
            model = loader.loadModel('phase_4/models/gui/AdoptReturnSell')
            modelPos = (0, 0, -0.3)
            modelScale = 0.055
            DirectFrame.__init__(self, relief=None, state='normal', geom=model, geom_scale=(modelScale, modelScale, modelScale), pos=modelPos, frameSize=(-1, 1, -1, 1))
            self.initialiseoptions(PetshopGUI.MainMenuDlg)
            textScale = TTLocalizer.PGUItextScale
            sellFishImageList = (model.find('**/SellButtonUp'),
             model.find('**/SellButtonDown'),
             model.find('**/SellButtonRollover'),
             model.find('**/SellButtonDown'))
            fishLogoImageList = model.find('**/Fish')
            cancelImageList = (model.find('**/CancelButtonUp'), model.find('**/cancelButtonDown'), model.find('**/CancelButtonRollover'))
            XImageList = model.find('**/CancelIcon')
            adoptImageList = (model.find('**/AdoptButtonUp'), model.find('**/AdoptButtonDown'), model.find('**/AdoptButtonRollover'))
            pawLogoAdoptImageList = model.find('**/PawPink')
            returnImageList = (model.find('**/ReturnButtonUp'),
             model.find('**/ReturnButtonDown'),
             model.find('**/ReturnButtonRollover'),
             model.find('**/ReturnButtonDown'))
            pawLogoReturnImageList = model.find('**/PawYellow')
            self.cancelButton = DirectButton(parent=self, relief=None, scale=(modelScale, modelScale, modelScale), geom=XImageList, image=cancelImageList, text=('', TTLocalizer.PetshopCancel), text_pos=TTLocalizer.PGUIcancelButtonPos, text_scale=0.8, pressEffect=False, command=lambda : messenger.send(doneEvent, [0]))
            self.sellFishButton = DirectButton(parent=self, relief=None, image=sellFishImageList, image3_color=disabledImageColor, geom=fishLogoImageList, scale=(modelScale, modelScale, modelScale), text=TTLocalizer.PetshopSell, text_scale=textScale, text_pos=(0, 6), text0_fg=text2Color, text1_fg=text2Color, text2_fg=text0Color, text3_fg=text3Color, pressEffect=False, command=lambda : messenger.send(doneEvent, [1]))
            fishValue = base.localAvatar.fishTank.getTotalValue()
            if fishValue == 0:
                self.sellFishButton['state'] = DGG.DISABLED
            self.adoptPetButton = DirectButton(parent=self, relief=None, image=adoptImageList, geom=pawLogoAdoptImageList, scale=(modelScale, modelScale, modelScale), text=TTLocalizer.PetshopAdoptAPet, text_scale=textScale, text_pos=(0, 12.5), text0_fg=text0Color, text1_fg=text1Color, text2_fg=text2Color, text3_fg=text3Color, pressEffect=False, command=lambda : messenger.send(doneEvent, [2]))
            self.returnPetButton = DirectButton(parent=self, relief=None, image=returnImageList, geom=pawLogoReturnImageList, image3_color=disabledImageColor, scale=(modelScale, modelScale, modelScale), text=TTLocalizer.PetshopReturnPet, text_scale=textScale, text_pos=(-0.6, 9.2), text0_fg=text2Color, text1_fg=text2Color, text2_fg=text0Color, text3_fg=text3Color, pressEffect=False, command=lambda : messenger.send(doneEvent, [3]))
            if not base.localAvatar.hasPet():
                self.returnPetButton['state'] = DGG.DISABLED
            model.removeNode()
            return

    class AdoptPetDlg(DirectFrame):
        notify = DirectNotifyGlobal.directNotify.newCategory('PetshopGUI.AdoptPetDlg')

        def __init__(self, doneEvent, petSeed, petNameIndex):
            zoneId = ZoneUtil.getCanonicalSafeZoneId(base.localAvatar.getZoneId())
            name, dna, traitSeed = PetUtil.getPetInfoFromSeed(petSeed, zoneId)
            name = PetNameGenerator.PetNameGenerator().getName(petNameIndex)
            cost = PetUtil.getPetCostFromSeed(petSeed, zoneId)
            model = loader.loadModel('phase_4/models/gui/AdoptPet')
            modelPos = (0, 0, -0.3)
            modelScale = 0.055
            DirectFrame.__init__(self, relief=None, state='normal', geom=model, geom_color=ToontownGlobals.GlobalDialogColor, geom_scale=modelScale, frameSize=(-1, 1, -1, 1), pos=modelPos, text=TTLocalizer.PetshopAdoptConfirm % (name, cost), text_wordwrap=12, text_scale=0.05, text_pos=(0, 0.55), text_fg=text0Color)
            self.initialiseoptions(PetshopGUI.AdoptPetDlg)
            self.petView = self.attachNewNode('petView')
            self.petView.setPos(-0.13, 0, 0.8)
            self.petModel = Pet.Pet(forGui=1)
            self.petModel.setDNA(dna)
            self.petModel.fitAndCenterHead(0.395, forGui=1)
            self.petModel.reparentTo(self.petView)
            self.petModel.setH(130)
            self.petModel.enterNeutralHappy()
            self.moneyDisplay = DirectLabel(parent=self, relief=None, text=str(base.localAvatar.getTotalMoney()), text_scale=0.075, text_fg=(0.95, 0.95, 0, 1), text_shadow=(0, 0, 0, 1), text_pos=(0.225, 0.33), text_font=ToontownGlobals.getSignFont())
            self.accept(localAvatar.uniqueName('moneyChange'), self.__moneyChange)
            self.accept(localAvatar.uniqueName('bankMoneyChange'), self.__moneyChange)
            okImageList = (model.find('**/CheckButtonUp'), model.find('**/CheckButtonDown'), model.find('**/CheckButtonRollover'))
            cancelImageList = (model.find('**/CancelButtonUp'), model.find('**/CancelButtonDown'), model.find('**/CancelRollover'))
            cancelIcon = model.find('**/CancelIcon')
            checkIcon = model.find('**/CheckIcon')
            self.cancelButton = DirectButton(parent=self, relief=None, image=cancelImageList, geom=cancelIcon, scale=modelScale, text=('', TTLocalizer.PetshopGoBack), text_pos=(-5.8, 4.4), text_scale=0.7, pressEffect=False, command=lambda : messenger.send(doneEvent, [0]))
            self.okButton = DirectButton(parent=self, relief=None, image=okImageList, geom=checkIcon, scale=modelScale, text=('', TTLocalizer.PetshopAdopt), text_pos=(5.8, 4.4), text_scale=0.7, pressEffect=False, command=lambda : messenger.send(doneEvent, [1]))
            model.removeNode()
            return

        def destroy(self):
            self.ignore(localAvatar.uniqueName('moneyChange'))
            self.ignore(localAvatar.uniqueName('bankMoneyChange'))
            self.petModel.delete()
            DirectFrame.destroy(self)

        def __moneyChange(self, money):
            self.moneyDisplay['text'] = str(base.localAvatar.getTotalMoney())

    class ReturnPetDlg(DirectFrame):
        notify = DirectNotifyGlobal.directNotify.newCategory('PetshopGUI.ReturnPetDlg')

        def __init__(self, doneEvent):

            def showDialog(avatar):
                model = loader.loadModel('phase_4/models/gui/ReturnPet')
                modelPos = (0, 0, -0.3)
                modelScale = (0.055, 0.055, 0.055)
                base.r = self
                DirectFrame.__init__(self, relief=None, state='normal', geom=model, geom_scale=modelScale, frameSize=(-1, 1, -1, 1), pos=modelPos, text=TTLocalizer.PetshopReturnConfirm % avatar.getName(), text_wordwrap=12, text_scale=TTLocalizer.PGUIreturnConfirm, text_pos=(0, 0.45), text_fg=text2Color)
                self.initialiseoptions(PetshopGUI.ReturnPetDlg)
                okImageList = (model.find('**/CheckButtonUp'), model.find('**/CheckButtonDown'), model.find('**/CheckRollover'))
                cancelImageList = (model.find('**/CancelButtonUp'), model.find('**/CancelButtonDown'), model.find('**/CancelRollover'))
                cancelIcon = model.find('**/CancelIcon')
                checkIcon = model.find('**/CheckIcon')
                self.cancelButton = DirectButton(parent=self, relief=None, image=cancelImageList, geom=cancelIcon, scale=modelScale, text=('', TTLocalizer.PetshopGoBack), text_pos=(-5.8, 4.4), text_scale=0.7, pressEffect=False, command=lambda : messenger.send(doneEvent, [0]))
                self.okButton = DirectButton(parent=self, relief=None, image=okImageList, geom=checkIcon, scale=modelScale, text=('', TTLocalizer.PetshopReturn), text_pos=(5.8, 4.4), text_scale=0.7, pressEffect=False, command=lambda : messenger.send(doneEvent, [1]))
                self.petView = self.attachNewNode('petView')
                self.petView.setPos(-0.15, 0, 0.8)
                self.petModel = Pet.Pet(forGui=1)
                self.petModel.setDNA(avatar.getDNA())
                self.petModel.fitAndCenterHead(0.395, forGui=1)
                self.petModel.reparentTo(self.petView)
                self.petModel.setH(130)
                self.petModel.enterNeutralSad()
                model.removeNode()
                self.initialized = True
                return

            self.initialized = False
            self.petPanel = PetDetail.PetDetail(base.localAvatar.getPetId(), showDialog)

        def destroy(self):
            if self.initialized:
                self.petPanel.avatar.disable()
                self.petPanel.avatar.delete()
                self.petPanel.avatar = None
                self.PetPanel = None
                self.petModel.delete()
                DirectFrame.destroy(self)
            return

    class ChoosePetDlg(DirectFrame):
        notify = DirectNotifyGlobal.directNotify.newCategory('PetshopGUI.ChoosePetDlg')

        def __init__(self, doneEvent, petSeeds):
            model = loader.loadModel('phase_4/models/gui/PetShopInterface')
            modelPos = (0, 0, -0.9)
            modelScale = (0.185, 0.185, 0.185)
            DirectFrame.__init__(self, relief=None, state='normal', geom=model, geom_scale=modelScale, frameSize=(-1, 1, -1, 1), pos=modelPos, text=TTLocalizer.PetshopChooserTitle, text_wordwrap=26, text_scale=TTLocalizer.PGUIchooserTitle, text_fg=Vec4(0.36, 0.94, 0.93, 1), text_pos=(0, 1.58))
            self.initialiseoptions(PetshopGUI.ChoosePetDlg)
            adoptImageList = (model.find('**/AdoptButtonUp'),
             model.find('**/AdoptButtonDown'),
             model.find('**/AdoptButtonRollover'),
             model.find('**/AdoptButtonRollover'))
            cancelImageList = (model.find('**/CancelButtonUp'), model.find('**/CancelButtonDown'), model.find('**/CancelButtonRollover'))
            cancelIcon = model.find('**/CancelIcon')
            pawLImageList = (model.find('**/Paw1Up'), model.find('**/Paw1Down'), model.find('**/Paw1Rollover'))
            pawLArrowImageList = model.find('**/Arrow1')
            pawRImageList = (model.find('**/Paw2Up'), model.find('**/Paw2Down'), model.find('**/Paw2Rollover'))
            pawRArrowImageList = model.find('**/Arrow2')
            self.cancelButton = DirectButton(parent=self, relief=None, image=cancelImageList, geom=cancelIcon, scale=modelScale, pressEffect=False, command=lambda : messenger.send(doneEvent, [-1]))
            self.pawLButton = DirectButton(parent=self, relief=None, image=pawLImageList, geom=pawLArrowImageList, scale=modelScale, pressEffect=False, command=lambda : self.__handlePetChange(-1))
            self.pawRButton = DirectButton(parent=self, relief=None, image=pawRImageList, geom=pawRArrowImageList, scale=modelScale, pressEffect=False, command=lambda : self.__handlePetChange(1))
            self.okButton = DirectButton(parent=self, relief=None, image=adoptImageList, image3_color=disabledImageColor, scale=modelScale, text=TTLocalizer.PetshopAdopt, text_scale=TTLocalizer.PGUIokButton, text_pos=TTLocalizer.PGUIokButtonPos, text0_fg=text0Color, text1_fg=text1Color, text2_fg=text2Color, text3_fg=text3Color, pressEffect=False, command=lambda : messenger.send(doneEvent, [self.curPet]))
            self.moneyDisplay = DirectLabel(parent=self, relief=None, text=str(base.localAvatar.getTotalMoney()), text_scale=0.1, text_fg=(0.95, 0.95, 0, 1), text_shadow=(0, 0, 0, 1), text_pos=(0.34, 0.12), text_font=ToontownGlobals.getSignFont())
            self.accept(localAvatar.uniqueName('moneyChange'), self.__moneyChange)
            self.accept(localAvatar.uniqueName('bankMoneyChange'), self.__moneyChange)
            self.petView = self.attachNewNode('petView')
            self.petView.setPos(-0.05, 0, 1.15)
            model.removeNode()
            self.petSeeds = petSeeds
            self.makePetList()
            self.showPet()
            return

        def makePetList(self):
            self.numPets = len(self.petSeeds)
            self.curPet = 0
            self.petDNA = []
            self.petName = []
            self.petDesc = []
            self.petCost = []
            for i in range(self.numPets):
                random.seed(self.petSeeds[i])
                zoneId = ZoneUtil.getCanonicalSafeZoneId(base.localAvatar.getZoneId())
                name, dna, traitSeed = PetUtil.getPetInfoFromSeed(self.petSeeds[i], zoneId)
                cost = PetUtil.getPetCostFromSeed(self.petSeeds[i], zoneId)
                traits = PetTraits.PetTraits(traitSeed, zoneId)
                traitList = traits.getExtremeTraitDescriptions()
                numGenders = len(PetDNA.PetGenders)
                gender = i % numGenders
                PetDNA.setGender(dna, gender)
                self.petDNA.append(dna)
                self.petName.append(TTLocalizer.PetshopUnknownName)
                descList = []
                descList.append(TTLocalizer.PetshopDescGender % PetDNA.getGenderString(gender=gender))
                if traitList:
                    descList.append(TTLocalizer.PetshopDescTrait % traitList[0])
                else:
                    descList.append(TTLocalizer.PetshopDescTrait % TTLocalizer.PetshopDescStandard)
                traitList.extend(['',
                 '',
                 '',
                 ''])
                for trait in traitList[1:4]:
                    descList.append('\t%s' % trait)

                descList.append(TTLocalizer.PetshopDescCost % cost)
                self.petDesc.append(string.join(descList, '\n'))
                self.petCost.append(cost)

        def destroy(self):
            self.ignore(localAvatar.uniqueName('moneyChange'))
            self.ignore(localAvatar.uniqueName('bankMoneyChange'))
            self.petModel.delete()
            DirectFrame.destroy(self)

        def __handlePetChange(self, nDir):
            self.curPet = (self.curPet + nDir) % self.numPets
            self.nameLabel.destroy()
            self.petModel.delete()
            self.descLabel.destroy()
            self.showPet()

        def showPet(self):
            self.nameLabel = DirectLabel(parent=self, pos=(0, 0, 1.35), relief=None, text=self.petName[self.curPet], text_fg=Vec4(0.45, 0, 0.61, 1), text_pos=(0, 0), text_scale=0.08, text_shadow=(1, 1, 1, 1))
            self.petModel = Pet.Pet(forGui=1)
            self.petModel.setDNA(self.petDNA[self.curPet])
            self.petModel.fitAndCenterHead(0.57, forGui=1)
            self.petModel.reparentTo(self.petView)
            self.petModel.setH(130)
            self.petModel.enterNeutralHappy()
            self.descLabel = DirectLabel(parent=self, pos=(-0.4, 0, 0.72), relief=None, scale=0.05, text=self.petDesc[self.curPet], text_align=TextNode.ALeft, text_wordwrap=TTLocalizer.PGUIwordwrap, text_scale=TTLocalizer.PGUIdescLabel)
            if self.petCost[self.curPet] > base.localAvatar.getTotalMoney():
                self.okButton['state'] = DGG.DISABLED
            else:
                self.okButton['state'] = DGG.NORMAL
            return

        def __moneyChange(self, money):
            self.moneyDisplay['text'] = str(base.localAvatar.getTotalMoney())

    def __init__(self, eventDict, petSeeds):
        self.eventDict = eventDict
        self.mainMenuDoneEvent = 'MainMenuGuiDone'
        self.adoptPetDoneEvent = 'AdoptPetGuiDone'
        self.returnPetDoneEvent = 'ReturnPetGuiDone'
        self.petChooserDoneEvent = 'PetChooserGuiDone'
        self.fishGuiDoneEvent = 'MyFishGuiDone'
        self.namePickerDoneEvent = 'NamePickerGuiDone'
        self.goHomeDlgDoneEvent = 'GoHomeDlgDone'
        self.dialog = None
        self.dialogStack = []
        self.petSeeds = petSeeds
        self.timer = ToontownTimer.ToontownTimer()
        self.timer.reparentTo(aspect2d)
        self.timer.posInTopRightCorner()
        self.timer.countdown(PetConstants.PETCLERK_TIMER, self.__timerExpired)
        self.doDialog(Dialog_MainMenu)
        return

    def __timerExpired(self):
        messenger.send(self.eventDict['guiDone'], [True])

    def destroy(self):
        self.destroyDialog()
        self.timer.destroy()
        del self.timer
        self.ignore(self.mainMenuDoneEvent)
        self.ignore(self.adoptPetDoneEvent)
        self.ignore(self.returnPetDoneEvent)
        self.ignore(self.petChooserDoneEvent)
        self.ignore(self.fishGuiDoneEvent)
        self.ignore(self.namePickerDoneEvent)
        self.ignore(self.goHomeDlgDoneEvent)

    def destroyDialog(self):
        if self.dialog != None:
            self.dialog.destroy()
            self.dialog = None
        return

    def popDialog(self):
        self.dialogStack.pop()
        self.doDialog(self.dialogStack.pop())

    def doDialog(self, nDialog):
        self.destroyDialog()
        self.dialogStack.append(nDialog)
        if nDialog == Dialog_MainMenu:
            self.acceptOnce(self.mainMenuDoneEvent, self.__handleMainMenuDlg)
            self.dialog = self.MainMenuDlg(self.mainMenuDoneEvent)
        elif nDialog == Dialog_AdoptPet:
            self.acceptOnce(self.adoptPetDoneEvent, self.__handleAdoptPetDlg)
            self.dialog = self.AdoptPetDlg(self.adoptPetDoneEvent, self.petSeeds[self.adoptPetNum], self.adoptPetNameIndex)
        elif nDialog == Dialog_ChoosePet:
            self.acceptOnce(self.petChooserDoneEvent, self.__handleChoosePetDlg)
            self.dialog = self.ChoosePetDlg(self.petChooserDoneEvent, self.petSeeds)
        elif nDialog == Dialog_ReturnPet:
            self.acceptOnce(self.returnPetDoneEvent, self.__handleReturnPetDlg)
            self.dialog = self.ReturnPetDlg(self.returnPetDoneEvent)
        elif nDialog == Dialog_SellFish:
            self.acceptOnce(self.fishGuiDoneEvent, self.__handleFishSellDlg)
            self.dialog = FishSellGUI.FishSellGUI(self.fishGuiDoneEvent)
        elif nDialog == Dialog_NamePicker:
            self.acceptOnce(self.namePickerDoneEvent, self.__handleNamePickerDlg)
            self.dialog = self.NamePicker(self.namePickerDoneEvent, self.petSeeds[self.adoptPetNum], gender=self.adoptPetNum % 2)
        elif nDialog == Dialog_GoHome:
            self.acceptOnce(self.goHomeDlgDoneEvent, self.__handleGoHomeDlg)
            self.dialog = self.GoHomeDlg(self.goHomeDlgDoneEvent)

    def __handleMainMenuDlg(self, exitVal):
        if exitVal == 0:
            messenger.send(self.eventDict['guiDone'])
        elif exitVal == 1:
            self.doDialog(Dialog_SellFish)
        elif exitVal == 2:
            self.doDialog(Dialog_ChoosePet)
        elif exitVal == 3:
            self.doDialog(Dialog_ReturnPet)

    def __handleFishSellDlg(self, exitVal):
        if exitVal == 0:
            self.popDialog()
        elif exitVal == 1:
            self.destroyDialog()
            messenger.send(self.eventDict['fishSold'])

    def __handleChoosePetDlg(self, exitVal):
        if exitVal == -1:
            self.popDialog()
        else:
            self.adoptPetNum = exitVal
            self.doDialog(Dialog_NamePicker)

    def __handleNamePickerDlg(self, exitVal):
        if exitVal == -1:
            self.popDialog()
        else:
            self.adoptPetNameIndex = exitVal
            if base.localAvatar.hasPet():
                self.doDialog(Dialog_ReturnPet)
            else:
                self.doDialog(Dialog_AdoptPet)

    def __handleAdoptPetDlg(self, exitVal):
        if exitVal == 0:
            self.popDialog()
        elif exitVal == 1:
            self.destroyDialog()
            messenger.send(self.eventDict['petAdopted'], [self.adoptPetNum, self.adoptPetNameIndex])
            messenger.send(self.eventDict['guiDone'])

    def __handleGoHomeDlg(self, exitVal):
        if exitVal == 0:
            messenger.send(self.eventDict['guiDone'])
        elif exitVal == 1:
            messenger.send(self.eventDict['guiDone'])
            place = base.cr.playGame.getPlace()
            if place == None:
                self.notify.warning('Tried to go home, but place is None.')
                return
            place.goHomeNow(base.localAvatar.lastHood)
        return

    def __handleReturnPetDlg(self, exitVal):
        if exitVal == 0:
            self.popDialog()
        elif exitVal == 1:
            if self.dialogStack[len(self.dialogStack) - 2] == Dialog_NamePicker:
                self.doDialog(Dialog_AdoptPet)
            else:
                self.destroyDialog()
                messenger.send(self.eventDict['petReturned'])
                messenger.send(self.eventDict['guiDone'])
