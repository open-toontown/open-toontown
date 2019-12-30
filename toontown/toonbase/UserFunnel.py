import os, sys, socket, random
from urllib.parse import quote_plus
from pandac.PandaModules import HTTPClient
from pandac.PandaModules import HTTPCookie
from pandac.PandaModules import URLSpec
from pandac.PandaModules import Ramfile
from pandac.PandaModules import Ostream
from pandac.PandaModules import HTTPDate
from pandac.PandaModules import DocumentSpec
from direct.task.Task import Task
from direct.directnotify.DirectNotifyGlobal import directNotify
notify = directNotify.newCategory('UserFunnel')

class UserFunnel:

    def __init__(self):
        self.hitboxAcct = 'DM53030620EW'
        self.language = 'en-us'
        self.cgRoot = 'ToonTown_Online'
        self.cgBeta = 'Beta'
        self.cgRelease = 'Release'
        self.cgLocation = 'US'
        self.campaignID = ''
        self.cfCookieFile = 'cf.txt'
        self.dynamicVRFunnel = 'http://download.toontown.com/'
        self.hostDict = {0: 'Internal Disney PHP Collector Site',
         1: 'ehg-dig.hitbox.com/HG?',
         2: 'ehg-dig.hitbox.com/HG?',
         3: 'build64.online.disney.com:5020/index.php?'}
        self.CurrentHost = ''
        self.URLtoSend = ''
        self.gameName = 'ToonTown'
        self.browserName = 'Panda3D%20(' + self.gameName + ';%20' + sys.platform + ')'
        self.HTTPUserHeader = [('User-agent', 'Panda3D')]
        self.osMajorver = ''
        self.osMinorver = ''
        self.osRevver = ''
        self.osBuild = ''
        self.osType = ''
        self.osComments = ''
        self.msWinTypeDict = {0: 'Win32s on Windows 3.1',
         1: 'Windows 95/98/ME',
         2: 'Windows NT/2000/XP',
         3: 'Windows CE'}
        self.milestoneDict = {0: 'New User',
         1: 'Create Account',
         2: 'View EULA',
         3: 'Accept EULA',
         4: 'Download Start',
         5: 'Download End',
         6: 'Installer Run',
         7: 'Launcher Start',
         8: 'Launcher Login',
         9: 'Client Opens',
         10: 'Create Pirate Loads',
         11: 'Create Pirate Exit',
         12: 'Cutscene One Start',
         13: 'Cutscene One Ends',
         14: 'Cutscene Two Start',
         15: 'Cutscene Thee Start',
         16: 'Cutscene Three Ends',
         17: 'Access Cannon',
         18: 'Cutscene Four Starts',
         19: 'Cutscene Four Ends',
         20: 'Dock - Start Game'}
        self.macTypeDict = {2: 'Jaguar',
         1: 'Puma',
         3: 'Panther',
         4: 'Tiger',
         5: 'Lepard'}
        self.milestone = ''
        self.pandaHTTPClientVarWSS = []
        self.pandaHTTPClientVarCTG = []
        self.pandaHTTPClientVarDM = []
        self.checkForCFfile()
        self.httpSession = HTTPClient()
        self.whatOSver()

    def checkForCFfile(self):
        if firstRun() == True:
            pass
        elif os.path.isfile(self.cfCookieFile) == False:
            firstRun('write', True)

    def whatOSver(self):
        if sys.platform == 'win32':
            self.osMajorver = str(sys.getwindowsversion()[0])
            self.osMinorver = str(sys.getwindowsversion()[1])
            self.osBuild = str(sys.getwindowsversion()[2])
            self.osType = str(sys.getwindowsversion()[3])
            self.osComments = str(sys.getwindowsversion()[4])
            return
        if sys.platform == 'darwin':
            self.osMajorver = '10'
            osxcmd = '/usr/sbin/system_profiler SPSoftwareDataType |/usr/bin/grep "System Version"'
            infopipe = os.popen(osxcmd, 'r')
            parseLine = infopipe.read()
            infopipe.close()
            del infopipe
            notify.info('parseLine = %s' % str(parseLine))
            versionStringStart = parseLine.find('10.')
            notify.info('versionStringStart = %s' % str(versionStringStart))
            testPlist = False
            try:
                self.osMinorver = parseLine[versionStringStart + 3]
                self.osRevver = parseLine[versionStringStart + 5:versionStringStart + 7].strip(' ')
                self.osBuild = parseLine[int(parseLine.find('(')) + 1:parseLine.find(')')]
            except:
                notify.info("couldn't parse the system_profiler output, using zeros")
                self.osMinorver = '0'
                self.osRevver = '0'
                self.osBuild = '0000'
                testPlist = True

            del versionStringStart
            del parseLine
            del osxcmd
            if testPlist:
                try:
                    import plistlib
                    pl = plistlib.readPlist('/System/Library/CoreServices/SystemVersion.plist')
                    notify.info('pl=%s' % str(pl))
                    parseLine = pl['ProductVersion']
                    numbers = parseLine.split('.')
                    notify.info('parseline =%s numbers =%s' % (parseLine, numbers))
                    self.osMinorver = numbers[1]
                    self.osRevver = numbers[2]
                    self.osBuild = pl['ProductBuildVersion']
                except:
                    notify.info('tried plist but still got exception')
                    self.osMinorver = '0'
                    self.osRevver = '0'
                    self.osBuild = '0000'

            return

    def setmilestone(self, ms):
        if firstRun() == False:
            self.milestone = ms
        else:
            self.milestone = '%s_INITIAL' % ms

    def setgamename(self, gamename):
        self.gameName = gamename

    def printosComments(self):
        return self.osComments

    def setHost(self, hostID):
        self.CurrentHost = hostID

    def getFunnelURL(self):
        if patcherVer() == ['OFFLINE']:
            return
        if patcherVer() == []:
            patcherHTTP = HTTPClient()
            if checkParamFile() == None:
                patcherDoc = patcherHTTP.getDocument(URLSpec('http://download.toontown.com/english/currentVersion/content/patcher.ver'))
                vconGroup('w', self.cgRelease)
            else:
                patcherDoc = patcherHTTP.getDocument(URLSpec(checkParamFile()))
                vconGroup('w', self.cgBeta)
            rf = Ramfile()
            patcherDoc.downloadToRam(rf)
            self.patcherURL = rf.getData()
            if self.patcherURL.find('FUNNEL_LOG') == -1:
                patcherVer('w', 'OFFLINE')
                return
            self.patcherURL = self.patcherURL.split('\n')
            del rf
            del patcherDoc
            del patcherHTTP
            while self.patcherURL:
                self.confLine = self.patcherURL.pop()
                if self.confLine.find('FUNNEL_LOG=') != -1 and self.confLine.find('#FUNNEL_LOG=') == -1:
                    self.dynamicVRFunnel = self.confLine[11:].strip('\n')
                    patcherVer('w', self.confLine[11:].strip('\n'))

        else:
            self.dynamicVRFunnel = patcherVer()[0]
        return

    def isVarSet(self, varInQuestion):
        try:
            tempvar = type(varInQuestion)
            return 1
        except NameError:
            return 0

    def buildURL(self):
        if sys.platform == 'win32':
            hitboxOSType = 'c3'
        else:
            hitboxOSType = 'c4'
        if self.CurrentHost == 1:
            self.URLtoSend = 'http://' + self.hostDict[self.CurrentHost] + 'hb=' + str(self.hitboxAcct) + '&n=' + str(self.milestone) + '&ln=' + self.language + '&gp=STARTGAME&fnl=TOONTOWN_FUNNEL&vcon=/' + self.cgRoot + '/' + self.cgLocation + '/' + str(vconGroup()) + '&c1=' + str(sys.platform) + '&' + str(hitboxOSType) + '=' + str(self.osMajorver) + '_' + str(self.osMinorver) + '_' + str(self.osRevver) + '_' + str(self.osBuild)
        if self.CurrentHost == 2:
            self.URLtoSend = 'http://' + self.hostDict[self.CurrentHost] + 'hb=' + str(self.hitboxAcct) + '&n=' + str(self.milestone) + '&ln=' + self.language + '&vcon=/' + self.cgRoot + '/' + self.cgLocation + '/' + str(vconGroup()) + '&c1=' + str(sys.platform) + '&' + str(hitboxOSType) + '=' + str(self.osMajorver) + '_' + str(self.osMinorver) + '_' + str(self.osRevver) + '_' + str(self.osBuild)
        if self.CurrentHost == 0:
            localMAC = str(getMAC())
            self.URLtoSend = str(self.dynamicVRFunnel) + '?funnel=' + str(self.milestone) + '&platform=' + str(sys.platform) + '&sysver=' + str(self.osMajorver) + '_' + str(self.osMinorver) + '_' + str(self.osRevver) + '_' + str(self.osBuild) + '&mac=' + localMAC + '&username=' + str(loggingSubID()) + '&id=' + str(loggingAvID())

    def readInPandaCookie(self):
        thefile = open(self.cfCookieFile, 'r')
        thedata = thefile.read().split('\n')
        thefile.close()
        del thefile
        if thedata[0].find('Netscape HTTP Cookie File') != -1:
            return
        thedata.pop()
        try:
            while thedata:
                temp = thedata.pop()
                temp = temp.split('\t')
                domain = temp[0]
                loc = temp[1]
                variable = temp[2]
                value = temp[3]
                if variable == 'CTG':
                    self.pandaHTTPClientVarCTG = [domain,
                     loc,
                     variable,
                     value]
                    self.setTheHTTPCookie(self.pandaHTTPClientVarCTG)
                if variable == self.hitboxAcct + 'V6':
                    self.pandaHTTPClientVarDM = [domain,
                     loc,
                     variable,
                     value]
                    self.setTheHTTPCookie(self.pandaHTTPClientVarDM)
                if variable == 'WSS_GW':
                    self.pandaHTTPClientVarWSS = [domain,
                     loc,
                     variable,
                     value]
                    self.setTheHTTPCookie(self.pandaHTTPClientVarWSS)

        except IndexError:
            print('UserFunnel(Warning): Cookie Data file bad')

        del thedata

    def updateInstanceCookieValues(self):
        a = self.httpSession.getCookie(HTTPCookie('WSS_GW', '/', '.hitbox.com'))
        if a.getName():
            self.pandaHTTPClientVarWSS = ['.hitbox.com',
             '/',
             'WSS_GW',
             a.getValue()]
        b = self.httpSession.getCookie(HTTPCookie('CTG', '/', '.hitbox.com'))
        if b.getName():
            self.pandaHTTPClientVarCTG = ['.hitbox.com',
             '/',
             'CTG',
             b.getValue()]
        c = self.httpSession.getCookie(HTTPCookie(self.hitboxAcct + 'V6', '/', 'ehg-dig.hitbox.com'))
        if c.getName():
            self.pandaHTTPClientVarDM = ['ehg-dig.hitbox.com',
             '/',
             self.hitboxAcct + 'V6',
             c.getValue()]
        del a
        del b
        del c

    def setTheHTTPCookie(self, cookieParams):
        c = HTTPCookie(cookieParams[2], cookieParams[1], cookieParams[0])
        c.setValue(cookieParams[3])
        self.httpSession.setCookie(c)

    def writeOutPandaCookie(self):
        try:
            thefile = open(self.cfCookieFile, 'w')
            if len(self.pandaHTTPClientVarWSS) == 4:
                thefile.write(self.pandaHTTPClientVarWSS[0] + '\t' + self.pandaHTTPClientVarWSS[1] + '\t' + self.pandaHTTPClientVarWSS[2] + '\t' + self.pandaHTTPClientVarWSS[3] + '\n')
            if len(self.pandaHTTPClientVarCTG) == 4:
                thefile.write(self.pandaHTTPClientVarCTG[0] + '\t' + self.pandaHTTPClientVarCTG[1] + '\t' + self.pandaHTTPClientVarCTG[2] + '\t' + self.pandaHTTPClientVarCTG[3] + '\n')
            if len(self.pandaHTTPClientVarDM) == 4:
                thefile.write(self.pandaHTTPClientVarDM[0] + '\t' + self.pandaHTTPClientVarDM[1] + '\t' + self.pandaHTTPClientVarDM[2] + '\t' + self.pandaHTTPClientVarDM[3] + '\n')
            thefile.close()
        except IOError:
            return

    def prerun(self):
        self.getFunnelURL()
        self.buildURL()
        if os.path.isfile(self.cfCookieFile) == True:
            if self.CurrentHost == 1 or self.CurrentHost == 2:
                self.readInPandaCookie()

    def run(self):
        if self.CurrentHost == 0 and patcherVer() == ['OFFLINE']:
            return
        self.nonBlock = self.httpSession.makeChannel(False)
        self.nonBlock.beginGetDocument(DocumentSpec(self.URLtoSend))
        instanceMarker = str(random.randint(1, 1000))
        instanceMarker = 'FunnelLoggingRequest-%s' % instanceMarker
        self.startCheckingAsyncRequest(instanceMarker)

    def startCheckingAsyncRequest(self, name):
        taskMgr.remove(name)
        taskMgr.doMethodLater(0.5, self.pollFunnelTask, name)

    def stopCheckingFunnelTask(self, name):
        taskMgr.remove('pollFunnelTask')

    def pollFunnelTask(self, task):
        result = self.nonBlock.run()
        if result == 0:
            self.stopCheckingFunnelTask(task)
            if self.CurrentHost == 1 or self.CurrentHost == 2:
                self.updateInstanceCookieValues()
                self.writeOutPandaCookie()
        else:
            return Task.again


def logSubmit(setHostID, setMileStone):
    if __dev__:
        return
    trackItem = UserFunnel()
    trackItem.setmilestone(quote_plus(setMileStone))
    trackItem.setHost(setHostID)
    trackItem.prerun()
    trackItem.run()


def getVRSFunnelURL():
    a = UserFunnel()
    a.getFunnelURL()


class HitBoxCookie:

    def __init__(self):
        self.ieCookieDir = os.getenv('USERPROFILE') + '\\Cookies'
        self.pythonCookieFile = 'cf.txt'
        self.hitboxCookieFile = None
        self.ehgdigCookieFile = None
        self.hitboxAcct = 'DM53030620EW'
        self.ctg = None
        self.wss_gw = None
        self.dmAcct = None
        self.pythonCookieHeader = '    # Netscape HTTP Cookie File\n    # http://www.netscape.com/newsref/std/cookie_spec.html\n    # This is a generated file!  Do not edit.\n\n'
        return

    def returnIECookieDir(self):
        return self.ieCookieDir

    def findIECookieFiles(self):
        try:
            sdir = os.listdir(self.ieCookieDir)
        except WindowsError:
            print('Dir does not exist, do nothing')
            return

        while sdir:
            temp = sdir.pop()
            if temp.find('@hitbox[') != -1:
                self.hitboxCookieFile = temp
            if temp.find('@ehg-dig.hitbox[') != -1:
                self.ehgdigCookieFile = temp

        if self.hitboxCookieFile != None and self.ehgdigCookieFile != None:
            return 1
        if self.hitboxCookieFile == None and self.ehgdigCookieFile == None:
            return 0
        else:
            return -1
        return

    def openHitboxFile(self, filename, type = 'python'):
        if type == 'ie':
            fullfile = self.ieCookieDir + '\\' + filename
        else:
            fullfile = filename
        cf = open(fullfile, 'r')
        data = cf.read()
        cf.close()
        return data

    def splitIECookie(self, filestream):
        return filestream.split('*\n')

    def sortIECookie(self, filestreamListElement):
        return [filestreamListElement.split('\n')[2], filestreamListElement.split('\n')[0], filestreamListElement.split('\n')[1]]

    def sortPythonCookie(self, filestreamListElement):
        return [filestreamListElement.split('\t')[0], filestreamListElement.split('\t')[5], filestreamListElement.split('\t')[6]]

    def writeIEHitBoxCookies(self):
        if self.ctg == None or self.wss_gw == None or self.dmAcct == None:
            return
        if sys.platform != 'win32':
            return
        self.findIECookieFiles()
        iecData = self.openHitboxFile(self.ehgdigCookieFile, 'ie')
        iecData = iecData.split('*\n')
        x = 0
        while x < len(iecData):
            if iecData[x].find(self.hitboxAcct) != -1:
                iecData.pop(x)
                print('Removed it from the list')
                break
            x += 1

        iecWrite = open(self.ieCookieDir + '\\' + self.ehgdigCookieFile, 'w')
        while iecData:
            iecBuffer = iecData.pop() + '*\n'
            iecBuffer = iecBuffer.strip('/')
            if iecBuffer[0] == '.':
                iecBuffer = iecBuffer[1:]
            iecWrite.write(iecBuffer)

        tempDMBUFFER = self.dmAcct[0]
        if tempDMBUFFER[0].find('.') == 0:
            tempDMBUFFER = tempDMBUFFER[1:]
        iecWrite.write(self.dmAcct[1] + '\n' + self.dmAcct[2] + '\n' + tempDMBUFFER + '/\n*\n')
        iecWrite.close()
        del iecData
        del iecWrite
        del iecBuffer
        iecWrite = open(self.ieCookieDir + '\\' + self.hitboxCookieFile, 'w')
        iecBuffer = self.ctg[0]
        if iecBuffer[0] == '.':
            iecBuffer = iecBuffer[1:]
        if iecBuffer.find('/') == -1:
            iecBuffer = iecBuffer + '/'
        iecWrite.write(self.ctg[1] + '\n' + self.ctg[2] + '\n' + iecBuffer + '\n*\n')
        iecWrite.write(self.wss_gw[1] + '\n' + self.wss_gw[2] + '\n' + iecBuffer + '\n*\n')
        iecWrite.close()
        return

    def OLDwritePythonHitBoxCookies(self, filename = 'cf.txt'):
        if self.ctg == None or self.wss_gw == None or self.dmAcct == None:
            return
        outputfile = open(filename, 'w')
        outputfile.write(self.pythonCookieHeader)
        outputfile.write('.' + self.dmAcct[0].strip('/') + '\tTRUE\t/\tFALSE\t9999999999\t' + self.dmAcct[1] + '\t' + self.dmAcct[2] + '\n')
        outputfile.write('.' + self.ctg[0].strip('/') + '\tTRUE\t/\tFALSE\t9999999999\t' + self.ctg[1] + '\t' + self.ctg[2] + '\n')
        outputfile.write('.' + self.wss_gw[0].strip('/') + '\tTRUE\t/\tFALSE\t9999999999\t' + self.wss_gw[1] + '\t' + self.wss_gw[2] + '\n')
        outputfile.close()
        return

    def writePythonHitBoxCookies(self, filename = 'cf.txt'):
        if self.ctg == None or self.wss_gw == None or self.dmAcct == None:
            return
        outputfile = open(filename, 'w')
        outputfile.write('.' + self.dmAcct[0].strip('/') + '\t/\t' + self.dmAcct[1] + '\t' + self.dmAcct[2] + '\n')
        outputfile.write('.' + self.ctg[0].strip('/') + '\t/\t' + self.ctg[1] + '\t' + self.ctg[2] + '\n')
        outputfile.write('.' + self.wss_gw[0].strip('/') + '\t/\t' + self.wss_gw[1] + '\t' + self.wss_gw[2] + '\n')
        outputfile.close()
        return

    def loadPythonHitBoxCookies(self):
        if os.path.isfile(self.pythonCookieFile) != 1:
            return
        pythonStandard = self.openHitboxFile(self.pythonCookieFile, 'python')
        pythonStandard = pythonStandard.split('\n\n').pop(1)
        pythonStandard = pythonStandard.split('\n')
        for x in pythonStandard:
            if x.find('\t' + self.hitboxAcct) != -1:
                self.dmAcct = self.sortPythonCookie(x)
            if x.find('\tCTG\t') != -1:
                self.ctg = self.sortPythonCookie(x)
            if x.find('\tWSS_GW\t') != -1:
                self.wss_gw = self.sortPythonCookie(x)

    def loadIEHitBoxCookies(self):
        if self.findIECookieFiles() != 1:
            return
        if sys.platform != 'win32':
            return
        hitboxStandard = self.openHitboxFile(self.hitboxCookieFile, 'ie')
        hitboxDIG = self.openHitboxFile(self.ehgdigCookieFile, 'ie')
        hitboxStandard = self.splitIECookie(hitboxStandard)
        hitboxDIG = self.splitIECookie(hitboxDIG)
        ctg = None
        wss = None
        for x in hitboxStandard:
            if x.find('CTG\n') != -1:
                ctg = x
            if x.find('WSS_GW\n') != -1:
                wss = x

        if ctg == None or wss == None:
            return
        DM = None
        for x in hitboxDIG:
            if x.find(self.hitboxAcct) != -1:
                DM = x

        if DM == None:
            return
        self.ctg = self.sortIECookie(ctg)
        self.wss_gw = self.sortIECookie(wss)
        self.dm560804E8WD = self.sortIECookie(DM)
        return


def convertHitBoxIEtoPython():
    if sys.platform != 'win32':
        print('Cookie Converter: Warning: System is not MS-Windows. I have not been setup to work with other systems yet. Sorry ' + sys.platform + ' user. The game client will create a cookie.')
        return
    if __dev__:
        return
    a = HitBoxCookie()
    a.loadIEHitBoxCookies()
    a.writePythonHitBoxCookies()
    del a


def convertHitBoxPythontoIE():
    if sys.platform != 'win32':
        print('System is not MS-Windows. I have not been setup to work with other systems yet. Sorry ' + sys.platform + ' user.')
        return
    if os.path.isfile('cf.txt') == True:
        return
    a = HitBoxCookie()
    a.loadPythonHitBoxCookies()
    a.writeIEHitBoxCookies()
    del a


def getreg(regVar):
    if sys.platform != 'win32':
        print("System is not MS-Windows. I haven't been setup yet to work with systems other than MS-Win using MS-Internet Explorer Cookies")
        return ''
    siteName = 'toontown.online.disney'
    cookiedir = os.getenv('USERPROFILE') + '\\Cookies'
    sdir = os.listdir(cookiedir)
    wholeCookie = None
    while sdir:
        temp = sdir.pop()
        if temp.find(siteName) != -1:
            wholeCookie = temp
            break

    if wholeCookie == None:
        print('Cookie not found for site name: ' + siteName)
        return ''
    CompleteCookiePath = cookiedir + '\\' + wholeCookie
    cf = open(CompleteCookiePath, 'r')
    data = cf.read()
    cf.close()
    del cf
    data = data.replace('%3D', '=')
    data = data.replace('%26', '&')
    regNameStart = data.find(regVar)
    if regNameStart == -1:
        return ''
    regVarStart = data.find('=', regNameStart + 1)
    regVarEnd = data.find('&', regNameStart + 1)
    return data[regVarStart + 1:regVarEnd]


def getMAC(staticMAC = [None]):
    if staticMAC[0] == None:
        if sys.platform == 'win32':
            correctSection = 0
            try:
                ipconfdata = os.popen('/WINDOWS/SYSTEM32/ipconfig /all').readlines()
            except:
                staticMAC[0] = 'NO_MAC'
                return staticMAC[0]

            for line in ipconfdata:
                if line.find('Local Area Connection') >= 0:
                    correctSection = 1
                if line.find('Physical Address') >= 0 and correctSection == 1:
                    pa = line.split(':')[-1].strip()
                    correctSection = 0
                    staticMAC[0] = pa
                    return pa

        if sys.platform == 'darwin':
            macconfdata = os.popen('/usr/sbin/system_profiler SPNetworkDataType |/usr/bin/grep MAC').readlines()
            result = '-1'
            if macconfdata:
                if macconfdata[0].find('MAC Address') != -1:
                    pa = macconfdata[0][macconfdata[0].find(':') + 2:macconfdata[0].find(':') + 22].strip('\n')
                    staticMAC[0] = pa.replace(':', '-')
                    result = staticMAC[0]
            return result
        if sys.platform != 'darwin' and sys.platform != 'win32':
            print('System is not running OSX or MS-Windows.')
            return '-2'
    else:
        return staticMAC[0]
    return


def firstRun(operation = 'read', newPlayer = None, newPlayerBool = [False]):
    if operation != 'read':
        if len(newPlayerBool) != 0:
            newPlayerBool.pop()
        newPlayerBool.append(newPlayer)
    return newPlayerBool[0]


def patcherVer(operation = 'read', url = None, patchfile = []):
    if operation != 'read':
        if len(patchfile) != 0:
            patchfile.pop()
        patchfile.append(url)
    return patchfile


def loggingAvID(operation = 'read', newId = None, localAvId = [None]):
    if operation == 'write':
        localAvId[0] = newId
    else:
        return localAvId[0]


def loggingSubID(operation = 'read', newId = None, localSubId = [None]):
    if operation == 'write':
        localSubId[0] = newId
    else:
        return localSubId[0]


def vconGroup(operation = 'read', group = None, staticStore = []):
    if operation != 'read':
        if len(staticStore) != 0:
            staticStore.pop()
        staticStore.append(group)
    try:
        return staticStore[0]
    except IndexError:
        return None

    return None


def printUnreachableLen():
    import gc
    gc.set_debug(gc.DEBUG_SAVEALL)
    gc.collect()
    unreachableL = []
    for it in gc.garbage:
        unreachableL.append(it)

    return len(str(unreachableL))


def printUnreachableNum():
    import gc
    gc.set_debug(gc.DEBUG_SAVEALL)
    gc.collect()
    return len(gc.garbage)


def reportMemoryLeaks():
    if printUnreachableNum() == 0:
        return
    import bz2, gc
    gc.set_debug(gc.DEBUG_SAVEALL)
    gc.collect()
    uncompressedReport = ''
    for s in gc.garbage:
        try:
            uncompressedReport += str(s) + '&'
        except TypeError:
            pass

    reportdata = bz2.compress(uncompressedReport, 9)
    headers = {'Content-type': 'application/x-bzip2',
     'Accept': 'text/plain'}
    try:
        baseURL = patcherVer()[0].split('/lo')[0]
    except IndexError:
        print('Base URL not available for leak submit')
        return

    basePort = 80
    if baseURL.count(':') == 2:
        basePort = baseURL[-4:]
        baseURL = baseURL[:-5]
    baseURL = baseURL[7:]
    if basePort != 80:
        finalURL = 'http://' + baseURL + ':' + str(basePort) + '/logging/memory_leak.php?leakcount=' + str(printUnreachableNum())
    else:
        finalURL = 'http://' + baseURL + '/logging/memory_leak.php?leakcount=' + str(printUnreachableNum())
    reporthttp = HTTPClient()
    reporthttp.postForm(URLSpec(finalURL), reportdata)


def checkParamFile():
    if os.path.exists('parameters.txt') == 1:
        paramfile = open('parameters.txt', 'r')
        contents = paramfile.read()
        paramfile.close()
        del paramfile
        contents = contents.split('\n')
        newURL = ''
        while contents:
            checkLine = contents.pop()
            if checkLine.find('PATCHER_BASE_URL=') != -1 and checkLine[0] == 'P':
                newURL = checkLine.split('=')[1]
                newURL = newURL.replace(' ', '')
                break

        if newURL == '':
            return
        else:
            return newURL + 'patcher.ver'
