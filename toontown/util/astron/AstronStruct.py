class AstronStruct:

    def toStruct(self):
        raise NotImplementedError

    @classmethod
    def fromStruct(cls, struct):
        if struct:
            return cls(*struct)
        else:
            return cls()

    @staticmethod
    def toStructList(astronStructs):
        return [astronStruct.toStruct() for astronStruct in astronStructs]

    @classmethod
    def fromStructList(cls, struct):
        return [cls.fromStruct(substruct) for substruct in struct]
