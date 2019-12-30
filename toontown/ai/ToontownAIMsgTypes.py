from otp.ai.AIMsgTypes import *
TTAIMsgName2Id = {'DBSERVER_GET_ESTATE': 1040,
 'DBSERVER_GET_ESTATE_RESP': 1041,
 'PARTY_MANAGER_UD_TO_ALL_AI': 1042,
 'IN_GAME_NEWS_MANAGER_UD_TO_ALL_AI': 1043,
 'WHITELIST_MANAGER_UD_TO_ALL_AI': 1044}
TTAIMsgId2Names = invertDictLossless(TTAIMsgName2Id)
if not isClient():
    print('EXECWARNING ToontownAIMsgTypes: %s' % TTAIMsgName2Id)
    printStack()
for name, value in list(TTAIMsgName2Id.items()):
    exec('%s = %s' % (name, value))

del name
del value
DBSERVER_PET_OBJECT_TYPE = 5
