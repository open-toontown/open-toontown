from direct.directnotify import DirectNotifyGlobal


class CogPageManagerAI:
    notify = DirectNotifyGlobal.directNotify.newCategory('CogPageManagerAI')

    def __init__(self, air):
        self.air = air

    def toonKilledCogs(self, toon, suitsKilled, zoneId):
        pass  # TODO

    def toonEncounteredCogs(self, toon, suitsEncountered, zoneId):
        pass  # TODO
