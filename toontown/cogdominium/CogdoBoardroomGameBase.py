from toontown.cogdominium import CogdoBoardroomGameConsts as Consts
from toontown.cogdominium import CogdoBoardroomGameSpec


class CogdoBoardroomGameBase:

    def getConsts(self):
        return Consts

    def getSpec(self):
        return CogdoBoardroomGameSpec
