from toontown.toonbase import ToontownGlobals
ALLOW_TEMP_MINIGAMES = simbase.config.GetBool('allow-temp-minigames', False)
TEMP_MG_ID_COUNTER = ToontownGlobals.TravelGameId - 1
TempMgCtors = {}

def _printMessage(message):
    print '\n\n!!!', message, '\n\n'


def _registerTempMinigame(name, Class, id, minPlayers = 1, maxPlayers = 4):
    if not ALLOW_TEMP_MINIGAMES:
        _printMessage('registerTempMinigame WARNING: allow-temp-minigames config is set to false, but we are trying to register temp minigame ' + name)
        import traceback
        traceback.print_stack()
        return
    ToontownGlobals.MinigameIDs += (id,)
    ToontownGlobals.MinigameNames[name] = id
    TempMgCtors[id] = Class
    for i in range(minPlayers, maxPlayers):
        ToontownGlobals.MinigamePlayerMatrix[i] += (id,)

    _printMessage('registerTempMinigame: ' + name)


if ALLOW_TEMP_MINIGAMES:
    pass
