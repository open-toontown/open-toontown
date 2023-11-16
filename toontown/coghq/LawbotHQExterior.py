from panda3d.core import *

from direct.directnotify import DirectNotifyGlobal
from direct.fsm import ClassicFSM, State

from toontown.battle import BattlePlace
from toontown.building import Elevator
from toontown.coghq import CogHQExterior
from toontown.toonbase import ToontownGlobals


class LawbotHQExterior(CogHQExterior.CogHQExterior):
    notify = DirectNotifyGlobal.directNotify.newCategory('LawbotHQExterior')
