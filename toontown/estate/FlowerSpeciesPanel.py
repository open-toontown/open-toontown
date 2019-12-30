from toontown.toonbase import ToontownGlobals
from direct.directnotify import DirectNotifyGlobal
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from toontown.toonbase import TTLocalizer
from . import GardenGlobals
from . import FlowerPhoto
from toontown.estate import BeanRecipeGui

class FlowerSpeciesPanel(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('FlowerSpeciesPanel')

    def __init__(self, species = None, itemIndex = 0, *extraArgs):
        flowerGui = loader.loadModel('phase_3.5/models/gui/fishingBook')
        albumGui = flowerGui.find('**/photo_frame1')
        pictureGroup = albumGui.attachNewNode('PictureGroup')
        hideList = ['corner_backs',
         'shadow',
         'bg',
         'corners',
         'picture']
        for name in hideList:
            temp = flowerGui.find('**/%s' % name)
            if not temp.isEmpty():
                temp.wrtReparentTo(pictureGroup)

        pictureGroup.setPos(0, 0, 1.0)
        albumGui.find('**/arrows').removeNode()
        optiondefs = (('relief', None, None),
         ('state', DGG.NORMAL, None),
         ('image', albumGui, None),
         ('image_scale', (0.025, 0.025, 0.025), None),
         ('image_pos', (0, 1, 0), None),
         ('text', TTLocalizer.FlowerUnknown, None),
         ('text_scale', 0.065, None),
         ('text_fg', (0.2, 0.1, 0.0, 1), None),
         ('text_pos', (-0.5, -0.34), None),
         ('text_font', ToontownGlobals.getInterfaceFont(), None),
         ('text_wordwrap', 13.5, None),
         ('text_align', TextNode.ALeft, None))
        self.defineoptions({}, optiondefs)
        DirectFrame.__init__(self)
        self.initialiseoptions(FlowerSpeciesPanel)
        self.flowerPanel = None
        self.species = None
        self.variety = 0
        self.flowerCollection = extraArgs[0]
        self.setSpecies(int(species))
        self.setScale(1.2)
        albumGui.removeNode()
        self.beanRecipeGui = None
        return

    def destroy(self):
        if self.flowerPanel:
            self.flowerPanel.destroy()
            del self.flowerPanel
        self.flowerCollection = None
        self.cleanupBeanRecipeGui()
        DirectFrame.destroy(self)
        return

    def load(self):
        pass

    def setSpecies(self, species):
        if self.species == species:
            return
        self.species = species
        if self.species != None:
            if self.flowerPanel:
                self.flowerPanel.destroy()
            varietyToUse = self.flowerCollection.getInitialVariety(self.species)
            self.variety = varietyToUse
            self.flowerPanel = FlowerPhoto.FlowerPhoto(species=self.species, variety=varietyToUse, parent=self)
            zAdj = 0.0131
            xAdj = -0.002
            self.flowerPanel.setPos(-0.229 + xAdj, 1, -0.01 + zAdj)
            self.flowerPanel.setSwimBounds(-0.2461, 0.2367, -0.207 + zAdj, 0.2664 + zAdj)
            self.flowerPanel.setSwimColor(0.75, 0.75, 0.75, 1.0)
            varietyList = GardenGlobals.getFlowerVarieties(self.species)
            self.speciesLabels = []
            offset = 0.075
            startPos = len(varietyList) / 2 * offset
            if not len(varietyList) % 2:
                startPos -= offset / 2
            for variety in range(len(varietyList)):
                label = DirectButton(parent=self, frameSize=(0,
                 0.445,
                 -0.02,
                 0.04), relief=None, state=DGG.DISABLED, pos=(0.06, 0, startPos - variety * offset), text=TTLocalizer.FlowerUnknown, text_fg=(0.2, 0.1, 0.0, 1), text_scale=(0.045, 0.045, 0.45), text_align=TextNode.ALeft, text_font=ToontownGlobals.getInterfaceFont(), command=self.changeVariety, extraArgs=[variety], text1_bg=Vec4(1, 1, 0, 1), text2_bg=Vec4(0.5, 0.9, 1, 1), text3_fg=Vec4(0.4, 0.8, 0.4, 1))
                self.speciesLabels.append(label)

        return

    def show(self):
        self.update()
        DirectFrame.show(self)

    def hide(self):
        if self.flowerPanel is not None:
            self.flowerPanel.hide()
        if self.beanRecipeGui is not None:
            self.beanRecipeGui.hide()
        DirectFrame.hide(self)
        return

    def showRecipe(self):
        if base.localAvatar.flowerCollection.hasSpecies(self.species):
            self['text'] = TTLocalizer.FlowerSpeciesNames[self.species]
            if base.localAvatar.flowerCollection.hasFlower(self.species, self.variety):
                name = GardenGlobals.getFlowerVarietyName(self.species, self.variety)
                recipeKey = GardenGlobals.PlantAttributes[self.species]['varieties'][self.variety][0]
                self['text'] = name
                self.createBeanRecipeGui(GardenGlobals.Recipes[recipeKey]['beans'])
            else:
                self.cleanupBeanRecipeGui()
        else:
            self['text'] = TTLocalizer.FlowerUnknown
            self.cleanupBeanRecipeGui()

    def update(self):
        if base.localAvatar.flowerCollection.hasSpecies(self.species):
            self.flowerPanel.show(showBackground=0)
            self['text'] = TTLocalizer.FlowerSpeciesNames[self.species]
        for variety in range(len(GardenGlobals.getFlowerVarieties(self.species))):
            if base.localAvatar.flowerCollection.hasFlower(self.species, variety):
                name = GardenGlobals.getFlowerVarietyName(self.species, variety)
                self.speciesLabels[variety]['text'] = name
                self.speciesLabels[variety]['state'] = DGG.NORMAL

        self.showRecipe()

    def changeVariety(self, variety):
        self.variety = variety
        self.flowerPanel.changeVariety(variety)
        self.flowerPanel.show()
        self.showRecipe()

    def createBeanRecipeGui(self, recipe):
        if self.beanRecipeGui:
            self.beanRecipeGui.destroy()
        pos1 = (-0.2, 0, -0.365)
        pos2 = (-0.46, 0, 0.3)
        pos3 = (-0.46, 0, -0.3)
        pos4 = (-0.6, 0, -0.27)
        self.beanRecipeGui = BeanRecipeGui.BeanRecipeGui(aspect2dp, recipe, pos=pos4, scale=1.3, frameColor=(0.8, 0.8, 0.8, 1.0))

    def cleanupBeanRecipeGui(self):
        if self.beanRecipeGui:
            self.beanRecipeGui.destroy()
            self.beanRecipeGui = None
        return
