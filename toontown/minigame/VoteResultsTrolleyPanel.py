from direct.gui.DirectGui import DirectFrame, DGG, DirectLabel
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import ToontownGlobals
from pandac.PandaModules import Point3, TextNode, Vec4
from toontown.minigame import TravelGameGlobals
from toontown.toonbase import TTLocalizer
from direct.interval.IntervalGlobal import Parallel, Sequence, LerpFunc, Func, Wait, SoundInterval
from otp.otpbase.PythonUtil import pdir

class VoteResultsTrolleyPanel(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('VoteResultsTrolleyPanel')

    def __init__(self, numPlayers, avIdList, votes, directions, namesList, disconnectedList, directionToGo, directionReason, directionTotals, *args, **kwargs):
        opts = {'relief': None,
         'geom': DGG.getDefaultDialogGeom(),
         'geom_color': ToontownGlobals.GlobalDialogColor[:3] + (0.8,),
         'geom_scale': (1.75, 1, 0.25),
         'pos': (0, 0, 0.825)}
        opts.update(kwargs)
        DirectFrame.__init__(self, *args, **opts)
        self.initialiseoptions(VoteResultsTrolleyPanel)
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
        self.upLabel = DirectLabel(parent=self, relief=None, pos=(-0.5, 0, 0.06), text=TTLocalizer.TravelGameDirections[0] + ':', text_fg=(0.0, 0.0, 1.0, 1.0), text_scale=0.05, text_align=TextNode.ARight)
        self.downLabel = DirectLabel(parent=self, relief=None, pos=(0.5, 0, 0.06), text=TTLocalizer.TravelGameDirections[1] + ':', text_fg=(1.0, 0.0, 0.0, 1.0), text_scale=0.05, text_align=TextNode.ARight)
        self.totalVotesUpLabel = DirectLabel(parent=self.upLabel, relief=None, pos=(0.2, 0, 0.0), text='0', text_fg=(0.0, 0.0, 1.0, 1.0), text_scale=0.05, text_align=TextNode.ARight)
        self.totalVotesDownLabel = DirectLabel(parent=self.downLabel, relief=None, pos=(0.2, 0, 0.0), text='0', text_fg=(1.0, 0.0, 0.0, 1.0), text_scale=0.05, text_align=TextNode.ARight)
        self.totalFrame = DirectFrame(parent=self, relief=None, pos=self.getRowPos(self.numPlayers))
        self.totalVotesLabels = [self.totalVotesUpLabel, self.totalVotesDownLabel]
        self.resultFrame = DirectFrame(parent=self, relief=None, pos=self.getRowPos(0.5))
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

        self.avVotesLabel = {}
        self.avArrows = {}
        matchingGameGui = loader.loadModel('phase_3.5/models/gui/matching_game_gui')
        minnieArrow = matchingGameGui.find('**/minnieArrow')
        from toontown.minigame.DistributedTravelGame import map3dToAspect2d
        for index in range(self.numPlayers):
            avId = self.avIdList[index]
            av = base.cr.doId2do.get(avId)
            if av:
                height = av.getHeight()
                avPos = av.getPos(render)
                avPos.setZ(av.getZ() + 5)
                labelPos = map3dToAspect2d(render, avPos)
                if not labelPos:
                    continue
                labelPos.setZ(labelPos.getZ() + 0.3)
                arrow = None
                if self.votes[index] > 0:
                    arrow = aspect2d.attachNewNode('avArrow')
                    minnieArrow.copyTo(arrow)
                    arrow.setScale(1.1, 1, 1.15)
                    arrow.setPos(labelPos)
                    if self.directions[index] == 0:
                        arrow.setR(-90)
                        arrow.setColorScale(0, 0, 1, 1)
                    else:
                        arrow.setR(90)
                        arrow.setColorScale(1, 0, 0, 1)
                    arrow.wrtReparentTo(self.resultFrame)
                    arrow.hide()
                    self.avArrows[index] = arrow
                fgColor = Vec4(0, 0, 0, 1)
                if self.votes[index] > 0:
                    if self.directions[index] == 0:
                        fgColor = Vec4(0, 0, 1, 1)
                    else:
                        fgColor = Vec4(1, 0, 0, 1)
                if self.votes[index] > 0:
                    newLabel = DirectLabel(parent=aspect2d, relief=None, pos=labelPos, text='test', text_fg=(1, 1, 1, 1), text_scale=0.1, text_align=TextNode.ACenter, text_font=ToontownGlobals.getSignFont(), text_pos=(0, -0.01, 0))
                else:
                    newLabel = DirectLabel(parent=aspect2d, geom=DGG.getDefaultDialogGeom(), geom_scale=(0.2, 1, 0.2), relief=None, pos=labelPos, text='test', text_fg=(0.5, 0.5, 0.5, 1), text_scale=0.1, text_align=TextNode.ACenter, text_font=ToontownGlobals.getSignFont(), text_pos=(0, -0.035, 0))
                newLabel.wrtReparentTo(self.resultFrame)
                newLabel.hide()
                self.avVotesLabel[index] = newLabel

        matchingGameGui.removeNode()
        self.curArrowSfxIndex = 0
        self.upArrowSfx = []
        self.downArrowSfx = []
        for i in range(5):
            self.upArrowSfx.append(base.loader.loadSfx('phase_4/audio/sfx/MG_sfx_travel_game_blue_arrow.ogg'))
            self.downArrowSfx.append(base.loader.loadSfx('phase_4/audio/sfx/MG_sfx_travel_game_red_arrow.ogg'))

        self.winVoteSfx = base.loader.loadSfx('phase_4/audio/sfx/MG_sfx_travel_game_win_vote.ogg')
        self.noVoteSfx = base.loader.loadSfx('phase_4/audio/sfx/MG_sfx_travel_game_square_no_vote_1.ogg')
        self.loseVoteSfx = base.loader.loadSfx('phase_4/audio/sfx/MG_sfx_travel_game_lose_vote.ogg')
        self.localAvatarWon = False
        self.localAvatarLost = False
        localIndex = self.avIdList.index(base.localAvatar.doId)
        localDirection = self.directions[localIndex]
        localVotes = self.votes[localIndex]
        if localVotes:
            if localDirection == self.directionToGo:
                if not TravelGameGlobals.ReverseWin:
                    self.localAvatarWon = True
                else:
                    self.localAvatarLost = True
            elif not TravelGameGlobals.ReverseWin:
                self.localAvatarLost = True
            else:
                self.localAvatarWon = True
        return

    def getRowPos(self, place):
        return Point3(-0.72, -0.01, 0.0 - place * 0.1)

    def setupResultLabel(self):
        reasonStr = ''
        if self.directionReason == TravelGameGlobals.ReasonVote:
            if self.directionToGo == 0:
                losingDirection = 1
            else:
                losingDirection = 0
            diffVotes = self.directionTotals[self.directionToGo] - self.directionTotals[losingDirection]
            if diffVotes > 1:
                reasonStr = TTLocalizer.TravelGameReasonVotesPlural % {'dir': TTLocalizer.TravelGameDirections[self.directionToGo],
                 'numVotes': diffVotes}
            else:
                reasonStr = TTLocalizer.TravelGameReasonVotesSingular % {'dir': TTLocalizer.TravelGameDirections[self.directionToGo],
                 'numVotes': diffVotes}
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
        startVotes = 0
        for prev in range(index):
            if self.directions[prev] == direction:
                startVotes += self.votes[prev]

        def totalTicker(t, label = self.totalVotesLabels[direction], startVotes = startVotes, additionalVotes = numVotes):
            label['text'] = str(int(t * additionalVotes + startVotes))

        track.append(LerpFunc(totalTicker, duration=duration, name='countTotal %d' % index))
        if index in self.avVotesLabel:

            def avVotesTicker(t, label = self.avVotesLabel[index], startVotes = 0, endVotes = numVotes, direction = direction):
                oldValue = label['text']
                newValue = int(t * endVotes + startVotes)
                label['text'] = str(newValue)
                if not oldValue == label['text']:
                    if newValue:
                        if direction == 0:
                            self.upArrowSfx[self.curArrowSfxIndex].play()
                        else:
                            self.downArrowSfx[self.curArrowSfxIndex].play()
                            self.curArrowSfxIndex += 1
                        if self.curArrowSfxIndex >= len(self.upArrowSfx):
                            self.curArrowSfxIndex = 0

            label = self.avVotesLabel[index]
            track.append(Func(self.avVotesLabel[index].show, name='showName %d' % index))
            if index in self.avArrows:
                track.append(Func(self.avArrows[index].show, name='showArrow %d' % index))
            if direction == 0 and numVotes:
                pass
            elif direction == 1 and numVotes:
                pass
            else:
                track.append(SoundInterval(self.noVoteSfx))
            track.append(LerpFunc(avVotesTicker, duration=duration, name='countAvVotes %d' % index))
        return track

    def startMovie(self):
        self.movie = Sequence()
        for index in range(self.numPlayers):
            track = self.createOnePlayerSequence(index, 1.25)
            self.movie.append(track)
            self.movie.append(Wait(0.75))

        self.movie.append(Func(self.resultLabel.show))
        soundAndWait = Parallel()
        soundAndWait.append(Wait(2.0))
        if self.localAvatarWon:
            soundAndWait.append(SoundInterval(self.winVoteSfx))
        elif self.localAvatarLost:
            soundAndWait.append(SoundInterval(self.loseVoteSfx, duration=0.43))
        self.movie.append(soundAndWait)
        self.movie.start()

    def destroy(self):
        self.movie.finish()
        del self.movie
        del self.winVoteSfx
        del self.noVoteSfx
        del self.upArrowSfx
        del self.loseVoteSfx
        del self.downArrowSfx
        DirectFrame.destroy(self)
