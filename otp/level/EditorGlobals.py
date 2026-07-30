from direct.showbase.PythonUtil import uniqueElements
EditTargetPostName = 'inGameEditTarget'
EntIdRange = 10000
username2entIdBase = {'darren': 1 * EntIdRange,
 'samir': 2 * EntIdRange,
 'skyler': 3 * EntIdRange,
 'joe': 4 * EntIdRange,
 'DrEvil': 5 * EntIdRange,
 'asad': 6 * EntIdRange,
 'drose': 7 * EntIdRange,
 'pappy': 8 * EntIdRange,
 'patricia': 9 * EntIdRange,
 'jloehrle': 10 * EntIdRange,
 'rurbino': 11 * EntIdRange}
usernameConfigVar = 'level-edit-username'
undefinedUsername = 'UNDEFINED_USERNAME'
editUsername = config.GetString(usernameConfigVar, undefinedUsername)

def checkNotReadyToEdit():
    if editUsername == undefinedUsername:
        return "you must config '%s'; see %s.py" % (usernameConfigVar, __name__)
    if editUsername not in username2entIdBase:
        return "unknown editor username '%s'; see %s.py" % (editUsername, __name__)
    return None


def assertReadyToEdit():
    msg = checkNotReadyToEdit()
    if msg is not None:
        pass
    return


def getEditUsername():
    return editUsername


def getEntIdAllocRange():
    baseId = username2entIdBase[editUsername]
    return [baseId, baseId + EntIdRange]
