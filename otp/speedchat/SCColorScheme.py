from ColorSpace import *

class SCColorScheme:

    def __init__(self, arrowColor = (0.5, 0.5, 1), rolloverColor = (0.53, 0.9, 0.53), frameColor = None, pressedColor = None, menuHolderActiveColor = None, emoteIconColor = None, textColor = (0, 0, 0), emoteIconDisabledColor = (0.5, 0.5, 0.5), textDisabledColor = (0.4, 0.4, 0.4), alpha = 0.95):

        def scaleColor(color, s):
            y, u, v = rgb2yuv(*color)
            return yuv2rgb(y * s, u, v)

        def scaleIfNone(color, srcColor, s):
            if color is not None:
                return color
            else:
                return scaleColor(srcColor, s)
            return

        self.__arrowColor = arrowColor
        self.__rolloverColor = rolloverColor
        self.__frameColor = frameColor
        if self.__frameColor is None:
            h, s, v = rgb2hsv(*arrowColor)
            self.__frameColor = hsv2rgb(h, 0.2 * s, v)
        h, s, v = rgb2hsv(*self.__frameColor)
        self.__frameColor = hsv2rgb(h, 0.5 * s, v)
        self.__pressedColor = scaleIfNone(pressedColor, self.__rolloverColor, 0.92)
        self.__menuHolderActiveColor = scaleIfNone(menuHolderActiveColor, self.__rolloverColor, 0.84)
        self.__emoteIconColor = emoteIconColor
        if self.__emoteIconColor is None:
            h, s, v = rgb2hsv(*self.__rolloverColor)
            self.__emoteIconColor = hsv2rgb(h, 1.0, 0.8 * v)
        self.__emoteIconDisabledColor = emoteIconDisabledColor
        self.__textColor = textColor
        self.__textDisabledColor = textDisabledColor
        self.__alpha = alpha
        return

    def getArrowColor(self):
        return self.__arrowColor

    def getRolloverColor(self):
        return self.__rolloverColor

    def getFrameColor(self):
        return self.__frameColor

    def getPressedColor(self):
        return self.__pressedColor

    def getMenuHolderActiveColor(self):
        return self.__menuHolderActiveColor

    def getEmoteIconColor(self):
        return self.__emoteIconColor

    def getTextColor(self):
        return self.__textColor

    def getEmoteIconDisabledColor(self):
        return self.__emoteIconDisabledColor

    def getTextDisabledColor(self):
        return self.__textDisabledColor

    def getAlpha(self):
        return self.__alpha

    def __str__(self):
        members = ('arrowColor', 'rolloverColor', 'frameColor', 'pressedColor', 'menuHolderActiveColor', 'emoteIconColor', 'textColor', 'emoteIconDisabledColor', 'textDisabledColor', 'alpha')
        result = ''
        for member in members:
            result += '%s = %s' % (member, self.__dict__['_%s__%s' % (self.__class__.__name__, member)])
            if member is not members[-1]:
                result += '\n'

        return result

    def __repr__(self):
        return str(self)
