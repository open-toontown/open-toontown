from panda3d.core import *

_speech_balloon_3d = None


def setSpeechBalloon3d(speech_balloon_3d):
    global _speech_balloon_3d
    _speech_balloon_3d = speech_balloon_3d


def getSpeechBalloon3d():
    return _speech_balloon_3d


_global_nametag_scale = 1.0


def setGlobalNametagScale(global_nametag_scale):
    global _global_nametag_scale
    _global_nametag_scale = global_nametag_scale


def getGlobalNametagScale():
    return _global_nametag_scale


_camera = NodePath()


def setCamera(camera):
    global _camera
    _camera = camera


def getCamera():
    return _camera


_master_nametags_active = True


def setMasterNametagsActive(master_nametags_active):
    global _master_nametags_active
    _master_nametags_active = master_nametags_active


def getMasterNametagsActive():
    return _master_nametags_active


_min_2d_alpha = 0.0


def setMin2dAlpha(min_2d_alpha):
    global _min_2d_alpha
    global _margin_prop_seq
    _min_2d_alpha = min_2d_alpha
    _margin_prop_seq += 1


def getMin2dAlpha():
    return _min_2d_alpha


_arrow_color = [
    Vec4(1.0, 0.40000001, 0.2, 1.0),
    Vec4(1.0, 0.40000001, 0.2, 1.0),
    Vec4(1.0, 0.40000001, 0.2, 1.0),
    Vec4(1.0, 0.40000001, 0.2, 1.0),
    Vec4(0.30000001, 0.60000002, 1.0, 1.0),
    Vec4(0.55000001, 0.55000001, 0.55000001, 1.0),
    Vec4(0.30000001, 0.60000002, 1.0, 1.0),
    Vec4(0.30000001, 0.69999999, 0.30000001, 1.0),
    Vec4(0.30000001, 0.30000001, 0.69999999, 1.0)
]


def getArrowColor(index):
    return _arrow_color[index]


_mouse_watcher = None


def setMouseWatcher(mouse_watcher):
    global _mouse_watcher
    _mouse_watcher = mouse_watcher


def getMouseWatcher():
    return _mouse_watcher


_master_arrows_on = True


def setMasterArrowsOn(master_arrows_on):
    global _master_arrows_on
    _master_arrows_on = master_arrows_on


def getMasterArrowsOn():
    return _master_arrows_on


_toon = NodePath()


def setToon(toon):
    global _toon
    _toon = toon


def getToon():
    return _toon


_master_nametags_visible = True


def setMasterNametagsVisible(master_nametags_visible):
    global _master_nametags_visible
    _master_nametags_visible = master_nametags_visible


def getMasterNametagsVisible():
    return _master_nametags_visible


_thought_balloon_2d = None


def setThoughtBalloon2d(thought_balloon_2d):
    global _thought_balloon_2d
    _thought_balloon_2d = thought_balloon_2d


def getThoughtBalloon2d():
    return _thought_balloon_2d


_max_2d_alpha = 0.6


def setMax2dAlpha(max_2d_alpha):
    global _max_2d_alpha
    global _margin_prop_seq
    _max_2d_alpha = max_2d_alpha
    _margin_prop_seq += 1


def getMax2dAlpha():
    return _max_2d_alpha


_onscreen_chat_forced = False


def setOnscreenChatForced(onscreen_chat_forced):
    global _onscreen_chat_forced
    _onscreen_chat_forced = onscreen_chat_forced


def getOnscreenChatForced():
    return _onscreen_chat_forced


_nametag_card = NodePath()


def setNametagCard(nametag_card, nametag_card_frame):
    global _nametag_card
    global _nametag_card_frame
    _nametag_card = nametag_card
    _nametag_card_frame = nametag_card_frame


def getNametagCard():
    return _nametag_card


_nametag_card_frame = Vec4(0, 0, 0, 0)


def getNametagCardFrame():
    return _nametag_card_frame


_rollover_sound = None


def setRolloverSound(rollover_sound):
    global _rollover_sound
    _rollover_sound = rollover_sound


def getRolloverSound():
    return _rollover_sound


_speech_balloon_2d = None


def setSpeechBalloon2d(speech_balloon_2d):
    global _speech_balloon_2d
    _speech_balloon_2d = speech_balloon_2d


def getSpeechBalloon2d():
    return _speech_balloon_2d


_text_node = TextNode('nametag')


def getTextNode():
    return _text_node


_click_sound = None


def setClickSound(click_sound):
    global _click_sound
    _click_sound = click_sound


def getClickSound():
    return _click_sound


_quit_button = [NodePath(), NodePath(), NodePath(), NodePath()]


def setQuitButton(state, quit_button):
    global _quit_button
    _quit_button[state] = quit_button


def getQuitButton(state):
    return _quit_button[state]


_arrow_model = NodePath()


def setArrowModel(arrow_model):
    global _arrow_model
    _arrow_model = arrow_model


def getArrowModel():
    return _arrow_model


_thought_balloon_3d = None


def setThoughtBalloon3d(thought_balloon_3d):
    global _thought_balloon_3d
    _thought_balloon_3d = thought_balloon_3d


def getThoughtBalloon3d():
    return _thought_balloon_3d


_name_bg = [
    # CCNormal
    Vec4(0.8, 0.8, 0.8, 0.5),
    Vec4(0.2, 0.2, 0.2, 0.6),
    Vec4(1, 1, 1, 1),
    Vec4(0.8, 0.8, 0.8, 0.5),

    # CCNoChat
    Vec4(1, 1, 1, 0.5),
    Vec4(0.2, 0.2, 0.2, 0.6),
    Vec4(1, 1, 1, 1),
    Vec4(0.8, 0.8, 0.8, 0.5),

    # CCNonPlayer
    Vec4(1, 1, 1, 0.5),
    Vec4(0.2, 0.2, 0.2, 0.6),
    Vec4(1, 1, 1, 1),
    Vec4(0.8, 0.8, 0.8, 0.5),

    # CCSuit
    Vec4(0.8, 0.8, 0.8, 0.5),
    Vec4(0.2, 0.2, 0.2, 0.6),
    Vec4(1, 1, 1, 1),
    Vec4(0.8, 0.8, 0.8, 0.5),

    # CCToonBuilding
    Vec4(0.8, 0.8, 0.8, 0.5),
    Vec4(0.2, 0.2, 0.2, 0.6),
    Vec4(1, 1, 1, 1),
    Vec4(0.8, 0.8, 0.8, 0.5),

    # CCSuitBuilding
    Vec4(0.8, 0.8, 0.8, 0.5),
    Vec4(0.2, 0.2, 0.2, 0.6),
    Vec4(1, 1, 1, 1),
    Vec4(0.8, 0.8, 0.8, 0.5),

    # CCHouseBuilding
    Vec4(0.8, 0.8, 0.8, 0.5),
    Vec4(0.2, 0.2, 0.2, 0.6),
    Vec4(1, 1, 1, 1),
    Vec4(0.8, 0.8, 0.8, 0.5),

    # CCSpeedChat
    Vec4(1, 1, 1, 0.5),
    Vec4(0.2, 0.2, 0.2, 0.6),
    Vec4(1, 1, 1, 1),
    Vec4(0.8, 0.8, 0.8, 0.5),

    # CCFreeChat
    Vec4(0.8, 0.8, 0.8, 0.5),
    Vec4(0.2, 0.2, 0.2, 0.6),
    Vec4(1, 1, 1, 1),
    Vec4(0.8, 0.8, 0.8, 0.5)
]


def getNameBg(color_code, state):
    return _name_bg[4 * color_code + state]


_page_button = [NodePath(), NodePath(), NodePath(), NodePath()]


def setPageButton(state, page_button):
    global _page_button
    _page_button[state] = page_button


def getPageButton(state):
    return _page_button[state]


_name_fg = [
    # CCNormal
    Vec4(0, 0, 1, 1),
    Vec4(0.5, 0.5, 1, 1),
    Vec4(0.5, 0.5, 1, 1),
    Vec4(0.3, 0.3, 0.7, 1),

    # CCNoChat
    Vec4(0.8, 0.4, 0, 1),
    Vec4(1, 0.5, 0.5, 1),
    Vec4(1, 0.5, 0, 1),
    Vec4(0.6, 0.4, 0.2, 1),

    # CCNonPlayer
    Vec4(0.8, 0.4, 0, 1),
    Vec4(1, 0.5, 0.5, 1),
    Vec4(1, 0.5, 0, 1),
    Vec4(0.6, 0.4, 0.2, 1),

    # CCSuit
    Vec4(0, 0, 0, 1),
    Vec4(1, 1, 1, 1),
    Vec4(0.5, 0.5, 0.5, 1),
    Vec4(0.2, 0.2, 0.2, 1),

    # CCToonBuilding
    Vec4(0, 0, 0, 1),
    Vec4(1, 1, 1, 1),
    Vec4(0.5, 0.5, 0.5, 1),
    Vec4(0.3, 0.6, 1, 1),

    # CCSuitBuilding
    Vec4(0, 0, 0, 1),
    Vec4(1, 1, 1, 1),
    Vec4(0.5, 0.5, 0.5, 1),
    Vec4(0.55, 0.55, 0.55, 1),

    # CCHouseBuilding
    Vec4(0, 0, 0, 1),
    Vec4(1, 1, 1, 1),
    Vec4(0.5, 0.5, 0.5, 1),
    Vec4(0.3, 0.6, 1, 1),

    # CCSpeedChat
    Vec4(0, 0.6, 0.2, 1),
    Vec4(0, 0.6, 0.2, 1),
    Vec4(0, 1, 0.5, 1),
    Vec4(0.1, 0.4, 0.2, 1),

    # CCFreeChat
    Vec4(0.3, 0.3, 0.7, 1),
    Vec4(0.2, 0.2, 0.5, 1),
    Vec4(0.5, 0.5, 1, 1),
    Vec4(0.3, 0.3, 0.7, 1)
]


def getNameFg(color_code, state):
    return _name_fg[4 * color_code + state]


def getNameWordwrap():
    return 7.5


_card_pad = Vec4(0.1, 0.1, 0.1, 0)


def getCardPad():
    return _card_pad


_whisper_colors = [
    [
        (Vec4(0.0, 0.0, 0.0, 1.0), Vec4(0.3, 0.6, 0.8, 0.6)),
        (Vec4(1.0, 0.5, 0.5, 1.0), Vec4(1.0, 1.0, 1.0, 1.0)),
        (Vec4(0.0, 0.0, 0.0, 1.0), Vec4(0.4, 0.8, 1.0, 1.0)),
        (Vec4(0.0, 0.0, 0.0, 1.0), Vec4(0.3, 0.6, 0.8, 0.6))
    ],
    [
        (Vec4(0.0, 0.0, 0.0, 1.0), Vec4(0.3, 0.6, 0.8, 0.6)),
        (Vec4(1.0, 0.5, 0.5, 1.0), Vec4(1.0, 1.0, 1.0, 1.0)),
        (Vec4(0.0, 0.0, 0.0, 1.0), Vec4(0.4, 0.8, 1.0, 1.0)),
        (Vec4(0.0, 0.0, 0.0, 1.0), Vec4(0.3, 0.6, 0.8, 0.6))
    ],
    [
        (Vec4(0.0, 0.0, 0.0, 1.0), Vec4(0.8, 0.3, 0.6, 0.6)),
        (Vec4(1.0, 0.5, 0.5, 1.0), Vec4(1.0, 1.0, 1.0, 1.0)),
        (Vec4(0.0, 0.0, 0.0, 1.0), Vec4(0.8, 0.4, 1.0, 1.0)),
        (Vec4(0.0, 0.0, 0.0, 1.0), Vec4(0.8, 0.3, 0.6, 0.6))
    ],
    [
        (Vec4(0.0, 0.0, 0.0, 1.0), Vec4(0.8, 0.3, 0.6, 0.6)),
        (Vec4(1.0, 0.5, 0.5, 1.0), Vec4(1.0, 1.0, 1.0, 1.0)),
        (Vec4(0.0, 0.0, 0.0, 1.0), Vec4(0.8, 0.4, 1.0, 1.0)),
        (Vec4(0.0, 0.0, 0.0, 1.0), Vec4(0.8, 0.3, 0.6, 0.6))
    ],
    [
        (Vec4(0.0, 0.0, 0.0, 1.0), Vec4(0.3, 0.6, 0.8, 0.6)),
        (Vec4(1.0, 0.5, 0.5, 1.0), Vec4(1.0, 1.0, 1.0, 1.0)),
        (Vec4(0.0, 0.0, 0.0, 1.0), Vec4(0.4, 1.0, 1.0, 0.4)),
        (Vec4(0.0, 0.0, 0.0, 1.0), Vec4(0.3, 0.8, 0.3, 0.6))
    ],
    [
        (Vec4(0.0, 0.0, 0.0, 1.0), Vec4(0.97, 0.43, 0.1, 0.6)),
        (Vec4(1.0, 0.5, 0.5, 1.0), Vec4(1.0, 1.0, 1.0, 1.0)),
        (Vec4(0.0, 0.0, 0.0, 1.0), Vec4(0.98, 0.6, 0.38, 0.6)),
        (Vec4(0.0, 0.0, 0.0, 1.0), Vec4(0.97, 0.43, 0.1, 0.6))
    ]
]


def getWhisperFg(color_code, state):
    return Vec4(_whisper_colors[color_code][state][0])


def getWhisperBg(color_code, state):
    return Vec4(_whisper_colors[color_code][state][1])


_balloon_modulation_color = Vec4(1.0, 1.0, 1.0, 1.0)


def setBalloonModulationColor(balloon_modulation_color):
    global _balloon_modulation_color
    _balloon_modulation_color = balloon_modulation_color


def getBalloonModulationColor():
    return _balloon_modulation_color


def getChatFg(color_code, state):
    return [Vec4(0.0, 0.0, 0.0, 1.0),
            Vec4(1.0, 0.5, 0.5, 1.0),
            Vec4(0.0, 0.6, 0.6, 1.0),
            Vec4(0.0, 0.0, 0.0, 1.0)][state]


def getChatBg(color_code, state):
    return [Vec4(1.0, 1.0, 1.0, 1.0),
            Vec4(1.0, 1.0, 1.0, 1.0),
            Vec4(1.0, 1.0, 1.0, 1.0),
            Vec4(1.0, 1.0, 1.0, 1.0)][state]


_margin_prop_seq = 0
_default_qt_color = Vec4(0.8, 0.8, 1, 1)
_balloon_text_origin = Point3(1.0, 0, 2.0)
