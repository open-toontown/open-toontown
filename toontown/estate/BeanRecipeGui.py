from direct.gui.DirectGui import *
from direct.directnotify import DirectNotifyGlobal
from pandac.PandaModules import *
from toontown.estate import GardenGlobals
from toontown.estate import PlantingGUI
from toontown.toonbase import TTLocalizer

class BeanRecipeGui(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('PlantingGUI')

    def __init__(self, parent, recipe, **kw):
        left = 0
        right = 0.445
        bottom = 0
        top = 0.08
        borderWidth = 0.01
        optiondefs = [('relief', DGG.RIDGE, None),
         ('state', 'normal', None),
         ('pos', (0, 0, 0), None),
         ('frameSize', (left,
           right,
           bottom,
           top), None),
         ('borderWidth', (borderWidth, borderWidth), self.setBorderWidth)]
        self.defineoptions(kw, optiondefs)
        DirectFrame.__init__(self, parent)
        self.initialiseoptions(BeanRecipeGui)
        self.jellyBeanBoxList = []
        xIncrement = 0.052
        for i in range(len(recipe)):
            beanIndex = GardenGlobals.BeanColorLetters.index(recipe[i])
            self.createJellyBeanBox(beanIndex, borderWidth + xIncrement * i, borderWidth)

        for j in range(len(recipe), GardenGlobals.getNumberOfShovelBoxes()):
            self.createEmptyBeanBox(borderWidth + xIncrement * j, borderWidth)

        return

    def createJellyBeanBox(self, beanIndex, xPos, zPos):
        geomColor = (1, 1, 1, 1)
        state = DGG.NORMAL
        command = None
        xAdj = 0.03
        zAdj = 0.03
        newBox = DirectButton(parent=self, pos=(xPos + xAdj, 0, zPos + zAdj), geom=DGG.getDefaultDialogGeom(), geom_scale=(0.1, 1.0, 0.1), geom_color=geomColor, scale=(0.5, 1, 0.5), relief=None, state=state, command=command, extraArgs=[beanIndex], text=TTLocalizer.BeanColorWords[beanIndex], text_pos=(0.0, 0.1), text_scale=0.07, text_fg=Vec4(0, 0, 0, 0), text1_fg=Vec4(0, 0, 0, 1), text2_fg=Vec4(0, 0, 0, 1), text3_fg=Vec4(0, 0, 0, 0), clickSound=None, pressEffect=0)
        beanParent = newBox.attachNewNode('bean_%d' % beanIndex)
        PlantingGUI.loadJellyBean(beanParent, beanIndex)
        self.jellyBeanBoxList.append(newBox)
        return

    def createEmptyBeanBox(self, xPos, zPos):
        geomColor = (1, 1, 1, 1)
        state = DGG.NORMAL
        command = None
        xAdj = 0.03
        zAdj = 0.03
        newBox = DirectButton(parent=self, pos=(xPos + xAdj, 0, zPos + zAdj), geom=DGG.getDefaultDialogGeom(), geom_scale=(0.1, 1.0, 0.1), geom_color=geomColor, scale=(0.5, 1, 0.5), relief=None, state=state, command=command, text='', text_pos=(0.0, 0.1), text_scale=0.07, text_fg=Vec4(0, 0, 0, 0), text1_fg=Vec4(0, 0, 0, 1), text2_fg=Vec4(0, 0, 0, 1), text3_fg=Vec4(0, 0, 0, 0), clickSound=None, pressEffect=0)
        newBox.setColorScale(0.5, 0.5, 0.5, 1)
        self.jellyBeanBoxList.append(newBox)
        return
