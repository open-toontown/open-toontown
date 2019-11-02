from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals
GREETING = 0
COMMENT = 1
GOODBYE = 2
DaisyChatter = TTLocalizer.DaisyChatter
MickeyChatter = TTLocalizer.MickeyChatter
VampireMickeyChatter = TTLocalizer.VampireMickeyChatter
MinnieChatter = TTLocalizer.MinnieChatter
GoofyChatter = TTLocalizer.GoofyChatter
GoofySpeedwayChatter = TTLocalizer.GoofySpeedwayChatter
DonaldChatter = TTLocalizer.DonaldChatter
ChipChatter = TTLocalizer.ChipChatter
DaleChatter = TTLocalizer.DaleChatter

def getExtendedChat(chatset, extendedChat):
    newChat = []
    for chatList in chatset:
        newChat.append(list(chatList))

    newChat[1] += extendedChat
    return newChat


def getChatter(charName, chatterType):
    if charName == TTLocalizer.Mickey:
        if chatterType == ToontownGlobals.APRIL_FOOLS_COSTUMES:
            return TTLocalizer.AFMickeyChatter
        elif chatterType == ToontownGlobals.WINTER_CAROLING:
            return TTLocalizer.WinterMickeyCChatter
        elif chatterType == ToontownGlobals.WINTER_DECORATIONS:
            return TTLocalizer.WinterMickeyDChatter
        elif chatterType == ToontownGlobals.WACKY_WINTER_CAROLING:
            return TTLocalizer.WinterMickeyCChatter
        elif chatterType == ToontownGlobals.WACKY_WINTER_DECORATIONS:
            return TTLocalizer.WinterMickeyDChatter
        elif chatterType == ToontownGlobals.VALENTINES_DAY:
            return TTLocalizer.ValentinesMickeyChatter
        elif chatterType == ToontownGlobals.SILLY_CHATTER_ONE:
            SillyMickeyChatter = getExtendedChat(MickeyChatter, TTLocalizer.SillyPhase1Chatter)
            return SillyMickeyChatter
        elif chatterType == ToontownGlobals.SILLY_CHATTER_TWO:
            SillyMickeyChatter = getExtendedChat(MickeyChatter, TTLocalizer.SillyPhase2Chatter)
            return SillyMickeyChatter
        elif chatterType == ToontownGlobals.SILLY_CHATTER_THREE:
            SillyMickeyChatter = getExtendedChat(MickeyChatter, TTLocalizer.SillyPhase3Chatter)
            return SillyMickeyChatter
        elif chatterType == ToontownGlobals.SILLY_CHATTER_FOUR:
            SillyMickeyChatter = getExtendedChat(MickeyChatter, TTLocalizer.SillyPhase4Chatter)
            return SillyMickeyChatter
        elif chatterType == ToontownGlobals.SELLBOT_FIELD_OFFICE:
            fieldOfficeMickeyChatter = getExtendedChat(MickeyChatter, TTLocalizer.FieldOfficeMickeyChatter)
            return fieldOfficeMickeyChatter
        else:
            return MickeyChatter
    elif charName == TTLocalizer.VampireMickey:
        return VampireMickeyChatter
    elif charName == TTLocalizer.Minnie:
        if chatterType == ToontownGlobals.APRIL_FOOLS_COSTUMES:
            return TTLocalizer.AFMinnieChatter
        elif chatterType == ToontownGlobals.WINTER_CAROLING:
            return TTLocalizer.WinterMinnieCChatter
        elif chatterType == ToontownGlobals.WINTER_DECORATIONS:
            return TTLocalizer.WinterMinnieDChatter
        elif chatterType == ToontownGlobals.WACKY_WINTER_CAROLING:
            return TTLocalizer.WinterMinnieCChatter
        elif chatterType == ToontownGlobals.WACKY_WINTER_DECORATIONS:
            return TTLocalizer.WinterMinnieDChatter
        elif chatterType == ToontownGlobals.VALENTINES_DAY:
            return TTLocalizer.ValentinesMinnieChatter
        elif chatterType == ToontownGlobals.SILLY_CHATTER_ONE:
            SillyMinnieChatter = getExtendedChat(MinnieChatter, TTLocalizer.SillyPhase1Chatter)
            return SillyMinnieChatter
        elif chatterType == ToontownGlobals.SILLY_CHATTER_TWO:
            SillyMinnieChatter = getExtendedChat(MinnieChatter, TTLocalizer.SillyPhase2Chatter)
            return SillyMinnieChatter
        elif chatterType == ToontownGlobals.SILLY_CHATTER_THREE:
            SillyMinnieChatter = getExtendedChat(MinnieChatter, TTLocalizer.SillyPhase3Chatter)
            return SillyMinnieChatter
        elif chatterType == ToontownGlobals.SILLY_CHATTER_FOUR:
            SillyMinnieChatter = getExtendedChat(MinnieChatter, TTLocalizer.SillyPhase4Chatter)
            return SillyMinnieChatter
        elif chatterType == ToontownGlobals.SELLBOT_FIELD_OFFICE:
            fieldOfficeMinnieChatter = getExtendedChat(MinnieChatter, TTLocalizer.FieldOfficeMinnieChatter)
            return fieldOfficeMinnieChatter
        else:
            return MinnieChatter
    elif charName == TTLocalizer.WitchMinnie:
        return TTLocalizer.WitchMinnieChatter
    elif charName == TTLocalizer.Daisy or charName == TTLocalizer.SockHopDaisy:
        if chatterType == ToontownGlobals.APRIL_FOOLS_COSTUMES:
            return TTLocalizer.AFDaisyChatter
        elif chatterType == ToontownGlobals.HALLOWEEN_COSTUMES:
            return TTLocalizer.HalloweenDaisyChatter
        elif chatterType == ToontownGlobals.SPOOKY_COSTUMES:
            return TTLocalizer.HalloweenDaisyChatter
        elif chatterType == ToontownGlobals.WINTER_CAROLING:
            return TTLocalizer.WinterDaisyCChatter
        elif chatterType == ToontownGlobals.WINTER_DECORATIONS:
            return TTLocalizer.WinterDaisyDChatter
        elif chatterType == ToontownGlobals.WACKY_WINTER_CAROLING:
            return TTLocalizer.WinterDaisyCChatter
        elif chatterType == ToontownGlobals.WACKY_WINTER_DECORATIONS:
            return TTLocalizer.WinterDaisyDChatter
        elif chatterType == ToontownGlobals.VALENTINES_DAY:
            return TTLocalizer.ValentinesDaisyChatter
        elif chatterType == ToontownGlobals.SILLY_CHATTER_ONE:
            SillyDaisyChatter = getExtendedChat(DaisyChatter, TTLocalizer.SillyPhase1Chatter)
            return SillyDaisyChatter
        elif chatterType == ToontownGlobals.SILLY_CHATTER_TWO:
            SillyDaisyChatter = getExtendedChat(DaisyChatter, TTLocalizer.SillyPhase2Chatter)
            return SillyDaisyChatter
        elif chatterType == ToontownGlobals.SILLY_CHATTER_THREE:
            SillyDaisyChatter = getExtendedChat(DaisyChatter, TTLocalizer.SillyPhase3Chatter)
            return SillyDaisyChatter
        elif chatterType == ToontownGlobals.SILLY_CHATTER_FOUR:
            SillyDaisyChatter = getExtendedChat(DaisyChatter, TTLocalizer.SillyPhase4Chatter)
            return SillyDaisyChatter
        elif chatterType == ToontownGlobals.SELLBOT_FIELD_OFFICE:
            fieldOfficeDaisyChatter = getExtendedChat(DaisyChatter, TTLocalizer.FieldOfficeDaisyChatter)
            return fieldOfficeDaisyChatter
        else:
            return DaisyChatter
    elif charName == TTLocalizer.Goofy:
        if chatterType == ToontownGlobals.APRIL_FOOLS_COSTUMES:
            return TTLocalizer.AFGoofySpeedwayChatter
        elif chatterType == ToontownGlobals.CRASHED_LEADERBOARD:
            return TTLocalizer.CLGoofySpeedwayChatter
        elif chatterType == ToontownGlobals.CIRCUIT_RACING_EVENT:
            return TTLocalizer.GPGoofySpeedwayChatter
        elif chatterType == ToontownGlobals.WINTER_DECORATIONS or chatterType == ToontownGlobals.WINTER_CAROLING or chatterType == ToontownGlobals.WACKY_WINTER_DECORATIONS or chatterType == ToontownGlobals.WACKY_WINTER_CAROLING:
            return TTLocalizer.WinterGoofyChatter
        elif chatterType == ToontownGlobals.VALENTINES_DAY:
            return TTLocalizer.ValentinesGoofyChatter
        elif chatterType == ToontownGlobals.SILLY_CHATTER_ONE:
            SillyGoofySpeedwayChatter = getExtendedChat(GoofySpeedwayChatter, TTLocalizer.SillyPhase1Chatter)
            return SillyGoofySpeedwayChatter
        elif chatterType == ToontownGlobals.SILLY_CHATTER_TWO:
            SillyGoofySpeedwayChatter = getExtendedChat(GoofySpeedwayChatter, TTLocalizer.SillyPhase2Chatter)
            return SillyGoofySpeedwayChatter
        elif chatterType == ToontownGlobals.SILLY_CHATTER_THREE:
            SillyGoofySpeedwayChatter = getExtendedChat(GoofySpeedwayChatter, TTLocalizer.SillyPhase3Chatter)
            return SillyGoofySpeedwayChatter
        elif chatterType == ToontownGlobals.SILLY_CHATTER_FOUR:
            SillyGoofySpeedwayChatter = getExtendedChat(GoofySpeedwayChatter, TTLocalizer.SillyPhase4Chatter)
            return SillyGoofySpeedwayChatter
        else:
            return GoofySpeedwayChatter
    elif charName == TTLocalizer.SuperGoofy:
        return TTLocalizer.SuperGoofyChatter
    elif charName == TTLocalizer.Donald or charName == TTLocalizer.FrankenDonald:
        if chatterType == ToontownGlobals.APRIL_FOOLS_COSTUMES:
            return TTLocalizer.AFDonaldChatter
        elif chatterType == ToontownGlobals.HALLOWEEN_COSTUMES:
            return TTLocalizer.HalloweenDreamlandChatter
        elif chatterType == ToontownGlobals.SPOOKY_COSTUMES:
            return TTLocalizer.HalloweenDreamlandChatter
        elif chatterType == ToontownGlobals.WINTER_CAROLING:
            return TTLocalizer.WinterDreamlandCChatter
        elif chatterType == ToontownGlobals.WINTER_DECORATIONS:
            return TTLocalizer.WinterDreamlandDChatter
        elif chatterType == ToontownGlobals.WACKY_WINTER_CAROLING:
            return TTLocalizer.WinterDreamlandCChatter
        elif chatterType == ToontownGlobals.WACKY_WINTER_DECORATIONS:
            return TTLocalizer.WinterDreamlandDChatter
        elif chatterType == ToontownGlobals.VALENTINES_DAY:
            return TTLocalizer.ValentinesDreamlandChatter
        elif chatterType == ToontownGlobals.SELLBOT_FIELD_OFFICE:
            fieldOfficeDreamlandChatter = getExtendedChat(DonaldChatter, TTLocalizer.FieldOfficeDreamlandChatter)
            return fieldOfficeDreamlandChatter
        else:
            return DonaldChatter
    elif charName == TTLocalizer.DonaldDock:
        if chatterType == ToontownGlobals.APRIL_FOOLS_COSTUMES:
            return TTLocalizer.AFDonaldDockChatter
        elif chatterType == ToontownGlobals.HALLOWEEN_COSTUMES:
            return TTLocalizer.HalloweenDonaldChatter
        elif chatterType == ToontownGlobals.SPOOKY_COSTUMES:
            return TTLocalizer.HalloweenDonaldChatter
        elif chatterType == ToontownGlobals.WINTER_CAROLING:
            return TTLocalizer.WinterDonaldCChatter
        elif chatterType == ToontownGlobals.WINTER_DECORATIONS:
            return TTLocalizer.WinterDonaldDChatter
        elif chatterType == ToontownGlobals.WACKY_WINTER_CAROLING:
            return TTLocalizer.WinterDonaldCChatter
        elif chatterType == ToontownGlobals.WACKY_WINTER_DECORATIONS:
            return TTLocalizer.WinterDonaldDChatter
        elif chatterType == ToontownGlobals.VALENTINES_DAY:
            return TTLocalizer.ValentinesDonaldChatter
        else:
            return None
    elif charName == TTLocalizer.Pluto:
        if chatterType == ToontownGlobals.APRIL_FOOLS_COSTUMES:
            return TTLocalizer.AFPlutoChatter
        elif chatterType == ToontownGlobals.HALLOWEEN_COSTUMES:
            return TTLocalizer.WesternPlutoChatter
        elif chatterType == ToontownGlobals.SPOOKY_COSTUMES:
            return TTLocalizer.WesternPlutoChatter
        elif chatterType == ToontownGlobals.WINTER_CAROLING:
            return TTLocalizer.WinterPlutoCChatter
        elif chatterType == ToontownGlobals.WINTER_DECORATIONS:
            return TTLocalizer.WinterPlutoDChatter
        elif chatterType == ToontownGlobals.WACKY_WINTER_CAROLING:
            return TTLocalizer.WinterPlutoCChatter
        elif chatterType == ToontownGlobals.WACKY_WINTER_DECORATIONS:
            return TTLocalizer.WinterPlutoDChatter
        else:
            return None
    elif charName == TTLocalizer.WesternPluto:
        if chatterType == ToontownGlobals.HALLOWEEN_COSTUMES:
            return TTLocalizer.WesternPlutoChatter
        elif chatterType == ToontownGlobals.SPOOKY_COSTUMES:
            return TTLocalizer.WesternPlutoChatter
        else:
            return None
    elif charName == TTLocalizer.Chip or charName == TTLocalizer.PoliceChip:
        if chatterType == ToontownGlobals.APRIL_FOOLS_COSTUMES:
            return TTLocalizer.AFChipChatter
        elif chatterType == ToontownGlobals.HALLOWEEN_COSTUMES:
            return TTLocalizer.HalloweenChipChatter
        elif chatterType == ToontownGlobals.SPOOKY_COSTUMES:
            return TTLocalizer.HalloweenChipChatter
        elif chatterType == ToontownGlobals.WINTER_DECORATIONS or chatterType == ToontownGlobals.WINTER_CAROLING or chatterType == ToontownGlobals.WACKY_WINTER_DECORATIONS or chatterType == ToontownGlobals.WACKY_WINTER_CAROLING:
            return TTLocalizer.WinterChipChatter
        elif chatterType == ToontownGlobals.VALENTINES_DAY:
            return TTLocalizer.ValentinesChipChatter
        elif chatterType == ToontownGlobals.SILLY_CHATTER_ONE:
            SillyChipChatter = getExtendedChat(ChipChatter, TTLocalizer.SillyPhase1Chatter)
            return SillyChipChatter
        elif chatterType == ToontownGlobals.SILLY_CHATTER_TWO:
            SillyChipChatter = getExtendedChat(ChipChatter, TTLocalizer.SillyPhase2Chatter)
            return SillyChipChatter
        elif chatterType == ToontownGlobals.SILLY_CHATTER_THREE:
            SillyChipChatter = getExtendedChat(ChipChatter, TTLocalizer.SillyPhase3Chatter)
            return SillyChipChatter
        elif chatterType == ToontownGlobals.SILLY_CHATTER_FOUR:
            SillyChipChatter = getExtendedChat(ChipChatter, TTLocalizer.SillyPhase4Chatter)
            return SillyChipChatter
        else:
            return ChipChatter
    elif charName == TTLocalizer.Dale or TTLocalizer.JailbirdDale:
        if chatterType == ToontownGlobals.APRIL_FOOLS_COSTUMES:
            return TTLocalizer.AFDaleChatter
        elif chatterType == ToontownGlobals.HALLOWEEN_COSTUMES:
            return TTLocalizer.HalloweenDaleChatter
        elif chatterType == ToontownGlobals.SPOOKY_COSTUMES:
            return TTLocalizer.HalloweenDaleChatter
        elif chatterType == ToontownGlobals.WINTER_DECORATIONS or chatterType == ToontownGlobals.WINTER_CAROLING or chatterType == ToontownGlobals.WACKY_WINTER_DECORATIONS or chatterType == ToontownGlobals.WACKY_WINTER_CAROLING:
            return TTLocalizer.WinterDaleChatter
        elif chatterType == ToontownGlobals.VALENTINES_DAY:
            return TTLocalizer.ValentinesDaleChatter
        elif chatterType == ToontownGlobals.SILLY_CHATTER_ONE:
            SillyDaleChatter = getExtendedChat(DaleChatter, TTLocalizer.SillyPhase1Chatter)
            return SillyDaleChatter
        elif chatterType == ToontownGlobals.SILLY_CHATTER_TWO:
            SillyDaleChatter = getExtendedChat(DaleChatter, TTLocalizer.SillyPhase2Chatter)
            return SillyDaleChatter
        elif chatterType == ToontownGlobals.SILLY_CHATTER_THREE:
            SillyDaleChatter = getExtendedChat(DaleChatter, TTLocalizer.SillyPhase3Chatter)
            return SillyDaleChatter
        elif chatterType == ToontownGlobals.SILLY_CHATTER_FOUR:
            SillyDaleChatter = getExtendedChat(DaleChatter, TTLocalizer.SillyPhase4Chatter)
            return SillyDaleChatter
        else:
            return DaleChatter
    return None
