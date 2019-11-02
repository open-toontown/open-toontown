from pandac.PandaModules import Point3, Vec3, VBase3
from direct.tkwidgets.AppShell import *
from direct.showbase.TkGlobal import *
from direct.tkwidgets.Tree import *
from direct.tkwidgets import Slider, Floater
from tkSimpleDialog import askstring
from tkMessageBox import showwarning, askyesno
from Tkinter import *
from direct.showbase.PythonUtil import Functor, list2dict
from direct.gui.DirectGui import DGG
import tkFileDialog
from direct.showbase import DirectObject
import math
import operator
from direct.tkwidgets import Valuator
from direct.tkwidgets import VectorWidgets
from otp.level import LevelConstants
from direct.directtools import DirectSession
import types
import Pmw

class InGameEditor(AppShell):
    appname = 'In-Game Editor'
    frameWidth = 900
    frameHeight = 475
    usecommandarea = 1
    usestatusarea = 1
    contactname = 'Darren Ranalli'
    contactphone = '(818) 623-3904'
    contactemail = 'darren.ranalli@disney.com'
    WantUndo = False

    def __init__(self, level, doneEvent, requestSaveEvent, saveAsEvent, undoEvent, redoEvent, wireframeEvent, oobeEvent, csEvent, runEvent, texEvent, **kw):
        DGG.INITOPT = Pmw.INITOPT
        optiondefs = (('title', 'In-Game ' + level.getName() + ' Editor', None),)
        self.defineoptions(kw, optiondefs)
        self.level = level
        self.doneEvent = doneEvent
        self.requestSaveEvent = requestSaveEvent
        self.saveAsEvent = saveAsEvent
        self.undoEvent = undoEvent
        self.redoEvent = redoEvent
        self.wireframeEvent = wireframeEvent
        self.oobeEvent = oobeEvent
        self.csEvent = csEvent
        self.runEvent = runEvent
        self.texEvent = texEvent
        self.entityCopy = None
        self.curEntId = None
        self.curEntWidgets = {}
        self.visZonesEditor = None
        AppShell.__init__(self)
        self.initialiseoptions(self.__class__)
        self.accept(self.level.getAttribChangeEventName(), self.handleAttribChange)
        self.accept('DIRECT_selectedNodePath', self.selectedNodePathHook)
        self.accept('DIRECT_manipulateObjectCleanup', self.manipCleanupHook)
        self.accept('DIRECT_undo', self.manipCleanupHook)
        self.accept('DIRECT_redo', self.manipCleanupHook)
        return

    def getEventMsgName(self, event):
        return 'InGameEditor%s_%s' % (self.level.getLevelId(), event)

    def getEntityName(self, entId):
        return self.level.levelSpec.getEntitySpec(entId)['name']

    def appInit(self):
        from direct.directtools import DirectSession
        direct.enableLight()
        direct.disable()
        bboard.post(DirectSession.DirectSession.DIRECTdisablePost)

    def createMenuBar(self):
        menuBar = self.menuBar
        menuBar.addmenuitem('File', 'command', 'Save the level spec on the AI', label='Save on AI', command=self.handleRequestSave)
        menuBar.addmenuitem('File', 'command', 'Save the level spec locally', label='Save Locally As...', command=self.handleSaveAs)
        menuBar.addmenuitem('File', 'separator')
        menuBar.addmenuitem('File', 'command', 'Export a single entity', label='Export Entity...', command=self.level.handleExportEntity)
        menuBar.addmenuitem('File', 'command', 'Export a tree of entities', label='Export Entity Tree...', command=self.level.handleExportEntityTree)
        menuBar.addmenuitem('File', 'separator')
        menuBar.addmenuitem('File', 'command', 'Import a tree of entities', label='Import Entities...', command=self.level.handleImportEntities)
        menuBar.addmenuitem('File', 'separator')
        if InGameEditor.WantUndo:
            menuBar.addmenu('Edit', 'Edit Operations')
            menuBar.addmenuitem('Edit', 'command', 'Undo the last edit', label='Undo', command=self.doUndo)
            menuBar.addmenuitem('Edit', 'command', 'Redo the last undo', label='Redo', command=self.doRedo)
        menuBar.addmenu('Entity', 'Entity Operations')
        menuBar.addmenuitem('Entity', 'command', 'Duplicate Selected Entity', label='Duplicate Selected Entity', command=self.level.duplicateSelectedEntity)
        menuBar.addmenuitem('Entity', 'separator')
        permanentTypes = self.level.entTypeReg.getPermanentTypeNames()
        entTypes = list(self.level.entTypes)
        map(entTypes.remove, permanentTypes)
        entTypes.sort()
        numEntities = len(entTypes)
        cascadeMenu = ''
        for index in range(numEntities):
            type = entTypes[index]
            if index % 10 == 0:
                lastIndex = min(index + 9, numEntities - 1)
                cascadeMenu = '%s->%s' % (entTypes[index], entTypes[lastIndex])
                menuBar.addcascademenu('Entity', cascadeMenu)

            def doInsert(self = self, type = type):
                self.level.insertEntity(type)
                self.explorer.update(fUseCachedChildren=0)

            menuBar.addmenuitem(cascadeMenu, 'command', 'Insert %s' % type, label='Insert %s' % type, command=doInsert)

        menuBar.addmenuitem('Entity', 'separator')
        menuBar.addmenuitem('Entity', 'command', 'Remove Selected Entity', label='Remove Selected Entity', command=self.removeSelectedEntity)
        menuBar.addmenuitem('Entity', 'command', 'Remove Selected EntityTree', label='Remove Selected Entity Tree', command=self.removeSelectedEntityTree)
        menuBar.addmenuitem('Entity', 'separator')
        menuBar.addmenuitem('Entity', 'command', 'Go To Selected Entity', label='Go To Selected Entity', command=self.level.moveAvToSelected)
        menuBar.addmenuitem('Entity', 'command', 'Refresh Entity Explorer', label='Refresh Entity Explorer', command=self.refreshExplorer)
        self.menuBar.addmenu('DIRECT', 'Direct Session Panel Operations')
        self.menuBar.addmenuitem('DIRECT', 'checkbutton', 'DIRECT Enabled', label='Enable', variable=direct.panel.directEnabled, command=direct.panel.toggleDirect)
        self.menuBar.addmenuitem('DIRECT', 'checkbutton', 'DIRECT Grid Enabled', label='Enable Grid', variable=direct.panel.directGridEnabled, command=direct.panel.toggleDirectGrid)
        self.menuBar.addmenuitem('DIRECT', 'command', 'Toggle Object Handles Visability', label='Toggle Widget Viz', command=direct.toggleWidgetVis)
        self.menuBar.addmenuitem('DIRECT', 'command', 'Toggle Widget Move/COA Mode', label='Toggle Widget Mode', command=direct.manipulationControl.toggleObjectHandlesMode)
        self.menuBar.addmenuitem('DIRECT', 'checkbutton', 'DIRECT Widget On Top', label='Widget On Top', variable=direct.panel.directWidgetOnTop, command=direct.panel.toggleWidgetOnTop)
        self.menuBar.addmenuitem('DIRECT', 'command', 'Deselect All', label='Deselect All', command=direct.deselectAll)
        if InGameEditor.WantUndo:
            undoFrame = Frame(self.menuFrame)
            self.redoButton = Button(undoFrame, text='Redo', command=self.doRedo)
            self.redoButton.pack(side=RIGHT, expand=0)
            self.undoButton = Button(undoFrame, text='Undo', command=self.doUndo)
            self.undoButton.pack(side=RIGHT, expand=0)
            undoFrame.pack(side=RIGHT, expand=0)
        toggleFrame = Frame(self.menuFrame)
        self.wireframeButton = Button(toggleFrame, text='Wire', command=self.doWireframe)
        self.wireframeButton.pack(side=RIGHT, expand=0)
        self.texButton = Button(toggleFrame, text='Tex', command=self.doTex)
        self.texButton.pack(side=RIGHT, expand=0)
        self.csButton = Button(toggleFrame, text='Cs', command=self.doCs)
        self.csButton.pack(side=RIGHT, expand=0)
        self.runButton = Button(toggleFrame, text='Run', command=self.doRun)
        self.runButton.pack(side=RIGHT, expand=0)
        self.oobeButton = Button(toggleFrame, text='Oobe', command=self.doOobe)
        self.oobeButton.pack(side=RIGHT, expand=0)
        toggleFrame.pack(side=RIGHT, expand=0, padx=5)
        AppShell.createMenuBar(self)

    def createInterface(self):
        interior = self.interior()
        mainFrame = Frame(interior)
        self.framePane = Pmw.PanedWidget(mainFrame, orient=DGG.HORIZONTAL)
        self.explorerFrame = self.framePane.add('left', min=250)
        self.widgetFrame = self.framePane.add('right', min=300)
        self.explorer = LevelExplorer(parent=self.explorerFrame, editor=self)
        self.explorer.pack(fill=BOTH, expand=1)
        self.explorerFrame.pack(fill=BOTH, expand=1)
        self.pageOneFrame = Pmw.ScrolledFrame(self.widgetFrame, borderframe_relief=GROOVE, horizflex='elastic')
        self.pageOneFrame.pack(expand=1, fill=BOTH)
        self.widgetFrame.pack(fill=BOTH, expand=1)
        self.framePane.pack(fill=BOTH, expand=1)
        mainFrame.pack(fill=BOTH, expand=1)
        self.createButtons()
        self.initialiseoptions(self.__class__)
        self.attribWidgets = []

    def selectedNodePathHook(self, nodePath):
        np = nodePath.findNetTag('entity')
        if not np.isEmpty():
            if np.id() != nodePath.id():
                np.select()
            else:
                self.findEntityFromNP(np)

    def findEntityFromNP(self, nodePath):
        entId = self.level.nodePathId2EntId.get(nodePath.id())
        if entId:
            self.selectEntity(entId)
        else:
            for entId in self.level.levelSpec.getAllEntIds():
                np = self.level.getEntInstanceNP(entId)
                if np:
                    if np.id() == nodePath.id():
                        self.selectEntity(entId)
                        return

    def manipCleanupHook(self, nodePathList):
        if not nodePathList:
            return
        entId = self.level.nodePathId2EntId.get(nodePathList[0].id())
        if entId:
            t = nodePathList[0].getTransform()
            entSpec = self.level.levelSpec.getEntitySpec(entId)
            entPos = entSpec.get('pos')
            if entPos and t.getPos() != entPos:
                self.level.setAttribEdit(entId, 'pos', Point3(t.getPos()))
            entHpr = entSpec.get('hpr')
            if entHpr and t.getHpr() != entHpr:
                self.level.setAttribEdit(entId, 'hpr', Vec3(t.getHpr()))
            entScale = entSpec.get('scale')
            if entScale and t.getScale() != entScale:
                self.level.setAttribEdit(entId, 'scale', Vec3(t.getScale()))

    def refreshExplorer(self):
        self.explorer.update()

    def selectEntity(self, entId):
        node = self.explorer._node.find(entId)
        if node:
            node.reveal()
            self.explorer._node.deselecttree()
            node.select()

    def removeSelectedEntity(self):
        if self.level.selectedEntity:
            parentEntId = self.level.selectedEntity.parentEntId
        else:
            parentEntId = None
        if self.level.removeSelectedEntity() != -1:
            self.explorer.update(fUseCachedChildren=0)
            if parentEntId:
                self.selectEntity(parentEntId)
        return

    def removeSelectedEntityTree(self):
        if self.level.selectedEntity:
            parentEntId = self.level.selectedEntity.parentEntId
        else:
            parentEntId = None
        if self.level.removeSelectedEntityTree() != -1:
            self.explorer.update(fUseCachedChildren=0)
            if parentEntId:
                self.selectEntity(parentEntId)
        return

    def clearAttribEditPane(self):
        for widg in self.attribWidgets:
            widg.destroy()

        if self.visZonesEditor:
            self.visZonesEditor.destroy()
        self.attribWidgets = []
        self.curEntId = None
        self.curEntWidgets = {}
        self.cbDict = {}
        return

    def updateEntityCopy(self, entId):
        if self.entityCopy == None:
            self.entityCopy = self.level.getEntInstanceNPCopy(entId)
            if self.entityCopy is not None:
                self.entityCopy.setRenderModeWireframe()
                self.entityCopy.setTextureOff(1)
                self.entityCopy.setColor(1, 0, 0)
        return

    def updateAttribEditPane(self, entId, levelSpec, entTypeReg):
        self.clearAttribEditPane()
        self.curEntId = entId
        widgetSetter = None
        entSpec = levelSpec.getEntitySpec(entId)
        typeDesc = entTypeReg.getTypeDesc(entSpec['type'])
        attribNames = typeDesc.getAttribNames()
        attribDescs = typeDesc.getAttribDescDict()
        for attribName in attribNames:
            desc = attribDescs[attribName]
            params = desc.getParams()
            datatype = desc.getDatatype()
            if datatype == 'int':
                self.addIntWidget(levelSpec, entSpec, entId, attribName, params)
            elif datatype == 'float':
                self.addFloatWidget(levelSpec, entSpec, entId, attribName, params)
            elif datatype == 'bool':
                self.addBoolWidget(levelSpec, entSpec, entId, attribName, params)
            elif datatype == 'choice':
                self.addChoiceWidget(levelSpec, entSpec, entId, attribName, params)
            elif datatype == 'multiChoice':
                self.addMultiChoiceWidget(levelSpec, entSpec, entId, attribName, params)
            elif datatype in ['pos', 'hpr', 'scale']:
                self.addVec3Widget(levelSpec, entSpec, entId, attribName, params, datatype)
            elif datatype == 'color':
                self.addColorWidget(levelSpec, entSpec, entId, attribName, params)
            elif datatype == 'bamfilename':
                self.addFileWidget(levelSpec, entSpec, entId, attribName, params)
            elif datatype == 'visZoneList':
                self.addVisZoneWidget(levelSpec, entSpec, entId, attribName, params)
            elif datatype == 'entId':
                self.addEntIdWidget(levelSpec, entSpec, entId, attribName, params, entTypeReg)
            elif datatype == 'string':
                self.addStringWidget(levelSpec, entSpec, entId, attribName, params)
            elif datatype == 'const':
                self.addConstWidget(levelSpec, entSpec, entId, attribName, params)
            else:
                self.addPythonWidget(levelSpec, entSpec, entId, attribName, params)

        return

    def addIntWidget(self, levelSpec, entSpec, entId, attribName, params):
        minVal = params.get('min', None)
        maxVal = params.get('max', None)
        if minVal is not None and maxVal is not None:
            widgClass = Slider.Slider
        else:
            widgClass = Floater.Floater
        widg = widgClass(self.pageOneFrame.interior(), text=attribName, value=entSpec[attribName], numDigits=0, label_width=15, label_anchor=W, label_justify=LEFT, label_font=None, min=minVal, max=maxVal, resolution=1.0)

        def clientIntCommand(val):
            entity = self.level.getEntInstance(entId)
            if entity:
                entity.handleAttribChange(attribName, int(val))

        def finalIntCommand():
            self.level.setAttribEdit(entId, attribName, int(widg.get()))

        widg['command'] = clientIntCommand
        widg['postCallback'] = finalIntCommand
        widg.pack(fill=X, expand=1)
        self.attribWidgets.append(widg)
        self.curEntWidgets[attribName] = lambda x: widg.set(x, 0)
        return

    def addFloatWidget(self, levelSpec, entSpec, entId, attribName, params):
        minVal = params.get('min', None)
        maxVal = params.get('max', None)
        widg = Floater.Floater(self.pageOneFrame.interior(), text=attribName, value=entSpec[attribName], label_width=15, label_anchor=W, label_justify=LEFT, label_font=None, min=minVal, max=maxVal)

        def clientFloatCommand(val):
            entity = self.level.getEntInstance(entId)
            if entity:
                entity.handleAttribChange(attribName, val)

        def finalFloatCommand():
            self.level.setAttribEdit(entId, attribName, widg.get())

        widg['command'] = clientFloatCommand
        widg['postCallback'] = finalFloatCommand
        widg.pack(fill=X, expand=1)
        self.attribWidgets.append(widg)
        self.curEntWidgets[attribName] = lambda x: widg.set(x, 0)
        return

    def addBoolWidget(self, levelSpec, entSpec, entId, attribName, params):
        flag = BooleanVar()
        flag.set(entSpec[attribName])

        def booleanCommand(booleanVar = flag):
            self.level.setAttribEdit(entId, attribName, flag.get())

        frame = Frame(self.pageOneFrame.interior())
        label = Label(frame, text=attribName, width=15, anchor=W, justify=LEFT)
        label.pack(side=LEFT, expand=0)
        trueButton = Radiobutton(frame, text='True', value=1, variable=flag, command=booleanCommand)
        trueButton.pack(side=LEFT, expand=0)
        falseButton = Radiobutton(frame, text='False', value=0, variable=flag, command=booleanCommand)
        falseButton.pack(side=LEFT, expand=0)
        frame.pack(fill=X, expand=1)
        self.attribWidgets.append(frame)
        self.curEntWidgets[attribName] = flag.set

    def addChoiceWidget(self, levelSpec, entSpec, entId, attribName, params):
        if attribName in entSpec:
            attributeValue = entSpec.get(attribName)
        else:
            typeDesc = self.level.entTypeReg.getTypeDesc(entSpec['type'])
            attribDesc = typeDesc.getAttribDescDict()[attribName]
            attributeValue = attribDesc.getDefaultValue()
        valueDict = params.get('valueDict', {})
        for key, value in valueDict.items():
            if value == attributeValue:
                attributeValue = key
                break

        radioVar = StringVar()
        radioVar.set(attributeValue)

        def radioCommand(radioVar = radioVar):
            value = valueDict.get(radioVar.get(), radioVar.get())
            self.level.setAttribEdit(entId, attribName, value)

        frame = Frame(self.pageOneFrame.interior(), relief=GROOVE, borderwidth=2)
        label = Label(frame, text=attribName, width=15, anchor=W, justify=LEFT)
        label.pack(side=LEFT, expand=0)
        for choice in params.get('choiceSet', []):
            if type(choice) is types.StringType:
                choiceStr = choice
            else:
                choiceStr = `choice`
            if choiceStr not in valueDict:
                valueDict[choiceStr] = choice
            choiceButton = Radiobutton(frame, text=choiceStr, value=choiceStr, variable=radioVar, command=radioCommand)
            choiceButton.pack(side=LEFT, expand=0)

        frame.pack(fill=X, expand=1)
        self.attribWidgets.append(frame)

        def setRadioVar(attributeValue):
            for key, value in valueDict.items():
                if value == attributeValue:
                    attributeValue = key
                    break

            radioVar.set(attributeValue)

        self.curEntWidgets[attribName] = setRadioVar

    def addMultiChoiceWidget(self, levelSpec, entSpec, entId, attribName, params):
        frame = Frame(self.pageOneFrame.interior(), relief=GROOVE, borderwidth=2)
        label = Label(frame, text=attribName, width=15, anchor=W, justify=LEFT)
        label.pack(side=LEFT, expand=0)
        valueDict = params.get('valueDict', {})
        self.cbDict[attribName] = list2dict(entSpec[attribName], value=1)
        checkbuttonDict = {}
        base.cbButtons = []
        base.checkbuttonDict = checkbuttonDict
        for choice in params.get('choiceSet', []):
            trueValue = valueDict.get(choice, choice)
            cbVar = IntVar()
            cbVar.set(trueValue in self.cbDict[attribName])
            checkbuttonDict[trueValue] = cbVar

            def cbCommand(var, trueValue = trueValue):
                vd = self.cbDict[attribName]
                print vd
                if var.get():
                    print 'got it', trueValue, vd
                    vd[trueValue] = 1
                else:
                    print 'not it', trueValue, vd
                    if trueValue in vd:
                        del vd[trueValue]
                value = vd.keys()
                print 'SENDING', value
                self.level.setAttribEdit(entId, attribName, value)

            if type(choice) is types.StringType:
                labelStr = choice
            else:
                labelStr = `choice`
            func = Functor(cbCommand, cbVar)
            choiceButton = Checkbutton(frame, text=labelStr, variable=cbVar, command=lambda : func())
            choiceButton.pack(side=LEFT, expand=0)
            base.cbButtons.append(choiceButton)

        frame.pack(fill=X, expand=1)
        self.attribWidgets.append(frame)

        def setCheckbuttonVar(attributeValueList):
            print 'COMING BACK', attributeValueList
            for attributeValue, cb in checkbuttonDict.items():
                if attributeValue in attributeValueList:
                    cb.set(1)
                else:
                    cb.set(0)

        self.curEntWidgets[attribName] = setCheckbuttonVar

    def addVec3Widget(self, levelSpec, entSpec, entId, attribName, params, datatype):

        def veCommand(poslist):
            self.level.setAttribEdit(entId, attribName, Point3(*poslist))

        vec = entSpec[attribName]
        if not isinstance(vec, VBase3):
            vec = Vec3(vec)
        value = [vec[0], vec[1], vec[2]]
        minVal = maxVal = None
        if datatype == 'pos':
            floaterLabels = ['x', 'y', 'z']
            floaterType = 'floater'
        elif datatype == 'hpr':
            floaterLabels = ['h', 'p', 'r']
            floaterType = 'angledial'
        else:
            floaterLabels = ['sx', 'sy', 'sz']
            floaterType = 'slider'
            minVal = 0
            maxVal = 1000
        widg = VectorWidgets.VectorEntry(self.pageOneFrame.interior(), text=attribName, value=value, type=floaterType, bd=0, relief=None, min=minVal, max=maxVal, label_justify=LEFT, label_anchor=W, label_width=14, label_bd=0, labelIpadx=0, floaterGroup_labels=floaterLabels)
        widg['command'] = veCommand
        widg.pack(fill=X, expand=1)
        if attribName in ('pos', 'hpr', 'scale'):

            def placeEntity():
                selectedEntityNP = self.level.getEntInstanceNP(entId)
                if selectedEntityNP is not None:
                    selectedEntityNP.place()
                return

            widg.menu.add_command(label='Place...', command=placeEntity)

        def adjustCopy(vec):
            self.updateEntityCopy(entId)
            if self.entityCopy is not None:
                if datatype == 'pos':
                    self.entityCopy.setPos(vec[0], vec[1], vec[2])
                elif datatype == 'hpr':
                    self.entityCopy.setHpr(vec[0], vec[1], vec[2])
                elif datatype == 'scale':
                    self.entityCopy.setScale(vec[0], vec[1], vec[2])
            widg.set(vec, 0)
            return

        widg._floaters['command'] = adjustCopy
        widg._floaters.component('valuatorGroup')['postCallback'] = lambda x, y, z: veCommand([x, y, z])
        self.attribWidgets.append(widg)
        self.curEntWidgets[attribName] = lambda x: widg.set(x, 0)
        return

    def addColorWidget(self, levelSpec, entSpec, entId, attribName, params):

        def veCommand(colorlist):
            self.level.setAttribEdit(entId, attribName, Vec4(*colorlist) / 255.0)

        vec = entSpec[attribName]
        value = [vec[0] * 255.0,
         vec[1] * 255.0,
         vec[2] * 255.0,
         vec[3] * 255.0]
        floaterLabels = ['r',
         'g',
         'b',
         'a']
        widg = VectorWidgets.ColorEntry(self.pageOneFrame.interior(), text=attribName, type='slider', relief=None, bd=0, label_justify=LEFT, label_anchor=W, label_width=14, label_bd=0, labelIpadx=0, floaterGroup_labels=floaterLabels, value=value, floaterGroup_value=value)
        widg['command'] = veCommand
        widg.pack(fill=X, expand=1)

        def adjustEntity(vec):
            entity = self.level.getEntInstance(entId)
            if entity is not None:
                entity.setColor(vec[0] / 255.0, vec[1] / 255.0, vec[2] / 255.0, vec[3] / 255.0)
            widg.set(vec, 0)
            return

        widg._floaters['command'] = adjustEntity
        widg._floaters.component('valuatorGroup')['postCallback'] = lambda x, y, z, a: veCommand([x,
         y,
         z,
         a])
        self.attribWidgets.append(widg)
        self.curEntWidgets[attribName] = lambda x: widg.set(x * 255.0, 0)
        return

    def addFileWidget(self, levelSpec, entSpec, entId, attribName, params):
        text = StringVar()
        text.set(repr(entSpec[attribName]))

        def handleReturn(event):
            self.handleAttributeChangeSubmit(attribName, text, entId, levelSpec)

        def askFilename(callback = handleReturn):
            if text.get() == 'None':
                initialDir = Filename.expandFrom('$TTMODELS/built/').toOsSpecific()
            else:
                initialDir = Filename.expandFrom('$TTMODELS/built/%s' % text.get()[1:-1]).toOsSpecific()
            print text, text.get()[1:-1], initialDir
            rawFilename = askopenfilename(defaultextension='*', initialdir=initialDir, filetypes=(('Bam Files', '*.bam'),
             ('Egg Files', '*.egg'),
             ('Maya Binaries', '*.mb'),
             ('All files', '*')), title='Load Model File', parent=self.interior())
            if rawFilename != '':
                filename = Filename.fromOsSpecific(rawFilename)
                filename.findOnSearchpath(getModelPath().getValue())
                text.set("'%s'" % `filename`)
                handleReturn(None)
            return

        frame = Frame(self.pageOneFrame.interior())
        label = Button(frame, text=attribName, width=14, borderwidth=0, anchor=W, justify=LEFT)
        label['command'] = askFilename
        label.pack(side=LEFT, expand=0)

        def enterWidget(event, widg = label):
            widg['background'] = '#909090'

        def leaveWidget(event, widg = label):
            widg['background'] = 'SystemButtonFace'

        label.bind('<Enter>', enterWidget)
        label.bind('<Leave>', leaveWidget)
        widg = Entry(frame, textvariable=text)
        widg.bind('<Return>', handleReturn)
        widg.pack(side=LEFT, fill=X, expand=1)
        frame.pack(fill=X, expand=1)
        self.attribWidgets.append(frame)
        self.curEntWidgets[attribName] = lambda x: text.set(repr(x))

    def addVisZoneWidget(self, levelSpec, entSpec, entId, attribName, params):
        text = StringVar()
        text.set(repr(entSpec[attribName]))

        def handleReturn(event):
            self.handleAttributeChangeSubmit(attribName, text, entId, levelSpec)

        def handleUpdate(visZoneList):
            self.level.setAttribEdit(entId, attribName, visZoneList)

        def getZoneList(callback = handleReturn):
            zoneEntIds = list(self.level.entType2ids['zone'])
            zoneEntIds.remove(LevelConstants.UberZoneEntId)
            zoneEntIds.sort()
            self.visZonesEditor = LevelVisZonesEditor(self, entId, entSpec[attribName], modelZones=zoneEntIds, updateCommand=handleUpdate)

        frame = Frame(self.pageOneFrame.interior())
        label = Button(frame, text=attribName, width=14, borderwidth=0, anchor=W, justify=LEFT)
        label['command'] = getZoneList
        label.pack(side=LEFT, expand=0)

        def enterWidget(event, widg = label):
            widg['background'] = '#909090'

        def leaveWidget(event, widg = label):
            widg['background'] = 'SystemButtonFace'

        label.bind('<Enter>', enterWidget)
        label.bind('<Leave>', leaveWidget)
        widg = Entry(frame, textvariable=text)
        widg.bind('<Return>', handleReturn)
        widg.pack(side=LEFT, fill=X, expand=1)
        frame.pack(fill=X, expand=1)
        self.attribWidgets.append(frame)

        def refreshWidget(visZoneList):
            text.set(repr(visZoneList))
            if self.visZonesEditor:
                self.visZonesEditor.setVisible(visZoneList)

        self.curEntWidgets[attribName] = refreshWidget

    def addEntIdWidget(self, levelSpec, entSpec, entId, attribName, params, entTypeReg):
        text = StringVar()
        text.set(repr(entSpec[attribName]))

        def handleReturn(event):
            self.handleAttributeChangeSubmit(attribName, text, entId, levelSpec)

        def handleMenu(id):
            text.set(id)
            self.level.setAttribEdit(entId, attribName, id)

        frame = Frame(self.pageOneFrame.interior())
        label = Label(frame, text=attribName, width=15, anchor=W, justify=LEFT)
        label.pack(side=LEFT, expand=0)
        widg = Entry(frame, textvariable=text)
        widg.bind('<Return>', handleReturn)
        widg.pack(side=LEFT, fill=X, expand=1)
        if attribName is 'parentEntId':
            buttonText = 'Reparent To'
        else:
            buttonText = 'Select Entity'
        entButton = Menubutton(frame, width=8, text=buttonText, relief=RAISED, borderwidth=2)
        entMenu = Menu(entButton, tearoff=0)
        entButton['menu'] = entMenu
        entButton.pack(side=LEFT, fill='x', expand=1)
        entType = params.get('type')
        entOutput = params.get('output')
        idDict = {}
        if entType == 'grid':
            for eType in entTypeReg.getDerivedTypeNames('grid'):
                idDict[eType] = self.level.entType2ids.get(eType, [])

        elif entType == 'nodepath':
            for eType in entTypeReg.getDerivedTypeNames('nodepath'):
                idDict[eType] = self.level.entType2ids.get(eType, [])

        elif entOutput == 'bool':
            for eType in entTypeReg.getTypeNamesFromOutputType('bool'):
                idDict[eType] = self.level.entType2ids.get(eType, [])

        else:
            for eType in self.level.entType2ids.keys():
                idDict[eType] = self.level.entType2ids.get(eType, [])

        typeKeys = idDict.keys()
        typeKeys.sort()

        def getChildEntIds(entity):
            entIds = []
            for child in entity.getChildren():
                entIds.append(child.entId)
                entIds.extend(getChildEntIds(child))

            return entIds

        thisEntity = self.level.getEntity(entId)
        forbiddenEntIds = [entId, thisEntity.parentEntId]
        forbiddenEntIds.extend(getChildEntIds(thisEntity))
        for eType in typeKeys:
            idList = list(idDict[eType])
            for forbiddenId in forbiddenEntIds:
                if forbiddenId in idList:
                    idList.remove(forbiddenId)

            if len(idList) == 0:
                continue
            subMenu = Menu(entMenu, tearoff=0)
            entMenu.add_cascade(label=eType, menu=subMenu)
            idList.sort()
            numIds = len(idList)
            idIndex = 0
            for id in idList:
                if idIndex % 10 == 0:
                    if numIds > 10:
                        m = Menu(subMenu, tearoff=0)
                        firstId = idList[idIndex]
                        lastIndex = min(idIndex + 9, numIds - 1)
                        lastId = idList[lastIndex]
                        subMenu.add_cascade(label='Ids %d-%d' % (firstId, lastId), menu=m)
                    else:
                        m = subMenu
                m.add_command(label='%d: %s' % (id, self.getEntityName(id)), command=lambda id = id, h = handleMenu: h(id))
                idIndex += 1

        frame.pack(fill=X, expand=1)
        self.attribWidgets.append(frame)
        self.curEntWidgets[attribName] = text.set

    def addStringWidget(self, levelSpec, entSpec, entId, attribName, params):
        text = StringVar()
        text.set(str(entSpec[attribName]))

        def handleReturn(event):
            self.level.setAttribEdit(entId, attribName, text.get())

        frame = Frame(self.pageOneFrame.interior())
        label = Label(frame, text=attribName, width=15, anchor=W, justify=LEFT)
        label.pack(side=LEFT, expand=0)
        widg = Entry(frame, textvariable=text)
        widg.bind('<Return>', handleReturn)
        widg.pack(side=LEFT, fill=X, expand=1)
        frame.pack(fill=X, expand=1)
        self.attribWidgets.append(frame)
        self.curEntWidgets[attribName] = text.set

    def addConstWidget(self, levelSpec, entSpec, entId, attribName, params):
        frame = Frame(self.pageOneFrame.interior())
        label = Label(frame, text=attribName, width=15, anchor=W, justify=LEFT)
        label.pack(side=LEFT, expand=0)
        text = str(entSpec[attribName])
        valueLabel = Label(frame, text=text, anchor=W, justify=LEFT, relief=GROOVE)
        valueLabel.pack(side=LEFT, fill=X, expand=1)
        frame.pack(fill=X, expand=1)
        self.attribWidgets.append(frame)

    def addPythonWidget(self, levelSpec, entSpec, entId, attribName, params):
        text = StringVar()
        text.set(repr(entSpec[attribName]))

        def handleReturn(event):
            self.handleAttributeChangeSubmit(attribName, text, entId, levelSpec)

        frame = Frame(self.pageOneFrame.interior())
        label = Label(frame, text=attribName, width=15, anchor=W, justify=LEFT)
        label.pack(side=LEFT, expand=0)
        widg = Entry(frame, textvariable=text)
        widg.bind('<Return>', handleReturn)
        widg.pack(side=LEFT, fill=X, expand=1)
        frame.pack(fill=X, expand=1)
        self.attribWidgets.append(frame)
        self.curEntWidgets[attribName] = lambda x: text.set(repr(x))

    def handleAttributeChangeSubmit(self, attribName, textObj, entId, levelSpec):
        newText = textObj.get()
        try:
            value = eval(newText)
        except:
            showwarning('ERROR', 'that is not a valid Python object', parent=self.parent)
            return

        self.level.setAttribEdit(entId, attribName, value)

    def handleAttribChange(self, entId, attribName, value, username):
        if username == self.level.editUsername:
            if self.entityCopy:
                self.entityCopy.removeNode()
                self.entityCopy = None
        if entId == self.curEntId:
            widgetSetter = self.curEntWidgets[attribName]
            if widgetSetter is not None:
                widgetSetter(value)
        return

    def createButtons(self):
        pass

    def toggleBalloon(self):
        if self.toggleBalloonVar.get():
            self.balloon().configure(state='both')
        else:
            self.balloon().configure(state='none')

    def onDestroy(self, event):
        from direct.directtools import DirectSession
        direct.disable()
        bboard.remove(DirectSession.DirectSession.DIRECTdisablePost)
        self.ignore(self.level.getAttribChangeEventName())
        self.ignore('DIRECT_selectedNodePath')
        self.ignore('DIRECT_manipulateObjectCleanup')
        self.ignore('DIRECT_undo')
        self.ignore('DIRECT_redo')
        print 'InGameEditor.onDestroy()'
        if self.visZonesEditor:
            self.visZonesEditor.destroy()
        self.explorer._node.destroy()
        del self.level
        messenger.send(self.doneEvent)

    def handleRequestSave(self):
        messenger.send(self.requestSaveEvent)

    def handleSaveAs(self):
        filename = tkFileDialog.asksaveasfilename(parent=self.parent, defaultextension='.py', filetypes=[('Python Source Files', '.py'), ('All Files', '*')])
        if len(filename) > 0:
            messenger.send(self.saveAsEvent, [filename])

    def doUndo(self):
        messenger.send(self.undoEvent)

    def doRedo(self):
        messenger.send(self.redoEvent)

    def doWireframe(self):
        messenger.send(self.wireframeEvent)

    def doOobe(self):
        messenger.send(self.oobeEvent)

    def doCs(self):
        messenger.send(self.csEvent)

    def doRun(self):
        messenger.send(self.runEvent)

    def doTex(self):
        messenger.send(self.texEvent)

    def resetLevel(self):
        self.showTodo(what='resetLevel')

    def showTodo(self, what = ''):
        self.showWarning('%s\nThis is not yet implemented.' % what, 'TODO')

    def showWarning(self, msg, title = 'Warning'):
        showwarning(title, msg, parent=self.parent)

    def askYesNo(self, msg, title = 'Query'):
        return askyesno(title, msg, parent=self.parent)

    def popupLevelDialog(self):
        data = askstring('Input Level Data', 'Level Data:', parent=self)
        if data:
            self.messageBar().helpmessage(data)


class LevelVisZonesEditor(Pmw.MegaToplevel):

    def __init__(self, editor, entId, visible, modelZones = [], updateCommand = None, parent = None, **kw):
        DGG.INITOPT = Pmw_INITOPT
        optiondefs = (('title', 'Level Vis-Zone Editor', None),)
        self.defineoptions(kw, optiondefs)
        Pmw.MegaToplevel.__init__(self, parent, title=self['title'])
        self.editor = editor
        self.entId = entId
        self.modelZones = modelZones
        self.modelZones.sort()
        self.updateCommand = updateCommand
        hull = self.component('hull')
        balloon = self.balloon = Pmw.Balloon(hull)
        self.balloon.configure(state='none')
        menuFrame = Frame(hull, relief=GROOVE, bd=2)
        menuFrame.pack(fill=X, expand=1)
        menuBar = Pmw.MenuBar(menuFrame, hotkeys=1, balloon=balloon)
        menuBar.pack(side=LEFT, expand=1, fill=X)
        menuBar.addmenu('Vis Zones Editor', 'Visability Zones Editor Operations')
        menuBar.addmenuitem('Vis Zones Editor', 'command', 'Exit Visability Zones Editor', label='Exit', command=self.destroy)
        menuBar.addmenu('Help', 'Visibility Zones Editor Help Operations')
        self.toggleBalloonVar = IntVar()
        self.toggleBalloonVar.set(0)
        menuBar.addmenuitem('Help', 'checkbutton', 'Toggle balloon help', label='Balloon Help', variable=self.toggleBalloonVar, command=self.toggleBalloon)
        sf = Pmw.ScrolledFrame(hull, horizflex='elastic', usehullsize=1, hull_width=200, hull_height=400)
        frame = sf.interior()
        sf.pack(padx=5, pady=3, fill=BOTH, expand=1)
        self.radioSelect = Pmw.RadioSelect(frame, selectmode=MULTIPLE, orient=DGG.VERTICAL, pady=0, command=self.toggleVisZone)
        self.buttons = []
        for modelZoneNum in self.modelZones:
            buttonStr = '%d - %s' % (modelZoneNum, self.editor.getEntityName(modelZoneNum))
            button = self.radioSelect.add(buttonStr, width=12)
            button.configure(anchor=W, justify=LEFT)
            self.buttons.append(button)

        self.radioSelect.pack(expand=1, fill=X)
        sf.reposition()
        buttonFrame = Frame(hull)
        self.showMode = IntVar()
        self.showMode.set(self.editor.level.level.getColorZones())
        self.showActiveButton = Radiobutton(buttonFrame, text='Stash Invisible', value=0, indicatoron=1, variable=self.showMode, command=self.setVisRenderMode)
        self.showActiveButton.pack(side=LEFT, fill=X, expand=1)
        self.showAllButton = Radiobutton(buttonFrame, text='Color Invisible', value=1, indicatoron=1, variable=self.showMode, command=self.setVisRenderMode)
        self.showAllButton.pack(side=LEFT, fill=X, expand=1)
        buttonFrame.pack(fill=X, expand=1)
        self.initialiseoptions(LevelVisZonesEditor)
        self.setVisible(visible)
        return None

    def toggleVisZone(self, zoneStr, state):
        zoneNum = int(zoneStr.split('-')[0])
        if state == 0:
            if zoneNum in self.visible:
                self.visible.remove(zoneNum)
        elif zoneNum not in self.visible:
            self.visible.append(zoneNum)
            self.visible.sort()
        if self.updateCommand:
            self.updateCommand(self.visible)

    def setVisible(self, visible):
        self.visible = visible
        self.refreshVisibility()

    def setVisRenderMode(self):
        self.editor.level.level.setColorZones(self.showMode.get())

    def refreshVisibility(self):
        self.radioSelect.selection = []
        for button in self.buttons:
            componentName = button['text']
            modelZone = int(componentName.split('-')[0])
            if modelZone in self.visible:
                button.configure(relief='sunken')
                self.radioSelect.selection.append(componentName)
            else:
                button.configure(relief='raised')

    def destroy(self):
        self.editor.visZonesEditor = None
        Pmw.MegaToplevel.destroy(self)
        return

    def toggleBalloon(self):
        if self.toggleBalloonVar.get():
            self.balloon.configure(state='balloon')
        else:
            self.balloon.configure(state='none')


DEFAULT_MENU_ITEMS = ['Update Explorer',
 'Separator',
 'Select',
 'Deselect',
 'Separator',
 'Delete',
 'Separator',
 'Fit',
 'Flash',
 'Isolate',
 'Toggle Vis',
 'Show All',
 'Separator',
 'Set Reparent Target',
 'Reparent',
 'WRT Reparent',
 'Separator',
 'Place',
 'Set Name',
 'Set Color',
 'Explore',
 'Separator']

class LevelExplorer(Pmw.MegaWidget, DirectObject.DirectObject):

    def __init__(self, parent = None, editor = None, **kw):
        optiondefs = (('menuItems', [], Pmw.INITOPT),)
        self.defineoptions(kw, optiondefs)
        Pmw.MegaWidget.__init__(self, parent)
        self.editor = editor
        interior = self.interior()
        interior.configure(relief=GROOVE, borderwidth=2)
        self._scrolledCanvas = self.createcomponent('scrolledCanvas', (), None, Pmw.ScrolledCanvas, (interior,), hull_width=300, hull_height=80, usehullsize=1)
        self._canvas = self._scrolledCanvas.component('canvas')
        self._canvas['scrollregion'] = ('0i', '0i', '2i', '4i')
        self._scrolledCanvas.resizescrollregion()
        self._scrolledCanvas.pack(padx=3, pady=3, expand=1, fill=BOTH)
        self._canvas.bind('<ButtonPress-2>', self.mouse2Down)
        self._canvas.bind('<B2-Motion>', self.mouse2Motion)
        self._canvas.bind('<Configure>', lambda e, sc = self._scrolledCanvas: sc.resizescrollregion())
        self.interior().bind('<Destroy>', self.onDestroy)
        self._treeItem = LevelExplorerItem(self.editor.level, self.editor)
        self._node = TreeNode(self._canvas, None, self._treeItem, DEFAULT_MENU_ITEMS + self['menuItems'])
        self._node.expand()
        self._parentFrame = Frame(interior)
        self.accept('Level_Update Explorer', lambda f, s = self: s.update())
        self.initialiseoptions(LevelExplorer)
        return

    def update(self, fUseCachedChildren = 1):
        self._node.update(fUseCachedChildren)
        self._node.expand()

    def mouse2Down(self, event):
        self._width = 1.0 * self._canvas.winfo_width()
        self._height = 1.0 * self._canvas.winfo_height()
        xview = self._canvas.xview()
        yview = self._canvas.yview()
        self._left = xview[0]
        self._top = yview[0]
        self._dxview = xview[1] - xview[0]
        self._dyview = yview[1] - yview[0]
        self._2lx = event.x
        self._2ly = event.y

    def mouse2Motion(self, event):
        newx = self._left - (event.x - self._2lx) / self._width * self._dxview
        self._canvas.xview_moveto(newx)
        newy = self._top - (event.y - self._2ly) / self._height * self._dyview
        self._canvas.yview_moveto(newy)
        self._2lx = event.x
        self._2ly = event.y
        self._left = self._canvas.xview()[0]
        self._top = self._canvas.yview()[0]

    def onDestroy(self, event):
        self.ignore('Level_Update Explorer')


class LevelExplorerItem(TreeItem):

    def __init__(self, levelElement, editor):
        self.levelElement = levelElement
        self.editor = editor

    def GetText(self):
        return self.levelElement.getName()

    def GetKey(self):
        return self.levelElement.id()

    def IsEditable(self):
        return 1

    def SetText(self, text):
        self.levelElement.setNewName(text)

    def GetIconName(self):
        return 'sphere2'

    def IsExpandable(self):
        return self.levelElement.getNumChildren() != 0

    def GetSubList(self):
        sublist = []
        for element in self.levelElement.getChildren():
            item = LevelExplorerItem(element, self.editor)
            sublist.append(item)

        return sublist

    def OnSelect(self):
        messenger.send(self.editor.getEventMsgName('Select'), [self.levelElement])

    def MenuCommand(self, command):
        messenger.send(self.editor.getEventMsgName(command), [self.levelElement])
