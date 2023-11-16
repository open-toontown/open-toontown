import random

from direct.directnotify import DirectNotifyGlobal
from direct.task import Task

from toontown.effects import DistributedFireworkShowAI


class HolidayBaseAI:

    def __init__(self, air, holidayId):
        self.air = air
        self.holidayId = holidayId

    def start(self):
        pass

    def stop(self):
        pass
