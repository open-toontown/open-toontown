from direct.directnotify import DirectNotifyGlobal


class PetManagerAI:
    notify = DirectNotifyGlobal.directNotify.newCategory('PetManagerAI')

    def __init__(self, air):
        self.air = air

    def getAvailablePets(self, *args, **kwargs):
        return []
