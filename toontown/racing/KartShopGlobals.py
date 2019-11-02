from direct.showbase import PythonUtil

class KartShopGlobals:
    EVENTDICT = {'guiDone': 'guiDone',
     'returnKart': 'returnKart',
     'buyKart': 'buyAKart',
     'buyAccessory': 'buyAccessory'}
    KARTCLERK_TIMER = 180
    MAX_KART_ACC = 16


class KartGlobals:
    ENTER_MOVIE = 1
    EXIT_MOVIE = 2
    COUNTDOWN_TIME = 30
    BOARDING_TIME = 10.0
    ENTER_RACE_TIME = 6.0
    ERROR_CODE = PythonUtil.Enum('success, eGeneric, eTickets, eBoardOver, eNoKart, eOccupied, eTrackClosed, eTooLate, eUnpaid')
    FRONT_LEFT_SPOT = 0
    FRONT_RIGHT_SPOT = 1
    REAR_LEFT_SPOT = 2
    REAR_RIGHT_SPOT = 3
    PAD_GROUP_NUM = 4

    def getPadLocation(padId):
        return padId % KartGlobals.PAD_GROUP_NUM

    getPadLocation = staticmethod(getPadLocation)
