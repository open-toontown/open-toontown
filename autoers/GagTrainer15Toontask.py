import random
import __main__
from toontown.battle import BattlePlace
from toontown.safezone import *
from toontown.toonbase import ToontownBattleGlobals
from toontown.safezone import Playground
from toontown.suit import DistributedSuit
from toontown.suit import SuitDNA
from toontown.toon import HealthForceAcknowledge
from toontown.battle import DistributedBattle
from toontown.distributed import ToontownClientRepository
from toontown.effects import DistributedFireworkShow
for attribute in dir(DistributedFireworkShow.DistributedFireworkShow):
    exec('DistributedFireworkShow.DistributedFireworkShow.'+attribute+'=lambda *args,**kwds: None')

ToontownBattleGlobals.SkipMovie=1
oldDumpShards=ToontownClientRepository.ToontownClientRepository.dumpAllSubShardObjects
def newDumpShards(self):
    try:
        oldDumpShards(self)
    except:
        pass
ToontownClientRepository.ToontownClientRepository.dumpAllSubShardObjects=newDumpShards
    
suitToDamage={1:4,2:6,3:9,4:13,5:15,6:19,7:22,8:25,9:27,10:29,11:30,12:40}

faceOffHook = lambda self, ts, name, callback:self.d_faceOffDone(self)
DistributedBattle.DistributedBattle._DistributedBattle__faceOff = faceOffHook

oldHandleEnterCollisionSphereParty=DistributedNPCPartyPerson.DistributedNPCPartyPerson.handleCollisionSphereEnter
DistributedNPCPartyPerson.DistributedNPCPartyPerson.handleCollisionSphereEnter=lambda *args: None
oldHandleEnterCollisionSphereFisherman=DistributedNPCFisherman.DistributedNPCFisherman.handleCollisionSphereEnter
DistributedNPCFisherman.DistributedNPCFisherman.handleEnterCollisionSphere=lambda *args: None

hooks='''
try:
    _announceGenerate1
except:
    _announceGenerate1 = DistributedDoor.DistributedDoor.announceGenerate
def announceGenerate(self):
    try:
        _announceGenerate1(self)
    except:
        return None
DistributedDoor.DistributedDoor.announceGenerate = announceGenerate
try:
    _announceGenerate2
except:
    _announceGenerate2 = DistributedPartyGate.DistributedPartyGate.announceGenerate
def announceGenerate(self):
    try:
        _announceGenerate2(self)
    except:
        return None
DistributedPartyGate.DistributedPartyGate.announceGenerate = announceGenerate
try:
    old__init__
except:
    old__init__ = DistributedTrolley.DistributedTrolley.__init__
def new__init__(self, cr):
    for obj in dir(self):
        exec('self.%s = lambda *x:None' % obj, globals(), locals())
    return None
DistributedTrolley.DistributedTrolley.__init__ = new__init__
try:
    old__init__2
except:
    old__init__2 = DistributedPartyGate.DistributedPartyGate.__init__
def new__init__2(self, cr):
    for obj in dir(self):
        exec('self.%s = lambda *x:None' % obj, globals(), locals())
    return None
DistributedPartyGate.DistributedPartyGate.__init__ = new__init__2
try:
    old__init__3
except:
    old__init__3 = DistributedDoor.DistributedDoor.__init__
def new__init__3(self, cr):
    for obj in dir(self):
        exec('self.%s = lambda *x:None' % obj, globals(), locals())
    return None
DistributedDoor.DistributedDoor.__init__ = new__init__3
try:
    old__init__4
except:
    old__init__4 = DistributedPicnicBasket.DistributedPicnicBasket.__init__
def new__init__4(self, cr):
    for obj in dir(self):
        exec('self.%s = lambda *x:None' % obj, globals(), locals())
    return None
DistributedPicnicBasket.DistributedPicnicBasket.__init__ = new__init__4
base.localAvatar.stopLookAroundNow()
base.localAvatar.findSomethingToLookAt = lambda *x:None
ToonHead.ToonHead._ToonHead__lookAround = lambda *x:None
'''


class Inventory:

    def __init__(self):
        self.firstTrack=4
        self.secondTrack=5
        self.useOwnLevels=False
        self.firstTrackLevel=0
        self.secondTrackLevel=0
        self.noTrolley=False
        self.inBattle=False
        
    def getInv(self,command):
        if command=="get1":
            try:
                return self.firstTrack
            except:
                return 4
        elif command=="get2":
            try:
                return self.secondTrack
            except:
                return 5
        elif command=="getLevel1":
            try:
                return self.firstTrackLevel
            except:
                return 0
        elif command=="getLevel2":
            try:
                return self.secondTrackLevel
            except:
                return 0
        elif command=="useOwnLevels":
            try:
                return self.useOwnLevels
            except:
                return False
                
    def setThrow1(self):
        self.firstTrack=4
        base.localAvatar.setSystemMessage(0,'Gag trainer set to use throw as first gag',5)
    def setThrow2(self):
        self.secondTrack=4
        base.localAvatar.setSystemMessage(0,'Gag trainer set to use throw as second gag',5)
        
    def setSquirt1(self):
        self.firstTrack=5
        base.localAvatar.setSystemMessage(0,'Gag trainer set to use squirt as first gag',5)
        
    def setSquirt2(self):
        self.secondTrack=5
        base.localAvatar.setSystemMessage(0,'Gag trainer set to use squirt as second gag',5)
        
    def setLure1(self):
        self.firstTrack=2
        base.localAvatar.setSystemMessage(0,'Gag trainer set to use lure as first gag',5)
        
    def setLure2(self):
        self.secondTrack=2
        base.localAvatar.setSystemMessage(0,'Gag trainer set to use lure as second gag',5)
        
    def setTrap1(self):
        self.firstTrack=1
        base.localAvatar.setSystemMessage(0,'Gag trainer set to use trap as first gag',5)
        
    def setTrap2(self):
        self.secondTrack=1
        base.localAvatar.setSystemMessage(0,'Gag trainer set to use trap as second gag',5)
        
    def setSound1(self):
        self.firstTrack=3
        base.localAvatar.setSystemMessage(0,'Gag trainer set to use sound as first gag',5)
        
    def setSound2(self):
        self.secondTrack=3
        base.localAvatar.setSystemMessage(0,'Gag trainer set to use sound as second gag',5)
        
    def setDrop1(self):
        self.firstTrack=6
        base.localAvatar.setSystemMessage(0,'Gag trainer set to use drop as first gag',5)
        
    def setDrop2(self):
        self.secondTrack=6
        base.localAvatar.setSystemMessage(0,'Gag trainer set to use drop as second gag',5)
        
    def setToonUp1(self):
        self.secondTrack=0
        
    def setToonUp2(self):
        self.secondTrack=0
        
    def track1Set1(self):
        self.firstTrackLevel=0
        base.localAvatar.setSystemMessage(0,'Gag trainer set to use level 1 on first track',4)
        
    def track2Set1(self):
        self.secondTrackLevel=0
        base.localAvatar.setSystemMessage(0,'Gag trainer set to use level 1 on second track',4)
        
    def track1Set2(self):
        self.firstTrackLevel=1
        base.localAvatar.setSystemMessage(0,'Gag trainer set to use level 2 on first track',4)
        
    def track2Set2(self):
        self.secondTrackLevel=1
        base.localAvatar.setSystemMessage(0,'Gag trainer set to use level 2 on second track',4)
        
    def track1Set3(self):
        self.firstTrackLevel=2
        base.localAvatar.setSystemMessage(0,'Gag trainer set to use level 3 on first track',4)
        
    def track2Set3(self):
        self.secondTrackLevel=2
        base.localAvatar.setSystemMessage(0,'Gag trainer set to use level 3 on second track',4)
        
    def track1Set4(self):
        self.firstTrackLevel=3
        base.localAvatar.setSystemMessage(0,'Gag trainer set to use level 4 on first track',4)
        
    def track2Set4(self):
        self.secondTrackLevel=3
        base.localAvatar.setSystemMessage(0,'Gag trainer set to use level 4 on second track',4)
        
    def track1Set5(self):
        self.firstTrackLevel=4
        base.localAvatar.setSystemMessage(0,'Gag trainer set to use level 5 on first track',4)
        
    def track2Set5(self):
        self.secondTrackLevel=4
        base.localAvatar.setSystemMessage(0,'Gag trainer set to use level 5 on second track',4)
        
    def track1Set6(self):
        self.firstTrackLevel=5
        base.localAvatar.setSystemMessage(0,'Gag trainer set to use level 6 on first track',4)
        
    def track2Set6(self):
        self.secondTrackLevel=5
        base.localAvatar.setSystemMessage(0,'Gag trainer set to use level 6 on second track',4)
        
    def useLevelsTrue(self):
        self.useOwnLevels=True
        levelsTrueFalse.setText("Using custom levels")
        base.localAvatar.setSystemMessage(0,'Gag trainer set to use levels')
        
    def useLevelsFalse(self):
        self.useOwnLevels=False
        levelsTrueFalse.setText("Not Using custom levels")
        base.localAvatar.setSystemMessage(0,'Gag trainer set to not use levels')
        
    def setNoTrolley(self,value):
        self.noTrolley=value
        
    def getNoTrolley(self):
        return self.noTrolley
    
class Restock:

    def __init__(self):
        self.inventory=Inventory()
        self.tryNum=1
        self.maxCarryGags = base.localAvatar.getMaxCarry()
        self.numToZone={1:2000,2:3000,3:9000,4:4000,5:6000,6:5000}
        self.gagshop_zoneId = 4503
        self.noToons=Sequence(Func(self.removeToons), Wait(3)) # Something is broken with this in new toontown
        base.localAvatar.stopLookAroundNow()
        
        self.lookAroundHookSeq = Sequence(Func(self.lookAroundHookFunc), Wait(2.5))
        self.lookAroundHookSeq.loop()
        ToonHead.ToonHead._ToonHead__lookAround = lambda *x:None
        
    def lookAroundHookFunc(self):
        if hasattr(base, 'localAvatar'):
            base.localAvatar.findSomethingToLookAt = lambda *x:None
            self.oldFindSomethingToLookAt = base.localAvatar.findSomethingToLookAt
            self.lookAroundHookSeq.finish()
        self.oldLookAround = ToonHead.ToonHead._ToonHead__lookAround
        
    def collectLaff(self):
        for treasure in base.cr.doFindAll('Treasure'):
            treasure.d_requestGrab()
    
    def removeToons(self):
    
        for x in base.cr.doFindAll('Fisherman'):
            try:
                if x.zoneId != base.localAvatar.zoneId:
                    x.removeNode()
                    x.nametag.unmanage(base.marginManager)
            except:
                pass
 
        for x in base.cr.doFindAll('Party Planner'):
            try:
                if x.zoneId != base.localAvatar.zoneId:
                    x.removeNode()
                    x.nametag.unmanage(base.marginManager)
            except:
                pass
           
        for x in base.cr.doFindAll('render/donald'):
            try:
                if x.zoneId != base.localAvatar.zoneId:
                    x.removeNode()
                    x.nametag.unmanage(base.marginManager)
            except:
                pass
 
        for x in base.cr.doFindAll('render/minnie'):
            try:
                if x.zoneId != base.localAvatar.zoneId:
                    x.removeNode()
                    x.nametag.unmanage(base.marginManager)
            except:
                pass
 
        for x in base.cr.doFindAll('render/mickey'):
            try:
                if x.zoneId != base.localAvatar.zoneId:
                    x.removeNode()
                    x.nametag.unmanage(base.marginManager)
            except:
                pass
 
        for x in base.cr.doFindAll('render/pluto'):
            try:
                if x.zoneId != base.localAvatar.zoneId:
                    x.removeNode()
                    x.nametag.unmanage(base.marginManager)
            except:
                pass
 
        for x in base.cr.doFindAll('render/daisy'):
            try:
                if x.zoneId != base.localAvatar.zoneId:
                    x.removeNode()
                    x.nametag.unmanage(base.marginManager)
            except:
                pass
 
        for x in base.localAvatar.getNearbyPlayers(100000000000000, False):
            try:
                y = base.cr.doId2do.get(x)
                if y.zoneId != base.localAvatar.zoneId:
                    y.removeNode()
                    y.nametag.unmanage(base.marginManager)
            except:
                pass
 
        for x in base.cr.doFindAll('Butterfly'):
            x.butterflyNode.remove()
 
        for x in base.cr.doFindAll('Flower'):
            x.bigFlower.removeNode()
 
        for x in base.cr.doFindAll('Treasure'):
            x.setPosition(0, 0, 8**8)
 
        for x in base.cr.doFindAll('render/DistributedFishingTarget'):
            x.bubbles.removeNode()
            x.removeNode()

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
                    clerk.setMovie=lambda *args: None
                    clerk.freeAvatar=lambda *args: None
                    clerk.sendUpdate('avatarEnter')
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
        base.cr.removeInterest(self.contextId)
        
    def restockGags(self,specificGag=[]):
        if not specificGag:
            self.gagShopRetZone = 4503
            self.firstTrack=self.inventory.getInv("get1")
            self.secondTrack=self.inventory.getInv("get2")
            
            firstTrackLevel=self.inventory.getInv("getLevel1")
            secondTrackLevel=self.inventory.getInv("getLevel2")
            useOwnLevel=self.inventory.getInv("useOwnLevels")
            
            desiredLevel1=self.executeGags("return1")
            desiredLevel2=self.executeGags("return2")
            
            if desiredLevel1==6:
                desiredLevel1=5
                
            if desiredLevel2==6:
                desiredLevel2=5
        else:
            self.firstTrack=specificGag[0]
            desiredLevel1=specificGag[1]
            self.secondTrack=5
            desiredLevel2=0
            
        self.desiredInv=""
            
        for i in range(7*7):
            if i==((self.firstTrack*7)+desiredLevel1):
                if desiredLevel1>3:
                    if self.firstTrack==1:
                        self.desiredInv+="\x02"
                    else:
                        self.desiredInv+="\x03"
                        
                elif self.firstTrack==1:
                    self.desiredInv+="\x03"
                    
                else:
                    self.desiredInv+="\x04"
                    
            elif i==((self.secondTrack*7)+desiredLevel2):
                if desiredLevel2>3:
                    if self.secondTrack==1:
                        self.desiredInv+="\x02"
                    else:
                        self.desiredInv+="\x03"
                        
                elif self.secondTrack==1:
                    self.desiredInv+="\x03"
                    
                else:
                    self.desiredInv+="\x04"

            else:
                self.desiredInv+="\x00"
    
        if base.localAvatar.inventory.inventory[self.firstTrack][self.executeGags("return1")]<2 or base.localAvatar.inventory.inventory[self.secondTrack][self.executeGags("return2")]<2 or specificGag:
            Sequence(Func(self.loadGagshop),Wait(1),Func(self.buyGags),Wait(0.5),Func(self.unloadGagshop)).start()
        
    def gainLaff(self):
        if self.tryNum>5:
            self.tryNum=0
        self.tryNum+=1
        
        zone=self.numToZone[self.tryNum]
        if base.localAvatar.getHp()!=base.localAvatar.getMaxHp():
            self.toonUp=base.cr.addInterest(base.localAvatar.defaultShard, zone, description='5', event=None)
            Sequence(Wait(1.0),Func(self.collectLaff),Func(base.cr.removeInterest, self.toonUp)).start()
    
    def gag(self,battle,track,level,toAttack):
        battle.sendUpdate('requestAttack', [track, level, toAttack])
        battle.sendUpdate('movieDone')
        
    def executeGags(self,command):
        badGags=[1,3,5]
        firstTrackLevel=self.inventory.getInv("getLevel1")
        secondTrackLevel=self.inventory.getInv("getLevel2")
        useOwnLevel=self.inventory.getInv("useOwnLevels")
        firstTrack=self.inventory.getInv("get1")
        secondTrack=self.inventory.getInv("get2")
        
        if useOwnLevel:
            desiredLevel1=firstTrackLevel
            desiredLevel2=secondTrackLevel
        else:
            desiredLevel1=base.localAvatar.experience.getExpLevel(firstTrack)
            desiredLevel2=base.localAvatar.experience.getExpLevel(secondTrack)
            
        if desiredLevel1==6:
            desiredLevel1=5
            
        if desiredLevel2==6:
            desiredLevel2=5
        
        if firstTrack==0 and desiredLevel1 in badGags:
            desiredLevel1-=1
            
        if secondTrack==0 and desiredLevel2 in badGags:
            desiredLevel2-=1
            
        if command=="return1":
            return desiredLevel1
        elif command=="return2":
            return desiredLevel2

        for battle in base.cr.doFindAll('battle'):
            if base.localAvatar in battle.toons:
                try:
                    if firstTrack==0:
                        toAttack1=base.localAvatar.doId
                    else:
                        toAttack1=battle.suits[0].doId
                        
                    if secondTrack==0:
                        toAttack2=base.localAvatar.doId
                    else:
                        toAttack2=battle.suits[0].doId
                        
                    if base.localAvatar.inventory.inventory[firstTrack][desiredLevel1]>0:
                        self.gag(battle,firstTrack,desiredLevel1,toAttack1)
                        
                    if base.localAvatar.inventory.inventory[secondTrack][desiredLevel2]>0:
                        self.gag(battle,secondTrack,desiredLevel2,toAttack2)
                                        
                except:
                    pass
        

class GagTrainer:
    oldBattlePlaceTeleportIn=BattlePlace.BattlePlace.exitTeleportIn
    oldEnterReward=DistributedBattle.DistributedBattle.enterReward
    oldEnterFaceOff=DistributedBattle.DistributedBattle.enterFaceOff
    oldDenyBattle=DistributedSuit.DistributedSuit.denyBattle
    oldEnterHealth=HealthForceAcknowledge.HealthForceAcknowledge.enter
    
    def __init__(self):
        self.restock=Restock()
        self.clearSettings()
        self.shouldContinue=False
        self.shouldChangeHood=False
        self.shouldChangeDistrict=True
        self.shouldChangeStreet=True
        self.checkCogWalked=None
        self.shardIds=[]
        for shard in base.cr.activeDistrictMap:
            if base.cr.activeDistrictMap[shard].avatarCount<50:
                self.shardIds.append(shard)
        self.lastCogId=0
        self.buyGags=Sequence(Func(self.restock.restockGags),Wait(3.0))
        self.gainLaff=Sequence(Func(self.restock.gainLaff),Wait(3.0))
        self.battleLoop=Sequence(Wait(1.5),Func(self.restock.executeGags,None))
        self.invisibleSeq=Sequence(Func(base.localAvatar.d_setParent,1),Wait(1))
        DistributedBattle.DistributedBattle.enterReward=lambda newSelf,*args: self.newEnterReward(newSelf,*args)
        DistributedSuit.DistributedSuit.denyBattle=lambda newSelf,*args: self.newDenyBattle(newSelf,*args)
        DistributedBattle.DistributedBattle.enterFaceOff=lambda newSelf,*args: self.newEnterFaceOff(newSelf,*args)
        HealthForceAcknowledge.HealthForceAcknowledge.enter=lambda newSelf,hplevel: self.newEnterHealth(newSelf,hplevel)
        BattlePlace.BattlePlace.exitTeleportIn=lambda newSelf,*args: self.newBattlePlaceTeleportIn(newSelf,*args)
        
    def newEnterHealth(self,newSelf,hplevel):
        try:
            self.oldEnterHealth(newSelf,hplevel)
            newSelf.handleOk(base.localAvatar.getHp())
            newSelf.exit()
            if self.shouldContinue:
                Sequence(Wait(3),Func(self.teleportBackToStreet)).start()
        except:
            pass
    
    def newEnterFaceOff(self,newSelf,*args):
        self.oldEnterFaceOff(newSelf,*args)
        if self.checkCogWalked:
            self.checkCogWalked.pause()
    
    def newDenyBattle(self,newSelf,*args):
        self.oldDenyBattle(newSelf,*args)
        if self.lastCogId==newSelf.doId and self.shouldContinue:
            if self.checkCogWalked:
                self.checkCogWalked.pause()
            Sequence(Wait(1),Func(self.enterRandomBattle)).start()
    
    def newEnterReward(self,newSelf,*args):
        self.oldEnterReward(newSelf,*args)
        if base.localAvatar in newSelf.toons and self.shouldContinue:
            newSelf.d_rewardDone(base.localAvatar.doId)
            
            if not taskAutoer.isQuestComplete():
                Sequence(Wait(3),Func(self.enterRandomBattle)).start()
            else:
                self.stop()
                base.localAvatar.collisionsOff()
                Sequence(Wait(3),Func(taskAutoer.checkWhatToDo)).start()
    
    def newBattlePlaceTeleportIn(self,newSelf,*args):
        self.oldBattlePlaceTeleportIn(newSelf,*args)
        if self.shouldContinue:
            self.startLoops()
            Sequence(Wait(2),Func(self.enterRandomBattle)).start()
    
    def clearSettings(self):
        self.hasSettings=False
        self.shouldChangeHood = False
        self.cogName=None
        self.cogType=None
        self.cogLevel=None
    
    def setCogName(self,name):
        self.hasSettings=True
        self.cogName=name
    
    def setCogType(self,type):
        self.hasSettings=True
        if type=='l':
            type='Lawbot'
        elif type=='s':
            type='Sellbot'
        elif type=='m':
            type='Cashbot'
        elif type=='c':
            type='Bossbot'
        self.cogType=type
    
    def setCogLevel(self,level):
        self.hasSettings=True
        self.cogLevel=level
       
    def newDistrict(self):
        if self.shardIds[0] == base.localAvatar.defaultShard:
            self.shardIds.append(self.shardIds[0])
            del self.shardIds[0]
            
        base.cr.playGame.getPlace().requestTeleport(round(base.localAvatar.getZoneId(),-3),self.streetId,self.shardIds[0],None)
        self.shardIds.append(self.shardIds[0])
        del self.shardIds[0]
        
    def newStreet(self):
        todo='street'
        if self.streetId<9000:
            if int(str(self.streetId)[1:])>300:
                if self.shouldChangeDistrict:
                    self.streetId-=200
                    todo='district'
                elif self.shouldChangeHood:
                    todo='hood'
                else:
                    self.streetId-=200
            else:
                self.streetId+=100
        elif int(str(self.streetId)[1:])>200:
            if self.shouldChangeDistrict:
                self.streetId-=100
                todo='district'
                
            elif self.shouldChangeHood:
                todo='hood'
            else:
                self.streetId-=100
        else:
            self.streetId+=100
        
        if todo=='district':
            Sequence(Wait(2),Func(self.newDistrict)).start()
        elif todo=='hood':
            self.newHood()
        else:
            self.teleportBackToStreet()  
        
    def nextZone(self):
        try:
            base.cr.playGame.getPlace().enterZone(base.localAvatar.getZoneId()+1)
            Sequence(Wait(0.5),Func(self.enterRandomBattle)).start()
        except KeyError:
            if self.shouldChangeStreet:
                self.newStreet()
            elif self.shouldChangeDistrict:
                self.newDistrict()
            else:
                base.cr.playGame.getPlace().enterZone(self.streetId)
                Sequence(Wait(0.5),Func(self.enterRandomBattle)).start()
                
    def enterRandomBattle(self):
        if self.checkCogWalked:
            self.checkCogWalked.pause()
        firstTrack=self.restock.inventory.getInv("get1")
        secondTrack=self.restock.inventory.getInv("get2")
        battles = []
        battles2 = []
        for x in base.cr.doFindAllInstances(DistributedSuit.DistributedSuit):
            if x.activeState == 6:
                if x.getCurrentAnim() in ['walk','landing']:
                    if self.hasSettings and x.getActualLevel()>=self.cogLevel and (x.getName()==self.cogName or x.getStyleDept()==self.cogType or (not self.cogType and not self.cogName)):
                        battles.append(x)
                        battles2.append(True)
                    elif not self.hasSettings and x.getActualLevel()>self.restock.executeGags("return2") and x.getActualLevel()>self.restock.executeGags("return2"):
                        if base.localAvatar.getMaxHp()>suitToDamage[x.getActualLevel()] or self.restock.executeGags("return1")>3 or self.restock.executeGags("return2")>3:
                            battles.append(x)
                            battles2.append(True)
                        elif self.getPlace()>=11200 and self.getPlace()<=11300 and self.restock.executeGags("return1")>2 and self.restock.executeGags("return2")>2:
                            battles.append(x)
                            battles2.append(True)
                        else:
                            battles2.append(False)
                    else:
                        battles2.append(False)
        if not taskAutoer.isQuestComplete():
            try:
                if battles and base.localAvatar.getHp()>0:
                    battle = random.choice(battles)
                    pos, hpr = battle.getPos(), battle.getHpr()
                    base.localAvatar.collisionsOn()
                    base.localAvatar.setPosHpr(pos, hpr)
                    battle.d_requestBattle(pos,hpr)
                    self.checkCogWalked=Sequence(Wait(20),Func(self.enterRandomBattle))
                    self.checkCogWalked.start()
                    self.lastCogId=battle.doId
                else:
                    if hasattr(base.cr.playGame.getPlace(),'enterZone') and base.localAvatar.getZoneId() not in range(HQZONES[0],HQZONES[-1]+1000):
                        self.nextZone()
                    else:
                        self.newDistrict()
            except:
                pass
        else:
            self.stop()
            base.localAvatar.collisionsOff()
            Sequence(Wait(2),Func(taskAutoer.checkWhatToDo)).start()
    
    def setLocation(self,zoneId):
        if zoneId in range(10000,13999):
            self.streetId=zoneId
            self.shouldChangeStreet=True
        elif round(zoneId,-3)!=zoneId:
            self.streetId=zoneId+2
            self.shouldChangeStreet=False
        else:
            self.shouldChangeStreet=True
            self.streetId=zoneId+102
    
    def teleportBackToStreet(self):
        self.walk()
        self.restock.collectLaff()
        base.cr.playGame.getPlace().requestTeleport(round(self.streetId,-3),self.streetId,None,None)
    
    def startLoops(self):
        self.buyGags.loop()
        self.gainLaff.loop()
        self.battleLoop.loop()
        self.invisibleSeq.loop()
    
    def stopLoops(self):
        self.buyGags.finish()
        self.gainLaff.finish()
        self.battleLoop.finish()
        self.invisibleSeq.finish()
    
    def start(self):
        if base.localAvatar.getTrackAccess()[0]:
            self.restock.inventory.setToonUp2()
        self.shouldContinue=True
        exec(hooks, __main__.__dict__)
        if base.localAvatar.getZoneId() not in range(self.streetId,self.streetId+90):
            self.teleportBackToStreet()
        else:
            self.startLoops()
            self.enterRandomBattle()
    
    def stop(self):
        DistributedDoor.DistributedDoor.announceGenerate=_announceGenerate1
        DistributedPartyGate.DistributedPartyGate.announceGenerate=_announceGenerate2
        DistributedTrolley.DistributedTrolley.__init__=old__init__
        DistributedPartyGate.DistributedPartyGate.__init__=old__init__2
        DistributedDoor.DistributedDoor.__init__=old__init__3
        DistributedPicnicBasket.DistributedPicnicBasket.__init__=old__init__4
        self.shouldContinue=False
        self.stopLoops()
    
    def walk(self):
        base.cr.playGame.getPlace().fsm.forceTransition('walk')