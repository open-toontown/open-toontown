from direct.directnotify import DirectNotifyGlobal


class QuestManagerAI:
    notify = DirectNotifyGlobal.directNotify.newCategory('QuestManagerAI')

    def __init__(self, air):
        self.air = air

    def recoverItems(self, toon, suitsKilled, zoneId):
        return [], []  # TODO

    def toonKilledCogs(self, toon, suitsKilled, zoneId, activeToonList):
        pass  # TODO

    def requestInteract(self, avId, npc):
        npc.rejectAvatar(avId)  # TODO

    def hasTailorClothingTicket(self, toon, npc):
        return 0  # TODO

    def toonKilledBuilding(self, toon, track, difficulty, numFloors, zoneId, activeToons):
        pass  # TODO

    def toonKilledCogdo(self, toon, difficulty, numFloors, zoneId, activeToons):
        pass  # TODO

    def toonPlayedMinigame(self, toon, toons):
        pass  # TODO

    def toonRecoveredCogSuitPart(self, av, zoneId, avList):
        pass  # TODO

    def toonDefeatedFactory(self, toon, factoryId, activeVictors):
        pass  # TODO

    def toonDefeatedMint(self, toon, mintId, activeVictors):
        pass  # TODO

    def toonDefeatedStage(self, toon, stageId, activeVictors):
        pass  # TODO
