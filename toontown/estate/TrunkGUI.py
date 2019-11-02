from direct.showbase.PythonUtil import Functor
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.distributed import ClockDelta
from direct.fsm import StateData
from direct.task.Task import Task
import ClosetGlobals
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals
from toontown.toontowngui import TTDialog
from toontown.toon import ToonDNA
from toontown.makeatoon.MakeAToonGlobals import *
from toontown.makeatoon import ShuffleButton

class TrunkGUI(StateData.StateData):
    notify = directNotify.newCategory('TrunkGUI')

    def __init__(self, isOwner, doneEvent, cancelEvent, swapHatEvent, swapGlassesEvent, swapBackpackEvent, swapShoesEvent, deleteEvent, hatList = None, glassesList = None, backpackList = None, shoesList = None):
        StateData.StateData.__init__(self, doneEvent)
        self.toon = None
        self.hatList = hatList
        self.glassesList = glassesList
        self.backpackList = backpackList
        self.shoesList = shoesList
        self.isOwner = isOwner
        self.swapHatEvent = swapHatEvent
        self.swapGlassesEvent = swapGlassesEvent
        self.swapBackpackEvent = swapBackpackEvent
        self.swapShoesEvent = swapShoesEvent
        self.deleteEvent = deleteEvent
        self.cancelEvent = cancelEvent
        self.genderChange = 0
        self.verify = None
        return

    def load(self):
        self.gui = loader.loadModel('phase_3/models/gui/tt_m_gui_mat_mainGui')
        guiRArrowUp = self.gui.find('**/tt_t_gui_mat_arrowUp')
        guiRArrowRollover = self.gui.find('**/tt_t_gui_mat_arrowUp')
        guiRArrowDown = self.gui.find('**/tt_t_gui_mat_arrowDown')
        guiRArrowDisabled = self.gui.find('**/tt_t_gui_mat_arrowDisabled')
        guiArrowRotateUp = self.gui.find('**/tt_t_gui_mat_arrowRotateUp')
        guiArrowRotateDown = self.gui.find('**/tt_t_gui_mat_arrowRotateDown')
        shuffleFrame = self.gui.find('**/tt_t_gui_mat_shuffleFrame')
        shuffleArrowUp = self.gui.find('**/tt_t_gui_mat_shuffleArrowUp')
        shuffleArrowDown = self.gui.find('**/tt_t_gui_mat_shuffleArrowDown')
        shuffleArrowRollover = self.gui.find('**/tt_t_gui_mat_shuffleArrowUp')
        shuffleArrowDisabled = self.gui.find('**/tt_t_gui_mat_shuffleArrowDisabled')
        self.parentFrame = DirectFrame(relief=DGG.RAISED, pos=(0.98, 0, 0.416), frameColor=(1, 0, 0, 0))

        def addFrame(posZ, text):
            return DirectFrame(parent=self.parentFrame, image=shuffleFrame, image_scale=halfButtonInvertScale, relief=None, pos=(0, 0, posZ), hpr=(0, 0, 3), scale=1.2, frameColor=(1, 1, 1, 1), text=text, text_scale=0.0575, text_pos=(-0.001, -0.015), text_fg=(1, 1, 1, 1))

        def addButton(parent, scale, hoverScale, posX, command, extraArg):
            return DirectButton(parent=parent, relief=None, image=(shuffleArrowUp,
             shuffleArrowDown,
             shuffleArrowRollover,
             shuffleArrowDisabled), image_scale=scale, image1_scale=hoverScale, image2_scale=hoverScale, pos=(posX, 0, 0), command=command, extraArgs=[extraArg])

        self.hatFrame = addFrame(0.1, TTLocalizer.TrunkHatGUI)
        self.hatLButton = addButton(self.hatFrame, halfButtonScale, halfButtonHoverScale, -0.2, self.swapHat, -1)
        self.hatRButton = addButton(self.hatFrame, halfButtonInvertScale, halfButtonInvertHoverScale, 0.2, self.swapHat, 1)
        self.glassesFrame = addFrame(-0.15, TTLocalizer.TrunkGlassesGUI)
        self.glassesLButton = addButton(self.glassesFrame, halfButtonScale, halfButtonHoverScale, -0.2, self.swapGlasses, -1)
        self.glassesRButton = addButton(self.glassesFrame, halfButtonInvertScale, halfButtonInvertHoverScale, 0.2, self.swapGlasses, 1)
        self.backpackFrame = addFrame(-0.4, TTLocalizer.TrunkBackpackGUI)
        self.backpackLButton = addButton(self.backpackFrame, halfButtonScale, halfButtonHoverScale, -0.2, self.swapBackpack, -1)
        self.backpackRButton = addButton(self.backpackFrame, halfButtonInvertScale, halfButtonInvertHoverScale, 0.2, self.swapBackpack, 1)
        self.shoesFrame = addFrame(-0.65, TTLocalizer.TrunkShoesGUI)
        self.shoesLButton = addButton(self.shoesFrame, halfButtonScale, halfButtonHoverScale, -0.2, self.swapShoes, -1)
        self.shoesRButton = addButton(self.shoesFrame, halfButtonInvertScale, halfButtonInvertHoverScale, 0.2, self.swapShoes, 1)
        self.parentFrame.hide()
        self.shuffleFetchMsg = 'TrunkShuffle'
        self.shuffleButton = ShuffleButton.ShuffleButton(self, self.shuffleFetchMsg)
        self.gui = loader.loadModel('phase_3/models/gui/create_a_toon_gui')
        self.cancelButton = DirectButton(relief=None, image=(self.gui.find('**/CrtAtoon_Btn2_UP'), self.gui.find('**/CrtAtoon_Btn2_DOWN'), self.gui.find('**/CrtAtoon_Btn2_RLLVR')), pos=(0.15, 0, -0.85), command=self.__handleCancel, text=('', TTLocalizer.MakeAToonCancel, TTLocalizer.MakeAToonCancel), text_font=ToontownGlobals.getInterfaceFont(), text_scale=0.08, text_pos=(0, -0.03), text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1))
        self.cancelButton.hide()
        self.rotateL = DirectButton(relief=None, pos=(-0.15, 0, 0.85), image=(guiArrowRotateUp,
         guiArrowRotateDown,
         guiArrowRotateUp,
         guiArrowRotateDown), image_scale=(-0.7, 0.7, 0.7), image1_scale=(-0.8, 0.8, 0.8), image2_scale=(-0.8, 0.8, 0.8))
        self.rotateL.hide()
        self.rotateL.bind(DGG.B1PRESS, self.__rotateLDown)
        self.rotateL.bind(DGG.B1RELEASE, self.__rotateLUp)
        self.rotateR = DirectButton(relief=None, pos=(0.15, 0, 0.85), image=(guiArrowRotateUp,
         guiArrowRotateDown,
         guiArrowRotateUp,
         guiArrowRotateDown), image_scale=(0.7, 0.7, 0.7), image1_scale=(0.8, 0.8, 0.8), image2_scale=(0.8, 0.8, 0.8))
        self.rotateR.hide()
        self.rotateR.bind(DGG.B1PRESS, self.__rotateRDown)
        self.rotateR.bind(DGG.B1RELEASE, self.__rotateRUp)
        if self.isOwner:
            trashcanGui = loader.loadModel('phase_3/models/gui/trashcan_gui.bam')
            trashImage = (trashcanGui.find('**/TrashCan_CLSD'), trashcanGui.find('**/TrashCan_OPEN'), trashcanGui.find('**/TrashCan_RLVR'))
            self.trashPanel = DirectFrame(parent=aspect2d, image=DGG.getDefaultDialogGeom(), image_color=(1, 1, 0.75, 0.8), image_scale=(0.36, 0, 1.2), pos=(-.86, 0, 0.1), relief=None)

            def addTrashButton(posZ, text, extraArg):
                return DirectButton(parent=self.trashPanel, image=trashImage, relief=None, pos=(-0.09, 0, posZ), command=self.__handleDelete, text=text, extraArgs=[extraArg], scale=(0.5, 0.5, 0.5), text_font=ToontownGlobals.getInterfaceFont(), text_scale=0.12, text_pos=(0.3, 0), text_fg=(0.8, 0.2, 0.2, 1), text_shadow=(0, 0, 0, 1), textMayChange=0)

            self.hatTrashButton = addTrashButton(0.5, TTLocalizer.TrunkDeleteHat, ToonDNA.HAT)
            self.glassesTrashButton = addTrashButton(0.2, TTLocalizer.TrunkDeleteGlasses, ToonDNA.GLASSES)
            self.backpackTrashButton = addTrashButton(-0.1, TTLocalizer.TrunkDeleteBackpack, ToonDNA.BACKPACK)
            self.shoesTrashButton = addTrashButton(-0.4, TTLocalizer.TrunkDeleteShoes, ToonDNA.SHOES)
            self.button = DirectButton(relief=None, image=(self.gui.find('**/CrtAtoon_Btn1_UP'), self.gui.find('**/CrtAtoon_Btn1_DOWN'), self.gui.find('**/CrtAtoon_Btn1_RLLVR')), pos=(-0.15, 0, -0.85), command=self.__handleButton, text=('', TTLocalizer.MakeAToonDone, TTLocalizer.MakeAToonDone), text_font=ToontownGlobals.getInterfaceFont(), text_scale=0.08, text_pos=(0, -0.03), text_fg=(1, 1, 1, 1), text_shadow=(0, 0, 0, 1))
            trashcanGui.removeNode()
        return

    def unload(self):
        taskMgr.remove(self.taskName('rotateL'))
        taskMgr.remove(self.taskName('rotateR'))
        self.ignore('verifyDone')
        self.gui.removeNode()
        del self.gui
        self.parentFrame.destroy()
        self.hatFrame.destroy()
        self.glassesFrame.destroy()
        self.backpackFrame.destroy()
        self.shoesFrame.destroy()
        self.hatLButton.destroy()
        self.hatRButton.destroy()
        self.glassesLButton.destroy()
        self.glassesRButton.destroy()
        self.backpackLButton.destroy()
        self.backpackRButton.destroy()
        self.shoesLButton.destroy()
        self.shoesRButton.destroy()
        del self.parentFrame
        del self.hatFrame
        del self.glassesFrame
        del self.backpackFrame
        del self.shoesFrame
        del self.hatLButton
        del self.hatRButton
        del self.glassesLButton
        del self.glassesRButton
        del self.backpackLButton
        del self.backpackRButton
        del self.shoesLButton
        del self.shoesRButton
        self.shuffleButton.unload()
        self.ignore('MAT-newToonCreated')
        self.cancelButton.destroy()
        del self.cancelButton
        self.rotateL.destroy()
        del self.rotateL
        self.rotateR.destroy()
        del self.rotateR
        if self.isOwner:
            self.hatTrashButton.destroy()
            self.glassesTrashButton.destroy()
            self.backpackTrashButton.destroy()
            self.shoesTrashButton.destroy()
            self.button.destroy()
            del self.hatTrashButton
            del self.glassesTrashButton
            del self.backpackTrashButton
            del self.shoesTrashButton
            del self.button
            self.trashPanel.destroy()
            del self.trashPanel
        if self.verify:
            self.verify.cleanup()
            del self.verify

    def showButtons(self):
        self.parentFrame.show()
        self.cancelButton.show()
        self.rotateL.show()
        self.rotateR.show()
        if self.isOwner:
            self.hatTrashButton.show()
            self.glassesTrashButton.show()
            self.backpackTrashButton.show()
            self.shoesTrashButton.show()
            self.button.show()

    def hideButtons(self):
        self.parentFrame.hide()
        self.cancelButton.hide()
        self.rotateL.hide()
        self.rotateR.hide()
        if self.isOwner:
            self.hatTrashButton.hide()
            self.glassesTrashButton.hide()
            self.backpackTrashButton.hide()
            self.shoesTrashButton.hide()
            self.button.hide()

    def enter(self, toon):
        self.notify.debug('enter')
        base.disableMouse()
        self.toon = toon
        self.setupScrollInterface()
        currHat = self.toon.hat
        currHatIdx = self.hats.index(currHat)
        self.swapHat(currHatIdx - self.hatChoice)
        currGlasses = self.toon.glasses
        currGlassesIdx = self.glasses.index(currGlasses)
        self.swapGlasses(currGlassesIdx - self.glassesChoice)
        currBackpack = self.toon.backpack
        currBackpackIdx = self.backpacks.index(currBackpack)
        self.swapBackpack(currBackpackIdx - self.backpackChoice)
        currShoes = self.toon.shoes
        currShoesIdx = self.shoes.index(currShoes)
        self.swapShoes(currShoesIdx - self.shoesChoice)
        choicePool = [self.hats,
         self.glasses,
         self.backpacks,
         self.shoes]
        self.shuffleButton.setChoicePool(choicePool)
        self.accept(self.shuffleFetchMsg, self.changeAccessories)
        self.acceptOnce('MAT-newToonCreated', self.shuffleButton.cleanHistory)

    def exit(self):
        try:
            del self.toon
        except:
            self.notify.warning('TrunkGUI: toon not found')

        self.hideButtons()
        self.ignore('enter')
        self.ignore('next')
        self.ignore('last')
        self.ignore(self.shuffleFetchMsg)

    def setupButtons(self):
        self.acceptOnce('last', self.__handleBackward)
        self.acceptOnce('next', self.__handleForward)
        return None

    def setupScrollInterface(self):
        self.notify.debug('setupScrollInterface')
        if self.hatList == None:
            self.hatList = self.toon.getHatList()
        if self.glassesList == None:
            self.glassesList = self.toon.getGlassesList()
        if self.backpackList == None:
            self.backpackList = self.toon.getBackpackList()
        if self.shoesList == None:
            self.shoesList = self.toon.getShoesList()
        self.hats = []
        self.glasses = []
        self.backpacks = []
        self.shoes = []
        self.hats.append((self.toon.hat[0], self.toon.hat[1], self.toon.hat[2]))
        self.glasses.append((self.toon.glasses[0], self.toon.glasses[1], self.toon.glasses[2]))
        self.backpacks.append((self.toon.backpack[0], self.toon.backpack[1], self.toon.backpack[2]))
        self.shoes.append((self.toon.shoes[0], self.toon.shoes[1], self.toon.shoes[2]))
        i = 0
        while i < len(self.hatList):
            self.hats.append((self.hatList[i], self.hatList[i + 1], self.hatList[i + 2]))
            i = i + 3

        i = 0
        while i < len(self.glassesList):
            self.glasses.append((self.glassesList[i], self.glassesList[i + 1], self.glassesList[i + 2]))
            i = i + 3

        i = 0
        while i < len(self.backpackList):
            self.backpacks.append((self.backpackList[i], self.backpackList[i + 1], self.backpackList[i + 2]))
            i = i + 3

        i = 0
        while i < len(self.shoesList):
            self.shoes.append((self.shoesList[i], self.shoesList[i + 1], self.shoesList[i + 2]))
            i = i + 3

        self.hatChoice = 0
        self.glassesChoice = 0
        self.backpackChoice = 0
        self.shoesChoice = 0
        self.swapHat(0)
        self.swapGlasses(0)
        self.swapBackpack(0)
        self.swapShoes(0)
        self.updateTrashButtons()
        self.setupButtons()
        return

    def updateTrashButtons(self):
        if not self.isOwner:
            return
        if len(self.hats) < 2 or self.toon.hat[0] == 0:
            self.hatTrashButton['state'] = DGG.DISABLED
        else:
            self.hatTrashButton['state'] = DGG.NORMAL
        if len(self.glasses) < 2 or self.toon.glasses[0] == 0:
            self.glassesTrashButton['state'] = DGG.DISABLED
        else:
            self.glassesTrashButton['state'] = DGG.NORMAL
        if len(self.backpacks) < 2 or self.toon.backpack[0] == 0:
            self.backpackTrashButton['state'] = DGG.DISABLED
        else:
            self.backpackTrashButton['state'] = DGG.NORMAL
        if len(self.shoes) < 2 or self.toon.shoes[0] == 0:
            self.shoesTrashButton['state'] = DGG.DISABLED
        else:
            self.shoesTrashButton['state'] = DGG.NORMAL

    def rotateToonL(self, task):
        self.toon.setH(self.toon.getH() - 4)
        return Task.cont

    def rotateToonR(self, task):
        self.toon.setH(self.toon.getH() + 4)
        return Task.cont

    def __rotateLUp(self, event):
        messenger.send('wakeup')
        taskMgr.remove(self.taskName('rotateL'))

    def __rotateLDown(self, event):
        messenger.send('wakeup')
        task = Task(self.rotateToonL)
        taskMgr.add(task, self.taskName('rotateL'))

    def __rotateRUp(self, event):
        messenger.send('wakeup')
        taskMgr.remove(self.taskName('rotateR'))

    def __rotateRDown(self, event):
        messenger.send('wakeup')
        task = Task(self.rotateToonR)
        taskMgr.add(task, self.taskName('rotateR'))

    def setGender(self, gender):
        self.ownerGender = gender
        self.genderChange = 1

    def swapHat(self, offset):
        length = len(self.hats)
        self.hatChoice += offset
        if self.hatChoice <= 0:
            self.hatChoice = 0
        self.updateScrollButtons(self.hatChoice, length, 0, self.hatLButton, self.hatRButton)
        if self.hatChoice < 0 or self.hatChoice >= len(self.hats) or len(self.hats[self.hatChoice]) != 3:
            self.notify.warning('hatChoice index is out of range!')
            return None
        hat = self.hats[self.hatChoice]
        self.toon.setHat(hat[0], hat[1], hat[2])
        if self.swapHatEvent != None:
            messenger.send(self.swapHatEvent)
        messenger.send('wakeup')

    def swapGlasses(self, offset):
        length = len(self.glasses)
        self.glassesChoice += offset
        if self.glassesChoice <= 0:
            self.glassesChoice = 0
        self.updateScrollButtons(self.glassesChoice, length, 0, self.glassesLButton, self.glassesRButton)
        if self.glassesChoice < 0 or self.glassesChoice >= len(self.glasses) or len(self.glasses[self.glassesChoice]) != 3:
            self.notify.warning('glassesChoice index is out of range!')
            return None
        glasses = self.glasses[self.glassesChoice]
        self.toon.setGlasses(glasses[0], glasses[1], glasses[2])
        if self.swapGlassesEvent != None:
            messenger.send(self.swapGlassesEvent)
        messenger.send('wakeup')

    def swapBackpack(self, offset):
        length = len(self.backpacks)
        self.backpackChoice += offset
        if self.backpackChoice <= 0:
            self.backpackChoice = 0
        self.updateScrollButtons(self.backpackChoice, length, 0, self.backpackLButton, self.backpackRButton)
        if self.backpackChoice < 0 or self.backpackChoice >= len(self.backpacks) or len(self.backpacks[self.backpackChoice]) != 3:
            self.notify.warning('backpackChoice index is out of range!')
            return None
        backpack = self.backpacks[self.backpackChoice]
        self.toon.setBackpack(backpack[0], backpack[1], backpack[2])
        if self.swapBackpackEvent != None:
            messenger.send(self.swapBackpackEvent)
        messenger.send('wakeup')

    def swapShoes(self, offset):
        length = len(self.shoes)
        self.shoesChoice += offset
        if self.shoesChoice <= 0:
            self.shoesChoice = 0
        self.updateScrollButtons(self.shoesChoice, length, 0, self.shoesLButton, self.shoesRButton)
        if self.shoesChoice < 0 or self.shoesChoice >= len(self.shoes) or len(self.shoes[self.shoesChoice]) != 3:
            self.notify.warning('shoesChoice index is out of range!')
            return None
        shoes = self.shoes[self.shoesChoice]
        self.toon.setShoes(shoes[0], shoes[1], shoes[2])
        if self.swapShoesEvent != None:
            messenger.send(self.swapShoesEvent)
        messenger.send('wakeup')

    def updateScrollButtons(self, choice, length, startTex, lButton, rButton):
        if choice >= length - 1:
            rButton['state'] = DGG.DISABLED
        else:
            rButton['state'] = DGG.NORMAL
        if choice <= 0:
            lButton['state'] = DGG.DISABLED
        else:
            lButton['state'] = DGG.NORMAL

    def __handleForward(self):
        self.doneStatus = 'next'
        messenger.send(self.doneEvent)

    def __handleBackward(self):
        self.doneStatus = 'last'
        messenger.send(self.doneEvent)

    def resetClothes(self, style):
        if self.toon:
            oldHat = style[ToonDNA.HAT]
            oldGlasses = style[ToonDNA.GLASSES]
            oldBackpack = style[ToonDNA.BACKPACK]
            oldShoes = style[ToonDNA.SHOES]
            self.toon.setHat(oldHat[0], oldHat[1], oldHat[2])
            self.toon.setGlasses(oldGlasses[0], oldGlasses[1], oldGlasses[2])
            self.toon.setBackpack(oldBackpack[0], oldBackpack[1], oldBackpack[2])
            self.toon.setShoes(oldShoes[0], oldShoes[1], oldShoes[2])
            self.toon.loop('neutral', 0)

    def changeAccessories(self):
        self.notify.debug('Entering changeAccessories')
        NoItem = (0, 0, 0)
        newChoice = self.shuffleButton.getCurrChoice()
        if newChoice[0] in self.hats:
            newHatIndex = self.hats.index(newChoice[0])
        else:
            newHatIndex = self.hats.index(NoItem)
        if newChoice[1] in self.glasses:
            newGlassesIndex = self.glasses.index(newChoice[1])
        else:
            newGlassesIndex = self.glasses.index(NoItem)
        if newChoice[2] in self.backpacks:
            newBackpackIndex = self.backpacks.index(newChoice[2])
        else:
            newBackpackIndex = self.backpacks.index(NoItem)
        if newChoice[3] in self.shoes:
            newShoesIndex = self.shoes.index(newChoice[3])
        else:
            newShoesIndex = self.shoes.index(NoItem)
        oldHatIndex = self.hatChoice
        oldGlassesIndex = self.glassesChoice
        oldBackpackIndex = self.backpackChoice
        oldShoesIndex = self.shoesChoice
        self.swapHat(newHatIndex - oldHatIndex)
        self.swapGlasses(newGlassesIndex - oldGlassesIndex)
        self.swapBackpack(newBackpackIndex - oldBackpackIndex)
        self.swapShoes(newShoesIndex - oldShoesIndex)

    def getCurrToonSetting(self):
        return [self.hats[self.hatChoice],
         self.glasses[self.glassesChoice],
         self.backpacks[self.backpackChoice],
         self.shoes[self.shoesChoice]]

    def removeHat(self, index):
        listLen = len(self.hats)
        if index < listLen:
            del self.hats[index]
            if self.hatChoice > index:
                self.hatChoice -= 1
            elif self.hatChoice == index:
                self.hatChoice = 0
            return 1
        return 0

    def removeGlasses(self, index):
        listLen = len(self.glasses)
        if index < listLen:
            del self.glasses[index]
            if self.glassesChoice > index:
                self.glassesChoice -= 1
            elif self.glassesChoice == index:
                self.glassesChoice = 0
            return 1
        return 0

    def removeBackpack(self, index):
        listLen = len(self.backpacks)
        if index < listLen:
            del self.backpacks[index]
            if self.backpackChoice > index:
                self.backpackChoice -= 1
            elif self.backpackChoice == index:
                self.backpackChoice = 0
            return 1
        return 0

    def removeShoes(self, index):
        listLen = len(self.shoes)
        if index < listLen:
            del self.shoes[index]
            if self.shoesChoice > index:
                self.shoesChoice -= 1
            elif self.shoesChoice == index:
                self.shoesChoice = 0
            return 1
        return 0

    def __handleButton(self):
        self.doneStatus = 'next'
        messenger.send(self.doneEvent)
        messenger.send('wakeup')

    def __handleCancel(self):
        messenger.send(self.cancelEvent)
        messenger.send('wakeup')

    def __handleDelete(self, which):
        abortDeletion = False
        if which == ToonDNA.HAT:
            item = TTLocalizer.TrunkHat
        elif which == ToonDNA.GLASSES:
            item = TTLocalizer.TrunkGlasses
        elif which == ToonDNA.BACKPACK:
            item = TTLocalizer.TrunkBackpack
        else:
            item = TTLocalizer.TrunkShoes
        self.verify = TTDialog.TTGlobalDialog(doneEvent='verifyDone', message=TTLocalizer.ClosetVerifyDelete % item, style=TTDialog.TwoChoice)
        self.verify.show()
        self.accept('verifyDone', Functor(self.__handleVerifyDelete, which))
        messenger.send('wakeup')

    def __handleVerifyDelete(self, which):
        status = self.verify.doneStatus
        self.ignore('verifyDone')
        self.verify.cleanup()
        del self.verify
        self.verify = None
        if status == 'ok':
            messenger.send(self.deleteEvent, [which])
        messenger.send('wakeup')
        return

    def taskName(self, idString):
        return idString + '-TrunkGUI'
