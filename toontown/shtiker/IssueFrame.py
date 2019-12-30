import os
from pandac.PandaModules import VirtualFileSystem, Filename, DSearchPath
from pandac.PandaModules import Texture, CardMaker, PNMImage, TextureStage
from pandac.PandaModules import NodePath
from pandac.PandaModules import Point2
from direct.showbase import DirectObject
from direct.gui.DirectGui import DirectFrame, DirectButton, DGG, DirectLabel
from direct.directnotify import DirectNotifyGlobal
from toontown.toonbase import TTLocalizer
from toontown.toonbase import ToontownGlobals
WEB_WIDTH_PIXELS = 784
WEB_HEIGHT_PIXELS = 451
WEB_WIDTH = 1024
WEB_HEIGHT = 512
WEB_HALF_WIDTH = WEB_WIDTH / 2
WIN_WIDTH = 800
WIN_HEIGHT = 600

class IssueFrame(DirectFrame):
    NewsBaseDir = config.GetString('news-base-dir', '/httpNews')
    FrameDimensions = (-1.30666637421,
     1.30666637421,
     -0.751666665077,
     0.751666665077)
    notify = DirectNotifyGlobal.directNotify.newCategory('IssueFrame')
    ContentPattern = 'tt_i_art_%s_%s%d.jpg'
    SectionIdents = ['hom',
     'new',
     'evt',
     'tot',
     'att',
     'tnr']

    def __init__(self, parent, newsDir, dateStr, myIssueIndex, numIssues, strFilenames):
        DirectFrame.__init__(self, frameColor=(1, 1, 1, 0), frameSize=self.FrameDimensions, relief=DGG.FLAT, parent=parent)
        self.hide()
        self.accept('newsSnapshot', self.doSnapshot)
        self._parent = parent
        self.newsDir = newsDir
        self.dateStr = dateStr
        self.myIssueIndex = myIssueIndex
        self.numIssues = numIssues
        self.strFilenames = strFilenames
        self.sectionList = []
        self.sectionFrames = {}
        self.flatSubsectionList = []
        self.parseNewsContent()
        self.load()
        self.curSection = 0
        self.curSubsection = 0

    def parseNewsContent(self):
        for section, ident in enumerate(self.SectionIdents):
            subSectionList = []
            curSubSection = 0
            endSearch = False
            while not endSearch:
                justName = self.ContentPattern % (self.dateStr, ident, curSubSection + 1)
                fullName = Filename(self.newsDir + '/' + justName)
                if self.strFilenames:
                    if justName in self.strFilenames:
                        subSectionList.append(fullName)
                        self.flatSubsectionList.append((section, curSubSection))
                        curSubSection += 1
                    else:
                        endSearch = True
                else:
                    theFile = vfs.getFile(Filename(fullName), status_only=1)
                    if theFile:
                        subSectionList.append(fullName)
                        self.flatSubsectionList.append((section, curSubSection))
                        curSubSection += 1
                    else:
                        endSearch = True

            if not subSectionList:
                self.notify.warning('Could not load %s' % fullName)
                subSectionList.append('error_' + str(fullName))
                self.flatSubsectionList.append((section, 0))
            self.sectionList.append(subSectionList)

        self.notify.debug('%s' % self.sectionList)

    def getPreviousTarget(self, section, subSection):
        result = None
        if (section, subSection) in self.flatSubsectionList:
            index = self.flatSubsectionList.index((section, subSection))
            if index > 0:
                result = self.flatSubsectionList[index - 1]
        return result

    def getNextTarget(self, section, subSection):
        result = None
        if (section, subSection) in self.flatSubsectionList:
            index = self.flatSubsectionList.index((section, subSection))
            if index < len(self.flatSubsectionList) - 1:
                result = self.flatSubsectionList[index + 1]
        return result

    def load(self):
        self.gui = loader.loadModel('phase_3.5/models/gui/tt_m_gui_ign_directNewsGui')
        self.guiNav = loader.loadModel('phase_3.5/models/gui/tt_m_gui_ign_directNewsGuiNav')
        numPagesLoaded = 0
        totalNumberOfPages = len(self.flatSubsectionList)
        for section, subSectionList in enumerate(self.sectionList):
            self.notify.debug('loading section %d' % section)
            self.sectionFrames[section] = {}
            for subsection, fullFilename in enumerate(subSectionList):
                self.notify.debug('loading subsection %d' % subsection)
                newPage = self.createPage(section, subsection, fullFilename)
                numPagesLoaded += 1
                self.sectionFrames[section][subsection] = newPage

    def createPage(self, section, subsection, fullFilename):
        upsellBackground = loader.loadModel('phase_3.5/models/gui/tt_m_gui_ign_newsStatusBackground')
        imageScaleX = self.FrameDimensions[1] - self.FrameDimensions[0]
        imageScaleY = self.FrameDimensions[3] - self.FrameDimensions[2]
        pageFrame = DirectFrame(frameColor=(1, 1, 1, 0), frameSize=self.FrameDimensions, image=upsellBackground, image_scale=(imageScaleX, 1, imageScaleY), relief=DGG.FLAT, parent=self, text='', text_scale=0.06, text_pos=(0, -0.4))
        if 'error_' in str(fullFilename):
            pageFrame['text'] = TTLocalizer.NewsPageErrorDownloadingFileCanStillRead % fullFilename[len('error_'):]
        else:
            quad = self.loadFlatQuad(fullFilename)
            if quad:
                quad.reparentTo(pageFrame)
            else:
                pageFrame['text'] = TTLocalizer.NewsPageErrorDownloadingFileCanStillRead % fullFilename
        self.loadRightArrow(section, subsection, pageFrame)
        self.loadLeftArrow(section, subsection, pageFrame)
        if section == 0 and subsection == 0:
            self.loadHomePageButtons(section, subsection, pageFrame)
        else:
            self.loadNavButtons(pageFrame)
            pageFrame.hide()
        return pageFrame

    def loadRightArrow(self, section, subsection, pageFrame):
        nextTarget = self.getNextTarget(section, subsection)
        position = (1.16, 0, -0.69)
        xSize = 48
        desiredXSize = 22
        imageScale = float(desiredXSize) / xSize
        if nextTarget:
            image = self.gui.find('**/tt_i_art_btn_ArrowRight')
            rollover = self.gui.find('**/tt_i_art_btn_ArrowRightRo')
            rightArrow = DirectButton(relief=None, parent=pageFrame, command=self.gotoPage, extraArgs=(nextTarget[0], nextTarget[1]), image=(image,
             image,
             rollover,
             image), pos=position, image_scale=imageScale)
        return

    def loadLeftArrow(self, section, subsection, pageFrame):
        prevTarget = self.getPreviousTarget(section, subsection)
        position = (-1.16, 0, -0.69)
        xSize = 48
        desiredXSize = 22
        imageScale = float(desiredXSize) / xSize
        if prevTarget:
            image = self.gui.find('**/tt_i_art_btn_ArrowLeft')
            rollover = self.gui.find('**/tt_i_art_btn_ArrowLeftRo')
            rightArrow = DirectButton(relief=None, parent=pageFrame, command=self.gotoPage, extraArgs=(prevTarget[0], prevTarget[1]), image=(image,
             image,
             rollover,
             image), pos=position, image_scale=imageScale)
        return

    def loadHomePageButtons(self, section, subsection, pageFrame):
        buttonNames = ['',
         'tt_i_art_btn_HomNew',
         'tt_i_art_btn_HomEvt',
         'tt_i_art_btn_HomTot',
         'tt_i_art_btn_HomAsk',
         'tt_i_art_btn_HomTnr']
        rolloverButtonNames = []
        for name in buttonNames:
            ro = name + 'Ro'
            rolloverButtonNames.append(ro)

        positions = [(0, 0.0),
         (-1.05333, 0, 0.29333),
         (-1.05333, 0, 0.0666667),
         (-1.05333, 0, -0.156667),
         (-1.05333, 0, -0.383333),
         (-1.05333, 0, -0.606667)]
        xSize = 136
        desiredXSize = 69
        image_scale = float(desiredXSize) / xSize
        image_scale *= float(69) / 70
        self.sectionBtns = []
        for section in range(1, len(self.SectionIdents)):
            image = self.gui.find('**/%s' % buttonNames[section])
            rolloverImage = self.gui.find('**/%s' % rolloverButtonNames[section])
            if image.isEmpty():
                self.notify.error('cant find %s' % buttonNames[section])
            sectionBtn = DirectButton(relief=None, parent=pageFrame, image=(image,
             image,
             rolloverImage,
             image), image_scale=image_scale, command=self.gotoPage, extraArgs=(section, 0), enableEdit=1, pos=positions[section])

        readMorePos = (0.906666, 0, -0.19)
        readImage = self.gui.find('**/tt_i_art_btn_ReadMore')
        readRollover = self.gui.find('**/tt_i_art_btn_ReadMoreRo')
        xSize = 228.0
        desiredXSize = 113.0
        imageScale = desiredXSize / xSize
        readMoreBtn = DirectButton(relief=None, parent=pageFrame, image=(readImage,
         readImage,
         readRollover,
         readImage), image_scale=imageScale, command=self.gotoPage, extraArgs=(1, 0), enableEdit=1, pos=readMorePos)
        self.loadWeekNavButtons(pageFrame)
        return

    def loadWeekNavButtons(self, pageFrame):
        if self.numIssues <= 1:
            return
        if self.myIssueIndex == self.numIssues - 1:
            weekStr = TTLocalizer.IssueFrameThisWeek
        elif self.myIssueIndex == self.numIssues - 2:
            weekStr = TTLocalizer.IssueFrameLastWeek
        else:
            weeksAgo = self.numIssues - self.myIssueIndex - 1
            weekStr = TTLocalizer.IssueFrameWeeksAgo % weeksAgo
        prevImage = self.gui.find('**/tt_i_art_btn_ArchiveArrwLeftNormal')
        prevImageRo = self.gui.find('**/tt_i_art_btn_ArchiveArrwLeftRo')
        prevImageDisabled = self.gui.find('**/tt_i_art_btn_ArchiveArrwLeftDisabled')
        actualY1 = 78.0
        desiredY1 = 42.0
        y1Scale = desiredY1 / actualY1
        prevWeekBtn = DirectButton(relief=None, parent=pageFrame, image=[prevImage,
         prevImage,
         prevImageRo,
         prevImageDisabled], image_scale=y1Scale, command=self.changeWeek, extraArgs=(self.myIssueIndex - 1,), pos=(0.806666, 0, 0.62))
        if self.myIssueIndex == 0:
            prevWeekBtn['state'] = DGG.DISABLED
        nextImage = self.gui.find('**/tt_i_art_btn_ArchiveArrwRightNormal')
        nextImageRo = self.gui.find('**/tt_i_art_btn_ArchiveArrwRightRo')
        nextImageDisabled = self.gui.find('**/tt_i_art_btn_ArchiveArrwRightDisabled')
        actualY2Scale = 63.0
        desiredY2Scale = 34.0
        y2Scale = desiredY2Scale / actualY2Scale
        nextWeekBtn = DirectButton(relief=None, parent=pageFrame, image=[nextImage,
         nextImage,
         nextImageRo,
         nextImageDisabled], image_scale=y2Scale, command=self.changeWeek, extraArgs=(self.myIssueIndex + 1,), pos=(1.16, 0, 0.623333))
        if self.myIssueIndex == self.numIssues - 1:
            nextWeekBtn['state'] = DGG.DISABLED
        actualX = 176.0
        desiredX = 89.0
        imageScale = desiredX / actualX
        midImage = self.gui.find('**/tt_i_art_btn_ArchiveMiddle')
        weekColor = (0.0 / 255.0,
         23.0 / 255.0,
         140.0 / 255.0,
         1.0)
        weekLabel = DirectLabel(relief=None, image=midImage, image_scale=imageScale, parent=pageFrame, text=weekStr, text_font=ToontownGlobals.InterfaceFont, text_fg=weekColor, text_scale=0.043, text_pos=(0, -0.01, 0), pos=(0.983333, 0, 0.62))
        return

    def loadNavButtons(self, pageFrame):
        buttonNames = ['tt_i_art_btn_NavHom',
         'tt_i_art_btn_NavNew',
         'tt_i_art_btn_NavEvt',
         'tt_i_art_btn_NavTot',
         'tt_i_art_btn_NavAtt',
         'tt_i_art_btn_NavTnr']
        rolloverButtonNames = []
        for name in buttonNames:
            ro = name + 'Ro'
            rolloverButtonNames.append(ro)

        xPos = 1.24667
        positions = [(xPos, 0, 0.623333),
         (xPos, 0, 0.536663),
         (xPos, 0, 0.45),
         (xPos, 0, 0.36333),
         (xPos, 0, 0.276667),
         (xPos, 0, 0.19)]
        xSize1 = 177
        desiredXSize1 = 90
        image_scale1 = float(desiredXSize1) / xSize1
        image_scale = 1
        xSize2 = 300
        desiredXSize2 = 152
        image_scale2 = float(desiredXSize2) / xSize2
        image_scale2 *= 30.0 / 30.0
        rolloverPositions = [(1.15, 0, 0.623333),
         (1.15, 0, 0.533333),
         (1.15, 0, 0.443333),
         (1.045, 0, 0.353333),
         (1.045, 0, 0.263334),
         (1.045, 0, 0.173333)]
        imageScales = [image_scale1,
         image_scale1,
         image_scale1,
         image_scale2,
         image_scale2,
         image_scale2]
        frameSizeAdj1 = 0.1
        frameSize1 = (-0.04 + frameSizeAdj1,
         0.04 + frameSizeAdj1,
         -0.04,
         0.04)
        frameSizeAdj2 = 0.21
        frameSize2 = (-0.04 + frameSizeAdj2,
         0.04 + frameSizeAdj2,
         -0.04,
         0.04)
        frameSizes = (frameSize1,
         frameSize1,
         frameSize1,
         frameSize2,
         frameSize2,
         frameSize2)
        self.sectionBtns = []
        for section in range(0, len(self.SectionIdents)):
            image = self.guiNav.find('**/%s' % buttonNames[section])
            rolloverImage = self.guiNav.find('**/%s' % rolloverButtonNames[section])
            if image.isEmpty():
                self.notify.error('cant find %s' % buttonNames[section])
            sectionBtn = DirectButton(relief=None, parent=pageFrame, frameSize=frameSizes[section], image=(image,
             rolloverImage,
             rolloverImage,
             image), image_scale=imageScales[section], command=self.gotoPage, extraArgs=(section, 0), enableEdit=1, pos=rolloverPositions[section])

        return

    def gotoPage(self, section, subsection):
        if base.config.GetBool('want-qa-regression', 0):
            self.notify.info('QA-REGRESSION: INGAMENEWS: Goto Page')
        self.sectionFrames[self.curSection][self.curSubsection].hide()
        self.sectionFrames[section][subsection].show()
        self.curSection = section
        self.curSubsection = subsection
        messenger.send('wakeup')
        base.cr.centralLogger.writeClientEvent('news gotoPage %s %s %s' % (self.dateStr, section, subsection))

    def loadFlatQuad(self, fullFilename):
        cm = CardMaker('cm-%s' % fullFilename)
        cm.setColor(1.0, 1.0, 1.0, 1.0)
        aspect = base.camLens.getAspectRatio()
        htmlWidth = 2.0 * aspect * WEB_WIDTH_PIXELS / float(WIN_WIDTH)
        htmlHeight = 2.0 * float(WEB_HEIGHT_PIXELS) / float(WIN_HEIGHT)
        cm.setFrame(-htmlWidth / 2.0, htmlWidth / 2.0, -htmlHeight / 2.0, htmlHeight / 2.0)
        bottomRightX = WEB_WIDTH_PIXELS / float(WEB_WIDTH + 1)
        bottomRightY = WEB_HEIGHT_PIXELS / float(WEB_HEIGHT + 1)
        cm.setUvRange(Point2(0, 1 - bottomRightY), Point2(bottomRightX, 1))
        card = cm.generate()
        quad = NodePath(card)
        jpgFile = PNMImage(WEB_WIDTH, WEB_HEIGHT)
        smallerJpgFile = PNMImage()
        readFile = smallerJpgFile.read(Filename(fullFilename))
        if readFile:
            jpgFile.copySubImage(smallerJpgFile, 0, 0)
            guiTex = Texture('guiTex')
            guiTex.setupTexture(Texture.TT2dTexture, WEB_WIDTH, WEB_HEIGHT, 1, Texture.TUnsignedByte, Texture.FRgba)
            guiTex.setMinfilter(Texture.FTLinear)
            guiTex.load(jpgFile)
            guiTex.setWrapU(Texture.WMClamp)
            guiTex.setWrapV(Texture.WMClamp)
            ts = TextureStage('webTS')
            quad.setTexture(ts, guiTex)
            quad.setTransparency(0)
            quad.setTwoSided(True)
            quad.setColor(1.0, 1.0, 1.0, 1.0)
            result = quad
        else:
            result = None
        Texture.setTexturesPower2(1)
        return result

    def loadBackground(self):
        self.backFrame = DirectFrame(parent=self, frameColor=(1, 1, 1, 1), frameSize=self.FrameDimensions, pos=(0, 0, 0), relief=None)
        return

    def loadMainPage(self):
        self.mainFrame = DirectFrame(parent=self, frameSize=self.FrameDimensions, frameColor=(1, 0, 0, 1))

    def activate(self):
        pass

    def deactivate(self):
        pass

    def unload(self):
        self.ignore('newsSnapshot')

    def doSnapshot(self):
        pass

    def changeWeek(self, newIssueWeek):
        if base.config.GetBool('want-qa-regression', 0):
            self.notify.info('QA-REGRESSION: INGAMENEWS: Change Week')
        messenger.send('newsChangeWeek', [newIssueWeek])
