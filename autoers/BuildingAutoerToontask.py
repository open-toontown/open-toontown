from toontown.town import Street
from toontown.toon import HealthForceAcknowledge
from toontown.safezone import *
from toontown.toonbase import ToontownBattleGlobals
from toontown.battle import DistributedBattleBldg
from toontown.building import SuitInterior
from toontown.building import DistributedBuilding
from toontown.building import DistributedElevatorExt
from toontown.building import DistributedSuitInterior
from direct.interval.IntervalGlobal import *

ToontownBattleGlobals.SkipMovie=1

faceOffHook = lambda self, ts, name, callback:self._DistributedBattleBldg__handleFaceOffDone()
DistributedBattleBldg.DistributedBattleBldg._DistributedBattleBldg__faceOff = faceOffHook

class BuildingAutoer:
    oldTeleportInStreet=Street.Street.exitTeleportIn
    
    oldExitBecomingToon=DistributedBuilding.DistributedBuilding.exitBecomingToon
    oldEnterHealth=HealthForceAcknowledge.HealthForceAcknowledge.enter
    oldEnterElevator=DistributedSuitInterior.DistributedSuitInterior.enterElevator
    oldEnterFloorReward=DistributedBattleBldg.DistributedBattleBldg.enterReward
    oldEnterBuildingReward=DistributedBattleBldg.DistributedBattleBldg.enterBuildingReward
    
    def __init__(self):
        Street.Street.exitTeleportIn=lambda newSelf,*args,**kwds: self.newTeleportInStreet(newSelf,*args,**kwds)
        
        DistributedBuilding.DistributedBuilding.exitBecomingToon=lambda newSelf: self.newExitBecomingToon(newSelf)
        DistributedSuitInterior.DistributedSuitInterior.enterElevator=lambda newSelf,*args: self.newEnterElevator(newSelf,*args)
        DistributedBattleBldg.DistributedBattleBldg.enterReward=lambda newSelf,*args: self.newEnterFloorReward(newSelf,*args)
        DistributedBattleBldg.DistributedBattleBldg.enterBuildingReward=lambda newSelf,*args: self.newEnterBuildingReward(newSelf,*args)
        HealthForceAcknowledge.HealthForceAcknowledge.enter=lambda newSelf,hplevel: self.newEnterHealth(newSelf,hplevel)
        self.attackSeq=Sequence(Func(self.attack),Wait(1),Func(self.restock),Wait(1))
        self.invisibleSeq=Sequence(Func(base.localAvatar.d_setParent,1),Wait(1))
        self.shouldChangeDistrict=True
        self.shouldChangeStreet=True
        self.shouldChangeHood=False
        self.shouldContinue=False
        self.shouldStop=False
        self.findDistrictIds()
        self.buildingLevel=1
        self.buildingType=''
        self.foundElevator=False
        self.bldgCount=0
        self.hoods=['1','3','4','5','9']
        self.lastElevator=None
        self.killElevators=[]
        self.gagshop_zoneId = 4503
        self.firstTrack=0
        self.secondTrack=4
        self.thirdTrack=2

        self.desiredLevel1=4
        self.desiredLevel2=5
        self.desiredLevel3=5
            
        
    
    def newEnterHealth(self,newSelf,hplevel):
        try:
            self.oldEnterHealth(newSelf,hplevel)
            newSelf.handleOk(base.localAvatar.getHp())
            newSelf.exit()
            if self.shouldContinue:
                Sequence(Wait(2),Func(self.teleportBackToStreet)).start()
        except:
            pass
    
    def createInventory(self):
        desiredInv=""
        for i in range(7*7):
            if i==((self.firstTrack*7)+self.desiredLevel1):
                if self.firstTrack==1:
                    desiredInv+="\x02"
                elif self.desiredLevel1>3:
                    desiredInv+="\x02"
                else:
                    desiredInv+="\x04"
            elif i==((self.secondTrack*7)+self.desiredLevel2):
                if self.secondTrack==1:
                    desiredInv+="\x02"
                elif self.desiredLevel2>3:
                    desiredInv+="\x02"
                else:
                    desiredInv+="\x04"
            elif i==((self.thirdTrack*7)+self.desiredLevel3) and base.localAvatar.getTrackAccess()[self.thirdTrack]:
                if self.thirdTrack==1:
                    desiredInv+="\x02"
                elif self.desiredLevel3>3:
                    desiredInv+="\x02"
                else:
                    desiredInv+="\x04"
            else:
                desiredInv+="\x00"
        self.desiredInv=desiredInv
    
    def clearSettings(self):
        self.buildingType=''
        self.numFloors=1
        
    def teleportBackToStreet(self):
        print('Teleporting back')
        self.foundElevator=False
        self.walk()
        for treasure in base.cr.doFindAll('Treasure'):
            treasure.sendUpdate('requestGrab')
        base.cr.playGame.getPlace().requestTeleport(round(self.startId,-3),self.startId,None,None)
    
    def findBuilding(self):
        self.checkStop()
        
        if self.shouldContinue:
            for elevator in base.cr.doFindAllInstances(DistributedElevatorExt.DistributedElevatorExt):
                if 'sbfo' not in str(elevator.getElevatorModel()) and 'waitEmpty' in str(elevator.fsm) and elevator.bldg.numFloors>=self.numFloors and self.buildingType in str(elevator.getElevatorModel()) and elevator.doId not in self.killElevators:
                    self.walk()
                    elevator.sendUpdate('requestBoard')
                    self.lastElevator=elevator.doId
                    self.foundElevator=True
                    return
            self.nextZone()
        
    def newTeleportInStreet(self,newSelf,*args,**kwds):
        self.oldTeleportInStreet(newSelf,*args,**kwds)
        self.checkStop()
            
        if self.shouldContinue:
            Sequence(Wait(2),Func(self.findBuilding)).start()
    
    def newExitBecomingToon(self,newSelf):
        self.oldExitBecomingToon(newSelf)
        self.checkStop()
            
        if self.shouldContinue and not self.foundElevator:
            if not taskAutoer.isQuestComplete():
                Sequence(Wait(1),Func(self.findBuilding)).start()
            else:
                self.stop()
                taskAutoer.checkWhatToDo()
            
    def newEnterFloorReward(self,newSelf,*args):
        self.oldEnterFloorReward(newSelf,*args)
        if self.shouldContinue:
            Sequence(Wait(7),Func(self.boardElevator)).start()
    
    def boardElevator(self):
        if self.shouldContinue and base.cr.doFind('Elevator'):
            base.cr.doFind('Elevator').sendUpdate('requestBoard')
            Sequence(Wait(2),Func(base.cr.doFind('Elevator').sendUpdate,'requestExit'),Wait(0.5),Func(base.cr.doFind('Elevator').sendUpdate,'requestBoard')).start()
    
    def newEnterBuildingReward(self,newSelf,*args):
        self.oldEnterBuildingReward(newSelf,*args)
        if self.shouldContinue:
            newSelf._DistributedBattleBldg__handleBuildingRewardDone()
            self.foundElevator=False
            self.bldgCount+=1
    
    def newEnterElevator(self,newSelf,*args):
        self.oldEnterElevator(newSelf,*args)
        if self.shouldContinue:
            newSelf.sendUpdate('elevatorDone', [])
            for x in base.cr.doFindAll('DistributedCogdoInterior'):
                x.sendUpdate('elevatorDone', [])
            
    def checkStop(self):
        if self.shouldStop:
            self.shouldContinue=False
            self.shouldStop=False
            self.attackSeq.finish()
            self.invisibleSeq.finish()
    
    def findDistrictIds(self):
        self.shardIds=[]
        for shard in base.cr.activeDistrictMap:
            if base.cr.activeDistrictMap[shard].avatarCount<50:
                self.shardIds.append(shard)
    
    def nextZone(self):
        try:
            base.cr.playGame.getPlace().enterZone(base.localAvatar.getZoneId()+1)
            Sequence(Wait(0.5),Func(self.findBuilding)).start()
        except KeyError:
            if self.shouldChangeStreet:
                self.newStreet()
            else:
                base.cr.playGame.getPlace().enterZone(self.startId)
                Sequence(Wait(0.5),Func(self.findBuilding)).start()
    
    def checkWhatToDo(self):
        if hasattr(base.cr.playGame.getPlace(),'enterZone') and round(base.localAvatar.getZoneId(),-2)==round(self.startId,-2):
            self.findBuilding()
            
        else:
            if self.startId!=0:
                self.teleportBackToStreet()
            else:
                base.localAvatar.setSystemMessage(0,'The building auto needs to be started on a street')
            
    def newDistrict(self):
        if self.shardIds[0] == base.localAvatar.defaultShard:
            self.shardIds.append(self.shardIds[0])
            del self.shardIds[0]
            
        base.cr.playGame.getPlace().requestTeleport(round(base.localAvatar.getZoneId(),-3),self.startId,self.shardIds[0],None)
        self.shardIds.append(self.shardIds[0])
        del self.shardIds[0]
    
    def newStreet(self):
        todo='street'
        
        if self.startId<9000:
            if int(str(self.startId)[1:])>300:
                if self.shouldChangeDistrict:
                    self.startId-=200
                    todo='district'
                elif self.shouldChangeHood:
                    todo='hood'
                else:
                    self.startId-=200
            else:
                self.startId+=100
                
        elif int(str(self.startId)[1:])>200:
            if self.shouldChangeDistrict:
                self.startId-=100
                todo='district'
                
            elif self.shouldChangeHood:
                todo='hood'
            else:
                self.startId-=100
        else:
            self.startId+=100
        
        if todo=='district':
            self.newDistrict()
        elif todo=='hood':
            Sequence(Wait(3),Func(self.newHood)).start()
        else:
            self.teleportBackToStreet()
    
    def newHood(self):
        if self.hoods[0] == str(base.localAvatar.getZoneId())[0]:
            self.hoods.append(self.hoods[0])
            del self.hoods[0]
            
        self.startId=int(self.hoods[0]+'102')
        self.teleportBackToStreet()
    
    def setLocation(self,zoneId):
        self.startId=int(str(zoneId)[0]+'102')
    
    def setNumFloors(self,numFloors):
        self.numFloors=numFloors
    
    def setBuildingType(self,type):
        if type=='l':
            type='legal'
        elif type=='s':
            type='sales'
        elif type=='m':
            type='money'
        elif type=='c':
            type='corp'
        self.buildingType=type
        
    def workOutStreetId(self):
        zoneId=base.localAvatar.getZoneId()
        self.startId=int(str(zoneId)[:2]+'01')
    
    def loadGagshop(self):           
        if not base.cr.doFind('Clerk'):
            self.contextId = base.cr.addInterest(base.localAvatar.defaultShard, self.gagshop_zoneId, description='4', event=None)
        try:
            if not int(render.find('**/*gagShop_interior_english*').getZ()) == 8**8:
                render.find('**/*gagShop_interior_english*').setZ(8**8)
                for k in base.cr.doFindAll('Clerk'):
                    k.nametag.unmanage(base.marginManager)
        except:
            pass
            
    def buyGags(self):
        desiredInv=self.desiredInv
        try:
            maxCarryGags = base.localAvatar.getMaxCarry()     
            if base.cr.doFind('Clerk'):
                num_gags = 0
                for inventory_number in base.localAvatar.inventory.makeFromNetString(desiredInv):
                    for k in inventory_number[:-1]:
                        num_gags += k
                change = base.localAvatar.getMoney() - num_gags
                oldString = base.localAvatar.inventory.makeNetString()
                newString = desiredInv[:6] + oldString[6] + desiredInv[7:13] + oldString[13] + desiredInv[14:20] + oldString[20] + desiredInv[21:27] + oldString[27] + desiredInv[28:34] + oldString[34] + desiredInv[35:41] + oldString[41] + desiredInv[42:48] + oldString[48]
                for clerk in base.cr.doFindAll('Clerk'):
                    clerk.setMovie=lambda *args,**kwds: None
                    clerk.freeAvatar=lambda *args: None
                    clerk.sendUpdate('avatarEnter')
                for clerk in base.cr.doFindAll('Clerk'):
                    clerk.sendUpdate('setInventory', [newString, change, 1])
                    
                money = base.localAvatar.getMoney()
                maxMoney = base.localAvatar.getMaxMoney()
                try:
                    base.cr.bankManager.d_transferMoney(money - maxMoney)
                except AttributeError:
                    pass
        except:
            pass
    
    def unloadGagshop(self):
        if hasattr(self, 'contextId'):
            try:
                base.cr.removeInterest(self.contextId)
            except:
                pass
        
    def restock(self):
        self.desiredLevel1=base.localAvatar.experience.getExpLevel(self.firstTrack)
        if self.desiredLevel1 in [1,3,5]:
            self.desiredLevel1-=1
        self.desiredLevel2=base.localAvatar.experience.getExpLevel(self.secondTrack)
        self.desiredLevel3=base.localAvatar.experience.getExpLevel(self.thirdTrack)
        if self.desiredLevel1>5:
            self.desiredLevel1=4
        if self.desiredLevel2>5:
            self.desiredLevel2=5
        if self.desiredLevel3>5:
            self.desiredLevel3=5
        self.createInventory()
        if base.localAvatar.inventory.inventory[self.firstTrack][self.desiredLevel1]<2 or base.localAvatar.inventory.inventory[self.secondTrack][self.desiredLevel2]<2 or (base.localAvatar.inventory.inventory[self.thirdTrack][self.desiredLevel3]<2 and base.localAvatar.getTrackAccess()[self.thirdTrack]):
            Sequence(Func(self.loadGagshop),Wait(1),Func(self.buyGags),Wait(0.5),Func(self.unloadGagshop)).start()
        
    def attack(self):
        try:
            for battle in base.cr.doFindAll('battle'):
                if base.localAvatar.getTrackAccess()[2]:
                    if base.localAvatar.inventory.inventory[2][self.desiredLevel3]>0:
                        battle.sendUpdate('requestAttack', [2, self.desiredLevel3, battle.suits[0].doId])
                        battle.sendUpdate('movieDone')
                    else:
                        break
                    
                if base.localAvatar.getHp()<(base.localAvatar.getMaxHp()*0.9):
                
                    if base.localAvatar.inventory.inventory[0][self.desiredLevel1]>0:
                        battle.sendUpdate('requestAttack', [0, self.desiredLevel1, base.localAvatar.doId])
                        battle.sendUpdate('movieDone')
                    else:
                        break
                        
                    if base.localAvatar.inventory.inventory[4][self.desiredLevel2]>0:
                        battle.sendUpdate('requestAttack', [4, self.desiredLevel2, battle.suits[0].doId])
                        battle.sendUpdate('movieDone')
                    else:
                        break
                        
                else:
                    if base.localAvatar.inventory.inventory[4][self.desiredLevel2]>0:
                        battle.sendUpdate('requestAttack', [4, self.desiredLevel2, battle.suits[0].doId])
                        battle.sendUpdate('movieDone')
                    else:
                        break
        except:
            pass
    
    def walk(self):
        try:
            base.cr.playGame.getPlace().fsm.forceTransition('walk')
        except:
            pass
        
    def getBuildingType(self):
        if self.buildingType=='legal':
            return 'Lawbot'
        elif self.buildingType=='sales':
            return 'Sellbot'
        elif self.buildingType=='money':
            return 'Cashbot'
        elif self.buildingType=='corp':
            return 'Bossbot'
        else:
            return 'All'
         
    def getBuildingLevel(self):
        return self.buildingLevel
            
    def start(self):
        print('starting')
        self.shouldContinue=True
        self.shouldStop=False
        self.createInventory()
        self.attackSeq.loop()
        self.invisibleSeq.loop()
        self.checkWhatToDo()
    
    def stop(self):
        self.shouldContinue=False
        self.shouldStop=False
        self.attackSeq.finish()
        self.invisibleSeq.finish()
        
    def revert(self):
        Street.Street.exitTeleportIn=self.oldTeleportInStreet
    
        DistributedBuilding.DistributedBuilding.exitBecomingToon=self.oldExitBecomingToon
        HealthForceAcknowledge.HealthForceAcknowledge.enter=self.oldEnterHealth
        DistributedSuitInterior.DistributedSuitInterior.enterElevator=self.oldEnterElevator
        DistributedBattleBldg.DistributedBattleBldg.enterReward=self.oldEnterFloorReward
        DistributedBattleBldg.DistributedBattleBldg.enterBuildingReward=self.oldEnterBuildingReward
        ToontownBattleGlobals.SkipMovie=0
        self.attackSeq.finish()