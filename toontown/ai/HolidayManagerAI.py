class HolidayManagerAI:
    def __init__(self, air):
        self.air = air
        self.currentHolidays = {}

    def isHolidayRunning(self, holidayId):
        return False  # NO
