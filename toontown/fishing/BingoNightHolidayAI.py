#################################################################
# class: BingoNightHolidayAI.py
#
# Purpose: Manages the Bingo Night Holiday for all ponds in all
#          hoods.
# Note: The Holiday Manager System(HMS) deletes each Holiday AI 
#       instance when the particular Holiday Expires. Unfortunately,this
#       sort of functionality is not ideal for the BingoManagerAI
#       class because we want to allow players to finish a final
#       game of bingo before the BingoManagerAI shuts down. 
#
#       In order to prevent the BingoManagerAI from shutting down
#       unexpectantly in the middle of a game, we provide this
#       class to act as a "buffer" between the HSM
#       and the BingoManagerAI. This class is created
#       and destroyed by the HMS. When the HMS tells this class
#       to start, it instantiates a BingoManagerAI object to
#       run the actual Bingo Night Holiday.
#
#       When the stop call is received, it tells the BingoManagerAI
#       to stop after the next game and then it removes the reference
#       to the BingoManagerAI. A reference to the BingoManagerAI still
#       remains in the AIR so that the BingoManagerAI can finish
#       the final Bingo Night Games before it deletes itself.
#################################################################

#################################################################
# Direct Specific Modules
#################################################################
from direct.directnotify import DirectNotifyGlobal
from otp.otpbase import PythonUtil
from direct.task import Task

#################################################################
# Toontown Specific Modules
#################################################################
from toontown.ai import HolidayBaseAI
from toontown.fishing import BingoGlobals
from toontown.fishing import BingoManagerAI

#################################################################
# Python Specific Modules
#################################################################
import time

class BingoNightHolidayAI(HolidayBaseAI.HolidayBaseAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('BingoNightHolidayAI')
    ############################################################
    # Method:  __init__
    # Purpose: This method initializes the HolidayBaseAI
    #          base class.
    # Input: air - The AI Repository.
    # Output: None
    ############################################################
    def __init__(self, air, holidayId):
        HolidayBaseAI.HolidayBaseAI.__init__(self, air, holidayId)

    ############################################################
    # Method:  start
    # Purpose: This method instantiates a BingoManagerAI and
    #          tells it to start up bingo night.
    # Input: None
    # Output: None
    ############################################################
    def start(self):

        if self.air.bingoMgr:
            raise PythonUtil.SingletonError("Bingo Manager already Exists! DO NOT RUN HOLIDAY!!")
        else:
            self.notify.info('Starting BingoNight Holiday: %s' % (time.ctime()))
            self.bingoMgr = BingoManagerAI.BingoManagerAI(self.air)
            self.bingoMgr.start()
                                
    ############################################################
    # Method:  start
    # Purpose: This method tells the BingoManagerAI to shutdown
    #          and removes the reference. The BingoManagerAI
    #          does not actually shutdown until it finish all
    #          the PBMgrAIs have done so. The AIR maintains a
    #          reference to the BingoManagerAI so this method
    #          does not actually delete it.
    # Input: None
    # Output: None
    ############################################################
    def stop(self):
        if self.bingoMgr:
            self.notify.info('stop: Tell the BingoManagerAI to stop BingoNight Holiday - %s' %(time.ctime()))
            self.bingoMgr.stop()
            del self.bingoMgr
