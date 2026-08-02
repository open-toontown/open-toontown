from toontown.util.astron.AstronStruct import AstronStruct
import json


class AstronDict(dict, AstronStruct):

    def toStruct(self):
        return [json.dumps(self)]

    @classmethod
    def fromStruct(cls, struct):
        if not struct[0]:
            return cls()
        return cls(json.loads(struct[0]))

    @classmethod
    def fromDict(cls, d: dict):
        return cls(d)
