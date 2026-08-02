from toontown.golf import DistributedGolfHole
from toontown.safezone import GZPlayground
from toontown.toon import LocalToon
from otp.otpbase import OTPGlobals
from direct.interval.IntervalGlobal import *

class GolfAutoer:

    oldEnterChooseTee = DistributedGolfHole.DistributedGolfHole.enterChooseTee
    oldGolferChooseTee = DistributedGolfHole.DistributedGolfHole.golferChooseTee
    oldBallMovie2Client = DistributedGolfHole.DistributedGolfHole.ballMovie2Client
    oldSetCourseBest = LocalToon.LocalToon.setGolfCourseBest
    oldGotGolfCourse = DistributedGolfHole.DistributedGolfHole._DistributedGolfHole__gotGolfCourse
    oldEnterWalk = GZPlayground.GZPlayground.enterWalk
    oldSetAnim=LocalToon.LocalToon.setAnimState
    
    def __init__(self):
        self.shouldContinue=False
        self.shouldStop=False
        self.shouldMember=False
        self.automatic=True
        self.course=2
        self.courseNum=0
        self.accountNum=0
        self.trophieStartNum=0
        self.canSetParentAgain=True
        
        DistributedGolfHole.DistributedGolfHole.enterChooseTee = lambda newSelf: self.newEnterChooseTee(newSelf)
        DistributedGolfHole.DistributedGolfHole.golferChooseTee = lambda newSelf, avId: self.newGolferChooseTee(newSelf,avId)
        DistributedGolfHole.DistributedGolfHole.ballMovie2Client = lambda newSelf, *args: self.newBallMovie2Client(newSelf,*args)
        DistributedGolfHole.DistributedGolfHole._DistributedGolfHole__gotGolfCourse = lambda newSelf, golfCourse: self.new_DistributedGolfHole__gotGolfCourse(newSelf,golfCourse)
        LocalToon.LocalToon.setGolfCourseBest = lambda newSelf, courseBest: self.setGolfCourseBest(newSelf,courseBest)
        GZPlayground.GZPlayground.enterWalk = lambda newSelf,*args,**kwds: self.newEnterWalk(newSelf,*args,**kwds)
        LocalToon.LocalToon.setAnimState=lambda *args,**kwds:self.newSetAnimState(*args,**kwds)
        
        self.autoerGui=AutoerGui('Golf Autoer',
        
                                ['Run Time','NO. Courses',\
                                 'Courses/Hour','Number of Trophies','Trophies Gained'],\
                                 
                                ['self.hours+":"+self.minutes+":"+self.seconds','str(golfAutoer.courseNum)',\
                                 'str(self.workOutNumberAnHour(golfAutoer.courseNum))',\
                                 'str(golfAutoer.getNumTrophies())','str(golfAutoer.getNumTrophies()-golfAutoer.trophieStartNum)'],\
                                 
                                 'AUTO GOLF'
                                 
                                 ,None)
        
    def newBallMovie2Client(self, newSelf, *args):
        self.oldBallMovie2Client(newSelf,*args)
        if self.shouldContinue:
            newSelf.sendUpdate('ballInHole')
            self.autoerGui.display.newLine('Completing Hole %s'%(self.holeNum))
            self.holeNum+=1
            
    def newSetAnimState(self,*args,**kwds):
        self.oldSetAnim(*args,**kwds)
        if self.canSetParentAgain and self.shouldContinue:
            base.localAvatar.d_setParent(1)
            self.canSetParentAgain=False
            Sequence(Wait(2),Func(self.doUnsetCanSetParentAgain)).start()
      
    def doUnsetCanSetParentAgain(self):
        self.canSetParentAgain=True
        
    def newEnterChooseTee(self,newSelf):
        self.oldEnterChooseTee(newSelf)
        if self.shouldContinue:
            newSelf.sendUpdate('setAvatarTee', [0])
        
    def newGolferChooseTee(self, newSelf, avId):
        self.oldGolferChooseTee(newSelf,avId)
        if self.shouldContinue:
            if avId != base.localAvatar.doId:
                return None
            newSelf.sendUpdate('postSwingState', [
                                                  0.0, 0, 1.0, -2.5, 0.7, 1.0, 1.8, 0.6,
                                                  [
                                                   (
                                                    0, 0, 4.3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
                                                   ),
                                                   (
                                                    0, 99, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
                                                   )
                                                  ]
                                                 ]
                               )
         
    def new_DistributedGolfHole__gotGolfCourse(self,newSelf,golfCourse):
        self.oldGotGolfCourse(newSelf,golfCourse)
        if self.shouldContinue:
            newSelf.sendUpdate('setAvatarTee', [0])
        
    def setGolfCourseBest(self, newSelf, courseBest):
        self.oldSetCourseBest(newSelf,courseBest)
        if self.shouldContinue:
            newSelf.courseBest = courseBest
            self.courseNum+=1
            self.autoerGui.display.newLine('Finished Course')
            base.cr.doFind('DistributedGolfCourse').sendUpdate('setDoneReward', [])
    
    def newEnterWalk(self,newSelf,*args,**kwds):
        self.oldEnterWalk(newSelf,**kwds)
        if self.shouldStop:
            self.shouldContinue=False
            try:
                self.autoerGui.display.newLine('Stopped')
            except:
                pass
            base.localAvatar.setSystemMessage(0,"Thanks for using freshollie's golf autoer!")
        if self.shouldContinue and len(args)>0:
            self.goKart()
           
    def goKart(self):
        if self.shouldStop:
            self.shouldContinue=False
            try:
                self.autoerGui.display.newLine('Stopped')
            except:
                pass
            base.localAvatar.setSystemMessage(0,"Thanks for using freshollie's golf autoer!")
        if self.shouldContinue:
            self.autoerGui.display.newLine('Attempting to board kart')
            self.workOutCourse()
            self.walk()
            for golfKart in base.cr.doFindAll('DistributedGolfKart'):
                if golfKart.golfCourse==self.course:
                    self.holeNum=1
                    Sequence(Wait(self.accountNum),Func(golfKart.handleEnterGolfKartSphere,0),Wait(4),Func(self.checkInKart)).start()
                    return
                
    def checkInKart(self):
        if base.localAvatar.getCurrentAnim()!='sit':
            Sequence(Func(self.goKart)).start()
        else:
            pass

    def walk(self):
        try:
            base.cr.playGame.getPlace().fsm.forceTransition('walk')
        except:
            pass
    
    def getNumTrophies(self):
        numTrophies=0
        for trophie in base.localAvatar.getGolfTrophies():
            if trophie:
                numTrophies+=1
        return numTrophies
            
    def makeMember(self):
        base.cr._OTPClientRepository__isPaid = True
        OTPGlobals.AccessVelvetRope = 2
        OTPGlobals.AccessFull = 2
        LocalToon.LocalToon.gameAccess = 2
        base.launcher.setValue(base.launcher.PaidUserLoggedInKey, '1')
        LocalToon.LocalToon.getGameAccess = lambda *args: 2
        base.cr.allowSecretChat = lambda *args,**kwds: True
        base.cr.isParentPasswordSet = lambda *args,**kwds: True
    
    def setMember(self):
        self.shouldMember=True
        base.localAvatar.setSystemMessage(0,"Golf Autoer: Toon will become a pretend member.")
    
    def unsetMember(self):
        self.shouldMember=False
        base.localAvatar.setSystemMessage(0,"Golf Autoer: Toon set not to be a member.")
        
    def setAutomatic(self):
        self.automatic=True
        base.localAvatar.setSystemMessage(0,"Golf Autoer: Set to be automatic (Works out what courses you need).")
    
    def setPar(self):
        self.automatic=False
        self.course=0
        base.localAvatar.setSystemMessage(0,"Golf Autoer: Set to do the course 'Walk in the par'")
        
    def setFun(self):
        self.automatic=False
        self.course=1
        base.localAvatar.setSystemMessage(0,"Golf Autoer: Set to do the course 'Holesome fun'")
    
    def setHoleKit(self):
        self.automatic=False
        self.course=2
        base.localAvatar.setSystemMessage(0,"Golf Autoer: Set to do the course 'The hole kit and caboodle'")
    
    def setFirst(self):
        self.accountNum=0
    
    def setSecond(self):
        self.accountNum=5
    
    def workOutCourse(self):
        if self.automatic:
            if self.getNumTrophies()>=22 and not base.localAvatar.getGolfTrophies()[23]:
                self.course=0
            elif self.getNumTrophies()>=25 and not base.localAvatar.getGolfTrophies()[26]:
                self.course=1
            else:
                self.course=2
    
    def start(self):
        self.trophieStartNum=self.getNumTrophies()
        self.courseNum=0
        self.shouldContinue=True
        self.shouldStop=False
        self.autoerGui.startTimer()
        self.workOutCourse()
        if self.shouldMember:
            self.makeMember()
        if base.localAvatar.getZoneId()==17000:
            self.goKart()
        else:
            base.cr.playGame.getPlace().handleBookCloseTeleport(17000, 17000)
    
    def setStop(self):
        self.shouldStop=True
        base.localAvatar.setSystemMessage(0,"The Autoer will stop at the end of this run")
        self.autoerGui.stopTimer()
        
    def revertFunctions(self):
         DistributedGolfHole.DistributedGolfHole.enterChooseTee = self.oldEnterChooseTee
         DistributedGolfHole.DistributedGolfHole.golferChooseTee = self.oldGolferChooseTee
         DistributedGolfHole.DistributedGolfHole.ballMovie2Client = self.oldBallMovie2Client
         LocalToon.LocalToon.setGolfCourseBest = self.oldSetCourseBest
         DistributedGolfHole.DistributedGolfHole._DistributedGolfHole__gotGolfCourse = self.oldGotGolfCourse
         GZPlayground.GZPlayground.enterWalk = self.oldEnterWalk
         self.autoerGui.destroy()

global golfAutoer
golfAutoer=GolfAutoer()