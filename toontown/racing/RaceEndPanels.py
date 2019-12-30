from direct.gui.DirectGui import *
from pandac.PandaModules import *
from direct.directnotify import DirectNotifyGlobal
from direct.interval.IntervalGlobal import *
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.racing import RaceGlobals
from toontown.shtiker.KartPage import RacingTrophy
from toontown.racing import RaceGlobals

class RaceResultsPanel(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('RaceEndPanels')

    def __init__(self, numRacers, race, raceEndPanel, *args, **kwargs):
        opts = {'relief': None,
         'geom': DGG.getDefaultDialogGeom(),
         'geom_color': ToontownGlobals.GlobalDialogColor[:3] + (0.8,),
         'geom_scale': (1.75, 1, 0.75)}
        opts.update(kwargs)
        DirectFrame.__init__(self, *args, **opts)
        self.initialiseoptions(RaceResultsPanel)
        self.entryList = []
        self.entryListSeqs = []
        self.pointSeqs = []
        self.numRacers = numRacers
        base.resultsPanel = self
        self.circuitFinishSeq = None
        self.tickets = {}
        self.race = race
        self.raceEndPanel = raceEndPanel
        self.pointsLabel = DirectLabel(parent=self, relief=None, pos=(0.7, 0, 0.3), text=TTLocalizer.KartRace_CircuitPoints, text_fg=(0.0, 0.0, 0.0, 1.0), text_scale=TTLocalizer.REPsmallLabel)
        self.pointsLabel.hide()
        self.rowFrame = []
        for x in range(self.numRacers):
            frame = DirectFrame(parent=self, relief=None, pos=self.getRowPos(x))
            self.rowFrame.append(frame)
            pLabel = DirectLabel(parent=frame, relief=None, pos=(0.0, 0.0, -0.01), text=repr((x + 1)) + ' -', text_fg=(0.5, 0.5, 0.5, 1.0), text_scale=TTLocalizer.REPlargeLabel, text_align=TextNode.ARight, text_font=DGG.getDefaultFont())
            fFrame = DirectFrame(parent=frame, relief=None, pos=(0.1, -0.01, 0.01))
            nLabel = DirectLabel(parent=frame, relief=None, pos=(0.46, 0.0, 0.0), text='', text_fg=(0.0, 0.0, 0.0, 1.0), text_scale=TTLocalizer.REPsmallLabel, text_align=TextNode.ACenter, text_font=DGG.getDefaultFont())
            tLabel = DirectLabel(parent=frame, relief=None, pos=(0.9, 0.0, 0.0), text="--'--''--", text_fg=(0.5, 0.5, 0.5, 1.0), text_scale=TTLocalizer.REPsmallLabel, text_font=DGG.getDefaultFont())
            wLabel = DirectLabel(parent=frame, relief=None, pos=(1.14, 0.0, 0.0), text='', text_fg=(0, 0, 0, 1), text_scale=TTLocalizer.REPsmallLabel, text_align=TextNode.ALeft, text_font=DGG.getDefaultFont())
            cpLabel = DirectLabel(parent=frame, relief=None, pos=(1.4, 0.0, 0.0), text='', text_fg=(0, 0, 0, 1), text_scale=TTLocalizer.REPsmallLabel, text_align=TextNode.ALeft, text_font=DGG.getDefaultFont())
            ncpLabel = DirectLabel(parent=frame, relief=None, pos=(1.44, 0.0, 0.0), text='', text_fg=(1, 0, 0, 1), text_scale=TTLocalizer.REPsmallLabel, text_align=TextNode.ALeft, text_font=DGG.getDefaultFont())
            self.entryList.append((pLabel,
             fFrame,
             nLabel,
             tLabel,
             wLabel,
             cpLabel,
             ncpLabel))

        return

    def getRowPos(self, place):
        return Point3(-0.72, -0.01, 0.25 - place * 0.18)

    def displayRacer(self, place, headFrame, name, time, qualify, tickets, bonus, trophies, circuitPoints, circuitTime):
        self.notify.debug('displayRacer: place=%d name=%s tickets=%d bonus=%d' % (place,
         name,
         tickets,
         bonus))
        self.tickets[place] = tickets
        self.entryList[place - 1][0].configure(text_fg=(0.0, 0.0, 0.0, 1.0))
        if headFrame:
            headFrame.reparentTo(self.entryList[place - 1][1])
            headFrame.setPos(0, -1.0, 0)
            headFrame.setScale(0.25)
            headFrame.show()
        self.entryList[place - 1][2]['text'] = name
        if len(name) > 24:
            self.entryList[place - 1][2]['text_scale'] = 0.036
        else:
            self.entryList[place - 1][2]['text_scale'] = 0.04
        minutes = int(time / 60)
        time -= minutes * 60
        seconds = int(time)
        padding = (seconds < 10 and ['0'] or [''])[0]
        time -= seconds
        fraction = str(time)[2:4]
        fraction = fraction + '0' * (2 - len(fraction))
        timeStr = "%d'%s%d''%s" % (minutes,
            padding,
            seconds,
            fraction)
        self.entryList[place - 1][3].configure(text_fg=(0.0, 0.0, 0.0, 1.0))
        self.entryList[place - 1][3]['text'] = timeStr

        def flipText(flip, label = self.entryList[place - 1][3], timeStr = timeStr, recStr = TTLocalizer.KartRace_Record):
            self.entryList[place - 1][3].configure(text_scale=0.06)
            self.entryList[place - 1][3].configure(text_fg=(0.95, 0.0, 0.0, 1.0))
            if flip:
                self.entryList[place - 1][3].configure(text_font=DGG.getDefaultFont())
                self.entryList[place - 1][3]['text'] = timeStr
            else:
                self.entryList[place - 1][3].configure(text_font=ToontownGlobals.getSignFont())
                self.entryList[place - 1][3]['text'] = recStr

        bonusSeq = Sequence()
        if qualify and bonus:
            qText = TTLocalizer.KartRace_Qualified
            for i in range(1, 7):
                bonusSeq.append(Func(flipText, 0, recStr=qText))
                bonusSeq.append(Wait(0.5))
                bonusSeq.append(Func(flipText, 1))
                bonusSeq.append(Wait(0.5))
                bonusSeq.append(Func(flipText, 0))
                bonusSeq.append(Wait(0.5))
                bonusSeq.append(Func(flipText, 1))
                bonusSeq.append(Wait(0.5))

        elif qualify:
            qText = TTLocalizer.KartRace_Qualified
            for i in range(0, 12):
                bonusSeq.append(Func(flipText, i % 2, recStr=qText))
                bonusSeq.append(Wait(0.5))

        elif bonus:
            for i in range(0, 12):
                bonusSeq.append(Func(flipText, i % 2))
                bonusSeq.append(Wait(0.5))

        if trophies:
            DirectFrame(parent=headFrame, relief=None, image=loader.loadModel('phase_6/models/karting/trophy'), image_pos=(0.25, -1.01, -0.25), image_scale=0.25)

        def ticketTicker(t, label = self.entryList[place - 1][4], tickets = tickets):
            label['text'] = TTLocalizer.KartRace_TicketPhrase % int(t * tickets)

        ticketSeq = LerpFunc(ticketTicker, duration=2)
        displayPar = Parallel(bonusSeq, ticketSeq)
        displayPar.start()
        self.entryListSeqs.append(displayPar)
        if not circuitPoints == []:
            self.pointsLabel.show()
            newPoints = circuitPoints[:].pop()
            currentPoints = sum(circuitPoints[:-1])
            self.entryList[place - 1][5]['text'] = '%s' % currentPoints
            self.entryList[place - 1][6]['text'] = ' + %s' % newPoints

            def totalPointTicker(t, label = self.entryList[place - 1][5], current = currentPoints, new = newPoints):
                label['text'] = '%s' % int(currentPoints + t * new)

            def newPointTicker(t, label = self.entryList[place - 1][6], new = newPoints):
                label['text'] = '+%s' % int(new - t * new)

            def endTicker(newLabel = self.entryList[place - 1][6]):
                newLabel.hide()

            seq = Sequence(Wait(1), Parallel(LerpFunc(totalPointTicker, duration=1), LerpFunc(newPointTicker, duration=1)), Func(endTicker))
            self.pointSeqs.append(seq)

    def updateWinnings(self, place, newTotalTickets):
        self.notify.debug('updateWinnings: self.tickets=%s place=%d newTotalTickets=%d' % (self.tickets, place, newTotalTickets))
        winnings = newTotalTickets - self.tickets[place]
        if winnings != 0:
            self.entryListSeqs[place - 1].finish()
            newTickets = self.tickets[place] + winnings

            def ticketTicker(t, label = self.entryList[place - 1][4], tickets = newTickets):
                label['text'] = TTLocalizer.KartRace_TicketPhrase % int(t * tickets)

            ticketSeq = LerpFunc(ticketTicker, duration=2)
            ticketSeq.start()
            self.entryListSeqs[place - 1] = ticketSeq

    def circuitFinished(self, placeFixup):
        calcPointsSeq = Parallel()
        for seq in self.pointSeqs:
            calcPointsSeq.append(seq)

        shiftRacersSeq = Parallel()
        for oldPlace, newPlace in placeFixup:
            if oldPlace != newPlace:

                def fixPlaceValue(oldPlace = oldPlace, newPlace = newPlace):
                    self.entryList[oldPlace][0]['text'] = '%s -' % str(newPlace + 1)

                newPos = self.getRowPos(newPlace)
                shiftRacersSeq.append(Parallel(Func(fixPlaceValue), LerpPosInterval(self.rowFrame[oldPlace], 1, newPos)))

        self.circuitFinishSeq = Sequence(calcPointsSeq, shiftRacersSeq)
        if not len(self.race.circuitLoop) == 0:
            self.notify.debug('Not the last race in a circuit, pressing next race in 30 secs')
            self.circuitFinishSeq.append(Wait(30))
            self.circuitFinishSeq.append(Func(self.raceEndPanel.closeButtonPressed))
        self.circuitFinishSeq.start()

    def destroy(self):
        for seq in self.entryListSeqs:
            seq.finish()
            del seq

        del self.entryListSeqs
        if self.circuitFinishSeq:
            self.circuitFinishSeq.finish()
            del self.circuitFinishSeq
        del self.entryList
        del self.pointsLabel
        DirectFrame.destroy(self)


class RaceWinningsPanel(DirectFrame):

    def __init__(self, race, *args, **kwargs):
        opts = {'relief': None,
         'geom': DGG.getDefaultDialogGeom(),
         'geom_color': ToontownGlobals.GlobalDialogColor[:3] + (0.8,),
         'geom_scale': (1.75, 1, 0.75)}
        opts.update(kwargs)
        DirectFrame.__init__(self, *args, **opts)
        self.initialiseoptions(RaceWinningsPanel)
        self.race = race
        frame = DirectFrame(parent=self, relief=None, pos=(0, -0.01, 0))
        tFrame = DirectFrame(parent=frame, relief=None, pos=(0, 0, 0))
        tLabel = DirectLabel(parent=tFrame, relief=None, pos=(0.0, 0.0, 0.25), text=TTLocalizer.KartRace_Tickets, text_fg=(0.0, 0.0, 0.0, 1.0), text_scale=0.1, text_font=DGG.getDefaultFont())
        DirectLabel(parent=tFrame, relief=None, pos=(TTLocalizer.REPtextPosX, 0.0, 0.1), text=TTLocalizer.KartRace_Deposit + TTLocalizer.KartRace_Colon, text_fg=(0.0, 0.0, 0.0, 1.0), text_scale=TTLocalizer.REPlargeLabel, text_align=TextNode.ALeft, text_font=DGG.getDefaultFont())
        dLabel = DirectLabel(parent=tFrame, relief=None, pos=(0.05, 0.0, 0.1), text=TTLocalizer.KartRace_Zero, text_fg=(0.0, 0.0, 0.0, 1.0), text_scale=TTLocalizer.REPlargeLabel, text_align=TextNode.ARight, text_font=DGG.getDefaultFont())
        DirectLabel(parent=tFrame, relief=None, pos=(TTLocalizer.REPtextPosX, 0.0, 0.0), text=TTLocalizer.KartRace_Winnings + TTLocalizer.KartRace_Colon, text_fg=(0.0, 0.0, 0.0, 1.0), text_scale=TTLocalizer.REPlargeLabel, text_align=TextNode.ALeft, text_font=DGG.getDefaultFont())
        wLabel = DirectLabel(parent=tFrame, relief=None, pos=(0.05, 0.0, 0.0), text=TTLocalizer.KartRace_Zero, text_fg=(0.0, 0.0, 0.0, 1.0), text_scale=TTLocalizer.REPlargeLabel, text_align=TextNode.ARight, text_font=DGG.getDefaultFont())
        DirectLabel(parent=tFrame, relief=None, pos=(TTLocalizer.REPtextPosX, 0.0, -0.1), text=TTLocalizer.KartRace_Bonus + TTLocalizer.KartRace_Colon, text_fg=(0.0, 0.0, 0.0, 1.0), text_scale=TTLocalizer.REPlargeLabel, text_align=TextNode.ALeft, text_font=DGG.getDefaultFont())
        bLabel = DirectLabel(parent=tFrame, relief=None, pos=(0.05, 0.0, -0.1), text=TTLocalizer.KartRace_Zero, text_fg=(0.0, 0.0, 0.0, 1.0), text_scale=TTLocalizer.REPlargeLabel, text_align=TextNode.ARight, text_font=DGG.getDefaultFont())
        self.raceTotalLabel = DirectLabel(parent=tFrame, relief=None, pos=(TTLocalizer.REPtextPosX, 0.0, -0.2), text=TTLocalizer.KartRace_RaceTotal + TTLocalizer.KartRace_Colon, text_fg=(0.0, 0.0, 0.0, 1.0), text_scale=TTLocalizer.REPlargeLabel, text_align=TextNode.ALeft, text_font=DGG.getDefaultFont())
        self.circuitTotalLabel = DirectLabel(parent=tFrame, relief=None, pos=(TTLocalizer.REPtextPosX, 0.0, -0.2), text=TTLocalizer.KartRace_CircuitTotal + TTLocalizer.KartRace_Colon, text_fg=(0.0, 0.0, 0.0, 1.0), text_scale=TTLocalizer.REPlargeLabel, text_align=TextNode.ALeft, text_font=DGG.getDefaultFont())
        self.doubleTicketsLabel = DirectLabel(parent=tFrame, relief=None, pos=(0.5, 0.0, -0.26), text=TTLocalizer.KartRace_DoubleTickets, text_fg=(1.0, 0.125, 0.125, 1.0), text_scale=TTLocalizer.REPlargeLabel, text_align=TextNode.ACenter, text_shadow=(0, 0, 0, 1), text_font=DGG.getDefaultFont())
        fLabel = DirectLabel(parent=tFrame, relief=None, pos=(0.05, 0.0, -0.2), text=TTLocalizer.KartRace_Zero, text_fg=(0.0, 0.0, 0.0, 1.0), text_scale=TTLocalizer.REPlargeLabel, text_align=TextNode.ARight, text_font=DGG.getDefaultFont())
        ticketPic = DirectFrame(parent=tFrame, relief=None, image=loader.loadModel('phase_6/models/karting/tickets'), image_pos=(0.5, 0, -0.02), image_scale=0.4)
        self.ticketFrame = tFrame
        self.ticketComponents = (dLabel,
         wLabel,
         bLabel,
         fLabel)
        tFrame = DirectFrame(parent=frame, relief=None, pos=(0, 0, 0))
        tLabel = DirectLabel(parent=tFrame, relief=None, pos=(0.0, 0.0, 0.25), text=TTLocalizer.KartRace_Bonus, text_fg=(0.0, 0.0, 0.0, 1.0), text_scale=0.1, text_font=DGG.getDefaultFont())
        textFrame = DirectFrame(parent=tFrame, relief=None, text='', text_scale=TTLocalizer.REPlargeLabel, text_font=DGG.getDefaultFont(), text_pos=(-0.3, 0.1, 0))
        bonusPic = DirectFrame(parent=tFrame, relief=None, image=loader.loadModel('phase_6/models/karting/tickets'), image_pos=(0.5, 0, -0.02), image_scale=0.4)
        self.bonusFrame = tFrame
        self.bonusComponents = (textFrame, bonusPic)
        tFrame = DirectFrame(parent=frame, relief=None, pos=(0, 0, 0))
        tLabel = DirectLabel(parent=tFrame, relief=None, pos=(0.0, 0.0, 0.25), text=TTLocalizer.KartRace_Trophies, text_fg=(0.0, 0.0, 0.0, 1.0), text_scale=0.1, text_font=DGG.getDefaultFont())
        textFrame = DirectFrame(parent=tFrame, relief=None, text='', text_scale=TTLocalizer.REPlargeLabel, text_font=DGG.getDefaultFont(), text_pos=(-0.3, 0.1, 0))
        trophyPic = DirectFrame(parent=tFrame, relief=None)
        self.trophyFrame = tFrame
        self.trophyComponents = (textFrame, trophyPic)
        self.ticketFrame.hide()
        self.bonusFrame.hide()
        self.trophyFrame.hide()
        return

    def generateDisplaySequences(self, track, ticDeposit, ticWon, ticBonus, trophies, endOfCircuitRace = False):

        def ticketTicker(t, label, startTickets, endTickets):
            label['text'] = str(int(t * endTickets + (1 - t) * startTickets))

        def wrapStr(str = '', maxWidth = 10, font = DGG.getDefaultFont()):
            textNode = TextNode('WidthChecker')
            textNode.setFont(font)
            tokens = str.split()
            outStr = ''
            lineStr = ''
            tempStr = ''
            while tokens:
                if lineStr:
                    tempStr = ' '.join([lineStr, tokens[0]])
                else:
                    tempStr = tokens[0]
                if textNode.calcWidth(tempStr) > maxWidth:
                    if not outStr:
                        outStr = lineStr
                    else:
                        outStr = '\n'.join([outStr, lineStr])
                    lineStr = tokens.pop(0)
                else:
                    lineStr = tempStr
                    tokens.pop(0)

            if lineStr:
                if not outStr:
                    outStr = lineStr
                else:
                    outStr = '\n'.join([outStr, lineStr])
            return outStr

        ticketSeq = Sequence()
        origTicBonus = ticBonus
        bonusType = None
        if ticBonus > 0:
            if not endOfCircuitRace:
                bonusType = list(RaceGlobals.PeriodDict.values()).index(ticBonus)
            else:
                ticBonus = 0
        if endOfCircuitRace:
            self.circuitTotalLabel.unstash()
            self.raceTotalLabel.stash()
        else:
            self.circuitTotalLabel.stash()
            self.raceTotalLabel.unstash()
        if ToontownGlobals.KARTING_TICKETS_HOLIDAY not in base.cr.newsManager.getHolidayIdList() or self.race.raceType != RaceGlobals.Practice:
            self.doubleTicketsLabel.stash()
        if ticBonus:
            ticketSeq.append(Sequence(Func(self.ticketFrame.hide), Func(self.bonusFrame.show), Func(self.trophyFrame.hide), Func(self.bonusComponents[0].configure, text=wrapStr(TTLocalizer.KartRace_RecordString % (TTLocalizer.KartRecordStrings[bonusType], TTLocalizer.KartRace_TrackNames[track], str(ticBonus)))), Wait(3)))
        ticketSeq.append(Sequence(Func(self.bonusFrame.hide), Func(self.trophyFrame.hide), Func(self.ticketFrame.show), Func(self.ticketComponents[3].configure, text_color=Vec4(0, 0, 0, 1)), Func(self.ticketComponents[0].configure, text_color=Vec4(1, 0, 0, 1)), Parallel(LerpFunc(ticketTicker, duration=(ticDeposit and [1] or [0])[0], extraArgs=[self.ticketComponents[0], 0, ticDeposit]), LerpFunc(ticketTicker, duration=(ticDeposit and [1] or [0])[0], extraArgs=[self.ticketComponents[3], 0, ticDeposit])), Func(self.ticketComponents[0].configure, text_color=Vec4(0, 0, 0, 1)), Func(self.ticketComponents[1].configure, text_color=Vec4(1, 0, 0, 1)), Parallel(LerpFunc(ticketTicker, duration=(ticWon and [1] or [0])[0], extraArgs=[self.ticketComponents[1], 0, ticWon]), LerpFunc(ticketTicker, duration=(ticWon and [1] or [0])[0], extraArgs=[self.ticketComponents[3], ticDeposit, ticDeposit + ticWon])), Func(self.ticketComponents[1].configure, text_color=Vec4(0, 0, 0, 1)), Func(self.ticketComponents[2].configure, text_color=Vec4(1, 0, 0, 1)), Parallel(LerpFunc(ticketTicker, duration=(origTicBonus and [1] or [0])[0], extraArgs=[self.ticketComponents[2], 0, origTicBonus]), LerpFunc(ticketTicker, duration=(origTicBonus and [1] or [0])[0], extraArgs=[self.ticketComponents[3], ticDeposit + ticWon, ticDeposit + ticWon + origTicBonus])), Func(self.ticketComponents[2].configure, text_color=Vec4(0, 0, 0, 1)), Func(self.ticketComponents[3].configure, text_color=Vec4(1, 0, 0, 1))))
        winningsSeq = Sequence(Func(self.ticketFrame.show), Func(self.bonusFrame.hide), Func(self.trophyFrame.hide), Wait(5))
        if ticBonus:
            winningsSeq.append(Sequence(Func(self.ticketFrame.hide), Func(self.bonusFrame.show), Func(self.trophyFrame.hide), Wait(5)))

        def showCorrectTrophy(trophyId):
            if hasattr(self, 'trophyImage'):
                self.trophyImage.destroy()
            self.trophyImage = RacingTrophy(level=trophyId, parent=self.trophyComponents[1], pos=(0.5, 0, -0.25))
            if trophyId == RaceGlobals.GrandTouring or trophyId == RaceGlobals.TotalQuals or trophyId == RaceGlobals.TotalWins:
                scale = self.trophyImage.getScale()
                scale = scale * 0.5
                self.trophyImage.setScale(scale)

        base.trop = self
        if trophies:
            winningsSeq.append(Sequence(Func(self.ticketFrame.hide), Func(self.bonusFrame.hide), Func(self.trophyFrame.show)))
            for x in trophies:
                winningsSeq.append(Sequence(Func(self.trophyComponents[0].configure, text=wrapStr(TTLocalizer.KartTrophyDescriptions[x])), Func(showCorrectTrophy, x), Wait(5)))

        return (ticketSeq, winningsSeq)


class RaceEndPanel(DirectFrame):

    def __init__(self, numRacers, race, *args, **kwargs):
        opts = {'relief': None}
        opts.update(kwargs)
        DirectFrame.__init__(self, *args, **opts)
        self.initialiseoptions(RaceEndPanel)
        self.enabled = False
        self.race = race
        self.results = RaceResultsPanel(numRacers, race, self, parent=self, pos=(0, 0, 0.525))
        self.winnings = RaceWinningsPanel(race, parent=self, pos=(0, 0, -0.525))
        if len(self.race.circuitLoop) == 0:
            exitText = TTLocalizer.KartRace_Exit
        else:
            exitText = TTLocalizer.KartRace_NextRace
        gui = loader.loadModel('phase_3.5/models/gui/avatar_panel_gui')
        self.closeButton = DirectButton(parent=self, image=(gui.find('**/CloseBtn_UP'),
         gui.find('**/CloseBtn_DN'),
         gui.find('**/CloseBtn_Rllvr'),
         gui.find('**/CloseBtn_UP')), relief=None, scale=2.0, text=exitText, text_scale=TTLocalizer.REPsmallLabel, text_pos=(0, -0.1), text_fg=VBase4(1, 1, 1, 1), pos=(1.1, 0, -0.5), command=self.closeButtonPressed)
        self.closeButton.hide()
        self.disable()
        return

    def destroy(self):
        taskMgr.remove('showExitButton')
        try:
            if self.seq:
                self.seq.pause()
            self.seq = None
        except AttributeError:
            pass

        DirectFrame.destroy(self)
        return

    def enable(self):
        self.show()
        self.enabled = True

    def disable(self):
        self.hide()
        self.enabled = False

    def closeButtonPressed(self):
        messenger.send('leaveRace')

    def displayRacer(self, place, entryFee, qualify, winnings, track, bonus, trophies, headFrame, name, time, circuitPoints, circuitTime):
        self.results.displayRacer(place, headFrame, name, time, qualify, entryFee + winnings + bonus, bonus, trophies, circuitPoints, circuitTime)

    def updateWinnings(self, place, winnings):
        self.results.updateWinnings(place, winnings)

    def updateWinningsFromCircuit(self, place, entryFee, winnings, bonus, trophies = ()):
        print('updateWinningsFromCircuit')
        self.seq.finish()
        totalTickets = winnings + entryFee + bonus
        self.results.updateWinnings(place, totalTickets)
        self.startWinningsPanel(entryFee, winnings, 0, bonus, trophies, True)

    def startWinningsPanel(self, entryFee, winnings, track, bonus = None, trophies = (), endOfCircuitRace = False):
        if not self.enabled:
            return
        taskMgr.remove('showExitButton')
        try:
            if self.seq:
                self.seq.pause()
            self.seq = None
        except AttributeError:
            pass

        tSeq, wSeq = self.winnings.generateDisplaySequences(track, entryFee, winnings, bonus, trophies, endOfCircuitRace)

        def showButton(s = self, w = wSeq):
            s.seq.finish()
            s.seq = Sequence(Func(self.closeButton.show), wSeq)
            s.seq.loop()

        self.seq = Sequence(tSeq, wSeq)
        if self.race.raceType != RaceGlobals.Circuit:
            if self.seq.getDuration() < 5.0:
                taskMgr.doMethodLater(5.0, showButton, 'showExitButton', extraArgs=[])
            else:
                taskMgr.doMethodLater(self.seq.getDuration(), showButton, 'showExitButton', extraArgs=[])
        self.seq.start()
        return

    def circuitFinished(self, placeFixup):
        self.closeButton.show()
        self.results.circuitFinished(placeFixup)
