from toontown.cogdominium import CogdoCraneGameSpec
from toontown.cogdominium import CogdoCraneGameConsts as Consts

class CogdoCraneGameBase:

    def getConsts(self):
        return Consts

    def getSpec(self):
        return CogdoCraneGameSpec
