import random
from direct.interval.IntervalGlobal import *
from direct.distributed import DistributedObject
from toontown.distributed import ToontownClientRepository
from toontown.battle import DistributedBattleFinal
from toontown.battle import DistributedBattle
from toontown.toonbase import ToontownBattleGlobals
from toontown.toon import *
from toontown.coghq import DistributedCountryClubBattle
from toontown.coghq import DistributedCountryClub
from toontown.coghq import DistributedGolfGreenGame
from toontown.coghq import DistributedCogHQDoor
from toontown.coghq import CogDisguiseGlobals
from toontown.coghq import BossbotHQExterior
from toontown.coghq import CashbotHQExterior
from toontown.coghq import CountryClubInterior
from toontown.suit.DistributedMintSuit import DistributedMintSuit
from toontown.suit.DistributedSuit import DistributedSuit
from toontown.suit import DistributedBossbotBoss
from toontown.safezone import DDPlayground
from toontown.safezone import DistributedPartyGate
from toontown.safezone import DistributedTrolley
from toontown.building import DistributedDoor
from toontown.building import DistributedBoardingParty

ToontownBattleGlobals.SkipMovie=1
ToontownClientRepository.ToontownClientRepository.forbidCheesyEffects=lambda *x,**kwds: None
ToontownClientRepository.ToontownClientRepository.dumpAllSubShardObjects=lambda self: None

faceOffHook = lambda self, ts, name, callback:self.d_faceOffDone(self)
DistributedCountryClubBattle.DistributedCountryClubBattle._DistributedLevelBattle__faceOff = faceOffHook
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
        self.firstTrack=2
        self.secondTrack=0
        self.thirdTrack=4
        self.fourthTrack=3
        self.desiredLevel1=5
        self.desiredLevel2=4
        self.desiredLevel3=5
        self.desiredLevel4=5
        self.desiredInv='\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        self.maxCarryGags = base.localAvatar.getMaxCarry()
        self.gagshop_zoneId = 4503
        self.noToons=Sequence(Func(self.removeToons), Wait(1.5))
        self.noTrolley=False
        self.unloaded=True
        self.wasInBattle=False
        
        DistributedNPCFisherman.DistributedNPCFisherman.announceGenerate = newFishermanAnnounceGenerate
        DistributedNPCPartyPerson.DistributedNPCPartyPerson.announceGenerate = newPartyPlannerAnnounceGenerate
        
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
                
    def gainLaff(self):
        if base.localAvatar.getHp()!=base.localAvatar.getMaxHp():
            if self.unloaded:
                ceoMaxer.countryClubAutoer.preTele()
                self.interest1=base.cr.addInterest(base.localAvatar.defaultShard, 9000, 5, None)
                self.interest2=base.cr.addInterest(base.localAvatar.defaultShard, 3000, 5, None)
                self.unloaded=False
            self.collectLaff()
        if self.wasInBattle:
            ceoMaxer.countryClubAutoer.enterBattle()
     
    def loadGagshop(self):           
        if not base.cr.doFind('Clerk'):
            self.contextId = base.cr.addInterest(base.localAvatar.defaultShard, self.gagshop_zoneId, 4, event=None)
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
        self.noToons.finish()
        try:
            base.cr.removeInterest(self.interest1)
            base.cr.removeInterest(self.interest2)
            self.unloaded=True
        except:
            pass

class OtherFunctions:
    oldDockEnterTeleportIn=DDPlayground.DDPlayground.enterTeleportIn
    oldBossEnterWalk=BossbotHQExterior.BossbotHQExterior.enterWalk
    oldCashEnterWalk=CashbotHQExterior.CashbotHQExterior.enterWalk
    oldEnterReward=DistributedBattle.DistributedBattle.enterReward
    oldDenyBattle=DistributedSuit.denyBattle
    oldSendUpdate=DistributedObject.DistributedObject.sendUpdate
    oldEnterHealth=HealthForceAcknowledge.HealthForceAcknowledge.enter
    oldSetAnim=LocalToon.LocalToon.setAnimState
    oldPostInvite=DistributedBoardingParty.DistributedBoardingParty.postInvite
    oldNpcFreeAvatar=DistributedNPCToonBase.DistributedNPCToonBase.freeAvatar
    
    def __init__(self):
        self.shouldContinue=False
        self.bossCount=0
        self.limit10=True
        self.onlyClub=False
        self.isHealing=False
        self.canSetParentAgain=True
        self.numberToSuit={0:'Flunky',1:'Pencil Pusher',2:'Yesman',3:'Micromanager',
                           4:'Downsizer',5:'Head Hunter',6:'Corporate Raider',7:'The Big Cheese'}
        DDPlayground.DDPlayground.enterTeleportIn=lambda newSelf,*args:self.newDockEnterTeleportIn(newSelf,*args)
        BossbotHQExterior.BossbotHQExterior.enterWalk=lambda newSelf,*args: self.newBossEnterWalk(newSelf,*args)
        CashbotHQExterior.CashbotHQExterior.enterWalk=lambda newSelf,*args: self.newCashEnterWalk(newSelf,*args)
        DistributedBattle.DistributedBattle.enterReward=lambda newSelf,*args: self.newEnterReward(newSelf,*args)
        DistributedSuit.denyBattle=lambda *args: self.newDenyBattle(*args)
        LocalToon.LocalToon.setAnimState=lambda *args,**kwds:self.newSetAnimState(*args,**kwds)
        HealthForceAcknowledge.HealthForceAcknowledge.enter=lambda newSelf,hplevel: self.newEnterHealth(newSelf,hplevel)
        DistributedBoardingParty.DistributedBoardingParty.postInvite=lambda newSelf,leaderId,inviterId: self.newPostInvite(newSelf,leaderId,inviterId)
        DistributedNPCToonBase.DistributedNPCToonBase.freeAvatar=lambda *args: None

    def attack(self):
        try:
            for battle in base.cr.doFindAll('battle'):
                if base.localAvatar.inventory.inventory[ceoMaxer.restock.firstTrack][ceoMaxer.restock.desiredLevel1]>0:
                    battle.sendUpdate('requestAttack', [ceoMaxer.restock.firstTrack, ceoMaxer.restock.desiredLevel1, battle.suits[0].doId])
                else:
                    break
                    
                if base.localAvatar.getHp()<(base.localAvatar.getMaxHp()*0.9) or self.isHealing:
                
                    if base.localAvatar.inventory.inventory[ceoMaxer.restock.secondTrack][ceoMaxer.restock.desiredLevel2]>0:
                        battle.sendUpdate('requestAttack', [ceoMaxer.restock.secondTrack, ceoMaxer.restock.desiredLevel2, base.localAvatar.doId])
                    else:
                        break
                        
                    if base.localAvatar.inventory.inventory[ceoMaxer.restock.thirdTrack][ceoMaxer.restock.desiredLevel3]>0:
                        battle.sendUpdate('requestAttack', [ceoMaxer.restock.thirdTrack, ceoMaxer.restock.desiredLevel3, battle.suits[0].doId])
                    else:
                        break
                        
                else:
                    if base.localAvatar.inventory.inventory[ceoMaxer.restock.thirdTrack][ceoMaxer.restock.desiredLevel3]>0:
                        battle.sendUpdate('requestAttack', [ceoMaxer.restock.thirdTrack, ceoMaxer.restock.desiredLevel3, battle.suits[0].doId])
                    else:
                        break
        except:
            pass
            
    def sendUpdateHook(self, newself, fieldName, args=[], sendToId=None):
        if fieldName=="requestAttack":
            self.oldSendUpdate(newself,"requestAttack", args, sendToId)
            self.oldSendUpdate(newself,"movieDone",[])
            newself.d_rewardDone(base.localAvatar.doId)
        else:
            self.oldSendUpdate(newself,fieldName, args, sendToId)
        
    def newDockEnterTeleportIn(self,newSelf,*args):
        self.oldDockEnterTeleportIn(newSelf,*args)
        if self.shouldContinue: 
            ceoMaxer.countryClubAutoer.gainLaffSeq.finish()
            ceoMaxer.countryClubAutoer.attackSeq.finish()
            Sequence(Wait(2),Func(self.checkStocks)).start()
    
    def newPostInvite(self,newSelf,leaderId,inviterId):
        if leaderId==base.localAvatar.doId:
            newSelf.sendUpdate('requestAcceptInvite',[inviterId,leaderId])
        else:
            self.oldPostInvite(newSelf,leaderId,inviterId)
    
    def newEnterHealth(self,newSelf,hplevel):
        try:
            self.oldEnterHealth(newSelf,hplevel)
            newSelf.handleOk(base.localAvatar.getHp())
            newSelf.exit()
            if self.shouldContinue:
                Sequence(Wait(2),Func(self.checkStocks)).start()
        except:
            pass
         
    def newCashEnterWalk(self,newSelf,*args):
        self.oldCashEnterWalk(newSelf,*args)
        if len(args)>0:
            if self.shouldContinue and args[0]:
                ceoMaxer.countryClubAutoer.attackSeq.loop()
                self.enterRandomBattle()
    
    def newBossEnterWalk(self,newSelf,*args):
        self.oldBossEnterWalk(newSelf,*args)
        if len(args)>0:
            if self.shouldContinue and args[0]:
                self.checkStocks()
    
    def newEnterReward(self,newSelf,*args):
        self.oldEnterReward(newSelf,*args)
        if self.shouldContinue and self.isHealing:
            if base.localAvatar.getHp()>105:
                self.isHealing=False
                ceoMaxer.countryClubAutoer.attackSeq.finish()
                Sequence(Wait(2),Func(self.teleBack)).start()
            else:
                self.enterRandomBattle()
     
    def newDenyBattle(self,*args):
        self.oldDenyBattle(*args)
        if self.shouldContinue and self.isHealing and self.lastCogId==args[0].doId:
            self.enterRandomBattle()
            
    def newSetAnimState(self,*args,**kwds):
        self.oldSetAnim(*args,**kwds)
        if self.canSetParentAgain:
            base.localAvatar.d_setParent(1)
            self.canSetParentAgain=False
            Sequence(Wait(1),Func(self.doUnsetCanSetParentAgain)).start()
            
    def doUnsetCanSetParentAgain(self):
        self.canSetParentAgain=True
        
    def checkStocks(self):
        if self.onlyClub:
            base.localAvatar.cogMerits[0]=-4000
        if self.limit10 and self.bossCount>9:
            self.shouldContinue=False
        if self.shouldEnd:
            self.shouldContinue=False
        if self.haveJb():
            if self.shouldContinue:
                if self.getStocksLeft()==0 and not self.onlyClub:
                    if base.cr.doFind('DistributedCogHQDoor') and base.localAvatar.getZoneId()>=10000 and base.localAvatar.getZoneId()<10100:
                        ceoMaxer.ceoAutoer.start()
                    else:
                        ceoMaxer.restock.restock()
                        ceoMaxer.restock.collectLaff()
                        self.walk()
                        ceoMaxer.autoerGui.display.newLine('Teleporting to bossbot hq')
                        self.teleBack()
                else:
                    if base.cr.doFind('DistributedCogHQDoor') and base.localAvatar.getZoneId()>=10000 and base.localAvatar.getZoneId()<10100:
                        if base.localAvatar.getHp()>105:
                            ceoMaxer.countryClubAutoer.start()
                        else:
                            self.isHealing=True
                            ceoMaxer.autoerGui.display.newLine('Gaining laff back')
                            ceoMaxer.restock.restock()
                            ceoMaxer.restock.collectLaff()
                            self.walk()
                            self.teleBack(12000)
                    else:
                        ceoMaxer.restock.restock()
                        ceoMaxer.restock.collectLaff()
                        self.walk()
                        if base.localAvatar.getHp()>105:
                            ceoMaxer.autoerGui.display.newLine('Teleporting to bossbot hq')
                            self.walk()
                            self.teleBack()
                        else:
                            self.isHealing=True
                            ceoMaxer.autoerGui.display.newLine('Gaining laff back')
                            self.walk()
                            self.teleBack(12000)
            else:
                ceoMaxer.restock.noToons.finish()
                try:
                    base.cr.removeInterest(ceoMaxer.restock.interest1)
                    base.cr.removeInterest(ceoMaxer.restock.interest2)
                    ceoMaxer.restock.unloaded=True
                except:
                    pass
                base.localAvatar.setSystemMessage(0,"Thanks for using freshollie's ceo maxer")
                ceoMaxer.autoerGui.display.newLine('Stopped')
        else:
            ceoMaxer.autoerGui.display.newLine('Out of jellybeans')
            base.localAvatar.setSystemMessage(0,'You have run out of jelly beans, please use the fishing code to gain some')
    
    def getStocksLeft(self):
        return CogDisguiseGlobals.getTotalMerits(base.localAvatar,0)-base.localAvatar.cogMerits[0]

    def walk(self):
        try:
            base.cr.playGame.getPlace().fsm.forceTransition('walk')
        except:
            pass
       
    def teleBack(self,zone=10000):
        try:
            self.walk()
            base.cr.playGame.getPlace().handleBookCloseTeleport(zone, zone)
        except:
            pass
                
    def onlyDoClub(self):
        self.onlyClub=True
        base.localAvatar.setSystemMessage(0,'CEO maxer set to only do the Country Club')
    
    def doBoth(self):
        self.onlyClub=False
        base.localAvatar.setSystemMessage(0,'CEO maxer set to do both the Country Club and the CEO')
        
    def haveJb(self):
        if base.localAvatar.cogLevels[0]==49:
            return True
        elif base.localAvatar.getTotalMoney()<100:
            return False
        else:
            return True
           
    def enterRandomBattle(self):
        battles = []
        cogList = base.cr.doFindAll("render")
        for x in cogList:
            if isinstance(x, DistributedSuit):
                if x.activeState == 6:
                    battles.append(x)
        if battles != []:
            self.walk()
            battle = random.choice(battles)
            pos, hpr = battle.getPos(), battle.getHpr()
            base.localAvatar.setPosHpr(pos, hpr)
            battle.d_requestBattle(pos, hpr)
            self.lastCogId=battle.doId
        else:
            pass
        
    def limiterOn(self):
        self.limit10=True
        base.localAvatar.setSystemMessage(0,'CEO maxer set to be limited to only 10 CEOs')
    
    def limiterOff(self):
        self.limit10=False
        base.localAvatar.setSystemMessage(0,'CEO maxer set to unlimited number of CEOs')
        
    def setStop(self):
        self.shouldEnd=True
        base.localAvatar.setSystemMessage(1,"The Autoer will stop at the end of this run")
        ceoMaxer.autoerGui.stopTimer()
    
    def start(self):
        DistributedObject.DistributedObject.sendUpdate=lambda newself, fieldName, args=[], sendToId=None: self.sendUpdateHook(newself, fieldName, args, sendToId)
        self.bossCount=0
        self.shouldContinue=True
        self.shouldEnd=False
        ceoMaxer.autoerGui.startTimer()
        emptyShardList=[]
        for shard in base.cr.activeDistrictMap:
            if base.cr.activeDistrictMap[shard].avatarCount<30:
                emptyShardList.append(shard)
        if emptyShardList==[]:
            emptyShardList=[650000000, 754000000, 608000000, 756000000, 658000000, 712000000, 360000000, 410000000, 620000000, 454000000, 726000000, 362000000, 688000000, 316000000]
        if base.localAvatar.defaultShard not in emptyShardList:
            ceoMaxer.autoerGui.display.newLine('TPing to an empty district')
            base.cr.playGame.getPlace().requestTeleport(10000,10000,random.choice(emptyShardList),None)
        else:
            self.checkStocks()
        ceoMaxer.restock.noToons.loop()
    
    def revertFunctions(self):
        DDPlayground.DDPlayground.enterTeleportIn=self.oldDockEnterTeleportIn
        BossbotHQExterior.BossbotHQExterior.enterWalk=self.oldBossEnterWalk
        CashbotHQExterior.CashbotHQExterior.enterWalk=self.oldCashEnterWalk
        DistributedBattle.DistributedBattle.enterReward=self.oldEnterReward
        DistributedSuit.denyBattle=self.oldDenyBattle
        DistributedObject.DistributedObject.sendUpdate=self.oldSendUpdate
        HealthForceAcknowledge.HealthForceAcknowledge.enter=self.oldEnterHealth
        DistributedBoardingParty.DistributedBoardingParty.postInvite=self.oldPostInvite
        LocalToon.LocalToon.setAnimState=self.oldSetAnim
        DistributedNPCToonBase.DistributedNPCToonBase.freeAvatar=self.oldNpcFreeAvatar
    
class CeoAutoer:
    oldBossEnterElevator=DistributedBossbotBoss.DistributedBossbotBoss.enterElevator
    oldEnterBattleTwo=DistributedBossbotBoss.DistributedBossbotBoss.enterBattleTwo
    oldEnterBattleFour=DistributedBossbotBoss.DistributedBossbotBoss.enterBattleFour
    oldEnterPrepareBattleTwo=DistributedBossbotBoss.DistributedBossbotBoss.enterPrepareBattleTwo
    oldEnterPrepareBattleThree=DistributedBossbotBoss.DistributedBossbotBoss.enterPrepareBattleThree
    oldEnterPrepareBattleFour=DistributedBossbotBoss.DistributedBossbotBoss.enterPrepareBattleFour
    oldEnterEpilogue=DistributedBossbotBoss.DistributedBossbotBoss.enterEpilogue
    oldEnterWaitForInput=DistributedBattleFinal.DistributedBattleFinal.enterWaitForInput
    oldBossEnterIntro=DistributedBossbotBoss.DistributedBossbotBoss.enterIntroduction
    oldAvatarExit=DistributedCogHQDoor.DistributedCogHQDoor.avatarExit
    
    def __init__(self):
        DistributedCogHQDoor.DistributedCogHQDoor.avatarExit=lambda newSelf,id: self.newAvatarExit(newSelf,id)
        DistributedBossbotBoss.DistributedBossbotBoss.enterElevator=lambda newSelf: self.newBossEnterElevator(newSelf)
        DistributedBossbotBoss.DistributedBossbotBoss.enterIntroduction=lambda newSelf,*args: self.newBossEnterIntro(newSelf,*args)
        DistributedBossbotBoss.DistributedBossbotBoss.enterBattleFour=lambda newSelf: self.newEnterBattleFour(newSelf)
        DistributedBossbotBoss.DistributedBossbotBoss.enterBattleTwo=lambda newSelf: self.newEnterBattleTwo(newSelf)
        DistributedBattleFinal.DistributedBattleFinal.enterWaitForInput=lambda *args: self.newEnterWaitForInput(*args)
        DistributedBossbotBoss.DistributedBossbotBoss.enterPrepareBattleThree=lambda newSelf: self.newEnterPrepareBattleThree(newSelf)
        DistributedBossbotBoss.DistributedBossbotBoss.enterPrepareBattleTwo=lambda newSelf: self.newEnterPrepareBattleTwo(newSelf)
        DistributedBossbotBoss.DistributedBossbotBoss.enterPrepareBattleFour=lambda newSelf: self.newEnterPrepareBattleFour(newSelf)
        DistributedBossbotBoss.DistributedBossbotBoss.enterEpilogue=lambda newSelf: self.newEnterEpilogue(newSelf)
    
    def newAvatarExit(self,newSelf,id):
        self.oldAvatarExit(newSelf,id)
        if base.cr.doFind('Elevator') and id==base.localAvatar.doId and ceoMaxer.otherFunctions.shouldContinue:
            ceoMaxer.otherFunctions.walk()
            ceoMaxer.autoerGui.display.newLine('Heading to CEO')
            base.cr.doFind('Boarding').sendUpdate('requestInvite',[base.localAvatar.doId])
            base.cr.doFind('Boarding').sendUpdate('requestGoToSecondTime',[base.cr.doFind('Elevator').doId])
    
    def newBossEnterIntro(self,newSelf,*args):
        self.oldBossEnterIntro(newSelf,*args)
        if ceoMaxer.otherFunctions.shouldContinue:
            newSelf.exitIntroduction()
            ceoMaxer.autoerGui.display.newLine('Skipping CEO introduction')
    
    def newEnterPrepareBattleTwo(self,newSelf):
        self.oldEnterPrepareBattleTwo(newSelf)
        if ceoMaxer.otherFunctions.shouldContinue:
            newSelf.exitPrepareBattleTwo()
            ceoMaxer.autoerGui.display.newLine('Skipping cutscene')
    
    def newEnterEpilogue(self,newSelf):
        self.oldEnterEpilogue(newSelf)
        if ceoMaxer.otherFunctions.shouldContinue:
            ceoMaxer.otherFunctions.bossCount+=1
            ceoMaxer.otherFunctions.teleBack()
            ceoMaxer.autoerGui.display.newLine('Finished CEO')
    
    def newEnterPrepareBattleThree(self,newSelf):
        self.oldEnterPrepareBattleThree(newSelf)
        newSelf.exitPrepareBattleThree()
        ceoMaxer.autoerGui.display.newLine('Skipping cutscene')
    
    def newEnterPrepareBattleFour(self,newSelf):
        self.oldEnterPrepareBattleFour(newSelf)
        newSelf.exitPrepareBattleFour()
        ceoMaxer.autoerGui.display.newLine('Skipping cutscene')
    
    def destroyBattle(self):
        base.cr.doFind('SafeZone').sendUpdate('enterSafeZone')
    
    def exploit(self):
        Sequence(Func(self.destroyBattle), Wait(.5), Func(ceoMaxer.otherFunctions.walk)).start()
    
    def newEnterWaitForInput(self,*args):
        self.oldEnterWaitForInput(*args)
        if ceoMaxer.otherFunctions.shouldContinue:
            self.exploit()
            ceoMaxer.autoerGui.display.newLine('Skipping Battle')
    
    def newBossEnterElevator(self,newSelf):
        self.oldBossEnterElevator(newSelf)
        if ceoMaxer.otherFunctions.shouldContinue:
            ceoMaxer.autoerGui.display.newLine('Skipping Elevator')
            newSelf._DistributedBossCog__doneElevator()
    
    def newEnterBattleTwo(self,newSelf):
        self.oldEnterBattleTwo(newSelf)
        ceoMaxer.autoerGui.display.newLine('Waiting for timer')
        
    def newEnterBattleFour(self,newSelf):
        self.oldEnterBattleFour(newSelf)
        self.endBattle(newSelf)
        
    def start(self):
        base.cr.doFind('DistributedCogHQDoor').sendUpdate('requestEnter')
        ceoMaxer.autoerGui.display.newLine('Starting the CEO')
        ceoMaxer.autoerGui.display.newLine('Entering Lobby')
        
    def endBattle(self,newSelf):
        newSelf.sendUpdate('hitBoss', [250])
        ceoMaxer.autoerGui.display.newLine('Killing CEO')
        newSelf.exitBattleFour()
        
    def revertFunctions(self):   
        DistributedBossbotBoss.DistributedBossbotBoss.enterElevator=self.oldBossEnterElevator
        DistributedBossbotBoss.DistributedBossbotBoss.enterBattleTwo=self.oldEnterBattleTwo
        DistributedBossbotBoss.DistributedBossbotBoss.enterBattleFour=self.oldEnterBattleFour
        DistributedBossbotBoss.DistributedBossbotBoss.enterPrepareBattleTwo=self.oldEnterPrepareBattleTwo
        DistributedBossbotBoss.DistributedBossbotBoss.enterPrepareBattleThree=self.oldEnterPrepareBattleThree
        DistributedBossbotBoss.DistributedBossbotBoss.enterPrepareBattleFour=self.oldEnterPrepareBattleFour
        DistributedBossbotBoss.DistributedBossbotBoss.enterEpilogue=self.oldEnterEpilogue
        DistributedBattleFinal.DistributedBattleFinal.enterWaitForInput=self.oldEnterWaitForInput
        DistributedBossbotBoss.DistributedBossbotBoss.enterIntroduction=self.oldBossEnterIntro
        DistributedCogHQDoor.DistributedCogHQDoor.avatarExit=self.oldAvatarExit      
        
class CountryClubAutoer:
    oldCountryClubInit=DistributedCountryClub.DistributedCountryClub.__init__
    oldEnterReward=DistributedCountryClubBattle.DistributedCountryClubBattle.enterReward
    oldGolfGameToonEnter=DistributedGolfGreenGame.DistributedGolfGreenGame._DistributedGolfGreenGame__handleToonEnter
    oldEnterCountryClubReward=DistributedCountryClubBattle.DistributedCountryClubBattle.enterCountryClubReward
    
    def __init__(self,ceoMaxer): 
        self.attackSeq=Sequence(Func(ceoMaxer.restock.restock),Wait(1.0),Func(ceoMaxer.otherFunctions.attack),Wait(1.0))
        self.gainLaffSeq=Sequence(Func(ceoMaxer.restock.gainLaff),Wait(3.0))
        self.battleNum=1
        DistributedCountryClub.DistributedCountryClub.__init__=lambda *args:self.newCountryClubInit(*args)
        DistributedCountryClubBattle.DistributedCountryClubBattle.enterReward=lambda *args:self.newEnterReward(*args)
        DistributedGolfGreenGame.DistributedGolfGreenGame._DistributedGolfGreenGame__handleToonEnter=lambda *args:self.newGolfGameToonEnter(*args)
        base.localAvatar.died=lambda *args: self.newSafeZone(*args)
        DistributedCountryClubBattle.DistributedCountryClubBattle.enterCountryClubReward=lambda *args:self.newEnterCountryClubReward(*args)
    
    def setFrontThree(self):
        self.floorNumToKartRoomNum={0:17,1:17,2:18}
        self.battles=[1,3,5]
        self.greenRoom=9
        self.countryClubName='The Front Three'

    def setMiddleSix(self):
        self.greenRoom=29 
        self.battles=[1,3,5,7,9,11]
        self.floorNumToKartRoomNum={0:17,1:17,2:17,3:17,4:17,5:18}
        self.countryClubName='The Middle Six'
    
    def setBackNine(self):
        self.greenRoom=39
        self.battles=[1,3,5,7,9,11,13,15,17]
        self.floorNumToKartRoomNum={0:17,1:17,2:17,3:17,4:17,5:17,6:17,7:17,8:18}
        self.countryClubName='The Back Nine'
        
    def preTele(self):
        DistributedTrolley.DistributedTrolley.__init__ = newInit
        DistributedPartyGate.DistributedPartyGate.__init__ = newInit
        DistributedDoor.DistributedDoor.__init__ = newInit
        base.localAvatar.stopLookAroundNow()
            
    def generateAgain(self):
        DistributedTrolley.DistributedTrolley.__init__ = oldTrolleyInit
        DistributedPartyGate.DistributedPartyGate.__init__ = oldPartyInit
        DistributedDoor.DistributedDoor.__init__ = oldDoorInit
        base.localAvatar.findSomethingToLookAt = ceoMaxer.restock.oldFindSomethingToLookAt
        ToonHead.ToonHead._ToonHead__lookAround = ceoMaxer.restock.oldLookAround

    def enterBattle(self):
        if base.localAvatar.getHp()>0:
            ceoMaxer.restock.wasInBattle=False
            battles = []
            cogList = base.cr.doFindAll("render")
            for x in cogList:
                if isinstance(x, DistributedMintSuit):
                    if x.activeState == 6:
                        if self.battleNum in self.battles:
                            if x.doId not in base.cr.doFind('DistributedCountryClubRoom '+str(self.floorNumToKartRoomNum[base.cr.doFind('DistributedCountryClub.DistributedCountryClub').floorNum])).suitIds:
                                battles.append(x)
                        else:
                            if x.doId in base.cr.doFind('DistributedCountryClubRoom '+str(self.floorNumToKartRoomNum[base.cr.doFind('DistributedCountryClub.DistributedCountryClub').floorNum])).suitIds:
                                battles.append(x)
                            
            if battles != []:
                battle=battles[0]
                ceoMaxer.otherFunctions.walk()
                pos, hpr = battle.getPos(), battle.getHpr()
                base.localAvatar.collisionsOn()
                base.localAvatar.setPosHpr(pos, hpr)
                battle.d_requestBattle(pos, hpr)
                ceoMaxer.autoerGui.display.newLine('Entering Battle '+str(self.battleNum))
                return True
            else:
                return False
        else:
            return True
    
    def doMoles(self):
        moleSeq=Sequence()
        ceoMaxer.autoerGui.display.newLine('Entering Floor '+str(base.cr.doFind('DistributedCountryClub.DistributedCountryClub').floorNum+1))
        ceoMaxer.autoerGui.display.newLine('Completing Mole Field')
        for moleField in base.cr.doFindAll('MoleField'):
            for i in range(moleField.numMoles):
                moleSeq.append(Func(moleField.sendUpdate,'whackedMole', [0, i]))
                moleSeq.append(Wait(0.05))
        moleSeq.append(Wait(0.5))
        moleSeq.append(Func(self.enterBattle))
        moleSeq.start()
            
    def doGolf(self):
        gameSeq=Sequence()
        ceoMaxer.autoerGui.display.newLine('Completing Golf')
        for greenGame in base.cr.doFindAll('GolfGreenGame'):
            for i in range(greenGame.boardsLeft):
                gameSeq.append(Func(greenGame.sendUpdate,'requestBoard', [1]))
        gameSeq.append(Wait(2))
        gameSeq.append(Func(self.endFloor))
        gameSeq.start()
        
    def enterCountryClub(self):
        for kart in base.cr.doFindAll('DistributedCogKart'):
            if kart.getDestName()==self.countryClubName:
                base.cr.doFind('Boarding').sendUpdate('requestInvite',[base.localAvatar.doId])
                base.cr.doFind('Boarding').sendUpdate('requestGoToSecondTime',[kart.doId])
                break
    
    def boardKart(self):
        ceoMaxer.otherFunctions.walk()
        self.attackSeq.finish()
        self.gainLaffSeq.finish()
        for kart in base.cr.doFindAll('DistributedClubElevator'):
            kart.handleEnterSphere(base.localAvatar.doId)
            ceoMaxer.autoerGui.display.newLine('Boarding Kart')
            return
        ceoMaxer.otherFunctions.walk()
        ceoMaxer.autoerGui.display.newLine('Finishing Country Club')
        ceoMaxer.otherFunctions.teleBack()
        self.generateAgain()
    
    def warpToRoom(self,room):
        if base.cr.doFind('DistributedCountryClub.DistributedCountryClub'):
            base.cr.doFind('DistributedCountryClub.DistributedCountryClub').warpToRoom(room)
                
    def newCountryClubInit(self,*args):
        self.oldCountryClubInit(*args)
        self.attackSeq.loop()
        self.gainLaffSeq.loop()
        Sequence(Wait(3),Func(self.doMoles)).start()
    
    def newGolfGameToonEnter(self,*args):
        self.oldGolfGameToonEnter(*args)
        if ceoMaxer.otherFunctions.shouldContinue:
            Sequence(Wait(3),Func(self.doGolf)).start()
    
    def newEnterReward(self,*args):
        self.oldEnterReward(*args)
        if ceoMaxer.otherFunctions.shouldContinue:
            ceoMaxer.autoerGui.display.newLine('Finished Battle '+str(self.battleNum))
            base.cr.doFind('battle').d_rewardDone(base.localAvatar.doId)
            self.battleNum+=1
            ceoMaxer.otherFunctions.walk()
            if not self.enterBattle():
                self.warpToRoom(self.greenRoom)
                ceoMaxer.otherFunctions.walk()
    
    def newSafeZone(self,*args):
        Sequence(Wait(1),Func(ceoMaxer.otherFunctions.walk)).start()
        ceoMaxer.restock.wasInBattle=True
        ceoMaxer.autoerGui.display.newLine('Died, recovering')

    def newEnterCountryClubReward(self,*args):
        self.oldEnterCountryClubReward(*args)
        if ceoMaxer.otherFunctions.shouldContinue:
            ceoMaxer.autoerGui.display.newLine('Finished Predident')
            Sequence(Wait(1.5),Func(self.boardKart)).start()

    def endFloor(self):
        ceoMaxer.otherFunctions.walk()
        self.warpToRoom(self.floorNumToKartRoomNum[base.cr.doFind('DistributedCountryClub.DistributedCountryClub').floorNum])
        Sequence(Wait(1),Func(self.boardKart)).start()
    
    def start(self):
        self.battleNum=1
        if ceoMaxer.otherFunctions.getStocksLeft()>953 and base.localAvatar.getCogParts()[0]!=0:
            ceoMaxer.autoerGui.display.newLine('Entering The Back Nine')
            self.setBackNine()
        elif ceoMaxer.otherFunctions.getStocksLeft()>386 and base.localAvatar.getCogParts()[0]!=0:
            ceoMaxer.autoerGui.display.newLine('Entering The Middle Six')
            self.setMiddleSix()
        else:
            ceoMaxer.autoerGui.display.newLine('Entering The Front Three')
            self.setFrontThree()
        Sequence(Wait(1),Func(self.enterCountryClub)).start()
    
    def revertFunctions(self):
        DistributedCountryClub.DistributedCountryClub.__init__=self.oldCountryClubInit
        DistributedCountryClubBattle.DistributedCountryClubBattle.enterReward=self.oldEnterReward
        DistributedGolfGreenGame.DistributedGolfGreenGame._DistributedGolfGreenGame__handleToonEnter=self.oldGolfGameToonEnter
        DistributedCountryClubBattle.DistributedCountryClubBattle.enterCountryClubReward=self.oldEnterCountryClubReward
        base.localAvatar.died=lambda *args: None
        self.generateAgain()

class CEOMaxer:

    def __init__(self):
        self.restock=restock()
        self.otherFunctions=OtherFunctions()
        self.ceoAutoer=CeoAutoer()
        self.countryClubAutoer=CountryClubAutoer(self)
        self.autoerGui=AutoerGui('CEO Maxer',['Run Time',"Number of ceo's","Ceo's/Hour",'Suit','Stocks needed'],\
                                ['self.hours+":"+self.minutes+":"+self.seconds','str(ceoMaxer.otherFunctions.bossCount)','str(self.workOutNumberAnHour(ceoMaxer.otherFunctions.bossCount))'\
                                ,'str(ceoMaxer.otherFunctions.numberToSuit[base.localAvatar.cogTypes[0]])+" Lvl "+str(base.localAvatar.cogLevels[0]+1)','str(ceoMaxer.otherFunctions.getStocksLeft())'],\
                                'CEO MXR','boss')
        
    def revert(self):
        self.restock.revertFunctions()
        self.countryClubAutoer.revertFunctions()
        self.ceoAutoer.revertFunctions()
        self.otherFunctions.revertFunctions()
        self.autoerGui.destroy()
        DistributedNPCFisherman.DistributedNPCFisherman.handleCollisionSphereEnter=oldHandleEnterCollisionSphereFisherman
        DistributedNPCPartyPerson.DistributedNPCPartyPerson.handleCollisionSphereEnter=oldHandleEnterCollisionSphereParty
        DistributedNPCFisherman.DistributedNPCFisherman.announceGenerate=oldFisherAnnounceGenerate
        DistributedNPCPartyPerson.DistributedNPCPartyPerson.announceGenerate=oldPartyPlannerAnnounceGenerate
        
ceoMaxer=CEOMaxer()
