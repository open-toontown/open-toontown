from direct.directnotify import DirectNotifyGlobal
import random
from direct.task import Task
from toontown.effects import DistributedFireworkShowAI

class HolidayBaseAI:
    """
    Base class for all holidays
    """

    def __init__(self, air, holidayId):
        self.air = air
        self.holidayId = holidayId

    def start(self):
        pass

    def stop(self):
        pass


        
