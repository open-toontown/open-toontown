from direct.interval.IntervalGlobal import *
from toontown.safezone import GSPlayground
from toontown.racing import DistributedRace
from toontown.racing import DistributedStartingBlock
from toontown.toon import LocalToon
from otp.otpbase import OTPGlobals

class RaceAutoer:

    oldTeleportIn=GSPlayground.GSPlayground.exitTeleportIn
    oldRaceAnnounceGenerate=DistributedRace.DistributedRace.announceGenerate
    oldStartCountdownClock=DistributedRace.DistributedRace.startCountdownClock
    oldRejectEnter=DistributedStartingBlock.DistributedStartingBlock.rejectEnter
    oldSetAnim=LocalToon.LocalToon.setAnimState
    
    def __init__(self):
        self.accountNum=0
        self.setSpeedway()
        self.trackType=0
        self.raceNum=0
        self.shouldStop=False
        self.shouldContinue=False
        self.shouldMember=False
        self.canSetParentAgain=True
        self.autoerGui=AutoerGui('Race Autoer',
        
                                ['Run Time','NO. Races Completed',\
                                 'Races/hour','Number of tickets','NO. Trophies'],\
                                 
                                ['self.hours+":"+self.minutes+":"+self.seconds','str(raceAutoer.raceNum)',\
                                 'str(self.workOutNumberAnHour(raceAutoer.raceNum))',\
                                 'str(base.localAvatar.getTickets())','str(raceAutoer.getNumTrophies())'],\
                                 
                                 'AUTO RACE'
                                 
                                 ,None)
                                                
        GSPlayground.GSPlayground.exitTeleportIn=lambda *args: self.newTeleportIn(*args)
        DistributedRace.DistributedRace.announceGenerate=lambda newSelf,*args: self.newRaceAnnounceGenerate(newSelf,*args)
        DistributedRace.DistributedRace.startCountdownClock=lambda newSelf,*args: self.newStartCountdownClock(newSelf,*args)
        LocalToon.LocalToon.setAnimState=lambda *args,**kwds:self.newSetAnimState(*args,**kwds)
        DistributedStartingBlock.DistributedStartingBlock.rejectEnter=lambda newSelf,errCode: self.newRejectEnter(newSelf,errCode)
        
    def newRaceAnnounceGenerate(self,newSelf,*args):
        self.oldRaceAnnounceGenerate(newSelf,*args)
        Sequence(Wait(3),Func(self.doRules,newSelf)).start()
    
    def doRules(self,newSelf):
        if self.shouldContinue:
            self.autoerGui.display.newLine('Accepting rules')
            newSelf.handleRulesDone()
            
    def newStartCountdownClock(self,newSelf,*args):
        if self.shouldContinue:
            self.raceNum+=1
            self.autoerGui.display.newLine('Completing race place '+str(self.accountNum+1))
            Sequence(Wait(self.accountNum),Func(newSelf.enterRacing),Wait(0.5),Func(newSelf.sendUpdate,'heresMyT',[base.localAvatar.doId, 3, 1.0, 1]),Wait(0.5),Func(newSelf.leaveRace)).start()
        
    def newTeleportIn(self,*args):
        self.oldTeleportIn(*args)
        if self.shouldContinue:
            Sequence(Wait(1),Func(self.goToBlock)).start()
    
    def newRejectEnter(self,newSelf,errCode):
        if self.shouldContinue:
            Sequence(Wait(2),Func(self.goToBlock)).start()
        else:
            self.oldRejectEnter(newSelf,errCode)
    
    def newSetAnimState(self,*args,**kwds):
        self.oldSetAnim(*args,**kwds)
        if self.canSetParentAgain and self.shouldContinue:
            base.localAvatar.d_setParent(1)
            self.canSetParentAgain=False
            Sequence(Wait(2),Func(self.doUnsetCanSetParentAgain)).start()
      
    def doUnsetCanSetParentAgain(self):
        self.canSetParentAgain=True
    
    def walk(self):
        try:
            base.cr.playGame.getPlace().fsm.forceTransition('walk')
        except:
            pass
        
    def goToBlock(self):
        if self.shouldStop:
            self.shouldContinue=False
            
        if self.shouldContinue:
            self.walk()
            self.workOutTrack()
            base.localAvatar.collisionsOff()
            padList,trackIds=[],[]

            for x in base.cr.doFindAll("RacePad"):
                if x.trackType==self.trackType and x.trackNameNode.getText() in self.tracks:
                    if self.tracks[0] not in trackIds or self.tracks[1] not in trackIds:
                        trackIds.append(x.trackNameNode.getText())
                        padList.append(x)
                    else:
                        for y in range(len(padList)):
                            if padList[y].trackNameNode.getText==x.trackNameNode.getText() and padList[y].doId>x.doId:
                                del padList[y]
                                del trackIds[y]
                                    
            padList.sort()
            if len(padList)>0:
                for race in padList:
                    numBlocksEmpty=0
                    for block in race.startingBlocks:
                        if block.state=='Off':
                            numBlocksEmpty+=1
                            startingBlock=block
                            
                    if numBlocksEmpty>1:
                        self.autoerGui.display.newLine('Going to block '+str(self.accountNum+1))
                        startingBlock.sendUpdate("requestEnter",[True])
                        break
            else:
                base.localAvatar.setSystemMessage(0,'Race Autoer: The track type was not found, or there were no free spots, trying again')
                Sequence(Wait(2),Func(self.goToBlock)).start()
             
    
    def setAccountNum1(self):
        self.accountNum=0
        base.localAvatar.setSystemMessage(0,'Race Autoer: Toon number set to 1')
    
    def setAccountNum2(self):
        self.accountNum=1
        base.localAvatar.setSystemMessage(0,'Race Autoer: Toon number set to 2')
    
    def setAccountNum3(self):
        self.accountNum=2
        base.localAvatar.setSystemMessage(0,'Race Autoer: Toon number set to 3')
    
    def setAccountNum4(self):
        self.accountNum=3
        base.localAvatar.setSystemMessage(0,'Race Autoer: Toon number set to 4')
        
    def setSpeedway(self):
        self.tracks=('Screwball Stadium', 'Corkscrew Coliseum')
        self.automatic=False
        base.localAvatar.setSystemMessage(0,'Race Autoer: Set to do stadium tracks')
        
    def setUrban(self):
        self.tracks=('Airborne Acres', 'Rustic Raceway')
        self.automatic=False
        base.localAvatar.setSystemMessage(0,'Race Autoer: Set to do urban tracks')
    
    def setRural(self):
        self.tracks=('City Circuit', 'Blizzard Boulevard')
        self.automatic=False
        base.localAvatar.setSystemMessage(0,'Race Autoer: Set to do rural tracks')
        
    def setTournament(self):
        self.trackType=2
        self.automatic=False
        base.localAvatar.setSystemMessage(0,'Race Autoer: This may not work properly unless all account have more than 1000 tickets')
    
    def setToonbattle(self):
        self.trackType=1
        self.automatic=False
        base.localAvatar.setSystemMessage(0,'Race Autoer: This may not work properly unless all account have more than 500 tickets')
    
    def setPractice(self):
        self.trackType=0
        self.automatic=False
        base.localAvatar.setSystemMessage(0,"Race Auoter: To Gain any trohpies more than 1 account needs to be used")
    
    def setMember(self):
        self.shouldMember=True
        base.localAvatar.setSystemMessage(0,"Race Auoter: Toon will become a pretend member (so it can do toonbattle and Grand Prix) when started")
    
    def setAutomatic(self):
        self.automatic=True
        base.localAvatar.setSystemMessage(0,"Race Auoter: The autoer will work out what track and track type to do based on your trophies needed")
    
    def unsetMember(self):
        self.shouldMember=False
        base.localAvatar.setSystemMessage(0,"Race Auoter: Toon set not to be a member")
    
    def getNumTrophies(self):
        numTrophies=0
        for trophie in base.localAvatar.getKartingTrophies():
            if trophie:
                numTrophies+=1
        return numTrophies
    
    def workOutTrack(self):
        if self.automatic:
            override=False
            tracks=[]
            for x in base.cr.doFindAll("RacePad"):
                tracks.append(x.trackType)
                
            if not base.localAvatar.getKartingTrophies()[2]:
                self.tracks=('Screwball Stadium', 'Corkscrew Coliseum')
                
            elif not base.localAvatar.getKartingTrophies()[5]:
                self.tracks=('Airborne Acres', 'Rustic Raceway')
            
            elif not base.localAvatar.getKartingTrophies()[8]:
                self.tracks=('City Circuit', 'Blizzard Boulevard')
             
            else:
                override=True
                self.trackType=2

            if not override:
                if base.localAvatar.getTickets()>400 and 1 in tracks:
                    self.trackType=1
                elif base.localAvatar.getTickets()>1000 and 2 in tracks:
                    self.trackType=2
                else:
                    self.trackType=0
    
    def makeMember(self):
        base.cr._OTPClientRepository__isPaid = True
        OTPGlobals.AccessVelvetRope = 2
        OTPGlobals.AccessFull = 2
        LocalToon.LocalToon.gameAccess = 2
        base.launcher.setValue(base.launcher.PaidUserLoggedInKey, '1')
        LocalToon.LocalToon.getGameAccess = lambda *args: 2
        base.cr.allowSecretChat = lambda *args,**kwds: True
        base.cr.isParentPasswordSet = lambda *args,**kwds: True
    
    def revertFunctions(self):
        GSPlayground.GSPlayground.exitTeleportIn=self.oldTeleportIn
        DistributedRace.DistributedRace.announceGenerate=self.oldRaceAnnounceGenerate
        DistributedRace.DistributedRace.startCountdownClock=self.oldStartCountdownClock
        DistributedStartingBlock.DistributedStartingBlock.rejectEnter=self.oldRejectEnter
        LocalToon.LocalToon.setAnimState=self.oldSetAnim
        self.autoerGui.destroy()
    
    def start(self):
        self.raceNum=0
        self.startingTickets=base.localAvatar.getTickets()
        self.shouldContinue=True
        self.shouldStop=False
        self.autoerGui.startTimer()
        if self.shouldMember:
            self.makeMember()
        if base.localAvatar.getZoneId()==8000:
            self.goToBlock()
        else:
            base.cr.playGame.getPlace().handleBookCloseTeleport(8000, 8000)
    
    def setStop(self):
        self.shouldStop=True
        self.autoerGui.stopTimer()

raceAutoer=RaceAutoer()        