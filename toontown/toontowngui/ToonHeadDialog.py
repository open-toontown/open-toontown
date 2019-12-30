from pandac.PandaModules import *
from toontown.toonbase.ToontownGlobals import *
from direct.directnotify import DirectNotifyGlobal
from . import TTDialog
from toontown.toon import ToonHead

class ToonHeadDialog(TTDialog.TTDialog):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToonHeadDialog')

    def __init__(self, dna, **kw):
        self.dna = dna
        head = hidden.attachNewNode('head', 20)
        self.headModel = ToonHead.ToonHead()
        self.headModel.setupHead(self.dna, forGui=1)
        self.headModel.fitAndCenterHead(1.0, forGui=1)
        self.headModel.reparentTo(head)
        self.headModel.setName('headModel')
        self.headModel.startBlink()
        optiondefs = (('dialogName', 'ToonHeadDialog', None),
         ('style', TTDialog.NoButtons, None),
         ('geom', head, None),
         ('geom_scale', 0.35, None),
         ('geom_pos', (-0.25, 0, 0), None),
         ('text_wordwrap', 9, None),
         ('fadeScreen', 0, None))
        self.defineoptions(kw, optiondefs)
        TTDialog.TTDialog.__init__(self, style=self['style'])
        self.initialiseoptions(ToonHeadDialog)
        self.postInitialiseFuncList.append(self.replaceHead)
        return

    def replaceHead(self):
        head = self.stateNodePath[0].find('**/head')
        headModelCopy = self.stateNodePath[0].find('**/headModel')
        headModelCopy.removeNode()
        self.headModel.reparentTo(head)

    def cleanup(self):
        TTDialog.TTDialog.cleanup(self)
        self.headModel.stopBlink()
        self.headModel.stopLookAroundNow()
        self.headModel.delete()
