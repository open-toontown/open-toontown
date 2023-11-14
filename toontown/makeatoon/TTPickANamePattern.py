from direct.showbase.PythonUtil import listToItem2index
from otp.namepanel.PickANamePattern import PickANamePatternTwoPartLastName
from toontown.makeatoon.NameGenerator import NameGenerator
import types

class TTPickANamePattern(PickANamePatternTwoPartLastName):
    NameParts = None
    LastNamePrefixesCapped = None

    def _getNameParts(self):
        if TTPickANamePattern.NameParts is None:
            TTPickANamePattern.NameParts = {}
            ng = NameGenerator()
            TTPickANamePattern.NameParts['n'] = ng.getAllNameParts()
        return TTPickANamePattern.NameParts['n']

    def _getLastNameCapPrefixes(self):
        if TTPickANamePattern.LastNamePrefixesCapped is None:
            ng = NameGenerator()
            TTPickANamePattern.LastNamePrefixesCapped = ng.getLastNamePrefixesCapped()[:]
        return TTPickANamePattern.LastNamePrefixesCapped
