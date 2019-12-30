from .ClickablePopup import *
from .MarginPopup import *


class WhisperPopup(ClickablePopup, MarginPopup):
    WTNormal = 0
    WTQuickTalker = 1
    WTSystem = 2
    WTBattleSOS = 3
    WTEmote = 4
    WTToontownBoardingGroup = 5

    def __init__(self, text, font, type):
        ClickablePopup.__init__(self)
        MarginPopup.__init__(self)

        self.m_text = text
        self.m_font = font
        self.m_type = type

        self.m_np_balloon = None
        self.m_avname = ''
        self.m_region = None
        self.m_mouse_watcher = None
        self.m_manager = None

        # self.setCullCallback()
        self.cbNode = CallbackNode(self.getName() + '-cbNode')
        self.cbNode.setCullCallback(PythonCallbackObject(self.cullCallback))
        self.addChild(self.cbNode)

        self.m_time = 0
        self.m_culled = False
        self.m_clickable = False
        self.m_avid = 0
        self.m_is_player = False
        self.m_is_player_id = None
        self.m_state = 3
        self.m_objcode = 0

    def setClickable(self, avatar_name, avatar_id, is_player_id=False):
        self.m_clickable = True
        self.m_avname = avatar_name
        self.m_avid = avatar_id
        self.m_is_player_id = is_player_id
        self.m_state = 0

    def click(self):
        messenger.send('clickedWhisper', [self.m_avid, self.m_is_player])

    def considerVisible(self):
        if self.m_clickable and self.m_visible and self.m_mouse_watcher != NametagGlobals._mouse_watcher:
            return False

        if self.m_seq != NametagGlobals._margin_prop_seq:
            self.m_seq = NametagGlobals._margin_prop_seq
            self.updateContents()

        return True

    def manage(self, manager):
        self.m_manager = manager
        manager.managePopup(self)

    def unmanage(self, manager):
        manager.unmanagePopup(self)
        del self.m_manager

    def cullCallback(self, *args):
        if not self.m_culled:
            self.m_culled = True
            self.m_time = globalClock.getFrameTime()

    def setVisible(self, value):
        MarginPopup.setVisible(self, value)
        self.updateContents()

        if self.m_clickable:
            if self.m_region:
                if self.m_visible:
                    self.m_region.activate()
                    self.m_mouse_watcher = NametagGlobals._mouse_watcher
                    self.m_mouse_watcher.addRegion(self.m_region)

                elif self.m_mouse_watcher:
                    self.m_region.deactivate()
                    self.m_mouse_watcher.removeRegion(self.m_region)
                    self.m_mouse_watcher = None

    def setRegion(self, frame, sort):
        if self.m_region:
            self.m_region.setFrame(frame)

        else:
            self.m_region = self._createRegion(frame)

        self.m_region.setSort(sort)

    def updateContents(self):
        if self.m_np_balloon:
            self.m_np_balloon.removeNode()
            self.m_np_balloon = None

        if self.m_visible:
            self.generateText(NametagGlobals._speech_balloon_2d, self.m_text, self.m_font)

    def generateText(self, balloon, text, font):
        text_color = Vec4(NametagGlobals.getWhisperFg(self.m_type, self.m_state))
        balloon_color = Vec4(NametagGlobals.getWhisperBg(self.m_type, self.m_state))
        balloon_color[3] = max(balloon_color[3], NametagGlobals._min_2d_alpha)
        balloon_color[3] = min(balloon_color[3], NametagGlobals._max_2d_alpha)

        balloon_result = balloon.generate(text, font, 8.0, text_color, balloon_color,
                                          False, False, 0, None, False, False, None)

        self.m_np_balloon = self.m_np.attachNewNode(balloon_result)

        v34 = self.m_cell_width * 0.22222222
        v35 = balloon.m_text_height * balloon.m_hscale * 0.5
        v57 = -balloon.m_hscale * 5.5
        v16 = -(NametagGlobals._balloon_text_origin[2] + v35)

        v64 = Mat4(v34, 0, 0, 0,
                   0, v34, 0, 0,
                   0, 0, v34, 0,
                   v57 * v34, 0, v16 * v34, 1.0)

        self.m_np_balloon.setMat(v64)

        reducer = SceneGraphReducer()
        reducer.applyAttribs(self.m_np_balloon.node())

        if self.m_clickable:
            v22 = self.m_np.getNetTransform().getMat()
            v39, _, v41 = v22.xformPoint(Point3(v57 * v34, 0.0, v16 * v34))
            v27, _, v28 = v22.xformPoint(Point3(-v57 * v34, 0.0, -v16 * v34))
            self.setRegion(Vec4(v39, v27, v41, v28), 0)

    def setObjectCode(self, objcode):
        self.m_objcode = objcode

    def getObjectCode(self):
        return self.m_objcode

    def getScore(self):
        result = 2000

        if self.m_culled:
            elapsed = globalClock.getFrameTime() - self.m_time
            result -= elapsed * 200

            # moved from considerManage:
            if elapsed > 15.0:
                self.unmanage(self.m_manager)

        return result
