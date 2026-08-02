import random
from direct.interval.IntervalGlobal import *
from direct.distributed import DistributedObject
from toontown.toonbase import ToontownBattleGlobals
from toontown.safezone import *
from toontown.toon import *
from toontown.coghq import *
from toontown.distributed import ToontownClientRepository
from toontown.battle import DistributedBattle
from toontown.battle import DistributedBattleFinal
from toontown.suit.DistributedFactorySuit import DistributedFactorySuit
from toontown.suit.DistributedSuit import DistributedSuit
from toontown.suit import DistributedSellbotBoss
from toontown.building import DistributedDoor
from toontown.building import DistributedBoardingParty

ToontownBattleGlobals.SkipMovie=1
ToontownClientRepository.ToontownClientRepository.dumpAllSubShardObjects=lambda self: None
ToontownClientRepository.ToontownClientRepository.forbidCheesyEffects=lambda *x,**kwds: None

faceOffHook = lambda self, ts, name, callback:self.d_faceOffDone(self)
DistributedBattleFactory.DistributedBattleFactory._DistributedLevelBattle__faceOff = faceOffHook
DistributedBattle.DistributedBattle._DistributedBattle__faceOff = faceOffHook

oldTrolleyInit = DistributedTrolley.DistributedTrolley.__init__
oldPartyInit = DistributedPartyGate.DistributedPartyGate.__init__
oldDoorInit = DistributedDoor.DistributedDoor.__init__

oldHandleEnterCollisionSphereParty=DistributedNPCPartyPerson.DistributedNPCPartyPerson.handleCollisionSphereEnter
DistributedNPCPartyPerson.DistributedNPCPartyPerson.handleCollisionSphereEnter=lambda *args: None
oldHandleEnterCollisionSphereFisherman=DistributedNPCFisherman.DistributedNPCFisherman.handleCollisionSphereEnter
DistributedNPCFisherman.DistributedNPCFisherman.handleEnterCollisionSphere=lambda *args: None
 
oldFisherAnnounceGenerate = DistributedNPCFisherman.DistributedNPCFisherman.announceGenerate
def newFishermanAnnounceGenerate(self):
    try:
        oldFisherAnnounceGenerate(self)
    except:
        return None
        
oldFishermanInitToonState = DistributedNPCFisherman.DistributedNPCFisherman.initToonState
def newFishermanInitToonState(self):
    try:
        oldFishermanInitToonState(self)
    except:
        return None
 
oldPartyPlannerAnnounceGenerate = DistributedNPCPartyPerson.DistributedNPCPartyPerson.announceGenerate
def newPartyPlannerAnnounceGenerate(self):
    try:
        oldPartyPlannerAnnounceGenerate(self)
    except:
        return None
 
def newInit(self, cr):
    for obj in dir(self):
        exec('self.%s = lambda *x:None' % obj, globals(), locals())
    return None

class restock:

    def __init__(self):
        if not base.localAvatar.getTrackAccess()[0] or base.localAvatar.experience.getExpLevel(0)<4:
            self.noToonUp=True
            self.secondTrack=4
            self.desiredLevel2=5
        else:
            self.noToonUp=False
            self.secondTrack=0
            self.desiredLevel2=4
            
        if not base.localAvatar.getTrackAccess()[2] or base.localAvatar.experience.getExpLevel(2)<5:
            self.noLure=True
            self.firstTrack=4
            self.desiredLevel1=5
        else:
            self.noLure=False
            self.firstTrack=2
            self.desiredLevel1=5
            
        if base.localAvatar.experience.getExpLevel(4)<5:
            base.localAvatar.setSystemMessage(0,'You do not have the required throw level to run this.')
            
        self.thirdTrack=4
        self.desiredLevel3=5
        self.createInventory()
        self.maxCarryGags = base.localAvatar.getMaxCarry()
        self.gagshop_zoneId = 4503
        self.noToons=Sequence(Func(self.removeToons), Wait(1.5))
        self.noTrolley=False
        self.unloaded=True
        self.wasInBattle=False
        DistributedNPCFisherman.DistributedNPCFisherman.announceGenerate = newFishermanAnnounceGenerate
        DistributedNPCFisherman.DistributedNPCFisherman.initToonState = newFishermanInitToonState
        DistributedNPCPartyPerson.DistributedNPCPartyPerson.announceGenerate = newPartyPlannerAnnounceGenerate
        
        self.lookAroundHookSeq = Sequence(Func(self.lookAroundHookFunc), Wait(2.5))
        self.lookAroundHookSeq.loop()
        ToonHead.ToonHead._ToonHead__lookAround = lambda *x:None
    
    def createInventory(self):
        self.desiredInv=""
        if self.desiredLevel1==6:
            self.desiredLevel1=5
            
        if self.desiredLevel2==6:
            self.desiredLevel2=5
            
        for i in range(49):
            if i==((self.firstTrack*7)+self.desiredLevel1):
                if self.firstTrack==1:
                    self.desiredInv+="\x02"
                elif self.desiredLevel1>3:
                    self.desiredInv+="\x02"
                else:
                    self.desiredInv+="\x04"
            elif i==((self.secondTrack*7)+self.desiredLevel2):
                if self.secondTrack==1:
                    self.desiredInv+="\x02"
                elif self.desiredLevel2>3:
                    self.desiredInv+="\x02"
                else:
                    self.desiredInv+="\x04"
            elif i==((self.thirdTrack*7)+self.desiredLevel3):
                if self.thirdTrack==1:
                    self.desiredInv+="\x02"
                elif self.desiredLevel3>3:
                    self.desiredInv+="\x02"
                else:
                    self.desiredInv+="\x04"
            else:
                self.desiredInv+="\x00"
        
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
 
        #for x in base.cr.doFindAll('Flower'):
         #   print('test')
            #x.bigFlower.removeNode()
 
        for x in base.cr.doFindAll('Treasure'):
            x.setPosition(0, 0, 8**8)
 
        for x in base.cr.doFindAll('render/DistributedFishingTarget'):
            x.bubbles.removeNode()
            x.removeNode()
                
    def gainLaff(self):
        if base.localAvatar.getHp()!=base.localAvatar.getMaxHp():
            if self.unloaded:
                vpMaxer.factoryAutoer.preTele()
                self.interest1=base.cr.addInterest(base.localAvatar.defaultShard, 9000, '5', None)
                self.interest2=base.cr.addInterest(base.localAvatar.defaultShard, 3000, '5', None)
                self.unloaded=False
            self.collectLaff()
        if self.wasInBattle:
            vpMaxer.factoryAutoer.enterBattle()
     
    def loadGagshop(self):           
        if not base.cr.doFind('Clerk'):
            self.contextId = base.cr.addInterest(base.localAvatar.defaultShard, self.gagshop_zoneId, '4', event=None)
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
                    clerk.sendUpdate('setInventory', [newString, change, 1])
                    
                money = base.localAvatar.getMoney()
                maxMoney = base.localAvatar.getMaxMoney()
                base.cr.bankManager.d_transferMoney(money - maxMoney)
        except:
            pass
    
    def unloadGagshop(self):
        if hasattr(self, 'contextId'):
            try:
                base.cr.removeInterest(self.contextId)
            except:
                pass
        
    def restock(self):
        try:
            if base.localAvatar.inventory.inventory[self.firstTrack][self.desiredLevel1]<2 or base.localAvatar.inventory.inventory[self.secondTrack][self.desiredLevel2]<2 or base.localAvatar.inventory.inventory[self.thirdTrack][self.desiredLevel3]<2:
                Sequence(Func(self.loadGagshop),Wait(1),Func(self.buyGags),Wait(0.5),Func(self.unloadGagshop)).start()
        
        except:
            pass
    
    def revertFunctions(self):
        #self.noToons.finish()
        try:
            base.cr.removeInterest(self.interest1)
            base.cr.removeInterest(self.interest2)
            self.unloaded=True
        except:
            pass
            
class OtherFunctions:

    oldGardensInit=DGPlayground.DGPlayground.__init__
    oldSellbotInit=SellbotHQExterior.SellbotHQExterior.__init__
    oldSendUpdate=DistributedObject.DistributedObject.sendUpdate
    oldEnterHealth=HealthForceAcknowledge.HealthForceAcknowledge.enter
    oldSetAnim=LocalToon.LocalToon.setAnimState
    oldPostInvite=DistributedBoardingParty.DistributedBoardingParty.postInvite


    def __init__(self):
        self.shouldContinue=False
        self.bossCount=0
        self.shouldEnd=False
        self.onlyFactory=False
        self.canSetParentAgain=True
        self.isMember=True
        self.numberToSuit={0:'Cold Caller',1:'Telemarketer',2:'Name Dropper',3:'Glad Hander',
                           4:'Mover & Shaker',5:'Two-Face',6:'The Mingler',7:'Mr. Hollywood'}

        DGPlayground.DGPlayground.__init__=lambda *args:self.newGardensInit(*args)
        SellbotHQExterior.SellbotHQExterior.__init__=lambda *args: self.newSellbotInit(*args)
        HealthForceAcknowledge.HealthForceAcknowledge.enter=lambda newSelf,hplevel: self.newEnterHealth(newSelf,hplevel)
        LocalToon.LocalToon.setAnimState=lambda *args,**kwds:self.newSetAnimState(*args,**kwds)
        DistributedBoardingParty.DistributedBoardingParty.postInvite=lambda newSelf,leaderId,inviterId: self.newPostInvite(newSelf,leaderId,inviterId)

    def attack(self):
        try:
            for battle in base.cr.doFindAll('battle'):
                if vpMaxer.factoryAutoer.roomNum==len(vpMaxer.factoryAutoer.roomsNeeded):
                    if len(battle.suits)>1:
                        for suit in battle.suits: 
                            if suit.getName()!='Skelecog':
                                attackSuit=suit
                    else:
                        attackSuit=battle.suits[0]
                else:
                    attackSuit=battle.suits[0]
                    
                if vpMaxer.restock.noToonUp and not vpMaxer.restock.noLure:
                    if vpMaxer.restock.firstTrack==2 and base.localAvatar.getHp()>(base.localAvatar.getMaxHp()*0.75):
                        battle.sendUpdate('requestAttack', [vpMaxer.restock.firstTrack, vpMaxer.restock.desiredLevel1, attackSuit.doId])
                    if base.localAvatar.getHp()>(base.localAvatar.getMaxHp()*0.75):
                        battle.sendUpdate('requestAttack', [vpMaxer.restock.thirdTrack, vpMaxer.restock.desiredLevel3, attackSuit.doId])
                        
                elif vpMaxer.restock.noLure:
                    if vpMaxer.restock.secondTrack==0 and base.localAvatar.getHp()<(base.localAvatar.getMaxHp()*0.75):
                        battle.sendUpdate('requestAttack', [vpMaxer.restock.secondTrack, vpMaxer.restock.desiredLevel2, base.localAvatar.doId])
                    if base.localAvatar.getHp()>(base.localAvatar.getMaxHp()*0.75):
                        battle.sendUpdate('requestAttack', [vpMaxer.restock.thirdTrack, vpMaxer.restock.desiredLevel3, attackSuit.doId])
                        
                else:
                    if base.localAvatar.inventory.inventory[vpMaxer.restock.firstTrack][vpMaxer.restock.desiredLevel1]>0:
                        battle.sendUpdate('requestAttack', [vpMaxer.restock.firstTrack, vpMaxer.restock.desiredLevel1, attackSuit.doId])
                    else:
                        break
                        
                    if base.localAvatar.getHp()<(base.localAvatar.getMaxHp()*0.5):
                    
                        if base.localAvatar.inventory.inventory[vpMaxer.restock.secondTrack][vpMaxer.restock.desiredLevel2]>0:
                            battle.sendUpdate('requestAttack', [vpMaxer.restock.secondTrack, vpMaxer.restock.desiredLevel2, base.localAvatar.doId])
                        else:
                            break
                            
                        if base.localAvatar.inventory.inventory[vpMaxer.restock.thirdTrack][vpMaxer.restock.desiredLevel3]>0:
                            battle.sendUpdate('requestAttack', [vpMaxer.restock.thirdTrack, vpMaxer.restock.desiredLevel3, attackSuit.doId])
                        else:
                            break
                            
                    else:
                        if base.localAvatar.inventory.inventory[vpMaxer.restock.thirdTrack][vpMaxer.restock.desiredLevel3]>0:
                            battle.sendUpdate('requestAttack', [vpMaxer.restock.thirdTrack, vpMaxer.restock.desiredLevel3, attackSuit.doId])
                        else:
                            break
        except:
            pass
        
    def sendUpdateHook(self, newself, fieldName, args=[], sendToId=None):
        if fieldName=="requestAttack":
            self.oldSendUpdate(newself,"requestAttack", args, sendToId)
            self.oldSendUpdate(newself,"movieDone",[])
        else:
            self.oldSendUpdate(newself,fieldName, args, sendToId)
        
    def newGardensInit(self,*args):
        self.oldGardensInit(*args)
        if self.shouldContinue:
            vpMaxer.factoryAutoer.gainLaffSeq.finish()
            vpMaxer.factoryAutoer.attackSeq.finish()
            vpMaxer.restock.wasInBattle=False
            self.checkMerits()
    
    def newSetAnimState(self,*args,**kwds):
        self.oldSetAnim(*args,**kwds)
        if self.canSetParentAgain and self.shouldContinue:
            base.localAvatar.d_setParent(1)
            self.canSetParentAgain=False
            Sequence(Wait(2),Func(self.doUnsetCanSetParentAgain)).start()
    
    def doUnsetCanSetParentAgain(self):
        self.canSetParentAgain=True
    
    def newEnterHealth(self,newSelf,hplevel):
        try:
            self.oldEnterHealth(newSelf,hplevel)
            newSelf.handleOk(base.localAvatar.getHp())
            newSelf.exit()
            if self.shouldContinue:
                Sequence(Wait(2),Func(self.checkMerits)).start()
        except:
            pass
            
    def newSellbotInit(self,*args):
        self.oldSellbotInit(*args)
        if self.shouldContinue:
            self.walk()
            base.localAvatar.setWantBattles(False)
            Sequence(Wait(2),Func(self.checkMerits)).start()
    
    def newPostInvite(self,newSelf,leaderId,inviterId):
        print('test')
        if leaderId==base.localAvatar.doId:
            newSelf.sendUpdate('requestAcceptInvite',[inviterId,leaderId])
        else:
            self.oldPostInvite(newSelf,leaderId,inviterId)
        
    def checkMerits(self):
        # TTI Brought in a promotion button?
        if base.localAvatar.promotionStatus[3] == 1:
            base.localAvatar.promotionStatus[3] = 0
            base.localAvatar.sendUpdate('requestPromotion', [3])
            vpMaxer.autoerGui.display.newLine('Promoting')
            Sequence(Wait(1),Func(self.checkMerits)).start()
            return
            
        if self.onlyFactory:
            base.localAvatar.cogMerits[3]=-4000
        if self.shouldEnd:
            self.shouldContinue=False
            base.localAvatar.setWantBattles(True)
        if self.haveJb():
            if self.shouldContinue:
                if self.getMeritsLeft()==0 and self.isSuitComplete() and not self.onlyFactory:
                    if base.cr.doFind('DistributedCogHQDoor') and base.localAvatar.getZoneId()>=11000 and base.localAvatar.getZoneId()<11100:
                        vpMaxer.vpAutoer.start()
                    else:
                        vpMaxer.restock.restock()
                        vpMaxer.restock.collectLaff()
                        self.walk()
                        vpMaxer.autoerGui.display.newLine('Teleporting to Sellbot hq')
                        Sequence(Wait(2),Func(self.teleBack)).start()
                else:
                    if base.cr.doFind('DistributedCogHQDoor') and base.localAvatar.getZoneId()>=11000 and base.localAvatar.getZoneId()<11100:
                        print('test')
                        vpMaxer.factoryAutoer.goFactory()
                    else:
                        vpMaxer.restock.restock()
                        vpMaxer.restock.collectLaff()
                        self.walk()
                        vpMaxer.autoerGui.display.newLine('Teleporting to Sellbot hq')
                        Sequence(Wait(2),Func(self.teleBack)).start()
            else:
                #vpMaxer.restock.noToons.finish()
                try:
                    base.cr.removeInterest(vpMaxer.restock.interest1)
                    base.cr.removeInterest(vpMaxer.restock.interest2)
                    vpMaxer.restock.unloaded=True
                except:
                    pass
                base.localAvatar.setSystemMessage(1,"Thanks for using freshollie's VP maxer")
                vpMaxer.autoerGui.display.newLine("Stopped")
                vpMaxer.factoryAutoer.attackSeq.finish()
        else:
            vpMaxer.autoerGui.display.newLine('Out of jellybeans')
            base.localAvatar.setSystemMessage(0,'You have run out of jelly beans, please use the fishing code to gain some')
    
    def getMeritsLeft(self):
        return CogDisguiseGlobals.getTotalMerits(base.localAvatar,3)-base.localAvatar.cogMerits[3]
       
    def isSuitComplete(self):
        return base.localAvatar.cogParts[3] == CogDisguiseGlobals.PartsPerSuitBitmasks[3]

    def walk(self):
        try:
            base.cr.playGame.getPlace().fsm.forceTransition('walk')
        except:
            pass
       
    def teleBack(self,zone=11000):
        try:
            self.walk()
            base.cr.playGame.getPlace().handleBookCloseTeleport(zone, zone)
        except:
            pass
            
    def onlyDoFactory(self):
        self.onlyFactory=True
        base.localAvatar.setSystemMessage(0,'The VP Maxer will do only factory runs')
        
    def doBoth(self):
        self.onlyFactory=False
        base.localAvatar.setSystemMessage(0,'The VP Maxer will do both factories and VPs')
        
    def haveJb(self):
        if base.localAvatar.cogLevels[0]==49:
            return True
        elif base.localAvatar.getTotalMoney()<100:
            return False
        else:
            return True
        
    def setStop(self):
        self.shouldEnd=True
        base.localAvatar.setSystemMessage(1,"The Autoer will stop at the end of this run")
        vpMaxer.autoerGui.stopTimer()
    
    def start(self):
        DistributedObject.DistributedObject.sendUpdate=lambda newself, fieldName, args=[], sendToId=None: self.sendUpdateHook(newself, fieldName, args, sendToId)
        self.shouldEnd=False
        self.shouldContinue=True
        self.bossCount=0
        vpMaxer.autoerGui.startTimer()
        emptyShardList=[]
        for shard in base.cr.activeDistrictMap:
            if base.cr.activeDistrictMap[shard].avatarCount<30:
                emptyShardList.append(shard)
        if emptyShardList==[]:
            emptyShardList=[650000000, 754000000, 608000000, 756000000, 658000000, 712000000, 360000000, 410000000, 620000000, 454000000, 726000000, 362000000, 688000000, 316000000]
        if base.localAvatar.defaultShard not in emptyShardList:
            vpMaxer.autoerGui.display.newLine('TPing to an empty district')
            base.cr.playGame.getPlace().requestTeleport(11000,11000,random.choice(emptyShardList),None)            
        else:
            self.checkMerits()
        #vpMaxer.restock.noToons.loop()
        
    def revertFunctions(self):
        LocalToon.LocalToon.setAnimState=self.oldSetAnim
        DGPlayground.DGPlayground.__init__=self.oldGardensInit
        SellbotHQExterior.SellbotHQExterior.__init__=self.oldSellbotInit
        DistributedObject.DistributedObject.sendUpdate=self.oldSendUpdate
        HealthForceAcknowledge.HealthForceAcknowledge.enter=self.oldEnterHealth
        DistributedBoardingParty.DistributedBoardingParty.postInvite=self.oldPostInvite

class VpAutoer:
    oldBossEnterElevator=DistributedSellbotBoss.DistributedSellbotBoss.enterElevator
    oldEnterBattleThree=DistributedSellbotBoss.DistributedSellbotBoss.enterBattleThree
    oldEnterPrepareBattleTwo=DistributedSellbotBoss.DistributedSellbotBoss.enterPrepareBattleTwo
    oldEnterPrepareBattleThree=DistributedSellbotBoss.DistributedSellbotBoss.enterPrepareBattleThree
    oldEnterEpilogue=DistributedSellbotBoss.DistributedSellbotBoss.enterEpilogue
    oldEnterRollToBattleTwo=DistributedSellbotBoss.DistributedSellbotBoss.enterRollToBattleTwo
    oldEnterWaitForInput=DistributedBattleFinal.DistributedBattleFinal.enterWaitForInput
    oldBossEnterIntro=DistributedSellbotBoss.DistributedSellbotBoss.enterIntroduction
    oldAvatarExit=DistributedCogHQDoor.DistributedCogHQDoor.avatarExit
    oldEnterWalk=CogHQLobby.CogHQLobby.enterWalk
    
    def __init__(self):
        self.filter=False
        self.cardsWanted=['Flippy','Barnacle Bessie','Lil Oldman','Professor Pete','Stinky Ned','Daffy Don','Moe Zart','Sid Sonata','Franz Neckvein']
        
        DistributedSellbotBoss.DistributedSellbotBoss.enterElevator=lambda newSelf: self.newBossEnterElevator(newSelf)
        DistributedSellbotBoss.DistributedSellbotBoss.enterIntroduction=lambda newSelf,*args: self.newBossEnterIntro(newSelf,*args)
        DistributedSellbotBoss.DistributedSellbotBoss.enterRollToBattleTwo=lambda newSelf: self.newEnterRollToBattleTwo(newSelf)
        DistributedSellbotBoss.DistributedSellbotBoss.enterBattleThree=lambda newSelf: self.newEnterBattleThree(newSelf)
        DistributedBattleFinal.DistributedBattleFinal.enterWaitForInput=lambda *args: self.newEnterWaitForInput(*args)
        DistributedCogHQDoor.DistributedCogHQDoor.avatarExit=lambda newSelf,id: self.newAvatarExit(newSelf,id)
        CogHQLobby.CogHQLobby.enterWalk=lambda newSelf,*args,**kwds: self.newEnterWalk(newSelf,*args,**kwds)
        DistributedSellbotBoss.DistributedSellbotBoss.enterPrepareBattleThree=lambda newSelf: self.newEnterPrepareBattleThree(newSelf)
        DistributedSellbotBoss.DistributedSellbotBoss.enterPrepareBattleTwo=lambda newSelf: self.newEnterPrepareBattleTwo(newSelf)
        DistributedSellbotBoss.DistributedSellbotBoss.enterEpilogue=lambda newSelf: self.newEnterEpilogue(newSelf)
        
    def newBossEnterElevator(self,newSelf):
        self.oldBossEnterElevator(newSelf)
        if vpMaxer.otherFunctions.shouldContinue:
            vpMaxer.autoerGui.display.newLine('Skipping Elevator')
            newSelf._DistributedBossCog__doneElevator()
            
    def newBossEnterIntro(self,newSelf,*args):
        self.oldBossEnterIntro(newSelf,*args)
        if vpMaxer.otherFunctions.shouldContinue:
            if self.cardFilter():
                newSelf.exitIntroduction()
                vpMaxer.autoerGui.display.newLine('Skipping VP introduction')
            else:
                vpMaxer.autoerGui.display.newLine('Card not in wanted cards')
                vpMaxer.autoerGui.display.newLine('Restarting the VP')
                Sequence(Wait(2),Func(vpMaxer.otherFunctions.teleBack)).start()
    
    def newEnterEpilogue(self,newSelf):
        self.oldEnterEpilogue(newSelf)
        if vpMaxer.otherFunctions.shouldContinue:
            vpMaxer.otherFunctions.bossCount+=1
            vpMaxer.otherFunctions.teleBack()
            vpMaxer.autoerGui.display.newLine('Finished VP')
    
    def newEnterRollToBattleTwo(self,newSelf):
        self.oldEnterRollToBattleTwo(newSelf)
        if vpMaxer.otherFunctions.shouldContinue:
            newSelf.exitRollToBattleTwo()
            vpMaxer.autoerGui.display.newLine('Skipping cutscene')
    
    def newEnterPrepareBattleTwo(self,newSelf):
        self.oldEnterPrepareBattleTwo(newSelf)
        if vpMaxer.otherFunctions.shouldContinue:
            newSelf._DistributedSellbotBoss__onToBattleTwo(33)
            vpMaxer.autoerGui.display.newLine('Skipping dialogue 1')
    
    def newEnterPrepareBattleThree(self,newSelf):
        self.oldEnterPrepareBattleThree(newSelf)
        if vpMaxer.otherFunctions.shouldContinue:
            newSelf._DistributedSellbotBoss__onToBattleThree(33)
            vpMaxer.autoerGui.display.newLine('Skipping dialogue 2')
    
    def newEnterBattleThree(self,newSelf):
        self.oldEnterBattleThree(newSelf)
        if vpMaxer.otherFunctions.shouldContinue:
            self.endBattle()
            vpMaxer.autoerGui.display.newLine('Completing pie round')
    
    def newEnterWaitForInput(self,*args):
        self.oldEnterWaitForInput(*args)
        if vpMaxer.otherFunctions.shouldContinue:
            self.exploit()
            vpMaxer.autoerGui.display.newLine('Skipping Battle')
    
    def newEnterWalk(self,newSelf,*args,**kwds):
        self.oldEnterWalk(newSelf,*args,**kwds)
        if len(args)>0:
            if vpMaxer.otherFunctions.shouldContinue and args[0]:
                self.goVpBattle()
            
        
    def newAvatarExit(self,newSelf,id):
        self.oldAvatarExit(newSelf,id)
        if base.cr.doFind('Elevator') and id==base.localAvatar.doId and vpMaxer.otherFunctions.shouldContinue:
            self.goVpBattle()

    def goVpBattle(self):
        vpMaxer.otherFunctions.walk()
        vpMaxer.autoerGui.display.newLine('Heading to VP')
        base.localAvatar.setWantBattles(True)
        base.cr.doFind('Boarding').sendUpdate('requestLeave',[base.localAvatar.doId])
        base.cr.doFind('Boarding').sendUpdate('requestInvite',[base.localAvatar.doId])
        base.cr.doFind('Boarding').sendUpdate('requestGoToSecondTime',[base.cr.doFind('Elevator').doId])
            
    def destroyBattle(self):
        base.cr.doFind('V. P').sendUpdate('skipBattleCheat')
    
    def filterOn(self):
        self.filter=True
        self.cardsWanted=['Flippy','Barnacle Bessie','Lil Oldman','Professor Pete','Stinky Ned','Daffy Don','Moe Zart','Sid Sonata','Franz Neckvein']
        base.localAvatar.setSystemMessage(0,'The VP Maxer will filter bad cards')
    
    def filterOn16(self):
        self.filter=True
        self.cardsWanted=['Flippy', 'Daffy Don', 'Clerk Clara', 'Clerk Penny', 'Lil Oldman', 'Stinky Ned', 'Moe Zart', 'Sid Sonata', 'Barnacle Bessie',\
                          'Franz Neckvein', 'Madam Chuckle', 'Clerk Will', 'Nancy Gas', 'Mr. Freeze', 'Professor Pete', 'Soggy Nell']
        base.localAvatar.setSystemMessage(0,'The VP Maxer will filter for 16 cards')
    
    def filterOff(self):
        self.filter=False
        base.localAvatar.setSystemMessage(0,'The VP Maxer will not filter bad cards')

    def exploit(self):
        Sequence(Func(self.destroyBattle), Wait(.5), Func(vpMaxer.otherFunctions.walk)).start()
        
    def endBattle(self):
        if base.cr.doFind('V. P'):
            base.cr.doFind('V. P').sendUpdate('hitBossInsides')
            base.cr.doFind('V. P').sendUpdate('hitBoss', [100])
            base.cr.doFind('V. P').sendUpdate('finalPieSplat')

    def start(self):
        if vpMaxer.otherFunctions.isMember:
            base.localAvatar.collisionsOff()
            vpMaxer.autoerGui.display.newLine('Starting Vice President')
            vpMaxer.autoerGui.display.newLine('Entering Lobby')
            base.cr.doFind('DistributedCogHQDoor').sendUpdate('requestEnter')
        else:
            vpMaxer.otherFunctions.walk()
            vpMaxer.autoerGui.display.newLine('Starting Vice President')
            vpMaxer.autoerGui.display.newLine('Teleporting to lobby')
            base.cr.playGame.getPlace().requestTeleport(11000,11100,None,None)
            
    def cardFilter(self):
        if base.cr.doFind('V. P').cagedToon.getName() in self.cardsWanted or not self.filter:
            return True
        else:
            return False
    
    def revertFunctions(self):
        DistributedSellbotBoss.DistributedSellbotBoss.enterElevator=self.oldBossEnterElevator
        DistributedSellbotBoss.DistributedSellbotBoss.enterBattleThree=self.oldEnterBattleThree
        DistributedSellbotBoss.DistributedSellbotBoss.enterPrepareBattleTwo=self.oldEnterPrepareBattleTwo
        DistributedSellbotBoss.DistributedSellbotBoss.enterPrepareBattleThree=self.oldEnterPrepareBattleThree
        DistributedSellbotBoss.DistributedSellbotBoss.enterEpilogue=self.oldEnterEpilogue
        DistributedSellbotBoss.DistributedSellbotBoss.enterRollToBattleTwo=self.oldEnterRollToBattleTwo
        DistributedBattleFinal.DistributedBattleFinal.enterWaitForInput=self.oldEnterWaitForInput
        DistributedSellbotBoss.DistributedSellbotBoss.enterIntroduction=self.oldBossEnterIntro
        DistributedCogHQDoor.DistributedCogHQDoor.avatarExit=self.oldAvatarExit
        CogHQLobby.CogHQLobby.enterWalk=self.oldEnterWalk
            
class FactoryAutoer:
    oldFactoryInit=FactoryExterior.FactoryExterior.__init__
    oldDistributedFactoryInit=DistributedFactory.DistributedFactory.__init__
    oldEnterReward=DistributedBattleFactory.DistributedBattleFactory.enterReward
    oldExitReward=DistributedBattleFactory.DistributedBattleFactory.exitReward
    oldEnterFactoryReward=DistributedBattleFactory.DistributedBattleFactory.enterFactoryReward
    
    def __init__(self,vpMaxer):
        self.roomNum=0
        self.zones=[4,7,8,13,22,24,34,32]
        self.roomValues=[28,36,32,56,32,40,80,56]
        self.gainLaffSeq=Sequence(Func(vpMaxer.restock.gainLaff),Wait(3.0))
        self.attackSeq=Sequence(Func(vpMaxer.restock.restock),Wait(1.0),Func(vpMaxer.otherFunctions.attack),Wait(1.0))
        
        FactoryExterior.FactoryExterior.__init__=lambda *args: self.newFactoryInit(*args)
        DistributedFactory.DistributedFactory.__init__=lambda *args: self.newDistributedFactoryInit(*args)
        DistributedBattleFactory.DistributedBattleFactory.enterReward=lambda newSelf,*args:self.newEnterReward(newSelf,*args)
        #DistributedBattleFactory.DistributedBattleFactory.exitReward=lambda newSelf,*args, **kwds:self.newExitReward(newSelf,*args,**kwds)
        base.cr.doFind('SafeZone').d_enterSafeZone=lambda *args: self.newSafeZone(*args)
        base.localAvatar.died=lambda *args: self.newSafeZone(*args)
        DistributedBattleFactory.DistributedBattleFactory.d_toonDied=lambda *args: self.newSafeZone(*args)
        DistributedBattleFactory.DistributedBattleFactory.enterFactoryReward=lambda newSelf,*args:self.newEnterFactoryReward(newSelf,*args)
                
    def enterBattle(self):
        if base.localAvatar.getHp()>0:
            if base.cr.doFindAll('battle')==[]:
                battles = []
                cogList = base.cr.doFindAll("render")
                for x in cogList:
                    if isinstance(x, DistributedFactorySuit) or isinstance(x, DistributedSuit):
                        if x.activeState == 6:
                            battles.append(x)
                try:
                    if battles != []:
                        battle=battles[0]
                        pos, hpr = battle.getPos(), battle.getHpr()
                        vpMaxer.otherFunctions.walk()
                        vpMaxer.restock.wasInBattle=False
                        base.localAvatar.collisionsOn()
                        base.localAvatar.setPosHpr(pos, hpr)
                        battle.d_requestBattle(pos, hpr)
                        return True
                    else:
                        self.warpToZone(self.roomsNeeded[self.roomNum])
                        return False
                except:
                    return False
            else:
                return False
        else:
            return False
    
    def newExitReward(self, newself, *args, **kwds):
        returnValue = self.oldExitReward(newSelf, *args,**kwds)
        '''
        if self.roomNum>=len(self.roomsNeeded):
            self.attackSeq.finish()
            self.gainLaffSeq.finish()
            self.generateAgain()
            vpMaxer.autoerGui.display.newLine('Error in completing factory')
            vpMaxer.autoerGui.display.newLine('No merits Recieved')
            Sequence(Wait(1),Func(vpMaxer.otherFunctions.walk),Func(vpMaxer.otherFunctions.teleBack)).start()
            
        else:
            #vpMaxer.otherFunctions.walk()
            Sequence(Wait(1), Func(self.newBattle)).start()
            pass
            ''',
        return returnValue
    
    def newEnterReward(self,newSelf,*args):
        
        if vpMaxer.otherFunctions.shouldContinue:
            newSelf._DistributedLevelBattle__handleFloorRewardDone()
            newSelf.d_rewardDone(base.localAvatar.doId)
            vpMaxer.otherFunctions.walk()
            vpMaxer.autoerGui.display.newLine('Finished Factory Battle '+str(self.roomNum))
            if self.roomNum>=len(self.roomsNeeded):
                self.attackSeq.finish()
                self.gainLaffSeq.finish()
                self.generateAgain()
                vpMaxer.autoerGui.display.newLine('Error in completing factory')
                vpMaxer.autoerGui.display.newLine('No merits Recieved')
                Sequence(Wait(1),Func(vpMaxer.otherFunctions.walk),Func(vpMaxer.otherFunctions.teleBack)).start()
            else:
                Sequence(Wait(5),Func(self.enterBattle)).start()
    
    def newEnterFactoryReward(self,newSelf,*args):
        self.oldEnterFactoryReward(newSelf,*args)
        if vpMaxer.otherFunctions.shouldContinue:
            newSelf._DistributedBattleFactory__handleFactoryRewardDone()
            self.attackSeq.finish()
            self.gainLaffSeq.finish()
            self.generateAgain()
            vpMaxer.autoerGui.display.newLine('Completed Factory')
            Sequence(Wait(1),Func(vpMaxer.otherFunctions.walk),Func(vpMaxer.otherFunctions.teleBack)).start()
                
    def newFactoryInit(self,*args):
        self.oldFactoryInit(*args)
        if vpMaxer.otherFunctions.shouldContinue:
            Sequence(Wait(2),Func(self.enterElevator)).start()
        
    def newDistributedFactoryInit(self,*args):
        self.oldDistributedFactoryInit(*args)
        if vpMaxer.otherFunctions.shouldContinue:
            vpMaxer.otherFunctions.walk()
            self.attackSeq.loop()
            self.gainLaffSeq.loop()
            self.roomNum=0
            self.workOutRoomsNeeded()
            vpMaxer.autoerGui.display.newLine('Entering Factory')
            Sequence(Wait(2),Func(self.warpToZone,self.roomsNeeded[self.roomNum])).start()
    
    def workOutRoomsNeeded(self):
        self.roomsNeeded=[]
        meritsNeeded=vpMaxer.otherFunctions.getMeritsLeft()
        meritsNeeded-=self.roomValues[-1]
        for i in range(7):
            if meritsNeeded>0:
                self.roomsNeeded.append(self.zones[i])
                meritsNeeded-=self.roomValues[i]
            else:
                break
        self.roomsNeeded.append(self.zones[-1])
            
    def warpToZone(self,zone):
        for factory in base.cr.doFindAll('Factory'):
            if hasattr(factory, 'warpToZone'):
                factory.warpToZone(zone)
                vpMaxer.autoerGui.display.newLine('Warping to Room '+str(self.roomNum+1))
                self.roomNum+=1
                break
        Sequence(Wait(1),Func(self.enterBattle)).start()
    
    def newSafeZone(self,*args):
        Sequence(Wait(1),Func(vpMaxer.otherFunctions.walk),Func(base.localAvatar.collisionsOff)).start()
        base.cr.doFind('SafeZone').sendUpdate('enterSafeZone')
        vpMaxer.restock.wasInBattle=True
        vpMaxer.autoerGui.display.newLine('Died, recovering')
        
    def preTele(self):
        DistributedTrolley.DistributedTrolley.__init__ = newInit
        DistributedPartyGate.DistributedPartyGate.__init__ = newInit
        DistributedDoor.DistributedDoor.__init__ = newInit
        base.localAvatar.stopLookAroundNow()
            
    def generateAgain(self):
        DistributedTrolley.DistributedTrolley.__init__ = oldTrolleyInit
        DistributedPartyGate.DistributedPartyGate.__init__ = oldPartyInit
        DistributedDoor.DistributedDoor.__init__ = oldDoorInit
        base.localAvatar.findSomethingToLookAt = vpMaxer.restock.oldFindSomethingToLookAt
        ToonHead.ToonHead._ToonHead__lookAround = vpMaxer.restock.oldLookAround
             
    def goFactory(self):
        vpMaxer.otherFunctions.walk()
        base.localAvatar.setWantBattles(True)
        vpMaxer.autoerGui.display.newLine('Heading to the factory')
        base.localAvatar.setPos(167.151, -157.024, -0.64781)
        
    def enterElevator(self):
        for elevator in base.cr.doFindAll("Elevator"):
            if elevator.getDestName()=='Front Entrance':
                vpMaxer.otherFunctions.walk()
                base.localAvatar.collisionsOff()
                vpMaxer.autoerGui.display.newLine('Teleporting to Factory')
                base.cr.doFind('Boarding').sendUpdate('requestLeave',[base.localAvatar.doId])
                base.cr.doFind('Boarding').sendUpdate('requestInvite',[base.localAvatar.doId])
                base.cr.doFind('Boarding').sendUpdate('requestGoToSecondTime',[elevator.doId])
                return
                
    def revertFunctions(self):
        FactoryExterior.FactoryExterior.__init__=self.oldFactoryInit
        DistributedFactory.DistributedFactory.__init__=self.oldDistributedFactoryInit
        DistributedBattleFactory.DistributedBattleFactory.enterReward=self.oldEnterReward
        DistributedBattleFactory.DistributedBattleFactory.enterFactoryReward=self.oldEnterFactoryReward
        base.cr.doFind('SafeZone').d_enterSafeZone=lambda *args: None
        base.localAvatar.died=lambda *args: None
        DistributedBattleFactory.DistributedBattleFactory.d_toonDied=lambda *args: None
        self.generateAgain()
        
class VPMaxer:
    def __init__(self):
        self.restock=restock()
        self.otherFunctions=OtherFunctions()
        self.vpAutoer=VpAutoer()
        self.factoryAutoer=FactoryAutoer(self)
        self.autoerGui=AutoerGui('VP Maxer',['Run Time',"Number of VP's","VP's/Hour",'Suit','Merits needed'],\
                                ['self.formattedTime','str(vpMaxer.otherFunctions.bossCount)',\
                                'str(self.workOutNumberAnHour(vpMaxer.otherFunctions.bossCount))',\
                                'str(vpMaxer.otherFunctions.numberToSuit[base.localAvatar.cogTypes[3]])+" lvl "+str(base.localAvatar.cogLevels[3]+1)','str(vpMaxer.otherFunctions.getMeritsLeft())'],\
                                'VP MXR','sell')
        
    def revert(self):
        self.restock.revertFunctions()
        self.factoryAutoer.revertFunctions()
        self.vpAutoer.revertFunctions()
        self.otherFunctions.revertFunctions()
        self.autoerGui.destroy()
        DistributedNPCFisherman.DistributedNPCFisherman.handleCollisionSphereEnter=oldHandleEnterCollisionSphereFisherman
        DistributedNPCPartyPerson.DistributedNPCPartyPerson.handleCollisionSphereEnter=oldHandleEnterCollisionSphereParty
        DistributedNPCFisherman.DistributedNPCFisherman.announceGenerate=oldFisherAnnounceGenerate
        DistributedNPCFisherman.DistributedNPCFisherman.initToonState=oldFishermanInitToonState
        DistributedNPCPartyPerson.DistributedNPCPartyPerson.announceGenerate=oldPartyPlannerAnnounceGenerate

global vpMaxer
vpMaxer=VPMaxer()