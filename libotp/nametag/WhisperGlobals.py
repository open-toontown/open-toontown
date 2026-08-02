from enum import IntEnum, auto

from panda3d.core import Vec4

from .ColorProfile import ColorProfile, GRAY


class WhisperType(IntEnum):

    WTNormal                = auto()
    WTQuickTalker           = auto()
    WTSystem                = auto()
    WTBattleSOS             = auto()
    WTEmote                 = auto()
    WTToontownBoardingGroup = auto()
    WTMagicWord             = auto()


# Defines some default color profiles from a whisper type.
# Overrides can however be defined when calling localAvatar.displayWhisper()
# Maps whisper type -> (ColorProfile(text), ColorProfile(background))
WHISPER_COLORS = {

    # Normal whisper popups
    WhisperType.WTNormal: (
        ColorProfile(Vec4(0.0, 0.0, 0.0, 1.0), Vec4(1.0, 0.5, 0.5, 1.0), Vec4(0.0, 0.0, 0.0, 1.0),Vec4(0.0, 0.0, 0.0, 1.0)),
        ColorProfile(Vec4(0.3, 0.6, 0.8, 0.6), Vec4(1.0, 1.0, 1.0, 1.0), Vec4(0.4, 0.8, 1.0, 1.0),Vec4(0.3, 0.6, 0.8, 0.6)),
    ),

    # Toons whispering to each other
    WhisperType.WTQuickTalker: (
        ColorProfile(Vec4(0.0, 0.0, 0.0, 1.0), Vec4(1.0, 0.5, 0.5, 1.0), Vec4(0.0, 0.0, 0.0, 1.0), Vec4(0.0, 0.0, 0.0, 1.0)),
        ColorProfile(Vec4(0.3, 0.6, 0.8, 0.6), Vec4(1.0, 1.0, 1.0, 1.0), Vec4(0.4, 0.8, 1.0, 1.0), Vec4(0.3, 0.6, 0.8, 0.6)),
    ),

    # System messages
    WhisperType.WTSystem: (
        ColorProfile(Vec4(0.0, 0.0, 0.0, 1.0), Vec4(1.0, 0.5, 0.5, 1.0), Vec4(0.0, 0.0, 0.0, 1.0), Vec4(0.0, 0.0, 0.0, 1.0)),
        ColorProfile(Vec4(0.8, 0.3, 0.6, 0.6), Vec4(1.0, 1.0, 1.0, 1.0), Vec4(0.8, 0.4, 1.0, 1.0), Vec4(0.8, 0.3, 0.6, 0.6)),
    ),

    # Battle SOS
    WhisperType.WTBattleSOS: (
        ColorProfile(Vec4(0.0, 0.0, 0.0, 1.0),   Vec4(1.0, 0.5, 0.5, 1.0), Vec4(0.0, 0.0, 0.0, 1.0),   Vec4(0.0, 0.0, 0.0, 1.0)),
        ColorProfile(Vec4(0.8, 0.3, 0.6, 0.6),   Vec4(1.0, 1.0, 1.0, 1.0), Vec4(0.8, 0.4, 1.0, 1.0),   Vec4(0.8, 0.3, 0.6, 0.6)),
    ),

    # Emote whispers
    WhisperType.WTEmote: (
        ColorProfile(Vec4(0.0, 0.0, 0.0, 1.0),   Vec4(1.0, 0.5, 0.5, 1.0), Vec4(0.0, 0.0, 0.0, 1.0),   Vec4(0.0, 0.0, 0.0, 1.0)),
        ColorProfile(Vec4(0.3, 0.6, 0.8, 0.6),   Vec4(1.0, 1.0, 1.0, 1.0), Vec4(0.4, 1.0, 1.0, 0.4),   Vec4(0.3, 0.8, 0.3, 0.6)),
    ),

    # Boarding groups
    WhisperType.WTToontownBoardingGroup: (
        ColorProfile(Vec4(0.0, 0.0, 0.0, 1.0),   Vec4(1.0, 0.5, 0.5, 1.0), Vec4(0.0, 0.0, 0.0, 1.0),   Vec4(0.0, 0.0, 0.0, 1.0)),
        ColorProfile(Vec4(0.97, 0.43, 0.1, 0.6), Vec4(1.0, 1.0, 1.0, 1.0), Vec4(0.98, 0.6, 0.38, 0.6), Vec4(0.97, 0.43, 0.1, 0.6)),
    ),

    # Commands
    WhisperType.WTMagicWord: (
        ColorProfile(Vec4(0.0, 0.0, 0.0, 1.0),   Vec4(1.0, 0.5, 0.5, 1.0), Vec4(0.0, 0.0, 0.0, 1.0),   Vec4(0.0, 0.0, 0.0, 1.0)),
        ColorProfile(Vec4(0.7, 0.7, 0.1, 0.6),   Vec4(1.0, 1.0, 0.4, 0.8), Vec4(0.8, 0.8, 0.2, 0.6),   Vec4(0.8, 0.8, 0.1, 0.6)),
    ),

}

# Indeces of what is stored in the above dict per whisper type
TEXT_COLOR = 0
BACKGROUND_COLOR = 1


# Given a whisper type, return its color profile for text.
# If not found, returns gray as a fallback.
def getWhisperTextColorProfile(color_code: WhisperType):

    colors = WHISPER_COLORS.get(color_code)
    if colors is None:
        print(f'WhisperGlobals.getWhisperTextColorProfile(): Unknown color code: {color_code}! Defaulting to GRAY.')
        return GRAY

    return colors[TEXT_COLOR]


# Given a whisper type,
def getWhisperBackgroundColorProfile(color_code):

    colors = WHISPER_COLORS.get(color_code)
    if colors is None:
        print(f'WhisperGlobals.getWhisperBackgroundColorProfile(): Unknown color code: {color_code}! Defaulting to GRAY.')
        return GRAY

    return colors[BACKGROUND_COLOR]



