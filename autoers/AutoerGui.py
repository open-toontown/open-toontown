import time as timeModule
import datetime

class Ticker:
    def __init__(self,logName):
        self.line=[]
        self.display=[]
        self.lineNum=0
        self.lastMessages=['','']
        self.bottemDisplayNum=0
        self.isScrolled=False
        self.logName=logName
        for i in range(9):
            self.display.append("")
        self.lines=[]
        for i in range(11,20,1):
            self.lines.append(OnscreenText(text='', style=1, fg=(1,1,1,1), pos=(-.81,i/20.0,0), scale=.04, align=TextNode.ALeft))

    def newLine(self,text):
        runTime=[]
        for item in timeModule.localtime():
            runTime.append(item)
        for i in range(3,6,1):
            if len(str(runTime[i]))==1:
                runTime[i]='0'+str(runTime[i])
            else:
                runTime[i]=str(runTime[i])
        text='::'+runTime[3]+':'+runTime[4]+':'+runTime[5]+' - '+self.logName+': '+text
        self.line.append(text)
        self.lineNum+=1
        
        if not self.isScrolled:
            self.bottemDisplayNum=self.lineNum
            self.tick()
            self.printDisplay()
            
        else:
            self.scrollDown()

    def showLines(self):
        for line in self.lines:
            line.show()

    def hideLines(self):
        for line in self.lines:
            line.hide()
            
    def tick(self):
        for i in range(8,0,-1):
            self.display[i]=self.display[i-1]
        self.display[0]=self.line[-1]

    def printDisplay(self):
        i=8
        for line in reversed(self.display):
            self.lines[i].setText(line)
            i-=1
            
    def scrollUp(self):
        original=self.bottemDisplayNum
        if self.isScrolled:
            option=1
            self.bottemDisplayNum-=1
        else:
            option=2
            self.bottemDisplayNum=self.lineNum-1
            self.isScrolled=True
            
        if self.bottemDisplayNum-9>-1:
            for i in range(1,9):
                self.display[i-1]=self.display[i]
            self.display[8]=self.line[self.bottemDisplayNum-9]
        else:
            self.bottemDisplayNum=original
            if option==2:
                self.isScrolled=False
        self.printDisplay()

    def scrollDown(self):
        if self.isScrolled:
            if self.bottemDisplayNum+1==self.lineNum:
                self.isScrolled=False
            
            self.bottemDisplayNum+=1
            for i in range(8,0,-1):
                self.display[i]=self.display[i-1]
            self.display[0]=self.line[self.bottemDisplayNum-1]
        self.printDisplay()

    def checkLine(self,line):
        letterInLine=False
        for letter in line:
            if letter!=" ":
                letterInLine=True
                break
        return letterInLine
    
    def destroy(self):
        for line in self.lines:
            line.destroy()
        del self.line

class AutoerGui:
    def __init__(self,logName,catagories,statsMethods,title,icon):
        self.startTime=None
        self.catagories=catagories[:]
        self.statsMethods=statsMethods[:]
        self.panel=[]
        self.formattedTime=str(datetime.timedelta(seconds=0))
        for i in range(3):
            self.panel.append(guiTools.loadImageAsPlane('phase_12/maps/WallBricksBig2.jpg',170,170))
            self.panel[i].reparentTo(aspect2d)
        self.panel[0].setPos(0,0,.77)
        self.panel[1].setPos(.566,0,.77)
        self.panel[2].setPos(-.566,0,.77)
        
        self.overLay=guiTools.loadImageAsPlane('phase_11/maps/lawbotHQ_palette_2tmla_1.jpg',510,170)
        self.overLay.reparentTo(aspect2d)
        self.overLay.setPos(0,0,.77)
        self.overLay.setTransparency(TransparencyAttrib.MAlpha)
        self.overLay.setAlphaScale(0.6)
        
        self.sides=[]
        self.corner=[]
        for i in range(2):
            self.corner.append(guiTools.loadImageAsPlane("phase_9/maps/CeilingMetalPlate2.jpg",20,20))
            self.corner[i].reparentTo(aspect2d)
        self.corner[0].setPos(-.85,0,.504)
        self.corner[1].setPos(.147,0,.504)
        for i in range(4):
            self.sides.append(guiTools.loadImageAsPlane("phase_7/maps/screwsBar.jpg",140,20))  
            self.sides[i].reparentTo(aspect2d)
        self.sides[0].setHpr(0,0,90)
        self.sides[0].setPos(.147,0,.77)
        self.sides[1].setHpr(0,0,270)
        self.sides[1].setPos(-.85,0,.77)
        self.sides[2].setPos(-.586,0,.504)
        self.sides[3].setPos(-.119,0,.504)
        
        self.frame=guiTools.loadImageAsPlane('phase_5/maps/tt_t_gui_cmg_miniMap_frame.jpg',220,159)
        self.frame.reparentTo(aspect2d)
        self.frame.setTransparency(TransparencyAttrib.MBinary, 1)
        self.frame.setPos(.547,0,.735)
        if icon!=None:
            if icon.lower()=='boss':
                icon='CorpIcon'
            elif icon.lower()=='sell':
                icon='SalesIcon'
            elif icon.lower()=='law':
                icon='LegalIcon'
            elif icon.lower()=='cash':
                icon='MoneyIcon'
            cogLogoModel=loader.loadModel('phase_3/models/gui/cog_icons.bam')
            self.cogLogo=cogLogoModel.find('**/'+icon)
            self.cogLogo.reparentTo(aspect2d)
            self.cogLogo.setScale(0.15)
            self.cogLogo.setPos(.76,0,.88)
        
        self.display=Ticker(logName)
        
        textList=[catagories[0]+': N/A',catagories[1]+': N/A',catagories[2]+': N/A', catagories[3]+': N/A', catagories[4]+': N/A']
        
        posList=[.77,.72,.67,.62,.57]
        self.text=[]
        for i in range(5):
            self.text.append(OnscreenText(text=textList[i], style=1, fg=(1,1,1,1), pos=(.27,posList[i],0), scale=.05, align=TextNode.ALeft))
        self.title=OnscreenText(text='\x01shadow\x01'+title+'\x02', style=1, fg=(1,1,1,1), pos=(.26,.85,0), scale=.1, align=TextNode.ALeft)
        self.buttons=[]
        self.buttons.append(guiTools.createButton(self.display.scrollUp,(.15,0,.85),'phase_3.5/models/gui/friendslist_gui.bam',['Horiz_Arrow_UP','Horiz_Arrow_DN','Horiz_Arrow_Rllvr']))
        self.buttons.append(guiTools.createButton(self.display.scrollDown,(.15,0,.68),'phase_3.5/models/gui/friendslist_gui.bam',['Horiz_Arrow_UP','Horiz_Arrow_DN','Horiz_Arrow_Rllvr']))
        
        self.buttons[0].setHpr(0,0,270)
        self.buttons[1].setHpr(0,0,90)
        base.accept('wheel_up',self.display.scrollUp)
        base.accept('wheel_down',self.display.scrollDown)
        
    def startTimer(self):
        self.formattedTime=str(datetime.timedelta(seconds=0))
        self.startTime=time.time()
        self.display.newLine('Started')
        taskMgr.add(self.updateAllText,'Autogui Clock')
    
    def stopTimer(self):
        taskMgr.remove('Autogui Clock')
        
    def updateAllText(self,task):
        if self.startTime:
            self.formattedTime=str(datetime.timedelta(seconds=round(time.time()-self.startTime)))
        
        self.text[0].setText(self.catagories[0]+': '+eval(self.statsMethods[0]))
        self.text[1].setText(self.catagories[1]+': '+eval(self.statsMethods[1]))
        self.text[2].setText(self.catagories[2]+': '+eval(self.statsMethods[2]))
        self.text[3].setText(self.catagories[3]+': '+eval(self.statsMethods[3]))
        self.text[4].setText(self.catagories[4]+': '+eval(self.statsMethods[4]))
        return task.cont
    
    def workOutNumberAnHour(self,number):
        if round(time.time()-self.startTime)==0:
            return 0
        else:
            return int((number/(time.time()-self.startTime))*3600)
     
    def hideAll(self):
        for panel in self.panel:
            panel.hide()
        for side in self.sides:
            side.hide()
        for corner in self.corner:
            corner.hide()
        for text in self.text:
            text.hide()
        for button in self.buttons:
            button.hide()
        self.title.hide()
        self.frame.hide()
        self.overLay.hide()
        try:self.cogLogo.hide()
        except:pass
        self.display.hideLines()
        base.ignore('wheel_up')
        base.ignore('wheel_down')
    
    def showAll(self):
        for panel in self.panel:
            panel.show()
        for side in self.sides:
            side.show()
        for corner in self.corner:
            corner.show()
        for text in self.text:
            text.show()
        for button in self.buttons:
            button.show()
        self.title.show()
        self.frame.show()
        self.overLay.show()
        try:self.cogLogo.show()
        except:pass
        self.display.showLines()
        base.accept('wheel_up',self.display.scrollUp)
        base.accept('wheel_down',self.display.scrollDown)
    
    def destroy(self):
        for panel in self.panel:
            panel.removeNode()
        for side in self.sides:
            side.removeNode()
        for corner in self.corner:
            corner.removeNode()
        for text in self.text:
            text.removeNode()
        for button in self.buttons:
            button.removeNode()
        self.title.removeNode()
        self.frame.removeNode()
        self.overLay.removeNode()
        try:self.cogLogo.removeNode()
        except:pass
        self.display.destroy()
        base.ignore('wheel_up')
        base.ignore('wheel_down')
        del self.display