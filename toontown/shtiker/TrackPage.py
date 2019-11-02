from pandac.PandaModules import *
import ShtikerPage
from direct.gui.DirectGui import *
from pandac.PandaModules import *
from toontown.quest import Quests
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import ToontownBattleGlobals
from toontown.toonbase import TTLocalizer
from toontown.toon import Toon
MAX_FRAMES = 18
Track2Anim = {ToontownBattleGlobals.HEAL_TRACK: 'juggle',
 ToontownBattleGlobals.TRAP_TRACK: 'toss',
 ToontownBattleGlobals.LURE_TRACK: 'hypnotize',
 ToontownBattleGlobals.SOUND_TRACK: 'sound',
 ToontownBattleGlobals.THROW_TRACK: 'throw',
 ToontownBattleGlobals.SQUIRT_TRACK: 'firehose',
 ToontownBattleGlobals.DROP_TRACK: 'pushbutton'}

class TrackFrame(DirectFrame):

    def __init__(self, index):
        DirectFrame.__init__(self, relief=None)
        self.initialiseoptions(TrackFrame)
        filmstrip = loader.loadModel('phase_3.5/models/gui/filmstrip')
        self.index = index
        self.frame = DirectFrame(parent=self, relief=None, image=filmstrip, image_scale=1, text=str(self.index - 1), text_pos=(0.26, -0.22), text_fg=(1, 1, 1, 1), text_scale=0.1)
        self.question = DirectLabel(parent=self.frame, relief=None, pos=(0, 0, -0.15), text='?', text_scale=0.4, text_pos=(0, 0.04), text_fg=(0.72, 0.72, 0.72, 1))
        self.toon = None
        filmstrip.removeNode()
        return

    def makeToon(self):
        if not self.toon:
            self.toon = Toon.Toon()
            self.toon.setDNA(base.localAvatar.getStyle())
            self.toon.getGeomNode().setDepthWrite(1)
            self.toon.getGeomNode().setDepthTest(1)
            self.toon.useLOD(500)
            self.toon.reparentTo(self.frame)
            self.toon.setPosHprScale(0, 10, -0.25, 210, 0, 0, 0.12, 0.12, 0.12)
            self.ignore('nametagAmbientLightChanged')

    def play(self, trackId):
        if not base.launcher or base.launcher and base.launcher.getPhaseComplete(5):
            anim = Track2Anim[trackId]
        else:
            anim = 'neutral'
        if self.toon:
            numFrames = self.toon.getNumFrames(anim) - 1
            fromFrame = 0
            toFrame = (self.toon.getNumFrames(anim) - 1) / MAX_FRAMES * self.index
            self.toon.play(anim, None, fromFrame, toFrame - 1)
        return

    def setTrained(self, trackId):
        if self.toon == None:
            self.makeToon()
        if not base.launcher or base.launcher and base.launcher.getPhaseComplete(5):
            anim = Track2Anim[trackId]
            frame = (self.toon.getNumFrames(anim) - 1) / MAX_FRAMES * self.index
        else:
            anim = 'neutral'
            frame = 0
        self.toon.pose(anim, frame)
        self.toon.show()
        self.question.hide()
        trackColorR, trackColorG, trackColorB = ToontownBattleGlobals.TrackColors[trackId]
        self.frame['image_color'] = Vec4(trackColorR, trackColorG, trackColorB, 1)
        self.frame['text_fg'] = Vec4(trackColorR * 0.3, trackColorG * 0.3, trackColorB * 0.3, 1)
        return

    def setUntrained(self, trackId):
        if self.toon:
            self.toon.delete()
            self.toon = None
        self.question.show()
        if trackId == -1:
            self.frame['image_color'] = Vec4(0.7, 0.7, 0.7, 1)
            self.frame['text_fg'] = Vec4(0.5, 0.5, 0.5, 1)
            self.question['text_fg'] = Vec4(0.6, 0.6, 0.6, 1)
        else:
            trackColorR, trackColorG, trackColorB = ToontownBattleGlobals.TrackColors[trackId]
            self.frame['image_color'] = Vec4(trackColorR * 0.7, trackColorG * 0.7, trackColorB * 0.7, 1)
            self.frame['text_fg'] = Vec4(trackColorR * 0.3, trackColorG * 0.3, trackColorB * 0.3, 1)
            self.question['text_fg'] = Vec4(trackColorR * 0.6, trackColorG * 0.6, trackColorB * 0.6, 1)
        return


class TrackPage(ShtikerPage.ShtikerPage):

    def __init__(self):
        ShtikerPage.ShtikerPage.__init__(self)
        self.trackFrames = []

    def placeFrames(self):
        rowY = 0.38
        rowSpace = -0.32
        rowPos = []
        for i in range(3):
            rowPos.append(rowY)
            rowY += rowSpace

        colX = -0.7
        colSpace = 0.276
        colPos = []
        for i in range(6):
            colPos.append(colX)
            colX += colSpace

        for index in range(1, MAX_FRAMES + 1):
            frame = self.trackFrames[index - 1]
            col = (index - 1) % 6
            row = (index - 1) / 6
            frame.setPos(colPos[col], 0, rowPos[row])
            frame.setScale(0.39)

    def load(self):
        self.title = DirectLabel(parent=self, relief=None, text=TTLocalizer.TrackPageTitle, text_scale=0.1, pos=(0, 0, 0.65))
        self.subtitle = DirectLabel(parent=self, relief=None, text=TTLocalizer.TrackPageSubtitle, text_scale=0.05, text_fg=(0.5, 0.1, 0.1, 1), pos=(0, 0, 0.56))
        self.trackText = DirectLabel(parent=self, relief=None, text='', text_scale=0.05, text_fg=(0.5, 0.1, 0.1, 1), pos=(0, 0, -0.5))
        for index in range(1, MAX_FRAMES + 1):
            frame = TrackFrame(index)
            frame.reparentTo(self)
            self.trackFrames.append(frame)

        self.placeFrames()
        self.startFrame = self.trackFrames[0]
        self.endFrame = self.trackFrames[-1]
        self.startFrame.frame['text'] = ''
        self.startFrame.frame['text_scale'] = TTLocalizer.TPstartFrame
        self.startFrame.frame['image_color'] = Vec4(0.2, 0.2, 0.2, 1)
        self.startFrame.frame['text_fg'] = (1, 1, 1, 1)
        self.startFrame.frame['text_pos'] = (0, 0.08)
        self.startFrame.question.hide()
        self.endFrame.frame['text'] = TTLocalizer.TrackPageDone
        self.endFrame.frame['text_scale'] = TTLocalizer.TPendFrame
        self.endFrame.frame['image_color'] = Vec4(0.2, 0.2, 0.2, 1)
        self.endFrame.frame['text_fg'] = (1, 1, 1, 1)
        self.endFrame.frame['text_pos'] = (0, 0)
        self.endFrame.question.hide()
        return

    def unload(self):
        del self.title
        del self.subtitle
        del self.trackText
        del self.trackFrames
        ShtikerPage.ShtikerPage.unload(self)

    def clearPage(self):
        for index in range(1, MAX_FRAMES - 1):
            self.trackFrames[index].setUntrained(-1)

        self.startFrame.frame['text'] = ''
        self.trackText['text'] = TTLocalizer.TrackPageClear

    def updatePage(self):
        trackId, trackProgress = base.localAvatar.getTrackProgress()
        if trackId == -1:
            self.clearPage()
        else:
            trackName = ToontownBattleGlobals.Tracks[trackId].capitalize()
            self.trackText['text'] = TTLocalizer.TrackPageTraining % (trackName, trackName)
            trackProgressArray = base.localAvatar.getTrackProgressAsArray()
            for index in range(1, MAX_FRAMES - 2):
                if trackProgressArray[index - 1]:
                    self.trackFrames[index].setTrained(trackId)
                else:
                    self.trackFrames[index].setUntrained(trackId)

            self.trackFrames[MAX_FRAMES - 2].setUntrained(trackId)
            self.startFrame.frame['text'] = TTLocalizer.TrackPageFilmTitle % trackName

    def enter(self):
        self.updatePage()
        ShtikerPage.ShtikerPage.enter(self)

    def exit(self):
        self.clearPage()
        ShtikerPage.ShtikerPage.exit(self)
