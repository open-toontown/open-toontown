from pandac.PandaModules import Filename
from direct.directnotify import DirectNotifyGlobal
from direct.gui.DirectGui import DGG, DirectFrame, DirectButton
from toontown.shtiker import IssueFrame

class IssueFrameV2(IssueFrame.IssueFrame):
    notify = DirectNotifyGlobal.directNotify.newCategory('IssueFrameV2')
    SectionIdents = ['hom',
     'new',
     'evt',
     'tot',
     'att',
     'tnr',
     'ext']

    def __init__(self, parent, newsDir, dateStr, myIssueIndex, numIssues, strFilenames, newsIndexEntries):
        self.newsIndexEntries = newsIndexEntries
        self.dateStr = dateStr
        self.calcActualSectionsInThisIssue()
        IssueFrame.IssueFrame.__init__(self, parent, newsDir, dateStr, myIssueIndex, numIssues, strFilenames)
        self.notify.debug('version2 %s' % dateStr)

    def load(self):
        self.guiNavV2 = loader.loadModel('phase_3.5/models/gui/tt_m_gui_ign_directNewsGuiNavV2')
        IssueFrame.IssueFrame.load(self)

    def calcActualSectionsInThisIssue(self):
        self.actualSectionIdents = []
        for ident in self.SectionIdents:
            identTest = self.dateStr + '_' + ident + '1'
            if self.isSectionInIndex(identTest):
                self.actualSectionIdents.append(ident)

    def isSectionInIndex(self, sectionIdent):
        for name in self.newsIndexEntries:
            if sectionIdent in name and self.dateStr in name:
                return True

        return False

    def parseNewsContent(self):
        existingSectionIndex = 0
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
                        self.flatSubsectionList.append((existingSectionIndex, curSubSection))
                        curSubSection += 1
                    else:
                        endSearch = True
                else:
                    theFile = vfs.getFile(Filename(fullName), status_only=1)
                    if theFile:
                        subSectionList.append(fullName)
                        self.flatSubsectionList.append((existingSectionIndex, curSubSection))
                        curSubSection += 1
                    else:
                        if curSubSection == 0 and self.isSectionInIndex(ident):
                            self.notify.warning('could not find %s' % fullName)
                            subSectionList.append(fullName)
                            self.flatSubsectionList.append((existingSectionIndex, curSubSection))
                        endSearch = True

            if not subSectionList:
                pass
            else:
                self.sectionList.append(subSectionList)
                existingSectionIndex += 1

        self.notify.debug('IssueFrameV2 self.sectionList=%s' % self.sectionList)

    def loadHomePageButtons(self, section, subsection, pageFrame):
        self.notify.debug('Doing nothing for loadNavButtons')
        if section == 0 and subsection == 0:
            self.loadNavButtons(pageFrame)
            self.parentOfWeekNav = DirectFrame(frameColor=(1, 1, 1, 0), relief=DGG.FLAT, parent=pageFrame)
            self.loadWeekNavButtons(self.parentOfWeekNav)
            self.parentOfWeekNav.setPos(-1.94, 0, 0)

    def loadNavButtons(self, pageFrame):
        identToButtonNames = {'hom': 'tt_i_art_btn_NavHom2',
         'new': 'tt_i_art_btn_NavNew2',
         'evt': 'tt_i_art_btn_NavEvt2',
         'tot': 'tt_i_art_btn_NavTot2',
         'att': 'tt_i_art_btn_NavAtt2',
         'tnr': 'tt_i_art_btn_NavTnr2',
         'ext': 'tt_i_art_btn_NavExt2'}
        identToRolloverButtonNames = {'hom': 'tt_i_art_btn_NavHomRo2',
         'new': 'tt_i_art_btn_NavNewRo2',
         'evt': 'tt_i_art_btn_NavEvtRo2',
         'tot': 'tt_i_art_btn_NavTotRo2',
         'att': 'tt_i_art_btn_NavAttRo2',
         'tnr': 'tt_i_art_btn_NavTnrRo2',
         'ext': 'tt_i_art_btn_NavExtRo2'}
        xPos = 1.24667
        positions = [(xPos, 0, 0.623333),
         (xPos, 0, 0.536663),
         (xPos, 0, 0.45),
         (xPos, 0, 0.36333),
         (xPos, 0, 0.276667),
         (xPos, 0, 0.19),
         (xPos, 0, 0.08)]
        xSize1 = 177
        desiredXSize1 = 90
        image_scale1 = float(desiredXSize1) / xSize1
        image_scale = 1
        xSize2 = 300
        desiredXSize2 = 152
        image_scale2 = float(desiredXSize2) / xSize2
        image_scale2 *= 30.0 / 30.0
        rolloverPositions = [(1.045, 0, 0.623333),
         (1.045, 0, 0.533333),
         (1.045, 0, 0.443333),
         (1.045, 0, 0.353333),
         (1.045, 0, 0.263334),
         (1.045, 0, 0.173333),
         (1.045, 0, 0.09)]
        imageScales = [image_scale2,
         image_scale2,
         image_scale2,
         image_scale2,
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
        frameSizes = (frameSize2,
         frameSize2,
         frameSize2,
         frameSize2,
         frameSize2,
         frameSize2,
         frameSize2)
        self.sectionBtns = []
        for section, ident in enumerate(self.actualSectionIdents):
            image = self.guiNavV2.find('**/%s' % identToButtonNames[ident])
            rolloverImage = self.guiNavV2.find('**/%s' % identToRolloverButtonNames[ident])
            if image.isEmpty():
                self.notify.error('cant find %s' % identToButtonNames[ident])
            sectionBtn = DirectButton(relief=None, parent=pageFrame, frameSize=frameSizes[section], image=(image,
             rolloverImage,
             rolloverImage,
             image), image_scale=imageScales[section], command=self.gotoPage, extraArgs=(section, 0), enableEdit=1, pos=rolloverPositions[section])

        return
