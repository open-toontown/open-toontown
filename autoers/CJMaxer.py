import random
from direct.interval.IntervalGlobal import *
from direct.distributed import DistributedObject
from toontown.distributed import ToontownClientRepository
from toontown.battle import DistributedBattleFinal
from toontown.toonbase import ToontownBattleGlobals
from toontown.toon import *
from toontown.battle import DistributedBattle
from toontown.coghq import DistributedCogHQDoor
from toontown.coghq import CogDisguiseGlobals
from toontown.coghq import DistributedStage
from toontown.coghq import DistributedStageBattle
from toontown.coghq import DistributedLawOfficeElevatorExt
from toontown.coghq import LawbotHQExterior
from toontown.suit.DistributedMintSuit import DistributedMintSuit
from toontown.suit.DistributedSuit import DistributedSuit
from toontown.suit import DistributedLawbotBoss
from toontown.safezone import BRPlayground
from toontown.safezone import DistributedPartyGate
from toontown.safezone import DistributedTrolley
from toontown.building import DistributedDoor
from toontown.building import DistributedBoardingParty

ToontownBattleGlobals.SkipMovie=1
ToontownClientRepository.ToontownClientRepository.dumpAllSubShardObjects=lambda self: None
ToontownClientRepository.ToontownClientRepository.forbidCheesyEffects=lambda *x,**kwds: None

faceOffHook = lambda self, ts, name, callback:self.d_faceOffDone(self)
DistributedStageBattle.DistributedStageBattle._DistributedLevelBattle__faceOff = faceOffHook
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
                cjMaxer.daAutoer.preTele()
                self.interest1=base.cr.addInterest(base.localAvatar.defaultShard, 9000, 5, None)
                self.interest2=base.cr.addInterest(base.localAvatar.defaultShard, 3000, 5, None)
                self.unloaded=False
                Sequence(Wait(3),Func(cjMaxer.daAutoer.generateAgain)).start()
            self.collectLaff()
        if self.wasInBattle:
            cjMaxer.daAutoer.enterBattle()
     
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
    oldBrrInit=BRPlayground.BRPlayground.__init__
    oldEnterWalk=LawbotHQExterior.LawbotHQExterior.enterWalk
    oldEnterReward=DistributedBattle.DistributedBattle.enterReward
    oldDenyBattle=DistributedSuit.denyBattle
    oldSendUpdate=DistributedObject.DistributedObject.sendUpdate
    oldEnterHealth=HealthForceAcknowledge.HealthForceAcknowledge.enter
    oldPostInvite=DistributedBoardingParty.DistributedBoardingParty.postInvite
    
    
    def __init__(self):
        self.shouldContinue=False
        self.lastCogId=0
        self.bossCount=0
        self.onlyDA=False
        self.canSetParentAgain=True
        self.isHealing=False
        self.isGlitched=False
        self.numberToSuit={0:'Bottom Feeder',1:'Bloodsucker',2:'Double Talker',3:'Ambulance Chaser',
                           4:'Back Stabber',5:'Spin Doctor',6:'Legal Eagle',7:'Big Wig'}
        self.oldSetAnim = LocalToon.LocalToon.setAnimState
        BRPlayground.BRPlayground.__init__=lambda *args:self.newBrrInit(*args)
        LawbotHQExterior.LawbotHQExterior.enterWalk=lambda newSelf,*args: self.newEnterWalk(newSelf,*args)
        DistributedBattle.DistributedBattle.enterReward=lambda newSelf,*args: self.newEnterReward(newSelf,*args)
        DistributedSuit.denyBattle=lambda *args: self.newDenyBattle(*args)
        LocalToon.LocalToon.setAnimState=lambda *args,**kwds:self.newSetAnimState(*args,**kwds)
        HealthForceAcknowledge.HealthForceAcknowledge.enter=lambda newSelf,hplevel: self.newEnterHealth(newSelf,hplevel)
        DistributedBoardingParty.DistributedBoardingParty.postInvite=lambda newSelf,leaderId,inviterId: self.newPostInvite(newSelf,leaderId,inviterId)

    def attack(self):
        try:
            for battle in base.cr.doFindAll('battle'):
                if len(battle.suits)>1:
                    for suit in battle.suits: 
                        if suit.getName()!='Skelecog':
                            attackSuit=suit
                else:
                    attackSuit=battle.suits[0]
                    
                if base.localAvatar.inventory.inventory[cjMaxer.restock.firstTrack][cjMaxer.restock.desiredLevel1]>0:
                    battle.sendUpdate('requestAttack', [cjMaxer.restock.firstTrack, cjMaxer.restock.desiredLevel1, attackSuit.doId])
                else:
                    break
                    
                if base.localAvatar.getHp()<(base.localAvatar.getMaxHp()*0.9) or self.isHealing:
                
                    if base.localAvatar.inventory.inventory[cjMaxer.restock.secondTrack][cjMaxer.restock.desiredLevel2]>0:
                        battle.sendUpdate('requestAttack', [cjMaxer.restock.secondTrack, cjMaxer.restock.desiredLevel2, base.localAvatar.doId])
                    else:
                        break
                        
                    if base.localAvatar.inventory.inventory[cjMaxer.restock.thirdTrack][cjMaxer.restock.desiredLevel3]>0:
                        battle.sendUpdate('requestAttack', [cjMaxer.restock.thirdTrack, cjMaxer.restock.desiredLevel3, attackSuit.doId])
                    else:
                        break
                        
                else:
                    if base.localAvatar.inventory.inventory[cjMaxer.restock.thirdTrack][cjMaxer.restock.desiredLevel3]>0:
                        battle.sendUpdate('requestAttack', [cjMaxer.restock.thirdTrack, cjMaxer.restock.desiredLevel3, attackSuit.doId])
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
        
    def newBrrInit(self,*args):
        self.oldBrrInit(*args)
        if self.shouldContinue:
            cjMaxer.daAutoer.gainLaffSeq.finish()
            cjMaxer.daAutoer.generateAgain()
            cjMaxer.daAutoer.attackSeq.finish()
            cjMaxer.restock.wasInBattle=False
            self.checkNotices()
    
    def newEnterHealth(self,newSelf,hplevel):
        try:
            self.oldEnterHealth(newSelf,hplevel)
            newSelf.handleOk(base.localAvatar.getHp())
            newSelf.exit()
            if self.shouldContinue:
                Sequence(Wait(2),Func(self.checkNotices)).start()
        except:
            pass
    
    def newPostInvite(self,newSelf,leaderId,inviterId):
        if leaderId==base.localAvatar.doId:
            newSelf.sendUpdate('requestAcceptInvite',[inviterId,leaderId])
        else:
            self.oldPostInvite(newSelf,leaderId,inviterId)
           
    def newEnterWalk(self,newSelf,*args):
        self.oldEnterWalk(newSelf,args)
        if self.shouldContinue and len(args)>0:
            base.localAvatar.setWantBattles(False)
            self.checkNotices()
    
    def newEnterReward(self,newSelf,*args):
        self.oldEnterReward(newSelf,*args)
        if self.shouldContinue and self.isHealing:
            if base.localAvatar.getHp()>96:
                cjMaxer.daAutoer.attackSeq.finish()
                self.isHealing=False
                Sequence(Wait(1),Func(self.checkNotices)).start()
            else:
                Sequence(Wait(1),Func(self.enterRandomBattle)).start()
     
    def newDenyBattle(self,*args):
        self.oldDenyBattle(*args)
        if self.shouldContinue and self.isHealing and self.lastCogId==args[0].doId:
            self.enterRandomBattle()
           
    def newSetAnimState(self,*args,**kwds):
        a = args if len(args) <= 7 else args[:7]
        self.oldSetAnim(*a, **kwds)
        if self.canSetParentAgain:
            base.localAvatar.d_setParent(1)
            self.canSetParentAgain=False
            Sequence(Wait(2),Func(self.doUnsetCanSetParentAgain)).start()
      
    def doUnsetCanSetParentAgain(self):
        self.canSetParentAgain=True
        
    def checkNotices(self):
        if self.shouldEnd:
            self.shouldContinue=False
            base.localAvatar.setWantBattles(True)
        if self.haveJb():
            if self.shouldContinue:
                if self.getNoticesLeft()==0 and not self.onlyDA:
                    if base.cr.doFind('DistributedCogHQDoor') and base.localAvatar.getZoneId()>=13000 and base.localAvatar.getZoneId()<13100:
                        cjMaxer.cjAutoer.start()
                    else:
                        cjMaxer.restock.restock()
                        cjMaxer.restock.collectLaff()
                        self.walk()
                        cjMaxer.autoerGui.display.newLine('Teleporting to lawbot hq')
                        Sequence(Wait(2),Func(self.teleBack)).start()
                else:
                    if base.cr.doFind('DistributedCogHQDoor') and base.localAvatar.getZoneId()>=13000 and base.localAvatar.getZoneId()<13100:
                        if (base.localAvatar.getHp()>96 and self.getNoticesLeft()>10) or self.isGlitched:
                            cjMaxer.daAutoer.start()
                        else:
                            cjMaxer.daAutoer.attackSeq.loop()
                            self.isHealing=True
                            self.enterRandomBattle()
                    else:
                        cjMaxer.restock.restock()
                        cjMaxer.restock.collectLaff()
                        self.walk()
                        cjMaxer.autoerGui.display.newLine('Teleporting to lawbot hq')
                        Sequence(Wait(2),Func(self.teleBack)).start()
            else:
                cjMaxer.restock.noToons.finish()
                try:
                    base.cr.removeInterest(cjMaxer.restock.interest1)
                    base.cr.removeInterest(cjMaxer.restock.interest2)
                    cjMaxer.restock.unloaded=True
                except:
                    pass
                base.localAvatar.setSystemMessage(0,"Thanks for using freshollie's cj maxer")
                cjMaxer.autoerGui.display.newLine('Stopped')
        else:
            cjMaxer.autoerGui.display.newLine('Out of jellybeans')
            base.localAvatar.setSystemMessage(0,'You have run out of jelly beans, please use the fishing code to gain some')
    
    def getNoticesLeft(self):
        return CogDisguiseGlobals.getTotalMerits(base.localAvatar,1)-base.localAvatar.cogMerits[1]

    def walk(self):
        try:
            base.cr.playGame.getPlace().fsm.forceTransition('walk')
        except:
            pass
       
    def teleBack(self,zone=13000):
        try:
            self.walk()
            base.cr.playGame.getPlace().handleBookCloseTeleport(zone, zone)
        except:
            pass
                
    def onlyDoDA(self):
        self.onlyDA=True
        base.localAvatar.setSystemMessage(0,'CJ maxer set to only do the DA Office')
    
    def doBoth(self):
        self.onlyDA=False
        base.localAvatar.setSystemMessage(0,'CJ maxer set to do both the DA Office and the CJ')
        
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
        
    def setStop(self):
        self.shouldEnd=True
        base.localAvatar.setSystemMessage(1,"The Autoer will stop at the end of this run")
        cjMaxer.autoerGui.stopTimer()
    
    def start(self):
        DistributedObject.DistributedObject.sendUpdate=lambda newself, fieldName, args=[], sendToId=None: self.sendUpdateHook(newself, fieldName, args, sendToId)
        self.bossCount=0
        self.shouldContinue=True
        self.shouldEnd=False
        cjMaxer.autoerGui.startTimer()
        emptyShardList=[]
        for shard in base.cr.activeDistrictMap:
            if base.cr.activeDistrictMap[shard].avatarCount<30:
                emptyShardList.append(shard)
        if emptyShardList==[]:
            emptyShardList=[650000000, 754000000, 608000000, 756000000, 658000000, 712000000, 360000000, 410000000, 620000000, 454000000, 726000000, 362000000, 688000000, 316000000]
        if base.localAvatar.defaultShard not in emptyShardList:
            cjMaxer.autoerGui.display.newLine('TPing to an empty district')
            base.cr.playGame.getPlace().requestTeleport(13000,13000,random.choice(emptyShardList),None)
        else:
            self.checkNotices()
        cjMaxer.restock.noToons.loop()
    
    def revertFunctions(self):
        LocalToon.LocalToon.setAnimState=self.oldSetAnim
        BRPlayground.BRPlayground.__init__=self.oldBrrInit
        LawbotHQExterior.LawbotHQExterior.enterWalk=self.oldEnterWalk
        DistributedBattle.DistributedBattle.enterReward=self.oldEnterReward
        DistributedSuit.denyBattle=self.oldDenyBattle
        DistributedObject.DistributedObject.sendUpdate=self.oldSendUpdate
        HealthForceAcknowledge.HealthForceAcknowledge.enter=self.oldEnterHealth
        DistributedBoardingParty.DistributedBoardingParty.postInvite=self.oldPostInvite

class CjAutoer:
    oldBossEnterElevator=DistributedLawbotBoss.DistributedLawbotBoss.enterElevator
    oldEnterBattleThree=DistributedLawbotBoss.DistributedLawbotBoss.enterBattleThree
    oldEnterPrepareBattleTwo=DistributedLawbotBoss.DistributedLawbotBoss.enterPrepareBattleTwo
    oldEnterPrepareBattleThree=DistributedLawbotBoss.DistributedLawbotBoss.enterPrepareBattleThree
    oldEnterEpilogue=DistributedLawbotBoss.DistributedLawbotBoss.enterEpilogue
    oldEnterRollToBattleTwo=DistributedLawbotBoss.DistributedLawbotBoss.enterRollToBattleTwo
    oldEnterWaitForInput=DistributedBattleFinal.DistributedBattleFinal.enterWaitForInput
    oldBossEnterIntro=DistributedLawbotBoss.DistributedLawbotBoss.enterIntroduction
    oldAvatarExit=DistributedCogHQDoor.DistributedCogHQDoor.avatarExit
    
    def __init__(self):
        DistributedLawbotBoss.DistributedLawbotBoss.enterElevator=lambda newSelf: self.newBossEnterElevator(newSelf)
        DistributedLawbotBoss.DistributedLawbotBoss.enterIntroduction=lambda newSelf,*args: self.newBossEnterIntro(newSelf,*args)
        DistributedLawbotBoss.DistributedLawbotBoss.enterRollToBattleTwo=lambda newSelf: self.newEnterRollToBattleTwo(newSelf)
        DistributedLawbotBoss.DistributedLawbotBoss.enterBattleThree=lambda newSelf: self.newEnterBattleThree(newSelf)
        DistributedBattleFinal.DistributedBattleFinal.enterWaitForInput=lambda *args: self.newEnterWaitForInput(*args)
        DistributedCogHQDoor.DistributedCogHQDoor.avatarExit=lambda newSelf,id: self.newAvatarExit(newSelf,id)
        DistributedLawbotBoss.DistributedLawbotBoss.enterPrepareBattleThree=lambda newSelf: self.newEnterPrepareBattleThree(newSelf)
        DistributedLawbotBoss.DistributedLawbotBoss.enterPrepareBattleTwo=lambda newSelf: self.newEnterPrepareBattleTwo(newSelf)
        DistributedLawbotBoss.DistributedLawbotBoss.enterEpilogue=lambda newSelf: self.newEnterEpilogue(newSelf)
        
    def newBossEnterElevator(self,newSelf):
        self.oldBossEnterElevator(newSelf)
        if cjMaxer.otherFunctions.shouldContinue:
            cjMaxer.autoerGui.display.newLine('Skipping Elevator')
            newSelf._DistributedBossCog__doneElevator()
            
    def newBossEnterIntro(self,newSelf,*args):
        self.oldBossEnterIntro(newSelf,*args)
        if cjMaxer.otherFunctions.shouldContinue:
            newSelf.exitIntroduction()
            cjMaxer.autoerGui.display.newLine('Skipping CJ introduction')
    
    def newEnterEpilogue(self,newSelf):
        self.oldEnterEpilogue(newSelf)
        if cjMaxer.otherFunctions.shouldContinue:
            cjMaxer.otherFunctions.bossCount+=1
            newSelf._DistributedLawbotBoss__doneEpilogue()
            cjMaxer.otherFunctions.walk()
            cjMaxer.otherFunctions.teleBack()
            cjMaxer.autoerGui.display.newLine('Finished CJ')
    
    def newEnterRollToBattleTwo(self,newSelf):
        self.oldEnterRollToBattleTwo(newSelf)
        if cjMaxer.otherFunctions.shouldContinue:
            newSelf.exitRollToBattleTwo()
            cjMaxer.autoerGui.display.newLine('Skipping cutscene')
    
    def newEnterPrepareBattleTwo(self,newSelf):
        self.oldEnterPrepareBattleTwo(newSelf)
        if cjMaxer.otherFunctions.shouldContinue:
            newSelf._DistributedLawbotBoss__onToBattleTwo(33)
            cjMaxer.autoerGui.display.newLine('Skipping dialogue 1')
            cjMaxer.autoerGui.display.newLine('Waiting for cannon round...')
    
    def newEnterPrepareBattleThree(self,newSelf):
        self.oldEnterPrepareBattleThree(newSelf)
        if cjMaxer.otherFunctions.shouldContinue:
            newSelf._DistributedLawbotBoss__onToBattleThree(33)
            cjMaxer.autoerGui.display.newLine('Skipping dialogue 2')
    
    def newEnterBattleThree(self,newSelf):
        self.oldEnterBattleThree(newSelf)
        if cjMaxer.otherFunctions.shouldContinue:
            self.endBattle()
            cjMaxer.autoerGui.display.newLine('Completing evidence round')
    
    def newEnterWaitForInput(self,*args):
        self.oldEnterWaitForInput(*args)
        if cjMaxer.otherFunctions.shouldContinue:
            self.exploit()
            cjMaxer.autoerGui.display.newLine('Skipping Battle')
        
    def newAvatarExit(self,newSelf,id):
        self.oldAvatarExit(newSelf,id)
        if base.cr.doFind('Elevator') and id==base.localAvatar.doId and cjMaxer.otherFunctions.shouldContinue and base.localAvatar.getZoneId()==13100:
            cjMaxer.otherFunctions.walk()
            cjMaxer.autoerGui.display.newLine('Heading to CJ')
            base.cr.doFind('Boarding').sendUpdate('requestInvite',[base.localAvatar.doId])
            base.cr.doFind('Boarding').sendUpdate('requestGoToSecondTime',[base.cr.doFind('Elevator').doId])

    def destroyBattle(self):
        base.cr.doFind('SafeZone').sendUpdate('enterSafeZone')

    def exploit(self):
        Sequence(Func(self.destroyBattle), Wait(.5), Func(cjMaxer.otherFunctions.walk)).start()
        
    def endBattle(self):
        CJ = base.cr.doFind('Chief Justice')
        killSeq=Sequence()
        for i in range(20):
            killSeq.append(Func(CJ.sendUpdate,'hitBoss', [100]))
            killSeq.append(Wait(0.05))
        killSeq.start()

    def start(self):
        cjMaxer.autoerGui.display.newLine('Starting Chief Justice')
        cjMaxer.autoerGui.display.newLine('Entering Lobby')
        base.localAvatar.setWantBattles(True)
        firstId=base.cr.doFindAll('CogHQDoor')[0].doId
        if isinstance(base.cr.doId2do.get(firstId-2),DistributedCogHQDoor.DistributedCogHQDoor):
            base.cr.doId2do.get(firstId-2).sendUpdate('requestEnter')
        else:
            base.cr.doId2do.get(firstId).sendUpdate('requestEnter')
    
    
    def revertFunctions(self):
        DistributedLawbotBoss.DistributedLawbotBoss.enterElevator=self.oldBossEnterElevator
        DistributedLawbotBoss.DistributedLawbotBoss.enterBattleThree=self.oldEnterBattleThree
        DistributedLawbotBoss.DistributedLawbotBoss.enterPrepareBattleTwo=self.oldEnterPrepareBattleTwo
        DistributedLawbotBoss.DistributedLawbotBoss.enterPrepareBattleThree=self.oldEnterPrepareBattleThree
        DistributedLawbotBoss.DistributedLawbotBoss.enterEpilogue=self.oldEnterEpilogue
        DistributedLawbotBoss.DistributedLawbotBoss.enterRollToBattleTwo=self.oldEnterRollToBattleTwo
        DistributedBattleFinal.DistributedBattleFinal.enterWaitForInput=self.oldEnterWaitForInput
        DistributedLawbotBoss.DistributedLawbotBoss.enterIntroduction=self.oldBossEnterIntro
        DistributedCogHQDoor.DistributedCogHQDoor.avatarExit=self.oldAvatarExit
        
class DAautoer:
    oldElevatorAnnounceGenerate=DistributedLawOfficeElevatorExt.DistributedLawOfficeElevatorExt.announceGenerate
    oldEnterStageReward=DistributedStageBattle.DistributedStageBattle.enterStageReward
    oldEnterReward=DistributedStageBattle.DistributedStageBattle.enterReward
    oldStageGenerate=DistributedStage.DistributedStage.announceGenerate
    
    def __init__(self,cjMaxer):
        self.gainLaffSeq=Sequence(Func(cjMaxer.restock.gainLaff),Wait(3.0))
        self.attackSeq=Sequence(Func(cjMaxer.restock.restock),Wait(1.0),Func(cjMaxer.otherFunctions.attack),Wait(1.0))
        DistributedLawOfficeElevatorExt.DistributedLawOfficeElevatorExt.announceGenerate=lambda *args:self.newElevatorAnnounceGenerate(*args)
        DistributedStageBattle.DistributedStageBattle.enterStageReward=lambda *args:self.newEnterStageReward(*args)
        DistributedStageBattle.DistributedStageBattle.enterReward=lambda *args:self.newEnterReward(*args)
        DistributedStage.DistributedStage.announceGenerate=lambda newSelf,*args:self.newStageGenerate(newSelf,*args)
        base.cr.doFind('SafeZone').d_enterSafeZone=lambda *args: self.newSafeZone(*args)
        base.localAvatar.died=lambda *args: self.newSafeZone(*args)
        DistributedStageBattle.DistributedStageBattle.d_toonDied=lambda *args: self.newSafeZone(*args)

    def newStageAnnounceGenerate(self,newSelf,*args):
        self.oldStageAnnounceGenerate(newSelf,*args)
        if cjMaxer.otherFunctions.shouldContinue:
            self.floorNum+=1
            cjMaxer.autoerGui.display.newLine('Entering Floor '+str(self.floorNum))
            Sequence(Wait(3),Func(self.doFloor,newSelf)).start()
    
    def newElevatorAnnounceGenerate(self,*args):
        self.oldElevatorAnnounceGenerate(*args)
        if cjMaxer.otherFunctions.shouldContinue and 'Office A' in args[0].getDestName():
            self.workOutOfficeNeeded()
            Sequence(Wait(2),Func(self.boardElevator)).start()
    
    def newEnterStageReward(self,*args):
        self.oldEnterStageReward(*args)
        if cjMaxer.otherFunctions.shouldContinue:
            cjMaxer.autoerGui.display.newLine('Completed Final Battle')
            self.gainLaffSeq.finish()
            self.attackSeq.finish()
            self.generateAgain()
            cjMaxer.otherFunctions.isGlitched=False
            Sequence(Wait(2),Func(cjMaxer.otherFunctions.teleBack)).start()
    
    def newEnterReward(self,*args):
        self.oldEnterReward(*args)
        if cjMaxer.otherFunctions.shouldContinue:
            cjMaxer.autoerGui.display.newLine('Error no notices received')
            self.gainLaffSeq.finish()
            self.attackSeq.finish()
            self.generateAgain()
            cjMaxer.otherFunctions.teleBack()
            cjMaxer.otherFunctions.isGlitched=True
    
    def newStageGenerate(self,newSelf,*args):
        self.oldStageGenerate(newSelf,*args)
        if cjMaxer.otherFunctions.shouldContinue:
            self.floorNum+=1
            cjMaxer.autoerGui.display.newLine('Entering Floor '+str(self.floorNum))
            Sequence(Wait(3),Func(self.doFloor,newSelf)).start()
    
    def newSafeZone(self,*args):
        Sequence(Wait(1),Func(cjMaxer.otherFunctions.walk),Func(base.localAvatar.collisionsOff)).start()
        cjMaxer.restock.wasInBattle=True
        cjMaxer.autoerGui.display.newLine('Died, recovering')
        
    def enterBattle(self):
        if base.localAvatar.getHp()>0:
            try:
                base.cr.doFind('DistributedStage.DistributedStage').warpToRoom(2)
            except:
                pass
            base.localAvatar.collisionsOn()
            cjMaxer.restock.wasInBattle=False
    
    def workOutOfficeNeeded(self):
        noticesNeeded=cjMaxer.otherFunctions.getNoticesLeft()
        if noticesNeeded<98 or base.localAvatar.getHp()<81:
            self.office='Office A'
        elif noticesNeeded<190 or base.localAvatar.getHp()<86:
            self.office='Office B'
        elif noticesNeeded<324 or base.localAvatar.getHp()<96:
            self.office='Office C'
        else:
            self.office='Office D'
    
    def doFloor(self,floor):
        if base.cr.doFind('DistributedElevatorFloor'):
            base.cr.doFind('DistributedElevatorFloor').handleEnterSphere(base.localAvatar.doId)
            cjMaxer.autoerGui.display.newLine('Boarding Floor '+str(self.floorNum)+' elevator')
        else:
            floor.warpToRoom(2)
            cjMaxer.autoerGui.display.newLine('Entering Final Battle')
    
    def boardElevator(self):
        for elevator in base.cr.doFindAll('Elevator'):
            if self.office in elevator.getDestName():
                if cjMaxer.otherFunctions.isGlitched:
                    cjMaxer.autoerGui.display.newLine('Fixing a glitch')
                    elevator.sendUpdate('requestBoard')
                else:
                    base.cr.doFind('Boarding').sendUpdate('requestInvite',[base.localAvatar.doId])
                    base.cr.doFind('Boarding').sendUpdate('requestGoToSecondTime',[elevator.doId])
                    cjMaxer.autoerGui.display.newLine('Heading to Office: '+self.office.split()[-1])
                self.gainLaffSeq.loop()
                self.attackSeq.loop()
                self.floorNum=0
                return
                    
    def goToElevators(self):
        firstId=base.cr.doFindAll('CogHQDoor')[0].doId
        if isinstance(base.cr.doId2do.get(firstId+2),DistributedCogHQDoor.DistributedCogHQDoor):
            base.cr.doId2do.get(firstId+2).sendUpdate('requestEnter')
        else:
            base.cr.doId2do.get(firstId).sendUpdate('requestEnter')
    
    def start(self):
        base.localAvatar.setWantBattles(True)
        self.goToElevators()
    
    def preTele(self):
        DistributedTrolley.DistributedTrolley.__init__ = newInit
        DistributedPartyGate.DistributedPartyGate.__init__ = newInit
        DistributedDoor.DistributedDoor.__init__ = newInit
        base.localAvatar.stopLookAroundNow()
            
    def generateAgain(self):
        DistributedTrolley.DistributedTrolley.__init__ = oldTrolleyInit
        DistributedPartyGate.DistributedPartyGate.__init__ = oldPartyInit
        DistributedDoor.DistributedDoor.__init__ = oldDoorInit
        base.localAvatar.findSomethingToLookAt = cjMaxer.restock.oldFindSomethingToLookAt
        ToonHead.ToonHead._ToonHead__lookAround = cjMaxer.restock.oldLookAround
    
    def revertFunctions(self):
        DistributedLawOfficeElevatorExt.DistributedLawOfficeElevatorExt.announceGenerate=self.oldElevatorAnnounceGenerate
        DistributedStageBattle.DistributedStageBattle.enterStageReward=self.oldEnterStageReward
        DistributedStageBattle.DistributedStageBattle.enterReward=self.oldEnterReward
        DistributedStage.DistributedStage.announceGenerate=self.oldStageGenerate
        base.cr.doFind('SafeZone').d_enterSafeZone=lambda *args: None
        base.localAvatar.died=lambda *args: None
        DistributedStageBattle.DistributedStageBattle.d_toonDied=lambda *args: None
        self.attackSeq.finish()
        self.gainLaffSeq.finish()
        self.generateAgain()

class CJMaxer:
    def __init__(self):
        self.restock=restock()
        self.otherFunctions=OtherFunctions()
        self.cjAutoer=CjAutoer()
        self.daAutoer=DAautoer(self)
        self.autoerGui=AutoerGui('CJ Maxer',['Run Time',"Number of CJ's","CJ's/Hour",'Suit','Notices needed'],\
                                ['self.hours+":"+self.minutes+":"+self.seconds','str(cjMaxer.otherFunctions.bossCount)',\
                                'str(self.workOutNumberAnHour(cjMaxer.otherFunctions.bossCount))',\
                                'str(cjMaxer.otherFunctions.numberToSuit[base.localAvatar.cogTypes[1]])+" lvl "+str(base.localAvatar.cogLevels[1]+1)','str(cjMaxer.otherFunctions.getNoticesLeft())'],\
                                'CJ MXR','law')
        
    def revert(self):
        self.restock.revertFunctions()
        self.daAutoer.revertFunctions()
        self.cjAutoer.revertFunctions()
        self.otherFunctions.revertFunctions()
        self.autoerGui.destroy()
        DistributedNPCFisherman.DistributedNPCFisherman.handleCollisionSphereEnter=oldHandleEnterCollisionSphereFisherman
        DistributedNPCPartyPerson.DistributedNPCPartyPerson.handleCollisionSphereEnter=oldHandleEnterCollisionSphereParty
        DistributedNPCFisherman.DistributedNPCFisherman.announceGenerate=oldFisherAnnounceGenerate
        DistributedNPCPartyPerson.DistributedNPCPartyPerson.announceGenerate=oldPartyPlannerAnnounceGenerate

global cjMaxer
cjMaxer=CJMaxer()
