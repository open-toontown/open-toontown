from direct.directnotify import DirectNotifyGlobal
from toontown.ai import HolidayBaseAI
from . import SuitInvasionManagerAI
from toontown.toonbase import ToontownGlobals

class HolidaySuitInvasionManagerAI(HolidayBaseAI.HolidayBaseAI):

    notify = DirectNotifyGlobal.directNotify.newCategory('HolidaySuitInvasionManagerAI')
    
    def __init__(self, air, holidayId):
        HolidayBaseAI.HolidayBaseAI.__init__(self, air, holidayId)

    def start(self):
        # Stop any current invasion that might be happening by chance
        if self.air.suitInvasionManager.getInvading():
            self.notify.info("Stopping current invasion to make room for holiday %s" %
                             (self.holidayId))
            self.air.suitInvasionManager.stopInvasion()
            
        if not simbase.config.GetBool('want-invasions', 1):
            return 1
            
        if (self.holidayId == ToontownGlobals.HALLOWEEN):
            # Bloodsucker invasion on Halloween
            cogType = 'b'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0
        elif (self.holidayId == ToontownGlobals.SKELECOG_INVASION):
            # any cog will do
            from . import SuitDNA
            import random
            cogType = random.choice(SuitDNA.suitHeadTypes) 
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 1
        elif (self.holidayId == ToontownGlobals.MR_HOLLYWOOD_INVASION):
            # Mr. Hollywood of course...
            cogType = 'mh'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0
        elif (self.holidayId == ToontownGlobals.BOSSCOG_INVASION):
            # any cog will do
            from . import SuitDNA
            import random
            cogType = SuitDNA.getRandomSuitByDept('c')
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0
        elif (self.holidayId == ToontownGlobals.MARCH_INVASION):
            # Backstabbers...
            cogType = 'bs'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0
        elif (self.holidayId == ToontownGlobals.DECEMBER_INVASION):
            # Sellbots...
            cogType = 'cc'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0
        elif (self.holidayId == ToontownGlobals.SELLBOT_SURPRISE_1):
            # Sellbot Surprise... cold caller
            cogType = 'cc'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0
        elif (self.holidayId == ToontownGlobals.SELLBOT_SURPRISE_2 or \
                self.holidayId == ToontownGlobals.NAME_DROPPER_INVASION):
            # Sellbot Surprise ... Name dropper
            cogType = 'nd'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0
        elif (self.holidayId == ToontownGlobals.SELLBOT_SURPRISE_3):
            # Sellbot Surprise ... gladhander
            cogType = 'gh'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0
        elif (self.holidayId == ToontownGlobals.SELLBOT_SURPRISE_4 or \
                self.holidayId == ToontownGlobals.MOVER_AND_SHAKER_INVASION):
            # Sellbot Surprise ... mover & shaker
            cogType = 'ms'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0
        elif (self.holidayId == ToontownGlobals.CASHBOT_CONUNDRUM_1):
            # Cashbot Conundrum... Short Change
            cogType = 'sc'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0
        elif (self.holidayId == ToontownGlobals.CASHBOT_CONUNDRUM_2 or \
            self.holidayId == ToontownGlobals.PENNY_PINCHER_INVASION):
            # Cashbot Conundrum... Penny Pincher
            cogType = 'pp'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0
        elif (self.holidayId == ToontownGlobals.CASHBOT_CONUNDRUM_3):
            # Cashbot Conundrum... Bean Counter
            cogType = 'bc'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0
        elif (self.holidayId == ToontownGlobals.CASHBOT_CONUNDRUM_4 or \
            self.holidayId == ToontownGlobals.NUMBER_CRUNCHER_INVASION):
            # Cashbot Conundrum... Number Cruncher
            cogType = 'nc'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0
        elif (self.holidayId == ToontownGlobals.LAWBOT_GAMBIT_1):
            # Lawbot Gambit... bottom feeder
            cogType = 'bf'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0
        elif (self.holidayId == ToontownGlobals.LAWBOT_GAMBIT_2 or \
            self.holidayId == ToontownGlobals.DOUBLE_TALKER_INVASION):
            # Lawbot Gambit... double talker
            cogType = 'dt'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0
        elif (self.holidayId == ToontownGlobals.LAWBOT_GAMBIT_3 or \
            self.holidayId == ToontownGlobals.AMBULANCE_CHASER_INVASION):
            # Lawbot Gambit... ambulance chaser
            cogType = 'ac'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0
        elif (self.holidayId == ToontownGlobals.LAWBOT_GAMBIT_4):
            # Lawbot Gambit... back stabber
            cogType = 'bs'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0
        elif (self.holidayId == ToontownGlobals.TROUBLE_BOSSBOTS_1):
            # The Trouble with Bossbots ... flunky
            cogType = 'f'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0
        elif (self.holidayId == ToontownGlobals.TROUBLE_BOSSBOTS_2):
            # The Trouble with Bossbots ... pencil pusher
            cogType = 'p'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0
        elif (self.holidayId == ToontownGlobals.TROUBLE_BOSSBOTS_3 or \
            self.holidayId == ToontownGlobals.MICROMANAGER_INVASION):
            # The Trouble with Bossbots ... micro manager
            cogType = 'mm'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0
        elif (self.holidayId == ToontownGlobals.TROUBLE_BOSSBOTS_4 or \
                self.holidayId == ToontownGlobals.DOWN_SIZER_INVASION ):
            # The Trouble with Bossbots ... downsizer
            cogType = 'ds'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0
        elif (self.holidayId == ToontownGlobals.COLD_CALLER_INVASION):
            cogType = 'cc'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0
        elif (self.holidayId == ToontownGlobals.BEAN_COUNTER_INVASION):
            cogType = 'bc'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0
        elif (self.holidayId == ToontownGlobals.DOUBLE_TALKER_INVASION):
            # The Trouble with Bossbots ... downsizer
            cogType = 'dt'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0
        elif (self.holidayId == ToontownGlobals.DOWNSIZER_INVASION):
            # The Trouble with Bossbots ... downsizer
            cogType = 'ds'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0               
        elif (self.holidayId == ToontownGlobals.YES_MAN_INVASION):
            # The Trouble with Bossbots ... yes man
            cogType = 'ym'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0      
        elif (self.holidayId == ToontownGlobals.TIGHTWAD_INVASION):
            # tightwad
            cogType = 'tw'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0   
        elif (self.holidayId == ToontownGlobals.TELEMARKETER_INVASION):
            # telemarketer
            cogType = 'tm'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0  
        elif (self.holidayId == ToontownGlobals.HEADHUNTER_INVASION):
            # head hunter
            cogType = 'hh'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0  
        elif (self.holidayId == ToontownGlobals.SPINDOCTOR_INVASION):
            # spin doctor
            cogType = 'sd'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0  
        elif (self.holidayId == ToontownGlobals.MONEYBAGS_INVASION):
            # money bags
            cogType = 'mb'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0  
        elif (self.holidayId == ToontownGlobals.TWOFACES_INVASION):
            # two faces
            cogType = 'tf'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0 
        elif (self.holidayId == ToontownGlobals.MINGLER_INVASION):
            # mingler
            cogType = 'm'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0  
        elif (self.holidayId == ToontownGlobals.LOANSHARK_INVASION):
            # loan sharks
            cogType = 'ls'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0  
        elif (self.holidayId == ToontownGlobals.CORPORATE_RAIDER_INVASION):
            # corporate raider
            cogType = 'cr'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0  
        elif (self.holidayId == ToontownGlobals.LEGAL_EAGLE_INVASION):
            # legal eagle
            cogType = 'le'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0  
        elif (self.holidayId == ToontownGlobals.ROBBER_BARON_INVASION):
            # robber baron
            cogType = 'rb'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0  
        elif (self.holidayId == ToontownGlobals.BIG_WIG_INVASION):
            # big wig
            cogType = 'bw'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0  
        elif (self.holidayId == ToontownGlobals.BIG_CHEESE_INVASION):
            # big cheese
            cogType = 'tbc'
            # Max the number so they will not run out
            numCogs = 1000000000
            skeleton = 0  
        else:
            self.notify.warning("Unrecognized holidayId: %s" % (self.holidayId))
            return 0
        
        self.air.suitInvasionManager.startInvasion(cogType, numCogs, skeleton)
        self.air.suitInvasionManager.waitForNextInvasion()
        return 1
                        
    def stop(self):
        # Holiday is over, stop the invasion if it happens to still be running
        if self.air.suitInvasionManager.getInvading():
            self.notify.info("Prematurely stopping holiday invasion: %s" % (self.holidayId))
            self.air.suitInvasionManager.stopInvasion()
