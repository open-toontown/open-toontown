##################################################
# The Toontown Offline Magic Word Manager
##################################################
# Author: Benjamin Frisby
# Copyright: Copyright 2020, Toontown Offline
# Credits: Benjamin Frisby, John Cote, Ruby Lord, Frank, Nick, Little Cat, Ooowoo
# License: MIT
# Version: 1.0.0
# Email: belloqzafarian@gmail.com
##################################################

import collections, types

from direct.distributed.ClockDelta import *
from direct.interval.IntervalGlobal import *

from panda3d.otp import NametagGroup, WhisperPopup

from otp.otpbase import OTPLocalizer
from otp.otpbase import OTPGlobals

from . import MagicWordConfig
import time, random, re, json

magicWordIndex = collections.OrderedDict()


class MagicWord:
    notify = DirectNotifyGlobal.directNotify.newCategory('MagicWord')

    # Whether this Magic word should be considered "hidden"
    # If your Toontown source has a page for Magic Words in the Sthickerbook, this will be useful for that
    hidden = False

    # Whether this Magic Word is an administrative command or not
    # Good for config settings where you want to disable cheaty Magic Words, but still want moderation ones
    administrative = False

    # List of names that will also invoke this word - a setHP magic word might have "hp", for example
    # A Magic Word will always be callable with its class name, so you don't have to put that in the aliases
    aliases = None

    # Description of the Magic Word
    # If your Toontown source has a page for Magic Words in the Sthickerbook, this will be useful for that
    desc = MagicWordConfig.MAGIC_WORD_DEFAULT_DESC

    # Advanced description that gives the user a lot more information than normal
    # If your Toontown source has a page for Magic Words in the Sthickerbook, this will be useful for that
    advancedDesc = MagicWordConfig.MAGIC_WORD_DEFAULT_ADV_DESC

    # Default example with for commands with no arguments set
    # If your Toontown source has a page for Magic Words in the Sthickerbook, this will be useful for that
    example = ""

    # The minimum access level required to use this Magic Word
    accessLevel = 'MODERATOR'

    # A restriction on the Magic Word which sets what kind or set of Distributed Objects it can be used on
    # By default, a Magic Word can affect everyone
    affectRange = [MagicWordConfig.AFFECT_SELF, MagicWordConfig.AFFECT_OTHER, MagicWordConfig.AFFECT_BOTH]

    # Where the magic word will be executed -- EXEC_LOC_CLIENT or EXEC_LOC_SERVER
    execLocation = MagicWordConfig.EXEC_LOC_INVALID

    # List of all arguments for this word, with the format [(type, isRequired), (type, isRequired)...]
    # If the parameter is not required, you must provide a default argument: (type, False, default)
    arguments = None

    def __init__(self):
        if self.__class__.__name__ != "MagicWord":
            self.aliases = self.aliases if self.aliases is not None else []
            self.aliases.insert(0, self.__class__.__name__)
            self.aliases = [x.lower() for x in self.aliases]
            self.arguments = self.arguments if self.arguments is not None else []

            if len(self.arguments) > 0:
                for arg in self.arguments:
                    argInfo = ""
                    if not arg[MagicWordConfig.ARGUMENT_REQUIRED]:
                        argInfo += "(default: {0})".format(arg[MagicWordConfig.ARGUMENT_DEFAULT])
                    self.example += "[{0}{1}] ".format(arg[MagicWordConfig.ARGUMENT_NAME], argInfo)

            self.__register()

    def __register(self):
        for wordName in self.aliases:
            if wordName in magicWordIndex:
                self.notify.error('Duplicate Magic Word name or alias detected! Invalid name: {}'. format(wordName))
            magicWordIndex[wordName] = {'class': self,
                                        'classname': self.__class__.__name__,
                                        'hidden': self.hidden,
                                        'administrative': self.administrative,
                                        'aliases': self.aliases,
                                        'desc': self.desc,
                                        'advancedDesc': self.advancedDesc,
                                        'example': self.example,
                                        'execLocation': self.execLocation,
                                        'access': self.accessLevel,
                                        'affectRange': self.affectRange,
                                        'args': self.arguments}

    def loadWord(self, air=None, cr=None, invokerId=None, targets=None, args=None):
        self.air = air
        self.cr = cr
        self.invokerId = invokerId
        self.targets = targets
        self.args = args

    def executeWord(self):
        executedWord = None
        validTargets = len(self.targets)
        for avId in self.targets:
            invoker = None
            toon = None
            if self.air:
                invoker = self.air.doId2do.get(self.invokerId)
                toon = self.air.doId2do.get(avId)
            elif self.cr:
                invoker = self.cr.doId2do.get(self.invokerId)
                toon = self.cr.doId2do.get(avId)
            if hasattr(toon, "getName"):
                name = toon.getName()
            else:
                name = avId

            if not self.validateTarget(toon):
                if len(self.targets) > 1:
                    validTargets -= 1
                    continue
                return "{} is not a valid target!".format(name)

            # TODO: Should we implement locking?
            # if toon.getLocked() and not self.administrative:
            #     if len(self.targets) > 1:
            #         validTargets -= 1
            #         continue
            #     return "{} is currently locked. You can only use administrative commands on them.".format(name)

            if invoker.getAccessLevel() <= toon.getAccessLevel() and toon != invoker:
                if len(self.targets) > 1:
                    validTargets -= 1
                    continue
                targetAccess = OTPGlobals.AccessLevelDebug2Name.get(OTPGlobals.AccessLevelInt2Name.get(toon.getAccessLevel()))
                invokerAccess = OTPGlobals.AccessLevelDebug2Name.get(OTPGlobals.AccessLevelInt2Name.get(invoker.getAccessLevel()))
                return "You don't have a high enough Access Level to target {0}! Their Access Level: {1}. Your Access Level: {2}.".format(name, targetAccess, invokerAccess)

            if self.execLocation == MagicWordConfig.EXEC_LOC_CLIENT:
                self.args = json.loads(self.args)

            executedWord = self.handleWord(invoker, avId, toon, *self.args)
        # If you're only using the Magic Word on one person and there is a response, return that response
        if executedWord and len(self.targets) == 1:
            return executedWord
        # If the amount of targets is higher than one...
        elif validTargets > 0:
            # And it's only 1, and that's yourself, return None
            if validTargets == 1 and self.invokerId in self.targets:
                return None
            # Otherwise, state how many targets you executed it on
            return "Magic Word successfully executed on %s target(s)." % validTargets
        else:
            return "Magic Word unable to execute on any targets."

    def validateTarget(self, target):
        if self.air:
            from toontown.toon.DistributedToonAI import DistributedToonAI
            return isinstance(target, DistributedToonAI)
        elif self.cr:
            from toontown.toon.DistributedToon import DistributedToon
            return isinstance(target, DistributedToon)
        return False

    def handleWord(self, invoker, avId, toon, *args):
        raise NotImplementedError


class SetHP(MagicWord):
    aliases = ["hp", "setlaff", "laff"]
    desc = "Sets the target's current laff."
    advancedDesc = "This Magic Word will change the current amount of laff points the target has to whichever " \
                   "value you specify. You are only allowed to specify a value between -1 and the target's maximum " \
                   "laff points. If you specify a value less than 1, the target will instantly go sad unless they " \
                   "are in Immortal Mode."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("hp", int, True)]

    def handleWord(self, invoker, avId, toon, *args):
        hp = args[0]

        if not -1 <= hp <= toon.getMaxHp():
            return "Can't set {0}'s laff to {1}! Specify a value between -1 and {0}'s max laff ({2}).".format(
                toon.getName(), hp, toon.getMaxHp())

        if hp <= 0 and toon.immortalMode:
            return "Can't set {0}'s laff to {1} because they are in Immortal Mode!".format(toon.getName(), hp)

        toon.b_setHp(hp)
        return "{}'s laff has been set to {}.".format(toon.getName(), hp)


class SetMaxHP(MagicWord):
    aliases = ["maxhp", "setmaxlaff", "maxlaff"]
    desc = "Sets the target's max laff."
    advancedDesc = "This Magic Word will change the maximum amount of laff points the target has to whichever value " \
                   "you specify. You are only allowed to specify a value between 15 and 137 laff points."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    arguments = [("maxhp", int, True)]

    def handleWord(self, invoker, avId, toon, *args):
        maxhp = args[0]

        if not 15 <= maxhp <= 137:
            return "Can't set {}'s max laff to {}! Specify a value between 15 and 137.".format(toon.getName(), maxhp)

        toon.b_setMaxHp(maxhp)
        toon.toonUp(maxhp)
        return "{}'s max laff has been set to {}.".format(toon.getName(), maxhp)


class ToggleOobe(MagicWord):
    aliases = ["oobe"]
    desc = "Toggles the out of body experience mode, which lets you move the camera freely."
    advancedDesc = "This Magic Word will toggle what is known as 'Out Of Body Experience' Mode, hence the name " \
                   "'Oobe'. When this mode is active, you are able to move the camera around with your mouse- " \
                   "though your camera will still follow your Toon."
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT

    def handleWord(self, invoker, avId, toon, *args):
        base.oobe()
        return "Oobe mode has been toggled."


class ToggleRun(MagicWord):
    aliases = ["run"]
    desc = "Toggles run mode, which gives you a faster running speed."
    advancedDesc = "This Magic Word will toggle Run Mode. When this mode is active, the target can run around at a " \
                   "very fast speed."
    execLocation = MagicWordConfig.EXEC_LOC_CLIENT

    def handleWord(self, invoker, avId, toon, *args):
        from direct.showbase.InputStateGlobal import inputState
        inputState.set('debugRunning', not inputState.isSet('debugRunning'))
        return "Run mode has been toggled."

class MaxToon(MagicWord):
    aliases = ["max", "idkfa"]
    desc = "Maxes your target toon."
    execLocation = MagicWordConfig.EXEC_LOC_SERVER
    accessLevel = 'ADMIN'

    def handleWord(self, invoker, avId, toon, *args):
        from toontown.toonbase import ToontownGlobals

        # TODO: Handle this better, like giving out all awards, set the quest tier, stuff like that.
        # This is mainly copied from Anesidora just so I can better work on things.
        toon.b_setTrackAccess([1, 1, 1, 1, 1, 1, 1])

        toon.b_setMaxCarry(ToontownGlobals.MaxCarryLimit)
        toon.b_setQuestCarryLimit(ToontownGlobals.MaxQuestCarryLimit)

        toon.experience.maxOutExp()
        toon.d_setExperience(toon.experience.makeNetString())

        toon.inventory.maxOutInv()
        toon.d_setInventory(toon.inventory.makeNetString())

        toon.b_setMaxHp(ToontownGlobals.MaxHpLimit)
        toon.b_setHp(ToontownGlobals.MaxHpLimit)

        toon.b_setMaxMoney(250)
        toon.b_setMoney(toon.maxMoney)
        toon.b_setBankMoney(toon.maxBankMoney)

        return f"Successfully maxed {toon.getName()}!"

# Instantiate all classes defined here to register them.
# A bit hacky, but better than the old system
for item in list(globals().values()):
    if isinstance(item, type) and issubclass(item, MagicWord):
        i = item()
