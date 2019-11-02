from pandac.PandaModules import *
from direct.directnotify import DirectNotifyGlobal
from direct.showbase.DirectObject import DirectObject
from toontown.minigame import ToonBlitzGlobals
from toontown.minigame import TwoDStomper

class TwoDStomperMgr(DirectObject):
    notify = DirectNotifyGlobal.directNotify.newCategory('TwoDStomperMgr')

    def __init__(self, section, stomperList):
        self.section = section
        self.stomperList = stomperList
        self.load()

    def destroy(self):
        self.section = None
        while len(self.stompers):
            stomper = self.stompers[0]
            stomper.destroy()
            self.stompers.remove(stomper)

        self.stompers = None
        return

    def load(self):
        if len(self.stomperList):
            self.stompersNP = NodePath('Stompers')
            self.stompersNP.reparentTo(self.section.sectionNP)
        self.stompers = []
        for index in xrange(len(self.stomperList)):
            stomperAttribs = self.stomperList[index]
            self.createNewStomper(stomperAttribs)

    def createNewStomper(self, attrib, model = None):
        stomperId = self.section.getSectionizedId(len(self.stompers))
        if model == None:
            model = self.section.sectionMgr.game.assetMgr.stomper
        newStomper = TwoDStomper.TwoDStomper(self, stomperId, attrib, model)
        newStomper.model.reparentTo(self.stompersNP)
        self.stompers.append(newStomper)
        return

    def enterPlay(self, elapsedTime):
        for stomper in self.stompers:
            stomper.start(elapsedTime)

    def exitPlay(self):
        pass

    def enterPause(self):
        for stomper in self.stompers:
            stomper.enterPause()

    def exitPause(self):
        for stomper in self.stompers:
            stomper.exitPause()
