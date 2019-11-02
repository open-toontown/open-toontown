from direct.gui.DirectGui import DirectFrame, DGG, DirectLabel
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from pandac.PandaModules import Point3, TextNode
from toontown.minigame import TravelGameGlobals
from toontown.toonbase import TTLocalizer
from direct.interval.IntervalGlobal import Parallel, Sequence, LerpFunc, Func, Wait

class VoteResultsPanel(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('VoteResultsPanel')

    def __init__(self, numPlayers, avIdList, votes, directions, namesList, disconnectedList, directionToGo, directionReason, directionTotals, *args, **kwargs):
        opts = {'relief': None,
         'geom': DGG.getDefaultDialogGeom(),
         'geom_color': ToontownGlobals.GlobalDialogColor[:3] + (0.8,),
         'geom_scale': (1.75, 1, 0.75),
         'pos': (0, 0, 0.525)}
        opts.update(kwargs)
        DirectFrame.__init__(self, *args, **opts)
        self.initialiseoptions(VoteResultsPanel)
        listMultiplier = 1
        if TravelGameGlobals.SpoofFour:
            listMultiplier = 4
        self.avIdList = avIdList * listMultiplier
        self.numPlayers = numPlayers * listMultiplier
        self.votes = votes * listMultiplier
        self.directions = directions * listMultiplier
        self.namesList = namesList * listMultiplier
        self.disconnectedList = disconnectedList * listMultiplier
        self.directionToGo = directionToGo
        self.directionReason = directionReason
        self.directionTotals = directionTotals
        self.entryList = []
        self.rowFrame = []
        self.upDownFrame = DirectFrame(parent=self, relief=None, pos=self.getRowPos(-1))
        self.upLabel = DirectLabel(parent=self.upDownFrame, relief=None, pos=(1.2, 0, 0.0), text=TTLocalizer.TravelGameDirections[0], text_fg=(0.0, 0.0, 1.0, 1.0), text_scale=0.05, text_align=TextNode.ARight)
        self.downLabel = DirectLabel(parent=self.upDownFrame, relief=None, pos=(1.43, 0, 0.0), text=TTLocalizer.TravelGameDirections[1], text_fg=(1.0, 0.0, 0.0, 1.0), text_scale=0.05, text_align=TextNode.ARight)
        self.totalFrame = DirectFrame(parent=self, relief=None, pos=self.getRowPos(self.numPlayers))
        self.totalText = DirectLabel(parent=self.totalFrame, relief=None, pos=(1.0, 0, 0.0), text='Total', text_fg=(0.0, 0.0, 0.0, 1.0), text_scale=0.05, text_align=TextNode.ARight)
        self.totalVotesUpLabel = DirectLabel(parent=self.totalFrame, relief=None, pos=(1.2, 0, 0.0), text='', text_fg=(0.0, 0.0, 1.0, 1.0), text_scale=0.05, text_align=TextNode.ARight)
        self.totalVotesDownLabel = DirectLabel(parent=self.totalFrame, relief=None, pos=(1.43, 0, 0.0), text='', text_fg=(1.0, 0.0, 0.0, 1.0), text_scale=0.05, text_align=TextNode.ARight)
        self.totalVotesLabels = [self.totalVotesUpLabel, self.totalVotesDownLabel]
        self.resultFrame = DirectFrame(parent=self, relief=None, pos=self.getRowPos(5))
        self.resultLabel = DirectLabel(parent=self.resultFrame, text='', text_scale=0.06, pos=(0.7, 0, 0.0), text_align=TextNode.ACenter)
        self.setupResultLabel()
        for index in range(self.numPlayers):
            frame = DirectFrame(parent=self, relief=None, pos=self.getRowPos(index))
            self.rowFrame.append(frame)
            nameLabel = DirectFrame(parent=frame, relief=None, pos=(0.46, 0.0, 0.0), text=self.namesList[index], text_fg=(0.0, 0.0, 0.0, 1.0), text_scale=0.05, text_align=TextNode.ACenter, text_font=DGG.getDefaultFont())
            votesUpLabel = DirectLabel(parent=frame, relief=None, pos=(1.2, 0.0, 0.0), text='', text_fg=(0, 0, 1, 1), text_scale=0.05, text_align=TextNode.ARight, text_font=DGG.getDefaultFont())
            votesDownLabel = DirectLabel(parent=frame, relief=None, pos=(1.43, 0.0, 0.0), text='', text_fg=(1, 0, 0, 1), text_scale=0.05, text_align=TextNode.ARight, text_font=DGG.getDefaultFont())
            nameLabel.hide()
            self.entryList.append((nameLabel, votesUpLabel, votesDownLabel))

        return

    def getRowPos(self, place):
        return Point3(-0.72, -0.01, 0.2 - place * 0.1)

    def setupResultLabel(self):
        reasonStr = ''
        if self.directionReason == TravelGameGlobals.ReasonVote:
            reasonStr = TTLocalizer.TravelGameReasonVotes % {'dir': TTLocalizer.TravelGameDirections[self.directionToGo],
             'numVotes': self.directionTotals[self.directionToGo]}
        elif self.directionReason == TravelGameGlobals.ReasonRandom:
            reasonStr = TTLocalizer.TravelGameReasonRandom % {'dir': TTLocalizer.TravelGameDirections[self.directionToGo],
             'numVotes': self.directionTotals[self.directionToGo]}
        elif self.directionReason == TravelGameGlobals.ReasonPlaceDecider:
            reasonStr = TravelGameReasonPlace % {'name': 'TODO NAME',
             'dir': TTLocalizer.TravelGameDirections[self.directionToGo]}
        self.resultLabel['text'] = reasonStr
        self.resultLabel.hide()

    def createOnePlayerSequence(self, index, duration):
        numVotes = self.votes[index]
        direction = self.directions[index]

        def ticketTicker(t, label = self.entryList[index][direction + 1], startVotes = 0, endVotes = numVotes):
            label['text'] = str(int(t * endVotes + startVotes))

        track = Parallel()
        track.append(Func(self.entryList[index][0].show, name='showName %d' % index))
        track.append(LerpFunc(ticketTicker, duration=duration, name='countVotes %d' % index))
        startVotes = 0
        for prev in range(index):
            if self.directions[prev] == direction:
                startVotes += self.votes[prev]

        def totalTicker(t, label = self.totalVotesLabels[direction], startVotes = startVotes, additionalVotes = numVotes):
            label['text'] = str(int(t * additionalVotes + startVotes))

        track.append(LerpFunc(totalTicker, duration=duration, name='countTotal %d' % index))
        return track

    def startMovie(self):
        self.movie = Sequence()
        for index in range(self.numPlayers):
            track = self.createOnePlayerSequence(index, 1.25)
            self.movie.append(track)
            self.movie.append(Wait(0.75))

        self.movie.append(Func(self.resultLabel.show))
        self.movie.append(Wait(2.0))
        self.movie.start()

    def destroy(self):
        self.movie.finish()
        DirectFrame.destroy(self)
