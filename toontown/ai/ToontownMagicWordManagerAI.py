from direct.directnotify import DirectNotifyGlobal
from otp.ai.MagicWordManagerAI import MagicWordManagerAI

class ToontownMagicWordManagerAI(MagicWordManagerAI):
    notify = DirectNotifyGlobal.directNotify.newCategory("ToontownMagicWordManagerAI")

    def requestTeleport(self, todo0, todo1, todo2, todo3, todo4):
        pass

