import traceback
import types
import collections
from typing import List, Dict

from direct.interval.IntervalGlobal import *

from libotp import NametagGroup

from otp.otpbase import OTPLocalizer
from otp.otpbase import OTPGlobals

from toontown.battle import SuitBattleGlobals
from toontown.coghq import CogDisguiseGlobals
try:
    from toontown.coghq import CraneLeagueGlobals
    from toontown.coghq.ActivityLog import ActivityLog
    from toontown.coghq.CraneLeagueHeatDisplay import CraneLeagueHeatDisplay
except Exception:
    CraneLeagueGlobals = None
    ActivityLog = None
    CraneLeagueHeatDisplay = None
from toontown.estate import GardenGlobals
from toontown.fishing import FishGlobals
from toontown.golf import GolfGlobals
from toontown.quest import Quests
from toontown.racing.KartDNA import *
from toontown.racing import RaceGlobals
from toontown.shtiker import CogPageGlobals
from toontown.toon import NPCToons
from toontown.suit import SuitDNA
from toontown.toon import Experience
from toontown.toon import ToonDNA
from toontown.toonbase import ToontownBattleGlobals
from toontown.toonbase import ToontownGlobals
from toontown.toonbase import TTLocalizer
from toontown.hood import ZoneUtil

from . import MagicWordConfig
import time
import random
import json

DEBUG_SCOREBOARD = None
DEBUG_HEAT = None
DEBUG_LOG = None

magicWordIndex = collections.OrderedDict()


def getMagicWord(name):
    magicWord = globals().get(name)
    if not magicWord:
        magicWord = MagicWord()
    return magicWord


class MagicWord:
    # Whether this Magic word should be considered "hidden". This impacts if it is shown on the Magic Word page.
    hidden = False

    # Whether this Magic Word is an administrative command or not.
    # Administrative commands will be allowed on "Legit" servers.
    # Only these commands can be used on caged Toons.
    administrative = False

    # List of names that will also invoke this word - a setHP magic word might have "hp", for example.
    # A Magic Word will always be callable with its class name, so you don't have to put that in the aliases.
    aliases = None

    # Description of the Magic Word for use in the Shtikerbook.
    desc = "A simple Magic Word."

    # Default example with for commands with no arguments set.
    example = ""

    # The minimum access level required to use this Magic Word. By default, USER.
    accessLevel = 'USER'

    # This word has priority to be shown at the top of the spellbook page
    priority = False

    # A restriction on the Magic Word which sets what kind or set of Distributed Objects it can be used on. By default, AFFECT_EVERYONE.
    affectRange = [MagicWordConfig.AFFECT_SINGLE, MagicWordConfig.AFFECT_OTHER, MagicWordConfig.AFFECT_BOTH]

    # Where the magic word will be executed -- EXEC_LOC_CLIENT or EXEC_LOC_SERVER.
    execLocation = MagicWordConfig.EXEC_LOC_INVALID

    # List of all arguments for this word, with the format [(type, isRequired), (type, isRequired)...]
    # If the parameter is not required, you must provide a default argument: (type, False, default).
    arguments = None

    def __init__(self, air=None, cr=None, invokerId=None, targets=None, args=None):
        self.air = air
        self.cr = cr
        self.invokerId = invokerId
        self.targets = targets
        self.args = args
        self.posHprString = None
        if self.__class__.__name__ != "MagicWord":  # If not the base class,
            self.aliases = self.aliases if self.aliases is not None else []  # if we use [] by default, it might get overwritten
            self.aliases.insert(0, self.__class__.__name__)  # add the class name to the alias list,
            self.aliases = [x.lower() for x in self.aliases]  # make all the aliases lowercase,
            self.arguments = self.arguments if self.arguments is not None else []

            if len(self.arguments) > 0:
                for arg in self.arguments:
                    argInfo = ""
                    if not arg[MagicWordConfig.ARGUMENT_REQUIRED]:
                        argInfo += "(DF:{0})".format(arg[MagicWordConfig.ARGUMENT_DEFAULT])
                    self.example += "[{0}{1}] ".format(arg[MagicWordConfig.ARGUMENT_NAME], argInfo)

            self.__register()  # and register the magic word.

    def __register(self):
        for wordName in self.aliases:
            magicWordIndex[wordName] = {
                'classname': self.__class__.__name__,  # This class
                'hidden': self.hidden,
                'administrative': self.administrative,
                'aliases': self.aliases,
                'desc': self.desc,
                'example': self.example,
                'execLocation': self.execLocation,
                'access': self.accessLevel,
                'priority': self.priority,
                'affectRange': self.affectRange,
                'args': self.arguments
            }

    def executeWord(self):
        executedWord = None
        for avId in self.targets:
            invoker = None
            toon = None
            if self.air:
                invoker = self.air.doId2do.get(self.invokerId)
                toon = self.air.doId2do.get(avId)
            elif self.cr:
                invoker = self.cr.doId2do.get(self.invokerId)
                toon = self.cr.doId2do.get(avId)
            if not self.validateTarget(toon):
                if hasattr(toon, "getName"):
                    return "{} is not a valid target!".format(toon.getName())
                else:
                    return "{} is not a valid target!".format(avId)

            if self.execLocation == MagicWordConfig.EXEC_LOC_CLIENT:
                self.args = json.loads(self.args)

            # Attempt to run the command, if we fail then tell the user why.
            try:
                executedWord = self.handleWord(invoker, avId, toon, *self.args)
            except Exception as e:
                traceback.print_exc()
                toCheck = 'AI logs' if self.execLocation == MagicWordConfig.EXEC_LOC_SERVER else 'logs'
                return f"An exception was caught when trying to invoke {self.__class__.__name__}: {e}\n\nCheck {toCheck} for a traceback."

        if executedWord:
            return executedWord

    def validateTarget(self, target):
        if self.air:
            from toontown.toon.DistributedToonAI import DistributedToonAI
            return isinstance(target, DistributedToonAI)
        elif self.cr:
            from toontown.toon.DistributedToon import DistributedToon
            return isinstance(target, DistributedToon)
        return False

    def handleWord(self, invoker, avId, toon, *args):
        raise NotImplemented("Please implement the handleWord method!")


# When creating new Magic Words, please try to use a consistent naming etiquette. Here are some rules we should follow:

# Restock - If a word gives you an item that you can consistently obtain and use (for example, a cog summon), but you cannot specify the amount you recieve, we give this command the prefix of "Restock"
# Unlock - If a word gives you an item that you can only ever obtain once (for example, pet trick phrases or emotes), we give this command the prefix of "Unlock"
# Set - If a word gives you an item that you can consistently obtain and use, or if it is a value on your toon (for example, a pinkslip, unite, or laff point value), and you can specify the amount you recieve, we give this command the prefix of "Set"
# Transform - If a word transforms you into something, we give this command the prefix of "Transform"
# Toggle - If a word toggles something on or off, we give this command the prefix of "Toggle"


# Start Magic Words that were present in the source when forked from TTOff
class SetHP(MagicWord):
    aliases = ["hp", "setlaff", "laff"]
    desc = "Sets the target's current laff."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("hp", int, True)]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        hp = args[0]

        if not -1 <= hp <= toon.getMaxHp():
            return "Can't set {0}'s laff to {1}! Specify a value between -1 and {0}'s max laff ({2}).".format(
                toon.getName(), hp, toon.getMaxHp())

        if toon.getHp() > 0 >= hp:
            toon.setDeathReason(DeathReason.SPELLBOOK)

        toon.b_setHp(hp)
        return "{}'s laff has been set to {}.".format(toon.getName(), hp)


class SetMaxHP(MagicWord):
    aliases = ["maxhp", "setmaxlaff", "maxlaff"]
    desc = "Sets the target's max laff."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("maxhp", int, True)]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        maxhp = args[0]

        if not 1 <= maxhp <= ToontownGlobals.MaxHpLimit:
            return "Can't set {}'s max laff to {}! Specify a value between 1 and {}.".format(toon.getName(), maxhp,
                                                                                              ToontownGlobals.MaxHpLimit)

        toon.b_setMaxHp(maxhp)
        toon.toonUp(maxhp)
        return "{}'s max laff has been set to {}.".format(toon.getName(), maxhp)


class StartHoliday(MagicWord):
    aliases = ["startH"]
    desc = "Starts a specified holiday ID."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("id", int, True)]
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        id = args[0]
        try:
            self.air.holidayManager.startHoliday(id)
            return "Started holiday %d" % id
        except:
            return "Invalid holiday ID: %d" % id


class Shout(MagicWord):
    aliases = ["shout", "yell", "s", "scream"]
    desc = "Sends a direct message to every toon on the server."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("shout", str, True)]
    accessLevel = 'NO_ACCESS'
    priority = True

    def handleWord(self, invoker, avId, toon, *args):
        shout = args[0]
        shoutString = f"{toon.getName()} shouts: {shout}"
        try:
            self.air.newsManager.d_setToonShout(shoutString)
            return "Sent your shout!"
        except:
            return "Invalid shout!"


class EndHoliday(MagicWord):
    aliases = ["endH"]
    desc = "Ends a specified holiday ID."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("id", int, True)]
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        id = args[0]
        try:
            self.air.holidayManager.endHoliday(id)
            return "Ended holiday %d" % id
        except:
            return "Invalid holiday ID: %d" % id


class ToggleOobe(MagicWord):
    aliases = ["oobe"]
    desc = "Toggles the out of body experience mode, which lets you move the camera freely."
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT
    accessLevel = 'NO_ACCESS'

    def handleWord(self, invoker, avId, toon, *args):
        base.oobe()
        return "Oobe mode has been toggled."


class ToggleRun(MagicWord):
    aliases = ["run"]
    desc = "Toggles run mode, which gives you a faster running speed."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'NO_ACCESS'
    priority = True

    def handleWord(self, invoker, avId, toon, *args):
        toon.d_setRun()
        return "Run mode has been toggled."


class SetSpeed(MagicWord):
    aliases = ["speed"]
    desc = "Sets your running speed."
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT
    arguments = [("speed", float, False, OTPGlobals.ToonForwardSpeed)]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        speed = args[0]

        if not 1.0 <= speed <= 1000.0:
            return "Can't set speed to {}! Specify a value between 1 and 1000.".format(toon.getName())

        if speed == OTPGlobals.ToonForwardSpeed:
            base.localAvatar.currentSpeed = OTPGlobals.ToonForwardSpeed
            base.localAvatar.currentReverseSpeed = OTPGlobals.ToonReverseSpeed
            base.localAvatar.controlManager.setSpeeds(OTPGlobals.ToonForwardSpeed, OTPGlobals.ToonJumpForce,
                                                      OTPGlobals.ToonReverseSpeed, OTPGlobals.ToonRotateSpeed)
            return "Your speed has been set to the default ({}).".format(OTPGlobals.ToonForwardSpeed)
        else:
            reverseSpeed = speed / 3
            base.localAvatar.currentSpeed = speed
            base.localAvatar.currentReverseSpeed = reverseSpeed
            base.localAvatar.controlManager.setSpeeds(speed, OTPGlobals.ToonJumpForce, reverseSpeed,
                                                      OTPGlobals.ToonRotateSpeed)
            return "Your speed has been set to {}.".format(speed)


class MaxToon(MagicWord):
    aliases = ["max"]
    desc = "Maxes out the target's stats. You can provide a gag track to exclude from the target's unlocked tracks."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("missingTrack", str, False, '')]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        missingTrack = args[0]

        gagTracks = [8, 8, 8, 8, 8, 8, 8]  # 8s to allow gag exp overflow
        if missingTrack != '':
            try:
                index = ('toonup', 'trap', 'lure', 'sound', 'throw',
                         'squirt', 'drop').index(missingTrack)
            except:
                return 'Missing Gag track is invalid!'
            gagTracks[index] = 0
        toon.b_setTrackAccess(gagTracks)
        toon.b_setMaxCarry(ToontownGlobals.MaxCarryLimit)

        experience = Experience.Experience(toon.getExperience(), toon)
        for i, track in enumerate(toon.getTrackAccess()):
            if track:
                experience.experience[i] = ToontownBattleGlobals.MaxSkill
        toon.b_setExperience(experience.getCurrentExperience())

        toon.inventory.maxInventory(clearFirst=True)
        toon.b_setInventory(toon.inventory.makeNetString())

        toon.b_setBaseGagSkillMultiplier(50)

        toon.b_setMaxMoney(30000)
        toon.b_setMoney(toon.getMaxMoney())
        toon.b_setBankMoney(ToontownGlobals.DefaultMaxBankMoney)

        toon.b_setMaxHp(ToontownGlobals.MaxHpLimit)
        toon.toonUp(ToontownGlobals.MaxHpLimit)

        toon.b_setHoodsVisited(ToontownGlobals.Hoods)
        toon.b_setTeleportAccess(ToontownGlobals.HoodsForTeleportAll)

        toon.b_setCogParts([
            CogDisguiseGlobals.PartsPerSuitBitmasks[0],
            CogDisguiseGlobals.PartsPerSuitBitmasks[1],
            CogDisguiseGlobals.PartsPerSuitBitmasks[2],
            CogDisguiseGlobals.PartsPerSuitBitmasks[3],
        ])
        toon.b_setCogLevels([ToontownGlobals.MaxCogSuitLevel] * 4)
        toon.b_setCogTypes([7] * 4)

        toon.b_setCogCount([CogPageGlobals.get_max_cog_quota(toon)] * 8 * 4)
        cogStatus = [CogPageGlobals.COG_COMPLETE2] * SuitDNA.suitsPerDept
        toon.b_setCogStatus(cogStatus * 4)
        toon.b_setCogRadar([1] * 4)
        toon.b_setBuildingRadar([1] * 4)

        for id in toon.getQuests():
            toon.removeQuest(id)
        toon.b_setQuestCarryLimit(ToontownGlobals.MaxQuestCarryLimit)
        toon.b_setRewardHistory(Quests.LOOPING_FINAL_TIER, toon.getRewardHistory()[1])

        allFish = TTLocalizer.FishSpeciesNames
        fishLists = [[], [], []]
        for genus in list(allFish.keys()):
            for species in range(len(allFish[genus])):
                fishLists[0].append(genus)
                fishLists[1].append(species)
                fishLists[2].append(FishGlobals.getRandomWeight(genus, species))
        toon.b_setFishCollection(*fishLists)
        toon.b_setFishingRod(FishGlobals.MaxRodId)
        toon.b_setFishingTrophies(list(FishGlobals.TrophyDict.keys()))

        if not toon.hasKart() and simbase.wantKarts:
            toon.b_setKartBodyType(list(KartDict.keys())[1])
        toon.b_setTickets(RaceGlobals.MaxTickets)
        maxTrophies = RaceGlobals.NumTrophies + RaceGlobals.NumCups
        toon.b_setKartingTrophies(list(range(1, maxTrophies + 1)))
        toon.b_setTickets(99999)

        toon.b_setGolfHistory([600] * (GolfGlobals.MaxHistoryIndex * 2))

        toon.b_setAccessKeys([_ for _ in range(100)])

        return "Maxed out {}'s stats.".format(toon.getName())


class UnlockEmotes(MagicWord):
    aliases = ["emotes"]
    desc = "Unlock all of the target's emotes."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'NO_ACCESS'

    def handleWord(self, invoker, avId, toon, *args):
        emoteAccess = list(toon.getEmoteAccess())

        # Old version of command made emote access list shorter. Let's fix that.
        if len(emoteAccess) < len(OTPLocalizer.EmoteFuncDict):
            emoteAccess = [0] * len(OTPLocalizer.EmoteFuncDict)

        for emoteId in list(OTPLocalizer.EmoteFuncDict.values()):
            if emoteId > 25 or emoteId in [17, 18, 19]:
                continue
            emoteAccess[emoteId] = 1

        toon.b_setEmoteAccess(emoteAccess)
        return "Unlocked all of {}'s emotes.".format(toon.getName())


class SetBeans(MagicWord):
    aliases = ["beans", "setjellybeans", "jellybeans", "setmoney", "money"]
    desc = "Sets the target's jellybean count."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("beans", int, True)]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        beans = args[0]

        if not 0 <= beans <= toon.getMaxMoney():
            return ("Can't set {0}'s jellybean count to {1}! Specify a value between 0 and {0}'s jellybean jar size ({"
                    "2}).").format(toon.getName(), beans, toon.getMaxMoney())

        toon.b_setMoney(beans)
        return "{}'s jellybean count has been set to {}.".format(toon.getName(), beans)


class SetMaxBeans(MagicWord):
    aliases = ["maxbeans", "setmaxjellybeans", "maxjellybeans", "setmaxmoney", "maxMoney"]
    desc = "Sets the target's jellybean jar size."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("maxBeans", int, True)]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        maxBeans = args[0]

        if not 0 <= maxBeans <= 9999:
            return "Can't set {}'s jellybean jar size to {}! Specify a value between 0 and 9999.".format(toon.getName(),
                                                                                                         maxBeans)

        toon.b_setMaxMoney(maxBeans)
        return "{}'s jellybean jar size has been set to {}.".format(toon.getName(), maxBeans)


########################################################################################################################
class SetEmblems(MagicWord):
    aliases = ["emblems"]
    desc = "Gives the target a specified amount of silver and gold emblems, respectively."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("silver", int, True), ("gold", int, True)]
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        emblems = (args[0], args[1])
        toon.addEmblems(emblems)
        return "Gave {} {} silver and {} gold emblems!".format(toon.getName(), *emblems)


class ToggleImmortal(MagicWord):
    aliases = ["immortal"]
    desc = "Makes the target immortal."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        toon.b_setImmortalMode(not toon.getImmortalMode())
        return "{} is {} immortal!".format(toon.getName(), "now" if toon.getImmortalMode() else "no longer")


class ToggleUnlimitedGags(MagicWord):
    aliases = ["unlimitedgags"]
    desc = "Toggles unlimited gags for the target."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):

        from toontown.toon.InventoryBase import InventoryBase

        inventory: InventoryBase = toon.inventory
        inventory.maxInventory(mode=InventoryBase.FillMode.ALL, clearFirst=True)

        invoker.b_setInventory(inventory.makeNetString())
        toon.b_setUnlimitedGags(not toon.getUnlimitedGags())

        return "{} {} has unlimited gags!".format(toon.getName(), "now" if toon.getUnlimitedGags() else "no longer")


class ToggleInstaKill(MagicWord):
    aliases = ["instakill"]
    desc = "Lets the target instantly kill Cogs with any amount of damage."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        toon.b_setInstaKill(not toon.getInstaKill())
        return "{} can {} insta-kill Cogs!".format(toon.getName(), "now" if toon.getInstaKill() else "no longer")
    

class SetDamageMultiplier(MagicWord):
    aliases = ["damagemult", "mult", "dm"]
    desc = "Sets the target's damage mult to the given %."
    arguments = [("damageMult", int, True)]
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        mult = args[0]
        if mult < 1 or mult > 500:
            return "Your damage mult must be within the range 1-500!"
        if invoker != toon:
            return "You can only set your own damage mult!"
        toon.b_setDamageMultiplier(mult)
        return "{}'s damage mult is now at {}%!".format(toon.getName(), str(mult))


class SetOverflowMultiplier(MagicWord):
    aliases = ["overflow", "setoverflow", "om"]
    desc = "Sets the target's overflow rate to the given %."
    arguments = [("overflowMult", int, True)]
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        mult = args[0]
        if mult < 1 or mult > 300:
            return "Your overflow rate must be within the range 1-300!"
        if invoker != toon:
            return "You can only set your own overflow rate!"
        toon.b_setOverflowMod(mult)
        return "{}'s overflow rate is now at {}%!".format(toon.getName(), str(mult))


class SkipMovie(MagicWord):
    desc = "Skips the current round of animations in a Cog battle."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        battleId = toon.getBattleId()
        if not battleId:
            return "You cannot skip a movie if you are not currently in battle!"
        battle = self.air.doId2do.get(battleId)
        if not battle:
            return "{} is not a valid battle!".format(battleId)
        battle._DistributedBattleBaseAI__movieDone()
        return "Successfully skipped Battle movie!"


class ToggleGod(MagicWord):
    aliases = ["god", 'godmode']
    desc = "Makes the target fast, immortal, all-powerful, and omnipotent."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        isGod = not toon.getImmortalMode()
        toon.d_setRun()
        toon.b_setImmortalMode(isGod)
        toon.b_setUnlimitedGags(isGod)
        toon.b_setInstaKill(isGod)
        return "God mode {} for {}!".format("enabled" if isGod else "disabled", toon.getName())


class ToggleCollisionsOff(MagicWord):
    aliases = ['collisionsoff', 'noclip']
    desc = "Disables collisions for the target."
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        return "This command is not supported. If you need to noclip, please use ~ghost."


class GetPos(MagicWord):
    desc = "Get the current position of your toon."
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        if not base.localAvatar:
            return "Your Toon does not exist!"
        return str(base.localAvatar.getPos())


class SetPos(MagicWord):
    desc = "Set the current position of your Toon."
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT
    arguments = [("x", float, True), ("y", float, True), ("z", float, True)]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        toonX = args[0]
        toonY = args[1]
        toonZ = args[2]
        if not base.localAvatar:
            return "Your Toon does not exist!"
        for arg in args:
            if not -2500 <= arg <= 2500:
                return "This position is too far out!"
        base.localAvatar.setPos(toonX, toonY, toonZ)


class GetHpr(MagicWord):
    desc = "Returns the rotation value of your Toon."
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        if not base.localAvatar:
            return "No Toon found!"
        return str(base.localAvatar.getHpr())


class SetHpr(MagicWord):
    desc = "Set the rotation value of your Toon."
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT
    arguments = [("h", int, True), ("p", int, True), ("r", int, True), ("part", str, False, '')]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        toonH = args[0]

        if not base.localAvatar:
            return "No Toon found!"

        part = args[3].lower()

        if part in ('head', 'torso', 'legs'):
            for lod in toon.getLODNames():
                base.localAvatar.getPart(part, lod).setH(toonH)

        base.localAvatar.setHpr(args[0], args[1], args[2])


class PrintPosHpr(MagicWord):
    aliases = ['pph']
    desc = "Print Pos Hpr"
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        count = 0

        def printPosHpr(count):
            count += 1
            if count <= 100:
                print(("%s %s" % (toon.getPos(), toon.getHpr())))
                taskMgr.doMethodLater(0.1, printPosHpr, "print the damn points", extraArgs=[count])
            else:
                return

        printPosHpr(0)


class Camera(MagicWord):
    aliases = ['cam']
    desc = "Set a movie sequence"
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT
    arguments = [("command", str, True), ("x", float, False, 0), ("y", float, False, 0), ("z", float, False, 0),
                 ("h", float, False, 0), ("p", float, False, 0), ("r", float, False, 0), ("duration", float, False, 1)]
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        command = args[0]
        x = args[1]
        y = args[2]
        z = args[3]
        h = args[4]
        p = args[5]
        r = args[6]
        duration = args[7]
        valid_commands = ['startpoint', 'addpoint', 'clear', 'play', 'list', 'ease']
        if command not in valid_commands:
            return "Invalid command! Please use ~camera startpoint or ~camera addpoint."
        if command == 'startpoint':
            if None in [x, y, z, h, p, r]:
                return "The command syntax is [~camera startpoint x y z h p r]!"
            base.localAvatar.camStart = [x, y, z, h, p, r]
            return "%d %d %d %d %d %d is set as the starting point!" % (x, y, z, h, p, r)
        elif command == 'addpoint':
            if None in [x, y, z, h, p, r]:
                return "The command syntax is [~camera addpoint x y z h p r duration]!"
            base.localAvatar.camPoints.append([x, y, z, h, p, r, duration])
            return "Point %d %d %d %d %d %d with a duration of %d was added!" % (x, y, z, h, p, r, duration)
        elif command == 'clear':
            base.localAvatar.camPoints = []
            return "Successfully cleared all camera points!"
        elif command == 'play':
            start = base.localAvatar.camStart
            camera = base.camera
            track = Sequence()
            track.append(Func(base.localAvatar.stopUpdateSmartCamera))
            track.append(Func(camera.wrtReparentTo, render))
            track.append(Func(camera.setPosHpr, start[0], start[1], start[2], start[3], start[4], start[5]))
            for point in base.localAvatar.camPoints:
                track.append(camera.posHprInterval(point[6], Point3(point[0], point[1], point[2]),
                                                   Point3(point[3], point[4], point[5])))
            track.append(Func(camera.wrtReparentTo, base.localAvatar))
            track.append(Func(base.localAvatar.startUpdateSmartCamera))
            track.start()
        elif command == 'ease':
            start = base.localAvatar.camStart
            camera = base.camera
            track = Sequence()
            track.append(Func(base.localAvatar.stopUpdateSmartCamera))
            track.append(Func(camera.wrtReparentTo, render))
            track.append(Func(camera.setPosHpr, start[0], start[1], start[2], start[3], start[4], start[5]))
            for point in base.localAvatar.camPoints:
                track.append(camera.posHprInterval(point[6], Point3(point[0], point[1], point[2]),
                                                   Point3(point[3], point[4], point[5]), blendType='easeInOut'))
            track.append(Func(camera.wrtReparentTo, base.localAvatar))
            track.append(Func(base.localAvatar.startUpdateSmartCamera))
            track.start()
        elif command == 'list':
            start = base.localAvatar.camStart
            points = "[x%d, y%d, z%d, h%d, p%d, r%d]" % (start[0], start[1], start[2], start[3], start[4], start[5])
            for point in base.localAvatar.camPoints:
                points = points + "\n [x%d, y%d, z%d, h%d, p%d, r%d, dur%d]" % (
                    point[0], point[1], point[2], point[3], point[4], point[5], point[6])
            return points


class PrintCamera(MagicWord):
    aliases = ['pc']
    desc = "Prints the coordinates of the current camera position."
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        print(f"current camera pos:          {base.camera}")
        print(f"current local av camera pos: {base.localAvatar.camera}")
        return "Printed your current camera positions in your logs."


class ToggleCollisionsOn(MagicWord):
    aliases = ['collisionson', 'clip', 'yesclip']
    desc = "Enables collisions for the target."
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        return "This command is not supported. If you need to noclip, please use ~ghost."


class GlobalTP(MagicWord):
    aliases = ["alltp"]
    desc = "Allows you to teleport anywhere."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        hoodsVisited = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000, 12000, 13000]
        toon.b_setHoodsVisited(hoodsVisited)
        toon.b_setTeleportAccess(hoodsVisited)
        return "{} can now teleport anywhere!".format(toon.getName())


class Help(MagicWord):
    administrative = True
    desc = "Tells you to come here for more info... but you're already here!"
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT
    accessLevel = 'NO_ACCESS'

    def handleWord(self, invoker, avId, toon, *args):
        try:
            # make sure this is running on client
            settings = base.settings
        except NameError:
            # someone made this a server MW, so default to '~'
            mw_prefix = MagicWordConfig.PREFIX_ALLOWED[0]
        else:
            # we're actually client; get the actual prefix, or '~' if invalid
            idx = settings.get('magic-word-activator')
            idx = idx if 0 <= idx < len(MagicWordConfig.PREFIX_ALLOWED) else 0
            mw_prefix = MagicWordConfig.PREFIX_ALLOWED[idx]
        return "Refer to your Shticker Book for a list of all commands! Some may require a higher access level. Clicking a Toon's nametag and then using 2 '{}' characters will run a command on them.".format(
            mw_prefix)


class ToggleSleeping(MagicWord):
    aliases = ["sleep", "sleeping"]
    desc = "Enables or disables sleeping for your current session. This does not affect other Toons."
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT
    accessLevel = 'NO_ACCESS'

    def handleWord(self, invoker, avId, toon, *args):
        if not base.localAvatar.neverSleep:
            base.localAvatar.disableSleeping()
            return "Sleeping has been deactivated for the current session."
        else:
            base.localAvatar.enableSleeping()
            return "Sleeping has been activated for the current session."


class Teleport(MagicWord):
    aliases = ["tp"]
    desc = "Teleports the target to a specified location."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("hood", str, False, '')]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        hood = args[0]

        if not hood:
            toon.d_doTeleport('GUI')
            return "Teleport GUI opened!"

        try:
            request = ToontownGlobals.hood2Id[hood.upper()]
        except:
            return "Invalid location!"

        hoodId = request[0]

        toon.d_doTeleport(hood)
        return "Teleporting {0} to {1}!".format(toon.getName(), ToontownGlobals.hoodNameMap[hoodId][-1])


class SetTrackAccess(MagicWord):
    aliases = ["trackaccess"]
    desc = "Set the tracks a toon has."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("wantTrack", int, True)] * 7
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        # args = toonup, trap, lure, sound, throw, squirt, drop
        tracks = ['toonup', 'trap', 'lure', 'sound', 'throw', 'squirt', 'drop']
        if len(args) == 7:
            ret = ''
            for track, accessLevel in enumerate(args):
                ret += '\n'
                toon.setTrackAccessLevel(track, accessLevel)
                ret += f"{tracks[track]}: {accessLevel}"

            return f"Set your track access to the following:\n{ret}"
        else:
            return "Invalid amount of arguments! There must be 7..."


class SetTracks(MagicWord):
    aliases = ["tracks"]
    desc = "Grants all the gag tracks, with the option of leaving one out."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("leftOutTrack", str, False, '')]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        leftOutTrack = args[0]

        tracks = [("toonup", 1), ("trap", 1), ("lure", 1), ("sound", 1), ("throw", 1), ("squirt", 1), ("drop", 1)]
        tracks = collections.OrderedDict(tracks)
        if leftOutTrack in list(tracks.keys()):
            tracks[leftOutTrack] = 0

        toon.b_setTrackAccess(list(tracks.values()))
        if leftOutTrack:
            msg = "Set your gag tracks, %sless Toon!" % (leftOutTrack)
        else:
            msg = "Set your gag tracks, Toon!"

        return msg


class Catalog(MagicWord):
    desc = "Gives the toon a new catalog."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        simbase.air.catalogManager.deliverCatalogFor(toon)


class GetAccId(MagicWord):
    administrative = True
    aliases = ["accId", "accountId"]
    desc = "Get the accountId from the target player."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        accountId = toon.DISLid
        return "%s has the accountId of %d" % (toon.getName(), accountId)


class GetAvId(MagicWord):
    administrative = True
    aliases = ["avId", "avatarId"]
    desc = "Get the avId from the target player."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        return "%s has the avId of %d" % (toon.getName(), toon.getDoId())


class SetGravity(MagicWord):
    aliases = ["gravity"]
    desc = "Set your gravity value."
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT
    arguments = [("gravity", float, False, ToontownGlobals.GravityValue * 2.0), ("override", bool, False, False)]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        gravityValue = args[0]
        overrideWarning = args[1]

        if not base.localAvatar:
            return "Your Toon does not exist!"

        if gravityValue < 1 and not overrideWarning:
            return "A value lower than 1 may crash your client."

        base.localAvatar.controlManager.currentControls.setGravity(gravityValue)
        if gravityValue == ToontownGlobals.GravityValue * 2.0:
            return "Gravity returned to normal."
        elif gravityValue == ToontownGlobals.GravityValue * 0.75:
            return "April fools gravity enabled!"


class TrueFriend(MagicWord):
    aliases = ["tf"]
    desc = "Automatically add a Toon as a true friend."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("avIdShort", int, True)]
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        avIdShort = args[0]
        avIdFull = 400000000 - (300000000 - avIdShort)
        av = simbase.air.doId2do.get(avIdFull)
        if not av:
            return "avId not found/online!"
        if int(str(avIdFull)[:2]) >= 40:  # AI
            return "%s is an NPC!" % av.getName()
        if invoker == av:
            return "Cannot true friend yourself!"

        invoker.extendFriendsList(av.getDoId(), 1)
        av.extendFriendsList(invoker.getDoId(), 1)

        invoker.d_setFriendsList(invoker.getFriendsList())
        av.d_setFriendsList(av.getFriendsList())


class ToggleOobeCull(MagicWord):
    aliases = ["oobecull"]
    desc = "Toggle 'out of body experience' view, with culling debugging."
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        base.oobeCull()


class ToggleWire(MagicWord):
    aliases = ["wire", "wireframe"]
    desc = "Toggle wireframe view."
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        base.toggleWireframe()


class ToggleTextures(MagicWord):
    aliases = ["textures"]
    desc = "Toggle textures."
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        base.toggleTexture()


class ToggleFPS(MagicWord):
    aliases = ["fps", "showfps"]
    desc = "Toggle frame rate meter."
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT
    accessLevel = 'NO_ACCESS'

    def handleWord(self, invoker, avId, toon, *args):
        base.setFrameRateMeter(not base.frameRateMeter)


class GetAccess(MagicWord):
    desc = "Get the access level of a target."
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        return "Access level: " + str(toon.getAccessLevel())


class Aspect2D(MagicWord):
    aliases = ["a2d"]
    desc = "Toggles Aspect2d."
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        if aspect2d.isHidden():
            aspect2d.show()
        else:
            aspect2d.hide()


class InvasionStatus(MagicWord):
    desc = "Returns the number of cogs remaining in an invasion."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        invasionMgr = simbase.air.suitInvasionManager

        if not invasionMgr.getInvading():
            return "There is no invasion in progress!"

        invadingCog = invasionMgr.getInvadingCog()
        simbase.air.newsManager.sendUpdateToAvatarId(invoker.getDoId(), 'setInvasionStatus', [
            ToontownGlobals.SuitInvasionUpdate, invadingCog[0], invasionMgr.numSuits, invadingCog[1]])


class RevealMap(MagicWord):
    desc = "Reveals map in the Sellbot Field Office maze game."
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        mazeGame = None
        from toontown.cogdominium.DistCogdoMazeGame import DistCogdoMazeGame
        for do in list(base.cr.doId2do.values()):
            if isinstance(do, DistCogdoMazeGame):
                if invoker.doId in do.getToonIds():
                    mazeGame = do
                    break

        if mazeGame:
            mazeGame.game.guiMgr.mazeMapGui.showExit()
            mazeGame.game.guiMgr.mazeMapGui.revealAll()
            return "Map revealed!"

        return "You are not in a Maze Game!"


class EndMaze(MagicWord):
    desc = "Ends the maze game in a Sellbot Field Office."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        mazeGame = None
        from toontown.cogdominium.DistCogdoMazeGameAI import DistCogdoMazeGameAI
        for do in list(simbase.air.doId2do.values()):
            if isinstance(do, DistCogdoMazeGameAI):
                if invoker.doId in do.getToonIds():
                    mazeGame = do
                    break

        if mazeGame:
            mazeGame.openDoor()
            return "Completed Maze Game"

        return "You are not in a Maze Game!"


class SpawnBuilding(MagicWord):
    aliases = ["building", "spawnbldg", "bldg"]
    desc = "Spawns a Cog Building with the given suit index."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("department", str, True), ("floorCount", int, True)]
    accessLevel = 'NO_ACCESS'
    priority = True

    def handleWord(self, invoker, avId, toon, *args):
        suitDeptToCode = {
            'boss': 'c',
            'bossbot': 'c',
            'law': 'l',
            'lawbot': 'l',
            'cash': 'm',
            'cashbot': 'm',
            'sell': 's',
            'sellbot': 's',
        }
        department = args[0]
        floors = args[1]

        if department in suitDeptToCode:
            departmentCode = suitDeptToCode[department]
        else:
            return "Couldn't spawn a building with department {0}.".format(department)

        if floors not in range(1, 6):
            return "Building floor count must be a number from 1 to 5."

        returnCode = invoker.doBuildingTakeover(None, departmentCode, floors)
        if returnCode[0] == 'success':
            return "Successfully spawned a {0} building with '{1}' floor(s)!".format(department, floors)
        return "Couldn't spawn a {0} building with '{1}' floor(s)!".format(department, floors)


class SpawnFO(MagicWord):
    aliases = ["fo", "spawncogdo", "cogdo"]
    desc = "Spawns a Field Office with the given type and difficulty."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("type", str, True), ("difficulty", int, False, 0)]
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        from toontown.building import SuitBuildingGlobals
        track = args[0]
        difficulty = args[1]

        tracks = ['s', 'l']
        if track not in tracks:
            return "Invalid Field Office type! Supported types are 's' and 'l'"
        if not 0 <= difficulty < len(SuitBuildingGlobals.SuitBuildingInfo):
            return "Difficulty out of bounds!"

        try:
            building = invoker.findClosestDoor()
        except KeyError:
            return "You\'re not on a street!"
        if building is None:
            return "Unable to spawn a %s Field Office with a difficulty of %d." % (
                ToontownGlobals.Dept2Dept.get(track), difficulty)

        building.cogdoTakeOver(track, difficulty, 2)
        return "Successfully spawned a %s Field Office with a difficulty of %d!" % (
            ToontownGlobals.Dept2Dept.get(track), difficulty)


class SetCEIndex(MagicWord):
    aliases = ["setce", "ce", "cheesyeffect"]
    desc = "Set Cheesy Effect of the target."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("index", int, True), ("zoneId", int, False, 0), ("duration", int, False, 0)]
    accessLevel = 'NO_ACCESS'

    def handleWord(self, invoker, avId, toon, *args):
        """Set Cheesy Effect of the target."""
        index = args[0]
        zoneId = args[1]
        duration = args[2]

        if not 0 <= index <= 17:
            return "Invalid value %s specified for Cheesy Effect." % index
        if index == 17 and (not hasattr(self.air, 'holidayManager') or not self.air.holidayManager.isHolidayRunning(
                ToontownGlobals.APRIL_FOOLS)):
            return "Invalid value %s specified for Cheesy Effect." % index
        if zoneId != 0 and not 100 < zoneId < ToontownGlobals.DynamicZonesBegin:
            return "Invalid zoneId specified."
        toon.b_setCheesyEffect(index, zoneId, time.time() + duration)


class SetFishingRod(MagicWord):
    aliases = ["rod", "setrod"]
    desc = "Set target's fishing rod value."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("rodVal", int, True)]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        rodVal = args[0]
        if not 0 <= rodVal <= 4:
            return "Rod value must be between 0 and 4."
        toon.b_setFishingRod(rodVal)
        return "Rod changed to " + str(rodVal)


class SetFishingBucket(MagicWord):
    aliases = ["fishbucket", "bucket", "maxtank"]
    desc = "Set target's max fish tank value."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("tankVal", int, True)]
    accessLevel = 'USER'
    def handleWord(self, invoker, avId, toon, *args):
        tankVal = args[0]
        if not 20 <= tankVal <= 99:
            return "Max fish tank value must be between 20 and 99"
        toon.b_setMaxFishTank(tankVal)
        return "Max size of fish tank changed to " + str(tankVal)


class ClearFishCollection(MagicWord):
    aliases = ["clearfishcollection"]
    desc = "Clears target's fish collection."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        toon.b_setFishCollection([], [], [])
        return "Cleared fish collection on target"


class SetPlayRate(MagicWord):
    aliases = ["playrate"]
    desc = "Set target's play rate."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("playRate", float, False, 1.0)]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        rate = args[0]
        toon.d_setAnimPlayRate(rate)
        if rate == 1:
            return "Set playrate to normal!"


class SetName(MagicWord):
    aliases = ["name"]
    desc = "Set target's name."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("name", str, True)]
    accessLevel = 'NO_ACCESS'

    def handleWord(self, invoker, avId, toon, *args):
        nameStr = args[0]
        oldName = toon.getName()

        if not nameStr:
            return "Cannot change %s's name to nothing!" % oldName
        elif ":" in nameStr:
            return "Cannot change %s's name to %s. Invalid characters specified." % (oldName, nameStr)

        toon.b_setName(nameStr)
        return "Changed %s's name to %s!" % (oldName, nameStr)


class SetColor(MagicWord):
    aliases = ["tooncolor"]
    desc = "Set shirt color of target toon."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("partName", str, True), ("colorId", int, False, 0)]
    accessLevel = 'NO_ACCESS'

    def handleWord(self, invoker, avId, toon, *args):
        dna = ToonDNA.ToonDNA()
        dna.makeFromNetString(toon.getDNAString())
        toonParts = ['all', 'legs', 'arms', 'head']
        toonPart = args[0]
        toonColor = args[1]

        if toonPart not in toonParts:
            return "Invalid toon part specified!"
        if toonColor not in ToonDNA.defaultBoyColorList:
            return "Invalid toon color specified!"
        if toonPart == toonParts[0]:
            dna.headColor = toonColor
            dna.armColor = toonColor
            dna.legColor = toonColor
        elif toonPart == toonParts[1]:
            dna.legColor = toonColor
        elif toonPart == toonParts[2]:
            dna.armColor = toonColor
        elif toonPart == toonParts[3]:
            dna.headColor = toonColor
        toon.b_setDNAString(dna.makeNetString())


class SetTop(MagicWord):
    aliases = ["shirt"]
    desc = "Set shirt of target toon."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("textureId", int, True)]
    accessLevel = 'NO_ACCESS'

    def handleWord(self, invoker, avId, toon, *args):
        dna = ToonDNA.ToonDNA()
        dna.makeFromNetString(toon.getDNAString())

        topTex = args[0]

        if not 0 <= topTex <= len(ToonDNA.Shirts):
            return "Invalid shirt texture specified!"
        dna.topTex = topTex
        toon.b_setDNAString(dna.makeNetString())


class SetTopColor(MagicWord):
    aliases = ["shirtcolor"]
    desc = "Set shirt color of target toon."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("colorId", int, True)]
    accessLevel = 'NO_ACCESS'

    def handleWord(self, invoker, avId, toon, *args):
        dna = ToonDNA.ToonDNA()
        dna.makeFromNetString(toon.getDNAString())

        topTexColor = args[0]

        if not 0 <= topTexColor <= len(ToonDNA.ClothesColors):
            return "Invalid shirt color specified!"
        dna.topTexColor = topTexColor
        toon.b_setDNAString(dna.makeNetString())


class SetSleeves(MagicWord):
    aliases = ["sleeves"]
    desc = "Set sleeves of target toon."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("textureId", int, True)]
    accessLevel = 'NO_ACCESS'

    def handleWord(self, invoker, avId, toon, *args):
        dna = ToonDNA.ToonDNA()
        dna.makeFromNetString(toon.getDNAString())

        sleeveTex = args[0]

        if not 0 <= sleeveTex <= len(ToonDNA.Sleeves):
            return "Invalid sleeves texture specified!"
        dna.sleeveTex = sleeveTex
        toon.b_setDNAString(dna.makeNetString())


class SetSleevesColor(MagicWord):
    aliases = ["sleevescolor"]
    desc = "Set sleeves color of target toon."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("colorId", int, True)]
    accessLevel = 'NO_ACCESS'

    def handleWord(self, invoker, avId, toon, *args):
        dna = ToonDNA.ToonDNA()
        dna.makeFromNetString(toon.getDNAString())

        sleeveTexColor = args[0]

        if not 0 <= sleeveTexColor <= len(ToonDNA.ClothesColors):
            return "Invalid sleeves color specified!"
        dna.sleeveTexColor = sleeveTexColor
        toon.b_setDNAString(dna.makeNetString())


class SetBottoms(MagicWord):
    aliases = ["bottoms"]
    desc = "Set bottoms of target toon."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("textureId", int, True)]
    accessLevel = 'NO_ACCESS'

    def handleWord(self, invoker, avId, toon, *args):
        dna = ToonDNA.ToonDNA()
        dna.makeFromNetString(toon.getDNAString())

        if dna.gender == 'm':
            bottoms = ToonDNA.BoyShorts
        elif dna.gender == 'f':
            bottoms = ToonDNA.GirlBottoms
        else:
            return 'Unknown gender... perhaps you\'re a helicopter?'

        botTex = args[0]

        if not 0 <= botTex <= len(bottoms):
            return "Invalid bottoms texture specified!"
        dna.botTex = botTex
        toon.b_setDNAString(dna.makeNetString())


class SetBottomsColor(MagicWord):
    aliases = ["bottomscolor"]
    desc = "Set bottoms color of target toon."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("colorId", int, True)]
    accessLevel = 'NO_ACCESS'

    def handleWord(self, invoker, avId, toon, *args):
        dna = ToonDNA.ToonDNA()
        dna.makeFromNetString(toon.getDNAString())

        botTexColor = args[0]

        if not 0 <= botTexColor <= len(ToonDNA.ClothesColors):
            return "Invalid bottoms color specified!"
        dna.botTexColor = botTexColor
        toon.b_setDNAString(dna.makeNetString())


class SetHat(MagicWord):
    aliases = ["hat"]
    desc = "Set hat of target toon."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("id", int, True), ("textureId", int, False, 0)]
    accessLevel = 'NO_ACCESS'

    def handleWord(self, invoker, avId, toon, *args):
        hatId = args[0]
        hatTex = args[1]

        if hatId == 58:
            return "Invalid hat specified."
        if not 0 <= hatId <= 60:
            return "Invalid hat specified."
        if not 0 <= hatTex <= 40:
            return "Invalid hat texture specified."
        toon.b_setHat(hatId, hatTex, 0)


class SetGlasses(MagicWord):
    aliases = ["glasses"]
    desc = "Set glasses of target toon."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("id", int, True), ("textureId", int, False, 0)]
    accessLevel = 'NO_ACCESS'

    def handleWord(self, invoker, avId, toon, *args):
        glassesId = args[0]
        glassesTex = args[1]

        if not 0 <= glassesId <= 24:
            return "Invalid glasses specified."
        if not 0 <= glassesTex <= 25:
            return "Invalid glasses texture specified."
        toon.b_setGlasses(glassesId, glassesTex, 0)


class SetBackpack(MagicWord):
    aliases = ["backpack"]
    desc = "Set backpack of target toon."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("id", int, True), ("textureId", int, False, 0)]
    accessLevel = 'NO_ACCESS'

    def handleWord(self, invoker, avId, toon, *args):
        bpId = args[0]
        bpTex = args[1]

        if not 0 <= bpId <= 26:
            return "Invalid backpack specified."
        if not 0 <= bpTex <= 22:
            return "Invalid backpack texture specified."
        toon.b_setBackpack(bpId, bpTex, 0)


class SetShoes(MagicWord):
    aliases = ["shoes"]
    desc = "Set shoes of target toon."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("id", int, True), ("textureId", int, False, 0)]
    accessLevel = 'NO_ACCESS'

    def handleWord(self, invoker, avId, toon, *args):
        shoesId = args[0]
        shoesTex = args[1]

        if not 0 <= shoesId <= 3:
            return "Invalid shoe type specified."
        if (shoesTex == 54 and not __debug__) or not 0 <= shoesTex <= 54:
            return "Invalid shoe specified."
        toon.b_setShoes(shoesId, shoesTex, 0)


class ClearAccessories(MagicWord):
    aliases = ["removeallaccessories", "removeaccessories"]
    desc = "Clear's all the accessories of the target."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'NO_ACCESS'

    def handleWord(self, invoker, avId, toon, *args):
        toon.b_setHat(0, 0, 0)
        toon.b_setGlasses(0, 0, 0)
        toon.b_setBackpack(0, 0, 0)
        toon.b_setShoes(0, 0, 0)
        return "Cleared the target's accessories."


class SetInventory(MagicWord):
    aliases = ["inventory"]
    desc = "Modify gag inventory. Can reset (clear) inventory or restock."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("command", str, True), ("level", int, False, 5), ("track", int, False, -1)]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        type = args[0]
        level = args[1]
        track = args[2]

        inventory = toon.inventory
        if type in ('reset', 'clear'):
            maxLevelIndex = level or 5
            if not 0 <= maxLevelIndex < len(ToontownBattleGlobals.Levels[0]):
                return "Invalid max level index: {0}".format(maxLevelIndex)
            targetTrack = -1 or track
            if not -1 <= targetTrack < len(ToontownBattleGlobals.Tracks):
                return "Invalid target track index: {0}".format(targetTrack)
            for track in range(0, len(ToontownBattleGlobals.Tracks)):
                if (targetTrack == -1) or (track == targetTrack):
                    inventory.inventory[track][:maxLevelIndex + 1] = [0] * (maxLevelIndex + 1)
            toon.b_setInventory(inventory.makeNetString())
            if targetTrack == -1:
                return "Inventory cleared."
            else:
                return "Inventory cleared for target track index: {0}".format(targetTrack)
        elif type == "restock":
            maxLevelIndex = level or 5
            if not 0 <= maxLevelIndex < len(ToontownBattleGlobals.Levels[0]):
                return "Invalid max level index: {0}".format(maxLevelIndex)
            targetTrack = -1 or track
            if not -1 <= targetTrack < len(ToontownBattleGlobals.Tracks):
                return "Invalid target track index: {0}".format(targetTrack)
            if (targetTrack != -1) and (not toon.hasTrackAccess(targetTrack)):
                return "The target Toon doesn't have target track index: {0}".format(targetTrack)
            inventory.maxInventory(maxLevel=level, clearFirst=True)
            toon.b_setInventory(inventory.makeNetString())
            if targetTrack == -1:
                return "Inventory restocked."
            else:
                return "Inventory restocked for target track index: {0}".format(targetTrack)
        else:
            try:
                targetTrack = int(type)
            except:
                return "Invalid first argument."
            if not toon.hasTrackAccess(targetTrack):
                return "The target Toon doesn't have target track index: {0}".format(targetTrack)
            maxLevelIndex = level or 6
            if not 0 <= maxLevelIndex < len(ToontownBattleGlobals.Levels[0]):
                return "Invalid max level index: {0}".format(maxLevelIndex)
            for _ in range(track):
                inventory.addItem(targetTrack, maxLevelIndex)
                toon.b_setInventory(inventory.makeNetString())
            return "Restored {0} Gags to: {1}, {2}".format(track, targetTrack, maxLevelIndex)


class ToggleGM(MagicWord):
    desc = "Toggle the target's GM icon."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        access = invoker.getAccessLevel()
        if invoker.isGM():
            invoker.b_setGM(0)
            return "You have disabled your GM icon."
        else:
            if access >= 800:
                invoker.b_setGM(5)
            elif access >= 700:
                invoker.b_setGM(6)
            elif access >= 600:
                invoker.b_setGM(8)
                invoker.b_setGM(7)
                invoker.b_setGM(4)
            elif access >= 500:
                invoker.b_setGM(3)
            elif access >= 400:
                invoker.b_setGM(2)
            elif access >= 200:
                invoker.b_setGM(1)
            return "You have enabled your GM icon."


class ToggleGhost(MagicWord):
    aliases = ["ghost"]
    desc = "Set toon to invisible."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        if invoker.ghostMode == 0:
            invoker.b_setGhostMode(2)
            return "Going ghost!"
        else:
            invoker.b_setGhostMode(0)


class SetGM(MagicWord):
    aliases = ["gmicon", "gm"]
    desc = "Set the target's GM Icon."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("id", int, True), ("name", bool, False, False)]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        gmId = args[0]

        # if gmId == 1:
        #    return 'This GM is reserved for the Toon Council. Use ~setGM 2 instead.'

        if not 0 <= gmId <= 8:
            return "Invalid GM Icon specified."

        accessLevel = toon.getAccessLevel()
        if gmId > 3 and accessLevel < 600:
            return "Your access level is too low to use this GM icon."
        else:
            if (accessLevel < 400 and gmId > 2) or (accessLevel < 500 and gmId > 3):
                return "Your access level is too low to use this GM icon."

        if toon.isGM() and gmId != 0:
            toon.b_setGM(0)
        elif toon.isGM and gmId == 0:
            toon.b_setGM(0)

        toon.b_setGM(gmId)

        if __debug__:
            pass
        else:
            toon.d_requestVerifyGM()

        return "You have set %s to GM type %s" % (toon.getName(), gmId)


class SetTickets(MagicWord):
    aliases = ["tickets"]
    desc = "Set the target's racing ticket's value."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("val", int, True)]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        tixVal = args[0]
        if not 0 <= tixVal <= 99999:
            return "Ticket value out of range (0-99999)"
        toon.b_setTickets(tixVal)
        return "%s's tickets were set to %s." % (toon.getName(), tixVal)


class GrowFlowers(MagicWord):
    desc = "Grow a target's flowers."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        estate = toon.air.estateMgr._lookupEstate(toon)

        if not estate:
            return "Estate not found!"

        house = estate.getAvHouse(avId)
        garden = house.gardenManager.gardens.get(toon.doId)
        if not garden:
            return "Garden not found!"

        now = int(time.time())
        i = 0
        for flower in garden.flowers:
            flower.b_setWaterLevel(5)
            flower.b_setGrowthLevel(2)
            flower.update()
            i += 1

        return "%d flowers grown." % i


class PickAllFlowers(MagicWord):
    aliases = ["pickflowers"]
    desc = "Picks all of the target's flowers."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        estate = toon.air.estateMgr._lookupEstate(toon)

        if not estate:
            return "Estate not found!"

        house = estate.getAvHouse(avId)
        garden = house.gardenManager.gardens.get(toon.doId)
        if not garden:
            return "Garden not found!"

        i = 0
        for flower in garden.flowers.copy():
            if flower.getGrowthLevel() >= flower.growthThresholds[2]:
                flower.removeItem(1)
                i += 1

        return "%d flowers picked." % i


class GrowTrees(MagicWord):
    desc = "Grows the target's trees."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("track", str, True), ("index", int, True), ("amount", int, False, 21)]
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        track = args[0]
        index = args[1]
        grown = args[2]

        estate = toon.air.estateMgr._lookupEstate(toon)

        if not estate:
            return "Estate not found!"

        house = estate.getAvHouse(avId)
        garden = house.gardenManager.gardens.get(toon.doId)
        if not garden:
            return "Garden not found!"

        try:
            trackIndex = ('toonup', 'trap', 'lure', 'sound', 'throw',
                          'squirt', 'drop').index(track)
        except ValueError:
            # Backwards compatibility
            try:
                trackIndex = int(track)
            except ValueError:
                return 'Gag track is invalid.'

        if trackIndex > 6:
            return 'Gag track is invalid.'

        tree = garden.getTree(trackIndex, index)
        if not tree:
            return "Tree not found!"

        result = tree.doGrow(grown)
        return '%d trees grown.' % result


class PickTrees(MagicWord):
    desc = "Picks the target's trees."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("track", str, True), ("index", int, True)]
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        track = args[0]
        index = args[1]
        estate = toon.air.estateMgr._lookupEstate(toon)

        if not estate:
            return "Estate not found!"

        house = estate.getAvHouse(avId)
        garden = house.gardenManager.gardens.get(toon.doId)
        if not garden:
            return "Garden not found!"

        try:
            trackIndex = ('toonup', 'trap', 'lure', 'sound', 'throw',
                          'squirt', 'drop').index(track)
        except ValueError:
            # Backwards compatibility
            try:
                trackIndex = int(track)
            except ValueError:
                return 'Gag track is invalid.'

        if trackIndex > 6:
            return 'Gag track is invalid.'

        tree = garden.getTree(trackIndex, index)
        if not tree:
            return "Tree not found!"

        tree.calculate(0, tree.lastCheck)
        tree.sendUpdate('setFruiting', [tree.getFruiting()])
        return "Trees picked."


class FlowerAll(MagicWord):
    desc = "Flowers the target's flowers."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("species", int, False, 49), ("variety", int, False, 0)]
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        species = args[0]
        variety = args[1]

        estate = toon.air.estateMgr._lookupEstate(toon)
        if not estate:
            return "Estate not found!"

        house = estate.getAvHouse(avId)
        garden = house.gardenManager.gardens.get(toon.doId)
        if not garden:
            return "Garden not found!"

        from toontown.estate.DistributedGardenPlotAI import DistributedGardenPlotAI
        i = 0
        for obj in garden.objects.copy():
            if isinstance(obj, DistributedGardenPlotAI):
                if obj.plotType != GardenGlobals.FLOWER_TYPE:
                    continue

                if not obj.plantFlower(species, variety, 1):
                    return "Error on plot %d!" % i

                i += 1

        return "%d flowers planted." % i


class RestockFlowerSpecials(MagicWord):
    desc = "Give special flowers."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        toon.gardenSpecials = []
        for x in (100, 101, 102, 103, 105, 106, 107, 108, 109, 130, 131, 135):
            toon.addGardenItem(x, 99)


class MaxDoodle(MagicWord):
    desc = "Maxes the target's doodle."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        petId = invoker.getPetId()
        pet = simbase.air.doId2do.get(petId)
        if not pet:
            return "You must be at your estate and own a doodle to use this magic word!"

        pet.b_setTrickAptitudes([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])
        return "Maxed your doodle!"


class LeaveRace(MagicWord):
    desc = "Leave the current race you are in."
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        messenger.send('leaveRace')


class RestartPieRound(MagicWord):
    aliases = ['rsp', 'restartpie']
    desc = "Restarts the pie round"
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("round", str, False, "next")]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        battle = args[0]
        from toontown.suit.DistributedSellbotBossAI import DistributedSellbotBossAI
        boss = None
        for do in list(simbase.air.doId2do.values()):
            if isinstance(do, DistributedSellbotBossAI):
                if invoker.doId in do.involvedToons:
                    boss = do
                    break
        if not boss:
            return "You aren't in a VP!"

        boss.exitIntroduction()
        boss.b_setState('BattleThree')
        return "Restarting Pie Round"


class SkipCFO(MagicWord):
    desc = "Skips to the indicated round of the CFO."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("round", str, False, "next")]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        battle = args[0]

        from toontown.suit.DistributedCashbotBossAI import DistributedCashbotBossAI
        boss = None
        for do in list(simbase.air.doId2do.values()):
            if isinstance(do, DistributedCashbotBossAI):
                if invoker.doId in do.involvedToons:
                    boss = do
                    break
        if not boss:
            return "You aren't in a CFO!"

        battle = battle.lower()

        if battle == 'two':
            if boss.state in ('PrepareBattleThree', 'BattleThree'):
                return "You can not return to previous rounds!"
            else:
                boss.exitIntroduction()
                boss.b_setState('PrepareBattleThree')
                return "Skipping to last round..."

        if battle == 'next':
            if boss.state in ('PrepareBattleOne', 'BattleOne'):
                boss.exitIntroduction()
                boss.b_setState('PrepareBattleThree')
                return "Skipping current round..."
            elif boss.state in ('PrepareBattleThree', 'BattleThree'):
                boss.exitIntroduction()
                boss.b_setState('Victory')
                return "Skipping final round..."


class HitCFO(MagicWord):
    desc = "Hits the CFO."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("damage", int, False, 0)]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        dmg = args[0]
        from toontown.suit.DistributedCashbotBossAI import DistributedCashbotBossAI
        boss = None
        for do in list(simbase.air.doId2do.values()):
            if isinstance(do, DistributedCashbotBossAI):
                if invoker.doId in do.involvedToons:
                    boss = do
                    break
        if not boss:
            return "You aren't in a CFO!"

        boss.magicWordHit(dmg, invoker.doId)


class RestartCraneRound(MagicWord):
    aliases = ['rcr', 'restartcrane']
    desc = "Restarts the crane round"
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("round", str, False, "next")]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        battle = args[0]
        from toontown.suit.DistributedCashbotBossAI import DistributedCashbotBossAI
        boss = None
        for do in list(simbase.air.doId2do.values()):
            if isinstance(do, DistributedCashbotBossAI):
                if invoker.doId in do.involvedToons:
                    boss = do
                    break
        if not boss:
            return "You aren't in a CFO!"

        if boss.state == 'Elevator':
            boss.sendUpdate('setState', ['Introduction'])
            
        boss.clearObjectSpeedCaching()
        battle = battle.lower()
        boss.exitIntroduction()
        boss.b_setState('PrepareBattleThree')
        boss.b_setState('BattleThree')
        
        return "Restarting Crane Round"


class SetCFOModifiers(MagicWord):
    aliases = ['cfomodifiers', 'cfomods']
    desc = "Dynamically tweak modifiers mid CFO"
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'USER'
    VALID_SUBCOMMANDS = ['debug', 'amount', 'random', 'clear', 'add', 'remove', 'on', 'off']
    arguments = [
        ('subcommand', str, False, 'debug'),  # subcommand
        ('mod-id/yes/no', str, False, 'debug'),  # modifier id/on/off/int
        ('tier', int, False, 1),  # tier
    ]

    def handleWord(self, invoker, avId, toon, *args):

        from toontown.suit.DistributedCashbotBossAI import DistributedCashbotBossAI
        boss = None
        for do in list(simbase.air.doId2do.values()):
            if isinstance(do, DistributedCashbotBossAI):
                if invoker.doId in do.involvedToons:
                    boss = do
                    break

        if not boss:
            return "You aren't in a CFO!"

        # Handle if no arguments given
        if args[0].lower() == self.VALID_SUBCOMMANDS[0]:
            return 'Valid subcommands: ' + ', '.join(self.VALID_SUBCOMMANDS)

        # Handle if they just want to turn them on or off
        if args[0].lower() in ['on', 'off']:

            if args[0].lower() == 'off':
                boss.numModsWanted = 0
                boss.rollModsOnStart = True
                return 'Modifiers turned off!'
            elif args[0].lower() == 'on':
                boss.numModsWanted = 5
                boss.rollModsOnStart = True
                return 'Modifiers turned on! Defaulted to 5 modifiers'

            return 'this should never happen lol'

        # Handle if setting amount of mods wanted
        if args[0].lower() == self.VALID_SUBCOMMANDS[1]:

            try:
                n = int(args[1])
            except:
                return "Please specify a number!"

            range = (0, len(list(CraneLeagueGlobals.CFORulesetModifierBase.MODIFIER_SUBCLASSES.values())))

            if n < range[0] or n > range[1]:
                return "Number of modifiers must be in between %s and %s" % (range[0], range[1])

            boss.numModsWanted = n
            return "Set desired amount of modifiers to %s" % n

        # Handle if we wanna randomize mods
        if args[0].lower() == self.VALID_SUBCOMMANDS[2]:

            response = args[1].lower()
            valid_responses = ('on', 'off')

            if response not in valid_responses:
                return "Please say on or off! ex: ~modifiers random on"

            map = {'on': True, 'off': False}
            boss.rollModsOnStart = map[response]
            return 'Randomize modifiers on restart set to: %s' % response

        # Handle if we want to clear the mods for the next round
        if args[0].lower() == self.VALID_SUBCOMMANDS[3]:
            ret = "Cleared modifiers, ~rcr to have changes take effect"
            if boss.rollModsOnStart:
                ret += ' warning: roll modifers on rcr active, use ~modifiers random off'
            boss.modifiers = []
            return ret

        # Handle if we want to add a modifier
        if args[0].lower() == self.VALID_SUBCOMMANDS[4]:

            try:
                mod_id = int(args[1])
            except:
                return "Please provide a number for modifier ID"

            mod = CraneLeagueGlobals.CFORulesetModifierBase.MODIFIER_SUBCLASSES.get(mod_id)
            if not mod:
                return "Invalid modifier ID provided"

            tier = args[2]
            if tier <= 0:
                return "Please provide a tier above 0!"

            m_instance = mod(tier)

            for m in list(boss.modifiers):
                if m.MODIFIER_ENUM == m_instance.MODIFIER_ENUM:
                    boss.modifiers.remove(m)

            boss.modifiers.append(m_instance)
            s = "Added modifier %s, ~rcr to take effect" % m_instance.getName()
            if boss.rollModsOnStart:
                s += ' warning: roll modifiers on rcr active, use ~modifiers random off'

            return s

        # Handle if we want to remove a modifier
        if args[0].lower() == self.VALID_SUBCOMMANDS[5]:

            try:
                mod_id = int(args[1])
            except:
                return "Please provide a number for modifier ID"

            mod = CraneLeagueGlobals.CFORulesetModifierBase.MODIFIER_SUBCLASSES.get(mod_id)
            if not mod:
                return "Invalid modifier ID provided"

            for m in list(boss.modifiers):
                if m.MODIFIER_ENUM == mod_id:
                    boss.modifiers.remove(m)

            s = "Removed modifier %s, ~rcr to take effect" % mod_id
            if boss.rollModsOnStart:
                s += ' warning: roll modifiers on rcr active, use ~modifiers random off'

            return s


class DisableGoons(MagicWord):
    desc = "Stuns all of the goons in an area."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        from toontown.suit.DistributedGoonAI import DistributedGoonAI
        for goon in simbase.air.doFindAllInstances(DistributedGoonAI):
            goon.requestStunned(0)
        return "Disabled all Goons!"


class SkipCJ(MagicWord):
    desc = "Skips to the indicated round of the CJ."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("round", str, False, "next")]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        battle = args[0]
        from toontown.suit.DistributedLawbotBossAI import DistributedLawbotBossAI
        boss = None
        for do in list(simbase.air.doId2do.values()):
            if isinstance(do, DistributedLawbotBossAI):
                if invoker.doId in do.involvedToons:
                    boss = do
                    break
        if not boss:
            return "You aren't in a CJ!"

        battle = battle.lower()

        if battle == 'two':
            if boss.state in ('RollToBattleTwo', 'PrepareBattleTwo', 'BattleTwo', 'PrepareBattleThree', 'BattleThree'):
                return "You can not return to previous rounds!"
            else:
                boss.exitIntroduction()
                boss.b_setState('RollToBattleTwo')
                return "Skipping to second round..."

        if battle == 'three':
            if boss.state in ('PrepareBattleThree', 'BattleThree'):
                return "You can not return to previous rounds!"
            else:
                boss.exitIntroduction()
                boss.b_setState('PrepareBattleThree')
                return "Skipping to final round..."

        if battle == 'next':
            if boss.state in ('PrepareBattleOne', 'BattleOne'):
                boss.exitIntroduction()
                boss.b_setState('RollToBattleTwo')
                return "Skipping current round..."
            elif boss.state in ('RollToBattleTwo', 'PrepareBattleTwo', 'BattleTwo'):
                boss.exitIntroduction()
                boss.b_setState('PrepareBattleThree')
                return "Skipping current round..."
            elif boss.state in ('PrepareBattleThree', 'BattleThree'):
                boss.exitIntroduction()
                boss.enterNearVictory()
                boss.b_setState('Victory')
                return "Skipping final round..."


class StunLawyers(MagicWord):
    desc = "Stuns all the lawyers in the CJ Evidence round."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        boss = None
        from toontown.suit.DistributedLawbotBossAI import DistributedLawbotBossAI
        for do in list(simbase.air.doId2do.values()):
            if isinstance(do, DistributedLawbotBossAI):
                if invoker.doId in do.involvedToons:
                    boss = do
                    break
        if not boss:
            return "You aren't in a CJ!"
        if not boss.state == 'BattleThree':
            return "You aren't in the evidence round."
        for suit in boss.lawyers:
            suit.hitByToon(avIdOverride=avId)

        return "Stunned the lawyers!"


class RestartScaleRound(MagicWord):
    aliases = ['rsc', 'restartscale']
    desc = "Restarts the scale round"
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("round", str, False, "next")]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        battle = args[0]
        from toontown.suit.DistributedLawbotBossAI import DistributedLawbotBossAI
        boss = None
        for do in list(simbase.air.doId2do.values()):
            if isinstance(do, DistributedLawbotBossAI):
                if invoker.doId in do.involvedToons:
                    boss = do
                    break
        if not boss:
            return "You aren't in a CJ!"

        battle = battle.lower()
        boss.exitIntroduction()
        boss.b_setState('BattleThree')
        return "Restarting Scale Round"


class StartCannonRound(MagicWord):
    aliases = ['cannons', 'startcannons']
    desc = "Enters the cannon round"
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("round", str, False, "next")]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        battle = args[0]
        from toontown.suit.DistributedLawbotBossAI import DistributedLawbotBossAI
        boss = None
        for do in list(simbase.air.doId2do.values()):
            if isinstance(do, DistributedLawbotBossAI):
                if invoker.doId in do.involvedToons:
                    boss = do
                    break
        if not boss:
            return "You aren't in a CJ!"

        battle = battle.lower()
        boss.exitIntroduction()
        boss.b_setState('BattleOne')
        boss.b_setState('PrepareBattleTwo')
        return "Entering Cannon Round"


class FillJury(MagicWord):
    desc = "Fills all of the chairs in the CJ's Jury Round."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        boss = None
        from toontown.suit.DistributedLawbotBossAI import DistributedLawbotBossAI
        for do in list(simbase.air.doId2do.values()):
            if isinstance(do, DistributedLawbotBossAI):
                if invoker.doId in do.involvedToons:
                    boss = do
                    break
        if not boss:
            return "You aren't in a CJ!"
        if not boss.state == 'BattleTwo':
            return "You aren't in the cannon round."
        for i in range(len(boss.chairs)):
            boss.chairs[i].b_setToonJurorIndex(0)
            boss.chairs[i].requestToonJuror()
        return "Filled chairs."


class RestartSeltzerRound(MagicWord):
    aliases = ['rss', 'restartseltzer']
    desc = "Restarts the seltzer round"
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("round", str, False, "next")]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        battle = args[0]
        from toontown.suit.DistributedBossbotBossAI import DistributedBossbotBossAI
        boss = None
        for do in list(simbase.air.doId2do.values()):
            if isinstance(do, DistributedBossbotBossAI):
                if invoker.doId in do.involvedToons:
                    boss = do
                    break
        if not boss:
            return "You aren't in a CEO!"

        boss.exitIntroduction()
        boss.b_setState('BattleFour')
        return "Restarting Seltzer Round"


class KillBoss(MagicWord):
    aliases = ['skipaction', 'killboss', 'skipfinal']
    desc = "Skips the final round of a Cog Boss."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'NO_ACCESS'
    priority = True

    def handleWord(self, invoker, avId, toon, *args):
        from toontown.suit.DistributedSellbotBossAI import DistributedSellbotBossAI
        from toontown.suit.DistributedCashbotBossAI import DistributedCashbotBossAI
        from toontown.suit.DistributedLawbotBossAI import DistributedLawbotBossAI
        from toontown.suit.DistributedBossbotBossAI import DistributedBossbotBossAI
        boss = None
        bossType = None
        for do in list(simbase.air.doId2do.values()):
            if isinstance(do, DistributedSellbotBossAI):
                if invoker.doId in do.involvedToons:
                    boss = do
                    bossType = 'sell'
                    break
            elif isinstance(do, DistributedCashbotBossAI):
                if invoker.doId in do.involvedToons:
                    boss = do
                    bossType = 'cash'
                    break
            elif isinstance(do, DistributedLawbotBossAI):
                if invoker.doId in do.involvedToons:
                    boss = do
                    bossType = 'law'
                    break
            elif isinstance(do, DistributedBossbotBossAI):
                if invoker.doId in do.involvedToons:
                    boss = do
                    bossType = 'boss'
                    break
        if not boss:
            return "You aren't in a Cog Boss!"

        if bossType == 'sell':
            if boss.state in ('PrepareBattleThree', 'BattleThree'):
                boss.exitIntroduction()
                boss.b_setState('Victory')
                return "Skipping VP Final..."
            else:
                return "You aren't in the final round!"
        elif bossType == 'cash':
            if boss.state in ('PrepareBattleThree', 'BattleThree'):
                boss.exitIntroduction()
                boss.b_setState('Victory')
                return "Skipping CFO Final..."
            else:
                return "You aren't in the final round!"
        elif bossType == 'law':
            if boss.state in ('PrepareBattleThree', 'BattleThree'):
                boss.exitIntroduction()
                boss.b_setState('Victory')
                return "Skipping CJ Final..."
            else:
                return "You aren't in the final round!"
        elif bossType == 'boss':
            if boss.state in ('PrepareBattleFour', 'BattleFour'):
                boss.exitIntroduction()
                boss.b_setState('Victory')
                return "Skipping CEO Final..."
            else:
                return "You aren't in the final round!"
        else:
            return "Got an invalid/no boss!"


class SkipVP(MagicWord):
    desc = "Skips to the indicated round of the VP."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("round", str, False, "next")]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        battle = args[0]
        from toontown.suit.DistributedSellbotBossAI import DistributedSellbotBossAI
        boss = None
        for do in list(simbase.air.doId2do.values()):
            if isinstance(do, DistributedSellbotBossAI):
                if invoker.doId in do.involvedToons:
                    boss = do
                    break
        if not boss:
            return "You aren't in a VP!"

        battle = battle.lower()

        if battle == 'one':
            boss.b_setState("Introduction")
            boss.b_setState('BattleOne')
            return "Starting battle one!"

        if battle == 'three':
            if boss.state in ('PrepareBattleThree', 'BattleThree'):
                return "You can not return to previous rounds!"
            else:
                boss.exitIntroduction()
                boss.b_setState('PrepareBattleThree')
                return "Skipping to final round..."

        if battle == 'next':
            if boss.state in ('PrepareBattleOne', 'BattleOne'):
                boss.exitIntroduction()
                boss.b_setState('PrepareBattleThree')
                return "Skipping current round..."
            elif boss.state in ('PrepareBattleThree', 'BattleThree'):
                boss.exitIntroduction()
                boss.b_setState('Victory')
                return "Skipping final round..."
            elif boss.state in ("Introduction", "Elevator"):
                if boss.state in ("Elevator"):
                    boss.b_setState("Introduction")
                boss.b_setState('BattleOne')
                return "Skipping introduction!"


class StunVP(MagicWord):
    desc = "Stuns the VP in the final round of his battle."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        from toontown.suit.DistributedSellbotBossAI import DistributedSellbotBossAI
        boss = None
        for do in list(simbase.air.doId2do.values()):
            if isinstance(do, DistributedSellbotBossAI):
                if invoker.doId in do.involvedToons:
                    boss = do
                    break
        if not boss:
            return "You aren't in a VP!"
        currState = boss.getCurrentOrNextState()
        if currState != 'BattleThree':
            return "You aren't in the final round of a VP!"
        boss.b_setAttackCode(ToontownGlobals.BossCogDizzyNow)
        boss.b_setBossDamage(boss.getBossDamage(), 0, 0)


class SkipCEO(MagicWord):
    desc = "Skips to the indicated round of the CEO."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("round", str, False, "next")]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        battle = args[0]
        from toontown.suit.DistributedBossbotBossAI import DistributedBossbotBossAI
        boss = None
        for do in list(simbase.air.doId2do.values()):
            if isinstance(do, DistributedBossbotBossAI):
                if invoker.doId in do.involvedToons:
                    boss = do
                    break
        if not boss:
            return "You aren't in a CEO!"

        battle = battle.lower()

        if battle == 'two':
            if boss.state in (
                    'PrepareBattleFour', 'BattleFour', 'PrepareBattleThree', 'BattleThree', 'PrepareBattleTwo',
                    'BattleTwo'):
                return "You can not return to previous rounds!"
            else:
                boss.exitIntroduction()
                boss.b_setState('PrepareBattleTwo')
                return "Skipping to second round..."

        if battle == 'three':
            if boss.state in ('PrepareBattleFour', 'BattleFour', 'PrepareBattleThree', 'BattleThree'):
                return "You can not return to previous rounds!"
            else:
                boss.exitIntroduction()
                boss.b_setState('PrepareBattleThree')
                return "Skipping to third round..."

        if battle == 'four':
            if boss.state in ('PrepareBattleFour', 'BattleFour'):
                return "You can not return to previous rounds!"
            else:
                boss.exitIntroduction()
                boss.b_setState('PrepareBattleFour')
                return "Skipping to last round..."

        if battle == 'next':
            if boss.state in ('PrepareBattleOne', 'BattleOne'):
                boss.exitIntroduction()
                boss.b_setState('PrepareBattleTwo')
                return "Skipping current round..."
            elif boss.state in ('PrepareBattleTwo', 'BattleTwo'):
                boss.exitIntroduction()
                boss.b_setState('PrepareBattleThree')
                return "Skipping current round..."
            elif boss.state in ('PrepareBattleThree', 'BattleThree'):
                boss.exitIntroduction()
                boss.b_setState('PrepareBattleFour')
                return "Skipping current round..."
            elif boss.state in ('PrepareBattleFour', 'BattleFour'):
                boss.exitIntroduction()
                boss.b_setState('Victory')
                return "Skipping final round..."


class FeedDiners(MagicWord):
    desc = "Feed the diners in the CEO battle."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        boss = None
        from toontown.suit.DistributedBossbotBossAI import DistributedBossbotBossAI
        for do in list(simbase.air.doId2do.values()):
            if isinstance(do, DistributedBossbotBossAI):
                if invoker.doId in do.involvedToons:
                    boss = do
                    break
        if not boss:
            return "You aren't in a CEO!"

        if boss.state != 'BattleTwo':
            return "You aren't in the waiter round!"

        for table in boss.tables:
            for chairIndex in list(table.dinerInfo.keys()):
                dinerStatus = table.getDinerStatus(chairIndex)
                if dinerStatus in (table.HUNGRY, table.ANGRY):
                    table.foodServed(chairIndex)

        return "All diners have been fed!"


class AbortGame(MagicWord):
    aliases = ["abortminigame", "leaveminigame"]
    desc = "Abort any minigame you are currently in."
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        messenger.send('minigameAbort')


class RequestMinigame(MagicWord):
    aliases = ['request', 'wantgame', 'requestgame']
    desc = "Request a specific minigame for the trolley."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [('game', str, True)]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):

        requested_name = args[0].lower()
        wanted_game_id = ToontownGlobals.MinigameNames.get(requested_name)

        if wanted_game_id is None:
            return f"There is no game registered with the name: {requested_name}\nValid choices are: {', '.join(ToontownGlobals.MinigameNames.keys())}"

        self.air.minigameMgr.storeRequest(toon.doId, wanted_game_id)
        return f"The next trolley game that {toon.getName()} plays will be {requested_name}!"


class ToggleSuitPaths(MagicWord):
    aliases = ['suitpaths']
    desc = "Toggles visualization of suit paths if they exist in your current zone."
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):

        # Attempt to find a SuitPlanner in the zone.
        from toontown.suit.DistributedSuitPlanner import DistributedSuitPlanner
        suitPlanners: Dict[int, DistributedSuitPlanner] = base.cr.getObjectsOfClass(DistributedSuitPlanner)

        # Are there none?
        if len(suitPlanners) <= 0:
            return "No suit planners found in your zone!"

        # Are we turning it off?
        if list(suitPlanners.values())[0].pathViz is not None:
            for suitPlanner in suitPlanners.values():
                suitPlanner.hidePaths()
            return f"Now un-visualizing {len(suitPlanners)} suit planners!"

        # Visualize them!
        for suitPlanner in suitPlanners.values():
            suitPlanner.showPaths()
        return f"Now visualizing {len(suitPlanners)} suit planners!"


class SpawnCog(MagicWord):
    aliases = ["cog"]
    desc = "Spawns a cog with the defined level"
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("suit", str, True), ("level", int, False, 1), ("specialSuit", int, False, 0), ("revives", int, False, 0)]
    accessLevel = 'NO_ACCESS'
    priority = True

    def handleWord(self, invoker, avId, toon, *args):
        name = args[0]
        level = args[1]
        specialSuit = args[2]
        revives = args[3]
        if name not in SuitDNA.suitHeadTypes:
            return "Suit %s is not a valid suit!" % name
        if level not in ToontownGlobals.SuitLevels:
            return "Invalid Cog Level."

        streetId = ZoneUtil.getBranchZone(invoker.zoneId)
        if streetId not in invoker.air.suitPlanners:
            return "Unable to spawn a level %d %s in current zone." % (level, name)
        sp = invoker.air.suitPlanners[streetId]
        map = sp.getZoneIdToPointMap()
        zones = [invoker.zoneId, invoker.zoneId - 1, invoker.zoneId + 1]

        if not sp:
            return "Unable to spawn a level %d %s in current zone." % (level, name)
        try:
            # This probably wont be needed, but in the rare case that we somehow try spawning a cog while the area is capped
            # We will remove one
            sp.commandCheckFlyRandomSuit()
            for zoneId in zones:
                if zoneId in map:
                    points = map[zoneId][:]
                    sp.createNewSuit([], points, suitName=name, suitLevel=level, skelecog=specialSuit, revives=revives)
            return "Spawned a level %d %s in current zone." % (level, name)
        except IndexError:
            return "Level %d is out of range for %s." % (level, name)


class SpawnInvasion(MagicWord):
    aliases = ["invasion"]
    desc = "Spawn an invasion on the current AI if one doesn't exist."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("command", str, True), ("suit", str, False, "f"), ("amount", int, False, 1000),
                 ("skelecog", bool, False, False)]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        cmd = args[0]
        name = args[1]
        num = args[2]
        skeleton = args[3]

        if not 10 <= num <= 25000:
            return "Can't the invasion amount to {}! Specify a value between 10 and 25,000.".format(num)

        invMgr = simbase.air.suitInvasionManager
        if cmd == 'start':
            if invMgr.getInvading():
                return "There is already an invasion on the current AI!"
            if not name in SuitDNA.suitHeadTypes:
                return "This cog does not exist!"
            invMgr.startInvasion(name, num, skeleton)
        elif cmd == 'stop':
            if not invMgr.getInvading():
                return "There is no invasion on the current AI!"
            # elif invMgr.undergoingMegaInvasion:
            #    return "The current invasion is a mega invasion, you must stop the holiday to stop the invasion."
            invMgr.stopInvasion()
        else:
            return "You didn't enter a valid command! Commands are ~invasion start or stop."


class SetTrophyScore(MagicWord):
    aliases = ["trophyscore"]
    desc = "Set the trophy score of target."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("val", int, True)]
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        amt = args[0]

        if not 0 <= amt <= 255:
            return "The amount must be between 0 and 255!"
        simbase.air.trophyMgr.addTrophy(toon.doId, toon.name, amt, True)


class GivePies(MagicWord):
    aliases = ["pies"]
    desc = "Gives the target pies to throw."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("type", int, True), ("amount", int, False, -1)]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        pieType = args[0]
        numPies = args[1]
        if pieType == -1:
            toon.b_setNumPies(0)
            return "Removed %s's pies." % toon.getName()
        if not 0 <= pieType <= 7:
            return "You can only specify between pie types 0 and 7."
        if numPies == -1:
            toon.b_setPieType(pieType)
            toon.b_setNumPies(ToontownGlobals.FullPies)
            return "Gave %s an infinite amount of pies" % toon.getName()
        if not 0 <= numPies <= 99:
            return "You can only specify between 0 and 99 pies."
        toon.b_setPieType(pieType)
        toon.b_setNumPies(numPies)


class SetQP(MagicWord):
    aliases = ["qp", "questprogress"]
    desc = "Get and set the targets quest progress."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("id", int, False, 0), ("progress", int, False, 0)]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        questId = args[0]
        progress = args[1]
        questIds = ""
        for index in range(len(toon.quests)):
            questIds += "{0} ".format(toon.quests[index][0])
            if toon.quests[index][0] == questId:
                toon.quests[index][4] = progress
        toon.b_setQuests(toon.quests)
        return questIds


class CompleteQuests(MagicWord):
    aliases = ["cq", "completequest"]
    desc = "Completes all quests on the target."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):

        for index in range(len(toon.quests)):
            toon.quests[index][4] = 2**16
        toon.b_setQuests(toon.quests)
        return f"Completed {len(toon.quests)} of {toon.getName()}'s quests!"


class SetUnites(MagicWord):
    aliases = ["unites", "restockunites"]
    desc = "Restocks the target's unites. The default amount is 999."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("amount", int, False, 999)]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        amt = args[0]
        if not 1 <= amt <= 999:
            return "Unite amount must be between 0 and 999!"
        toon.restockAllResistanceMessages(amt)
        return "Restocked " + str(amt) + " unites successfully!"


class UnlockTricks(MagicWord):
    aliases = ["tricks"]
    desc = "Unlock all the target's pet trick phrases."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        invoker.b_setPetTrickPhrases(list(range(7)))
        return "Unlocked pet tricks!"


class RestockSummons(MagicWord):
    desc = "Restock all of the target's CJ summons."
    aliases = ["summons"]
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        # Make sure we have every cog in our Cog Page.
        cogCount = []
        for deptIndex in range(5):
            for cogIndex in range(9):
                cogCount.append(CogPageGlobals.get_max_cog_quota(invoker) if cogIndex != 8 else 0)
        invoker.b_setCogCount(cogCount)
        invoker.b_setCogStatus(([CogPageGlobals.COG_COMPLETE2] * 8 + [0]) * 5)
        invoker.restockAllCogSummons()
        return "Restocked all cog summons successfully!"


class SetPinkSlips(MagicWord):
    aliases = ["pinkslips", "setfires", "fires"]
    desc = "Sets the target's pink slips. The default amount is 255."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("amount", int, False, 255)]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        amt = args[0]
        plural = 's'
        if not 0 <= amt <= 255:
            return "The amount must be between 0 and 255!"
        if amt == 1:
            plural = ''
        toon.b_setPinkSlips(amt)
        return "Restocked {0} pink slip{1} successfully!".format(amt, plural)


class QuestTier(MagicWord):
    desc = "Sets the target's quest tier to specified value."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("tier", int, True)]
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        tier = args[0]

        if not 0 <= tier <= 255:
            return "Can't set {}'s quest tier to {}! Specify a value between 0 and 255.".format(toon.getName(), tier)

        toon.b_setQuests([])
        toon.b_setRewardHistory(tier, [])
        return "Set %s's quest tier to %d." % (toon.getName(), tier)


class SetExp(MagicWord):
    aliases = ["exp"]
    desc = "Sets the target's experience for the specified gag track. The default amount is 0."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("track", str, True), ("amount", int, False, 0)]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        track = args[0]
        amt = args[1]

        tracks = ['toon-up', 'trap', 'lure', 'sound', 'throw', 'squirt', 'drop']
        maxed = ['max', 'maxxed']

        if track not in tracks + maxed:
            return "Invalid gag track specified!"

        if not 0 <= amt <= ToontownBattleGlobals.MaxSkill:
            return "Can't set {0}'s jellybean count to {1}! Specify a value between 0 and 999,9999.".format(
                toon.getName(), amt)

        if track in maxed:
            for track in tracks:
                toon.experience.setExp(track, amt if amt > 0 else 10000)
            toon.b_setExperience(toon.experience.getCurrentExperience())
            return "Maxed all of {}'s gag tracks.".format(toon.getName())
        else:
            trackIndex = TTLocalizer.BattleGlobalTracks.index(track)
            toon.experience.setExp(trackIndex, amt)
            toon.b_setExperience(toon.experience.getCurrentExperience())
            return "Set %s exp to %d successfully." % (track, amt)


class TrackBonus(MagicWord):
    desc = "Modify the invoker's track bonus level. "
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("track", int, True)]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        track = args[0]

        trackLength = ToontownBattleGlobals.UBER_GAG_LEVEL_INDEX
        numTracks = ToontownBattleGlobals.NUM_GAG_TRACKS
        gagAccess = invoker.getTrackAccess()

        trackBonusLevel = [-1] * numTracks
        if track == 8:
            bonusAccess = lambda x: trackLength if x > 0 else x
            trackBonusLevel = list(map(bonusAccess, gagAccess))
        elif 0 <= track < numTracks:
            if gagAccess[track]:
                trackBonusLevel[track] = trackLength
            else:
                return "You don\'t have that track!"
        else:
            return "Invalid track!"

        invoker.b_setTrackBonusLevel(trackBonusLevel)
        return "Track bonus set!"


class SetCogSuit(MagicWord):
    aliases = ["cogsuit"]
    desc = "Set disguise type and level."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("corp", str, True), ("type", str, True), ("level", int, True)]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        corp = args[0]
        type = args[1]
        level = args[2]
        corps = ['bossbot', 'lawbot', 'cashbot', 'sellbot']
        corp = corp.lower()
        if corp not in corps:
            return "Invalid cog corp. specified."
        corpIndex = corps.index(corp)

        if type == "nosuit":
            # They want to reset their suit entirely.
            parts = toon.getCogParts()
            parts[corpIndex] = 0
            toon.b_setCogParts(parts)
            types = toon.getCogTypes()
            types[corpIndex] = 0
            toon.b_setCogTypes(types)
            levels = toon.getCogLevels()
            levels[corpIndex] = 0
            toon.b_setCogLevels(levels)
            merits = toon.getCogMerits()
            merits[corpIndex] = 0
            toon.b_setCogMerits(merits)
            return "Reset %s disguise and removed all earned parts." % corp.capitalize()

        # Get the cog type from the specified short-hand value.
        types = SuitDNA.suitHeadTypes[8 * corpIndex:(8 * corpIndex) + 8]
        if type not in types:
            return "Invalid cog type specified.."
        typeIndex = types.index(type)

        # Make sure they gave a level that is in range.
        if typeIndex == 7:
            # The final suit can go up to Level 50.
            levelRange = list(range(8, 51))  # Last digit is exclusive.
        else:
            levelRange = list(range((typeIndex + 1), (typeIndex + 6)))
        if level not in levelRange:
            return "Invalid level specified for %s disguise %s." % (
                corp.capitalize(), SuitBattleGlobals.getSuitAttributes(type).name)

        # Reset their merits to 0.
        merits = toon.getCogMerits()
        merits[corpIndex] = 0
        toon.b_setCogMerits(merits)

        # Ensure they have all the parts.
        parts = toon.getCogParts()
        parts[corpIndex] = CogDisguiseGlobals.PartsPerSuitBitmasks[corpIndex]
        toon.b_setCogParts(parts)

        # Find out if they need laff boosts or laff points removed.
        # for levelBoost in [14, 19, 29, 39, 49]:
        #     if level <= levelBoost and not levelBoost > toon.getCogLevels()[corpIndex]:
        #         if toon.getMaxHp() <= 15:
        #             continue
        #         toon.b_setMaxHp(toon.getMaxHp() - 1)
        #     elif level > levelBoost and not levelBoost <= toon.getCogLevels()[corpIndex]:
        #         if toon.getMaxHp() >= 137:
        #             continue
        #         toon.b_setMaxHp(toon.getMaxHp() + 1)
        # # Lets be nice and give them a toonup or make them suffer.
        # if toon.getHp() > toon.getMaxHp():
        #     toon.takeDamage(toon.getHp() - toon.getMaxHp())
        # else:
        #     toon.toonUp(toon.getMaxHp() - toon.getHp())

        # Set their type and level that they specified.
        types = toon.getCogTypes()
        types[corpIndex] = typeIndex
        toon.b_setCogTypes(types)
        levels = toon.getCogLevels()
        levels[corpIndex] = level - 1  # -1 because it starts at 0
        toon.b_setCogLevels(levels)

        return "Set %s disguise to %s Level %d." % (
            corp.capitalize(), SuitBattleGlobals.getSuitAttributes(type).name, level)


class Merits(MagicWord):
    desc = "Set the target's merits to the value specified."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("corp", str, True), ("amount", int, True)]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        corp = args[0]
        amount = args[1]
        corps = ['bossbot', 'lawbot', 'cashbot', 'sellbot']
        if corp not in corps:
            return "Invalid cog corp. specified."
        corpIndex = corps.index(corp)

        merits = toon.getCogMerits()
        merits[corpIndex] = amount
        toon.b_setCogMerits(merits)


class Pouch(MagicWord):
    desc = "Set the target's max gag limit."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("amount", int, True)]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        amt = args[0]

        if not 1 <= amt <= 255:
            return "Can't set {0}'s pouch size to {1}! Specify a value between 1 and 255.".format(toon.getName(), amt)

        toon.b_setMaxCarry(amt)
        return "Set %s's pouch size to %d" % (toon.getName(), amt)


class SetNametagStyle(MagicWord):
    aliases = ["setnametag", "nametag", "nametagstyle"]
    desc = "Set the style of the target's nametag to the specified ID."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("style", str, True)]
    accessLevel = 'NO_ACCESS'

    def handleWord(self, invoker, avId, toon, *args):
        styleName = args[0]

        nametag_list = list(TTLocalizer.NametagFontNames)
        for index, item in enumerate(nametag_list):
            nametag_list[index] = item.lower()
        styleName = styleName.lower()

        if styleName in nametag_list:
            index = nametag_list.index(styleName)
        elif styleName == "basic":
            index = 100
        else:
            return "Invalid nametag name entered."

        toon.b_setNametagStyle(index)
        return "Set %s's nametag style successfully." % toon.getName()


class SetNametagType(MagicWord):
    aliases = ["nametagtype", "lacker"]
    desc = "Set the style of the target's nametag to the specified ID."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("type", int, False, 0)]
    accessLevel = 'NO_ACCESS'

    def handleWord(self, invoker, avId, toon, *args):
        type = args[0]

        nametagTypeList = [(0, NametagGroup.CCNormal), (1, NametagGroup.CCNonPlayer), (3, NametagGroup.CCSuit)]
        for nametag in nametagTypeList:
            if type == nametag[0]:
                toon.b_setNametagType(nametag[0])
                return "Changed %s's nametag type successfully." % toon.getName()

        return "Invalid nametag type specified!"


class Phrase(MagicWord):
    desc = "Unlocks a new phrase and adds it to target's list of 'My Phrases'."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("id", int, True)]
    accessLevel = 'NO_ACCESS'

    def handleWord(self, invoker, avId, toon, *args):
        phraseId = args[0]

        strings = OTPLocalizer.CustomSCStrings
        scId = int(phraseId) * 10
        id = None
        if scId in iter(strings.keys()):
            id = scId

        if id:
            if toon.customMessages.count(id) != 0:
                return "%s already has this custom phrase!" % toon.getName()
            if len(toon.customMessages) >= ToontownGlobals.MaxCustomMessages:
                toon.customMessages = toon.customMessages[1:]
            toon.customMessages.append(id)
            toon.d_setCustomMessages(toon.customMessages)
            return "Added new phrase to %s's custom phrases." % toon.getName()

        return "Invalid phrase id!"


class SetSos(MagicWord):
    aliases = ["sos"]
    desc = "Sets the target's SOS cards. The default is 1 Flippy card."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("amount", int, False, 1), ("name", str, False, 'Flippy')]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        amt = args[0]
        name = args[1]

        if not 0 <= amt <= 100:
            return "The amount must be between 0 and 100!"

        for npcId, npcName in TTLocalizer.NPCToonNames.items():
            if name.lower() == npcName.lower():
                if npcId not in NPCToons.npcFriends:
                    continue
                break
        else:
            return "The {0} SOS card was not found!".format(name)
        if (amt == 0) and (npcId in invoker.NPCFriendsDict):
            del toon.NPCFriendsDict[npcId]
        else:
            toon.NPCFriendsDict[npcId] = amt
        toon.d_setNPCFriendsDict(toon.NPCFriendsDict)
        return "Restocked {0} {1} SOS cards successfully!".format(amt, npcName)


class FreeBldg(MagicWord):
    desc = "Closest cog building gets freed."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):

        returnCode = invoker.doBuildingFree()
        if returnCode[0] == 'success':
            return "Successfully took back building!"
        elif returnCode[0] == 'busy':
            return "Toons are currently taking back the building!"
        return "Couldn't free building."


class MaxGarden(MagicWord):
    desc = "Maxes your garden."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        invoker.b_setShovel(3)
        invoker.b_setWateringCan(3)
        invoker.b_setShovelSkill(639)
        invoker.b_setWateringCanSkill(999)
        invoker.b_setGardenTrophies(list(GardenGlobals.TrophyDict.keys()))
        # invoker.b_setFlowerCollection([1, 2, 3, 4, 5], [1, 2, 3, 4, 5, 6, 7, 8, 9])
        # print invoker.flowerCollection.getNetLists()


class InstaDelivery(MagicWord):
    aliases = ["fastdel"]
    desc = "Instant delivery of an item."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        invoker.instantDelivery = not invoker.instantDelivery
        for item in toon.onOrder:
            item.deliveryDate = int(time.time() / 60)  # Deliver all the packages that they already ordered, too.
        return "Instant Delivery has been turned {0}.".format('on' if invoker.instantDelivery else 'off')


class SetMuzzle(MagicWord):
    aliases = ["muzzle"]
    desc = "Modify the targets muzzle."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("id", int, False, 0)]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        muzzle = args[0]
        if not 0 <= muzzle <= 5:
            return "Invalid muzzle. (0-5)"

        toon.b_setMuzzle(muzzle)
        if muzzle == 0:
            return "Returned muzzle to normal!"


class SetEyes(MagicWord):
    aliases = ["eyes"]
    desc = "Modify the targets eyes."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("id", int, False, 0)]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        type = args[0]
        if not 0 <= type <= 3:
            return "The type must be between 0 and 3!"

        toon.b_setEyes(type)
        if type == 0:
            return "Returned eyes to normal!"


class SetTaskCarryLimit(MagicWord):
    aliases = ["taskcarrylimit", "settaskcarry", "taskcarry", "setcarry"]
    desc = "Set the amount of tasks a toon can carry."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("limit", int, False, 1)]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        amt = args[0]
        plural = 's'

        if not 1 <= amt <= 6:
            return "The amount must be between 1 and 6!"
        if amt == 1:
            plural = ''
        toon.b_setQuestCarryLimit(amt)
        return "You can now carry {0} task{1}!".format(amt, plural)


class SetAlwaysHitCogs(MagicWord):
    aliases = ["alwayshitcogs", "hitcogs"]
    desc = "Enable/Disable always hitting cogs."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        if not toon:
            return

        if not toon.getAlwaysHitSuits():
            toon.setAlwaysHitSuits(True)
        else:
            toon.setAlwaysHitSuits(False)

        return "Toggled always hitting Cogs %s for %s" % ('ON' if toon.getAlwaysHitSuits() else 'OFF', toon.getName())


class EndFlying(MagicWord):
    desc = "Ends the flying game in a Lawbot Field Office."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        from toontown.cogdominium.DistCogdoFlyingGameAI import DistCogdoFlyingGameAI
        flyingGame = None
        for do in list(simbase.air.doId2do.values()):
            if isinstance(do, DistCogdoFlyingGameAI):
                if invoker.doId in do.getToonIds():
                    flyingGame = do
                    break

        if flyingGame:
            flyingGame._handleGameFinished()
            return "Completed the flying game."

        return "You are not in a flying game!"


class Ping(MagicWord):
    desc = "Pong!"
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'NO_ACCESS'

    def handleWord(self, invoker, avId, toon, *args):
        return "Pong!"


class GardenGame(MagicWord):
    aliases = ["gardendrop"]
    desc = "Start the garden drop mini-game."
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        from toontown.estate import GardenDropGame
        base.localAvatar.game = GardenDropGame.GardenDropGame()


class WinGame(MagicWord):
    aliases = ["winminigame"]
    desc = "Win the trolley game you are in."
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        messenger.send("minigameVictory")
        return "Trolley game won."


class GetZone(MagicWord):
    aliases = ["getzoneid"]
    desc = "Returns the target's zone ID."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'NO_ACCESS'

    def handleWord(self, invoker, avId, toon, *args):
        return "{}'s zone ID is {}.".format(toon.getName(), str(toon.zoneId))


class SetAccessLevel(MagicWord):
    aliases = ["accesslevel", "access", "setaccess"]
    desc = "Sets the target's access level."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("rank", int, False, 100)]
    affectRange = [MagicWordConfig.AFFECT_OTHER]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        rank = args[0]

        if not -100 <= rank <= 800:
            return "Can't set {0}'s speed to {1}! Specify a value between -100 and 800.".format(toon.getName(), rank)

        if invoker.getAccessLevel() == rank:
            return "You cannot set the target to your own Access Level!"

        rank = OTPGlobals.AccessLevelInt2Name.get(rank)
        toon.b_setAccessLevel(rank)
        return "Set {0}'s Access Level to {1}.".format(toon.getName(), rank)


class RestrictAccess(MagicWord):
    aliases = ["restrict", "remove", "block", "remove"]
    desc = "Restricts the target's access for the rest of the session."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    affectRange = [MagicWordConfig.AFFECT_OTHER]
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        if invoker == toon:
            return "You can't restrict access for yourself!"
        toon.b_setAccessLevel(OTPGlobals.AccessLevelName2Int.get('RESTRICTED'))
        return "Restricted {0}'s access for the rest of their session.".format(toon.getName())


class ToggleCheats(MagicWord):
    aliases = ["cheat", "cheats", "command", "commands"]
    desc = "Toggles cheats on and off for the Toon."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'NO_ACCESS'

    def handleWord(self, invoker, avId, toon, *args):
        if invoker != toon:
            return "You can only toggle cheats for yourself!"
        if toon.getAccessLevel() >= OTPGlobals.AccessLevelName2Int.get('USER'):
            toon.b_setAccessLevel(OTPGlobals.AccessLevelName2Int.get('NO_ACCESS'))
            return "Toggled cheats OFF."
        toon.b_setAccessLevel(OTPGlobals.AccessLevelName2Int.get('USER'))
        return "Toggled cheats ON. WARNING: Some commands may be unstable and cause bugs/crashes!"


class ToggleAdmin(MagicWord):
    aliases = ["admin", "setAdmin"]
    desc = "Toggles admin on and off for the toon."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        if invoker != toon:
            return "You can only toggle admin for yourself!"
        if toon.getAccessLevel() >= OTPGlobals.AccessLevelName2Int.get('TTOFF_DEVELOPER'):
            toon.b_setAccessLevel(OTPGlobals.AccessLevelName2Int.get('USER'))
            return "Toggled admin OFF."
        toon.b_setAccessLevel(OTPGlobals.AccessLevelName2Int.get('TTOFF_DEVELOPER'))
        return "Toggled admin ON. WARNING: Some commands may be unstable and cause bugs/crashes!"


class PrintChildren(MagicWord):
    aliases = ["children"]
    desc = "Prints all of render's children to the client log."
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT
    arguments = [("type", int, False, 0), ("mode", int, False, 0)]
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        type = args[0]
        mode = args[1]

        if not type:
            node = render
        else:
            node = render2d

        if not mode:
            print(node.getChildren())
        elif mode == 2:
            for child in node.getChildren():
                for secondaryChild in child.getChildren():
                    print(secondaryChild.getChildren())
        elif mode == 3:
            for child in node.getChildren():
                for secondaryChild in child.getChildren():
                    for thirdChild in secondaryChild.getChildren():
                        print(thirdChild.getChildren())
        elif mode == 4:
            for child in node.getChildren():
                for secondaryChild in child.getChildren():
                    for thirdChild in secondaryChild.getChildren():
                        for fourthChild in thirdChild.getChildren():
                            print(fourthChild.getChildren())
        elif mode == 5:
            for child in node.getChildren():
                for secondaryChild in child.getChildren():
                    for thirdChild in secondaryChild.getChildren():
                        for fourthChild in thirdChild.getChildren():
                            for fifthChild in fourthChild.getChildren():
                                print(fifthChild.getChildren())
        else:
            for child in node.getChildren():
                print(child.getChildren())


class StartBoss(MagicWord):
    aliases = ['startvp', 'startcfo', 'startcj', 'startceo']
    desc = 'Starts a boss battle.'
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):

        from ..toon.DistributedToonAI import DistributedToonAI

        hood_zones = [ToontownGlobals.BossbotHQ, ToontownGlobals.LawbotHQ,
                      ToontownGlobals.CashbotHQ, ToontownGlobals.SellbotHQ]
        if toon.zoneId not in hood_zones:
            return 'Toon is not in the correct zone! Expected a Cog HQ courtyard, got {}.'.format(toon.zoneId)

        # Get all players online
        online_toons: List[DistributedToonAI] = simbase.air.getAllOfType(DistributedToonAI)
        for online_toon in list(online_toons):
            if not online_toon.isPlayerControlled():
                online_toons.remove(online_toon)

        for hood in simbase.air.hoods:
            if hood.zoneId == toon.zoneId:

                toons_in_zone = [online_toon for online_toon in online_toons if online_toon.zoneId == toon.zoneId]

                # If there are more than 8 players, just grab the first 7 we find and assure that invoker is in it
                if len(toons_in_zone) > 8:
                    if toon.getDoId() in toons_in_zone:
                        toons_in_zone.remove(toon)

                    toons_in_zone = toons_in_zone[0:7]
                    toons_in_zone.append(toon)

                zone = hood.lobbyMgr.createBossOffice([t.getDoId() for t in toons_in_zone])
                for t in toons_in_zone:
                    t.sendUpdate('forceEnterBoss', [t.zoneId, zone])
                return f'Successfully created a boss for {len(toons_in_zone)} toons!!'

        return 'Cog HQ hood data not found!'


class CFOFight(MagicWord):
    aliases = ['cfo', 'cfofight', 'cfoboss']
    desc = 'Teleports you into a fresh CFO boss instance.'
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        # Create a new Cashbot boss office instance and force the invoker into it.
        # NOTE: forceEnterBoss relies on the CogHQ loader flow client-side, so we must
        # first get the toon into the Cashbot HQ courtyard, then enter the boss instance,
        # then fast-forward to the crane round (Battle Three).
        cashbotHoodId = ToontownGlobals.CashbotHQ

        for hood in simbase.air.hoods:
            if hood.zoneId != cashbotHoodId:
                continue

            zone = hood.lobbyMgr.createBossOffice([toon.getDoId()])
            # If we're not already in Cashbot HQ courtyard, teleport there first.
            if getattr(toon, 'zoneId', None) != cashbotHoodId:
                toon.d_doTeleport('CFO')

            def __enterBossInstance(attempt=0):
                # Wait until the toon is actually in Cashbot HQ before forcing boss entry.
                if getattr(toon, 'zoneId', None) != cashbotHoodId:
                    if attempt >= 50:
                        return
                    taskMgr.doMethodLater(0.1, __enterBossInstance, f'cfo-enter-boss-{toon.doId}', extraArgs=[attempt + 1])
                    return

                toon.sendUpdate('forceEnterBoss', [cashbotHoodId, zone])

            def __skipToCraneRound(attempt=0):
                from toontown.suit.DistributedCashbotBossAI import DistributedCashbotBossAI

                boss = None
                for do in list(simbase.air.doId2do.values()):
                    if isinstance(do, DistributedCashbotBossAI) and getattr(do, 'zoneId', None) == zone:
                        boss = do
                        break

                # Boss and/or toon may not have generated/entered yet; retry briefly.
                # We only fast-forward once the toon is actually inside the boss instance zone.
                if (not boss) or (getattr(toon, 'zoneId', None) != zone):
                    if attempt >= 80:
                        return
                    taskMgr.doMethodLater(0.1, __skipToCraneRound, f'cfo-skip-to-crane-{zone}', extraArgs=[attempt + 1])
                    return

                # Ensure we are treated as involved for state logic.
                if toon.doId not in boss.involvedToons:
                    boss.involvedToons.append(toon.doId)

                # Mirror the existing restart/skip logic used by ~rcr.
                if boss.state == 'Elevator':
                    boss.sendUpdate('setState', ['Introduction'])

                # If we're already in crane round, don't spam state changes.
                if boss.state in ('PrepareBattleThree', 'BattleThree'):
                    return

                boss.clearObjectSpeedCaching()
                boss.exitIntroduction()
                boss.b_setState('PrepareBattleThree')
                boss.b_setState('BattleThree')

            taskMgr.doMethodLater(0.1, __enterBossInstance, f'cfo-enter-boss-{toon.doId}', extraArgs=[0])
            taskMgr.doMethodLater(0.1, __skipToCraneRound, f'cfo-skip-to-crane-{zone}', extraArgs=[0])
            return 'Created a new CFO instance and teleported you into the crane round.'

        return 'Cashbot HQ hood data not found!'


class ExitCFOCrane(MagicWord):
    aliases = ['exitcfo', 'leavecfo', 'cfoexit', 'cfotc']
    desc = 'Exits the CFO crane round and returns you to Toontown Central.'
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        # If the toon is currently involved in a CFO instance, remove them cleanly.
        try:
            from toontown.suit.DistributedCashbotBossAI import DistributedCashbotBossAI
            for do in list(simbase.air.doId2do.values()):
                if isinstance(do, DistributedCashbotBossAI) and invoker.doId in getattr(do, 'involvedToons', []):
                    do.removeToon(invoker.doId, died=False)
                    break
        except Exception:
            # Always fall back to teleporting out.
            pass

        toon.d_doTeleport('TTC')
        return 'Teleported you back to Toontown Central.'


class SetDNA(MagicWord):
    aliases = ['dna']
    desc = 'Modify a DNA part on the invoker'
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("part", str, True), ("value", str, True)]
    accessLevel = 'NO_ACCESS'

    def handleWord(self, invoker, avId, toon, *args):
        dna = ToonDNA.ToonDNA()
        dna.makeFromNetString(invoker.getDNAString())

        part = args[0]
        value = args[1]

        part = part.lower()
        if part.endswith('color') or part.endswith('tex') or part.endswith('size') or part.endswith(
                'gloves') or part.endswith('torso'):
            try:
                value = int(value)
            except:
                return 'Invalid value type for: ' + part

        if part == 'gender':
            if value not in ('m', 'f', 'male', 'female'):
                return 'Invalid gender: ' + value
            dna.gender = value[0]
            invoker.b_setDNAString(dna.makeNetString())
            return 'Gender set to: ' + dna.gender

        if part in ('head', 'species'):
            speciesNames = (
                'dog', 'cat', 'horse', 'mouse', 'rabbit', 'duck', 'monkey', 'bear',
                'pig', 'deer', 'beaver', 'alligator', 'fox', 'bat', 'raccoon', 'turkey',
                'koala', 'kangaroo', 'kiwi', 'armadillo'
            )
            if value in speciesNames:
                speciesIndex = speciesNames.index(value)
                value = ToonDNA.toonSpeciesTypes[speciesIndex]
            if value not in ToonDNA.toonSpeciesTypes:
                return 'Invalid species: ' + value
            dna.head = value + dna.head[1:3]
            invoker.b_setDNAString(dna.makeNetString())
            return 'Species set to: ' + dna.head[0]

        if part == 'headsize':
            sizes = ('ls', 'ss', 'sl', 'll')
            if not 0 <= value <= len(sizes):
                return 'Invalid head size index: ' + str(value)
            dna.head = dna.head[0] + sizes[value]
            invoker.b_setDNAString(dna.makeNetString())
            return 'Head size index set to: ' + dna.head[1:]

        if part == 'torso':
            if dna.gender not in ('m', 'f'):
                return 'Unknown gender.'
            try:
                value = int(value)
            except:
                return 'Invalid value type for: ' + part
            if (dna.gender == 'm') and (not 0 <= value <= 2):
                return 'Male torso index out of range (0-2).'
            if (dna.gender == 'f') and (not 3 <= value <= 8):
                return 'Female torso index out of range (3-8).'
            dna.torso = ToonDNA.toonTorsoTypes[value]
            invoker.b_setDNAString(dna.makeNetString())
            return 'Torso set to: ' + dna.torso

        if part == 'legs':
            try:
                value = int(value)
            except:
                return 'Invalid value type for: ' + part
            if not 0 <= value <= len(ToonDNA.toonLegTypes):
                return 'Legs index out of range (0-%d).' % len(ToonDNA.toonLegTypes)
            dna.legs = ToonDNA.toonLegTypes[value]
            invoker.b_setDNAString(dna.makeNetString())
            return 'Legs set to: ' + dna.legs

        if part == 'headcolor':
            if dna.gender not in ('m', 'f'):
                return 'Unknown gender.'
            if (dna.gender == 'm') and (value not in ToonDNA.defaultBoyColorList):
                return 'Invalid male head color index: ' + str(value)
            if (dna.gender == 'f') and (value not in ToonDNA.defaultGirlColorList):
                return 'Invalid female head color index: ' + str(value)
            dna.headColor = value
            invoker.b_setDNAString(dna.makeNetString())
            return 'Head color index set to: ' + str(dna.headColor)

        if part == 'armcolor':
            if dna.gender not in ('m', 'f'):
                return 'Unknown gender.'
            if (dna.gender == 'm') and (value not in ToonDNA.defaultBoyColorList):
                return 'Invalid male arm color index: ' + str(value)
            if (dna.gender == 'f') and (value not in ToonDNA.defaultGirlColorList):
                return 'Invalid female arm color index: ' + str(value)
            dna.armColor = value
            invoker.b_setDNAString(dna.makeNetString())
            return 'Arm color index set to: ' + str(dna.armColor)

        if part == 'legcolor':
            if dna.gender not in ('m', 'f'):
                return 'Unknown gender.'
            if (dna.gender == 'm') and (value not in ToonDNA.defaultBoyColorList):
                return 'Invalid male leg color index: ' + str(value)
            if (dna.gender == 'f') and (value not in ToonDNA.defaultGirlColorList):
                return 'Invalid female leg color index: ' + str(value)
            dna.legColor = value
            invoker.b_setDNAString(dna.makeNetString())
            return 'Leg color index set to: ' + str(dna.legColor)

        if part == 'color':
            if dna.gender not in ('m', 'f'):
                return 'Unknown gender.'
            if (dna.gender == 'm') and (value not in ToonDNA.defaultBoyColorList):
                return 'Invalid male leg color index: ' + str(value)
            if (dna.gender == 'f') and (value not in ToonDNA.defaultGirlColorList):
                return 'Invalid female leg color index: ' + str(value)
            dna.headColor = value
            dna.armColor = value
            dna.legColor = value
            invoker.b_setDNAString(dna.makeNetString())
            return 'Color index set to: ' + str(dna.headColor)

        if part == 'gloves':
            try:
                value = int(value)
            except:
                return 'Invalid value type for: ' + part
            if value != 0:
                return 'Invalid glove color: ' + str(value)
            dna.gloveColor = value
            invoker.b_setDNAString(dna.makeNetString())
            return 'Glove color set to: ' + str(dna.gloveColor)

        if part == 'toptex':
            if not 0 <= value <= len(ToonDNA.Shirts):
                return 'Top texture index out of range (0-%d).' % len(ToonDNA.Shirts)
            dna.topTex = value
            invoker.b_setDNAString(dna.makeNetString())
            return 'Top texture index set to: ' + str(dna.topTex)

        if part == 'toptexcolor':
            if not 0 <= value <= len(ToonDNA.ClothesColors):
                return 'Top texture color index out of range(0-%d).' % len(ToonDNA.ClothesColors)
            dna.topTexColor = value
            invoker.b_setDNAString(dna.makeNetString())
            return 'Top texture color index set to: ' + str(dna.topTexColor)

        if part == 'sleevetex':
            if not 0 <= value <= len(ToonDNA.Sleeves):
                return 'Sleeve texture index out of range(0-%d).' % len(ToonDNA.Sleeves)
            dna.sleeveTex = value
            invoker.b_setDNAString(dna.makeNetString())
            return 'Sleeve texture index set to: ' + str(dna.sleeveTex)

        if part == 'sleevetexcolor':
            if not 0 <= value <= len(ToonDNA.ClothesColors):
                return 'Sleeve texture color index out of range(0-%d).' % len(ToonDNA.ClothesColors)
            dna.sleeveTexColor = value
            invoker.b_setDNAString(dna.makeNetString())
            return 'Sleeve texture color index set to: ' + str(dna.sleeveTexColor)

        if part == 'bottex':
            if dna.gender not in ('m', 'f'):
                return 'Unknown gender.'
            if dna.gender == 'm':
                bottoms = ToonDNA.BoyShorts
            else:
                bottoms = ToonDNA.GirlBottoms
            if not 0 <= value <= len(bottoms):
                return 'Bottom texture index out of range (0-%d).' % len(bottoms)
            dna.botTex = value
            invoker.b_setDNAString(dna.makeNetString())
            return 'Bottom texture index set to: ' + str(dna.botTex)

        if part == 'bottexcolor':
            if not 0 <= value <= len(ToonDNA.ClothesColors):
                return 'Bottom texture color index out of range(0-%d).' % len(ToonDNA.ClothesColors)
            dna.botTexColor = value
            invoker.b_setDNAString(dna.makeNetString())
            return 'Bottom texture color index set to: ' + str(dna.botTexColor)

        # these arguments don't work
        # if part == 'save':
        #     backup = simbase.backups.load('toon', (invoker.doId,), default={})
        #     backup.setdefault('dna', {})[value] = invoker.getDNAString()
        #     simbase.backups.save('toon', (invoker.doId,), backup)
        #     return 'Saved a DNA backup for %s under the name: %s' % (invoker.getName(), value)

        # if part == 'restore':
        #     backup = simbase.backups.load('toon', (invoker.doId,), default={})
        #     if value not in backup.get('dna', {}):
        #         return "Couldn't find a DNA backup for %s under the name: %s" % (invoker.getName(), value)
        #     invoker.b_setDNAString(backup['dna'][value])
        #     return 'Restored a DNA backup for %s under the name: %s' % (invoker.getName(), value)

        return 'Invalid part: ' + part


# Start new magic words implemented for crane league debugging
class ShowScoreboard(MagicWord):
    aliases = ['scoreboard']
    desc = 'make scoreboard appear'
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT
    accessLevel = 'TTOFF_DEVELOPER'

    def getNearbyToons(self):
        from toontown.toon.Toon import Toon
        t = []
        for disObj in list(base.cr.doId2do.values()):
            if isinstance(disObj, Toon):
                t.append(disObj)

        return t

    def handleWord(self, invoker, avId, toon, *args):

        global DEBUG_SCOREBOARD
        global DEBUG_HEAT

        if not DEBUG_SCOREBOARD:
            from toontown.coghq.CogBossScoreboard import CogBossScoreboard
            DEBUG_SCOREBOARD = CogBossScoreboard()
            DEBUG_SCOREBOARD.show()
            DEBUG_HEAT = CraneLeagueHeatDisplay()
            # for toon in self.getNearbyToons():
            #     DEBUG_SCOREBOARD.addToon(toon.getDoId())

            return "scoreboard created!"

        n = random.randint(100, 1500)
        m = random.randint(5, 80)
        if random.randint(0, 99) <= 50:
            s = "BONUS!"
        else:
            s = ''

        DEBUG_HEAT.set_heat(n)
        DEBUG_SCOREBOARD.addScore(avId, m, reason=s)

        return "set heat to " + str(n)


class ShowActivityLog(MagicWord):
    aliases = ['log', 'activitylog']
    desc = 'make debug log appear'
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT
    accessLevel = 'NO_ACCESS'

    CHOICES = [
        'ye',
        'as;lkdfj;laksdfj;lkasdjf;lkasdfl;kasdljk;fasdf',
        'aaaaaaaaaaaaaaaaaaaaa',
        'words words words words words words words words words words words',
        'msg_labelmsg_labelmsg_labelmsg_labelmsg_labelmsg_label msg_label msg_labelmsg_label msg_label'

    ]

    def handleWord(self, invoker, avId, toon, *args):
        global DEBUG_LOG

        if not DEBUG_LOG:
            DEBUG_LOG = ActivityLog()

        DEBUG_LOG.addToLog(random.choice(self.CHOICES))

        return 'modified log'


# Command that forces your state to the 'Walk' state.
# Used in rare circumstances where your toon gets softlocked to prevent having to restart the game.
# Note: This is still a cheat so it should only be used when needed, as there are many scenarios where you
# can break the game by running this command when you shouldn't.
class FreeLocalToon(MagicWord):
    aliases = ['free', 'unstuck', 'freeme', 'unstick', 'imstuck', 'stuck']
    desc = "Forces your toon to be set in the 'walk' state where you can regain control of your toon and walk around freely. Use at your own risk."
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):

        # Check for common errors when trying to do this
        if not hasattr(self.cr, 'playGame') or not hasattr(self.cr.playGame, 'place') or self.cr.playGame.getPlace() is None:
            return "Your toon is in an invalid state to run this command!"

        self.cr.playGame.getPlace().setState('walk')
        return "Freed your toon!"


# Command to start a "sandbox" battle.
# Used for toying with battle mechanics.
class SandboxBattle(MagicWord):
    aliases = ['sandbox', 'custombattle']
    desc = 'Starts a sandbox turn based battle. Used for testing battle mechanics and gives control of a dynamic suit planner.'
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'TTOFF_DEVELOPER'

    def handleWord(self, invoker, avId, toon, *args):
        from ..battle.DistributedBattleSandboxAI import DistributedBattleSandboxAI
        from ..toon.DistributedToonAI import DistributedToonAI

        if toon.isBattling():
            return f"{toon.getName()} is battling! Cannot start a new one."

        teammates: List[int] = []
        for otherToonId, otherToon in self.air.getObjectsOfClassInZone(self.air.districtId, toon.zoneId, DistributedToonAI).items():
            if otherToon.isPlayerControlled() and toon != otherToon:
                teammates.append(otherToonId)

        if len(teammates) > 3:
            teammates = teammates[:3]

        zoneId = toon.zoneId

        # Start a new battle for them.
        battle: DistributedBattleSandboxAI = DistributedBattleSandboxAI(self.air, zoneId)
        battle.generateWithRequired(zoneId)
        battle.start(toon.doId, otherToons=teammates)
        suff = f" and {len(teammates)} others!" if len(teammates) > 0 else '!'
        return f"Started a sandbox battle for {toon.getName()}{suff}"


# Use this command template for spawning objects client side to tweak attributes quickly
# class SpawnObject(MagicWord):
#     aliases = ["sb"]
#     desc = "Spawn barrel."
#     execLocation = MagicWordConfig.EXEC_LOC_CLIENT
#
#     def handleWord(self, invoker, avId, toon, *args):
#         from ..coghq.DistributedAPCheckBarrel import DistributedAPCheckBarrel
#         b = DistributedAPCheckBarrel(base.cr)
#         b.generateInit()
#         b.reparentTo(render)
#         b.loadModel()
#         b.applyLabel()
#         pos = base.localAvatar.getPos()
#         b.setPos(pos[0]+5, pos[1], pos[2])
#         return "Spawned a barrel"


class QMSetInventory(MagicWord):
    aliases = ["qmsetinventory"]
    desc = "Sets inventory for quick match toon."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("invStr", str, True)]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        invStr = args[0]
        try:
            counts = [int(x) for x in invStr.split(",")]
            if len(counts) != 49:
                return "Invalid gag count length!"
        except Exception as e:
            return f"Error parsing inventory: {str(e)}"
            
        inventory = toon.inventory
        idx = 0
        for track in range(7):
            for level in range(7):
                inventory.inventory[track][level] = counts[idx]
                idx += 1
                
        inventory.calcTotalProps()
        toon.b_setInventory(inventory.makeNetString())
        return "Quick match inventory set successfully."


class QMStartCogBattle(MagicWord):
    aliases = ["qmstartcogbattle"]
    desc = "Starts the quick match cog battle."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        zoneId = self.air.allocateZone()
        from toontown.building.DistributedQuickMatchCogInteriorAI import DistributedSuitInteriorAI
        interior = DistributedSuitInteriorAI(self.air, zoneId, toon.doId)
        interior.generateWithRequired(zoneId)
        
        if not hasattr(self.air, 'debos'):
            self.air.debos = {}
        self.air.debos[toon.doId] = interior
        
        self.air.magicWordManager.sendClientCommand(
            avId, 'qmteleporttobattle', 'QMTeleportToBattle',
            targetIds=[avId], parsedArgList=[zoneId]
        )
        return "Quick match battle started."


class QMTeleportToBattle(MagicWord):
    aliases = ["qmteleporttobattle"]
    desc = "Client side teleport to quick match cog battle."
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT
    arguments = [("zoneId", int, True)]
    accessLevel = 'USER'

    def handleWord(self, invoker, avId, toon, *args):
        zoneId = args[0]
        requestStatus = {
            'hoodId': ToontownGlobals.ToontownCentral,
            'zoneId': zoneId,
            'loader': 'suitInterior',
            'where': 'suitInterior',
            'how': 'teleportIn',
            'shardId': None,
            'avId': -1
        }
        place = base.cr.playGame.getPlace()
        if place:
            place.fsm.request('teleportOut', [requestStatus])


# Loop through every registered subclass of MagicWord and instantiate it.
for magicWordSubclass in MagicWord.__subclasses__():
    _ = magicWordSubclass()
