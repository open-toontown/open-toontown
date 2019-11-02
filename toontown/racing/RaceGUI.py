from pandac.PandaModules import *
from direct.showbase.PythonUtil import clampScalar
from direct.distributed.ClockDelta import *
from direct.distributed import DistributedObject
from direct.directnotify import DirectNotifyGlobal
from direct.gui.DirectLabel import *
from direct.gui.DirectButton import *
from direct.showbase import BulletinBoardWatcher
from direct.interval.IntervalGlobal import *
from otp.otpbase import OTPGlobals
from direct.interval.IntervalGlobal import *
from toontown.toonbase import ToontownGlobals, TTLocalizer
from toontown.racing.KartDNA import InvalidEntry, getAccessory, getDefaultColor
from toontown.racing.RaceHeadFrame import RaceHeadFrame
from toontown.racing.RaceGag import RaceGag
from toontown.racing.RaceEndPanels import RaceEndPanel
from toontown.racing import RaceGlobals
from pandac.PandaModules import CardMaker, OrthographicLens, LineSegs
from direct.particles.ParticleEffect import *
from math import fmod
from math import sqrt
import time
import operator
from direct.gui.DirectGui import DirectFrame
import random

class RaceGUI:
    GagPie = 0
    gagRoot = 'phase_3.5/maps/inventory_'

    class RacerInfo:

        def __init__(self, face, mapSpot):
            self.curvetime = 0
            self.maxlaphit = 0
            self.face = face
            self.mapspot = mapSpot
            self.place = 1
            self.enabled = True
            self.finished = False
            self.gag = None
            return

        def update(self, curvetime = None, maxlaphit = None, faceX = None, mapspotPt = None, place = None, finished = None):
            if self.enabled:
                if not curvetime == None:
                    self.curvetime = curvetime
                if not maxlaphit == None:
                    self.maxlaphit = maxlaphit
                if not faceX == None:
                    self.face.setX(faceX)
                if not mapspotPt == None:
                    self.mapspot.setPos(mapspotPt)
                if not place == None:
                    self.place = place
                if not finished == None:
                    self.finished = finished
            return

        def disable(self):
            self.enabled = False
            if not self.finished:
                self.face.hide()
            self.mapspot.hide()

        def enable(self):
            self.enabled = True
            self.face.show()
            self.mapspot.show()

    def __init__(self, distRace):
        self.race = distRace
        self.timerEnabled = False
        self.maxLapHit = 0
        self.photoFinish = False
        toonInteriorTextures = loader.loadModel('phase_3.5/models/modules/toon_interior_textures')
        invTextures = loader.loadModel('phase_3.5/models/gui/inventory_icons')
        racingTextures = loader.loadModel('phase_6/models/karting/racing_textures')
        self.gagTextures = [toonInteriorTextures.find('**/couch'),
         invTextures.find('**/inventory_bannana_peel'),
         racingTextures.find('**/boost_arrow'),
         invTextures.find('**/inventory_anvil'),
         invTextures.find('**/inventory_creampie')]
        self.gagTextures[1].setScale(7.5)
        self.gagTextures[3].setScale(7.5)
        self.gagTextures[4].setScale(7.5)
        self.cardMaker = CardMaker('card')
        self.racerDict = {}
        self.render2dRoot = render2d.attachNewNode('RaceGuiRender2dRoot')
        self.render2dRoot.setDepthWrite(1)
        self.directObjList = []
        self.aspect2dRoot = aspect2d.attachNewNode('RaceGuiAspect2dRoot')
        self.aspect2dRoot.setDepthWrite(1)
        self.raceModeRoot = self.aspect2dRoot.attachNewNode('RaceModeRoot')
        gui = loader.loadModel('phase_3.5/models/gui/avatar_panel_gui')
        self.closeButton = DirectButton(image=(gui.find('**/CloseBtn_UP'),
         gui.find('**/CloseBtn_DN'),
         gui.find('**/CloseBtn_Rllvr'),
         gui.find('**/CloseBtn_UP')), relief=None, scale=1.05, text=TTLocalizer.KartRace_Leave, text_scale=0.04, text_pos=(0, -0.07), text_fg=VBase4(1, 1, 1, 1), pos=(-0.99, 0, 0.925), command=self.race.leaveRace)
        self.closeButton.reparentTo(self.aspect2dRoot)
        self.directObjList.append(self.closeButton)
        self.raceTimeDelta = 0
        self.raceModeReady = False
        self.resultModeReady = False
        self.gagCycleSound = base.loadSfx('phase_3.5/audio/sfx/tick_counter.mp3')
        if hasattr(self.gagCycleSound, 'setPlayRate'):
            self.gagCycleSound.setPlayRate(0.2)
        self.gagCycleSound.setLoop(1)
        self.gagAcquireSound = base.loadSfx('phase_6/audio/sfx/SZ_MM_gliss.mp3')
        self.disable()
        return

    def initRaceMode(self):
        self.mapScene = self.raceModeRoot.attachNewNode('MapScene')
        self.mapScene.setPos(1.1, 0, 0.75)
        self.mapScene.setScale(0.25, 0.001, 0.25)
        maxT = self.race.curve.getMaxT()
        pt = Vec3(0, 0, 0)
        ls = LineSegs('MapLines')
        ls.setColor(1, 1, 1, 1)
        ls.setThickness(2)
        for x in range(101):
            self.race.curve.getPoint(x / 100.0 * maxT, pt)
            if x == 0:
                ls.moveTo(pt[0], pt[1], pt[2])
            else:
                ls.drawTo(pt[0], pt[1], pt[2])

        self.mapLines = self.mapScene.attachNewNode(ls.create())
        self.mapLines.setScale(0.00025 * RaceGlobals.TrackDict[self.race.trackId][6])
        self.mapLines.setP(90)
        self.faceStartPos = Vec3(-0.8, 0, 0.93)
        self.faceEndPos = Vec3(0.8, 0, 0.93)
        self.placeLabelNum = DirectLabel(relief=None, pos=TTLocalizer.RGUIplaceLabelNumPos, text='1', text_scale=0.35, text_fg=(0.95, 0.95, 0, 1), text_font=ToontownGlobals.getSignFont())
        self.placeLabelNum.reparentTo(self.raceModeRoot)
        self.directObjList.append(self.placeLabelNum)
        self.placeLabelStr = DirectLabel(relief=None, pos=TTLocalizer.RGUIplaceLabelStrPos, text=TTLocalizer.KartRace_FirstSuffix, text_scale=0.1, text_fg=(0.95, 0.95, 0, 1), text_font=ToontownGlobals.getSignFont())
        self.placeLabelStr.reparentTo(self.raceModeRoot)
        self.directObjList.append(self.placeLabelStr)
        self.lapLabel = DirectLabel(relief=None, pos=(1.1, 0, 0.45), text='1/' + str(self.race.lapCount), text_scale=0.1, text_fg=(0.95, 0.95, 0, 1), text_font=ToontownGlobals.getSignFont())
        self.lapLabel.reparentTo(self.raceModeRoot)
        self.directObjList.append(self.lapLabel)
        self.photoFinishLabel = DirectLabel(relief=None, pos=(0, 0, -0.1), text=TTLocalizer.KartRace_PhotoFinish, text_scale=TTLocalizer.RGUIphotoFinish, text_fg=(0.95, 0.95, 0, 1), text_font=ToontownGlobals.getSignFont())
        self.photoFinishLabel.hide()
        self.directObjList.append(self.photoFinishLabel)
        self.wrongWayLabel = DirectLabel(relief=None, pos=(1.1, 0, 0.85), text=TTLocalizer.KartRace_WrongWay, text_scale=0.1, text_fg=(0.95, 0, 0, 1), text_font=ToontownGlobals.getSignFont())
        self.wrongWayLabel.reparentTo(self.raceModeRoot)
        self.directObjList.append(self.wrongWayLabel)
        self.wrongWayLabel.setColorScale(Vec4(1, 1, 1, 0))
        self.wrongWaySeq = Sequence(self.wrongWayLabel.colorScaleInterval(0.25, colorScale=Vec4(1, 1, 1, 1), startColorScale=Vec4(1, 1, 1, 0)), self.wrongWayLabel.colorScaleInterval(0.25, colorScale=Vec4(1, 1, 1, 0), startColorScale=Vec4(1, 1, 1, 1)))
        interpolateFacePos = lambda x: self.faceStartPos * (1.0 - x) + self.faceEndPos * x
        self.timeLabels = []
        for x in range(self.race.lapCount):
            minLabel = DirectLabel(relief=None, pos=(interpolateFacePos((2.0 * x + 1) / (self.race.lapCount * 2))[0] - 0.06, 0, 0.84), text="0'", text_scale=0.06, text_fg=(0.95, 0.95, 0, 1), text_font=ToontownGlobals.getSignFont(), text_align=TextNode.ARight)
            minLabel.reparentTo(self.raceModeRoot)
            self.directObjList.append(minLabel)
            secLabel = DirectLabel(relief=None, pos=(interpolateFacePos((2.0 * x + 1) / (self.race.lapCount * 2))[0] + 0.06, 0, 0.84), text="00''", text_scale=0.06, text_fg=(0.95, 0.95, 0, 1), text_font=ToontownGlobals.getSignFont(), text_align=TextNode.ARight)
            secLabel.reparentTo(self.raceModeRoot)
            self.directObjList.append(secLabel)
            fractionLabel = DirectLabel(relief=None, pos=(interpolateFacePos((2.0 * x + 1) / (self.race.lapCount * 2))[0] + 0.14, 0, 0.84), text='00', text_scale=0.06, text_fg=(0.95, 0.95, 0, 1), text_font=ToontownGlobals.getSignFont(), text_align=TextNode.ARight)
            fractionLabel.reparentTo(self.raceModeRoot)
            self.directObjList.append(fractionLabel)
            self.timeLabels.append((minLabel, secLabel, fractionLabel))

        self.cardMaker.reset()
        self.cardMaker.setName('GagIndicator')
        self.cardMaker.setFrame(-0.5, 0.5, -0.5, 0.5)
        self.cardMaker.setColor(1, 1, 1, 1)
        self.gagPanel = DirectFrame(parent=self.raceModeRoot, relief=None, image=loader.loadModel('phase_6/models/karting/gag_panel'), image_scale=0.25, pos=(-1.13, 0, -0.5))
        self.directObjList.append(self.gagPanel)
        self.gag = self.gagPanel.attachNewNode('gag')
        self.gag.setScale(0.2)
        for gag in self.gagTextures:
            gag.reparentTo(self.gag)
            gag.hide()

        self.cardMaker.reset()
        self.cardMaker.setName('RaceProgressLine')
        self.cardMaker.setFrame(-0.5, 0.5, -0.5, 0.5)
        line = self.raceModeRoot.attachNewNode(self.cardMaker.generate())
        line.setScale(self.faceEndPos[0] - self.faceStartPos[0], 1, 0.01)
        line.setPos(0, 0, self.faceStartPos[2])
        self.cardMaker.setName('RaceProgressLineHash')
        for n in range(self.race.lapCount + 1):
            hash = self.raceModeRoot.attachNewNode(self.cardMaker.generate())
            hash.setScale(line.getScale()[2], 1, line.getScale()[2] * 5)
            t = float(n) / self.race.lapCount
            hash.setPos(self.faceStartPos[0] * (1 - t) + self.faceEndPos[0] * t, self.faceStartPos[1], self.faceStartPos[2])

        self.raceModeReady = True
        self.disable()
        return

    def initResultMode(self):
        self.endPanel = RaceEndPanel(len(self.race.avIds), self.race)
        self.endPanel.reparentTo(self.aspect2dRoot)
        self.directObjList.append(self.endPanel)
        self.resultModeReady = True
        self.disable()

    def showGag(self, gagIndex):
        if gagIndex < len(self.gagTextures):
            for gag in self.gagTextures:
                gag.hide()

            self.gagTextures[gagIndex].show()

    def updateGag(self, gagIndex):
        if self.gag:
            if hasattr(self, 'gagCycleInterval'):
                self.gagCycleInterval.finish()
                del self.gagCycleInterval
            self.gag.setHpr(0, 0, 0)
            self.showGag(gagIndex)
            if gagIndex == 0:
                self.gag.hide()
            else:
                self.gag.show()
                self.gagAcquireSound.play()
                self.gagAcquireInterval = LerpHprInterval(self.gag, duration=0.5, blendType='easeOut', startHpr=Point3(0, -90, 0), hpr=Point3(0, 0, 0))
                self.gagAcquireInterval.start()

    def waitingOnGag(self, cycleTime):
        if self.gag:
            numTextures = len(self.gagTextures)
            startOffset = random.choice(range(0, numTextures))
            self.gag.show()
            self.gagCycleInterval = Parallel(LerpFunc(self.showNextGag, fromData=startOffset, toData=numTextures * 2 * cycleTime + startOffset, blendType='easeOut', duration=cycleTime), LerpHprInterval(self.gag, duration=cycleTime, hpr=Point3(0, 180 * numTextures * 2 * cycleTime - 90, 0), blendType='easeOut', startHpr=Point3(0, 0, 0)), SoundInterval(self.gagCycleSound, loop=1, duration=cycleTime, startTime=0), name='gagCycleInterval')
            self.gagCycleInterval.start()

    def showNextGag(self, t):
        if self.gag:
            currGagIndex = int(t % (len(self.gagTextures) - 1)) + 1
            self.showGag(currGagIndex)

    def enableSpeedometer(self):
        self.race.localKart.showSpeedometer()

    def disableSpeedometer(self):
        self.race.localKart.hideSpeedometer()

    def disableRaceMode(self):
        self.disableSpeedometer()
        self.render2dRoot.hide()
        self.raceModeRoot.hide()
        for x in self.timeLabels:
            for y in x:
                y.hide()

        self.setTimerEnabled(False)

    def disableResultMode(self):
        self.endPanel.disable()

    def disable(self):
        self.closeButton.hide()
        taskMgr.removeTasksMatching('clearRaceEndPanel')
        if self.raceModeReady:
            self.disableRaceMode()
        if self.resultModeReady:
            self.disableResultMode()

    def enableRaceMode(self):
        self.enableSpeedometer()
        self.render2dRoot.show()
        self.raceModeRoot.show()
        self.maxLapHit = min(self.maxLapHit, self.race.lapCount - 1)
        for x in range(self.maxLapHit + 1):
            for y in self.timeLabels[x]:
                y.configure(text_font=ToontownGlobals.getSignFont())
                y.show()

        for y in self.timeLabels[self.maxLapHit]:
            y.configure(text_font=ToontownGlobals.getSignFont())

    def enableResultMode(self):
        self.endPanel.enable()
        if not self.race.circuitLoop:
            taskMgr.doMethodLater(180, self.endPanel.closeButtonPressed, 'clearRaceEndPanel', extraArgs=[])

    def destroy(self):
        self.disable()
        if hasattr(self, 'wrongWaySeq'):
            self.wrongWaySeq.finish()
            self.wrongWaySeq = None
        taskMgr.removeTasksMatching('removeIt')
        taskMgr.removeTasksMatching('removeCam*')
        taskMgr.removeTasksMatching('clearRaceEndPanel')
        for obj in self.directObjList:
            obj.destroy()

        if hasattr(self, 'mapScene'):
            self.mapScene.removeNode()
            self.mapScene = None
        self.aspect2dRoot.removeNode()
        self.aspect2dRoot = None
        self.raceModeRoot.removeNode()
        self.raceModeRoot = None
        self.render2dRoot.removeNode()
        self.render2dRoot = None
        self.closeButton = None
        self.gag = None
        self.lapLabel = None
        self.timeLabels = None
        self.placeLabelStr = None
        self.placeLabelNum = None
        self.photoFinishLabel = None
        self.mapScene = None
        self.race = None
        return

    def setSpotAsymptotic(self, diffT, spot):
        p = (-1, 1)[diffT > 0] * (1 - 1 / pow(abs(diffT) / self.cutoff + 1, 2))
        spot.setX(p)

    def setSpotRaceLinear(self, t, spot):
        spot.setX(-1.0 + 2.0 * (t / self.lapCount))

    def setSpotLapLinear(self, t, spot):
        spot.setX(-1.0 + 2.0 * (t - int(t)))

    def update(self, time):
        placeSorter = []
        placeCount = 0
        for key in self.racerDict.keys():
            racer = self.racerDict[key]
            curvetime = racer.curvetime
            face = racer.face
            mapspot = racer.mapspot
            maxlaphit = racer.maxlaphit
            if not racer.finished and racer.enabled:
                placeSorter.append((curvetime, key))
            if racer.finished or racer.enabled:
                placeCount += 1
            pt = Vec3(0, 0, 0)
            mapT = (curvetime % 1 + self.race.startT / self.race.curve.getMaxT()) % 1 * self.race.curve.getMaxT()
            self.race.curve.getPoint(mapT, pt)
            self.race.curve.getPoint(mapT % self.race.curve.getMaxT(), pt)
            lapT = clampScalar(curvetime / self.race.lapCount, 0.0, 1.0)
            faceX = self.faceStartPos[0] * (1 - lapT) + self.faceEndPos[0] * lapT
            racer.update(faceX=faceX, mapspotPt=pt)
            t = time - self.race.baseTime - self.raceTimeDelta
            if key == localAvatar.doId:
                if self.race.laps > maxlaphit:
                    racer.update(maxlaphit=self.race.laps)
                    self.maxLapHit = racer.maxlaphit
                    if self.maxLapHit < self.race.lapCount:
                        for y in self.timeLabels[self.maxLapHit - 1]:
                            y.configure(text_font=ToontownGlobals.getSignFont())

                        for y in self.timeLabels[self.maxLapHit]:
                            y.show()

                        for y in self.timeLabels[self.maxLapHit]:
                            y.configure(text_font=ToontownGlobals.getSignFont())

                        self.raceTimeDelta = globalClock.getFrameTime() - self.race.baseTime
                        lapNotice = DirectLabel()
                        lapNotice.setScale(0.1)
                        if self.maxLapHit == self.race.lapCount - 1:
                            lapNotice['text'] = TTLocalizer.KartRace_FinalLapText
                        else:
                            lapNotice['text'] = TTLocalizer.KartRace_LapText % str(self.maxLapHit + 1)
                        taskMgr.doMethodLater(2, lapNotice.remove, 'removeIt', extraArgs=[])
                self.lapLabel['text'] = str(clampScalar(self.maxLapHit + 1, 1, self.race.lapCount)) + '/' + str(self.race.lapCount)

        suffix = {1: TTLocalizer.KartRace_FirstSuffix,
         2: TTLocalizer.KartRace_SecondSuffix,
         3: TTLocalizer.KartRace_ThirdSuffix,
         4: TTLocalizer.KartRace_FourthSuffix}
        placeSorter.sort()
        for x, p in zip(placeSorter, xrange(len(placeSorter), 0, -1)):
            self.racerDict[x[1]].update(place=p + placeCount - len(placeSorter))

        localRacer = self.racerDict[localAvatar.doId]
        nearDiff, farDiff = RaceGlobals.TrackDict[self.race.trackId][8]
        if not localRacer.finished and self.faceEndPos[0] - localRacer.face.getX() < nearDiff:
            for racerId in self.racerDict.keys():
                racer = self.racerDict[racerId]
                if not racer.enabled or racerId == localAvatar.doId or racer.face.getX() >= self.faceEndPos[0]:
                    continue
                if self.faceEndPos[0] - racer.face.getX() < farDiff:
                    self.photoFinish = True

        if self.photoFinish:
            self.photoFinishLabel.show()
            self.placeLabelNum['text'] = ''
            self.placeLabelStr['text'] = ''
        else:
            self.photoFinishLabel.hide()
            self.placeLabelNum['text'] = str(self.racerDict[localAvatar.doId].place)
            self.placeLabelStr['text'] = suffix[self.racerDict[localAvatar.doId].place]
        minutes = int(t / 60)
        t -= minutes * 60
        seconds = int(t)
        padding = (seconds < 10 and ['0'] or [''])[0]
        t -= seconds
        fraction = str(t)[2:4]
        fraction = fraction + '0' * (2 - len(fraction))
        if self.timerEnabled and self.maxLapHit < self.race.lapCount:
            self.timeLabels[self.maxLapHit][0]['text'] = "%d'" % minutes
            self.timeLabels[self.maxLapHit][1]['text'] = "%s%d''" % (padding, seconds)
            self.timeLabels[self.maxLapHit][2]['text'] = '%s' % fraction
        if self.race.wrongWay and not self.wrongWaySeq.isPlaying():
            self.wrongWaySeq.loop()
        elif not self.race.wrongWay and self.wrongWaySeq.isPlaying():
            self.wrongWaySeq.finish()

    def updateRacerInfo(self, avId, curvetime = None, maxlaphit = None):
        if avId in self.racerDict.keys():
            self.racerDict[avId].update(curvetime=curvetime, maxlaphit=maxlaphit)

    def racerEntered(self, avId):
        toon = base.cr.doId2do.get(avId, None)
        kart = base.cr.doId2do.get(self.race.kartMap.get(avId, None), None)
        if not toon or not kart:
            return
        if kart.getBodyColor() == InvalidEntry:
            bodyColor = getDefaultColor()
        else:
            bodyColor = getAccessory(kart.getBodyColor())
        headframe = RaceHeadFrame(av=toon, color=bodyColor)
        eyes = headframe.head.find('**/eyes*')
        eyes.setDepthTest(1)
        eyes.setDepthWrite(1)
        headframe.configure(geom_scale=(0.5, 0.5, 0.5))
        headframe.setZ(self.faceStartPos[2])
        headframe.setDepthWrite(True)
        headframe.setDepthTest(True)
        headframe.reparentTo(self.raceModeRoot)
        self.directObjList.append(headframe)
        mapspot = loader.loadModel('phase_6/models/karting/race_mapspot')
        mapspot.setColor(bodyColor)
        mapspot.reparentTo(self.mapLines)
        mapspot.setHpr(self.mapScene, 0, 0, 0)
        self.racerDict[avId] = self.RacerInfo(headframe, mapspot)
        for key, i in zip(self.racerDict.keys(), range(len(self.racerDict.keys()))):
            face = self.racerDict[key].face
            mapspot = self.racerDict[key].mapspot
            face.setX(self.faceStartPos[0])
            face.setY(-1 - 5 * (i + 1))
            face.setScale(0.15)
            mapspot.getChild(0).setY((-5 - 5 * (i + 1)) * 1000)
            mapspot.setScale(self.mapScene, 0.15)
            mapspot.setPos(self.race.startingPos[0][0])
            if key == localAvatar.doId:
                face.setY(-1)
                face.setScale(face.getScale() * 1.25)
                mapspot.getChild(0).setY(-5 * 1000)
                mapspot.setScale(mapspot.getScale() * 1.25)
                self.face = face
                self.mapspot = mapspot

        return

    def racerLeft(self, avId, unexpected = False):
        racer = self.racerDict.get(avId, None)
        if racer:
            racer.disable()
        return

    def racerFinished(self, avId, trackId, place, totalTime, entryFee, qualify, winnings, bonus, trophies, circuitPoints, circuitTime):
        racer = self.racerDict.get(avId, None)
        if racer:
            racer.update(finished=True)
            racer.disable()
            self.endPanel.displayRacer(place, entryFee, qualify, winnings, trackId, bonus, trophies, racer.face, base.cr.doId2do[avId].getName(), totalTime, circuitPoints, circuitTime)
            self.directObjList.remove(racer.face)
            if avId == localAvatar.doId:
                self.disableRaceMode()
                self.enableResultMode()
                self.endPanel.startWinningsPanel(entryFee, winnings, trackId, bonus, trophies)
        return

    def racerFinishedCircuit(self, avId, place, entryFee, winnings, bonus, trophies):
        racer = self.racerDict.get(avId, None)
        if racer:
            newTotalTickets = winnings + entryFee + bonus
            self.endPanel.updateWinnings(place, newTotalTickets)
            if avId == localAvatar.doId:
                self.endPanel.updateWinningsFromCircuit(place, entryFee, winnings, bonus, trophies)
        return

    def circuitFinished(self, placeFixup):
        self.endPanel.circuitFinished(placeFixup)

    def setTimerEnabled(self, enabled):
        self.timerEnabled = enabled
