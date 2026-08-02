import urllib
import os
import __main__
from pandac.PandaModules import *
from direct.gui.DirectGui import *
from direct.interval.IntervalGlobal import *
from toontown.effects import DistributedFireworkShow
for attribute in dir(DistributedFireworkShow.DistributedFireworkShow):
    exec('DistributedFireworkShow.DistributedFireworkShow.'+attribute+'=lambda *args,**kwds: None')
    
class GuiTools:

    def __init__(self):
        pass
        
    def loadImageAsPlane(self,filepath,resX=None,resY=None):
        yresolution=600
        tex = loader.loadTexture(filepath)
        tex.setBorderColor(Vec4(0,0,0,0))
        tex.setWrapU(Texture.WMRepeat)
        tex.setWrapV(Texture.WMRepeat)
        cm = CardMaker(filepath + ' card')
        if resX==None:
            resX=tex.getOrigFileXSize()
        if resY==None:
            resY=tex.getOrigFileYSize()
        cm.setFrame(-resX, resX, -resY, resY)
        card = NodePath(cm.generate())
        card.setTexture(tex)
        card.flattenLight()
        card.setScale(card.getScale()/ yresolution)
        return card
    
    def createButton(self, cmd, position, model, buttonImgs, colour=(1,1,1,1),text=''):
        ButtonImage = loader.loadModel(model)
        ButtonImageUp = ButtonImage.find("**/"+buttonImgs[0]);
        ButtonImageDown = ButtonImage.find("**/"+buttonImgs[1]);
        ButtonImageRollover = ButtonImage.find("**/"+buttonImgs[-1]);
        return DirectButton(frameSize=None, image=(ButtonImageUp, \
               ButtonImageDown, ButtonImageRollover), relief=None, command=cmd, \
               geom=None, pad=(0.01, 0.01), text=text, suppressKeys=0, pos=position, text_fg=(1,1,1,1), color=colour ,text_scale=0.059, borderWidth=(0.13, 0.01), scale=.7)
    
    def createBox(self):
        background=[]
        for i in range(2):
           background.append(guiTools.loadImageAsPlane('phase_12/maps/WallBricksBig2.jpg',175,175))
           background[i].reparentTo(aspect2d)
        background[0].setPos(-.585,0,0.235)
        background[1].setPos(-.585,0,-.22)
        
        overlay=guiTools.loadImageAsPlane('phase_11/maps/lawbotHQ_palette_2tmla_1.jpg',175,315)
        overlay.reparentTo(aspect2d)
        overlay.setTransparency(TransparencyAttrib.MAlpha)
        overlay.setAlphaScale(0.6)
        overlay.setPos(-.585,0,0)
        
        sides=[]
        for i in range(6):
            sides.append(guiTools.loadImageAsPlane("phase_7/maps/screwsBar.jpg",140,20))
            sides[i].reparentTo(aspect2d)
            
        sides[0].setHpr(0,0,270)
        sides[0].setPos(-.85,0,.237)

        sides[1].setPos(-.586,0,.504)

        sides[2].setHpr(0,0,90)
        sides[2].setPos(-.32,0,.237)

        sides[3].setHpr(0,0,90)
        sides[3].setPos(-.32,0,-.23)

        sides[4].setHpr(0,0,270)
        sides[4].setPos(-.85,0,-.23)

        sides[5].setHpr(0,0,180)
        sides[5].setPos(-.585,0,-.4955)
        
        corners=[]
        for i in range(4):
            corners.append(guiTools.loadImageAsPlane("phase_9/maps/CeilingMetalPlate2.jpg",20,20))
            corners[i].reparentTo(aspect2d)
        corners[0].setPos(-.85,0,.504)
        corners[1].setPos(-.85,0,-.4955)
        corners[2].setPos(-.32,0,.504)
        corners[3].setPos(-.32,0,-.4955)
        
        title=OnscreenText(text='',style=1, fg=(1,1,1,1), pos=(-.585,.42), scale=0.06)
        return background,overlay,sides,corners,title
        
guiTools=GuiTools()

class About:
    def __init__(self):
        self.background,self.overlay,self.sides,self.corners,self.title=guiTools.createBox()
        self.closeButton=guiTools.createButton(self.close,(-0.917,0,.45),'phase_3.5/models/gui/friendslist_gui.bam',['Horiz_Arrow_UP','Horiz_Arrow_DN','Horiz_Arrow_Rllvr'])
        self.openButton=guiTools.createButton(self.open,(-0.917,0,.45),'phase_3.5/models/gui/friendslist_gui.bam',['Horiz_Arrow_UP','Horiz_Arrow_DN','Horiz_Arrow_Rllvr'])
        self.closeButton.setHpr(0,0,180)
        self.text=[]
        for i in range(3):
            self.text.append(OnscreenText(text='', style=1, fg=(1,1,1,1), pos=(0,0,0), scale=.05, align=TextNode.ALeft))
        self.text[0].setPos(-0.26,.33)
        self.text[1].setPos(-0.26,.25)
        self.text[2].setPos(-0.26,.17)
        for i in range(21):
            self.text.append(OnscreenText(text='', style=1, fg=(1,1,1,1), pos=(0,0,0), scale=.04, align=TextNode.ALeft))
        num=0.14
        for i in range(3,24):
            num-=0.04
            self.text[i].setPos(-0.26,num)
        self.closeButton.hide()
        self.title.setText('About Script')
        self.offsetEverything()
        self.close()
        
    def offsetEverything(self):
        for side in self.sides:
            x=side.getPos()[0]+0.53
            y=side.getPos()[2]
            side.setPos(x,0,y)
        for background in self.background:
            x=background.getPos()[0]+0.53
            y=background.getPos()[2]
            background.setPos(x,0,y)
        for corner in self.corners:
            x=corner.getPos()[0]+0.53
            y=corner.getPos()[2]
            corner.setPos(x,0,y)
        
        x=self.overlay.getPos()[0]+0.53
        y=self.overlay.getPos()[2]
        self.overlay.setPos(x,0,y)
        x=self.title.getPos()[0]+0.53
        y=self.title.getPos()[1]
        self.title.setPos(x,y)
        
    def open(self):
        for side in self.sides:
            side.show()
        for background in self.background:
            background.show()
        for corner in self.corners:
            corner.show()
        for text in self.text:
            text.show()
        self.overlay.show()
        self.closeButton.show()
        self.title.show()
        self.openButton.hide()
        
    def close(self):
        for side in self.sides:
            side.hide()
        for background in self.background:
            background.hide()
        for corner in self.corners:
            corner.hide()
        for text in self.text:
            text.hide()
        self.overlay.hide()
        self.closeButton.hide()
        self.title.hide()
        self.openButton.show()
    
    def wrapText(self,line):
        for i in range(3,24):
            if len(line)>25:
                if line[24]==" ":
                    self.text[i].setText(line[:24])
                    line=line[24:]
                    
                else:
                    for x in range(25,0,-1):
                        if line[x-1]==" ":
                            self.text[i].setText(line[:x-1])
                            line=line[x-1:]
                            break
            else:
                self.text[i].setText(line)
                break
    
    def update(self,currentScript):
        for text in self.text:
            text.setText('')
        self.text[0].setText('Name: '+currentScript['name'])
        self.text[1].setText('Author: '+currentScript['author'])
        self.text[2].setText('Version: '+currentScript['version'])
        self.wrapText(' '+currentScript['description'])
    

class Options:

    def __init__(self):
        self.background,self.overlay,self.sides,self.corners,self.title=guiTools.createBox()
        self.title.setText('Options')
        self.optionButtons=[]
        self.optionText=[]
        self.closeButton=guiTools.createButton(self.close,(-0.917,0,.323),'phase_3.5/models/gui/friendslist_gui.bam',['Horiz_Arrow_UP','Horiz_Arrow_DN','Horiz_Arrow_Rllvr'])
        self.openButton=guiTools.createButton(self.open,(-0.917,0,.323),'phase_3.5/models/gui/friendslist_gui.bam',['Horiz_Arrow_UP','Horiz_Arrow_DN','Horiz_Arrow_Rllvr'])
        self.closeButton.setHpr(0,0,180)
        self.closeButton.hide()
        self.close()
    
    def open(self):
        for side in self.sides:
            side.show()
        for background in self.background:
            background.show()
        for corner in self.corners:
            corner.show()
        for button in self.optionButtons:
            button.show()
        for text in self.optionText:
            text.show()
        self.overlay.show()
        self.closeButton.show()
        self.title.show()
        self.openButton.hide()
        
    def close(self):
        for side in self.sides:
            side.hide()
        for background in self.background:
            background.hide()
        for corner in self.corners:
            corner.hide()
        for button in self.optionButtons:
            button.hide()
        for text in self.optionText:
            text.hide()
        self.overlay.hide()
        self.closeButton.hide()
        self.title.hide()
        self.openButton.show()
            
    def update(self,currentScript):
        for i in range(len(self.optionButtons)):
            self.optionButtons[i].destroy()
            del self.optionButtons[i]
        self.removeButtons()
        model='phase_3/models/gui/quit_button.bam'
        buttonImgs=['QuitBtn_UP','QuitBtn_DN','QuitBtn_RLVR']
        for key in currentScript['options']:
            self.optionButtons.append(guiTools.createButton(eval(currentScript['options'][key]['command']), self.getButtonPos(currentScript['options'][key]['pos']), model, buttonImgs, colour=(0.5,0.1,0.5,1),text=key))
        self.updateText(currentScript)
    
    def updateText(self,currentScript):
        self.title.setText(currentScript['name']+' Options')
        for i in range(len(self.optionText)):
            self.optionText[i].destroy()
            del self.optionText[i]
        if 'text' in currentScript:
            for key in currentScript['text']:
                self.optionText.append(OnscreenText(text=key, style=1, fg=(1,1,1,1), pos=(self.getButtonPos(currentScript['text'][key])[0],self.getButtonPos(currentScript['text'][key])[2]), scale=.04))
        
    def removeText(self):
        for text in self.optionText:
            text.destroy()
        del self.optionText
        self.optionText=[]
    
    def removeButtons(self):
        for button in self.optionButtons:
            button.destroy()
        del self.optionButtons
        self.optionButtons=[]
        self.removeText()
        self.title.setText('Options')
        
    def getButtonPos(self,pos):
        columnNum=pos[1]
        rowNum=pos[0]
        if columnNum==0:
            x=-0.73
        else:
            x=-0.44
        y=0.35-(0.07*rowNum)
        return (x,0,y)

class Scroller:
    def __init__(self,itemList,textNode,aboutClass):
        self.list=itemList[:]
        self.listPos=0
        self.textNode=textNode
        self.about=aboutClass
        self.shownItem=self.list[self.listPos]
        
        self.upArrow=guiTools.createButton(self.scrollUp,(-1.11,0,0.44),'phase_3.5/models/gui/friendslist_gui.bam',['FndsLst_ScrollUp','FndsLst_ScrollDN','FndsLst_ScrollUp_Rllvr'])
        self.upArrow.setScale(1.1)
        
        self.downArrow=guiTools.createButton(self.scrollDown,(-1.11,0,0.335),'phase_3.5/models/gui/friendslist_gui.bam',['FndsLst_ScrollUp','FndsLst_ScrollDN','FndsLst_ScrollUp_Rllvr'])
        self.downArrow.setHpr(0,0,180)
        self.downArrow.setScale(1.1)
        self.updateShownItem()
        
        
    def scrollUp(self):
        if self.listPos-1<0:
            return
        else:
            self.listPos-=1
            self.shownItem=self.list[self.listPos]
            self.updateShownItem()
    
    def updateList(self,newList):
        self.list=newList[:]
        self.shownItem=self.list[self.listPos]
        self.updateShownItem()

    def scrollDown(self):
        if self.listPos+1>=len(self.list):
            return
        else:
            self.listPos+=1
            self.shownItem=self.list[self.listPos]
            self.updateShownItem()

    def updateShownItem(self):
        self.textNode.setText(self.shownItem['name'])
        self.about.update(self.shownItem)
    
    def hideAll(self):
        self.upArrow.hide()
        self.downArrow.hide()
        self.textNode.hide()
    
    def showAll(self):
        self.upArrow.show()
        self.downArrow.show()
        self.textNode.show()
    
    def destroy(self):
        self.upArrow.destroy()
        self.downArrow.destroy()
        self.textNode.destroy()
        
class ToonBot:
    TOONBOT_DIRECTORY = "toonbot/"
    SCRIPTS_DIRECTORY = TOONBOT_DIRECTORY + "scripts/"
    LIBS_DIRECTORY = TOONBOT_DIRECTORY + "libs/"

    TOONBOT_STRING = "ToonBot: "

    def __init__(self):
        self.scriptCurrentlyLoaded=False
        self.scriptLoaded=None
        self.scriptOn=False
        self.defaultScript=\
            {'name':'No Scripts',\
            'description':'You appear to have installed \n\
             no scripts to Toon-Bot go to \n\
             youtube.com/toontowninjecting \n\
             where you will find some scripts',\
            'author': 'None',\
            'version': 'None',\
            'load':'no scripts.txt',\
            'unload':None,\
            'start':'pass',\
            'stop':'pass',\
            'options':'None',\
            'location':'None',
            'description':'None'}
        self.scripts=[self.defaultScript]
        
        if not os.path.exists(ToonBot.SCRIPTS_DIRECTORY):
            os.makedirs(ToonBot.SCRIPTS_DIRECTORY)
            os.makedirs(ToonBot.LIBS_DIRECTORY)
        self.createGui()
        self.importScripts()
        
    def addScript(self,script):
        if 'https://' not in script['location']:
            scriptLib=open(ToonBot.LIBS_DIRECTORY + script['name']+'.txt','w')
            scriptLib.write(str(script))
            scriptLib.close()
            self.importScripts()
            base.localAvatar.setSystemMessage(0, ToonBot.TOONBOT_STRING+script['name']+' Added to Toon-Bot, you will never need to inject it again!')
        else:
            base.localAvatar.setSystemMessage(0,'ToonBot: The script you tried to add contained a url with https, it needs to be http to work.')
        
    def downloadScript(self,script):
        myfile=open(ToonBot.SCRIPTS_DIRECTORY + script['name']+'.txt','w')
        try:
            downloadedScript=urllib.urlopen(script['location']).read()
        except:
            base.localAvatar.setSystemMessage(0, ToonBot.TOONBOT_STRING + 'Script location doesnt exist')
            myfile.close()
            return False
        myfile.write(downloadedScript)
        myfile.close()
        return True
    
    def loadScript(self):
        if not self.scriptCurrentlyLoaded:
            script=self.scripts[self.scroller.listPos]
            if script['location'] == 'None':
                base.localAvatar.setSystemMessage(0, ToonBot.TOONBOT_STRING + 'Cannot load a script with no location')
                return
            if not self.downloadScript(script):
                return 
            myfile=open(ToonBot.SCRIPTS_DIRECTORY + script['name'] + '.txt','r')
            for line in myfile:
                if '#outdated' in line:
                    base.localAvatar.setSystemMessage(0, ToonBot.TOONBOT_STRING + 'The Script you loaded appears to be outdated, go to the authors youtube to download the latest version')
                    break
            myfile.close()
            execfile(ToonBot.SCRIPTS_DIRECTORY + script['name'] + '.txt',globals())
            self.scriptCurrentlyLoaded=True
            self.scriptLoaded=script
            self.options.open()
            self.options.update(self.scriptLoaded)
            self.closeAutoerGuiButton.show()
            self.openAutoerGuiButton.hide()
        else:
            base.localAvatar.setSystemMessage(0, ToonBot.TOONBOT_STRING + 'You already have a script loaded. Unload that script before reloading a new one')
    
    def unloadScript(self):
        if self.scriptCurrentlyLoaded:
            if not self.scriptOn:
                eval(self.scriptLoaded['unload'])
                self.scriptCurrentlyLoaded=False
                self.scriptLoaded=None
                self.options.close()
                self.options.removeButtons()
                self.closeAutoerGuiButton.hide()
                self.openAutoerGuiButton.show()
            else:
                base.localAvatar.setSystemMessage(0, ToonBot.TOONBOT_STRING + 'You cannot unload a script while the script is running')
        else:
            base.localAvatar.setSystemMessage(0, ToonBot.TOONBOT_STRING + 'You currently do not have a loaded script')
            
    def startScript(self):
        if not self.scriptOn:
            if self.scriptCurrentlyLoaded:
                self.scriptOn=True
                eval(self.scriptLoaded['start'])
            else:
                base.localAvatar.setSystemMessage(0, ToonBot.TOONBOT_STRING + 'You cannot start a script that has not been loaded')
        else:
            base.localAvatar.setSystemMessage(0, ToonBot.TOONBOT_STRING + 'The script is already running')
        
    def stopScript(self):
        if self.scriptOn:
            self.scriptOn=False
            eval(self.scriptLoaded['stop'])
        else:
            base.localAvatar.setSystemMessage(0, ToonBot.TOONBOT_STRING + 'The script is already stopped')
        
        
    def importScripts(self):
        self.scripts=[]    
        for script in os.listdir(ToonBot.LIBS_DIRECTORY):
            try:
                self.scripts.append(eval(open(ToonBot.LIBS_DIRECTORY + script,'r').read()))
            except:
                os.remove(ToonBot.LIBS_DIRECTORY + script)
            
        if self.scripts==[]:
            self.scripts=[self.defaultScript]
            
        self.reloadScroller()
        
    def createGui(self):
        self.background=[]
        for i in range(2):
            self.background.append(guiTools.loadImageAsPlane('phase_12/maps/WallBricksBig2.jpg',170,170))
            self.background[i].reparentTo(aspect2d)
        self.background[0].setPos(-1.11,-0.5,0.65)
        self.background[0].setScale(0.0013)
        self.background[1].setPos(-1.11,-0.5,0.51)
        self.background[1].setScale(0.0013)
        
        self.overLay=guiTools.loadImageAsPlane('phase_11/maps/lawbotHQ_palette_2tmla_1.jpg',130,175)
        self.overLay.reparentTo(aspect2d)
        self.overLay.setTransparency(TransparencyAttrib.MAlpha)
        self.overLay.setAlphaScale(0.6)
        self.overLay.setPos(-1.1,0,.59)
        
        self.sides=[]
        for i in range(5):
            self.sides.append(guiTools.loadImageAsPlane("phase_7/maps/screwsBar.jpg",140,20))
            self.sides[i].reparentTo(aspect2d)
        self.sides[0].setHpr(0,0,90)
        self.sides[0].setPos(-0.917,0.6,0.59)
        self.sides[1].setHpr(0,0,270)
        self.sides[1].setPos(-1.3,0.6,0.59)
        self.sides[2].setPos(-1.117,0.6,0.85)
        self.sides[3].setPos(-1.117,0.6,0.323)
        self.sides[4].setPos(-1.117,0.6,0.45)
        
        self.corners=[]
        for i in range(6):
            self.corners.append(guiTools.loadImageAsPlane("phase_9/maps/CeilingMetalPlate2.jpg",20,20))
            self.corners[i].reparentTo(aspect2d)
        self.corners[0].setPos(-0.917,0,0.85)
        self.corners[1].setPos(-1.3,0,0.85)
        self.corners[2].setPos(-0.917,0,.323)
        self.corners[3].setPos(-1.3,0,.323)
        self.corners[4].setPos(-0.917,0,.45)
        self.corners[5].setPos(-1.3,0,.45)
        model='phase_3/models/gui/quit_button.bam'
        
        buttonImgs=['QuitBtn_UP','QuitBtn_DN','QuitBtn_RLVR']
        
        self.options=Options()
        self.about=About()
        self.scroller=Scroller(self.scripts,OnscreenText(text='',style=1, fg=(1,1,1,1), pos=(-1.11,.37), scale=0.06),self.about)
        
        self.closeButton=guiTools.createButton(self.hideGui,(-1.3,0,.323),'phase_3.5/models/gui/friendslist_gui.bam',['Horiz_Arrow_UP','Horiz_Arrow_DN','Horiz_Arrow_Rllvr'])
        self.closeButton.setHpr(0,0,180)
        self.openButton=guiTools.createButton(self.showGui,(-1.3,0,.323),'phase_3.5/models/gui/friendslist_gui.bam',['Horiz_Arrow_UP','Horiz_Arrow_DN','Horiz_Arrow_Rllvr'])
        self.openButton.hide()
        
        self.closeAutoerGuiButton=guiTools.createButton(self.closeAutoerGui,(-0.917,0,0.85),'phase_3.5/models/gui/friendslist_gui.bam',['Horiz_Arrow_UP','Horiz_Arrow_DN','Horiz_Arrow_Rllvr'])
        self.closeAutoerGuiButton.setHpr(0,0,180)
        self.openAutoerGuiButton=guiTools.createButton(self.openAutoerGui,(-0.917,0,0.85),'phase_3.5/models/gui/friendslist_gui.bam',['Horiz_Arrow_UP','Horiz_Arrow_DN','Horiz_Arrow_Rllvr'])
        self.closeAutoerGuiButton.hide()
        
        self.buttons=[]
        self.buttons.append(guiTools.createButton(self.loadScript,(-1.11,0,.77), model, buttonImgs, colour=(0.5,0.1,0.5,1),text='Load Script'))
        self.buttons.append(guiTools.createButton(self.startScript,(-1.11,0,.697), model, buttonImgs, colour=(0.5,0.1,0.5,1),text='Start Script'))
        self.buttons.append(guiTools.createButton(self.stopScript,(-1.11,0,.624), model, buttonImgs, colour=(0.5,0.1,0.5,1),text='Stop Script'))
        self.buttons.append(guiTools.createButton(self.unloadScript,(-1.11,0,.551), model, buttonImgs, colour=(0.5,0.1,0.5,1),text='Unload Script'))
        
        
    def reloadScroller(self):
        self.scroller.updateList(self.scripts)
    
    def closeAutoerGui(self):
        if self.scriptCurrentlyLoaded:
            eval(self.scriptLoaded['close'])
            self.closeAutoerGuiButton.hide()
            self.openAutoerGuiButton.show()
        
    def openAutoerGui(self):
        if self.scriptCurrentlyLoaded:
            eval(self.scriptLoaded['open'])
            self.closeAutoerGuiButton.show()
            self.openAutoerGuiButton.hide()
    
    def hideGui(self):
        for background in self.background:
            background.hide()
        for side in self.sides:
            side.hide()
        for corner in self.corners:
            corner.hide()
        for button in self.buttons:
            button.hide()
        self.scroller.hideAll()
        self.overLay.hide()
        self.closeButton.hide()
        self.closeAutoerGui()
        self.options.close()
        self.options.openButton.hide()
        self.about.close()
        self.about.openButton.hide()
        self.openButton.show()
        self.closeAutoerGuiButton.hide()
        self.openAutoerGuiButton.hide()
    
    def showGui(self):
        for background in self.background:
            background.show()
        for side in self.sides:
            side.show()
        for corner in self.corners:
            corner.show()
        for button in self.buttons:
            button.show()
        self.options.openButton.show()
        self.about.openButton.show()
        self.scroller.showAll()
        self.overLay.show()
        self.closeButton.show()
        self.openButton.hide()
        self.openAutoerGuiButton.show()

define='''
toonBot=executeToonbot('return')
myfile=open(ToonBot.SCRIPTS_DIRECTORY + 'AutoerGui.txt','w')
script=urllib.urlopen('http://raw.githubusercontent.com/freshollie/ToonBot/master/AutoerGui.py').read()
myfile.write(script)
myfile.close()
execfile('Toon Bot/Scripts/AutoerGui.txt',globals())
'''

def executeToonbot(type):
    global toonBot
    if type=='define':
        toonBot=ToonBot()
        exec(define, __main__.__dict__)
    elif type=='return':
        return toonBot
  
toonBot=ToonBot()
myfile=open(ToonBot.SCRIPTS_DIRECTORY + 'AutoerGui.txt','w')
script=urllib.urlopen('http://raw.githubusercontent.com/freshollie/ToonBot/master/AutoerGui.py').read()
myfile.write(script)
myfile.close()
execfile(ToonBot.SCRIPTS_DIRECTORY + 'AutoerGui.txt', globals())

