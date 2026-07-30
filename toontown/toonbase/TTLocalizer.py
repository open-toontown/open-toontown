from panda3d.core import *

language = ConfigVariableString('language', 'english').value
checkLanguage = ConfigVariableBool('check-language', 0).value

def getLanguage():
    return language


print('TTLocalizer: Running in language: %s' % language)
if language == 'english':
    _languageModule = 'toontown.toonbase.TTLocalizer' + language.capitalize()
else:
    checkLanguage = 1
    _languageModule = 'toontown.toonbase.TTLocalizer_' + language
print('from ' + _languageModule + ' import *')
from toontown.toonbase.TTLocalizerEnglish import *
if checkLanguage:
    l = {}
    g = {}
    englishModule = __import__('toontown.toonbase.TTLocalizerEnglish', g, l)
    foreignModule = __import__(_languageModule, g, l)
    for key, val in list(englishModule.__dict__.items()):
        if key not in foreignModule.__dict__:
            print('WARNING: Foreign module: %s missing key: %s' % (_languageModule, key))
            locals()[key] = val
        elif isinstance(val, dict):
            fval = foreignModule.__dict__.get(key)
            for dkey, dval in list(val.items()):
                if dkey not in fval:
                    print('WARNING: Foreign module: %s missing key: %s.%s' % (_languageModule, key, dkey))
                    fval[dkey] = dval

            for dkey in list(fval.keys()):
                if dkey not in val:
                    print('WARNING: Foreign module: %s extra key: %s.%s' % (_languageModule, key, dkey))

    for key in list(foreignModule.__dict__.keys()):
        if key not in englishModule.__dict__:
            print('WARNING: Foreign module: %s extra key: %s' % (_languageModule, key))
