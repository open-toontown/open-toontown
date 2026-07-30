from . import Street


class DDStreet(Street.Street):

    def __init__(self, loader, parentFSM, doneEvent):
        Street.Street.__init__(self, loader, parentFSM, doneEvent)

    def load(self):
        Street.Street.load(self)

    def unload(self):
        Street.Street.unload(self)

    def enter(self, requestStatus):
        self.loader.hood.setWhiteFog()
        Street.Street.enter(self, requestStatus)

    def exit(self):
        self.loader.hood.setNoFog()
        Street.Street.exit(self)
