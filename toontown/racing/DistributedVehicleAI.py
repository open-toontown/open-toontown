from otp.ai.AIBase import *
from toontown.toonbase.ToontownGlobals import *
from toontown.racing.KartDNA import *

from direct.distributed.ClockDelta import *

from direct.distributed import DistributedSmoothNodeAI
from direct.fsm import FSM
from direct.task import Task

if( __debug__ ):
    import pdb

class DistributedVehicleAI(DistributedSmoothNodeAI.DistributedSmoothNodeAI, FSM.FSM):
    
    notify = DirectNotifyGlobal.directNotify.newCategory("DistributedVehicleAI")
    
    def __init__(self, air, avId):
        """__init__(air)
        """
        assert self.notify.debug("__init__ avId = %d" % avId)
        self.ownerId = avId
        
        DistributedSmoothNodeAI.DistributedSmoothNodeAI.__init__(self, air)
        FSM.FSM.__init__(self, 'DistributedVehicleAI')

        
        self.driverId = 0

        # Initialize default Kart DNA List, then update it based on the
        # actual DNA found on the distributed toon.
        self.kartDNA = [ -1 ] * ( getNumFields() )
        
        self.__initDNA()        
        self.request("Off")
        
    def generate(self):
        DistributedSmoothNodeAI.DistributedSmoothNodeAI.generate(self)
        
    def delete(self):
        assert self.notify.debug("delete %d" % self.doId)
        DistributedSmoothNodeAI.DistributedSmoothNodeAI.delete(self)

    # setState()

    def __initDNA( self ):
        """
        Purpose:

        Params:
        Return:
        """

        # Retrieve the Distributed Object of the owner in order to set
        # each of the kart dna fields.
        owner = self.air.doId2do.get( self.ownerId )
        if( owner ):
            # If new DNA fields are added, update here as well.
            self.kartDNA[ KartDNA.bodyType ] = owner.getKartBodyType()
            self.kartDNA[ KartDNA.bodyColor ] = owner.getKartBodyColor()
            self.kartDNA[ KartDNA.accColor ] = owner.getKartAccessoryColor()
            self.kartDNA[ KartDNA.ebType ] = owner.getKartEngineBlockType()
            self.kartDNA[ KartDNA.spType ] = owner.getKartSpoilerType()
            self.kartDNA[ KartDNA.fwwType ] = owner.getKartFrontWheelWellType()
            self.kartDNA[ KartDNA.bwwType ] = owner.getKartBackWheelWellType()
            self.kartDNA[ KartDNA.rimsType ] = owner.getKartRimType()
            self.kartDNA[ KartDNA.decalType ] = owner.getKartDecalType()

        else:
            self.notify.warning( "__initDNA - OWNER %s OF KART NOT FOUND!" % ( self.ownerId ) )


            

    def d_setState(self, state, avId):
        assert self.notify.debug("d_setState %s %d" % (state,avId))
        self.sendUpdate('setState', [state, avId])

    def requestControl(self):
        assert self.notify.debug("requestControl %d" % self.doId)
        # A client wants to start controlling the car.
        avId = self.air.getAvatarIdFromSender()
        
        #if avId == self.ownerId and self.driverId == 0:
        if self.driverId == 0:
            self.request('Controlled', avId)

    def requestParked(self):
        assert self.notify.debug("requestParked %d" % self.doId)        
        # A client wants to stop controlling the car.
        avId = self.air.getAvatarIdFromSender()

        if avId == self.driverId:
            self.request('Parked')

    ### How you start up the vehicle ###
    def start(self):
        assert self.notify.debug("start %d" % self.doId)        
        self.request('Parked')

    # Specific State functions

    ##### off state #####

    def enterOff(self):
        assert self.notify.debug("enterOff ownerId = %d" % self.ownerId)        
        return None

    def exitOff(self):
        assert self.notify.debug("exitOff ownerId= %d" % self.ownerId)        
        return None

    ##### Parked state #####

    def enterParked(self):
        assert self.notify.debug("enterParked %d" % self.doId)        
        self.driverId = 0
        self.d_setState("P", 0)
        return None

    def exitParked(self):
        assert self.notify.debug("exitParked %d" % self.doId)        
        return None

    ##### Controlled state #####

    def enterControlled(self, avId):
        assert self.notify.debug("enterControllled %d" % self.doId)        
        self.driverId = avId
        fieldList = [
        "setComponentL",
        "setComponentX",
        "setComponentY",
        "setComponentZ",
        "setComponentH",
        "setComponentP",
        "setComponentR",
        "setComponentT",
        "setSmStop",
        "setSmH",
        "setSmZ",
        "setSmXY",
        "setSmXZ",
        "setSmPos",
        "setSmHpr",
        "setSmXYH",
        "setSmXYZH",
        "setSmPosHpr",
        "setSmPosHprL",
        "clearSmoothing", 
        "suggestResync",
        "returnResync",
        ]
        #import pdb; pdb.set_trace()
        self.air.setAllowClientSend(avId, self, fieldNameList = fieldList)
        self.d_setState("C", self.driverId)


    def exitControlled(self):
        assert self.notify.debug("exitControlled %d" % self.doId)        
        pass


        
    def __handleUnexpectedExit(self):
        self.notify.warning('toon: %d exited unexpectedly, resetting vehicle %d' % (self.driverId, self.doId))
        self.request("Parked")
        self.requestDelete()

    def getBodyType( self ):
        """
        Purpose: The getBodyType Method obtains the local AI side
        body type of the kart that the toon currently owns.
        
        Params: None
        Return: bodyType - the body type of the kart.
        """
        return self.kartDNA[ KartDNA.bodyType ]

    def getBodyColor( self ):
        """
        Purpose: The getBodyColor Method obtains the current
        body color of the kart.
        
        Params: None
        Return: bodyColor - the color of the kart body.
        """
        return self.kartDNA[ KartDNA.bodyColor ]

    def getAccessoryColor( self ):
        """
        Purpose: The getAccessoryColor Method obtains the
        accessory color for the kart.
        
        Params: None
        Return: accColor - the color of the accessories
        """
        return self.kartDNA[ KartDNA.accColor ]

    def getEngineBlockType( self ):
        """
        Purpose: The getEngineBlockType Method obtains the engine
        block type accessory for the kart by accessing the
        current Kart DNA.
        
        Params: None
        Return: ebType - the type of engine block accessory.
        """
        return self.kartDNA[ KartDNA.ebType ]

    def getSpoilerType( self ):
        """
        Purpose: The getSpoilerType Method obtains the spoiler
        type accessory for the kart by accessing the current Kart DNA.
        
        Params: None
        Return: spType - the type of spoiler accessory 
        """
        return self.kartDNA[ KartDNA.spType ]

    def getFrontWheelWellType( self ):
        """
        Purpose: The getFrontWheelWellType Method obtains the
        front wheel well accessory for the kart accessing the
        Kart DNA.
        
        Params: None
        Return: fwwType - the type of Front Wheel Well accessory
        """
        return self.kartDNA[ KartDNA.fwwType ]
    
    def getBackWheelWellType( self ):
        """
        Purpose: The getWheelWellType Method gets the Back
        Wheel Wheel accessory for the kart by updating the Kart DNA.
        
        Params: bwwType - the type of Back Wheel Well accessory.
        Return: None
        """
        return self.kartDNA[ KartDNA.bwwType ]

    def getRimType( self ):
        """
        Purpose: The setRimType Method sets the rims accessory
        for the karts tires by accessing the Kart DNA.
        
        Params: None
        Return: rimsType - the type of rims for the kart tires.
        """
        return self.kartDNA[ KartDNA.rimsType ]

    def getDecalType( self ):
        """
        Purpose: The getDecalType Method obtains the decal
        accessory of the kart by accessing the Kart DNA.
        
        Params: None
        Return: decalType - the type of decal set for the kart.
        """
        return self.kartDNA[ KartDNA.decalType ]

    def getOwner(self):
        return self.ownerId
    
