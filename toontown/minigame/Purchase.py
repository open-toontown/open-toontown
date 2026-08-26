from panda3d.otp import *
from .PurchaseBase import *
from direct.task.Task import Task
from toontown.toon import ToonHead
from toontown.toonbase import ToontownTimer
from direct.gui import DirectGuiGlobals as DGG
from direct.directnotify import DirectNotifyGlobal
from direct.showbase.PythonUtil import Functor
from toontown.minigame import TravelGameGlobals
from toontown.distributed import DelayDelete
from toontown.toonbase import ToontownGlobals
from . import MinigameGlobals
COUNT_UP_RATE = 0.15
COUNT_UP_DURATION = 0.5
DELAY_BEFORE_COUNT_UP = 1.0
DELAY_AFTER_COUNT_UP = 1.0
COUNT_DOWN_RATE = 0.075
COUNT_DOWN_DURATION = 0.5
DELAY_AFTER_COUNT_DOWN = 0.0
DELAY_AFTER_CELEBRATE = 2.6
COUNT_SFX_MIN_DELAY = 0.034
COUNT_SFX_START_T = 0.079
OVERMAX_SFX_MIN_DELAY = 0.067
OVERMAX_SFX_START_T = 0.021

class Purchase(PurchaseBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('Purchase')

    def __init__(self, toon, pointsArray, playerMoney, ids, states, remain, doneEvent, metagameRound = -1, votesArray = None):
        PurchaseBase.__init__(self, toon, doneEvent)
        self.ids = ids
        self.pointsArray = pointsArray
        self.playerMoney = playerMoney
        self.states = states
        self.remain = remain
        self.tutorialMode = 0
        self.metagameRound = metagameRound
        self.votesArray = votesArray
        self.voteMultiplier = 1
        self.fsm.addState(State.State('reward', self.enterReward, self.exitReward, ['purchase']))
        doneState = self.fsm.getStateNamed('done')
        doneState.addTransition('reward')
        self.unexpectedEventNames = []
        self.unexpectedExits = []
        self.setupUnexpectedExitHooks()

    def load(self):
        purchaseModels = loader.loadModel('phase_4/models/gui/purchase_gui')
        PurchaseBase.load(self, purchaseModels)
        interiorPhase = 3.5
        self.bg = loader.loadModel('phase_%s/models/modules/toon_interior' % interiorPhase)
        self.bg.setPos(0.0, 5.0, -1.0)
        self.wt = self.bg.find('**/random_tc1_TI_wallpaper')
        wallTex = loader.loadTexture('phase_%s/maps/wall_paper_a5.jpg' % interiorPhase)
        self.wt.setTexture(wallTex, 100)
        self.wt.setColorScale(0.8, 0.67, 0.549, 1.0)
        self.bt = self.bg.find('**/random_tc1_TI_wallpaper_border')
        wallTex = loader.loadTexture('phase_%s/maps/wall_paper_a5.jpg' % interiorPhase)
        self.bt.setTexture(wallTex, 100)
        self.bt.setColorScale(0.8, 0.67, 0.549, 1.0)
        self.wb = self.bg.find('**/random_tc1_TI_wainscotting')
        wainTex = loader.loadTexture('phase_%s/maps/wall_paper_b4.jpg' % interiorPhase)
        self.wb.setTexture(wainTex, 100)
        self.wb.setColorScale(0.473, 0.675, 0.488, 1.0)
        self.playAgain = DirectButton(parent=self.frame, relief=None, scale=1.04, pos=(0.72, 0, -0.24), image=(purchaseModels.find('**/PurchScrn_BTN_UP'),
         purchaseModels.find('**/PurchScrn_BTN_DN'),
         purchaseModels.find('**/PurchScrn_BTN_RLVR'),
         purchaseModels.find('**/PurchScrn_BTN_UP')), text=TTLocalizer.GagShopPlayAgain, text_fg=(0, 0.1, 0.7, 1), text_scale=0.05, text_pos=(0, 0.015, 0), image3_color=Vec4(0.6, 0.6, 0.6, 1), text3_fg=Vec4(0, 0, 0.4, 1), command=self.__handlePlayAgain)
        self.backToPlayground = DirectButton(parent=self.frame, relief=None, scale=1.04, pos=(0.72, 0, -0.045), image=(purchaseModels.find('**/PurchScrn_BTN_UP'),
         purchaseModels.find('**/PurchScrn_BTN_DN'),
         purchaseModels.find('**/PurchScrn_BTN_RLVR'),
         purchaseModels.find('**/PurchScrn_BTN_UP')), text=TTLocalizer.GagShopBackToPlayground, text_fg=(0, 0.1, 0.7, 1), text_scale=0.05, text_pos=(0, 0.015, 0), image3_color=Vec4(0.6, 0.6, 0.6, 1), text3_fg=Vec4(0, 0, 0.4, 1), command=self.__handleBackToPlayground)
        self.timer = ToontownTimer.ToontownTimer()
        self.timer.reparentTo(self.frame)
        self.timer.posInTopRightCorner()
        numAvs = 0
        count = 0
        localToonIndex = 0
        for index in range(len(self.ids)):
            avId = self.ids[index]
            if avId == base.localAvatar.doId:
                localToonIndex = index
            if self.states[index] != PURCHASE_NO_CLIENT_STATE and self.states[index] != PURCHASE_DISCONNECTED_STATE:
                numAvs = numAvs + 1

        layoutList = (None,
         (0,),
         (0, 2),
         (0, 1, 3),
         (0, 1, 2, 3))
        layout = layoutList[numAvs]
        headFramePosList = (Vec3(0.105, 0, -0.384),
         Vec3(0.105, 0, -0.776),
         Vec3(0.85, 0, -0.555),
         Vec3(-0.654, 0, -0.555))
        AVID_INDEX = 0
        LAYOUT_INDEX = 1
        TOON_INDEX = 2
        self.avInfoArray = [(base.localAvatar.doId, headFramePosList[0], localToonIndex)]
        pos = 1
        for index in range(len(self.ids)):
            avId = self.ids[index]
            if self.states[index] != PURCHASE_NO_CLIENT_STATE and self.states[index] != PURCHASE_DISCONNECTED_STATE:
                if avId != base.localAvatar.doId:
                    if avId in base.cr.doId2do:
                        self.avInfoArray.append((avId, headFramePosList[layout[pos]], index))
                        pos = pos + 1

        self.headFrames = []
        for avInfo in self.avInfoArray:
            av = base.cr.doId2do.get(avInfo[AVID_INDEX])
            if av:
                headFrame = PurchaseHeadFrame(av, purchaseModels)
                headFrame.setAvatarState(self.states[avInfo[TOON_INDEX]])
                headFrame.setPos(avInfo[LAYOUT_INDEX])
                self.headFrames.append((avInfo[AVID_INDEX], headFrame))

        purchaseModels.removeNode()
        self.foreground = loader.loadModel('phase_3.5/models/modules/TT_A1')
        self.foreground.setPos(12.5, -20, -5.5)
        self.foreground.setHpr(180, 0, 0)
        self.backgroundL = loader.loadModel('phase_3.5/models/modules/TT_A1')
        self.backgroundL.setPos(-12.5, -25, -5)
        self.backgroundL.setHpr(180, 0, 0)
        self.backgroundR = self.backgroundL.copyTo(hidden)
        self.backgroundR.setPos(20, -25, -5)
        streets = loader.loadModel('phase_3.5/models/modules/street_modules')
        sidewalk = streets.find('**/street_sidewalk_40x40')
        self.sidewalk = sidewalk.copyTo(hidden)
        self.sidewalk.setPos(-20, -25, -5.5)
        self.sidewalk.setColor(0.9, 0.6, 0.4)
        streets.removeNode()
        doors = loader.loadModel('phase_4/models/modules/doors')
        door = doors.find('**/door_single_square_ur_door')
        self.door = door.copyTo(hidden)
        self.door.setH(180)
        self.door.setPos(0, -16.75, -5.5)
        self.door.setScale(1.5, 1.5, 2.0)
        self.door.setColor(1.0, 0.8, 0, 1)
        doors.removeNode()
        self.convertingVotesToBeansLabel = DirectLabel(text=TTLocalizer.TravelGameConvertingVotesToBeans, text_fg=VBase4(1, 1, 1, 1), relief=None, pos=(0.0, 0, -0.58), scale=0.075)
        self.convertingVotesToBeansLabel.hide()
        self.rewardDoubledJellybeanLabel = DirectLabel(text=TTLocalizer.PartyRewardDoubledJellybean, text_fg=(1.0, 0.125, 0.125, 1.0), text_shadow=(0, 0, 0, 1), relief=None, pos=(0.0, 0, -0.67), scale=0.08)
        self.rewardDoubledJellybeanLabel.hide()
        self.countSound = base.loader.loadSfx('phase_3.5/audio/sfx/tick_counter.ogg')
        self.overMaxSound = base.loader.loadSfx('phase_3.5/audio/sfx/AV_collision.ogg')
        self.celebrateSound = base.loader.loadSfx('phase_4/audio/sfx/MG_win.ogg')
        return

    def unload(self):
        PurchaseBase.unload(self)
        self.cleanupUnexpectedExitHooks()
        self.bg.removeNode()
        del self.bg
        self.notify.debug('destroying head frames')
        for headFrame in self.headFrames:
            if not headFrame[1].isEmpty():
                headFrame[1].reparentTo(hidden)
                headFrame[1].destroy()

        del self.headFrames
        self.playAgain.destroy()
        del self.playAgain
        self.backToPlayground.destroy()
        del self.backToPlayground
        self.timer.stop()
        del self.timer
        for counter in self.counters:
            counter.destroy()
            del counter

        del self.counters
        for total in self.totalCounters:
            total.destroy()
            del total

        del self.totalCounters
        loader.unloadModel('phase_3.5/models/modules/TT_A1')
        loader.unloadModel('phase_3.5/models/modules/street_modules')
        loader.unloadModel('phase_4/models/modules/doors')
        taskMgr.remove('countUpTask')
        taskMgr.remove('countVotesUpTask')
        taskMgr.remove('countDownTask')
        taskMgr.remove('countVotesDownTask')
        taskMgr.remove('celebrate')
        taskMgr.remove('purchase-trans')
        taskMgr.remove('delayAdd')
        taskMgr.remove('delaySubtract')
        self.foreground.removeNode()
        del self.foreground
        self.backgroundL.removeNode()
        del self.backgroundL
        self.backgroundR.removeNode()
        del self.backgroundR
        self.sidewalk.removeNode()
        del self.sidewalk
        self.door.removeNode()
        del self.door
        self.collisionFloor.removeNode()
        del self.collisionFloor
        del self.countSound
        del self.celebrateSound
        self.convertingVotesToBeansLabel.removeNode()
        self.rewardDoubledJellybeanLabel.removeNode()
        del self.convertingVotesToBeansLabel
        del self.rewardDoubledJellybeanLabel

    def showStatusText(self, text):
        self.statusLabel['text'] = text
        taskMgr.remove('resetStatusText')
        taskMgr.doMethodLater(2.0, self.resetStatusText, 'resetStatusText')

    def resetStatusText(self, task):
        self.statusLabel['text'] = ''
        return Task.done

    def __handlePlayAgain(self):
        for headFrame in self.headFrames:
            headFrame[1].wrtReparentTo(aspect2d)

        self.toon.inventory.reparentTo(hidden)
        self.toon.inventory.hide()
        taskMgr.remove('resetStatusText')
        taskMgr.remove('showBrokeMsgTask')
        self.statusLabel['text'] = TTLocalizer.GagShopWaitingOtherPlayers
        messenger.send('purchasePlayAgain')

    def handleDone(self, playAgain):
        base.localAvatar.b_setParent(ToontownGlobals.SPHidden)
        if playAgain:
            self.doneStatus = {'loader': 'minigame',
             'where': 'minigame'}
        else:
            self.doneStatus = {'loader': 'safeZoneLoader',
             'where': 'playground'}
        messenger.send(self.doneEvent)

    def __handleBackToPlayground(self):
        self.toon.inventory.reparentTo(hidden)
        self.toon.inventory.hide()
        messenger.send('purchaseBackToToontown')

    def __timerExpired(self):
        messenger.send('purchaseTimeout')

    def findHeadFrame(self, id):
        for headFrame in self.headFrames:
            if headFrame[0] == id:
                return headFrame[1]

        return None

    def __handleStateChange(self, playerStates):
        self.states = playerStates
        for avInfo in self.avInfoArray:
            index = avInfo[2]
            headFrame = self.findHeadFrame(avInfo[0])
            state = self.states[index]
            headFrame.setAvatarState(state)

    def enter(self):
        base.playMusic(self.music, looping=1, volume=0.8)
        self.fsm.request('reward')

    def enterReward(self):
        numToons = 0
        toonLayouts = ((2,),
         (1, 3),
         (0, 2, 4),
         (0, 1, 3, 4))
        toonPositions = (5.0,
         1.75,
         -0.25,
         -1.75,
         -5.0)
        self.toons = []
        self.toonsKeep = []
        self.counters = []
        self.totalCounters = []
        camera.reparentTo(render)
        base.camLens.setFov(ToontownGlobals.DefaultCameraFov)
        camera.setPos(0, 16.0, 2.0)
        camera.lookAt(0, 0, 0.75)
        base.transitions.irisIn(0.4)
        self.title.reparentTo(aspect2d)
        self.foreground.reparentTo(render)
        self.backgroundL.reparentTo(render)
        self.backgroundR.reparentTo(render)
        self.sidewalk.reparentTo(render)
        self.door.reparentTo(render)
        size = 20
        z = -2.5
        floor = CollisionPolygon(Point3(-size, -size, z), Point3(size, -size, z), Point3(size, size, z), Point3(-size, size, z))
        floor.setTangible(1)
        floorNode = CollisionNode('collision_floor')
        floorNode.addSolid(floor)
        self.collisionFloor = render.attachNewNode(floorNode)
        NametagGlobals.setOnscreenChatForced(1)
        for index in range(len(self.ids)):
            avId = self.ids[index]
            if self.states[index] != PURCHASE_NO_CLIENT_STATE and self.states[index] != PURCHASE_DISCONNECTED_STATE and avId in base.cr.doId2do:
                numToons += 1
                toon = base.cr.doId2do[avId]
                toon.stopSmooth()
                self.toons.append(toon)
                self.toonsKeep.append(DelayDelete.DelayDelete(toon, 'Purchase.enterReward'))
                counter = DirectLabel(parent=hidden, relief=None, pos=(0.0, 0.0, 0.0), text=str(0), text_scale=0.2, text_fg=(0.95, 0.95, 0, 1), text_pos=(0, -0.1, 0), text_font=ToontownGlobals.getSignFont())
                counter['image'] = DGG.getDefaultDialogGeom()
                counter['image_scale'] = (0.33, 1, 0.33)
                counter.setScale(0.5)
                counter.count = 0
                counter.max = self.pointsArray[index]
                self.counters.append(counter)
                money = self.playerMoney[index]
                totalCounter = DirectLabel(parent=hidden, relief=None, pos=(0.0, 0.0, 0.0), text=str(money), text_scale=0.2, text_fg=(0.95, 0.95, 0, 1), text_pos=(0, -0.1, 0), text_font=ToontownGlobals.getSignFont(), image=self.jarImage)
                totalCounter.setScale(0.5)
                totalCounter.count = money
                totalCounter.max = toon.getMaxMoney()
                self.totalCounters.append(totalCounter)

        self.accept('clientCleanup', self._handleClientCleanup)
        pos = 0
        toonLayout = toonLayouts[numToons - 1]
        for toon in self.toons:
            thisPos = toonPositions[toonLayout[pos]]
            toon.setPos(Vec3(thisPos, 1.0, -2.5))
            toon.setHpr(Vec3(0, 0, 0))
            toon.setAnimState('neutral', 1)
            toon.setShadowHeight(0)
            if not toon.isDisabled():
                toon.reparentTo(render)
            self.counters[pos].setPos(thisPos * -0.17, 0, toon.getHeight() / 10 + 0.25)
            self.counters[pos].reparentTo(aspect2d)
            self.totalCounters[pos].setPos(thisPos * -0.17, 0, -0.825)
            self.totalCounters[pos].reparentTo(aspect2d)
            pos += 1

        self.maxPoints = max(self.pointsArray)
        if self.votesArray:
            self.maxVotes = max(self.votesArray)
            numToons = len(self.toons)
            self.voteMultiplier = TravelGameGlobals.PercentOfVotesConverted[numToons] / 100.0
            self.maxBeansFromVotes = int(self.voteMultiplier * self.maxVotes)
        else:
            self.maxVotes = 0
            self.maxBeansFromVotes = 0

        def reqCountUp(state):
            self.countUp()
            return Task.done

        countUpDelay = DELAY_BEFORE_COUNT_UP
        taskMgr.doMethodLater(countUpDelay, reqCountUp, 'countUpTask')

        def reqCountDown(state):
            self.countDown()
            return Task.done

        countDownDelay = countUpDelay + COUNT_UP_DURATION + DELAY_AFTER_COUNT_UP
        taskMgr.doMethodLater(countDownDelay, reqCountDown, 'countDownTask')

        def celebrate(task):
            for counter in task.counters:
                counter.hide()

            winningPoints = max(task.pointsArray)
            for i in range(len(task.ids)):
                if task.pointsArray[i] == winningPoints:
                    avId = task.ids[i]
                    if avId in base.cr.doId2do:
                        toon = base.cr.doId2do[avId]
                        toon.setAnimState('jump', 1.0)

            base.playSfx(task.celebrateSound)
            return Task.done

        celebrateDelay = countDownDelay + COUNT_DOWN_DURATION + DELAY_AFTER_COUNT_DOWN
        celebrateTask = taskMgr.doMethodLater(celebrateDelay, celebrate, 'celebrate')
        celebrateTask.counters = self.counters
        celebrateTask.pointsArray = self.pointsArray
        celebrateTask.ids = self.ids
        celebrateTask.celebrateSound = self.celebrateSound

        def reqCountVotesUp(state):
            self.countVotesUp()
            return Task.done

        def reqCountVotesDown(state):
            self.countVotesDown()
            return Task.done

        if self.metagameRound == TravelGameGlobals.FinalMetagameRoundIndex:
            countVotesUpDelay = celebrateDelay + DELAY_AFTER_CELEBRATE
            taskMgr.doMethodLater(countVotesUpDelay, reqCountVotesUp, 'countVotesUpTask')
            countVotesUpTime = self.maxVotes * COUNT_UP_RATE + DELAY_AFTER_COUNT_UP
            countVotesDownDelay = countVotesUpDelay + countVotesUpTime
            taskMgr.doMethodLater(countVotesDownDelay, reqCountVotesDown, 'countVotesDownTask')
            celebrateDelay += countVotesUpTime + self.maxVotes * COUNT_DOWN_RATE + DELAY_AFTER_COUNT_DOWN

        def reqPurchase(state):
            self.fsm.request('purchase')
            return Task.done

        purchaseDelay = celebrateDelay + DELAY_AFTER_CELEBRATE
        taskMgr.doMethodLater(purchaseDelay, reqPurchase, 'purchase-trans')
        if base.skipMinigameReward:
            self.fsm.request('purchase')
        return

    def _changeCounterUp(self, task, counter, newCount, toonId):
        counter.count = newCount
        counter['text'] = str(counter.count)
        if toonId == base.localAvatar.doId:
            now = globalClock.getRealTime()
            if task.lastSfxT + COUNT_SFX_MIN_DELAY < now:
                base.playSfx(task.countSound, time=COUNT_SFX_START_T)
                task.lastSfxT = now

    def _countUpTask(self, task):
        now = globalClock.getRealTime()
        startT = task.getStartTime()
        if now >= startT + task.duration:
            for counter, toonId in zip(self.counters, self.ids):
                if counter.count != counter.max:
                    self._changeCounterUp(task, counter, counter.max, toonId)

            return Task.done
        t = (now - startT) / task.duration
        for counter, toonId in zip(self.counters, self.ids):
            curCount = int(triglerp(0, counter.max, t))
            if curCount != counter.count:
                self._changeCounterUp(task, counter, curCount, toonId)

        return Task.cont

    def countUp(self):
        totalDelay = 0
        if base.cr.newsManager.isHolidayRunning(ToontownGlobals.JELLYBEAN_TROLLEY_HOLIDAY) or base.cr.newsManager.isHolidayRunning(ToontownGlobals.JELLYBEAN_TROLLEY_HOLIDAY_MONTH):
            self.rewardDoubledJellybeanLabel.show()
        countUpTask = taskMgr.add(self._countUpTask, 'countUp')
        countUpTask.duration = COUNT_UP_DURATION
        countUpTask.countSound = self.countSound
        countUpTask.lastSfxT = 0

    def _changeCounterDown(self, task, counter, newCount, total, toonId):
        counter.count = newCount
        counter['text'] = str(counter.count)
        total.count = total.startAmount + (counter.max - newCount)
        if total.count > total.max:
            total.count = total.max
        total['text'] = str(total.count)
        if total.count == total.max:
            total['text_fg'] = (1, 0, 0, 1)
        if toonId == base.localAvatar.doId:
            now = globalClock.getRealTime()
            if total.count < total.max:
                minDelay = COUNT_SFX_MIN_DELAY
                snd = task.countSound
                startT = COUNT_SFX_START_T
            else:
                minDelay = OVERMAX_SFX_MIN_DELAY
                snd = task.overMaxSound
                startT = OVERMAX_SFX_START_T
            if task.lastSfxT + minDelay < now:
                task.lastSfxT = now
                base.playSfx(snd, time=startT)

    def _countDownTask(self, task):
        now = globalClock.getRealTime()
        startT = task.getStartTime()
        if now >= startT + task.duration:
            for counter, total, toonId in zip(self.counters, self.totalCounters, self.ids):
                if counter.count != 0:
                    self._changeCounterDown(task, counter, 0, total, toonId)

            return Task.done
        t = (now - startT) / task.duration
        for counter, total, toonId in zip(self.counters, self.totalCounters, self.ids):
            curCount = int(triglerp(counter.max, 0, t))
            if curCount != counter.count:
                self._changeCounterDown(task, counter, curCount, total, toonId)

        return Task.cont

    def countDown(self):
        totalDelay = 0
        for total in self.totalCounters:
            total.startAmount = total.count

        countDownTask = taskMgr.add(self._countDownTask, 'countDown')
        countDownTask.duration = COUNT_DOWN_DURATION
        countDownTask.countSound = self.countSound
        countDownTask.overMaxSound = self.overMaxSound
        countDownTask.lastSfxT = 0

    def countVotesUp(self):
        totalDelay = 0
        self.convertingVotesToBeansLabel.show()
        if base.cr.newsManager.isHolidayRunning(ToontownGlobals.JELLYBEAN_TROLLEY_HOLIDAY) or base.cr.newsManager.isHolidayRunning(ToontownGlobals.JELLYBEAN_TROLLEY_HOLIDAY_MONTH):
            self.rewardDoubledJellybeanLabel.show()
        counterIndex = 0
        for index in range(len(self.ids)):
            avId = self.ids[index]
            if self.states[index] != PURCHASE_NO_CLIENT_STATE and self.states[index] != PURCHASE_DISCONNECTED_STATE and avId in base.cr.doId2do:
                self.counters[counterIndex].count = 0
                self.counters[counterIndex].max = self.votesArray[index]
                self.counters[counterIndex].show()
                counterIndex += 1

        def delayAdd(state):
            state.counter.count += 1
            state.counter['text'] = str(state.counter.count)
            if state.toonId == base.localAvatar.doId:
                base.playSfx(state.countSound)
            return Task.done

        for count in range(0, self.maxVotes):
            for counter in self.counters:
                index = self.counters.index(counter)
                if count < counter.max:
                    addTask = taskMgr.doMethodLater(totalDelay, delayAdd, 'delayAdd')
                    addTask.counter = counter
                    addTask.toonId = self.ids[index]
                    addTask.countSound = self.countSound

            totalDelay += COUNT_UP_RATE

    def countVotesDown(self):
        totalDelay = 0

        def delaySubtract(state):
            state.counter.count -= 1
            state.counter['text'] = str(state.counter.count)
            state.total.count += 1 * self.voteMultiplier
            if state.total.count <= state.total.max:
                state.total['text'] = str(int(state.total.count))
            if state.total.count == state.total.max + 1:
                state.total['text_fg'] = (1, 0, 0, 1)
            if state.toonId == base.localAvatar.doId:
                if state.total.count <= state.total.max:
                    base.playSfx(state.countSound)
                else:
                    base.playSfx(state.overMaxSound)
            return Task.done

        for count in range(0, self.maxVotes):
            for counter in self.counters:
                if count < counter.max:
                    index = self.counters.index(counter)
                    subtractTask = taskMgr.doMethodLater(totalDelay, delaySubtract, 'delaySubtract')
                    subtractTask.counter = counter
                    subtractTask.total = self.totalCounters[index]
                    subtractTask.toonId = self.ids[index]
                    subtractTask.countSound = self.countSound
                    subtractTask.overMaxSound = self.overMaxSound

            totalDelay += COUNT_DOWN_RATE

    def exitReward(self):
        self.ignore('clientCleanup')
        taskMgr.remove('countUpTask')
        taskMgr.remove('countVotesUpTask')
        taskMgr.remove('countDownTask')
        taskMgr.remove('countVotesDownTask')
        taskMgr.remove('celebrate')
        taskMgr.remove('purchase-trans')
        taskMgr.remove('delayAdd')
        taskMgr.remove('delaySubtract')
        for toon in self.toons:
            toon.detachNode()

        del self.toons
        if hasattr(self, 'toonsKeep'):
            for delayDelete in self.toonsKeep:
                delayDelete.destroy()

            del self.toonsKeep
        for counter in self.counters:
            counter.reparentTo(hidden)

        for total in self.totalCounters:
            total.reparentTo(hidden)

        self.foreground.reparentTo(hidden)
        self.backgroundL.reparentTo(hidden)
        self.backgroundR.reparentTo(hidden)
        self.sidewalk.reparentTo(hidden)
        self.door.reparentTo(hidden)
        self.title.reparentTo(self.frame)
        self.convertingVotesToBeansLabel.hide()
        self.rewardDoubledJellybeanLabel.hide()
        NametagGlobals.setOnscreenChatForced(0)

    def _handleClientCleanup(self):
        if hasattr(self, 'toonsKeep'):
            for delayDelete in self.toonsKeep:
                delayDelete.destroy()

            del self.toonsKeep
        self.ignore('clientCleanup')

    def enterPurchase(self):
        PurchaseBase.enterPurchase(self)
        self.convertingVotesToBeansLabel.hide()
        self.rewardDoubledJellybeanLabel.hide()
        self.bg.reparentTo(render)
        base.setBackgroundColor(0.05, 0.14, 0.4)
        self.accept('purchaseStateChange', self.__handleStateChange)
        self.playAgain.reparentTo(self.toon.inventory.purchaseFrame)
        self.backToPlayground.reparentTo(self.toon.inventory.purchaseFrame)
        self.pointDisplay.reparentTo(self.toon.inventory.purchaseFrame)
        self.statusLabel.reparentTo(self.toon.inventory.purchaseFrame)
        for headFrame in self.headFrames:
            headFrame[1].show()
            headFrame[1].reparentTo(self.toon.inventory.purchaseFrame)

        if base.cr.periodTimerExpired:
            base.cr.loginFSM.request('periodTimeout')
            return
        if not self.tutorialMode:
            if not config.GetBool('disable-purchase-timer', 0):
                self.timer.countdown(self.remain, self.__timerExpired)
            if config.GetBool('metagame-disable-playAgain', 0):
                if self.metagameRound > -1:
                    self.disablePlayAgain()
        else:
            self.timer.hide()
            self.disablePlayAgain()
            self.accept('disableGagPanel', Functor(self.toon.inventory.setActivateMode, 'gagTutDisabled', gagTutMode=1))
            self.accept('disableBackToPlayground', self.disableBackToPlayground)
            self.accept('enableGagPanel', self.handleEnableGagPanel)
            self.accept('enableBackToPlayground', self.enableBackToPlayground)
            for avId, headFrame in self.headFrames:
                if avId != self.newbieId:
                    headFrame.hide()

        messenger.send('gagScreenIsUp')
        if base.autoPlayAgain or self.doMetagamePlayAgain():
            base.transitions.fadeOut(0)
            self.__handlePlayAgain()

    def exitPurchase(self):
        PurchaseBase.exitPurchase(self)
        self.ignore('disableGagPanel')
        self.ignore('disableBackToPlayground')
        self.ignore('enableGagPanel')
        self.ignore('enableBackToPlayground')
        self.bg.reparentTo(hidden)
        self.playAgain.reparentTo(self.frame)
        self.backToPlayground.reparentTo(self.frame)
        self.pointDisplay.reparentTo(self.frame)
        self.statusLabel.reparentTo(self.frame)
        self.ignore('purchaseStateChange')
        base.setBackgroundColor(ToontownGlobals.DefaultBackgroundColor)
        if base.autoPlayAgain or self.doMetagamePlayAgain():
            base.transitions.fadeIn()

    def disableBackToPlayground(self):
        self.backToPlayground['state'] = DGG.DISABLED

    def enableBackToPlayground(self):
        self.backToPlayground['state'] = DGG.NORMAL

    def disablePlayAgain(self):
        self.playAgain['state'] = DGG.DISABLED

    def enablePlayAgain(self):
        self.playAgain['state'] = DGG.NORMAL

    def enterTutorialMode(self, newbieId):
        self.tutorialMode = 1
        self.newbieId = newbieId

    def handleEnableGagPanel(self):
        self.toon.inventory.setActivateMode('purchase', gagTutMode=1)
        self.checkForBroke()

    def handleGagTutorialDone(self):
        self.enableBackToPlayground()

    def doMetagamePlayAgain(self):
        if hasattr(self, 'metagamePlayAgainResult'):
            return self.metagamePlayAgainResult
        numToons = 0
        for avId in self.ids:
            if avId in base.cr.doId2do and avId not in self.unexpectedExits:
                numToons += 1

        self.metagamePlayAgainResult = False
        if numToons > 1:
            if self.metagameRound > -1 and self.metagameRound < TravelGameGlobals.FinalMetagameRoundIndex:
                self.metagamePlayAgainResult = True
        return self.metagamePlayAgainResult

    def setupUnexpectedExitHooks(self):
        for avId in self.ids:
            if avId in base.cr.doId2do:
                toon = base.cr.doId2do[avId]
                eventName = toon.uniqueName('disable')
                self.accept(eventName, self.__handleUnexpectedExit, extraArgs=[avId])
                self.unexpectedEventNames.append(eventName)

    def cleanupUnexpectedExitHooks(self):
        for eventName in self.unexpectedEventNames:
            self.ignore(eventName)

    def __handleUnexpectedExit(self, avId):
        self.unexpectedExits.append(avId)


class PurchaseHeadFrame(DirectFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('Purchase')

    def __init__(self, av, purchaseModels):
        DirectFrame.__init__(self, relief=None, image=purchaseModels.find('**/Char_Pnl'))
        self.initialiseoptions(PurchaseHeadFrame)
        self.statusLabel = DirectLabel(parent=self, relief=None, text='', text_scale=TTLocalizer.PstatusLabel, text_wordwrap=7.5, text_fg=(0.05, 0.14, 0.4, 1), text_pos=(0.1, 0, 0))
        self.av = av
        self.avKeep = DelayDelete.DelayDelete(av, 'PurchaseHeadFrame.av')
        self.accept('clientCleanup', self._handleClientCleanup)
        self.head = self.stateNodePath[0].attachNewNode('head', 20)
        self.head.setPosHprScale(-0.22, 10.0, -0.1, 180.0, 0.0, 0.0, 0.1, 0.1, 0.1)
        self.headModel = ToonHead.ToonHead()
        self.headModel.setupHead(self.av.style, forGui=1)
        self.headModel.reparentTo(self.head)
        self.tag2Node = NametagFloat2d()
        self.tag2Node.setContents(Nametag.CName)
        self.av.nametag.addNametag(self.tag2Node)
        self.tag2 = self.attachNewNode(self.tag2Node.upcastToPandaNode())
        self.tag2.setPosHprScale(-0.22, 10.0, 0.12, 0, 0, 0, 0.046, 0.046, 0.046)
        self.tag1Node = NametagFloat2d()
        self.tag1Node.setContents(Nametag.CSpeech | Nametag.CThought)
        self.av.nametag.addNametag(self.tag1Node)
        self.tag1 = self.attachNewNode(self.tag1Node.upcastToPandaNode())
        self.tag1.setPosHprScale(-0.15, 0, -0.1, 0, 0, 0, 0.046, 0.046, 0.046)
        self.hide()
        return

    def destroy(self):
        DirectFrame.destroy(self)
        del self.statusLabel
        self.headModel.delete()
        del self.headModel
        self.head.removeNode()
        del self.head
        self.av.nametag.removeNametag(self.tag1Node)
        self.av.nametag.removeNametag(self.tag2Node)
        self.tag1.removeNode()
        self.tag2.removeNode()
        del self.tag1
        del self.tag2
        del self.tag1Node
        del self.tag2Node
        del self.av
        self.removeAvKeep()

    def setAvatarState(self, state):
        if state == PURCHASE_DISCONNECTED_STATE:
            self.statusLabel['text'] = TTLocalizer.GagShopPlayerDisconnected % self.av.getName()
            self.statusLabel['text_pos'] = (0.015, 0.072, 0)
            self.head.hide()
            self.tag1.hide()
            self.tag2.hide()
        elif state == PURCHASE_EXIT_STATE:
            self.statusLabel['text'] = TTLocalizer.GagShopPlayerExited % self.av.getName()
            self.statusLabel['text_pos'] = (0.015, 0.072, 0)
            self.head.hide()
            self.tag1.hide()
            self.tag2.hide()
        elif state == PURCHASE_PLAYAGAIN_STATE:
            self.statusLabel['text'] = TTLocalizer.GagShopPlayerPlayAgain
            self.statusLabel['text_pos'] = (0.1, -0.12, 0)
        elif state == PURCHASE_WAITING_STATE:
            self.statusLabel['text'] = TTLocalizer.GagShopPlayerBuying
            self.statusLabel['text_pos'] = (0.1, -0.12, 0)
        elif state == PURCHASE_NO_CLIENT_STATE:
            Purchase.notify.warning("setAvatarState('no client state'); OK for gag purchase tutorial")
        else:
            Purchase.notify.warning('unknown avatar state: %s' % state)

    def _handleClientCleanup(self):
        self.destroy()

    def removeAvKeep(self):
        if hasattr(self, 'avKeep'):
            self.notify.debug('destroying avKeep %s' % self.avKeep)
            self.avKeep.destroy()
            del self.avKeep
        self.ignore('clientCleanup')
