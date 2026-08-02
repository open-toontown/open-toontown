from panda3d.core import *
from toontown.toonbase import ToontownGlobals
from . import AvatarChoice
from direct.fsm import StateData
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from toontown.launcher import DownloadForceAcknowledge
from direct.gui.DirectGui import *
from panda3d.core import *
from toontown.toonbase import TTLocalizer
from toontown.toonbase import DisplayOptions
from direct.directnotify import DirectNotifyGlobal
from direct.interval.IntervalGlobal import *
import random
MAX_AVATARS = 6
BASE_POSITIONS = (Vec3(-0.840167, 0, 0.359333),
 Vec3(0.00933349, 0, 0.306533),
 Vec3(0.862, 0, 0.3293),
 Vec3(-0.863554, 0, -0.445659),
 Vec3(0.00999999, 0, -0.5181),
 Vec3(0.864907, 0, -0.445659))
COLORS = (Vec4(0.917, 0.164, 0.164, 1),
 Vec4(0.152, 0.75, 0.258, 1),
 Vec4(0.598, 0.402, 0.875, 1),
 Vec4(0.133, 0.59, 0.977, 1),
 Vec4(0.895, 0.348, 0.602, 1),
 Vec4(0.977, 0.816, 0.133, 1))
chooser_notify = DirectNotifyGlobal.directNotify.newCategory('AvatarChooser')

class AvatarChooser(StateData.StateData):

    def __init__(self, avatarList, parentFSM, doneEvent):
        StateData.StateData.__init__(self, doneEvent)
        self.choice = None
        self.avatarList = avatarList
        self.displayOptions = None
        self.fsm = ClassicFSM.ClassicFSM('AvatarChooser', [State.State('Choose', self.enterChoose, self.exitChoose, ['CheckDownload']), State.State('CheckDownload', self.enterCheckDownload, self.exitCheckDownload, ['Choose'])], 'Choose', 'Choose')
        self.fsm.enterInitialState()
        self.parentFSM = parentFSM
        self.parentFSM.getCurrentState().addChild(self.fsm)
        return

    def enter(self):
        self.notify.info('AvatarChooser.enter')
        if not self.displayOptions:
            self.displayOptions = DisplayOptions.DisplayOptions()
        self.notify.info('calling self.displayOptions.restrictToEmbedded(False)')
        if base.appRunner:
            self.displayOptions.loadFromSettings()
            self.displayOptions.restrictToEmbedded(False)
        if self.isLoaded == 0:
            self.load()
        base.disableMouse()
        self.title.reparentTo(aspect2d)
        self.quitButton.show()
        if base.cr.loginInterface.supportsRelogin():
            self.logoutButton.show()
        # Revamp: do not show the pick-a-toon background panel; the chooser UI
        # should overlay the in-world backdrop (Toontown Central).
        if getattr(self, 'pickAToonBG', None):
            self.pickAToonBG.reparentTo(hidden)
        choice = base.config.GetInt('auto-avatar-choice', -1)
        for panel in self.panelList:
            # Ensure panels are in the visible GUI graph and render on top.
            panel.reparentTo(aspect2d)
            panel.setBin('gui-popup', 10)
            panel.show()
            self.accept(panel.doneEvent, self.__handlePanelDone)
            if panel.position == choice and panel.mode == AvatarChoice.AvatarChoice.MODE_CHOOSE:
                self.__handlePanelDone('chose', panelChoice=choice)

        # A "cool transition" into Pick-a-Toon: quick pop + fade for the panels and title.
        try:
            if getattr(self, '_enterIval', None):
                self._enterIval.finish()
            items = []
            items.append(self.title)
            for p in self.panelList:
                items.append(p)
            # Buttons too, for a unified entrance.
            items.append(self.quitButton)
            if self.logoutButton:
                items.append(self.logoutButton)

            for item in items:
                try:
                    item.setColorScale(1, 1, 1, 0)
                except Exception:
                    pass

            def _fade(alpha):
                for item in items:
                    try:
                        item.setColorScale(1, 1, 1, alpha)
                    except Exception:
                        pass

            self._enterIval = Sequence(
                Parallel(
                    LerpFunc(_fade, fromData=0.0, toData=1.0, duration=0.28, blendType='easeOut'),
                ),
            )
            self._enterIval.start()
        except Exception:
            pass

    def exit(self):
        if self.isLoaded == 0:
            return None
        for panel in self.panelList:
            panel.hide()

        self.ignoreAll()
        self.title.reparentTo(hidden)
        self.quitButton.hide()
        self.logoutButton.hide()
        if getattr(self, 'pickAToonBG', None):
            self.pickAToonBG.reparentTo(hidden)
        return None

    def load(self, isPaid):
        if self.isLoaded == 1:
            return None
        self.isPaid = isPaid
        gui = loader.loadModel('phase_3/models/gui/pick_a_toon_gui')
        gui2 = loader.loadModel('phase_3/models/gui/quit_button')
        # Prefer the live TTC backdrop. If it failed (or is disabled), fall back
        # to the legacy pick-a-toon background art to avoid a blank/grey screen.
        self.pickAToonBG = None
        try:
            failed = bool(getattr(base.cr, '_pickAToonTTCBackdropFailed', False))
            haveBackdrop = bool(getattr(base.cr, '_pickAToonTTCBackdrop', None))
        except Exception:
            failed = False
            haveBackdrop = False
        guiOk = False
        try:
            guiOk = gui is not None and not gui.isEmpty()
        except Exception:
            guiOk = False

        if (failed or not haveBackdrop) and guiOk:
            try:
                self.pickAToonBG = DirectFrame(
                    parent=aspect2d,
                    relief=None,
                    image=gui,
                    image_scale=(1.33, 1.0, 1.0),
                    pos=(0, 0, 0),
                )
                self.pickAToonBG.setBin('fixed', -10)
            except Exception:
                self.pickAToonBG = None
        elif failed or not haveBackdrop:
            chooser_notify.warning('pick_a_toon_gui failed to load; skipping legacy background image')
        self.title = OnscreenText(TTLocalizer.AvatarChooserPickAToon, scale=TTLocalizer.ACtitle, parent=hidden, font=ToontownGlobals.getSignFont(), fg=(1, 0.9, 0.1, 1), pos=(0.0, 0.82))

        # Some forks remove/rename assets; guard against missing models so we
        # don't trip Panda NodePath empty assertions.
        quitHover = None
        try:
            if guiOk:
                q = gui.find('**/QuitBtn_RLVR')
                if q is not None and not q.isEmpty():
                    quitHover = q
        except Exception:
            quitHover = None
        if quitHover is None:
            # Safe fallback: DirectButton allows image=None.
            chooser_notify.warning('pick_a_toon_gui missing QuitBtn_RLVR; using fallback button visuals')
        # Widescreen-aware: pin the quit/logout buttons to the screen edges
        quitButtonPos = (base.getWidescreenXOffset(1.08, 'right') if hasattr(base, 'getWidescreenXOffset') else 1.08, 0, -0.907)
        self.quitButton = DirectButton(image=(quitHover, quitHover, quitHover), relief=None, text=TTLocalizer.AvatarChooserQuit, text_font=ToontownGlobals.getSignFont(), text_fg=(0.977, 0.816, 0.133, 1), text_pos=TTLocalizer.ACquitButtonPos, text_scale=TTLocalizer.ACquitButton, image_scale=1, image1_scale=1.05, image2_scale=1.05, scale=1.05, pos=quitButtonPos, command=self.__handleQuit)
        logoutButtonPos = (base.getWidescreenXOffset(-1.17, 'left') if hasattr(base, 'getWidescreenXOffset') else -1.17, 0, -0.914)
        self.logoutButton = DirectButton(relief=None, image=(quitHover, quitHover, quitHover), text=TTLocalizer.OptionsPageLogout, text_font=ToontownGlobals.getSignFont(), text_fg=(0.977, 0.816, 0.133, 1), text_scale=TTLocalizer.AClogoutButton, text_pos=(0, -0.035), pos=logoutButtonPos, image_scale=1.15, image1_scale=1.15, image2_scale=1.18, scale=0.5, command=self.__handleLogoutWithoutConfirm)

        self.logoutButton.hide()
        try:
            if gui is not None and not gui.isEmpty():
                gui.removeNode()
        except Exception:
            pass
        try:
            if gui2 is not None and not gui2.isEmpty():
                gui2.removeNode()
        except Exception:
            pass
        self.panelList = []
        used_position_indexs = []
        positions = BASE_POSITIONS
        for av in self.avatarList:
            if base.cr.isPaid():
                okToLockout = 0
            else:
                okToLockout = 1
                if av.position in AvatarChoice.AvatarChoice.OLD_TRIALER_OPEN_POS:
                    okToLockout = 0
            panel = AvatarChoice.AvatarChoice(av, position=av.position, paid=isPaid, okToLockout=okToLockout)
            panel.setPos(positions[av.position])
            used_position_indexs.append(av.position)
            self.panelList.append(panel)

        for panelNum in range(0, MAX_AVATARS):
            if panelNum not in used_position_indexs:
                panel = AvatarChoice.AvatarChoice(position=panelNum, paid=isPaid)
                panel.setPos(positions[panelNum])
                self.panelList.append(panel)

        if len(self.avatarList) > 0:
            self.initLookAtInfo()
        self.isLoaded = 1


    def getLookAtPosition(self, toonHead, toonidx):
        lookAtChoice = random.random()
        if len(self.used_panel_indexs) == 1:
            lookFwdPercent = 0.33
            lookAtOthersPercent = 0
        else:
            lookFwdPercent = 0.2
            if len(self.used_panel_indexs) == 2:
                lookAtOthersPercent = 0.4
            else:
                lookAtOthersPercent = 0.65
        lookRandomPercent = 1.0 - lookFwdPercent - lookAtOthersPercent
        if lookAtChoice < lookFwdPercent:
            self.IsLookingAt[toonidx] = 'f'
            return Vec3(0, 1.5, 0)
        elif lookAtChoice < lookRandomPercent + lookFwdPercent or len(self.used_panel_indexs) == 1:
            self.IsLookingAt[toonidx] = 'r'
            return toonHead.getRandomForwardLookAtPoint()
        else:
            other_toon_idxs = []
            for i in range(len(self.IsLookingAt)):
                if self.IsLookingAt[i] == toonidx:
                    other_toon_idxs.append(i)

            if len(other_toon_idxs) == 1:
                IgnoreStarersPercent = 0.4
            else:
                IgnoreStarersPercent = 0.2
            NoticeStarersPercent = 0.5
            bStareTargetTurnsToMe = 0
            if len(other_toon_idxs) == 0 or random.random() < IgnoreStarersPercent:
                other_toon_idxs = []
                for i in self.used_panel_indexs:
                    if i != toonidx:
                        other_toon_idxs.append(i)

                if random.random() < NoticeStarersPercent:
                    bStareTargetTurnsToMe = 1
            if len(other_toon_idxs) == 0:
                return toonHead.getRandomForwardLookAtPoint()
            else:
                lookingAtIdx = random.choice(other_toon_idxs)
            if bStareTargetTurnsToMe:
                self.IsLookingAt[lookingAtIdx] = toonidx
                otherToonHead = None
                for panel in self.panelList:
                    if panel.position == lookingAtIdx:
                        otherToonHead = panel.headModel

                otherToonHead.doLookAroundToStareAt(otherToonHead, self.getLookAtToPosVec(lookingAtIdx, toonidx))
            self.IsLookingAt[toonidx] = lookingAtIdx
            return self.getLookAtToPosVec(toonidx, lookingAtIdx)
        return

    def getLookAtToPosVec(self, fromIdx, toIdx):
        x = -(BASE_POSITIONS[toIdx][0] - BASE_POSITIONS[fromIdx][0])
        y = BASE_POSITIONS[toIdx][1] - BASE_POSITIONS[fromIdx][1]
        z = BASE_POSITIONS[toIdx][2] - BASE_POSITIONS[fromIdx][2]
        return Vec3(x, y, z)

    def initLookAtInfo(self):
        self.used_panel_indexs = []
        for panel in self.panelList:
            if panel.dna != None:
                self.used_panel_indexs.append(panel.position)

        if len(self.used_panel_indexs) == 0:
            return
        self.IsLookingAt = []
        for i in range(MAX_AVATARS):
            self.IsLookingAt.append('f')

        for panel in self.panelList:
            if panel.dna != None:
                panel.headModel.setLookAtPositionCallbackArgs((self, panel.headModel, panel.position))

        return

    def unload(self):
        if self.isLoaded == 0:
            return None
        cleanupDialog('globalDialog')
        for panel in self.panelList:
            panel.destroy()

        del self.panelList
        self.title.removeNode()
        del self.title
        self.quitButton.destroy()
        del self.quitButton
        self.logoutButton.destroy()
        del self.logoutButton
        if getattr(self, 'pickAToonBG', None):
            self.pickAToonBG.removeNode()
        del self.pickAToonBG
        del self.avatarList
        self.parentFSM.getCurrentState().removeChild(self.fsm)
        del self.parentFSM
        del self.fsm
        self.ignoreAll()
        self.isLoaded = 0
        ModelPool.garbageCollect()
        TexturePool.garbageCollect()
        return None

    def __handlePanelDone(self, panelDoneStatus, panelChoice = 0):
        self.doneStatus = {}
        self.doneStatus['mode'] = panelDoneStatus
        self.choice = panelChoice
        if panelDoneStatus == 'chose':
            self.__handleChoice()
        elif panelDoneStatus == 'nameIt':
            self.__handleCreate()
        elif panelDoneStatus == 'delete':
            self.__handleDelete()
        elif panelDoneStatus == 'create':
            self.__handleCreate()

    def getChoice(self):
        return self.choice

    def __handleChoice(self):
        self.fsm.request('CheckDownload')

    def __handleCreate(self):
        base.transitions.fadeOut(finishIval=EventInterval(self.doneEvent, [self.doneStatus]))

    def __handleDelete(self):
        messenger.send(self.doneEvent, [self.doneStatus])

    def __handleQuit(self):
        cleanupDialog('globalDialog')
        self.doneStatus = {'mode': 'exit'}
        messenger.send(self.doneEvent, [self.doneStatus])

    def enterChoose(self):
        pass

    def exitChoose(self):
        pass

    def enterCheckDownload(self):
        self.accept('downloadAck-response', self.__handleDownloadAck)
        self.downloadAck = DownloadForceAcknowledge.DownloadForceAcknowledge('downloadAck-response')
        self.downloadAck.enter(4)

    def exitCheckDownload(self):
        self.downloadAck.exit()
        self.downloadAck = None
        self.ignore('downloadAck-response')
        return

    def __handleDownloadAck(self, doneStatus):
        if doneStatus['mode'] == 'complete':
            base.transitions.fadeOut(finishIval=EventInterval(self.doneEvent, [self.doneStatus]))
        else:
            self.fsm.request('Choose')

    def __handleLogoutWithoutConfirm(self):
        base.cr.loginFSM.request('login')
