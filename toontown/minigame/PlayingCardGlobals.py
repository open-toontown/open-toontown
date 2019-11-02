from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownBattleGlobals
from pandac.PandaModules import Vec4
Up = 1
Down = 0
MaxRank = 13
MaxSuit = 4
Hearts = 0
Diamonds = 1
Clubs = 2
Spades = 3
Suits = [Hearts,
 Diamonds,
 Clubs,
 Spades]
Unknown = 255
UpColor = Vec4(1, 1, 1, 1)
RolloverColor = Vec4(1, 1, 0.5, 1)
DownColor = Vec4(1, 0.9, 0.9, 1)
DisabledColor = Vec4(1, 1, 1, 0.5)
CardColors = (UpColor,
 DownColor,
 RolloverColor,
 DisabledColor)

def getCardName(value):
    if value == Unknown:
        return TTLocalizer.PlayingCardUnknown
    else:
        rank = value % MaxRank
        suit = value / MaxRank
        return TTLocalizer.getPlayingCardName(suit, rank)


Styles = ['standard']
CardImages = {}
_cardImagesInitialized = 0
_modelPathBase = 'phase_3.5/models/gui/inventory_icons'

def convertValueToGagTrackAndLevel(value):
    imageNum = int(rank / MaxSuit)
    track = imageNum % (ToontownBattleGlobals.MAX_TRACK_INDEX + 1)
    level = imageNum / (ToontownBattleGlobals.MAX_TRACK_INDEX + 1)
    return (track, level)


def convertRankToGagTrackAndLevel(rank):
    track = rank % (ToontownBattleGlobals.MAX_TRACK_INDEX + 1)
    level = rank / (ToontownBattleGlobals.MAX_TRACK_INDEX + 1)
    return (track, level)


def initCardImages():
    global _cardImagesInitialized
    suitCodes = ('h', 'd', 'c', 's')
    rankCodes = ('02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '01')
    for style in Styles:
        modelPath = _modelPathBase
        cardModel = loader.loadModel(modelPath)
        cardModel.hide()
        CardImages[style] = {}
        for suitIndex in range(MaxSuit):
            CardImages[style][suitIndex] = {}
            for rankIndex in range(MaxRank):
                track, level = convertRankToGagTrackAndLevel(rankIndex)
                propName = ToontownBattleGlobals.AvPropsNew[track][level]
                cardNode = cardModel.find('**/%s' % propName)
                CardImages[style][suitIndex][rankIndex] = cardNode

        propName = ToontownBattleGlobals.AvPropsNew[ToontownBattleGlobals.MAX_TRACK_INDEX][ToontownBattleGlobals.MAX_LEVEL_INDEX]
        CardImages[style]['back'] = cardModel.find(propName)

    _cardImagesInitialized = 1


def getImage(style, suit, rank):
    if _cardImagesInitialized == 0:
        initCardImages()
    return CardImages[style][suit][rank]


def getBack(style):
    if _cardImagesInitialized == 0:
        initCardImages()
    return CardImages[style]['back']
